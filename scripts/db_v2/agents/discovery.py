"""discovery — descoberta de publicações NOVAS ligadas aos cards existentes (modo sombra, sem auto-apply).

    python3 scripts/db_v2/agents/discovery.py amostra [--n 30]              # amostra estratificada → state/discovery/piloto.json
    python3 scripts/db_v2/agents/discovery.py coletar <uid>... [--rede]     # estágio 0 determinístico → state/discovery/<uid>/
    python3 scripts/db_v2/agents/discovery.py tarefa <uid>                  # prompt do database-curator (modo discovery)
    python3 scripts/db_v2/agents/discovery.py entrada <uid>                 # entrada do database-verifier (sem raciocínio do curator)
    python3 scripts/db_v2/agents/discovery.py ingerir curator|verifier <uid> <arquivo>
    python3 scripts/db_v2/agents/discovery.py consolidar <uid>...          # funde vereditos → state/discovery/relatorio.json

Estágio 0 (determinístico, sem LLM):
  • candidatos só por vínculo verificável com o registro do estudo: PubMed [si] (DataBank da própria publicação),
    referências do CT.gov API v2 e Europe PMC (ID do registro no título/resumo). Crossref não é usado para descobrir.
  • elimina: publicação já cadastrada (PMID/DOI do card ou de secundário do card), duplicata PMID/DOI entre fontes,
    errata. Comentário/editorial/carta → NO_ACTION determinístico; retratação/expression of concern → HUMAN_REVIEW.
Estágio 1 (LLM, assistente): o database-curator gera analysis_signature da análise do card e de cada candidato,
relação e ação editorial, com trecho literal. O database-verifier confere de forma independente.
Estágio 2 (determinístico): trechos literais, números da assinatura nos trechos citados, relação recalculada pela
assinatura (signature.relacao) e coerência relação × ação. Veredito final = o pior. Nada escreve no Database.
"""
from __future__ import annotations

import argparse
import collections
import concurrent.futures as cf
import os
import threading
import datetime
import hashlib
import json
import pathlib
import re
import sys
import urllib.parse

AQUI = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
import bibliografia as B  # noqa: E402
import v2lib as L  # noqa: E402

try:
    from . import agent_types as T, checks as K, signature as G, sources as S
except ImportError:
    import agent_types as T
    import checks as K
    import signature as G
    import sources as S

DISC = S.STATE / "discovery"
SCHEMA_PACOTE = "theratrials-db-discovery-packet/1"
SCHEMA_CURATOR = "theratrials-db-discovery-curator/1"
SCHEMA_VERIFIER = "theratrials-db-discovery-verification/1"

RELACOES = T.DISCOVERY_RELATIONS       # inclui SAME_ANALYSIS: mesma análise e mesmo corte (sem atualização)
ACOES = T.DISCOVERY_ACTIONS
# ações que cada relação admite; fora disso → HUMAN_REVIEW (nunca silêncio)
ACOES_DA_RELACAO = {
    "SAME_ANALYSIS_UPDATE": {"UPDATE_CARD", "STORE_SOURCE", "WATCH", "HUMAN_REVIEW"},
    "LONG_TERM_FOLLOWUP": {"UPDATE_CARD", "ADD_SECONDARY", "STORE_SOURCE", "WATCH", "HUMAN_REVIEW"},
    "SECONDARY_ANALYSIS": {"ADD_SECONDARY", "STORE_SOURCE", "WATCH", "NO_ACTION", "HUMAN_REVIEW"},
    "SUBGROUP": {"ADD_SECONDARY", "STORE_SOURCE", "WATCH", "NO_ACTION", "HUMAN_REVIEW"},
    "NEW_COHORT": {"ADD_SECONDARY", "STORE_SOURCE", "WATCH", "NO_ACTION", "HUMAN_REVIEW"},
    "SAME_ANALYSIS": {"STORE_SOURCE", "NO_ACTION", "HUMAN_REVIEW"},
    "UNRELATED": {"NO_ACTION"},
    "UNDETERMINED": {"WATCH", "HUMAN_REVIEW"},
    "PROTOCOL": {"STORE_SOURCE", "HUMAN_REVIEW"},                  # protocolo do próprio estudo: vínculo preservado
    "POOLED_ANALYSIS": {"STORE_SOURCE", "HUMAN_REVIEW", "NO_ACTION"},  # vários estudos: nunca secundário automático
}
PIPELINE_VERSION = "discovery/3"
# tipos de publicação sem dado original do estudo (PubMed e Europe PMC, comparados em minúsculas)
SEM_DADO_ORIGINAL = {"review", "review-article", "systematic review", "systematic-review", "meta-analysis",
                     "practice guideline", "guideline", "consensus development conference",
                     "consensus development conference, nih", "patient education handout", "historical article",
                     "news", "interview", "biography", "portrait", "editorial", "comment", "letter",
                     "newspaper article"}
TIPOS_ENSAIO = {"clinical trial", "randomized controlled trial", "controlled clinical trial", "multicenter study",
                "clinical trial, phase i", "clinical trial, phase ii", "clinical trial, phase iii",
                "clinical trial, phase iv", "pragmatic clinical trial", "equivalence trial", "observational study",
                "research-article", "clinical study"}
REGULATORIO = re.compile(r"\b(FDA|EMA|CHMP|EPAR|MHRA|PMDA|ANVISA|Health Canada|Project Orbis)\b[^.]{0,80}\b(approv\w*|"
                         r"summary|assessment|authori[sz]ation|review)\b|approval summary|regulatory (review|assessment)", re.I)
PROTOCOLO = re.compile(r"study protocol|trial protocol|protocol (for|of) (a|an|the)\b|:\s*protocol\b|rationale and design|"
                       r"design and rationale|trial in progress|statistical analysis plan", re.I)
POOLED = re.compile(  # agregação EXPLÍCITA de dados de ≥2 estudos (verbo/termo de combinação)
    r"pooled,? (?!(\w+ )?arms?\b)(\w+[, ]+){0,2}?(analysis|analyses|data|population|dataset|safety)|pooled across|"
    r"integrated (safety |efficacy )?(analysis|analyses|summary|data|dataset)|integrating data|"
    r"data (were |was )?(pooled|combined)|pooling (of )?data|"
    r"combined (data|analysis|dataset|results) (of|from)|(were|was) combined (from|across)|"
    r"individual[- ](patient|participant|level)[- ]data|patient[- ]level data (from|of)|"
    r"indirect (treatment )?comparison|matching[- ]adjusted|network meta", re.I)
POOLED_CONTAGEM = re.compile(  # "samples/patients/data from three trials": vale só se não houver relato separado
    r"\b(data|datasets|samples|specimens|tumou?rs|patients|participants|subjects|individuals|cases)\b[^.]{0,120}?"
    r"\b(from|in|across)\s+(the\s+)?(two|three|four|five|six|seven|eight|nine|ten|\d+|multiple|several)\s+"
    r"([\w/]+[ ,-]+){0,5}?(clinical\s+)?(trials|studies)\b", re.I)          # coortes de UM ensaio não são estudos distintos
ANTERIOR = re.compile(r"\bpreviously\b|\bwe (have )?(previously )?(reported|showed|shown|evaluated)\b|"
                     r"\bprior (report|analysis|study|publication)\b|\bearlier (report|analysis)\b", re.I)
MESMO_ENSAIO = re.compile(r"\bparts? \d|\bparts? (one|two|1|2)\b|\barms? (\d|[a-c])\b|\b(both|all) arms\b", re.I)
SEPARADO = re.compile(r"\bseparately\b|\bin each of\b|\bfor each (trial|study|cohort)\b|\beach (trial|study) (was|is) "
                      r"(analy[sz]ed|reported)", re.I)
POOLED_ATRAVES = re.compile(r"\bacross (the )?(\w+[ ,-]+){0,3}?(phase \w+ )?(clinical )?(trials|studies|program(me)?)\b", re.I)
PRECLINICO = re.compile(r"\bpre-?clinical\b|\bin vitro\b|\bin vivo\b|\bxenograft|\bmice\b|\bmouse\b|\bmurine\b|"
                        r"\brats?\b|\bcynomolgus\b|non-?human primate|\bcell lines?\b|\borganoids?\b", re.I)
