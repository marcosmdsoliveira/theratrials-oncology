#!/usr/bin/env python3
"""
test_db_freshness.py — registro de identidade (Fase 0) e freshness (Fase 1).

Offline. Cards e coletas sintéticos e mínimos; o parser do PubMed é testado
contra três efetch reais gravados em fixtures/ em 2026-09-28:
  db_pubmed_34161051.xml — VISION (NEJM 2021), com ReferenceList cheia de IDs
                           de outros artigos;
  db_pubmed_32356626.xml — NEJM 2020 retratado (RetractionIn,
                           ExpressionOfConcernIn, "Retracted Publication");
  db_pubmed_24775727.xml — Can J Urol 2014, sem DOI no PubMed.

Uso:
    python3 scripts/test_db_freshness.py
"""
from __future__ import annotations

import ast
import copy
import hashlib
import json
import re
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

import db_fontes as F  # noqa: E402
import db_freshness as FR  # noqa: E402
import db_registro as R  # noqa: E402
from br_ctgov import RespostaParcial  # noqa: E402

FIX = SCRIPTS / "fixtures"
RCT3 = ["Clinical Trial, Phase III", "Journal Article", "Randomized Controlled Trial"]
RESUMO_PRIMARIO = ("Median rPFS was 8.7 vs 3.4 months (hazard ratio 0.40; 99.2% CI 0.29 to 0.57). "
                   "Median overall survival 15.3 vs 11.3 months (hazard ratio 0.62).")


# ── construtores sintéticos ─────────────────────────────────────────────────

def card(uid, nct="NCT00000001", pmid=None, status="Publicado", categoria="lupsma_prostata",
         primario="rPFS (BICR) 8,7 vs 3,4 m (HR 0,40; IC 0,29-0,57) | OS 15,3 vs 11,3 m (HR 0,62)",
         ref="", ano_pub=2021, fase="Fase 3"):
    return {"uid": uid, "estudo": uid.upper(), "acron": uid, "nct": nct, "fase": fase,
            "nct_url": f"https://clinicaltrials.gov/study/{nct}" if nct.startswith("NCT") else "",
            "pubmed_url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else "",
            "status": status, "category_id": categoria, "primario": primario, "ref": ref,
            "ano_pub": ano_pub}


def art(pmid, titulo, data, pubtypes=RCT3, resumo="", correcoes=None, doi=None, registros=()):
    return {"pmid": pmid, "titulo": titulo, "resumo": resumo, "periodico": "N Engl J Med",
            "data": data, "pubtypes": list(pubtypes), "doi": f"10.1/{pmid}" if doi is None else doi,
            "pmcid": "", "registros": list(registros), "correcoes": correcoes or []}


def ctg(nct, status="COMPLETED", has_results=False, refs=(), first_post=""):
    return {"nct": nct, "acronimo": "", "status": status, "why_stopped": "",
            "has_results": has_results, "results_first_post": first_post, "last_update_post": "",
            "primary_completion": "", "referencias": [{"pmid": p, "tipo": t} for p, t in refs]}


def coleta(si=None, artigos=None, ctgov=None, crossref=None, ausentes=None):
    return {"gerado_em": "2026-09-28T00:00:00Z", "si": si or {}, "artigos": artigos or {},
            "ctgov": ctgov or {}, "crossref": crossref or {}, "idconv": {},
            "crossref_status": "completa", "ausentes_pubmed": ausentes or [],
            "chamadas": {}, "duracao_s": 0}


def registro(cards, col, confirmacoes=None):
    return R.construir({"studies": cards}, col, confirmacoes or {})


def rodar(cards, col, baseline=None, estado=None, confirmacoes=None):
    dados = {"studies": cards}
    reg = R.construir(dados, col, confirmacoes or {})
    return reg, FR.avaliar(reg, dados, col, baseline, estado)


def por_uid(reg, uid):
    return next(c for c in reg["cards"] if c["uid"] == uid)


def classes(res, uid=None):
    return sorted(a["classe"] for a in res["alertas_novos"] if uid is None or a["uid"] == uid)


def vision(pmids=("100",), extra=None):
    artigos = {"100": art("100", "Drug X for metastatic prostate cancer", "2021-06-23",
                          resumo=RESUMO_PRIMARIO)}
    artigos.update(extra or {})
    return coleta(si={"NCT00000001": list(pmids)}, artigos=artigos,
                  ctgov={"NCT00000001": ctg("NCT00000001")})


# ── Fase 0: identidade ──────────────────────────────────────────────────────

