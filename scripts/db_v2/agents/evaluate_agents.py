"""evaluate_agents — mede o curator/verifier contra o golden set e resume o corpus real (modo sombra).

    python3 scripts/db_v2/agents/evaluate_agents.py      # grava state/evaluation.json e state/evaluation.md

Dimensões medidas SEPARADAMENTE (nunca um escore único): identidade, relação da publicação, assinatura (braços),
extração clínica esperada, atribuição de braço, α declarado, conflitos não resolvidos, reported × derived, proveniência
completa, concordância do verifier, falsos positivos (incl. "atualização" indevida), falsos negativos, decisão humana
respeitada, quarentena. As expectativas vêm do golden_set.json (dados), nunca de regra por estudo.
"""
from __future__ import annotations

import collections
import json
import pathlib
import re
import sys

AQUI = pathlib.Path(__file__).resolve().parent
try:
    from . import corpus as CO, curator as C, decision_packet as D, sources as S, verifier as V
except ImportError:
    import corpus as CO
    import curator as C
    import decision_packet as D
    import sources as S
    import verifier as V

SAIDA_J = S.STATE / "evaluation.json"
SAIDA_M = S.STATE / "evaluation.md"
FORTES = ("confirmed", "pilot_verified")


def _txt(it: dict) -> str:
    partes = [str(it.get("proposed_value") or "")]
    for c in (it.get("conflict") or {}).get("candidates") or []:
        partes.append(str(c.get("value")))
    return " ".join(partes)


def casa(it: dict, exp: dict, veredito: str | None) -> bool:
    if it.get("field") not in exp["fields"]:
        return False
    t = _txt(it).lower()
    if exp.get("expect_verdict") == "CONFLICT":
        return bool(it.get("conflict")) or veredito == "CONFLICT"
    if exp.get("types") and it.get("proposal_type") not in exp["types"]:
        return False
    for grupo in exp.get("include_any") or []:
        if not any(g.lower() in t for g in grupo):
            return False
    for x in exp.get("exclude") or []:
        if re.search(rf"\b{re.escape(x.lower())}\b", t):
            return False
    return True


def papel_do_numero(texto: str, numero: str, papeis: dict) -> str | None:
    """Papel (experimental/control) do rótulo de braço mais próximo ANTES da ocorrência do número."""
    t = texto.lower()
    for forma in {numero, numero.replace(".", ",")}:
        i = t.find(forma)
        if i >= 0:
            melhor, pos = None, -1
            for papel, rotulos in papeis.items():
                for r in rotulos:
                    j = t.rfind(r.lower(), 0, i)
                    if j > pos:
                        melhor, pos = papel, j
            return melhor
    return None


def carregar(uid: str):
    pk = C.pacote(uid) if (S.STATE / "packets" / uid / "packet.json").exists() else None
    prop = V.proposta(uid) if (C.CURADOR / f"{uid}.json").exists() else None
    ver = json.loads((V.VERIF / f"{uid}.json").read_text()) if (V.VERIF / f"{uid}.json").exists() else None
    dp = json.loads((D.PACOTES / f"{uid}.json").read_text()) if (D.PACOTES / f"{uid}.json").exists() else None
    return pk, prop, ver, dp


PRIO_DO_TIPO = {"INTEGRITY_FIX": "P0", "BIBLIOGRAPHIC_FIX": "P3", "EDITORIAL_ONLY": "P3", "LONG_TERM_FOLLOWUP": "P1",
                "SAME_ANALYSIS_UPDATE": "P1", "NEW_PUBLICATION_RELATIONSHIP": "P2", "SECONDARY_ANALYSIS": "P2"}


def _prio_esperadas(e: dict) -> set:
    try:
        from . import sufficiency as SF
    except ImportError:
        import sufficiency as SF
    ps = {PRIO_DO_TIPO.get(t, "P2") for t in e.get("types") or []}
    if "INTEGRITY_FIX" in (e.get("types") or []) and not set(e["fields"]) & SF.CAMPOS_CLINICOS:
        ps.add("P3")                                   # campo não clínico: integridade sem identidade é P3
    if e.get("expect_verdict") == "CONFLICT":
        ps = {"P0"} if set(e["fields"]) & SF.CAMPOS_CLINICOS else {"P2"}
    return ps


