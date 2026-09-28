#!/usr/bin/env python3
"""
db_registro.py — registro de identidade do Database (Fase 0). Só leitura.

Para cada card de assets/js/data.js registra o que se pode afirmar sobre a
publicação que ele representa e sobre as demais publicações do estudo:
identificadores normalizados, PMID/DOI/PMCID, relação de cada publicação com o
estudo, tipo de análise, endpoint, população, data de corte e maturidade.

O `uid` é a chave e nunca é alterado: ele sustenta os deep links do Tumor
Boards (database.html#uid), os favoritos e as notas guardados no navegador e
o `parentUid` das publicações secundárias.

Cada valor classificado carrega a sua ORIGEM:
  explicit        — a fonte primária diz: título do artigo, tipo de publicação
                    no PubMed, abstract literal, referência do CT.gov, texto
                    do próprio card (endpoints);
  inferred        — regra do pipeline (ex.: "primeiro relato ligado ao
                    registro" ⇒ publicação primária). Fica registrado, mas NÃO
                    autoriza nem bloqueia atualização automática até ser
                    confirmado (`autoriza_automacao: false`);
  human_confirmed — decisão humana (tipo "classificacao") em
                    scripts/db_decisoes.json, válida só enquanto o card citar o
                    mesmo PMID.
  machine_verified — fato de identidade/relação bibliográfica demonstrado por
                    fontes estruturadas independentes (ver db_confianca.py).
O que não dá para determinar com segurança fica null e o card sai com
`requires_review: true` e o motivo.

Fontes: PubMed E-utilities, ClinicalTrials.gov v2, NCBI ID Converter e, como
complemento, Crossref (ver db_fontes.py). Os arquivos listados em
db_fontes.FONTES_PROIBIDAS não são fonte (ver db_PIPELINE.md).

Não escreve em data.js. Grava só scripts/_db_* (e, uma única vez, o
scripts/db_backlog_baseline.json do db_freshness).

Uso:
    python3 scripts/db_registro.py                  # coleta nas APIs e grava o registro
    python3 scripts/db_registro.py --reusar-coleta  # usa scripts/_db_coleta.json
    python3 scripts/db_registro.py --sem-crossref   # não consulta a Crossref
"""
from __future__ import annotations

import json
import re
import sys
import time
import urllib.error
from collections import Counter, defaultdict
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
SITE = SCRIPTS.parent
DATA_JS = SITE / "assets" / "js" / "data.js"
DECISOES = SCRIPTS / "db_decisoes.json"
CONFLITOS_FONTE = SCRIPTS / "db_conflitos_fonte.json"
BASELINE = SCRIPTS / "db_backlog_baseline.json"
SAIDA = {
    "coleta": SCRIPTS / "_db_coleta.json",
    "registro": SCRIPTS / "_db_registro.json",
    "registro_md": SCRIPTS / "_db_registro.md",
}

sys.path.insert(0, str(SCRIPTS))
import db_fontes  # noqa: E402
from br_ctgov import RespostaParcial  # noqa: E402

FALHA_TECNICA = 2

EXPLICIT, INFERRED, HUMAN = "explicit", "inferred", "human_confirmed"
FORCA_ORIGEM = {INFERRED: 0, EXPLICIT: 1, HUMAN: 2}

TIPOS = ("abstract", "interim", "primary", "final", "long-term update", "secondary")
MATURIDADE = {"press release": 0, "abstract": 1, "interim": 2, "primary": 3,
              "final": 4, "long-term update": 4}
ROTULO_MATURIDADE = {0: "press release", 1: "abstract", 2: "artigo com análise interina",
                     3: "publicação da análise primária",
                     4: "análise final / atualização madura"}
RELACOES = ("primary_publication", "follow_up", "secondary_analysis", "subgroup", "qol",
            "safety", "protocol", "correction", "retraction", "unknown")


# ── E/S ──────────────────────────────────────────────────────────────────────

def carregar_dados(caminho: Path = DATA_JS) -> dict:
    db_fontes.garantir_fonte_permitida(caminho)
    texto = caminho.read_text(encoding="utf-8")
    m = re.search(r"window\.THERA_DATA\s*=\s*(\{[\s\S]*\})\s*;?\s*$", texto)
    if not m:
        raise ValueError(f"window.THERA_DATA não encontrado em {caminho}")
    return json.loads(m.group(1))


def gravar(caminho: Path, conteudo: str, criar_somente: bool = False,
           migrar_baseline_v1: bool = False) -> None:
    """Única porta de escrita do pipeline: scripts/_db_* e, criado uma vez só,
    scripts/db_backlog_baseline.json. Nunca data.js.
    `migrar_baseline_v1` permite trocar UMA vez um baseline v1 por v2, e só se
    nenhum item do v1 tiver decisão humana registrada."""
    alvo = caminho.resolve()
    permitido = alvo.parent == SCRIPTS and (alvo.name.startswith("_db_") or alvo == BASELINE.resolve())
    if alvo == DATA_JS.resolve() or not permitido:
        raise PermissionError(f"recusado: o pipeline do Database só grava scripts/_db_* ({alvo})")
    if alvo == BASELINE.resolve():
        if migrar_baseline_v1 and alvo.exists():
            antigo = json.loads(alvo.read_text(encoding="utf-8"))
            if antigo.get("schema") != "theratrials-db-backlog-baseline/1" or \
                    any(i.get("revisao") for i in antigo.get("itens", [])):
                raise PermissionError("recusado: só migra baseline v1 sem nenhuma decisão registrada")
        elif alvo.exists() or not criar_somente:
            raise PermissionError("recusado: o baseline é criado uma vez e é imutável")
    tmp = alvo.with_name(alvo.name + ".tmp")
    tmp.write_text(conteudo, encoding="utf-8")
    tmp.replace(alvo)


def conferir_uids(registro: dict, dados: dict) -> None:
    """O registro tem exatamente os uids do banco, na mesma ordem."""
    a = [c["uid"] for c in registro["cards"]]
    b = [s["uid"] for s in dados["studies"]]
    if a != b:
        raise AssertionError("uids do registro divergem dos do data.js")
    if len(set(b)) != len(b):
        raise AssertionError("uid duplicado no data.js")


# ── Identificadores ─────────────────────────────────────────────────────────

RE_NCT = re.compile(r"NCT\d{8}")
RE_ISRCTN = re.compile(r"ISRCTN\d{8}")
RE_OUTROS = re.compile(r"EudraCT[\s:-]*\d{4}-\d{6}-\d{2}|\bNTR\d+|ChiCTR[\w-]+|ACTRN\d+|"
                       r"UMIN\d+|DRKS\d+|JPRN[\w-]+|CTRI/[\d/]+", re.I)
# Texto que indica que o campo não lista todos os registros do estudo.
RE_RESSALVA = re.compile(r"\be outros\b|variantes|\bbase\b|séries|múltiplos|não confirmado", re.I)


def identificadores(card: dict) -> dict:
    bruto = f"{card.get('nct') or ''} {card.get('nct_url') or ''}"
    ncts = list(dict.fromkeys(RE_NCT.findall(bruto)))
    isrctn = list(dict.fromkeys(RE_ISRCTN.findall(bruto)))
    outros = list(dict.fromkeys(m.group(0) for m in RE_OUTROS.finditer(bruto)))
    if len(ncts) > 1:
        situacao = "nct_multiplo"
    elif ncts:
        situacao = "nct_unico"
    elif isrctn:
        situacao = "isrctn"
    elif outros:
        situacao = "outro_registro"
    else:
        situacao = "sem_registro"
    campo = str(card.get("nct") or "")
    return {"situacao": situacao, "nct": ncts, "isrctn": isrctn, "outros": outros,
            "campo_nct": campo, "ressalva": bool((ncts or isrctn) and RE_RESSALVA.search(campo))}


def pmid_do_card(card: dict) -> str | None:
    m = re.search(r"pubmed\.ncbi\.nlm\.nih\.gov/(\d+)", str(card.get("pubmed_url") or ""))
    return m.group(1) if m else None


