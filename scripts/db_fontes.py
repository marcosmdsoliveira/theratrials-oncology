#!/usr/bin/env python3
"""
db_fontes.py — coleta do pipeline do Database (data.js). Só leitura.

Fontes, todas estruturadas:
  • PubMed E-utilities — publicações ligadas ao registro (`NCT…[si]`,
    `ISRCTN…[si]`) e o registro de cada artigo (efetch XML: tipo de
    publicação, DOI, PMCID, erratum/retratação em CommentsCorrections).
  • NCBI ID Converter — PMCID e DOI dos artigos que estão no PMC.
  • ClinicalTrials.gov v2 — status, hasResults, datas de resultado e as
    referências que o patrocinador declara como RESULT.
  • Crossref — COMPLEMENTAR: só correções, erratas e retratações do DOI do
    card (`updated-by`, que inclui a base do Retraction Watch). A fonte de
    correção é o PubMed (CommentsCorrections); falha da Crossref não impede
    a coleta e fica registrada como verificação incompleta.

FONTES PROIBIDAS (ver db_PIPELINE.md): assets/data/tracker.json e
assets/data/explorer.json — nem descoberta, nem identidade, nem validação,
nem enriquecimento, nem proveniência. O tracker tem NCTs que não
correspondem ao estudo descrito; o Explorer é índice de descoberta do site,
não fonte clínica. Nenhum script db_* lê arquivo local além do data.js.
Não grava nada.

Resposta parcial segue o padrão do br_ctgov: repetir uma vez, conferir o
que foi pedido contra o que voltou e, se ainda faltar, abortar com
RespostaParcial. Ausência só é aceita quando a fonte a confirma (404 ou erro
explícito de "não encontrado" na consulta individual).

Variáveis de ambiente opcionais:
  NCBI_API_KEY   — 10 req/s em vez de 3 req/s no E-utilities.
  DB_CONTATO     — e-mail de contato enviado ao NCBI (`email`) e à Crossref
                   (`mailto`, pool educado). Sem ele, a coleta funciona com
                   os limites públicos.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from br_ctgov import UA, RespostaParcial, http_json  # noqa: E402

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
IDCONV = "https://pmc.ncbi.nlm.nih.gov/tools/idconv/api/v1/articles/"
CROSSREF = "https://api.crossref.org/works/"
CTGOV = "https://clinicaltrials.gov/api/v2/studies"

API_KEY = os.environ.get("NCBI_API_KEY", "")
CONTATO = os.environ.get("DB_CONTATO", "")
PAUSA_NCBI = 0.11 if API_KEY else 0.34
PAUSA_CROSSREF = 0.12 if CONTATO else 0.25

# Quantas chamadas cada fonte recebeu nesta execução (vai para o relatório).
CHAMADAS: Counter = Counter()

# Arquivos locais que nenhum script db_* pode ler (checado por
# garantir_fonte_permitida e por test_db_freshness.py).
FONTES_PROIBIDAS = ("assets/data/tracker.json", "assets/data/tracker.js",
                    "assets/data/explorer.json", "assets/data/explorer.js")


def garantir_fonte_permitida(caminho) -> None:
    alvo = str(caminho).replace("\\", "/")
    if any(alvo.endswith(f) for f in FONTES_PROIBIDAS):
        raise PermissionError(f"fonte proibida para o Database: {caminho}")


CAMPOS_CTGOV = "|".join([
    "protocolSection.identificationModule.nctId",
    "protocolSection.identificationModule.acronym",
    "protocolSection.identificationModule.briefTitle",
    "protocolSection.identificationModule.officialTitle",
    "protocolSection.statusModule",
    "protocolSection.referencesModule.references",
    "hasResults",
])

# CommentsCorrections que mudam a confiança no artigo. CommentIn e afins não.
CORRECOES_PUBMED = {
    "RetractionIn": "retratacao",
    "ExpressionOfConcernIn": "expressao_de_preocupacao",
    "ErratumIn": "errata",
    "CorrectedandRepublishedIn": "corrigido_e_republicado",
    "RepublishedIn": "republicado",
    "UpdateIn": "atualizacao",
}
# Tipos da Crossref em `updated-by` que interessam aqui.
CORRECOES_CROSSREF = {
    "retraction": "retratacao",
    "withdrawal": "retratacao",
    "removal": "retratacao",
    "expression_of_concern": "expressao_de_preocupacao",
    "correction": "errata",
    "erratum": "errata",
    "corrigendum": "errata",
    "partial_retraction": "retratacao",
}


# ── HTTP ─────────────────────────────────────────────────────────────────────

def http_texto(url: str, tentativas: int = 4) -> str:
    """Mesmo contrato do br_ctgov.http_json, para respostas XML."""
    for n in range(tentativas):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA),
                                        timeout=90) as r:
                return r.read().decode("utf-8")
        except Exception as e:  # noqa: BLE001
            if isinstance(e, urllib.error.HTTPError) and 400 <= e.code < 500 and e.code != 429:
                raise
            if n == tentativas - 1:
                raise
            espera = 2 ** n
            print(f"[db] {e} — nova tentativa em {espera}s", file=sys.stderr)
            time.sleep(espera)
    raise RuntimeError("inalcançável")


def _ncbi_url(rota: str, **params) -> str:
    params.setdefault("tool", "theratrials")
    if API_KEY:
        params["api_key"] = API_KEY
    if CONTATO:
        params["email"] = CONTATO
    return f"{EUTILS}/{rota}?{urllib.parse.urlencode(params)}"


def _ncbi_json(rota: str, **params) -> dict:
    CHAMADAS["pubmed"] += 1
    d = http_json(_ncbi_url(rota, retmode="json", **params))
    time.sleep(PAUSA_NCBI)
    # O NCBI às vezes responde 200 com {"error": "API rate limit exceeded"}.
    if isinstance(d, dict) and "error" in d and "esearchresult" not in d and "result" not in d:
        raise RespostaParcial(f"E-utilities respondeu erro: {d['error']}")
    return d


# ── PubMed: publicações ligadas ao registro ─────────────────────────────────

def pmids_ligados(ident: str, lote: int = 500, tentativas: int = 3) -> list[str]:
    """PMIDs que o PubMed liga ao identificador de registro (`[si]`).

    `count` é o total que o PubMed diz ter; a lista devolvida tem de fechar
    com ele. Resposta malformada (sem `count`, com ERROR) e lista incompleta
    são tratadas igual: nova tentativa com espera crescente; se persistir
    depois de `tentativas`, é resposta parcial e a coleta aborta."""
    def uma_vez() -> list[str]:
        ids: list[str] = []
        inicio = 0
        while True:
            d = _ncbi_json("esearch.fcgi", db="pubmed", term=f"{ident}[si]",
                           retmax=str(lote), retstart=str(inicio))
            r = d.get("esearchresult")
            if not isinstance(r, dict) or "ERROR" in r or "count" not in r:
                raise RespostaParcial(f"{ident}: esearch sem esearchresult/count válido "
                                      f"({json.dumps(d)[:160]})")
            total = int(r["count"])
            ids += r.get("idlist", [])
            inicio += lote
            if inicio >= total:
                if len(set(ids)) != total:
                    raise RespostaParcial(f"{ident}: esearch devolveu {len(set(ids))} de "
                                          f"{total} PMIDs")
                return ids

    for n in range(tentativas):
        try:
            return sorted(set(uma_vez()), key=int)
        except RespostaParcial as e:
            if n == tentativas - 1:
                raise
            espera = 3 * 2 ** n
            print(f"[db] {e} — nova tentativa em {espera}s", file=sys.stderr)
            time.sleep(espera)
    raise RuntimeError("inalcançável")


# ── PubMed: registro de cada artigo ─────────────────────────────────────────

def _texto(e) -> str:
    return re.sub(r"\s+", " ", "".join(e.itertext())).strip() if e is not None else ""


_MESES = {m: i for i, m in enumerate(
    "jan feb mar apr may jun jul aug sep oct nov dec".split(), 1)}


def _data(e) -> str:
    """AAAA-MM-DD, AAAA-MM ou AAAA a partir de um nó de data do PubMed."""
    if e is None:
        return ""
    ano = e.findtext("Year")
    if not ano:
        m = re.search(r"(19|20)\d\d", e.findtext("MedlineDate") or "")
        return m.group(0) if m else ""
    mes = (e.findtext("Month") or "").strip()
    if mes and not mes.isdigit():
        mes = str(_MESES.get(mes[:3].lower(), ""))
    dia = (e.findtext("Day") or "").strip()
    partes = [ano] + ([mes.zfill(2)] if mes else []) + ([dia.zfill(2)] if mes and dia else [])
    return "-".join(partes)


def parse_efetch(xml: str) -> dict[str, dict]:
    """Um dicionário por PubmedArticle. IDs vêm só de PubmedData/ArticleIdList
    — a ReferenceList do mesmo XML também tem ArticleId, dos artigos citados."""
    raiz = ET.fromstring(xml)
    out: dict[str, dict] = {}
    for a in raiz.findall("PubmedArticle"):
        mc = a.find("MedlineCitation")
        art = mc.find("Article")
        pmid = mc.findtext("PMID")
        ids = {i.get("IdType"): (i.text or "").strip()
               for i in a.findall("PubmedData/ArticleIdList/ArticleId")}
        doi = ids.get("doi") or next(
            ((x.text or "").strip() for x in art.findall("ELocationID")
             if x.get("EIdType") == "doi"), "")
        resumo = " ".join(
            ((t.get("Label") + ": ") if t.get("Label") else "") + _texto(t)
            for t in art.findall("Abstract/AbstractText"))
        eletronica = next((x for x in art.findall("ArticleDate")
                           if x.get("DateType") == "Electronic"), None)
        impressa = art.find("Journal/JournalIssue/PubDate")
        d_ele, d_imp = _data(eletronica), _data(impressa)
        correcoes = []
        for c in mc.findall("CommentsCorrectionsList/CommentsCorrections"):
            tipo = CORRECOES_PUBMED.get(c.get("RefType", ""))
            if tipo:
                correcoes.append({"tipo": tipo, "fonte": "pubmed",
                                  "pmid": c.findtext("PMID") or "",
                                  "ref": c.findtext("RefSource") or ""})
        out[pmid] = {
            "pmid": pmid,
            "titulo": _texto(art.find("ArticleTitle")),
            "resumo": resumo,
            "periodico": art.findtext("Journal/ISOAbbreviation") or art.findtext("Journal/Title") or "",
            # A data eletrônica é a primeira aparição; a impressa pode vir meses depois.
            "data": min([d for d in (d_ele, d_imp) if d], default=""),
            "pubtypes": [_texto(p) for p in art.findall("PublicationTypeList/PublicationType")],
            "doi": doi.lower(),
            "pmcid": ids.get("pmc", ""),
            "primeiro_autor": (mc.findtext("Article/AuthorList/Author/LastName") or
                               mc.findtext("Article/AuthorList/Author/CollectiveName") or ""),
            "registros": sorted({(n.text or "").strip() for n in
                                 mc.findall("Article/DataBankList/DataBank/AccessionNumberList/AccessionNumber")}),
            "correcoes": correcoes,
        }
    return out


def _efetch(pmids: list[str]) -> dict[str, dict]:
    CHAMADAS["pubmed"] += 1
    xml = http_texto(_ncbi_url("efetch.fcgi", db="pubmed", retmode="xml", id=",".join(pmids)))
    time.sleep(PAUSA_NCBI)
    return parse_efetch(xml)


def _existe_no_pubmed(pmid: str) -> bool:
    """Consulta individual. False só se o PubMed disser explicitamente que não
    há registro — ausência confirmada, como o 404 do CT.gov."""
    d = _ncbi_json("esummary.fcgi", db="pubmed", id=pmid)
    item = d.get("result", {}).get(pmid)
    if item is None:
        raise RespostaParcial(f"PMID {pmid}: esummary respondeu sem o item pedido")
    return "error" not in item


def buscar_artigos(pmids: list[str], lote: int = 200,
                   max_ausentes: int = 3) -> tuple[dict[str, dict], list[str]]:
    """(artigos, ausentes_confirmados). Lote incompleto é repetido; o que
    continuar faltando é conferido um a um e só é aceito como ausente se o
    PubMed confirmar. Mais de `max_ausentes` faltando num lote aborta."""
    out: dict[str, dict] = {}
    ausentes: list[str] = []
    for i in range(0, len(pmids), lote):
        parte = pmids[i:i + lote]
        achados = _efetch(parte)
        faltam = [p for p in parte if p not in achados]
        if faltam:
            print(f"[db] efetch lote {i // lote + 1}: {len(faltam)} de {len(parte)} não voltaram "
                  f"— nova tentativa", file=sys.stderr)
            time.sleep(3)
            achados.update(_efetch(faltam))
            faltam = [p for p in parte if p not in achados]
        if len(faltam) > max_ausentes:
            raise RespostaParcial(
                f"efetch lote {i // lote + 1}: {len(faltam)} de {len(parte)} PMIDs não voltaram "
                f"mesmo após nova tentativa ({', '.join(faltam[:5])})")
        for p in faltam:
            if _existe_no_pubmed(p):
                raise RespostaParcial(f"PMID {p} existe no PubMed, mas o efetch não o devolveu")
            print(f"[db] PMID {p}: sem registro no PubMed — ausência confirmada", file=sys.stderr)
            ausentes.append(p)
        out.update({p: a for p, a in achados.items() if p in parte})
        print(f"[db] artigos {min(i + lote, len(pmids))}/{len(pmids)}", file=sys.stderr)
    return out, ausentes


# ── NCBI ID Converter ───────────────────────────────────────────────────────

def converter_ids(pmids: list[str], lote: int = 200) -> dict[str, dict]:
    """{pmid: {doi, pmcid}} para quem está no PMC; {} para quem não está.
    Todo PMID pedido tem de voltar como registro — com ou sem erro."""
    out: dict[str, dict] = {}
    for i in range(0, len(pmids), lote):
        parte = pmids[i:i + lote]
        params = {"ids": ",".join(parte), "format": "json", "tool": "theratrials"}
        if CONTATO:
            params["email"] = CONTATO

        def uma_vez() -> dict[str, dict]:
            CHAMADAS["idconv"] += 1
            d = http_json(f"{IDCONV}?{urllib.parse.urlencode(params)}")
            time.sleep(PAUSA_NCBI)
            if d.get("status") != "ok":
                raise RespostaParcial(f"ID Converter respondeu status {d.get('status')!r}")
            r = {}
            for rec in d.get("records", []):
                pid = str(rec.get("requested-id") or rec.get("pmid") or "")
                r[pid] = {} if rec.get("status") == "error" else {
                    "doi": (rec.get("doi") or "").lower(), "pmcid": rec.get("pmcid") or ""}
            return r

        achados = uma_vez()
        if any(p not in achados for p in parte):
            time.sleep(3)
            achados = uma_vez()
            faltam = [p for p in parte if p not in achados]
            if faltam:
                raise RespostaParcial(f"ID Converter: {len(faltam)} de {len(parte)} PMIDs sem registro")
        out.update({p: achados[p] for p in parte})
    return out


# ── Crossref: correções e retratações ───────────────────────────────────────

def crossref_atualizacoes(doi: str, tentativas: int = 3) -> list[dict] | None:
    """Avisos que atualizam o DOI (`updated-by`). None se o DOI não está na
    Crossref (404 — outra agência de registro); isso não é falha. Resposta
    sem a obra pedida é repetida; se persistir, aborta."""
    for n in range(tentativas):
        try:
            return _crossref_uma(doi)
        except RespostaParcial as e:
            if n == tentativas - 1:
                raise
            print(f"[db] {e} — nova tentativa em {3 * 2 ** n}s", file=sys.stderr)
            time.sleep(3 * 2 ** n)
    raise RuntimeError("inalcançável")


def _crossref_uma(doi: str) -> list[dict] | None:
    q = f"?mailto={urllib.parse.quote(CONTATO)}" if CONTATO else ""
    CHAMADAS["crossref"] += 1
    try:
        d = http_json(f"{CROSSREF}{urllib.parse.quote(doi, safe='/()')}{q}")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise
    finally:
        time.sleep(PAUSA_CROSSREF)
    msg = d.get("message")
    if not isinstance(msg, dict) or (msg.get("DOI") or "").lower() != doi.lower():
        raise RespostaParcial(f"Crossref: resposta sem a obra pedida ({doi})")
    out = []
    for u in msg.get("updated-by", []) or []:
        tipo = CORRECOES_CROSSREF.get(u.get("type", ""))
        if tipo:
            partes = (u.get("updated") or {}).get("date-parts") or [[]]
            out.append({"tipo": tipo, "fonte": f"crossref:{u.get('source', '')}",
                        "doi": (u.get("DOI") or "").lower(),
                        "data": "-".join(str(x).zfill(2) for x in partes[0])})
    return out


# ── ClinicalTrials.gov v2 ───────────────────────────────────────────────────

def _resumo_ctgov(s: dict) -> dict:
    p = s.get("protocolSection", {})
    st = p.get("statusModule", {})
    return {
        "nct": p.get("identificationModule", {}).get("nctId", ""),
        "acronimo": p.get("identificationModule", {}).get("acronym", ""),
        "titulo_breve": p.get("identificationModule", {}).get("briefTitle", ""),
        "titulo_oficial": p.get("identificationModule", {}).get("officialTitle", ""),
        "status": st.get("overallStatus", ""),
        "why_stopped": st.get("whyStopped", ""),
        "has_results": bool(s.get("hasResults")),
        "results_first_post": (st.get("resultsFirstPostDateStruct") or {}).get("date", ""),
        "last_update_post": (st.get("lastUpdatePostDateStruct") or {}).get("date", ""),
        "primary_completion": (st.get("primaryCompletionDateStruct") or {}).get("date", ""),
        "referencias": sorted(
            ({"pmid": r.get("pmid", ""), "tipo": r.get("type", "")}
             for r in p.get("referencesModule", {}).get("references", []) if r.get("pmid")),
            key=lambda r: (r["tipo"], r["pmid"])),
    }


def _ctgov_lote(parte: list[str], lote: int) -> dict[str, dict]:
    CHAMADAS["ctgov"] += 1
    q = urllib.parse.urlencode({"filter.ids": "|".join(parte), "fields": CAMPOS_CTGOV,
                                "pageSize": str(lote * 2)})
    out = {}
    for s in http_json(f"{CTGOV}?{q}").get("studies", []):
        r = _resumo_ctgov(s)
        if r["nct"] in parte:
            out[r["nct"]] = r
    return out


def _ctgov_um(nct: str) -> dict | None:
    CHAMADAS["ctgov"] += 1
    try:
        d = http_json(f"{CTGOV}/{nct}?{urllib.parse.urlencode({'fields': CAMPOS_CTGOV})}")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise
    if not d.get("protocolSection"):
        raise RespostaParcial(f"{nct}: consulta individual respondeu 200 sem o registro")
    return _resumo_ctgov(d)


def registros_ctgov(ncts: list[str], lote: int = 50) -> dict[str, dict | None]:
    """Mesma disciplina do br_ctgov.buscar_por_ids. None = 404 confirmado."""
    out: dict[str, dict | None] = {}
    for i in range(0, len(ncts), lote):
        parte = ncts[i:i + lote]
        achados = _ctgov_lote(parte, lote)
        faltam = [n for n in parte if n not in achados]
        if faltam:
            time.sleep(3)
            achados.update(_ctgov_lote(faltam, lote))
            faltam = [n for n in parte if n not in achados]
        if len(faltam) > 1:
            raise RespostaParcial(f"CT.gov lote {i // lote + 1}: {len(faltam)} de {len(parte)} "
                                  f"NCTs não voltaram ({', '.join(faltam[:5])})")
        for nct in faltam:
            r = _ctgov_um(nct)
            if r is not None and r["nct"] != nct:
                raise RespostaParcial(f"{nct}: consulta individual devolveu registro inesperado")
            achados[nct] = r
        out.update(achados)
        time.sleep(0.4)
    return out


# ── Busca por título ────────────────────────────────────────────────────────

def pmids_por_titulo(titulo: str) -> list[str]:
    """Candidatos para um título: palavras significativas com [ti], ligadas por
    AND (a busca por frase exata não funciona para títulos longos no PubMed).
    Quem decide se o título é o mesmo é a comparação exata, depois, em
    db_confianca. Mesma disciplina de contagem do [si]."""
    palavras = [w for w in re.findall(r"[A-Za-z][A-Za-z0-9]{3,}", titulo)
                if w.lower() not in {"with", "versus", "from", "after", "patients", "trial",
                                     "study", "phase", "randomized", "randomised", "among",
                                     "without", "plus", "treatment", "therapy"}][:8]
    if len(palavras) < 3:
        return []
    termo = " AND ".join(f"{w}[ti]" for w in palavras)
    for n in range(3):
        try:
            d = _ncbi_json("esearch.fcgi", db="pubmed", term=termo, retmax="20")
        except RespostaParcial:
            d = {}
        r = d.get("esearchresult")
        if isinstance(r, dict) and "count" in r and "ERROR" not in r and \
                len(r.get("idlist", [])) == min(int(r["count"]), 20):
            return r.get("idlist", [])
        time.sleep(3 * 2 ** n)
    raise RespostaParcial(f"busca por título sem resposta válida: {titulo[:60]!r}")


# ── Complemento: títulos do CT.gov, notas de errata, busca por título ───────

def complementar(coleta: dict, ncts: list[str], pmids_avisos: list[str],
                 titulos: dict[str, str]) -> dict:
    """Acrescenta à coleta o que as regras de verificação precisam:
      ctgov        — títulos/acrônimo de todos os NCTs pedidos (inclusive os
                     declarados pelo artigo e que o card não cita);
      avisos       — registro PubMed de cada nota de errata/retratação;
      por_titulo   — {uid: PMIDs com título idêntico ao `titulo_full`} e os
                     artigos correspondentes.
    Resposta parcial aborta, como na coleta principal."""
    t0 = time.time()
    antes = dict(CHAMADAS)
    novo = dict(coleta)
    novo["ctgov"] = dict(coleta["ctgov"])
    novo["ctgov"].update(registros_ctgov(sorted(set(ncts))))
    avisos, ausentes = buscar_artigos(sorted(set(pmids_avisos), key=int)) if pmids_avisos else ({}, [])
    por_titulo = {uid: pmids_por_titulo(t) for uid, t in titulos.items() if t}
    extra = sorted({p for ps in por_titulo.values() for p in ps} - set(coleta["artigos"]), key=int)
    artigos = dict(coleta["artigos"])
    if extra:
        artigos.update(buscar_artigos(extra)[0])
    novo.update(artigos=artigos, avisos=avisos, avisos_ausentes=ausentes, por_titulo=por_titulo,
                complemento_em=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                complemento_chamadas={k: CHAMADAS[k] - antes.get(k, 0) for k in CHAMADAS},
                complemento_s=round(time.time() - t0, 1))
    return novo


# ── Coleta completa ─────────────────────────────────────────────────────────

def coletar(identificadores: list[str], pmids_cards: list[str], ncts: list[str],
            usar_crossref: bool = True) -> dict:
    """Tudo o que o registro e o freshness precisam, numa passada.

    identificadores — NCT e ISRCTN para o `[si]`;
    pmids_cards     — os PMIDs que os cards citam hoje (entram mesmo sem [si]);
    ncts            — para o CT.gov.
    Qualquer RespostaParcial sobe: coleta parcial não produz relatório."""
    t0 = time.time()
    CHAMADAS.clear()
    si: dict[str, list[str]] = {}
    for n, ident in enumerate(identificadores, 1):
        si[ident] = pmids_ligados(ident)
        if n % 50 == 0:
            print(f"[db] [si] {n}/{len(identificadores)}", file=sys.stderr)

    ctgov = registros_ctgov(ncts)
    declarados = {r["pmid"] for c in ctgov.values() if c for r in c["referencias"]}

    todos = sorted(set(pmids_cards) | {p for v in si.values() for p in v} | declarados, key=int)
    artigos, ausentes = buscar_artigos(todos)
    idconv = converter_ids(sorted(set(pmids_cards) & set(artigos), key=int))

    # Crossref é complementar: uma falha aqui não invalida o que o PubMed e o
    # CT.gov responderam. O DOI fica marcado como não verificado.
    crossref: dict[str, list | None] = {}
    crossref_falhas: list[str] = []
    if usar_crossref:
        for p in pmids_cards:
            doi = (artigos.get(p) or {}).get("doi") or idconv.get(p, {}).get("doi")
            if doi and doi not in crossref and doi not in crossref_falhas:
                try:
                    crossref[doi] = crossref_atualizacoes(doi)
                except (RespostaParcial, urllib.error.URLError, TimeoutError, OSError) as e:
                    print(f"[db] Crossref {doi}: {e} — segue sem esta verificação", file=sys.stderr)
                    crossref_falhas.append(doi)

    return {
        "schema": "theratrials-db-coleta/1",
        "gerado_em": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "si": si,
        "ctgov": ctgov,
        "artigos": artigos,
        "ausentes_pubmed": ausentes,
        "idconv": idconv,
        "crossref": crossref,
        "crossref_status": ("desligada" if not usar_crossref else
                            "incompleta" if crossref_falhas else "completa"),
        "crossref_falhas": crossref_falhas,
        "chamadas": dict(CHAMADAS),
        "duracao_s": round(time.time() - t0, 1),
    }


if __name__ == "__main__":
    print(json.dumps(pmids_ligados(sys.argv[1]) if len(sys.argv) > 1 else {}, indent=1))
