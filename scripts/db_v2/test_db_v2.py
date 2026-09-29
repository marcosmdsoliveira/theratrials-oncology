"""Testes offline da fundação do Database v2 (dados sintéticos; nenhum estudo real codificado).

    python3 -m unittest scripts/db_v2/test_db_v2.py      (a partir de site/)
    cd scripts/db_v2 && python3 -m unittest test_db_v2
"""
from __future__ import annotations

import copy
import json
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import export_legacy as X  # noqa: E402
import fixtures_v2 as F  # noqa: E402
import lift_v1 as LF  # noqa: E402
import v2lib as L  # noqa: E402
import validate_v2 as V  # noqa: E402

FIX = {f.stem: json.loads(f.read_text(encoding="utf-8")) for f in F.PASTA.glob("*.json")}


def rodar(recs):
    recs = recs if isinstance(recs, dict) else {r["uid"]: r for r in recs}
    return V.validar(recs)


def codigos(rep, uid=None):
    return {i["codigo"] for i in rep.itens if uid is None or i["uid"] == uid}


class Fixtures(unittest.TestCase):
    def test_fixtures_em_dia_com_o_gerador(self):
        self.assertEqual(set(FIX), set(F.todos()), "rode python3 fixtures_v2.py")
        for uid, r in F.todos().items():
            self.assertEqual(json.loads(json.dumps(r)), FIX[uid], uid)

    def test_todas_as_fixtures_validas_sem_lacuna(self):
        rep = rodar(copy.deepcopy(FIX))
        self.assertEqual([i for i in rep.itens if not i["codigo"].startswith("W_NOT_APPLICABLE")], [])

    def test_cobertura_dos_cenarios_pedidos(self):
        mods = {m["module"] for r in FIX.values() for m in r["modules"]}
        self.assertTrue({"radionuclide_therapy", "adc", "immunotherapy", "targeted_therapy", "ddr_hrd",
                         "t_cell_engager", "cellular", "radiotherapy", "surgery", "locoregional", "chemotherapy",
                         "diagnostic"} <= mods)
        tipos = {r["record_type"] for r in FIX.values()}
        self.assertTrue({"trial", "trial_cohort", "diagnostic_study", "publication", "evidence_collection"} <= tipos)


class Estados(unittest.TestCase):
    def setUp(self):
        self.r = copy.deepcopy(FIX["syn-adc"])

    def test_present_sem_prov(self):
        self.r["population"]["disease"].pop("prov")
        self.assertIn("E_PROV", codigos(rodar([self.r])))

    def test_estado_nao_present_com_valor(self):
        self.r["population"]["disease"] = {"state": "not_applicable", "v": "x"}
        self.assertIn("E_STATE", codigos(rodar([self.r])))

    def test_estado_invalido(self):
        self.r["population"]["disease"] = {"state": "talvez"}
        self.assertIn("E_SCHEMA", codigos(rodar([self.r])))

    def test_not_reported_em_curated_exige_fontes_conferidas(self):
        self.r["population"]["prior_therapy"] = {"state": "not_reported"}
        self.assertIn("E_STATE", codigos(rodar([self.r])))
        self.r["population"]["prior_therapy"]["checked_sources"] = ["p1"]
        self.assertNotIn("E_STATE", codigos(rodar([self.r])))

    def test_legacy_proibido_em_curated(self):
        self.r["provenance"]["v1"] = {"source": {"type": "v1_legacy"}, "extraction": "lifted_v1",
                                      "evidence_confidence": "low"}
        self.r["population"]["disease"] = {"state": "present", "origin": "legacy", "v": "x", "prov": "v1"}
        self.assertIn("E_ORIGIN", codigos(rodar([self.r])))
        self.r["curation"]["level"] = "modeled"
        self.assertNotIn("E_ORIGIN", codigos(rodar([self.r])))

    def test_reported_exige_fonte_primaria(self):
        self.r["provenance"]["v1"] = {"source": {"type": "v1_legacy"}, "extraction": "lifted_v1",
                                      "evidence_confidence": "low"}
        self.r["population"]["disease"]["prov"] = "v1"
        self.assertIn("E_PROV", codigos(rodar([self.r])))

    def test_derived_exige_formula_suposicoes_e_campos_fonte(self):
        self.r["provenance"]["pd"] = {"source": {"type": "publication", "pmid": "00000001"},
                                      "extraction": "derived", "evidence_confidence": "moderate"}
        self.r["population"]["baseline"] = {"state": "present", "origin": "derived", "v": 5, "prov": "pd"}
        self.assertIn("E_DERIVED", codigos(rodar([self.r])))
        self.r["population"]["baseline"]["derivation"] = {"formula": "a/b", "assumptions": ["x"],
                                                          "source_fields": ["design.sample_size"], "version": "t@1"}
        self.assertNotIn("E_DERIVED", codigos(rodar([self.r])))
        self.r["population"]["baseline"]["derivation"].pop("assumptions")
        self.assertIn("E_SCHEMA", codigos(rodar([self.r])))

    def test_html_proibido(self):
        self.r["interpretation"]["takehome"]["v"] = "<strong>x</strong>"
        self.assertIn("E_HTML", codigos(rodar([self.r])))


