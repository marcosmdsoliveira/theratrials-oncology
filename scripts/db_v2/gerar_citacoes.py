"""gerar_citacoes — projeta a camada bibliográfica v2 no card v1 (campo opcional `citation`), numa CÓPIA do data.js.

    python3 scripts/db_v2/gerar_citacoes.py                  # grava scripts/_db_copia/data.js + relatório
    python3 scripts/db_v2/gerar_citacoes.py --data-js X      # outra origem (ex.: uma cópia)
    python3 scripts/db_v2/gerar_citacoes.py --aplicar --sha-origem <sha do data.js> --sha-copia <sha da cópia validada>

Para cada card, bibliografia.elegibilidade() decide se a publicação representada (PMID do card, metadados do
snapshot PubMed offline) é segura para citação estruturada. Se for, `citation` = citation_v1(publicação) entra logo
depois de `ref`; se não for, o card fica SEM `citation` (e o frontend mostra o `ref` literal ou a referência do
registro, sem autor inventado). `ref` e `sponsor` nunca são alterados. Nenhuma rede.

Idempotente: rodar sobre um data.js que já tem `citation` regenera o mesmo resultado (inclusive removendo `citation`
de card que deixou de ser elegível, p.ex. por item novo no backlog). Recusa gravar no data.js publicado.
Relatório: scripts/_db_citacoes_relatorio.json (ignorado pelo git).

--aplicar promove a cópia JÁ VALIDADA ao data.js publicado, e só se: o data.js tem exatamente --sha-origem, a cópia
tem exatamente --sha-copia, os 503 uids e a ordem são os mesmos, o topo do objeto (categorias etc.) é idêntico e a
única diferença entre cartões é `citation`. Depois: node scripts/export_app_data.mjs.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import shutil
import json
import pathlib
import sys

import bibliografia as B
import v2lib as L

COPIA = L.SCRIPTS / "_db_copia" / "data.js"
RELATORIO = L.SCRIPTS / "_db_citacoes_relatorio.json"


def inserir_apos(card: dict, chave: str, nova: str, valor) -> dict:
    out = {}
    for k, v in card.items():
        if k == nova:
            continue
        out[k] = v
        if k == chave:
            out[nova] = valor
    if nova not in out:
        out[nova] = valor
    return out


def projetar(estudos: list[dict], snapshot: dict, bloqueios: dict, colecoes: set, papeis: dict):
    saida, linhas = [], []
    for card in estudos:
        pub, motivo = B.elegibilidade(card, snapshot, bloqueios, colecoes, papeis)
        novo = inserir_apos(card, "ref", "citation", B.citation_v1(pub)) if pub else \
            {k: v for k, v in card.items() if k != "citation"}
        saida.append(novo)
        linhas.append({"uid": card["uid"], "motivo": motivo, "pmid": B.pmid_do_card(card),
                       "citation": novo.get("citation")})
    return saida, linhas


def sha(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def aplicar(sha_origem: str, sha_copia: str) -> int:
    if sha(L.DATA_JS) != sha_origem:
        print(f"recusado: data.js tem {sha(L.DATA_JS)[:16]}, esperado {sha_origem[:16]}", file=sys.stderr)
        return 2
    if not COPIA.exists() or sha(COPIA) != sha_copia:
        print("recusado: a cópia não existe ou não é a cópia validada (SHA diferente)", file=sys.stderr)
        return 2
    _, a, _ = L.ler_data_js(L.DATA_JS.read_text(encoding="utf-8"))
    _, c, _ = L.ler_data_js(COPIA.read_text(encoding="utf-8"))
    if [s["uid"] for s in a["studies"]] != [s["uid"] for s in c["studies"]]:
        print("recusado: uids ou ordem diferentes", file=sys.stderr)
        return 2
    if {k: v for k, v in a.items() if k != "studies"} != {k: v for k, v in c.items() if k != "studies"}:
        print("recusado: topo do objeto (categorias etc.) diferente", file=sys.stderr)
        return 2
    for x, y in zip(a["studies"], c["studies"]):
        fora = {k for k in set(x) | set(y) if x.get(k) != y.get(k)} - {"citation"}
        if fora:
            print(f"recusado: {x['uid']} muda campos além de citation: {sorted(fora)}", file=sys.stderr)
            return 2
    shutil.copyfile(COPIA, L.DATA_JS)
    print(f"aplicado: data.js {sha_origem[:16]} → {sha_copia[:16]}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-js", default=str(L.DATA_JS))
    ap.add_argument("--out", default=str(COPIA))
    ap.add_argument("--backlog", default=str(L.SCRIPTS / "db_candidatos_integridade.json"))
    ap.add_argument("--decisoes", default=str(L.SCRIPTS / "db_decisoes.json"))
    ap.add_argument("--aplicar", action="store_true", help="promove a cópia validada ao data.js publicado")
    ap.add_argument("--sha-origem")
    ap.add_argument("--sha-copia")
    a = ap.parse_args(argv)
    if a.aplicar:
        if not (a.sha_origem and a.sha_copia):
            print("--aplicar exige --sha-origem e --sha-copia", file=sys.stderr)
            return 2
        return aplicar(a.sha_origem, a.sha_copia)
    out = pathlib.Path(a.out)
    if out.resolve() == L.DATA_JS.resolve():
        print("recusado: gerar_citacoes grava só em cópia; o data.js publicado muda por migração aprovada",
              file=sys.stderr)
        return 2
    prefixo, obj, sufixo = L.ler_data_js(pathlib.Path(a.data_js).read_text(encoding="utf-8"))
    uids = [c["uid"] for c in obj["studies"]]
    decs = json.loads(pathlib.Path(a.decisoes).read_text(encoding="utf-8")).get("decisoes", [])
    backlog = json.loads(pathlib.Path(a.backlog).read_text(encoding="utf-8"))
    estudos, linhas = projetar(obj["studies"], B.carregar_snapshot(), B.bloqueios_do_backlog(backlog),
                               B.colecoes_das_decisoes(decs), B.papeis_das_decisoes(decs))
    assert [c["uid"] for c in estudos] == uids, "uid/ordem mudou"
    for antes, depois in zip(obj["studies"], estudos):
        mudou = {k for k in set(antes) | set(depois) if antes.get(k) != depois.get(k)}
        assert mudou <= {"citation"}, f"{antes['uid']}: campos fora de citation mudaram: {mudou}"
    obj = dict(obj, studies=estudos)
    out.parent.mkdir(exist_ok=True)
    out.write_text(L.serializar_data_js(prefixo, obj, sufixo), encoding="utf-8")
    motivos = collections.Counter(l["motivo"].split(":")[0] for l in linhas)
    RELATORIO.write_text(json.dumps({"cards": len(linhas), "com_citation": motivos["ok"], "motivos": dict(motivos),
                                     "cards_detalhe": linhas}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"cards": len(linhas), "com_citation": motivos["ok"], "motivos": dict(motivos.most_common()),
                      "saida": str(out)}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
