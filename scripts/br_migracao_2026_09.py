#!/usr/bin/env python3
"""
br_migracao_2026_09.py — primeira atualização real do Trial Matcher (set/2026).

Aplica, sobre um ARQUIVO INDICADO (nunca direto no banco publicado):

  1. META.status  + 'Recrutamento encerrado no Brasil' (brazil_status CLOSED_IN_BRAZIL)
  2. META.biomarcadores + 'HER2-low'
  3. migração semântica de biomarcadores em 28 cards (tabela MIGRACAO abaixo)

Idempotente: rodar duas vezes não muda nada na segunda. Seguro: se um card não
estiver exatamente no estado `antes` da tabela, ele NÃO é tocado e o script
termina com erro — o banco mudou desde a revisão e a tabela precisa ser revista.

Uso:
    cp assets/js/trials_br.js scripts/_br_base/trials_br.js
    python3 scripts/br_migracao_2026_09.py scripts/_br_base/trials_br.js
    python3 scripts/br_ciclo.py --sem-descoberta --base scripts/_br_base/trials_br.js

── O campo novo ─────────────────────────────────────────────────────────────

`biomarcadores` (lista de strings) continua existindo e continua sendo o que o
filtro usa — o app já publicado lê esse campo, então o tipo não pode mudar. O
que muda é a REGRA: ali só entra o que o paciente PRECISA TER (positivo,
presente, mutado, no estado exigido). Negatividade exigida nunca entra ali.

`biomarcadores_criterios` (opcional) é o detalhe. Quando existe, é a fonte, e
`biomarcadores` é derivado dele (os `requerido`, na ordem):

    { marcador: 'HER2',      exigencia: 'requerido', estado: 'positivo (IHQ 3+ ou ISH+)' }
    { marcador: 'HER2-low',  exigencia: 'requerido', estado: 'IHQ 1+ ou 2+/ISH−' }
    { marcador: 'HER2',      exigencia: 'excluido',  estado: 'positivo' }      ← HER2−
    { marcador: 'PD-L1',     exigencia: 'requerido', estado: 'TPS ≥ 50%' }     ← corte
    { marcador: 'PD-L1',     exigencia: 'avaliado',  estado: 'resultado avaliável' }
    { marcador: 'EGFR',      exigencia: 'requerido', estado: 'mutação sensibilizante' }
    { marcador: 'KRAS G12C', exigencia: 'requerido' }
    { marcador: 'BRCA',      exigencia: 'requerido', estado: 'BRCA1/2 germinativo' }
    { marcador: 'PIK3CA',    exigencia: 'excluido',  estado: 'mutação' }       ← wild-type

`exigencia` ∈ requerido | excluido | avaliado. Em estudo com coortes de
critérios diferentes, cada critério leva `coorte` (ex.: BREAKER-101: HER2
requerido em 'Mama HER2+' e excluído em 'Mama HR+/HER2−').

`alvos` (opcional, lista de strings) é o ALVO MOLECULAR DA INTERVENÇÃO —
TROP-2 de um anti-TROP-2, EGFR/HER3 de um biespecífico. Não é critério de
elegibilidade e o filtro não o usa. Um marcador pode estar nos dois (CLDN18.2
no LUCERNA é alvo do zolbetuximabe E critério de entrada).

── A tabela ─────────────────────────────────────────────────────────────────

Cada entrada cita a evidência do PRÓPRIO card (subtipo, critérios, testes).
Nada vem de conhecimento externo sobre o fármaco. `revisar` marca o que o texto
do card não resolve e fica para o revisor clínico — nesses casos o marcador foi
mantido como estava.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

R, X, A = "requerido", "excluido", "avaliado"
C_MAMA_HER2, C_MAMA_HR = "Mama HER2+", "Mama HR+/HER2−"
C_CRC, C_NSCLC = "Colorretal KRAS-mutado", "NSCLC KRAS-mutado"
HER2_NEG = ("HER2", X, "positivo")

MIGRACAO: dict[str, dict] = {
    # ── HER2-negativos com HER2 listado como exigido (o erro do filtro) ─────
    "cambria-1": dict(antes=["RE", "HER2"], criterios=[("RE", R, ">10%"), HER2_NEG],
                      evidencia="Mama invasivo RE >10%/HER2-"),
    "cambria-2": dict(antes=["RE", "HER2"], criterios=[("RE", R, ">10%"), HER2_NEG],
                      evidencia="Mama invasivo ressecado RE >10%/HER2-"),
    "pf-07248144-fulvestranto-fase-3": dict(
        antes=["RE", "HER2"], criterios=[("RE", R, "HR+"), HER2_NEG],
        evidencia="Câncer de mama avançado ou metastático HR+/HER2−"),
    "opera-01": dict(antes=["RE", "HER2"], criterios=[("RE", R, ""), HER2_NEG],
                     evidencia="Mama ER+/HER2− localmente avançada ou metastática"),
    "elegant": dict(antes=["RE", "HER2"], criterios=[("RE", R, "≥10% por IHQ"), HER2_NEG],
                    evidencia="RE positivo (≥10% por IHQ), HER2 negativo"),
    "moonrose": dict(antes=["RE", "HER2"], criterios=[("RE", R, ""), HER2_NEG],
                     evidencia="RE positivo e HER2 negativo documentados"),
    "pikalo-2": dict(antes=["PIK3CA", "RE", "HER2"],
                     criterios=[("PIK3CA", R, "mutação documentada"), ("RE", R, "HR+"), HER2_NEG],
                     evidencia="HR positivo e HER2 negativo; Mutação de PIK3CA documentada"),
    "adela": dict(antes=["ESR1", "RE", "HER2"],
                  criterios=[("ESR1", R, "mutação documentada"), ("RE", R, ""), HER2_NEG],
                  evidencia="ER positivo e HER2 negativo; Mutação de ESR1 documentada"),
    "bgb-43395-fase-1a-1b": dict(
        antes=["RE", "HER2"],
        criterios=[("RE", R, "mama HR+ (a fase 1a também inclui ovário e endométrio)"), HER2_NEG],
        evidencia="Fase 1b (expansão): mama HR+/HER2− metastática"),
    "mk-2870-010": dict(
        antes=["RE", "HER2", "TROP-2"],
        criterios=[("RE", R, "HR+, confirmado centralmente"), HER2_NEG],
        alvos=["TROP-2"],
        evidencia="Receptor hormonal positivo e HER2 negativo, confirmados centralmente; "
                  "TROP-2 é o alvo do fármaco, sem critério de elegibilidade (decisão do "
                  "revisor, 2026-09-27)"),
    "neosamba": dict(antes=["HER2"], criterios=[HER2_NEG],
                     evidencia="Carcinoma invasivo de mama HER2 negativo"),
    "inavolisibe-ribociclibe-chr8p-loss": dict(
        antes=["PIK3CA", "RE", "RP", "HER2"],
        criterios=[("RE", R, "RE e/ou RP ≥1%"), ("RP", R, "RE e/ou RP ≥1%"),
                   ("Perda de 8p", R, "perda heterozigótica, laboratório central"),
                   ("PIK3CA", X, "mutação — exige PIK3CA sem mutação"), HER2_NEG],
        evidencia="Perda heterozigótica de 8p E ausência de mutação de PIK3CA, ambas por "
                  "laboratório central"),
    "rosetta-breast-01": dict(
        antes=["TNBC", "PD-L1", "RE", "HER2"],
        criterios=[("TNBC", R, "TNBC ou RE-baixo (RE e/ou RP 1–10%)"),
                   ("PD-L1", X, "status que torna elegível a anti-PD(L)1"),
                   ("RE", A, "RE-baixo (1–10%) aceito, não exigido"), HER2_NEG],
        evidencia="Inelegível a imunoterapia anti-PD(L)1 ... pelo status de PD-L1; TNBC ... "
                  "OU mama ER-low (RE e/ou RP 1-10%) HER2 negativo"),
    "rosetta-gi-202": dict(
        antes=["PD-L1", "HER2"],
        criterios=[("PD-L1", R, "≥1 obrigatório na fase 3 (a fase 2 aceita <1)"), HER2_NEG],
        evidencia="PD-L1 documentado ≥ 1 ou menor que 1 na fase 2; PD-L1 ≥ 1 obrigatório "
                  "na fase 3; HER2 negativo documentado"),
    "sonesitatugue-vedotina-em-gastrico-cldn18-2": dict(
        antes=["CLDN18.2", "HER2", "PD-L1", "CPS"],
        criterios=[("CLDN18.2", R, "positivo, IHQ central"),
                   ("PD-L1", A, "CPS define a coorte: positivo ou negativo"),
                   ("CPS", A, "define a coorte"), HER2_NEG],
        evidencia="CLDN18.2 positivo; PD-L1 CPS: coorte 1 positivo, coorte 2 negativo; "
                  "exclusão: HER2 positivo conhecido"),
    "lucerna": dict(
        antes=["CLDN18.2", "HER2"],
        criterios=[("CLDN18.2", R, "≥75% das células, marcação membranar moderada/forte, IHQ central"),
                   ("PD-L1", R, "CPS ≥ 1, IHQ central"), HER2_NEG],
        alvos=["CLDN18.2"],
        evidencia="Registro NCT06901531: HER2-negative tumor; CLDN18.2 ≥ 75% ... central IHC; "
                  "PD-L1 CPS ≥ 1 ... central IHC (conferido na API em 2026-09-27)"),
    # ── HER2-low / HER2 IHQ 0 ───────────────────────────────────────────────
    "nct05950945": dict(
        antes=["HER2"], criterios=[("HER2", X, "positivo — aceita HER2-low e IHQ 0")],
        evidencia="HER2 IHQ 1+ ou IHQ 2+/ISH negativo (HER2-baixo), ou HER2 IHQ 0; nunca ter "
                  "sido HER2 positivo"),
    "disitamab-vedotina-fase-1b-2": dict(
        antes=["HER2"],
        criterios=[("HER2", R, "positivo (IHQ 3+ ou 2+/ISH+) — coorte 1"),
                   ("HER2-low", R, "baixo ou ultrabaixo — coortes 2 e 3")],
        evidencia="Três coortes: HER2+ (IHQ 3+ ou 2+/ISH+); HR+ com HER2-low; HR+ HER2-ultralow "
                  "ou HR− HER2-low"),
    "t-dxd-subcut-neo": dict(
        antes=["HER2"],
        criterios=[("HER2", R, "positivo (mama) ou mutação ativadora (NSCLC)"),
                   ("HER2-low", R, "baixo ou ultrabaixo (mama)")],
        evidencia="Mama HER2-positiva, mama HER2-baixo ou ultrabaixo ..., e NSCLC com mutação "
                  "de HER2"),
    "breaker-101": dict(
        antes=["HER2", "HR+", "HER2-", "KRAS"],
        criterios=[("HER2", R, "positivo", C_MAMA_HER2),
                   ("HR+", R, "", C_MAMA_HR),
                   ("HER2", X, "positivo", C_MAMA_HR),
                   ("PIK3CA", R, "mutação confirmada — só coortes com fulvestranto", C_MAMA_HR),
                   ("KRAS", R, "mutado", C_CRC),
                   ("KRAS G12R", X, "mutação", C_CRC),
                   ("BRAF", X, "V600E", C_CRC),
                   ("HER2", X, "amplificação", C_CRC),
                   ("MSI-H", X, "dMMR/MSI-H", C_CRC),
                   ("KRAS", R, "mutado", C_NSCLC),
                   ("KRAS G12R", X, "mutação", C_NSCLC),
                   ("EGFR", X, "driver acionável", C_NSCLC),
                   ("ALK", X, "driver acionável", C_NSCLC),
                   ("ROS1", X, "driver acionável", C_NSCLC),
                   ("BRAF", X, "driver acionável", C_NSCLC),
                   ("RET", X, "driver acionável", C_NSCLC),
                   ("MET", X, "driver acionável", C_NSCLC),
                   ("NTRK", X, "driver acionável", C_NSCLC),
                   ("HER2", X, "driver acionável", C_NSCLC),
                   ],
        evidencia="Registro NCT06625775: HER2-positive aBC; HR-positive/HER2-negative aBC "
                  "(+ PIK3CA confirmada nas coortes com fulvestranto); KRAS mutant aCRC sem "
                  "G12R, BRAF V600E, HER2amp, dMMR/MSI-H; KRAS mutant aNSCLC sem G12R nem outro "
                  "driver acionável (conferido na API em 2026-09-27)"),
    # ── token 'HER2-' dentro da lista de exigidos ───────────────────────────
    "inavo123": dict(
        antes=["PIK3CA", "HR+", "HER2-"],
        criterios=[("PIK3CA", R, "mutação confirmada centralmente"), ("HR+", R, ""), HER2_NEG],
        evidencia="RE-positivo e/ou RP-positivo e HER2-negativo; Mutação de PIK3CA confirmada"),
    "pionera-breast-cancer": dict(
        antes=["RE+", "HER2-", "ESR1"],
        criterios=[("RE+", R, ""), HER2_NEG, ("ESR1", A, "status mutacional em ctDNA, central")],
        evidencia="RE-positivo e HER2-negativo; ESR1 avaliado, não exigido (decisão do revisor, "
                  "2026-09-27)"),
    "viktoria-2": dict(
        antes=["HR+", "HER2-", "PIK3CA"],
        criterios=[("HR+", R, ""), HER2_NEG,
                   ("PIK3CA", A, "status mutacional analisado; mutação não exigida no card")],
        evidencia="HR+/HER2-; testes: 'Análise do status mutacional de PIK3CA' — o subtipo não "
                  "exige mutação",
        revisar="PIK3CA passou de exigido para avaliado: o card só pede a análise. Confirmar "
                "no registro."),
    "herthena-breast04": dict(
        antes=["HR+", "HER2-", "HER3"],
        criterios=[("HR+", R, "confirmação central"), HER2_NEG,
                   ("HER3", A, "resultado avaliável em biópsia recente")],
        evidencia="Confirmação central de HR+ e HER2- e resultado avaliável de HER3"),
    "izabright-breast01": dict(
        antes=["Triplo-negativo", "RE-baixo", "HER2-", "EGFR", "HER3"],
        criterios=[("TNBC", R, "triplo-negativo ou RE-baixo (RE e/ou RP 1–10%)"), HER2_NEG],
        alvos=["EGFR", "HER3"],
        evidencia="Mama triplo-negativa ou RE-baixo HER2-negativa; EGFR e HER3 são alvos do "
                  "fármaco, sem critério de elegibilidade (decisão do revisor, 2026-09-27)"),
    "inavolisibe-neoadjuvante": dict(
        antes=["PIK3CA", "RE+", "HER2-", "Ki-67"],
        criterios=[("PIK3CA", R, "mutação confirmada"), ("RE+", R, ""), HER2_NEG,
                   ("Ki-67", R, "≥5% em avaliação local")],
        evidencia="RE-positivo e HER2-negativo; Ki-67 ≥5%; Mutação de PIK3CA confirmada"),
    "adjuvant-wider": dict(
        antes=["HR+", "HER2-"],
        criterios=[("HR+", R, ""), ("HER2", X, "positivo — aceita IHQ 0, 1+ ou 2+/ISH−")],
        evidencia="HER2-negativo por ISH negativa ou IHQ 0, 1+ ou 2+ com ISH negativa"),
    "lara": dict(
        antes=["RE+", "RP+", "HER2-"],
        criterios=[("RE+", R, "RE e/ou RP"), ("RP+", R, "RE e/ou RP"), HER2_NEG],
        evidencia="RE-positivo e/ou RP-positivo; exclusão: Mama HER2-positiva"),
}

STATUS_NOVO = "{ id: 'Recrutamento encerrado no Brasil', label: 'Encerrado no Brasil', color: '#a8a29e' },"


def js_str(v: str) -> str:
    return "'" + v.replace("\\", "\\\\").replace("'", "\\'") + "'"


def js_criterios(criterios: list[tuple]) -> str:
    linhas = []
    for c in criterios:
        m, ex, est = c[:3]
        coorte = c[3] if len(c) > 3 else ""
        partes = [f"marcador: {js_str(m)}", f"exigencia: {js_str(ex)}"]
        if est:
            partes.append(f"estado: {js_str(est)}")
        if coorte:
            partes.append(f"coorte: {js_str(coorte)}")
        linhas.append("      { " + ", ".join(partes) + " },\n")
    return "[\n" + "".join(linhas) + "    ]"


def js_lista(vs: list[str]) -> str:
    return "[" + ", ".join(js_str(v) for v in vs) + "]"


def ler_lista(txt: str) -> list[str]:
    return [m.group(1).replace("\\'", "'") for m in re.finditer(r"'((?:[^'\\]|\\.)*)'", txt)]


def migrar_meta(texto: str) -> tuple[str, list[str]]:
    feito = []
    if "id: 'Recrutamento encerrado no Brasil'" not in texto:
        alvo = re.search(r"^(\s*)\{ id: 'Encerrado',", texto, re.M)
        if not alvo:
            raise SystemExit("META.status: não achei a entrada 'Encerrado'")
        texto = texto[:alvo.start()] + alvo.group(1) + STATUS_NOVO + "\n" + texto[alvo.start():].lstrip("\n")
        feito.append("META.status + 'Recrutamento encerrado no Brasil'")
    bloco = re.search(r"^  biomarcadores: \[\n(.*?)^  \],", texto, re.S | re.M)
    if not bloco:
        raise SystemExit("META.biomarcadores não encontrado")
    if "'HER2-low'" not in bloco.group(1):
        novo = bloco.group(1).replace("'HER2', ", "'HER2', 'HER2-low', ", 1)
        if novo == bloco.group(1):
            raise SystemExit("META.biomarcadores: não achei 'HER2' para inserir 'HER2-low' ao lado")
        texto = texto[:bloco.start(1)] + novo + texto[bloco.end(1):]
        feito.append("META.biomarcadores + 'HER2-low'")
    return texto, feito


def bloco_do_card(texto: str, id_: str) -> tuple[int, int]:
    m = re.search(rf"^    id: {re.escape(js_str(id_))},$", texto, re.M)
    if not m:
        raise KeyError(id_)
    ini = texto.rfind("\n  {\n", 0, m.start()) + 1
    fim = texto.find("\n  },\n", m.end()) + len("\n  },\n")
    return ini, fim


def migrar_cards(texto: str) -> tuple[str, list[str], list[str]]:
    feitos, erros = [], []
    for id_, regra in MIGRACAO.items():
        try:
            ini, fim = bloco_do_card(texto, id_)
        except KeyError:
            erros.append(f"{id_}: card não encontrado")
            continue
        bloco = texto[ini:fim]
        derivado: list[str] = []
        for c in regra["criterios"]:
            if c[1] == R and c[0] not in derivado:
                derivado.append(c[0])
        if "biomarcadores_criterios:" in bloco:
            continue  # já migrado
        m = re.search(r"^(\s*)biomarcadores\s*:\s*(\[.*?\]),\n", bloco, re.S | re.M)
        if not m:
            erros.append(f"{id_}: campo biomarcadores não encontrado")
            continue
        atual = ler_lista(m.group(2))
        if atual != regra["antes"]:
            erros.append(f"{id_}: biomarcadores = {atual}, a tabela esperava {regra['antes']}")
            continue
        novo = (f"    biomarcadores: {js_lista(derivado)},\n"
                f"    biomarcadores_criterios: {js_criterios(regra['criterios'])},\n")
        if regra.get("alvos"):
            novo += f"    alvos: {js_lista(regra['alvos'])},\n"
        bloco = bloco[:m.start()] + novo + bloco[m.end():]
        texto = texto[:ini] + bloco + texto[fim:]
        feitos.append(f"{id_}: {atual} → {derivado}")
    return texto, feitos, erros


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__.split("\n\n")[0], file=sys.stderr)
        print("uso: br_migracao_2026_09.py ARQUIVO.js", file=sys.stderr)
        return 2
    alvo = Path(sys.argv[1]).resolve()
    publicado = (Path(__file__).resolve().parent.parent / "assets" / "js" / "trials_br.js").resolve()
    if alvo == publicado:
        print("recusado: aplique numa cópia, não no banco publicado", file=sys.stderr)
        return 2
    texto = alvo.read_text(encoding="utf-8")
    texto, meta = migrar_meta(texto)
    texto, feitos, erros = migrar_cards(texto)
    for f in meta + feitos:
        print("  ✓", f)
    for e in erros:
        print("  ✗", e, file=sys.stderr)
    if erros:
        print("nada foi gravado.", file=sys.stderr)
        return 1
    alvo.write_text(texto, encoding="utf-8")
    print(f"{len(meta)} mudanças na META, {len(feitos)} cards migrados → {alvo.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
