"""Testes da expansão de cobertura (new_trial_discovery.py). Offline, dados sintéticos, sem LLM.

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
import delta as DL  # noqa: E402
import discovery as DS  # noqa: E402
import new_trial_discovery as NT  # noqa: E402
import sources as S  # noqa: E402

CARDS = {
    "u_alfa": {"uid": "u_alfa", "estudo": "ALPHA-301 (2022)", "acron": "ALPHA-301", "nct": "NCT01111111",
               "titulo_full": "Drug A versus placebo in metastatic gastric adenocarcinoma", "category_id": "esofago_egj",
               "pubmed_url": "https://pubmed.ncbi.nlm.nih.gov/30000001/", "citation": {"pmid": "30000001", "doi": "10.1/abc"}},
    "u_beta": {"uid": "u_beta", "estudo": "BRAVO (2021)", "acron": "BRAVO", "nct": "NCT02222222",
               "titulo_full": "Radioligand therapy in neuroendocrine tumours", "category_id": "net_gep"},
}
SECS = [{"id": "sec1", "parentUid": "u_beta", "pmid": "30000009", "doi": "10.9/sec"}]


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.orig = (NT.DIR, DS.cards, DS.secundarios)
        NT.DIR = pathlib.Path(self.tmp.name)
        DS.cards = lambda: CARDS
        DS.secundarios = lambda: SECS
        self.idx = NT.indice()

    def tearDown(self):
        NT.DIR, DS.cards, DS.secundarios = self.orig
        self.tmp.cleanup()


class Isolamento(unittest.TestCase):
    def test_versao_propria_sem_tocar_discovery_e_delta(self):
        self.assertTrue(NT.versao().startswith("novos/1+"))
        for f in NT.ARQUIVOS_VERSAO:
            if f.startswith("new_trial") or f.startswith("novos") or "novos" in f:
                self.assertNotIn(f, DS.ARQUIVOS_PIPELINE)
                self.assertNotIn(f, DL.ARQUIVOS_VERSAO)

    def test_schemas_versionados_em_sincronia(self):
        for nome, s in NT.SCHEMAS.items():
            self.assertEqual(json.loads((AG / "schemas" / nome).read_text()), s, nome)

    def test_nao_escreve_no_database_publicado(self):
        codigo = (AG / "new_trial_discovery.py").read_text(encoding="utf-8").split('"""', 2)[2]   # sem o docstring
        for proibido in ("assets/js", "secondary-cards.js\"", "app-data", "DATA_JS", "explorer.json", "tracker.json"):
            self.assertNotIn(proibido, codigo)

    def test_runner_mapeia_os_papeis_para_as_definicoes_versionadas(self):
        t = (AG / "run_agents.py").read_text()
        self.assertIn('"novos_curator": "database-curator"', t)
        self.assertIn('"novos_verifier": "database-verifier"', t)