def categoria_status(status: str) -> str:
    s = (status or "").strip().lower()
    for prefixo, cat in (("publicado", "publicado"), ("apresentado", "apresentado"),
                         ("em andamento", "em_andamento"), ("concluído", "concluido"),
                         ("concluido", "concluido"), ("encerrado", "encerrado")):
        if s.startswith(prefixo):
            return cat
    return "outro"


def ano_de_referencia(card: dict) -> int | None:
    """Ano a partir do qual um artigo pode ser "novo" para o card: o do
    congresso no status, senão o ano_pub."""
    m = re.search(r"(20\d\d)", str(card.get("status") or ""))
    if m:
        return int(m.group(1))
    try:
        a = int(card.get("ano_pub") or 0)
    except (TypeError, ValueError):
        a = 0
    return a or None


# ── Natureza e tipo do artigo ───────────────────────────────────────────────

PT_AVISO = {"Published Erratum", "Retraction of Publication", "Expression of Concern",
            "Retraction Notice"}
PT_PROTOCOLO = {"Clinical Trial Protocol"}
PT_DIRETRIZ = {"Practice Guideline", "Guideline", "Consensus Development Conference"}
PT_PREPRINT = {"Preprint"}
PT_CASO = {"Case Reports"}
PT_COMENTARIO = {"Comment", "Editorial", "Letter", "News", "Interview", "Newspaper Article",
                 "Biography", "Portrait"}
PT_REVISAO = {"Review", "Systematic Review", "Meta-Analysis", "Scoping Review"}
PT_ENSAIO = {"Randomized Controlled Trial", "Clinical Trial", "Clinical Trial, Phase I",
             "Clinical Trial, Phase II", "Clinical Trial, Phase III", "Clinical Trial, Phase IV",
             "Controlled Clinical Trial", "Pragmatic Clinical Trial", "Adaptive Clinical Trial",
             "Equivalence Trial", "Multicenter Study", "Observational Study"}
PT_FASE = {"Randomized Controlled Trial", "Clinical Trial, Phase I", "Clinical Trial, Phase II",
           "Clinical Trial, Phase III", "Clinical Trial, Phase IV", "Clinical Trial"}
FASE_PT = {"Clinical Trial, Phase I": {1}, "Clinical Trial, Phase II": {2},
           "Clinical Trial, Phase III": {3}, "Clinical Trial, Phase IV": {4}}
# Artigo de desenho sem o tipo "Clinical Trial Protocol" no PubMed.
T_DESENHO = re.compile(r"rationale (for|and)|(study|trial) design|design (of|and rationale)|"
                       r"trial in progress|\bprotocol\b", re.I)


def natureza(art: dict) -> str:
    pt = set(art.get("pubtypes") or [])
    if pt & PT_AVISO:
        return "aviso"
    if pt & PT_DIRETRIZ:
        return "diretriz"
    if pt & PT_PROTOCOLO or T_DESENHO.search(art.get("titulo") or ""):
        return "protocolo"
    if pt & PT_PREPRINT:
        return "preprint"
    if pt & PT_CASO:
        return "relato_de_caso"
    if pt & PT_COMENTARIO:
        return "comentario"
    if pt & PT_REVISAO and not pt & PT_FASE:
        return "revisao"
    if pt & PT_ENSAIO:
        return "relato_de_ensaio"
    if "Journal Article" in pt:
        return "artigo"           # revisado por pares, tipo ainda não indexado
    return "outro"


# Relação com o estudo declarada no TÍTULO — o artigo dizendo o que é.
T_QOL = re.compile(r"quality[- ]of[- ]life|patient[- ]reported|health[- ]related quality|"
                   r"\bhrqol\b|\bpros?\b", re.I)
T_SAFETY = re.compile(r"\bsafety (analys|outcomes|profile|results|data|findings)|adverse events|"
                      r"toxicit(y|ies)\b|\bcardiotoxic|multiorgan safety", re.I)
T_SUBGRUPO = re.compile(
    r"\b(japanese|chinese|east asian|asian|korean|taiwanese|indian|elderly|older) "
    r"(patients|subgroup|subpopulation|population|cohort|participants)\b|\bsubgroup|"
    r"\bsubpopulation|\bwho (had|achieved|received|discontinued|completed)\b|outcomes by|"
    r"according to|by (baseline|age|sex|region|pd-l1|histolog)|long[- ]term survivors", re.I)
T_SECUNDARIA = re.compile(
    r"post[- ]?hoc|exploratory (analysis|analyses)|secondary analys|cost[- ]effective|"
    r"pooled analys|\bpooled\b|biomarker analys|translational analys|correlative analys|"
    r"pharmacokinetic|predictors? of|prognostic|factors (of|associated|predict)|"
    r"association (of|between)|\bassociation\b|correlation|\bestimat|\bmodel+ing\b|"
    r"multivariable|relationship (with|between)|landmark|characteri[sz]ation|reader agreement|"
    r"substudy|quantitative .*pet|comparative (efficacy|effectiveness)|real[- ]world|"
    r"matching[- ]adjusted|external control|indirect (treatment )?comparison", re.I)
T_FINAL = re.compile(r"\bfinal (overall survival|os\b|analys|results|report|efficacy|survival)", re.I)
T_LONGO = re.compile(r"long[- ]term|updated (analys|results|overall survival|survival|efficacy|"
                     r"outcomes|data)|extended follow[- ]up|longer follow[- ]up|mature (results|"
                     r"data|overall survival|survival)", re.I)
T_LONGO_ANOS = re.compile(r"\b(\d+|three|four|five|six|seven|eight|ten)[- ]year "
                          r"(follow[- ]up|outcomes|results|update|survival|analys|efficacy|data)",
                          re.I)
T_INTERIM = re.compile(r"\binterim (analys|results|report)", re.I)
T_PRIMARIA = re.compile(r"\bprimary (analys|results|report)", re.I)

# Abstract: só frases em que o artigo se descreve — "exploratory analyses
# showed…" aparece em relato primário e não pode rebaixá-lo a secundário.
R_SECUNDARIA = re.compile(r"\b(this|we (report|performed|conducted|present) (a|an|the))\s+"
                          r"(post[- ]?hoc|exploratory|secondary|prespecified exploratory)\s+"
                          r"analys", re.I)
R_FINAL = re.compile(r"\b(final (overall survival|os\b|analys)|at the final analysis)", re.I)
R_LONGO = re.compile(r"long[- ]term follow[- ]up|extended follow[- ]up|updated (analys|results|"
                     r"overall survival|efficacy)", re.I)
R_INTERIM = re.compile(r"\binterim analys", re.I)


