"""Fixtures SINTÉTICAS do Database v2 (nenhum estudo real). Gera scripts/db_v2/fixtures/*.json.

    python3 scripts/db_v2/fixtures_v2.py

Cada fixture é um registro 'curated' completo e válido para um cenário de modelagem.
Os testes (test_db_v2.py) carregam os JSON gerados e aplicam mutações para os casos negativos.
"""
from __future__ import annotations

import copy
import json
import pathlib
import zlib

import v2lib as L

PASTA = pathlib.Path(__file__).resolve().parent / "fixtures"


def P(v, origin="reported", prov="p1", **kw):
    return {"state": "present", "origin": origin, "v": v, "prov": prov, **kw}


def ED(v):
    return {"state": "present", "origin": "editorial", "v": v}


def Q(x, op="="):
    return {"op": op, "value": x}


def tox(term, arm, pct, modulo=None, scope="any"):
    t = {"term": term, "scope": scope, "arm_id": arm, "value": Q(pct)}
    if modulo:
        t["aesi_of"] = [modulo]
    return t


def endpoint(eid, code, level="primary", comp="c1", arms=(("exp", 10.0), ("ctl", 6.0)), summary="median",
             ptype=None, **extra):
    h = {"level": level}
    if ptype:
        h["primary_type"] = ptype
    ep = {"endpoint_id": eid, "code": code, "hierarchy": h, "comparison_id": comp,
          "population": {"label": "ITT"}, "measure": {"summary": summary},
          "timepoint": {"type": "median" if summary == "median" else "landmark", **({"months": 12} if summary != "median" else {})},
          "assessment": "BICR", "analysis_set": {"name": "ITT"},
          "arms_values": [{"arm_id": a, "value": Q(v)} for a, v in arms],
          "effect": {"measure": "HR", "value": Q(0.7), "ci": {"level": 95, "low": 0.55, "high": 0.88}, "p": "0.002",
                     "sided": 2, "significance": "met"},
          "maturity": {"analysis_ref": "a1"},
          "state": "present", "origin": "reported", "prov": "p1"}
    for k, v in extra.items():
        if k == "hierarchy":
            ep["hierarchy"].update(v)
        else:
            ep[k] = v
    return ep


def assinatura(aid="a1", comp="c1", endpoint_code="PFS", summary="median"):
    return {"analysis_id": aid, "analysis_type": "primary", "data_cutoff": "2025-01-01",
            "publication_role": "primary_publication", "prov": "p1",
            "signature": {"trial_key": "NCT00000000", "cohort": None, "population": "ITT", "comparison": comp,
                          "endpoint": endpoint_code, "summary_measure": summary, "timepoint": "median",
                          "assessment_method": "BICR", "analysis_set": "ITT"}}