CLINICO_NO_TITULO = re.compile(r"clinical (data|results?|outcomes?|activity|efficacy|experience|trial)|\bpatients?\b|"
                               r"\bphase (1|2|3|i|ii|iii)\b|first[- ]in[- ]human", re.I)
LEIGO = re.compile(r"plain[- ]language summary|lay (language )?summary|summary for patients|patient[- ]friendly summary", re.I)
TUMOR_AGNOSTICO = re.compile(r"agn[oó]stic|tumores s[oó]lidos|solid tumou?rs|pan-?tumou?r|tissue-agnostic", re.I)
TUMORES = {  # grupos de tumor (PT/EN) para saber se um candidato fala da coorte do card de basket
    "biliar": r"biliar|\bBTC\b|cholangio|colangio|gallbladder|ves[ií]cula|ampul", "hepatocel": r"hepatocell|\bHCC\b|CHC",
    "cervix": r"cervical|cervix|colo do [uú]tero|c[eé]rvix", "endometrio": r"endometri", "ovario": r"ovari",
    "pulmao_pc": r"small[- ]cell lung|\bSCLC\b|pequenas c[eé]lulas", "pulmao": r"\bNSCLC\b|non[- ]small|lung|pulm",
    "mama": r"breast|\bmama", "prostata": r"prostat|pr[oó]stata", "colorretal": r"(?<!non)(?<!non-)(?<!non )colorectal|(?<!n[aã]o-)colorretal|\bCRC\b",
    "gastroesof": r"gastric|g[aá]stric|esophag|es[oô]fag|gastroesophageal", "pancreas": r"pancrea",
    "melanoma": r"melanoma", "renal": r"renal cell|kidney|\bRCC\b|renal", "urotelial": r"urothelial|urotelial|bladder|bexiga",
    "tireoide": r"thyroid|tireoide|tiroide", "sarcoma": r"sarcoma", "snc": r"glioma|glioblastoma|\bbrain\b|\bCNS\b|SNC",
    "linfoma": r"lymphoma|linfoma", "mieloma": r"myeloma|mieloma", "leucemia": r"leuk|leucemia|\bAML\b|\bLMA\b",
    "net": r"neuroendocrin|\bNETs?\b|carcinoid", "cabeca_pescoco": r"head and neck|\bHNSCC\b|cabe[cç]a e pesco[cç]o",
    "mesotelioma": r"mesothelioma|mesotelioma", "anal": r"\banal\b", "neuroblastoma": r"neuroblastoma",
    "meningioma": r"meningioma", "endocrino_adrenal": r"adrenocortical|pheochromocytoma|paraganglioma|feocromocitoma"}


def grupos_tumor(texto: str) -> set[str]:
    g = {g for g, rx in TUMORES.items() if re.search(rx, texto or "", re.I)}
    if "pulmao_pc" in g and not re.search(r"\bNSCLC\b|non[- ]small", texto or "", re.I):
        g.discard("pulmao")                          # "small cell lung" é SCLC, não pulmão genérico
    return g
CARD_INTEGRADO = re.compile(r"pooled|agrupad|integrad|combinad|basket|an[aá]lise conjunta", re.I)
ECONOMICO = re.compile(r"cost[- ]effective|cost[- ]utility|cost[- ]consequence|cost[- ]minimi[sz]ation|economic evaluation|"
                       r"budget impact|pharmacoeconomic|health[- ]economic|markov (model|analysis)|partitioned survival model", re.I)
DA_ASSINATURA = {"DIFFERENT_STUDY": "UNRELATED"}               # vocabulário de signature.relacao → discovery
COMENTARIO = {"Comment", "Editorial", "Letter", "News", "Interview", "Newspaper Article", "Biography"}
ERRATA = {"Published Erratum"}
ALERTA = {"Retraction of Publication", "Retracted Publication", "Expression of Concern"}
REGISTRO = re.compile(r"NCT\d{8}|ACTRN\d{14}|ISRCTN\d{8}|EudraCT[ :]*\d{4}-\d{6}-\d{2}|\d{4}-\d{6}-\d{2}|"
                      r"jRCT\w{10,}|ChiCTR[-\w]{6,}|JapicCTI-\d{6}|UMIN\d{9}|CTRI/\d{4}/\d+/\d+")
MAX_LLM = 30                                                   # candidatos por card enviados ao curator
RADIO = re.compile(r"177\s*Lu|225\s*Ac|223\s*Ra|131\s*I\b|90\s*Y\b|212\s*Pb|227\s*Th|161\s*Tb|\bLu-|\bAc-|\bRa-|"
                   r"I-131|MIBG|rádio|radio(?!terapia)|PSMA-617|DOTATATE", re.I)


# ── cards e o que o Database já tem ─────────────────────────────────────────────────────────────────────────────
def cards() -> dict:
    return {c["uid"]: c for c in L.ler_data_js(L.DATA_JS.read_text(encoding="utf-8"))[1]["studies"]}


def secundarios() -> list[dict]:
    txt = (L.SITE / "assets" / "js" / "secondary-cards.js").read_text(encoding="utf-8")
    ini = txt.index("[", txt.index("window.THERA_SECONDARY"))
    return json.JSONDecoder().raw_decode(txt, ini)[0]


def _doi(v) -> str | None:
    m = re.search(r"10\.\d{4,9}/[^\s\"'<>,;]+", str(v or ""))
    return m.group(0).rstrip(".)").lower() if m else None


def conhecidos(card: dict, secs: list[dict]) -> dict:
    """PMIDs e DOIs que o Database já representa para este card (card + secundários dele)."""
    texto = json.dumps(card, ensure_ascii=False)
    pmids = set(re.findall(r"pubmed\.ncbi\.nlm\.nih\.gov/(\d+)", texto)) | set(re.findall(r"PMID[:\s]*(\d{6,9})", texto))
    pmids |= set(re.findall(r'"pmid:(\d+)"', texto))
    dois = {d.lower().rstrip(".)") for d in re.findall(r"10\.\d{4,9}/[^\s\"'<>,;]+", texto)}
    origem = {p: "card" for p in pmids} | {d: "card" for d in dois}
    for s in secs:
        if s.get("parentUid") != card["uid"]:
            continue
        for p in filter(None, [s.get("pmid"), *re.findall(r"pubmed\.ncbi\.nlm\.nih\.gov/(\d+)", str(s.get("sourceUrl")))]):
            pmids.add(str(p))
            origem.setdefault(str(p), f"secundário {s['id']}")
        d = _doi(s.get("doi"))
        if d:
            dois.add(d)
            origem.setdefault(d, f"secundário {s['id']}")
    return {"pmids": pmids, "dois": dois, "origem": origem}


def registros(card: dict) -> list[str]:
    ids = []
    for campo in ("nct", "nct_url", "estudo", "ref", "desenho"):
        for m in REGISTRO.findall(str(card.get(campo) or "")):
            m = re.sub(r"^EudraCT[ :]*", "", m)
            if m not in ids:
                ids.append(m)
    return ids[:4]


# ── fontes de descoberta (cache em state/cache, como o resto do db_v2) ──────────────────────────────────────────
def pubmed_si(rid: str, rede: bool) -> list[str]:
    termo = urllib.parse.quote(f"{rid}[si]")
    raw, _ = S._get(f"{S.EUTILS}esearch.fcgi?db=pubmed&retmode=json&retmax=300&term={termo}", rede,
                    S.CACHE / "esearch_si" / f"{re.sub(r'[^\w.-]', '_', rid)}.json")
    return json.loads(raw)["esearchresult"]["idlist"] if raw else []