def avaliar_modo(modo: str) -> dict:
    """modo = 'production_assisted' (uid) | 'blind_discovery' (uid__cego). Métricas NUNCA misturadas."""
    g = CO.golden()["casos"]
    linhas, tot = {}, collections.Counter()
    for base, caso in g.items():
        uid = base if modo == "production_assisted" else f"{base}__cego"
        pk, prop, ver, dp = carregar(uid)
        itens = (prop or {}).get("proposals") or []
        vered = {r["proposal_id"]: r["verdict"] for r in (ver or {}).get("results") or []}
        prio = {f["proposal_id"]: f["final_priority"] for f in (dp or {}).get("fields", []) + (dp or {}).get("dropped_fail", [])}
        r = {"estudo": caso["estudo"], "processado_llm": prop is not None}
        r["identity_ok"] = bool(pk) and pk["identity"]["pmid"] == caso["identity"]["pmid"] and \
            pk["identity"]["nct"] == caso["identity"]["nct"]
        r["withheld_ok"] = (not caso["withheld"]) or (bool(pk) and pk["withheld"] and not itens and
                                                    (dp or {}).get("suggested_decision") in (None, "NONE"))
        rel = ((prop or {}).get("represented_publication") or {}).get("relation_to_primary")
        r["relation"], r["relation_ok"] = rel, (not caso["represented_relation"]) or (rel in caso["represented_relation"])
        if caso.get("arm_roles"):
            arms = [a for sg in (prop or {}).get("analysis_signatures") or [] for a in sg.get("arms") or []]
            r["arm_roles_ok"] = all(any(a.get("role") == papel and any(t.lower() in (a.get("label") or "").lower()
                                                                          for t in toks) for a in arms)
                                    for papel, toks in caso["arm_roles"].items())
        esperados = []
        backstop = [{"proposal_id": f["proposal_id"], "field": f["field"], "origin": "backstop",
                     "proposal_type": "WATCH", "proposed_value": None}
                    for f in (dp or {}).get("fields", []) if f.get("origin") == "backstop"]
        itens = itens + backstop
        vered.update({b["proposal_id"]: "UNSUPPORTED" for b in backstop})
        for e in caso["expected"]:
            no_campo = [it for it in itens if it.get("field") in e["fields"]]
            sinalizados = [it for it in no_campo if prio.get(it["proposal_id"]) is not None]   # FAIL não conta
            corretos = [it for it in sinalizados if casa(it, e, vered.get(it["proposal_id"]))
                        and prio.get(it["proposal_id"]) in _prio_esperadas(e)]
            resolvido = e.get("must_not_resolve") and any(
                it.get("proposed_value") not in (None, "") and not it.get("conflict")
                and vered.get(it["proposal_id"]) == "PASS" for it in no_campo)
            atrib = None
            if e.get("arm_attribution") and corretos and caso.get("arm_roles"):
                atrib = all(papel_do_numero(_txt(corretos[0]), n, caso["arm_roles"]) == p
                            for n, p in e["arm_attribution"].items())
            esperados.append({"basis": e["basis"], "strength": e["strength"], "flagged": bool(sinalizados),
                              "correct": bool(corretos), "via": sorted({it.get("origin", "curator") for it in sinalizados}),
                              "priorities": sorted({prio.get(it["proposal_id"]) or "-" for it in sinalizados}),
                              "verdicts": sorted({vered.get(it["proposal_id"]) for it in sinalizados}),
                              "resolved_conflict_wrongly": bool(resolvido), "arm_attribution_ok": atrib})
        r["expected"] = esperados
        for hp in (caso.get("human_decision_protected") or []) if modo == "production_assisted" else []:
            # no modo cego o pacote não tem decisões humanas: a métrica não se aplica (N/A), não é falha
            toca = [it for it in itens if it["field"] in hp["fields"]]
            r["human_decision_respected"] = (not toca) or (
                (dp or {}).get("suggested_decision") == hp["expected_packet_decision"]
                and all(prio.get(it["proposal_id"]) not in ("P0", "P1") for it in toca))
        casados = {it["proposal_id"] for e in caso["expected"] for it in itens if it.get("field") in e["fields"]}
        r["unmatched"] = [{"proposal_id": it["proposal_id"], "field": it["field"], "origin": it.get("origin"),
                           "verdict": vered.get(it["proposal_id"]), "priority": prio.get(it["proposal_id"])}
                          for it in itens if it["proposal_id"] not in casados]
        r["false_update"] = sum(1 for it in itens if it.get("proposal_type") in ("SAME_ANALYSIS_UPDATE", "LONG_TERM_FOLLOWUP")
                                and set(caso["represented_relation"]) <= {"SAME_ANALYSIS"} and it.get("origin") != "deterministic"
                                and vered.get(it["proposal_id"]) == "PASS" and it.get("field") in ("primario", "resultado_chave")
                                and not it.get("_update_ok"))
        linhas[base] = r
        for e in esperados:
            k = "forte" if e["strength"] in FORTES else "candidato"
            tot[f"{k}_total"] += 1
            tot[f"{k}_sinalizado"] += e["flagged"]
            tot[f"{k}_correto"] += e["correct"]
            tot["conflito_resolvido_indevidamente"] += e["resolved_conflict_wrongly"]
        tot["todos_total"] = tot["forte_total"] + tot["candidato_total"]
        tot["todos_sinalizado"] = tot["forte_sinalizado"] + tot["candidato_sinalizado"]
        tot["todos_correto"] = tot["forte_correto"] + tot["candidato_correto"]
        tot["falsa_atualizacao"] += r["false_update"]
        tot["identidade_ok"] += r["identity_ok"]
        tot["relacao_ok"] += r["relation_ok"]
        tot["withheld_ok"] += r["withheld_ok"]
        if modo == "production_assisted":
            tot["decisao_humana_respeitada"] += r.get("human_decision_respected", True)
    return {"casos": linhas, "totais": dict(tot)}


