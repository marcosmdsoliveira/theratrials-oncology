"""Testes do backlog canônico de integridade (db_integridade.py). Offline.

    cd scripts && python3 -m unittest test_db_integridade
"""
from __future__ import annotations

import copy
import unittest

import db_integridade as I


def item(uid="card_x", desc="tox_g3 diverge da fonte (78% vs 60%)", tipo="numeric_mismatch", campos=("tox_g3",)):
    return {"uid": uid, "card": uid.upper(), "issue_type": tipo, "description": desc, "affected_fields": list(campos),
            "evidence": [{"kind": "primary_source_snippet", "snippet": "…"}], "priority": "medium",
            "detection_method": "primary_source_check"}


def doc_vazio():
    return {"schema": I.SCHEMA, "ids_retirados": [], "itens": []}


class Arquivo(unittest.TestCase):
    def test_arquivo_versionado_valido(self):
        self.assertEqual(I.validar(I.carregar()), [])

    def test_ids_unicos_e_estaveis(self):
        ids = [x["id"] for x in I.carregar()["itens"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(all(i.startswith("INT-") for i in ids))


class Mesclagem(unittest.TestCase):
    def test_redeteccao_nao_cria_outro_id(self):
        d = doc_vazio()
        i1, st1 = I.mesclar(d, item(), "2026-09-29", "scan A")
        i2, st2 = I.mesclar(d, item(desc="tox_g3 diverge da fonte: 78% vs 60%"), "2026-10-05", "scan B")
        self.assertEqual((st1, st2), ("novo", "existente"))
        self.assertEqual(i1, i2)
        self.assertEqual(len(d["itens"]), 1)
        self.assertEqual(d["itens"][0]["history"][-1]["event"], "redetected")

    def test_mesma_chave_com_problema_diferente_vira_item_relacionado(self):
        d = doc_vazio()
        i1, _ = I.mesclar(d, item(), "2026-09-29", "scan")
        i2, st = I.mesclar(d, item(desc="óbitos relacionados omitidos no campo de segurança"), "2026-09-29", "scan")
        self.assertEqual(st, "novo")
        self.assertNotEqual(i1, i2)
        self.assertIn(i1, d["itens"][1]["related_ids"])

    def test_id_retirado_nunca_e_reutilizado(self):
        d = doc_vazio()
        d["ids_retirados"] = ["INT-card_x-001"]
        i, _ = I.mesclar(d, item(), "2026-09-29", "scan")
        self.assertEqual(i, "INT-card_x-002")

    def test_redeteccao_de_item_confirmado_nao_rebaixa(self):
        d = doc_vazio()
        i, _ = I.mesclar(d, item(), "2026-09-29", "scan")
        I.mudar_status(d, i, "confirmed", "2026-09-29", "auditoria")
        I.mesclar(d, item(), "2026-10-01", "scan")
        self.assertEqual(d["itens"][0]["status"], "confirmed")


class Transicoes(unittest.TestCase):
    def base(self):
        d = doc_vazio()
        self.id, _ = I.mesclar(d, item(), "2026-09-29", "scan")
        I.mudar_status(d, self.id, "confirmed", "2026-09-29", "auditoria")
        return d

    def test_apagar_item_e_proibido(self):
        antes = self.base()
        depois = copy.deepcopy(antes)
        depois["itens"] = []
        self.assertTrue(any("apagado" in e for e in I.invariantes_de_transicao(antes, depois)))

    def test_confirmado_nao_volta_a_open_sem_decisao_humana(self):
        d = self.base()
        with self.assertRaises(ValueError):
            I.mudar_status(d, self.id, "open", "2026-10-01", "script")
        I.mudar_status(d, self.id, "open", "2026-10-01", "editor", decisao={"by": "editor", "decision": "reabrir"})
        self.assertEqual(d["itens"][0]["status"], "open")

    def test_rebaixar_por_edicao_direta_e_detectado(self):
        antes = self.base()
        depois = copy.deepcopy(antes)
        depois["itens"][0]["status"] = "open"
        self.assertTrue(any("rebaixado" in e for e in I.invariantes_de_transicao(antes, depois)))

    def test_resolvido_exige_commit_e_permanece(self):
        d = self.base()
        with self.assertRaises(ValueError):
            I.mudar_status(d, self.id, "resolved", "2026-10-01", "editor")
        I.mudar_status(d, self.id, "resolved", "2026-10-01", "editor",
                       resolucao={"commit": "abc1234", "date": "2026-10-01"})
        self.assertEqual(I.validar(d), [])
        self.assertEqual(d["itens"][0]["status"], "resolved")

    def test_history_nao_pode_ser_reescrito(self):
        antes = self.base()
        depois = copy.deepcopy(antes)
        depois["itens"][0]["history"][0]["by"] = "outro"
        self.assertTrue(any("reescrito" in e for e in I.invariantes_de_transicao(antes, depois)))

    def test_dismissed_exige_decisao_humana(self):
        d = self.base()
        d["itens"][0]["status"] = "dismissed"
        self.assertTrue(any("dismissed sem decisão" in e for e in I.validar(d)))


if __name__ == "__main__":
    unittest.main()
