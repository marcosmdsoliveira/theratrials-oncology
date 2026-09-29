"""corpus — corpus REAL de teste do curator/verifier, montado deterministicamente do estado atual.

  golden : os 10 cards auditados à mão (golden/golden_set.json), com a versão de entrada de cada um;
  A      : cards com PMID cuja citação estruturada está bloqueada por item bibliográfico no backlog;
  B      : os 24 B-pendentes do piloto v2.1 — estão todos em cards do golden (as expectativas vêm de lá);
  C      : status 'Apresentado' com PMID de artigo publicado (fluxo de freshness, NÃO P0);
  D      : amostra estratificada do backlog aberto/confirmado, até 2 cards por tipo de problema pedido.
Mesma entrada → mesmo corpus (ordenação por id; nenhuma aleatoriedade).
"""
from __future__ import annotations

import json
import pathlib
import sys

AQUI = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
import bibliografia as B  # noqa: E402
import v2lib as L  # noqa: E402

GOLDEN = AQUI / "golden" / "golden_set.json"
TIPOS_D = ["identifier_mismatch", "publication_relationship", "cross_source_conflict", "bibliographic_mismatch",
           "safety_misattribution", "arm_or_comparator", "source_internal_inconsistency"]


def golden() -> dict:
    return json.loads(GOLDEN.read_text(encoding="utf-8"))


def corpus() -> dict:
    g = golden()["casos"]
    estudos = L.ler_data_js(L.DATA_JS.read_text(encoding="utf-8"))[1]["studies"]
    backlog = json.loads((L.SCRIPTS / "db_candidatos_integridade.json").read_text(encoding="utf-8"))
    decs = json.loads((L.SCRIPTS / "db_decisoes.json").read_text(encoding="utf-8")).get("decisoes", [])
    snap = B.carregar_snapshot()
    bloq = B.bloqueios_do_backlog(backlog)
    col = B.colecoes_das_decisoes(decs)
    a = [c["uid"] for c in estudos if B.pmid_do_card(c) and B.elegibilidade(c, snap, bloq, col)[1].startswith("backlog")]
    cc = [c["uid"] for c in estudos if str(c.get("status", "")).startswith("Apresentado") and B.pmid_do_card(c)
          and "journal article" in " ".join((snap.get(B.pmid_do_card(c)) or {}).get("pubtype", [])).lower()]
    d, vistos = [], set(g) | set(a) | set(cc)
    for tipo in TIPOS_D:
        n = 0
        for x in sorted(backlog["itens"], key=lambda x: x["id"]):
            if x["issue_type"] == tipo and x["status"] in ("open", "confirmed") and x["uid"] not in vistos and n < 2:
                d.append(x["uid"])
                vistos.add(x["uid"])
                n += 1
    cards = {u: g[u]["input_card_ref"] for u in g}
    for u in a + cc + d:
        cards.setdefault(u, "HEAD")
    return {"cards": cards, "golden": list(g), "A": a, "C": cc, "D": d,
            "B_nota": "24 B-pendentes do piloto, todos dentro dos cards do golden"}


if __name__ == "__main__":
    c = corpus()
    print(json.dumps({k: (len(v) if isinstance(v, (list, dict)) else v) for k, v in c.items()}, ensure_ascii=False))
    print("A:", c["A"])
    print("C:", c["C"])
    print("D:", c["D"])
