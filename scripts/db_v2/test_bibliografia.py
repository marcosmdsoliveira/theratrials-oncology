"""Testes da camada bibliográfica (bibliografia.py, gerar_citacoes, checagens do validate_v2). Offline.

    cd scripts/db_v2 && python3 -m unittest test_bibliografia

Nenhuma regra por estudo: os casos são sintéticos ou usam o snapshot versionado só como fonte de metadados reais.
"""
from __future__ import annotations

import copy
import unittest

import bibliografia as B
import gerar_citacoes as G
import lift_v1 as LF
import v2lib as L
import validate_v2 as V


def snap(pmid="11111111", autores=("Autor AB", "Segundo C"), coletivo=None, pages="100-110", volume="12",
         issue="3", pubdate="2024 Mar", pubtype=("Journal Article",), title="A trial of something.", doi="10.1/x"):
    a = [{"name": n, "authtype": "Author"} for n in autores]
    if coletivo:
        a.append({"name": coletivo, "authtype": "CollectiveName"})
    return {"pmid": pmid, "authors": a, "title": title, "source": "J Test", "fulljournalname": "Journal of Testing",
            "pubdate": pubdate, "epubdate": "", "volume": volume, "issue": issue, "pages": pages, "elocationid": "",
            "doi": doi, "pmcid": None, "pubtype": list(pubtype), "retrieved_at": "2026-09-29"}


def card(uid="c1", pmid="11111111", ref="Autor AB, et al. J Test 2024;12:100-110.", ano=2024,
         sponsor="Sponsor | PI: Fulano de Tal (Hospital Central)", status="Publicado"):
    return {"uid": uid, "estudo": "ESTUDO (2024)", "acron": "ESTUDO — teste", "sponsor": sponsor, "ref": ref,
            "pubmed_url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else "", "nct": "NCT00000001",
            "nct_url": "https://clinicaltrials.gov/study/NCT00000001", "ano_pub": ano, "status": status}


class Nomes(unittest.TestCase):
    def test_sobrenome_composto_sufixo_e_iniciais(self):
        self.assertEqual(B.parse_nome("de Bono JS"), {"family": "de Bono", "given_initials": "JS"})
        self.assertEqual(B.parse_nome("Wells SA Jr"), {"family": "Wells", "given_initials": "SA", "suffix": "Jr"})
        self.assertEqual(B.parse_nome("Park JR"), {"family": "Park", "given_initials": "JR"})   # iniciais, não sufixo
        self.assertEqual(B.nome_exibicao(B.parse_nome("von Minckwitz G")), "von Minckwitz G")


class Publicacao(unittest.TestCase):
    def test_primeiro_autor_vem_do_pubmed(self):
        p = B.publicacao_de_snapshot(snap())
        self.assertEqual(p["first_author"], "Autor AB")
        self.assertEqual(B.validar_publicacao(p), [])

    def test_autor_coletivo_sem_pessoais(self):
        p = B.publicacao_de_snapshot(snap(autores=(), coletivo="ESMO Guidelines Committee"))
        self.assertEqual((p["authors"], p["first_author"]), ([], "ESMO Guidelines Committee"))
        self.assertEqual(B.validar_publicacao(p), [])

    def test_article_number_e_paginas(self):
        self.assertEqual(B.publicacao_de_snapshot(snap(pages="e005755")).get("article_number"), "e005755")
        self.assertNotIn("pages", B.publicacao_de_snapshot(snap(pages="1483953")))
        self.assertEqual(B.publicacao_de_snapshot(snap(pages="1915-42"))["pages"], "1915-42")

    def test_metadado_ausente_e_omitido_nao_null(self):
        p = B.publicacao_de_snapshot(snap(volume="", issue="", pages="", doi=None))
        for k in ("volume", "issue", "pages", "article_number", "doi", "pmcid"):
            self.assertNotIn(k, p)
        self.assertEqual(B.validar_publicacao(p), [])

    def test_tipo_guideline_e_meta_analise(self):
        self.assertEqual(B.publicacao_de_snapshot(snap(pubtype=("Journal Article", "Practice Guideline")))
                         ["publication_type"], "guideline")
        self.assertEqual(B.publicacao_de_snapshot(snap(pubtype=("Meta-Analysis", "Journal Article")))
                         ["publication_type"], "meta_analysis")

    def test_titulo_sem_ponto_final_e_sem_html(self):
        self.assertEqual(B.publicacao_de_snapshot(snap(title="<i>BRCA</i> &amp; PARP."))["title"], "BRCA & PARP")

    def test_invariantes_do_def(self):
        p = B.publicacao_de_snapshot(snap())
        self.assertTrue(B.validar_publicacao(dict(p, first_author="Outro X")))           # ≠ authors[0]
        self.assertTrue(B.validar_publicacao(dict(p, metadata_source="sponsor")))        # sponsor nunca é fonte
        self.assertTrue(B.validar_publicacao(dict(p, article_number="e1")))              # pages e article_number
        self.assertTrue(B.validar_publicacao(dict(p, role="representada")))

    def test_projecao_v1_e_inversa(self):
        p = B.publicacao_de_snapshot(snap(autores=[f"A{i} X" for i in range(9)]))
        c = B.citation_v1(p)
        self.assertEqual((len(c["authors"]), c["authors_total"]), (6, 9))
        self.assertEqual(B.citation_v1(B.publicacao_de_citation(c)), c)