class Dedup(Base):
    def cls(self, **c):
        return NT.deduplicar({"pmids": [], "dois": [], **c}, self.idx)["classe"]

    def test_registro_pmid_doi_ja_existentes(self):
        self.assertEqual(self.cls(nct="NCT01111111"), "ALREADY_EXISTS")
        self.assertEqual(self.cls(nct="NCT09999999", pmids=["30000001"]), "ALREADY_EXISTS")
        self.assertEqual(self.cls(nct="NCT09999999", pmids=["30000009"]), "ALREADY_EXISTS")      # PMID de secundária
        self.assertEqual(self.cls(nct="NCT09999999", dois=["10.1/ABC"]), "ALREADY_EXISTS")

    def test_acronimo_igual_com_outro_registro_e_possivel_duplicata(self):
        self.assertEqual(self.cls(nct="NCT09999999", acronym="Alpha-301"), "POSSIBLE_DUPLICATE")

    def test_acronimo_derivado_so_e_relacionado_se_for_extensao(self):
        self.assertEqual(self.cls(nct="NCT09999998", acronym="ALPHA-301-LTE", title="Long-term extension of ALPHA-301 "
                                  "in gastric cancer"), "RELATED_TO_EXISTING")
        r = NT.deduplicar({"pmids": [], "dois": [], "nct": "NCT09999995", "acronym": "ALPHA-3015",
                           "title": "Drug B in gastric cancer"}, self.idx)
        self.assertEqual(r["classe"], "NEW_STUDY_CANDIDATE")          # ensaio irmão: vai ao curator com a dica
        self.assertTrue(any("família" in d for d in r["dicas"]))

    def test_acronimo_homonimo_de_outro_tumor_nao_e_duplicata(self):
        r = NT.deduplicar({"pmids": [], "dois": [], "nct": "NCT09999994", "acronym": "BRAVO",
                           "title": "Drug C in chronic lymphocytic leukemia", "conditions": ["Chronic Lymphocytic Leukemia"]},
                          self.idx)
        self.assertEqual(r["classe"], "NEW_STUDY_CANDIDATE")
        self.assertTrue(any("homônimo" in d for d in r["dicas"]))

    def test_titulo_muito_parecido(self):
        # sem registro para desempatar (publicação sem NCT): possível duplicata
        self.assertEqual(self.cls(title="Drug A versus placebo in metastatic gastric adenocarcinoma"), "POSSIBLE_DUPLICATE")
        # com NCT próprio e o card com outro registro: ensaio diferente, segue com a dica
        self.assertEqual(self.cls(nct="NCT09999997", title="Drug A versus placebo in metastatic gastric adenocarcinoma"),
                         "NEW_STUDY_CANDIDATE")

    def test_publicacao_primaria_sem_tipo_indexado(self):
        pubs = [{"pmid": "1", "title": "Oral vinorelbine in mesothelioma (VIM): a randomised phase 2 trial",
                 "pubtypes": ["Journal Article"], "abstract": True},
                {"pmid": "2", "title": "Emerging drugs in mesothelioma", "pubtypes": ["Journal Article", "Review"],
                 "abstract": True}]
        self.assertEqual(NT.principal({}, pubs)["pmid"], "1")

    def test_novo_de_verdade(self):
        self.assertEqual(self.cls(nct="NCT09999996", acronym="ZETA", title="Drug Z in soft tissue sarcoma"),
                         "NEW_STUDY_CANDIDATE")


class Filtro(unittest.TestCase):
    def f(self, prim=True, **c):
        base = {"nct": "NCT1", "title": "Drug X in advanced gastric cancer", "phases": ["PHASE3"],
                "allocation": "RANDOMIZED", "purpose": "TREATMENT", "status": "COMPLETED", "has_results": True,
                "interventions": ["Drug X"]}
        return NT.filtro_editorial({**base, **c}, [], {"pmid": "1"} if prim else None)[0]

    def test_regras(self):
        self.assertIsNone(self.f())
        self.assertEqual(self.f(title="Exercise in healthy volunteers", conditions=["Healthy"]), "NO_ACTION")
        self.assertEqual(self.f(phases=["PHASE1"]), "NO_ACTION")
        self.assertIsNone(self.f(phases=["PHASE1"], interventions=["225Ac-PSMA-617"]))          # exceção: radioligante
        self.assertIsNone(self.f(phases=["PHASE2"], allocation="NA", title="Drug Y in NTRK fusion solid tumors"))
        self.assertEqual(self.f(phases=["PHASE2"], allocation="NA"), "NO_ACTION")
        self.assertIsNone(self.f(phases=["PHASE2"], allocation="NA", interventions=["177Lu-PSMA-617"]))  # radioligante
        self.assertEqual(self.f(purpose="SUPPORTIVE_CARE"), "NO_ACTION")
        self.assertEqual(self.f(prim=False, status="ACTIVE_NOT_RECRUITING", has_results=False), "WATCH")
        self.assertEqual(self.f(prim=False, has_results=False), "WATCH")