def classificar_artigo(art: dict) -> dict:
    """Relação com o estudo e tipo de análise que o ARTIGO declara, com a
    origem de cada um. A regra do "primeiro relato" é do card, não daqui."""
    nat = natureza(art)
    pt = set(art.get("pubtypes") or [])
    t, r = art.get("titulo") or "", art.get("resumo") or ""
    out = {"natureza": nat, "relacao": "unknown", "relacao_origem": None, "relacao_evidencia": "",
           "tipo": None, "tipo_origem": None, "tipo_evidencia": ""}

    def rel(relacao, origem, evid):
        out.update(relacao=relacao, relacao_origem=origem, relacao_evidencia=evid)

    if nat == "aviso":
        if pt & {"Retraction of Publication", "Retraction Notice"}:
            rel("retraction", EXPLICIT, "PubMed: Retraction of Publication")
        else:
            rel("correction", EXPLICIT, "PubMed: " + "/".join(sorted(pt & PT_AVISO)))
        return out
    if nat == "protocolo":
        rel("protocol", EXPLICIT if pt & PT_PROTOCOLO else INFERRED,
            "PubMed: Clinical Trial Protocol" if pt & PT_PROTOCOLO
            else f"título: {T_DESENHO.search(t).group(0)!r}")
        return out
    if nat not in ("relato_de_ensaio", "artigo"):
        return out                # revisão, comentário, diretriz, caso, preprint: unknown

    for rx, relacao in ((T_QOL, "qol"), (T_SAFETY, "safety"), (T_SUBGRUPO, "subgroup"),
                        (T_SECUNDARIA, "secondary_analysis")):
        m = rx.search(t)
        if m and not (relacao == "safety" and re.search(r"efficacy", t, re.I)):
            rel(relacao, EXPLICIT, f"título: {m.group(0)!r}")
            out.update(tipo="secondary", tipo_origem=EXPLICIT, tipo_evidencia=m.group(0))
            return out
    for rx, tipo, origem, onde in ((T_FINAL, "final", EXPLICIT, "t"),
                                   (T_LONGO, "long-term update", EXPLICIT, "t"),
                                   (T_INTERIM, "interim", EXPLICIT, "t"),
                                   (T_PRIMARIA, "primary", EXPLICIT, "t"),
                                   (T_LONGO_ANOS, "long-term update", INFERRED, "t"),
                                   (R_FINAL, "final", INFERRED, "r"),
                                   (R_LONGO, "long-term update", INFERRED, "r"),
                                   (R_INTERIM, "interim", INFERRED, "r")):
        m = rx.search(t if onde == "t" else r)
        if m:
            out.update(tipo=tipo, tipo_origem=origem, tipo_evidencia=m.group(0))
            if tipo in ("final", "long-term update"):
                rel("follow_up", origem, f"{'título' if onde == 't' else 'abstract'}: {m.group(0)!r}")
            return out
    m = R_SECUNDARIA.search(r)
    if m:
        rel("secondary_analysis", INFERRED, f"abstract: {m.group(0)!r}")
        out.update(tipo="secondary", tipo_origem=INFERRED, tipo_evidencia=m.group(0))
    return out


# ── Endpoint, avaliação e ancoragem ─────────────────────────────────────────

# (nome, termo no `primario` do card, termo no título/abstract em inglês)
ENDPOINTS = [
    ("rPFS", r"\brpfs\b|slpr", r"radiographic progression[- ]free|\brpfs\b"),
    ("PFS2", r"\bpfs2\b|slp2", r"\bpfs2\b|second progression"),
    ("PFS", r"(?<!r)\bpfs\b|\bslp\b|sobrevida livre de progress", r"(?<!radiographic )progression[- ]free|(?<!r)\bpfs\b"),
    ("OS", r"\bos\b|\bsg\b|sobrevida global", r"overall survival|\bos\b"),
    ("EFS", r"\befs\b|\bsle\b|livre de evento", r"event[- ]free|\befs\b"),
    ("DFS", r"\bi?dfs\b|\bsld\b|livre de doença", r"disease[- ]free|\bdfs\b"),
    ("RFS", r"\brfs\b|livre de recid|livre de recorr", r"(recurrence|relapse)[- ]free|\brfs\b"),
    ("MFS", r"\bmfs\b|livre de metást", r"metastasis[- ]free|\bmfs\b"),
    ("pCR", r"\bpcr\b|resposta patológica completa", r"pathologic(al)? complete response|\bpcr\b"),
    ("ORR", r"\borr\b|\btro\b|taxa de resposta", r"(objective|overall) response|\borr\b"),
    ("PSA", r"\bpsa\d*\b", r"\bpsa\b|prostate[- ]specific antigen"),
]
R_BICR = re.compile(r"\bbicr\b|\birc\b|revis(ã|a)o central|central independente|"
                    r"independent (central )?review|blinded independent", re.I)
R_INV = re.compile(r"investigador|investigator[- ]assessed|\binv\b|local review|avaliação local", re.I)


def endpoints_card(card: dict) -> dict:
    """Endpoints e forma de avaliação que o `primario` do card declara."""
    t = str(card.get("primario") or "")
    nomes = [n for n, pt, _ in ENDPOINTS if re.search(pt, t, re.I)]
    aval = "BICR" if R_BICR.search(t) else "investigador" if R_INV.search(t) else None
    return {"valores": nomes or None, "avaliacao": aval,
            "origem": EXPLICIT if nomes else None, "fonte": "primario do card" if nomes else None}


def endpoints_artigo(art: dict, nomes: list[str] | None = None) -> list[str]:
    t = f"{art.get('titulo', '')} {art.get('resumo', '')}"
    return [n for n, _, en in ENDPOINTS if (nomes is None or n in nomes) and re.search(en, t, re.I)]


TRIVIAIS = {"0.001", "0.0001", "0.01", "0.05", "0.025", "95", "100"}


def _num(s: str) -> str:
    s = s.replace(",", ".").replace("·", ".")
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    if s.startswith("0."):
        return s
    return s.lstrip("0") or "0"


def numeros_card(texto: str) -> set[str]:
    """Decimais e percentuais do `primario` — o que identifica uma análise."""
    t = str(texto or "")
    dec = re.findall(r"(?<![\d.,])\d+[.,]\d+", t)
    pct = re.findall(r"(?<![\d.,])(\d+(?:[.,]\d+)?)\s?%", t)
    return {_num(x) for x in dec + pct} - TRIVIAIS


def numeros_resumo(texto: str) -> set[str]:
    return {_num(x) for x in re.findall(r"\d+(?:[.·]\d+)?", str(texto or ""))}


def ancoragem(card: dict, art: dict | None) -> dict:
    alvo = numeros_card(card.get("primario"))
    if not art or not art.get("resumo"):
        return {"numeros_card": len(alvo), "achados": 0, "nivel": "sem_resumo"}
    k, n = len(alvo & numeros_resumo(art["resumo"])), len(alvo)
    nivel = ("insuficiente" if n < 3 else "forte" if k >= 3 and k / n >= 0.5
             else "fraca" if k >= 1 else "nenhuma")
    return {"numeros_card": n, "achados": k, "nivel": nivel}


# ── Data de corte / seguimento ──────────────────────────────────────────────

_MES = r"(?:January|February|March|April|May|June|July|August|September|October|November|December)"
R_SEGUIMENTO = re.compile(r"median (?:duration of |time of |)follow[- ]up(?: time)?(?: was| of|:|,)?"
                          r"\s*(?:was\s*)?(\d+(?:[.·]\d+)?)\s*(months?|years?|mo\b)", re.I)
R_CORTE = re.compile(rf"data[- ]?cut[- ]?off(?: date)?(?: of| was| on|:|,)?\s*"
                     rf"({_MES}\s+\d{{1,2}},?\s+\d{{4}}|\d{{1,2}}\s+{_MES}\s+\d{{4}}|{_MES},?\s+\d{{4}})",
                     re.I)


def data_de_corte(art: dict | None) -> dict | None:
    """Literal do abstract (origem explicit) ou None."""
    if not art or not art.get("resumo"):
        return None
    r = art["resumo"]
    seg, corte = R_SEGUIMENTO.search(r), R_CORTE.search(r)
    if not seg and not corte:
        return None
    return {"seguimento_mediano": f"{seg.group(1).replace('·', '.')} {seg.group(2)}" if seg else None,
            "data_corte": corte.group(1) if corte else None, "origem": EXPLICIT,
            "fonte": f"abstract PMID {art['pmid']}", "trecho": (seg or corte).group(0)}


# ── Coorte (basket / plataforma) ────────────────────────────────────────────

TERMO_TUMOR = [
    ("hepatobiliar", r"biliary|cholangio|gallbladder|hepatocellular|\bliver\b|\bhcc\b"),
    ("pancreas", r"pancrea"), ("endometrio", r"endometri"), ("cervix", r"cervi"),
    ("ovario", r"ovar"), ("tireoide", r"thyroid"), ("urotelial", r"urothel|bladder"),
    ("nsclc", r"lung|nsclc"), ("sclc", r"lung|sclc"), ("breast", r"breast"),
    ("colorretal", r"colorectal|colon|rectal"), ("esofago", r"esophag|oesophag|gastr"),
    ("melanoma", r"melanoma"), ("hnscc", r"head and neck|oropharyn|nasopharyn|laryn"),
    ("rcc", r"renal|kidney"), ("mieloma", r"myeloma"), ("linfoma", r"lymphoma"),
    ("lma", r"leukemia|leukaemia|\baml\b"), ("neuroblastoma", r"neuroblastoma"),
    ("net_gep", r"neuroendocrine"), ("ppgl", r"pheochromocytoma|paraganglioma"),
    ("meningioma", r"meningioma"), ("prostata", r"prostat"), ("lupsma_prostata", r"prostat"),
    ("ra223", r"prostat"), ("rt_prostata", r"prostat"), ("novos_psma", r"prostat"),
]


