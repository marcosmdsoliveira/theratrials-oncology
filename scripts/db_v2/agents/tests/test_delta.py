"""Testes do delta editorial de UPDATE_CARD (componente separado do discovery). Offline, dados genéricos.

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
import sources as S  # noqa: E402

CAMPOS = {"primario": "PFS mediana 36,6 vs 13,4 m (HR 0,41; p<0,00001) — POSITIVO.",
          "secundario": "OS HR 0,57 (análise interina); benefício de OS sustentado."}
NOVA = "At the second interim analysis, overall survival favoured BVd (HR 0.58; 95% CI 0.43-0.79)."


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.antigo = DL.DIR
        DL.DIR = pathlib.Path(self.tmp.name)
        pasta = DL.DIR / "d1"
        (pasta / "fontes").mkdir(parents=True)
        fontes = []
        for sid, pars, papel in (("pmid:222:abstract", [("Title", "Trial X second interim"), ("Abstract", NOVA)], "candidate"),
                                 ("pmid:111:abstract", [("Title", "Trial X"), ("Abstract", "PFS was 36.6 months.")], "represented")):
            p = S.gravar_fonte(pasta / "fontes", sid, pars)
            fontes.append({"source_id": sid, "source_type": "pubmed_abstract", "text_level": "abstract",
                           "path": f"fontes/{p.name}", "role": papel})
        (pasta / "packet.json").write_text(json.dumps({"packet_sha256": "h", "card_fields": CAMPOS, "sources": fontes}))

    def tearDown(self):
        DL.DIR = self.antigo
        self.tmp.cleanup()

    def item(self, **kw):
        base = {"item_id": "i1", "field_path": "secundario", "decision": "DELTA", "segment_current": "OS HR 0,57 (análise interina)",
                "segment_proposed": "OS HR 0,58 (2ª análise interina)", "endpoint": "OS",
                "evidence": [{"source_id": "pmid:222:abstract", "source_type": "pubmed_abstract", "locator": "¶0002",
                              "snippet": NOVA}]}
        base.update(kw)
        return base

    def veredito(self, *itens):
        return DL.conferir("d1", {"items": list(itens)})


class Checagens(Base):
    def test_delta_cirurgico_de_campo_secundario_passa(self):
        # o card representa PFS, mas exibe OS: a publicação que atualiza OS muda SÓ o trecho de OS
        r = self.veredito(self.item())["i1"]
        self.assertEqual(r["verdict"], "PASS", r)

    def test_trecho_atual_precisa_ser_literal(self):
        r = self.veredito(self.item(segment_current="OS HR 0,57 no corte final"))["i1"]
        self.assertIn("CURRENT_NOT_FOUND", {a["code"] for a in r["achados"]})
        self.assertEqual(r["verdict"], "FAIL")

    def test_campo_inexistente_ou_nao_editavel(self):
        for campo in ("takehome", "tox_g3", "limit"):           # tox_g3 é editável, mas este card não o exibe
            r = self.veredito(self.item(field_path=campo))["i1"]
            self.assertIn("FIELD_NOT_EXISTING", {a["code"] for a in r["achados"]}, campo)

    def test_expansao_e_reescrita_do_campo_inteiro(self):
        longo = "OS HR 0,58 (IC95% 0,43-0,79), com benefício consistente em todos os subgrupos, " * 3
        r = self.veredito(self.item(segment_proposed=longo))["i1"]
        self.assertIn("EXPANSION", {a["code"] for a in r["achados"]})
        inteiro = CAMPOS["secundario"]
        CAMPOS_LONGO = inteiro + " Seguimento mediano ainda curto para conclusões definitivas sobre OS."
        pac = json.loads((DL.DIR / "d1" / "packet.json").read_text())
        pac["card_fields"]["secundario"] = CAMPOS_LONGO
        (DL.DIR / "d1" / "packet.json").write_text(json.dumps(pac))
        r = self.veredito(self.item(segment_current=CAMPOS_LONGO, segment_proposed="OS HR 0,58"))["i1"]
        self.assertIn("WHOLE_FIELD_REWRITE", {a["code"] for a in r["achados"]})

    def test_numero_sem_trecho_e_evidencia_de_outra_publicacao(self):
        r = self.veredito(self.item(segment_proposed="OS HR 0,61 (2ª análise interina)"))["i1"]
        self.assertIn("NUMBER_UNSUPPORTED", {a["code"] for a in r["achados"]})
        ev = [{"source_id": "pmid:111:abstract", "source_type": "pubmed_abstract", "locator": "¶0002",
               "snippet": "PFS was 36.6 months."}]
        r = self.veredito(self.item(segment_current="PFS mediana 36,6", field_path="primario",
                                    segment_proposed="PFS mediana 36,6 m", evidence=ev))["i1"]
        self.assertIn("EVIDENCE_NOT_FROM_NEW_PUBLICATION", {a["code"] for a in r["achados"]})

    def test_human_review_sem_texto_clinico(self):
        ok = self.veredito(self.item(decision="HUMAN_REVIEW", segment_current=None, segment_proposed=None,
                                     human_review_reason="o card não exibe a OS do corte final"))["i1"]
        self.assertEqual(ok["verdict"], "PASS")
        ruim = self.veredito(self.item(decision="HUMAN_REVIEW", human_review_reason="x"))["i1"]
        self.assertIn("HUMAN_REVIEW_WITH_TEXT", {a["code"] for a in ruim["achados"]})
        sem = self.veredito(self.item(decision="HUMAN_REVIEW", segment_current=None, segment_proposed=None))["i1"]
        self.assertIn("HUMAN_REVIEW_NO_REASON", {a["code"] for a in sem["achados"]})

    def test_trechos_sobrepostos_no_mesmo_campo(self):
        r = self.veredito(self.item(), self.item(item_id="i2", segment_current="HR 0,57",
                                                 segment_proposed="HR 0,58"))
        self.assertIn("OVERLAP", {a["code"] for a in r["i2"]["achados"]})


class Isolamento(unittest.TestCase):
    def test_versao_propria_e_discovery_intacto(self):
        self.assertTrue(DL.versao().startswith("delta/1+"))
        self.assertFalse(any("delta" in f for f in DS.ARQUIVOS_PIPELINE))       # mudar o delta não muda o discovery
        self.assertNotIn("takehome", DL.CAMPOS_EDITAVEIS)
        self.assertNotIn("limit", DL.CAMPOS_EDITAVEIS)

    def test_schemas_versionados_em_sincronia(self):
        for nome, s in DL.SCHEMAS.items():
            self.assertEqual(json.loads((AG / "schemas" / nome).read_text()), s, nome)

    def test_delta_nao_escreve_no_database(self):
        codigo = (AG / "delta.py").read_text(encoding="utf-8")
        self.assertNotIn("DATA_JS", codigo)
        self.assertNotIn("secondary-cards.js", codigo)


class Lote(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.orig = (DL.DIR, DS.cards, DL.versao)
        DL.DIR = pathlib.Path(self.tmp.name)
        self.card = {"uid": "u1", "secundario": "OS HR 0,57"}
        DS.cards = lambda: {"u1": self.card}
        self.chamadas = []
        etapa = lambda n: (lambda x: self.chamadas.append(n) or {})  # noqa: E731
        self.etapas = {"preparar": etapa("preparar"), "curator": etapa("curator"), "verifier": etapa("verifier")}
        self.linha = {"uid": "u1", "pmid": "222", "relation": "LONG_TERM_FOLLOWUP", "action": "UPDATE_CARD",
                      "final_verdict": "PASS"}

    def tearDown(self):
        DL.DIR, DS.cards, DL.versao = self.orig
        self.tmp.cleanup()

    def test_resume_e_invalidacao(self):
        DL.executar_lote([self.linha], etapas=self.etapas)
        self.assertEqual(DL.executar_lote([self.linha], etapas=self.etapas)[0]["etapas_executadas"], [])
        self.card["secundario"] = "OS HR 0,58"                                 # card mudou: refaz
        self.assertEqual(DL.executar_lote([self.linha], etapas=self.etapas)[0]["estado_inicial"], "invalidado")
        DL.versao = lambda: "delta/999"                                        # versão mudou: refaz
        self.assertEqual(DL.executar_lote([self.linha], etapas=self.etapas)[0]["estado_inicial"], "invalidado")


if __name__ == "__main__":
    unittest.main()