class Identidade(unittest.TestCase):

    def test_registro_basico_e_inferencia_nao_autoriza(self):
        r = por_uid(registro([card("vision", pmid="100")], vision()), "vision")
        self.assertEqual(r["identidade"]["nivel"], "completa")
        self.assertEqual(r["primary_publication"], "100")
        a = r["analise"]
        self.assertEqual((a["tipo"], a["tipo_origem"]), ("primary", "inferred"))   # regra ⇒ inferred
        self.assertEqual(a["endpoint"]["valores"], ["rPFS", "OS"])
        self.assertEqual(a["endpoint"]["avaliacao"], "BICR")
        self.assertEqual(r["origem_classificacao"], "inferred")
        self.assertFalse(r["automation"]["clinical_extraction"]["autorizado"])   # inferred não decide
        self.assertFalse(r["automation"]["published_write"]["autorizado"])
        self.assertFalse(r["requires_review"])

    def test_tipo_explicito_no_titulo(self):
        col = vision(extra={"100": art("100", "Drug X: final overall survival analysis",
                                       "2021-06-23", resumo=RESUMO_PRIMARIO)})
        r = por_uid(registro([card("v", pmid="100")], col), "v")
        self.assertEqual((r["analise"]["tipo"], r["analise"]["tipo_origem"]), ("final", "explicit"))
        self.assertEqual(r["confianca"], "alta")
        self.assertFalse(r["automation"]["clinical_extraction"]["autorizado"])   # nunca nesta fase

    def test_indeterminado_fica_null_e_vai_para_revisao(self):
        col = vision(pmids=("90", "100"), extra={
            "90": art("90", "Drug X in prostate cancer", "2020-01-01"),
            "100": art("100", "Drug X, another report", "2021-06-23", resumo=RESUMO_PRIMARIO)})
        r = por_uid(registro([card("v", pmid="100")], col), "v")
        self.assertIsNone(r["analise"]["tipo"])
        self.assertIsNone(r["analise"]["maturidade"])
        self.assertIsNone(r["origem_classificacao"])
        # dúvida clínica não vira decisão agora: fica sob demanda
        self.assertFalse(r["requires_review"])
        self.assertTrue(any(m.startswith("tipo_indeterminado") for m in r["revisao"]["clinico_sob_demanda"]))

    def test_confirmacao_humana_vale_so_para_o_mesmo_pmid(self):
        col = vision(pmids=("90", "100"), extra={
            "90": art("90", "Drug X in prostate cancer", "2020-01-01"),
            "100": art("100", "Drug X, another report", "2021-06-23", resumo=RESUMO_PRIMARIO)})
        ok = {"v": [{"uid": "v", "pmid": "100", "campo": "tipo_analise", "valor": "final",
                     "confirmado_em": "2026-09-28", "motivo": "conferido no texto completo"}]}
        r = por_uid(registro([card("v", pmid="100")], col, ok), "v")
        self.assertEqual((r["analise"]["tipo"], r["analise"]["tipo_origem"]), ("final", "human_confirmed"))
        self.assertEqual(r["origem_classificacao"], "human_confirmed")
        outro = {"v": [dict(ok["v"][0], pmid="999")]}
        r = por_uid(registro([card("v", pmid="100")], col, outro), "v")
        self.assertIsNone(r["analise"]["tipo"])
        with tempfile.TemporaryDirectory() as tmp:
            arq = Path(tmp) / "c.json"
            base = {"id": "v:100", "tipo": "classificacao", "uid": "v", "pmid": "100",
                    "campo": "tipo_analise", "decidido_em": "2026-09-28", "motivo": "m"}
            arq.write_text(json.dumps({"decisoes": [dict(base, valor="definitivo"),
                                                    dict(base, valor="final", decidido_em="28/09")]}))
            validas, avisos = R.ler_confirmacoes(arq)
            self.assertEqual(validas, {})
            self.assertEqual(len(avisos), 2)

    def test_card_sem_nct(self):
        c = card("coorte", nct="Coorte retrospectiva institucional", pmid="500",
                 categoria="ppgl", primario="ORR 30% vs 12%")
        self.assertEqual(R.pedidos({"studies": [c]}), ([], ["500"], []))
        col = coleta(artigos={"500": art("500", "Temozolomide in PPGL", "2014-01-01",
                                         pubtypes=["Journal Article"], resumo="30% versus 12%.")})
        reg, res = rodar([c], col)
        r = por_uid(reg, "coorte")
        self.assertEqual(r["identidade"]["situacao"], "sem_registro")
        self.assertEqual(r["identidade"]["nivel"], "parcial")
        self.assertIn("registro (NCT/ISRCTN)", r["identidade"]["faltando"])
        self.assertFalse(r["automation"]["identity"]["autorizado"])
        self.assertEqual(classes(res), [])

    def test_multiplos_ncts_e_isrctn(self):
        c1 = card("pool", nct="NCT00000006 / NCT00000007 / NCT00000008", pmid="100")
        c2 = card("uk", nct="ISRCTN12345678")
        c3 = card("parcial", nct="NCT00000009 e outros")
        ids = R.identificadores(c1)
        self.assertEqual((ids["situacao"], ids["nct"]),
                         ("nct_multiplo", ["NCT00000006", "NCT00000007", "NCT00000008"]))
        self.assertEqual(R.identificadores(c2)["situacao"], "isrctn")
        self.assertTrue(R.identificadores(c3)["ressalva"])
        idents, _, ncts = R.pedidos({"studies": [c1, c2]})
        self.assertIn("ISRCTN12345678", idents)
        self.assertNotIn("ISRCTN12345678", ncts)
        col = coleta(si={"NCT00000006": ["100"]},
                     artigos={"100": art("100", "Efficacy of drug X", "2020-01-01",
                                         resumo=RESUMO_PRIMARIO)},
                     ctgov={n: ctg(n) for n in ids["nct"]})
        r = por_uid(registro([c1], col), "pool")
        self.assertIsNone(r["analise"]["populacao"])
        self.assertTrue(any(m.startswith("populacao_indeterminada") for m in r["motivos_revisao"]))

    def test_pmid_sem_doi(self):
        a = F.parse_efetch((FIX / "db_pubmed_24775727.xml").read_text(encoding="utf-8"))["24775727"]
        self.assertEqual((a["doi"], a["pmcid"]), ("", ""))
        c = card("guia", nct="—", pmid="24775727", categoria="ra223_prostata", primario="—")
        r = por_uid(registro([c], coleta(artigos={"24775727": a})), "guia")
        self.assertIsNone(r["doi"])
        self.assertIn("DOI", r["identidade"]["faltando"])

    def test_varios_pmids_e_relacoes(self):
        extra = {
            "90": art("90", "Protocol of the X trial", "2019-01-01",
                      pubtypes=["Clinical Trial Protocol", "Journal Article"]),
            "101": art("101", "Health-related quality of life with drug X", "2022-01-01"),
            "102": art("102", "Safety analyses of the phase 3 X trial", "2023-01-01"),
            "103": art("103", "Outcomes by baseline PSA in X", "2023-02-01"),
            "104": art("104", "Final overall survival of drug X", "2024-01-01"),
            "105": art("105", "Erratum", "2021-09-01", pubtypes=["Published Erratum"]),
            "106": art("106", "Biomarker analysis of drug X: post hoc", "2024-05-01"),
        }
        col = vision(pmids=("90", "100", "101", "102", "103", "104", "105", "106"), extra=extra)
        r = por_uid(registro([card("v", pmid="100")], col), "v")
        rel = {p["pmid"]: p["relacao"] for p in r["publicacoes"]}
        self.assertEqual(rel, {"90": "protocol", "100": "primary_publication", "101": "qol",
                               "102": "safety", "103": "subgroup", "104": "follow_up",
                               "105": "correction", "106": "secondary_analysis"})
        self.assertEqual(r["publicacao_representada"]["pmid"], "100")
        self.assertTrue(set(rel.values()) <= set(R.RELACOES))

    def test_primeiro_relato_respeita_fase_e_tipo(self):
        col = vision(pmids=("99", "100", "101", "102"), extra={
            "99": art("99", "Radionuclide therapy: prospects", "2017-01-01", pubtypes=["Journal Article"]),
            "100": art("100", "Rationale and design of the X trial", "2018-01-01"),
            "101": art("101", "First-in-human study of X", "2019-01-01",
                       pubtypes=["Clinical Trial, Phase I", "Journal Article"]),
            "102": art("102", "X versus Y in prostate cancer", "2021-06-23", resumo=RESUMO_PRIMARIO)})
        r = por_uid(registro([card("fase3", pmid="102")], col), "fase3")
        self.assertEqual(r["primary_publication"], "102")
        self.assertEqual(r["analise"]["tipo"], "primary")

    def test_card_de_diretriz(self):
        c = card("ata", nct="Diretriz · não-trial", pmid="800", categoria="tireoide_avancado")
        col = coleta(artigos={"800": art("800", "2025 ATA Management Guidelines", "2025-08-01",
                                         pubtypes=["Journal Article", "Practice Guideline"])})
        r = por_uid(registro([c], col), "ata")
        self.assertFalse(r["analise"]["aplicavel"])
        self.assertFalse(r["requires_review"])

    def test_uid_imutavel_e_escrita_restrita(self):
        cards = [card("b_2", pmid="100"), card("a_1", nct="NCT00000002", status="Em andamento")]
        dados = {"studies": copy.deepcopy(cards)}
        col = vision()
        col["ctgov"]["NCT00000002"] = ctg("NCT00000002", "RECRUITING")
        reg = R.construir(dados, col, {})
        self.assertEqual([c["uid"] for c in reg["cards"]], ["b_2", "a_1"])
        FR.avaliar(reg, dados, col, None, None)
        self.assertEqual(dados["studies"], cards)                       # dados intocados
        reg["cards"][0]["uid"] = "outro"
        with self.assertRaises(AssertionError):
            R.conferir_uids(reg, dados)
        for alvo in (R.DATA_JS, SCRIPTS / "db_registro.json", SCRIPTS.parent / "_db_x.json"):
            with self.assertRaises(PermissionError):
                R.gravar(alvo, "{}")
        with self.assertRaises(PermissionError):                        # baseline: só criar_somente
            R.gravar(R.BASELINE, "{}")

    def test_baseline_nunca_e_sobrescrito(self):
        with tempfile.TemporaryDirectory() as tmp:
            falso = Path(tmp).resolve() / "db_backlog_baseline.json"
            falso.write_text("{}")
            with mock.patch.object(R, "BASELINE", falso), mock.patch.object(R, "SCRIPTS", Path(tmp).resolve()):
                R.gravar(falso.with_name("_db_ok.json"), "{}")        # a porta funciona aqui…
                with self.assertRaises(PermissionError):
                    R.gravar(falso, "{}", criar_somente=True)
            self.assertEqual(falso.read_text(), "{}")


# ── Fase 1: sinais e maturidade ─────────────────────────────────────────────