def europepmc(rid: str, rede: bool) -> list[dict]:
    q = urllib.parse.quote(f'(TITLE:"{rid}" OR ABSTRACT:"{rid}")')
    raw, _ = S._get(f"{S.EUROPEPMC}search?query={q}&format=json&resultType=core&pageSize=200", rede,
                    S.CACHE / "epmc_search" / f"{re.sub(r'[^\w.-]', '_', rid)}.json")
    if not raw:
        return []
    out = []
    for r in json.loads(raw).get("resultList", {}).get("result", []):
        out.append({"pmid": r.get("pmid"), "doi": (r.get("doi") or "").lower() or None, "epmc_id": r.get("id"),
                    "source": r.get("source"), "title": r.get("title"), "pubdate": r.get("firstPublicationDate"),
                    "journal": (r.get("journalInfo") or {}).get("journal", {}).get("title"),
                    "pubtype": (r.get("pubTypeList") or {}).get("pubType", []), "abstract": r.get("abstractText")})
    return out


def ctgov_refs(rid: str, rede: bool) -> list[dict]:
    if not rid.startswith("NCT"):
        return []
    rec = S.ctgov(rid, rede)
    refs = (rec or {}).get("protocolSection", {}).get("referencesModule", {}).get("references") or []
    return [{"pmid": str(r["pmid"]), "type": r.get("type")} for r in refs if r.get("pmid")]


def _esummary_doi(m: dict) -> str | None:
    return next(((a.get("value") or "").lower() for a in m.get("articleids", []) if a.get("idtype") == "doi"), None)


# ── estágio 0 ───────────────────────────────────────────────────────────────────────────────────────────────────
def triagem(brutos: list[dict], conhec: dict) -> tuple[list[dict], list[dict]]:
    """Funde por PMID/DOI e elimina deterministicamente. Retorna (candidatos, eliminados)."""
    por_chave, ordem = {}, []
    for b in brutos:
        chaves = [k for k in (f"pmid:{b['pmid']}" if b.get("pmid") else None,
                              f"doi:{b['doi']}" if b.get("doi") else None) if k]
        alvo = next((por_chave[k] for k in chaves if k in por_chave), None)
        if alvo is None:
            alvo = dict(b, via=[b["via"]])
            ordem.append(alvo)
        else:
            alvo["via"] = sorted(set(alvo["via"]) | {b["via"]})
            for k, v in b.items():
                if k != "via" and not alvo.get(k) and v:
                    alvo[k] = v
        for k in [f"pmid:{alvo['pmid']}" if alvo.get("pmid") else None, f"doi:{alvo['doi']}" if alvo.get("doi") else None]:
            if k:
                por_chave[k] = alvo
    cand, elim = [], []
    for c in ordem:
        tipos = set(c.get("pubtype") or [])
        titulo = str(c.get("title") or "")
        ja = (c.get("pmid") and c["pmid"] in conhec["pmids"]) or (c.get("doi") and c["doi"] in conhec["dois"])
        if ja:
            elim.append({**c, "eliminado": "ja_cadastrada",
                         "detalhe": conhec["origem"].get(c.get("pmid")) or conhec["origem"].get(c.get("doi"))})
        elif tipos & ERRATA or re.match(r"^\s*(correction|erratum|corrigendum)\b", titulo, re.I):
            elim.append({**c, "eliminado": "errata"})
        elif not (c.get("pmid") or c.get("doi")):
            elim.append({**c, "eliminado": "sem_identificador"})
        else:
            cand.append(c)
    return cand, elim


def pre_acao(c: dict) -> tuple[str | None, str | None, str | None]:
    """(ação, motivo, relação) quando o tipo da publicação já decide, sem LLM. Relação None = não se aplica."""
    tipos = {str(x).lower() for x in (c.get("pubtype") or [])}
    titulo = str(c.get("title") or "")
    if {"retraction of publication", "retracted publication", "expression of concern"} & tipos or \
            re.match(r"^\s*(retraction|retracted|expression of concern)", titulo, re.I):
        return "HUMAN_REVIEW", "retratação/expression of concern: impacto editorial exige humano", None
    if REGULATORIO.search(titulo):              # regulatório nunca é descartado: segue para o curator
        return None, None, None
    if "clinical trial protocol" in tipos or PROTOCOLO.search(titulo):
        return "STORE_SOURCE", "protocolo do próprio estudo (vínculo pelo registro): fonte de desenho, sem resultados", "PROTOCOL"
    if LEIGO.search(titulo) or "patient education handout" in tipos:
        return "NO_ACTION", "resumo em linguagem leiga: sem dado original do estudo", None
    if PRECLINICO.search(titulo) and not CLINICO_NO_TITULO.search(titulo):     # título que anuncia dado clínico segue
        return "NO_ACTION", "pré-clínico/in vitro/animal: sem dado clínico do estudo", None
    if ECONOMICO.search(titulo):
        return "NO_ACTION", "custo-efetividade/modelagem econômica: sem dado original do estudo", None
    if "case reports" in tipos or re.search(r"\bcase (report|series)\b|\ba case of\b", titulo, re.I):
        return "NO_ACTION", "relato de caso: sem dado original do estudo", None
    if tipos & SEM_DADO_ORIGINAL and not tipos & TIPOS_ENSAIO:
        return "NO_ACTION", f"sem dado original do estudo ({', '.join(sorted(tipos & SEM_DADO_ORIGINAL))})", None
    if re.search(r"\b(guideline|guidelines|consensus statement|recommendations? (from|of) the)\b", titulo, re.I) and \
            not tipos & TIPOS_ENSAIO:
        return "NO_ACTION", "diretriz/consenso: sem dado original do estudo", None
    if c.get("source") == "PPR" or "preprint" in tipos:
        return "WATCH", "preprint: resultado não revisado por pares", None
    return None, None, None


def outro_ensaio_citado(c: dict, rids: list[str]) -> bool:
    """Publicação de OUTRO ensaio que só aparece porque o registro do card a cita, ou cujo próprio DataBank declara
    outro registro e não o do card. Não vale para quem o PubMed liga ao registro do card ([si]) ou o CT.gov lista
    como resultado."""
    vias = set(c.get("via") or [])
    if any(v.startswith("pubmed_si:") for v in vias) or c.get("ctgov_type") in ("RESULT", "DERIVED"):
        return False
    if vias and all(v.startswith("ctgov_ref:") for v in vias) and c.get("ctgov_type") == "BACKGROUND":
        return True
    db = set(c.get("databank") or [])
    return bool(db) and not db & set(rids)


PLATAFORMA = re.compile(r"platform|multi[- ]arm|multi[- ]?stage|\bMAMS\b|umbrella|master protocol|plataforma", re.I)


def sinal_pooled(texto: str, databank: list[str] | None = None, rids: list[str] | None = None,
                 card_plataforma: bool = False) -> str | None:
    """Pooled SÓ com frase explícita de agregação de vários estudos/coortes no texto. Outro registro no DataBank,
    estudo de plataforma, vários braços ou referências cruzadas NÃO bastam sozinhos. Comparações de uma plataforma
    (card de plataforma ou texto que a descreve) sem nenhum registro além do(s) do card não são multi-estudo."""
    m = None
    separado = bool(SEPARADO.search(texto or ""))
    for frase in re.split(r"(?<=[.;])\s+", texto or ""):         # frase a frase
        if ANTERIOR.search(frase):                                # trabalho anterior citado não é esta publicação
            continue
        if MESMO_ENSAIO.search(frase) and not re.search(r"\b(trials|studies)\b", frase, re.I):
            continue                                              # partes/braços de um mesmo ensaio
        m = POOLED.search(frase) or (None if separado else (POOLED_CONTAGEM.search(frase) or POOLED_ATRAVES.search(frase)))
        if m:
            break
    if not m:
        return None
    registros_citados = set(REGISTRO.findall(texto or "")) | set(databank or [])
    if rids is not None and (card_plataforma or PLATAFORMA.search(texto or "")):
        prefixos = {re.match(r"[A-Za-z]*", r).group(0) for r in rids}      # o mesmo estudo pode ter NCT e ISRCTN
        mesmos_tipos = {r for r in registros_citados if re.match(r"[A-Za-z]*", r).group(0) in prefixos}
        if mesmos_tipos <= set(rids):
            return None
    return f"texto: '{m.group(0)}'"


