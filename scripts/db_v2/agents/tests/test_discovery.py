"""Testes do discovery de publicações novas (modo sombra). Offline, dados genéricos.

    cd scripts/db_v2/agents && python3 -m unittest discover -s tests
"""
from __future__ import annotations

import json
import pathlib
import sys
import tempfile
import unittest

AG = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(AG))
sys.path.insert(0, str(AG.parent))
import agent_types as T  # noqa: E402
import discovery as DS  # noqa: E402
import sources as S  # noqa: E402

CONHEC = {"pmids": {"111"}, "dois": {"10.1/sec"}, "origem": {"111": "card", "10.1/sec": "secundário x"}}


def sig(**kw):
    base = {"signature_id": "s", "trial_key": "TRIAL-X", "registry_ids": ["NCT00000001"], "cohort": None,
            "population": "adults with disease y", "disease_state": None, "treatment_line": None,
            "arms": [{"label": "A", "role": "experimental"}, {"label": "B", "role": "control"}],
            "analysis_set": "itt", "endpoint": "overall survival", "endpoint_hierarchy": "secondary",
            "summary_measure": "hazard ratio", "comparison": "A vs B", "timepoint": None, "assessment_method": None,
            "sample_size": None, "data_cutoff": "2022-01", "follow_up_median_months": None,
            "analysis_type": "primary", "publication_role": "primary_publication", "publication_id": "pmid:111"}
    base.update(kw)
    return base


def comp(**kw):
    base = {k: "same" for k in T.DISCOVERY_COMPARED}
    base["timepoint"] = "different"
    base.update(kw)
    return {k: {"status": v, "note": None} for k, v in base.items()}