class Sinais(unittest.TestCase):

    def test_apresentado_que_ganhou_artigo(self):
        c = card("emer", nct="NCT00000002", status="Apresentado (ASCO 2026, LBA1)",
                 categoria="hepatobiliar", ano_pub=2026)
        col = coleta(si={"NCT00000002": ["300", "301"]},
                     artigos={"300": art("300", "Durvalumab with TACE in liver cancer", "2021-01-01"),
                              "301": art("301", "Durvalumab plus TACE in hepatocellular carcinoma",
                                         "2026-09-01")},
                     ctgov={"NCT00000002": ctg("NCT00000002", "ACTIVE_NOT_RECRUITING",
                                               refs=[("301", "DERIVED")])})
        reg, res = rodar([c], col)
        self.assertEqual(classes(res), ["apresentado_publicado"])     # 2021 < ASCO 2026: fora
        self.assertEqual(res["alertas_novos"][0]["candidato"]["pmid"], "301")
        self.assertEqual(por_uid(reg, "emer")["analise"]["tipo_origem"], "inferred")

    def test_publicado_sem_pmid_exige_relato_tipado(self):
        c = card("nut", nct="NCT00000004", status="Publicado", categoria="hepatobiliar",
                 ref="Press release Aug/2023", ano_pub=2023)
        col = coleta(si={"NCT00000004": ["400", "401"]},
                     artigos={"400": art("400", "NUC-1031 in biliary tract cancer", "2025-02-01"),
                              "401": art("401", "Biliary cancer: a view", "2025-03-01",
                                         pubtypes=["Journal Article"])},
                     ctgov={"NCT00000004": ctg("NCT00000004", "TERMINATED", has_results=True,
                                               first_post="2023-05-24")})
        reg, res = rodar([c], col)
        r = por_uid(reg, "nut")
        self.assertEqual(r["analise"]["maturidade"], "press release")
        self.assertIsNone(r["analise"]["tipo"])
        self.assertEqual(classes(res), ["ctgov", "publicado_sem_pmid"])
        pub = next(a for a in res["alertas_novos"] if a["classe"] == "publicado_sem_pmid")
        self.assertEqual([x["pmid"] for x in pub["candidatos"]], ["400"])   # 401 não é relato tipado

    def test_correcao_e_retratacao(self):
        a = F.parse_efetch((FIX / "db_pubmed_32356626.xml").read_text(encoding="utf-8"))["32356626"]
        c = card("ret", nct="Coorte", pmid="32356626", categoria="outra", primario="5,8% vs 9,4%")
        col = coleta(artigos={"32356626": a},
                     crossref={a["doi"]: [
                         {"tipo": "retratacao", "fonte": "crossref:retraction-watch",
                          "doi": "10.1056/nejmc2021225", "data": "2020-06-04"},
                         {"tipo": "errata", "fonte": "crossref:publisher", "doi": "10.1056/x",
                          "data": "2020-06-01"}]})
        reg, res = rodar([c], col)
        cor = [x for x in res["alertas_novos"] if x["classe"] == "correcao"]
        self.assertEqual(len(cor), 1)
        self.assertEqual(cor[0]["gravidade"], "crítica")
        tipos = {v["tipo"]: v for v in cor[0]["avisos"]}
        self.assertEqual(set(tipos), {"errata", "expressao_de_preocupacao", "retratacao"})
        self.assertEqual(sorted(tipos["retratacao"]["fontes"]), ["crossref:retraction-watch", "pubmed"])
        self.assertEqual({v["relacao"] for v in cor[0]["avisos"]}, {"correction", "retraction"})

    def test_inconsistencia_clara_pmid_nct(self):
        errado = card("errado", nct="NCT00000001", pmid="700")
        a1 = card("ppgl_a", nct="Coorte retrospectiva", pmid="950", categoria="ppgl", primario="30%")
        a2 = card("ppgl_b", nct="Coortes pooled", pmid="950", categoria="ppgl", primario="30%")
        col = vision(extra={"700": art("700", "Poziotinib in lung cancer", "2022-01-01",
                                       resumo=RESUMO_PRIMARIO, registros=["NCT03318939"]),
                            "950": art("950", "Temozolomide in PPGL", "2014-01-01",
                                       pubtypes=["Journal Article"], resumo="30%")})
        reg, res = rodar([errado, a1, a2], col)
        motivos = {a["uid"]: a["motivo"] for a in res["alertas_novos"]
                   if a["classe"] == "inconsistencia_pmid_nct"}
        self.assertTrue(motivos["errado"].startswith("databank_divergente"))
        self.assertTrue(motivos["ppgl_a"].startswith("pmid_compartilhado"))
        self.assertTrue(motivos["ppgl_b"].startswith("pmid_compartilhado"))

    def test_status_em_andamento_com_pmid_de_resultado_vai_para_revisao(self):
        c = card("des", nct="NCT00000011", pmid="900", status="Em andamento",
                 categoria="neuroblastoma", primario="EFS por publicar")
        col = coleta(si={"NCT00000011": ["900"]},
                     artigos={"900": art("900", "A safety trial of MIBG", "2021-05-24",
                                         pubtypes=["Journal Article"])},
                     ctgov={"NCT00000011": ctg("NCT00000011", "ACTIVE_NOT_RECRUITING")})
        r = por_uid(registro([c], col), "des")
        self.assertTrue(any(m.startswith("status_x_pmid") for m in r["motivos_revisao"]))

    def test_follow_up_mais_maduro_nao_e_alerta_e_nao_autoriza(self):
        extra = {"200": art("200", "Final overall survival analysis of drug X in prostate cancer",
                            "2024-03-01", resumo="Overall survival by blinded independent review.")}
        reg, res = rodar([card("v", pmid="100")], vision(("100", "200"), extra))
        self.assertEqual(classes(res), [])
        item = res["baseline"]["itens"][0]
        self.assertEqual(item["destino"], "possível atualização: comparar com a representada")
        self.assertEqual(item["relacao"], "follow_up")
        self.assertIsNot(item["comparabilidade"]["comparavel"], True)   # nunca True por regra

    def test_novo_mais_recente_e_menos_maduro(self):
        col = vision(("100", "200"), {
            "100": art("100", "Final analysis of drug X in prostate cancer", "2023-01-01",
                       resumo=RESUMO_PRIMARIO),
            "200": art("200", "Interim analysis of drug X plus Y", "2025-01-01")})
        reg, res = rodar([card("v", pmid="100")], col)
        self.assertEqual(por_uid(reg, "v")["analise"]["tipo"], "final")
        self.assertEqual(classes(res), [])
        item = res["baseline"]["itens"][0]
        self.assertEqual((item["tipo_analise"], item["destino"]), ("interim", "revisar"))

    def test_analise_secundaria(self):
        reg, res = rodar([card("v", pmid="100")], vision(("100", "200"), {
            "200": art("200", "Pain outcomes with drug X: a post hoc analysis", "2023-05-01")}))
        self.assertEqual(classes(res), [])
        item = res["baseline"]["itens"][0]
        self.assertEqual((item["relacao"], item["relacao_origem"]), ("secondary_analysis", "explicit"))
        self.assertEqual(item["destino"], "secondary-cards (candidata)")

    def test_comparabilidade_regra_6(self):
        c = card("v", pmid="100")
        rep = art("100", "Drug X in metastatic prostate cancer", "2021-01-01")
        casos = {
            "subgroup": art("201", "Drug X in patients who had prior docetaxel", "2023-01-01"),
            "investigador": art("202", "Updated analysis of drug X", "2023-01-01",
                                resumo="rPFS by investigator-assessed review; overall survival"),
            "PFS2": art("203", "Updated analysis of drug X", "2023-01-01",
                        resumo="PFS2 and overall survival were reported"),
            "biomarcador": art("204", "Drug X in HRR-deficient prostate cancer: final analysis",
                               "2023-01-01", resumo="overall survival"),
            "endpoint": art("205", "Final analysis of drug X", "2023-01-01", resumo="response only"),
        }
        for nome, a in casos.items():
            with self.subTest(nome):
                pub = R._pub(a, R.classificar_artigo(a), ["pubmed_si"], True)
                comp = R.comparabilidade(c, rep, a, pub)
                self.assertIs(comp["comparavel"], False, comp)
        limpo = art("206", "Final analysis of drug X", "2024-01-01",
                    resumo="rPFS by blinded independent central review; overall survival")
        comp = R.comparabilidade(c, rep, limpo,
                                 R._pub(limpo, R.classificar_artigo(limpo), ["pubmed_si"], True))
        self.assertIsNone(comp["comparavel"])                 # sem diferença ≠ comparável

    def test_basket_nct_com_varios_uids(self):
        a = card("hepatobiliar_1", nct="NCT00000005", status="Apresentado (ESMO 2026)",
                 categoria="hepatobiliar", ano_pub=2026)
        b = card("endometrio_1", nct="NCT00000005", status="Apresentado (ESMO 2026)",
                 categoria="endometrio", ano_pub=2026)
        k1 = card("k_bili", nct="NCT00000012", pmid="960", categoria="hepatobiliar")
        k2 = card("k_endo", nct="NCT00000012", pmid="960", categoria="endometrio")
        col = coleta(si={"NCT00000005": ["600"], "NCT00000012": ["960"]},
                     artigos={"600": art("600", "Drug Y in biliary tract cancer", "2026-10-01"),
                              "960": art("960", "Pembrolizumab in MSI-H tumours", "2020-01-01")},
                     ctgov={"NCT00000005": ctg("NCT00000005"), "NCT00000012": ctg("NCT00000012")})
        reg, res = rodar([a, b, k1, k2], col)
        self.assertEqual(R.mapa_irmaos([a, b])["NCT00000005"], ["hepatobiliar_1", "endometrio_1"])
        self.assertEqual(por_uid(reg, "endometrio_1")["identidade"]["nct_compartilhado_com"],
                         ["hepatobiliar_1"])
        self.assertEqual([x["uid"] for x in res["alertas_novos"]
                          if x["classe"] == "apresentado_publicado"], ["hepatobiliar_1"])
        self.assertIs(por_uid(reg, "endometrio_1")["publicacoes"][0]["coorte"], False)
        for u in ("k_bili", "k_endo"):            # basket: mesmo artigo no mesmo NCT é legítimo
            self.assertFalse(any(m.startswith("pmid_compartilhado")
                                 for m in por_uid(reg, u)["motivos_revisao"]))


# ── Baseline × execuções futuras ────────────────────────────────────────────