def termo_tumor(category_id: str) -> str | None:
    for prefixo, rx in TERMO_TUMOR:
        if category_id.startswith(prefixo):
            return rx
    return None


def coorte(uid: str, art: dict, irmaos: list[str], cat_de: dict[str, str]) -> bool | None:
    """NCT compartilhado por vários cards: o título diz de que coorte o artigo
    trata? True = deste card; False = de outro; None = não dá para dizer."""
    if len(irmaos) < 2:
        return True
    if any(termo_tumor(cat_de[u]) is None for u in irmaos):
        return None
    titulo = art.get("titulo") or ""
    casam = [u for u in irmaos if re.search(termo_tumor(cat_de[u]), titulo, re.I)]
    if casam == [uid]:
        return True
    if casam and uid not in casam:
        return False
    return None


# ── Comparabilidade (regra 6) ───────────────────────────────────────────────

R_BIOMARCADOR = re.compile(r"\b(pd-l1|brca\d?|hrr|hrd|msi-h|dmmr|her2[- ]low|her2|egfr|alk|kras|"
                           r"braf|pik3ca|esr1|fgfr\d?|ntrk|ret|met|idh\d?|flt3|npm1|tp53|"
                           r"deficien\w*|mutat\w*|positive|negative)\b", re.I)


def comparabilidade(card: dict, rep_art: dict | None, art: dict, pub: dict) -> dict:
    """Uma publicação só poderia substituir a representada se a análise for
    comparável: mesma população (ITT × subgrupo, global × biomarcador), mesmo
    endpoint (primário × secundário, PFS × PFS2), mesma avaliação (BICR ×
    investigador), mesma metodologia. Só ANOTA — nunca decide nem autoriza.
    `comparavel` é False quando uma diferença foi detectada, e None em todos
    os outros casos: ausência de diferença detectada não prova comparabilidade."""
    dif, ok = [], []
    if pub["relacao"] in ("subgroup", "secondary_analysis", "qol", "safety"):
        dif.append(f"relação {pub['relacao']} ({pub['relacao_evidencia']})")
    ep = endpoints_card(card)
    if ep["valores"]:
        achados = endpoints_artigo(art, ep["valores"])
        if achados:
            ok.append(f"endpoint do card presente no artigo: {achados}")
        else:
            dif.append(f"endpoint do card {ep['valores']} ausente do título/abstract")
        if "PFS2" in endpoints_artigo(art) and "PFS2" not in ep["valores"]:
            dif.append("artigo relata PFS2; o card, não")
    resumo = art.get("resumo") or ""
    if ep["avaliacao"] == "BICR" and R_INV.search(resumo) and not R_BICR.search(resumo):
        dif.append("card por BICR; artigo cita só avaliação do investigador")
    bm_art = {m.lower() for m in R_BIOMARCADOR.findall(art.get("titulo") or "")}
    bm_rep = {m.lower() for m in R_BIOMARCADOR.findall((rep_art or {}).get("titulo") or "")}
    if bm_art - bm_rep:
        dif.append(f"título restringe por biomarcador ausente na representada: {sorted(bm_art - bm_rep)}")
    if pub.get("coorte") is not True:
        dif.append("coorte não verificada (NCT compartilhado)")
    return {"comparavel": False if dif else None, "diferencas": dif, "iguais": ok,
            "origem": INFERRED}


# ── `ref` do card ───────────────────────────────────────────────────────────

R_REF_ATUALIZACAO = re.compile(r"atualiza|update|follow[- ]?up|seguimento|longo prazo|long[- ]term|"
                               r"análise final|final analysis|\d+[- ]?(yr|anos?|year)", re.I)


def ref_cita_outra(card: dict, art: dict | None) -> str | None:
    ref = str(card.get("ref") or "")
    if not R_REF_ATUALIZACAO.search(ref):
        return None
    ano = (art or {}).get("data", "")[:4]
    outros = sorted({a for a in re.findall(r"\b(?:19|20)\d\d\b", ref) if a != ano})
    return f"ref menciona atualização e os anos {', '.join(outros)}" if outros else None


def citado_no_ref(card: dict, art: dict) -> bool:
    """O `ref` já cita este artigo (mesmo ano e mesmo periódico)?"""
    ref = str(card.get("ref") or "").lower()
    ano = (art.get("data") or "")[:4]
    per = (art.get("periodico") or "").lower().replace(".", "")
    if not ano or ano not in ref or not per:
        return False
    tokens = [t for t in re.split(r"\s+", per) if len(t) >= 3]
    return bool(tokens) and all(t in ref.replace(".", "") for t in tokens[:2])


# ── Fase ────────────────────────────────────────────────────────────────────

def fases_do_card(card: dict) -> set[int]:
    m = re.search(r"fase\s*([1-4](?:\s*/\s*[1-4])?)", str(card.get("fase") or ""), re.I)
    return {int(x) for x in re.findall(r"[1-4]", m.group(1))} if m else set()


def fase_compativel(pub: dict, fases: set[int]) -> bool:
    declaradas = set().union(*(FASE_PT.get(t, set()) for t in pub["pubtypes"]))
    return not declaradas or not fases or bool(declaradas & fases)


# ── Confirmações humanas ────────────────────────────────────────────────────

CAMPOS_CONFIRMAVEIS = {"tipo_analise", "populacao", "relacao", "integridade", "publicacao_primaria"}
VALORES_INTEGRIDADE = {"SOURCE_METADATA_ERROR", "EDITORIAL_QUARANTINE"}


TIPOS_DECISAO = ("ignore", "approve", "defer", "classificacao")


def ler_decisoes(caminho: Path | None = None) -> tuple[list[dict], list[str]]:
    """Decisões humanas válidas e avisos das inválidas. Arquivo ausente = nada.
    Cada decisão: {id, tipo, decidido_em, motivo, ...}. `id` é o identificador
    estável do item (chave do sinal ou "uid:pmid" do baseline); `defer` exige
    `ate` (AAAA-MM-DD); `classificacao` exige uid, pmid, campo e valor."""
    caminho = caminho or DECISOES
    if not caminho.exists():
        return [], []
    ok, avisos = [], []
    for e in json.loads(caminho.read_text(encoding="utf-8")).get("decisoes", []):
        falta = [k for k in ("id", "tipo", "decidido_em", "motivo") if not e.get(k)]
        if e.get("tipo") == "defer" and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(e.get("ate", ""))):
            falta.append("ate")
        if falta or e.get("tipo") not in TIPOS_DECISAO or \
                not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(e.get("decidido_em", ""))):
            avisos.append(f"decisão ignorada ({e.get('id')}): incompleta ou tipo não aceito")
            continue
        ok.append(e)
    return ok, avisos


def ler_confirmacoes(caminho: Path | None = None) -> tuple[dict, list[str]]:
    """Decisões do tipo "classificacao", por uid."""
    decisoes, avisos = ler_decisoes(caminho)
    ok = defaultdict(list)
    for e in decisoes:
        if e["tipo"] != "classificacao":
            continue
        e = dict(e, confirmado_em=e["decidido_em"])
        falta = [k for k in ("uid", "pmid", "campo", "valor") if not e.get(k)]
        if falta or e.get("campo") not in CAMPOS_CONFIRMAVEIS:
            avisos.append(f"classificação ignorada ({e.get('id')}): incompleta ou campo não aceito")
            continue
        if e["campo"] == "tipo_analise" and e["valor"] not in TIPOS:
            avisos.append(f"confirmação ignorada ({e['uid']}): tipo {e['valor']!r} fora do vocabulário")
            continue
        if e["campo"] == "integridade" and (e["valor"] not in VALORES_INTEGRIDADE or not e.get("evidencia")):
            avisos.append(f"classificação ignorada ({e['id']}): integridade exige valor aceito e evidência")
            continue
        if e["campo"] == "relacao" and e["valor"] not in RELACOES:
            avisos.append(f"confirmação ignorada ({e['uid']}): relação {e['valor']!r} fora do vocabulário")
            continue
        ok[e["uid"]].append(e)
    return dict(ok), avisos