def base(uid, modules=(), arms=None, comps=None, record_type="trial"):
    arms = arms or [
        {"arm_id": "exp", "label": "Experimental", "role": "experimental", "n": Q(200),
         "interventions": [{"agent": "AGENTE-X", "role": "investigational"}]},
        {"arm_id": "ctl", "label": "Controle", "role": "control", "n": Q(200),
         "interventions": [{"agent": "PADRAO-Y", "role": "control"}]},
    ]
    comps = comps or [{"comparison_id": "c1", "exp_arms": ["exp"], "ctl_arms": ["ctl"], "hypothesis": "superiority"}]
    return {
        "schema": L.SCHEMA_ID, "uid": uid, "record_type": record_type,
        "curation": {"level": "curated"},
        "relationships": {"parent_uid": None, "child_uids": [], "links": []},
        "modules": list(modules),
        "identity": {
            "short_name": ED(uid.upper()), "display_title": ED(f"{uid} — título sintético"),
            "category_id": ED("sintetica"), "evidence_stage": P("published_primary"),
            "registrations": P([{"registry": "NCT", "id": "NCT00000000"}], prov="p2"),
            "phase": P("3", prov="p2"),
            "represented_publication": P({"pmid": "00000001", "year": 2025}),
            "tumors": P(["tumor_sintetico"]),
        },
        "population": {
            "disease": P("doença sintética avançada"), "setting": P("advanced_first_line"),
            "biomarker_selection": P([{"id": "b0", "biomarker": "nenhum", "family": "other", "rule": "none"}]),
            "prior_therapy": P([{"requirement": "excluded", "therapy": "terapia sistêmica prévia"}]),
        },
        "design": {
            "structure": P("single_cohort"), "allocation": P("randomized", prov="p2"),
            "masking": P("open", prov="p2"), "control": P({"type": "active"}),
            "arms": P(arms), "comparisons": P(comps), "sample_size": P({"randomized": sum(a["n"]["value"] for a in arms)}),
        },
        "endpoints": P([endpoint("e1", "PFS")]),
        "safety": {
            "grade3plus_any": P([{"arm_id": a["arm_id"], "value": Q(40)} for a in arms]),
            "discontinuation_ae": P([{"arm_id": a["arm_id"], "value": Q(8)} for a in arms]),
            "treatment_related_deaths": P([{"arm_id": a["arm_id"], "n": 1} for a in arms]),
            "key_toxicities": P([tox("fadiga", arms[0]["arm_id"], 30)]),
        },
        "interpretation": {"key_result": ED("PFS mediana 10,0 vs 6,0 m"), "takehome": ED("mensagem sintética"),
                           "limitations": ED(["estudo aberto"])},
        "analyses": [assinatura()],
        "review": {"editorial_status": "active", "integrity": {"status": "none"}},
        "provenance": {
            "p1": {"source": {"type": "publication", "pmid": "00000001"}, "locator": {"section": "Results"},
                   "extraction": "explicit", "evidence_confidence": "high"},
            "p2": {"source": {"type": "registry", "nct": "NCT00000000"}, "extraction": "explicit",
                   "evidence_confidence": "high"},
        },
        "legacy": {"v1": {"uid": uid}, "position": 0},
    }


def mod(nome, role="tested", arm_ids=("exp",), **campos):
    return {"module": nome, "role": role, "arm_ids": list(arm_ids) if arm_ids != "all" else "all",
            "fields": {k: P(v) for k, v in campos.items()},
            "classification": {"basis": "curated"}}


def set_tox(r, *toxs):
    r["safety"]["key_toxicities"] = P(list(toxs))


# ── cenários ────────────────────────────────────────────────────────────────
def radionuclide():
    r = base("syn-radionuclide", [mod("radionuclide_therapy", delivery="systemic_ligand", target="PSMA",
                                      radionuclide={"isotope": "177Lu", "emission": "beta"},
                                      activity_per_administration={"value": 7.4, "unit": "GBq", "basis": "fixed"},
                                      cycles={"planned_min": 4, "planned_max": 6, "condition": "resposta"},
                                      imaging_selection={"tracers": ["PSMA-PET"], "criteria": "SUV > fígado"})])
    set_tox(r, tox("hematologic", "exp", 12, "radionuclide_therapy", "g3plus"),
            tox("renal", "exp", 2, "radionuclide_therapy"), tox("xerostomia_salivary", "exp", 35, "radionuclide_therapy"))
    return r


def adc():
    r = base("syn-adc", [mod("adc", target="HER2", payload_class="topo1_inhibitor",
                             target_expression=[{"biomarker_ref": "b1", "scoring": "IHC", "cutoff": "1+ ou 2+/ISH-"}],
                             prior_same_target={"requirement": "allowed"}),
                         mod("chemotherapy", role="control", arm_ids=("ctl",), regimen_label="escolha do investigador")])
    r["population"]["biomarker_selection"] = P([{"id": "b1", "biomarker": "HER2-low", "family": "HER2", "rule": "required"}])
    set_tox(r, tox("ild_pneumonitis", "exp", 10, "adc"), tox("lvef_decline", "exp", 2, "adc"))
    return r