class Baseline(unittest.TestCase):

    def cenario(self):
        cards = [card("v", pmid="100"),
                 card("apr", nct="NCT00000002", status="Apresentado (ASCO 2026)", ano_pub=2026,
                      categoria="hepatobiliar")]
        col = vision(("100", "200", "201"), {
            "200": art("200", "Final overall survival of drug X", "2024-01-01", resumo="overall survival"),
            "201": art("201", "QoL: post hoc analysis", "2023-01-01")})
        col["si"]["NCT00000002"] = []
        col["ctgov"]["NCT00000002"] = ctg("NCT00000002", "ACTIVE_NOT_RECRUITING")
        return cards, col

    def test_baseline_nao_reaparece_como_novidade(self):
        cards, col = self.cenario()
        _, r1 = rodar(cards, col)
        self.assertTrue(r1["primeira_fotografia"])
        self.assertEqual({i["pmid"] for i in r1["baseline"]["itens"]}, {"200", "201"})
        _, r2 = rodar(cards, col, r1["baseline"], r1["estado_novo"])
        self.assertEqual(r2["alertas_novos"], [])
        self.assertEqual(r2["novos_sem_alerta"], [])
        self.assertIsNone(r2["baseline"])                       # não recria

    def test_depois_do_baseline_so_o_novo_conta(self):
        cards, col = self.cenario()
        _, r1 = rodar(cards, col)
        col2 = copy.deepcopy(col)
        col2["si"]["NCT00000001"].append("202")
        col2["artigos"]["202"] = art("202", "Long-term outcomes of drug X", "2026-02-01")
        col2["si"]["NCT00000002"] = ["300"]
        col2["artigos"]["300"] = art("300", "Drug Z in hepatocellular carcinoma", "2026-09-01")
        col2["ctgov"]["NCT00000001"] = ctg("NCT00000001", has_results=True, first_post="2026-09-01")
        _, r2 = rodar(cards, col2, r1["baseline"], r1["estado_novo"])
        self.assertEqual(classes(r2), ["apresentado_publicado", "ctgov", "ctgov"])
        self.assertEqual([x["pmid"] for x in r2["novos_sem_alerta"]], ["202"])   # informativo
        self.assertIn("202", r2["estado_novo"]["vistos_pos_baseline"]["v"])
        _, r3 = rodar(cards, col2, r1["baseline"], r2["estado_novo"])
        self.assertEqual(r3["alertas_novos"], [])
        self.assertEqual(r3["novos_sem_alerta"], [])

    def test_card_novo_nao_despeja_historico_e_uid_removido_alerta(self):
        cards, col = self.cenario()
        _, r1 = rodar(cards, col)
        novo = card("novo", nct="NCT00000001", pmid="100")
        _, r2 = rodar([cards[0], novo], col, r1["baseline"], r1["estado_novo"])
        self.assertEqual(r2["cards_novos"], ["novo"])
        self.assertEqual([(a["classe"], a["uid"]) for a in r2["alertas_novos"]],
                         [("integridade", "apr")])


# ── Coleta: parser, resposta parcial, fontes ────────────────────────────────

class Coleta(unittest.TestCase):

    def test_parser_ids_so_do_proprio_artigo(self):
        a = F.parse_efetch((FIX / "db_pubmed_34161051.xml").read_text(encoding="utf-8"))
        self.assertEqual(list(a), ["34161051"])
        v = a["34161051"]
        self.assertEqual((v["doi"], v["pmcid"], v["data"], v["registros"]),
                         ("10.1056/nejmoa2107322", "PMC8446332", "2021-06-23", ["NCT03511664"]))

    def test_esearch_parcial_e_malformado(self):
        parcial = {"esearchresult": {"count": "5", "idlist": ["1", "2", "3"]}}
        ruim = {"esearchresult": {"ERROR": "Search Backend failed"}}
        bom = {"esearchresult": {"count": "1", "idlist": ["7"]}}
        with mock.patch.object(F.time, "sleep"):
            with mock.patch.object(F, "_ncbi_json", return_value=parcial):
                self.assertRaises(RespostaParcial, F.pmids_ligados, "NCT00000001")
            with mock.patch.object(F, "_ncbi_json", side_effect=[ruim, bom]):
                self.assertEqual(F.pmids_ligados("NCT00000001"), ["7"])
            with mock.patch.object(F, "_ncbi_json", return_value=ruim):
                self.assertRaises(RespostaParcial, F.pmids_ligados, "NCT00000001")

    def test_efetch_ctgov_idconv_parciais_abortam(self):
        with mock.patch.object(F.time, "sleep"):
            with mock.patch.object(F, "_efetch", return_value={}):
                self.assertRaises(RespostaParcial, F.buscar_artigos, [str(i) for i in range(10)])
            um = {"1": {"pmid": "1"}}
            with mock.patch.object(F, "_efetch", return_value=um), \
                 mock.patch.object(F, "_existe_no_pubmed", return_value=False):
                self.assertEqual(F.buscar_artigos(["1", "2"]), (um, ["2"]))   # ausência confirmada
            with mock.patch.object(F, "_efetch", return_value=um), \
                 mock.patch.object(F, "_existe_no_pubmed", return_value=True):
                self.assertRaises(RespostaParcial, F.buscar_artigos, ["1", "2"])
            with mock.patch.object(F, "_ctgov_lote", return_value={}):
                self.assertRaises(RespostaParcial, F.registros_ctgov, ["NCT00000001", "NCT00000002"])
            with mock.patch.object(F, "http_json",
                                   return_value={"status": "ok", "records": [{"requested-id": "1"}]}):
                self.assertRaises(RespostaParcial, F.converter_ids, ["1", "2"])

    def test_crossref_e_complementar(self):
        artigos = {"1": art("1", "t", "2020-01-01", doi="10.1/a")}
        comum = dict(pmids_ligados=mock.DEFAULT, registros_ctgov=mock.DEFAULT,
                     buscar_artigos=mock.DEFAULT, converter_ids=mock.DEFAULT)
        with mock.patch.multiple(F, **comum) as m, \
             mock.patch.object(F, "crossref_atualizacoes", side_effect=urllib.error.URLError("x")):
            m["pmids_ligados"].return_value = ["1"]
            m["registros_ctgov"].return_value = {}
            m["buscar_artigos"].return_value = (artigos, [])
            m["converter_ids"].return_value = {"1": {}}
            col = F.coletar(["NCT00000001"], ["1"], [])
        self.assertEqual((col["crossref_status"], col["crossref_falhas"]), ("incompleta", ["10.1/a"]))
        with mock.patch.multiple(F, **comum) as m, \
             mock.patch.object(F, "crossref_atualizacoes") as cr:
            m["pmids_ligados"].return_value = ["1"]
            m["registros_ctgov"].return_value = {}
            m["buscar_artigos"].return_value = (artigos, [])
            m["converter_ids"].return_value = {"1": {}}
            col = F.coletar(["NCT00000001"], ["1"], [], usar_crossref=False)
            cr.assert_not_called()
        self.assertEqual(col["crossref_status"], "desligada")

    def test_falha_tecnica_nao_grava_nada(self):
        antes = hashlib.sha256(R.DATA_JS.read_bytes()).hexdigest()
        with mock.patch.object(R, "obter_coleta", side_effect=RespostaParcial("simulada")), \
             mock.patch.object(R, "gravar") as gravar:
            self.assertEqual(FR.executar(reusar=False), R.FALHA_TECNICA)
            gravar.assert_not_called()
        self.assertEqual(hashlib.sha256(R.DATA_JS.read_bytes()).hexdigest(), antes)


# ── Fase 1.5: machine_verified, domínios, prioridade, integridade, inbox ─────

import db_confianca as Cf  # noqa: E402


def registro_ct(nct="NCT00000001", acronimo="", titulo=""):
    c = ctg(nct)
    c.update(acronimo=acronimo, titulo_breve=titulo, titulo_oficial="")
    return c


