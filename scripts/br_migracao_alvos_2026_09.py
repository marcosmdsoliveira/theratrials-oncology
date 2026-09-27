#!/usr/bin/env python3
"""
br_migracao_alvos_2026_09.py — alvo da droga × critério de elegibilidade (set/2026).

Segunda migração de biomarcadores do Trial Matcher. Revisa os 42 casos de
`_br_alvos_a_revisar.md` (marcador em `biomarcadores` que o card não sustentava
como critério), mais 7 cards achados na mesma revisão em que EGFR/ALK/ROS1/
KRAS/NRAS/BRAF estavam como EXIGIDOS quando o registro exige o tipo selvagem.

Toda decisão vem do registro oficial do ClinicalTrials.gov (API v2, consultada
em 2026-09-27) — elegibilidade, títulos, descrição, intervenções, palavras-chave
e desfechos. Nada é inferido pelo mecanismo da droga.

Classes de decisão (campo `classe` de cada movimento):
  alvo-direto      o registro descreve o mecanismo (anti-X, X-directed), lista X
                   nas palavras-chave ou mede "anticorpo anti-X total" na PK, e a
                   elegibilidade não exige X                          → `alvos`
  alvo-contextual  a elegibilidade só cita X como TRATAMENTO PRÉVIO dirigido a X
                   (excluído ou regulado), nunca como expressão exigida → `alvos`
  avaliado         o registro mede X e aceita qualquer resultado
  requerido        a elegibilidade exige X — permanece
  revisao          o registro não cita X em lugar nenhum — NADA muda; fica para
                   o revisor clínico (tabela REVISAO)

Mesma disciplina da primeira migração: roda sobre uma CÓPIA, é idempotente, e
aborta sem gravar se algum card não estiver no estado `antes` esperado.

Uso:
    python3 scripts/br_migracao_alvos_2026_09.py scripts/_br_base/trials_br.js
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from br_migracao_2026_09 import bloco_do_card, js_lista, js_str, ler_lista  # noqa: E402

R, X, A = "requerido", "excluido", "avaliado"

# ── Movimentos para `alvos` (sem outros critérios no card) ──────────────────
# id → (antes, [(marcador, classe, evidência do registro)])
PARA_ALVOS: dict[str, tuple[list[str], list[tuple[str, str, str]]]] = {
    "tropical-1": (["PD-L1", "TROP-2"], [("TROP-2", "alvo-direto",
        "Dato-DXd ... composed of a humanized anti-TROP2 IgG1 monoclonal antibody")]),
    "magnetismm-6": (["BCMA"], [("BCMA", "alvo-direto",
        "binding of elranatamab to CD3-expressing T-cells and BCMA-expressing multiple myeloma cells")]),
    "nct05020236": (["BCMA"], [("BCMA", "alvo-direto",
        "the BCMA-CD3 bispecific antibody elranatamab; keywords: B-Cell Maturation Antigen")]),
    "ideate-lung02": (["B7-H3"], [("B7-H3", "alvo-direto",
        "Ifinatamab Deruxtecan (I-DXd), a B7-H3 Antibody Drug Conjugate")]),
    "linker-mm3": (["BCMA"], [("BCMA", "alvo-direto",
        "Anti- BCMA x Anti-CD3 Bispecific Antibody")]),
    "arlocabtagene-autoleucel": (["GPRC5D"], [("GPRC5D", "alvo-direto",
        "Arlocabtagene Autoleucel (BMS-986393), a GPRC5D-directed CAR-T Cell Therapy")]),
    "durga-4": (["BCMA", "CD19"], [
        ("BCMA", "alvo-direto", "AZD0120, a Dual-Targeting ... CAR-T Therapy Directed Against BCMA and CD19"),
        ("CD19", "alvo-direto", "AZD0120, a Dual-Targeting ... CAR-T Therapy Directed Against BCMA and CD19")]),
    "trofuse-011": (["TNBC", "PD-L1", "CPS", "TROP-2"], [("TROP-2", "alvo-direto",
        "keyword: Trophoblast cell-surface antigen 2 (TROP2); elegibilidade não cita TROP2")]),
    "nct07216703": (["PD-L1", "TROP-2"], [("TROP-2", "alvo-direto",
        "keyword: Trophoblast Cell Surface Antigen 2 (TROP2); elegibilidade não cita TROP2")]),
    "tropion-breast05": (["TNBC", "PD-L1", "CPS", "TROP-2"], [("TROP-2", "alvo-direto",
        "keyword TROP2; PK: total anti-TROP2 antibody; exclusão: prior TROP2-targeted therapy")]),
    "nct06629779": (["EZH2", "AR"], [
        ("EZH2", "alvo-direto", "keyword: EZH2; elegibilidade não cita EZH2"),
        ("AR", "alvo-contextual", "exclusão: sem androgen receptor signaling inhibitors prévios (ARSi) — "
                                  "é histórico de tratamento, não biomarcador")]),
    "nct07028853": (["EZH2", "AR"], [("EZH2", "alvo-direto", "keyword: EZH2; elegibilidade não cita EZH2")]),
    "nct06084936": (["CD20"], [("CD20", "alvo-contextual",
        "exclusão: prior glofitamab or other bispecific antibodies targeting both CD20 and CD3")]),
    "nct06966700": (["TROP-2", "PD-L1"], [("TROP-2", "alvo-contextual",
        "exclusão: prior TROP2-targeted antibody-drug conjugate (ADC)")]),
    "nct07419295": (["TROP-2", "PD-L1", "Nectin-4"], [("TROP-2", "alvo-contextual",
        "exclusão: prior TROP2-targeted antibody drug conjugate (ADC)")]),
    "andrometa-crc": (["c-MET"], [("c-MET", "alvo-contextual",
        "exclusão: prior systemic regimen containing c-Met targeting agent(s)")]),
    "majestec-4": (["BCMA"], [("BCMA", "alvo-contextual", "exclusão: any prior BCMA-directed therapy")]),
    "dreamm-20": (["BCMA"], [("BCMA", "alvo-contextual",
        "exclusão: prior treatment with OTHER anti-BCMA directed agents is allowed (washout 6 meses)")]),
}

# ── Cards que ganham biomarcadores_criterios (+ alvos) ──────────────────────
# id → dict(antes, criterios, alvos, evidencia)
COM_CRITERIOS: dict[str, dict] = {
    # avaliado — o registro mede e aceita os dois resultados
    "nct06459180": dict(antes=["TROP-2"], criterios=[
        ("TROP-2", A, "expressão alta define uma população da hipótese primária; não é critério de entrada")],
        evidencia="hipótese: OS superior 'in participants with high TROP2 expression level and in all "
                  "participants'; elegibilidade não cita TROP2"),
    "nct06136650": dict(antes=["AR"], criterios=[
        ("AR", A, "mutação do LBD: positivos e negativos entram")],
        evidencia="hipótese: OS 'in AR LBD mutation positive and negative participants'"),
    "nct06136624": dict(antes=["AR"], criterios=[
        ("AR", A, "mutação do LBD: positivos e negativos entram")],
        evidencia="hipótese e desfecho: OS in AR LBD mutation-negative and -positive participants"),
    # selvagem exigido estava como exigido (achados na revisão; registro confere)
    "origami-2": dict(antes=["KRAS", "NRAS", "BRAF", "EGFR", "MET"], criterios=[
        ("KRAS", X, "mutação — exige selvagem"), ("NRAS", X, "mutação — exige selvagem"),
        ("BRAF", X, "mutação — exige selvagem"), ("HER2", X, "positivo/amplificado"),
        ("MSI-H", X, "dMMR/MSI-H")], alvos=["EGFR", "MET"],
        evidencia="KRAS, NRAS and BRAF wild-type (WT) tumor; exclui dMMR/MSI-H e HER2-positive/amplified; "
                  "exclui prior agents that target EGFR, MET or VEGF"),
    "origami-3": dict(antes=["KRAS", "NRAS", "BRAF", "EGFR", "MET"], criterios=[
        ("KRAS", X, "mutação G12/G13 — exige selvagem"), ("NRAS", X, "mutação G12/G13 — exige selvagem"),
        ("BRAF", X, "V600X — exige selvagem"), ("HER2", X, "positivo/amplificado"),
        ("MSI-H", X, "dMMR/MSI-H sem imunoterapia prévia")], alvos=["EGFR", "MET"],
        evidencia="KRAS/NRAS G12, G13 and BRAF V600X wild-type; exclui HER2-positive/amplified e dMMR/MSI-H "
                  "sem imunoterapia; exclui prior agents that target EGFR or MET"),
    "pacific-8": dict(antes=["PD-L1", "EGFR", "ALK"], criterios=[
        ("PD-L1", R, "≥ 1%, laboratório central"), ("EGFR", X, "mutação — exige selvagem"),
        ("ALK", X, "rearranjo — exige selvagem")],
        evidencia="Documented tumour PD-L1 status ≥ 1% by central lab; Documented EGFR and ALK wild-type status"),
    "nivolumabe-em-baixa-dose-neoadjuvante": dict(antes=["PD-L1", "EGFR", "ALK", "ROS1"], criterios=[
        ("PD-L1", A, "expressão documentada e avaliável"), ("EGFR", X, "positivo"),
        ("ALK", X, "expressão positiva"), ("ROS1", X, "expressão positiva")],
        evidencia="Negative for EGFR gene expression; Negative for ALK and ROS1 protein expression; "
                  "PD-L1 protein expression documented and assessable"),
    "artemide-lung04": dict(antes=["PD-L1", "EGFR", "ALK", "ROS1"], criterios=[
        ("PD-L1", R, "alto (título oficial: PD-L1-high)"),
        ("EGFR", X, "mutação sensibilizante — não escamoso"), ("ALK", X, "rearranjo — não escamoso"),
        ("ROS1", X, "rearranjo — não escamoso")],
        evidencia="Official title: ... PD-L1-high Metastatic NSCLC; Absence of sensitizing EGFR mutations and "
                  "ALK and ROS1 rearrangements (negative assay required for non-squamous)"),
    # achado pela trava nova do QA (marcador exigido com texto "negativo")
    "trofuse-021": dict(antes=["HRD"], criterios=[
        ("HRD", X, "positivo, desconhecido ou inconclusivo (laboratório central)")],
        evidencia="Título: 'Non-HRD Positive Ovarian Cancer'; exclusão: HRD-positive, unknown, or "
                  "inconclusive tumor status as determined by the central laboratory"),
    "telisotuzumabe-vedotina-c-met": dict(antes=["c-Met", "EGFR"], criterios=[
        ("c-Met", R, "superexpressão: ≥25% das células 3+ (IHQ do patrocinador)"),
        ("EGFR", X, "mutação ativadora (ex19del, L858R, T790M, ex20ins)")], alvos=["c-Met"],
        evidencia="Must have c-Met overexpressing NSCLC (>= 25% tumor cells with 3+); exclusão: EGFR activating "
                  "mutations; exclusão: prior c-Met-targeted antibodies or ADC"),
}

# ── Só `alvos`, card já com critérios ───────────────────────────────────────
ALVOS_EXTRA = {
    "viktoria-2": (["PI3K", "mTOR"], "Gedatolisib is an intravenously administered pan-PI3K/mTOR inhibitor; "
                   "PIK3CA segue `avaliado`: elegibilidade só exige material 'for the analysis of PIK3CA "
                   "mutational status', e as coortes são por sensibilidade endócrina"),
}

# ── Sem mudança: o registro não cita o marcador em lugar nenhum ─────────────
REVISAO = [
    ("nct06525220", "LGR5"), ("nct06780111", "TROP-2"), ("nct06445972", "TROP-2"),
    ("nct05633654", "TROP-2"), ("nct06208150", "GPRC5D"), ("nct06208150", "BCMA"),
    ("nct05552222", "BCMA"), ("nct05552222", "GPRC5D"), ("nct06679101", "BCMA"),
    ("nct07076121", "CEACAM5"), ("nct07028853", "AR"), ("nct06170788", "TROP-2"),
    ("nct06469944", "TROP-2"), ("nct07218380", "Nectin-4"), ("nct07419295", "Nectin-4"),
    ("evoke-sclc-04", "TROP-2"),
]
# Motivo comum: nem elegibilidade, nem descrição, nem palavras-chave, nem
# desfechos citam o marcador. Em nct06445972 e nct06469944 a exclusão cita
# "TROP2- or HER3-targeted agent" — não diz qual dos dois é o da droga.
PERMANECE = [("tropion-lung17", "TROP-2",
              "Prospectively assessed TROP2 NMR positive ... central laboratory — critério real")]


def js_criterios(criterios: list[tuple]) -> str:
    linhas = []
    for m, ex, est in criterios:
        partes = [f"marcador: {js_str(m)}", f"exigencia: {js_str(ex)}"]
        if est:
            partes.append(f"estado: {js_str(est)}")
        linhas.append("      { " + ", ".join(partes) + " },\n")
    return "[\n" + "".join(linhas) + "    ]"


def aplicar(texto: str) -> tuple[str, list[str], list[str]]:
    feitos, erros = [], []

    def trocar_bloco(id_: str, fn) -> None:
        nonlocal texto
        try:
            ini, fim = bloco_do_card(texto, id_)
        except KeyError:
            erros.append(f"{id_}: card não encontrado")
            return
        bloco = texto[ini:fim]
        novo = fn(bloco)
        if isinstance(novo, str) and novo != bloco:
            texto = texto[:ini] + novo + texto[fim:]

    def campo_bio(bloco: str):
        return re.search(r"^(\s*)biomarcadores\s*:\s*(\[.*?\]),\n", bloco, re.S | re.M)

    def por_alvos(id_, antes, movs):
        def fn(bloco):
            if re.search(r"^    alvos\s*:", bloco, re.M):
                return bloco  # já migrado
            m = campo_bio(bloco)
            atual = ler_lista(m.group(2)) if m else None
            if atual != antes:
                erros.append(f"{id_}: biomarcadores = {atual}, esperado {antes}")
                return bloco
            sai = [mk for mk, _, _ in movs]
            fica = [b for b in atual if b not in sai]
            novo = f"    biomarcadores: {js_lista(fica)},\n    alvos: {js_lista(sai)},\n"
            feitos.append(f"{id_}: {', '.join(sai)} → alvos ({'/'.join(sorted({c for _, c, _ in movs}))})")
            return bloco[:m.start()] + novo + bloco[m.end():]
        return fn

    def por_criterios(id_, regra):
        def fn(bloco):
            if "biomarcadores_criterios:" in bloco:
                return bloco
            m = campo_bio(bloco)
            atual = ler_lista(m.group(2)) if m else None
            if atual != regra["antes"]:
                erros.append(f"{id_}: biomarcadores = {atual}, esperado {regra['antes']}")
                return bloco
            req: list[str] = []
            for mk, ex, _ in regra["criterios"]:
                if ex == R and mk not in req:
                    req.append(mk)
            novo = (f"    biomarcadores: {js_lista(req)},\n"
                    f"    biomarcadores_criterios: {js_criterios(regra['criterios'])},\n")
            if regra.get("alvos"):
                novo += f"    alvos: {js_lista(regra['alvos'])},\n"
            feitos.append(f"{id_}: {atual} → {req}" + (f" + alvos {regra['alvos']}" if regra.get("alvos") else ""))
            return bloco[:m.start()] + novo + bloco[m.end():]
        return fn

    def alvos_extra(id_, alvos):
        def fn(bloco):
            if re.search(r"^    alvos\s*:", bloco, re.M):
                return bloco
            m = re.search(r"^    biomarcadores_criterios\s*:\s*\[.*?^    \],\n", bloco, re.S | re.M)
            if not m:
                erros.append(f"{id_}: esperava biomarcadores_criterios")
                return bloco
            feitos.append(f"{id_}: + alvos {alvos}")
            return bloco[:m.end()] + f"    alvos: {js_lista(alvos)},\n" + bloco[m.end():]
        return fn

    for id_, (antes, movs) in PARA_ALVOS.items():
        trocar_bloco(id_, por_alvos(id_, antes, movs))
    for id_, regra in COM_CRITERIOS.items():
        trocar_bloco(id_, por_criterios(id_, regra))
    for id_, (alvos, _) in ALVOS_EXTRA.items():
        trocar_bloco(id_, alvos_extra(id_, alvos))
    return texto, feitos, erros


def main() -> int:
    if len(sys.argv) != 2:
        print("uso: br_migracao_alvos_2026_09.py ARQUIVO.js", file=sys.stderr)
        return 2
    alvo = Path(sys.argv[1]).resolve()
    publicado = (Path(__file__).resolve().parent.parent / "assets" / "js" / "trials_br.js").resolve()
    if alvo == publicado:
        print("recusado: aplique numa cópia, não no banco publicado", file=sys.stderr)
        return 2
    texto, feitos, erros = aplicar(alvo.read_text(encoding="utf-8"))
    for f in feitos:
        print("  ✓", f)
    for e in erros:
        print("  ✗", e, file=sys.stderr)
    if erros:
        print("nada foi gravado.", file=sys.stderr)
        return 1
    alvo.write_text(texto, encoding="utf-8")
    print(f"{len(feitos)} cards alterados → {alvo.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
