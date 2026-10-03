"""new_trial_discovery — EXPANSÃO DE COBERTURA: ensaios oncológicos relevantes que ainda NÃO têm card.

Componente SEPARADO do discovery (que busca publicações novas de cards existentes) e do delta, com versão/hash
próprio (NOVOS_VERSION). Não altera discovery, delta, cards, data.js, secondary-cards.js nem app-data. Nada é
aplicado: a saída é fila de revisão humana.

    python3 scripts/db_v2/agents/new_trial_discovery.py universo                 # escopo editorial inferido dos 503 cards
    python3 scripts/db_v2/agents/new_trial_discovery.py schemas
    python3 scripts/db_v2/agents/new_trial_discovery.py coletar --rede           # CT.gov v2 + PubMed (cache em state/cache)
    python3 scripts/db_v2/agents/new_trial_discovery.py piloto --n 25            # seleção estratificada para o LLM
    python3 scripts/db_v2/agents/new_trial_discovery.py lote --rede [--paralelo 4]
    python3 scripts/db_v2/agents/new_trial_discovery.py consolidar

Fluxo:  coleta (CT.gov v2, PubMed) → candidato por ensaio (NCT) ou publicação sem registro → deduplicação
determinística contra os 503 cards e as 34 secundárias (ALREADY_EXISTS / RELATED_TO_EXISTING / POSSIBLE_DUPLICATE /
NEW_STUDY_CANDIDATE) → filtros editoriais determinísticos → curator → verifier → checagens → fila humana.
Fontes proibidas: Explorer, tracker, o próprio TheraTrials como evidência (os cards entram só como contexto de
cobertura, marcado como tal).
"""
from __future__ import annotations

import argparse
import collections
import concurrent.futures as cf
import datetime
import difflib
import hashlib
import json
import os
import pathlib
import re
import sys
import threading
import urllib.parse

AQUI = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))

try:
    from . import agent_types as T, checks as K, discovery as DS, sources as S
except ImportError:
    import agent_types as T
    import checks as K
    import discovery as DS
    import sources as S

import bibliografia as B  # noqa: E402

DIR = S.STATE / "novos"
NOVOS_BASE = "novos/1"
INSTRUCOES = AQUI / "novos_instrucoes.md"
DEDUP = ["ALREADY_EXISTS", "RELATED_TO_EXISTING", "POSSIBLE_DUPLICATE", "NEW_STUDY_CANDIDATE"]
ACOES = ["NEW_CARD", "RELATED_TO_EXISTING", "WATCH", "NO_ACTION", "HUMAN_REVIEW"]
MATURIDADE = ["published_primary", "published_secondary_only", "registry_results_only", "congress_provisional",
              "ongoing_no_results", "undetermined"]
BASE_POLITICA = ["fase3_pergunta_nao_representada", "fase2_randomizado_relevancia_clara", "fase2_negativo_relevante",
                 "excecao_braco_unico_radioligante", "excecao_braco_unico_tumor_agnostico", "excecao_braco_unico_doenca_rara",
                 "excecao_braco_unico_registracional", "excecao_braco_unico_sem_comparador", "excecao_fase1",
                 "cirurgia_randomizada_relevante", "formulacao_sc_registracional", "extensao_regional_questao_propria",
                 "congresso_fase3_provisorio", "nao_se_aplica"]
EXCECOES_BRACO_UNICO = {b for b in BASE_POLITICA if b.startswith("excecao_braco_unico")}
TIPOS_COMPARACAO = ["randomizado_vs_padrao", "randomizado_vs_nao_padrao", "randomizado_nao_comparativo", "braco_unico",
                    "nao_se_aplica"]
STR, NSTR = {"type": "string"}, {"type": ["string", "null"]}

NOVOS_SCHEMA = {
    "$id": "theratrials-db-novos-curator/1", "type": "object",
    "properties": {
        "schema": {"const": "theratrials-db-novos-curator/1"}, "cand_id": STR, "packet_sha256": STR,
        "action": {"enum": ACOES}, "study": STR, "nct": NSTR,
        "main_publication": {"type": ["object", "null"], "properties": {"pmid": NSTR, "doi": NSTR}},
        "tumor": STR, "intervention": STR, "comparator": NSTR, "phase": STR, "primary_endpoint": NSTR,
        "reason": STR, "main_result": NSTR, "maturity": {"enum": MATURIDADE}, "related_card_uid": NSTR,
        "policy_basis": {"enum": BASE_POLITICA}, "editorial_limitation": NSTR,
        "comparison_type": {"enum": TIPOS_COMPARACAO},
        "evidence": {"type": "array", "items": T.EVIDENCE_SCHEMA}, "notes_for_human": STR},
    "required": ["schema", "cand_id", "packet_sha256", "action", "study", "tumor", "intervention", "phase", "reason",
                 "maturity", "policy_basis", "comparison_type", "evidence"],
}
NOVOS_VERIFICATION_SCHEMA = {
    "$id": "theratrials-db-novos-verification/1", "type": "object",
    "properties": {
        "schema": {"const": "theratrials-db-novos-verification/1"}, "cand_id": STR, "curator_sha256": STR,
        "evidence_verdict": {"enum": T.VERDICTS}, "action_verdict": {"enum": T.VERDICTS},
        "verdict": {"enum": T.VERDICTS}, "reason": {"type": "string", "minLength": 5}},
    "required": ["schema", "cand_id", "curator_sha256", "evidence_verdict", "action_verdict", "verdict", "reason"],
}
SCHEMAS = {"novos.schema.json": NOVOS_SCHEMA, "novos_verification.schema.json": NOVOS_VERIFICATION_SCHEMA}
ARQUIVOS_VERSAO = ["new_trial_discovery.py", "novos_instrucoes.md", "checks.py", "sources.py",
                   "schemas/novos.schema.json", "schemas/novos_verification.schema.json",
                   "../../../.claude/agents/database-curator.md", "../../../.claude/agents/database-verifier.md"]