class Referencias(unittest.TestCase):
    def test_modulo_aponta_braco_inexistente(self):
        r = copy.deepcopy(FIX["syn-adc"])
        r["modules"][0]["arm_ids"] = ["fantasma"]
        self.assertIn("E_ARM_REF", codigos(rodar([r])))

    def test_endpoint_com_comparacao_inexistente(self):
        r = copy.deepcopy(FIX["syn-adc"])
        r["endpoints"]["v"][0]["comparison_id"] = "c9"
        self.assertIn("E_COMPARISON_REF", codigos(rodar([r])))

    def test_braco_fora_da_comparacao(self):
        r = copy.deepcopy(FIX["syn-tres-bracos"])
        r["endpoints"]["v"][1]["arms_values"][0]["arm_id"] = "combo"
        self.assertIn("E_ARM_REF", codigos(rodar([r])))

    def test_ni_sem_margem(self):
        r = copy.deepcopy(FIX["syn-tres-bracos"])
        r["design"]["comparisons"]["v"][1].pop("ni_margin")
        self.assertIn("E_COMPARISON_REF", codigos(rodar([r])))

    def test_nivel_de_fator_inexistente(self):
        r = copy.deepcopy(FIX["syn-fatorial"])
        r["endpoints"]["v"][0]["arms_values"][0]["arm_group"]["level"] = "média"
        self.assertIn("E_ARM_REF", codigos(rodar([r])))

    def test_biomarcador_e_coorte_referenciados(self):
        r = copy.deepcopy(FIX["syn-basket-coorte"])
        r["endpoints"]["v"][0]["population"]["cohort_id"] = "Z"
        self.assertIn("E_COHORT_REF", codigos(rodar([r])))

    def test_assinatura_de_analise(self):
        r = copy.deepcopy(FIX["syn-adc"])
        r["analyses"][0]["signature"].pop("timepoint")
        self.assertIn("E_SIGNATURE", codigos(rodar([r])))
        r = copy.deepcopy(FIX["syn-adc"])
        r["endpoints"]["v"][0]["maturity"]["analysis_ref"] = "a9"
        self.assertIn("E_SIGNATURE", codigos(rodar([r])))


class Primarios(unittest.TestCase):
    def test_dois_primarios_sole_no_mesmo_escopo(self):
        r = copy.deepcopy(FIX["syn-adc"])
        r["endpoints"]["v"].append(F.endpoint("e2", "OS"))
        self.assertIn("E_PRIMARY", codigos(rodar([r])))

    def test_co_primario_valido_e_sequencia(self):
        self.assertEqual(codigos(rodar([copy.deepcopy(FIX["syn-coprimario"])])), set())
        r = copy.deepcopy(FIX["syn-coprimario"])
        r["design"]["multiplicity"]["v"]["families"][0]["members"][1]["order"] = 3
        self.assertIn("E_PRIMARY", codigos(rodar([r])))

    def test_dual_primario_exige_alfa_dividido(self):
        r = copy.deepcopy(FIX["syn-dualprimario"])
        r["design"]["multiplicity"]["v"]["families"][0]["members"][1]["alpha"] = 0.045
        self.assertIn("E_PRIMARY", codigos(rodar([r])))
        r = copy.deepcopy(FIX["syn-dualprimario"])
        for e in r["endpoints"]["v"]:
            e["hierarchy"].pop("testing")
        self.assertIn("E_PRIMARY", codigos(rodar([r])))

    def test_co_primario_com_um_so(self):
        r = copy.deepcopy(FIX["syn-adc"])
        r["endpoints"]["v"][0]["hierarchy"]["primary_type"] = "co_primary"
        self.assertIn("E_PRIMARY", codigos(rodar([r])))

    def test_medida_de_apoio_nao_conta_como_segundo_primario(self):
        # taxa em landmark (análise do protocolo) + mediana (apoio) do mesmo endpoint
        self.assertEqual(codigos(rodar([copy.deepcopy(FIX["syn-conflito"])])), set())

    def test_primario_por_coorte_e_por_comparacao(self):
        r = copy.deepcopy(FIX["syn-tres-bracos"])
        r["endpoints"]["v"][1]["hierarchy"]["level"] = "primary"   # c2 com primário próprio: escopo distinto
        self.assertNotIn("E_PRIMARY", codigos(rodar([r])))

    def test_emenda_preserva_historico(self):
        r = copy.deepcopy(FIX["syn-adc"])
        r["endpoints"]["v"][0]["hierarchy"]["history"] = [{"level": "secondary", "reason": "amendment",
                                                           "changed_at": "2022-01-01"}]
        self.assertEqual(codigos(rodar([r])), set())


class PapelEAtivacao(unittest.TestCase):
    def test_crs_obrigatorio_so_no_braco_do_tce_testado(self):
        r = copy.deepcopy(FIX["syn-tce"])
        self.assertEqual(codigos(rodar([r])), set())  # braço de QT controle não tem CRS e não é erro
        r["safety"]["key_toxicities"]["v"] = [t for t in r["safety"]["key_toxicities"]["v"] if t["term"] != "crs"]
        self.assertIn("E_REQUIRED", codigos(rodar([r])))

    def test_crs_em_braco_de_controle_nao_satisfaz(self):
        r = copy.deepcopy(FIX["syn-tce"])
        for t in r["safety"]["key_toxicities"]["v"]:
            if t["term"] == "crs":
                t["arm_id"] = "ctl"
        self.assertIn("E_REQUIRED", codigos(rodar([r])))

    def test_mesmo_modulo_como_controle_nao_exige_campos_de_testado(self):
        r = copy.deepcopy(FIX["syn-controle"])
        self.assertEqual(codigos(rodar([r])), set())

    def test_pdl1_so_quando_pdl1_esta_envolvido(self):
        self.assertEqual(codigos(rodar([copy.deepcopy(FIX["syn-io-sem-pdl1"])])), set())
        r = copy.deepcopy(FIX["syn-io"])
        r["modules"][0]["fields"].pop("pdl1")
        self.assertIn("E_REQUIRED", codigos(rodar([r])))
        r["design"].pop("stratification")
        self.assertNotIn("E_REQUIRED", codigos(rodar([r])))

    def test_alvo_do_radionuclideo_so_para_ligante(self):
        self.assertEqual(codigos(rodar([copy.deepcopy(FIX["syn-fatorial"])])), set())  # metabólico, sem target
        r = copy.deepcopy(FIX["syn-radionuclide"])
        r["modules"][0]["fields"].pop("target")
        self.assertIn("E_REQUIRED", codigos(rodar([r])))

    def test_aesi_condicionado_ao_payload(self):
        r = copy.deepcopy(FIX["syn-adc"])
        r["modules"][0]["fields"]["payload_class"]["v"] = "microtubule_inhibitor"
        c = codigos(rodar([r]))
        self.assertIn("E_REQUIRED", c)  # agora exige ocular e neuropatia; ILD deixa de ser exigido
        itens = {i["caminho"] for i in rodar([r]).itens}
        self.assertIn("safety.key_toxicities[ocular_surface]", itens)
        self.assertNotIn("safety.key_toxicities[ild_pneumonitis]", itens)

    def test_campo_not_applicable_contradiz_obrigatorio_ativo(self):
        r = copy.deepcopy(FIX["syn-radionuclide"])
        r["modules"][0]["fields"]["target"] = {"state": "not_applicable"}
        self.assertIn("E_NA_CONTRADICTION", codigos(rodar([r])))

    def test_campo_fora_do_registro_do_modulo(self):
        r = copy.deepcopy(FIX["syn-adc"])
        r["modules"][0]["fields"]["crs"] = F.P("x")
        self.assertIn("E_MODULE", codigos(rodar([r])))

    def test_papel_indeterminado_proibido_em_curated(self):
        r = copy.deepcopy(FIX["syn-adc"])
        r["modules"][0]["role"] = "undetermined"
        self.assertIn("E_MODULE", codigos(rodar([r])))

    def test_perfil_por_record_type(self):
        r = copy.deepcopy(FIX["syn-diag"])
        self.assertEqual(codigos(rodar([r])), set())  # sem braços, segurança e key_result: não se aplicam
        r["endpoints"] = {"state": "unknown"}
        self.assertIn("E_REQUIRED", codigos(rodar([r])))

    def test_braco_unico_torna_mascara_e_controle_nao_aplicaveis(self):
        self.assertEqual(codigos(rodar([copy.deepcopy(FIX["syn-basket-coorte"])])), set())

    def test_lacuna_em_shadow_e_aviso_nao_erro(self):
        r = copy.deepcopy(FIX["syn-tce"])
        r["curation"]["level"] = "modeled"
        r["safety"]["key_toxicities"] = {"state": "unknown"}
        c = codigos(rodar([r]))
        self.assertIn("W_REQUIRED", c)
        self.assertFalse(any(x.startswith("E_") for x in c))


