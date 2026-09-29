"""sources — coleta DETERMINÍSTICA das fontes permitidas, com cache e índice de parágrafos.

Fontes permitidas: PubMed (esummary/efetch), PMC via Europe PMC (texto completo aberto), ClinicalTrials.gov API v2.
Proibidas como verdade do Database: tracker.json, Explorer, snippets secundários, memória do modelo — nunca coletadas.

Cada fonte vira um texto com parágrafos numerados e localizáveis:
    ¶0012 [Results > Safety] texto do parágrafo…
O localizador de uma evidência é "¶0012" (+ seção). O verificador confere o trecho literal nesse parágrafo.

Cache em scripts/db_v2/state/cache/ (ignorado pelo git). Sem --rede, só lê o cache (execução offline reprodutível).
"""
from __future__ import annotations

import datetime
import json
import pathlib
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

AQUI = pathlib.Path(__file__).resolve().parent
STATE = AQUI.parent / "state"
CACHE = STATE / "cache"
EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
EUROPEPMC = "https://www.ebi.ac.uk/europepmc/webservices/rest/"
CTGOV = "https://clinicaltrials.gov/api/v2/studies/"
FONTES_PERMITIDAS_HOSTS = ("eutils.ncbi.nlm.nih.gov", "www.ebi.ac.uk", "clinicaltrials.gov")


class SemCache(Exception):
    pass


def _get(url: str, rede: bool, destino: pathlib.Path) -> tuple[bytes, str]:
    """Conteúdo + retrieved_at. Com cache, nunca vai à rede."""
    meta = destino.with_suffix(destino.suffix + ".meta.json")
    if destino.exists() and meta.exists():
        return destino.read_bytes(), json.loads(meta.read_text())["retrieved_at"]
    if not rede:
        raise SemCache(str(destino))
    assert urllib.parse.urlparse(url).hostname in FONTES_PERMITIDAS_HOSTS, url
    time.sleep(0.35)
    status = 200
    for tentativa in range(2):
        try:
            dados = urllib.request.urlopen(url, timeout=60).read()
            break
        except urllib.error.HTTPError as e:      # 4xx/5xx: fonte indisponível (ex.: texto não aberto na Europe PMC)
            dados, status = b"", e.code
            break
        except urllib.error.URLError:
            if tentativa:
                raise
            time.sleep(2)
    hoje = datetime.date.today().isoformat()
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_bytes(dados)
    meta.write_text(json.dumps({"url": url, "retrieved_at": hoje, "http_status": status}))
    return dados, hoje


def _txt(el) -> str:
    return re.sub(r"\s+", " ", "".join(el.itertext())).strip() if el is not None else ""


# ── PubMed ──────────────────────────────────────────────────────────────────────────────────────────────────
def pubmed_efetch(pmid: str, rede: bool) -> dict:
    raw, quando = _get(f"{EUTILS}efetch.fcgi?db=pubmed&id={pmid}&retmode=xml", rede, CACHE / "pubmed" / f"{pmid}.xml")
    if not raw:
        return {}
    art = ET.fromstring(raw).find(".//PubmedArticle")
    if art is None:
        return {}
    blocos = []
    for ab in art.findall(".//Abstract/AbstractText"):
        blocos.append(((ab.get("Label") or "Abstract").title(), _txt(ab)))
    nct = sorted({_txt(a) for db in art.findall(".//DataBank") if _txt(db.find("DataBankName")) == "ClinicalTrials.gov"
                  for a in db.findall(".//AccessionNumber")})
    ids = {i.get("IdType"): _txt(i) for i in art.findall(".//PubmedData/ArticleIdList/ArticleId")}
    tipos = [_txt(t) for t in art.findall(".//PublicationType")]
    return {"pmid": pmid, "title": _txt(art.find(".//ArticleTitle")), "abstract": blocos, "databank_nct": nct,
            "pmcid": ids.get("pmc"), "doi": ids.get("doi"), "pubtypes": tipos, "retrieved_at": quando}


def pubmed_por_nct(nct: str, rede: bool) -> tuple[list[str], str]:
    raw, quando = _get(f"{EUTILS}esearch.fcgi?db=pubmed&retmode=json&retmax=50&term={nct}%5Bsi%5D", rede,
                       CACHE / "esearch" / f"{nct}.json")
    return (json.loads(raw)["esearchresult"]["idlist"] if raw else []), quando


def pubmed_esummary(pmids: list[str], rede: bool) -> dict:
    out = {}
    for p in pmids:
        raw, _ = _get(f"{EUTILS}esummary.fcgi?db=pubmed&retmode=json&id={p}", rede, CACHE / "esummary" / f"{p}.json")
        if raw:
            r = json.loads(raw).get("result", {}).get(p)
            if r and "error" not in r:
                out[p] = r
    return out


