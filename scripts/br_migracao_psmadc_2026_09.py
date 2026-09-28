#!/usr/bin/env python3
"""
br_migracao_psmadc_2026_09.py — exclusões do PSMA-DC (NCT05939414), set/2026.

O card entrou com 6 exclusões resumidas e deixou fora critérios que eliminam
candidatos de fato (conferido no registro em 2026-09-28): obstrução vesical ou
incontinência não controláveis, estrógenos/inibidores da 5-α-redutase,
terapia concomitante (inclusive inibidor de PARP) e a exigência de adiar a
castração até a progressão à distância. O registro tem 8 itens de exclusão.

Troca SÓ `criterios_exclusao` deste card, e só se as 6 exclusões atuais forem
exatamente as esperadas. Mesma disciplina das outras migrações: cópia,
idempotente, aborta sem gravar.

Uso:
    python3 scripts/br_migracao_psmadc_2026_09.py scripts/_br_base/trials_br.js
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

NCT = "NCT05939414"

ANTES = [
    "Doença oligometastática de novo (sem tratamento definitivo prévio do primário)",
    "ADT ou ARPI para doença metastática; ADT/ARPI neo/adjuvante ou para recidiva só se "
    "suspensos há ≥12 meses (ADT) ou ≥3 meses (ARPI isolado); CRPC excluído",
    "Radiofármaco prévio (ex.: estrôncio-89, radioligante dirigido a PSMA), imunoterapia "
    "(ex.: sipuleucel-T) ou quimioterapia fora do cenário neo/adjuvante concluído há >12 meses",
    "Radioterapia externa ou braquiterapia nos 28 dias antes da randomização",
    "Outra neoplasia que altere a expectativa de vida ou interfira na avaliação (exceto "
    "tratada e livre de doença há >3 anos, pele não melanoma e bexiga superficial)",
    "Arritmia clinicamente significativa, BAV de 2º/3º grau sem marca-passo ou QT longo "
    "familiar; necessidade imediata de ADT ou outra terapia sistêmica",
]

DEPOIS = [
    "Doença oligometastática de novo (sem tratamento definitivo prévio do primário)",
    "ADT ou ARPI para doença metastática, e CRPC; ADT/ARPI neo/adjuvante ou na recidiva só "
    "se suspensos há ≥12 meses (ADT) ou ≥3 meses (ARPI isolado ou antiandrogênio de 1ª "
    "geração); estrógenos ou inibidores da 5-α-redutase usados para o câncer de próstata "
    "(para HPB, só se suspensos há ≥3 meses)",
    "Radiofármaco prévio (ex.: estrôncio-89, radioligante dirigido a PSMA), imunoterapia "
    "(ex.: sipuleucel-T), quimioterapia fora do cenário neo/adjuvante concluído há >12 "
    "meses, ou outro agente sistêmico ou experimental para doença metastática",
    "Radioterapia externa ou braquiterapia nos 28 dias antes da randomização; "
    "quimioterapia, imunoterapia, radioligante, hormonioterapia, inibidor de PARP, terapia "
    "biológica ou experimental concomitantes",
    "Obstrução do trato de saída vesical ou incontinência urinária não controláveis com o "
    "cuidado padrão",
    "Outra neoplasia que altere a expectativa de vida ou interfira na avaliação (exceto "
    "tratada e livre de doença há >3 anos, pele não melanoma e bexiga superficial)",
    "Arritmia clinicamente significativa, BAV de 2º/3º grau sem marca-passo, QT longo "
    "familiar ou história familiar de torsades de pointes",
    "Necessidade imediata de ADT ou outra terapia sistêmica, ou falta de disposição para "
    "adiar a castração até a progressão à distância confirmada por revisão central",
]


def js_lista(itens: list[str]) -> str:
    esc = lambda s: s.replace("\\", "\\\\").replace("'", "\\'")  # noqa: E731
    return "[\n" + "".join(f"      '{esc(s)}',\n" for s in itens) + "    ]"


def main() -> int:
    if len(sys.argv) != 2:
        print("uso: br_migracao_psmadc_2026_09.py ARQUIVO.js", file=sys.stderr)
        return 2
    alvo = Path(sys.argv[1]).resolve()
    publicado = (Path(__file__).resolve().parent.parent / "assets" / "js" / "trials_br.js").resolve()
    if alvo == publicado:
        print("recusado: aplique numa cópia, não no banco publicado", file=sys.stderr)
        return 2
    texto = alvo.read_text(encoding="utf-8")
    m = re.search(rf"^    nct: '{NCT}',$", texto, re.M)
    if not m:
        print(f"{NCT}: card não encontrado — nada foi gravado.", file=sys.stderr)
        return 1
    ini = texto.rfind("\n  {\n", 0, m.start()) + 1
    fim = texto.find("\n  },\n", m.end()) + len("\n  },\n")
    bloco = texto[ini:fim]
    lista = re.search(r"(    criterios_exclusao: )(\[\n.*?\n    \])", bloco, re.S)
    if not lista:
        print(f"{NCT}: criterios_exclusao não encontrado — nada foi gravado.", file=sys.stderr)
        return 1
    atual = lista.group(2)
    if atual == js_lista(DEPOIS):
        print("já aplicado")
        return 0
    if atual != js_lista(ANTES):
        print(f"{NCT}: as exclusões atuais não são as 6 esperadas — nada foi gravado.",
              file=sys.stderr)
        return 1
    novo_bloco = bloco[:lista.start(2)] + js_lista(DEPOIS) + bloco[lista.end(2):]
    alvo.write_text(texto[:ini] + novo_bloco + texto[fim:], encoding="utf-8")
    print(f"{NCT}: criterios_exclusao 6 → {len(DEPOIS)} itens → {alvo.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
