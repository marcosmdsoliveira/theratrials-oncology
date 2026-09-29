"""evidence_packet — ESTÁGIO 0, determinístico: tudo que dá para resolver sem LLM, por card.

    python3 scripts/db_v2/agents/evidence_packet.py --uid <uid> [--card-ref <commit>] [--rede]
    python3 scripts/db_v2/agents/evidence_packet.py --corpus [--rede]

Resolve deterministicamente: identidade PMID/NCT/DOI (cruzamento PubMed DataBank × CT.gov references), metadados
bibliográficos (snapshot), status do registro, publicações ligadas ao NCT que o card ainda não representa,
deduplicação contra o backlog, relações já decididas por humano, quarentena, freshness e o inventário de trechos
(fontes com parágrafos numerados). Só o que sobra — interpretação semântica, correspondência análise × publicação,
extração clínica e impacto — vai para o curator (LLM).

Saída (ignorada pelo git): scripts/db_v2/state/packets/<uid>/packet.json + fontes/*.txt. Nunca escreve no data.js.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import subprocess
import sys

AQUI = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
import bibliografia as B  # noqa: E402
import lift_v1 as LF  # noqa: E402
import v2lib as L  # noqa: E402

try:
    from . import sources as S
except ImportError:
    import sources as S

PACKETS = S.STATE / "packets"
SCHEMA = "theratrials-db-evidence-packet/1"
CAMPOS_CLINICOS = ["estudo", "acron", "fase", "desenho", "centros", "periodo", "indicacao", "incl", "excl", "estrat",
                   "basal", "n", "molecular", "biomarc", "radiofarmaco", "esquema", "cumul", "comparador", "estatistica",
                   "analises", "primario", "secundario", "subgrupo", "tox_g3", "tox_interesse", "impacto_reg", "limit",
                   "ref", "resultado_chave", "takehome", "linha", "preparo", "sponsor", "status", "ano_pub",
                   "pubmed_url", "nct", "titulo_full"]
MAX_PUBS_EXTRAS = 4


def cards_de(ref: str) -> dict:
    if ref == "HEAD":
        texto = L.DATA_JS.read_text(encoding="utf-8")
    else:
        texto = subprocess.check_output(["git", "-C", str(L.SITE), "show", f"{ref}:assets/js/data.js"]).decode()
    return {c["uid"]: c for c in L.ler_data_js(texto)[1]["studies"]}


def _no_ref(caminho: str, ref: str) -> dict:
    """Arquivo versionado como estava no commit `ref` (replay histórico); HEAD = arquivo atual."""
    if ref == "HEAD":
        return json.loads((L.SITE / caminho).read_text(encoding="utf-8"))
    try:
        return json.loads(subprocess.check_output(["git", "-C", str(L.SITE), "show", f"{ref}:{caminho}"],
                                                  stderr=subprocess.DEVNULL).decode())
    except subprocess.CalledProcessError:
        return {}


def _backlog(uid: str, ref: str = "HEAD") -> list[dict]:
    d = _no_ref("scripts/db_candidatos_integridade.json", ref) or {"itens": []}
    return [{k: x.get(k) for k in ("id", "status", "issue_type", "affected_fields", "description", "priority",
                                    "related_decisions", "human_decision", "resolution")}
            for x in d["itens"] if x["uid"] == uid]


def _decisoes(uid: str, ref: str = "HEAD") -> list[dict]:
    d = _no_ref("scripts/db_decisoes.json", ref)
    return [x for x in d.get("decisoes", []) if x.get("uid") == uid or uid in str(x.get("id", ""))]


def construir(uid: str, card_ref: str = "HEAD", rede: bool = False, cego: bool = False) -> dict:
    """card_ref ≠ HEAD: replay histórico — card, backlog e decisões como estavam naquele commit.
    cego: sem backlog nem decisões humanas (mede descoberta sem candidatos); grava em packets/<uid>__cego/."""
    card = cards_de(card_ref)[uid]
    pasta = PACKETS / (f"{uid}__cego" if cego else uid)
    fontes_dir = pasta / "fontes"
    fontes_dir.mkdir(parents=True, exist_ok=True)
    for f in fontes_dir.glob("*.txt"):
        f.unlink()
    snapshot = B.carregar_snapshot()
    pmid = B.pmid_do_card(card)
    ncts = re.findall(r"NCT\d{8}", str(card.get("nct") or ""))[:2]
    fontes, achados, pubs = [], [], []

    def fonte(source_id, source_type, text_level, pars, extra):
        if not pars:
            return
        p = S.gravar_fonte(fontes_dir, source_id, pars)
        fontes.append({"source_id": source_id, "source_type": source_type, "text_level": text_level,
                       "path": f"fontes/{p.name}", "paragraphs": len(pars), **extra})

    # ── metadados estruturados da publicação representada (snapshot versionado) ──
    meta_rep = snapshot.get(pmid) if pmid else None
    if meta_rep:
        fonte(f"pmid:{pmid}:metadata", "pubmed_metadata", "metadata", [
            ("PMID", pmid), ("Title", meta_rep.get("title") or ""), ("Journal", meta_rep.get("source") or ""),
            ("PubDate", meta_rep.get("pubdate") or ""), ("EPubDate", meta_rep.get("epubdate") or ""),
            ("Volume/Issue/Pages", f"{meta_rep.get('volume') or ''} ({meta_rep.get('issue') or ''}) {meta_rep.get('pages') or ''}"),
            ("DOI", meta_rep.get("doi") or ""),
            ("PublicationType", "; ".join(meta_rep.get("pubtype") or []))],
            {"pmid": pmid, "retrieved_at": meta_rep.get("retrieved_at")})
    # ── identidade e fontes da publicação representada ──
    ef = S.pubmed_efetch(pmid, rede) if pmid else {}
    if ef:
        fonte(f"pmid:{pmid}:abstract", "pubmed_abstract", "abstract",
              [("Title", ef["title"])] + [(f"Abstract > {s}", t) for s, t in ef["abstract"]],
              {"pmid": pmid, "doi": ef.get("doi"), "retrieved_at": ef["retrieved_at"]})
        if ef.get("pmcid"):
            pars = S.pmc_fulltext(ef["pmcid"], rede)
            fonte(f"pmc:{ef['pmcid']}:fulltext", "europepmc_fulltext", "fulltext", pars,
                  {"pmid": pmid, "pmcid": ef["pmcid"], "retrieved_at": ef["retrieved_at"]})
    registros = {}
    for n in ncts:
        rec = S.ctgov(n, rede)
        if rec:
            registros[n] = rec
            fonte(f"nct:{n}:registry", "ctgov_record", "registry", S.ctgov_paragrafos(rec),
                  {"nct": n, "retrieved_at": rec.get("_retrieved_at"),
                   "has_results": bool(rec.get("hasResults") or rec.get("resultsSection"))})
    refs_ct = {str(r.get("pmid")) for rec in registros.values()
               for r in (rec.get("protocolSection", {}).get("referencesModule", {}).get("references") or [])
               if r.get("pmid")}
    identidade = {"pmid": pmid, "nct": ncts, "doi": (snapshot.get(pmid) or {}).get("doi") if pmid else None,
                  "pmcid": ef.get("pmcid") if ef else None,
                  "pmid_lists_nct": (bool(set(ncts) & set(ef.get("databank_nct") or [])) if ef and ef.get(
                      "databank_nct") else None),
                  "ctgov_lists_pmid": (pmid in refs_ct) if (pmid and registros) else None}
    if pmid and ncts and identidade["pmid_lists_nct"] is False and identidade["ctgov_lists_pmid"] is False:
        identidade["status"] = "conflict"
        achados.append({"code": "IDENTITY_UNLINKED", "priority": "P0",
                        "detail": "nem o PubMed lista o NCT do card nem o CT.gov lista o PMID"})
    elif pmid and (identidade["pmid_lists_nct"] or identidade["ctgov_lists_pmid"]):
        identidade["status"] = "machine_verified"
    else:
        identidade["status"] = "unverified"
    # ── publicações ligadas ao(s) NCT que o card não representa ──
    ligados = set(refs_ct)
    for n in ncts:
        ligados |= set(S.pubmed_por_nct(n, rede)[0])
    ligados.discard(pmid)
    meta = S.pubmed_esummary(sorted(ligados, key=int), rede) if ligados else {}
    ano_rep = (snapshot.get(pmid) or {}).get("pubdate", "")[:4] if pmid else ""
    for p, m in sorted(meta.items(), key=lambda kv: kv[1].get("sortpubdate", ""), reverse=True):
        pubs.append({"pmid": p, "title": m.get("title"), "journal": m.get("source"), "pubdate": m.get("pubdate"),
                     "pubtype": m.get("pubtype", []), "first_author": (m.get("authors") or [{}])[0].get("name"),
                     "newer_than_represented": bool(ano_rep) and (m.get("pubdate", "")[:4] > ano_rep),
                     "cited_in_ref": p in str(card.get("ref") or "")})
    extras = [x for x in pubs if x["newer_than_represented"] and "Journal Article" in x["pubtype"]
              and not {"Comment", "Editorial", "Letter", "Review"} & set(x["pubtype"])][:MAX_PUBS_EXTRAS]
    for x in extras:
        e2 = S.pubmed_efetch(x["pmid"], rede)
        if e2:
            fonte(f"pmid:{x['pmid']}:abstract", "pubmed_abstract", "abstract",
                  [("Title", e2["title"])] + [(f"Abstract > {s}", t) for s, t in e2["abstract"]],
                  {"pmid": x["pmid"], "doi": e2.get("doi"), "retrieved_at": e2["retrieved_at"]})
    if extras:
        achados.append({"code": "NEWER_LINKED_PUBLICATIONS", "priority": "P1",
                        "detail": f"{len(extras)} artigo(s) ligados ao NCT mais recentes que a publicação representada: "
                                  + ", ".join(x["pmid"] for x in extras)})
    # ── bibliografia, backlog, decisões humanas ──
    colecoes = B.colecoes_das_decisoes(json.loads((L.SCRIPTS / "db_decisoes.json").read_text()).get("decisoes", []))
    _, motivo = B.elegibilidade(card, snapshot, B.bloqueios_do_backlog(
        json.loads((L.SCRIPTS / "db_candidatos_integridade.json").read_text())), colecoes)
    backlog = [] if cego else _backlog(uid, card_ref)
    decisoes = [] if cego else _decisoes(uid, card_ref)
    protegidos = sorted({f for x in backlog if x.get("related_decisions") or x.get("human_decision")
                         for f in (x.get("affected_fields") or [])})
    withheld = str(card.get("status", "")).startswith("Em revisão") or any(
        d.get("valor") == "EDITORIAL_QUARANTINE" for d in decisoes)
    status = str(card.get("status", ""))
    if withheld:
        achados.append({"code": "WITHHELD_DUE_TO_INTEGRITY", "priority": None,
                        "detail": "card em quarentena editorial: nenhum conteúdo clínico é proposto"})
    if status.startswith("Apresentado") and pmid and "journal article" in " ".join(
            (snapshot.get(pmid) or {}).get("pubtype", [])).lower():
        achados.append({"code": "FRESHNESS_PRESENTED_BUT_PUBLISHED", "priority": "P2",
                        "detail": "status 'Apresentado' mas o PMID do card é artigo publicado (fluxo de freshness)"})
    # ano_pub × ano da publicação representada (metadado estruturado; sem tolerância silenciosa)
    ano_rep = (meta_rep or {}).get("pubdate", "")[:4]
    if meta_rep and ano_rep.isdigit() and str(card.get("ano_pub", "")).strip() != ano_rep:
        achados.append({"code": "ANO_PUB_MISMATCH", "priority": "P3", "field": "ano_pub",
                        "detail": f"ano_pub {card.get('ano_pub')!r} × publicação representada {ano_rep} "
                                  f"(epub {(meta_rep.get('epubdate') or '—')[:10]})",
                        "proposed": ano_rep, "source_id": f"pmid:{pmid}:metadata", "match": f"PubDate"})
    # mascaramento declarado no registro × descrito na publicação (conflito entre fontes, nunca escolhido)
    for n, rec in registros.items():
        mask = (rec.get("protocolSection", {}).get("designModule", {}).get("designInfo", {})
                .get("maskingInfo", {}).get("masking"))
        if not mask:
            continue
        pub_txt = [(f["source_id"], f["path"]) for f in fontes if f["text_level"] in ("abstract", "fulltext")]
        for sid, path in pub_txt:
            pars = S.ler_paragrafos(pasta / path)
            for num, t in pars.items():
                secao = t[1:t.find("]")].lower() if t.startswith("[") else ""
                if not re.search(r"method|design|abstract|mask|blind|randomi|procedure|trial", secao) or \
                        re.search(r"discussion|introduction|limitation|reference", secao) or re.search(r"extension", t, re.I):
                    continue                              # só o desenho DESTE estudo, em Métodos/Resumo
                aberto = re.search(r"open[- ]label|was not masked|were not masked|not blinded|unblinded|no masking", t, re.I)
                blind = re.search(r"double[- ]blind|triple[- ]blind|placebo[- ]controlled", t, re.I)
                if aberto and blind:
                    continue                              # parágrafo ambíguo: não é evidência de conflito
                if (mask != "NONE" and aberto) or (mask == "NONE" and blind):
                    achados.append({"code": "MASKING_CROSS_SOURCE", "priority": "P2", "field": "desenho",
                                    "detail": f"registro {n}: masking={mask}; {sid} ¶{num}: '{(aberto or blind).group(0)}'",
                                    "registry": n, "masking": mask, "pub_source": sid, "pub_par": num,
                                    "pub_match": (aberto or blind).group(0)})
                    break
            else:
                continue
            break
    if motivo.startswith("backlog"):
        achados.append({"code": "BIBLIOGRAPHIC_BLOCKED", "priority": "P3",
                        "detail": f"citação estruturada bloqueada: {motivo}"})
    abertos = [x for x in backlog if x["status"] in ("open", "confirmed")]
    rec = LF.lift(dict(card), 0, {})
    pacote = {
        "schema": SCHEMA, "uid": f"{uid}__cego" if cego else uid, "card_ref": card_ref, "mode": "cego" if cego else "assistido", "card": {k: card.get(k) for k in CAMPOS_CLINICOS},
        "citation": card.get("citation"), "record_type": rec["record_type"],
        "record_type_basis": rec["curation"]["record_type_basis"],
        "identity": identidade,
        "bibliographic": {"eligibility": motivo, "has_structured_citation": bool(card.get("citation"))},
        "publication_relationship": {"human_decisions": [d for d in decisoes if d.get("campo") in (
            "tipo_analise", "publicacao_primaria", "relacao")], "status": "human_decision" if any(
            d.get("campo") in ("tipo_analise", "publicacao_primaria") for d in decisoes) else "undetermined"},
        "linked_publications": pubs,
        "backlog": backlog, "backlog_open_count": len(abertos), "human_decisions": decisoes,
        "human_decision_protected_fields": protegidos,
        "withheld": withheld, "deterministic_findings": achados,
        "sources": fontes,
        "forbidden_sources_excluded": ["tracker.json", "Explorer", "snippets secundários", "memória do modelo"],
        "llm_needed": not withheld and bool(fontes),
    }
    corpo = json.dumps(pacote, ensure_ascii=False, sort_keys=True)
    pacote["packet_sha256"] = hashlib.sha256(corpo.encode()).hexdigest()
    (pasta / "packet.json").write_text(json.dumps(pacote, ensure_ascii=False, indent=1), encoding="utf-8")
    return pacote


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--uid")
    ap.add_argument("--card-ref", default="HEAD")
    ap.add_argument("--corpus", action="store_true")
    ap.add_argument("--rede", action="store_true", help="permite buscar fontes ausentes do cache (PubMed, Europe PMC, CT.gov)")
    ap.add_argument("--cego", action="store_true", help="sem backlog nem decisões humanas (teste de descoberta)")
    a = ap.parse_args(argv)
    try:
        from . import corpus as C
    except ImportError:
        import corpus as C
    if a.uid and a.cego:
        p = construir(a.uid, a.card_ref, a.rede, cego=True)
        print(p["uid"], p["packet_sha256"])
        return 0
    alvos = [(a.uid, a.card_ref)] if a.uid else [(u, r) for u, r in C.corpus()["cards"].items()]
    res = []
    for uid, ref in alvos:
        try:
            p = construir(uid, ref, a.rede)
            res.append((uid, len(p["sources"]), [x["code"] for x in p["deterministic_findings"]], p["llm_needed"]))
        except S.SemCache as e:
            res.append((uid, 0, [f"SEM_CACHE {e}"], False))
        except Exception as e:                        # um card com falha não derruba o corpus
            res.append((uid, 0, [f"ERRO {type(e).__name__}: {e}"], False))
    for r in res:
        print(f"{r[0][:40]:40s} fontes={r[1]} llm={r[3]} {r[2]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