class Fase15(unittest.TestCase):

    def ident(self, cards, col, uid):
        return por_uid(registro(cards, col), uid)["automation"]["identity"]

    def test_regras_machine_verified(self):
        c = card("ember", pmid="100")
        c["estudo"] = "EMBER-3 (2025)"
        col = vision(extra={"100": art("100", "Imlunestrant in EMBER-3", "2021-06-23",
                                       resumo=RESUMO_PRIMARIO)})
        col["ctgov"]["NCT00000001"] = registro_ct(acronimo="EMBER-3")
        i = self.ident([c], col, "ember")
        self.assertEqual((i["nivel"], i["regra"].split(":")[0]), ("machine_verified", "MV-2"))
        self.assertTrue(i["autorizado"])

    def test_titulo_copiado_nao_verifica_estudo(self):
        """E e D (título e números copiados do artigo) não bastam quando o card
        tem nome de estudo que não aparece nem no registro nem no artigo."""
        c = card("k", pmid="100")
        c.update(estudo="KEYNOTE-999 (2020)", titulo_full="Drug X for metastatic prostate cancer")
        i = self.ident([c], vision(), "k")
        self.assertEqual(i["nivel"], "insuficiente")

    def test_conflito_nunca_e_machine_verified(self):
        c = card("k", pmid="700")
        c["estudo"] = "EMBER-3 (2025)"
        col = vision(extra={"700": art("700", "EMBER-3 results", "2022-01-01", resumo=RESUMO_PRIMARIO,
                                       registros=["NCT09999999"])})
        col["si"]["NCT00000001"] = ["700"]
        col["ctgov"]["NCT00000001"] = registro_ct(acronimo="EMBER-3")
        i = self.ident([c], col, "k")
        self.assertEqual(i["nivel"], "conflito")
        self.assertFalse(i["autorizado"])

    def test_sem_registro_autor_ano_e_sem_pmid_com_sigla(self):
        c = card("h", nct="Coorte retrospectiva", pmid="950", categoria="ppgl",
                 primario="ORR 30% vs 12%; DCR 45% vs 20%")
        c["estudo"] = "Temozolomida em PPGL (Hadoux, 2014)"
        a = art("950", "SDHB and temozolomide", "2014-05-01", pubtypes=["Journal Article"],
                resumo="30% versus 12%; 45% versus 20%")
        a["primeiro_autor"] = "Hadoux"
        self.assertEqual(self.ident([c], coleta(artigos={"950": a}), "h")["regra"].split(":")[0], "MV-5")
        d = card("des", nct="NCT00000002", status="Em andamento")
        d["estudo"] = "COMPOSE (em andamento)"
        col = coleta(si={"NCT00000002": []}, ctgov={"NCT00000002": registro_ct("NCT00000002", "COMPOSE")})
        self.assertEqual(self.ident([d], col, "des")["regra"].split(":")[0], "MV-6")

    def test_dominios_clinico_e_escrita_nunca_autorizados(self):
        c = card("ember", pmid="100")
        c["estudo"] = "EMBER-3 (2025)"
        col = vision(extra={"100": art("100", "EMBER-3: final overall survival analysis", "2021-06-23",
                                       resumo=RESUMO_PRIMARIO)})
        col["ctgov"]["NCT00000001"] = registro_ct(acronimo="EMBER-3")
        col["crossref"] = {"10.1/100": []}
        a = por_uid(registro([c], col), "ember")["automation"]
        self.assertTrue(a["identity"]["autorizado"])
        self.assertTrue(a["bibliographic_metadata"]["autorizado"])
        self.assertTrue(a["publication_relationship"]["autorizado"])
        self.assertFalse(a["clinical_extraction"]["autorizado"])
        self.assertFalse(a["published_write"]["autorizado"])

    def test_errata_impacto(self):
        col = coleta()
        col["avisos"] = {
            "1": art("1", "Erratum.", "2025-01-01", pubtypes=["Published Erratum"]),
            "2": art("2", "Correction", "2025-01-01", pubtypes=["Published Erratum"],
                     resumo="The name of the fourth author was misspelled."),
            "3": art("3", "Correction", "2025-01-01", pubtypes=["Published Erratum"],
                     resumo="In Table 2, the hazard ratio for overall survival should read 0.71."),
        }
        aviso = lambda p, t="errata": {"tipo": t, "pmid": p, "chave": f"{t}:{p}"}  # noqa: E731
        self.assertEqual(Cf.impacto_aviso(aviso("1"), col)["impacto"], "indeterminada")
        self.assertEqual(Cf.impacto_aviso(aviso("9"), col)["impacto"], "indeterminada")   # sem nota
        self.assertEqual(Cf.impacto_aviso(aviso("2"), col)["impacto"], "administrativa")
        self.assertEqual(Cf.impacto_aviso(aviso("3"), col)["impacto"], "potencialmente_clinica")
        sinal = {"classe": "correcao", "uid": "v", "estudo": "V", "categoria": "c", "chave": "correcao:v:x",
                 "motivo": "m", "avisos": [aviso("1"), aviso("2"), aviso("3"),
                                           aviso("4", "expressao_de_preocupacao")]}
        itens = Cf.priorizar_sinal(sinal, {"uid": "v"}, {}, col, {})
        # Fase 1.6: a prioridade de uma errata vem do TEXTO lido por db_correcoes.
        # Sem nota processada, é UNRESOLVED: acompanhada, nunca presumida benigna.
        self.assertEqual([(i["classe"], i["acao"]) for i in itens],
                         [("P2_SECONDARY_OR_WATCH", "acompanhar")] * 3 + [("P0_INTEGRITY", "humana")])
        self.assertTrue(all(i["clinical_materiality"] == "indeterminada" for i in itens[:3]))

    def test_ctgov_sem_publicacao_e_watch(self):
        sinal = {"classe": "ctgov", "uid": "v", "estudo": "V", "categoria": "c", "chave": "ctgov:v:x",
                 "motivo": "NCT00000001: resultados depositados no CT.gov (2025-01-01), mas o card é "
                           "'Apresentado' sem artigo"}
        it = Cf.priorizar_sinal(sinal, {"uid": "v"}, {}, coleta(), {})[0]
        self.assertEqual((it["classe"], it["acao"]), ("WATCH_PUBLICATION_PENDING", "acompanhar"))

    def test_eixos_separados_alta_confianca_baixa_materialidade_nao_vai_para_humano(self):
        reg = por_uid(registro([card("v", pmid="100")], vision()), "v")
        prot = {"pmid": "9", "relacao": "protocol", "relacao_origem": "explicit", "natureza": "protocolo",
                "coorte": True, "ligacao": ["pubmed_si"], "tipo_analise": None, "tipo_origem": None}
        it = Cf.priorizar_publicacao(prot, reg, card("v", pmid="100"), vision())
        self.assertEqual((it["evidence_confidence"], it["clinical_materiality"], it["acao"]),
                         ("alta", "baixa", "arquivar"))
        qol = dict(prot, relacao="qol", natureza="relato_de_ensaio")
        it = Cf.priorizar_publicacao(qol, reg, card("v", pmid="100"), vision())
        self.assertEqual((it["classe"], it["acao"]), ("P2_SECONDARY_OR_WATCH", "acompanhar"))

    def cenario_integridade(self):
        c_nct = card("aspen", nct="NCT00000001", pmid="100")
        c_nct["estudo"] = "ASPEN (2016)"
        c_pmid = card("kn", nct="NCT00000002", pmid="200", categoria="endometrio")
        c_pmid["estudo"] = "KEYNOTE-158 endométrio (2020)"
        c_meta = card("sor", nct="NCT00000003", pmid="300", categoria="hepatobiliar")
        c_meta["estudo"] = "SORAMIC (2019)"
        dono = card("anbl_a", nct="NCT00000004", pmid="400", categoria="neuroblastoma")
        dono["estudo"] = "ANBL09P1 (2021)"
        outro = card("anbl_b", nct="NCT00000005", pmid="400", status="Em andamento",
                     categoria="neuroblastoma")
        outro["estudo"] = "ANBL1531 (COG)"
        col = coleta(
            si={"NCT00000001": [], "NCT00000002": ["201", "202"], "NCT00000003": [],
                "NCT00000004": ["400"], "NCT00000005": ["400"]},
            artigos={
                "100": art("100", "ASPEN: everolimus vs sunitinib", "2016-01-01", registros=["NCT00000009"]),
                "200": art("200", "Poziotinib in lung cancer", "2021-01-01", registros=["NCT00000008"]),
                "201": art("201", "Pembrolizumab in endometrial cancer: KEYNOTE-158", "2022-01-06"),
                "202": art("202", "Health-related quality of life in endometrial cancer in KEYNOTE-158",
                           "2022-07-11"),
                "300": art("300", "SORAMIC palliative cohort", "2019-01-01", registros=["NCT00000007"]),
                "400": art("400", "A safety trial of MIBG in neuroblastoma", "2021-05-24",
                           pubtypes=["Journal Article"], registros=["NCT00000004", "NCT00000005"]),
            },
            ctgov={"NCT00000001": registro_ct("NCT00000001", "", "Another study"),
                   "NCT00000009": registro_ct("NCT00000009", "ASPEN"),
                   "NCT00000002": registro_ct("NCT00000002", "KEYNOTE-158"),
                   "NCT00000008": registro_ct("NCT00000008", "", "Poziotinib in NSCLC"),
                   "NCT00000003": registro_ct("NCT00000003", "SORAMIC"),
                   "NCT00000007": registro_ct("NCT00000007", "", "Eye disease study"),
                   "NCT00000004": registro_ct("NCT00000004", "", "MIBG induction"),
                   "NCT00000005": registro_ct("NCT00000005", "", "MIBG or lorlatinib")})
        cards = [c_nct, c_pmid, c_meta, dono, outro]
        return cards, col

    def test_integridade_classificacoes(self):
        cards, col = self.cenario_integridade()
        reg = registro(cards, col)
        a = Cf.analisar_integridade(reg, {"studies": cards}, col)
        self.assertEqual({u: x["classificacao"] for u, x in a.items()},
                         {"aspen": "MACHINE_VERIFIED_ERROR", "kn": "MACHINE_VERIFIED_ERROR",
                          "sor": "SOURCE_METADATA_ERROR", "anbl_a": "MACHINE_VERIFIED_CORRECT",
                          "anbl_b": "NO_REPLACEMENT_FOUND"})
        self.assertEqual(a["aspen"]["nct_candidato"], ["NCT00000009"])
        self.assertEqual([x["pmid"] for x in a["kn"]["candidatos"]], ["201"])     # QoL fica de fora
        self.assertTrue(a["sor"]["fontes_concordam"] and a["sor"]["fontes_divergem"])

    def test_decisoes_e_baseline_v2(self):
        itens = [{"id": "a"}, {"id": "b"}, {"id": "c"}, {"id": "d"}]
        dec = [{"id": "a", "tipo": "ignore"}, {"id": "b", "tipo": "approve"},
               {"id": "c", "tipo": "defer", "ate": "2099-01-01"},
               {"id": "d", "tipo": "defer", "ate": "2000-01-01"}]
        abertos, resolvidos = FR.aplicar_decisoes(itens, dec, "2026-09-28")
        self.assertEqual(([i["id"] for i in abertos], len(resolvidos)), (["d"], 3))
        cards, col = Baseline().cenario()
        _, r1 = rodar(cards, col)
        base = r1["baseline"]
        self.assertEqual(base["schema"], "theratrials-db-backlog-baseline/2")
        self.assertTrue(all("revisao" not in i and "prioridade" in i for i in base["itens"]))
        with tempfile.TemporaryDirectory() as tmp:
            arq = Path(tmp).resolve() / "db_backlog_baseline.json"
            with mock.patch.object(R, "BASELINE", arq), mock.patch.object(R, "SCRIPTS", Path(tmp).resolve()):
                arq.write_text(json.dumps({"schema": "theratrials-db-backlog-baseline/1",
                                           "itens": [{"revisao": {"decisao": "x"}}]}))
                with self.assertRaises(PermissionError):         # v1 com decisão: não migra
                    R.gravar(arq, "{}", migrar_baseline_v1=True)
                arq.write_text(json.dumps({"schema": "theratrials-db-backlog-baseline/2", "itens": []}))
                with self.assertRaises(PermissionError):         # v2 é imutável
                    R.gravar(arq, "{}", migrar_baseline_v1=True)
                arq.write_text(json.dumps({"schema": "theratrials-db-backlog-baseline/1",
                                           "itens": [{"revisao": None}]}))
                R.gravar(arq, '{"schema": "theratrials-db-backlog-baseline/2"}', migrar_baseline_v1=True)

    def test_inbox_semanal(self):
        from datetime import date
        extra = {"200": art("200", "Final overall survival of drug X in prostate cancer", "2026-09-22",
                            resumo="overall survival by blinded independent review"),
                 "201": art("201", "Quality of life with drug X", "2026-09-22")}
        cards = [card("v", pmid="100")]
        col = vision(("100", "200", "201"), extra)
        reg = R.construir({"studies": cards}, col, {})
        sim = Cf.simular_inbox(reg, {"studies": cards}, col, date(2026, 9, 28), semanas=2)
        self.assertEqual(sim["totais"], {"humana": 1, "acompanhar": 1, "arquivar": 0})