# ── Card ────────────────────────────────────────────────────────────────────

def _pub(art: dict, cls: dict, ligacao: list[str], coorte_ok) -> dict:
    return {
        "pmid": art["pmid"], "doi": art.get("doi") or None, "pmcid": art.get("pmcid") or None,
        "titulo": art.get("titulo", ""), "periodico": art.get("periodico", ""),
        "data": art.get("data", ""), "pubtypes": art.get("pubtypes", []),
        "registros_no_artigo": art.get("registros", []),
        "natureza": cls["natureza"],
        "relacao": cls["relacao"], "relacao_origem": cls["relacao_origem"],
        "relacao_evidencia": cls["relacao_evidencia"],
        "tipo_analise": cls["tipo"], "tipo_origem": cls["tipo_origem"],
        "tipo_evidencia": cls["tipo_evidencia"],
        "maturidade_nivel": MATURIDADE.get(cls["tipo"]) if cls["tipo"] != "secondary" else None,
        "ligacao": ligacao, "coorte": coorte_ok,
    }


def compacto_ref(ref: str | None) -> str:
    """Chave para nota citada só pela referência (sem PMID nem DOI)."""
    return "ref:" + re.sub(r"[^a-z0-9]", "", str(ref or "").lower())[:40]


def avisos_do_artigo(art: dict | None, doi: str | None, coleta: dict) -> list[dict]:
    """Correções e retratações do artigo do card. PubMed primeiro; Crossref
    como complemento; a mesma nota vinda das duas fontes vira um item."""
    if not art:
        return []
    brutos = list(art.get("correcoes", []))
    if "Retracted Publication" in (art.get("pubtypes") or []) and \
            not any(c["tipo"] == "retratacao" for c in brutos):
        brutos.append({"tipo": "retratacao", "fonte": "pubmed:pubtype", "pmid": art["pmid"]})
    brutos += (coleta.get("crossref", {}).get(doi) or []) if doi else []
    por_chave: dict[str, dict] = {}
    for c in brutos:
        d = (c.get("doi") or "").lower()
        if not d:
            m = re.search(r"doi:\s*(\S+?)\.?$", c.get("ref") or "", re.I)
            d = m.group(1).lower() if m else ""
        chave = f"{c['tipo']}:{d or c.get('pmid') or compacto_ref(c.get('ref'))}"
        if chave in por_chave:
            por_chave[chave]["fontes"].append(c["fonte"])
        else:
            por_chave[chave] = {"chave": chave, "tipo": c["tipo"],
                                "relacao": "retraction" if c["tipo"] == "retratacao" else "correction",
                                "doi": d or None, "pmid": c.get("pmid") or None,
                                "ref": c.get("ref") or "", "data": c.get("data") or "",
                                "fontes": [c["fonte"]], "origem": EXPLICIT}
    return sorted(por_chave.values(), key=lambda a: a["chave"])


def registrar_card(card: dict, coleta: dict, irmaos_de: dict[str, list[str]],
                   cat_de: dict[str, str], confirmacoes: dict) -> dict:
    uid = card["uid"]
    ids = identificadores(card)
    pmid = pmid_do_card(card)
    arts = coleta["artigos"]
    st = categoria_status(card.get("status", ""))

    ligados: set[str] = set()
    for ident in ids["nct"] + ids["isrctn"]:
        ligados |= set(coleta["si"].get(ident, []))
    ctg = [coleta["ctgov"].get(n) for n in ids["nct"]]
    result = {r["pmid"] for c in ctg if c for r in c["referencias"] if r["tipo"] == "RESULT"}
    derived = {r["pmid"] for c in ctg if c for r in c["referencias"] if r["tipo"] == "DERIVED"}
    irmaos = sorted({u for n in ids["nct"] for u in irmaos_de.get(n, [])})

    pubs = []
    for p in sorted(ligados | result | ({pmid} if pmid else set()), key=int):
        art = arts.get(p)
        if not art:
            continue
        lig = [r for r, cond in (("pubmed_si", p in ligados), ("ctgov_result", p in result),
                                 ("ctgov_derived", p in derived),
                                 ("databank", bool(set(ids["nct"] + ids["isrctn"]) &
                                                   set(art.get("registros", [])))))
               if cond]
        pubs.append(_pub(art, classificar_artigo(art), lig, coorte(uid, art, irmaos, cat_de)))
    pubs.sort(key=lambda x: (x["data"], int(x["pmid"])))

    # Publicação primária do estudo (regra ⇒ inferred): primeiro relato ligado
    # ao registro, da fase do card, que não seja secundário/protocolo. Relato
    # tipado como ensaio tem precedência sobre "Journal Article" sem tipo.
    fases = fases_do_card(card)
    compat = [x for x in pubs if x["natureza"] in ("relato_de_ensaio", "artigo")
              and x["relacao"] in ("unknown", "follow_up") and x["coorte"] is not False
              and fase_compativel(x, fases) and (x["ligacao"] or x["pmid"] == pmid)]
    primeiro = next((x for x in compat if x["natureza"] == "relato_de_ensaio"),
                    next(iter(compat), None))
    if primeiro and primeiro["relacao"] == "unknown":
        primeiro.update(relacao="primary_publication", relacao_origem=INFERRED,
                        relacao_evidencia="primeiro relato ligado ao registro, fase compatível")

    doi = (arts.get(pmid) or {}).get("doi") or coleta["idconv"].get(pmid or "", {}).get("doi") or None
    doi_origem = ("pubmed" if (arts.get(pmid) or {}).get("doi") else "idconv" if doi else None)
    pmcid = (arts.get(pmid) or {}).get("pmcid") or coleta["idconv"].get(pmid or "", {}).get("pmcid") or None

    reg = {
        "uid": uid, "estudo": card.get("estudo", ""), "acron": card.get("acron", ""),
        "categoria": card.get("category_id", ""), "status_card": card.get("status", ""),
        "status_categoria": st, "ano_pub": card.get("ano_pub"),
        "identidade": dict(ids, nct_compartilhado_com=[u for u in irmaos if u != uid]),
        "pmid_atual": pmid, "doi": doi, "doi_origem": doi_origem, "pmcid": pmcid,
        "publicacao_representada": None,
        "analise": None,
        "primary_publication": primeiro["pmid"] if primeiro else None,
        "publicacoes": pubs,
        "avisos": avisos_do_artigo(arts.get(pmid), doi, coleta),
        "origem_classificacao": None, "confianca": None,
        "requires_review": False, "motivos_revisao": [], "evidencias": [],
    }
    analisar(reg, card, coleta, irmaos, primeiro)
    aplicar_confirmacoes(reg, confirmacoes.get(uid, []))
    completar_identidade(reg)
    return reg