def immunotherapy(pdl1=True):
    campos = {"target": "PD-1", "prior_io": {"requirement": "excluded"}}
    if pdl1:
        campos["pdl1"] = {"assay": "22C3", "score": "CPS", "cutoff": "≥1", "role": "stratification"}
    r = base("syn-io" if pdl1 else "syn-io-sem-pdl1", [mod("immunotherapy", **campos)])
    if pdl1:
        r["design"]["stratification"] = P([{"factor": "PD-L1 CPS ≥1", "family": "PD-L1"}])
    set_tox(r, tox("immune_related_g3plus", "exp", 12, "immunotherapy", "g3plus"))
    return r


def targeted():
    r = base("syn-alvo", [mod("targeted_therapy", target="KRAS G12C", agent_class="small_molecule_other",
                              required_alteration="b1", detection={"method": "NGS", "sample": "tissue"},
                              prior_targeted_therapy={"requirement": "excluded"})])
    r["population"]["biomarker_selection"] = P([{"id": "b1", "biomarker": "KRAS G12C", "family": "KRAS", "rule": "required"}])
    return r


def ddr():
    r = base("syn-ddr", [mod("targeted_therapy", target="PARP", agent_class="parpi", required_alteration="b1",
                             detection={"method": "NGS", "sample": "tissue"},
                             prior_targeted_therapy={"requirement": "excluded"}),
                         mod("ddr_hrd", genes=["BRCA1", "BRCA2"],
                             origin={"tested_in": "tissue", "distinguishes_origin": False, "allowed": "either"},
                             stratified_results=["e2"])])
    r["population"]["biomarker_selection"] = P([{"id": "b1", "biomarker": "BRCA1/2", "family": "BRCA", "rule": "required"}])
    r["endpoints"] = P([endpoint("e1", "PFS"),
                        endpoint("e2", "PFS", level="exploratory", population={"label": "BRCAm", "biomarker_ref": "b1"})])
    set_tox(r, tox("mds_aml", "exp", 1, "targeted_therapy"), tox("anemia", "exp", 20, "targeted_therapy", "g3plus"))
    return r


def tce_vs_chemo():
    r = base("syn-tce", [mod("t_cell_engager", targets={"tumor_target": "DLL3", "effector": "CD3"}),
                         mod("chemotherapy", role="control", arm_ids=("ctl",), regimen_label="QT padrão")])
    set_tox(r, tox("crs", "exp", 50, "t_cell_engager"), tox("icans", "exp", 5, "t_cell_engager"),
            tox("infections", "exp", 20, "t_cell_engager"))
    return r


def car_t():
    arms = [{"arm_id": "exp", "label": "CAR-T", "role": "experimental", "n": Q(100),
             "interventions": [{"agent": "CAR-T sintético", "role": "investigational", "module": "cellular",
                                "phase": "single_administration"},
                               {"agent": "ponte", "role": "supportive", "phase": "bridging"}],
             "proceeded_to_planned_therapy": [{"step": "infusion", "pct": 90}]},
            {"arm_id": "ctl", "label": "Padrão", "role": "control", "n": Q(100),
             "interventions": [{"agent": "QT + ASCT", "role": "control", "module": "chemotherapy"}],
             "proceeded_to_planned_therapy": [{"step": "asct", "pct": 45}]}]
    r = base("syn-cart", [mod("cellular", product_type="car_t", target="CD19"),
                          mod("chemotherapy", role="control", arm_ids=("ctl",),
                              high_dose={"conditioning_regimen": "BEAM", "stem_cell_rescue": "autologous"},
                              agent_class="high_dose_with_autologous_rescue")], arms=arms)
    set_tox(r, tox("crs", "exp", 40, "cellular"), tox("icans", "exp", 10, "cellular"),
            tox("prolonged_cytopenias", "exp", 30, "cellular"), tox("sos_vod", "ctl", 1, "chemotherapy"))
    return r