class Triagem(unittest.TestCase):
    def test_funde_por_pmid_e_doi_e_elimina_cadastradas_errata_e_sem_id(self):
        brutos = [
            {"pmid": "222", "via": "pubmed_si:NCT1", "title": "Trial X final analysis", "pubtype": ["Journal Article"]},
            {"pmid": "222", "doi": "10.1/new", "via": "europepmc:NCT1"},
            {"doi": "10.1/new", "via": "europepmc:NCT1"},                          # mesma pelo DOI
            {"pmid": "111", "via": "ctgov_ref:NCT1"},                              # card
            {"doi": "10.1/sec", "via": "europepmc:NCT1"},                          # secundário
            {"pmid": "333", "via": "pubmed_si:NCT1", "title": "Correction to: Trial X", "pubtype": ["Journal Article"]},
            {"pmid": "444", "via": "pubmed_si:NCT1", "title": "x", "pubtype": ["Published Erratum"]},
            {"via": "europepmc:NCT1", "title": "sem id"},
        ]
        cand, elim = DS.triagem(brutos, CONHEC)
        self.assertEqual([c["pmid"] for c in cand], ["222"])
        self.assertEqual(cand[0]["doi"], "10.1/new")
        self.assertEqual(cand[0]["via"], ["europepmc:NCT1", "pubmed_si:NCT1"])
        self.assertEqual(sorted(e["eliminado"] for e in elim),
                         ["errata", "errata", "ja_cadastrada", "ja_cadastrada", "sem_identificador"])

    def test_review_sem_dado_original_e_no_action_antes_do_llm(self):
        for pub in ({"title": "PSMA theranostics: a narrative review", "pubtype": ["Journal Article", "Review"]},
                    {"title": "x", "pubtype": ["Meta-Analysis", "Systematic Review"]},
                    {"title": "Guideline of guidelines: radioligand therapy", "pubtype": ["Journal Article"]},
                    {"title": "x", "pubtype": ["review-article"]},                       # grafia Europe PMC
                    {"title": "Plain language summary", "pubtype": ["Patient Education Handout"]}):
            self.assertEqual(DS.pre_acao(pub)[0], "NO_ACTION", pub)

    def test_documento_regulatorio_nao_e_descartado(self):
        a, _, _ = DS.pre_acao({"title": "FDA Approval Summary: drug A for metastatic disease",
                               "pubtype": ["Journal Article", "Review"]})
        self.assertIsNone(a)                                          # vai para o curator

    def test_protocolo_reconhecido_antes_do_llm(self):
        self.assertEqual(DS.pre_acao({"title": "Trial X: study protocol for a randomised phase II trial",
                                      "pubtype": ["Journal Article"]}),
                         ("STORE_SOURCE", DS.pre_acao({"title": "a study protocol", "pubtype": []})[1], "PROTOCOL"))
        self.assertEqual(DS.pre_acao({"title": "x", "pubtype": ["Clinical Trial Protocol"]})[2], "PROTOCOL")

    def test_sinal_pooled_so_por_texto_explicito(self):
        self.assertTrue(DS.sinal_pooled("Data were pooled from five phase 3 trials", None, ["NCT1"]))
        self.assertTrue(DS.sinal_pooled("An individual patient data meta-analysis of 3 trials"))
        for frase in ("Pooled central mutation test data from nine global clinical trials were analyzed",
                      "Deidentified datasets from 8 clinical trials were accessed",
                      "Patient-level data from the TRIAL-A (NCT1) and TRIAL-B (NCT2) trials were used",
                      "A matching-adjusted indirect comparison of drug A versus drug B"):
            self.assertTrue(DS.sinal_pooled(frase), frase)
        self.assertIsNone(DS.sinal_pooled("Patients were randomised in the phase 3 trial."))
        # plataforma: comparações do mesmo protocolo registrado não são multi-estudo
        txt = "Data from 7129 patients from five trials of the multi-arm, multistage platform were analysed."
        self.assertIsNone(DS.sinal_pooled(txt, ["NCT00268476"], ["NCT00268476"]))
        self.assertIsNone(DS.sinal_pooled("Patients from five comparisons were pooled.", [], ["NCT1"], card_plataforma=True))
        # braços agregados dentro de um único ensaio não são multi-estudo
        self.assertIsNone(DS.sinal_pooled("A pooled treatment arm analysis of the randomised trial."))
        # o mesmo estudo registrado em NCT e ISRCTN continua sendo a mesma plataforma
        self.assertIsNone(DS.sinal_pooled("Data from five trials of the platform (ISRCTN78818544) were analysed.",
                                          ["NCT00268476"], ["NCT00268476"], card_plataforma=True))
        # mas plataforma + outro registro citado no texto é multi-estudo
        self.assertTrue(DS.sinal_pooled(txt + " External data from NCT09999999 were added.", ["NCT00268476"], ["NCT00268476"]))
        # outro registro no DataBank, plataforma, vários braços ou citação cruzada NÃO bastam
        self.assertIsNone(DS.sinal_pooled("single trial", ["NCT1", "NCT9"], ["NCT1"]))
        self.assertIsNone(DS.sinal_pooled("STAMPEDE is a multi-arm, multistage platform protocol with several comparisons"))
        self.assertIsNone(DS.sinal_pooled("Results were consistent with those of the phase 2 study (NCT0000009)."))

    def test_custo_efetividade_e_relato_de_caso_antes_do_llm(self):
        self.assertEqual(DS.pre_acao({"title": "Cost-effectiveness of drug A in first-line NSCLC",
                                      "pubtype": ["Journal Article", "Randomized Controlled Trial"]})[0], "NO_ACTION")
        self.assertEqual(DS.pre_acao({"title": "A Markov model analysis of drug A", "pubtype": ["Journal Article"]})[0],
                         "NO_ACTION")
        self.assertEqual(DS.pre_acao({"title": "Successful rechallenge: a case report",
                                      "pubtype": ["Case Reports", "Journal Article"]})[0], "NO_ACTION")

    def test_outro_ensaio_apenas_citado_pelo_registro(self):
        self.assertTrue(DS.outro_ensaio_citado({"via": ["ctgov_ref:NCT1"], "ctgov_type": "BACKGROUND"}, ["NCT1"]))
        self.assertTrue(DS.outro_ensaio_citado({"via": ["europepmc:NCT1"], "databank": ["NCT9"]}, ["NCT1"]))
        self.assertFalse(DS.outro_ensaio_citado({"via": ["pubmed_si:NCT1"], "databank": ["NCT9"]}, ["NCT1"]))
        self.assertFalse(DS.outro_ensaio_citado({"via": ["ctgov_ref:NCT1"], "ctgov_type": "RESULT"}, ["NCT1"]))
        self.assertFalse(DS.outro_ensaio_citado({"via": ["europepmc:NCT1"], "databank": ["NCT1", "NCT9"]}, ["NCT1"]))

    def test_pre_acao_por_tipo_de_publicacao(self):
        self.assertEqual(DS.pre_acao({"pubtype": ["Comment", "Letter"]})[0], "NO_ACTION")
        self.assertEqual(DS.pre_acao({"pubtype": ["Editorial"]})[0], "NO_ACTION")
        self.assertEqual(DS.pre_acao({"pubtype": ["Retraction of Publication"]})[0], "HUMAN_REVIEW")
        self.assertEqual(DS.pre_acao({"source": "PPR", "pubtype": []})[0], "WATCH")
        self.assertIsNone(DS.pre_acao({"pubtype": ["Journal Article", "Randomized Controlled Trial"]})[0])
        # carta que é ensaio clínico não é descartada como comentário
        self.assertIsNone(DS.pre_acao({"pubtype": ["Letter", "Clinical Trial"]})[0])

    def test_conhecidos_do_card_e_dos_secundarios(self):
        card = {"uid": "u1", "pubmed_url": "https://pubmed.ncbi.nlm.nih.gov/111/", "ref": "doi:10.1056/NEJMoa2000001. PMID: 5555555"}
        secs = [{"id": "s1", "parentUid": "u1", "pmid": "777", "doi": "10.1016/S1470-2045(23)00001-1", "sourceUrl": ""},
                {"id": "s2", "parentUid": "outro", "pmid": "888", "doi": "10.4/no"}]
        k = DS.conhecidos(card, secs)
        self.assertEqual(k["pmids"], {"111", "5555555", "777"})
        self.assertEqual(k["dois"], {"10.1056/nejmoa2000001", "10.1016/s1470-2045(23)00001-1"})
        self.assertEqual(k["origem"]["777"], "secundário s1")

    def test_registros_so_ids_de_registro(self):
        self.assertEqual(DS.registros({"nct": "NCT01234567 / ACTRN12615000912583", "ref": "EudraCT 2015-001234-56"}),
                         ["NCT01234567", "ACTRN12615000912583", "2015-001234-56"])

    def test_vocabulario_e_regras_de_acao(self):
        self.assertEqual(set(DS.ACOES_DA_RELACAO), set(T.DISCOVERY_RELATIONS))
        self.assertEqual(DS.ACOES_DA_RELACAO["UNRELATED"], {"NO_ACTION"})
        self.assertNotIn("UPDATE_CARD", DS.ACOES_DA_RELACAO["SECONDARY_ANALYSIS"])
        self.assertNotIn("UPDATE_CARD", DS.ACOES_DA_RELACAO["UNDETERMINED"])
        self.assertIn("NO_ACTION", DS.ACOES_DA_RELACAO["NEW_COHORT"])       # outras coortes de basket


