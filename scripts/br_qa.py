#!/usr/bin/env python3
"""
br_qa.py — trial-qa do Trial Matcher.

Compara o banco atual (assets/js/trials_br.js) com um banco PROPOSTO e roda os
validadores existentes contra o proposto, numa cópia temporária do site. O
trials_br.js real e o app-data/ real nunca são tocados.

Travas (FAIL: o proposto não pode ser aplicado):
  - não parseia, ou THERA_TRIALS_BR não é array
  - algum card existente sumiu            → remoção automática é proibida
  - id ou NCT de card existente mudou
  - id ou NCT repetido
  - THERA_TRIALS_BR_META mudou            → taxonomia só muda à mão
  - card sem campo obrigatório
  - neoplasia, linha, modalidade, fase ou status fora da META
  - biomarcadores (ver `checar_biomarcadores`):
      · token de negatividade em `biomarcadores` ('HER2-', 'EGFR wild-type'…)
      · HER2 exigido num card cujo texto diz HER2-negativo
      · `biomarcadores_criterios` malformado, contraditório ou diferente de
        `biomarcadores` (que tem de ser exatamente os `requerido`)
  - radioligante (ver `checar_radioligante`): card com modalidade
    'radioligante' sem nenhum alvo em `alvos` e sem `alvos_justificativa`
  - validador existente falhou na cópia

Avisos (WARN: aplicável, mas uma pessoa precisa olhar):
  - card existente mudou fora dos campos factuais (status, centros, cidades,
    estados, data_atualizacao) — é mudança editorial
  - card novo com biomarcador fora da lista de filtros da META
  - radioligante com alvo fora de ALVOS_RLT (a classe cresce: não bloqueia)
  - card novo com radiofármaco na intervenção e sem modalidade 'radioligante'
  - contagens do texto do site ficariam defasadas (sync_counts --check)

Uso:
    python3 scripts/br_qa.py PROPOSTO.js [--sem-rede] [--json saida.json]
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import br_ctgov as ct  # noqa: E402

SITE = ct.SITE

# Campos que a auditoria pode mudar sozinha porque vêm do registro oficial.
# Qualquer outro campo alterado num card existente é interpretação clínica.
FACTUAIS = {"status", "brazil_status", "centros", "cidades", "estados", "data_atualizacao"}
# Mudança aprovada de semântica de biomarcador (br_migracao_2026_09.py): não é
# factual, mas também não é reescrita clínica livre. Vira aviso próprio.
BIOMARCADOR = {"biomarcadores", "biomarcadores_criterios", "alvos"}

EXIGENCIAS = {"requerido", "excluido", "avaliado"}

# Negatividade dentro do próprio token: 'HER2-', 'HER2−', 'EGFR wild-type',
# 'KRAS selvagem', 'PD-L1 negativo'. Nada disso pode estar na lista de
# exigidos — é o erro que fazia o filtro HER2 devolver estudo HER2-negativo.
# 'Triplo-negativo' é fenótipo EXIGIDO (o paciente precisa ser TNBC), não
# negação de um marcador — por isso fica fora.
RE_TOKEN_NEGATIVO = re.compile(
    r"[-−]$|(?<!triplo-)(?<!triple-)(?<!triplo )(?<!triple )negativ"
    r"|wild[- ]?type|\bwt\b|selvagem|aus[eê]ncia|sem muta", re.I)

# O card diz que exige HER2-negativo? Casa 'HER2-', 'HER2−', 'HER2 negativo',
# 'HER2-negativa', 'HER2 IHQ 0', 'triplo-negativo', 'TNBC'. NÃO casa
# 'HER2-positivo', 'HER2-low', 'HER2-baixo', 'HER2-ultralow'.
RE_TEXTO_HER2_NEG = re.compile(
    r"HER2\s*[-−]\s*(?:negativ|$|[\s,;./)])|HER2\s+negativ|HER2\s+IHQ\s*0"
    r"|triplo[- ]negativ|\bTNBC\b", re.I | re.M)
RE_TEXTO_HER2_POS = re.compile(r"HER2\s*[-−]?\s*(?:positiv|\+|3\+|amplific|low|baix|ultra|expressa|muta)", re.I)


# Negação colada ao marcador ("EGFR selvagem", "EGFR-negativo", "EGFR wild-type",
# "EGFR: negativo") ou fechando uma LISTA de marcadores no plural ("KRAS, NRAS
# e BRAF selvagens", "EGFR e ALK selvagens"). "RE positivo e HER2 negativo" não
# casa para RE: entre os dois há uma palavra que não é marcador. E "c-Met e
# EGFR selvagem", no singular, só nega o EGFR.
_NEG_SING = r"(?:selvagem|wild[- ]?type|\bWT\b|sem muta\w*|n[ãa]o[- ]mutad[oa]|negativ[oa])\b"
_NEG_PLUR = r"(?:selvagens|negativ[oa]s)\b"
_MARCADOR = r"[A-Z][\w.+-]*(?:\s*\([^)]{0,20}\))?"


def _re_negado(b: str) -> re.Pattern:
    m = re.escape(b) + r"(?:\s*\([^)]{0,20}\))?"
    return re.compile(
        rf"(?<![\w-]){m}[\s:-]{{0,3}}{_NEG_SING}"
        rf"|(?<![\w-]){m}(?:\s*(?:,|/|\be\b|\band\b)\s*{_MARCADOR})*\s+(?:V600\s+)?{_NEG_PLUR}",
        re.I)


# Alvos moleculares conhecidos de radioligantes. Alvo fora daqui só gera aviso:
# a classe cresce mais rápido do que esta lista.
ALVOS_RLT = {"PSMA", "SSTR", "SSTR2", "FAP", "GRPR", "CXCR4", "NTSR1", "CA-IX",
             "DLL3", "GPC3", "MC1R", "CD20", "CD37", "CD38", "CD45", "CD66", "HER2",
             "B7-H3", "Nectin-4", "KLK2", "IGF-1R", "NET", "NIS"}


def checar_radioligante(t: dict) -> list[str]:
    """Radioligante tem de dizer o alvo, ou por que não tem (rádio-223)."""
    if "radioligante" not in (t.get("modalidade") or []):
        return []
    alvos = t.get("alvos")
    if alvos is not None and not isinstance(alvos, list):
        return ["`alvos` não é lista"]
    if not alvos and not (t.get("alvos_justificativa") or "").strip():
        return ["modalidade 'radioligante' sem alvo em `alvos` e sem `alvos_justificativa`"]
    return []


def avisos_radioligante(t: dict, novo: bool) -> list[str]:
    avisos = []
    alvos = t.get("alvos") or []
    if "radioligante" in (t.get("modalidade") or []):
        if alvos and not any(a in ALVOS_RLT for a in alvos):
            avisos.append(f"radioligante com alvo fora de ALVOS_RLT: {alvos} — conferir")
    elif novo:
        from br_discover import TERANOSTICO
        m = TERANOSTICO.search(t.get("intervencao") or "")
        if m:
            avisos.append(f"intervenção cita radiofármaco ('{m.group(0)}') e a modalidade "
                          "não tem 'radioligante' — conferir")
    return avisos


def checar_biomarcadores(t: dict) -> list[str]:
    """Regras semânticas de biomarcador. Devolve as falhas do card."""
    falhas = []
    bio = t.get("biomarcadores") or []
    for b in bio:
        if RE_TOKEN_NEGATIVO.search(b or ""):
            falhas.append(f"token de negatividade em `biomarcadores`: {b!r} — "
                          "use biomarcadores_criterios com exigencia 'excluido'")
    crit = t.get("biomarcadores_criterios")
    if crit is not None:
        if not isinstance(crit, list):
            return falhas + ["biomarcadores_criterios não é lista"]
        # Conflito requerido×excluído só conta DENTRO da mesma coorte: no
        # BREAKER-101, HER2 é exigido na coorte HER2+ e excluído na HR+/HER2−.
        vistos: dict[tuple, set] = {}
        for c in crit:
            if not isinstance(c, dict) or not (c.get("marcador") or "").strip():
                falhas.append(f"critério sem marcador: {c!r}")
                continue
            if c.get("exigencia") not in EXIGENCIAS:
                falhas.append(f"{c['marcador']}: exigencia {c.get('exigencia')!r} inválida")
                continue
            vistos.setdefault((c["marcador"], c.get("coorte") or ""), set()).add(c["exigencia"])
        for (m, co), ex in vistos.items():
            if {"requerido", "excluido"} <= ex:
                falhas.append(f"{m} ao mesmo tempo requerido e excluído" + (f" na coorte {co!r}" if co else ""))
        req: list[str] = []
        for c in crit:
            if isinstance(c, dict) and c.get("exigencia") == "requerido" and c["marcador"] not in req:
                req.append(c["marcador"])
        if req != list(bio):
            falhas.append(f"`biomarcadores` {bio} ≠ requeridos de biomarcadores_criterios {req}")
    # Generalização do caso HER2: o texto do card diz que o marcador tem de ser
    # selvagem/negativo, mas ele está na lista de EXIGIDOS. Em 2026-09 isso
    # fazia o filtro EGFR devolver estudos que excluem EGFR mutado (PACIFIC-8,
    # ARTEMIDE-Lung04…) e o filtro KRAS devolver estudos RAS-selvagem (OrigAMI).
    por_coorte_ = any((c or {}).get("coorte") for c in (crit or []) if isinstance(c, dict))
    if not por_coorte_:
        texto_card = " ".join([t.get("subtipo") or "", t.get("neoplasia_label") or ""])
        for b in bio:
            if b == "HER2" or not b:
                continue  # HER2 tem regra própria, abaixo
            if re.search(_re_negado(b), texto_card):
                falhas.append(f"{b} exigido, mas o card diz que precisa ser selvagem/negativo — "
                              f"use exigencia 'excluido'")
    alvos = t.get("alvos")
    if alvos is not None and (not isinstance(alvos, list)
                              or not all(isinstance(a, str) and a.strip() for a in alvos)):
        falhas.append(f"`alvos` precisa ser lista de nomes: {alvos!r}")
    # Texto do card diz HER2-negativo, mas HER2 está como exigido. Com
    # critérios por coorte, quem decide é o critério, não o rótulo do card.
    por_coorte = any((c or {}).get("coorte") for c in (crit or []) if isinstance(c, dict))
    if "HER2" in bio and not por_coorte:
        texto = " ".join([t.get("subtipo") or "", t.get("neoplasia_label") or ""])
        if RE_TEXTO_HER2_NEG.search(texto) and not RE_TEXTO_HER2_POS.search(texto):
            falhas.append("HER2 exigido num card HER2-negativo (subtipo/rótulo) — "
                          "HER2 deve ser 'excluido' em biomarcadores_criterios")
    return falhas


OBRIGATORIOS = [
    "id", "nome", "titulo", "nct", "fase", "status", "neoplasia", "neoplasia_label",
    "subtipo", "linha_terapeutica", "cenario_clinico", "modalidade", "biomarcadores",
    "testes_fornecidos", "intervencao", "comparador", "racional",
    "criterios_principais", "criterios_exclusao", "centros", "estados", "cidades",
    "patrocinador", "fonte_url", "contato_url", "data_atualizacao",
]

# O mínimo para o export e os três validadores rodarem na cópia.
COPIAR = ["assets/js", "assets/lang", "assets/data", "scripts", "app-data"]


def diff_meta(a: dict, b: dict) -> list[str]:
    """O que mudou na META, bloco a bloco, em linguagem legível."""
    out = []
    for k in sorted(set(a) | set(b)):
        ia = [x["id"] if isinstance(x, dict) else x for x in a.get(k, [])]
        ib = [x["id"] if isinstance(x, dict) else x for x in b.get(k, [])]
        for v in ib:
            if v not in ia:
                out.append(f"META.{k} + {v!r}")
        for v in ia:
            if v not in ib:
                out.append(f"META.{k} − {v!r}")
    return out


def comparar(atual: list[dict], meta_atual: dict,
             proposto: list[dict], meta_prop: dict, permitir_meta: bool = False,
             renomear: dict[str, str] | None = None) -> dict:
    falhas, avisos = [], []
    por_id = {t.get("id"): t for t in atual}
    # Renomeação explícita de id (ex.: id derivado de um acrônimo errado). Só
    # vale se o card mantiver o MESMO NCT — senão seria outro estudo com o id
    # de um card removido, e isso continua proibido.
    for velho, novo in (renomear or {}).items():
        antigo = por_id.get(velho)
        novo_card = next((t for t in proposto if t.get("id") == novo), None)
        if antigo is None or novo_card is None:
            falhas.append(f"renomeação {velho} → {novo}: card não encontrado")
        elif antigo.get("nct") != novo_card.get("nct"):
            falhas.append(f"renomeação {velho} → {novo}: NCT diferente ({antigo.get('nct')} ≠ {novo_card.get('nct')})")
        else:
            por_id[novo] = dict(antigo, id=novo)
            del por_id[velho]
            avisos.append(f"id renomeado: {velho} → {novo} (mesmo NCT {antigo.get('nct')})")
    prop_id = {t.get("id"): t for t in proposto}

    removidos = [i for i in por_id if i not in prop_id]
    for i in removidos:
        falhas.append(f"card removido: {i} ({por_id[i].get('nct')}) — remoção automática é proibida")

    for campo in ("id", "nct"):
        vistos: dict[str, int] = {}
        for t in proposto:
            v = t.get(campo) or ""
            vistos[v] = vistos.get(v, 0) + 1
        for v, n in vistos.items():
            if v and n > 1:
                falhas.append(f"{campo} repetido {n}×: {v}")

    if json.dumps(meta_atual, sort_keys=True) != json.dumps(meta_prop, sort_keys=True):
        mudancas = diff_meta(meta_atual, meta_prop) or ["mudança de rótulo/cor/ordem"]
        removidos_meta = [m for m in mudancas if " − " in m]
        if removidos_meta:
            # Tirar valor da taxonomia deixa cards órfãos de filtro: nunca automático.
            falhas.append("META perdeu valores: " + "; ".join(removidos_meta))
        elif permitir_meta:
            avisos.append("META mudou (aprovado com --permitir-meta): " + "; ".join(mudancas))
        else:
            falhas.append("THERA_TRIALS_BR_META mudou — taxonomia só muda à mão "
                          "(--permitir-meta se aprovado): " + "; ".join(mudancas))

    ids = {k: {x["id"] if isinstance(x, dict) else x for x in meta_prop.get(k, [])}
           for k in ("neoplasias", "linhas", "modalidades", "fases", "status", "biomarcadores")}

    alterados, novos = [], []
    for t in proposto:
        rot = f"{t.get('nome') or t.get('id')} ({t.get('nct')})"
        falta = [c for c in OBRIGATORIOS if c not in t]
        if falta:
            falhas.append(f"{rot}: sem {', '.join(falta)}")
        if t.get("neoplasia") not in ids["neoplasias"]:
            falhas.append(f"{rot}: neoplasia fora da META: {t.get('neoplasia')!r}")
        if t.get("linha_terapeutica") not in ids["linhas"]:
            falhas.append(f"{rot}: linha fora da META: {t.get('linha_terapeutica')!r}")
        if t.get("fase") not in ids["fases"]:
            falhas.append(f"{rot}: fase fora da META: {t.get('fase')!r}")
        if t.get("status") not in ids["status"]:
            falhas.append(f"{rot}: status fora da META: {t.get('status')!r}")
        for m in t.get("modalidade") or []:
            if m not in ids["modalidades"]:
                falhas.append(f"{rot}: modalidade fora da META: {m!r}")
        falhas += [f"{rot}: {f}" for f in checar_biomarcadores(t)]
        falhas += [f"{rot}: {f}" for f in checar_radioligante(t)]
        avisos += [f"{rot}: {a}" for a in avisos_radioligante(t, t.get("id") not in por_id)]
        # brazil_status (o que conta como "recrutando" no site) e `status`
        # (o rótulo) não podem se contradizer. REVIEW_REQUIRED não mexe no
        # rótulo — é o caso do ROSETTA RCC-201 —, então qualquer status vale.
        bs = t.get("brazil_status")
        if bs is not None:
            if bs not in ct.BRAZIL_STATUS:
                falhas.append(f"{rot}: brazil_status inválido: {bs!r}")
            elif bs != ct.REVIEW_REQUIRED and ct.STATUS_CARD.get(bs) != t.get("status"):
                falhas.append(f"{rot}: status {t.get('status')!r} contradiz brazil_status {bs}")

        antes = por_id.get(t.get("id"))
        if antes is None:
            novos.append(t.get("id"))
            fora = [b for b in t.get("biomarcadores") or [] if b not in ids["biomarcadores"]]
            if fora:
                avisos.append(f"{rot} (novo): biomarcador fora dos filtros da META: {fora}")
            continue
        if antes.get("nct") != t.get("nct"):
            falhas.append(f"{rot}: NCT mudou ({antes.get('nct')} → {t.get('nct')})")
        mudou = sorted(k for k in set(antes) | set(t) if antes.get(k) != t.get(k))
        if mudou:
            alterados.append({"id": t.get("id"), "campos": mudou})
            editoriais = [k for k in mudou if k not in FACTUAIS | BIOMARCADOR]
            if editoriais:
                avisos.append(f"{rot}: mudança editorial em {', '.join(editoriais)}")

    return {"falhas": falhas, "avisos": avisos, "novos": novos,
            "alterados": alterados, "removidos": removidos,
            "total_atual": len(atual), "total_proposto": len(proposto)}


def rodar(cmd: list[str], cwd: Path) -> tuple[int, str]:
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=900)
    return r.returncode, (r.stdout + r.stderr).strip()


def validar_copia(proposto_js: Path, rede: bool) -> list[dict]:
    """Roda os validadores existentes numa cópia do site com o banco proposto."""
    resultados = []
    with tempfile.TemporaryDirectory(prefix="br_qa_") as tmp:
        raiz = Path(tmp)
        for rel in COPIAR:
            shutil.copytree(SITE / rel, raiz / rel,
                            ignore=shutil.ignore_patterns("node_modules", "_br_*"))
        for html in SITE.glob("*.html"):
            shutil.copy2(html, raiz / html.name)
        shutil.copy2(SITE / "manifest.json", raiz / "manifest.json")
        shutil.copy2(proposto_js, raiz / "assets" / "js" / "trials_br.js")

        # Sincroniza os números do texto NA CÓPIA com o banco proposto: a saída
        # mostra como a home ficará. Só bloqueia se violar uma trava do
        # sync_counts (frase proibida, vitrine com card não recrutando).
        etapas = [
            ("contagens do texto do site (sincronizadas na cópia)",
             ["node", "scripts/sync_counts.mjs"], True),
            ("export do app-data", ["node", "scripts/export_app_data.mjs"], True),
            ("validação do app-data", ["node", "scripts/validate_app_data.mjs"], True),
        ]
        if rede:
            etapas.append(("links e status no CT.gov",
                           ["node", "scripts/validate_trials_br.mjs"], True))
        for nome, cmd, bloqueia in etapas:
            rc, saida = rodar(cmd, raiz)
            resultados.append({"etapa": nome, "ok": rc == 0, "bloqueia": bloqueia,
                               "saida": saida[-6000:]})
    return resultados


def executar(proposto_js: Path, rede: bool, permitir_meta: bool = False,
             renomear: dict[str, str] | None = None) -> dict:
    atual, meta = ct.carregar_trials()
    try:
        prop, meta_p = ct.carregar_trials(proposto_js)
    except SystemExit as e:
        return {"ok": False, "falhas": [f"proposto não parseia: {e}"], "avisos": [],
                "validadores": []}
    res = comparar(atual, meta, prop, meta_p, permitir_meta, renomear)
    res["validadores"] = validar_copia(proposto_js, rede) if not res["falhas"] else []
    for v in res["validadores"]:
        if not v["ok"]:
            (res["falhas"] if v["bloqueia"] else res["avisos"]).append(
                f"{v['etapa']}: " + ("falhou" if v["bloqueia"] else "ficaria defasado"))
    res["ok"] = not res["falhas"]
    return res


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("proposto", type=Path)
    ap.add_argument("--sem-rede", action="store_true",
                    help="pula o validate_trials_br (que consulta o CT.gov)")
    ap.add_argument("--json", metavar="ARQ")
    ap.add_argument("--permitir-meta", action="store_true",
                    help="aceita META com valores ACRESCENTADOS (aprovação humana)")
    ap.add_argument("--renomear", action="append", default=[], metavar="VELHO=NOVO",
                    help="renomeação aprovada de id de card (mesmo NCT); pode repetir")
    args = ap.parse_args()

    ren = dict(r.split("=", 1) for r in args.renomear)
    res = executar(args.proposto, rede=not args.sem_rede, permitir_meta=args.permitir_meta, renomear=ren)
    print(f"QA: {'OK' if res['ok'] else 'BLOQUEADO'} — "
          f"{res.get('total_atual', '?')} → {res.get('total_proposto', '?')} cards, "
          f"{len(res.get('novos', []))} novos, {len(res.get('alterados', []))} alterados")
    for f in res["falhas"]:
        print(f"  FAIL  {f}")
    for a in res["avisos"]:
        print(f"  WARN  {a}")
    for v in res.get("validadores", []):
        print(f"  {'ok  ' if v['ok'] else 'erro'}  {v['etapa']}")
    if args.json:
        Path(args.json).write_text(json.dumps(res, ensure_ascii=False, indent=1),
                                   encoding="utf-8")
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