def radiotherapy():
    r = base("syn-rt", [mod("radiotherapy", role="tested", arm_ids=("exp",), technique="SBRT",
                            components=[{"arm_id": "exp", "technique": "SBRT", "target": "todas as lesões",
                                         "site": "thorax", "total_gy": {"op": "range", "low": 25, "high": 40},
                                         "fractions": 5}])])
    set_tox(r, tox("pneumonitis", "exp", 6, "radiotherapy", "g3plus"))
    return r


def perioperatorio():
    arms = [{"arm_id": "exp", "label": "QT perioperatória + cirurgia", "role": "experimental", "n": Q(200),
             "interventions": [{"agent": "QT", "role": "investigational", "phase": "neoadjuvant", "module": "chemotherapy"},
                               {"agent": "cirurgia", "role": "backbone", "module": "surgery"}],
             "proceeded_to_planned_therapy": [{"step": "surgery", "pct": 85}]},
            {"arm_id": "ctl", "label": "QRT pré-operatória + cirurgia", "role": "control", "n": Q(200),
             "interventions": [{"agent": "QRT", "role": "control", "phase": "neoadjuvant", "module": "radiotherapy"},
                               {"agent": "cirurgia", "role": "backbone", "module": "surgery"}],
             "proceeded_to_planned_therapy": [{"step": "surgery", "pct": 80}]}]
    r = base("syn-periop", [mod("chemotherapy", role="tested", arm_ids=("exp",), regimen_label="QT perioperatória"),
                            mod("radiotherapy", role="control", arm_ids=("ctl",), technique="3DCRT",
                                components=[{"arm_id": "ctl", "technique": "3DCRT", "target": "tumor primário",
                                             "site": "thorax", "total_gy": {"op": "=", "value": 41.4},
                                             "fractions": 23}]),
                            mod("surgery", role="backbone", arm_ids="all", procedure="esofagectomia"),
                            mod("locoregional", role="backbone", arm_ids="all", procedure="other")], arms=arms)
    r["endpoints"] = P([endpoint("e1", "OS"),
                        endpoint("e2", "pCR", level="secondary", summary="proportion",
                                 definition="ypT0 ypN0", timepoint={"type": "at_event"})])
    return r


def diagnostico():
    r = base("syn-diag", [mod("diagnostic", role="tested", arm_ids="all", index_test="PET sintético",
                              reference_standard="histologia", unit_of_analysis=["patient", "lesion"])],
             record_type="diagnostic_study",
             arms=[{"arm_id": "all_pts", "label": "Todos", "role": "single", "n": Q(120)}],
             comps=[{"comparison_id": "c0", "exp_arms": ["all_pts"], "hypothesis": "descriptive"}])
    for k in ("allocation", "masking", "control", "comparisons"):
        r["design"].pop(k)
    r["design"]["arms"] = {"state": "not_applicable"}
    r["safety"] = {}
    r["endpoints"] = P([{"endpoint_id": "e1", "code": "SENS", "hierarchy": {"level": "primary"}, "comparison_id": None,
                         "population": {"label": "pacientes avaliáveis"}, "measure": {"summary": "accuracy"},
                         "timepoint": {"type": "at_event"}, "unit_of_analysis": "patient",
                         "estimate": {"value": Q(78), "ci": {"level": 95, "low": 70, "high": 85}, "n": 120},
                         "state": "present", "origin": "reported", "prov": "p1"}])
    r["analyses"][0]["signature"].update({"comparison": "none", "endpoint": "SENS", "summary_measure": "accuracy"})
    r["interpretation"].pop("key_result")
    return r