def coletar(uid: str, rede: bool = False) -> dict:
    card = cards()[uid]
    conhec = conhecidos(card, secundarios())
    rids = registros(card)
    pasta = DISC / uid
    fdir = pasta / "fontes"
    fdir.mkdir(parents=True, exist_ok=True)
    for f in fdir.glob("*.txt"):
        f.unlink()
    brutos = []
    for rid in rids:
        brutos += [{"pmid": p, "via": f"pubmed_si:{rid}"} for p in pubmed_si(rid, rede)]
        brutos += [{"pmid": r["pmid"], "via": f"ctgov_ref:{rid}", "ctgov_type": r["type"]} for r in ctgov_refs(rid, rede)]
        brutos += [{**r, "via": f"europepmc:{rid}"} for r in europepmc(rid, rede)]
    pmids = sorted({b["pmid"] for b in brutos if b.get("pmid")}, key=int)
    meta = S.pubmed_esummary(pmids, rede) if pmids else {}
    for b in brutos:
        m = meta.get(b.get("pmid") or "")
        if m:
            b.update({"title": m.get("title"), "journal": m.get("source"), "pubdate": m.get("sortpubdate", "")[:10]
                      or m.get("pubdate"), "pubtype": m.get("pubtype", []), "doi": _esummary_doi(m) or b.get("doi")})
    cand, elim = triagem(brutos, conhec)
    pmid_rep = B.pmid_do_card(card)
    fontes = []

    def fonte(source_id, source_type, level, pars, extra):
        if pars:
            p = S.gravar_fonte(fdir, source_id, pars)
            fontes.append({"source_id": source_id, "source_type": source_type, "text_level": level,
                           "path": f"fontes/{p.name}", "paragraphs": len(pars), **extra})
    # publicação representada (o que o card mostra hoje)
    rep = S.pubmed_efetch(pmid_rep, rede) if pmid_rep else {}
    rep_data = ((S.pubmed_esummary([pmid_rep], rede).get(pmid_rep) or {}).get("sortpubdate", "")[:10]
                if pmid_rep else "") or None
    if rep:
        fonte(f"pmid:{pmid_rep}:abstract", "pubmed_abstract", "abstract",
              [("Title", rep["title"])] + [(f"Abstract > {s}", t) for s, t in rep["abstract"]],
              {"pmid": pmid_rep, "doi": rep.get("doi"), "retrieved_at": rep["retrieved_at"], "role": "represented"})
    # candidatos: pré-ação determinística ou fila do LLM
    cand.sort(key=lambda c: str(c.get("pubdate") or ""), reverse=True)
    for c in cand:
        c["candidate_id"] = f"pmid:{c['pmid']}" if c.get("pmid") else f"doi:{c['doi']}"
        c["pre_action"], c["pre_reason"], c["pre_relation"] = pre_acao(c)
        if not c["pre_action"] and outro_ensaio_citado(c, rids):
            c["pre_action"], c["pre_reason"], c["pre_relation"] = (
                "NO_ACTION", "outro ensaio apenas citado pelo registro (referência BACKGROUND do CT.gov)", "UNRELATED")
        c["in_llm"] = False
        c["regulatory"] = bool(REGULATORIO.search(str(c.get("title") or "")))
        c["older_than_represented"] = bool(rep_data and c.get("pubdate") and
                                           str(c["pubdate"]).replace("/", "-")[:10] < rep_data.replace("/", "-"))
    fila = [c for c in cand if not c["pre_action"]]
    for c in fila[:MAX_LLM]:
        if c.get("pmid"):
            e = S.pubmed_efetch(c["pmid"], rede)
            pars = [("Title", e["title"])] + [(f"Abstract > {s}", t) for s, t in e["abstract"]] if e else []
            if e:
                c["databank"] = e.get("databank_nct")
                if outro_ensaio_citado(c, rids) and not c.get("regulatory"):
                    c["pre_action"], c["pre_reason"], c["pre_relation"] = (
                        "NO_ACTION", "outro ensaio: o DataBank da publicação lista outro registro e não o do card", "UNRELATED")
                    continue
        else:
            pars = [("Title", c.get("title") or "")] + ([("Abstract", re.sub(r"<[^>]+>", " ", c["abstract"]))]
                                                        if c.get("abstract") else [])
        c["pooled_signal"] = sinal_pooled(" ".join(t for _, t in pars), c.get("databank"), rids,
                                          bool(PLATAFORMA.search(json.dumps(card, ensure_ascii=False))))
        if len(pars) > 1:
            fonte(f"{c['candidate_id']}:abstract", "pubmed_abstract" if c.get("pmid") else "europepmc_abstract",
                  "abstract", pars, {"pmid": c.get("pmid"), "doi": c.get("doi"), "role": "candidate"})
            c["in_llm"] = True
        else:
            c["pre_action"], c["pre_reason"] = "WATCH", "sem resumo disponível: relação não avaliável pelo texto"
    for c in fila[MAX_LLM:]:
        c["pre_action"], c["pre_reason"] = "WATCH", f"excedeu {MAX_LLM} candidatos por card nesta rodada"
    for rid in rids:
        rec = S.ctgov(rid, rede) if rid.startswith("NCT") else None
        if rec:
            fonte(f"nct:{rid}:registry", "ctgov_record", "registry", S.ctgov_paragrafos(rec),
                  {"nct": rid, "retrieved_at": rec.get("_retrieved_at")})
    secs = [{"id": s["id"], "title": s["title"], "pmid": s.get("pmid"), "doi": s.get("doi"), "year": s.get("year"),
             "recordType": s.get("recordType")} for s in secundarios() if s.get("parentUid") == uid]
    pacote = {
        "schema": SCHEMA_PACOTE, "uid": uid, "gerado_em": datetime.date.today().isoformat(),
        "card": {k: card.get(k) for k in ("estudo", "acron", "fase", "desenho", "n", "indicacao", "comparador",
                                          "primario", "secundario", "ano_pub", "status", "ref", "resultado_chave")},
        "card_note": "o texto do card diz O QUE o card representa; não é evidência de si mesmo",
        "represented_publication": {"pmid": pmid_rep, "title": rep.get("title") if rep else None, "pubdate": rep_data},
        "pipeline_version": PIPELINE_VERSION,
        "registry_ids": rids, "known": {"pmids": sorted(conhec["pmids"]), "dois": sorted(conhec["dois"])},
        "existing_secondaries": secs,
        "counts": {"raw": len(brutos), "unique": len(cand) + len(elim), "eliminated": len(elim), "candidates": len(cand)},
        "eliminated": [{k: e.get(k) for k in ("pmid", "doi", "title", "eliminado", "detalhe", "via")} for e in elim],
        "candidates": [{k: c.get(k) for k in ("candidate_id", "pmid", "doi", "title", "journal", "pubdate", "pubtype",
                                              "via", "ctgov_type", "databank", "pre_action", "pre_reason", "pre_relation",
                                              "in_llm", "regulatory", "older_than_represented", "pooled_signal")}
                       for c in cand],
        "sources": fontes,
        "forbidden_sources_excluded": ["tracker.json", "Explorer", "conteúdo do TheraTrials como verdade", "memória do modelo"],
    }
    corpo = json.dumps(pacote, ensure_ascii=False, sort_keys=True)
    pacote["packet_sha256"] = hashlib.sha256(corpo.encode()).hexdigest()
    (pasta / "packet.json").write_text(json.dumps(pacote, ensure_ascii=False, indent=1), encoding="utf-8")
    return pacote


# ── amostra estratificada do piloto ─────────────────────────────────────────────────────────────────────────────
def estratos(c: dict, secs_por_uid: dict) -> dict:
    fase = str(c.get("fase") or "")
    ano = str(c.get("ano_pub") or "")[:4]
    return {"tumor": c.get("category_short"),
            "fase": "3" if re.search(r"fase\s*3|phase\s*3|fase\s*iii", fase, re.I) else
                    "2" if re.search(r"fase\s*(1/)?2|phase\s*2|fase\s*ii", fase, re.I) else "outro",
            "terapia": "radioligante" if RADIO.search(str(c.get("radiofarmaco") or "")) and not re.match(
                r"\s*(não|nao|n/a|—|-)", str(c.get("radiofarmaco") or ""), re.I) else "sistêmica/outra",
            "idade": "antigo(≤2019)" if ano.isdigit() and int(ano) <= 2019 else "recente(≥2020)" if ano.isdigit() else "sem ano",
            "secundarios": "com" if secs_por_uid.get(c["uid"]) else "sem",
            "registro": "com" if registros(c) else "sem"}


