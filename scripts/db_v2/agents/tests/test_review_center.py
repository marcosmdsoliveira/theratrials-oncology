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


@unittest.skipUnless(TEM_REAL, "state local dos blocos 1–4 ausente (ex.: CI)")
class DadosReais(unittest.TestCase):
    def test_le_os_blocos_reais_sem_alterar_nada(self):
        antes = (sha_pasta(ESTADO_REAL / "discovery"), sha_pasta(ESTADO_REAL / "delta"), sha_arquivo(DATA_JS), sha_arquivo(SECUNDARIOS))
        carga = RC.carregar_itens(ESTADO_REAL, DATA_JS)
        itens = carga["itens"]
        filas = {b: json.loads((ESTADO_REAL / "discovery" / f"fila_humana_bloco{b}.json").read_text()) for b in carga["blocos"]}
        self.assertTrue({1, 2, 3, 4} <= set(carga["blocos"]))
        self.assertEqual(len({i["uid"] for i in itens}), sum(len(f["cards"]) for f in filas.values()))
        self.assertEqual(len({(i["uid"], i["pacote"]) for i in itens}),
                         sum(len(c["pacotes"]) for f in filas.values() for c in f["cards"].values()))
        pubs = {(u, RC.pub_id(x), p) for f in filas.values() for u, c in f["cards"].items() for p, l in c["pacotes"].items() for x in l}
        self.assertEqual(pubs, {(i["uid"], i["pub"], i["pacote"]) for i in itens})            # nenhuma publicação perdida
        self.assertEqual(len({i["decision_id"] for i in itens}), len(itens))
        self.assertEqual([i["decision_id"] for i in itens], [i["decision_id"] for i in RC.carregar_itens(ESTADO_REAL, DATA_JS)["itens"]])
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