def analisar(reg: dict, card: dict, coleta: dict, irmaos: list[str], primeiro: dict | None) -> None:
    """Preenche publicacao_representada, analise, origem, confiança e revisão."""
    ids, pmid, st = reg["identidade"], reg["pmid_atual"], reg["status_categoria"]
    rev, evid = reg["motivos_revisao"], reg["evidencias"]
    registro = ids["situacao"] in ("nct_unico", "nct_multiplo", "isrctn")
    if ids["ressalva"]:
        rev.append(f"registro_parcial: campo nct = {ids['campo_nct']!r}")
    for n in ids["nct"]:
        if n in coleta["ctgov"] and coleta["ctgov"][n] is None:
            rev.append(f"nct_inexistente: {n} respondeu 404 no CT.gov")
    analise = {"aplicavel": True, "tipo": None, "tipo_origem": None, "maturidade": None,
               "maturidade_nivel": None, "maturidade_origem": None, "endpoint": endpoints_card(card),
               "populacao": None, "populacao_origem": None, "data_corte": None, "ancoragem": None,
               "autoriza_automacao": False}
    reg["analise"] = analise
    ctg = [coleta["ctgov"].get(n) for n in ids["nct"]]

    # ── sem PMID ──────────────────────────────────────────────────────────
    if not pmid:
        if st == "apresentado":
            analise.update(tipo="abstract", tipo_origem=INFERRED, maturidade="abstract",
                           maturidade_nivel=1, maturidade_origem=INFERRED)
            reg["publicacao_representada"] = {"pmid": None, "relacao": "unknown",
                                              "fonte": card.get("status")}
            evid.append("status do card declara apresentação em congresso; sem PMID")
        elif st == "publicado":
            rev.append("publicado_sem_pmid: status diz Publicado e pubmed_url está vazio")
            if re.search(r"press release|comunicado", f"{card.get('ref')} {card.get('status')}", re.I):
                analise.update(maturidade="press release", maturidade_nivel=0,
                               maturidade_origem=INFERRED)
                evid.append("ref/status mencionam press release")
        elif st in ("em_andamento", "concluido", "encerrado"):
            analise["aplicavel"] = False
            evid.append("card de desenho: não representa análise")
            ano = ano_de_referencia(card)
            depois = [x for x in reg["publicacoes"] if x["natureza"] in ("relato_de_ensaio", "artigo")
                      and x["relacao"] in ("unknown", "primary_publication", "follow_up")
                      and x["coorte"] is True and (not ano or int(x["data"][:4] or 0) >= ano)]
            if depois:
                rev.append("desenho_com_publicacao: artigo ligado ao registro — "
                           + ", ".join(x["pmid"] for x in depois[:3]))
            if any(c and c["has_results"] for c in ctg):
                rev.append("resultados_no_ctgov: hasResults=true num card de desenho")
        else:
            rev.append(f"status_nao_classificado: {card.get('status')!r} sem PMID")
        return _fechar(reg)

    # ── com PMID ──────────────────────────────────────────────────────────
    art = coleta["artigos"].get(pmid)
    if pmid in coleta.get("ausentes_pubmed", []) or not art:
        rev.append(f"pmid_inexistente: PMID {pmid} sem registro no PubMed")
        return _fechar(reg)
    pub = next(x for x in reg["publicacoes"] if x["pmid"] == pmid)
    reg["publicacao_representada"] = {k: pub[k] for k in (
        "pmid", "titulo", "periodico", "data", "natureza", "relacao", "relacao_origem",
        "relacao_evidencia", "ligacao")}
    if registro and not pub["ligacao"]:
        rev.append("pmid_nao_ligado: o PMID do card não está ligado ao registro (nem PubMed [si], "
                   "nem DataBank do artigo, nem referências do CT.gov)")
    elif pub["ligacao"]:
        evid.append("PMID ligado ao registro: " + ", ".join(pub["ligacao"]))
    no_artigo = [r for r in pub["registros_no_artigo"] if r.startswith("NCT")]
    if ids["nct"] and no_artigo and not set(no_artigo) & set(ids["nct"]):
        rev.append(f"databank_divergente: o artigo declara {', '.join(no_artigo)}; o card, "
                   f"{', '.join(ids['nct'])}")
    if pub["coorte"] is False:
        rev.append("coorte_divergente: o título do artigo é de outra coorte do mesmo NCT")

    if pub["natureza"] == "diretriz":
        analise["aplicavel"] = False
        evid.append("PubMed classifica o PMID como diretriz: não representa análise de ensaio")
        return _fechar(reg)
    if pub["natureza"] == "protocolo" and st in ("em_andamento", "concluido", "encerrado"):
        analise["aplicavel"] = False
        evid.append("PMID é o protocolo; card de desenho")
        return _fechar(reg)
    if pub["natureza"] not in ("relato_de_ensaio", "artigo"):
        rev.append(f"pmid_nao_e_relato: o PMID do card é {pub['natureza']} "
                   f"({'/'.join(pub['pubtypes'])})")
    if st in ("em_andamento", "concluido") and pub["natureza"] in ("relato_de_ensaio", "artigo"):
        rev.append(f"status_x_pmid: o card diz {card.get('status')!r}, mas o PMID é um artigo de "
                   f"resultado ({pub['data'][:4]}, {pub['periodico']})")
    if pub["relacao"] in ("secondary_analysis", "subgroup", "qol", "safety"):
        rev.append(f"pmid_e_{pub['relacao']}: {pub['relacao_evidencia']}")

    anc = ancoragem(card, art)
    analise["ancoragem"] = anc
    if anc["nivel"] == "nenhuma":
        rev.append(f"sem_ancoragem: nenhum dos {anc['numeros_card']} números do primario está no abstract")
    elif anc["nivel"] == "forte":
        evid.append(f"ancoragem forte: {anc['achados']}/{anc['numeros_card']} números do primario no abstract")
    outra = ref_cita_outra(card, art)
    if outra:
        evid.append(f"ref_cita_outra_publicacao: {outra}")
        if anc["nivel"] != "forte":
            rev.append(f"ref_cita_outra_publicacao: {outra}; ancoragem {anc['nivel']}")

    # Tipo de análise: explicit (título) > inferred (abstract, indício, regra).
    tipo, origem = pub["tipo_analise"], pub["tipo_origem"]
    if tipo is None and primeiro and primeiro["pmid"] == pmid:
        tipo, origem = "primary", INFERRED
        evid.append("tipo 'primary' por regra: primeiro relato ligado ao registro"
                    + ("" if pub["natureza"] == "relato_de_ensaio" else " (sem tipo indexado)"))
    elif tipo:
        evid.append(f"tipo {tipo!r} ({origem}): {pub['tipo_evidencia']!r}")
    if tipo is None:
        rev.append("tipo_indeterminado: título e abstract não dizem que análise é, e o artigo não é "
                   "o primeiro relato ligado ao registro")
    analise.update(tipo=tipo, tipo_origem=origem)
    if tipo and tipo != "secondary":
        analise.update(maturidade=ROTULO_MATURIDADE[MATURIDADE[tipo]],
                       maturidade_nivel=MATURIDADE[tipo], maturidade_origem=origem)

    # População: subgrupo quando o título diz; global só por inferência.
    if pub["relacao"] == "subgroup":
        analise.update(populacao="subgrupo", populacao_origem=EXPLICIT)
    elif ids["situacao"] == "nct_multiplo":
        rev.append("populacao_indeterminada: card agrupa vários NCTs")
    elif pub["coorte"] is None:
        rev.append("populacao_indeterminada: NCT compartilhado com "
                   + ", ".join(u for u in irmaos if u != reg["uid"]))
    elif tipo in ("primary", "interim", "final", "long-term update"):
        analise.update(populacao="global (sem restrição de subgrupo no título)",
                       populacao_origem=INFERRED)
    analise["data_corte"] = data_de_corte(art)
    return _fechar(reg)


def _fechar(reg: dict) -> None:
    """Origem geral, confiança, requires_review e autorização."""
    a = reg["analise"]
    registro = reg["identidade"]["situacao"] in ("nct_unico", "nct_multiplo", "isrctn")
    if not a["aplicavel"]:
        reg["origem_classificacao"], reg["confianca"] = None, None
    elif a["tipo"] is None or (a["tipo"] != "secondary" and a["maturidade_nivel"] is None):
        reg["origem_classificacao"], reg["confianca"] = None, None
        if not any(m.startswith(("tipo_indeterminado", "publicado_sem_pmid", "pmid_inexistente",
                                 "maturidade_indeterminada"))
                   for m in reg["motivos_revisao"]):
            reg["motivos_revisao"].append("maturidade_indeterminada")
    else:
        origens = [o for o in (a["tipo_origem"], a["maturidade_origem"]) if o]
        origem = min(origens, key=FORCA_ORIGEM.get)
        reg["origem_classificacao"] = origem
        forte = (a.get("ancoragem") or {}).get("nivel") == "forte"
        ligado = bool((reg["publicacao_representada"] or {}).get("ligacao"))
        reg["confianca"] = ("alta" if origem in (EXPLICIT, HUMAN) and forte and (ligado or not registro)
                            else "média" if origem in (EXPLICIT, HUMAN) or (forte and ligado)
                            else "baixa")
    reg["requires_review"] = bool(reg["motivos_revisao"])
    a["autoriza_automacao"] = (reg["origem_classificacao"] in (EXPLICIT, HUMAN)
                               and not reg["requires_review"])


