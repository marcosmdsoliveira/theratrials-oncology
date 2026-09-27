#!/usr/bin/env python3
"""
br_migracao_nomes_2026_09.py — acrônimo de outro estudo da mesma família (set/2026).

Seis cards do Trial Matcher traziam o nome/número de OUTRA pesquisa da mesma
família. Em todos, título e intervenção do card batem com o registro do NCT
que o card traz (conferido na API v2 em 2026-09-27): o NCT, os critérios, os
biomarcadores, o status e os centros estão certos — só o nome está errado.

Três dos nomes errados são estudos reais, com outro NCT, então o erro não era
inofensivo: quem buscasse "MajesTEC-9" (NCT05572515, teclistamabe em 1ª
recidiva) caía num card do MajesTEC-7 (NDMM).

Troca apenas o texto exato indicado, dentro do bloco do card, e só uma vez.
Mesma disciplina das outras migrações: cópia, idempotente, aborta sem gravar.

Uso:
    python3 scripts/br_migracao_nomes_2026_09.py scripts/_br_base/trials_br.js
    python3 scripts/br_qa.py scripts/_br_base/trials_br.js --renomear dreamm-20=dynammic-1
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# NCT → (acrônimo no registro, outro estudo que usa o nome errado, [(antes, depois)])
CORRECOES: dict[str, tuple[str, str, list[tuple[str, str]]]] = {
    "NCT06208150": ("MonumenTAL-6", "nenhum estudo com 'MonumenTAL-7' no registro", [
        ("nome: 'MonumenTAL-7',", "nome: 'MonumenTAL-6',"),
        ("(MonumenTAL-7)',", "(MonumenTAL-6)',"),
    ]),
    "NCT05552222": ("MajesTEC-7", "MajesTEC-9 é o NCT05572515", [
        ("nome: 'MajesTEC-9',", "nome: 'MajesTEC-7',"),
        ("(MajesTEC-9)',", "(MajesTEC-7)',"),
    ]),
    "NCT06679101": ("DREAMM-10", "DREAMM-14 é o NCT05064358", [
        ("nome: 'DREAMM-14',", "nome: 'DREAMM-10',"),
        ("(DREAMM-14)',", "(DREAMM-10)',"),
    ]),
    "NCT05020236": ("MAGNETISMM-5", "MagnetisMM-7 é o NCT05317416", [
        ("nome: 'MagnetisMM-7',", "nome: 'MagnetisMM-5',"),
        ("(MagnetisMM-7)',", "(MagnetisMM-5)',"),
    ]),
    "NCT06136624": ("OMAHA-003", "nenhum estudo com 'OPTIME-003' no registro", [
        ("nome: 'OPTIME-003',", "nome: 'OMAHA-003',"),
    ]),
    # O id também sai: era derivado do nome errado, e a busca livre do Trial
    # Matcher varre o card inteiro — "DREAMM-20" continuaria achando este card.
    "NCT05714839": ("DynaMMic-1", "nenhum estudo com 'DREAMM-20' no registro", [
        ("id: 'dreamm-20',", "id: 'dynammic-1',"),
        ("nome: 'DREAMM-20',", "nome: 'DynaMMic-1',"),
    ]),
}


def bloco(texto: str, nct: str) -> tuple[int, int]:
    m = re.search(rf"^    nct: '{nct}',$", texto, re.M)
    if not m:
        raise KeyError(nct)
    ini = texto.rfind("\n  {\n", 0, m.start()) + 1
    fim = texto.find("\n  },\n", m.end()) + len("\n  },\n")
    return ini, fim


def main() -> int:
    if len(sys.argv) != 2:
        print("uso: br_migracao_nomes_2026_09.py ARQUIVO.js", file=sys.stderr)
        return 2
    alvo = Path(sys.argv[1]).resolve()
    publicado = (Path(__file__).resolve().parent.parent / "assets" / "js" / "trials_br.js").resolve()
    if alvo == publicado:
        print("recusado: aplique numa cópia, não no banco publicado", file=sys.stderr)
        return 2
    texto = alvo.read_text(encoding="utf-8")
    feitos, erros = [], []
    for nct, (acr, _, trocas) in CORRECOES.items():
        try:
            ini, fim = bloco(texto, nct)
        except KeyError:
            erros.append(f"{nct}: card não encontrado")
            continue
        b = texto[ini:fim]
        for antes, depois in trocas:
            if b.count(depois) == 1 and b.count(antes) == 0:
                continue  # já corrigido
            if b.count(antes) != 1:
                erros.append(f"{nct}: esperava 1× {antes!r}, achei {b.count(antes)}")
                continue
            b = b.replace(antes, depois)
            feitos.append(f"{nct} ({acr}): {antes}  →  {depois}")
        texto = texto[:ini] + b + texto[fim:]
    for f in feitos:
        print("  ✓", f)
    for e in erros:
        print("  ✗", e, file=sys.stderr)
    if erros:
        print("nada foi gravado.", file=sys.stderr)
        return 1
    alvo.write_text(texto, encoding="utf-8")
    print(f"{len(feitos)} trocas → {alvo.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
