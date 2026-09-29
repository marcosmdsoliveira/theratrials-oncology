"""lift_v1 — converte os cards do data.js em registros-SOMBRA v2 (curation.level = shadow).

    python3 scripts/db_v2/lift_v1.py            # grava scripts/_db_v2_shadow/ (ignorado pelo git)

Regras (conservadoras de propósito):
- o card v1 inteiro vai LITERAL para legacy.v1 (base do round-trip);
- nenhum dado clínico vira present: todo campo clínico fica state=unknown com legacy_ref para o campo v1;
- só entram como present (origin=legacy, prov=v1, confiança baixa) identificadores e navegação que mapeiam
  1:1 sem interpretação: short_name, display_title, category_id, registro com formato exato, PMID do link;
- "—", vazio e textos como "Não publicado"/"Variável" NÃO viram not_reported/not_applicable: não dá para
  distinguir, então ficam unknown;
- módulo só é atribuído com evidência forte (agente/isótopo terapêutico nomeado no campo de intervenção);
  papel e braços ficam 'undetermined'/null; o resto vira sugestão em curation.suggestions;
- record_type é inferido com base registrada (curation.record_type_basis).

Somente leitura do data.js. Nunca escreve fora de scripts/_db_v2_shadow/.
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import sys

import v2lib as L

VAZIO = {"", "—", "-", "–"}

# campos v1 → caminho v2 (core). Campos v1 sem destino direto ficam só no legado.
MAPA = {
    "identity.short_name": ["estudo"], "identity.display_title": ["acron"],
    "identity.registrations": ["nct", "nct_url"], "identity.phase": ["fase"],
    "identity.sponsor": ["sponsor"], "identity.centers": ["centros"], "identity.enrollment_period": ["periodo"],
    "identity.represented_publication": ["pubmed_url", "ano_pub", "titulo_full", "ref"],
    "identity.category_id": ["category_id"], "identity.tumors": ["tumors"],
    "identity.evidence_stage": ["status"],
    "population.disease": ["indicacao"], "population.setting": ["linha"],
    "population.biomarker_selection": ["molecular", "biomarc"],
    "population.key_inclusion": ["incl"], "population.key_exclusion": ["excl"], "population.baseline": ["basal"],
    "design.structure": ["desenho"], "design.arms": ["radiofarmaco", "esquema", "comparador", "n"],
    "design.control": ["comparador"], "design.comparisons": ["estatistica"], "design.sample_size": ["n"],
    "design.stratification": ["estrat"], "design.statistical_plan": ["estatistica", "analises"],
    "endpoints": ["primario", "secundario"], "subgroups": ["subgrupo"],
    "safety.grade3plus_any": ["tox_g3"], "safety.key_toxicities": ["tox_g3", "tox_interesse"],
    "interpretation.key_result": ["resultado_chave"], "interpretation.takehome": ["takehome"],
    "interpretation.limitations": ["limit"], "interpretation.clinical_impact": ["impacto_reg"],
}
# campos v1 que não têm destino no core e ficam SÓ no legado (documentado, não é perda: legacy.v1 é literal)
SO_LEGADO = {"cumul", "preparo", "category_name", "category_short", "category_color", "uid", "modalities",
             "fonte_principal", "grau_confianca", "status_curadoria", "ultima_revisao"}

# ── léxico de agentes (evidência forte = nome próprio) ──────────────────────
X = r"(?:e|a|o)?"  # sufixo português opcional (olaparibe, deruxtecana, govitecano)
LEX = {
    "radionuclide_therapy": [rf"177\s?-?lu\b", r"\blu-?177\b", r"225\s?-?ac\b", r"\bac-?225\b", r"\b131\s?-?i\b",
                             r"\bi-?131\b", r"iodo-131", r"radioiodo", r"\brai\b", r"223\s?-?ra\b", r"\bra-?223\b",
                             r"rádio-223", r"radium-223", r"\b90\s?-?y\b", r"\by-?90\b", r"sir-?spheres",
                             r"therasphere", r"212\s?-?pb\b", r"161\s?-?tb\b", r"67\s?-?cu\b", r"227\s?-?th\b",
                             r"lutathera", r"pluvicto", r"xofigo", r"azedra", r"ibritumomab", r"radioemboliz"],
    "adc": [rf"deruxtecan{X}", rf"govitecan{X}", rf"vedotin{X}", rf"emtansin{X}", rf"mafodotin{X}", rf"tesirin{X}",
            rf"ozogamicin{X}", rf"soravtansin{X}", r"\bt-?dxd\b", r"\bt-?dm1\b", r"\bdato-?dxd\b",
            rf"brengitecan{X}", rf"sacituzumab{X}"],
    "immunotherapy": [rf"{n}{X}" for n in ["pembrolizumab", "nivolumab", "atezolizumab", "durvalumab", "ipilimumab",
                                            "cemiplimab", "dostarlimab", "tislelizumab", "toripalimab", "avelumab",
                                            "camrelizumab", "sintilimab", "relatlimab", "tremelimumab", "serplulimab",
                                            "retifanlimab", "penpulimab", "cadonilimab", "spartalizumab"]]
                     + [r"\bpembro\b", r"\bnivo\b", r"\bipi\b", r"\batezo\b", r"\bdurva\b", r"\btreme\b",
                        r"anti-pd-?l?1", r"anti-ctla-?4", r"sipuleucel"]
                     + [r"\bbcg\b", r"interleucina-2", r"\bil-2\b", r"talimogen", r"nogapendekin", r"nadofaragen",
                        r"lifileucel"],
    "t_cell_engager": [rf"{n}{X}" for n in ["teclistamab", "elranatamab", "talquetamab", "linvoseltamab",
                                             "glofitamab", "epcoritamab", "mosunetuzumab", "odronextamab",
                                             "tarlatamab", "blinatumomab", "tebentafusp"]],
    "cellular": [r"\bcar-?t\b", r"axicabtagen", r"axi-cel", r"tisagenlecleucel", r"tisa-cel", r"lisocabtagen",
                 r"liso-cel", r"ciltacabtagen", r"cilta-cel", r"idecabtagen", r"ide-cel", r"brexucabtagen",
                 r"afamitresgen", r"afami-cel", r"tcth alog", r"transplante alog"],
    "targeted_therapy": [r"\w{3,}nib" + X + r"\b", r"\w+staurin" + X + r"\b", r"\w+nexor\b",
                         r"everolim(?:o|us)\b", r"\w+tinib" + X + r"\b", r"\w+rafenib" + X + r"\b", r"\w+metinib" + X + r"\b",
                         r"\w+ciclib" + X + r"\b", r"\w+parib" + X + r"\b", r"\w+lisib" + X + r"\b",
                         r"\w+sertib" + X + r"\b", r"\w+rasib" + X + r"\b", r"\w+degib" + X + r"\b",
                         r"trastuzumab(?:e)?(?!\s*(?:deruxtecan|emtansin))", rf"pertuzumab{X}", rf"bevacizumab{X}",
                         rf"ramucirumab{X}", rf"cetuximab{X}", rf"panitumumab{X}", rf"daratumumab{X}",
                         rf"isatuximab{X}", rf"elotuzumab{X}", rf"dinutuximab{X}", rf"naxitamab{X}", rf"rituximab{X}",
                         rf"obinutuzumab{X}", rf"tafasitamab{X}", rf"zolbetuximab{X}", rf"amivantamab{X}",
                         rf"ivonescimab{X}", rf"zanidatamab{X}", rf"everolimus{X}", rf"venetoclax{X}",
                         r"lenalidomid", r"pomalidomid", r"talidomid", r"bortezomib", r"carfilzomib",
                         rf"belzutifan{X}", rf"ivosidenib{X}", rf"enasidenib{X}", rf"revumenib{X}",
                         r"octreot[ií]d", r"lanreot[ií]d"],
    "endocrine": [r"enzalutamid", r"abirateron", r"apalutamid", r"darolutamid", r"\badt\b", r"privação androg",
                  r"letrozol", r"anastrozol", r"exemestan", r"fulvestrant", r"tamoxifen", r"elacestrant",
                  r"camizestrant", r"imlunestrant", r"giredestrant", r"vepdegestrant", r"degarelix", r"relugolix",
                  r"leuprorrel", r"gosserrel", r"goserel", r"supressão ovariana"],
    "chemotherapy": [r"docetaxel", r"cabazitaxel", r"paclitaxel", r"cisplatin", r"carboplatin", r"oxaliplatin",
                     r"gemcitabin", r"capecitabin", r"fluorouracil", r"\b5-?fu\b", r"folfox", r"folfiri",
                     r"folfirinox", r"\bcapox\b", r"\bxelox\b", r"\bflot\b", r"temozolomid", r"irinotecan",
                     r"etoposíd", r"etoposid", r"topotecan", r"doxorrubicin", r"doxorubicin", r"ciclofosfamid",
                     r"citarabin", r"cytarabin", r"pemetrexed", r"vinorelbin", r"lurbinectedin", r"trabectedin",
                     r"eribulin", r"azacitidin", r"decitabin", r"melfalan", r"busulfan", r"estreptozoc",
                     r"quimioterapia", r"\br-chop\b", r"\bchop\b", r"\bqt\b", r"\bep\b", r"\bhidac\b",
                     r"7\s?\+\s?3"],
    "radiotherapy": [r"\bsbrt\b", r"\bsabr\b", r"radioterapia", r"\bimrt\b", r"braquiterapia", r"radiocirurgia",
                     r"\b\d+(?:[.,]\d+)?\s?gy\b", r"quimiorradi", r"\bqrt\b", r"hipofracion"],
    "locoregional": [r"\btace\b", r"quimioemboliz", r"\bhaic\b", r"\bhipec\b", r"intravesical"],
}
TRACADOR = re.compile(r"68\s?-?ga|18\s?-?f\b|\bf-18|64\s?-?cu|89\s?-?zr|123\s?-?i\b|99m\s?-?tc|\bpet\b", re.I)
CAMPOS_INTERVENCAO = ["radiofarmaco", "esquema", "acron", "estudo"]  # evidência forte
CAMPOS_FRACOS = ["comparador", "desenho", "indicacao"]              # só sugestão


SOBRESCRITO = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹", "0123456789")


def _txt(card, campos):
    """Texto dos campos com sobrescritos normalizados (¹⁷⁷Lu → 177Lu)."""
    return " ".join(str(card.get(c) or "") for c in campos).translate(SOBRESCRITO)


def modulos(card: dict) -> tuple[list[dict], list[dict]]:
    """(módulos com evidência forte, sugestões de média confiança)."""
    fortes, sugest = [], []
    forte_txt, fraco_txt = _txt(card, CAMPOS_INTERVENCAO), _txt(card, CAMPOS_FRACOS)
    # "RAI-refratário"/"refratário ao iodo" descreve a população, não a intervenção
    forte_txt = re.sub(r"(rai|131\s?-?i|iodo)[-\s]?refrat\w*|refrat\w* (ao|a) (rai|iodo|131\s?-?i)", " ", forte_txt, flags=re.I)
    for mod, pads in LEX.items():
        ev_f = sorted({m.group(0) for p in pads for m in re.finditer(p, forte_txt, re.I)})
        ev_w = sorted({m.group(0) for p in pads for m in re.finditer(p, fraco_txt, re.I)} - set(ev_f))
        rf = str(card.get("radiofarmaco", "")).translate(SOBRESCRITO)
        if mod == "radionuclide_therapy" and ev_f and TRACADOR.search(rf) \
                and not re.search(r"177|225|131|223|90|212|161|67cu|terap", rf, re.I):
            sugest.append({"path": "modules", "value": mod, "confidence": "low",
                           "basis": "traçador diagnóstico no campo de intervenção"})
            continue
        if mod == "radionuclide_therapy" and ev_f and all(e.lower() in ("rai", "radioiodo") for e in ev_f):
            sugest.append({"path": "modules", "value": mod, "confidence": "medium",
                           "basis": "só a sigla RAI/radioiodo (pode ser covariável ou critério, não intervenção)"})
            continue
        if mod == "radiotherapy" and ev_f and all(re.fullmatch(r"\d+(?:[.,]\d+)?\s?gy", e, re.I) for e in ev_f) \
                and re.search("|".join(LEX["radionuclide_therapy"]), forte_txt, re.I):
            # só doses em Gy num card de radionuclídeo: dose absorvida (TARE/dosimetria), não RT externa
            sugest.append({"path": "modules", "value": mod, "confidence": "low",
                           "basis": "doses em Gy em card de radionuclídeo (provável dose absorvida): " + ", ".join(ev_f[:4])})
            continue
        if ev_f:
            fortes.append({"module": mod, "role": "undetermined", "arm_ids": None,
                           "classification": {"basis": "inferred", "confidence": "high",
                                              "evidence": [f"{'/'.join(CAMPOS_INTERVENCAO)}: {e}" for e in ev_f][:6]}})
        elif ev_w:
            sugest.append({"path": "modules", "value": mod, "confidence": "medium",
                           "basis": f"termo só em {'/'.join(CAMPOS_FRACOS)}: " + ", ".join(ev_w[:4])})
    if re.search(r"cirurg|ressecç|ectomia", _txt(card, ["radiofarmaco", "esquema"]), re.I):
        sugest.append({"path": "modules", "value": "surgery", "confidence": "low",
                       "basis": "procedimento citado no esquema; papel (intervenção × prévio) indeterminado"})
    return fortes, sugest


def record_type(card: dict) -> dict:
    f = (str(card.get("fase", "")) + " " + str(card.get("desenho", ""))[:160]).lower()
    regras = [
        ("guideline", "high", r"diretriz|guideline|consenso"),
        ("meta_analysis", "high", r"meta-?an[aá]lise|revisão sistem"),
        ("molecular_classification", "medium", r"classifica[çc][aã]o (molecular|who|oms)|estudo molecular"),
        ("pooled_analysis", "medium", r"an[aá]lise combinada|pooled|agrupad"),
        ("cohort_study", "medium", r"retrospectiv|real-world|registro nacional|coorte multic"),
        ("diagnostic_study", "medium", r"acur[aá]cia|diagn[oó]stic"),
    ]
    for tipo, conf, pad in regras:
        m = re.search(pad, f)
        if m:
            return {"value": tipo, "basis": "inferred", "confidence": conf, "evidence": [f"fase/desenho: '{m.group(0)}'"]}
    return {"value": "trial", "basis": "inferred", "confidence": "medium",
            "evidence": ["padrão: nenhum marcador de outro tipo em fase/desenho"]}


def _env_unknown(campos_v1, card) -> dict:
    tem = [c for c in campos_v1 if c in card and str(card[c]).strip() not in VAZIO]
    env = {"state": "unknown", "legacy_ref": campos_v1}
    if not tem:
        env["note"] = "v1 vazio ou '—': não relatado, não aplicável e não curado são indistinguíveis"
    return env


def _present_legacy(v, campos_v1) -> dict:
    return {"state": "present", "origin": "legacy", "v": v, "prov": "v1", "legacy_ref": campos_v1}


def lift(card: dict, pos: int, decisoes: dict, fonte_sha: str | None = None) -> dict:
    rt = record_type(card)
    fortes, sugest = modulos(card)
    unc, sug = [], list(sugest)
    rec = {"schema": L.SCHEMA_ID, "uid": card["uid"], "record_type": rt["value"],
           "curation": {"level": "shadow", "record_type_basis": rt, "uncertainty": unc, "suggestions": sug,
                        **({"source_sha256": fonte_sha} if fonte_sha else {})},
           "relationships": {"parent_uid": None, "child_uids": [], "links": []},
           "external_relationships": [],
           "modules": fortes}
    for path, campos in MAPA.items():
        env = _env_unknown(campos, card)
        if path == "identity.short_name" and card.get("estudo"):
            env = _present_legacy(card["estudo"], campos)
        elif path == "identity.display_title" and card.get("acron"):
            env = _present_legacy(card["acron"], campos)
        elif path == "identity.category_id":
            env = _present_legacy(card["category_id"], campos)
        elif path == "identity.registrations":
            nct = str(card.get("nct", "")).strip()
            if re.fullmatch(r"NCT\d{8}", nct):
                env = _present_legacy([{"registry": "NCT", "id": nct}], campos)
            elif re.fullmatch(r"ISRCTN\d{8}", nct):
                env = _present_legacy([{"registry": "ISRCTN", "id": nct}], campos)
            elif nct not in VAZIO:
                unc.append({"path": path, "reason": "nct com texto livre ou vários identificadores; não separado",
                            "legacy": nct[:120]})
        elif path == "identity.represented_publication":
            m = re.search(r"pubmed\.ncbi\.nlm\.nih\.gov/(\d+)", str(card.get("pubmed_url", "")))
            if m:
                pub = {"pmid": m.group(1)}
                if isinstance(card.get("ano_pub"), int) and card["ano_pub"] > 0:
                    pub["year"] = card["ano_pub"]
                elif card.get("ano_pub") not in (0, None, ""):
                    unc.append({"path": path + ".year", "reason": "ano_pub não é inteiro", "legacy": card["ano_pub"]})
                env = _present_legacy(pub, campos)
            elif str(card.get("pubmed_url", "")).strip():
                unc.append({"path": path, "reason": "pubmed_url sem PMID reconhecível",
                            "legacy": card["pubmed_url"][:120]})
        elif path == "identity.phase":
            m = re.search(r"fase\s*(1/2|2/3|[1-4])|phase\s*(1/2|2/3|[1-4])", str(card.get("fase", "")), re.I)
            if m:
                sug.append({"path": path, "value": m.group(1) or m.group(2), "confidence": "medium",
                            "basis": f"fase: '{card['fase'][:60]}'"})
        elif path == "identity.evidence_stage":
            st = str(card.get("status", ""))
            for pad, val in [(r"^Em revisão", None), (r"^Publicado", "published_*"), (r"^Apresentado", "presented"),
                             (r"^Em andamento", "ongoing"), (r"^Conclu", "published_*|registered"),
                             (r"^Encerrado", "registered")]:
                if re.search(pad, st):
                    if val:
                        sug.append({"path": path, "value": val, "confidence": "low",
                                    "basis": f"status: '{st[:60]}' (não distingue interina × primária × final)"})
                    break
        grupo = path.split(".")[0] if "." in path else None
        if grupo:
            rec.setdefault(grupo, {})[path.split(".", 1)[1]] = env
        else:
            rec[path] = env
    status = str(card.get("status", ""))
    quarentena = decisoes.get(card["uid"])
    rec["review"] = {"editorial_status": "withheld" if status.startswith("Em revisão") else "active",
                     "integrity": ({"status": "withheld", "reason": "quarentena editorial",
                                    "decision_ref": quarentena} if quarentena else {"status": "none"})}
    rec["provenance"] = {"v1": {"source": {"type": "v1_legacy", "field": "*"}, "extraction": "lifted_v1",
                                "evidence_confidence": "low"}}
    rec["legacy"] = {"v1": card, "position": pos}
    return rec


def main(argv=None):
    import argparse
    import pathlib
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-js", default=str(L.DATA_JS))
    ap.add_argument("--out", default=str(L.SHADOW))
    ap.add_argument("--decisoes", default=str(L.SCRIPTS / "db_decisoes.json"))
    a = ap.parse_args(argv)
    saida = pathlib.Path(a.out)
    texto = pathlib.Path(a.data_js).read_text(encoding="utf-8")
    prefixo, obj, sufixo = L.ler_data_js(texto)
    fonte_sha = hashlib.sha256(texto.encode("utf-8")).hexdigest()
    decs = json.loads(pathlib.Path(a.decisoes).read_text(encoding="utf-8")).get("decisoes", [])
    quarentena = {d["uid"]: d["id"] for d in decs
                  if d.get("tipo") == "classificacao" and d.get("valor") == "EDITORIAL_QUARANTINE"}
    if saida.resolve() in (L.DATA_JS.resolve().parent, L.SITE.resolve(), L.SCRIPTS.resolve()):
        raise SystemExit("recusado: --out tem de ser um diretório dedicado")
    if saida.exists():
        shutil.rmtree(saida)
    saida.mkdir(parents=True)
    estudos = obj["studies"]
    (saida / "_dataset.json").write_text(json.dumps({
        "prefix": prefixo, "suffix": sufixo, "top_keys": list(obj.keys()),
        "other": {k: v for k, v in obj.items() if k != "studies"},
        "study_order": [c["uid"] for c in estudos],
        "source_sha256": fonte_sha,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    from collections import Counter
    c_rt, c_mod, c_nmod, c_pres, c_unc, c_sug = Counter(), Counter(), Counter(), Counter(), 0, 0
    for pos, card in enumerate(estudos):
        rec = lift(card, pos, quarentena, fonte_sha)
        (saida / f"{card['uid']}.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
        c_rt[(rec["record_type"], rec["curation"]["record_type_basis"]["confidence"])] += 1
        c_mod.update(m["module"] for m in rec["modules"])
        c_nmod[len(rec["modules"])] += 1
        for g in ("identity", "population", "design", "safety", "interpretation"):
            for campo, env in rec.get(g, {}).items():
                c_pres[env["state"]] += 1
        for k in ("endpoints", "subgroups"):
            c_pres[rec[k]["state"]] += 1
        c_unc += len(rec["curation"]["uncertainty"])
        c_sug += len(rec["curation"]["suggestions"])
    resumo = {"cards": len(estudos), "record_type": {f"{a}/{b}": n for (a, b), n in sorted(c_rt.items())},
              "modulos_atribuidos": dict(c_mod.most_common()), "modulos_por_card": dict(sorted(c_nmod.items())),
              "estados": dict(c_pres), "incertezas": c_unc, "sugestoes": c_sug,
              "saida": str(saida)}
    print(json.dumps(resumo, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
