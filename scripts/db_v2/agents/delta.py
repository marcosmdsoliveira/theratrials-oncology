"""delta — DELTA EDITORIAL dos UPDATE_CARD do discovery: proposta cirúrgica por trecho de campo visível.

Componente SEPARADO do discovery, com versão/hash próprio (DELTA_VERSION). Não altera regras nem a versão do
discovery; lê só o relatório de um bloco já executado.

    python3 scripts/db_v2/agents/delta.py schemas                                  # grava os 2 schemas do delta
    python3 scripts/db_v2/agents/delta.py lote --relatorio relatorio_bloco1.json [--rede] [--paralelo 4]
    python3 scripts/db_v2/agents/delta.py consolidar --relatorio relatorio_bloco1.json

Regras (ver delta_instrucoes.md):
  • o delta compara a publicação nova com os CAMPOS VISÍVEIS atuais do card, não com o endpoint principal;
  • cada item troca um trecho LITERAL de um campo existente por um trecho do mesmo tamanho/estilo, com trecho-fonte;
  • nunca nova versão do card, nunca expansão, nunca campo novo; sem correspondência segura → HUMAN_REVIEW;
  • nada é aplicado: a saída é proposta para revisão humana.
"""
from __future__ import annotations

import argparse
import collections
import concurrent.futures as cf
import datetime
import hashlib
import json
import os
import pathlib
import re
import sys
import threading

AQUI = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))

try:
    from . import agent_types as T, checks as K, discovery as DS, sources as S
except ImportError:
    import agent_types as T
    import checks as K
    import discovery as DS
    import sources as S

DIR = S.STATE / "delta"
DELTA_BASE = "delta/1"
CAMPOS_EDITAVEIS = ["primario", "secundario", "resultado_chave", "tox_g3", "subgrupo"]   # resultados que o card exibe
DECISOES = ["DELTA", "HUMAN_REVIEW"]
INSTRUCOES = AQUI / "delta_instrucoes.md"
STR, NSTR = {"type": "string"}, {"type": ["string", "null"]}

DELTA_SCHEMA = {
    "$id": "theratrials-db-delta-curator/1", "type": "object",
    "properties": {
        "schema": {"const": "theratrials-db-delta-curator/1"}, "delta_id": STR, "packet_sha256": STR,
        "items": {"type": "array", "items": {"type": "object", "properties": {
            "item_id": STR, "field_path": {"enum": CAMPOS_EDITAVEIS}, "decision": {"enum": DECISOES},
            "segment_current": NSTR, "segment_proposed": NSTR, "endpoint": STR, "reason": STR,
            "human_review_reason": NSTR, "evidence": {"type": "array", "items": T.EVIDENCE_SCHEMA}},
            "required": ["item_id", "field_path", "decision", "endpoint", "evidence"]}},
        "notes_for_human": STR},
    "required": ["schema", "delta_id", "packet_sha256", "items"],
}
DELTA_VERIFICATION_SCHEMA = {
    "$id": "theratrials-db-delta-verification/1", "type": "object",
    "properties": {
        "schema": {"const": "theratrials-db-delta-verification/1"}, "delta_id": STR, "curator_sha256": STR,
        "items": {"type": "array", "items": {"type": "object", "properties": {
            "item_id": STR, "verdict": {"enum": T.VERDICTS}, "reason": {"type": "string", "minLength": 5},
            "locator": NSTR, "snippet": NSTR}, "required": ["item_id", "verdict", "reason"]}}},
    "required": ["schema", "delta_id", "curator_sha256", "items"],
}
SCHEMAS = {"delta.schema.json": DELTA_SCHEMA, "delta_verification.schema.json": DELTA_VERIFICATION_SCHEMA}
ARQUIVOS_VERSAO = ["delta.py", "delta_instrucoes.md", "checks.py", "sources.py", "schemas/delta.schema.json",
                   "schemas/delta_verification.schema.json", "../../../.claude/agents/database-curator.md",
                   "../../../.claude/agents/database-verifier.md"]