class Conflito(unittest.TestCase):
    def test_conflito_exige_dois_candidatos_com_locator(self):
        r = copy.deepcopy(FIX["syn-conflito"])
        r["endpoints"]["v"][2]["value_candidates"].pop()
        self.assertIn("E_CONFLICT", codigos(rodar([r])))

    def test_conflito_so_em_present(self):
        r = copy.deepcopy(FIX["syn-adc"])
        r["population"]["disease"] = {"state": "unknown", "conflict": "within_source_conflict"}
        self.assertIn("E_CONFLICT", codigos(rodar([r])))

    def test_projecao_legada_mostra_os_dois_valores(self):
        env = {"state": "present", "origin": "reported", "v": 17.4, "prov": "p1",
               "conflict": "within_source_conflict",
               "value_candidates": [{"value": 17.4, "locator": {"section": "Abstract"}},
                                    {"value": 17.6, "locator": {"section": "Results"}}]}
        self.assertEqual(X.render(env, "secundario"), "17,4 (Abstract) vs 17,6 (Results)")


class Integridade(unittest.TestCase):
    def test_withheld_valido_e_exige_decisao(self):
        self.assertEqual(codigos(rodar([copy.deepcopy(FIX["syn-withheld"])])), set())
        r = copy.deepcopy(FIX["syn-withheld"])
        r["population"]["disease"].pop("decision_ref")
        self.assertIn("E_STATE", codigos(rodar([r])))

    def test_withheld_na_projecao_legada(self):
        self.assertTrue(X.render({"state": "withheld_due_to_integrity", "decision_ref": "q"}, "primario")
                        .startswith("Em revisão editorial"))


class Relacoes(unittest.TestCase):
    def colecao(self):
        return {u: copy.deepcopy(FIX[u]) for u in ("syn-colecao", "syn-colecao-serie-a", "syn-colecao-serie-b")}

    def test_colecao_com_filhos_valida(self):
        self.assertEqual(codigos(rodar(self.colecao())), set())

    def test_pai_sem_reciprocidade(self):
        c = self.colecao()
        c["syn-colecao"]["relationships"]["child_uids"].remove("syn-colecao-serie-b")
        self.assertIn("E_REL", codigos(rodar(c)))

    def test_ciclo_parent(self):
        c = self.colecao()
        c["syn-colecao"]["relationships"]["parent_uid"] = "syn-colecao-serie-a"
        c["syn-colecao-serie-a"]["relationships"]["child_uids"] = ["syn-colecao"]
        self.assertIn("E_REL", codigos(rodar(c)))

    def test_ciclo_follow_up(self):
        c = self.colecao()
        c["syn-colecao-serie-a"]["relationships"]["links"] = [{"type": "follow_up_of",
                                                              "target_uid": "syn-colecao-serie-b"}]
        self.assertIn("E_REL", codigos(rodar(c)))

    def test_auto_referencia(self):
        c = self.colecao()
        c["syn-colecao"]["relationships"]["links"] = [{"type": "supersedes", "target_uid": "syn-colecao"}]
        self.assertIn("E_REL", codigos(rodar(c)))

    def test_colecao_preserva_uid_e_legado(self):
        pai = FIX["syn-colecao"]
        self.assertEqual(pai["record_type"], "evidence_collection")
        self.assertEqual(pai["legacy"]["v1"]["uid"], pai["uid"])


class UidImutavel(unittest.TestCase):
    def test_uid_do_head_ausente(self):
        rep = V.validar({"syn-adc": copy.deepcopy(FIX["syn-adc"])}, head={"syn-adc", "sumiu"})
        self.assertIn("E_UID_IMMUTABLE", codigos(rep, "sumiu"))

    def test_arquivo_com_nome_diferente_do_uid(self):
        rep = V.validar({"syn-adc": copy.deepcopy(FIX["syn-adc"])}, {"syn-adc": "outro.json"})
        self.assertIn("E_UID_IMMUTABLE", codigos(rep))

    def test_legado_com_uid_divergente(self):
        r = copy.deepcopy(FIX["syn-adc"])
        r["legacy"]["v1"]["uid"] = "x"
        self.assertIn("E_LEGACY", codigos(rodar([r])))

    def test_projecao_nunca_reescreve_uid(self):
        r = copy.deepcopy(FIX["syn-adc"])
        r["curation"]["legacy_projection"] = {"uid": "identity.short_name"}
        with self.assertRaises(ValueError):
            X.projetar(r)