# ── Fase 1.6: correções, integridade editorial, decisões de integridade ─────

import db_correcoes as K  # noqa: E402
import db_p0 as P0  # noqa: E402


class Fase16(unittest.TestCase):

    def test_classificacao_das_correcoes(self):
        t_orig = "Overall survival with drug X in randomised patients"
        casos = {
            "In the version initially published, John Smith was presented in the author list without a "
            "middle initial. "
            "The error has been corrected in the HTML and PDF versions of the article.": "ADMINISTRATIVE",
            "In Table 8, the row heading “Follicular Carcinoma” should read “Follicular Carcinoma and IEFVPTC”. "
            "These and additional minor spelling errors have been updated in the online article.": "PRESENTATIONAL",
            "In Table 1, seven rows have been added to the prior therapies section.": "CLINICAL_DATA",
            "In the Results section, the hazard ratio should read 0.71.": "CLINICAL_DATA",
            "Appendix 1 of this Article has been corrected as of December 19, 2024.": "UNRESOLVED",
        }
        for texto, esperado in casos.items():
            with self.subTest(esperado):
                self.assertEqual(K.classificar(texto, t_orig)["classe"], esperado)
        self.assertEqual(K.classificar(None)["classe"], "UNRESOLVED")          # sem texto: nunca benigna
        self.assertEqual(K.classificar("")["classe"], "UNRESOLVED")
        # a citação do artigo corrigido (com "survival", "randomised") não torna a nota clínica
        nota = f"Smith J, et al. {t_orig}. Lancet 2024; 404: 1227–39—the affiliation of the third author was wrong."
        self.assertEqual(K.classificar(nota, t_orig)["classe"], "ADMINISTRATIVE")
        # iniciais de nome não quebram a frase
        self.assertEqual(len(K.frases("Written by Theodore W. Laetsch and Lisa J. States. Licence changed.")), 2)

    def test_canais_exigem_identificador_da_nota(self):
        xml_outro = ('<pmc-articleset><article><front><article-meta><article-id pub-id-type="pmid">999</article-id>'
                     '</article-meta></front><body><p>texto</p></body></article></pmc-articleset>')
        xml_certo = xml_outro.replace(">999<", ">123<")
        with mock.patch.object(F, "http_texto", return_value=xml_outro), mock.patch.object(F.time, "sleep"):
            self.assertIn("rejeitado", K.pmc_texto("PMC1", "123", None))
        with mock.patch.object(F, "http_texto", return_value=xml_certo), mock.patch.object(F.time, "sleep"):
            self.assertEqual(K.pmc_texto("PMC1", "123", None)["texto"], "texto")
        outro = {"resultList": {"result": [{"pmid": "999", "doi": "10.1/outra"}]}}
        with mock.patch.object(K, "http_json", return_value=outro), mock.patch.object(K.time, "sleep"):
            self.assertIsNone(K.epmc_registro("123", "10.1/nota"))
        with mock.patch.object(F, "http_texto", return_value="J Clin Oncol|2013|31|3049||k|23845678"), \
             mock.patch.object(F.time, "sleep"):
            self.assertEqual(K.ecitmatch("J Clin Oncol. 2013 Aug 20;31(24):3049"), "23845678")

    def prioridade_da_correcao(self, classe, tipo="errata"):
        aviso = {"tipo": tipo, "pmid": "1", "chave": f"{tipo}:1", "ref": ""}
        col = coleta()
        col["notas"] = {"v|x": {"uid": "v", "aviso": aviso, "classe": classe, "base": "b", "canal": "PMC"}}
        sinal = {"classe": "correcao", "uid": "v", "estudo": "V", "categoria": "c", "chave": "correcao:v:x",
                 "motivo": "m", "avisos": [aviso]}
        return Cf.priorizar_sinal(sinal, {"uid": "v"}, {}, col, {})[0]

    def test_prioridade_por_classe_de_correcao(self):
        self.assertEqual(self.prioridade_da_correcao("ADMINISTRATIVE")["acao"], "arquivar")
        self.assertEqual(self.prioridade_da_correcao("PRESENTATIONAL")["acao"], "arquivar")
        it = self.prioridade_da_correcao("CLINICAL_DATA")
        self.assertEqual((it["classe"], it["acao"]), ("P1_CLINICAL_UPDATE", "humana"))
        it = self.prioridade_da_correcao("UNRESOLVED")
        self.assertEqual((it["acao"], it["clinical_materiality"]), ("acompanhar", "indeterminada"))
        # expressão de preocupação é P0 mesmo com texto administrativo
        it = self.prioridade_da_correcao("ADMINISTRATIVE", tipo="expressao_de_preocupacao")
        self.assertEqual((it["classe"], it["acao"]), ("P0_INTEGRITY", "humana"))

    def test_integrity_hold(self):
        c = card("s", pmid="100")
        col = vision(extra={"100": art("100", "Drug X", "2021-06-23", resumo=RESUMO_PRIMARIO,
                                       correcoes=[{"tipo": "expressao_de_preocupacao", "fonte": "pubmed",
                                                   "pmid": "7", "ref": "J. doi: 10.1/eoc."}])})
        dados = {"studies": [c]}
        r = por_uid(R.construir(dados, col, {}), "s")
        self.assertTrue(r["integrity_hold"]["ativo"])
        self.assertFalse(r["automation"]["clinical_extraction"]["autorizado"])
        reg = R.construir(dados, col, {})
        Cf.anotar(reg, dados, col, [{"id": "integrity_hold:s", "tipo": "approve"}])
        self.assertFalse(por_uid(reg, "s")["integrity_hold"]["ativo"])

    def test_decisao_de_integridade_so_para_o_mesmo_conflito(self):
        c = card("sor", pmid="300", categoria="hepatobiliar")
        c["estudo"] = "SORAMIC (2019)"
        col = vision(extra={"300": art("300", "SORAMIC palliative cohort", "2019-01-01",
                                       resumo=RESUMO_PRIMARIO, registros=["NCT00000007"])})
        col["si"]["NCT00000001"] = []
        col["ctgov"]["NCT00000001"] = registro_ct(acronimo="SORAMIC")
        base = {"id": "inconsistencia_pmid_nct:sor:databank_divergente", "uid": "sor", "pmid": "300",
                "campo": "integridade", "valor": "SOURCE_METADATA_ERROR", "confirmado_em": "2026-09-28",
                "motivo": "m"}
        ok = {"sor": [dict(base, evidencia={"nct_declarado_pelo_artigo": "NCT00000007"})]}
        r = por_uid(registro([c], col, ok), "sor")
        self.assertFalse(any(m.startswith("databank_divergente") for m in r["motivos_revisao"]))
        self.assertEqual(r["integridade_resolvida"]["valor"], "SOURCE_METADATA_ERROR")
        self.assertNotEqual(r["automation"]["identity"]["nivel"], "conflito")
        outro = {"sor": [dict(base, evidencia={"nct_declarado_pelo_artigo": "NCT00000099"})]}
        r = por_uid(registro([c], col, outro), "sor")
        self.assertTrue(any(m.startswith("databank_divergente") for m in r["motivos_revisao"]))
        with tempfile.TemporaryDirectory() as tmp:
            arq = Path(tmp) / "d.json"
            arq.write_text(json.dumps({"decisoes": [dict(base, tipo="classificacao", decidido_em="2026-09-28")]}))
            validas, avisos = R.ler_confirmacoes(arq)
            self.assertEqual(validas, {})                      # integridade sem evidência: ignorada
            self.assertTrue(avisos)

    def test_inbox_nao_recebe_errata_nao_resolvida(self):
        from datetime import date
        a = art("100", "Drug X", "2021-06-23", resumo=RESUMO_PRIMARIO,
                correcoes=[{"tipo": "errata", "fonte": "pubmed", "pmid": "7", "ref": "J. doi: 10.1/e."}])
        col = vision(extra={"100": a})
        col["avisos"] = {"7": art("7", "Erratum", "2026-09-22", pubtypes=["Published Erratum"])}
        cards = [card("v", pmid="100")]
        reg = R.construir({"studies": cards}, col, {})
        sim = Cf.simular_inbox(reg, {"studies": cards}, col, date(2026, 9, 28), semanas=2)
        self.assertEqual(sim["totais"]["humana"], 0)
        self.assertEqual(sim["totais"]["acompanhar"], 1)

    def test_utilidades_das_propostas(self):
        self.assertEqual(P0.faixas_unidade("SBRT 25-50 Gy em 5 frações; 200 mg"), {"25-50gy", "200mg"})
        with mock.patch.object(K, "ecitmatch", return_value="32070062"):
            c = P0.citacoes_no_ref("Tella SH et al. Int J Mol Sci 2020;21(4):1273 (revisão).")
        self.assertEqual((c[0]["autor_citado"], c[0]["pmid"]), ("Tella", "32070062"))
        p = P0.prop("nct", "A", "B", "CT.gov", "NCT1", "e", "alta", P0.BIB)
        self.assertEqual(set(p), {"campo", "valor_atual", "valor_proposto", "fonte", "identificador",
                                  "evidencia", "confianca", "natureza", "acao"})


