"""Testes do Review Center (scripts/db_v2/review_center.py). Sem LLM e sem rede externa.

    cd scripts/db_v2/agents && python3 -m unittest discover -s tests

O que grava usa um state sintético e um arquivo de decisões temporário. Os dados reais dos blocos são só lidos
(testes pulados quando o state local não existe, como no CI).
"""
from __future__ import annotations

import hashlib
import http.client
import json
import pathlib
import sys
import tempfile
import threading
import unittest

AG = pathlib.Path(__file__).resolve().parents[1]
V2 = AG.parent
sys.path.insert(0, str(V2))
import review_center as RC  # noqa: E402

SITE = V2.parent.parent
DATA_JS = SITE / "assets" / "js" / "data.js"
SECUNDARIOS = SITE / "assets" / "js" / "secondary-cards.js"
ESTADO_REAL = V2 / "state"
TEM_REAL = all((ESTADO_REAL / "discovery" / f"fila_humana_bloco{b}.json").exists() for b in (1, 2, 3, 4))


def sha_arquivo(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def sha_pasta(p: pathlib.Path) -> str:
    h = hashlib.sha256()
    for f in sorted(x for x in p.rglob("*") if x.is_file()):
        h.update(str(f.relative_to(p)).encode()); h.update(f.read_bytes())
    return h.hexdigest()


def _w(p: pathlib.Path, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")


EV = [{"source_id": "pmid:111:abstract", "locator": "¶0004 [Abstract]", "snippet": "hypertension (125 [21%]) ... hypokalaemia (70 [12%])"}]


def montar_state(raiz: pathlib.Path, titulo_add: str = "Dosimetry substudy of TESTE-1", proposto: str = "Hipertensão G3+ (21%)"):
    st = raiz / "state"
    comp = {"population": {"status": "different", "note": "só tratados"}, "endpoint": {"status": "different", "note": "dose-resposta"}}
    linha = lambda pmid, rel, acao, final="PASS", **kw: {  # noqa: E731
        "uid": "u1", "trial": "TESTE-1 (2020)", "pmid": pmid, "doi": f"10.1000/x{pmid}", "title": kw.pop("title", f"Pub {pmid}"),
        "date": "2024/01/01", "relation": rel, "action": acao, "origin": "llm", "reason": kw.pop("reason", f"motivo {pmid}"),
        "comparison": comp, "signature": {"candidate": {"population": "pop cand", "endpoint": "OS", "analysis_type": "final"}},
        "curator_checks": kw.pop("checks", []), "curator_verdict": "PASS", "verifier_verdict": final, "verifier_reason": f"ver {pmid}",
        "final_verdict": final, "evidence": EV, "temporal_marker": None, "relation_by_signature": [rel, ""], **kw}
    rows = [linha("111", "LONG_TERM_FOLLOWUP", "UPDATE_CARD"),
            linha("222", "SECONDARY_ANALYSIS", "ADD_SECONDARY", title=titulo_add),
            linha("333", "UNDETERMINED", "HUMAN_REVIEW", reason="não dá para saber se é a mesma coorte"),
            linha("444", "SECONDARY_ANALYSIS", "STORE_SOURCE", final="FAIL"),
            linha("555", "PROTOCOL", "STORE_SOURCE")]
    compacto = lambda r: {k: r.get(k) for k in ("pmid", "doi", "title", "date", "relation", "action", "final_verdict",  # noqa: E731
                                                "temporal_marker", "verifier_reason")}
    _w(st / "discovery" / "relatorio_bloco9.json", {"rows": rows})
    _w(st / "discovery" / "fila_humana_bloco9.json", {"cards": {"u1": {"trial": "TESTE-1 (2020)", "pacotes": {
        "UPDATE_CARD": [compacto(rows[0])], "ADD_SECONDARY": [compacto(rows[1])],
        "HUMAN_REVIEW": [compacto(rows[2]), compacto(rows[3])]}}}, "resumo": {}})
    _w(st / "discovery" / "u1" / "packet.json", {"candidates": [{"pmid": "222", "doi": "10.1000/x222", "journal": "Radiology"}]})
    _w(st / "discovery" / "u1" / "estado.json", {"compat": {"pipeline_version": "discovery/3+teste"}})
    item = lambda fp, dec, cur, prop, **kw: {  # noqa: E731
        "delta_id": "u1__111", "uid": "u1", "pmid": "111", "doi": "10.1000/x111", "field_path": fp, "endpoint": "G≥3",
        "decision": dec, "current": cur, "proposed": prop, "reason": "corte final", "human_review_reason": kw.get("hr"),
        "source": EV if dec == "DELTA" else [], "deterministic_verdict": "PASS", "deterministic_checks": [],
        "verifier_verdict": "PASS", "verifier_reason": "ok", "final_verdict": "PASS", "safe_delta": dec == "DELTA"}
    deltas = [item("tox_g3", "DELTA", "Hipertensão G3+ (20%)", proposto),
              item("tox_g3", "DELTA", "hipocalemia (10%)", "hipocalemia (12%)"),
              item("secundario", "HUMAN_REVIEW", None, None, hr="a frase sobre a análise final fica desatualizada")]
    _w(st / "delta" / "relatorio_bloco9.json", {"delta_version": "delta/1+teste", "updates": [
        {"delta_id": "u1__111", "uid": "u1", "pmid": "111", "status": "HUMAN_REVIEW", "notes_for_human": "nota"}], "deltas": deltas})
    _w(st / "delta" / "u1__111" / "curator.json", {"items": [{"item_id": "d01_hta", "field_path": "tox_g3"},
                                                             {"item_id": "d02_k", "field_path": "tox_g3"},
                                                             {"item_id": "d03_hr", "field_path": "secundario"}]})
    _w(st / "delta" / "u1__111" / "packet.json", {"card_fields": {"tox_g3": "Hipertensão G3+ (20%), hipocalemia (10%)."}})
    dj = raiz / "data.js"
    dj.write_text("/* teste */\nwindow.THERA_DATA = " + json.dumps({"studies": [
        {"uid": "u1", "estudo": "TESTE-1 (2020)", "tox_g3": "Hipertensão G3+ (20%), hipocalemia (10%).", "secundario": "OS interina."}]}) + ";\n",
        encoding="utf-8")
    return st, dj


def montar_novos(st: pathlib.Path, resultado: str = "DFS HR 0,68"):
    """Fixture do pipeline novos: NEW_CARD atual, saída de versão antiga, ARROW/NIPU (identidade), RELATED e HR."""
    nd = st / "novos"
    v = RC._versao_novos()
    cand = lambda cid, classe="NEW_STUDY_CANDIDATE", pre=None, uid=None, **kw: {  # noqa: E731
        "cand_id": cid, "nct": None if cid.startswith("pmid") else cid, "title": kw.pop("title", f"Trial {cid} in cancer"),
        "acronym": kw.pop("acronym", None), "phases": ["PHASE3"], "status": "COMPLETED", "pmids": kw.pop("pmids", []),
        "dois": [], "conditions": ["Bladder Cancer"], "tumor_groups": ["urotelial"],
        "dedup": {"classe": classe, "motivo": f"motivo {classe}", "uid": uid, "dicas": []}, "pre_action": pre,
        "pre_reason": kw.pop("pre_reason", None), **kw}
    tri = [cand("NCT07000001", acronym="POTOMAX"), cand("NCT07000002"),
           cand("pmid41779000", "POSSIBLE_DUPLICATE", "HUMAN_REVIEW", "NCT07000001", pmids=["41779000"],
                title="131I-LNTH-1095 plus enzalutamide", pre_reason="compatível com o ensaio NCT07000001"),
           cand("NCT07000003", pre="WATCH", acronym="NIPUX"),
           cand("pmid38447379", "POSSIBLE_DUPLICATE", "HUMAN_REVIEW", "NCT07000003", pmids=["38447379"],
                title="UV1 vaccine with ipilimumab and nivolumab", pre_reason="o resumo cita NIPUX"),
           cand("NCT07000004", "RELATED_TO_EXISTING", "RELATED_TO_EXISTING", "u1", title="China extension of TESTE-1"),
           cand("NCT07000005"), cand("NCT07000006")]
    _w(nd / "triagem.json", {"candidatos": tri})
    ev = [{"source_id": "pmid:1:abstract", "source_type": "pubmed_abstract", "locator": "¶0002", "snippet": "DFS HR 0.68"}]

    def llm(cid, acao, versao, final="PASS"):
        _w(nd / cid / "packet.json", {"candidate": {"nct": cid, "conditions": ["Bladder Cancer"]}})
        _w(nd / cid / "curator.json", {"action": acao, "study": f"Estudo {cid}", "main_publication": {"pmid": "1", "doi": "10.1/x"},
                                       "tumor": "NMIBC", "intervention": "Droga A", "comparator": "BCG", "phase": "fase 3",
                                       "primary_endpoint": "DFS", "main_result": resultado, "maturity": "published_primary",
                                       "reason": "acrescenta cobertura", "policy_basis": "fase3_pergunta_nao_representada",
                                       "comparison_type": "randomizado_vs_padrao", "evidence": ev, "_sha256": "c", "_erros": [],
                                       "_deterministico": {"verdict": "PASS", "achados": []}})
        _w(nd / cid / "verifier.json", {"verdict": final, "reason": "confere", "_erros": []})
        _w(nd / cid / "estado.json", {"compat": {"novos_version": versao}, "etapas": {
            k: {"ok": True} for k in ("preparar", "curator", "verifier")}})
    llm("NCT07000001", "NEW_CARD", v)
    llm("NCT07000002", "NEW_CARD", "novos/0+antiga")          # versão antiga: não entra
    llm("NCT07000005", "HUMAN_REVIEW", v)
    llm("NCT07000006", "NO_ACTION", v)                         # NO_ACTION + PASS: não entra


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.raiz = pathlib.Path(self.tmp.name)
        self.st, self.dj = montar_state(self.raiz)
        self.dec = RC.Decisoes(self.raiz / "review" / "decisions.json", self.st)

    def tearDown(self):
        self.tmp.cleanup()

    def itens(self, **kw):
        return RC.carregar_itens(self.st, self.dj)["itens"]

    def por(self, **filtro):
        return [i for i in self.itens() if all(i.get(k) == v for k, v in filtro.items())]


class Leitura(Base):
    def test_update_card_vira_um_item_por_trecho_do_delta(self):
        ups = self.por(pacote="UPDATE_CARD")
        self.assertEqual([(i["tipo"], i["field_path"], i["item_id"]) for i in ups],
                         [("delta", "tox_g3", "d01_hta"), ("delta", "tox_g3", "d02_k"), ("delta_hr", "secundario", "d03_hr")])
        d = ups[0]
        self.assertEqual((d["current"], d["proposed"]), ("Hipertensão G3+ (20%)", "Hipertensão G3+ (21%)"))
        self.assertEqual(d["source"][0]["snippet"], EV[0]["snippet"])
        self.assertTrue(d["safe_delta"]) and self.assertTrue(d["trecho_presente_hoje"])
        self.assertEqual(d["relation"], "LONG_TERM_FOLLOWUP")
        self.assertEqual(RC.pior("CONFLICT", "PASS"), "CONFLICT")       # veredito do item = pior(discovery, delta)
        self.assertEqual(RC.pior("PASS", "UNSUPPORTED"), "UNSUPPORTED")
        self.assertEqual(d["pipeline"], {"discovery": "discovery/3+teste", "delta": "delta/1+teste"})
        hr = ups[2]
        self.assertIsNone(hr["proposed"])            # revisão humana do delta não traz texto clínico
        self.assertIn("desatualizada", hr["human_review_reason"])
        for i in ups:                                # nunca o card inteiro
            self.assertNotIn("card_rewrite", i)
            if i["proposed"]:
                self.assertLess(len(i["proposed"]), len(i["campo_hoje"]))

    def test_add_secondary(self):
        (a,) = self.por(pacote="ADD_SECONDARY")
        self.assertEqual((a["tipo"], a["pmid"], a["journal"], a["relation"]), ("add_secondary", "222", "Radiology", "SECONDARY_ANALYSIS"))
        self.assertEqual(a["signature"]["population"], "pop cand")
        self.assertEqual(a["comparison"]["endpoint"]["note"], "dose-resposta")
        self.assertTrue(a["evidence"] and a["reason"] and a["verifier_reason"])

    def test_human_review_inclui_acao_humana_e_itens_sem_pass(self):
        hrs = self.por(pacote="HUMAN_REVIEW")
        self.assertEqual({(i["pmid"], i["acao_original"], i["verdict"]) for i in hrs},
                         {("333", "HUMAN_REVIEW", "PASS"), ("444", "STORE_SOURCE", "FAIL")})
        self.assertIn("mesma coorte", [i for i in hrs if i["pmid"] == "333"][0]["reason"])
        self.assertIn("Veredito final do discovery: FAIL", [i for i in hrs if i["pmid"] == "444"][0]["avisos"])
        self.assertFalse(self.por(pmid="555"))       # STORE_SOURCE + PASS não entra na fila

    def test_ordem_padrao_update_human_review_add(self):
        self.assertEqual([i["pacote"] for i in self.itens()][:4], ["UPDATE_CARD"] * 3 + ["HUMAN_REVIEW"])
        self.assertEqual(self.itens()[-1]["pacote"], "ADD_SECONDARY")

    def test_decision_id_estavel_e_unico(self):
        a, b = self.itens(), self.itens()
        self.assertEqual([i["decision_id"] for i in a], [i["decision_id"] for i in b])
        self.assertEqual([i["fingerprint"] for i in a], [i["fingerprint"] for i in b])
        self.assertEqual(len({i["decision_id"] for i in a}), len(a))
        self.assertEqual(RC.decision_id("u1", "pmid:111", "UPDATE_CARD", "tox_g3", "d01_hta"),
                         RC.decision_id("u1", "pmid:111", "UPDATE_CARD", "tox_g3", "d01_hta"))

    def test_card_mudado_gera_aviso(self):
        self.dj.write_text(self.dj.read_text().replace("(20%)", "(22%)"), encoding="utf-8")
        d = self.por(item_id="d01_hta")[0]
        self.assertFalse(d["trecho_presente_hoje"])
        self.assertTrue(any("não está mais no data.js" in a for a in d["avisos"]))


class Novos(Base):
    def setUp(self):
        super().setUp()
        montar_novos(self.st)

    def novos(self):
        return {i["cand_id"]: i for i in self.itens() if i["bloco"] == "novos"}

    def test_carrega_new_card_e_exclui_versao_antiga_e_no_action(self):
        n = self.novos()
        self.assertEqual(set(n), {"NCT07000001", "pmid41779000", "pmid38447379", "NCT07000004", "NCT07000005"})
        nc = n["NCT07000001"]
        self.assertEqual((nc["pacote"], nc["tipo"], nc["registry_ids"], nc["main_result"]),
                         ("NEW_CARD", "novo_card", ["NCT07000001"], "DFS HR 0,68"))
        self.assertEqual(nc["pipeline"], {"novos": RC._versao_novos()})
        self.assertTrue(any("MESMO estudo" in a for a in nc["avisos"]))       # ARROW aponta para ele
        self.assertEqual((n["NCT07000005"]["pacote"], n["NCT07000005"]["tipo"]), ("HUMAN_REVIEW", "novo_revisao"))

    def test_arrow_e_nipu_sao_identidade_nunca_new_card(self):
        n = self.novos()
        for cid, alvo in (("pmid41779000", "NCT07000001"), ("pmid38447379", "NCT07000003")):
            self.assertEqual((n[cid]["pacote"], n[cid]["tipo"]), ("HUMAN_REVIEW", "novo_identidade"))
            self.assertEqual(n[cid]["identidade"]["classe"], "POSSIBLE_DUPLICATE")
            self.assertEqual(n[cid]["identidade"]["relacionado"]["id"], alvo)
        self.assertEqual(sum(1 for i in n.values() if i["pacote"] == "NEW_CARD"), 1)

    def test_related_mostra_o_card(self):
        r = self.novos()["NCT07000004"]
        self.assertEqual((r["pacote"], r["identidade"]["classe"]), ("HUMAN_REVIEW", "RELATED_TO_EXISTING"))
        self.assertEqual(r["identidade"]["relacionado"], {"tipo": "card", "id": "u1", "nome": "TESTE-1 (2020)"})

    def test_publicacao_compartilhada_aponta_um_para_o_outro(self):
        n = self.novos()                     # NCT07000001 e NCT07000005 citam o mesmo PMID 1 / DOI 10.1/x na fixture
        a, b = n["NCT07000001"]["publicacao_compartilhada"], n["NCT07000005"]["publicacao_compartilhada"]
        self.assertEqual(a["chaves"], ["doi:10.1/x", "pmid:1"])
        self.assertEqual([c["cand_id"] for c in a["candidatos"]], ["NCT07000005"])
        self.assertEqual([c["cand_id"] for c in b["candidatos"]], ["NCT07000001"])
        self.assertEqual(a["candidatos"][0]["decision_id"], n["NCT07000005"]["decision_id"])
        self.assertEqual((n["NCT07000001"]["pacote"], n["NCT07000005"]["pacote"]), ("NEW_CARD", "HUMAN_REVIEW"))  # nada muda
        for cid in ("pmid41779000", "pmid38447379", "NCT07000004"):           # publicações próprias: sem alerta
            self.assertNotIn("publicacao_compartilhada", n[cid])

    def test_ordem_update_new_card_human_review_add(self):
        ordem = [i["pacote"] for i in self.itens()]
        self.assertLess(ordem.index("UPDATE_CARD"), ordem.index("NEW_CARD"))
        prim_novos = [i["pacote"] for i in self.itens() if i["bloco"] == "novos"]
        self.assertEqual(prim_novos[0], "NEW_CARD")
        self.assertEqual(RC.ORDEM, {"UPDATE_CARD": 0, "NEW_CARD": 1, "HUMAN_REVIEW": 2, "ADD_SECONDARY": 3})

    def test_decisoes_new_card_persistencia_stale_e_nada_aplicado(self):
        antes = (sha_pasta(self.st), sha_arquivo(DATA_JS), sha_arquivo(SECUNDARIOS))
        it = self.novos()["NCT07000001"]
        for d in RC.VALIDAS:
            reg = self.dec.registrar(it, d, "c")
        salvo = RC.Decisoes(self.dec.caminho, self.st).ler()["decisions"][it["decision_id"]]
        self.assertEqual((salvo["action"], salvo["cand_id"], salvo["registry_ids"], salvo["decision"], salvo["revision"]),
                         ("NEW_CARD", "NCT07000001", ["NCT07000001"], "DEFER", 3))
        self.assertEqual(salvo["pipeline"], {"novos": RC._versao_novos()})
        self.assertEqual(salvo["publication"]["pmid"], "1")
        self.assertEqual(antes, (sha_pasta(self.st), sha_arquivo(DATA_JS), sha_arquivo(SECUNDARIOS)))
        montar_novos(self.st, resultado="DFS HR 0,70")                   # o item mudou → STALE
        v = RC.visao(self.st, self.dj, self.dec)
        self.assertEqual([i["status"] for i in v["itens"] if i["decision_id"] == it["decision_id"]], ["STALE"])

    def test_decision_id_estavel(self):
        self.assertEqual(self.novos()["NCT07000001"]["decision_id"], self.novos()["NCT07000001"]["decision_id"])
        self.assertEqual(self.novos()["NCT07000001"]["decision_id"],
                         RC.decision_id("novos:NCT07000001", "cand:NCT07000001", "NEW_CARD"))


class Decisoes(Base):
    def test_approve_reject_defer_mudanca_persistencia_e_historico(self):
        it = self.itens()[0]
        for d in RC.VALIDAS:
            reg = self.dec.registrar(it, d, f"comentário {d}")
            self.assertEqual(reg["decision"], d)
        self.assertEqual(reg["revision"], 3)
        novo = RC.Decisoes(self.dec.caminho, self.st).ler()["decisions"][it["decision_id"]]   # persistiu
        self.assertEqual((novo["decision"], novo["comment"], novo["fingerprint"]), ("DEFER", "comentário DEFER", it["fingerprint"]))
        for k in ("uid", "publication", "action", "delta_id", "field_path", "pipeline", "reviewed_at", "item_id"):
            self.assertIn(k, novo)
        hist = [json.loads(x) for x in self.dec.historico.read_text().splitlines()]
        self.assertEqual([h["decision"] for h in hist], ["APPROVE", "REJECT", "DEFER"])
        self.assertEqual([h["previous"] for h in hist], [None, "APPROVE", "REJECT"])
        self.assertEqual(RC.status(it, novo), "DEFER")

    def test_decisao_invalida(self):
        it = self.itens()[0]
        for ruim in ("APPLY", "approve", "", None):
            with self.assertRaises(ValueError):
                self.dec.registrar(it, ruim)
        with self.assertRaises(ValueError):
            self.dec.registrar(it, "APPROVE", "x" * (RC.MAX_COMENTARIO + 1))
        self.assertFalse(self.dec.caminho.exists())

    def test_stale_quando_o_item_muda(self):
        it = self.por(item_id="d01_hta")[0]
        self.dec.registrar(it, "APPROVE")
        self.tmp2 = self.st
        montar_state(self.raiz, proposto="Hipertensão G3+ (21%; IC95% novo)")      # novo run muda o proposto
        novo = self.por(item_id="d01_hta")[0]
        self.assertEqual(novo["decision_id"], it["decision_id"])
        self.assertNotEqual(novo["fingerprint"], it["fingerprint"])
        v = RC.visao(self.st, self.dj, self.dec)
        self.assertEqual([i["status"] for i in v["itens"] if i["decision_id"] == it["decision_id"]], ["STALE"])
        self.assertEqual(v["meta"]["contagens"]["STALE"], 1)

    def test_arquivo_de_decisoes_nunca_dentro_do_state(self):
        with self.assertRaises(ValueError):
            RC.Decisoes(self.st / "review" / "decisions.json", self.st)
        self.assertNotIn(RC.STATE.resolve(), RC.DECISOES.resolve().parents)

    def test_state_e_dados_publicados_intactos(self):
        antes = (sha_pasta(self.st), sha_arquivo(DATA_JS), sha_arquivo(SECUNDARIOS))
        for it in self.itens():
            self.dec.registrar(it, "DEFER", "teste")
        RC.visao(self.st, DATA_JS, self.dec)
        self.assertEqual(antes, (sha_pasta(self.st), sha_arquivo(DATA_JS), sha_arquivo(SECUNDARIOS)))


class Servidor(Base):
    def setUp(self):
        super().setUp()
        self.srv = RC.criar_servidor(0, self.st, self.dj, self.raiz / "review" / "decisions.json")
        self.porta = self.srv.server_address[1]
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()

    def tearDown(self):
        self.srv.shutdown(); self.srv.server_close()
        super().tearDown()

    def req(self, metodo, rota, corpo=None, headers=None, host=None):
        c = http.client.HTTPConnection("127.0.0.1", self.porta, timeout=10)
        h = {"Host": host or f"127.0.0.1:{self.porta}", **(headers or {})}
        dados = json.dumps(corpo).encode() if corpo is not None else None
        if dados is not None:
            h.setdefault("Content-Type", "application/json")
        c.request(metodo, rota, body=dados, headers=h)
        r = c.getresponse()
        return r.status, dict(r.getheaders()), r.read()

    def post(self, corpo, **kw):
        return self.req("POST", "/api/decision", corpo, {"X-Review-Center": "1", **kw.pop("headers", {})}, **kw)

    def test_so_localhost(self):
        self.assertEqual(RC.HOST, "127.0.0.1")
        self.assertEqual(self.srv.server_address[0], "127.0.0.1")
        with self.assertRaises(SystemExit):
            RC.main(["--host", "0.0.0.0"])
        self.assertEqual(self.req("GET", "/api/items", host="evil.example:80")[0], 403)
        self.assertEqual(self.req("GET", "/", host=f"localhost:{self.porta}")[0], 200)

    def test_rotas_fixas_e_path_traversal_bloqueado(self):
        st, h, corpo = self.req("GET", "/")
        self.assertEqual(st, 200)
        self.assertIn("default-src 'none'", h["Content-Security-Policy"])
        self.assertEqual(h["X-Content-Type-Options"], "nosniff")
        for rota in ("/../review_center.py", "/%2e%2e/state/discovery/relatorio_bloco9.json", "/app.js/../../data.js",
                     "/state/discovery/relatorio_bloco9.json", "/review/decisions.json", "/..%2f..%2fassets/js/data.js",
                     "/review_center_web/app.js", "//etc/passwd"):
            self.assertEqual(self.req("GET", rota)[0], 404, rota)
        self.assertEqual(self.req("PUT", "/api/decision", {})[0], 405)
        self.assertEqual(self.req("DELETE", "/api/decision")[0], 405)

    def test_decisao_pela_api(self):
        it = json.loads(self.req("GET", "/api/items")[2])["itens"][0]
        ok = {"decision_id": it["decision_id"], "fingerprint": it["fingerprint"], "decision": "APPROVE", "comment": "ok"}
        self.assertEqual(self.req("POST", "/api/decision", ok)[0], 403)                          # sem cabeçalho
        self.assertEqual(self.post(ok, headers={"Origin": "http://evil.example"})[0], 403)       # outra origem
        self.assertEqual(self.post({**ok, "fingerprint": "velho"})[0], 409)                     # item mudou
        self.assertEqual(self.post({**ok, "decision": "APPLY"})[0], 400)
        self.assertEqual(self.post({**ok, "decision_id": "rc1-inexistente"})[0], 404)
        st, _, corpo = self.post(ok, headers={"Origin": f"http://127.0.0.1:{self.porta}"})
        self.assertEqual(st, 200, corpo)
        self.assertEqual(json.loads(corpo)["status"], "APPROVE")
        v = json.loads(self.req("GET", "/api/items")[2])
        self.assertEqual(v["meta"]["contagens"]["APPROVE"], 1)

    def test_conteudo_nao_vira_html(self):
        montar_state(self.raiz, titulo_add='<script>alert(1)</script><img src=x onerror=alert(2)>')
        st, h, corpo = self.req("GET", "/api/items")
        self.assertTrue(h["Content-Type"].startswith("application/json"))
        self.assertNotIn(b"<script", corpo)
        self.assertNotIn(b"<img", corpo)
        titulos = [i["title"] for i in json.loads(corpo)["itens"]]
        self.assertIn('<script>alert(1)</script><img src=x onerror=alert(2)>', titulos)    # preservado como texto
        js = (RC.WEB / "app.js").read_text(encoding="utf-8")
        for proibido in ("innerHTML", "outerHTML", "insertAdjacentHTML", "document.write", "eval(", "new Function"):
            self.assertNotIn(proibido, js)

    def test_sem_llm_rede_ou_shell(self):
        codigo = pathlib.Path(RC.__file__).read_text(encoding="utf-8")
        for proibido in ("subprocess", "run_agents", "urlopen", "urllib.request", "os.system", "anthropic", "requests"):
            self.assertNotIn(proibido, codigo)
        js = (RC.WEB / "app.js").read_text(encoding="utf-8")
        self.assertEqual(sorted(set(__import__("re").findall(r'fetch\("([^"]+)"', js))), ["/api/decision", "/api/items"])


def reescrever_data_js(dj: pathlib.Path, mutar):
    txt = dj.read_text(encoding="utf-8")
    i = txt.index("window.THERA_DATA = ")
    obj = json.loads(txt[i + len("window.THERA_DATA = "):].strip().rstrip(";"))
    mutar(obj)
    dj.write_text(txt[:i] + "window.THERA_DATA = " + json.dumps(obj) + ";\n", encoding="utf-8")


class Bloqueios(Base):
    """Migração estrutural: card que virou família → OBSOLETE; delta cujo trecho ATUAL sumiu → STALE.
    Os dois bloqueiam APPROVE e ficam fora do fingerprint."""

    def deltas(self):
        return {i["item_id"]: i for i in self.itens() if i["tipo"] == "delta"}

    def test_current_inalterado_fica_ativo(self):
        for it in self.deltas().values():
            self.assertNotIn("bloqueio", it)
        self.assertEqual(RC.status(self.deltas()["d01_hta"], None), "PENDING")

    def test_current_alterado_vira_STALE_so_no_item_afetado(self):
        reescrever_data_js(self.dj, lambda o: o["studies"][0].update(tox_g3="Hipertensão G3+ (25%), hipocalemia (10%)."))
        d = self.deltas()
        self.assertEqual(d["d01_hta"]["bloqueio"]["tipo"], "STALE")
        self.assertNotIn("bloqueio", d["d02_k"])                  # o outro trecho continua idêntico
        self.assertEqual(RC.status(d["d01_hta"], None), "STALE")

    def test_uid_aposentado_vira_OBSOLETE_com_a_familia(self):
        reescrever_data_js(self.dj, lambda o: o.update(studies=[], families=[
            {"family_id": "teste", "family_name": "TESTE", "legacy_uids": ["u1"]}]))
        u1 = [i for i in self.itens() if i["uid"] == "u1"]
        self.assertTrue(u1)
        for it in u1:
            self.assertEqual(it["bloqueio"]["tipo"], "OBSOLETE")
            self.assertEqual(it["bloqueio"]["motivo"], "SUPERSEDED BY STRUCTURAL MIGRATION")
            self.assertEqual(it["bloqueio"]["family"], {"family_id": "teste", "family_name": "TESTE"})
            self.assertEqual(RC.status(it, None), "OBSOLETE")
        v = RC.visao(self.st, self.dj, self.dec)
        self.assertEqual(v["meta"]["contagens"]["OBSOLETE"], len(u1))

    def test_aprovacao_antiga_nao_vale_em_item_bloqueado(self):
        reescrever_data_js(self.dj, lambda o: o["studies"][0].update(tox_g3="outro texto"))
        it = self.deltas()["d01_hta"]
        reg = {"fingerprint": it["fingerprint"], "decision": "APPROVE"}
        self.assertEqual(RC.status(it, reg), "STALE")
        self.assertEqual(RC.status(it, {**reg, "decision": "REJECT"}), "REJECT")

    def test_bloqueio_nao_altera_fingerprints(self):
        antes = {i["decision_id"]: i["fingerprint"] for i in self.itens()}
        # famílias novas que não aposentam uid de nenhum item: nenhum fingerprint muda
        reescrever_data_js(self.dj, lambda o: o.update(families=[{"family_id": "f", "family_name": "F", "legacy_uids": ["outro"]}]))
        self.assertEqual({i["decision_id"]: i["fingerprint"] for i in self.itens()}, antes)
        # bloquear() só acrescenta a marca: o fingerprint de cada item fica igual
        itens = self.itens()
        fps = [i["fingerprint"] for i in itens]
        RC.bloquear(itens, {"u1": {"family_id": "f", "family_name": "F"}})
        self.assertEqual([i["fingerprint"] for i in itens], fps)


class BloqueiosServidor(Base):
    req, post = Servidor.req, Servidor.post            # só os helpers HTTP, não os testes do Servidor

    def tearDown(self):
        self.srv.shutdown(); self.srv.server_close()
        Base.tearDown(self)

    def setUp(self):
        Base.setUp(self)
        reescrever_data_js(self.dj, lambda o: o["studies"][0].update(tox_g3="Hipertensão G3+ (25%), hipocalemia (10%)."))
        self.srv = RC.criar_servidor(0, self.st, self.dj, self.raiz / "review" / "decisions.json")
        self.porta = self.srv.server_address[1]
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()

    def test_servidor_recusa_APPROVE_em_STALE_e_aceita_REJECT(self):
        itens = json.loads(self.req("GET", "/api/items")[2])["itens"]
        it = next(i for i in itens if i.get("item_id") == "d01_hta")
        self.assertEqual(it["status"], "STALE")
        corpo = {"decision_id": it["decision_id"], "fingerprint": it["fingerprint"], "comment": ""}
        st, _, msg = self.post({**corpo, "decision": "APPROVE"})
        self.assertEqual(st, 409)
        self.assertIn("APPROVE bloqueado", json.loads(msg)["erro"])
        self.assertEqual(self.post({**corpo, "decision": "REJECT"})[0], 200)
        hist = (self.raiz / "review" / "history.jsonl").read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(hist), 1)                            # histórico só cresce; nada é apagado


class Compartilhadas(unittest.TestCase):
    """Regressão RELEVANCE: dois NCTs irmãos com a mesma publicação primária (PMID 30184451)."""

    def item(self, cid, pmid=None, doi=None, pacote="NEW_CARD"):
        it = {"cand_id": cid, "uid": f"novos:{cid}", "pub": f"cand:{cid}", "pacote": pacote, "acao_original": pacote,
              "registry_ids": [cid] if cid.startswith("NCT") else [], "trial": f"RELEVANCE {cid}", "pmid": pmid, "doi": doi,
              "verdict": "PASS"}
        return RC._fechar(it, RC.decision_id(it["uid"], it["pub"], pacote))

    def test_relevance_por_pmid_e_doi(self):
        a = self.item("NCT01476787", "30184451", "10.1056/NEJMoa1805104")
        b = self.item("NCT01650701", "30184451", "https://doi.org/10.1056/nejmoa1805104")
        c = self.item("NCT09999999", "11111111", "10.1/outro")
        so_doi = self.item("pmid22222222", "22222222", "doi:10.1056/NEJMOA1805104", "HUMAN_REVIEW")
        fps = [x["fingerprint"] for x in (a, b, c, so_doi)]
        RC.compartilhadas([a, b, c, so_doi])
        self.assertEqual(a["publicacao_compartilhada"]["chaves"], ["doi:10.1056/nejmoa1805104", "pmid:30184451"])
        self.assertEqual({x["cand_id"] for x in a["publicacao_compartilhada"]["candidatos"]}, {"NCT01650701", "pmid22222222"})
        self.assertEqual({x["cand_id"] for x in b["publicacao_compartilhada"]["candidatos"]}, {"NCT01476787", "pmid22222222"})
        self.assertEqual(so_doi["publicacao_compartilhada"]["chaves"], ["doi:10.1056/nejmoa1805104"])
        self.assertNotIn("publicacao_compartilhada", c)
        o = a["publicacao_compartilhada"]["candidatos"][0]
        self.assertTrue({"cand_id", "decision_id", "registry_ids", "trial", "pmid", "doi", "acao", "verdict", "pacote"} <= set(o))
        self.assertEqual([x["fingerprint"] for x in (a, b, c, so_doi)], fps)     # fora do fingerprint: nada fica STALE
        self.assertEqual((a["pacote"], b["pacote"]), ("NEW_CARD", "NEW_CARD"))  # não escolhe nem funde

    def test_mesmo_candidato_nao_conta_duas_vezes(self):
        a = self.item("NCT01476787", "30184451")
        RC.compartilhadas([a, self.item("NCT01476787", "30184451")])
        self.assertNotIn("publicacao_compartilhada", a)


@unittest.skipUnless((ESTADO_REAL / "novos" / "triagem.json").exists(), "state local do novos ausente (ex.: CI)")
class NovosReais(unittest.TestCase):
    def test_smoke_casos_do_piloto(self):
        n = {i["cand_id"]: i for i in RC.carregar_itens(ESTADO_REAL, DATA_JS)["itens"] if i["bloco"] == "novos"}
        for cid in ("NCT03528694", "NCT03836261", "NCT04685135", "pmid37866811"):     # POTOMAC, AMPLIFY, KRYSTAL-12, SAPPHIRE
            self.assertEqual(n[cid]["pacote"], "NEW_CARD", cid)
        for cid in ("NCT04625270", "NCT04934722"):                                   # RAMP 201, KEYNOTE-991 China
            self.assertEqual(n[cid]["pacote"], "HUMAN_REVIEW", cid)
        self.assertEqual(n["pmid41779000"]["identidade"]["relacionado"]["id"], "NCT03939689")   # ARROW
        self.assertEqual(n["pmid38447379"]["identidade"]["relacionado"]["id"], "NCT04300244")   # NIPU
        self.assertFalse(any(i["pacote"] == "NEW_CARD" and i["identidade"] for i in n.values()))
        for cid, outro in (("NCT01476787", "NCT01650701"), ("NCT01650701", "NCT01476787")):         # RELEVANCE
            pc = n[cid]["publicacao_compartilhada"]
            self.assertIn("pmid:30184451", pc["chaves"])
            self.assertIn(outro, [c["cand_id"] for c in pc["candidatos"]])


@unittest.skipUnless(TEM_REAL, "state local dos blocos 1–4 ausente (ex.: CI)")
class DadosReais(unittest.TestCase):
    def test_le_os_blocos_reais_sem_alterar_nada(self):
        antes = (sha_pasta(ESTADO_REAL / "discovery"), sha_pasta(ESTADO_REAL / "delta"), sha_arquivo(DATA_JS), sha_arquivo(SECUNDARIOS))
        carga = RC.carregar_itens(ESTADO_REAL, DATA_JS)
        itens = [i for i in carga["itens"] if isinstance(i["bloco"], int)]       # só o discovery (o novos tem teste próprio)
        filas = {b: json.loads((ESTADO_REAL / "discovery" / f"fila_humana_bloco{b}.json").read_text())
                 for b in carga["blocos"] if isinstance(b, int)}
        self.assertTrue({1, 2, 3, 4} <= set(carga["blocos"]))
        self.assertEqual(len({i["uid"] for i in itens}), sum(len(f["cards"]) for f in filas.values()))
        self.assertEqual(len({(i["uid"], i["pacote"]) for i in itens}),
                         sum(len(c["pacotes"]) for f in filas.values() for c in f["cards"].values()))
        pubs = {(u, RC.pub_id(x), p) for f in filas.values() for u, c in f["cards"].items() for p, l in c["pacotes"].items() for x in l}
        self.assertEqual(pubs, {(i["uid"], i["pub"], i["pacote"]) for i in itens})            # nenhuma publicação perdida
        self.assertEqual(len({i["decision_id"] for i in itens}), len(itens))
        self.assertEqual([i["decision_id"] for i in itens], [i["decision_id"] for i in RC.carregar_itens(ESTADO_REAL, DATA_JS)["itens"]
                                                            if isinstance(i["bloco"], int)])
        for i in itens:
            if i["tipo"] == "delta":
                self.assertIn(i["field_path"], RC.CAMPOS_VISIVEIS)
                self.assertTrue(i["current"] and i["proposed"] and i["source"])
            if i["tipo"] == "delta_hr":
                self.assertFalse(i["proposed"])
        self.assertEqual(antes, (sha_pasta(ESTADO_REAL / "discovery"), sha_pasta(ESTADO_REAL / "delta"),
                                 sha_arquivo(DATA_JS), sha_arquivo(SECUNDARIOS)))


if __name__ == "__main__":
    unittest.main()