CARD = {"estudo": "SYN-1", "acron": "SYN-1 — título", "nct": "NCT12345678; ver também ISRCTN", "sponsor": "—",
        "fase": "Fase 3, randomizado", "desenho": "RCT", "indicacao": "doença X", "primario": "PFS 10 vs 6 m",
        "radiofarmaco": "Olaparibe 300 mg 2×/d", "esquema": "—", "comparador": "Docetaxel", "cumul": "Variável",
        "preparo": "", "status": "Publicado", "pubmed_url": "https://pubmed.ncbi.nlm.nih.gov/123/", "ano_pub": "2024",
        "category_id": "cat", "uid": "syn-card"}


class Lift(unittest.TestCase):
    def setUp(self):
        self.r = LF.lift(dict(CARD), 0, {})

    def test_nenhum_campo_clinico_present(self):
        for g in ("population", "design", "safety", "interpretation"):
            for campo, env in self.r.get(g, {}).items():
                self.assertEqual(env["state"], "unknown", f"{g}.{campo}")
        self.assertEqual(self.r["endpoints"]["state"], "unknown")

    def test_ausencia_nunca_vira_estado_semantico(self):
        estados = {env["state"] for g in ("identity", "population", "design", "safety", "interpretation")
                   for env in self.r.get(g, {}).values()}
        self.assertTrue(estados <= {"present", "unknown"})

    def test_legado_literal_e_incerteza_registrada(self):
        self.assertEqual(self.r["legacy"]["v1"], CARD)
        caminhos = {u["path"] for u in self.r["curation"]["uncertainty"]}
        self.assertIn("identity.registrations", caminhos)          # NCT com texto livre
        self.assertIn("identity.represented_publication.year", caminhos)  # ano como string

    def test_modulo_so_com_evidencia_forte(self):
        mods = {m["module"]: m for m in self.r["modules"]}
        self.assertIn("targeted_therapy", mods)                    # olaparibe no campo de intervenção
        self.assertEqual(mods["targeted_therapy"]["role"], "undetermined")
        self.assertIsNone(mods["targeted_therapy"]["arm_ids"])
        self.assertNotIn("chemotherapy", mods)                     # docetaxel só no comparador → sugestão
        self.assertTrue(any(s["value"] == "chemotherapy" for s in self.r["curation"]["suggestions"]))

    def test_rai_refratario_nao_e_radioiodo(self):
        c = dict(CARD, acron="Cabozantinibe em CDT RAI-refratário", radiofarmaco="Cabozantinibe")
        mods = {m["module"] for m in LF.lift(c, 0, {})["modules"]}
        self.assertNotIn("radionuclide_therapy", mods)

    def test_gy_de_microsfera_nao_e_rt_externa(self):
        c = dict(CARD, radiofarmaco="90Y-microsferas", esquema="dose ao tumor 205 Gy", acron="TARE")
        mods = {m["module"] for m in LF.lift(c, 0, {})["modules"]}
        self.assertIn("radionuclide_therapy", mods)
        self.assertNotIn("radiotherapy", mods)

    def test_sombra_valida_sem_erro(self):
        rep = V.validar({self.r["uid"]: self.r})
        self.assertEqual([i for i in rep.itens if i["codigo"].startswith("E_")], [])


class RoundTrip(unittest.TestCase):
    def _dataset(self, pasta, cards):
        prefixo, sufixo = "/* cabeçalho */\nwindow.THERA_DATA = ", ";\n"
        obj = {"categories": [{"id": "cat"}], "studies": cards, "metadata": {"total": len(cards)}}
        texto = L.serializar_data_js(prefixo, obj, sufixo)
        (pasta / "_dataset.json").write_text(json.dumps({
            "prefix": prefixo, "suffix": sufixo, "top_keys": list(obj), "other": {k: v for k, v in obj.items()
                                                                                  if k != "studies"},
            "study_order": [c["uid"] for c in cards]}), encoding="utf-8")
        for n, c in enumerate(cards):
            (pasta / f"{c['uid']}.json").write_text(json.dumps(LF.lift(c, n, {})), encoding="utf-8")
        return texto

    def test_round_trip_byte_a_byte(self):
        with tempfile.TemporaryDirectory() as t:
            p = pathlib.Path(t)
            cards = [dict(CARD), dict(CARD, uid="syn-2", estudo="Ç ☢ ≥ 5 — “aspas”")]
            texto = self._dataset(p, cards)
            self.assertEqual(X.exportar(p), texto)

    def test_card_migrado_divergente_e_detectado(self):
        with tempfile.TemporaryDirectory() as t:
            p = pathlib.Path(t)
            texto = self._dataset(p, [dict(CARD)])
            r = json.loads((p / "syn-card.json").read_text())
            r["curation"]["level"] = "curated"
            r["curation"]["legacy_projection"] = {"estudo": "identity.short_name"}
            r["identity"]["short_name"] = {"state": "present", "origin": "editorial", "v": "SYN-1 NOVO"}
            (p / "syn-card.json").write_text(json.dumps(r))
            rel = X.comparar(X.exportar(p), texto)
            self.assertFalse(rel["bytes_identicos"])
            self.assertEqual(rel["cards_divergentes"][0]["campos"], ["estudo"])

    def test_export_recusa_gravar_no_data_js(self):
        self.assertEqual(X.main(["--out", str(L.DATA_JS)]), 2)


class Registro(unittest.TestCase):
    def test_todo_campo_de_modulo_tem_papeis_e_ativacao(self):
        for nome, spec in L.REGISTRY["module_fields"].items():
            for f in spec["fields"] + spec["aesi"]:
                self.assertEqual(set(f["requirement"]), set(L.REGISTRY["module_roles"]), f"{nome}.{f}")
                self.assertIn("op", f["activation"])

    def test_contexto_nunca_exige_aesi(self):
        for nome, spec in L.REGISTRY["module_fields"].items():
            for t in spec["aesi"]:
                self.assertEqual(t["requirement"]["context"], "not_applicable", f"{nome}.{t['term']}")

    def test_perfis_cobrem_todos_os_record_types(self):
        self.assertEqual(set(L.REGISTRY["profiles"]), set(L.REGISTRY["record_types"]))
        for tipo, p in L.REGISTRY["profiles"].items():
            self.assertFalse(set(p["required"]) & set(p["not_applicable"]), tipo)
            self.assertTrue(set(p["required"]) <= {c["path"] for c in L.REGISTRY["core"]}, tipo)

    def test_sem_regra_especifica_por_estudo(self):
        import re
        fontes = " ".join((pathlib.Path(__file__).parent / f).read_text(encoding="utf-8")
                          for f in ("registry_v2.py", "validate_v2.py", "lift_v1.py", "export_legacy.py", "v2lib.py"))
        self.assertIsNone(re.search(r"NCT\d{8}|['\"](?:rt_sbrt_oligo_5|ppgl_8|endometrio_6)['\"]", fontes))


