"""curator — prepara a tarefa do database-curator (LLM) e ingere a proposta com pré-checagem determinística.

    python3 scripts/db_v2/agents/curator.py tarefa <uid>            # imprime o prompt da tarefa
    python3 scripts/db_v2/agents/curator.py ingerir <uid> <arquivo>  # valida e grava state/curator/<uid>.json

O curator (LLM) lê SÓ o pacote de evidência e as fontes dele; devolve JSON no schema agents/schemas/proposal.schema.json.
Aqui: schema, sha do pacote, coerência tipo × prioridade, assinaturas, campos protegidos por decisão humana e as
checagens determinísticas de cada item (trecho literal, localizador, números, derivação, fonte permitida).
Proposta nunca é reescrita; só anotada. Nada é escrito no Database.
"""
from __future__ import annotations

import datetime
import json
import pathlib
import re
import sys

AQUI = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
import v2lib as L  # noqa: E402

try:
    from . import agent_types as T, checks as K, deterministic as DT, signature as G, sources as S
except ImportError:
    import agent_types as T
    import checks as K
    import deterministic as DT
    import signature as G
    import sources as S

CURADOR = S.STATE / "curator"
PROMPT_AGENTE = AQUI.parents[3] / ".claude" / "agents" / "database-curator.md"


def pacote(uid: str) -> dict:
    return json.loads((S.STATE / "packets" / uid / "packet.json").read_text(encoding="utf-8"))


def tarefa(uid: str) -> str:
    p = S.STATE / "packets" / uid
    return (f"Card: {uid}\nPacote de evidência: {p / 'packet.json'}\nFontes (só estas): {p / 'fontes'}\n"
            f"Schema de saída: {AQUI / 'schemas' / 'proposal.schema.json'}\n"
            f"packet_sha256: {pacote(uid)['packet_sha256']}\n"
            "Responda APENAS com o JSON da proposta (sem texto fora do JSON).")


def extrair_json(texto: str) -> dict:
    t = texto.strip()
    m = re.search(r"```(?:json)?\s*(\{.*\})\s*```", t, re.S)
    if m:
        t = m.group(1)
    else:
        t = t[t.index("{"): t.rindex("}") + 1]
    return json.loads(t)


def fontes_do_pacote(pk: dict) -> dict:
    return {f["source_id"]: f for f in pk["sources"]}


def ingerir(uid: str, texto: str) -> dict:
    pk = pacote(uid)
    prop = extrair_json(texto)
    avisos = [f"schema: {e}" for e in L.validar_schema(prop, T.PROPOSAL_SCHEMA)]
    if prop.get("uid") != uid:
        avisos.append(f"uid {prop.get('uid')!r} ≠ {uid}")
    if prop.get("packet_sha256") != pk["packet_sha256"]:
        avisos.append("packet_sha256 não corresponde ao pacote (proposta de outra versão das fontes)")
    sig_ids = set()
    for s in prop.get("analysis_signatures") or []:
        sig_ids.add(s.get("signature_id"))
        for e in G.validar(s):
            avisos.append(f"assinatura {s.get('signature_id')}: {e}")
    fontes = fontes_do_pacote(pk)
    pasta = S.STATE / "packets" / uid
    protegidos = set(pk.get("human_decision_protected_fields") or [])
    for it in prop.get("proposals") or []:
        it["_precheck"] = K.conferir_item(it, fontes, pasta)
        it["_precheck_verdict"] = K.pior(a["verdict"] for a in it["_precheck"])
        it["_flags"] = []
        if it.get("analysis_signature_ref") and it["analysis_signature_ref"] not in sig_ids:
            it["_flags"].append(f"analysis_signature_ref {it['analysis_signature_ref']} inexistente")
        if it.get("field") in protegidos:
            it["_flags"].append("campo protegido por decisão humana registrada: exige DEFER")
        for e in it.get("evidence") or []:           # retrieved_at vem do pacote quando o curator não informou
            f = fontes.get(e.get("source_id"))
            if f and not e.get("retrieved_at"):
                e["retrieved_at"] = f.get("retrieved_at")
    for it in prop.get("proposals") or []:
        # origem é imposta, nunca declarada: item do LLM é SEMPRE curator (senão escaparia do verifier)
        if it.get("origin") not in (None, "curator") or any(k.startswith("_det") for k in it):
            avisos.append(f"{it.get('proposal_id')}: origin '{it.get('origin')}' declarada pelo curator; "
                          "rebaixada para curator (item vai ao verifier)")
        for k in [k for k in it if k.startswith("_det")]:
            del it[k]
        it["origin"] = "curator"
        it["_curator_priority"] = it.pop("priority", None)       # sugestão do curator: guardada, ignorada
    if not pk.get("withheld"):
        for it in DT.itens(pk, prop, pasta):                      # regras determinísticas: silêncio não é resultado
            it["_precheck"] = K.conferir_item(it, fontes, pasta)
            it["_precheck_verdict"] = K.pior(a["verdict"] for a in it["_precheck"])
            it["_flags"] = []
            prop.setdefault("proposals", []).append(it)
    if pk.get("withheld") and prop.get("proposals"):
        avisos.append("card em quarentena: nenhuma proposta clínica é aceita")
        for it in prop["proposals"]:
            it["_precheck_verdict"] = "FAIL"
            it["_flags"].append("withheld_due_to_integrity")
    prop["_ingestao"] = {"em": datetime.datetime.now().isoformat(timespec="seconds"), "avisos": avisos,
                         "packet_sha256_ok": prop.get("packet_sha256") == pk["packet_sha256"]}
    CURADOR.mkdir(parents=True, exist_ok=True)
    (CURADOR / f"{uid}.json").write_text(json.dumps(prop, ensure_ascii=False, indent=1), encoding="utf-8")
    return prop


def main(argv=None) -> int:
    a = argv or sys.argv[1:]
    if a[:1] == ["tarefa"]:
        print(tarefa(a[1]))
    elif a[:1] == ["ingerir"]:
        p = ingerir(a[1], pathlib.Path(a[2]).read_text(encoding="utf-8"))
        print(json.dumps({"uid": a[1], "itens": len(p.get("proposals") or []), "avisos": p["_ingestao"]["avisos"],
                          "precheck": [i["_precheck_verdict"] for i in p.get("proposals") or []]}, ensure_ascii=False))
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
