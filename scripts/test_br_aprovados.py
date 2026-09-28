#!/usr/bin/env python3
"""
test_br_aprovados.py — o override humano (br_aprovados.json) é estreito.

Offline: a busca do ClinicalTrials.gov é substituída pelo registro real do
AcTFirst (NCT06855277), gravado em fixtures/ em 2026-09-28. O registro declara
primaryPurpose DIAGNOSTIC para um fase III terapêutico.

Uso:
    python3 scripts/test_br_aprovados.py
"""
from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

import br_ciclo  # noqa: E402
import br_ctgov as ct  # noqa: E402
import br_merge  # noqa: E402
import br_qa  # noqa: E402

NCT = "NCT06855277"
REGISTRO = json.loads((SCRIPTS / "fixtures" / f"ctgov_{NCT}.json").read_text(encoding="utf-8"))

OVERRIDE_OK = {
    "nct": NCT, "tipo": "primary_purpose", "valor_registro": "DIAGNOSTIC",
    "decisao": "TREATMENT", "motivo": "fase III terapêutico; DIAGNOSTIC é erro de preenchimento",
    "aprovado_em": "2026-09-28",
}


def estudo(status_br: str | None = None) -> dict:
    """O registro do AcTFirst; `status_br` troca o status dos centros brasileiros."""
    s = copy.deepcopy(REGISTRO)
    if status_br:
        for loc in s["protocolSection"]["contactsLocationsModule"]["locations"]:
            if loc.get("country") == "Brazil":
                loc["status"] = status_br
    return s


def descobrir(aprovados: list[dict] | None, estudos: list[dict] | None = None) -> dict:
    """Roda a triagem real do br_ciclo com um br_aprovados.json temporário."""
    with tempfile.TemporaryDirectory() as tmp:
        arq = Path(tmp) / "br_aprovados.json"
        if aprovados is not None:
            arq.write_text(json.dumps({"aprovados": aprovados}), encoding="utf-8")
        with mock.patch.object(br_ciclo, "APROVADOS", arq), \
             mock.patch("br_discover.buscar", return_value=estudos or [estudo()]):
            return br_ciclo.descobrir(publicados=set())


def faixa(desc: dict, nct: str = NCT) -> str | None:
    for k, v in desc["faixas"].items():
        if any(x["nct"] == nct for x in v):
            return k
    return None


class OverridePropósito(unittest.TestCase):

    def test_1_sem_arquivo_continua_em_revisao(self):
        d = descobrir(None)
        self.assertEqual(faixa(d), "revisar")
        item = next(x for x in d["faixas"]["revisar"] if x["nct"] == NCT)
        self.assertTrue(item["motivo"].startswith("propósito declarado: DIAGNOSTIC"))
        self.assertEqual(d["overrides"]["aplicados"], [])

    def test_2_override_correto_vai_para_recomendacao(self):
        d = descobrir([OVERRIDE_OK])
        self.assertEqual(faixa(d), "recomendado")
        self.assertEqual([x["nct"] for x in d["overrides"]["aplicados"]], [NCT])
        # a decisão chega ao curador pelo _br_discovery.json
        e = next(x for x in d["_achatados"] if x["nct"] == NCT)
        self.assertEqual(e["override_proposito"]["valor_registro"], "DIAGNOSTIC")
        self.assertEqual(e["brazil_status"], ct.BR_RECRUITING)

    def test_3_override_de_outro_nct_nao_vale(self):
        d = descobrir([dict(OVERRIDE_OK, nct="NCT00000001")])
        self.assertEqual(faixa(d), "revisar")
        self.assertEqual(d["overrides"]["aplicados"], [])
        self.assertEqual([x["nct"] for x in d["overrides"]["nao_aplicados"]], ["NCT00000001"])

    def test_4_override_de_outro_tipo_nao_vale(self):
        for tipo in ("brazil_status", "escopo", "qa", "*"):
            with self.subTest(tipo=tipo):
                d = descobrir([dict(OVERRIDE_OK, tipo=tipo)])
                self.assertEqual(faixa(d), "revisar")
                self.assertEqual(d["overrides"]["aplicados"], [])
                self.assertTrue(any("não é aceito" in a for a in d["overrides"]["avisos"]))

    def test_4b_entrada_incompleta_ou_divergente_nao_vale(self):
        casos = {
            "valor do registro diferente": dict(OVERRIDE_OK, valor_registro="SCREENING"),
            "decisão diferente de TREATMENT": dict(OVERRIDE_OK, decisao="SUPPORTIVE_CARE"),
            "sem motivo": dict(OVERRIDE_OK, motivo=""),
            "sem data": {k: v for k, v in OVERRIDE_OK.items() if k != "aprovado_em"},
            "data malformada": dict(OVERRIDE_OK, aprovado_em="28/09/2026"),
        }
        for nome, ov in casos.items():
            with self.subTest(nome):
                d = descobrir([ov])
                self.assertEqual(faixa(d), "revisar")
                self.assertEqual(d["overrides"]["aplicados"], [])

    def test_5a_nao_contorna_status_no_brasil(self):
        # centros brasileiros ainda não abertos: fica aguardando, override não aplica
        d = descobrir([OVERRIDE_OK], [estudo("NOT_YET_RECRUITING")])
        self.assertEqual(faixa(d), "aguardando_brasil")
        self.assertEqual(d["overrides"]["aplicados"], [])
        self.assertIn("ainda não abriu", d["overrides"]["nao_aplicados"][0]["motivo"])
        # centros brasileiros encerrados: sai da triagem, override não aplica
        d = descobrir([OVERRIDE_OK], [estudo("COMPLETED")])
        self.assertIsNone(faixa(d))
        self.assertEqual(d["overrides"]["aplicados"], [])

    def test_5b_nao_contorna_merge_nem_qa(self):
        # merge: card novo só com RECRUITING, override ou não
        with self.assertRaises(ValueError):
            br_merge.exigir_brazil_status({"nct": NCT, "brazil_status": "NOT_YET_RECRUITING"})
        # QA não conhece o arquivo de overrides...
        self.assertNotIn("br_aprovados", (SCRIPTS / "br_qa.py").read_text(encoding="utf-8"))
        # ...e barra um card do AcTFirst malformado como barraria qualquer outro
        atual, meta = ct.carregar_trials()
        ruim = dict(atual[0], id="actfirst", nct=NCT, modalidade=["radioligante"],
                    alvos=[], biomarcadores=["HER2-"])
        for campo in ("biomarcadores_criterios", "alvos_justificativa"):
            ruim.pop(campo, None)
        res = br_qa.comparar(atual, meta, atual + [ruim], meta)
        self.assertTrue(any("radioligante" in f for f in res["falhas"]), res["falhas"])
        self.assertTrue(any("negatividade" in f for f in res["falhas"]), res["falhas"])

    def test_6_relatorio_registra_a_excecao(self):
        d = descobrir([OVERRIDE_OK, dict(OVERRIDE_OK, nct="NCT00000001"),
                       dict(OVERRIDE_OK, nct="NCT00000002", tipo="brazil_status")])
        md = "\n".join(br_ciclo.secao_overrides(d))
        self.assertIn("Overrides humanos aplicados (1)", md)
        self.assertIn(NCT, md)
        self.assertIn("DIAGNOSTIC → TREATMENT", md)
        self.assertIn("2026-09-28", md)
        self.assertIn("NCT00000001", md)                 # registrado, sem efeito
        self.assertIn("não é aceito", md)                # entrada recusada
        item = next(x for x in d["faixas"]["recomendado"] if x["nct"] == NCT)
        self.assertIn("override humano", item["motivo"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