def aplicar_confirmacoes(reg: dict, entradas: list[dict]) -> None:
    """Decisão humana vale só para o PMID que o card cita hoje."""
    for e in entradas:
        vale_para_o_card = e["campo"] == "integridade" and e["valor"] == "EDITORIAL_QUARANTINE" and e["pmid"] == "*"
        if not vale_para_o_card and str(e["pmid"]) != str(reg["pmid_atual"]):
            reg["evidencias"].append(f"confirmação humana de {e['confirmado_em']} ignorada: "
                                     f"era para o PMID {e['pmid']}, o card cita {reg['pmid_atual']}")
            continue
        a = reg["analise"]
        if e["campo"] == "tipo_analise":
            a.update(tipo=e["valor"], tipo_origem=HUMAN)
            if e["valor"] != "secondary":
                a.update(maturidade=ROTULO_MATURIDADE[MATURIDADE[e["valor"]]],
                         maturidade_nivel=MATURIDADE[e["valor"]], maturidade_origem=HUMAN)
            reg["motivos_revisao"][:] = [m for m in reg["motivos_revisao"]
                                         if not m.startswith(("tipo_indeterminado",
                                                              "maturidade_indeterminada"))]
        elif e["campo"] == "populacao":
            a.update(populacao=e["valor"], populacao_origem=HUMAN)
            reg["motivos_revisao"][:] = [m for m in reg["motivos_revisao"]
                                         if not m.startswith("populacao_indeterminada")]
        elif e["campo"] == "publicacao_primaria":
            # A primária do estudo decidida por humano; a inferida por regra deixa de valer.
            for pub in reg["publicacoes"]:
                if pub["relacao"] == "primary_publication" and pub["relacao_origem"] == INFERRED:
                    pub.update(relacao="unknown", relacao_origem=None, relacao_evidencia="")
                if pub["pmid"] == str(e["valor"]):
                    pub.update(relacao="primary_publication", relacao_origem=HUMAN,
                               relacao_evidencia=f"decisão {e['id']}")
            reg["primary_publication"] = str(e["valor"])
        elif e["campo"] == "integridade" and e["valor"] == "EDITORIAL_QUARANTINE":
            # Quarentena editorial: o conteúdo clínico não tem fonte verificável.
            # Interna ao pipeline: bloqueia automação clínica e arquiva os sinais
            # do card; não muda o data.js nem o frontend.
            reg["quarentena_editorial"] = {"id": e["id"], "evidencia": e["evidencia"],
                                           "decidido_em": e.get("decidido_em") or e.get("confirmado_em")}
        elif e["campo"] == "integridade":
            # SOURCE_METADATA_ERROR: o conflito é do metadado da fonte, não do card.
            # Só vale para o mesmo conflito (o NCT errado declarado pelo artigo).
            alvo = str((e.get("evidencia") or {}).get("nct_declarado_pelo_artigo", ""))
            resolvidos = [m for m in reg["motivos_revisao"]
                          if m.startswith("databank_divergente") and alvo and alvo in m]
            if not resolvidos:
                reg["evidencias"].append(f"decisão de integridade ({e['id']}) não se aplica: conflito "
                                         f"com {alvo or '?'} não encontrado")
                continue
            reg["motivos_revisao"][:] = [m for m in reg["motivos_revisao"] if m not in resolvidos]
            reg["integridade_resolvida"] = {"valor": e["valor"], "id": e["id"], "evidencia": e["evidencia"],
                                            "decidido_em": e.get("decidido_em") or e.get("confirmado_em")}
        elif e["campo"] == "relacao" and reg["publicacao_representada"]:
            reg["publicacao_representada"].update(relacao=e["valor"], relacao_origem=HUMAN)
        reg["evidencias"].append(f"confirmação humana ({e['confirmado_em']}): {e['campo']} = "
                                 f"{e['valor']!r} — {e['motivo']}")
        _fechar(reg)


def completar_identidade(reg: dict) -> None:
    """Identidade completa = tudo o que o tipo de card exige está presente e
    verificado. Card de desenho/abstract não exige PMID; card com PMID exige
    registro, DOI e a ligação PMID↔registro vinda de uma fonte."""
    ids, falta = reg["identidade"], []
    registro = ids["situacao"] in ("nct_unico", "nct_multiplo", "isrctn")
    if not registro:
        falta.append("registro (NCT/ISRCTN)")
    if reg["pmid_atual"]:
        if not reg["doi"]:
            falta.append("DOI")
        if registro and not (reg["publicacao_representada"] or {}).get("ligacao"):
            falta.append("ligação PMID↔registro")
    elif reg["status_categoria"] not in ("apresentado", "em_andamento", "concluido", "encerrado"):
        falta.append("PMID")
    if ids["ressalva"]:
        falta.append("lista completa de registros")
    ids["nivel"] = "completa" if not falta else "parcial"
    ids["faltando"] = falta


def desmarcar_primaria_de_outro_card(cards: list[dict]) -> None:
    """Um artigo que é a publicação representada de OUTRO card, sem NCT em
    comum, não pode ser a primária inferida deste (o DataBank de um piloto
    costuma citar também o NCT do fase 3 que ele originou)."""
    dono = {}
    for c in cards:
        if c["pmid_atual"]:
            dono.setdefault(c["pmid_atual"], []).append(c)
    for c in cards:
        for pub in c["publicacoes"]:
            outros = [o for o in dono.get(pub["pmid"], []) if o is not c
                      and not set(o["identidade"]["nct"]) & set(c["identidade"]["nct"])]
            if outros and pub["relacao"] == "primary_publication" and pub["relacao_origem"] == INFERRED:
                pub.update(relacao="unknown", relacao_origem=None,
                           relacao_evidencia=f"publicação representada por {outros[0]['uid']} (outro estudo)")
                if c["primary_publication"] == pub["pmid"]:
                    c["primary_publication"] = None


def marcar_pmid_compartilhado(cards: list[dict]) -> None:
    """O mesmo PMID em cards que não compartilham nenhum NCT: um dos dois cita
    o artigo de outro estudo. Basket/plataforma (mesmo NCT) fica de fora."""
    por_pmid: dict[str, list[dict]] = defaultdict(list)
    for c in cards:
        if c["pmid_atual"]:
            por_pmid[c["pmid_atual"]].append(c)
    for pmid, grupo in por_pmid.items():
        if len(grupo) < 2:
            continue
        ncts = [set(c["identidade"]["nct"]) for c in grupo]
        if all(ncts) and set.intersection(*ncts):
            continue
        for c in grupo:
            outros = [o["uid"] for o in grupo if o is not c]
            c["motivos_revisao"].append(f"pmid_compartilhado: PMID {pmid} também é o de "
                                        f"{', '.join(outros)}, sem NCT em comum")
            c["requires_review"] = True
            c["analise"]["autoriza_automacao"] = False


# ── Registro completo ───────────────────────────────────────────────────────

def mapa_irmaos(estudos: list[dict]) -> dict[str, list[str]]:
    m: dict[str, list[str]] = defaultdict(list)
    for s in estudos:
        for n in identificadores(s)["nct"]:
            m[n].append(s["uid"])
    return dict(m)


def pedidos(dados: dict) -> tuple[list[str], list[str], list[str]]:
    """(identificadores para [si], PMIDs dos cards, NCTs para o CT.gov)."""
    idents, pmids, ncts = [], [], []
    for s in dados["studies"]:
        ids = identificadores(s)
        idents += ids["nct"] + ids["isrctn"]
        ncts += ids["nct"]
        if (p := pmid_do_card(s)):
            pmids.append(p)
    uniq = lambda xs: list(dict.fromkeys(xs))  # noqa: E731
    return uniq(idents), uniq(pmids), uniq(ncts)


