"""decision_packet — UM pacote de revisão humana por card, e a fila priorizada.

    python3 scripts/db_v2/agents/decision_packet.py          # grava state/decision_packets/*.json e state/human_queue.json

A unidade de revisão é o card: todos os campos, conflitos, fontes e vereditos num pacote só. O sistema SUGERE
APPROVE / REJECT / DEFER; `final_decision` fica sempre null (só humano preenche, fora deste pacote).

Regras da sugestão (nesta ordem):
  quarentena                              → NONE (sem pacote clínico; a quarentena é decisão humana própria)
  sem proposta                            → NONE
  só itens encaminhados, sem valor novo   → WATCH (nada a aprovar ou rejeitar)
  item P0 sem consenso de 2 verifiers      → DEFER + auto_approval_blocked (DISAGREEMENT ou SINGLE_RUN)
  item em campo protegido por decisão humana → DEFER
  algum CONFLICT                          → DEFER (adjudicação de fontes é humana; o sistema não escolhe)
  todos PASS                              → APPROVE
  nenhum PASS                             → REJECT
  misto                                   → DEFER (lista quais itens passariam)
Orçamento semanal: conta todo pacote humano, EXCETO P3 cujos itens são todos PASS determinístico (resolvível sem
revisão clínica — ex.: ano_pub = ano da publicação representada).
"""
from __future__ import annotations

import collections
import json
import pathlib
import sys

AQUI = pathlib.Path(__file__).resolve().parent
try:
    from . import agent_types as T, curator as C, priority as PR, sources as S, verifier as V
except ImportError:
    import agent_types as T
    import curator as C
    import priority as PR
    import sources as S
    import verifier as V

PACOTES = S.STATE / "decision_packets"
FILA = S.STATE / "human_queue.json"
ORDEM_P = {"P0": 0, "P1": 1, "P2": 2, "P3": 3, None: 9}
IMPACTO = {"none": 0, "low": 1, "moderate": 2, "high": 3}


