"""Testes do sistema database-curator / database-verifier (modo sombra). Offline.

    cd scripts/db_v2/agents && python3 -m unittest discover -s tests

Todos os casos são genéricos ou vêm do golden set como DADOS; nenhuma regra por nome de estudo.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import sys
import tempfile
import unittest

AG = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(AG))
sys.path.insert(0, str(AG.parent))
import agent_types as T  # noqa: E402
import checks as K  # noqa: E402
import corpus as CO  # noqa: E402
import curator as C  # noqa: E402
import decision_packet as D  # noqa: E402
import deterministic as DT  # noqa: E402
import priority as PR  # noqa: E402
import run_agents as RA  # noqa: E402
import sufficiency as SF  # noqa: E402
import signature as G  # noqa: E402
import sources as S  # noqa: E402
import v2lib as L  # noqa: E402
import verifier as V  # noqa: E402

FONTE = [("Results > Efficacy", "Median PFS was 8.3 months (80% CI 5.8-11.4) with drug A and 5.6 months with drug B."),
         ("Results > Safety", "Grade 3 or higher adverse events occurred in 40 of 51 patients (78%) with drug A."),
         ("Methods > Statistics", "Using a two-sided type I error rate of 0.20, 90 events were required.")]


def pasta_com_fonte(tipo="europepmc_fulltext", nivel="fulltext"):
    d = pathlib.Path(tempfile.mkdtemp())
    (d / "fontes").mkdir()
    S.gravar_fonte(d / "fontes", "pmc:PMC1:fulltext", FONTE)
    return d, {"pmc:PMC1:fulltext": {"source_type": tipo, "text_level": nivel, "path": "fontes/pmc_PMC1_fulltext.txt"}}


def ev(snippet, loc="¶0001 [Results > Efficacy]", sid="pmc:PMC1:fulltext", tipo="europepmc_fulltext"):
    return {"source_id": sid, "source_type": tipo, "locator": loc, "snippet": snippet}


def item(**kw):
    base = {"proposal_id": "p1", "field": "primario", "current_value": "x", "proposed_value": "PFS 8,3 vs 5,6 m",
            "change_kind": "replace", "proposal_type": "INTEGRITY_FIX", "defect": "numeric_contradiction",
            "value_origin": "reported",
            "evidence": [ev("Median PFS was 8.3 months (80% CI 5.8-11.4) with drug A and 5.6 months")],
            "reason": "r", "confidence": {"clinical_extraction": "high"}, "editorial_impact": "high"}
    base.update(kw)
    return base


def veredito(it):
    d, f = pasta_com_fonte()
    return K.pior(a["verdict"] for a in K.conferir_item(it, f, d)), K.conferir_item(it, f, d)


class Schemas(unittest.TestCase):
    def test_schemas_versionados_em_sincronia_com_o_codigo(self):
        for nome, s in T.schemas().items():
            self.assertEqual(json.loads((AG / "schemas" / nome).read_text()), json.loads(json.dumps(s)), nome)

    def test_dominios_de_confianca_separados_e_escrita_sempre_humana(self):
        self.assertEqual(set(T.DOMAINS), {"identity", "bibliographic_metadata", "publication_relationship",
                                          "clinical_extraction", "published_write"})
        self.assertEqual(T.DOMAINS["published_write"], ["human_required"])

    def test_tipos_e_prioridades(self):
        self.assertEqual(len(T.PROPOSAL_TYPES), 11)
        self.assertEqual(T.PRIORITY_OF_TYPE["INTEGRITY_FIX"], "P0")
        self.assertEqual(T.PRIORITY_OF_TYPE["BIBLIOGRAPHIC_FIX"], "P3")

    def test_assinatura_cobre_todos_os_campos_pedidos(self):
        pedidos = {"trial_key", "registry_ids", "cohort", "population", "disease_state", "treatment_line", "arms",
                   "analysis_set", "endpoint", "endpoint_hierarchy", "summary_measure", "comparison", "timepoint",
                   "assessment_method", "sample_size", "data_cutoff", "follow_up_median_months", "publication_role"}
        self.assertLessEqual(pedidos, set(T.SIGNATURE_FIELDS))


def sig(**kw):
    base = {"signature_id": "s", "trial_key": "NCT00000001", "registry_ids": ["NCT00000001"], "cohort": None,
            "population": "ITT", "disease_state": "metastático", "treatment_line": "1L",
            "arms": [{"label": "A", "role": "experimental"}, {"label": "B", "role": "control"}],
            "analysis_set": "ITT", "endpoint": "OS", "endpoint_hierarchy": "key_secondary", "summary_measure": "HR",
            "comparison": "A vs B", "timepoint": "median", "assessment_method": "INV", "data_cutoff": "2022-01-15",
            "follow_up_median_months": 24, "analysis_type": "primary", "publication_role": "primary_publication"}
    base.update(kw)
    return base


class Assinatura(unittest.TestCase):
    def test_outro_estudo(self):
        self.assertEqual(G.relacao(sig(), sig(trial_key="NCT09999999", registry_ids=["NCT09999999"]))[0],
                         "DIFFERENT_STUDY")

    def test_outra_coorte(self):
        self.assertEqual(G.relacao(sig(cohort="A"), sig(cohort="B"))[0], "NEW_COHORT")

    def test_subgrupo(self):
        self.assertEqual(G.relacao(sig(), sig(population="PD-L1 ≥50%"))[0], "SUBGROUP")

    def test_analise_secundaria_mesmo_mais_recente(self):
        # publicação mais nova com outro desfecho NÃO é atualização da análise do card
        self.assertEqual(G.relacao(sig(), sig(endpoint="QoL", data_cutoff="2025-01-01"))[0], "SECONDARY_ANALYSIS")

    def test_follow_up_longo_e_atualizacao(self):
        self.assertEqual(G.relacao(sig(), sig(data_cutoff="2024-06-01"))[0], "LONG_TERM_FOLLOWUP")
        self.assertEqual(G.relacao(sig(), sig(data_cutoff="2022-07-01"))[0], "SAME_ANALYSIS_UPDATE")
        self.assertEqual(G.relacao(sig(), sig(data_cutoff="2021-01-01"))[0], "SAME_ANALYSIS")

    def test_assinatura_incompleta_nao_chuta(self):
        self.assertEqual(G.relacao(sig(), sig(trial_key=None, registry_ids=[]))[0], "UNDETERMINED")
        self.assertEqual(G.relacao(sig(data_cutoff=None, follow_up_median_months=None),
                                   sig(data_cutoff=None, follow_up_median_months=None,
                                       publication_role="undetermined"))[0], "UNDETERMINED")

    def test_so_update_e_follow_up_podem_substituir(self):
        self.assertEqual(G.PODE_SUBSTITUIR, {"SAME_ANALYSIS_UPDATE", "LONG_TERM_FOLLOWUP"})


class Checagens(unittest.TestCase):
    def test_trecho_literal_e_numeros_sustentados_passam(self):
        self.assertEqual(veredito(item())[0], "PASS")

    def test_trecho_inexistente_falha(self):
        self.assertEqual(veredito(item(evidence=[ev("Median PFS was 9.9 months")]))[0], "FAIL")

    def test_localizador_errado_falha(self):
        v, a = veredito(item(evidence=[ev("Using a two-sided type I error rate of 0.20", loc="¶0001 [X]")],
                             proposed_value="α 0,20"))
        self.assertEqual(v, "FAIL")
        self.assertIn("LOCATOR_MISMATCH", [x["code"] for x in a])

    def test_numero_inventado_falha(self):
        v, a = veredito(item(proposed_value="PFS 8,3 vs 5,6 m; HR 1,41"))
        self.assertIn("NUMBER_UNSUPPORTED", [x["code"] for x in a])

    def test_decimal_em_grafia_de_periodico(self):
        self.assertTrue(K._num_no_texto("0.04", "PSA50 (P = .04)"))
        self.assertTrue(K._num_no_texto("0.66", "HR 1·09; p=0·66"))
        self.assertFalse(K._num_no_texto("0.04", "dose 10.04 mg"))

    def test_derivado_correto_passa_e_errado_falha(self):
        der = {"operands": [{"name": "n", "value": 40, "evidence_index": 0},
                            {"name": "t", "value": 51, "evidence_index": 0}], "rule": "n/t*100", "result": 78.4}
        e = [ev("Grade 3 or higher adverse events occurred in 40 of 51 patients", loc="¶0002 [Results > Safety]")]
        self.assertEqual(veredito(item(value_origin="derived", derivation=der, evidence=e,
                                       proposed_value="78,4% (40/51)"))[0], "PASS")
        self.assertEqual(veredito(item(value_origin="derived", derivation=dict(der, result=70.0), evidence=e,
                                       proposed_value="70%"))[0], "FAIL")
        self.assertEqual(veredito(item(value_origin="reported", derivation=der, evidence=e,
                                       proposed_value="78,4%"))[0], "FAIL")      # derivado fingindo ser reportado

    def test_fonte_proibida_e_fora_do_pacote(self):
        self.assertEqual(veredito(item(evidence=[ev("x" * 10, sid="tracker.json", tipo="pmc_fulltext")]))[0], "FAIL")
        self.assertEqual(veredito(item(evidence=[ev("Median PFS", sid="pmid:9:abstract")]))[0], "FAIL")

    def test_sem_evidencia_e_ausencia_em_resumo_sao_unsupported(self):
        self.assertEqual(veredito(item(evidence=[]))[0], "UNSUPPORTED")
        d, f = pasta_com_fonte(tipo="pubmed_abstract", nivel="abstract")
        it = item(evidence=[], change_kind="remove", absence_checked_in=["pmc:PMC1:fulltext"],
                  value_origin="editorial", proposed_value=None)
        self.assertEqual(K.pior(a["verdict"] for a in K.conferir_item(it, f, d)), "UNSUPPORTED")

    def test_conflito_declarado_vira_conflict(self):
        it = item(proposed_value=None, conflict={"description": "abstract × tabela",
                                                  "candidates": [{"value": 6, "evidence_index": 0},
                                                                 {"value": 5.9, "evidence_index": 0}]})
        self.assertEqual(veredito(it)[0], "CONFLICT")


class Verificador(unittest.TestCase):
    def prop(self):
        return {"uid": "u", "proposals": [item(), item(proposal_id="p2", field="tox_g3")]}

    def test_verifier_nao_ve_raciocinio_do_curator(self):
        self.assertNotIn("reason", T.VERIFIER_VISIBLE)
        self.assertNotIn("confidence", T.VERIFIER_VISIBLE)
        self.assertNotIn("editorial_impact", T.VERIFIER_VISIBLE)

    def test_fusao_pega_o_pior_e_nunca_promove(self):
        p = self.prop()
        det = {"p1": [{"verdict": "FAIL", "code": "X", "detail": ""}], "p2": [{"verdict": "PASS", "code": "OK",
                                                                               "detail": ""}]}
        llm = {"schema": "theratrials-db-verifier-result/1", "uid": "u", "proposal_sha256": V.sha_proposta(p),
               "results": [{"proposal_id": "p1", "field": "primario", "verdict": "PASS", "reason": "parece ok"},
                           {"proposal_id": "p2", "field": "tox_g3", "verdict": "UNSUPPORTED", "reason": "sem fonte"}]}
        r = {x["proposal_id"]: x for x in V.fundir(p, llm, det)["results"]}
        self.assertEqual((r["p1"]["verdict"], r["p2"]["verdict"]), ("FAIL", "UNSUPPORTED"))
        self.assertTrue(r["p1"]["divergence"])

    def test_item_nao_avaliado_e_tentativa_de_correcao_viram_unsupported(self):
        p = self.prop()
        det = {k: [{"verdict": "PASS", "code": "OK", "detail": ""}] for k in ("p1", "p2")}
        llm = {"schema": "theratrials-db-verifier-result/1", "uid": "u", "proposal_sha256": V.sha_proposta(p),
               "results": [{"proposal_id": "p1", "field": "primario", "verdict": "PASS", "reason": "ok, conferido",
                            "corrected_value": "outra coisa"}]}
        out = V.fundir(p, llm, det)
        r = {x["proposal_id"]: x for x in out["results"]}
        self.assertEqual((r["p1"]["verdict"], r["p2"]["verdict"]), ("UNSUPPORTED", "UNSUPPORTED"))
        self.assertTrue(any("E_VERIFIER_REWRITE" in a for a in out["_ingestao"]["avisos"]))
        self.assertEqual(p["proposals"][0]["proposed_value"], "PFS 8,3 vs 5,6 m")   # proposta intacta


class Consenso(unittest.TestCase):
    def test_estados(self):
        self.assertEqual([V.consenso(a, b) for a, b in [("PASS", "PASS"), ("FAIL", "FAIL"),
                                                          ("UNSUPPORTED", "UNSUPPORTED"), ("CONFLICT", "CONFLICT"),
                                                          ("PASS", "CONFLICT"), ("PASS", None)]],
                         ["UNANIMOUS_PASS", "UNANIMOUS_FAIL", "UNANIMOUS_UNSUPPORTED", "UNANIMOUS_CONFLICT",
                          "DISAGREEMENT", "SINGLE_RUN"])
        self.assertEqual(set(T.CONSENSUS_STATES) - {"SINGLE_RUN"},
                         {"UNANIMOUS_PASS", "UNANIMOUS_FAIL", "UNANIMOUS_UNSUPPORTED", "UNANIMOUS_CONFLICT",
                          "DISAGREEMENT"})

    def test_segunda_execucao_nao_ve_a_primeira(self):
        t = (AG / "run_agents.py").read_text()
        self.assertIn('verifier_input_b.json', t)
        self.assertNotIn("state/verifier", t)
        vis = set(T.VERIFIER_VISIBLE)
        self.assertFalse(vis & {"verdict", "run_a", "consensus", "semantic"})


class OrigemImposta(unittest.TestCase):
    def test_curator_nao_pode_se_declarar_deterministico_para_escapar_do_verifier(self):
        tmp = pathlib.Path(tempfile.mkdtemp())
        orig = (S.STATE, C.CURADOR)
        try:
            S.STATE, C.CURADOR = tmp, tmp / "curator"
            C.CURADOR.mkdir()
            pasta = tmp / "packets" / "u"
            (pasta / "fontes").mkdir(parents=True)
            pk = {"uid": "u", "card": {}, "sources": [], "deterministic_findings": [], "withheld": True,
                  "human_decision_protected_fields": []}
            pk["packet_sha256"] = "x"
            (pasta / "packet.json").write_text(json.dumps(pk))
            falso = item(origin="deterministic", _det_priority="P3", proposal_type="BIBLIOGRAPHIC_FIX")
            prop = {"uid": "u", "packet_sha256": "x", "proposals": [falso], "analysis_signatures": []}
            C.ingerir("u", json.dumps(prop))
            salvo = json.loads((C.CURADOR / "u.json").read_text())
            it = salvo["proposals"][0]
            self.assertEqual(it["origin"], "curator")
            self.assertNotIn("_det_priority", it)
            self.assertTrue(any("rebaixada para curator" in a for a in salvo["_ingestao"]["avisos"]))
            S.STATE = tmp
            (tmp / "tasks").mkdir(exist_ok=True)
            orig_t = V.TAREFAS
            V.TAREFAS = tmp / "tasks"
            try:
                self.assertEqual(len(V.entrada("u")["items"]), 1)      # vai ao verifier
            finally:
                V.TAREFAS = orig_t
        finally:
            S.STATE, C.CURADOR = orig


class PacoteDeDecisao(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        self._orig = (S.STATE, C.CURADOR, V.VERIF, D.PACOTES, D.FILA)
        S.STATE, C.CURADOR, V.VERIF = self.tmp, self.tmp / "curator", self.tmp / "verifier"
        D.PACOTES, D.FILA = self.tmp / "dp", self.tmp / "fila.json"
        for d in (C.CURADOR, V.VERIF, self.tmp / "packets" / "u"):
            d.mkdir(parents=True)

    def tearDown(self):
        S.STATE, C.CURADOR, V.VERIF, D.PACOTES, D.FILA = self._orig

    def montar(self, vereditos, withheld=False, protegidos=(), prioridade="P0", cvs="CONTRADICTED", extra=None,
               segundo=None):
        """segundo: lista de vereditos da 2ª execução (None = ainda não houve; "same" = igual à primeira)."""
        if segundo == "same":
            segundo = list(vereditos)
        pk = {"card": {"estudo": "E"}, "identity": {"status": "machine_verified"},
              "bibliographic": {"eligibility": "ok", "has_structured_citation": True},
              "publication_relationship": {"status": "undetermined"}, "withheld": withheld,
              "human_decision_protected_fields": list(protegidos), "deterministic_findings": [], **(extra or {})}
        (self.tmp / "packets" / "u" / "packet.json").write_text(json.dumps(pk))
        tipo = {"P0": ("INTEGRITY_FIX", "numeric_contradiction"), "P3": ("BIBLIOGRAPHIC_FIX", "bibliographic_format")}
        itens = [item(proposal_id=f"p{i}", field="primario" if prioridade == "P0" else "ref",
                      proposal_type=tipo[prioridade][0], defect=tipo[prioridade][1]) for i in range(len(vereditos))]
        (C.CURADOR / "u.json").write_text(json.dumps({"uid": "u", "card_classification": {
            "proposal_type": "INTEGRITY_FIX", "summary": "s"}, "proposals": itens}))
        (V.VERIF / "u.json").write_text(json.dumps({"results": [
            {"proposal_id": f"p{i}", "verdict": v, "current_value_status": cvs, "deterministic": {"verdict": v},
             "semantic": {"reason": "r"}}
            for i, v in enumerate(vereditos)], "relationship": {"verdict": "PASS"},
            **({"consensus": {f"p{i}": {"state": V.consenso(va, vb),
                                        "run_a": {"verdict": va, "current_value_status": cvs},
                                        "run_b": {"verdict": vb, "current_value_status": "UNSUPPORTED"}}
                              for i, (va, vb) in enumerate(zip(vereditos, segundo))}} if segundo else {})}))
        return D.montar("u")

    def test_um_pacote_por_card_com_decisao_final_nula(self):
        p = self.montar(["PASS", "PASS"], segundo="same")
        self.assertEqual((p["suggested_decision"], len(p["fields"]), p["final_decision"]), ("APPROVE", 2, None))
        self.assertEqual(p["domain_confidence"]["published_write"], "human_required")

    def test_sugestoes(self):
        self.assertEqual(self.montar(["UNSUPPORTED", "UNSUPPORTED"])["suggested_decision"], "REJECT")
        p = self.montar(["PASS", "FAIL"], cvs="SUPPORTED", segundo="same")  # FAIL sai da fila e fica registrado
        self.assertEqual((p["suggested_decision"], len(p["dropped_fail"])), ("APPROVE", 1))
        self.assertEqual(self.montar(["PASS", "CONFLICT"])["suggested_decision"], "DEFER")
        self.assertEqual(self.montar(["PASS"], protegidos=["primario"])["suggested_decision"], "DEFER")
        p = self.montar([], withheld=True)
        self.assertEqual((p["suggested_decision"], p["human_required"],
                          p["domain_confidence"]["clinical_extraction"]), ("NONE", False, "withheld"))

    def test_p0_com_dois_verifiers_concordantes(self):
        p = self.montar(["PASS"], segundo="same")
        f = p["fields"][0]
        self.assertEqual((f["verifier_consensus"], f["final_priority"], f["human_review_required"]),
                         ("UNANIMOUS_PASS", "P0", False))
        self.assertEqual((p["suggested_decision"], p["auto_approval_blocked"]), ("APPROVE", False))
        self.assertEqual(p["domain_confidence"]["published_write"], "human_required")

    def test_p0_com_verifiers_divergentes_vira_disagreement_defer_sem_rebaixar(self):
        for a, b in [("PASS", "FAIL"), ("PASS", "UNSUPPORTED"), ("CONFLICT", "PASS")]:
            p = self.montar([a], segundo=[b])
            f = p["fields"][0]
            self.assertEqual(f["verifier_consensus"], "DISAGREEMENT", (a, b))
            self.assertEqual(f["final_priority"], "P0", (a, b))           # prioridade clínica preservada
            self.assertTrue(f["human_review_required"])
            self.assertEqual((f["run_a"]["verdict"], f["run_b"]["verdict"]), (a, b))   # lado a lado
            self.assertEqual((p["suggested_decision"], p["auto_approval_blocked"]), ("DEFER", True), (a, b))
            self.assertTrue(p["counts_toward_weekly_budget"])

    def test_p0_sem_segunda_execucao_nao_e_aprovado(self):
        p = self.montar(["PASS"])
        self.assertEqual((p["fields"][0]["verifier_consensus"], p["suggested_decision"], p["auto_approval_blocked"]),
                         ("SINGLE_RUN", "DEFER", True))

    def test_nenhuma_discordancia_reduz_prioridade(self):
        # 2ª execução unânime no veredito, mas com valor atual "UNSUPPORTED" (que sozinho daria P1): fica P0
        p = self.montar(["PASS"], segundo="same")
        self.assertEqual((p["fields"][0]["priority_run_b"], p["fields"][0]["final_priority"]), ("P1", "P0"))
        for a, b in [("PASS", "FAIL"), ("PASS", "UNSUPPORTED"), ("CONFLICT", "PASS")]:
            self.assertEqual(self.montar([a], segundo=[b])["priority"], "P0")

    def test_backlog_sem_item_sobrevivente_e_encaminhado_e_so_watch_nao_vira_reject(self):
        pk_extra = {"backlog": [{"id": "INT-u-001", "status": "open", "affected_fields": ["primario"],
                                 "description": "d"},
                                {"id": "INT-u-002", "status": "resolved", "affected_fields": ["excl"]}]}
        p = self.montar(["FAIL"], cvs="SUPPORTED", extra=pk_extra)       # único item do campo caiu por FAIL
        self.assertEqual([(f["origin"], f["field"], f["final_priority"]) for f in p["fields"]],
                         [("backstop", "primario", "P2")])
        self.assertEqual((p["suggested_decision"], p["counts_toward_weekly_budget"]), ("WATCH", False))

    def test_p3_deterministico_nao_consome_orcamento(self):
        self.assertFalse(self.montar(["PASS"], prioridade="P3")["counts_toward_weekly_budget"])
        self.assertTrue(self.montar(["PASS"], prioridade="P0")["counts_toward_weekly_budget"])

    def test_alta_confianca_bibliografica_nao_autoriza_escrita(self):
        p = self.montar(["PASS"])
        self.assertEqual(p["domain_confidence"]["bibliographic_metadata"], "machine_verified")
        self.assertEqual(p["domain_confidence"]["published_write"], "human_required")


class SemApply(unittest.TestCase):
    def test_nenhum_caminho_de_escrita_em_producao(self):
        for f in AG.glob("*.py"):
            t = f.read_text()
            self.assertNotRegex(t, r"--apply|--aplicar", f.name)
            self.assertNotRegex(t, r"DATA_JS\.(write|open)|[\"']app-data|export_app_data|gerar_citacoes", f.name)
            self.assertNotRegex(t, r"git (commit|push)|\"commit\"|\"push\"", f.name)

    def test_prompts_dos_agentes_sem_ferramenta_de_escrita(self):
        for nome in ("database-curator.md", "database-verifier.md"):
            cab = (AG.parents[2] / ".claude" / "agents" / nome).read_text().split("---")[1]
            ferramentas = re.search(r"tools:\s*(.*)", cab).group(1)
            self.assertEqual({x.strip() for x in ferramentas.split(",")}, {"Read", "Grep", "Glob"})

    def test_verifier_prompt_explicita_as_regras(self):
        t = re.sub(r"\s+", " ", (AG.parents[2] / ".claude" / "agents" / "database-verifier.md").read_text())
        for trecho in ("não confia no curator", "UNSUPPORTED", "CONFLICT", "Não escolha uma fonte arbitrariamente",
                       "Corrigir, reescrever"):
            self.assertIn(trecho, t)


class Golden(unittest.TestCase):
    def test_golden_bem_formado_e_sem_regra_de_codigo(self):
        g = CO.golden()["casos"]
        self.assertEqual(len(g), 10)
        backlog = {x["id"] for x in json.loads((L.SCRIPTS / "db_candidatos_integridade.json").read_text())["itens"]}
        for uid, caso in g.items():
            for e in caso["expected"]:
                for ref in re.findall(r"INT-[\w\-]+?-\d{3}", e["basis"]):
                    self.assertIn(ref, backlog, f"{uid}: base {ref} inexistente no backlog")
                self.assertIn(e["strength"], ("confirmed", "pilot_verified", "candidate"))
        codigo = " ".join(f.read_text() for f in AG.glob("*.py"))
        for caso in g.values():
            nome = caso["estudo"].split()[0]
            self.assertNotIn(nome, codigo, f"nome de estudo no código: {nome}")

    def test_corpus_deterministico(self):
        self.assertEqual(CO.corpus(), CO.corpus())


PK = {"deterministic_findings": [], "human_decision_protected_fields": []}
FRESH = {"deterministic_findings": [{"code": "FRESHNESS_PRESENTED_BUT_PUBLISHED"}], "human_decision_protected_fields": []}


def prio(pacote=PK, veredito="PASS", cvs="CONTRADICTED", **kw):
    return PR.classificar(item(**kw), veredito, cvs, pacote)[0]


class Prioridade(unittest.TestCase):
    def test_identificador_errado_e_p0(self):
        self.assertEqual(prio(field="pubmed_url", proposal_type="INTEGRITY_FIX", defect="identifier_mismatch"), "P0")

    def test_toxicidade_no_braco_errado_e_p0(self):
        self.assertEqual(prio(field="tox_interesse", defect="safety_misattribution"), "P0")
        self.assertEqual(prio(field="tox_interesse", defect="arm_attribution"), "P0")

    def test_p0_exige_valor_atual_contradito_verificado(self):
        self.assertEqual(prio(field="primario", defect="numeric_contradiction", cvs="NOT_ADDRESSED"), "P1")
        self.assertEqual(prio(field="primario", defect="numeric_contradiction", cvs="SUPPORTED"), "P2")

    def test_mesma_analise_atualizada_e_p1_e_dado_novo_nao_e_erro(self):
        self.assertEqual(prio(field="secundario", proposal_type="SAME_ANALYSIS_UPDATE",
                              defect="newer_data_same_analysis", cvs="SUPPORTED"), "P1")
        self.assertEqual(prio(field="secundario", proposal_type="LONG_TERM_FOLLOWUP",
                              defect="newer_data_same_analysis", cvs="NOT_ADDRESSED"), "P1")

    def test_freshness_sozinho_nunca_e_p0(self):
        self.assertEqual(prio(FRESH, field="status", proposal_type="INTEGRITY_FIX", defect="stale_status"), "P3")
        self.assertEqual(prio(FRESH, field="status", proposal_type="INTEGRITY_FIX", defect="numeric_contradiction"), "P3")

    def test_formatacao_bibliografica_e_p3_e_identidade_e_p0(self):
        self.assertEqual(prio(field="ref", proposal_type="BIBLIOGRAPHIC_FIX", defect="bibliographic_format"), "P3")
        self.assertEqual(prio(field="ref", proposal_type="BIBLIOGRAPHIC_FIX", defect="numeric_contradiction"), "P3")
        self.assertEqual(prio(field="pubmed_url", proposal_type="BIBLIOGRAPHIC_FIX", defect="identifier_mismatch"), "P0")

    def test_curator_nao_promove_a_p0(self):
        self.assertEqual(prio(field="primario", proposal_type="INTEGRITY_FIX", defect="enrichment",
                              priority="P0"), "P2")

    def test_decisao_humana_e_campo_human_only_tem_precedencia(self):
        pk = {"deterministic_findings": [], "human_decision_protected_fields": ["esquema"]}
        self.assertEqual(prio(pk, field="esquema", defect="numeric_contradiction"), "P2")
        self.assertEqual(prio(field="impacto_reg", defect="unsupported_claim"), "P2")

    def test_fail_sai_da_fila_unsupported_vira_watch_conflict_clinico_e_p0(self):
        self.assertIsNone(prio(veredito="FAIL", cvs="SUPPORTED"))
        self.assertEqual(prio(veredito="UNSUPPORTED"), "P2")
        self.assertEqual(prio(veredito="CONFLICT", field="primario"), "P0")
        self.assertEqual(prio(veredito="CONFLICT", field="ref"), "P2")

    def test_fail_da_proposta_nao_apaga_valor_atual_contradito_nem_conflito(self):
        self.assertEqual(prio(veredito="FAIL", cvs="CONTRADICTED", field="primario"), "P1")
        self.assertIsNone(prio(veredito="FAIL", cvs="CONTRADICTED", field="ref"))
        conflito = {"description": "d", "candidates": [{"value": "a", "evidence_index": 0}]}
        self.assertEqual(prio(veredito="FAIL", cvs="NOT_ADDRESSED", conflict=conflito, proposed_value=None), "P2")

    def test_conflito_so_e_p0_em_resultado_ou_na_propria_fonte(self):
        self.assertEqual(prio(veredito="CONFLICT", field="esquema", defect="cross_source_conflict"), "P1")
        self.assertEqual(prio(veredito="CONFLICT", field="esquema", defect="within_source_conflict"), "P1")
        self.assertEqual(prio(veredito="CONFLICT", field="secundario", defect="within_source_conflict"), "P0")
        self.assertEqual(prio(veredito="CONFLICT", field="estatistica", defect="cross_source_conflict"), "P1")
        self.assertEqual(prio(veredito="CONFLICT", field="tox_g3", defect="cross_source_conflict"), "P0")

    def test_defeito_de_integridade_so_e_p0_no_campo_em_que_importa(self):
        self.assertEqual(prio(field="primario", defect="numeric_contradiction"), "P0")
        self.assertEqual(prio(field="incl", defect="numeric_contradiction"), "P1")
        self.assertEqual(prio(field="periodo", defect="numeric_contradiction"), "P3")
        self.assertEqual(prio(field="excl", defect="safety_misattribution"), "P1")
        self.assertEqual(prio(field="titulo_full", defect="identifier_mismatch"), "P0")

    def test_parametro_de_desenho_contraditorio_e_p1(self):
        self.assertEqual(prio(field="estatistica", defect="numeric_contradiction",
                              current_value="poder 86% para HR 0,75", proposed_value="poder 80% para HR 0,72"), "P1")
        self.assertEqual(prio(field="tox_interesse", defect="numeric_contradiction",
                              current_value="reverte em 4-6 sem", proposed_value="resolução mediana 12 semanas"), "P1")

    def test_resultado_clinico_material_no_braco_errado_e_p0(self):
        self.assertEqual(prio(field="primario", defect="arm_attribution"), "P0")
        self.assertEqual(prio(field="primario", defect="numeric_contradiction",
                              current_value="HR 0,49", proposed_value="HR 0,41"), "P0")

    def test_arredondamento_editorial_nao_e_p0(self):
        self.assertEqual(prio(field="primario", defect="numeric_contradiction",
                              current_value="ORR 57%; EA 2%", proposed_value="ORR 57,7%; EA 2,6%"), "P1")
        self.assertFalse(PR.so_arredondamento("12,0 m", "12,9 m"))
        self.assertTrue(PR.so_arredondamento("57,7%", "58%"))
        # número trocado escondido por outro igual em outro lugar do texto NÃO é arredondamento
        self.assertFalse(PR.so_arredondamento("anemia 6,2% vs 5%; fadiga 5%", "anemia 6% vs 7%; fadiga 1 vs 5%"))
        self.assertEqual(prio(field="tox_g3", defect="numeric_contradiction",
                              current_value="anemia 6,2% vs 5%", proposed_value="anemia 6% vs 7%"), "P0")

    def test_atualizacao_fora_de_campo_de_resultado_nao_e_p1(self):
        self.assertEqual(prio(field="centros", proposal_type="SAME_ANALYSIS_UPDATE", defect="enrichment",
                              cvs="NOT_ADDRESSED"), "P2")

    def test_orcamento_so_p0_p1(self):
        self.assertEqual(PR.ORCAMENTO, {"P0", "P1"})


def pacote_det(card, achados, fontes_pars, backlog=()):
    d = pathlib.Path(tempfile.mkdtemp())
    (d / "fontes").mkdir()
    fontes = []
    for sid, (tipo, nivel, pars) in fontes_pars.items():
        f = S.gravar_fonte(d / "fontes", sid, pars)
        fontes.append({"source_id": sid, "source_type": tipo, "text_level": nivel, "path": f"fontes/{f.name}"})
    return d, {"card": card, "deterministic_findings": achados, "sources": fontes, "backlog": list(backlog)}


class Deterministicos(unittest.TestCase):
    META = {"pmid:1:metadata": ("pubmed_metadata", "metadata", [("PMID", "1"), ("PubDate", "2023 Jun 20"),
                                                                 ("PublicationType", "Journal Article")])}

    def test_ano_pub_divergente_vira_item_p3_verificado(self):
        d, pk = pacote_det({"ano_pub": 2022}, [{"code": "ANO_PUB_MISMATCH", "proposed": "2023", "detail": "x",
                                                 "source_id": "pmid:1:metadata"}], self.META)
        its = DT.itens(pk, {"proposals": []}, d)
        self.assertEqual([(i["field"], i["proposed_value"], i["_det_priority"]) for i in its], [("ano_pub", "2023", "P3")])
        fontes = {f["source_id"]: f for f in pk["sources"]}
        self.assertEqual(K.pior(a["verdict"] for a in K.conferir_item(its[0], fontes, d)), "PASS")

    def test_apresentado_com_artigo_publicado_e_p3_nunca_p0(self):
        d, pk = pacote_det({"status": "Apresentado (ASCO)"}, [{"code": "FRESHNESS_PRESENTED_BUT_PUBLISHED",
                                                                "detail": "x"}], self.META)
        it = DT.itens(pk, {"proposals": []}, d)[0]
        self.assertEqual((it["field"], it["_det_priority"], it["defect"]), ("status", "P3", "stale_status"))

    def test_conflito_entre_fontes_sem_escolha(self):
        fp = {"nct:NCT1:registry": ("ctgov_record", "registry",
                                    [("protocolSection.designModule.designInfo.maskingInfo.masking", "TRIPLE")]),
              "pmc:PMC1:fulltext": ("europepmc_fulltext", "fulltext", [("Methods", "This open-label, phase 3 trial.")])}
        d, pk = pacote_det({"desenho": "Fase 3, aberto"}, [{"code": "MASKING_CROSS_SOURCE", "registry": "NCT1",
                                                            "masking": "TRIPLE", "pub_source": "pmc:PMC1:fulltext",
                                                            "pub_par": "0001", "pub_match": "open-label",
                                                            "detail": "x"}], fp)
        it = DT.itens(pk, {"proposals": []}, d)[0]
        self.assertIsNone(it["proposed_value"])
        self.assertEqual(len(it["conflict"]["candidates"]), 2)
        fontes = {f["source_id"]: f for f in pk["sources"]}
        self.assertEqual(K.pior(a["verdict"] for a in K.conferir_item(it, fontes, d)), "CONFLICT")

    def test_conflito_dentro_da_fonte_declarado_pelo_curator_vira_conflict(self):
        it = item(proposed_value=None, defect="within_source_conflict",
                  conflict={"description": "resumo × métodos", "candidates": [
                      {"value": "2 semanas", "evidence_index": 0}, {"value": "8 semanas", "evidence_index": 0}]})
        self.assertEqual(veredito(it)[0], "CONFLICT")

    def test_no_action_do_curator_nao_dispensa_revisao_do_campo_resumo(self):
        d, pk = pacote_det({"resultado_chave": "ORR 50%"}, [], {})
        prop = {"proposals": [item(field="secundario", proposal_type="LONG_TERM_FOLLOWUP", defect="enrichment")],
                "no_action_fields": ["resultado_chave"]}
        self.assertEqual([i["field"] for i in DT.itens(pk, prop, d)], ["resultado_chave"])

    def test_backlog_nao_tratado_e_resumo_dependente_nao_ficam_em_silencio(self):
        d, pk = pacote_det({"resultado_chave": "PFS 10 m"}, [], {}, backlog=[
            {"id": "INT-x-001", "status": "open", "affected_fields": ["periodo"], "description": "d"}])
        prop = {"proposals": [item(field="secundario", proposal_type="LONG_TERM_FOLLOWUP",
                                   defect="newer_data_same_analysis")]}
        campos = {(i["field"], i["_det_priority"]) for i in DT.itens(pk, prop, d)}
        self.assertEqual(campos, {("periodo", "P2"), ("resultado_chave", "P1")})


class Suficiencia(unittest.TestCase):
    F = {"a": {"text_level": "abstract"}, "t": {"text_level": "fulltext"}, "r": {"text_level": "registry"}}

    def test_resumo_basta_quando_explicito(self):
        it = item(field="primario", evidence=[{"source_id": "a"}])
        self.assertEqual(SF.avaliar(it, self.F, "explicit")[0], "PASS")

    def test_resumo_insuficiente_para_detalhe_sem_sustentacao_explicita(self):
        it = item(field="esquema", evidence=[{"source_id": "a"}])
        self.assertEqual(SF.avaliar(it, self.F, "partial")[0], "UNSUPPORTED")
        self.assertEqual(SF.avaliar(it, self.F, None)[0], "UNSUPPORTED")
        self.assertEqual(SF.avaliar(it, self.F, "explicit")[0], "PASS")     # não exige texto completo por princípio

    def test_ausencia_exige_texto_completo_ou_registro(self):
        it = item(field="secundario", change_kind="remove", absence_checked_in=["a"], evidence=[])
        self.assertEqual(SF.avaliar(it, self.F, "explicit")[0], "UNSUPPORTED")
        it = item(field="secundario", change_kind="remove", absence_checked_in=["t"], evidence=[])
        self.assertEqual(SF.avaliar(it, self.F, "explicit")[0], "PASS")

    def test_campo_human_only(self):
        self.assertEqual(SF.avaliar(item(field="impacto_reg"), self.F, "explicit")[0], "UNSUPPORTED")

    def test_matriz_cobre_as_classes(self):
        self.assertEqual({SF.classe(c) for c in ("ano_pub", "primario", "esquema", "impacto_reg")},
                         {"metadata", "abstract", "detail", "human"})


class ExecucaoRestrita(unittest.TestCase):
    def test_runner_usa_a_definicao_do_agente_e_proibe_shell(self):
        t = (AG / "run_agents.py").read_text()
        self.assertIn('"--agent", agente', t)
        self.assertIn('"database-verifier" if papel == "verifier_b" else f"database-{papel}"', t)
        for proibida in ("Bash", "Edit", "Write", "WebFetch", "WebSearch", "Agent", "Task"):
            self.assertIn(proibida, RA.PROIBIDAS_CLI)
        self.assertEqual(RA.PERMITIDAS, {"Read", "Grep", "Glob"})

    def test_auditoria_reprova_ferramenta_ausente_ou_proibida_sem_fallback(self):
        import subprocess as sp
        origem = sp.run

        def falso(ferramentas, usadas):
            linhas = [json.dumps({"type": "system", "subtype": "init", "tools": ferramentas})]
            for u in usadas:
                linhas.append(json.dumps({"type": "assistant", "message": {"content": [
                    {"type": "tool_use", "name": u, "input": {}}]}}))
            linhas.append(json.dumps({"type": "result", "subtype": "success", "result": "{}"}))
            return lambda *a, **k: sp.CompletedProcess(a, 0, "\n".join(linhas), "")
        tmp = pathlib.Path(tempfile.mkdtemp())
        orig = (RA.RUNS, RA.RAW, RA._prompt, RA.binario)
        RA.RUNS, RA.RAW = tmp / "runs", tmp / "raw"
        RA._prompt = lambda papel, uid: ("x", [tmp])
        RA.binario = lambda: "claude"
        try:
            for ferramentas, usadas in [(["Read", "Glob"], []), (["Read", "Grep", "Glob", "Bash"], []),
                                        (["Read", "Grep", "Glob"], ["Bash"])]:
                sp.run = falso(ferramentas, usadas)
                with self.assertRaises(RA.ExecucaoInvalida):
                    RA.executar("verifier", "u")
            sp.run = falso(["Read", "Grep", "Glob"], ["Read", "Grep"])
            self.assertEqual(RA.executar("verifier", "u")["violacoes"], [])
            # a 2ª verificação usa a MESMA definição e as mesmas restrições; Bash nela também reprova
            cmds = []
            ok = falso(["Read", "Grep", "Glob"], ["Read"])
            sp.run = lambda cmd, **k: (cmds.append(cmd), ok(cmd, **k))[1]
            self.assertEqual(RA.executar("verifier_b", "u")["agent"], "database-verifier")
            self.assertIn("--disallowedTools", cmds[0])
            self.assertIn("Bash", cmds[0][cmds[0].index("--disallowedTools") + 1])
            sp.run = falso(["Read", "Grep", "Glob"], ["Bash"])
            with self.assertRaises(RA.ExecucaoInvalida):
                RA.executar("verifier_b", "u")
        finally:
            sp.run = origem
            RA.RUNS, RA.RAW, RA._prompt, RA.binario = orig


if __name__ == "__main__":
    unittest.main()
