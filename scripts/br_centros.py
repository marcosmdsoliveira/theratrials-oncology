#!/usr/bin/env python3
"""
br_centros.py — audita (e corrige) os centros brasileiros dos cards já publicados.

Os cards curados à mão listavam poucos centros: 32 dos 79 tinham apenas um,
enquanto o ClinicalTrials.gov registrava vários. Um médico em Salvador não
encontrava um estudo que recruta em Salvador.

Isto aqui é 100% factual — lê os locais do registro oficial e compara com o
card. Nenhuma IA envolvida.

Uso:
    python3 scripts/br_centros.py            # só audita
    python3 scripts/br_centros.py --aplicar  # reescreve centros/cidades/estados
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from br_discover import CIDADE_UF, normalizar_cidade  # noqa: E402

SITE = Path(__file__).resolve().parent.parent
TRIALS_JS = SITE / "assets" / "js" / "trials_br.js"
API = "https://clinicaltrials.gov/api/v2/studies"


def locais_ctgov(ncts: list[str]) -> dict[str, list[dict]]:
    """Locais brasileiros de cada NCT, em lotes (a API aceita filtro por id)."""
    out: dict[str, list[dict]] = {}
    for i in range(0, len(ncts), 40):
        lote = ncts[i:i + 40]
        params = {
            "filter.ids": "|".join(lote),
            "fields": "NCTId|LocationCity|LocationState|LocationCountry|LocationFacility",
            "pageSize": "200",
        }
        req = urllib.request.Request(
            f"{API}?{urllib.parse.urlencode(params)}",
            headers={"User-Agent": "TheraTrials/1.0 (+https://theratrials.com)"},
        )
        with urllib.request.urlopen(req, timeout=60) as r:
            d = json.loads(r.read().decode("utf-8"))
        for s in d.get("studies", []):
            p = s.get("protocolSection", {})
            nct = p.get("identificationModule", {}).get("nctId", "")
            locs = p.get("contactsLocationsModule", {}).get("locations", [])
            vistos, locais = set(), []
            for l in locs:
                if l.get("country") != "Brazil":
                    continue
                cidade = normalizar_cidade(l.get("city") or "")
                if not cidade or cidade in vistos:
                    continue
                vistos.add(cidade)
                locais.append({"cidade": cidade, "uf": CIDADE_UF.get(cidade, "")})
            locais.sort(key=lambda x: x["cidade"])
            out[nct] = locais
        print(f"[centros] {min(i+40, len(ncts))}/{len(ncts)}", file=sys.stderr)
        time.sleep(0.4)
    return out


def js_arr(vs: list[str]) -> str:
    if not vs:
        return "[]"
    if sum(len(v) for v in vs) < 70 and len(vs) <= 4:
        return "[" + ", ".join("'" + v.replace("'", "\\'") + "'" for v in vs) + "]"
    return ("[\n" + "".join(f"      '{v}',\n" for v in vs) + "    ]")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--aplicar", action="store_true")
    ap.add_argument("--forcar", action="store_true",
                    help="reescreve mesmo quando a contagem já bate — usar depois "
                         "de ampliar o dicionário de cidades do br_discover.py")
    args = ap.parse_args()

    texto = TRIALS_JS.read_text(encoding="utf-8")
    campo = lambda k: rf"""['"]?{k}['"]?\s*:\s*['"]([^'"]*)['"]"""  # noqa: E731

    cards = []
    for m in re.finditer(campo("nct"), texto):
        nct = re.search(r"NCT\d{8}", m.group(1))
        if not nct:
            continue
        janela_ini = max(0, m.start() - 1500)
        nome = re.findall(campo("nome"), texto[janela_ini:m.start()])
        cards.append({"nct": nct.group(0), "pos": m.start(),
                      "nome": nome[-1] if nome else "?"})

    print(f"cards com NCT: {len(cards)}")
    oficiais = locais_ctgov([c["nct"] for c in cards])

    faltando, sem_brasil = [], []
    for c in cards:
        oficial = oficiais.get(c["nct"])
        if oficial is None:
            continue
        # O CT.gov não lista nenhum centro no Brasil. Pode ser estudo que
        # abriu centro sem atualizar o registro, ou informação vinda de outra
        # fonte (REBEC, contato direto com o patrocinador). Preservar o que o
        # curador escreveu e apenas sinalizar — apagar seria destruir dado
        # sem evidência de que está errado.
        if not oficial:
            sem_brasil.append(c)
            continue
        bloco = texto[c["pos"]: c["pos"] + 2500]
        atual = re.search(r"centros\s*:\s*\[(.*?)\]", bloco, re.S)
        n_atual = len(re.findall(r"'[^']+'", atual.group(1))) if atual else 0
        if args.forcar or len(oficial) > n_atual:
            faltando.append({**c, "atual": n_atual, "oficial": len(oficial),
                             "locais": oficial})

    faltando.sort(key=lambda x: x["oficial"] - x["atual"], reverse=True)
    print(f"\ncards com MENOS centros que o CT.gov: {len(faltando)}\n")
    print(f"  {'ESTUDO':32s} {'card':>5s} {'CT.gov':>7s}  ganho")
    for f in faltando[:28]:
        print(f"  {f['nome'][:32]:32s} {f['atual']:5d} {f['oficial']:7d}  "
              f"+{f['oficial'] - f['atual']}")
    total = sum(f["oficial"] - f["atual"] for f in faltando)
    print(f"\n  centros a acrescentar no total: {total}")

    if sem_brasil:
        print(f"\n⚠ SEM CENTRO NO BRASIL no CT.gov ({len(sem_brasil)}) — "
              f"card preservado, revisar manualmente:")
        for c in sem_brasil:
            print(f"   {c['nct']}  {c['nome'][:44]}")

    if not args.aplicar:
        print("\n(--aplicar para reescrever)")
        return 0

    # Reescreve de trás para frente para não invalidar as posições.
    for f in sorted(faltando, key=lambda x: x["pos"], reverse=True):
        ini, fim = f["pos"], f["pos"] + 2500
        bloco = texto[ini:fim]
        cidades = [l["cidade"] for l in f["locais"]]
        ufs = sorted({l["uf"] for l in f["locais"]} - {""})
        centros = [f"{l['cidade']} / {l['uf']}" if l["uf"] else l["cidade"]
                   for l in f["locais"]]
        novo = bloco
        for chave, valor in (("centros", centros), ("cidades", cidades), ("estados", ufs)):
            novo = re.sub(rf"({chave}\s*:\s*)\[.*?\]", 
                          lambda mm: mm.group(1) + js_arr(valor), novo, count=1, flags=re.S)
        texto = texto[:ini] + novo + texto[fim:]

    TRIALS_JS.write_text(texto, encoding="utf-8")
    print(f"\n{len(faltando)} cards atualizados")
    return 0


if __name__ == "__main__":
    sys.exit(main())