class RegressaoReteste(unittest.TestCase):
    """Bugs do validador achados na modelagem dos 35 cards reais (um teste por bug)."""

    def test_mesmo_primario_em_duas_analises_e_valido(self):
        r = copy.deepcopy(FIX["syn-adc"])
        r["analyses"].append(dict(copy.deepcopy(r["analyses"][0]), analysis_id="a2", analysis_type="update",
                                  publication_role="update"))
        e2 = copy.deepcopy(r["endpoints"]["v"][0]); e2["endpoint_id"] = "e1u"; e2["maturity"]["analysis_ref"] = "a2"
        r["endpoints"]["v"].append(e2)
        self.assertNotIn("E_PRIMARY", codigos(rodar([r])))

    def test_enum_fechado(self):
        r = copy.deepcopy(FIX["syn-adc"])
        r["identity"]["evidence_stage"]["v"] = "qualquer_coisa"
        self.assertIn("E_ENUM", codigos(rodar([r])))

    def test_codigo_de_endpoint_fechado(self):
        r = copy.deepcopy(FIX["syn-adc"])
        r["endpoints"]["v"][0]["code"] = "XYZ"
        self.assertIn("E_SCHEMA", codigos(rodar([r])))

    def test_braco_inexistente_na_seguranca_e_candidato(self):
        r = copy.deepcopy(FIX["syn-adc"])
        r["safety"]["discontinuation_ae"]["v"][0]["arm_id"] = "fantasma"
        self.assertIn("E_ARM_REF", codigos(rodar([r])))
        r = copy.deepcopy(FIX["syn-conflito"])
        r["endpoints"]["v"][2]["value_candidates"][0]["value"] = {"arm_id": "fantasma", "v": 17.4}
        self.assertIn("E_ARM_REF", codigos(rodar([r])))

    def test_intervencao_com_modulo_nao_declarado(self):
        r = copy.deepcopy(FIX["syn-adc"])
        r["design"]["arms"]["v"][0]["interventions"][0]["module"] = "t_cell_engager"
        self.assertIn("E_MODULE", codigos(rodar([r])))

    def test_primario_so_com_medida_de_apoio(self):
        r = copy.deepcopy(FIX["syn-adc"])
        r["endpoints"]["v"][0]["measure"]["analysis_role"] = "supportive"
        self.assertIn("E_PRIMARY", codigos(rodar([r])))

    def test_soma_dos_bracos_maior_que_randomizados(self):
        r = copy.deepcopy(FIX["syn-adc"])
        r["design"]["sample_size"]["v"]["randomized"] = 10
        self.assertIn("W_SAMPLE_SIZE", codigos(rodar([r])))

    def test_target_expression_so_quando_biomarcador_e_o_alvo(self):
        r = copy.deepcopy(FIX["syn-controle"])  # ADC anti-TROP2
        r["population"]["biomarker_selection"] = F.P([{"id": "b1", "biomarker": "HER2", "family": "HER2",
                                                      "rule": "excluded"}])
        self.assertNotIn("E_REQUIRED", codigos(rodar([r])))
        r["population"]["biomarker_selection"]["v"].append({"id": "b2", "biomarker": "TROP2", "family": "TROP2",
                                                            "rule": "analyzed"})
        self.assertIn("E_REQUIRED", codigos(rodar([r])))

    def test_referencias_de_coorte_modulo_e_estratificados(self):
        r = copy.deepcopy(FIX["syn-basket-coorte"])
        r["design"]["cohorts"]["v"][0]["biomarker_ref"] = "b9"
        self.assertIn("E_COHORT_REF", codigos(rodar([r])))
        r = copy.deepcopy(FIX["syn-ddr"])
        r["modules"][1]["fields"]["stratified_results"]["v"] = ["e9"]
        self.assertIn("E_COHORT_REF", codigos(rodar([r])))
        r = copy.deepcopy(FIX["syn-alvo"])
        r["modules"][0]["fields"]["required_alteration"]["v"] = "KRAS G12C"
        self.assertIn("E_COHORT_REF", codigos(rodar([r])))

    def test_prov_inexistente_em_analise_e_candidato(self):
        r = copy.deepcopy(FIX["syn-adc"])
        r["analyses"][0]["prov"] = "p9"
        self.assertIn("E_PROV", codigos(rodar([r])))

    def test_dual_primario_sem_alfa(self):
        r = copy.deepcopy(FIX["syn-dualprimario"])
        for m in r["design"]["multiplicity"]["v"]["families"][0]["members"]:
            m.pop("alpha")
        self.assertIn("E_PRIMARY", codigos(rodar([r])))

    def test_aesi_sem_valor_nao_cumpre(self):
        r = copy.deepcopy(FIX["syn-tce"])
        for t in r["safety"]["key_toxicities"]["v"]:
            if t["term"] == "crs":
                t.pop("value")
        self.assertIn("E_REQUIRED", codigos(rodar([r])))
        for t in r["safety"]["key_toxicities"]["v"]:
            if t["term"] == "crs":
                t.update({"state": "not_reported", "checked_sources": ["p1"]})
        self.assertNotIn("E_REQUIRED", codigos(rodar([r])))

    def test_mesmo_braco_tested_e_control(self):
        r = copy.deepcopy(FIX["syn-controle"])
        r["modules"][1]["module"] = "adc"
        r["modules"][1]["arm_ids"] = ["exp"]
        self.assertIn("E_MODULE", codigos(rodar([r])))

    def test_braco_controle_em_exp_arms(self):
        r = copy.deepcopy(FIX["syn-adc"])
        r["design"]["comparisons"]["v"][0]["exp_arms"] = ["ctl"]
        r["design"]["comparisons"]["v"][0]["ctl_arms"] = ["exp"]
        self.assertIn("E_COMPARISON_REF", codigos(rodar([r])))

    def test_ic_invertido_e_efeito_fora_do_ic(self):
        r = copy.deepcopy(FIX["syn-adc"])
        r["endpoints"]["v"][0]["effect"]["ci"] = {"level": 95, "low": 0.9, "high": 0.5}
        self.assertIn("E_VALUE", codigos(rodar([r])))
        r = copy.deepcopy(FIX["syn-adc"])
        r["endpoints"]["v"][0]["effect"]["value"] = F.Q(1.2)
        self.assertIn("E_VALUE", codigos(rodar([r])))

    def test_range_sem_limites(self):
        r = copy.deepcopy(FIX["syn-rt"])
        r["modules"][0]["fields"]["components"]["v"][0]["total_gy"] = {"op": "range", "low": 25}
        self.assertIn("E_VALUE", codigos(rodar([r])))

    def test_primario_randomizado_sem_comparacao(self):
        r = copy.deepcopy(FIX["syn-adc"])
        r["endpoints"]["v"][0]["comparison_id"] = None
        self.assertIn("E_COMPARISON_REF", codigos(rodar([r])))

    def test_not_yet_available_com_efeito(self):
        r = copy.deepcopy(FIX["syn-adc"])
        e = {"endpoint_id": "e9", "code": "OS", "hierarchy": {"level": "secondary"}, "population": {"label": "ITT"},
             "state": "not_yet_available", "effect": {"measure": "HR", "value": F.Q(0.8)}}
        r["endpoints"]["v"].append(e)
        self.assertIn("E_STATE", codigos(rodar([r])))
        e.pop("effect")
        self.assertNotIn("E_STATE", codigos(rodar([r])))  # sem medida/tempo: permitido fora de present

    def test_part_e_assinatura_inexistentes(self):
        r = copy.deepcopy(FIX["syn-adc"])
        r["endpoints"]["v"][0]["hierarchy"]["scope"] = {"part_id": "P9"}
        self.assertIn("E_COHORT_REF", codigos(rodar([r])))
        r = copy.deepcopy(FIX["syn-adc"])
        r["analyses"][0]["signature"]["endpoint"] = "OS"
        self.assertIn("E_SIGNATURE", codigos(rodar([r])))

    def test_aesi_de_modulo_ausente(self):
        r = copy.deepcopy(FIX["syn-adc"])
        r["safety"]["key_toxicities"]["v"][0]["aesi_of"] = ["cellular"]
        self.assertIn("E_MODULE", codigos(rodar([r])))

    def test_ordem_da_sequencia_trocada(self):
        r = copy.deepcopy(FIX["syn-coprimario"])
        r["endpoints"]["v"][0]["hierarchy"]["testing"]["order"] = 2
        self.assertIn("E_PRIMARY", codigos(rodar([r])))

    def test_testado_so_no_controle(self):
        r = copy.deepcopy(FIX["syn-radionuclide"])
        r["modules"][0]["arm_ids"] = ["ctl"]
        self.assertIn("E_MODULE", codigos(rodar([r])))

    def test_present_vazio(self):
        r = copy.deepcopy(FIX["syn-adc"])
        r["interpretation"]["limitations"]["v"] = []
        self.assertIn("E_STATE", codigos(rodar([r])))

    def test_unspecified_so_fora_de_curated(self):
        r = copy.deepcopy(FIX["syn-adc"])
        r["endpoints"]["v"][0]["hierarchy"]["level"] = "unspecified"
        self.assertIn("E_PRIMARY", codigos(rodar([r])))
        r["curation"]["level"] = "modeled"
        self.assertNotIn("E_PRIMARY", codigos(rodar([r])))

    def test_hematologico_nao_cobrado_em_tare(self):
        r = copy.deepcopy(FIX["syn-radionuclide"])
        f = r["modules"][0]["fields"]
        f["delivery"]["v"] = "intra_arterial_microsphere"
        for k in ("target", "imaging_selection", "activity_per_administration", "cycles"):
            f.pop(k)  # microsfera: sem alvo molecular nem atividade por ciclo
        f["absorbed_dose"] = F.P([{"arm_id": "exp", "compartment": "tumor", "prescribed_gy": 205}])
        r["safety"]["key_toxicities"]["v"] = [F.tox("liver_reild", "exp", 3, "radionuclide_therapy")]
        self.assertEqual(codigos(rodar([r])), set())

    def test_colecao_nao_cobra_aesi(self):
        c = {u: copy.deepcopy(FIX[u]) for u in ("syn-colecao", "syn-colecao-serie-a", "syn-colecao-serie-b")}
        c["syn-colecao"]["modules"] = [F.mod("radionuclide_therapy", arm_ids="all", delivery="systemic_ligand")]
        c["syn-colecao"]["modules"][0]["arm_ids"] = None
        c["syn-colecao"]["modules"][0]["role"] = "undetermined"
        c["syn-colecao"]["curation"]["level"] = "modeled"
        self.assertFalse(any(x.startswith("E_") for x in codigos(rodar(c))))

    def test_legado_divergente_do_data_js(self):
        r = copy.deepcopy(FIX["syn-adc"]); r["curation"]["level"] = "modeled"
        rep = V.validar({"syn-adc": r}, atuais={"syn-adc": {"uid": "syn-adc", "estudo": "outro"}})
        self.assertIn("E_LEGACY", codigos(rep))

    def test_aesi_por_nivel_de_fator(self):
        r = copy.deepcopy(FIX["syn-fatorial"])
        r["safety"]["key_toxicities"]["v"] = [{"term": "hematologic", "scope": "any", "aesi_of": ["radionuclide_therapy"],
                                               "arm_group": {"factor": "atividade", "level": "alta"}, "value": F.Q(1)}]
        self.assertNotIn("E_REQUIRED", codigos(rodar([r])))

    def test_resultado_so_de_direcao_dispensa_medida(self):
        r = copy.deepcopy(FIX["syn-adc"])
        r["endpoints"]["v"].append({"endpoint_id": "e5", "code": "QoL", "hierarchy": {"level": "secondary"},
                                    "comparison_id": "c1", "population": {"label": "ITT"},
                                    "effect": {"measure": "none", "value": {"op": "direction_only",
                                                                            "direction": "favors_exp"}},
                                    "state": "present", "origin": "reported", "prov": "p1"})
        self.assertNotIn("E_STATE", codigos(rodar([r])))

    def test_orfao_avisado(self):
        rep = rodar([copy.deepcopy(FIX["syn-colecao-serie-a"])])
        self.assertIn("W_REL_ORPHAN", codigos(rep))


