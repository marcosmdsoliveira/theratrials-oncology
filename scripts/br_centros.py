#!/usr/bin/env python3
"""
br_centros.py — audita (e corrige) os centros brasileiros dos cards já publicados.

Os cards curados à mão listavam poucos centros: 32 dos 79 tinham apenas um,
enquanto o ClinicalTrials.gov registrava vários. Um médico em Salvador não
encontrava um estudo que recruta em Salvador.

Isto aqui é 100% factual — lê os locais do registro oficial e compara com o
card. Nenhuma IA envolvida.

Desde 2026-08, `centros` guarda INSTITUIÇÃO, não cidade. Antes o script
deduplicava por município: um estudo com três hospitais em São Paulo virava um
único 'São Paulo / SP'. O card dizia "18 centros" quando eram 18 cidades, e a
home somava esses valores entre os cards — como São Paulo aparece em 128
estudos, ela entrava 128 vezes e o total dava 1042 para ~180 centros reais.

Formato de cada entrada:
    'A.C.Camargo Cancer Center — São Paulo / SP'   centro nomeado
    'São Paulo / SP'                               centro que o registro não nomeia

O sufixo ' / UF' é mantido nos dois casos porque o front-end agrupa por UF a
partir dele. Ver br_instituicoes.py para a resolução dos nomes.

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
from br_instituicoes import resolver  # noqa: E402

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
            "fields": ("NCTId|LocationCity|LocationState|LocationCountry"
                       "|LocationFacility|LocationStatus"),
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
            nomeados: set[tuple[str, str]] = set()
            anonimas: set[str] = set()
            for l in locs:
                if l.get("country") != "Brazil":
                    continue
                # Centro que o próprio registro marca como já encerrado não é
                # centro recrutador. Sem `status` o CT.gov herda o do estudo.
                st = l.get("status") or ""
                if st and "RECRUITING" not in st.upper():
                    continue
                cidade = normalizar_cidade(l.get("city") or "")
                if not cidade:
                    continue
                nome, _motivo = resolver(l.get("facility") or "", cidade)
                if nome:
                    nomeados.add((nome, cidade))
                else:
                    anonimas.add(cidade)

            locais = [{"instituicao": n, "cidade": c, "uf": CIDADE_UF.get(c, "")}
                      for n, c in nomeados]
            # Cidade que só tem centro anônimo entra sem nome. Se já houver um
            # centro nomeado ali no mesmo estudo, o anônimo é descartado: não
            # há como saber se é outra casa ou a mesma sob nome omitido, e
            # somar os dois inventaria um centro.
            com_nome = {c for _, c in nomeados}
            for c in sorted(anonimas - com_nome):
                locais.append({"instituicao": "", "cidade": c,
                               "uf": CIDADE_UF.get(c, "")})
            locais.sort(key=lambda x: (x["uf"], x["cidade"], x["instituicao"]))
            out[nct] = locais
        print(f"[centros] {min(i+40, len(ncts))}/{len(ncts)}", file=sys.stderr)
        time.sleep(0.4)
    return out


def js_arr(vs: list[str]) -> str:
    # O escape tem de valer nos DOIS ramos: nomes de instituição trazem
    # apóstrofo ("Instituto D'Or de Pesquisa e Ensino") e o ramo multilinha
    # gravava a aspa crua, quebrando o parse do arquivo inteiro.
    esc = lambda v: "'" + v.replace("\\", "\\\\").replace("'", "\\'") + "'"  # noqa: E731
    if not vs:
        return "[]"
    if sum(len(v) for v in vs) < 70 and len(vs) <= 4:
        return "[" + ", ".join(esc(v) for v in vs) + "]"
    return "[\n" + "".join(f"      {esc(v)},\n" for v in vs) + "    ]"


def validar(texto: str, esperado: int) -> tuple[bool, str]:
    """Parseia com node e confere a contagem de cards antes de deixar gravar."""
    import subprocess
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False,
                                     encoding="utf-8") as t:
        t.write(texto)
        tmp = t.name
    js = (f"global.window={{}};require({json.dumps(tmp)});"
          "const a=window.THERA_TRIALS_BR;"
          "if(!Array.isArray(a))throw new Error('THERA_TRIALS_BR não é array');"
          "const c=a.reduce((n,e)=>n+((e.centros||[]).length),0);"
          "console.log(JSON.stringify({n:a.length,c}));")
    try:
        r = subprocess.run(["node", "-e", js], capture_output=True, text=True,
                           timeout=60)
        if r.returncode != 0:
            return False, r.stderr.strip()[:400]
        d = json.loads(r.stdout)
        if esperado >= 0 and d["n"] != esperado:
            return False, f"contagem: esperado {esperado}, obtido {d['n']}"
        return True, f"{d['n']} cards, {d['c']} entradas de centro"
    finally:
        Path(tmp).unlink(missing_ok=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--aplicar", action="store_true")
    ap.add_argument("--forcar", action="store_true",
                    help="reescreve mesmo quando a contagem já bate — usar depois "
                         "de ampliar o dicionário de cidades do br_discover.py")
    args = ap.parse_args()

    texto = TRIALS_JS.read_text(encoding="utf-8")
    ok0, msg0 = validar(texto, -1)   # -1: só quero a contagem, não comparar
    n_original = int(re.search(r"(\d+) cards", msg0).group(1)) if "cards" in msg0 else -1
    if n_original < 0:
        print(f"não consegui parsear o arquivo atual: {msg0}", file=sys.stderr)
        return 1
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

    # Delimita cada card pelo início do próximo, em vez de uma janela fixa.
    # Com 2500 caracteres, cards de critérios longos deixavam `centros:` fora
    # do alcance — a auditoria lia 0 centros e a reescrita virava no-op. Em
    # cards curtos a janela vazava para o card seguinte, e um campo ausente
    # fazia a substituição acertar o vizinho.
    for i, c in enumerate(cards):
        c["fim"] = cards[i + 1]["pos"] if i + 1 < len(cards) else len(texto)

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
        bloco = texto[c["pos"]:c["fim"]]
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
        ini, fim = f["pos"], f["fim"]
        bloco = texto[ini:fim]
        cidades = sorted({l["cidade"] for l in f["locais"]})
        ufs = sorted({l["uf"] for l in f["locais"]} - {""})
        centros = []
        for l in f["locais"]:
            onde = f"{l['cidade']} / {l['uf']}" if l["uf"] else l["cidade"]
            centros.append(f"{l['instituicao']} — {onde}" if l["instituicao"] else onde)
        novo = bloco
        for chave, valor in (("centros", centros), ("cidades", cidades), ("estados", ufs)):
            novo, n = re.subn(rf"({chave}\s*:\s*)\[.*?\]",
                              lambda mm: mm.group(1) + js_arr(valor), novo,
                              count=1, flags=re.S)
            if not n:
                print(f"   ⚠ {f['nct']} {f['nome'][:28]}: campo '{chave}' não "
                      f"encontrado no card — nada reescrito", file=sys.stderr)
        texto = texto[:ini] + novo + texto[fim:]

    # Reparse antes de gravar: um apóstrofo mal escapado num nome de
    # instituição derruba o arquivo inteiro, e o sintoma seria o Trial Matcher
    # em branco em produção. O esperado é o total do array no arquivo ORIGINAL
    # — não `len(cards)`, que conta só os cards com NCT e deixaria de fora os
    # que ainda não têm registro.
    ok, msg = validar(texto, n_original)
    print(f"\nvalidação node ...... {'OK — ' + msg if ok else 'FALHOU — ' + msg}")
    if not ok:
        print("nada foi gravado.", file=sys.stderr)
        return 1

    TRIALS_JS.write_text(texto, encoding="utf-8")
    print(f"{len(faltando)} cards atualizados")
    return 0


if __name__ == "__main__":
    sys.exit(main())
