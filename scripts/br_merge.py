#!/usr/bin/env python3
"""
br_merge.py — etapa 3: escreve os cards curados no trials_br.js.

Lê scripts/_br_curated.json e insere os cards numa nova seção
`// ===== NOVOS ESTUDOS (data) =====` imediatamente antes do fecho do array,
que é o padrão que o próprio arquivo já usa. Não reescreve nem reordena nada
do que existe — só acrescenta.

Também aplica as mudanças de status detectadas pelo br_discover.py (troca de
`Recrutando` para `Encerrado`, etc.), que são factuais e vêm direto do CT.gov.

Valida o resultado com node antes de gravar: se o JS não parsear ou o número de
estudos não bater, aborta sem tocar no arquivo.

Uso:
    python3 scripts/br_merge.py            # aplica
    python3 scripts/br_merge.py --dry-run  # mostra o que faria
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent
TRIALS_JS = SITE / "assets" / "js" / "trials_br.js"
CURATED = Path(__file__).resolve().parent / "_br_curated.json"
DISCOVERY = Path(__file__).resolve().parent / "_br_discovery.json"

# 'NA' no ClinicalTrials.gov quer dizer "fase não aplicável" — é como o
# registro classifica ensaios de radioterapia, cirurgia e dispositivo, que não
# têm fase de desenvolvimento de fármaco. NÃO quer dizer observacional: o
# LAPIDARY, o PROMART e o HYPHEN são intervencionais e randomizados. Estudo
# observacional de verdade vem sem o campo `phases`, tratado à parte.
FASE_MAP = {"PHASE1": "I", "PHASE2": "II", "PHASE3": "III", "PHASE4": "IV",
            "EARLY_PHASE1": "I", "NA": "Sem fase"}
STATUS_MAP = {"RECRUITING": "Recrutando", "NOT_YET_RECRUITING": "Ainda não recrutando",
              "SUSPENDED": "Recrutamento suspenso", "ACTIVE_NOT_RECRUITING": "Encerrado",
              "COMPLETED": "Encerrado", "TERMINATED": "Encerrado", "WITHDRAWN": "Encerrado"}


def js_str(v: str) -> str:
    """Literal de string JS em aspas simples, como o resto do arquivo."""
    return "'" + str(v).replace("\\", "\\\\").replace("'", "\\'").replace("\n", " ") + "'"


def js_arr(vs: list[str], indent: int) -> str:
    if not vs:
        return "[]"
    if sum(len(v) for v in vs) < 70 and len(vs) <= 4:
        return "[" + ", ".join(js_str(v) for v in vs) + "]"
    pad = " " * (indent + 2)
    return "[\n" + "".join(f"{pad}{js_str(v)},\n" for v in vs) + " " * indent + "]"


def slug(nome: str, nct: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", nome.lower()).strip("-")
    return s or nct.lower()


def fase(fases: list[str]) -> str:
    if not fases:
        return "Observacional"
    if len(fases) > 1 and "PHASE1" in fases and "PHASE2" in fases:
        return "Ib/II"
    if len(fases) > 1 and "PHASE2" in fases and "PHASE3" in fases:
        return "II/III"
    return FASE_MAP.get(fases[0], "Observacional")


def card_js(c: dict) -> str:
    f = c["_factual"]
    nct = f["nct"]

    # Usar `locais`, onde cada entrada já traz {instituicao, cidade, uf} do
    # próprio registro. NÃO reconstruir com zip(cidades, estados): as duas
    # listas são deduplicadas e ordenadas separadamente, então o índice de uma
    # não corresponde ao da outra — isso produzia "Salvador / RJ" e descartava
    # centros quando as listas tinham tamanhos diferentes.
    #
    # Formato: 'Instituição — Cidade / UF', ou só 'Cidade / UF' quando o
    # registro não nomeia o centro. O front-end agrupa por UF a partir do
    # sufixo, então ele tem de existir nos dois casos.
    locais = f.get("locais") or []
    if locais:
        centros = []
        for l in locais:
            onde = f"{l['cidade']} / {l['uf']}" if l.get("uf") else l["cidade"]
            inst = l.get("instituicao")
            centros.append(f"{inst} — {onde}" if inst else onde)
    else:
        centros = f.get("cidades") or f.get("centros", [])[:4]
    url = f"https://clinicaltrials.gov/study/{nct}"
    campos = [
        ("id", js_str(slug(c["nome"], nct))),
        ("nome", js_str(c["nome"])),
        ("titulo", js_str(c["titulo"])),
        ("nct", js_str(nct)),
        ("fase", js_str(fase(f["fase"]))),
        ("status", js_str(STATUS_MAP.get(f["status_ctgov"], "Recrutando"))),
        ("neoplasia", js_str(c["neoplasia"])),
        ("neoplasia_label", js_str(c["neoplasia_label"])),
        ("subtipo", js_str(c["subtipo"])),
        ("linha_terapeutica", js_str(c["linha_terapeutica"])),
        ("cenario_clinico", js_str(c["cenario_clinico"])),
        ("modalidade", js_arr(c["modalidade"], 4)),
        ("biomarcadores", js_arr(c["biomarcadores"], 4)),
        ("testes_fornecidos", js_str(c["testes_fornecidos"])),
        ("intervencao", js_str(c["intervencao"])),
        ("comparador", js_str(c["comparador"])),
        ("racional", js_str(c["racional"])),
        ("criterios_principais", js_arr(c["criterios_principais"], 4)),
        ("criterios_exclusao", js_arr(c["criterios_exclusao"], 4)),
        ("centros", js_arr(centros, 4)),
        ("estados", js_arr(f["estados"], 4)),
        ("cidades", js_arr(f["cidades"], 4)),
        ("patrocinador", js_str(f["patrocinador"])),
        ("fonte_url", js_str(url)),
        ("contato_url", js_str(url)),
        ("data_atualizacao", js_str(f["data_atualizacao"])),
    ]
    corpo = "".join(f"    {k}: {v},\n" for k, v in campos)
    # Rastro para a revisão: fica no diff do PR e sai quando o revisor aprovar.
    # A nota é quebrada em linhas, não truncada. Cortar em 150 caracteres
    # decepava a nota no meio da palavra e, pior, jogava fora justamente o
    # trecho acionável — o "CONFERIR tal coisa" costuma vir no fim.
    nota = " ".join(c.get("notas_revisor", "").split())
    marca = ""
    linha = f"    // ⚠ RASCUNHO — confiança {c.get('confianca', '?')}."
    for palavra in nota.split(" "):
        if len(linha) + len(palavra) + 1 > 100:
            marca += linha + "\n"
            linha = "    //   " + palavra
        else:
            linha += " " + palavra
    marca += linha + "\n"
    return "  {\n" + marca + corpo + "  },\n"


def validar(texto: str, esperado: int) -> tuple[bool, str]:
    """Parseia com node e confere a contagem antes de deixar gravar."""
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False,
                                     encoding="utf-8") as t:
        t.write(texto)
        tmp = t.name
    js = (f"global.window={{}};require({json.dumps(tmp)});"
          "const a=window.THERA_TRIALS_BR;"
          "if(!Array.isArray(a))throw new Error('THERA_TRIALS_BR não é array');"
          "const semNct=a.filter(s=>!s.nct).length;"
          "console.log(JSON.stringify({n:a.length,semNct}));")
    try:
        r = subprocess.run(["node", "-e", js], capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            return False, r.stderr.strip()[:400]
        d = json.loads(r.stdout)
        if d["n"] != esperado:
            return False, f"contagem: esperado {esperado}, obtido {d['n']}"
        return True, f"{d['n']} estudos, {d['semNct']} sem nct"
    finally:
        Path(tmp).unlink(missing_ok=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not CURATED.exists():
        print("_br_curated.json não existe — rode br_curate.py --colher antes",
              file=sys.stderr)
        return 1
    cur = json.loads(CURATED.read_text(encoding="utf-8"))
    cards = cur["cards"]
    disc = json.loads(DISCOVERY.read_text(encoding="utf-8")) if DISCOVERY.exists() else {}
    mudancas = disc.get("mudou_status", [])

    original = TRIALS_JS.read_text(encoding="utf-8")
    antes = len(re.findall(r"""['"]?nct['"]?\s*:\s*['"]""", original))

    texto = original

    # 1) Mudanças de status (factuais, do CT.gov).
    aplicadas = 0
    for m in mudancas:
        pos = texto.find(f"'{m['nct']}'")
        if pos == -1:
            continue
        janela = texto[pos: pos + 1200]
        nova = re.sub(rf"(status\s*:\s*)'{re.escape(m['de'])}'",
                      rf"\1'{m['para']}'", janela, count=1)
        if nova != janela:
            texto = texto[:pos] + nova + texto[pos + 1200:]
            aplicadas += 1

    # 2) Cards novos, numa seção própria antes do fecho do array.
    if cards:
        bloco = (f"\n  // ============== NOVOS ESTUDOS ({date.today()}) "
                 f"— RASCUNHO, revisar antes de publicar ==============\n\n")
        bloco += "\n".join(card_js(c) for c in cards)
        fecho = re.search(r"\n\];\s*\n", texto)
        if not fecho:
            print("não encontrei o fecho do array THERA_TRIALS_BR", file=sys.stderr)
            return 1
        texto = texto[: fecho.start()] + "\n" + bloco + texto[fecho.start():]

    esperado = antes + len(cards)
    ok, msg = validar(texto, esperado)
    print(f"cards novos ......... {len(cards)}")
    print(f"status atualizados .. {aplicadas}/{len(mudancas)}")
    print(f"total ............... {antes} -> {esperado}")
    print(f"validação node ...... {'OK — ' + msg if ok else 'FALHOU — ' + msg}")
    if not ok:
        print("\nnada foi gravado.", file=sys.stderr)
        return 1

    baixa = [c["_factual"]["nct"] for c in cards if c.get("confianca") == "baixa"]
    if baixa:
        print(f"\n⚠ confiança baixa, revisar primeiro: {', '.join(baixa[:12])}")

    if args.dry_run:
        print("\n--dry-run: arquivo não foi alterado")
        return 0
    TRIALS_JS.write_text(texto, encoding="utf-8")
    print(f"\ngravado: {TRIALS_JS.relative_to(SITE)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