def gravar_schemas() -> None:
    for nome, s in SCHEMAS.items():
        (AQUI / "schemas" / nome).write_text(json.dumps(s, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def versao() -> str:
    return f"{DELTA_BASE}+{DS._sha(b''.join((AQUI / f).read_bytes() for f in ARQUIVOS_VERSAO))[:16]}"


def _norm_ws(t: str) -> str:
    return re.sub(r"\s+", " ", str(t or "")).strip()


# ── preparação (determinística) ─────────────────────────────────────────────────────────────────────────────────
def updates_do_relatorio(relatorio: str) -> list[dict]:
    r = json.loads((DS.DISC / relatorio).read_text())
    return [x for x in r["rows"] if x.get("action") == "UPDATE_CARD"]


def delta_id(linha: dict) -> str:
    return f"{linha['uid']}__{linha['pmid'] or re.sub(r'[^A-Za-z0-9]', '_', linha['doi'] or 'x')}"


def preparar(linha: dict, rede: bool = False) -> dict:
    uid, pmid = linha["uid"], linha.get("pmid")
    did = delta_id(linha)
    pasta = DIR / did
    fdir = pasta / "fontes"
    fdir.mkdir(parents=True, exist_ok=True)
    for f in fdir.glob("*.txt"):
        f.unlink()
    card = DS.cards()[uid]
    disc = json.loads((DS.DISC / uid / "packet.json").read_text())
    fontes = []

    def fonte(sid, stype, nivel, pars, papel):
        if pars:
            p = S.gravar_fonte(fdir, sid, pars)
            fontes.append({"source_id": sid, "source_type": stype, "text_level": nivel, "path": f"fontes/{p.name}",
                           "paragraphs": len(pars), "role": papel})
    # publicação nova: resumo (como no discovery) + texto completo aberto, se houver
    e = S.pubmed_efetch(pmid, rede) if pmid else {}
    if e:
        fonte(f"pmid:{pmid}:abstract", "pubmed_abstract", "abstract",
              [("Title", e["title"])] + [(f"Abstract > {s}", t) for s, t in e["abstract"]], "candidate")
        if e.get("pmcid"):
            fonte(f"pmc:{e['pmcid']}:fulltext", "europepmc_fulltext", "fulltext", S.pmc_fulltext(e["pmcid"], rede),
                  "candidate")
    # publicação que o card representa hoje (copiada do pacote do discovery)
    for f in disc["sources"]:
        if f.get("role") == "represented":
            pars = list(S.ler_paragrafos(DS.DISC / uid / f["path"]).values())
            fonte(f["source_id"], f["source_type"], f["text_level"],
                  [(t[1:t.index("]")] if t.startswith("[") else "", re.sub(r"^\[[^\]]*\]\s*", "", t)) for t in pars],
                  "represented")
    pacote = {
        "schema": "theratrials-db-delta-packet/1", "delta_id": did, "uid": uid, "delta_version": versao(),
        "discovery_version": DS.versao_pipeline(),
        "card_fields": {k: card.get(k) for k in CAMPOS_EDITAVEIS if str(card.get(k) or "").strip() not in ("", "—")},
        "card_note": "card_fields = o que o card mostra hoje; não é evidência",
        "card_context": {k: card.get(k) for k in ("estudo", "acron", "n", "ano_pub")},
        "candidate": {k: linha.get(k) for k in ("pmid", "doi", "title", "date")},
        "discovery": {k: linha.get(k) for k in ("relation", "action", "final_verdict", "verifier_verdict", "reason",
                                                 "signature")},
        "represented_publication": disc.get("represented_publication"),
        "sources": fontes,
    }
    pacote["packet_sha256"] = DS._sha(pacote)
    (pasta / "packet.json").write_text(json.dumps(pacote, ensure_ascii=False, indent=1), encoding="utf-8")
    return pacote


def tarefa(did: str) -> str:
    p = json.loads((DIR / did / "packet.json").read_text())
    return (f"MODO DELTA. Instruções: {INSTRUCOES}\nPacote: {DIR / did / 'packet.json'} · fontes em {DIR / did / 'fontes'}\n"
            f"Schema de saída: {AQUI / 'schemas' / 'delta.schema.json'}\n"
            f"delta_id: {did} · packet_sha256: {p['packet_sha256']}\n"
            f"Campos editáveis que o card exibe: {', '.join(p['card_fields'])}\n")


def entrada(did: str) -> pathlib.Path:
    cur = json.loads((DIR / did / "curator.json").read_text())
    visivel = ["item_id", "field_path", "decision", "segment_current", "segment_proposed", "endpoint",
               "human_review_reason", "evidence"]
    ent = {"delta_id": did, "packet": str(DIR / did / "packet.json"), "fontes": str(DIR / did / "fontes"),
           "curator_sha256": cur["_sha256"], "items": [{k: i.get(k) for k in visivel} for i in cur.get("items", [])]}
    alvo = DIR / did / "verifier_input.json"
    alvo.write_text(json.dumps(ent, ensure_ascii=False, indent=1), encoding="utf-8")
    return alvo


def tarefa_verifier(did: str) -> str:
    alvo = entrada(did)
    return (f"MODO DELTA. Instruções: {INSTRUCOES}\nEntrada: {alvo}\n"
            f"Schema de saída: {AQUI / 'schemas' / 'delta_verification.schema.json'}\n"
            f"delta_id: {did} · curator_sha256: {json.loads(alvo.read_text())['curator_sha256']}\n"
            "Avalie TODOS os itens da entrada.\n")


# ── checagens determinísticas ───────────────────────────────────────────────────────────────────────────────────
def limite_tamanho(atual: str) -> int:
    return max(int(len(atual) * 1.6), len(atual) + 60)


def conferir(did: str, cur: dict) -> dict:
    p = json.loads((DIR / did / "packet.json").read_text())
    pasta = DIR / did
    fontes = {f["source_id"]: f for f in p["sources"]}
    candidatas = {f["source_id"] for f in p["sources"] if f.get("role") == "candidate"}
    campos = p["card_fields"]
    out, usados = {}, collections.defaultdict(list)
    for it in cur.get("items", []):
        ach = []
        add = lambda code, v, d: ach.append({"code": code, "verdict": v, "detail": d})  # noqa: E731
        campo = it.get("field_path")
        if campo not in CAMPOS_EDITAVEIS or campo not in campos:
            add("FIELD_NOT_EXISTING", "FAIL", f"campo {campo!r} não é um campo editável que o card já exibe")
        if it.get("decision") not in DECISOES:
            add("DECISION_ENUM", "FAIL", f"decision inválida {it.get('decision')!r}")
        if it.get("decision") == "HUMAN_REVIEW":
            if it.get("segment_proposed"):
                add("HUMAN_REVIEW_WITH_TEXT", "FAIL", "HUMAN_REVIEW não pode trazer texto clínico proposto")
            if not (it.get("human_review_reason") or "").strip():
                add("HUMAN_REVIEW_NO_REASON", "UNSUPPORTED", "HUMAN_REVIEW sem dúvida objetiva")
            out[it.get("item_id")] = {"verdict": K.pior([a["verdict"] for a in ach] or ["PASS"]), "achados": ach}
            continue
        atual, novo = it.get("segment_current") or "", it.get("segment_proposed") or ""
        texto_campo = _norm_ws(campos.get(campo, ""))
        if not atual.strip() or _norm_ws(atual) not in texto_campo:
            add("CURRENT_NOT_FOUND", "FAIL", "segment_current não é trecho literal do campo atual")
        if not novo.strip() or _norm_ws(novo) == _norm_ws(atual):
            add("NO_CHANGE", "FAIL", "segment_proposed vazio ou igual ao atual")
        if atual and _norm_ws(atual) == texto_campo and len(texto_campo) > 80:
            add("WHOLE_FIELD_REWRITE", "UNSUPPORTED", "o item substitui o campo inteiro: delta deve ser cirúrgico")
        if atual and len(novo) > limite_tamanho(atual):
            add("EXPANSION", "FAIL", f"trecho proposto ({len(novo)} car.) excede o limite de {limite_tamanho(atual)}")
        for (ini, fim) in usados[campo]:
            j = texto_campo.find(_norm_ws(atual))
            if j >= 0 and not (j + len(_norm_ws(atual)) <= ini or j >= fim):
                add("OVERLAP", "FAIL", "dois itens alteram trechos sobrepostos do mesmo campo")
        j = texto_campo.find(_norm_ws(atual))
        if j >= 0:
            usados[campo].append((j, j + len(_norm_ws(atual))))
        ev = it.get("evidence") or []
        if not any(e.get("source_id") in candidatas for e in ev):
            add("EVIDENCE_NOT_FROM_NEW_PUBLICATION", "UNSUPPORTED", "nenhum trecho vem da publicação nova")
        item = {"evidence": ev, "change_kind": "replace", "value_origin": "reported", "proposed_value": novo}
        for a in K.conferir_item(item, fontes, pasta):
            if a["verdict"] != "PASS":
                ach.append(a)
        out[it.get("item_id")] = {"verdict": K.pior([a["verdict"] for a in ach] or ["PASS"]), "achados": ach}
    return out


def _json(txt: str) -> dict:
    m = re.search(r"\{.*\}", txt.strip(), re.S)
    return json.loads(m.group(0) if m else txt)


def ingerir(papel: str, did: str, arquivo: str) -> dict:
    d = _json(pathlib.Path(arquivo).read_text(encoding="utf-8"))
    sha = hashlib.sha256(json.dumps(d, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    p = json.loads((DIR / did / "packet.json").read_text())
    if papel == "curator":
        erros = [] if d.get("schema") == DELTA_SCHEMA["$id"] else [f"schema {d.get('schema')!r}"]
        if d.get("packet_sha256") != p["packet_sha256"]:
            erros.append("packet_sha256 não confere")
        d["_sha256"], d["_erros"] = sha, erros
        d["_deterministico"] = conferir(did, d)
        (DIR / did / "curator.json").write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    else:
        cur = json.loads((DIR / did / "curator.json").read_text())
        erros = [] if d.get("curator_sha256") == cur["_sha256"] else ["curator_sha256 não confere"]
        if any(k in i for i in d.get("items", []) for k in ("segment_proposed", "corrected", "proposed_text")):
            erros.append("verifier reescreveu (proibido)")
        d["_sha256"], d["_erros"] = sha, erros
        (DIR / did / "verifier.json").write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    return d


# ── lote retomável ──────────────────────────────────────────────────────────────────────────────────────────────
ETAPAS = ("preparar", "curator", "verifier")


def compat(linha: dict) -> dict:
    card = DS.cards()[linha["uid"]]
    return {"delta_version": versao(), "card_fields_sha": DS._sha({k: card.get(k) for k in CAMPOS_EDITAVEIS}),
            "discovery_row_sha": DS._sha({k: linha.get(k) for k in ("uid", "pmid", "relation", "action", "final_verdict")})}


def processar(linha: dict, etapas: dict, trava: threading.Lock) -> dict:
    did = delta_id(linha)
    comp = compat(linha)
    f = DIR / did / "estado.json"
    try:
        e = json.loads(f.read_text())
        inicial = "compativel" if e.get("compat") == comp else "invalidado"
        if inicial == "invalidado":
            e = {"compat": comp, "etapas": {}}
    except (FileNotFoundError, json.JSONDecodeError):
        e, inicial = {"compat": comp, "etapas": {}}, "novo"
    feitas = []
    for nome in ETAPAS:
        if (e["etapas"].get(nome) or {}).get("ok"):
            continue
        if nome == "preparar":
            with trava:
                res = etapas["preparar"](linha)
        else:
            res = etapas[nome](did)
        e["etapas"][nome] = {"ok": True, "em": datetime.datetime.now().isoformat(timespec="seconds"), **(res or {})}
        (DIR / did).mkdir(parents=True, exist_ok=True)
        tmp = DIR / did / "estado.json.tmp"
        tmp.write_text(json.dumps(e, ensure_ascii=False, indent=1), encoding="utf-8")
        os.replace(tmp, f)
        feitas.append(nome)
    return {"delta_id": did, "estado_inicial": inicial, "etapas_executadas": feitas}


def etapas_reais(rede: bool) -> dict:
    def prep(linha):
        return {"packet_sha256": preparar(linha, rede)["packet_sha256"]}

    def agente(papel):
        def rodar(did):
            try:
                from . import run_agents as RA
            except ImportError:
                import run_agents as RA
            au = RA.executar(f"delta_{papel}", did)
            d = ingerir(papel, did, str(RA.RAW / f"{did}.delta_{papel}.json"))
            if d.get("_erros"):
                raise RuntimeError(f"{papel}: {d['_erros']}")
            return {"sha256": d["_sha256"], "custo_usd": au.get("custo_usd")}
        return rodar
    return {"preparar": prep, "curator": agente("curator"), "verifier": agente("verifier")}


def executar_lote(linhas: list[dict], rede: bool = False, paralelo: int = 4, etapas: dict | None = None) -> list[dict]:
    etapas = etapas or etapas_reais(rede)
    trava, out = threading.Lock(), []
    with cf.ThreadPoolExecutor(max_workers=paralelo) as ex:
        futs = {ex.submit(processar, l, etapas, trava): delta_id(l) for l in linhas}
        for f in cf.as_completed(futs):
            try:
                out.append(f.result())
            except Exception as x:                               # noqa: BLE001
                out.append({"delta_id": futs[f], "erro": f"{type(x).__name__}: {x}"})
    return out


# ── consolidação ────────────────────────────────────────────────────────────────────────────────────────────────
def consolidar(linhas: list[dict], nome: str) -> dict:
    deltas, por_update = [], []
    for l in linhas:
        did = delta_id(l)
        pasta = DIR / did
        cur = json.loads((pasta / "curator.json").read_text()) if (pasta / "curator.json").exists() else {}
        ver = json.loads((pasta / "verifier.json").read_text()) if (pasta / "verifier.json").exists() else {}
        p = json.loads((pasta / "packet.json").read_text()) if (pasta / "packet.json").exists() else {}
        det = cur.get("_deterministico", {})
        vmap = {i.get("item_id"): i for i in ver.get("items", [])}
        itens = []
        for it in cur.get("items", []):
            iid = it.get("item_id")
            vv = vmap.get(iid, {})
            dd = det.get(iid, {"verdict": "UNSUPPORTED", "achados": []})
            vver = "FAIL" if (cur.get("_erros") or ver.get("_erros")) else (vv.get("verdict") or "UNSUPPORTED")
            final = K.pior([dd["verdict"], vver])
            seguro = it.get("decision") == "DELTA" and final == "PASS"
            itens.append({"delta_id": did, "uid": l["uid"], "pmid": l.get("pmid"), "doi": l.get("doi"),
                          "field_path": it.get("field_path"), "endpoint": it.get("endpoint"),
                          "decision": it.get("decision"), "current": it.get("segment_current"),
                          "proposed": it.get("segment_proposed"), "reason": it.get("reason"),
                          "human_review_reason": it.get("human_review_reason"),
                          "source": [{"source_id": e.get("source_id"), "locator": e.get("locator"),
                                      "snippet": e.get("snippet")} for e in it.get("evidence") or []],
                          "deterministic_verdict": dd["verdict"], "deterministic_checks": dd["achados"],
                          "verifier_verdict": vver, "verifier_reason": vv.get("reason"),
                          "final_verdict": final, "safe_delta": seguro})
        deltas += itens
        por_update.append({"delta_id": did, "uid": l["uid"], "pmid": l.get("pmid"), "title": l.get("title"),
                           "discovery_verdict": l.get("final_verdict"), "itens": len(itens),
                           "deltas_seguros": sum(i["safe_delta"] for i in itens),
                           "status": "DELTA_SEGURO" if itens and all(i["safe_delta"] for i in itens) else "HUMAN_REVIEW",
                           "notes_for_human": cur.get("notes_for_human"),
                           "card_fields_touched": sorted({i["field_path"] for i in itens if i["decision"] == "DELTA"}),
                           "card_fields_available": sorted((p.get("card_fields") or {}).keys())})
    rel = {"gerado_em": datetime.date.today().isoformat(), "delta_version": versao(),
           "discovery_version": DS.versao_pipeline(), "updates": por_update, "deltas": deltas,
           "resumo": {"updates": len(por_update),
                      "updates_com_delta_seguro": sum(u["status"] == "DELTA_SEGURO" for u in por_update),
                      "updates_human_review": sum(u["status"] == "HUMAN_REVIEW" for u in por_update),
                      "itens": len(deltas), "itens_seguros": sum(d["safe_delta"] for d in deltas),
                      "por_veredito": dict(collections.Counter(d["final_verdict"] for d in deltas))}}
    DIR.mkdir(parents=True, exist_ok=True)
    (DIR / f"relatorio_{nome}.json").write_text(json.dumps(rel, ensure_ascii=False, indent=1), encoding="utf-8")
    return rel


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["schemas", "lote", "consolidar", "tarefa", "entrada"])
    ap.add_argument("args", nargs="*")
    ap.add_argument("--relatorio", default="relatorio_bloco1.json")
    ap.add_argument("--rede", action="store_true")
    ap.add_argument("--paralelo", type=int, default=4)
    a = ap.parse_args(argv)
    nome = pathlib.Path(a.relatorio).stem.replace("relatorio_", "")
    if a.cmd == "schemas":
        gravar_schemas()
        print(versao())
    elif a.cmd == "lote":
        for r in executar_lote(updates_do_relatorio(a.relatorio), a.rede, a.paralelo):
            print(json.dumps(r, ensure_ascii=False), flush=True)
    elif a.cmd == "consolidar":
        r = consolidar(updates_do_relatorio(a.relatorio), nome)
        print(json.dumps(r["resumo"], ensure_ascii=False, indent=1))
    elif a.cmd == "tarefa":
        print(tarefa(a.args[0]))
    elif a.cmd == "entrada":
        print(tarefa_verifier(a.args[0]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