class Conferir(Base):
    def setUp(self):
        super().setUp()
        pasta = NT.DIR / "NCT09999996"
        (pasta / "fontes").mkdir(parents=True)
        p = S.gravar_fonte(pasta / "fontes", "pmid:40000001:abstract",
                           [("Title", "Drug Z versus doxorubicin in sarcoma"),
                            ("Abstract > Findings", "Median overall survival was 18.2 months versus 14.1 months "
                                                    "(hazard ratio 0.71; p=0.004).")])
        self.pac = {"packet_sha256": "h", "candidate": {"nct": "NCT09999996"},
                    "publications": [{"pmid": "40000001"}], "dedup": {"classe": "NEW_STUDY_CANDIDATE"},
                    "sources": [{"source_id": "pmid:40000001:abstract", "source_type": "pubmed_abstract",
                                 "text_level": "abstract", "path": f"fontes/{p.name}", "role": "primary_candidate"}]}
        self.gravar()

    def gravar(self):
        (NT.DIR / "NCT09999996" / "packet.json").write_text(json.dumps(self.pac))

    def cur(self, **kw):
        base = {"action": "NEW_CARD", "maturity": "published_primary", "nct": "NCT09999996",
                "policy_basis": "fase3_pergunta_nao_representada", "comparison_type": "randomizado_vs_padrao",
                "main_publication": {"pmid": "40000001"}, "main_result": "OS mediana 18,2 vs 14,1 m; HR 0,71",
                "evidence": [{"source_id": "pmid:40000001:abstract", "source_type": "pubmed_abstract", "locator": "¶0002",
                              "snippet": "Median overall survival was 18.2 months versus 14.1 months (hazard ratio 0.71"}]}
        base.update(kw)
        return NT.conferir("NCT09999996", base)

    def codes(self, r):
        return {a["code"] for a in r["achados"]}

    def test_new_card_com_numeros_lastreados_passa(self):
        self.assertEqual(self.cur()["verdict"], "PASS")

    def test_numero_sem_trecho_e_trecho_inexistente(self):
        self.assertIn("NUMBER_UNSUPPORTED", self.codes(self.cur(main_result="OS mediana 19,0 vs 14,1 m")))
        r = self.cur(evidence=[{"source_id": "pmid:40000001:abstract", "source_type": "pubmed_abstract",
                                "locator": "¶0002", "snippet": "Median overall survival was 25 months"}])
        self.assertIn("SNIPPET_NOT_FOUND", self.codes(r))
        self.assertEqual(r["verdict"], "FAIL")

    def test_identidade_e_coerencia_da_acao(self):
        self.assertIn("NCT_MISMATCH", self.codes(self.cur(nct="NCT00000001")))
        self.assertIn("PUBLICATION_UNKNOWN", self.codes(self.cur(main_publication={"pmid": "123"})))
        self.assertIn("RELATED_WITHOUT_CARD", self.codes(self.cur(action="RELATED_TO_EXISTING")))
        self.assertIn("RELATED_CARD_UNKNOWN", self.codes(self.cur(action="RELATED_TO_EXISTING", related_card_uid="x")))
        self.assertIn("RESULT_WITHOUT_DATA", self.codes(self.cur(maturity="ongoing_no_results")))
        self.pac["dedup"] = {"classe": "POSSIBLE_DUPLICATE"}
        self.gravar()
        self.assertIn("NEW_CARD_NOT_NEW", self.codes(self.cur()))


class Politica(Conferir):
    def test_new_card_exige_criterio_e_respeita_excecoes(self):
        self.assertIn("POLICY_BASIS_MISSING", self.codes(self.cur(policy_basis="nao_se_aplica")))
        self.pac["candidate"] = {"nct": "NCT09999996", "phases": ["PHASE2"], "allocation": "NA"}
        self.gravar()
        self.assertIn("POLICY_SINGLE_ARM", self.codes(self.cur(policy_basis="fase2_randomizado_relevancia_clara")))
        self.assertNotIn("POLICY_SINGLE_ARM", self.codes(self.cur(policy_basis="excecao_braco_unico_radioligante")))
        self.assertIn("POLICY_CONGRESS", self.codes(self.cur(policy_basis="excecao_braco_unico_doenca_rara",
                                                             maturity="congress_provisional", main_result=None)))
        self.pac["candidate"] = {"nct": "NCT09999996", "phases": ["PHASE1"], "allocation": "NA"}
        self.gravar()
        self.assertIn("POLICY_PHASE1", self.codes(self.cur(policy_basis="excecao_braco_unico_radioligante")))