def basket():
    arms = [{"arm_id": "coorte_x", "label": "Coorte X", "role": "single", "n": Q(40),
             "interventions": [{"agent": "AGENTE-X", "role": "investigational"}]}]
    r = base("syn-basket-coorte", [mod("immunotherapy", arm_ids=("coorte_x",), target="PD-1",
                                       msi_mmr={"status": "MSI-H/dMMR"}, prior_io={"requirement": "excluded"})],
             record_type="trial_cohort", arms=arms,
             comps=[{"comparison_id": "c0", "exp_arms": ["coorte_x"], "hypothesis": "descriptive"}])
    r["design"]["allocation"] = P("single_arm", prov="p2")
    for k in ("masking", "control"):
        r["design"].pop(k)
    r["design"]["structure"] = P("multi_cohort_basket")
    r["design"]["cohorts"] = P([{"cohort_id": "X", "kind": "analysis_population", "label": "tumor X MSI-H",
                                 "source_cohorts": ["D", "K"], "biomarker_ref": "b1"}])
    r["population"]["biomarker_selection"] = P([{"id": "b1", "biomarker": "MSI-H/dMMR", "family": "MSI/MMR",
                                                 "rule": "required"}])
    r["safety"]["population"] = P("pooled")
    r["endpoints"] = P([{"endpoint_id": "e1", "code": "ORR", "hierarchy": {"level": "primary", "scope": {"cohort_id": "X"}},
                         "comparison_id": None, "population": {"label": "coorte X", "cohort_id": "X"},
                         "measure": {"summary": "proportion"}, "timepoint": {"type": "best"},
                         "response_criteria": "RECIST1.1", "assessment": "BICR", "analysis_set": {"name": "efficacy_evaluable", "n": 40},
                         "estimate": {"value": Q(48)}, "state": "present", "origin": "reported", "prov": "p1"}])
    r["safety"]["grade3plus_any"] = P([{"arm_id": "coorte_x", "value": Q(15)}])
    r["safety"]["discontinuation_ae"] = P([{"arm_id": "coorte_x", "value": Q(5)}])
    r["safety"]["treatment_related_deaths"] = P([{"arm_id": "coorte_x", "n": 0}])
    set_tox(r, tox("immune_related_g3plus", "coorte_x", 10, "immunotherapy", "g3plus"))
    r["analyses"][0]["signature"].update({"cohort": "X", "comparison": "none", "endpoint": "ORR",
                                          "summary_measure": "proportion"})
    r["relationships"]["parent_uid"] = None
    # o estudo-mãe e a outra coorte não têm card: relação EXTERNA, sem uid inventado
    r["external_relationships"] = [
        {"registry": "clinicaltrials_gov", "registry_id": "NCT88888888", "relationship": "parent_trial",
         "url": "https://clinicaltrials.gov/study/NCT88888888", "label": "estudo basket sintético"},
        {"registry": "other", "registry_id": "SYN-REG-0001", "relationship": "related", "label": "registro local sintético"},
    ]
    return r


def co_primarios():
    r = base("syn-coprimario")
    r["endpoints"] = P([endpoint("e1", "PFS", ptype="co_primary", hierarchy={"testing": {"family_id": "F1", "order": 1}}),
                        endpoint("e2", "OS", ptype="co_primary", hierarchy={"testing": {"family_id": "F1", "order": 2}})])
    r["design"]["multiplicity"] = P({"families": [{"family_id": "F1", "overall_alpha": 0.05, "procedure": "fixed_sequence",
                                                   "members": [{"endpoint_id": "e1", "order": 1},
                                                               {"endpoint_id": "e2", "order": 2}]}]})
    return r


def dual_primarios():
    r = base("syn-dualprimario")
    r["endpoints"] = P([endpoint("e1", "PFS", ptype="dual_primary", hierarchy={"testing": {"family_id": "F1"}}),
                        endpoint("e2", "OS", ptype="dual_primary", hierarchy={"testing": {"family_id": "F1"}})])
    r["design"]["multiplicity"] = P({"families": [{"family_id": "F1", "overall_alpha": 0.05, "procedure": "alpha_split",
                                                   "members": [{"endpoint_id": "e1", "alpha": 0.01},
                                                               {"endpoint_id": "e2", "alpha": 0.04}]}]})
    return r


