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


SHA = "2749ac4ea4849523145667fdcf50d2a71cabacf6"


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

    def test_mesma_chave_com_problema_diferente_exige_discriminador(self):
        d = doc_vazio()
        I.mesclar(d, item(), "2026-09-29", "scan")
        with self.assertRaises(ValueError):
            I.mesclar(d, item(desc="óbitos relacionados omitidos no campo de segurança"), "2026-09-29", "scan")
        self.assertEqual(len(d["itens"]), 1)

    def test_problemas_legitimos_com_discriminadores_distintos(self):
        d = doc_vazio()
        i1, _ = I.mesclar(d, dict(item(), dedupe_discriminator="grade3_causality_attribution"), "2026-09-29", "s")
        c2 = dict(item(desc="óbitos relacionados omitidos no campo de segurança"),
                  dedupe_discriminator="fatal_event_omitted")
        i2, st = I.mesclar(d, c2, "2026-09-29", "scan")
        self.assertEqual(st, "novo")
        self.assertNotEqual(i1, i2)
        self.assertIn(i1, d["itens"][1]["related_ids"])
        self.assertEqual(I.validar(d), [])

    def test_remesclar_problema_existente_com_discriminador_atualiza_o_mesmo_item(self):
        d = doc_vazio()
        c = dict(item(), dedupe_discriminator="grade3_causality_attribution")
        i1, _ = I.mesclar(d, c, "2026-09-29", "scan A")
        i2, st = I.mesclar(d, dict(c, description="tox_g3 diverge da fonte: 78% vs 60%"), "2026-10-05", "scan B")
        self.assertEqual((i1, st, len(d["itens"])), (i2, "existente", 1))

    def test_id_retirado_nunca_e_reutilizado(self):
        d = doc_vazio()
        d["ids_retirados"] = ["INT-card_x-001"]
        i, _ = I.mesclar(d, item(), "2026-09-29", "scan")
        self.assertEqual(i, "INT-card_x-002")
        d["ids_retirados"].append("INT-card_x-003")
        j, _ = I.mesclar(d, dict(item(), dedupe_discriminator="fatal_event_omitted"), "2026-09-29", "scan")
        self.assertEqual(j, "INT-card_x-004")

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
        with self.assertRaises(ValueError):
            I.mudar_status(d, self.id, "resolved", "2026-10-01", "editor", resolucao={"commit": "abc1234"})
        I.mudar_status(d, self.id, "resolved", "2026-10-01", "editor",
                       resolucao={"commit": SHA, "date": "2026-10-01"})
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


class Invariantes(unittest.TestCase):
    def doc(self, status="resolved", resolucao=None):
        d = doc_vazio()
        i, _ = I.mesclar(d, item(), "2026-09-29", "scan")
        x = d["itens"][0]
        x["status"], x["last_reviewed_at"], x["resolution"] = status, "2026-09-29", resolucao
        return d

    def erros_commit(self, d):
        return [e for e in I.validar(d) if "resolution.commit" in e]

    def test_resolved_com_commit_valido_passa(self):
        self.assertEqual(I.validar(self.doc(resolucao={"commit": SHA})), [])

    def test_resolved_sem_resolution_falha(self):
        self.assertTrue(self.erros_commit(self.doc(resolucao=None)))

    def test_resolved_com_resolution_sem_commit_falha(self):
        self.assertTrue(self.erros_commit(self.doc(resolucao={"date": "2026-09-29"})))

    def test_resolved_com_commit_vazio_falha(self):
        self.assertTrue(self.erros_commit(self.doc(resolucao={"commit": ""})))

    def test_resolved_com_sha_curto_ou_invalido_falha(self):
        for c in ("2749ac4", SHA.upper(), SHA[:-1] + "g", SHA + "0", 1234):
            self.assertTrue(self.erros_commit(self.doc(resolucao={"commit": c})), c)

    def test_nao_resolvidos_nao_exigem_commit(self):
        for st in ("open", "confirmed", "deferred"):
            self.assertEqual(I.validar(self.doc(status=st)), [], st)

    def test_clone_manual_com_mesma_dedupe_key_falha(self):
        d = self.doc(status="open")
        clone = copy.deepcopy(d["itens"][0])
        clone["id"] = "INT-card_x-999"
        d["itens"].append(clone)
        self.assertTrue(any("dedupe_key duplicada" in e for e in I.validar(d)))

    def test_discriminador_contador_e_recusado(self):
        for disc in ("1", "item_2", "caso3", "dup"):
            d = self.doc(status="open")
            d["itens"][0]["dedupe_discriminator"] = disc
            d["itens"][0]["dedupe_key"] = I.dedupe_key(d["itens"][0])
            self.assertTrue(any("dedupe_discriminator" in e for e in I.validar(d)), disc)


if __name__ == "__main__":
    unittest.main()
