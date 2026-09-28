#!/usr/bin/env python3
"""
br_auditar.py — trial-status-auditor do Trial Matcher.

Confere TODOS os NCTs já publicados no trials_br.js contra o ClinicalTrials.gov
e responde, para cada um: o estudo ainda recruta NO BRASIL?

100% determinístico, sem IA. Não altera o trials_br.js — só relata e propõe.
Quem aplica é o br_ciclo.py, numa cópia, e quem publica é uma pessoa.

Compara em duas frentes:
  1. card publicado × registro atual — o que o site mostra está certo hoje?
  2. estado salvo na rodada anterior × registro atual — o que mudou desde então?
     (scripts/br_estado.json; na primeira rodada esta frente fica vazia)

Uso:
    python3 scripts/br_auditar.py                  # relata
    python3 scripts/br_auditar.py --json saida.json
    python3 scripts/br_auditar.py --gravar-estado  # atualiza br_estado.json e
                                                   # acrescenta br_eventos.jsonl
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import br_ctgov as ct  # noqa: E402

SCRIPTS = Path(__file__).resolve().parent
ESTADO = SCRIPTS / "br_estado.json"
EVENTOS = SCRIPTS / "br_eventos.jsonl"
SCHEMA_ESTADO = "theratrials-trials-br-estado/1"

# O CT.gov passa a exibir "Unknown status" quando o patrocinador não reverifica
# o registro por 2 anos. Antes disso já vale desconfiar: 1 ano sem verificação
# vai para revisão manual, sem proposta automática.
DIAS_VERIFICACAO_VELHA = 365


def ler_estado() -> dict:
    if not ESTADO.exists():
        return {"schema": SCHEMA_ESTADO, "estudos": {}}
    d = json.loads(ESTADO.read_text(encoding="utf-8"))
    if d.get("schema") != SCHEMA_ESTADO:
        raise SystemExit(f"{ESTADO.name}: schema {d.get('schema')!r} desconhecido")
    return d


def _dias_desde(ano_mes: str) -> int | None:
    """statusVerifiedDate vem como 'AAAA-MM' (às vezes 'AAAA-MM-DD')."""
    if not ano_mes:
        return None
    try:
        partes = [int(x) for x in ano_mes.split("-")]
        d = date(partes[0], partes[1], partes[2] if len(partes) > 2 else 1)
    except (ValueError, IndexError):
        return None
    return (date.today() - d).days


def auditar(trials: list[dict], anterior: dict) -> dict:
    """Núcleo da auditoria, importável pelo br_ciclo.py."""
    hoje = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    com_nct = [t for t in trials if (t.get("nct") or "").startswith("NCT")]
    registros = ct.buscar_por_ids([t["nct"] for t in com_nct])
    antes = anterior.get("estudos", {})

    estudos, eventos = [], []
    novo_estado = {}
    for t in com_nct:
        nct = t["nct"]
        p = registros.get(nct)
        # `revisao`: exige decisão humana antes de qualquer proposta.
        # `alertas`: vale olhar, mas não impede a proposta de status.
        linha = {"nct": nct, "id": t.get("id", ""), "nome": t.get("nome", ""),
                 "status_card": t.get("status", ""), "revisao": [], "alertas": []}
        if p is None:
            linha["brazil_status"] = ct.REVIEW_REQUIRED
            linha["revisao"].append("NCT ausente do registro (404 na consulta individual) — retirado ou renumerado?")
            estudos.append(linha)
            continue

        rb = ct.recrutamento_brasil(p)
        linha.update(rb)
        bs = rb["brazil_status"]

        # ── card × registro ────────────────────────────────────────────────
        proposto = ct.STATUS_CARD.get(bs)
        if proposto and proposto != linha["status_card"]:
            linha["status_proposto"] = proposto
        if bs == ct.REVIEW_REQUIRED:
            linha["revisao"].append(rb["motivo"] + (
                " (" + ", ".join(f"{k}×{v}" for k, v in rb["status_centros_br"].items()) + ")"
                if rb["status_centros_br"] else ""))
        dias = _dias_desde(rb["last_verified"])
        if dias is not None and dias > DIAS_VERIFICACAO_VELHA:
            linha["alertas"].append(
                f"registro não reverificado pelo patrocinador há {dias} dias "
                f"(statusVerifiedDate {rb['last_verified']})")

        locais = ct.locais_recrutando(p)
        rotulos = [ct.rotulo_centro(l) for l in locais]
        no_card = set(t.get("centros") or [])
        linha["centros_recrutando"] = rotulos
        linha["locais_recrutando"] = locais
        linha["centros_a_incluir"] = sorted(set(rotulos) - no_card)
        linha["centros_a_retirar"] = sorted(no_card - set(rotulos))

        # ── anterior × atual ───────────────────────────────────────────────
        a = antes.get(nct)
        # Última data em que se viu ≥1 centro BR RECRUITING. Vazio = nunca
        # visto desde que o histórico existe (não quer dizer "nunca recrutou").
        confirmado = hoje if bs == ct.BR_RECRUITING else (a or {}).get("br_confirmado_em", "")
        novo_estado[nct] = {
            "overall_status": rb["overall_status"],
            "brazil_status": bs,
            "last_checked": hoje,
            "last_update_posted": rb["last_update_posted"],
            "last_verified": rb["last_verified"],
            "br_confirmado_em": confirmado,
            "centros_br_recrutando": rotulos,
            "primeira_auditoria": (a or {}).get("primeira_auditoria", hoje),
        }
        if a:
            def ev(tipo, de, para):
                eventos.append({"data": hoje, "nct": nct, "tipo": tipo, "de": de, "para": para})
            for campo, tipo in (("overall_status", "overall_status"),
                                ("brazil_status", "brazil_status"),
                                ("last_update_posted", "registro_atualizado"),
                                ("last_verified", "reverificado")):
                if a.get(campo) != novo_estado[nct][campo]:
                    ev(tipo, a.get(campo), novo_estado[nct][campo])
            ant = set(a.get("centros_br_recrutando") or [])
            for c in sorted(set(rotulos) - ant):
                ev("centro_br_adicionado", None, c)
            for c in sorted(ant - set(rotulos)):
                ev("centro_br_removido", c, None)
        estudos.append(linha)

    sem_nct = [{"id": t.get("id", ""), "nome": t.get("nome", "")}
               for t in trials if not (t.get("nct") or "").startswith("NCT")]
    return {
        "gerado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "total_cards": len(trials),
        "estudos": estudos,
        "sem_nct": sem_nct,
        "eventos": eventos,
        "primeira_rodada": not antes,
        "_novo_estado": novo_estado,
    }


def gravar_estado(res: dict) -> None:
    """Estado corrente + log de eventos append-only. Só roda com --gravar-estado."""
    anterior = ler_estado()
    estudos = anterior.get("estudos", {})
    estudos.update(res["_novo_estado"])
    ESTADO.write_text(json.dumps({
        "schema": SCHEMA_ESTADO,
        "atualizado_em": res["gerado_em"],
        "estudos": dict(sorted(estudos.items())),
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    if res["eventos"]:
        with EVENTOS.open("a", encoding="utf-8") as f:
            for e in res["eventos"]:
                f.write(json.dumps(e, ensure_ascii=False) + "\n")


def resumo(res: dict) -> str:
    from collections import Counter
    e = res["estudos"]
    c = Counter(x.get("brazil_status") for x in e)
    props = [x for x in e if x.get("status_proposto")]
    linhas = [
        f"cards auditados ............ {len(e)} (de {res['total_cards']})",
        *(f"  brazil_status {k:<20s} {c.get(k, 0)}" for k in ct.BRAZIL_STATUS),
        f"status a corrigir no card .. {len(props)}",
        f"revisão manual ............. {sum(1 for x in e if x['revisao'])}",
        f"eventos desde a última ..... {len(res['eventos'])}"
        + (" (primeira rodada — sem base de comparação)" if res["primeira_rodada"] else ""),
    ]
    return "\n".join(linhas)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", metavar="ARQ", help="grava o resultado completo")
    ap.add_argument("--gravar-estado", action="store_true",
                    help="atualiza br_estado.json e acrescenta br_eventos.jsonl")
    args = ap.parse_args()

    trials, _ = ct.carregar_trials()
    res = auditar(trials, ler_estado())
    print(resumo(res))
    if args.json:
        Path(args.json).write_text(json.dumps(
            {k: v for k, v in res.items() if not k.startswith("_")},
            ensure_ascii=False, indent=1), encoding="utf-8")
    if args.gravar_estado:
        gravar_estado(res)
        print(f"estado gravado: {ESTADO.name} (+{len(res['eventos'])} eventos)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