class PoliticaV2(Conferir):
    def test_analise_nao_comparativa_exige_human_review(self):
        self.pac["candidate"] = {"nct": "NCT09999996", "phases": ["PHASE2"], "allocation": "RANDOMIZED"}
        self.gravar()
        r = self.cur(policy_basis="fase2_randomizado_relevancia_clara", comparison_type="randomizado_nao_comparativo")
        self.assertIn("POLICY_NON_COMPARATIVE", self.codes(r))
        self.assertNotIn("POLICY_NON_COMPARATIVE", self.codes(self.cur(
            policy_basis="excecao_braco_unico_doenca_rara", comparison_type="randomizado_nao_comparativo")))
        self.assertIn("POLICY_NON_COMPARATIVE", self.codes(self.cur(comparison_type="randomizado_vs_nao_padrao")))

    def test_cirurgia_fase2_exige_human_review(self):
        self.pac["candidate"] = {"nct": None, "phases": [], "allocation": None}
        self.gravar()
        self.assertIn("POLICY_SURGERY_PHASE2", self.codes(self.cur(policy_basis="cirurgia_randomizada_relevante",
                                                                   phase="fase 2 randomizado")))
        self.assertNotIn("POLICY_SURGERY_PHASE2", self.codes(self.cur(policy_basis="cirurgia_randomizada_relevante",
                                                                      phase="fase 3 randomizado")))
        self.assertIn("COMPARISON_TYPE_ENUM", self.codes(self.cur(comparison_type="x")))


class Identidade(Base):
    ARROW = {"cand_id": "NCT03939689", "nct": "NCT03939689", "acronym": "ARROW", "title": "I-131-1095 Radioligand Plus "
             "Enzalutamide vs Enzalutamide in mCRPC", "official_title": "", "conditions": ["Prostate Cancer"],
             "interventions": ["I-131-1095", "Enzalutamide"], "phases": ["PHASE2"], "enrollment": 120,
             "pmids": [], "dois": []}

    def ident(self, pub, texto, ensaios=None):
        orig = NT._texto_pub
        NT._texto_pub = lambda p, rede=False: texto
        try:
            return NT.identidade(pub, ensaios if ensaios is not None else [self.ARROW], CARDS)
        finally:
            NT._texto_pub = orig

    def test_regressao_arrow_publicacao_sem_nct_vira_possivel_duplicata(self):
        pub = {"cand_id": "pmid41779000", "nct": None, "pmids": ["41779000"],
               "title": "131I-LNTH-1095 Radioligand Therapy plus Enzalutamide versus Enzalutamide Alone in mCRPC"}
        r = self.ident(pub, "Randomized phase 2 trial in metastatic castration-resistant prostate cancer; 120 patients.")
        self.assertEqual((r["classe"], r["alvo"]), ("POSSIBLE_DUPLICATE", "NCT03939689"))

    def test_prova_por_pmid_ou_acronimo_liga(self):
        self.assertEqual(self.ident({"pmids": ["9"], "title": "x"}, "", [{**self.ARROW, "pmids": ["9"]}])["classe"],
                         "ALREADY_LINKED")
        self.assertEqual(self.ident({"pmids": ["8"], "title": "ARROW: final results"}, "")["classe"], "ALREADY_LINKED")

    def test_regressao_nipu_acronimo_so_no_resumo(self):
        nipu = {"cand_id": "NCT04300244", "nct": "NCT04300244", "acronym": "NIPU", "title": "Nivolumab and Ipilimumab "
                "+/- UV1 Vaccination as Second Line Treatment in Patients With Malignant Mesothelioma",
                "conditions": ["Mesothelioma"], "interventions": ["UV1", "Nivolumab", "Ipilimumab"], "pmids": []}
        r = self.ident({"pmids": ["38447379"], "title": "UV1 telomerase vaccine with ipilimumab and nivolumab as second "
                        "line treatment for pleural mesothelioma - A phase II randomised trial"},
                       "NIPU is a randomised phase II trial in pleural mesothelioma.", [nipu])
        self.assertEqual((r["classe"], r["alvo"]), ("POSSIBLE_DUPLICATE", "NCT04300244"))

    def test_publicacao_de_ensaio_que_ja_tem_card(self):
        r = self.ident({"pmids": ["7"], "title": "ALPHA-301 five-year update in gastric cancer"}, "", [])
        self.assertEqual((r["classe"], r["alvo"]), ("RELATED_TO_EXISTING", "u_alfa"))

    def test_sem_compatibilidade_nao_bloqueia(self):
        self.assertIsNone(self.ident({"pmids": ["6"], "title": "Drug Q in glioblastoma"}, "phase 3, 300 patients"))

    def test_extensao_regional_de_card_existente(self):
        r = NT.deduplicar({"pmids": [], "dois": [], "nct": "NCT09999993", "acronym": "China ALPHA-301",
                           "title": "ALPHA-301 in Chinese patients with gastric cancer"}, self.idx)
        self.assertEqual((r["classe"], r["uid"]), ("RELATED_TO_EXISTING", "u_alfa"))