def montar(uid: str) -> dict:
    pk = C.pacote(uid)
    prop = V.proposta(uid) if (C.CURADOR / f"{uid}.json").exists() else None
    ver = json.loads((V.VERIF / f"{uid}.json").read_text()) if (V.VERIF / f"{uid}.json").exists() else None
    itens = (prop or {}).get("proposals") or []
    vered = {r["proposal_id"]: r for r in (ver or {}).get("results") or []}
    protegidos = set(pk.get("human_decision_protected_fields") or [])
    campos, conflitos, fontes = [], [], set()
    for it in itens:
        r = vered.get(it["proposal_id"], {"verdict": "UNSUPPORTED"})
        prio, prio_motivo = PR.classificar(it, r["verdict"], r.get("current_value_status"), pk)
        campos.append({"final_priority": prio, "priority_reason": prio_motivo, "origin": it.get("origin", "curator"),
                       "defect": it.get("defect"), "current_value_status": r.get("current_value_status"),"proposal_id": it["proposal_id"], "field": it["field"], "current": it.get("current_value"),
                       "proposed": it.get("proposed_value"), "change_kind": it.get("change_kind"),
                       "value_origin": it.get("value_origin"), "proposal_type": it.get("proposal_type"),
                       "curator_priority": it.get("_curator_priority"), "verdict": r["verdict"],
                       "verifier_reason": (r.get("semantic") or {}).get("reason"),
                       "deterministic": (r.get("deterministic") or {}).get("verdict"),
                       "human_decision_protected": it["field"] in protegidos,
                       "evidence": [{k: e.get(k) for k in ("source_id", "locator", "snippet")}
                                    for e in it.get("evidence") or []]})
        fontes |= {e.get("source_id") for e in it.get("evidence") or []}
        if r["verdict"] == "CONFLICT" or it.get("conflict"):
            conflitos.append({"field": it["field"], "description": (it.get("conflict") or {}).get("description")
                              or (r.get("semantic") or {}).get("reason")})
    # verifier duplo: todo item P0 do curator precisa de duas verificações independentes concordantes. Divergência
    # (ou segunda execução ausente) é incerteza de VERIFICAÇÃO: a prioridade clínica fica (nunca desce), o item exige
    # revisão humana e o card não pode ser aprovado automaticamente.
    cons = (ver or {}).get("consensus") or {}
    por_id = {it["proposal_id"]: it for it in itens}
    for c in campos:
        if c["final_priority"] != "P0" or c["origin"] != "curator":
            continue
        k = cons.get(c["proposal_id"])
        c["verifier_consensus"] = k["state"] if k else "SINGLE_RUN"
        c["run_a"], c["run_b"] = (k or {}).get("run_a") or {"verdict": c["verdict"]}, (k or {}).get("run_b")
        if c["run_b"]:
            pb, _ = PR.classificar(por_id[c["proposal_id"]], c["run_b"]["verdict"],
                                   c["run_b"].get("current_value_status"), pk)
            c["priority_run_b"] = pb                     # só informativo: a final é a mais grave das duas
            c["final_priority"] = min([c["final_priority"], pb or "P0"], key=lambda x: ORDEM_P[x])
        c["human_review_required"] = c["verifier_consensus"] in ("DISAGREEMENT", "SINGLE_RUN")
    # campo-resumo dependente: só fica se alguma atualização que o motivou passou no verifier
    for c in campos:
        dep = (por_id.get(c["proposal_id"]) or {}).get("_depends_on")
        if dep and not any((vered.get(d) or {}).get("verdict") == "PASS" for d in dep):
            c["final_priority"], c["priority_reason"] = None, "atualização que motivou a revisão não passou no verifier"
    campos_todos = campos
    campos = [c for c in campos if c["final_priority"]]             # FAIL sai da fila (log de qualidade)
    # backstop "silêncio não é resultado": item aberto/confirmado do backlog sem NENHUM item sobrevivente nos seus
    # campos (o curator não tratou, ou o único item caiu por FAIL) é encaminhado explicitamente, como WATCH (P2)
    if not pk["withheld"]:
        vivos = {c["field"] for c in campos}
        for b in pk.get("backlog") or []:
            af = b.get("affected_fields") or []
            if b.get("status") in ("open", "confirmed") and af and not set(af) & vivos:
                campos.append({"final_priority": "P2", "priority_reason": f"backlog {b['id']} sem item sobrevivente: "
                               "encaminhado", "origin": "backstop", "defect": None, "current_value_status": None,
                               "proposal_id": f"B:{b['id']}", "field": af[0], "current": pk["card"].get(af[0]),
                               "proposed": None, "change_kind": "none", "value_origin": None, "proposal_type": "WATCH",
                               "curator_priority": None, "verdict": "UNSUPPORTED",
                               "verifier_reason": (b.get("description") or "")[:200], "deterministic": None,
                               "human_decision_protected": af[0] in protegidos, "evidence": []})
                vivos |= set(af)
    # backlog aberto de prioridade high: nenhum item nos seus campos fica abaixo de P1
    altos = {f for b in pk.get("backlog") or [] if b.get("status") in ("open", "confirmed")
             and b.get("priority") == "high" for f in b.get("affected_fields") or []}
    for c in campos:
        if c["field"] in altos and ORDEM_P[c["final_priority"]] > ORDEM_P["P1"]:
            c["final_priority"], c["priority_reason"] = "P1", f"backlog aberto high no campo (piso P1); antes: {c['priority_reason']}"
    contagem = collections.Counter(c["verdict"] for c in campos)
    prioridade = PR.do_card([c["final_priority"] for c in campos])
    tipo = ((prop or {}).get("card_classification") or {}).get("proposal_type") or "NO_ACTION"
    # confiança por domínio — nunca um escore único
    bib = pk["bibliographic"]
    rel = ((ver or {}).get("relationship") or {}).get("verdict")
    dominio = {
        "identity": pk["identity"]["status"],
        "bibliographic_metadata": ("machine_verified" if bib["has_structured_citation"] else
                                   "blocked_by_backlog" if bib["eligibility"].startswith("backlog") else
                                   "not_applicable" if bib["eligibility"] in ("sem_pmid", "quarentena_editorial") else
                                   "unverified"),
        "publication_relationship": ("human_decision" if pk["publication_relationship"]["status"] == "human_decision"
                                     else {"PASS": "verified", "CONFLICT": "conflict"}.get(rel, "undetermined")),
        "clinical_extraction": ("withheld" if pk["withheld"] else "not_applicable" if not campos else
                                "verifier_pass" if contagem["PASS"] == len(campos) else
                                "verifier_fail" if not contagem["PASS"] else "verifier_partial"),
        "published_write": "human_required",
    }
    bloqueio = any(c.get("human_review_required") for c in campos)
    if pk["withheld"]:
        sug, motivo = "NONE", "card em quarentena (withheld_due_to_integrity): nenhuma proposta clínica"
    elif not campos:
        sug, motivo = "NONE", "curator não propôs mudança"
    elif all(c["proposed"] is None and not c.get("conflict") and c["verdict"] != "CONFLICT" for c in campos):
        sug, motivo = "WATCH", "nenhuma alteração proposta: só itens encaminhados para acompanhamento (backlog/regra)"
    elif bloqueio:
        sug, motivo = "DEFER", ("verificação P0 sem consenso: " + ", ".join(
            f"{c['field']} ({c['verifier_consensus']}: {(c.get('run_a') or {}).get('verdict')} × "
            f"{(c.get('run_b') or {}).get('verdict')})" for c in campos if c.get("human_review_required"))
            + "; revisão humana obrigatória, sem aprovação automática")
    elif any(c["human_decision_protected"] for c in campos):
        sug, motivo = "DEFER", "proposta toca campo definido por decisão humana registrada; exige nova decisão"
    elif contagem["CONFLICT"]:
        sug, motivo = "DEFER", f"{contagem['CONFLICT']} item(ns) em CONFLICT: fontes divergem, adjudicação humana"
    elif contagem["PASS"] == len(campos):
        sug, motivo = "APPROVE", "todos os itens PASS no verifier"
    elif not contagem["PASS"]:
        sug, motivo = "REJECT", "nenhum item verificado (FAIL/UNSUPPORTED)"
    else:
        ok = [c["field"] for c in campos if c["verdict"] == "PASS"]
        sug, motivo = "DEFER", f"parcial: {len(ok)} de {len(campos)} itens PASS ({', '.join(ok)}); o resto não verificou"
    humano = sug != "NONE"
    no_orcamento = humano and prioridade in PR.ORCAMENTO             # só P0/P1 consomem o orçamento semanal
    impacto = max((it.get("editorial_impact") or "none" for it in itens), key=lambda x: IMPACTO.get(x, 0),
                  default="none")
    return {
        "schema": f"theratrials-db-decision-packet/{T.VERSAO}", "uid": uid, "card": (pk["card"].get("estudo") or uid),
        "priority": prioridade, "proposal_type": tipo,
        "summary": ((prop or {}).get("card_classification") or {}).get("summary") or "",
        "fields": campos, "dropped_fail": [c for c in campos_todos if not c["final_priority"]], "conflicts": conflitos, "sources": sorted(x for x in fontes if x),
        "clinical_impact": impacto,
        "verifier_summary": {v: contagem.get(v, 0) for v in T.VERDICTS},
        "domain_confidence": dominio, "suggested_decision": sug, "suggested_reason": motivo,
        "human_required": humano, "counts_toward_weekly_budget": no_orcamento,
        "verifier_consensus": {c["proposal_id"]: c["verifier_consensus"] for c in campos if "verifier_consensus" in c},
        "auto_approval_blocked": bloqueio,
        "final_decision": None,
        "deterministic_findings": pk["deterministic_findings"],
    }


