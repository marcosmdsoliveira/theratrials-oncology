"""bibliografia — camada bibliográfica estruturada do Database v2.

Fonte canônica da citação: a publicação REPRESENTADA pelo card (a que sustenta os dados exibidos), com metadados
de um snapshot offline do PubMed (bibliografia/pubmed_snapshot.json, gerado por snapshot_pubmed.py). Nada aqui
consulta a rede.

Regras:
  • autoria vem só dos metadados da publicação — nunca de `sponsor` (PI ≠ primeiro autor);
  • `ref` é texto editorial legado: não é fonte de autoria nem é reescrito;
  • o card só recebe `citation` estruturada quando a publicação representada passa em todas as guardas
    (elegibilidade()); caso contrário o frontend mostra o `ref` literal ou a referência do registro, sem autor;
  • evidence_collection não tem citação principal única;
  • conflito de identidade/relação entre publicações vai para o backlog, nunca é sobrescrito aqui.
"""
from __future__ import annotations

import html
import json
import pathlib
import re
import unicodedata

AQUI = pathlib.Path(__file__).resolve().parent
SNAPSHOT = AQUI / "bibliografia" / "pubmed_snapshot.json"
SNAPSHOT_SCHEMA = "theratrials-pubmed-snapshot/1"

PUBLICATION_ROLES = ["primary_publication", "update", "final", "long_term", "secondary_analysis",
                     "key_secondary_primary_analysis", "subgroup", "qol_pro", "safety", "translational", "pooled",
                     "correction", "congress", "congress_abstract", "undetermined"]
PUBLICATION_TYPES = ["journal_article", "guideline", "meta_analysis", "systematic_review", "review",
                     "congress_abstract", "erratum", "other"]
METADATA_SOURCES = ["pubmed_esummary", "crossref", "editorial"]          # "sponsor" nunca é fonte
SUFIXOS = {"Jr", "Jr.", "Sr", "Sr.", "2nd", "3rd", "III", "IV"}   # caixa importa: "JR" são iniciais
MAX_AUTORES_V1 = 6                                                      # Vancouver lista 6; AMA e ABNT usam menos
CAMPOS_CITATION = ["publication_id", "role", "pmid", "doi", "pmcid", "authors", "authors_total", "collective_name",
                   "first_author", "title", "journal", "journal_abbrev", "year", "volume", "issue", "pages",
                   "article_number", "publication_type", "metadata_source", "retrieved_at"]

# backlog: itens que tornam a publicação representada insegura para citação estruturada
TIPOS_BLOQUEIO = {"identifier_mismatch", "cross_source_conflict", "publication_relationship",
                  "bibliographic_mismatch", "aggregation"}
CAMPOS_BLOQUEIO = {"pubmed_url", "ref", "ano_pub", "titulo_full"}


# ── normalização ────────────────────────────────────────────────────────────────────────────────────────────
def fold(t: str | None) -> str:
    t = unicodedata.normalize("NFKD", t or "")
    return re.sub(r"[^a-z]", "", "".join(c for c in t if not unicodedata.combining(c)).lower())


def parse_nome(nome: str) -> dict:
    """'de Bono JS' → {family: 'de Bono', given_initials: 'JS'}; 'Wells SA Jr' → sufixo 'Jr'."""
    tok = (nome or "").split()
    suf = None
    if len(tok) > 2 and tok[-1] in SUFIXOS:
        suf = tok.pop()
    ini = ""
    if len(tok) > 1 and re.fullmatch(r"[A-Z]{1,4}", tok[-1]):
        ini = tok.pop()
    a = {"family": " ".join(tok), "given_initials": ini}
    if suf:
        a["suffix"] = suf.rstrip(".")
    return a


def nome_exibicao(a: dict) -> str:
    return " ".join(x for x in (a["family"], a.get("given_initials"), a.get("suffix")) if x)


def _titulo(t: str) -> str:
    t = html.unescape(re.sub(r"<[^>]+>", "", t or "")).strip()
    if t.startswith("[") and t.endswith("]."):               # título traduzido pelo PubMed: "[...]."
        t = t[1:-2]
    return t.rstrip(". ").strip()


def _paginas(pages: str | None) -> tuple[str | None, str | None]:
    p = (pages or "").strip()
    if not p:
        return None, None
    if "-" not in p and (p.lower().startswith("e") or len(p) >= 5):
        return None, p                                        # article number / e-page
    return p, None


def _tipo(pubtypes: list[str]) -> str:
    t = {x.lower() for x in pubtypes or []}
    for chave, tipo in [("published erratum", "erratum"), ("practice guideline", "guideline"), ("guideline", "guideline"),
                        ("meta-analysis", "meta_analysis"), ("systematic review", "systematic_review"),
                        ("congress", "congress_abstract"), ("review", "review")]:
        if chave in t:
            return tipo
    return "journal_article" if "journal article" in t else "other"


