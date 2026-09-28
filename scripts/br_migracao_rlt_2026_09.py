#!/usr/bin/env python3
"""
br_migracao_rlt_2026_09.py — modalidade 'radioligante' na META (set/2026).

Até 2026-09 o Trial Matcher excluía teranósticos, e a META não tinha como
classificá-los. A partir desta migração, radioligante é uma modalidade como
as outras: o discovery só marca o estudo, e a curadoria usa este valor.

Só acrescenta um valor à META.modalidades. Não mexe em card nenhum.
Mesma disciplina das outras migrações: cópia, idempotente, aborta sem gravar.

Uso:
    python3 scripts/br_migracao_rlt_2026_09.py scripts/_br_base/trials_br.js
    python3 scripts/br_ciclo.py --base scripts/_br_base/trials_br.js --permitir-meta
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

NOVA = "    { id: 'radioligante',     label: 'Radioligante (RLT / PRRT)' },\n"
DEPOIS_DE = "    { id: 'hormonioterapia',  label: 'Hormonioterapia' },\n"


def main() -> int:
    if len(sys.argv) != 2:
        print("uso: br_migracao_rlt_2026_09.py ARQUIVO.js", file=sys.stderr)
        return 2
    alvo = Path(sys.argv[1]).resolve()
    publicado = (Path(__file__).resolve().parent.parent / "assets" / "js" / "trials_br.js").resolve()
    if alvo == publicado:
        print("recusado: aplique numa cópia, não no banco publicado", file=sys.stderr)
        return 2
    texto = alvo.read_text(encoding="utf-8")
    m = re.search(r"^  modalidades: \[\n(.*?)^  \],\n", texto, re.S | re.M)
    if not m:
        print("META.modalidades não encontrado — nada foi gravado.", file=sys.stderr)
        return 1
    bloco = m.group(1)
    if "id: 'radioligante'" in bloco:
        print("já aplicado (META.modalidades tem 'radioligante')")
        return 0
    if bloco.count(DEPOIS_DE) != 1:
        print("esperava 1× a linha de 'hormonioterapia' em META.modalidades — "
              "nada foi gravado.", file=sys.stderr)
        return 1
    novo = bloco.replace(DEPOIS_DE, DEPOIS_DE + NOVA)
    alvo.write_text(texto[:m.start(1)] + novo + texto[m.end(1):], encoding="utf-8")
    print(f"META.modalidades + 'radioligante' → {alvo.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