def tres_bracos():
    arms = [{"arm_id": "combo", "label": "Combinação", "role": "experimental", "n": Q(390),
             "interventions": [{"agent": "ANTI-CTLA4", "role": "investigational", "phase": "single_administration",
                                "module": "immunotherapy"},
                               {"agent": "ANTI-PDL1", "role": "investigational", "module": "immunotherapy"}]},
            {"arm_id": "mono", "label": "Monoterapia", "role": "experimental", "n": Q(390),
             "interventions": [{"agent": "ANTI-PDL1", "role": "investigational", "module": "immunotherapy"}]},
            {"arm_id": "ctl", "label": "TKI", "role": "control", "n": Q(390),
             "interventions": [{"agent": "TKI", "role": "control", "module": "targeted_therapy"}]}]
    comps = [{"comparison_id": "c1", "exp_arms": ["combo"], "ctl_arms": ["ctl"], "hypothesis": "superiority"},
             {"comparison_id": "c2", "exp_arms": ["mono"], "ctl_arms": ["ctl"], "hypothesis": "non_inferiority",
              "ni_margin": {"measure": "HR", "value": 1.08}}]
    r = base("syn-tres-bracos", [mod("immunotherapy", arm_ids=("combo", "mono"), target=["CTLA-4", "PD-L1"],
                                     prior_io={"requirement": "excluded"}),
                                 mod("targeted_therapy", role="control", arm_ids=("ctl",), target="VEGFR")],
             arms=arms, comps=comps)
    r["endpoints"] = P([endpoint("e1", "OS", comp="c1", arms=(("combo", 16.4), ("ctl", 13.8))),
                        endpoint("e2", "OS", level="key_secondary", comp="c2", arms=(("mono", 16.6), ("ctl", 13.8)))])
    r["safety"]["grade3plus_any"] = P([{"arm_id": a, "value": Q(v)} for a, v in (("combo", 50), ("mono", 37), ("ctl", 52))])
    set_tox(r, tox("immune_related_g3plus", "combo", 12, "immunotherapy", "g3plus"),
            tox("immune_related_g3plus", "mono", 6, "immunotherapy", "g3plus"))
    return r


def modulo_so_no_controle():
    r = base("syn-controle", [mod("adc", target="TROP2", payload_class="topo1_inhibitor",
                                  prior_same_target={"requirement": "excluded"}),
                              mod("chemotherapy", role="control", arm_ids=("ctl",), regimen_label="docetaxel")])
    set_tox(r, tox("ild_pneumonitis", "exp", 8, "adc"))
    return r


