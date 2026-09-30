"""verifier — entrada do database-verifier (LLM), checagem determinística independente e fusão dos vereditos.

    python3 scripts/db_v2/agents/verifier.py entrada <uid>             # grava state/tasks/<uid>.verifier_input.json
    python3 scripts/db_v2/agents/verifier.py ingerir <uid> <arquivo>   # valida e grava state/verifier/<uid>.json
    python3 scripts/db_v2/agents/verifier.py ingerir_b <uid> <arquivo> # 2ª execução (itens P0): grava o consenso

Independência: o verifier recebe só os campos estruturados de cada item (agent_types.VERIFIER_VISIBLE) — nunca
`reason`, `confidence`, `editorial_impact`, resumo, notas ou a pré-checagem do curator. As checagens determinísticas
são refeitas aqui, lendo as fontes do disco.

Fusão: veredito final = o PIOR entre o determinístico e o semântico (FAIL > CONFLICT > UNSUPPORTED > PASS). O LLM
pode rebaixar um PASS determinístico, nunca promover um FAIL. Item que o verifier não avaliou = UNSUPPORTED.
O verifier nunca corrige: resultado com valor corrigido é rejeitado (E_VERIFIER_REWRITE) e o item fica UNSUPPORTED.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import pathlib
import sys

AQUI = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
import v2lib as L  # noqa: E402

try:
    from . import agent_types as T, checks as K, curator as C, sources as S, sufficiency as SF
except ImportError:
    import agent_types as T
    import checks as K
    import curator as C
    import sources as S
    import sufficiency as SF

VERIF = S.STATE / "verifier"
TAREFAS = S.STATE / "tasks"
CAMPOS_PROIBIDOS_NO_RESULTADO = {"corrected_value", "proposed_value", "new_value", "fixed_value", "suggested_value"}


def proposta(uid: str) -> dict:
    return json.loads((C.CURADOR / f"{uid}.json").read_text(encoding="utf-8"))


def sha_proposta(prop: dict) -> str:
    limpa = {k: v for k, v in prop.items() if not k.startswith("_")}
    limpa["proposals"] = [{k: v for k, v in it.items() if not k.startswith("_")} for it in prop.get("proposals") or []]
    return hashlib.sha256(json.dumps(limpa, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def entrada(uid: str, so_ids: list[str] | None = None, sufixo: str = "") -> dict:
    """O que o verifier vê: itens estruturados + assinaturas + alegação de relação. Nada do raciocínio do curator.
    so_ids/sufixo: entrada da SEGUNDA execução (só itens P0), num arquivo próprio que não cita a primeira."""
    prop = proposta(uid)
    rp = prop.get("represented_publication") or {}
    vis = {
        "uid": uid, "proposal_sha256": sha_proposta(prop),
        "packet": str(S.STATE / "packets" / uid / "packet.json"),
        "fontes": str(S.STATE / "packets" / uid / "fontes"),
        "represented_publication_claim": {k: rp.get(k) for k in ("publication_id", "relation_to_primary",
                                                                "primary_publication_id", "basis_evidence")},
        "analysis_signatures": prop.get("analysis_signatures") or [],
        "items": [{k: it.get(k) for k in T.VERIFIER_VISIBLE if k in it} for it in prop.get("proposals") or []
                  if it.get("origin") != "deterministic" and (so_ids is None or it["proposal_id"] in so_ids)],
    }                                                           # itens determinísticos não vão ao LLM
    TAREFAS.mkdir(parents=True, exist_ok=True)
    (TAREFAS / f"{uid}.verifier_input{sufixo}.json").write_text(json.dumps(vis, ensure_ascii=False, indent=1),
                                                                 encoding="utf-8")
    return vis


def consenso(va: str, vb: str | None) -> str:
    if vb is None:
        return "SINGLE_RUN"
    return f"UNANIMOUS_{va}" if va == vb else "DISAGREEMENT"


def ingerir_segundo(uid: str, texto: str, ids: list[str]) -> dict:
    """Funde a SEGUNDA execução (independente) só para os itens P0 e grava o consenso ao lado da primeira.
    A primeira fusão não é alterada: a divergência é registrada, nunca resolvida por máquina."""
    prop = proposta(uid)
    atual = json.loads((VERIF / f"{uid}.json").read_text(encoding="utf-8"))
    llm = C.extrair_json(texto) if texto else None
    b = fundir(prop, llm, deterministico(uid), C.fontes_do_pacote(C.pacote(uid)))
    ra = {r["proposal_id"]: r for r in atual["results"]}
    rb = {r["proposal_id"]: r for r in b["results"] if r["proposal_id"] in ids}
    resumo = lambda r: {k: (r.get(k) if k != "reason" else (r.get("semantic") or {}).get("reason"))  # noqa: E731
                        for k in ("verdict", "current_value_status", "support", "component", "reason")}
    atual["consensus"] = {pid: {"state": consenso(ra[pid]["verdict"], (rb.get(pid) or {}).get("verdict")),
                                "run_a": resumo(ra[pid]), "run_b": resumo(rb[pid]) if pid in rb else None}
                          for pid in ids if pid in ra}
    atual["_ingestao"]["avisos_run_b"] = b["_ingestao"]["avisos"]
    (VERIF / f"{uid}.json").write_text(json.dumps(atual, ensure_ascii=False, indent=1), encoding="utf-8")
    return atual


def deterministico(uid: str) -> dict[str, list[dict]]:
    pk = C.pacote(uid)
    fontes = C.fontes_do_pacote(pk)
    pasta = S.STATE / "packets" / uid
    return {it["proposal_id"]: K.conferir_item(it, fontes, pasta) for it in proposta(uid).get("proposals") or []}


def fundir(prop: dict, llm: dict | None, det: dict[str, list[dict]], fontes: dict | None = None) -> dict:
    avisos = []
    por_id = {}
    if llm is not None:
        for e in L.validar_schema(llm, T.VERIFICATION_SCHEMA):
            avisos.append(f"schema: {e}")
        if llm.get("proposal_sha256") != sha_proposta(prop):
            avisos.append("proposal_sha256 diferente: verificação de outra versão da proposta")
        for r in llm.get("results") or []:
            if CAMPOS_PROIBIDOS_NO_RESULTADO & set(r):
                avisos.append(f"E_VERIFIER_REWRITE em {r.get('proposal_id')}: verifier tentou corrigir o valor")
                r = {**{k: v for k, v in r.items() if k not in CAMPOS_PROIBIDOS_NO_RESULTADO},
                     "verdict": "UNSUPPORTED", "reason": "verifier tentou reescrever o campo; resultado descartado"}
            por_id[r.get("proposal_id")] = r
    saida = []
    for it in prop.get("proposals") or []:
        pid = it["proposal_id"]
        dv = K.pior(a["verdict"] for a in det.get(pid, []))
        if it.get("origin") == "deterministic":
            # item de regra: veredito só determinístico; "encaminhado sem proposta" = UNSUPPORTED (revisão humana)
            final = dv if (it.get("change_kind") != "none" or it.get("conflict")) else "UNSUPPORTED"
            saida.append({"proposal_id": pid, "field": it.get("field"), "verdict": final, "origin": "deterministic",
                          "current_value_status": "CONTRADICTED" if final == "PASS" else "NOT_ADDRESSED",
                          "deterministic": {"verdict": dv, "findings": det.get(pid, [])},
                          "semantic": {"verdict": "not_applicable", "reason": it.get("reason")},
                          "sufficiency": None, "divergence": False, "curator_precheck": it.get("_precheck_verdict")})
            continue
        r = por_id.get(pid)
        sv = r["verdict"] if r and r.get("verdict") in T.VERDICTS else "UNSUPPORTED"
        suf, suf_motivo = SF.avaliar(it, fontes or {}, (r or {}).get("support") if r else None)
        final = K.pior([dv, sv] + ([suf] if suf != "PASS" and sv == "PASS" else []))
        saida.append({"proposal_id": pid, "field": it.get("field"), "verdict": final,
                      "origin": "curator", "current_value_status": (r or {}).get("current_value_status"),
                      "component": (r or {}).get("component"),
                      "support": (r or {}).get("support"), "sufficiency": suf_motivo or None,
                      "deterministic": {"verdict": dv, "findings": det.get(pid, [])},
                      "semantic": {"verdict": sv, "reason": (r or {}).get("reason", "verifier não avaliou o item"),
                                   "source_used": (r or {}).get("source_used"), "snippet": (r or {}).get("snippet"),
                                   "locator": (r or {}).get("locator"),
                                   "analysis_signature_ref": (r or {}).get("analysis_signature_ref")},
                      "divergence": dv != sv, "curator_precheck": it.get("_precheck_verdict")})
    rel = (llm or {}).get("relationship") or {"verdict": "UNSUPPORTED", "reason": "relação não avaliada"}
    return {"schema": f"theratrials-db-verifier-result/{T.VERSAO}", "uid": prop["uid"],
            "proposal_sha256": sha_proposta(prop), "relationship": rel, "results": saida,
            "_ingestao": {"em": datetime.datetime.now().isoformat(timespec="seconds"), "avisos": avisos}}


def ingerir(uid: str, texto: str | None) -> dict:
    prop = proposta(uid)
    llm = C.extrair_json(texto) if texto else None
    out = fundir(prop, llm, deterministico(uid), C.fontes_do_pacote(C.pacote(uid)))
    VERIF.mkdir(parents=True, exist_ok=True)
    (VERIF / f"{uid}.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return out


def main(argv=None) -> int:
    a = argv or sys.argv[1:]
    if a[:1] == ["entrada"]:
        print(json.dumps(entrada(a[1]), ensure_ascii=False)[:400])
    elif a[:1] == ["ingerir"]:
        o = ingerir(a[1], pathlib.Path(a[2]).read_text(encoding="utf-8"))
        print(json.dumps({"uid": a[1], "vereditos": [r["verdict"] for r in o["results"]],
                          "avisos": o["_ingestao"]["avisos"]}, ensure_ascii=False))
    elif a[:1] == ["ingerir_b"]:                 # 2ª execução: ids = itens da entrada _b
        ids = [it["proposal_id"] for it in json.loads((TAREFAS / f"{a[1]}.verifier_input_b.json").read_text())["items"]]
        o = ingerir_segundo(a[1], pathlib.Path(a[2]).read_text(encoding="utf-8"), ids)
        print(json.dumps({"uid": a[1], "consenso": {k: v["state"] for k, v in o["consensus"].items()}},
                         ensure_ascii=False))
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