def amostra(n: int = 30) -> list[dict]:
    """Seleção determinística (sem sorteio): cobre cada valor de cada estrato ao menos uma vez e, depois, alterna
    tumores diferentes. Só cards com registro e publicação representada (a descoberta depende de ambos)."""
    cs = cards()
    secs_por_uid = collections.Counter(s.get("parentUid") for s in secundarios())
    elegiveis = [c for c in cs.values() if registros(c) and B.pmid_do_card(c)
                 and not str(c.get("status", "")).startswith("Em revisão")]
    info = {c["uid"]: estratos(c, secs_por_uid) for c in elegiveis}
    chave = lambda c: hashlib.sha256(c["uid"].encode()).hexdigest()  # noqa: E731 — ordem estável, sem viés alfabético
    escolhidos, motivos = [], {}
    # 1) todos os cards com secundários (maior chance de publicações derivadas) — limitados a 6
    for c in sorted([c for c in elegiveis if secs_por_uid.get(c["uid"])], key=chave)[:6]:
        escolhidos.append(c["uid"]); motivos[c["uid"]] = "tem secundários cadastrados"
    # 2) cobertura de estratos
    for dim in ("fase", "terapia", "idade"):
        for val in sorted({i[dim] for i in info.values()}):
            if any(info[u][dim] == val for u in escolhidos):
                continue
            c = next((c for c in sorted(elegiveis, key=chave) if info[c["uid"]][dim] == val and c["uid"] not in escolhidos), None)
            if c:
                escolhidos.append(c["uid"]); motivos[c["uid"]] = f"cobre {dim}={val}"
    # 3) completar com tumores ainda não cobertos, alternando antigo/recente
    alvo_idade = ["antigo(≤2019)", "recente(≥2020)"]
    k = 0
    for c in sorted(elegiveis, key=chave):
        if len(escolhidos) >= n:
            break
        u = c["uid"]
        if u in escolhidos or any(info[x]["tumor"] == info[u]["tumor"] for x in escolhidos):
            continue
        if info[u]["idade"] != alvo_idade[k % 2]:
            continue
        escolhidos.append(u); motivos[u] = f"tumor novo na amostra ({info[u]['tumor']}), {info[u]['idade']}"
        k += 1
    for c in sorted(elegiveis, key=chave):           # se faltar, completa por tumor novo sem alternância
        if len(escolhidos) >= n:
            break
        u = c["uid"]
        if u not in escolhidos and not any(info[x]["tumor"] == info[u]["tumor"] for x in escolhidos):
            escolhidos.append(u); motivos[u] = f"tumor novo na amostra ({info[u]['tumor']})"
    out = [{"uid": u, "estudo": cs[u]["estudo"], "ano_pub": cs[u].get("ano_pub"), **info[u], "motivo": motivos[u]}
           for u in escolhidos[:n]]
    DISC.mkdir(parents=True, exist_ok=True)
    (DISC / "piloto.json").write_text(json.dumps({"n": len(out), "criterio": amostra.__doc__, "cards": out},
                                                 ensure_ascii=False, indent=1), encoding="utf-8")
    return out


# ── estágio 1: tarefa do curator e entrada do verifier ──────────────────────────────────────────────────────────
def tarefa(uid: str) -> str:
    p = json.loads((DISC / uid / "packet.json").read_text())
    ids = [c["candidate_id"] for c in p["candidates"] if c["in_llm"]]
    return (f"MODO DISCOVERY. Pacote: {DISC / uid / 'packet.json'} · fontes em {DISC / uid / 'fontes'}\n"
            f"Schema de saída: {AQUI / 'schemas' / 'discovery.schema.json'}\n"
            f"uid: {uid} · packet_sha256: {p['packet_sha256']}\n"
            f"Classifique TODOS e SOMENTE estes candidatos ({len(ids)}): {', '.join(ids)}\n")


def entrada(uid: str) -> pathlib.Path:
    cur = json.loads((DISC / uid / "curator.json").read_text())
    visivel = ["candidate_id", "relation", "action", "candidate_signature", "evidence"]
    ent = {"uid": uid, "packet": str(DISC / uid / "packet.json"), "fontes": str(DISC / uid / "fontes"),
           "curator_sha256": cur["_sha256"], "represented_signature": cur.get("represented_signature"),
           "candidates": [{k: c.get(k) for k in visivel} for c in cur.get("candidates", [])]}
    alvo = DISC / uid / "verifier_input.json"
    alvo.write_text(json.dumps(ent, ensure_ascii=False, indent=1), encoding="utf-8")
    return alvo


def tarefa_verifier(uid: str) -> str:
    alvo = entrada(uid)
    sha = json.loads(alvo.read_text())["curator_sha256"]
    return (f"MODO DISCOVERY. Entrada: {alvo}\nSchema de saída: {AQUI / 'schemas' / 'discovery_verification.schema.json'}\n"
            f"uid: {uid} · curator_sha256: {sha}\nAvalie TODOS os candidatos da entrada.\n")


# ── estágio 2: checagens determinísticas e fusão ────────────────────────────────────────────────────────────────
def _json_da_resposta(txt: str) -> dict:
    txt = txt.strip()
    m = re.search(r"\{.*\}", txt, re.S)
    return json.loads(m.group(0) if m else txt)