def construir(dados: dict, coleta: dict, confirmacoes: dict | None = None,
              conflitos_fonte: list[dict] | None = None) -> dict:
    estudos = dados["studies"]
    irmaos = mapa_irmaos(estudos)
    cat_de = {s["uid"]: s.get("category_id", "") for s in estudos}
    if confirmacoes is None:
        confirmacoes, avisos_conf = ler_confirmacoes()
        decisoes = ler_decisoes()[0]
    else:
        avisos_conf, decisoes = [], []
    cards = [registrar_card(s, coleta, irmaos, cat_de, confirmacoes) for s in estudos]
    marcar_pmid_compartilhado(cards)
    desmarcar_primaria_de_outro_card(cards)
    reg = {
        "schema": "theratrials-db-registro/2",
        "gerado_em": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "coleta_em": coleta.get("gerado_em"),
        "crossref": coleta.get("crossref_status", "completa"),
        "fonte": "assets/js/data.js (somente leitura)",
        "regra_maturidade": "press release < abstract < artigo com análise interina < "
                            "publicação da análise primária < análise final / atualização madura; "
                            "substituição só entre análises comparáveis, e só com origem "
                            "explicit/human_confirmed",
        "avisos_confirmacoes": avisos_conf,
        "cards": cards,
    }
    conferir_uids(reg, dados)
    import db_confianca  # noqa: PLC0415 — depende deste módulo
    db_confianca.anotar(reg, dados, coleta, decisoes)
    if conflitos_fonte is None:
        conflitos_fonte = (json.loads(CONFLITOS_FONTE.read_text(encoding="utf-8")).get("achados", [])
                           if CONFLITOS_FONTE.exists() else [])
    db_confianca.aplicar_conflitos_na_fonte(reg, conflitos_fonte)
    return reg


# ── Relatório do registro ───────────────────────────────────────────────────

def resumo(reg: dict) -> dict:
    c = reg["cards"]
    return {
        "cards": len(c),
        "identidade": dict(Counter(x["identidade"]["nivel"] for x in c)),
        "requires_review": sum(x["requires_review"] for x in c),
        "origem_classificacao": dict(Counter(str(x["origem_classificacao"]) for x in c)),
        "confianca": dict(Counter(str(x["confianca"]) for x in c)),
        "automation": {d: dict(Counter(str(x["automation"][d].get("nivel")) for x in c))
                       for d in ("identity", "bibliographic_metadata", "publication_relationship",
                                 "clinical_extraction")},
        "autorizado": {d: sum(bool(x["automation"][d]["autorizado"]) for x in c)
                       for d in ("identity", "bibliographic_metadata", "publication_relationship",
                                 "clinical_extraction", "published_write")},
        "revisao": {k: sum(bool(x["revisao"][k]) for x in c)
                    for k in ("agora", "identidade_insuficiente", "clinico_sob_demanda", "editorial", "watch")},
        "situacao_registro": dict(Counter(x["identidade"]["situacao"] for x in c)),
        "com_nct": sum(bool(x["identidade"]["nct"]) for x in c),
        "com_isrctn": sum(bool(x["identidade"]["isrctn"]) for x in c),
        "com_pmid": sum(bool(x["pmid_atual"]) for x in c),
        "com_doi": sum(bool(x["doi"]) for x in c),
        "com_pmcid": sum(bool(x["pmcid"]) for x in c),
        "nct_compartilhado": sum(bool(x["identidade"]["nct_compartilhado_com"]) for x in c),
        "analise_nao_aplicavel": sum(not x["analise"]["aplicavel"] for x in c),
        "tipo_analise": dict(Counter(str(x["analise"]["tipo"]) for x in c if x["analise"]["aplicavel"])),
        "com_endpoint": sum(bool(x["analise"]["endpoint"]["valores"]) for x in c),
        "com_data_corte": sum(bool(x["analise"]["data_corte"]) for x in c),
        "publicacoes_ligadas": sum(len(x["publicacoes"]) for x in c),
        "relacoes": dict(Counter(p["relacao"] for x in c for p in x["publicacoes"])),
    }


def md_registro(reg: dict, coleta: dict) -> str:
    r = resumo(reg)
    L = [f"# Registro de identidade do Database — {reg['gerado_em'][:10]}", "",
         "Gerado por `scripts/db_registro.py` a partir de `assets/js/data.js` (somente leitura). "
         "Origem: `explicit` = a fonte diz; `inferred` = regra do pipeline, não autoriza nem "
         "bloqueia atualização; `machine_verified` = identidade/relação demonstrada por fontes "
         "independentes (db_confianca.py); `human_confirmed` = `db_decisoes.json`.", "",
         "| | |", "|---|---|"]
    L += [f"| {k} | {v} |" for k, v in r.items()]
    L += ["", f"Coleta: {coleta.get('gerado_em')} · {coleta.get('duracao_s')} s · chamadas "
          f"{coleta.get('chamadas')} · Crossref {coleta.get('crossref_status', 'completa')}", ""]
    fila = [x for x in reg["cards"] if x["requires_review"]]
    por_motivo: dict[str, list] = defaultdict(list)
    for x in fila:
        for m in x["revisao"]["agora"]:
            por_motivo[m.split(":")[0]].append((x, m))
    L += [f"## Decisão humana agora ({len(fila)} cards)", ""]
    for motivo, itens in sorted(por_motivo.items(), key=lambda kv: -len(kv[1])):
        L += [f"### {motivo} ({len(itens)})", ""]
        for x, m in itens:
            L.append(f"- `{x['uid']}` — {x['estudo']} · {x['identidade']['campo_nct'] or '—'} · "
                     f"PMID {x['pmid_atual'] or '—'} · {m.split(':', 1)[-1].strip()}")
        L.append("")
    insuf: dict[str, list] = defaultdict(list)
    for x in reg["cards"]:
        if x["automation"]["identity"]["nivel"] == "insuficiente":
            insuf[x["automation"]["identity"].get("falta") or "?"].append(x)
    L += [f"## Identidade não verificada, sem conflito ({sum(map(len, insuf.values()))} cards)", "",
          "Sem decisão agora: só pesa quando houver candidato de atualização para o card.", ""]
    for razao, itens in sorted(insuf.items(), key=lambda kv: -len(kv[1])):
        L += [f"### {razao} ({len(itens)})", ""]
        L += [f"- `{x['uid']}` — {x['estudo']} · famílias: "
              f"{', '.join(sorted(x['automation']['identity']['evidencias'])) or '—'}" for x in itens]
        L.append("")
    return "\n".join(L)


# ── CLI ─────────────────────────────────────────────────────────────────────

def obter_coleta(dados: dict, reusar: bool, usar_crossref: bool = True) -> dict:
    if reusar:
        return json.loads(SAIDA["coleta"].read_text(encoding="utf-8"))
    idents, pmids, ncts = pedidos(dados)
    print(f"[db] {len(idents)} identificadores de registro, {len(pmids)} PMIDs de card, "
          f"{len(ncts)} NCTs", file=sys.stderr)
    return db_fontes.coletar(idents, pmids, ncts, usar_crossref=usar_crossref)


def main(argv: list[str]) -> int:
    reusar = "--reusar-coleta" in argv
    dados = carregar_dados()
    try:
        coleta = obter_coleta(dados, reusar, "--sem-crossref" not in argv)
    except (RespostaParcial, urllib.error.URLError, TimeoutError, OSError) as e:
        print(f"FALHA TÉCNICA na coleta: {e}\nNada foi gravado.", file=sys.stderr)
        return FALHA_TECNICA
    reg = construir(dados, coleta)
    if not reusar:
        gravar(SAIDA["coleta"], json.dumps(coleta, ensure_ascii=False))
    gravar(SAIDA["registro"], json.dumps(reg, ensure_ascii=False, indent=1))
    gravar(SAIDA["registro_md"], md_registro(reg, coleta))
    print(json.dumps(resumo(reg), ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