def candidatos_p0(uid: str) -> list[str]:
    """Itens do curator com prioridade final P0 após a primeira verificação: vão à segunda execução."""
    return [c["proposal_id"] for c in montar(uid)["fields"] if c["final_priority"] == "P0" and c["origin"] == "curator"]


def todos(uids: list[str]) -> list[dict]:
    PACOTES.mkdir(parents=True, exist_ok=True)
    out = []
    for u in uids:
        p = montar(u)
        (PACOTES / f"{u}.json").write_text(json.dumps(p, ensure_ascii=False, indent=1), encoding="utf-8")
        out.append(p)
    fila = sorted((p for p in out if p["human_required"]), key=lambda p: (ORDEM_P[p["priority"]], p["uid"]))
    FILA.write_text(json.dumps([{k: p[k] for k in ("uid", "card", "priority", "proposal_type", "suggested_decision",
                                                     "suggested_reason", "counts_toward_weekly_budget")} for p in fila],
                               ensure_ascii=False, indent=1), encoding="utf-8")
    return out


if __name__ == "__main__":
    uids = sorted(p.parent.name for p in (S.STATE / "packets").glob("*/packet.json"))
    r = todos(uids)
    print(json.dumps(collections.Counter(p["suggested_decision"] for p in r), ensure_ascii=False))
    sys.exit(0)