class Elegibilidade(unittest.TestCase):
    S = {"11111111": snap()}

    def eleg(self, c, bloqueios=None, colecoes=frozenset(), snapshot=None, papeis=None):
        return B.elegibilidade(c, snapshot or self.S, bloqueios or {}, set(colecoes), papeis)

    def test_caso_limpo_recebe_citation_com_autor_da_publicacao(self):
        pub, motivo = self.eleg(card())
        self.assertEqual(motivo, "ok")
        self.assertEqual(pub["first_author"], "Autor AB")

    def test_pi_do_sponsor_nunca_vira_autor(self):
        for sp in ("X | PI: Fulano de Tal (Hospital Central)", "X | PI: Ana Souza / Beto Lima", "X | PI: Tal"):
            pub, _ = self.eleg(card(sponsor=sp))
            self.assertEqual(pub["first_author"], "Autor AB")
            self.assertNotIn("Tal", str(B.citation_v1(pub)))

    def test_sem_pmid_sem_publicacao_e_quarentena(self):
        self.assertEqual(self.eleg(card(pmid=None))[1], "sem_pmid")
        self.assertEqual(self.eleg(card(pmid="99999999"))[1], "pmid_fora_do_snapshot")
        self.assertEqual(self.eleg(card(status="Em revisão editorial"))[1], "quarentena_editorial")

    def test_backlog_bloqueia_sem_sobrescrever(self):
        pub, motivo = self.eleg(card(), bloqueios={"c1": ["INT-c1-001"]})
        self.assertIsNone(pub)
        self.assertEqual(motivo, "backlog:INT-c1-001")

    def test_evidence_collection_sem_principal(self):
        self.assertEqual(self.eleg(card(), colecoes={"c1"})[1], "evidence_collection")

    def test_ref_de_outro_artigo_bloqueia(self):
        pub, motivo = self.eleg(card(ref="Outro ZZ, et al. Lancet 2024;400:1-9."))
        self.assertEqual((pub, motivo), (None, "ref_diverge_do_pmid"))

    def test_ref_que_identifica_o_artigo_nao_bloqueia_mesmo_com_autor_diferente(self):
        pub, motivo = self.eleg(card(ref="Primária: Outro ZZ, et al. NEJM 2020. Atualização: J Test 2024;12:100-110."))
        self.assertEqual(motivo, "ok")

    def test_ano_nao_corroborado_bloqueia(self):
        self.assertEqual(self.eleg(card(ref="Autor AB, et al. Congresso 2019.", ano=2019))[1], "ano_nao_corroborado")

    def test_ano_da_citation_e_o_da_publicacao_representada(self):
        pub, _ = self.eleg(card(ano=2023))                  # ano_pub do card 2023 (epub), publicação 2024
        self.assertEqual(pub["year"], 2024)

    def test_follow_up_papel_vem_da_decisao_do_pmid(self):
        pub, _ = self.eleg(card(), papeis={("c1", "11111111"): "long_term"})
        self.assertEqual(pub["role"], "long_term")
        pub, _ = self.eleg(card(), papeis={("c1", "22222222"): "long_term"})   # decisão de outro PMID não vale
        self.assertEqual(pub["role"], "undetermined")

    def test_bloqueio_do_backlog_so_para_itens_bibliograficos_abertos(self):
        doc = {"itens": [
            {"id": "a", "uid": "u1", "status": "confirmed", "issue_type": "identifier_mismatch", "affected_fields": ["pubmed_url"]},
            {"id": "b", "uid": "u2", "status": "resolved", "issue_type": "identifier_mismatch", "affected_fields": ["pubmed_url"]},
            {"id": "c", "uid": "u3", "status": "open", "issue_type": "numeric_mismatch", "affected_fields": ["tox_g3"]},
            {"id": "d", "uid": "u4", "status": "open", "issue_type": "bibliographic_mismatch", "affected_fields": ["citation_author"]}]}
        self.assertEqual(B.bloqueios_do_backlog(doc), {"u1": ["a"]})