# ── Fechamento dos P0: aplicação em cópia, quarentena, rechecagem ───────────

import db_migracao_p0_2026_09 as AP  # noqa: E402


class FechamentoP0(unittest.TestCase):

    def base_js(self, tmp):
        dados = {"categories": [], "studies": [card("a_1", pmid="100"), card("b_2", pmid="200")],
                 "filters": {}, "metadata": {}}
        js = Path(tmp) / "data.js"
        js.write_text("/* cabeçalho */\nwindow.THERA_DATA = " +
                      json.dumps(dados, ensure_ascii=False, separators=(",", ":")) + ";\n", encoding="utf-8")
        return js

    def rodar_aplicador(self, tmp, mudancas):
        js = self.base_js(tmp)
        copia_dir = Path(tmp).resolve() / "_db_copia"
        with mock.patch.object(AP.R, "DATA_JS", js), mock.patch.object(AP, "COPIA_DIR", copia_dir), \
             mock.patch.object(AP, "COPIA", copia_dir / "data.js"), \
             mock.patch.object(AP, "PROV", Path(tmp).resolve() / "_db_prov.jsonl"), \
             mock.patch.object(AP, "DIFF", Path(tmp) / "_db_diff.md"), \
             mock.patch.object(AP.R, "SCRIPTS", Path(tmp).resolve()), \
             mock.patch.object(AP, "MUDANCAS", mudancas):
            rc = AP.main()
        return rc, js, copia_dir / "data.js", Path(tmp).resolve() / "_db_prov.jsonl"

    def test_aplica_em_copia_com_proveniencia(self):
        m = [("a_1", "nct", "NCT00000001", "NCT00000009", "NCT00000009", "CT.gov", "e", "m", "alta", "bib")]
        with tempfile.TemporaryDirectory() as tmp:
            rc, js, copia, prov = self.rodar_aplicador(tmp, m)
            self.assertEqual(rc, 0)
            original = js.read_text(encoding="utf-8")
            novo = copia.read_text(encoding="utf-8")
            self.assertIn("NCT00000001", original)                 # publicado intocado
            self.assertIn("NCT00000009", novo)
            self.assertEqual(novo.replace("NCT00000009", "NCT00000001", 1), original)   # diff mínimo
            linhas = [json.loads(x) for x in prov.read_text().splitlines()]
            self.assertEqual({k for k in linhas[0]} >= {"uid", "campo", "anterior", "novo", "identificador",
                                                        "fonte", "motivo", "evidence_confidence",
                                                        "decisao_humana"}, True)

    def test_valor_divergente_nao_grava_nada(self):
        m = [("a_1", "nct", "NCT09999999", "NCT00000009", "x", "x", "x", "x", "alta", "bib")]
        with tempfile.TemporaryDirectory() as tmp:
            rc, js, copia, prov = self.rodar_aplicador(tmp, m)
            self.assertEqual(rc, 1)
            self.assertFalse(copia.exists())
            self.assertFalse(prov.exists())

    def test_aplicador_real_so_mexe_em_campos_declarados(self):
        campos = {(u, c) for u, c, *_ in AP.MUDANCAS}
        self.assertTrue(all(c not in ("uid", "category_id") for _, c in campos))
        self.assertEqual(len(campos), len(AP.MUDANCAS))              # sem duplicatas

    def test_rechecagem_mensal_e_transicoes(self):
        self.assertTrue(K.precisa_rechecar(None, "2026-09-28"))
        self.assertFalse(K.precisa_rechecar({"ultima_rechecagem": "2026-09-28"}, "2026-10-20"))
        self.assertTrue(K.precisa_rechecar({"ultima_rechecagem": "2026-09-28"}, "2026-10-28"))
        t = K.transicoes({"a": "UNRESOLVED", "b": "UNRESOLVED", "c": "UNRESOLVED", "d": "CLINICAL_DATA"},
                         {"a": "CLINICAL_DATA", "b": "ADMINISTRATIVE", "c": "UNRESOLVED", "d": "CLINICAL_DATA"})
        self.assertEqual(t, {"para_inbox": ["a"], "arquivadas": ["b"], "seguem_unresolved": ["c"]})
        e = K.estado_novo({"intervalo_dias": 30}, {"a": {"classe": "UNRESOLVED"}}, "2026-09-28")
        self.assertEqual(e, {"intervalo_dias": 30, "ultima_rechecagem": "2026-09-28", "classes": {"a": "UNRESOLVED"}})

    def test_quarentena_e_historico_do_hold(self):
        c = card("q", pmid="100")
        col = vision(extra={"100": art("100", "Drug X", "2021-06-23", resumo=RESUMO_PRIMARIO,
                                       correcoes=[{"tipo": "expressao_de_preocupacao", "fonte": "pubmed",
                                                   "pmid": "7", "ref": "x"}])})
        q = {"q": [{"id": "quarentena:q", "uid": "q", "pmid": "100", "campo": "integridade",
                    "valor": "EDITORIAL_QUARANTINE", "evidencia": {"x": 1}, "confirmado_em": "2026-09-28",
                    "motivo": "m"}]}
        dados = {"studies": [c]}
        reg = R.construir(dados, col, q)
        Cf.anotar(reg, dados, col, [{"id": "integrity_hold:q", "tipo": "approve", "decidido_em": "2026-09-28",
                                     "motivo": "autoria resolvida"}])
        h = por_uid(reg, "q")["integrity_hold"]
        self.assertTrue(h["ativo"])                                  # a quarentena mantém o bloqueio
        self.assertIn("quarentena", h["motivo"])
        self.assertEqual(h["historico"][0]["liberado_por"], "integrity_hold:q")   # a EoC fica na história

    def test_sinais_de_card_em_quarentena_sao_arquivados(self):
        a1 = card("pa", nct="Coorte", pmid="950", categoria="ppgl", primario="30%")
        a2 = card("pb", nct="Coorte B", pmid="950", categoria="ppgl", primario="30%")
        col = coleta(artigos={"950": art("950", "Temozolomide in PPGL", "2014-01-01",
                                         pubtypes=["Journal Article"], resumo="30%")})
        q = {"pb": [{"id": "quarentena:pb", "uid": "pb", "pmid": "950", "campo": "integridade",
                     "valor": "EDITORIAL_QUARANTINE", "evidencia": {"x": 1}, "confirmado_em": "2026-09-28",
                     "motivo": "m"}]}
        dados = {"studies": [a1, a2]}
        reg = R.construir(dados, col, q)
        alertas = FR.sinais(reg, dados, col, None, None)
        FR.priorizar(alertas, reg, dados, col, {})
        acoes = {a["uid"]: a["prioridade"][0]["acao"] for a in alertas if a["classe"] == "inconsistencia_pmid_nct"}
        self.assertEqual(acoes["pb"], "arquivar")
        self.assertEqual(acoes["pa"], "humana")