class Conferir(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.antigo = DS.DISC
        DS.DISC = pathlib.Path(self.tmp.name)
        pasta = DS.DISC / "u1"
        (pasta / "fontes").mkdir(parents=True)
        fontes = []
        for sid, pars in {"pmid:222:abstract": [("Title", "Trial X: final overall survival analysis"),
                                                 ("Abstract > Results", "At a median follow-up of 60.2 months, 400 patients were analysed.")],
                          "pmid:333:abstract": [("Title", "A narrative review citing trial X"),
                                                ("Abstract", "We review phase 3 trials including NCT00000001.")],
                          "pmid:555:abstract": [("Title", "Trial X: second interim analysis"),
                                                ("Abstract", "We report updated efficacy data from the second interim analysis.")],
                          "pmid:666:abstract": [("Title", "Trial X: study protocol for a randomised phase 3 trial"),
                                                ("Abstract", "This is the protocol of trial X (NCT00000001).")],
                          "pmid:777:abstract": [("Title", "Pooled analysis of five trials of drug A"),
                                                ("Abstract", "Data were pooled from five phase 3 trials, including trial X.")]}.items():
            p = S.gravar_fonte(pasta / "fontes", sid, pars)
            fontes.append({"source_id": sid, "source_type": "pubmed_abstract", "text_level": "abstract",
                           "path": f"fontes/{p.name}"})
        pacote = {"packet_sha256": "h", "sources": fontes,
                  "candidates": [{"candidate_id": "pmid:222", "in_llm": True}, {"candidate_id": "pmid:333", "in_llm": True},
                                 {"candidate_id": "pmid:444", "in_llm": True},
                                 {"candidate_id": "pmid:555", "in_llm": True, "older_than_represented": True},
                                 {"candidate_id": "pmid:666", "in_llm": True,
                                  "title": "Trial X: study protocol for a randomised phase 3 trial"},
                                 {"candidate_id": "pmid:777", "in_llm": True, "pooled_signal": "texto: 'Data were pooled'"}]}
        (pasta / "packet.json").write_text(json.dumps(pacote))

    def tearDown(self):
        DS.DISC = self.antigo
        self.tmp.cleanup()

    def ev(self, cid, snip, par="¶0002"):
        return [{"source_id": f"{cid}:abstract", "source_type": "pubmed_abstract", "locator": par, "snippet": snip}]

    def test_casos(self):
        rep = sig()
        cur = {"represented_signature": rep, "candidates": [
            {"candidate_id": "pmid:222", "relation": "LONG_TERM_FOLLOWUP", "action": "UPDATE_CARD",
             "candidate_signature": sig(publication_id="pmid:222", data_cutoff="2024-06", analysis_type="final",
                                        follow_up_median_months=60.2, sample_size=401), "comparison": comp(),
             "evidence": self.ev("pmid:222", "At a median follow-up of 60.2 months, 400 patients were analysed.")},
            {"candidate_id": "pmid:333", "relation": "UNRELATED", "action": "ADD_SECONDARY",
             "candidate_signature": sig(trial_key=None, population="patients in many trials"),
             "comparison": comp(population="different", publication_role="different"),
             "evidence": self.ev("pmid:333", "texto que não existe na fonte")},
            {"candidate_id": "pmid:999", "relation": "UNDETERMINED", "action": "WATCH", "candidate_signature": {},
             "evidence": []},
        ]}
        r = DS.conferir("u1", cur)
        codes = {k: {a["code"] for a in v["achados"]} for k, v in r.items()}
        # ação incompatível com UNRELATED e trecho inexistente
        self.assertIn("ACTION_INCOMPATIBLE", codes["pmid:333"])
        self.assertIn("SNIPPET_NOT_FOUND", codes["pmid:333"])
        self.assertEqual(r["pmid:333"]["verdict"], "FAIL")
        # candidato fora da fila e candidato da fila não classificado
        self.assertIn("CANDIDATE_UNKNOWN", codes["pmid:999"])
        self.assertEqual(r["pmid:444"]["achados"][0]["code"], "NOT_CLASSIFIED")

    def cand(self, cid, rel, acao, snip, **kw):
        return {"candidate_id": cid, "relation": rel, "action": acao, "comparison": kw.pop("comparison", comp()),
                "candidate_signature": sig(publication_id=cid, **kw), "evidence": self.ev(cid, snip)}

    def test_corte_anterior_e_same_analysis_prior_superseded_store_source(self):
        snip = "We report updated efficacy data from the second interim analysis."
        ok = DS.conferir("u1", {"represented_signature": sig(), "candidates": [
            self.cand("pmid:555", "SAME_ANALYSIS", "STORE_SOURCE", snip, comparison=comp(timepoint="different"))]})
        self.assertEqual(ok["pmid:555"]["verdict"], "PASS")
        cur = {"represented_signature": sig(), "candidates": [
            self.cand("pmid:555", "SAME_ANALYSIS", "STORE_SOURCE", snip, comparison=comp(timepoint="different"))]}
        DS.conferir("u1", cur)
        self.assertEqual(cur["candidates"][0]["_temporal_marker"], "PRIOR_SUPERSEDED")
        ruim = DS.conferir("u1", {"represented_signature": sig(), "candidates": [
            self.cand("pmid:555", "SAME_ANALYSIS_UPDATE", "UPDATE_CARD", snip)]})["pmid:555"]
        self.assertIn("PRIOR_AS_UPDATE", {a["code"] for a in ruim["achados"]})
        self.assertEqual(ruim["verdict"], "FAIL")

    def test_protocolo_do_proprio_estudo_nao_e_unrelated(self):
        r = DS.conferir("u1", {"represented_signature": sig(), "candidates": [
            self.cand("pmid:666", "UNRELATED", "NO_ACTION", "This is the protocol of trial X (NCT00000001).",
                      comparison=comp(population="undetermined", publication_role="different"))]})["pmid:666"]
        self.assertIn("PROTOCOL_AS_UNRELATED", {a["code"] for a in r["achados"]})
        self.assertEqual(r["verdict"], "FAIL")
        ok = DS.conferir("u1", {"represented_signature": sig(), "candidates": [
            self.cand("pmid:666", "PROTOCOL", "STORE_SOURCE", "This is the protocol of trial X (NCT00000001).",
                      comparison=comp(publication_role="different"))]})["pmid:666"]
        self.assertEqual(ok["verdict"], "PASS")

    def test_pooled_nao_gera_add_secondary(self):
        snip = "Data were pooled from five phase 3 trials, including trial X."
        r = DS.conferir("u1", {"represented_signature": sig(), "candidates": [
            self.cand("pmid:777", "SECONDARY_ANALYSIS", "ADD_SECONDARY", snip,
                      comparison=comp(population="different"))]})["pmid:777"]
        codes = {a["code"] for a in r["achados"]}
        self.assertTrue({"POOLED_ADD_SECONDARY", "POOLED_AS_SECONDARY"} <= codes)
        self.assertEqual(r["verdict"], "FAIL")
        ok = DS.conferir("u1", {"represented_signature": sig(), "candidates": [
            self.cand("pmid:777", "POOLED_ANALYSIS", "STORE_SOURCE", snip, comparison=comp(population="different"))]})
        self.assertEqual(ok["pmid:777"]["verdict"], "PASS")

    def test_n_sem_trecho_nao_entra_na_assinatura(self):
        c = self.cand("pmid:222", "LONG_TERM_FOLLOWUP", "STORE_SOURCE",
                      "At a median follow-up of 60.2 months, 400 patients were analysed.",
                      sample_size=401, follow_up_median_months=60.2,
                      arms=[{"label": "A", "role": "experimental", "n": 200}, {"label": "B", "role": "control", "n": 400}])
        DS.sanear_assinatura(c)
        s = c["candidate_signature"]
        self.assertIsNone(s["sample_size"])                         # 401 não está no trecho
        self.assertEqual(s["follow_up_median_months"], 60.2)        # 60.2 está
        self.assertIsNone(s["arms"][0]["n"])
        self.assertEqual(s["arms"][1]["n"], 400)
        self.assertEqual(c["_not_verified"], ["sample_size", "arms[0].n"])
        self.assertEqual(c["_original_values"]["sample_size"], 401)

    def test_update_exige_mesma_analise_na_comparacao(self):
        cur = {"represented_signature": sig(), "candidates": [
            {"candidate_id": "pmid:222", "relation": "SAME_ANALYSIS_UPDATE", "action": "UPDATE_CARD",
             "candidate_signature": sig(publication_id="pmid:222", data_cutoff="2024-06"),
             "comparison": comp(endpoint="different"),        # ex.: card mostra PFS, candidato traz OS
             "evidence": self.ev("pmid:222", "At a median follow-up of 60.2 months, 400 patients were analysed.")}]}
        r = DS.conferir("u1", cur)["pmid:222"]
        msgs = " ".join(a["detail"] for a in r["achados"] if a["code"] == "RELATION_COMPARISON_MISMATCH")
        self.assertIn("SAME_ANALYSIS_UPDATE exige mesma análise", msgs)
        self.assertIn("UPDATE_CARD exige", msgs)
        self.assertEqual(r["verdict"], "CONFLICT")
        cur["candidates"][0]["comparison"] = comp(population="undetermined")     # falta de informação ≠ contradição
        self.assertEqual(DS.conferir("u1", cur)["pmid:222"]["verdict"], "UNSUPPORTED")

    def test_update_com_analysis_set_indeterminado_nao_e_barrado(self):
        cur = {"represented_signature": sig(), "candidates": [
            self.cand("pmid:222", "LONG_TERM_FOLLOWUP", "UPDATE_CARD",
                      "At a median follow-up of 60.2 months, 400 patients were analysed.",
                      comparison=comp(analysis_set="undetermined"), analysis_set=None)]}
        r = DS.conferir("u1", cur)["pmid:222"]
        self.assertEqual(r["verdict"], "PASS")
        self.assertIn("ANALYSIS_SET_UNDETERMINED", {a["code"] for a in r["achados"]})
        # continua indeterminado: nada é convertido em "same" nem em ITT
        self.assertEqual(cur["candidates"][0]["comparison"]["analysis_set"]["status"], "undetermined")
        self.assertIsNone(cur["candidates"][0]["candidate_signature"]["analysis_set"])
        # analysis set DIFERENTE continua barrando
        cur["candidates"][0]["comparison"] = comp(analysis_set="different")
        self.assertEqual(DS.conferir("u1", cur)["pmid:222"]["verdict"], "CONFLICT")

    def test_card_integrado_admite_subgrupo_do_mesmo_conjunto(self):
        pac = json.loads((DS.DISC / "u1" / "packet.json").read_text())
        p = S.gravar_fonte(DS.DISC / "u1" / "fontes", "pmid:111:abstract",
                           [("Title", "Integrated analysis"), ("Abstract", "Data were pooled from three phase 1/2 trials.")])
        pac["sources"].append({"source_id": "pmid:111:abstract", "source_type": "pubmed_abstract",
                               "text_level": "abstract", "path": f"fontes/{p.name}", "role": "represented"})
        (DS.DISC / "u1" / "packet.json").write_text(json.dumps(pac))
        r = DS.conferir("u1", {"represented_signature": sig(), "candidates": [
            self.cand("pmid:777", "SUBGROUP", "ADD_SECONDARY", "Data were pooled from five phase 3 trials, including trial X.",
                      comparison=comp(population="different"))]})["pmid:777"]
        self.assertEqual(r["verdict"], "PASS")

    def test_pooled_sem_frase_de_agregacao_nao_passa(self):
        r = DS.conferir("u1", {"represented_signature": sig(), "candidates": [
            self.cand("pmid:222", "POOLED_ANALYSIS", "STORE_SOURCE",
                      "At a median follow-up of 60.2 months, 400 patients were analysed.",
                      comparison=comp(population="different"))]})["pmid:222"]
        self.assertIn("POOLED_WITHOUT_TEXT", {a["code"] for a in r["achados"]})
        self.assertEqual(r["verdict"], "UNSUPPORTED")

    def test_texto_livre_da_assinatura_diferente_nao_gera_conflito(self):
        cur = {"represented_signature": sig(population="adults with disease y"), "candidates": [
            {"candidate_id": "pmid:222", "relation": "LONG_TERM_FOLLOWUP", "action": "UPDATE_CARD",
             "candidate_signature": sig(population="Adultos com doença y", publication_id="pmid:222",
                                        data_cutoff="2024-06", analysis_type="final"),
             "comparison": comp(),
             "evidence": self.ev("pmid:222", "At a median follow-up of 60.2 months, 400 patients were analysed.")}]}
        self.assertEqual(DS.conferir("u1", cur)["pmid:222"]["verdict"], "PASS")

    def test_comparacao_incompleta_e_timepoint_igual(self):
        c = comp(); del c["arms"]
        self.assertIn("comparação incompleta", DS.coerencia("SUBGROUP", "ADD_SECONDARY", {k: v["status"] for k, v in c.items()})[0])
        self.assertTrue(any("mesmo timepoint" in m for m in
                            DS.coerencia("LONG_TERM_FOLLOWUP", "UPDATE_CARD", {k: v["status"] for k, v in comp(timepoint="same").items()})))

    def test_update_compativel_passa(self):
        cur = {"represented_signature": sig(), "candidates": [
            {"candidate_id": "pmid:222", "relation": "LONG_TERM_FOLLOWUP", "action": "UPDATE_CARD",
             "candidate_signature": sig(publication_id="pmid:222", data_cutoff="2024-06", analysis_type="final",
                                        follow_up_median_months=60.2), "comparison": comp(),
             "evidence": self.ev("pmid:222", "At a median follow-up of 60.2 months, 400 patients were analysed.")}]}
        self.assertEqual(DS.conferir("u1", cur)["pmid:222"]["verdict"], "PASS")

    def test_unrelated_nao_e_recalculado_pela_assinatura(self):
        cur = {"represented_signature": sig(), "candidates": [
            {"candidate_id": "pmid:333", "relation": "UNRELATED", "action": "NO_ACTION",
             "candidate_signature": sig(population="older adults", publication_id="pmid:333"),
             "comparison": comp(population="different", arms="different", publication_role="different"),
             "evidence": self.ev("pmid:333", "We review phase 3 trials including NCT00000001.")}]}
        self.assertEqual(DS.conferir("u1", cur)["pmid:333"]["verdict"], "PASS")


class Isolamento(unittest.TestCase):
    def test_discovery_nao_escreve_no_database(self):
        codigo = (AG / "discovery.py").read_text(encoding="utf-8")
        self.assertNotIn("DATA_JS.write", codigo)
        self.assertNotIn("secondary-cards.js\").write", codigo)
        self.assertIn('DISC = S.STATE / "discovery"', codigo)


if __name__ == "__main__":
    unittest.main()


class Retomada(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.orig = (DS.DISC, DS.cards, DS.PIPELINE_VERSION, DS.MAX_LLM)
        DS.DISC = pathlib.Path(self.tmp.name)
        self.card = {"uid": "u1", "estudo": "X"}
        DS.cards = lambda: {"u1": self.card}
        self.chamadas = []

        def coleta(u):
            self.chamadas.append(("coleta", u))
            (DS.DISC / u).mkdir(parents=True, exist_ok=True)
            (DS.DISC / u / "packet.json").write_text(json.dumps({"candidates": [{"in_llm": True}]}))
            return {"packet_sha256": "p"}

        def etapa(nome):
            def f(u):
                self.chamadas.append((nome, u))
                return {"sha256": nome}
            return f
        self.etapas = {"coleta": coleta, "curator": etapa("curator"), "verifier": etapa("verifier")}

    def tearDown(self):
        DS.DISC, DS.cards, DS.PIPELINE_VERSION, DS.MAX_LLM = self.orig
        self.tmp.cleanup()

    def test_resume_reaproveita_estado_compativel(self):
        r1 = DS.executar_lote(["u1"], etapas=self.etapas)
        self.assertEqual(r1[0]["etapas_executadas"], ["coleta", "curator", "verifier"])
        r2 = DS.executar_lote(["u1"], etapas=self.etapas)
        self.assertEqual(r2[0]["estado_inicial"], "compativel")
        self.assertEqual(r2[0]["etapas_executadas"], [])
        self.assertEqual(len(self.chamadas), 3)

    def test_interrupcao_retoma_da_etapa_seguinte(self):
        def quebra(u):
            raise RuntimeError("sessão caiu")
        DS.executar_lote(["u1"], etapas={**self.etapas, "verifier": quebra})
        r = DS.executar_lote(["u1"], etapas=self.etapas)
        self.assertEqual(r[0]["etapas_executadas"], ["verifier"])      # coleta e curator não são refeitos

    def test_mudanca_de_versao_config_ou_card_invalida(self):
        DS.executar_lote(["u1"], etapas=self.etapas)
        DS.PIPELINE_VERSION = "discovery/999"
        r = DS.executar_lote(["u1"], etapas=self.etapas)
        self.assertEqual(r[0]["estado_inicial"], "invalidado")
        self.assertEqual(r[0]["invalidado_por"], ["pipeline_version"])
        self.assertEqual(r[0]["etapas_executadas"], ["coleta", "curator", "verifier"])
        DS.MAX_LLM = DS.MAX_LLM + 1
        self.assertEqual(DS.executar_lote(["u1"], etapas=self.etapas)[0]["invalidado_por"], ["config_sha"])
        self.card["estudo"] = "X (atualizado)"
        self.assertEqual(DS.executar_lote(["u1"], etapas=self.etapas)[0]["invalidado_por"], ["card_fingerprint"])


class FilaPorCard(unittest.TestCase):
    def linha(self, uid, pmid, acao, verdict="PASS"):
        return {"uid": uid, "trial": uid.upper(), "pmid": pmid, "doi": None, "title": f"t{pmid}", "date": None,
                "relation": None, "action": acao, "final_verdict": verdict}

    def test_unidade_de_revisao_e_o_card(self):
        L = [self.linha("a", "1", "STORE_SOURCE"), self.linha("a", "2", "STORE_SOURCE"),
             self.linha("a", "3", "NO_ACTION"), self.linha("a", "4", "WATCH"),
             self.linha("a", "5", "ADD_SECONDARY"), self.linha("a", "6", "ADD_SECONDARY"),
             self.linha("a", "7", "UPDATE_CARD"), self.linha("a", "8", "UPDATE_CARD", "UNSUPPORTED"),
             self.linha("b", "9", "STORE_SOURCE", "FAIL"), self.linha("b", "10", "HUMAN_REVIEW"),
             self.linha("c", "11", "NO_ACTION"), self.linha("c", "12", "STORE_SOURCE")]
        f = DS.fila_por_card(L)
        self.assertEqual([x["pmid"] for x in f["fontes_auto_registradas"]], ["1", "2", "12"])   # STORE_SOURCE PASS
        self.assertEqual(set(f["cards"]), {"a", "b"})                                           # c: nada a decidir
        self.assertEqual(sorted(f["cards"]["a"]["pacotes"]), ["ADD_SECONDARY", "UPDATE_CARD"])
        self.assertEqual(len(f["cards"]["a"]["pacotes"]["UPDATE_CARD"]), 2)                     # 1 decisão, 2 fontes
        self.assertEqual(sorted(f["cards"]["b"]["pacotes"]), ["HUMAN_REVIEW"])                  # sem PASS + HUMAN_REVIEW
        self.assertEqual(f["resumo"]["decisoes_humanas"], 3)
        self.assertEqual(f["resumo"]["publicacoes_em_revisao"], 6)


class DiscoveryV3(unittest.TestCase):
    """Regras da versão 3: pooled só com combinação explícita, basket, pré-clínico/resumo leigo, regulatório."""
    POOLED_SIM = ["Data were combined from PORTEC-1 and PORTEC-2.",
                  "Individual patient data (IPD) from entrectinib trials were analysed.",
                  "Tumour samples from three trials were analysed.",
                  "Deidentified datasets from 8 clinical trials were accessed.",
                  "We present integrated data of entrectinib from the STARTRK-NG, TAPISTRY, and STARTRK-2 trials.",
                  "Pooled, retrospective analysis of data from phase 3 trials.",
                  "Safety was evaluated in patients pooled across all 4 clinical studies.",
                  "The model was based on 2993 subjects from five clinical trials.",
                  "Pyrexia in patients treated with dabrafenib plus trametinib across clinical trials.",
                  "Data from 3 clinical trials (NCT1, NCT2, NCT3) were used; ORR was 30% and 40%, respectively."]
    POOLED_NAO = ["Data from the PALOMA-2 (NCT01740427) and PALOMA-3 studies were analysed separately.",
                  "Patients enrolled in the double-blind, placebo-controlled randomised clinical trials received drug A.",
                  "A joint analysis of PALOMA-2 and PALOMA-3.",
                  "A pooled treatment arm analysis of the randomised trial.",
                  "We previously evaluated TFS in a pooled analysis of trials A and B. Here we report trial A.",
                  "ENCO300 (parts 1 and 2) data were combined, per protocol, for PFS analysis.",
                  "Solid tumors across seven cohorts of the phase 2 basket trial.",
                  "PFS was 10 and 12 months in arms A and B, respectively, in this phase 3 trial."]

    def test_pooled_so_com_combinacao_explicita(self):
        for s in self.POOLED_SIM:
            self.assertTrue(DS.sinal_pooled(s), s)
        for s in self.POOLED_NAO:
            self.assertIsNone(DS.sinal_pooled(s), s)

    def test_plataforma_e_mesmo_estudo_em_dois_registros(self):
        txt = "Post-hoc analysis of data from five phase 3 trials (STAMPEDE platform protocol, ISRCTN78818544)."
        self.assertIsNone(DS.sinal_pooled(txt, ["NCT00268476"], ["NCT00268476"], card_plataforma=True))

    def test_grupos_de_tumor(self):
        self.assertEqual(DS.grupos_tumor("pembrolizumab in small cell lung cancer"), {"pulmao_pc"})
        self.assertEqual(DS.grupos_tumor("SCLC and non-small cell lung cancer"), {"pulmao_pc", "pulmao"})
        self.assertNotIn("colorretal", DS.grupos_tumor("noncolorectal and non-colorectal MSI-H cancers"))
        self.assertIn("biliar", DS.grupos_tumor("KEYNOTE-158 BTC cohort"))

    def test_preclinico_e_resumo_leigo_antes_do_llm(self):
        for t in ("Antitumor activity of drug X in mouse xenograft models",
                  "Novel in Vivo and in Vitro PK/PD-Based Human Starting Dose Selection for Drug X",
                  "Plain language summary of the TRIAL-X results", "A lay summary of trial X"):
            self.assertEqual(DS.pre_acao({"title": t, "pubtype": ["Journal Article", "Clinical Trial, Phase I"]})[0],
                             "NO_ACTION", t)
        # título que anuncia dado clínico segue para o curator
        self.assertIsNone(DS.pre_acao({"title": "Activity of drug X in brain metastases: preclinical models and "
                                                "clinical data from patients", "pubtype": ["Journal Article"]})[0])

    def test_regulatorio_continua_elegivel(self):
        for t in ("FDA Approval Summary: drug X for RET fusion cancers",
                  "US Food and Drug Administration Approval Summary: drug Y"):
            self.assertIsNone(DS.pre_acao({"title": t, "pubtype": ["Journal Article", "Review"]})[0], t)


class BasketOutraCoorte(Conferir):
    def preparar(self, card, titulo, texto):
        pac = json.loads((DS.DISC / "u1" / "packet.json").read_text())
        p = S.gravar_fonte(DS.DISC / "u1" / "fontes", "pmid:888:abstract", [("Title", titulo), ("Abstract", texto)])
        pac["sources"].append({"source_id": "pmid:888:abstract", "source_type": "pubmed_abstract",
                               "text_level": "abstract", "path": f"fontes/{p.name}"})
        pac["candidates"].append({"candidate_id": "pmid:888", "in_llm": True, "title": titulo})
        pac["card"] = card
        (DS.DISC / "u1" / "packet.json").write_text(json.dumps(pac))
        return texto

    def rodar(self, texto, rel="POOLED_ANALYSIS", acao="STORE_SOURCE"):
        return DS.conferir("u1", {"represented_signature": sig(), "candidates": [
            self.cand("pmid:888", rel, acao, texto, comparison=comp(population="different"))]})["pmid:888"]

    def test_pooled_de_outra_coorte_nao_e_registrado_automaticamente(self):
        card = {"estudo": "KEYNOTE-158 cervical cohort", "desenho": "Coorte cérvix do basket KN-158", "indicacao": "Cérvix"}
        txt = self.preparar(card, "Pembrolizumab for small cell lung cancer: pooled KEYNOTE-028 and KEYNOTE-158",
                            "Data were pooled from two trials of patients with small cell lung cancer.")
        r = self.rodar(txt)
        self.assertIn("BASKET_OTHER_COHORT", {a["code"] for a in r["achados"]})
        self.assertEqual(r["verdict"], "UNSUPPORTED")

    def test_analise_mae_multi_tumor_e_coorte_do_card_nao_sao_marcadas(self):
        card = {"estudo": "KEYNOTE-158 BTC cohort (tumor-agnóstico)", "desenho": "Coorte biliar do basket",
                "indicacao": "Câncer biliar MSI-H"}
        txt = self.preparar(card, "Pembrolizumab in MSI-H noncolorectal cancers: updated analysis",
                            "Data were pooled from cohorts including endometrial and gastric cancer patients across two trials.")
        self.assertNotIn("BASKET_OTHER_COHORT", {a["code"] for a in self.rodar(txt)["achados"]})

    def test_card_agnostico_nao_aplica_a_regra(self):
        card = {"estudo": "Larotrectinibe NTRK", "indicacao": "Tumores sólidos com fusão NTRK", "desenho": "pooled de 3 estudos"}
        txt = self.preparar(card, "Larotrectinib in sarcoma", "Data were pooled from three trials of sarcoma patients.")
        self.assertNotIn("BASKET_OTHER_COHORT", {a["code"] for a in self.rodar(txt, "SUBGROUP", "ADD_SECONDARY")["achados"]})