class AssinaturaPorEndpoint(unittest.TestCase):
    def test_dois_endpoints_na_mesma_assinatura_e_erro(self):
        r = copy.deepcopy(FIX["syn-coprimario"])
        r["endpoints"]["v"][1]["maturity"]["analysis_ref"] = r["endpoints"]["v"][0]["maturity"]["analysis_ref"]
        self.assertIn("E_SIGNATURE", codigos(rodar([r])))

    def test_medida_ou_tempo_diferente_exige_assinatura_propria(self):
        r = copy.deepcopy(FIX["syn-conflito"])   # PFS em 6 meses e PFS mediana
        eps = r["endpoints"]["v"]
        eps[1]["maturity"]["analysis_ref"] = eps[0]["maturity"]["analysis_ref"]
        itens = [i for i in rodar([r]).itens if i["codigo"] == "E_SIGNATURE"]
        self.assertTrue(any("summary_measure" in i["msg"] or "timepoint" in i["msg"] for i in itens))

    def test_comparacao_da_assinatura(self):
        r = copy.deepcopy(FIX["syn-tres-bracos"])
        r["analyses"][1]["signature"]["comparison"] = "c1"
        self.assertIn("E_SIGNATURE", codigos(rodar([r])))

    def test_tempo_canonico(self):
        self.assertEqual(V.tempo_canonico({"type": "landmark", "months": 6}), "landmark:6")
        self.assertEqual(V.tempo_canonico({"type": "at_event", "window": {"low": 6, "high": 10}}), "at_event:6-10")

    def test_codigos_especificos_existem_e_generico_nao_e_curinga(self):
        for code in ("DSS", "FFS", "PFS2", "TFST", "MPR"):
            r = copy.deepcopy(FIX["syn-adc"])
            e = r["endpoints"]["v"][0]
            e["code"] = code
            r["analyses"][0]["signature"]["endpoint"] = code
            self.assertEqual(codigos(rodar([r])), set(), code)