def publicacao_de_snapshot(s: dict, role: str = "undetermined") -> dict:
    """$def publication a partir de um registro do snapshot PubMed."""
    pessoais = [parse_nome(a["name"]) for a in s.get("authors", []) if a.get("authtype") == "Author"]
    coletivos = [a["name"] for a in s.get("authors", []) if a.get("authtype") == "CollectiveName"]
    pages, art = _paginas(s.get("pages"))
    ano = re.match(r"(\d{4})", s.get("pubdate") or "") or re.match(r"(\d{4})", s.get("epubdate") or "")
    pub = {
        "publication_id": f"pmid:{s['pmid']}", "role": role, "pmid": s["pmid"], "doi": s.get("doi"),
        "pmcid": s.get("pmcid"), "authors": pessoais, "authors_total": len(pessoais),
        "collective_name": coletivos[0] if coletivos else None,
        "first_author": nome_exibicao(pessoais[0]) if pessoais else (coletivos[0] if coletivos else None),
        "title": _titulo(s.get("title")), "journal": (s.get("fulljournalname") or "").strip() or None,
        "journal_abbrev": (s.get("source") or "").strip() or None, "year": int(ano.group(1)) if ano else None,
        "volume": s.get("volume") or None, "issue": s.get("issue") or None, "pages": pages, "article_number": art,
        "publication_type": _tipo(s.get("pubtype")), "metadata_source": "pubmed_esummary",
        "retrieved_at": s.get("retrieved_at"),
    }
    return {k: v for k, v in pub.items() if v not in (None, "")}     # campo ausente é omitido, nunca null


def citation_v1(pub: dict) -> dict:
    """Projeção v2 → v1 (campo opcional `citation` do card). Ordem de chaves fixa; até 6 autores pessoais."""
    c = {k: pub.get(k) for k in CAMPOS_CITATION}
    c["authors"] = [dict(a) for a in (pub.get("authors") or [])[:MAX_AUTORES_V1]]
    return {k: v for k, v in c.items() if v not in (None, "")}


def publicacao_de_citation(c: dict) -> dict:
    """Inverso de citation_v1 (para o lift): o card v1 carrega a publicação representada já normalizada."""
    pub = {k: c[k] for k in CAMPOS_CITATION if c.get(k) not in (None, "")}
    pub["authors"] = [dict(a) for a in c.get("authors") or []]
    return pub


def validar_publicacao(pub: dict) -> list[str]:
    """Invariantes do $def publication (usadas pelo validate_v2 e pelos testes)."""
    e = []
    for k in ("publication_id", "title", "year", "metadata_source"):
        if not pub.get(k):
            e.append(f"publication sem {k}")
    if pub.get("metadata_source") not in METADATA_SOURCES:
        e.append(f"metadata_source {pub.get('metadata_source')!r} não permitido (autoria nunca vem de sponsor)")
    if pub.get("role") not in PUBLICATION_ROLES:
        e.append(f"role {pub.get('role')!r} inválido")
    if pub.get("publication_type") not in PUBLICATION_TYPES:
        e.append(f"publication_type {pub.get('publication_type')!r} inválido")
    autores = pub.get("authors") or []
    if autores:
        if pub.get("first_author") != nome_exibicao(autores[0]):
            e.append(f"first_author {pub.get('first_author')!r} ≠ authors[0] {nome_exibicao(autores[0])!r}")
    elif pub.get("first_author") and pub.get("first_author") != pub.get("collective_name"):
        e.append("first_author sem autores pessoais tem de ser o collective_name")
    if pub.get("authors_total") is not None and pub["authors_total"] < len(autores):
        e.append("authors_total menor que a lista de autores")
    if pub.get("pmid") and pub.get("publication_id") != f"pmid:{pub['pmid']}":
        e.append("publication_id de publicação com PMID tem de ser 'pmid:<pmid>'")
    if pub.get("pages") and pub.get("article_number"):
        e.append("pages e article_number são exclusivos")
    return e


# ── elegibilidade (guardas genéricas; nenhuma regra por estudo) ─────────────────────────────────────────────
PARTICULAS = r"(?:(?:[Dd]e|[Dd]a|[Dd]el|[Dd]ella|[Dd]i|[Vv]an|[Vv]on|[Dd]er|[Dd]en|[Ll]e|[Ll]a|[Dd]u|[Dd]os|[Dd]as|St\.?)\s+)*"
REF_AUTOR = re.compile(r"(" + PARTICULAS + r"[A-ZÀ-Ý][A-Za-zÀ-ÿ'’\-]*[a-zà-ÿ][A-Za-zÀ-ÿ'’\-]*(?:\s+[A-ZÀ-Ý][a-zà-ÿ'’\-]+)?)"
                       r"\s+([A-Z]{1,4})(?=\s*(?:,|\.|;|\bet al|\bJr\b|$))")
ROTULO = re.compile(r"^\s*(?:análise primária|analise primaria|primary|atualização[^:]{0,30}|update[^:]{0,30}|"
                    r"publicação[^:]{0,30}|ref(?:erência)?[^:]{0,20}|fonte[^:]{0,20})\s*:\s*", re.I)