def dose_randomizada():
    arms = [{"arm_id": f"a{i}", "label": f"{atv} + {prep}", "role": "experimental", "n": Q(190),
             "factor_levels": {"atividade": atv, "preparo": prep},
             "interventions": [{"agent": "131I", "role": "investigational", "module": "radionuclide_therapy",
                                "dose": {"value": v, "unit": "GBq"}}]}
            for i, (atv, prep, v) in enumerate([("baixa", "A", 1.1), ("baixa", "B", 1.1), ("alta", "A", 3.7),
                                               ("alta", "B", 3.7)])]
    comps = [{"comparison_id": "c1", "exp_arms": ["a0", "a1"], "ctl_arms": ["a2", "a3"], "hypothesis": "non_inferiority",
              "ni_margin": {"measure": "risk_difference", "value": 10}}]
    r = base("syn-fatorial", [mod("radionuclide_therapy", arm_ids="all", delivery="metabolic", intent="ablation",
                                  radionuclide={"isotope": "131I", "emission": "beta"},
                                  activity_per_administration={"value": "por braço", "unit": "GBq"},
                                  cycles={"planned_min": 1, "planned_max": 1})], arms=arms, comps=comps)
    r["design"]["factors"] = P([{"factor": "atividade", "levels": ["baixa", "alta"]},
                                {"factor": "preparo", "levels": ["A", "B"]}])
    r["endpoints"] = P([endpoint("e1", "other", comp="c1", summary="proportion", definition="sucesso composto",
                                 arms=(("a0", 92), ("a2", 93)), timepoint={"type": "landmark", "months": 8})])
    ep = r["endpoints"]["v"][0]
    ep["arms_values"] = [{"arm_group": {"factor": "atividade", "level": "baixa"}, "value": Q(92)},
                         {"arm_group": {"factor": "atividade", "level": "alta"}, "value": Q(93)}]
    r["safety"]["grade3plus_any"] = P([{"arm_group": {"factor": "atividade", "level": "alta"}, "value": Q(3)}])
    set_tox(r, tox("hematologic", "a2", 1, "radionuclide_therapy"))
    r["safety"]["key_toxicities"]["v"].append({"term": "sialoadenite", "scope": "any",
                                               "arm_group": {"factor": "atividade", "level": "alta"}, "value": Q(12)})
    return r


def conflito():
    r = base("syn-conflito")
    ep = endpoint("e1", "PFS", summary="rate", timepoint={"type": "landmark", "months": 6},
                  measure={"summary": "rate", "analysis_role": "protocol_primary_analysis"})
    ep["effect"]["significance"] = "not_met"
    med = endpoint("e1m", "PFS", measure={"summary": "median", "analysis_role": "supportive"})
    os_ = endpoint("e2", "OS", level="secondary")
    os_["arms_values"][1] = {"arm_id": "ctl", "value": Q(17.4)}
    os_.update({"conflict": "within_source_conflict", "conflict_ref": "conflito:sintetico:os",
                "value_candidates": [{"value": 17.4, "locator": {"section": "Abstract"}},
                                     {"value": 17.6, "locator": {"section": "Results"}}]})
    r["endpoints"] = P([ep, med, os_])
    r["design"]["stopped_early"] = P({"stopped": True, "reason": "efficacy", "at": {"basis": "enrollment", "fraction": 0.68}})
    r["interpretation"]["outcome"] = ED("mixed")
    return r


def withheld():
    r = base("syn-withheld")
    r["review"] = {"editorial_status": "withheld",
                   "integrity": {"status": "withheld", "reason": "quarentena editorial", "decision_ref": "quarentena:syn"}}
    for g, campo in (("population", "disease"), ("interpretation", "key_result"), ("interpretation", "takehome")):
        r[g][campo] = {"state": "withheld_due_to_integrity", "decision_ref": "quarentena:syn"}
    r["endpoints"] = {"state": "withheld_due_to_integrity", "decision_ref": "quarentena:syn"}
    r["identity"]["represented_publication"] = {"state": "withheld_due_to_integrity", "decision_ref": "quarentena:syn"}
    return r


