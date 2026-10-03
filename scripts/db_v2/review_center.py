#!/usr/bin/env python3
"""Review Center editorial: revisão humana LOCAL dos outputs do discovery/delta (blocos já processados).

    python3 scripts/db_v2/review_center.py          →  http://127.0.0.1:8765

O que faz:
- lê (só lê) `scripts/db_v2/state/discovery/` e `scripts/db_v2/state/delta/`, e o `assets/js/data.js` atual;
- monta a fila por card com os pacotes UPDATE_CARD (um item por trecho do delta), HUMAN_REVIEW e ADD_SECONDARY;
- registra APPROVE / REJECT / DEFER + comentário em `scripts/db_v2/review/decisions.json`
  (histórico append-only em `history.jsonl`), fora do state.

O que NÃO faz: aplicar decisões, alterar data.js ou secondary-cards.js, criar card, commitar, chamar LLM ou API
externa. Decisão ≠ aplicação. O servidor só escuta em 127.0.0.1 e só serve as rotas fixas abaixo.

Uma decisão guarda o `fingerprint` do item que foi revisado. Se o conteúdo do item mudar depois (novo run, card
editado), a decisão fica STALE e o item volta a exigir revisão.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import http.server
import json
import os
import pathlib
import re
import sys
import tempfile
import threading
import urllib.parse
import xml.etree.ElementTree as ET

AQUI = pathlib.Path(__file__).resolve().parent
SITE = AQUI.parent.parent
STATE = AQUI / "state"
DECISOES = AQUI / "review" / "decisions.json"
DATA_JS = SITE / "assets" / "js" / "data.js"
WEB = AQUI / "review_center_web"

HOST = "127.0.0.1"          # fixo: nunca exposto à rede
PORTA = 8765
SCHEMA = "theratrials-review-decisions/1"
VALIDAS = ("APPROVE", "REJECT", "DEFER")
PACOTES = ("UPDATE_CARD", "NEW_CARD", "HUMAN_REVIEW", "ADD_SECONDARY")
ORDEM = {p: i for i, p in enumerate(PACOTES)}
CAMPOS_VISIVEIS = ("primario", "secundario", "resultado_chave", "tox_g3", "subgrupo")
MAX_COMENTARIO = 4000
MAX_CORPO = 20000
ESTATICOS = {"/": ("index.html", "text/html; charset=utf-8"),
             "/app.js": ("app.js", "text/javascript; charset=utf-8"),
             "/app.css": ("app.css", "text/css; charset=utf-8")}


# ---------------------------------------------------------------- leitura (somente leitura)
def _ler(p: pathlib.Path):
    return json.loads(p.read_text(encoding="utf-8"))


def _sha(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def blocos(state: pathlib.Path) -> list[int]:
    """Blocos com fila humana E relatório do discovery (pilotos ficam de fora)."""
    achados = []
    for f in (state / "discovery").glob("fila_humana_bloco*.json"):
        m = re.fullmatch(r"fila_humana_bloco(\d+)\.json", f.name)
        if m and (state / "discovery" / f"relatorio_bloco{m.group(1)}.json").exists():
            achados.append(int(m.group(1)))
    return sorted(achados)


def cards_atuais(data_js: pathlib.Path) -> dict:
    """Campos visíveis do data.js ATUAL, por uid (para avisar quando o card mudou desde o run)."""
    if not data_js.exists():
        return {}
    txt = data_js.read_text(encoding="utf-8")
    i = txt.index("window.THERA_DATA")
    corpo = txt[txt.index("{", i):].strip().rstrip(";")
    return {s["uid"]: {k: s.get(k) for k in CAMPOS_VISIVEIS + ("estudo",)} for s in json.loads(corpo)["studies"]}


def pub_id(x: dict) -> str:
    if x.get("pmid"):
        return f"pmid:{x['pmid']}"
    if x.get("doi"):
        return f"doi:{str(x['doi']).lower()}"
    return "sem-id"


def delta_id(x: dict) -> str:          # mesma regra de agents/delta.py
    return f"{x['uid']}__{x.get('pmid') or re.sub(r'[^A-Za-z0-9]', '_', x.get('doi') or 'x')}"


def decision_id(uid, pub, pacote, field_path=None, item_id=None) -> str:
    chave = "|".join([uid, pub, pacote, field_path or "", item_id or ""])
    return "rc1-" + hashlib.sha256(chave.encode()).hexdigest()[:20]


def _avisos(row: dict) -> list[str]:
    av = []
    for c in row.get("curator_checks") or []:
        if c.get("verdict") != "PASS":
            av.append(f"{c.get('code')} ({c.get('verdict')}): {c.get('detail')}")
    if row.get("final_verdict") and row["final_verdict"] != "PASS":
        av.append(f"Veredito final do discovery: {row['final_verdict']}")
    if row.get("temporal_marker"):
        av.append(f"Marcador temporal: {row['temporal_marker']}")
    if row.get("not_verified"):
        av.append(f"Campos da assinatura não verificados: {json.dumps(row['not_verified'], ensure_ascii=False)}")
    if row.get("pooled_signal"):
        av.append(f"Sinal de pooled: {json.dumps(row['pooled_signal'], ensure_ascii=False)}")
    rbs = row.get("relation_by_signature")
    if isinstance(rbs, list) and rbs and rbs[0] and rbs[0] != row.get("relation"):
        av.append(f"A comparação de assinaturas sugere {rbs[0]}" + (f": {rbs[1]}" if len(rbs) > 1 and rbs[1] else ""))
    return av


def _versao_discovery(state: pathlib.Path, uid: str) -> dict:
    f = state / "discovery" / uid / "estado.json"
    if not f.exists():
        return {"discovery": None}
    e = _ler(f)
    v = {"discovery": (e.get("compat") or {}).get("pipeline_version")}
    if e.get("migracao"):
        v["normalizado_de"] = (e.get("compat_v2") or {}).get("pipeline_version") or "discovery/2"
    return v


def _journal(state: pathlib.Path, uid: str, pub: str):
    f = state / "discovery" / uid / "packet.json"
    if not f.exists():
        return None
    for c in _ler(f).get("candidates") or []:
        if pub_id(c) == pub:
            return c.get("journal")
    return None


def carregar_itens(state: pathlib.Path = STATE, data_js: pathlib.Path = DATA_JS) -> dict:
    """Itens revisáveis dos blocos existentes. Não grava nada."""
    vivos = cards_atuais(data_js)
    itens, por_bloco = [], {}
    for b in blocos(state):
        fila = _ler(state / "discovery" / f"fila_humana_bloco{b}.json")
        rel = _ler(state / "discovery" / f"relatorio_bloco{b}.json")
        fdel = state / "delta" / f"relatorio_bloco{b}.json"
        dl = _ler(fdel) if fdel.exists() else {"updates": [], "deltas": []}
        linhas = {(r["uid"], pub_id(r)): r for r in rel.get("rows", [])}
        updates = {u["delta_id"]: u for u in dl.get("updates", [])}
        deltas: dict[str, list] = {}
        for d in dl.get("deltas", []):
            deltas.setdefault(d["delta_id"], []).append(d)
        n0 = len(itens)
        for uid, card in fila.get("cards", {}).items():
            versao = {**_versao_discovery(state, uid), "delta": dl.get("delta_version")}
            for pacote, lista in card.get("pacotes", {}).items():
                if pacote not in PACOTES:
                    continue
                for compacto in lista:
                    pub = pub_id(compacto)
                    row = {**compacto, **linhas.get((uid, pub), {}), "uid": uid}
                    base = {
                        "bloco": b, "uid": uid, "trial": card.get("trial"), "pacote": pacote,
                        "acao_original": row.get("action"), "pub": pub, "pmid": row.get("pmid"), "doi": row.get("doi"),
                        "title": row.get("title"), "journal": _journal(state, uid, pub), "date": row.get("date"),
                        "relation": row.get("relation"), "temporal_marker": row.get("temporal_marker"),
                        "origin": row.get("origin"), "reason": row.get("reason"),
                        "discovery_verdicts": {"curator": row.get("curator_verdict"), "verifier": row.get("verifier_verdict"),
                                               "final": row.get("final_verdict")},
                        "verifier_reason": row.get("verifier_reason"), "evidence": row.get("evidence") or [],
                        "comparison": row.get("comparison"), "signature": (row.get("signature") or {}).get("candidate"),
                        "checks": row.get("curator_checks") or [], "avisos": _avisos(row), "pipeline": versao,
                    }
                    if pacote != "UPDATE_CARD":
                        itens.append(_fechar({**base, "tipo": pacote.lower(), "verdict": row.get("final_verdict")},
                                             decision_id(uid, pub, pacote)))
                        continue
                    did = delta_id(row)
                    up = updates.get(did)
                    lst = deltas.get(did, [])
                    pasta = state / "delta" / did
                    ids = [i.get("item_id") for i in (_ler(pasta / "curator.json").get("items", [])
                                                      if (pasta / "curator.json").exists() else [])]
                    ctx = _ler(pasta / "packet.json").get("card_fields", {}) if (pasta / "packet.json").exists() else {}
                    comum = {**base, "delta_id": did, "delta_status": (up or {}).get("status"),
                             "notes_for_human": (up or {}).get("notes_for_human")}
                    if not lst:
                        av = list(base["avisos"]) + ([] if up else ["Delta ausente para este UPDATE_CARD"])
                        itens.append(_fechar({**comum, "tipo": "update_sem_itens", "avisos": av,
                                              "verdict": row.get("final_verdict")},
                                             decision_id(uid, pub, pacote, None, "sem-itens")))
                        continue
                    for k, d in enumerate(lst):
                        iid = ids[k] if k < len(ids) and ids[k] else f"idx{k + 1:02d}"
                        fp = d.get("field_path")
                        vivo = (vivos.get(uid) or {}).get(fp)
                        av = list(base["avisos"])
                        for c in d.get("deterministic_checks") or []:
                            av.append(f"Delta · {c.get('code')} ({c.get('verdict')}): {c.get('detail')}")
                        presente = None
                        if d.get("decision") == "DELTA" and d.get("current"):
                            presente = bool(vivo) and _norm(d["current"]) in _norm(vivo)
                            if not presente:
                                av.append("O trecho ATUAL não está mais no data.js de hoje: o card mudou desde o run")
                        if not d.get("safe_delta") and d.get("decision") == "DELTA":
                            av.append("safe_delta = false: este trecho não passou em todas as checagens")
                        itens.append(_fechar({
                            **comum, "tipo": "delta" if d.get("decision") == "DELTA" else "delta_hr",
                            "item_id": iid, "field_path": fp, "endpoint": d.get("endpoint"),
                            "current": d.get("current"), "proposed": d.get("proposed"), "delta_reason": d.get("reason"),
                            "human_review_reason": d.get("human_review_reason"), "source": d.get("source") or [],
                            "safe_delta": bool(d.get("safe_delta")),
                            "delta_verdicts": {"deterministic": d.get("deterministic_verdict"),
                                               "verifier": d.get("verifier_verdict"), "final": d.get("final_verdict")},
                            "delta_verifier_reason": d.get("verifier_reason"),
                            "campo_no_run": ctx.get(fp), "campo_hoje": vivo, "trecho_presente_hoje": presente,
                            "verdict": pior(row.get("final_verdict"), d.get("final_verdict")), "avisos": av,
                        }, decision_id(uid, pub, pacote, fp, iid)))
        por_bloco[b] = len(itens) - n0
    novos = carregar_novos(state, data_js)
    if novos:
        itens += novos
        por_bloco["novos"] = len(novos)
    for k, it in enumerate(itens):
        it["_seq"] = k                      # ordem da fila e do delta, preservada dentro de cada pacote
    itens.sort(key=_ordem(itens))
    for it in itens:
        del it["_seq"]
    return {"itens": itens, "blocos": por_bloco}


# ---------------------------------------------------------------- expansão de cobertura (state/novos), só leitura
def _versao_novos() -> str | None:
    try:
        sys.path.insert(0, str(AQUI / "agents"))
        import new_trial_discovery as NT                    # noqa: E402  (só para ler a versão congelada)
        return NT.versao()
    except Exception:                                        # noqa: BLE001
        return None


def _revista(state: pathlib.Path, pmid) -> tuple[str | None, str | None]:
    """Periódico/ano a partir do XML do PubMed já em cache (nenhuma rede)."""
    f = state / "cache" / "pubmed" / f"{pmid}.xml"
    if not pmid or not f.exists():
        return None, None
    try:
        art = ET.fromstring(f.read_bytes()).find(".//PubmedArticle")
        j = art.find(".//Journal")
        rev = (j.findtext("ISOAbbreviation") or j.findtext("Title")) if j is not None else None
        ano = art.findtext(".//JournalIssue/PubDate/Year") or (art.findtext(".//JournalIssue/PubDate/MedlineDate") or "")[:4]
        return rev, ano or None
    except Exception:                                        # noqa: BLE001
        return None, None


def carregar_novos(state: pathlib.Path, data_js: pathlib.Path) -> list[dict]:
    """NEW_CARD e dúvidas de identidade do pipeline novos. Saída do LLM só da versão congelada e completa; dúvidas de
    identidade determinísticas (POSSIBLE_DUPLICATE / RELATED_TO_EXISTING) entram como HUMAN_REVIEW, nunca como NEW_CARD."""
    nd = state / "novos"
    if not (nd / "triagem.json").exists():
        return []
    versao = _versao_novos()
    tri = _ler(nd / "triagem.json")["candidatos"]
    por_id = {c["cand_id"]: c for c in tri}
    vivos = cards_atuais(data_js)
    duvidas = {}
    for c in tri:
        if c["dedup"]["classe"] == "POSSIBLE_DUPLICATE" and c["dedup"].get("uid"):
            duvidas.setdefault(c["dedup"]["uid"], []).append(c["cand_id"])

    def alvo(uid):
        if not uid:
            return None
        if uid in vivos:
            return {"tipo": "card", "id": uid, "nome": vivos[uid].get("estudo")}
        o = por_id.get(uid)
        return {"tipo": "candidato", "id": uid, "nome": (o or {}).get("acronym") or (o or {}).get("title")}

    itens = []
    for c in tri:
        cid = c["cand_id"]
        pasta = nd / cid
        cur = ver = pac = None
        if all((pasta / f).exists() for f in ("curator.json", "verifier.json", "packet.json", "estado.json")):
            e = _ler(pasta / "estado.json")
            if versao and (e.get("compat") or {}).get("novos_version") == versao and \
                    all((e["etapas"].get(k) or {}).get("ok") for k in ("preparar", "curator", "verifier")):
                cur, ver, pac = _ler(pasta / "curator.json"), _ler(pasta / "verifier.json"), _ler(pasta / "packet.json")
        dd = c["dedup"]
        identidade = None
        if dd["classe"] in ("POSSIBLE_DUPLICATE", "RELATED_TO_EXISTING"):
            identidade = {"classe": dd["classe"], "motivo": dd.get("motivo"), "relacionado": alvo(dd.get("uid"))}
        if cur:
            det = (cur.get("_deterministico") or {}).get("verdict")
            vv = "FAIL" if (cur.get("_erros") or ver.get("_erros")) else ver.get("verdict")
            final = pior(det, vv or "UNSUPPORTED")
            acao = cur.get("action")
            if acao not in ("NEW_CARD", "HUMAN_REVIEW", "RELATED_TO_EXISTING") and final == "PASS":
                continue
            if acao == "RELATED_TO_EXISTING" and not identidade:
                identidade = {"classe": "RELATED_TO_EXISTING", "motivo": "curator: relacionado a card existente",
                              "relacionado": alvo(cur.get("related_card_uid"))}
        elif c.get("pre_action") in ("HUMAN_REVIEW", "RELATED_TO_EXISTING"):
            det = vv = final = None
            acao = c["pre_action"]
        else:
            continue
        pacote = "NEW_CARD" if acao == "NEW_CARD" and not identidade else "HUMAN_REVIEW"
        tipo = "novo_identidade" if identidade else ("novo_card" if pacote == "NEW_CARD" else "novo_revisao")
        mp = ((cur or {}).get("main_publication") or {})
        pmid = mp.get("pmid") or (cid[4:] if cid.startswith("pmid") else None)
        rev, ano = _revista(state, pmid)
        cand = (pac or {}).get("candidate") or {}
        av = []
        for a in ((cur or {}).get("_deterministico") or {}).get("achados") or []:
            if a.get("verdict") != "PASS":
                av.append(f"{a.get('code')} ({a.get('verdict')}): {a.get('detail')}")
        if final and final != "PASS":
            av.append(f"Veredito final: {final}")
        for d in dd.get("dicas") or []:
            av.append(f"Deduplicação: {d}")
        if cid in duvidas:
            av.append("Há publicação sem NCT que pode ser do MESMO estudo (identidade não comprovada): "
                      + ", ".join(duvidas[cid]) + " — revise antes de aprovar")
        item = {
            "bloco": "novos", "uid": f"novos:{cid}", "cand_id": cid, "pacote": pacote, "tipo": tipo, "acao_original": acao,
            "trial": (cur or {}).get("study") or c.get("acronym") or c.get("title"), "pub": f"cand:{cid}",
            "registry_ids": [c["nct"]] if c.get("nct") else [], "nct": c.get("nct"), "pmid": pmid,
            "doi": mp.get("doi") or (c.get("dois") or [None])[0], "title": c.get("title"), "journal": rev, "date": ano,
            "tumor": (cur or {}).get("tumor"), "tumor_groups": c.get("tumor_groups"),
            "phase": (cur or {}).get("phase") or ", ".join(c.get("phases") or []) or None,
            "intervention": (cur or {}).get("intervention") or ", ".join(c.get("interventions") or []) or None,
            "comparator": (cur or {}).get("comparator"), "population": ", ".join(cand.get("conditions") or c.get("conditions") or []) or None,
            "primary_endpoint": (cur or {}).get("primary_endpoint"), "main_result": (cur or {}).get("main_result"),
            "maturity": (cur or {}).get("maturity"), "reason": (cur or {}).get("reason") or c.get("pre_reason"),
            "policy_basis": (cur or {}).get("policy_basis"), "comparison_type": (cur or {}).get("comparison_type"),
            "editorial_limitation": (cur or {}).get("editorial_limitation"), "evidence": (cur or {}).get("evidence") or [],
            "discovery_verdicts": {"curator": det, "verifier": vv, "final": final},
            "verifier_reason": (ver or {}).get("reason"), "identidade": identidade, "avisos": av,
            "origem": "llm" if cur else "deterministic", "pipeline": {"novos": versao}, "verdict": final,
        }
        itens.append(_fechar(item, decision_id(item["uid"], item["pub"], pacote)))
    return itens


GRAVIDADE = {"PASS": 0, "UNSUPPORTED": 1, "CONFLICT": 2, "FAIL": 3}


def pior(*vs) -> str | None:
    """Veredito exibido de um trecho do delta: o pior entre o discovery (a classificação UPDATE_CARD) e o delta."""
    vs = [v for v in vs if v in GRAVIDADE]
    return max(vs, key=GRAVIDADE.get) if vs else None


def _norm(t: str) -> str:
    return re.sub(r"\s+", " ", t or "").strip()


def _fechar(item: dict, did: str) -> dict:
    item["decision_id"] = did
    item["fingerprint"] = _sha({k: v for k, v in item.items() if k not in ("decision_id", "fingerprint", "journal")})[:24]
    return item


def _ordem(itens):
    """Por card; cards com UPDATE_CARD primeiro, depois HUMAN_REVIEW, depois ADD_SECONDARY."""
    prioridade = {}
    for it in itens:
        prioridade[it["uid"]] = min(prioridade.get(it["uid"], 9), ORDEM[it["pacote"]])
    bloco = lambda b: (0, b, "") if isinstance(b, int) else (1, 0, str(b))  # noqa: E731  (blocos do discovery, depois "novos")
    return lambda it: (prioridade[it["uid"]], bloco(it["bloco"]), it["uid"], ORDEM[it["pacote"]], it["_seq"])


# ---------------------------------------------------------------- decisões (arquivo separado do state)
class Decisoes:
    def __init__(self, caminho: pathlib.Path = DECISOES, state: pathlib.Path = STATE):
        caminho = pathlib.Path(caminho).resolve()
        if pathlib.Path(state).resolve() in caminho.parents:
            raise ValueError("o arquivo de decisões não pode ficar dentro do state do discovery/delta")
        self.caminho = caminho
        self.historico = caminho.with_name("history.jsonl")
        self.trava = threading.Lock()

    def ler(self) -> dict:
        if not self.caminho.exists():
            return {"schema": SCHEMA, "decisions": {}}
        dados = _ler(self.caminho)
        if dados.get("schema") != SCHEMA or not isinstance(dados.get("decisions"), dict):
            raise ValueError(f"{self.caminho}: schema inesperado")
        return dados

    def registrar(self, item: dict, decisao: str, comentario: str = "", agora: str | None = None) -> dict:
        if decisao not in VALIDAS:
            raise ValueError(f"decisão inválida: {decisao!r}")
        if not isinstance(comentario, str) or len(comentario) > MAX_COMENTARIO:
            raise ValueError("comentário inválido")
        agora = agora or datetime.datetime.now().astimezone().isoformat(timespec="seconds")
        with self.trava:
            dados = self.ler()
            antes = dados["decisions"].get(item["decision_id"])
            reg = {
                "decision_id": item["decision_id"], "uid": item["uid"], "trial": item.get("trial"), "bloco": item["bloco"],
                "publication": {"id": item["pub"], "pmid": item.get("pmid"), "doi": item.get("doi"), "title": item.get("title")},
                "action": item["pacote"], "original_action": item.get("acao_original"),
                "delta_id": item.get("delta_id"), "field_path": item.get("field_path"), "item_id": item.get("item_id"),
                "pipeline": item.get("pipeline"), "cand_id": item.get("cand_id"),
                "registry_ids": item.get("registry_ids"), "decision": decisao, "comment": comentario.strip(),
                "reviewed_at": agora, "fingerprint": item["fingerprint"],
                "revision": (antes or {}).get("revision", 0) + 1,
            }
            dados["decisions"][item["decision_id"]] = reg
            self.caminho.parent.mkdir(parents=True, exist_ok=True)
            fd, tmp = tempfile.mkstemp(dir=self.caminho.parent, prefix=".decisions-", suffix=".json")
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(dados, fh, ensure_ascii=False, indent=1, sort_keys=True)
            os.replace(tmp, self.caminho)
            with self.historico.open("a", encoding="utf-8") as fh:      # append-only
                fh.write(json.dumps({"at": agora, "decision_id": reg["decision_id"], "decision": decisao,
                                     "comment": reg["comment"], "fingerprint": reg["fingerprint"],
                                     "previous": (antes or {}).get("decision"),
                                     "previous_fingerprint": (antes or {}).get("fingerprint")},
                                    ensure_ascii=False) + "\n")
            return reg


def status(item: dict, reg: dict | None) -> str:
    if not reg:
        return "PENDING"
    if reg.get("fingerprint") != item["fingerprint"]:
        return "STALE"
    return reg["decision"]


def visao(state: pathlib.Path, data_js: pathlib.Path, dec: Decisoes) -> dict:
    carga = carregar_itens(state, data_js)
    regs = dec.ler()["decisions"]
    ids = set()
    for it in carga["itens"]:
        ids.add(it["decision_id"])
        r = regs.get(it["decision_id"])
        it["status"] = status(it, r)
        it["registro"] = {k: r.get(k) for k in ("decision", "comment", "reviewed_at", "revision")} if r else None
    cont = {s: 0 for s in ("PENDING", "STALE") + VALIDAS}
    for it in carga["itens"]:
        cont[it["status"]] += 1
    return {"itens": carga["itens"], "meta": {
        "blocos": carga["blocos"], "contagens": cont, "total": len(carga["itens"]),
        "cards": len({i["uid"] for i in carga["itens"]}),
        "pacotes": len({(i["uid"], i["pacote"]) for i in carga["itens"]}),
        "orfas": sorted(set(regs) - ids), "arquivo_decisoes": _rel(dec.caminho)}}


def _rel(p: pathlib.Path) -> str:
    try:
        return str(p.relative_to(SITE))
    except ValueError:
        return str(p)


# ---------------------------------------------------------------- servidor HTTP (127.0.0.1, rotas fixas)
def _json_seguro(obj) -> bytes:
    """JSON sem '<', '>' e '&' literais: o conteúdo nunca vira HTML, nem por sniffing."""
    t = json.dumps(obj, ensure_ascii=False)
    return t.replace("&", "\\u0026").replace("<", "\\u003c").replace(">", "\\u003e").encode("utf-8")


CSP = ("default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self'; "
       "base-uri 'none'; form-action 'none'; frame-ancestors 'none'")


def criar_handler(state: pathlib.Path, data_js: pathlib.Path, dec: Decisoes, porta: int):
    hosts = {f"127.0.0.1:{porta}", f"localhost:{porta}"}
    origens = {f"http://{h}" for h in hosts}

    class Handler(http.server.BaseHTTPRequestHandler):
        server_version = "TheraTrialsReviewCenter"
        sys_version = ""

        def log_message(self, fmt, *args):         # silencioso, exceto erros
            pass

        def _enviar(self, codigo: int, corpo: bytes, tipo: str = "application/json; charset=utf-8"):
            self.send_response(codigo)
            self.send_header("Content-Type", tipo)
            self.send_header("Content-Length", str(len(corpo)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Content-Security-Policy", CSP)
            self.end_headers()
            self.wfile.write(corpo)

        def _erro(self, codigo: int, msg: str):
            self._enviar(codigo, _json_seguro({"ok": False, "erro": msg}))

        def _host_ok(self) -> bool:
            return self.headers.get("Host", "") in hosts      # bloqueia DNS rebinding

        def do_GET(self):
            if not self._host_ok():
                return self._erro(403, "host não permitido")
            rota = urllib.parse.urlsplit(self.path).path
            if rota in ESTATICOS:
                nome, tipo = ESTATICOS[rota]
                return self._enviar(200, (WEB / nome).read_bytes(), tipo)
            if rota == "/favicon.ico":                  # sem ícone: 204 evita erro no console
                self.send_response(204); self.send_header("Content-Length", "0"); self.end_headers()
                return None
            if rota == "/api/items":
                try:
                    return self._enviar(200, _json_seguro(visao(state, data_js, dec)))
                except Exception as e:  # noqa: BLE001
                    return self._erro(500, f"falha ao ler os outputs: {type(e).__name__}: {e}")
            return self._erro(404, "rota inexistente")

        def do_POST(self):
            if not self._host_ok():
                return self._erro(403, "host não permitido")
            if self.headers.get("Origin") and self.headers["Origin"] not in origens:
                return self._erro(403, "origem não permitida")
            if self.headers.get("X-Review-Center") != "1":
                return self._erro(403, "cabeçalho X-Review-Center ausente")
            if urllib.parse.urlsplit(self.path).path != "/api/decision":
                return self._erro(404, "rota inexistente")
            if not (self.headers.get("Content-Type") or "").startswith("application/json"):
                return self._erro(415, "use application/json")
            n = int(self.headers.get("Content-Length") or 0)
            if n <= 0 or n > MAX_CORPO:
                return self._erro(413, "corpo ausente ou grande demais")
            try:
                pedido = json.loads(self.rfile.read(n).decode("utf-8"))
                assert isinstance(pedido, dict)
            except Exception:  # noqa: BLE001
                return self._erro(400, "JSON inválido")
            itens = {i["decision_id"]: i for i in carregar_itens(state, data_js)["itens"]}
            item = itens.get(pedido.get("decision_id"))
            if not item:
                return self._erro(404, "item inexistente")
            if pedido.get("fingerprint") != item["fingerprint"]:
                return self._erro(409, "o item mudou desde que a página foi carregada: recarregue e revise de novo")
            try:
                reg = dec.registrar(item, pedido.get("decision"), pedido.get("comment") or "")
            except ValueError as e:
                return self._erro(400, str(e))
            return self._enviar(200, _json_seguro({"ok": True, "registro": reg, "status": status(item, reg)}))

        def _metodo_nao_permitido(self):
            self._erro(405, "método não permitido")

        do_PUT = do_DELETE = do_PATCH = _metodo_nao_permitido

    return Handler


def criar_servidor(porta: int = PORTA, state: pathlib.Path = STATE, data_js: pathlib.Path = DATA_JS,
                   decisoes: pathlib.Path = DECISOES) -> http.server.ThreadingHTTPServer:
    dec = Decisoes(decisoes, state)
    srv = http.server.ThreadingHTTPServer((HOST, porta), http.server.BaseHTTPRequestHandler)
    srv.RequestHandlerClass = criar_handler(state, data_js, dec, srv.server_address[1])   # porta real (0 nos testes)
    srv.daemon_threads = True
    return srv


def main(argv=None):
    ap = argparse.ArgumentParser(description="Review Center editorial (local, 127.0.0.1)")
    ap.add_argument("--porta", type=int, default=PORTA)
    ap.add_argument("--state", type=pathlib.Path, default=STATE, help="pasta state (somente leitura)")
    ap.add_argument("--decisoes", type=pathlib.Path, default=DECISOES, help="arquivo de decisões")
    a = ap.parse_args(argv)
    srv = criar_servidor(a.porta, a.state, DATA_JS, a.decisoes)
    v = visao(a.state, DATA_JS, Decisoes(a.decisoes, a.state))
    m = v["meta"]
    print(f"Review Center: http://{HOST}:{a.porta}")
    print(f"  {m['total']} itens · {m['cards']} cards · {m['pacotes']} pacotes · blocos {m['blocos']}")
    print(f"  decisões: {m['arquivo_decisoes']}  (pendentes {m['contagens']['PENDING']}, stale {m['contagens']['STALE']})")
    print("  Ctrl+C encerra. Nada aqui altera data.js, secondary-cards.js ou o state.")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()


if __name__ == "__main__":
    sys.exit(main())