# ── texto completo (Europe PMC, JATS) ───────────────────────────────────────────────────────────────────────
def pmc_fulltext(pmcid: str, rede: bool) -> list[tuple[str, str]]:
    raw, _ = _get(f"{EUROPEPMC}{pmcid}/fullTextXML", rede, CACHE / "pmc" / f"{pmcid}.xml")
    if not raw or b"<body" not in raw:          # fallback: PMC da NCBI (inclui manuscritos de autor)
        raw, _ = _get(f"{EUTILS}efetch.fcgi?db=pmc&id={pmcid.removeprefix('PMC')}&retmode=xml", rede,
                      CACHE / "pmc_ncbi" / f"{pmcid}.xml")
    if not raw or b"<body" not in raw:
        return []
    raiz = ET.fromstring(raw)
    pars: list[tuple[str, str]] = []
    for ab in raiz.findall(".//front//abstract"):
        for p in ab.iter("p"):
            pars.append(("Abstract", _txt(p)))

    def sec(el, trilha):
        titulo = _txt(el.find("title"))
        t = trilha + [titulo] if titulo else trilha
        for filho in el:
            if filho.tag == "p":
                pars.append((" > ".join(t) or "Body", _txt(filho)))
            elif filho.tag == "sec":
                sec(filho, t)
            elif filho.tag in ("table-wrap", "fig"):
                rot = _txt(filho.find("label")) or filho.tag
                pars.append((" > ".join(t + [rot]), (rot + " " + _txt(filho.find("caption"))).strip()))
                for tr in filho.iter("tr"):
                    cel = [_txt(c) for c in tr if c.tag in ("td", "th")]
                    if any(cel):
                        pars.append((" > ".join(t + [rot]), " | ".join(cel)))
                for fn in filho.iter("fn"):
                    pars.append((" > ".join(t + [rot, "footnote"]), _txt(fn)))
    body = raiz.find(".//body")
    if body is not None:
        sec(body, [])
    for tw in raiz.findall(".//back//table-wrap") + raiz.findall(".//floats-group//table-wrap"):
        rot = _txt(tw.find("label")) or "table"
        pars.append((rot, (rot + " " + _txt(tw.find("caption"))).strip()))
        for tr in tw.iter("tr"):
            cel = [_txt(c) for c in tr if c.tag in ("td", "th")]
            if any(cel):
                pars.append((rot, " | ".join(cel)))
    return [(s, p) for s, p in pars if p]


# ── ClinicalTrials.gov ──────────────────────────────────────────────────────────────────────────────────────
def ctgov(nct: str, rede: bool) -> dict:
    raw, quando = _get(f"{CTGOV}{nct}?format=json", rede, CACHE / "ctgov" / f"{nct}.json")
    return (json.loads(raw) | {"_retrieved_at": quando}) if raw else {}


def ctgov_paragrafos(rec: dict) -> list[tuple[str, str]]:
    pars = []

    def walk(o, path):
        if isinstance(o, dict):
            for k, v in o.items():
                if not k.startswith("_"):
                    walk(v, f"{path}.{k}" if path else k)
        elif isinstance(o, list):
            if all(not isinstance(x, (dict, list)) for x in o):
                pars.append((path, "; ".join(str(x) for x in o)))
            else:
                for i, v in enumerate(o):
                    walk(v, f"{path}[{i}]")
        elif o not in (None, ""):
            pars.append((path, str(o)))
    walk(rec, "")
    return pars


# ── gravação com parágrafos numerados ───────────────────────────────────────────────────────────────────────
def gravar_fonte(pasta: pathlib.Path, source_id: str, pars: list[tuple[str, str]]) -> pathlib.Path:
    nome = re.sub(r"[^A-Za-z0-9_.-]+", "_", source_id) + ".txt"
    linhas = [f"¶{i:04d} [{sec}] {txt}" for i, (sec, txt) in enumerate(pars, 1)]
    p = pasta / nome
    p.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    return p


def ler_paragrafos(caminho: pathlib.Path) -> dict[str, str]:
    """{NNNN: "[Seção] texto"}. Texto com quebra de linha (ex.: critérios de elegibilidade do CT.gov) continua o
    parágrafo anterior — a numeração ¶ não muda."""
    out, atual = {}, None
    for linha in caminho.read_text(encoding="utf-8").splitlines():
        m = re.match(r"¶(\d{4}) \[(.*?)\] (.*)$", linha)
        if m:
            atual = m.group(1)
            out[atual] = f"[{m.group(2)}] {m.group(3)}"
        elif atual is not None:
            out[atual] += " " + linha
    return out