class Gerador(unittest.TestCase):
    def test_insere_apos_ref_e_so_mexe_em_citation(self):
        est, lin = G.projetar([card(), card(uid="c2", pmid=None)], {"11111111": snap()}, {}, set(), {})
        self.assertEqual(list(est[0]).index("citation"), list(est[0]).index("ref") + 1)
        self.assertNotIn("citation", est[1])
        self.assertEqual([l["motivo"] for l in lin], ["ok", "sem_pmid"])

    def test_idempotente_e_remove_citation_que_deixou_de_ser_elegivel(self):
        est, _ = G.projetar([card()], {"11111111": snap()}, {}, set(), {})
        de_novo, _ = G.projetar(est, {"11111111": snap()}, {}, set(), {})
        self.assertEqual(de_novo, est)
        bloqueado, _ = G.projetar(est, {"11111111": snap()}, {"c1": ["INT-c1-001"]}, set(), {})
        self.assertNotIn("citation", bloqueado[0])


class Validacao(unittest.TestCase):
    """Checagens do validate_v2 sobre um registro real (primeiro card elegível do data.js, citation do snapshot)."""

    @classmethod
    def setUpClass(cls):
        _, obj, _ = L.ler_data_js(L.DATA_JS.read_text(encoding="utf-8"))
        s = B.carregar_snapshot()
        for c in obj["studies"]:
            pub, motivo = B.elegibilidade(c, s, {}, set())
            if motivo == "ok":
                cls.card = G.inserir_apos(c, "ref", "citation", B.citation_v1(pub))
                break

    def erros(self, rec, cod):
        return [e for e in V.validar({rec["uid"]: rec}).itens if e["codigo"] == cod]

    def rec(self, card=None):
        return LF.lift(copy.deepcopy(card or self.card), 0, {})

    def test_registro_com_citation_valida(self):
        r = self.rec()
        self.assertEqual([e for e in V.validar({r["uid"]: r}).erros()], [])
        self.assertEqual(L.valor(r["identity"]["represented_publication"])["publication_id"],
                         self.card["citation"]["publication_id"])

    def test_citation_editada_a_mao_diverge_do_snapshot(self):
        c = copy.deepcopy(self.card)
        c["citation"]["first_author"] = c["citation"]["authors"][0]["family"] = "Inventado"
        self.assertTrue(self.erros(self.rec(c), "E_CITATION"))

    def test_represented_aponta_publication_inexistente(self):
        r = self.rec()
        r["identity"]["represented_publication"]["v"]["publication_id"] = "pmid:1"
        self.assertTrue(self.erros(r, "E_PUBLICATION_REF"))

    def test_first_author_diferente_de_authors0(self):
        r = self.rec()
        r["identity"]["publications"]["v"][0]["first_author"] = "Outro X"
        self.assertTrue(self.erros(r, "E_PUBLICATION"))

    def test_evidence_collection_nao_tem_citation(self):
        r = LF.lift(copy.deepcopy(self.card), 0, {}, colecoes=frozenset({self.card["uid"]}))
        self.assertEqual(r["record_type"], "evidence_collection")
        self.assertTrue(self.erros(r, "E_CITATION"))


class Snapshot(unittest.TestCase):
    def test_todo_registro_do_snapshot_gera_publicacao_valida(self):
        s = B.carregar_snapshot()
        self.assertTrue(s)
        for pmid, r in s.items():
            self.assertEqual(B.validar_publicacao(B.publicacao_de_snapshot(r)), [], pmid)

    def test_card_com_pmid_fora_do_snapshot_fica_sem_citation(self):
        # PMID novo ainda não baixado não trava o CI: o card cai no fallback (ref literal), nunca em autor inventado
        self.assertEqual(B.elegibilidade(card(pmid="99999999"), {}, {}, set())[1], "pmid_fora_do_snapshot")


if __name__ == "__main__":
    unittest.main()