class Normalizacao(Conferir):
    def test_prefixo_do_paragrafo_no_trecho_e_normalizado(self):
        r = self.cur(evidence=[{"source_id": "pmid:40000001:abstract", "source_type": "pubmed_abstract", "locator": "¶0002",
                                "snippet": "¶0002 Median overall survival was 18.2 months versus 14.1 months (hazard ratio 0.71"}])
        self.assertEqual(r["verdict"], "PASS")
        self.assertIn("SNIPPET_PREFIX_NORMALIZED", self.codes(r))


class Ligacao(unittest.TestCase):
    def test_so_liga_pelo_acronimo_explicito_no_titulo(self):
        ens = lambda: {"cand_id": "NCT03939689", "nct": "NCT03939689", "acronym": "ARROW", "title": "I-131-1095 plus "  # noqa: E731
                       "enzalutamide", "pmids": [], "dois": [], "found_by": ["ctgov:x"]}
        cands = {"NCT03939689": ens(),
                 "pmidA": {"cand_id": "pmidA", "nct": None, "title": "ARROW: a randomized phase 2 trial of 131I-1095",
                           "pmids": ["1"], "dois": [], "found_by": ["pubmed:x"]},
                 "pmidB": {"cand_id": "pmidB", "nct": None, "title": "131I-LNTH-1095 Radioligand Therapy plus Enzalutamide",
                           "pmids": ["2"], "dois": [], "found_by": ["pubmed:x"]},
                 "pmidC": {"cand_id": "pmidC", "nct": None, "title": "Safety analyses of the phase 3 VISION trial of 177Lu",
                           "pmids": ["3"], "dois": [], "found_by": ["pubmed:x"]}}
        lig = NT.ligar_publicacoes(cands)
        self.assertEqual([(l["publicacao"], l["ensaio"]) for l in lig], [("pmidA", "NCT03939689")])
        self.assertIn("pmidB", cands)            # sem o acrônimo no título: não liga (limitação conhecida)
        self.assertIn("pmidC", cands)            # códigos/tokens parecidos não bastam


class Retomada(Base):
    def test_resume_e_invalidacao(self):
        (NT.DIR / "triagem.json").write_text(json.dumps({"candidatos": [
            {"cand_id": "NCT09999996", "nct": "NCT09999996", "pmids": [], "status": "COMPLETED", "phases": ["PHASE3"],
             "dedup": {"classe": "NEW_STUDY_CANDIDATE"}, "pre_action": None}]}))
        chamadas = []
        etapa = lambda n: (lambda x: chamadas.append(n) or {})  # noqa: E731
        etapas = {"preparar": etapa("preparar"), "curator": etapa("curator"), "verifier": etapa("verifier")}
        self.assertEqual(NT.executar_lote(["NCT09999996"], etapas=etapas)[0]["etapas_executadas"],
                         ["preparar", "curator", "verifier"])
        self.assertEqual(NT.executar_lote(["NCT09999996"], etapas=etapas)[0]["etapas_executadas"], [])
        orig = NT.versao
        try:
            NT.versao = lambda: "novos/999"
            self.assertEqual(NT.executar_lote(["NCT09999996"], etapas=etapas)[0]["estado_inicial"], "invalidado")
        finally:
            NT.versao = orig


if __name__ == "__main__":
    unittest.main()