def ref_primeiro_autor(ref: str | None) -> str | None:
    m = REF_AUTOR.match(ROTULO.sub("", ref or ""))
    return m.group(1).strip() if m else None


def pmid_do_card(card: dict) -> str | None:
    m = re.search(r"pubmed\.ncbi\.nlm\.nih\.gov/(\d+)", str(card.get("pubmed_url") or ""))
    return m.group(1) if m else None


def ref_identifica(ref: str, pub: dict) -> bool:
    """O `ref` aponta explicitamente este artigo (PMID, DOI ou volume:1ª página)?"""
    r = ref or ""
    if pub.get("pmid") and pub["pmid"] in r:
        return True
    if pub.get("doi") and pub["doi"].lower() in r.lower():
        return True
    pg1 = (pub.get("pages") or pub.get("article_number") or "").split("-")[0]
    return bool(pub.get("volume") and pg1 and re.search(
        rf"\b{re.escape(pub['volume'])}\s*(?:\(\d+\))?\s*:\s*{re.escape(pg1)}\b", r))


def bloqueios_do_backlog(doc: dict) -> dict[str, list[str]]:
    b: dict[str, list[str]] = {}
    for x in doc.get("itens", []):
        if (x["status"] in ("open", "confirmed") and x["issue_type"] in TIPOS_BLOQUEIO
                and CAMPOS_BLOQUEIO & set(x.get("affected_fields") or [])):
            b.setdefault(x["uid"], []).append(x["id"])
    return b


# db_decisoes.json · classificacao/tipo_analise (vocabulário de db_registro.TIPOS) → papel da publicação
PAPEL_DE_TIPO_ANALISE = {"primary": "primary_publication", "final": "final", "long-term update": "long_term",
                         "interim": "update", "secondary": "secondary_analysis", "abstract": "congress_abstract"}


def colecoes_das_decisoes(decisoes: list[dict]) -> set[str]:
    """uids declarados evidence_collection por decisão humana (classificacao, campo record_type)."""
    return {d["uid"] for d in decisoes if d.get("tipo") == "classificacao" and d.get("campo") == "record_type"
            and d.get("valor") == "evidence_collection"}


def papeis_das_decisoes(decisoes: list[dict]) -> dict[tuple[str, str], str]:
    """(uid, pmid) → role, a partir de classificações humanas de tipo de análise. Vale só para aquele PMID."""
    return {(d["uid"], str(d["pmid"])): PAPEL_DE_TIPO_ANALISE[d["valor"]] for d in decisoes
            if d.get("tipo") == "classificacao" and d.get("campo") == "tipo_analise"
            and d.get("valor") in PAPEL_DE_TIPO_ANALISE and d.get("uid") and d.get("pmid")}


def elegibilidade(card: dict, snapshot: dict, bloqueios: dict, colecoes: set,
                  papeis: dict | None = None) -> tuple[dict | None, str]:
    """(publicação representada, motivo). Publicação None = sem citação estruturada, com o motivo."""
    uid = card["uid"]
    if str(card.get("status", "")).startswith("Em revisão"):
        return None, "quarentena_editorial"
    if uid in colecoes:
        return None, "evidence_collection"
    pmid = pmid_do_card(card)
    if not pmid:
        return None, "sem_pmid"
    if pmid not in snapshot:
        return None, "pmid_fora_do_snapshot"
    if uid in bloqueios:
        return None, "backlog:" + ",".join(sorted(bloqueios[uid]))
    pub = publicacao_de_snapshot(snapshot[pmid], role=(papeis or {}).get((uid, pmid), "undetermined"))
    ref = str(card.get("ref") or "")
    anos_ref = {int(y) for y in re.findall(r"\b(19[89]\d|20[0-3]\d)\b", ref)}
    try:
        ano_card = int(card.get("ano_pub"))
    except (TypeError, ValueError):
        ano_card = None
    y = pub.get("year")
    ano_ok = y is not None and ((ano_card is not None and abs(ano_card - y) <= 1)
                                or bool({y - 1, y, y + 1} & anos_ref) or ref_identifica(ref, pub))
    if not ano_ok:
        return None, "ano_nao_corroborado"
    autor_ref = ref_primeiro_autor(ref)
    if autor_ref and pub.get("authors"):
        fa, fr = fold(pub["authors"][0]["family"]), fold(autor_ref)
        if not (fa == fr or fa.endswith(fr) or fr.endswith(fa)) and not ref_identifica(ref, pub):
            return None, "ref_diverge_do_pmid"
    if validar_publicacao(pub):
        return None, "metadados_invalidos"
    return pub, "ok"


def carregar_snapshot(caminho: pathlib.Path = SNAPSHOT) -> dict:
    d = json.loads(caminho.read_text(encoding="utf-8"))
    if d.get("schema") != SNAPSHOT_SCHEMA:
        raise ValueError(f"snapshot com schema {d.get('schema')!r}")
    return d["records"]