def conferir(uid: str, cur: dict) -> dict:
    """Checagens determinísticas por candidato: evidência literal, números da assinatura nos trechos citados,
    relação recalculada pela assinatura e coerência relação × ação. {candidate_id: {verdict, achados}}"""
    p = json.loads((DISC / uid / "packet.json").read_text())
    pasta = DISC / uid
    fontes = {f["source_id"]: f for f in p["sources"]}
    esperados = {c["candidate_id"] for c in p["candidates"] if c["in_llm"]}
    info = {c["candidate_id"]: c for c in p["candidates"]}

    def texto_fonte(sid):
        f = fontes.get(sid)
        return " ".join(S.ler_paragrafos(pasta / f["path"]).values()) if f else ""
    card_plat = bool(PLATAFORMA.search(json.dumps(p.get("card") or {}, ensure_ascii=False)))
    rep_sid = next((f["source_id"] for f in p["sources"] if f.get("role") == "represented"), None)
    card_txt = " ".join(str((p.get("card") or {}).get(k) or "") for k in ("estudo", "acron", "desenho"))
    card_pooled = bool((rep_sid and POOLED.search(texto_fonte(rep_sid))) or CARD_INTEGRADO.search(card_txt))
    card_full = " ".join(str((p.get("card") or {}).get(k) or "") for k in ("estudo", "acron", "indicacao", "desenho"))
    escopo = " ".join(str((p.get("card") or {}).get(k) or "") for k in ("estudo", "acron", "indicacao"))
    estudo_txt = " ".join(str((p.get("card") or {}).get(k) or "") for k in ("estudo", "acron"))
    coorte_especifica = bool(re.search(r"cohort|coorte", estudo_txt, re.I) and grupos_tumor(estudo_txt))
    tumores_card = grupos_tumor(card_full) if coorte_especifica or not TUMOR_AGNOSTICO.search(escopo) else set()
    rep = cur.get("represented_signature") or {}
    out = {}
    vistos = set()
    for c in cur.get("candidates", []):
        cid = c.get("candidate_id")
        ach = []
        add = lambda code, v, d: ach.append({"code": code, "verdict": v, "detail": d})  # noqa: E731
        if cid not in esperados:
            add("CANDIDATE_UNKNOWN", "FAIL", "candidato fora da fila do pacote")
        vistos.add(cid)
        rel, acao = c.get("relation"), c.get("action")
        if rel not in RELACOES:
            add("RELATION_ENUM", "FAIL", f"relação inválida {rel!r}")
        if acao not in ACOES:
            add("ACTION_ENUM", "FAIL", f"ação inválida {acao!r}")
        item = {"evidence": c.get("evidence") or [], "change_kind": "none", "value_origin": "reported"}
        if not item["evidence"]:
            add("NO_EVIDENCE", "UNSUPPORTED", "sem trecho literal")
        else:
            for a in K.conferir_item(item, fontes, pasta):
                if a["verdict"] != "PASS":
                    ach.append(a)
            if not any((e.get("source_id") or "").startswith(cid) for e in item["evidence"]):
                add("EVIDENCE_NOT_FROM_CANDIDATE", "UNSUPPORTED", "nenhum trecho vem da própria publicação candidata")
        sig = c.get("candidate_signature") or {}
        pc = info.get(cid, {})
        # corte/publicação anterior à representada: nunca update; mesma análise vira PRIOR_SUPERSEDED
        if pc.get("older_than_represented"):
            if rel in ("SAME_ANALYSIS_UPDATE", "LONG_TERM_FOLLOWUP") or acao == "UPDATE_CARD":
                add("PRIOR_AS_UPDATE", "FAIL", "publicação anterior à representada tratada como atualização")
            if rel == "SAME_ANALYSIS":
                c["_temporal_marker"] = "PRIOR_SUPERSEDED"
                if acao not in ("STORE_SOURCE", "HUMAN_REVIEW"):
                    add("PRIOR_SUPERSEDED_ACTION", "UNSUPPORTED", f"corte anterior superado pede STORE_SOURCE, não {acao}")
        elif c.get("temporal_marker") == "PRIOR_SUPERSEDED":
            add("PRIOR_MARKER_UNSUPPORTED", "UNSUPPORTED", "PRIOR_SUPERSEDED sem publicação anterior à representada")
        # protocolo do próprio estudo: vínculo preservado, nunca UNRELATED
        protocolo = PROTOCOLO.search(str(pc.get("title") or "")) or sig.get("publication_role") == "protocol"
        if protocolo and rel == "UNRELATED":
            add("PROTOCOL_AS_UNRELATED", "FAIL", "protocolo do próprio estudo classificado como UNRELATED")
        # análise de vários estudos: nunca secundária automática de um único card. O sinal é recalculado aqui, no
        # texto-fonte inteiro do candidato (não só no trecho citado), com a mesma regra da coleta.
        sinal = sinal_pooled(texto_fonte(f"{cid}:abstract"), pc.get("databank"), p.get("registry_ids") or [], card_plat)
        c["_pooled_signal"] = sinal
        if rel == "POOLED_ANALYSIS" and not sinal:
            add("POOLED_WITHOUT_TEXT", "UNSUPPORTED", "POOLED_ANALYSIS sem frase explícita de agregação de estudos na fonte")
        # card de basket/integrado: candidato que só fala de OUTROS tumores não é deste card (coorte não relacionada)
        if card_pooled and tumores_card and rel not in ("UNRELATED",) and acao != "NO_ACTION":
            tc = grupos_tumor(f"{pc.get('title') or ''} {texto_fonte(f'{cid}:abstract')}")
            if len(tc) == 1 and not tc & tumores_card:           # um único OUTRO tumor; multi-tumor = análise-mãe do basket
                add("BASKET_OTHER_COHORT", "UNSUPPORTED", f"card de basket ({', '.join(sorted(tumores_card))}) × "
                    f"candidato sobre {', '.join(sorted(tc))}: coorte não relacionada ao card")
        if (sinal or rel == "POOLED_ANALYSIS") and not card_pooled:  # card integrado: subgrupo do mesmo conjunto vale
            if acao == "ADD_SECONDARY":
                add("POOLED_ADD_SECONDARY", "FAIL", f"pooled ({sinal or 'declarado'}): ADD_SECONDARY bloqueado")
            if rel in ("SECONDARY_ANALYSIS", "SUBGROUP"):
                add("POOLED_AS_SECONDARY", "UNSUPPORTED", f"indício de pooled ({sinal}): "
                    "não é secundária de um único estudo sem revisão humana")
        if rel in ACOES_DA_RELACAO and acao in ACOES and acao not in ACOES_DA_RELACAO[rel]:
            add("ACTION_INCOMPATIBLE", "FAIL", f"ação {acao} incompatível com relação {rel}")
        comp = {k: (v or {}).get("status") for k, v in (c.get("comparison") or {}).items()}
        if (acao == "UPDATE_CARD" or rel in ("SAME_ANALYSIS_UPDATE", "SAME_ANALYSIS")) and comp.get("analysis_set") == "undetermined":
            add("ANALYSIS_SET_UNDETERMINED", "PASS", "analysis set não informado na fonte: tolerado, não presumido ITT")
        for msg in coerencia(rel, acao, comp):          # "different" contradiz a relação; "undetermined" só não a sustenta
            add("RELATION_COMPARISON_MISMATCH", "UNSUPPORTED" if "=different" not in msg and "iguais" not in msg
                and "mesmo timepoint" not in msg and "população ou braços diferentes" not in msg else "CONFLICT", msg)
        if rep and sig and rel != "UNRELATED":          # só informativo: texto livre das assinaturas diverge por
            det, motivo = G.relacao(rep, sig)            # redação (idioma, detalhe) e não sustenta CONFLICT sozinho
            c["_relacao_assinatura"] = [DA_ASSINATURA.get(det, det), motivo]
        out[cid] = {"verdict": K.pior([a["verdict"] for a in ach] or ["PASS"]), "achados": ach}
    for cid in esperados - vistos:
        out[cid] = {"verdict": "UNSUPPORTED", "achados": [{"code": "NOT_CLASSIFIED", "verdict": "UNSUPPORTED",
                                                          "detail": "curator não classificou o candidato"}]}
    return out


def sanear_assinatura(c: dict) -> None:
    """n e seguimento da assinatura só ficam se estiverem num trecho literal citado do candidato. Sem trecho, o valor
    sai (None) e o campo é marcado not_verified: nada de n inferido pelo LLM. O original fica anotado, não apagado."""
    sig = c.get("candidate_signature") or {}
    textos = " ".join(K.norm(e.get("snippet")) for e in c.get("evidence") or [])
    nv, orig = [], {}

    def ok(v):
        try:
            return K._num_no_texto(f"{float(v):g}", textos)
        except (TypeError, ValueError):
            return False
    for campo in ("sample_size", "follow_up_median_months"):
        v = sig.get(campo)
        if v not in (None, "") and not ok(v):
            orig[campo], sig[campo] = v, None
            nv.append(campo)
    for i, a in enumerate(sig.get("arms") or []):
        if a.get("n") not in (None, "") and not ok(a["n"]):
            orig[f"arms[{i}].n"], a["n"] = a["n"], None
            nv.append(f"arms[{i}].n")
    if nv:
        c["_not_verified"], c["_original_values"] = nv, orig


MESMA_ANALISE = ("population", "arms", "analysis_set", "endpoint", "comparison")
TOLERA_INDETERMINADO = {"analysis_set"}          # resumos raramente dizem "ITT"; ausência isolada não reprova


def _divergentes(comp: dict) -> list[str]:
    """Campos que impedem 'mesma análise'. analysis_set 'undetermined' é tolerado (continua undetermined, nunca
    'same'); 'different' em qualquer campo, ou 'undetermined' nos demais, impede."""
    return [k for k in MESMA_ANALISE if comp[k] != "same" and not (k in TOLERA_INDETERMINADO and comp[k] == "undetermined")]