class VocabularioDeEndpoints(unittest.TestCase):
    def test_sinonimos_apontam_para_codigos_existentes_sem_ambiguidade(self):
        vistos = {}
        for cod, sins in L.REGISTRY["endpoint_synonyms"].items():
            self.assertIn(cod, L.REGISTRY["endpoint_codes"])
            for x in sins:
                self.assertEqual(x, x.lower())
                self.assertNotIn(x, vistos, f"{x} em {cod} e {vistos.get(x)}")
                vistos[x] = cod


class CuradoDeclaraEstado(unittest.TestCase):
    def test_obrigatorio_ausente_em_curated_e_erro_mas_unknown_declarado_nao(self):
        r = copy.deepcopy(FIX["syn-adc"])
        r["population"].pop("prior_therapy")
        self.assertIn("E_REQUIRED", codigos(rodar([r])))
        r["population"]["prior_therapy"] = {"state": "unknown"}
        self.assertIn("E_REQUIRED", codigos(rodar([r])))          # unknown sem dizer o que foi conferido
        r["population"]["prior_therapy"]["checked_sources"] = ["p1"]
        c = codigos(rodar([r]))
        self.assertNotIn("E_REQUIRED", c)
        self.assertIn("W_REQUIRED_ACK", c)

    def test_aesi_unknown_declarado(self):
        r = copy.deepcopy(FIX["syn-tce"])
        for t in r["safety"]["key_toxicities"]["v"]:
            if t["term"] == "icans":
                t.pop("value"); t["state"] = "unknown"
        self.assertIn("E_REQUIRED", codigos(rodar([r])))
        for t in r["safety"]["key_toxicities"]["v"]:
            if t["term"] == "icans":
                t["checked_sources"] = ["p1"]
        self.assertNotIn("E_REQUIRED", codigos(rodar([r])))


class RelacoesExternas(unittest.TestCase):
    def base(self):
        return copy.deepcopy(FIX["syn-basket-coorte"])

    def test_valida(self):
        self.assertEqual(codigos(rodar([self.base()])), set())

    def test_formato_por_registro(self):
        casos = [("clinicaltrials_gov", "NCT123"), ("isrctn", "ISRCTN1"), ("eudract", "2020-1234-01"),
                 ("ctis", "2023-501234-12"), ("anzctr", "ACTRN123"), ("jrct", "RCT123")]
        for reg, rid in casos:
            r = self.base()
            r["external_relationships"] = [{"registry": reg, "registry_id": rid, "relationship": "related"}]
            self.assertIn("E_EXTERNAL", codigos(rodar([r])), reg)
        for reg, rid in [("eudract", "2020-123456-01"), ("ctis", "2023-501234-12-00"), ("anzctr", "ACTRN12620000123456"),
                         ("jrct", "jRCT2031210001"), ("isrctn", "ISRCTN12345678")]:
            r = self.base()
            r["external_relationships"] = [{"registry": reg, "registry_id": rid, "relationship": "predecessor"}]
            self.assertNotIn("E_EXTERNAL", codigos(rodar([r])), reg)

    def test_other_exige_rotulo(self):
        r = self.base()
        r["external_relationships"][1].pop("label")
        self.assertIn("E_EXTERNAL", codigos(rodar([r])))

    def test_url_do_registro_declarado(self):
        r = self.base()
        r["external_relationships"][0]["url"] = "https://exemplo.org/NCT88888888"
        self.assertIn("E_EXTERNAL", codigos(rodar([r])))
        r["external_relationships"][0]["url"] = "https://clinicaltrials.gov/study/NCT77777777"
        self.assertIn("E_EXTERNAL", codigos(rodar([r])))

    def test_relacao_fora_do_vocabulario_e_uid_proibido(self):
        r = self.base()
        r["external_relationships"][0]["relationship"] = "inventada"
        self.assertIn("E_SCHEMA", codigos(rodar([r])))
        r = self.base()
        r["external_relationships"][0]["target_uid"] = "uid-inventado"
        self.assertIn("E_SCHEMA", codigos(rodar([r])))

    def test_externo_que_ja_tem_card(self):
        a, b = copy.deepcopy(FIX["syn-adc"]), self.base()
        nct = a["identity"]["registrations"]["v"][0]["id"]
        b["external_relationships"] = [{"registry": "clinicaltrials_gov", "registry_id": nct, "relationship": "related"}]
        self.assertIn("W_EXTERNAL_HAS_CARD", codigos(rodar([a, b]), b["uid"]))