def gravar_schemas() -> None:
    for nome, s in SCHEMAS.items():
        (AQUI / "schemas" / nome).write_text(json.dumps(s, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def versao() -> str:
    return f"{NOVOS_BASE}+{DS._sha(b''.join((AQUI / f).read_bytes() for f in ARQUIVOS_VERSAO))[:16]}"


# ── grupos tumorais (referência para cobertura e para filtrar falsos positivos do query.cond) ──────────────────
GRUPOS = {
    "mama": (r"\bbreast\b", ["breast_hrpos", "breast_her2", "breast_tnbc_brca", "breast_radio_dev"]),
    "pulmao_nsclc": (r"non[- ]?small[- ]cell|\bnsclc\b", ["nsclc_alvo", "nsclc_periop", "nsclc_imuno", "lung_radio_dev"]),
    "pulmao_sclc": (r"\bsmall[- ]cell lung|\bsclc\b", ["sclc"]),
    "prostata": (r"prostat", ["prostata_contexto", "lupsma_prostata", "ra223_prostata", "novos_psma", "rt_prostata_local"]),
    "colorretal": (r"colorectal|\bcolon\b|\brect(al|um)\b", ["colorretal"]),
    "gastrico_esofago": (r"gastric|stomach|gastro-?o?esophageal|o?esophag", ["esofago_egj"]),
    "hepatobiliar": (r"hepatocellular|liver cancer|biliary|cholangio|gallbladder", ["hepatobiliar"]),
    "pancreas": (r"pancrea", ["pancreas"]),
    "neuroendocrino_ppgl": (r"neuroendocrine|carcinoid|pheochromocytoma|paraganglioma", ["net_gep", "ppgl"]),
    "renal": (r"renal cell|kidney cancer|\brcc\b", ["rcc_avancado", "rcc_adjuvante_naocc", "lupsma_ccrcc"]),
    "urotelial": (r"urothelial|bladder", ["urotelial_avancado", "urotelial_periop_nmibc"]),
    "ovario": (r"ovarian|fallopian|primary peritoneal", ["ovario"]),
    "endometrio": (r"endometri|uterine", ["endometrio"]),
    "colo_utero": (r"cervical cancer|\bcervix\b|cervical carcinoma", ["cervix"]),
    "cabeca_pescoco": (r"head and neck|oropharyn|nasopharyn|laryn|oral cavity|hnscc", ["hnscc"]),
    "melanoma": (r"melanoma", ["melanoma_adjuvante", "melanoma_avancado"]),
    "tireoide": (r"thyroid", ["tireoide_avancado"]),
    "mieloma": (r"myeloma", ["mieloma"]),
    "lma": (r"acute myeloid", ["lma"]),
    "linfoma_agressivo": (r"large b[- ]cell|\bdlbcl\b|hodgkin", ["linfoma_dlbcl"]),
    "neuroblastoma": (r"neuroblastoma", ["neuroblastoma"]),
    "meningioma": (r"meningioma", ["meningioma"]),
    # sem categoria hoje (lacunas candidatas)
    "glioma": (r"glioma|glioblastoma|astrocytoma|oligodendroglioma", []),
    "sarcoma_gist": (r"sarcoma|gastrointestinal stromal|\bgist\b", []),
    "linfoide_indolente_llc": (r"chronic lymphocytic|\bcll\b|follicular lymphoma|mantle[- ]cell|marginal zone|waldenstr",
                               []),
    "outras_hemato": (r"acute lymphoblastic|chronic myeloid|myelodysplastic|myelofibrosis|polycythemia", []),
    "mesotelioma": (r"mesothelioma", []),
    "pele_nao_melanoma": (r"merkel|cutaneous squamous|basal[- ]cell carcinoma", []),
    "germinativo": (r"germ[- ]cell tumou?r|testicular", []),
    "anal_vulva_penis": (r"\banal (canal|cancer|squamous)|vulvar|penile", []),
}
ONCO = re.compile(r"cancer|carcinoma|tumou?r|neoplas|oncolog|malignan|sarcoma|lymphoma|leuk(a)?emia|myeloma|melanoma|"
                  r"glioma|glioblastoma|blastoma|mesothelioma|metasta|ependymoma|astrocytoma|richter|myelodysplas|"
                  r"myelofibrosis|macroglobulin", re.I)


TUMOR_AGNOSTICO = re.compile(r"tumou?r[- ]agnostic|solid tumou?rs|advanced cancers|ntrk|msi-h|dmmr|tmb-h|"
                             r"any (solid )?tumou?r|histology[- ]independent|basket", re.I)


def grupo_de(texto: str) -> list[str]:
    return [g for g, (rx, _) in GRUPOS.items() if re.search(rx, texto or "", re.I)]


# ── modalidade terapêutica (heurística transparente, só para descrever o universo e priorizar) ──────────────────
MODALIDADES = [
    ("radioligante_radiofarmaco", r"177lu|lu-177|lutet|225ac|actin|223ra|radium|131i|i-131|iodine|mibg|90y|y-90|yttri|"
                                  r"161tb|212pb|psma-617|dotatate|radioligand|radioembol|\brlt\b|prrt"),
    ("imunoterapia", r"pembrolizumab|nivolumab|atezolizumab|durvalumab|ipilimumab|cemiplimab|tislelizumab|toripalimab|"
                     r"camrelizumab|sintilimab|dostarlimab|avelumab|tremelimumab|relatlimab|\bpd-?l?1\b|checkpoint"),
    ("adc", r"deruxtecan|govitecan|vedotin|emtansine|mafodotin|tesirine|\badc\b|conjugate"),
    ("biespecifico_celular", r"teclistamab|elranatamab|talquetamab|glofitamab|epcoritamab|mosunetuzumab|tarlatamab|"
                             r"blinatumomab|bispecific|car[- ]?t|axicabtagene|tisagenlecleucel|lisocabtagene|ciltacabtagene|"
                             r"idecabtagene|-cel\b"),
    ("alvo_molecular", r"[a-z]+tinib\b|[a-z]+rafenib|[a-z]+ciclib|olaparib|niraparib|rucaparib|talazoparib|inavolisib|"
                       r"alpelisib|capivasertib|everolimus|sotorasib|adagrasib|venetoclax|belzutifan|trastuzumab|pertuzumab|"
                       r"bevacizumab|cetuximab|panitumumab|ramucirumab|amivantamab"),
    ("hormonal", r"enzalutamide|abiraterone|apalutamide|darolutamide|letrozole|anastrozole|fulvestrant|tamoxifen|"
                 r"exemestane|camizestrant|elacestrant|imlunestrant|lanreotide|octreotide|\badt\b|androgen deprivation"),
    ("radioterapia", r"radioterap|radiotherap|\bsbrt\b|\bsabr\b|\brt\b|chemoradi|quimiorradi|irradia"),
    ("cirurgia", r"cirurg|surgery|resection|ressec|prostatectom|nephrectom|cystectom"),
]


def modalidades_de(texto: str) -> list[str]:
    return [m for m, rx in MODALIDADES if re.search(rx, texto or "", re.I)] or ["quimioterapia_ou_outra"]


SUFIXO_DROGA = re.compile(r"(mab|nib|ciclib|parib|rafenib|lisib|sertib|tecan|vedotin|tansine|tesirine|lutamide|relix|"
                          r"trozole|strant|citabine|platin|taxel|rubicin|domide|lidomide|rolimus|zomib|lutide|clax|leucel|"
                          r"tamab|limab|cept|tide|terone|gestrol|mycin|ifene|depsin|ostat|vimab|tuzumab|cabtagene)$")
BASE_COMUM = {"cisplatin", "carboplatin", "oxaliplatin", "paclitaxel", "docetaxel", "nabpaclitaxel", "pemetrexed",
              "gemcitabine", "capecitabine", "fluorouracil", "cyclophosphamide", "doxorubicin", "epirubicin",
              "temozolomide", "bevacizumab", "rituximab", "bendamustine", "fludarabine", "cytarabine", "enzalutamide",
              "abiraterone", "letrozole", "anastrozole", "exemestane", "fulvestrant", "tamoxifen", "dexamethasone",
              "prednisone", "nivolumab", "pembrolizumab", "ipilimumab", "atezolizumab", "durvalumab", "trastuzumab",
              "pertuzumab", "cetuximab", "lenalidomide", "bortezomib", "leuprolide", "goserelin", "degarelix",
              "obinutuzumab", "vincristine", "etoposide", "irinotecan"}


def farmacos(texto: str) -> set[str]:
    """Fármacos/códigos para identidade: nomes com sufixo de droga ou códigos com ≥4 dígitos (não ano, não isótopo).
    Palavras como 'analysis', 'clinical', 'quality' — que o CT.gov lista como 'intervenção' — não contam."""
    out = set()
    for w in re.findall(r"[a-z0-9]+", str(texto or "").lower()):
        if re.fullmatch(r"[a-z]{6,}", w) and SUFIXO_DROGA.search(w):
            out.add(w)
        elif re.fullmatch(r"\d{4,}", w) and not re.fullmatch(r"(19|20)\d\d", w):
            out.add(w)
        elif re.fullmatch(r"[a-z]+\d{3,}|\d+[a-z]+\d{3,}", w):
            d = re.search(r"\d{3,}$", w).group(0)
            if len(d) >= 4 and not re.fullmatch(r"(19|20)\d\d", d):
                out.add(d)
    return out


# ── universo editorial (determinístico, só leitura) ─────────────────────────────────────────────────────────────
def _fase(c: dict) -> str:
    f = str(c.get("fase") or "").lower()
    for rx, rot in ((r"diretri|guideline|consenso", "diretriz"), (r"meta-?an", "metanálise"),
                    (r"classifica", "classificação"), (r"fase 3|fase iii|phase 3", "fase 3"),
                    (r"fase 2|fase ii|phase 2", "fase 2"), (r"fase 1|fase i\b|phase 1", "fase 1"),
                    (r"fase 4", "fase 4"), (r"coorte|retrosp|registro|real[- ]world|estudo", "observacional/coorte")):
        if re.search(rx, f):
            return rot
    return "outro"


def _randomizado(c: dict) -> bool:
    return bool(re.search(r"randomi", f"{c.get('fase')} {c.get('desenho')}", re.I))


def universo() -> dict:
    cs = list(DS.cards().values())
    cat = collections.Counter(c.get("category_id") for c in cs)
    grupos = collections.Counter()
    cat_para_grupo = {cid: g for g, (_, cids) in GRUPOS.items() for cid in cids}
    for c in cs:
        grupos[cat_para_grupo.get(c.get("category_id"), "outros: " + str(c.get("category_id")))] += 1
    mod = collections.Counter()
    for c in cs:
        for m in modalidades_de(" ".join(str(c.get(k) or "") for k in ("estudo", "radiofarmaco", "esquema", "comparador",
                                                                       "titulo_full", "category_name"))):
            mod[m] += 1
    fases = collections.Counter(_fase(c) for c in cs)
    rnd = collections.Counter((_fase(c), _randomizado(c)) for c in cs if _fase(c) in ("fase 2", "fase 3"))
    anos = collections.Counter(int(c["ano_pub"]) for c in cs if str(c.get("ano_pub") or "").isdigit())
    faixas = collections.Counter("≤2014" if a <= 2014 else "2015–2019" if a <= 2019 else "2020–2022" if a <= 2022
                                 else "2023–2026" for a in anos.elements())
    status = collections.Counter(re.split(r"[ (]", str(c.get("status") or "?"))[0] for c in cs)
    revistas = collections.Counter(((c.get("citation") or {}).get("journal_abbrev") or (c.get("citation") or {}).get("journal")
                                    or "sem citation estruturada") for c in cs)
    com_nct = sum(1 for c in cs if DS.registros(c))
    com_pmid = sum(1 for c in cs if B.pmid_do_card(c))
    tera = sum(1 for c in cs if "radioligante_radiofarmaco" in modalidades_de(
        " ".join(str(c.get(k) or "") for k in ("estudo", "radiofarmaco", "esquema", "category_name"))))
    lacunas = [g for g, (_, cids) in GRUPOS.items() if not cids]
    finos = sorted(((g, grupos.get(g, 0)) for g, (_, cids) in GRUPOS.items() if cids), key=lambda x: x[1])[:6]
    return {
        "gerado_em": datetime.date.today().isoformat(), "cards": len(cs), "categorias": len(cat),
        "por_grupo_tumoral": dict(grupos.most_common()), "por_modalidade": dict(mod.most_common()),
        "por_fase": dict(fases.most_common()),
        "randomizacao": {f"{f} {'randomizado' if r else 'não randomizado'}": n for (f, r), n in sorted(rnd.items())},
        "por_ano_pub": dict(sorted(faixas.items())), "ano_min_max": [min(anos.elements()), max(anos.elements())],
        "por_status": dict(status.most_common()), "revistas_top": dict(revistas.most_common(12)),
        "com_registro": com_nct, "com_pmid": com_pmid, "com_radioligante": tera,
        "grupos_sem_categoria": lacunas, "grupos_com_menos_cards": finos,
        "nota": "contagens determinísticas; modalidade por palavras-chave (heurística transparente, não classificação clínica)",
    }


# ── índice do Database para deduplicação ───────────────────────────────────────────────────────────────────────
def _acr(t: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", str(t or "").upper())


def _toks(t: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", str(t or "").lower()) if len(w) > 2}


ACR_GENERICOS = {"STUDY", "TRIAL", "PHASE", "FASE", "ESTUDO", "COHORT", "COORTE", "INTERNATIONAL", "RANDOMIZED",
                 "RANDOMISED", "ENSAIO", "ANALISE", "METAANALISE", "REGISTRO", "CLASSIFICACAO",
                 # grupos cooperativos e famílias de ensaio sem número não identificam UM estudo
                 "EORTC", "SWOG", "ECOG", "ECOGACRIN", "RTOG", "NRG", "JCOG", "NCIC", "CCTG", "ETOP", "GETUG", "UNICANCER",
                 "ALLIANCE", "CALGB", "NSABP", "ANZUP", "TROG", "GBG", "AGO", "ENGOT", "GOG", "CHECKMATE", "KEYNOTE",
                 "DESTINY", "IMPOWER", "IMVIGOR", "JAVELIN", "TROPION", "MONARCH", "PALOMA", "MONALEESA", "CAPITELLO",
                 "EMBER", "POSEIDON", "PACIFIC", "AEGEAN", "TOPAZ", "HIMALAYA", "LEAP", "CLEAR", "STAMPEDE"}


def indice() -> dict:
    cs = DS.cards()
    idx = {"nct": {}, "pmid": {}, "doi": {}, "acr": {}, "titulos": [], "por_categoria": collections.defaultdict(list)}
    for uid, c in cs.items():
        for r in DS.registros(c):
            idx["nct"].setdefault(r.upper(), uid)
        cit = c.get("citation") or {}
        for p in (B.pmid_do_card(c), cit.get("pmid")):
            if p:
                idx["pmid"].setdefault(str(p), uid)
        if cit.get("doi"):
            idx["doi"].setdefault(str(cit["doi"]).lower(), uid)
        for a in (c.get("acron"), re.split(r"[\s(]", str(c.get("estudo") or "").strip())[0]):
            k = _acr(a)
            if len(k) >= 4 and k not in ACR_GENERICOS:
                idx["acr"].setdefault(k, uid)
        idx["titulos"].append((uid, _toks(f"{c.get('titulo_full') or ''} {c.get('estudo') or ''}")))
        idx.setdefault("grupos", {})[uid] = {g for g, (_, cids) in GRUPOS.items() if c.get("category_id") in cids}
        idx.setdefault("tem_registro", {})[uid] = bool(DS.registros(c))
        idx["por_categoria"][c.get("category_id")].append(uid)
    for s in DS.secundarios():
        if s.get("pmid"):
            idx["pmid"].setdefault(str(s["pmid"]), s.get("parentUid") or f"secundario:{s['id']}")
        if s.get("doi"):
            idx["doi"].setdefault(str(s["doi"]).lower(), s.get("parentUid") or f"secundario:{s['id']}")
    return idx


def deduplicar(cand: dict, idx: dict) -> dict:
    """Classe determinística + motivo + card(s) mais próximos. Na dúvida, nunca NEW_STUDY_CANDIDATE."""
    if cand.get("nct") and cand["nct"].upper() in idx["nct"]:
        return {"classe": "ALREADY_EXISTS", "motivo": f"NCT {cand['nct']} já é registro do card", "uid": idx["nct"][cand["nct"].upper()]}
    for p in cand.get("pmids") or []:
        if str(p) in idx["pmid"]:
            return {"classe": "ALREADY_EXISTS", "motivo": f"PMID {p} já está no Database", "uid": idx["pmid"][str(p)]}
    for d in cand.get("dois") or []:
        if str(d).lower() in idx["doi"]:
            return {"classe": "ALREADY_EXISTS", "motivo": f"DOI {d} já está no Database", "uid": idx["doi"][str(d).lower()]}
    acr = _acr(cand.get("acronym"))
    grupos_c = set(grupo_de(" ".join([cand.get("title") or "", cand.get("official_title") or "",
                                      " ".join(cand.get("conditions") or [])])))
    mesmo_grupo = lambda uid: not grupos_c or not idx.get("grupos", {}).get(uid) or bool(grupos_c & idx["grupos"][uid])  # noqa: E731
    dicas = []
    if acr and len(acr) >= 4 and acr not in ACR_GENERICOS:
        if acr in idx["acr"]:
            uid = idx["acr"][acr]
            if mesmo_grupo(uid):
                return {"classe": "POSSIBLE_DUPLICATE", "motivo": f"acrônimo {cand['acronym']} igual ao de um card do mesmo "
                                                                  "grupo tumoral, com outro registro", "uid": uid}
            dicas.append(f"acrônimo homônimo de {uid} (outro tumor): ensaio diferente")
        for k, uid in idx["acr"].items():                      # família de acrônimo: extensão ou ensaio irmão?
            if len(k) >= 5 and (acr.startswith(k) or k.startswith(acr) or k in acr) and acr != k and mesmo_grupo(uid):
                if re.search(r"extension|long[- ]term follow|rollover|\blte\b|sub-?study|continuation|\bchina\b|chinese|"
                             r"japan|asian|korea|\bindia|regional", f"{cand.get('title') or ''} {cand.get('official_title') or ''} "
                             f"{cand.get('acronym') or ''}", re.I):
                    return {"classe": "RELATED_TO_EXISTING", "motivo": f"extensão/coorte regional de {k}", "uid": uid}
                dicas.append(f"mesma família de acrônimo que {uid} ({k}): ensaio irmão; o curator decide")
    tt = _toks(f"{cand.get('title') or ''} {cand.get('official_title') or ''}")
    melhor = (0.0, None)
    for uid, toks in idx["titulos"]:
        if toks and tt:
            j = len(tt & toks) / len(tt | toks)
            if j > melhor[0]:
                melhor = (j, uid)
    if melhor[0] >= 0.5:
        if not (cand.get("nct") and idx.get("tem_registro", {}).get(melhor[1])):
            return {"classe": "POSSIBLE_DUPLICATE", "motivo": f"título muito parecido com o de um card (Jaccard "
                                                              f"{melhor[0]:.2f}) sem registro para desempatar", "uid": melhor[1]}
        dicas.append(f"título parecido com {melhor[1]} (Jaccard {melhor[0]:.2f}), mas com outro registro")
    return {"classe": "NEW_STUDY_CANDIDATE", "motivo": "sem correspondência por registro, PMID, DOI, acrônimo ou título",
            "uid": None, "titulo_mais_proximo": {"uid": melhor[1], "jaccard": round(melhor[0], 2)}, "dicas": dicas}


# ── coleta (CT.gov v2 + PubMed; somente leitura, com cache) ─────────────────────────────────────────────────────
CONSULTAS = [
    {"key": "gastrico_esofago", "cond": "gastric OR gastroesophageal junction adenocarcinoma", "pm": "gastric cancer"},
    {"key": "glioma", "cond": "glioma OR glioblastoma", "pm": "glioblastoma OR glioma"},
    {"key": "sarcoma_gist", "cond": "soft tissue sarcoma OR gastrointestinal stromal tumor", "pm": "sarcoma"},
    {"key": "linfoide_indolente_llc", "cond": "chronic lymphocytic leukemia OR follicular lymphoma OR mantle cell lymphoma",
     "pm": "chronic lymphocytic leukemia OR follicular lymphoma OR mantle cell lymphoma"},
    {"key": "mesotelioma", "cond": "mesothelioma", "pm": "mesothelioma"},
    {"key": "mama", "cond": "breast cancer", "pm": "breast cancer"},
    {"key": "pulmao_nsclc", "cond": "non-small cell lung cancer", "pm": "non-small cell lung cancer"},
    {"key": "prostata", "cond": "prostate cancer", "pm": "prostate cancer"},
    {"key": "urotelial", "cond": "urothelial carcinoma OR bladder cancer", "pm": "urothelial carcinoma OR bladder cancer"},
    {"key": "radioligante", "intr": "lutetium OR actinium OR radioligand OR radium-223 OR 177Lu",
     "pm": "radioligand therapy OR lutetium-177 OR actinium-225"},
]
FILTRO_CTGOV = ("AREA[StudyType]INTERVENTIONAL AND (AREA[Phase]PHASE3 OR (AREA[Phase]PHASE2 AND "
                "AREA[DesignAllocation]RANDOMIZED)) AND AREA[PrimaryCompletionDate]RANGE[2021-01-01,MAX]")
STATUS_CTGOV = "COMPLETED|ACTIVE_NOT_RECRUITING"


def _ctgov_busca(q: dict, rede: bool, n: int = 40) -> list[dict]:
    params = {"filter.advanced": FILTRO_CTGOV, "filter.overallStatus": STATUS_CTGOV, "pageSize": str(n),
              "sort": "LastUpdatePostDate:desc", "format": "json"}
    if q.get("cond"):
        params["query.cond"] = q["cond"]
    if q.get("intr"):
        params["query.intr"] = q["intr"]
    url = S.CTGOV.rstrip("/") + "?" + urllib.parse.urlencode(params)
    raw, _ = S._get(url, rede, S.CACHE / "novos_ctgov" / f"{q['key']}.json")
    return (json.loads(raw).get("studies") or []) if raw else []


def _pubmed_busca(q: dict, rede: bool, n: int = 25) -> list[str]:
    termo = (f"({q['pm']})[tiab] AND (randomized controlled trial[pt] OR clinical trial, phase iii[pt]) AND "
             f"(phase 3[tiab] OR phase III[tiab] OR phase 2[tiab] OR phase II[tiab]) AND (\"2024/01/01\"[dp] : \"3000\"[dp])")
    url = f"{S.EUTILS}esearch.fcgi?" + urllib.parse.urlencode({"db": "pubmed", "retmode": "json", "retmax": n,
                                                             "sort": "relevance", "term": termo})
    raw, _ = S._get(url, rede, S.CACHE / "novos_esearch" / f"{q['key']}.json")
    return json.loads(raw)["esearchresult"]["idlist"] if raw else []


def _ct_resumo(st: dict) -> dict:
    p = st.get("protocolSection") or {}
    ident, stat, des = p.get("identificationModule") or {}, p.get("statusModule") or {}, p.get("designModule") or {}
    refs = (p.get("referencesModule") or {}).get("references") or []
    return {
        "nct": ident.get("nctId"), "title": ident.get("briefTitle"), "official_title": ident.get("officialTitle"),
        "acronym": ident.get("acronym"), "phases": des.get("phases") or [],
        "allocation": (des.get("designInfo") or {}).get("allocation"),
        "purpose": (des.get("designInfo") or {}).get("primaryPurpose"), "status": stat.get("overallStatus"),
        "primary_completion": (stat.get("primaryCompletionDateStruct") or {}).get("date"),
        "last_update": (stat.get("lastUpdatePostDateStruct") or {}).get("date"),
        "conditions": (p.get("conditionsModule") or {}).get("conditions") or [],
        "interventions": [i.get("name") for i in (p.get("armsInterventionsModule") or {}).get("interventions") or []],
        "sponsor": ((p.get("sponsorCollaboratorsModule") or {}).get("leadSponsor") or {}).get("name"),
        "enrollment": (des.get("enrollmentInfo") or {}).get("count"),
        "has_results": bool(st.get("hasResults")),
        "ref_pmids": [r["pmid"] for r in refs if r.get("pmid") and r.get("type") in ("RESULT", "DERIVED")],
    }


def coletar(rede: bool = False) -> dict:
    """Candidatos brutos → um candidato por ensaio (NCT) ou por publicação sem registro. Grava state/novos/coleta.json."""
    brutos, cands = [], {}
    for q in CONSULTAS:
        for st in _ctgov_busca(q, rede):
            r = _ct_resumo(st)
            brutos.append({"via": f"ctgov:{q['key']}", "id": r["nct"]})
            c = cands.setdefault(r["nct"], {"cand_id": r["nct"], "nct": r["nct"], "found_by": [], "pmids": [], "dois": []})
            c.update({k: v for k, v in r.items() if k != "ref_pmids"})
            c["found_by"].append(f"ctgov:{q['key']}")
            c["pmids"] = sorted(set(c["pmids"]) | set(r["ref_pmids"]))
        for pmid in _pubmed_busca(q, rede):
            brutos.append({"via": f"pubmed:{q['key']}", "id": f"pmid:{pmid}"})
            e = S.pubmed_efetch(pmid, rede)
            if not e:
                continue
            ncts = [n for n in e.get("databank_nct") or [] if n.startswith("NCT")]
            chave = ncts[0] if ncts else f"pmid{pmid}"
            c = cands.setdefault(chave, {"cand_id": chave, "nct": ncts[0] if ncts else None, "found_by": [], "pmids": [],
                                         "dois": []})
            c["found_by"].append(f"pubmed:{q['key']}")
            c["pmids"] = sorted(set(c["pmids"]) | {pmid})
            if e.get("doi"):
                c["dois"] = sorted(set(c["dois"]) | {e["doi"].lower()})
            c.setdefault("title", e["title"])
            c.setdefault("pub_pubtypes", {})[pmid] = e.get("pubtypes")
    # registros das publicações que só vieram pelo PubMed + publicações dos ensaios que só vieram pelo CT.gov
    for c in cands.values():
        if c.get("nct") and "status" not in c:
            rec = S.ctgov(c["nct"], rede)
            if rec:
                r = _ct_resumo(rec)
                c.update({k: v for k, v in r.items() if k not in ("ref_pmids",)})
                c["pmids"] = sorted(set(c["pmids"]) | set(r["ref_pmids"]))
        if c.get("nct"):
            ids, _ = S.pubmed_por_nct(c["nct"], rede)
            c["pmids"] = sorted(set(c["pmids"]) | set(ids))
        c["found_by"] = sorted(set(c["found_by"]))
    ligados = ligar_publicacoes(cands)
    out = {"gerado_em": datetime.date.today().isoformat(), "versao": versao(), "consultas": CONSULTAS,
           "publicacoes_ligadas_a_ensaio": ligados,
           "filtro_ctgov": FILTRO_CTGOV, "status_ctgov": STATUS_CTGOV, "brutos": len(brutos),
           "candidatos": sorted(cands.values(), key=lambda x: x["cand_id"])}
    DIR.mkdir(parents=True, exist_ok=True)
    (DIR / "coleta.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return out


def ligar_publicacoes(cands: dict) -> list[dict]:
    """Publicação do PubMed sem NCT (DataBank vazio) cujo TÍTULO cita o acrônimo de um ensaio coletado do CT.gov:
    liga ao ensaio em vez de criar outro candidato. Só o acrônimo explícito: a semelhança por tokens/códigos ligava
    publicações a ensaios errados (testado no piloto 1). Publicação do mesmo ensaio sem o acrônimo no título continua
    como candidato à parte — limitação conhecida (ex.: ARROW)."""
    ligados = []
    ensaios = [c for c in cands.values() if c.get("nct") and len(_acr(c.get("acronym"))) >= 4
               and _acr(c.get("acronym")) not in ACR_GENERICOS]
    for chave in [k for k, c in cands.items() if not c.get("nct")]:
        pub = cands[chave]
        alvo = [e for e in ensaios if re.search(rf"(?<![A-Za-z0-9]){re.escape(e['acronym'])}(?![A-Za-z0-9])",
                                                pub.get("title") or "", re.I)]
        if len(alvo) == 1:                                   # ambíguo (2+ ensaios) não liga
            e = alvo[0]
            e["pmids"] = sorted(set(e["pmids"]) | set(pub["pmids"]))
            e["dois"] = sorted(set(e.get("dois") or []) | set(pub.get("dois") or []))
            e["found_by"] = sorted(set(e["found_by"]) | set(pub["found_by"]))
            ligados.append({"publicacao": chave, "ensaio": e["nct"], "titulo": pub.get("title")})
            del cands[chave]
    return ligados


def _texto_pub(pmid: str, rede: bool = False) -> str:
    try:
        e = S.pubmed_efetch(pmid, rede)
    except S.SemCache:
        return ""
    return " ".join([e.get("title") or ""] + [t for _, t in e.get("abstract") or []]) if e else ""


def _fase_no_texto(t: str) -> set[str]:
    f = set()
    if re.search(r"phase (3|iii)\b", t, re.I):
        f.add("PHASE3")
    if re.search(r"phase (2|ii)\b", t, re.I):
        f.add("PHASE2")
    return f


def identidade(pub: dict, ensaios: list[dict], cards: dict, rede: bool = False) -> dict | None:
    """Publicação SEM registro: a qual estudo pertence? Ordem: (1) prova contra os candidatos de registro (PMID nas
    referências do registro; acrônimo no título) → vínculo; (2) acrônimo de um card no título → RELATED_TO_EXISTING, no
    resumo → POSSIBLE_DUPLICATE; (3) compatibilidade forte sem prova com um candidato de registro (mesma doença e ≥2
    fármacos em comum com ≥1 distintivo, ou código de droga em comum + n/fase) → POSSIBLE_DUPLICATE.
    Nunca deixa a mesma pesquisa virar dois NEW_CARD só porque a publicação não informa o NCT (regressão: ARROW)."""
    pmids = set(pub.get("pmids") or [])
    texto = _texto_pub(sorted(pmids)[0], rede) if pmids else ""
    titulo = pub.get("title") or ""
    grupos_p = set(grupo_de(f"{titulo} {texto}"))
    citado = lambda acr, onde: len(_acr(acr)) >= 4 and _acr(acr) not in ACR_GENERICOS and re.search(  # noqa: E731
        rf"(?<![A-Za-z0-9]){re.escape(acr)}(?![A-Za-z0-9])", onde, re.I)
    for e in ensaios:                                                    # (1) provas
        if pmids & set(e.get("pmids") or []):
            return {"classe": "ALREADY_LINKED", "alvo": e["nct"], "motivo": "PMID nas referências do registro"}
        if citado(e.get("acronym") or "", titulo):
            return {"classe": "ALREADY_LINKED", "alvo": e["nct"], "motivo": f"acrônimo {e['acronym']} no título"}
    for uid, c in cards.items():                                          # (2) ensaios que já têm card
        acr = re.split(r"[\s(]", str(c.get("acron") or c.get("estudo") or "").strip())[0]
        gc = {g for g, (_, cids) in GRUPOS.items() if c.get("category_id") in cids}
        if grupos_p and gc and not (grupos_p & gc):                      # homônimo de outro tumor (ex.: AcTION × ACTION)
            continue
        if citado(acr, titulo):
            return {"classe": "RELATED_TO_EXISTING", "alvo": uid, "motivo": f"publicação do ensaio {acr}, que já tem card "
                    "(atualização/secundária: domínio do discovery)"}
        if len(_acr(acr)) >= 5 and citado(acr, texto):
            return {"classe": "POSSIBLE_DUPLICATE", "alvo": uid, "motivo": f"o resumo cita {acr}, que já tem card"}
    for e in ensaios:                                                    # acrônimo do ensaio só no RESUMO
        ge = set(grupo_de(" ".join([e.get("title") or "", e.get("official_title") or "", " ".join(e.get("conditions") or [])])))
        if len(_acr(e.get("acronym"))) >= 4 and citado(e.get("acronym") or "", texto) and \
                (not grupos_p or not ge or grupos_p & ge):
            return {"classe": "POSSIBLE_DUPLICATE", "alvo": e["nct"], "motivo": f"o resumo cita {e['acronym']} "
                    f"({e['nct']}), identidade não comprovada"}
    fp, fases_p = farmacos(f"{titulo} {texto}"), _fase_no_texto(f"{titulo} {texto}")
    melhor = None
    for e in ensaios:                                                    # (3) compatibilidade sem prova
        ge = set(grupo_de(" ".join([e.get("title") or "", e.get("official_title") or "", " ".join(e.get("conditions") or [])])))
        if not grupos_p or not ge or not (grupos_p & ge):
            continue
        comuns = fp & farmacos(" ".join([e.get("title") or "", " ".join(e.get("interventions") or [])]))
        codigos = {w for w in comuns if w.isdigit()}
        distintivos = comuns - BASE_COMUM
        n_ok = bool(e.get("enrollment")) and re.search(rf"\b{e['enrollment']}\b", texto) is not None
        fase_ok = bool(fases_p & set(e.get("phases") or []))
        if (len(comuns) >= 2 and distintivos) or (codigos and (n_ok or fase_ok)):
            sinais = {"farmacos": sorted(comuns), "n_registro_no_resumo": n_ok, "fase": fase_ok}
            if not melhor or len(comuns) > len(melhor[1]["farmacos"]):
                melhor = (e["nct"], sinais)
    if melhor:
        return {"classe": "POSSIBLE_DUPLICATE", "alvo": melhor[0], "motivo": f"compatível com o ensaio {melhor[0]} "
                f"({melhor[1]}), identidade não comprovada"}
    return None


# ── metadados das publicações ligadas e filtros editoriais determinísticos ──────────────────────────────────────
def publicacoes(c: dict, rede: bool) -> list[dict]:
    pubs = []
    for p in c.get("pmids") or []:
        e = S.pubmed_efetch(p, rede)
        if e:
            pubs.append({"pmid": p, "title": e["title"], "doi": e.get("doi"), "pubtypes": e.get("pubtypes") or [],
                         "abstract": bool(e.get("abstract")), "databank_nct": e.get("databank_nct") or []})
    return pubs


def principal(c: dict, pubs: list[dict]) -> dict | None:
    """Publicação primária provável: ensaio clínico/RCT, sem tipo que o próprio discovery descarta, com resumo."""
    boas = []
    for p in pubs:
        acao, _, _ = DS.pre_acao({"pubtype": p["pubtypes"], "title": p["title"]})
        tipos = {t.lower() for t in p["pubtypes"]}
        ensaio = {"randomized controlled trial", "clinical trial, phase iii", "clinical trial, phase ii", "clinical trial"} & tipos
        resultado = re.search(r"randomi[sz]ed|phase (2|3|ii|iii)\b|\btrial\b", p["title"], re.I) and not \
            ({"review", "systematic review", "meta-analysis", "editorial", "comment", "letter", "clinical trial protocol"} & tipos)
        if acao is None and p["abstract"] and (ensaio or resultado):
            boas.append((0 if ensaio else 1, int(p["pmid"]), p))
    return min(boas, key=lambda x: (x[0], x[1]))[2] if boas else None


def filtro_editorial(c: dict, pubs: list[dict], prim: dict | None) -> tuple[str | None, str]:
    """(ação, motivo) quando o próprio registro/publicação já decide sem LLM; (None, '') = segue para o curator."""
    texto = " ".join([c.get("title") or "", c.get("official_title") or "", " ".join(c.get("conditions") or [])])
    if not ONCO.search(texto):
        return "NO_ACTION", "fora do escopo oncológico (condições/título sem neoplasia)"
    fases = set(c.get("phases") or [])
    excecao = "radioligante_radiofarmaco" in modalidades_de(" ".join(c.get("interventions") or [])) or \
        bool(TUMOR_AGNOSTICO.search(texto))
    if c.get("nct") and fases and not ({"PHASE3", "PHASE2"} & fases) and not excecao:
        return "NO_ACTION", "só fase 1, sem exceção detectável (radioligante/tumor-agnóstico): política"
    if c.get("nct") and "PHASE3" not in fases and c.get("allocation") != "RANDOMIZED" and not excecao:
        return "NO_ACTION", "fase 2 de braço único sem exceção detectável (radioligante/tumor-agnóstico): política"
    if c.get("purpose") and c["purpose"] not in ("TREATMENT", None):
        return "NO_ACTION", f"propósito {c['purpose']}: não terapêutico"
    if not c.get("nct") and prim is None:
        return "NO_ACTION", "publicação sem registro e sem tipo de ensaio primário"
    if prim is None and c.get("status") == "ACTIVE_NOT_RECRUITING" and not c.get("has_results"):
        return "WATCH", "ensaio sem publicação nem resultados registrados: acompanhar"
    if prim is None and not c.get("has_results"):
        return "WATCH", "concluído no registro, sem publicação primária localizada nem resultados no CT.gov"
    return None, ""


# ── pacote, tarefa e entrada do verifier ────────────────────────────────────────────────────────────────────────
MODULOS_CTGOV = ("identificationModule", "statusModule", "sponsorCollaboratorsModule", "conditionsModule", "designModule",
                 "armsInterventionsModule", "outcomesModule", "referencesModule")


def preparar(c: dict, rede: bool = False) -> dict:
    pasta = DIR / c["cand_id"]
    fdir = pasta / "fontes"
    fdir.mkdir(parents=True, exist_ok=True)
    for f in fdir.glob("*.txt"):
        f.unlink()
    fontes = []

    def fonte(sid, stype, nivel, pars, papel):
        if pars:
            p = S.gravar_fonte(fdir, sid, pars)
            fontes.append({"source_id": sid, "source_type": stype, "text_level": nivel, "path": f"fontes/{p.name}",
                           "paragraphs": len(pars), "role": papel})
    if c.get("nct"):
        rec = S.ctgov(c["nct"], rede)
        if rec:
            filtrado = {"protocolSection": {k: v for k, v in (rec.get("protocolSection") or {}).items() if k in MODULOS_CTGOV},
                        "hasResults": rec.get("hasResults")}
            fonte(f"nct:{c['nct']}:registry", "ctgov_record", "registry", S.ctgov_paragrafos(filtrado), "registry")
    pubs = publicacoes(c, rede)
    prim = principal(c, pubs)
    escolhidas = ([prim] if prim else []) + sorted([p for p in pubs if p is not prim and p["abstract"]],
                                                   key=lambda p: -int(p["pmid"]))[:2]
    for p in escolhidas:
        e = S.pubmed_efetch(p["pmid"], rede)
        fonte(f"pmid:{p['pmid']}:abstract", "pubmed_abstract", "abstract",
              [("Title", e["title"])] + [(f"Abstract > {s}", t) for s, t in e["abstract"]],
              "primary_candidate" if p is prim else "other_publication")
    cs = DS.cards()
    grupos = grupo_de(" ".join([c.get("title") or "", " ".join(c.get("conditions") or [])]))
    contexto, cobertura = [], {}
    for g in grupos:
        por_cat = [[(u, x) for u, x in cs.items() if x.get("category_id") == cid] for cid in GRUPOS[g][1]]
        cobertura[g] = sum(len(l) for l in por_cat)
        alternado = [p for fila in __import__("itertools").zip_longest(*por_cat) for p in fila if p]   # todas as categorias
        contexto += [{"grupo": g, "uid": u, "estudo": x.get("estudo"), "categoria": x.get("category_id"),
                      "indicacao": str(x.get("indicacao") or "")[:160],
                      "intervencao": str(x.get("radiofarmaco") if str(x.get("radiofarmaco") or "—") != "—"
                                         else x.get("esquema") or "")[:120], "fase": x.get("fase")} for u, x in alternado[:8]]
    pacote = {
        "schema": "theratrials-db-novos-packet/1", "cand_id": c["cand_id"], "novos_version": versao(),
        "candidate": {k: c.get(k) for k in ("nct", "title", "official_title", "acronym", "phases", "allocation", "status",
                                             "primary_completion", "conditions", "interventions", "sponsor", "has_results")},
        "publications": [{k: p[k] for k in ("pmid", "title", "doi", "pubtypes")} for p in pubs],
        "primary_publication_guess": prim and prim["pmid"],
        "dedup": c.get("dedup"), "tumor_groups": grupos,
        "database_context": contexto, "database_coverage_by_group": cobertura,
        "database_context_note": ("cards existentes no mesmo grupo tumoral (no máximo 8 por grupo): contexto de "
                                  "COBERTURA, nunca evidência; a contagem total por grupo está em database_coverage_by_group"),
        "sources": fontes,
    }
    pacote["packet_sha256"] = DS._sha(pacote)
    (pasta / "packet.json").write_text(json.dumps(pacote, ensure_ascii=False, indent=1), encoding="utf-8")
    return pacote


def tarefa(cid: str) -> str:
    p = json.loads((DIR / cid / "packet.json").read_text())
    return (f"MODO NOVOS ENSAIOS. Instruções: {INSTRUCOES}\nPacote: {DIR / cid / 'packet.json'} · fontes em "
            f"{DIR / cid / 'fontes'}\nSchema de saída: {AQUI / 'schemas' / 'novos.schema.json'}\n"
            f"cand_id: {cid} · packet_sha256: {p['packet_sha256']}\n")


def entrada(cid: str) -> pathlib.Path:
    cur = json.loads((DIR / cid / "curator.json").read_text())
    visivel = ["action", "study", "nct", "main_publication", "tumor", "intervention", "comparator", "phase",
               "primary_endpoint", "main_result", "maturity", "related_card_uid", "policy_basis",
               "editorial_limitation", "comparison_type", "evidence"]
    ent = {"cand_id": cid, "packet": str(DIR / cid / "packet.json"), "fontes": str(DIR / cid / "fontes"),
           "curator_sha256": cur["_sha256"], "proposal": {k: cur.get(k) for k in visivel}}
    alvo = DIR / cid / "verifier_input.json"
    alvo.write_text(json.dumps(ent, ensure_ascii=False, indent=1), encoding="utf-8")
    return alvo


def tarefa_verifier(cid: str) -> str:
    alvo = entrada(cid)
    return (f"MODO NOVOS ENSAIOS (verificação). Instruções: {INSTRUCOES}\nEntrada: {alvo}\n"
            f"Schema de saída: {AQUI / 'schemas' / 'novos_verification.schema.json'}\n"
            f"cand_id: {cid} · curator_sha256: {json.loads(alvo.read_text())['curator_sha256']}\n")


# ── checagens determinísticas ───────────────────────────────────────────────────────────────────────────────────
def conferir(cid: str, cur: dict) -> dict:
    p = json.loads((DIR / cid / "packet.json").read_text())
    pasta = DIR / cid
    fontes = {f["source_id"]: f for f in p["sources"]}
    ach = []
    add = lambda code, v, d: ach.append({"code": code, "verdict": v, "detail": d})  # noqa: E731
    if cur.get("action") not in ACOES:
        add("ACTION_ENUM", "FAIL", f"ação inválida {cur.get('action')!r}")
    if cur.get("maturity") not in MATURIDADE:
        add("MATURITY_ENUM", "FAIL", f"maturidade inválida {cur.get('maturity')!r}")
    if cur.get("nct") and p["candidate"].get("nct") and cur["nct"].upper() != p["candidate"]["nct"].upper():
        add("NCT_MISMATCH", "FAIL", f"NCT {cur['nct']} ≠ registro do candidato {p['candidate']['nct']}")
    mp = (cur.get("main_publication") or {}).get("pmid")
    if mp and str(mp) not in {str(x["pmid"]) for x in p["publications"]}:
        add("PUBLICATION_UNKNOWN", "FAIL", f"publicação principal {mp} fora do pacote")
    rel = cur.get("related_card_uid")
    if rel and rel not in DS.cards():
        add("RELATED_CARD_UNKNOWN", "FAIL", f"card relacionado {rel!r} não existe")
    if cur.get("action") == "RELATED_TO_EXISTING" and not rel:
        add("RELATED_WITHOUT_CARD", "UNSUPPORTED", "RELATED_TO_EXISTING sem o uid do card relacionado")
    if cur.get("action") == "NEW_CARD":
        if (p.get("dedup") or {}).get("classe") != "NEW_STUDY_CANDIDATE":
            add("NEW_CARD_NOT_NEW", "FAIL", "NEW_CARD em candidato que a deduplicação não classificou como novo")
        if cur.get("maturity") == "ongoing_no_results" and cur.get("main_result"):
            add("RESULT_WITHOUT_DATA", "FAIL", "ensaio sem resultados não pode trazer resultado principal")
        if cur.get("maturity") in ("published_primary", "registry_results_only") and not cur.get("main_result"):
            add("RESULT_MISSING", "UNSUPPORTED", "NEW_CARD com dados disponíveis sem o resultado principal")
    evid = []
    for e in cur.get("evidence") or []:
        sn = str(e.get("snippet") or "")
        limpo = re.sub(r"^\s*¶\d{4}\s+", "", sn)
        if limpo != sn:
            add("SNIPPET_PREFIX_NORMALIZED", "PASS", "prefixo ¶NNNN removido do trecho (pertence ao locator)")
        evid.append({**e, "snippet": limpo})
    cand = p["candidate"]
    fases = set(cand.get("phases") or [])
    base = cur.get("policy_basis")
    if cur.get("action") == "NEW_CARD":
        if base in (None, "nao_se_aplica"):
            add("POLICY_BASIS_MISSING", "UNSUPPORTED", "NEW_CARD sem o critério da política editorial")
        if cand.get("nct") and fases and "PHASE3" not in fases and cand.get("allocation") != "RANDOMIZED" \
                and base not in EXCECOES_BRACO_UNICO and base != "excecao_fase1":
            add("POLICY_SINGLE_ARM", "UNSUPPORTED", "fase 2 de braço único só entra por exceção da política")
        if cand.get("nct") and fases and not ({"PHASE2", "PHASE3"} & fases) and base != "excecao_fase1":
            add("POLICY_PHASE1", "UNSUPPORTED", "fase 1 só entra excepcionalmente (excecao_fase1)")
        if cur.get("maturity") == "congress_provisional" and "PHASE3" not in fases and cand.get("nct"):
            add("POLICY_CONGRESS", "UNSUPPORTED", "só fase 3 entra com maturidade de congresso (provisória)")
        if cur.get("comparison_type") in ("randomizado_vs_nao_padrao", "randomizado_nao_comparativo") \
                and base not in EXCECOES_BRACO_UNICO:
            add("POLICY_NON_COMPARATIVE", "UNSUPPORTED", "comparador não padrão/análise não comparativa: HUMAN_REVIEW "
                                                          "obrigatório (fora das exceções de braço único)")
        fase3 = "PHASE3" in fases or bool(re.search(r"fase (3|iii)\b|phase (3|iii)\b", str(cur.get("phase") or ""), re.I))
        if base == "cirurgia_randomizada_relevante" and not fase3:
            add("POLICY_SURGERY_PHASE2", "UNSUPPORTED", "técnica cirúrgica: só fase 3 vira NEW_CARD; fase 2 → HUMAN_REVIEW")
    if cur.get("comparison_type") not in TIPOS_COMPARACAO:
        add("COMPARISON_TYPE_ENUM", "FAIL", f"comparison_type inválido {cur.get('comparison_type')!r}")
    item = {"evidence": evid, "change_kind": "replace", "value_origin": "reported",
            "proposed_value": cur.get("main_result") or ""}
    for a in K.conferir_item(item, fontes, pasta):
        if a["verdict"] != "PASS":
            ach.append(a)
    if not [a for a in ach if a["verdict"] != "PASS"]:
        add("DETERMINISTIC_OK", "PASS", "trechos literais, localizadores e números conferem")
    return {"verdict": K.pior([a["verdict"] for a in ach]), "achados": ach}


def _json(txt: str) -> dict:
    m = re.search(r"\{.*\}", txt.strip(), re.S)
    return json.loads(m.group(0) if m else txt)


def ingerir(papel: str, cid: str, arquivo: str) -> dict:
    d = _json(pathlib.Path(arquivo).read_text(encoding="utf-8"))
    sha = hashlib.sha256(json.dumps(d, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    p = json.loads((DIR / cid / "packet.json").read_text())
    if papel == "curator":
        erros = [] if d.get("schema") == NOVOS_SCHEMA["$id"] else [f"schema {d.get('schema')!r}"]
        if d.get("packet_sha256") != p["packet_sha256"]:
            erros.append("packet_sha256 não confere")
        d["_sha256"], d["_erros"] = sha, erros
        d["_deterministico"] = conferir(cid, d)
        (DIR / cid / "curator.json").write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    else:
        cur = json.loads((DIR / cid / "curator.json").read_text())
        erros = [] if d.get("curator_sha256") == cur["_sha256"] else ["curator_sha256 não confere"]
        if any(k in d for k in ("main_result", "proposed", "corrected", "card_text")):
            erros.append("verifier reescreveu (proibido)")
        d["_sha256"], d["_erros"] = sha, erros
        (DIR / cid / "verifier.json").write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    return d


# ── triagem (determinística) e seleção do piloto ────────────────────────────────────────────────────────────────
def triagem(rede: bool = False) -> dict:
    col = json.loads((DIR / "coleta.json").read_text())
    idx = indice()
    cards = DS.cards()
    ensaios = [c for c in col["candidatos"] if c.get("nct")]
    linhas = []
    for c in col["candidatos"]:
        c = dict(c)
        c["dedup"] = deduplicar(c, idx)
        c["tumor_groups"] = grupo_de(" ".join([c.get("title") or "", " ".join(c.get("conditions") or [])]))
        acao, motivo = None, ""
        if c["dedup"]["classe"] == "ALREADY_EXISTS":
            acao, motivo = "NO_ACTION", c["dedup"]["motivo"]
        elif c["dedup"]["classe"] == "POSSIBLE_DUPLICATE":
            acao, motivo = "HUMAN_REVIEW", c["dedup"]["motivo"]
        elif c["dedup"]["classe"] == "RELATED_TO_EXISTING":
            acao, motivo = "RELATED_TO_EXISTING", c["dedup"]["motivo"]
        if c["dedup"]["classe"] == "NEW_STUDY_CANDIDATE" and not c.get("nct"):
            ident = identidade(c, ensaios, cards, rede)
            if ident:
                c["identidade"] = ident
                if ident["classe"] == "ALREADY_LINKED":
                    acao, motivo = "NO_ACTION", f"mesma pesquisa do candidato {ident['alvo']} ({ident['motivo']})"
                elif ident["classe"] == "RELATED_TO_EXISTING":
                    acao, motivo = "RELATED_TO_EXISTING", ident["motivo"]
                    c["dedup"] = {**c["dedup"], "classe": "RELATED_TO_EXISTING", "uid": ident["alvo"], "motivo": ident["motivo"]}
                else:
                    acao, motivo = "HUMAN_REVIEW", ident["motivo"]
                    c["dedup"] = {**c["dedup"], "classe": "POSSIBLE_DUPLICATE", "uid": ident["alvo"], "motivo": ident["motivo"]}
        if acao is None and c["dedup"]["classe"] == "NEW_STUDY_CANDIDATE":
            pubs = publicacoes(c, rede)
            acao, motivo = filtro_editorial(c, pubs, principal(c, pubs))
        c["pre_action"], c["pre_reason"] = acao, motivo
        linhas.append(c)
    out = {"gerado_em": datetime.date.today().isoformat(), "versao": versao(), "brutos": col["brutos"],
           "candidatos": linhas}
    (DIR / "triagem.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return out


def selecionar(ids: list[str], nome: str, motivos: dict | None = None) -> list[str]:
    """Seleção manual (mini-piloto dirigido): só candidatos que a triagem deixou para o LLM."""
    tri = {c["cand_id"]: c for c in json.loads((DIR / "triagem.json").read_text())["candidatos"]}
    fora = [i for i in ids if i not in tri or tri[i]["pre_action"] is not None]
    if fora:
        raise SystemExit(f"fora dos elegíveis ao LLM: {[(i, (tri.get(i) or {}).get('pre_action')) for i in fora]}")
    (DIR / f"{nome}.json").write_text(json.dumps({"n": len(ids), "versao": versao(), "candidatos": ids,
                                                  "motivos": motivos or {}}, ensure_ascii=False, indent=1), encoding="utf-8")
    return ids


def piloto(n: int = 25, semente: str = "novos-piloto-1") -> list[str]:
    """Estratificado por grupo de consulta e alternando fase 3 / fase 2; ordem por hash (não pelos 'mais óbvios')."""
    tri = json.loads((DIR / "triagem.json").read_text())
    elegiveis = [c for c in tri["candidatos"] if c["pre_action"] is None]
    h = lambda x: hashlib.sha256(f"{semente}:{x}".encode()).hexdigest()  # noqa: E731
    por = collections.defaultdict(lambda: {"f3": [], "f2": []})
    for c in elegiveis:
        g = sorted(f.split(":")[1] for f in c["found_by"])[0]
        por[g]["f3" if "PHASE3" in (c.get("phases") or []) or not c.get("nct") else "f2"].append(c)
    for g in por:
        for k in ("f3", "f2"):
            por[g][k].sort(key=lambda c: h(c["cand_id"]))
    sel, rodada = [], 0
    while len(sel) < n and any(por[g]["f3"] or por[g]["f2"] for g in por):
        for g in sorted(por, key=h):
            ordem = ("f3", "f2") if rodada % 2 == 0 else ("f2", "f3")
            for k in ordem:
                if por[g][k] and len(sel) < n:
                    sel.append(por[g][k].pop(0)["cand_id"])
                    break
        rodada += 1
    (DIR / "piloto.json").write_text(json.dumps({"semente": semente, "n": len(sel), "elegiveis": len(elegiveis),
                                                 "versao": versao(), "candidatos": sel}, ensure_ascii=False, indent=1),
                                     encoding="utf-8")
    return sel


# ── lote retomável ──────────────────────────────────────────────────────────────────────────────────────────────
ETAPAS = ("preparar", "curator", "verifier")


def _cand(cid: str) -> dict:
    return next(c for c in json.loads((DIR / "triagem.json").read_text())["candidatos"] if c["cand_id"] == cid)


def compat(c: dict) -> dict:
    return {"novos_version": versao(), "candidato_sha": DS._sha({k: c.get(k) for k in (
        "nct", "pmids", "status", "phases", "dedup", "pre_action")}), "cards_sha": DS._sha(sorted(DS.cards()))}


def processar(cid: str, etapas: dict, trava: threading.Lock) -> dict:
    c = _cand(cid)
    comp = compat(c)
    f = DIR / cid / "estado.json"
    try:
        e = json.loads(f.read_text())
        inicial = "compativel" if e.get("compat") == comp else "invalidado"
        if inicial == "invalidado":
            e = {"compat": comp, "etapas": {}}
    except (FileNotFoundError, json.JSONDecodeError):
        e, inicial = {"compat": comp, "etapas": {}}, "novo"
    feitas = []
    for nome in ETAPAS:
        if (e["etapas"].get(nome) or {}).get("ok"):
            continue
        if nome == "preparar":
            with trava:
                res = etapas["preparar"](c)
        else:
            res = etapas[nome](cid)
        e["etapas"][nome] = {"ok": True, "em": datetime.datetime.now().isoformat(timespec="seconds"), **(res or {})}
        (DIR / cid).mkdir(parents=True, exist_ok=True)
        tmp = DIR / cid / "estado.json.tmp"
        tmp.write_text(json.dumps(e, ensure_ascii=False, indent=1), encoding="utf-8")
        os.replace(tmp, f)
        feitas.append(nome)
    return {"cand_id": cid, "estado_inicial": inicial, "etapas_executadas": feitas}


def etapas_reais(rede: bool) -> dict:
    def prep(c):
        return {"packet_sha256": preparar(c, rede)["packet_sha256"]}

    def agente(papel):
        def rodar(cid):
            try:
                from . import run_agents as RA
            except ImportError:
                import run_agents as RA
            au = RA.executar(f"novos_{papel}", cid)
            d = ingerir(papel, cid, str(RA.RAW / f"{cid}.novos_{papel}.json"))
            if d.get("_erros"):
                raise RuntimeError(f"{papel}: {d['_erros']}")
            return {"sha256": d["_sha256"], "custo_usd": au.get("custo_usd")}
        return rodar
    return {"preparar": prep, "curator": agente("curator"), "verifier": agente("verifier")}


def executar_lote(cids: list[str], rede: bool = False, paralelo: int = 4, etapas: dict | None = None) -> list[dict]:
    etapas = etapas or etapas_reais(rede)
    trava, out = threading.Lock(), []
    with cf.ThreadPoolExecutor(max_workers=paralelo) as ex:
        futs = {ex.submit(processar, cid, etapas, trava): cid for cid in cids}
        for f in cf.as_completed(futs):
            try:
                out.append(f.result())
            except Exception as x:                               # noqa: BLE001
                out.append({"cand_id": futs[f], "erro": f"{type(x).__name__}: {x}"})
    return out


# ── consolidação ────────────────────────────────────────────────────────────────────────────────────────────────
def consolidar(nome: str = "piloto") -> dict:
    tri = json.loads((DIR / "triagem.json").read_text())
    sel = set(json.loads((DIR / f"{nome}.json").read_text())["candidatos"]) if (DIR / f"{nome}.json").exists() else set()
    linhas, custo = [], 0.0
    for c in tri["candidatos"]:
        base = {"cand_id": c["cand_id"], "nct": c.get("nct"), "title": c.get("title"), "acronym": c.get("acronym"),
                "phases": c.get("phases"), "status": c.get("status"), "found_by": c.get("found_by"),
                "tumor_groups": c.get("tumor_groups"), "dedup": c["dedup"]["classe"], "dedup_reason": c["dedup"]["motivo"],
                "dedup_card": c["dedup"].get("uid")}
        if c["cand_id"] not in sel:
            linhas.append({**base, "origin": "deterministic", "action": c["pre_action"], "reason": c["pre_reason"],
                           "final_verdict": "PASS" if c["pre_action"] else None, "no_piloto": False})
            continue
        pasta = DIR / c["cand_id"]
        cur = json.loads((pasta / "curator.json").read_text()) if (pasta / "curator.json").exists() else {}
        ver = json.loads((pasta / "verifier.json").read_text()) if (pasta / "verifier.json").exists() else {}
        est = json.loads((pasta / "estado.json").read_text()) if (pasta / "estado.json").exists() else {"etapas": {}}
        custo += sum((est["etapas"].get(k) or {}).get("custo_usd") or 0 for k in ("curator", "verifier"))
        det = (cur.get("_deterministico") or {}).get("verdict", "UNSUPPORTED") if cur else None
        vv = "FAIL" if (cur.get("_erros") or ver.get("_erros")) else ver.get("verdict")
        final = K.pior([v for v in (det, vv or "UNSUPPORTED") if v]) if cur else None
        linhas.append({**base, "origin": "llm", "no_piloto": True, "action": cur.get("action"),
                       **{k: cur.get(k) for k in ("study", "main_publication", "tumor", "intervention", "comparator",
                                                  "phase", "primary_endpoint", "reason", "main_result", "maturity",
                                                  "related_card_uid", "evidence", "notes_for_human", "policy_basis",
                                                  "editorial_limitation", "comparison_type")},
                       "curator_verdict": det, "curator_checks": (cur.get("_deterministico") or {}).get("achados"),
                       "verifier_verdict": vv, "verifier_evidence": ver.get("evidence_verdict"),
                       "verifier_action": ver.get("action_verdict"), "verifier_reason": ver.get("reason"),
                       "final_verdict": final, "completo": bool(cur and ver)})
    llm = [l for l in linhas if l["origin"] == "llm"]
    fila = [l for l in linhas if l["action"] in ("NEW_CARD", "HUMAN_REVIEW", "RELATED_TO_EXISTING") or
            (l["origin"] == "llm" and l.get("final_verdict") not in ("PASS", None))]
    rel = {"gerado_em": datetime.date.today().isoformat(), "versao": versao(), "brutos": tri["brutos"],
           "candidatos_unicos": len(tri["candidatos"]),
           "dedup": dict(collections.Counter(l["dedup"] for l in linhas)),
           "pre_llm": dict(collections.Counter(l["action"] for l in linhas if l["origin"] == "deterministic")),
           "elegiveis_llm": sum(1 for c in tri["candidatos"] if c["pre_action"] is None), "no_piloto": len(llm),
           "acoes_llm": dict(collections.Counter(l["action"] for l in llm)),
           "vereditos_llm": dict(collections.Counter(l["final_verdict"] for l in llm)),
           "custo_usd": round(custo, 2), "fila_humana": len(fila), "rows": linhas}
    (DIR / f"relatorio_{nome}.json").write_text(json.dumps(rel, ensure_ascii=False, indent=1), encoding="utf-8")
    return rel


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["universo", "schemas", "coletar", "triagem", "piloto", "selecionar", "lote",
                                    "consolidar", "versao"])
    ap.add_argument("--piloto", default="piloto")
    ap.add_argument("--ids", nargs="*", default=[])
    ap.add_argument("--rede", action="store_true")
    ap.add_argument("--paralelo", type=int, default=4)
    ap.add_argument("--n", type=int, default=25)
    a = ap.parse_args(argv)
    DIR.mkdir(parents=True, exist_ok=True)
    if a.cmd == "universo":
        u = universo()
        (DIR / "universo_editorial.json").write_text(json.dumps(u, ensure_ascii=False, indent=1), encoding="utf-8")
        print(json.dumps(u, ensure_ascii=False, indent=1))
    elif a.cmd == "schemas":
        gravar_schemas()
        print(versao())
    elif a.cmd == "versao":
        print(versao())
    elif a.cmd == "coletar":
        r = coletar(a.rede)
        print(json.dumps({"brutos": r["brutos"], "candidatos": len(r["candidatos"])}))
    elif a.cmd == "triagem":
        t = triagem(a.rede)
        print(json.dumps({"dedup": dict(collections.Counter(c["dedup"]["classe"] for c in t["candidatos"])),
                          "pre": dict(collections.Counter(c["pre_action"] for c in t["candidatos"]))}, ensure_ascii=False))
    elif a.cmd == "piloto":
        print(json.dumps(piloto(a.n), ensure_ascii=False))
    elif a.cmd == "selecionar":
        print(json.dumps(selecionar(a.ids, a.piloto), ensure_ascii=False))
    elif a.cmd == "lote":
        sel = json.loads((DIR / f"{a.piloto}.json").read_text())["candidatos"]
        for r in executar_lote(sel, a.rede, a.paralelo):
            print(json.dumps(r, ensure_ascii=False), flush=True)
    elif a.cmd == "consolidar":
        r = consolidar(a.piloto)
        print(json.dumps({k: v for k, v in r.items() if k != "rows"}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