class PrimariaDoEstudo(unittest.TestCase):

    def test_artigo_de_outro_card_nao_vira_primaria_inferida(self):
        piloto = card("piloto", nct="NCT00000004", pmid="400", categoria="neuroblastoma", fase="Fase 1/2")
        fase3 = card("fase3", nct="NCT00000005", status="Em andamento", categoria="neuroblastoma")
        col = coleta(si={"NCT00000004": ["400"], "NCT00000005": ["400"]},
                     artigos={"400": art("400", "Pilot of MIBG in neuroblastoma", "2021-05-24",
                                         pubtypes=["Journal Article"],
                                         registros=["NCT00000004", "NCT00000005"])},
                     ctgov={"NCT00000004": ctg("NCT00000004"), "NCT00000005": ctg("NCT00000005", "RECRUITING")})
        reg = registro([piloto, fase3], col)
        self.assertEqual(por_uid(reg, "piloto")["primary_publication"], "400")
        self.assertIsNone(por_uid(reg, "fase3")["primary_publication"])

    def test_primaria_decidida_por_humano(self):
        col = vision(pmids=("90", "100", "200"), extra={
            "90": art("90", "Drug X pan-tumor", "2020-01-01"),
            "200": art("200", "Drug X in prostate cancer: long-term results", "2025-01-01",
                       resumo=RESUMO_PRIMARIO)})
        dec = {"v": [{"id": "publicacao_primaria:v", "uid": "v", "pmid": "200", "campo": "publicacao_primaria",
                      "valor": "100", "confirmado_em": "2026-09-28", "motivo": "m"}]}
        r = por_uid(registro([card("v", pmid="200")], col, dec), "v")
        rel = {p["pmid"]: (p["relacao"], p["relacao_origem"]) for p in r["publicacoes"]}
        self.assertEqual(r["primary_publication"], "100")
        self.assertEqual(rel["100"], ("primary_publication", "human_confirmed"))
        self.assertEqual(rel["90"][0], "unknown")


class ConflitoNaFonte(unittest.TestCase):
    """WITHIN_SOURCE_CONFLICT — regra genérica, com valores sintéticos."""

    def oc(self, valor, **kw):
        base = {"secao": "x", "trecho": "y", "valor": valor, "populacao": "braço A", "denominador": 100,
                "endpoint": "mediana de OS", "timepoint": "análise final", "metodo": "Kaplan-Meier"}
        return dict(base, **kw)

    def test_mesmo_valor_e_consistente(self):
        r = Cf.avaliar_conflito_na_fonte([self.oc(12.1), self.oc(12.1)])
        self.assertEqual((r["classe"], r["bloqueia_campo"]), ("CONSISTENTE", False))

    def test_mesmo_contexto_valores_incompativeis_bloqueia(self):
        r = Cf.avaliar_conflito_na_fonte([self.oc(12.1), self.oc(12.4)])
        self.assertEqual((r["classe"], r["bloqueia_campo"]), ("WITHIN_SOURCE_CONFLICT", True))

    def test_contexto_diferente_explica(self):
        for dim, a, b in (("populacao", "braço A", "ITT"), ("denominador", 100, 96),
                          ("endpoint", "sintomática", "sintomática + assintomática"),
                          ("timepoint", "interina", "final"), ("metodo", "Kaplan-Meier", "bruto")):
            with self.subTest(dim):
                r = Cf.avaliar_conflito_na_fonte([self.oc(10, **{dim: a}), self.oc(12, **{dim: b})])
                self.assertEqual((r["classe"], r["diferencas"], r["bloqueia_campo"]), ("EXPLICADA", [dim], False))

    def test_arredondamento_explica_so_quando_cabe(self):
        self.assertEqual(Cf.avaliar_conflito_na_fonte([self.oc(6), self.oc(5.9)])["classe"], "EXPLICADA")
        self.assertEqual(Cf.avaliar_conflito_na_fonte([self.oc(6), self.oc(6.6)])["classe"],
                         "WITHIN_SOURCE_CONFLICT")

    def test_contexto_nao_documentado_nao_explica(self):
        r = Cf.avaliar_conflito_na_fonte([self.oc(10, timepoint=""), self.oc(12)])
        self.assertEqual((r["classe"], r["bloqueia_campo"]), ("WITHIN_SOURCE_CONFLICT", True))

    def test_bloqueia_so_o_campo_e_nunca_autoriza(self):
        reg = R.construir({"studies": [card("v", pmid="100")]}, vision(), {}, [])
        achados = [{"id": "c1", "uid": "v", "pmid": "100", "campos": ["primario"], "medida": "m",
                    "ocorrencias": [self.oc(12.1), self.oc(12.4)]},
                   {"id": "c2", "uid": "v", "pmid": "100", "campos": ["tox_g3"], "medida": "t",
                    "ocorrencias": [self.oc(6, endpoint="a"), self.oc(7, endpoint="b")]},
                   {"id": "c3", "uid": "v", "pmid": "999", "campos": ["basal"], "medida": "outra publicação",
                    "ocorrencias": [self.oc(1), self.oc(2)]}]
        Cf.aplicar_conflitos_na_fonte(reg, achados)
        r = por_uid(reg, "v")
        self.assertEqual(r["automation"]["clinical_extraction"]["campos_bloqueados"], ["primario"])
        self.assertFalse(r["automation"]["clinical_extraction"]["autorizado"])
        self.assertEqual([(c["id"], c["classe"]) for c in r["conflitos_na_fonte"]],
                         [("c1", "WITHIN_SOURCE_CONFLICT"), ("c2", "EXPLICADA")])     # c3: outro PMID


class Neutralizacao(unittest.TestCase):

    def test_so_neutraliza_o_card_auditado_e_preserva_identidade(self):
        with self.assertRaises(ValueError):
            AP.neutralizar_ppgl8(card("ppgl_8", pmid="1"))              # hash diferente: recusa
        self.assertTrue(set(AP.PRESERVAR).isdisjoint(AP.NEUTRALIZAR))    # uid/categoria nunca mudam
        self.assertNotIn("uid", AP.NEUTRALIZAR)
        self.assertEqual(AP.NEUTRALIZAR["pubmed_url"], "")               # não atribui a outro artigo


class Travas(unittest.TestCase):
    """Garantias sobre o próprio código, não sobre dados."""

    # Módulos de detecção e priorização. As migrações (db_migracao_*) aplicam
    # decisões humanas sobre estudos nomeados, como as br_migracao_*: por
    # definição citam uids, e ficam fora desta trava.
    SCRIPTS_DB = sorted(p for p in SCRIPTS.glob("db_*.py") if not p.name.startswith("db_migracao_"))

    def strings_de_codigo(self, caminho):
        """Strings do código, fora docstrings e fora de FONTES_PROIBIDAS."""
        arvore = ast.parse(caminho.read_text(encoding="utf-8"))
        excluir = set()
        for no in ast.walk(arvore):
            if isinstance(no, (ast.Module, ast.FunctionDef, ast.ClassDef)) and ast.get_docstring(no):
                excluir.add(id(no.body[0].value))
            if isinstance(no, ast.Assign) and any(getattr(t, "id", "") == "FONTES_PROIBIDAS"
                                                  for t in no.targets):
                excluir |= {id(n) for n in ast.walk(no.value)}
        return [n.value for n in ast.walk(arvore) if isinstance(n, ast.Constant)
                and isinstance(n.value, str) and id(n) not in excluir]

    def test_tracker_e_explorer_proibidos(self):
        self.assertTrue(self.SCRIPTS_DB)
        for arq in self.SCRIPTS_DB:
            for s in self.strings_de_codigo(arq):
                self.assertNotRegex(s.lower(), r"tracker|explorer", f"{arq.name}: {s!r}")
        for f in F.FONTES_PROIBIDAS:
            with self.assertRaises(PermissionError):
                F.garantir_fonte_permitida(SCRIPTS.parent / f)
            with self.assertRaises(PermissionError):
                R.carregar_dados(SCRIPTS.parent / f)

    def test_nenhuma_regra_especifica_de_estudo(self):
        """Os casos reais de validação (EMERALD-3, AtTEnd, NuTide:121, ANBL1531,
        ppgl_8) têm de ser achados por regra geral."""
        proibidos = re.compile(r"emerald|attend|nutide|anbl|neuroblastoma_\d|ppgl_\d|hepatobiliar_\d|"
                               r"endometrio_\d|42636832|39102832|39978598|34028986|24752622|"
                               r"NCT05301842|NCT03603184|NCT04163900|NCT03126916", re.I)
        for arq in self.SCRIPTS_DB:
            for s in self.strings_de_codigo(arq):
                self.assertNotRegex(s, proibidos, f"{arq.name}: {s!r}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