class CorrecoesDoPiloto(unittest.TestCase):
    """Lacunas achadas na curadoria real do piloto v2.1 (regras genéricas)."""

    def test_modulo_de_contexto_de_biomarcador_nao_exige_intervencao_propria(self):
        r = copy.deepcopy(FIX["syn-ddr"])
        for a in r["design"]["arms"]["v"]:
            for i in a["interventions"]:
                i["module"] = "targeted_therapy"
        r["modules"][0]["arm_ids"] = ["exp"]; r["modules"][1]["arm_ids"] = ["exp"]
        self.assertNotIn("E_MODULE", codigos(rodar([r])))

    def test_ic_com_limite_superior_nao_atingido(self):
        r = copy.deepcopy(FIX["syn-adc"])
        r["endpoints"]["v"][0]["effect"]["ci"] = {"level": 95, "low": 0.5, "high": None, "high_not_reached": True}
        self.assertNotIn("E_VALUE", codigos(rodar([r])))
        self.assertIn("NA)", X.render_endpoint(r, r["endpoints"]["v"][0]))

    def test_conflito_entre_fontes_aparece_na_projecao(self):
        r = copy.deepcopy(FIX["syn-conflito"])
        e = r["endpoints"]["v"][2]; e["conflict"] = "cross_source_conflict"
        self.assertIn("divergência entre fontes", X.render_endpoint(r, e))

    def test_campo_nct_so_recebe_nct(self):
        env = {"state": "present", "origin": "reported", "v": [{"registry": "NCT", "id": "NCT12345678"},
                                                              {"registry": "EudraCT", "id": "2020-123456-01"}], "prov": "p"}
        self.assertEqual(X.render(env, "nct"), "NCT12345678")

    def test_unidade_nao_duplica(self):
        self.assertEqual(X.qual({"op": "=", "value": 8.3, "unit": "months"}, " m"), "8,3 m")

    def test_obitos_de_qualquer_causa_nao_viram_relacionados(self):
        r = copy.deepcopy(FIX["syn-adc"])
        for x in r["safety"]["treatment_related_deaths"]["v"]:
            x["attribution"] = "any"
        self.assertIn("qualquer causa", X.proj_tox(r))

    def test_chegou_a_terapia_derivado_exige_derivacao(self):
        r = copy.deepcopy(FIX["syn-cart"])
        r["design"]["arms"]["v"][0]["proceeded_to_planned_therapy"][0].update({"origin": "derived", "prov": "p1"})
        self.assertIn("E_DERIVED", codigos(rodar([r])))

    def test_termo_relatado_e_mapeamento(self):
        r = copy.deepcopy(FIX["syn-cart"])
        for t in r["safety"]["key_toxicities"]["v"]:
            if t["term"] == "icans":
                t.update({"reported_term": "neurologic events", "term_mapping": "broader"})
        self.assertEqual(codigos(rodar([r])), set())


class ProjetorDoPiloto(unittest.TestCase):
    def test_comparador_leva_dose_e_frequencia(self):
        r = copy.deepcopy(FIX["syn-adc"])
        r["design"]["arms"]["v"][1]["interventions"][0]["dose"] = {"value": 5, "unit": "mg", "frequency": "2x/dia"}
        self.assertIn("5 mg 2x/dia", X.proj_comparador(r))

    def test_aesi_mostra_todos_os_bracos_com_nome_clinico(self):
        r = copy.deepcopy(FIX["syn-adc"])
        r["safety"]["key_toxicities"]["v"].append({"term": "ild_pneumonitis", "scope": "any", "arm_id": "ctl", "value": F.Q(4)})
        t = X.proj_tox(r)
        self.assertIn("DPI/pneumonite", t)
        self.assertIn("(Controle)", t)


class CorrecoesDoPiloto2(unittest.TestCase):
    def test_braco_unico_sem_comparacao(self):
        r = copy.deepcopy(FIX["syn-basket-coorte"])
        r["design"].pop("comparisons")
        r["analyses"][0]["signature"]["comparison"] = "none"
        self.assertEqual(codigos(rodar([r])), set())

    def test_p_com_ponto_inicial(self):
        self.assertEqual(X._p("<.0001"), "<0,0001")
        self.assertEqual(X._p("0.004"), "=0,004")

    def test_primario_so_da_publicacao_representada(self):
        r = copy.deepcopy(FIX["syn-adc"])
        velho = copy.deepcopy(r["endpoints"]["v"][0]); velho["endpoint_id"] = "e_old"
        velho["arms_values"][0]["value"] = F.Q(99)
        r["provenance"]["p_old"] = {"source": {"type": "publication", "pmid": "00000099"}, "extraction": "explicit",
                                    "evidence_confidence": "high"}
        velho["prov"] = "p_old"
        a = copy.deepcopy(r["analyses"][0]); a["analysis_id"] = "a_old"; a["prov"] = "p_old"
        velho["maturity"]["analysis_ref"] = "a_old"
        r["analyses"].append(a); r["endpoints"]["v"].append(velho)
        self.assertNotIn("99", X.proj_primario(r))

    def test_vocabulario_novo(self):
        r = copy.deepcopy(FIX["syn-adc"])
        r["population"]["biomarker_selection"]["v"][0]["rule"] = "defines_arm"
        r["safety"]["key_toxicities"]["v"].append({"term": "fadiga", "scope": "g1", "arm_id": "exp", "value": F.Q(3)})
        r["design"]["comparisons"]["v"][0]["ctl_type"] = "contemporaneous_nonrandomized"
        self.assertFalse(any(c.startswith("E_") for c in codigos(rodar([r]))))


if __name__ == "__main__":
    unittest.main()