def coerencia(rel: str, acao: str, comp: dict) -> list[str]:
    """Relação e ação × a tabela de comparação estruturada do próprio curator (same/different/undetermined).
    Determinístico: não interpreta texto livre; só exige que a relação declarada não contradiga a comparação."""
    erros = []
    faltam = [k for k in T.DISCOVERY_COMPARED if comp.get(k) not in ("same", "different", "undetermined")]
    if faltam:
        return [f"comparação incompleta: {', '.join(faltam)}"]
    if rel in ("SAME_ANALYSIS_UPDATE", "SAME_ANALYSIS"):
        dif = _divergentes(comp)
        if dif:
            erros.append(f"{rel} exige mesma análise, mas a comparação diz {', '.join(f'{k}={comp[k]}' for k in dif)}")
    if rel == "LONG_TERM_FOLLOWUP" and "different" in (comp["population"], comp["arms"]):
        erros.append("LONG_TERM_FOLLOWUP com população ou braços diferentes")
    if rel == "SUBGROUP" and comp["population"] == "same" and comp["publication_role"] == "same":
        erros.append("SUBGROUP com população e papel da publicação iguais")
    if rel == "NEW_COHORT" and comp["population"] == "same" and comp["arms"] == "same":
        erros.append("NEW_COHORT com população e braços iguais")
    if acao == "UPDATE_CARD":
        dif = _divergentes(comp)
        if dif:
            erros.append("UPDATE_CARD exige mesma população, braços, analysis set, endpoint e comparação; "
                         f"a comparação diz {', '.join(f'{k}={comp[k]}' for k in dif)}")
        if comp["timepoint"] == "same":
            erros.append("UPDATE_CARD com o mesmo timepoint/corte: não há dado mais maduro")
    return erros


