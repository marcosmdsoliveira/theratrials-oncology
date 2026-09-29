"""snapshot_pubmed — snapshot OFFLINE e versionado dos metadados PubMed dos PMIDs usados no data.js.

    python3 scripts/db_v2/snapshot_pubmed.py            # rede (NCBI E-utilities esummary); regrava o snapshot
    python3 scripts/db_v2/snapshot_pubmed.py --check    # offline: todo PMID do data.js está no snapshot?

Só este script acessa a rede, e só quando rodado à mão; o CI, o site e o app leem o snapshot já gravado.
Guarda apenas o necessário para citar (autores, título, periódico, ano, volume, número, páginas, DOI, PMCID,
tipos de publicação), em ordem determinística. Registros já presentes não são reescritos, exceto com --refresh,
para que um PMID não mude de metadados sem decisão explícita. Nenhuma credencial ou identificação pessoal é enviada.
"""
from __future__ import annotations

import argparse
import datetime
import json
import sys
import time
import urllib.parse
import urllib.request

import bibliografia as B
import v2lib as L

ESUMMARY = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"


def pmids_do_data_js() -> list[str]:
    _, obj, _ = L.ler_data_js(L.DATA_JS.read_text(encoding="utf-8"))
    return sorted({p for c in obj["studies"] for p in [B.pmid_do_card(c)] if p}, key=int)


def reduzir(v: dict, hoje: str) -> dict:
    ids = {x["idtype"]: x["value"] for x in v.get("articleids", [])}
    return {"pmid": v["uid"],
            "authors": [{"name": a["name"], "authtype": a.get("authtype")} for a in v.get("authors", [])],
            "title": v.get("title"), "source": v.get("source"), "fulljournalname": v.get("fulljournalname"),
            "pubdate": v.get("pubdate"), "epubdate": v.get("epubdate"), "volume": v.get("volume"),
            "issue": v.get("issue"), "pages": v.get("pages"), "elocationid": v.get("elocationid"),
            "doi": ids.get("doi"), "pmcid": ids.get("pmc"), "pubtype": v.get("pubtype", []), "retrieved_at": hoje}


def buscar(pmids: list[str]) -> dict:
    out = {}
    for i in range(0, len(pmids), 150):
        dados = urllib.parse.urlencode({"db": "pubmed", "id": ",".join(pmids[i:i + 150]), "retmode": "json",
                                        "tool": "theratrials-db"}).encode()
        r = json.load(urllib.request.urlopen(ESUMMARY, dados, timeout=60))["result"]
        out.update({k: v for k, v in r.items() if k != "uids" and "error" not in v})
        time.sleep(0.4)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="offline: confere cobertura, não escreve")
    ap.add_argument("--refresh", action="store_true", help="rebaixa também os PMIDs já presentes")
    a = ap.parse_args(argv)
    pmids = pmids_do_data_js()
    atual = B.carregar_snapshot() if B.SNAPSHOT.exists() else {}
    faltam = [p for p in pmids if p not in atual]
    if a.check:
        print(json.dumps({"pmids_no_data_js": len(pmids), "no_snapshot": len(atual), "faltam": faltam},
                         ensure_ascii=False))
        return 1 if faltam else 0
    alvo = pmids if a.refresh else faltam
    hoje = datetime.date.today().isoformat()
    novos = {k: reduzir(v, hoje) for k, v in buscar(alvo).items()} if alvo else {}
    registros = {**atual, **novos}
    B.SNAPSHOT.parent.mkdir(exist_ok=True)
    B.SNAPSHOT.write_text(json.dumps({"schema": B.SNAPSHOT_SCHEMA, "source": "NCBI E-utilities esummary (PubMed)",
                                      "records": {k: registros[k] for k in sorted(registros, key=int)}},
                                     ensure_ascii=False, indent=0, sort_keys=False) + "\n", encoding="utf-8")
    print(json.dumps({"pmids_no_data_js": len(pmids), "buscados": len(alvo), "gravados": len(novos),
                      "no_snapshot": len(registros), "sem_retorno": sorted(set(alvo) - set(novos), key=int)},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