def colecao():
    pai = base("syn-colecao", record_type="evidence_collection")
    for g in ("population", "design", "safety"):
        pai[g] = {}
    pai.pop("endpoints")
    pai["analyses"] = []
    pai["identity"] = {k: pai["identity"][k] for k in ("short_name", "display_title", "category_id", "evidence_stage")}
    pai["collection"] = {"scope": ED("agregado legado de várias séries publicadas do mesmo agente")}
    pai["relationships"]["child_uids"] = ["syn-colecao-serie-a", "syn-colecao-serie-b"]
    pai["legacy"]["v1"] = {"uid": "syn-colecao", "acron": "texto agregado legado"}
    filhos = []
    for sufixo, sup in (("a", None), ("b", "syn-colecao-serie-a")):
        f = base(f"syn-colecao-serie-{sufixo}", record_type="publication")
        f["relationships"]["parent_uid"] = "syn-colecao"
        f["design"]["allocation"] = P("single_arm", prov="p2")
        for k in ("masking", "control", "comparisons"):
            f["design"].pop(k)
        if sup:
            f["relationships"]["links"] = [{"type": "follow_up_of", "target_uid": sup}]
        f["endpoints"] = P([endpoint("e1", "PSA50", comp=None, summary="proportion",
                                     timepoint={"type": "best"}, arms=())])
        f["endpoints"]["v"][0].pop("arms_values")
        f["endpoints"]["v"][0].pop("effect")
        f["endpoints"]["v"][0]["estimate"] = {"value": Q(60)}
        f["analyses"][0]["signature"].update({"comparison": "none", "endpoint": "PSA50", "summary_measure": "proportion"})
        filhos.append(f)
    return [pai] + filhos


CENARIOS = {
    "radionuclide": radionuclide, "adc": adc, "immunotherapy": immunotherapy,
    "immunotherapy_sem_pdl1": lambda: immunotherapy(pdl1=False), "targeted": targeted, "ddr_hrd": ddr,
    "t_cell_engager_vs_qt": tce_vs_chemo, "car_t": car_t, "radiotherapy": radiotherapy,
    "perioperatorio_multimodal": perioperatorio, "diagnostico": diagnostico, "basket": basket,
    "co_primarios": co_primarios, "dual_primarios": dual_primarios, "tres_bracos_ni": tres_bracos,
    "modulo_so_no_controle": modulo_so_no_controle, "dose_randomizada_fatorial": dose_randomizada,
    "conflito_na_fonte": conflito, "withheld": withheld,
}


def F_eps(r):
    e = r.get("endpoints") or {}
    return e.get("v") or [] if e.get("state") == "present" else []


def todos() -> dict[str, dict]:
    out = {}
    for nome, fn in CENARIOS.items():
        r = fn()
        out[r["uid"]] = r
    for r in colecao():
        out[r["uid"]] = r
    import validate_v2 as V
    for n, r in enumerate(out.values()):
        r["legacy"]["position"] = n
        nct = f"NCT9{zlib.crc32(r['uid'].encode()) % 10**7:07d}"   # NCT sintético único e estável por fixture
        if L.estado(r["identity"].get("registrations")) == "present":
            r["identity"]["registrations"]["v"] = [{"registry": "NCT", "id": nct}]
        r["provenance"]["p2"]["source"]["nct"] = nct
        # uma assinatura por endpoint/medida/tempo (regra de consistência)
        modelo = (r.get("analyses") or [None])[0]
        r["analyses"] = []
        for e in F_eps(r):
            aid = f"a_{e['endpoint_id']}"
            e.setdefault("maturity", {})["analysis_ref"] = aid
            pop = e.get("population") or {}
            r["analyses"].append({
                "analysis_id": aid, "analysis_type": "primary", "data_cutoff": "2025-01-01",
                "publication_role": "primary_publication", "prov": "p1",
                "signature": {"trial_key": nct, "cohort": pop.get("cohort_id"),
                              "population": pop.get("biomarker_ref") or pop.get("label"),
                              "comparison": e.get("comparison_id") or "none", "endpoint": e["code"],
                              "summary_measure": e["measure"]["summary"],
                              "timepoint": V.tempo_canonico(e.get("timepoint")),
                              "assessment_method": e.get("assessment"),
                              "analysis_set": (e.get("analysis_set") or {}).get("name")}})
        del modelo
    return out


def gravar():
    PASTA.mkdir(exist_ok=True)
    for f in PASTA.glob("*.json"):
        f.unlink()
    for uid, r in todos().items():
        (PASTA / f"{uid}.json").write_text(json.dumps(r, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return len(list(PASTA.glob("*.json")))


if __name__ == "__main__":
    print(gravar(), "fixtures em", PASTA)