def ingerir(papel: str, uid: str, arquivo: str) -> dict:
    d = _json_da_resposta(pathlib.Path(arquivo).read_text(encoding="utf-8"))
    sha = hashlib.sha256(json.dumps(d, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    p = json.loads((DISC / uid / "packet.json").read_text())
    if papel == "curator":
        erros = []
        if d.get("schema") != SCHEMA_CURATOR:
            erros.append(f"schema {d.get('schema')!r}")
        if d.get("packet_sha256") != p["packet_sha256"]:
            erros.append("packet_sha256 não confere")
        d["_sha256"], d["_erros"] = sha, erros
        for c in d.get("candidates", []):
            sanear_assinatura(c)
        d["_deterministico"] = conferir(uid, d)
        (DISC / uid / "curator.json").write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    else:
        cur = json.loads((DISC / uid / "curator.json").read_text())
        erros = [] if d.get("curator_sha256") == cur["_sha256"] else ["curator_sha256 não confere"]
        for c in d.get("candidates", []):
            if any(k in c for k in ("proposed_relation", "corrected_action", "corrected_value")):
                erros.append(f"{c.get('candidate_id')}: verifier reescreveu (proibido)")
        d["_sha256"], d["_erros"] = sha, erros
        (DISC / uid / "verifier.json").write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    return d


def fila_por_card(linhas: list[dict]) -> dict:
    """Unidade de revisão humana = o CARD. Por card, no máximo três pacotes, cada um UMA decisão:
      UPDATE_CARD (todas as publicações que sustentam a atualização), ADD_SECONDARY (propostas PASS, aprovar o
      conjunto ou itens), HUMAN_REVIEW (ação HUMAN_REVIEW + qualquer item sem PASS).
    STORE_SOURCE + PASS → registro automático de fonte (sem decisão). NO_ACTION/WATCH + PASS → nada.
    Nenhum pacote aplica conteúdo clínico: é só a fila de revisão."""
    compacto = lambda x: {k: x.get(k) for k in ("pmid", "doi", "title", "date", "relation", "action",  # noqa: E731
                                                "final_verdict", "temporal_marker", "verifier_reason")}
    cards_, fontes_auto = {}, []
    for x in linhas:
        ok = x["final_verdict"] == "PASS"
        if x["action"] == "STORE_SOURCE" and ok:
            fontes_auto.append({"uid": x["uid"], **compacto(x)})
            continue
        if x["action"] in ("NO_ACTION", "WATCH") and ok:
            continue
        pac = "UPDATE_CARD" if x["action"] == "UPDATE_CARD" else \
              "ADD_SECONDARY" if x["action"] == "ADD_SECONDARY" and ok else "HUMAN_REVIEW"
        cards_.setdefault(x["uid"], {"trial": x["trial"], "pacotes": {}})["pacotes"].setdefault(pac, []).append(compacto(x))
    decisoes = sum(len(c["pacotes"]) for c in cards_.values())
    return {"cards": cards_, "fontes_auto_registradas": fontes_auto,
            "resumo": {"cards_em_revisao": len(cards_), "decisoes_humanas": decisoes,
                       "publicacoes_em_revisao": sum(len(v) for c in cards_.values() for v in c["pacotes"].values()),
                       "fontes_auto": len(fontes_auto),
                       "pacotes": dict(collections.Counter(p for c in cards_.values() for p in c["pacotes"]))}}


def consolidar(uids: list[str], saida: str = "relatorio.json") -> dict:
    linhas, cards_ok = [], []
    for uid in uids:
        pasta = DISC / uid
        p = json.loads((pasta / "packet.json").read_text())
        cur = json.loads((pasta / "curator.json").read_text()) if (pasta / "curator.json").exists() else {}
        ver = json.loads((pasta / "verifier.json").read_text()) if (pasta / "verifier.json").exists() else {}
        det = cur.get("_deterministico", {})
        cmap = {c["candidate_id"]: c for c in cur.get("candidates", [])}
        vmap = {c["candidate_id"]: c for c in ver.get("candidates", [])}
        cards_ok.append(uid)
        for c in p["candidates"]:
            cid = c["candidate_id"]
            base = {"uid": uid, "trial": p["card"]["estudo"], "registry": p["registry_ids"], "pmid": c.get("pmid"),
                    "doi": c.get("doi"), "title": c.get("title"), "date": c.get("pubdate"), "via": c.get("via")}
            if not c["in_llm"]:
                linhas.append({**base, "relation": c.get("pre_relation"), "action": c["pre_action"], "origin": "deterministic",
                               "reason": c["pre_reason"], "curator_verdict": None, "verifier_verdict": None,
                               "final_verdict": "PASS", "signature": None, "evidence": [],
                               "human_review": c["pre_action"] == "HUMAN_REVIEW"})
                continue
            cc, vv, dd = cmap.get(cid, {}), vmap.get(cid, {}), det.get(cid, {"verdict": "UNSUPPORTED", "achados": []})
            vv_ver = vv.get("verdict") or ("UNSUPPORTED" if cc else None)
            if cur.get("_erros") or ver.get("_erros"):
                vv_ver = "FAIL"
            final = K.pior([dd["verdict"], vv_ver or "UNSUPPORTED"])
            acao = cc.get("action")
            humano = final != "PASS" or acao in ("UPDATE_CARD", "ADD_SECONDARY", "HUMAN_REVIEW") or \
                cc.get("relation") == "UNDETERMINED"
            linhas.append({**base, "relation": cc.get("relation"), "action": acao, "origin": "llm",
                           "reason": cc.get("reason"), "comparison": cc.get("comparison"),
                           "signature": {"represented": cur.get("represented_signature"), "candidate": cc.get("candidate_signature")},
                           "relation_by_signature": cc.get("_relacao_assinatura"),
                           "temporal_marker": cc.get("_temporal_marker") or cc.get("temporal_marker"),
                           "not_verified": cc.get("_not_verified"), "pooled_signal": cc.get("_pooled_signal"),
                           "evidence": cc.get("evidence", [])[:2], "curator_verdict": dd["verdict"],
                           "curator_checks": [a for a in dd["achados"]],
                           "verifier_verdict": vv_ver, "verifier_reason": vv.get("reason"),
                           "final_verdict": final, "human_review": humano})
    rel = collections.Counter(x["relation"] or "(determinístico)" for x in linhas)
    aco = collections.Counter(x["action"] for x in linhas)
    total_raw = sum(json.loads((DISC / u / "packet.json").read_text())["counts"]["raw"] for u in uids)
    total_unq = sum(json.loads((DISC / u / "packet.json").read_text())["counts"]["unique"] for u in uids)
    elim = collections.Counter(e["eliminado"] for u in uids for e in json.loads((DISC / u / "packet.json").read_text())["eliminated"])
    rel_final = {"gerado_em": datetime.date.today().isoformat(), "cards": len(cards_ok), "raw": total_raw,
                 "unique": total_unq, "eliminated": dict(elim), "candidates": len(linhas),
                 "by_relation": dict(rel), "by_action": dict(aco),
                 "by_final_verdict": dict(collections.Counter(x["final_verdict"] for x in linhas)),
                 "human_review": sum(x["human_review"] for x in linhas), "rows": linhas}
    fila = fila_por_card(linhas)
    rel_final["human_queue_by_card"] = fila["resumo"]
    rel_final["human_decisions_per_card"] = round(fila["resumo"]["decisoes_humanas"] / max(len(cards_ok), 1), 2)
    (DISC / saida).write_text(json.dumps(rel_final, ensure_ascii=False, indent=1), encoding="utf-8")
    (DISC / saida.replace("relatorio", "fila_humana")).write_text(json.dumps(fila, ensure_ascii=False, indent=1),
                                                                     encoding="utf-8")
    return rel_final


# ── lote retomável ──────────────────────────────────────────────────────────────────────────────────────────────
ETAPAS = ("coleta", "curator", "verifier")
ARQUIVOS_PIPELINE = ["discovery.py", "checks.py", "signature.py", "sources.py", "agent_types.py",
                     "schemas/discovery.schema.json", "schemas/discovery_verification.schema.json",
                     "../../../.claude/agents/database-curator.md", "../../../.claude/agents/database-verifier.md"]


def _sha(o) -> str:
    b = o if isinstance(o, bytes) else json.dumps(o, ensure_ascii=False, sort_keys=True, default=str).encode()
    return hashlib.sha256(b).hexdigest()


def configuracao() -> dict:
    return {"max_llm": MAX_LLM, "fontes": ["pubmed_si", "ctgov_ref", "europepmc"],
            "sem_dado_original": sorted(SEM_DADO_ORIGINAL), "tipos_ensaio": sorted(TIPOS_ENSAIO),
            "regulatorio": REGULATORIO.pattern, "protocolo": PROTOCOLO.pattern, "pooled": POOLED.pattern,
            "acoes_da_relacao": {k: sorted(v) for k, v in ACOES_DA_RELACAO.items()}}


def versao_pipeline() -> str:
    codigo = b"".join((AQUI / f).read_bytes() for f in ARQUIVOS_PIPELINE)
    return f"{PIPELINE_VERSION}+{_sha(codigo)[:16]}"


def compat(uid: str) -> dict:
    """O que precisa coincidir para reaproveitar trabalho: card, versão do pipeline e configuração."""
    return {"card_fingerprint": _sha(cards()[uid]), "pipeline_version": versao_pipeline(),
            "config_sha": _sha(configuracao())}


def carregar_estado(uid: str, comp: dict) -> tuple[dict, str]:
    try:
        e = json.loads((DISC / uid / "estado.json").read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {"uid": uid, "compat": comp, "etapas": {}}, "novo"
    if e.get("compat") != comp:
        mudou = [k for k in comp if (e.get("compat") or {}).get(k) != comp[k]]
        return {"uid": uid, "compat": comp, "etapas": {}, "invalidado_por": mudou}, "invalidado"
    return e, "compativel"


def gravar_estado(uid: str, e: dict) -> None:
    (DISC / uid).mkdir(parents=True, exist_ok=True)
    tmp = DISC / uid / "estado.json.tmp"
    tmp.write_text(json.dumps(e, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, DISC / uid / "estado.json")                 # gravação atômica: interrupção não corrompe o estado


def processar_card(uid: str, etapas: dict, trava_rede: threading.Lock) -> dict:
    comp = compat(uid)
    e, inicial = carregar_estado(uid, comp)
    feitas = []
    for nome in ETAPAS:
        if (e["etapas"].get(nome) or {}).get("ok"):
            continue
        if nome == "coleta":
            with trava_rede:                                        # NCBI/Europe PMC: coleta serializada
                res = etapas["coleta"](uid)
        else:
            p = json.loads((DISC / uid / "packet.json").read_text())
            res = etapas[nome](uid) if any(c["in_llm"] for c in p["candidates"]) else {"skipped": "sem candidato para o LLM"}
        e["etapas"][nome] = {"ok": True, "em": datetime.datetime.now().isoformat(timespec="seconds"), **(res or {})}
        gravar_estado(uid, e)                                       # progresso salvo a cada etapa
        feitas.append(nome)
    return {"uid": uid, "estado_inicial": inicial, "etapas_executadas": feitas,
            "invalidado_por": e.get("invalidado_por")}


def etapas_reais(rede: bool) -> dict:
    def coleta(u):
        return {"packet_sha256": coletar(u, rede)["packet_sha256"]}

    def agente(papel):
        def rodar(u):
            try:
                from . import run_agents as RA
            except ImportError:
                import run_agents as RA
            au = RA.executar(f"discovery_{papel}", u)
            d = ingerir(papel, u, str(RA.RAW / f"{u}.discovery_{papel}.json"))
            if d.get("_erros"):
                raise RuntimeError(f"{papel}: {d['_erros']}")
            return {"sha256": d["_sha256"], "custo_usd": au.get("custo_usd")}
        return rodar
    return {"coleta": coleta, "curator": agente("curator"), "verifier": agente("verifier")}


def executar_lote(uids: list[str], rede: bool = False, paralelo: int = 4, bloco: int = 50, etapas: dict | None = None) -> list[dict]:
    """Blocos de ~50 cards; dentro do bloco, `paralelo` cards ao mesmo tempo. Card com falha não derruba o lote e
    fica com as etapas concluídas salvas: a próxima execução retoma dele."""
    etapas = etapas or etapas_reais(rede)
    trava = threading.Lock()
    out = []
    for i in range(0, len(uids), bloco):
        with cf.ThreadPoolExecutor(max_workers=paralelo) as ex:
            futs = {ex.submit(processar_card, u, etapas, trava): u for u in uids[i:i + bloco]}
            for f in cf.as_completed(futs):
                try:
                    out.append(f.result())
                except Exception as x:                              # noqa: BLE001
                    out.append({"uid": futs[f], "erro": f"{type(x).__name__}: {x}"})
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["amostra", "coletar", "tarefa", "entrada", "ingerir", "consolidar", "lote"])
    ap.add_argument("--arquivo", help="JSON com lista 'cards' [{uid}] (lote/consolidar)")
    ap.add_argument("--bloco", type=int, default=50)
    ap.add_argument("--paralelo", type=int, default=4)
    ap.add_argument("args", nargs="*")
    ap.add_argument("--rede", action="store_true")
    ap.add_argument("--n", type=int, default=30)
    a = ap.parse_args(argv)
    if a.cmd == "amostra":
        for x in amostra(a.n):
            print(f"{x['uid'][:34]:34s} {x['tumor'][:16]:16s} F{x['fase']:5s} {x['terapia'][:12]:12s} {x['idade']:15s} sec={x['secundarios']} · {x['motivo']}")
    elif a.cmd == "coletar":
        uids = a.args or [x["uid"] for x in json.loads((DISC / "piloto.json").read_text())["cards"]]
        for u in uids:
            try:
                p = coletar(u, a.rede)
                print(f"{u[:34]:34s} {p['counts']} llm={sum(c['in_llm'] for c in p['candidates'])}")
            except S.SemCache as e:
                print(f"{u[:34]:34s} SEM_CACHE {e}")
    elif a.cmd == "tarefa":
        print(tarefa(a.args[0]))
    elif a.cmd == "entrada":
        print(tarefa_verifier(a.args[0]))
    elif a.cmd == "ingerir":
        d = ingerir(a.args[0], a.args[1], a.args[2])
        print(json.dumps({"erros": d.get("_erros")}, ensure_ascii=False))
    elif a.cmd == "lote":
        uids = a.args or [x["uid"] for x in json.loads(pathlib.Path(a.arquivo).read_text())["cards"]]
        for r in executar_lote(uids, a.rede, a.paralelo, a.bloco):
            print(json.dumps(r, ensure_ascii=False), flush=True)
    elif a.cmd == "consolidar":
        uids = a.args or [x["uid"] for x in json.loads(pathlib.Path(a.arquivo).read_text() if a.arquivo
                                                         else (DISC / "piloto.json").read_text())["cards"]]
        r = consolidar(uids, f"relatorio_{pathlib.Path(a.arquivo).stem}.json" if a.arquivo else "relatorio.json")
        print(json.dumps({k: v for k, v in r.items() if k != "rows"}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