def proveniencia(it: dict) -> bool:
    if it.get("conflict") or it.get("absence_checked_in"):
        return True
    ev = it.get("evidence") or []
    ok = bool(ev) and all(all(e.get(k) for k in ("source_id", "source_type", "locator", "snippet", "retrieved_at"))
                          for e in ev)
    if it.get("value_origin") == "derived":
        ok = ok and bool(it.get("derivation"))
    return ok and bool(it.get("value_origin"))


def avaliar_corpus() -> dict:
    co = CO.corpus()
    uids = list(co["cards"])
    m = collections.Counter()
    por_campo = collections.defaultdict(collections.Counter)
    diverg = []
    for uid in uids:
        pk, prop, ver, dp = carregar(uid)
        m["cards_estagio0"] += pk is not None
        if pk and pk["withheld"]:
            m["cards_withheld_deterministico"] += 1
        if prop is None:
            continue
        m["cards_llm"] += 1
        itens = prop.get("proposals") or []
        m["propostas"] += len(itens)
        m["proveniencia_completa"] += sum(proveniencia(it) for it in itens)
        res = {r["proposal_id"]: r for r in (ver or {}).get("results") or []}
        for it in itens:
            r = res.get(it["proposal_id"], {"verdict": "UNSUPPORTED"})
            m[r["verdict"]] += 1
            por_campo[it["field"]][r["verdict"]] += 1
            if r.get("divergence"):
                diverg.append({"uid": uid, "field": it["field"], "deterministic": r["deterministic"]["verdict"],
                               "semantic": r["semantic"]["verdict"]})
            if it.get("_precheck_verdict") == "PASS" and r["verdict"] != "PASS":
                m["curator_precheck_PASS_mas_verifier_nao"] += 1
            if it.get("value_origin") == "derived":
                m["derived"] += 1
        vs = [res.get(it["proposal_id"], {}).get("verdict") for it in itens]
        if itens and all(v == "PASS" for v in vs):
            m["cards_totalmente_verificados"] += 1
        elif any(v == "PASS" for v in vs):
            m["cards_parcialmente_verificados"] += 1
        elif itens:
            m["cards_sem_item_verificado"] += 1
        else:
            m["cards_sem_proposta"] += 1
        if dp and dp["human_required"]:
            m["cards_exigem_humano"] += 1
            m[f"sugestao_{dp['suggested_decision']}"] += 1
            m["pacotes_no_orcamento"] += dp["counts_toward_weekly_budget"]
    piores = sorted(((f, c) for f, c in por_campo.items() if sum(c.values()) >= 2),
                    key=lambda fc: -(sum(fc[1].values()) - fc[1]["PASS"]) / sum(fc[1].values()))[:8]
    return {"metricas": dict(m), "divergencias_det_x_semantico": diverg,
            "campos_mais_falhos": [{"field": f, **dict(c), "taxa_nao_PASS": round(
                (sum(c.values()) - c["PASS"]) / sum(c.values()), 2)} for f, c in piores],
            "composicao": {k: len(v) for k, v in co.items() if isinstance(v, (list, dict))}}


def main() -> int:
    D.todos(sorted(p.parent.name for p in (S.STATE / "packets").glob("*/packet.json")))
    out = {"production_assisted": avaliar_modo("production_assisted"), "blind_discovery": avaliar_modo("blind_discovery"),
           "corpus": avaliar_corpus()}
    SAIDA_J.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"production_assisted": out["production_assisted"]["totais"],
                      "blind_discovery": out["blind_discovery"]["totais"], "corpus": out["corpus"]["metricas"]},
                     ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
