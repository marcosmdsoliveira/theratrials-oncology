"""Registro do Database v2 — fonte única de campos, módulos, papéis e ativação.

Gera dois artefatos (não editar à mão):
  registry_v2.json        registro de campos (core, módulos, AESI, perfis, regras)
  schema_record_v2.json   JSON Schema (draft 2020-12) do registro canônico de um card

    python3 scripts/db_v2/registry_v2.py

Nada aqui toca o Database publicado.

Convenções
----------
* Todo campo do registro guarda um ENVELOPE: {state, origin?, v?, prov?, ...}.
  Chave ausente equivale a state=unknown.
* Obrigatoriedade de campo de MÓDULO depende do papel do módulo no braço
  (tested/backbone/control/context) E de uma condição de ativação estruturada.
  Campo inativo nunca é cobrado.
* Obrigatoriedade de campo do CORE depende do perfil do record_type.
"""
from __future__ import annotations

import json
import pathlib

AQUI = pathlib.Path(__file__).resolve().parent
VERSAO = "1.1"

E, U, S = "ESSENTIAL", "USEFUL", "SPECIALIZED"

# ── vocabulários ────────────────────────────────────────────────────────────
RECORD_TYPES = [
    "trial", "trial_cohort", "publication", "pooled_analysis", "meta_analysis",
    "cohort_study", "case_series", "diagnostic_study", "guideline",
    "molecular_classification", "translational", "evidence_collection",
]
STATES = ["present", "not_reported", "not_applicable", "unknown",
          "not_yet_available", "withheld_due_to_integrity"]
ORIGINS = ["reported", "derived", "editorial", "legacy"]  # legacy: copiado do v1, sem verificação
CURATION_LEVELS = ["shadow", "modeled", "curated"]
MODULES = ["radionuclide_therapy", "adc", "immunotherapy", "targeted_therapy", "ddr_hrd",
           "endocrine", "t_cell_engager", "cellular", "radiotherapy", "surgery",
           "locoregional", "chemotherapy", "diagnostic"]
ROLES = ["tested", "backbone", "control", "context"]
ARM_ROLES = ["experimental", "control", "contribution_of_components", "exploratory", "single", "exposure_group"]
INTERVENTION_ROLES = ["investigational", "backbone", "control", "supportive"]
INTERVENTION_PHASES = ["preparation", "upfront_local", "neoadjuvant", "adjuvant", "induction", "bridging",
                       "conditioning", "consolidation", "maintenance", "continuous", "single_administration"]
HIERARCHY_LEVELS = ["primary", "key_secondary", "secondary", "exploratory", "post_hoc", "safety", "unspecified"]
# "unspecified"/"multiple_unspecified": só em shadow/modeled (o v1 não diz); proibidos em curated
PRIMARY_TYPES = ["sole", "co_primary", "dual_primary", "multiple_unspecified"]
TESTING_PROCEDURES = ["none", "fixed_sequence", "graphical", "bonferroni", "holm", "hochberg",
                      "fallback", "alpha_split"]
SIGNIFICANCE = ["met", "not_met", "boundary_not_crossed", "stopped_for_futility", "descriptive", "not_tested"]
ANALYSIS_ROLES = ["protocol_primary_analysis", "supportive", "sensitivity"]
REL_LINKS = ["same_trial", "follow_up_of", "secondary_analysis_of", "supersedes", "member_of", "related"]
INTEGRITY = ["none", "hold", "quarantine", "withheld"]
# estudo EXTERNO (sem card, logo sem uid): identificador de registro validado por formato, sem rede
EXTERNAL_REGISTRIES = {
    "clinicaltrials_gov": {"pattern": r"^NCT\d{8}$", "host": "clinicaltrials.gov"},
    "isrctn": {"pattern": r"^ISRCTN\d{8}$", "host": "isrctn.com"},
    "eudract": {"pattern": r"^\d{4}-\d{6}-\d{2}$", "host": "clinicaltrialsregister.eu"},
    "ctis": {"pattern": r"^\d{4}-\d{6}-\d{2}-\d{2}$", "host": "euclinicaltrials.eu"},
    "anzctr": {"pattern": r"^ACTRN\d{14}$", "host": "anzctr.org.au"},
    "jrct": {"pattern": r"^jRCT[a-z]?\d{7,10}$", "host": "jrct.niph.go.jp"},
    "chictr": {"pattern": r"^ChiCTR[-A-Za-z0-9]{6,}$", "host": "chictr.org.cn"},
    "other": {"pattern": None, "host": None},
}
EXTERNAL_RELATIONS = ["same_trial", "related", "predecessor", "successor", "confirmatory", "parent_trial", "extension"]
BIOMARKER_FAMILIES = ["PD-L1", "MSI/MMR", "TMB", "BRCA", "HRR", "HRD", "HER2", "ER", "PR", "AR",
                      "ESR1", "PIK3CA", "EGFR", "ALK", "ROS1", "RET", "KRAS", "BRAF", "MET", "NTRK",
                      "FGFR", "IDH", "FLT3", "NPM1", "KMT2A", "MYCN", "TROP2", "FRα", "DLL3", "BCMA",
                      "CD19", "CD20", "GPRC5D", "Claudin18.2", "PSMA", "SSTR", "FAP", "MIBG", "ctDNA",
                      "other"]

# vocabulários fechados de campos escalares do core (validados quando present)
ENUMS = {
    "identity.evidence_stage": ["registered", "ongoing", "presented", "published_interim", "published_primary",
                                "published_final", "published_long_term"],
    "identity.phase": ["1", "1/2", "2", "2/3", "3", "4", "expanded_access", "not_applicable"],
    "population.setting": ["neoadjuvant", "perioperative", "adjuvant", "definitive", "consolidation", "maintenance",
                           "advanced_first_line", "advanced_later_line", "advanced_any_line", "salvage",
                           "on_treatment_switch", "newly_diagnosed", "relapsed_refractory", "transplant",
                           "staging", "restaging", "selection", "screening", "mixed"],
    "design.structure": ["single_cohort", "multi_cohort", "multi_cohort_basket", "umbrella", "platform", "factorial",
                         "observational"],
    "design.allocation": ["randomized", "nonrandomized", "single_arm", "observational"],
    "design.masking": ["open", "single_blind", "double_blind"],
    "design.question_type": ["drug_comparison", "add_on", "strategy", "de_escalation", "sequencing",
                             "dose_optimization"],
    "safety.population": ["safety_set", "cohort", "all_cohorts", "pooled"],
    "interpretation.outcome": ["positive", "negative", "mixed", "descriptive", "pending"],
}
ENDPOINT_CODES = ["PFS", "rPFS", "PFS2", "OS", "DFS", "iDFS", "EFS", "RFS", "MFS", "DSS", "FFS", "TFST", "ORR",
                  "CR", "CRh", "pCR", "MPR", "DoR", "DCR", "TTP", "CBR", "PSA50", "TTPP", "SSE", "MRD", "LC", "TTUP", "QoL",
                  "SENS", "SPEC", "PPV", "NPV", "DR", "SAFETY", "other"]
# sinônimos (PT/EN) → código; usados para NÃO deixar endpoint conhecido como 'other'
ENDPOINT_SYNONYMS = {
    "DSS": ["disease-specific survival", "cancer-specific survival", "sobrevida específica por doença",
            "sobrevida específica por câncer", "sobrevida câncer-específica", "sobrevida doença-específica"],
    "FFS": ["freedom from failure", "failure-free survival", "sobrevida livre de falha"],
    "PFS2": ["second progression-free survival", "time to second progression", "sobrevida livre de segunda progressão"],
    "TFST": ["time to first subsequent therapy", "tempo até a primeira terapia subsequente"],
    "MFS": ["metastasis-free survival", "sobrevida livre de metástase"],
    "RFS": ["recurrence-free survival", "relapse-free survival", "sobrevida livre de recorrência", "sobrevida livre de recidiva"],
    "EFS": ["event-free survival", "sobrevida livre de eventos"],
    "DFS": ["disease-free survival", "sobrevida livre de doença"],
    "LC": ["local control", "controle local"],
    "TTUP": ["time to untreatable progression", "tempo até progressão intratável"],
    "MPR": ["major pathological response", "resposta patológica maior"],
    "TTPP": ["time to psa progression", "tempo até progressão de psa"],
    "SSE": ["time to first symptomatic skeletal event", "symptomatic skeletal event", "tempo até 1º evento esquelético sintomático",
            "tempo até primeiro evento esquelético sintomático"],
}

# ── core ────────────────────────────────────────────────────────────────────
def C(path, tier, auto, v1=None, note=None):
    return {k: v for k, v in dict(path=path, tier=tier, automation=auto, v1=v1, note=note).items() if v is not None}

CORE = [
    C("identity.short_name", E, "human", "estudo"),
    C("identity.display_title", E, "human", "acron", "no v1 'acron' é título de exibição"),
    C("identity.acronym", U, "machine"),
    C("identity.aliases", U, "machine"),
    C("identity.registrations", E, "machine", "nct, nct_url"),
    C("identity.phase", E, "machine", "fase (parte)"),
    C("identity.sponsor", U, "machine", "sponsor"),
    C("identity.centers", U, "machine", "centros"),
    C("identity.enrollment_period", U, "machine", "periodo"),
    C("identity.represented_publication", E, "machine", "pubmed_url, ano_pub, titulo_full, ref, citation",
      "{publication_id, pmid, year}: aponta um publication_id de identity.publications; é a publicação que "
      "sustenta os dados exibidos e a única fonte da citação principal (evidence_collection não tem)"),
    C("identity.publications", U, "machine", "citation, ref, secondary-cards.js",
      "lista de $defs/publication (primária, updates, finais, secundárias, congresso); autoria só de metadados "
      "bibliográficos, nunca de sponsor"),
    C("identity.category_id", E, "human", "category_id"),
    C("identity.tumors", E, "verifier", "tumors / category"),
    C("identity.evidence_stage", E, "machine", "status (parte)"),
    C("identity.registry_status", U, "machine", "status (parte)"),
    C("population.disease", E, "verifier", "indicacao"),
    C("population.histology", U, "verifier", "indicacao/incl"),
    C("population.setting", E, "verifier", "linha (parte)"),
    C("population.line", U, "verifier", "linha (parte)"),
    C("population.disease_extent", U, "verifier", "indicacao"),
    C("population.risk_classification", U, "verifier", "incl/estrat/basal"),
    C("population.biomarker_selection", E, "verifier", "molecular, biomarc"),
    C("population.prior_therapy", E, "verifier", "incl/excl/linha"),
    C("population.fitness", U, "verifier", "incl"),
    C("population.key_inclusion", U, "verifier", "incl"),
    C("population.key_exclusion", U, "verifier", "excl"),
    C("population.performance_status", U, "verifier", "incl"),
    C("population.baseline", U, "verifier", "basal"),
    C("design.structure", E, "verifier", "desenho"),
    C("design.ratio", U, "verifier", "desenho"),
    C("design.cohorts", U, "verifier", "desenho/n"),
    C("design.question_type", U, "verifier", "desenho"),
    C("design.allocation", E, "machine", "desenho/fase"),
    C("design.masking", E, "machine", "desenho/fase"),
    C("design.control", E, "verifier", "comparador"),
    C("design.arms", E, "verifier", "radiofarmaco, esquema, comparador, n"),
    C("design.comparisons", E, "verifier", "estatistica"),
    C("design.multiplicity", U, "verifier", "estatistica"),
    C("design.factors", S, "verifier", "desenho"),
    C("design.sample_size", E, "verifier", "n"),
    C("design.stratification", U, "verifier", "estrat"),
    C("design.crossover", U, "verifier", "secundario/limit"),
    C("design.stopped_early", U, "verifier", "limit/status"),
    C("design.statistical_plan", S, "verifier", "estatistica, analises"),
    C("design.observational", E, "verifier", "desenho"),
    C("design.meta_analysis", E, "verifier", "desenho"),
    C("endpoints", E, "verifier", "primario, secundario"),
    C("subgroups", U, "verifier", "subgrupo"),
    C("safety.population", U, "verifier"),
    C("safety.grade3plus_any", E, "verifier", "tox_g3"),
    C("safety.serious_ae", U, "verifier", "tox_g3"),
    C("safety.discontinuation_ae", E, "verifier", "tox_g3/tox_interesse"),
    C("safety.dose_modification", U, "verifier", "tox_interesse"),
    C("safety.treatment_related_deaths", E, "verifier", "tox_g3"),
    C("safety.key_toxicities", E, "verifier", "tox_g3, tox_interesse"),
    C("safety.late_effects", S, "verifier"),
    C("interpretation.key_result", E, "human", "resultado_chave"),
    C("interpretation.takehome", E, "human", "takehome"),
    C("interpretation.outcome", U, "human", "status (parte)"),
    C("interpretation.limitations", E, "human", "limit"),
    C("interpretation.clinical_impact", U, "human", "impacto_reg (parte)"),
    C("interpretation.regulatory", U, "verifier", "impacto_reg (parte)"),
    C("interpretation.guideline_impact", U, "verifier", "impacto_reg (parte)"),
    C("guideline.issuing_bodies", E, "human"),
    C("guideline.version", E, "human"),
    C("guideline.status", E, "human"),
    C("guideline.recommendations", E, "human"),
    C("guideline.methodology", U, "human", None, "GRADE, consenso de especialistas…"),
    C("guideline.date", U, "human"),
    C("collection.summary", U, "human", None, "síntese agregada que não pode ser atribuída a um único filho"),
    C("collection.scope", E, "human", None, "evidence_collection: o que o registro agregado reúne"),
]
CORE_PATHS = [c["path"] for c in CORE]

# ── perfis por record_type (mapas explícitos por caminho) ───────────────────
IDENT = ["identity.short_name", "identity.display_title", "identity.category_id", "identity.evidence_stage"]
TRIAL_REQ = IDENT + [
    "identity.registrations", "identity.phase", "identity.represented_publication", "identity.tumors",
    "population.disease", "population.setting", "population.biomarker_selection", "population.prior_therapy",
    "design.structure", "design.allocation", "design.masking", "design.control", "design.arms",
    "design.comparisons", "design.sample_size", "endpoints",
    "safety.grade3plus_any", "safety.discontinuation_ae", "safety.treatment_related_deaths",
    "safety.key_toxicities", "interpretation.key_result", "interpretation.takehome",
    "interpretation.limitations",
]
NA_NON_TRIAL = ["design.allocation", "design.masking", "design.control", "design.comparisons",
                "design.multiplicity", "design.factors", "design.stratification", "design.crossover",
                "design.stopped_early"]
GUIDE = ["guideline.issuing_bodies", "guideline.version", "guideline.status", "guideline.recommendations"]
PROFILES = {
    "trial": {"required": TRIAL_REQ,
              "not_applicable": ["design.observational", "design.meta_analysis", "collection.scope"] + GUIDE},
    "trial_cohort": {"required": TRIAL_REQ + ["design.cohorts", "safety.population"],
                     "not_applicable": ["design.observational", "design.meta_analysis", "collection.scope"] + GUIDE},
    "publication": {"required": IDENT + ["identity.represented_publication", "population.disease", "endpoints",
                                         "interpretation.takehome"],
                    "not_applicable": ["collection.scope"] + GUIDE},
    "pooled_analysis": {"required": IDENT + ["identity.represented_publication", "population.disease", "endpoints",
                                             "interpretation.takehome", "interpretation.limitations"],
                        "not_applicable": ["design.observational", "collection.scope"] + GUIDE},
    "meta_analysis": {"required": IDENT + ["identity.represented_publication", "population.disease",
                                           "design.meta_analysis", "endpoints", "interpretation.limitations"],
                      "not_applicable": ["design.arms", "design.observational", "safety.grade3plus_any",
                                         "safety.treatment_related_deaths", "collection.scope"] + NA_NON_TRIAL + GUIDE},
    "cohort_study": {"required": IDENT + ["identity.represented_publication", "population.disease",
                                          "design.observational", "endpoints", "interpretation.limitations"],
                     "not_applicable": ["design.meta_analysis", "collection.scope"]
                     + [p for p in NA_NON_TRIAL if p != "design.comparisons"] + GUIDE},
    "case_series": {"required": IDENT + ["identity.represented_publication", "population.disease", "design.arms",
                                         "endpoints", "interpretation.limitations"],
                    "not_applicable": ["design.meta_analysis", "design.observational", "collection.scope"]
                    + NA_NON_TRIAL + GUIDE},
    "diagnostic_study": {"required": IDENT + ["identity.represented_publication", "population.disease", "endpoints",
                                              "interpretation.limitations"],
                         "not_applicable": ["design.arms", "design.meta_analysis", "design.observational",
                                            "safety.grade3plus_any", "safety.discontinuation_ae",
                                            "safety.treatment_related_deaths", "safety.key_toxicities",
                                            "collection.scope"] + NA_NON_TRIAL + GUIDE},
    "guideline": {"required": IDENT + GUIDE + ["interpretation.takehome"],
                  "not_applicable": [p for p in CORE_PATHS if p.startswith(("design.", "safety.", "endpoints",
                                                                            "subgroups"))] + ["collection.scope"]},
    "molecular_classification": {"required": IDENT + ["population.disease", "interpretation.takehome"],
                                 "not_applicable": [p for p in CORE_PATHS if p.startswith(("design.", "safety."))]
                                 + ["collection.scope"] + GUIDE},
    "translational": {"required": IDENT + ["identity.represented_publication", "population.disease", "endpoints"],
                      "not_applicable": ["design.meta_analysis", "collection.scope", "safety.grade3plus_any",
                                         "safety.treatment_related_deaths"] + NA_NON_TRIAL + GUIDE},
    "evidence_collection": {"required": IDENT + ["collection.scope"],
                            "not_applicable": [p for p in CORE_PATHS if p.startswith(("design.", "safety."))]
                            + ["endpoints", "subgroups"] + GUIDE},
}
# regra automática: braço único torna estes not_applicable sem curadoria
SINGLE_ARM_NA = ["design.masking", "design.control", "design.stratification", "design.crossover",
                 "design.multiplicity"]
# braço único: comparação deixa de ser EXIGIDA (pode existir como 'descriptive'), sem virar not_applicable
SINGLE_ARM_OPTIONAL = ["design.comparisons"]

# ── predicados de ativação (estruturados; avaliados por v2lib.ativo) ─────────
def always():
    return {"op": "always"}

def biomarker(*fams):
    """Biomarcador envolvido: seleção, estratificação, população de endpoint ou subgrupo."""
    return {"op": "biomarker_involved", "families": list(fams)}

def field_in(field, values):
    """Campo do PRÓPRIO módulo ($module.<campo>) ou caminho do core."""
    return {"op": "field_in", "field": field, "in": list(values)}

def agent_class(*classes):
    return {"op": "agent_class_in", "in": list(classes)}

def setting(*vals):
    return {"op": "setting_in", "in": list(vals)}

def randomized():
    return {"op": "field_in", "field": "design.allocation", "in": ["randomized"]}

def any_of(*conds):
    return {"op": "any_of", "conds": list(conds)}

def all_of(*conds):
    return {"op": "all_of", "conds": list(conds)}

def reported(field):
    """O campo já tem valor present (ex.: resultado estratificado registrado)."""
    return {"op": "present", "field": field}


# ── campos de módulo: requisito por papel + ativação ────────────────────────
# req: 4 letras na ordem tested/backbone/control/context — R required, O optional, N not_applicable
def M(name, tier, req, activation=None, note=None, auto="verifier", per="study"):
    r = dict(zip(ROLES, [{"R": "required", "O": "optional", "N": "not_applicable"}[c] for c in req.split()]))
    return {k: v for k, v in dict(field=name, tier=tier, requirement=r, activation=activation or always(),
                                    per=per, automation=auto, note=note).items() if v is not None}

def A(term, req, activation=None, note=None):
    """Termo de AESI do painel do módulo; gravado em safety.key_toxicities com aesi_of."""
    r = dict(zip(ROLES, [{"R": "required", "O": "optional", "N": "not_applicable"}[c] for c in req.split()]))
    return {k: v for k, v in dict(term=term, requirement=r, activation=activation or always(), note=note).items()
            if v is not None}

LIGAND = field_in("$module.delivery", ["systemic_ligand", "radioimmunoconjugate"])

MODULE_FIELDS = {
    "radionuclide_therapy": {
        "fields": [
            M("delivery", E, "R O O N", note="systemic_ligand | systemic_ion | radioimmunoconjugate | intra_arterial_microsphere | metabolic"),
            M("intent", U, "O O O N", note="treatment | ablation | adjuvant | consolidation | palliation"),
            M("target", E, "R O O N", LIGAND, note="PSMA, SSTR2, FAP…; ativo só para ligante sistêmico"),
            M("radionuclide", E, "R O O N", per="agent"),
            M("activity_per_administration", E, "R O O N",
              field_in("$module.delivery", ["systemic_ligand", "systemic_ion", "radioimmunoconjugate", "metabolic"]),
              per="agent", note="TARE usa absorbed_dose"),
            M("cycles", E, "R O O N",
              field_in("$module.delivery", ["systemic_ligand", "systemic_ion", "radioimmunoconjugate", "metabolic"]),
              per="agent"),
            M("absorbed_dose", U, "O O O N", note="ESSENTIAL de fato em TARE; ver ativação abaixo", per="arm"),
            M("device", S, "O O O N", field_in("$module.delivery", ["intra_arterial_microsphere"])),
            M("imaging_selection", E, "R O N N", LIGAND),
            M("dosimetry", U, "O O O N"),
            M("organ_protection", U, "O O N N"),
            M("patient_preparation", U, "O O O N", per="arm"),
            M("radiation_safety", S, "O O N N"),
        ],
        "required_overrides": [
            {"field": "absorbed_dose", "role": "tested",
             "activation": field_in("$module.delivery", ["intra_arterial_microsphere"])},
        ],
        "aesi": [
            A("hematologic", "R O N N", {"op": "not", "cond": field_in("$module.delivery", ["intra_arterial_microsphere"])}),
            A("renal", "R O N N", field_in("$module.delivery", ["systemic_ligand", "radioimmunoconjugate"])),
            A("xerostomia_salivary", "R O N N", field_in("$module.target", ["PSMA"])),
            A("mds_aml", "O O N N"),
            A("liver_reild", "R O N N", field_in("$module.delivery", ["intra_arterial_microsphere"])),
        ],
    },
    "adc": {
        "fields": [
            M("target", E, "R R O N", per="agent"),
            M("payload_class", E, "R O O N", per="agent"),
            M("payload", U, "O O O N", per="agent"),
            M("target_expression", E, "R O N N",
              any_of({"op": "biomarker_matches_field", "field": "$module.target"}, reported("$module.target_expression")),
              note="lista por coorte de expressão"),
            M("prior_same_target", E, "R N N N", note="VISÃO de population.prior_therapy filtrada pelo alvo"),
            M("prior_same_payload_class", U, "O N N N"),
        ],
        "aesi": [
            A("ild_pneumonitis", "R O O N", field_in("$module.payload_class", ["topo1_inhibitor"])),
            A("ocular_surface", "R O O N", field_in("$module.payload_class", ["microtubule_inhibitor", "dna_alkylator"])),
            A("peripheral_neuropathy", "R O O N", field_in("$module.payload_class", ["microtubule_inhibitor"])),
            A("lvef_decline", "R O O N", field_in("$module.target", ["HER2"])),
            A("neutropenia", "O O O N"),
            A("stomatitis", "O O O N"),
        ],
    },
    "immunotherapy": {
        "fields": [
            M("target", E, "R R O N", per="agent"),
            M("pdl1", E, "R O N O", biomarker("PD-L1"),
              note="assay, score, cutoff, papel (seleção|estratificação|análise); ativo só se PD-L1 é critério, estratificação, biomarcador analisado ou resultado por expressão"),
            M("msi_mmr", U, "R O N O", biomarker("MSI/MMR")),
            M("tmb", S, "O O N O", biomarker("TMB")),
            M("prior_io", E, "R N N O", note="VISÃO de population.prior_therapy"),
            M("treatment_duration", U, "O O O N", per="agent"),
        ],
        "aesi": [
            A("immune_related_g3plus", "R O O N"),
            A("pneumonitis", "O O O N"),
            A("colitis", "O O O N"),
            A("hepatitis", "O O O N"),
            A("endocrinopathy", "O O O N"),
        ],
    },
    "targeted_therapy": {
        "fields": [
            M("target", E, "R R O N", per="agent"),
            M("agent_class", U, "O O O N", per="agent"),
            M("required_alteration", E, "R O N O",
              all_of({"op": "not", "cond": agent_class("ssa", "cdk46i", "antiangiogenic", "mtori", "imid",
                                                        "proteasome_i", "bcl2i")},
                     {"op": "biomarker_rule_in", "in": ["required", "enriched"]}),
              note="referência a population.biomarker_selection[].id"),
            M("detection", E, "R O N O", {"op": "biomarker_rule_in", "in": ["required", "enriched", "stratified"]}),
            M("prior_targeted_therapy", E, "R N N O", note="VISÃO de population.prior_therapy"),
            M("cns", U, "O N N N"),
            M("resistance_mechanisms", S, "O N N N"),
        ],
        "aesi": [
            A("mds_aml", "R O N N", agent_class("parpi")),
            A("anemia", "R O N N", agent_class("parpi")),
            A("vte", "O O N N"),
            A("hyperglycemia", "R O N N", agent_class("pi3k_i", "akt_i")),
            A("qtc", "O O N N"),
            A("rash_paronychia", "R O N N", agent_class("egfr_mab", "bispecific_antibody")),
            A("infusion_reaction", "R O N N", agent_class("bispecific_antibody")),
        ],
    },
    "ddr_hrd": {
        "warn_if_absent": True,
        "biomarker_context": True,   # não tem agente próprio: não exige intervenção do módulo no braço
        "activation_module": any_of(biomarker("BRCA", "HRR", "HRD"),
                                    {"op": "subgroup_dimension_in", "in": ["BRCA", "HRR", "HRD"]}),
        "fields": [
            M("genes", E, "R R N R"),
            M("hrd_test", U, "O O N O", biomarker("HRD")),
            M("origin", E, "R O N O", note="{tested_in, distinguishes_origin, allowed}"),
            M("platinum_sensitivity", U, "O O N O", setting("maintenance")),
            M("stratified_results", E, "R O N O",
              {"op": "subgroup_dimension_in", "in": ["BRCA", "HRR", "HRD"]},
              note="referências a endpoints[] com population=biomarcador"),
        ],
        "aesi": [],
    },
    "endocrine": {
        "fields": [
            M("hormone_context", E, "R R O R"),
            M("receptor_status", U, "O O N O", field_in("$module.hormone_context", ["breast_hr_pos"])),
            M("menopausal_status", U, "O O N O", field_in("$module.hormone_context", ["breast_hr_pos"])),
            M("endocrine_resistance", E, "R O N O", field_in("$module.hormone_context", ["breast_hr_pos"])),
            M("castration_status", E, "R R N R",
              field_in("$module.hormone_context", ["prostate_hspc", "prostate_crpc", "prostate_nmcrpc"])),
            M("prior_endocrine", E, "R N N O", note="VISÃO de population.prior_therapy"),
            M("prior_cdk46", E, "R N N O", field_in("$module.hormone_context", ["breast_hr_pos"])),
            M("adt_backbone", U, "O O O O",
              field_in("$module.hormone_context", ["prostate_hspc", "prostate_crpc", "prostate_nmcrpc"])),
            M("disease_volume_risk", U, "O O N O", field_in("$module.hormone_context", ["prostate_hspc"])),
            M("esr1", U, "O O N O", biomarker("ESR1")),
        ],
        "aesi": [],
    },
    "t_cell_engager": {
        "fields": [
            M("targets", E, "R R O N", per="agent", note="{tumor_target, effector: CD3}"),
            M("format", U, "O O O N", per="agent"),
            M("step_up_dosing", U, "O O O N", per="agent"),
            M("hospitalization", U, "O O N N"),
            M("dosing_deescalation", S, "O O N N"),
        ],
        "aesi": [
            A("crs", "R O N N"),
            A("icans", "R O N N"),
            A("infections", "R O N N"),
            A("cytopenias", "O O N N"),
            A("hypogammaglobulinemia", "O O N N", biomarker("BCMA", "GPRC5D")),
        ],
    },
    "cellular": {
        "fields": [
            M("product_type", E, "R R R N", per="arm", note="car_t | tcr_t | til | allogeneic_hct"),
            M("target", E, "R R O N", field_in("$module.product_type", ["car_t", "tcr_t"]), per="agent"),
            M("cell_dose", U, "O O O N", per="agent"),
            M("bridging", U, "O O O N", field_in("$module.product_type", ["car_t", "tcr_t", "til"])),
            M("lymphodepletion_or_conditioning", U, "O O O N"),
            M("pre_infusion_events", U, "O O O N"),
            M("vein_to_vein", S, "O N N N"),
        ],
        "aesi": [
            A("crs", "R O O N", field_in("$module.product_type", ["car_t", "tcr_t", "til"])),
            A("icans", "R O O N", field_in("$module.product_type", ["car_t", "tcr_t"])),
            A("prolonged_cytopenias", "R O O N"),
            A("infections", "O O O N"),
            A("delayed_neurotoxicity", "O O N N", field_in("$module.product_type", ["car_t"])),
            A("secondary_malignancy", "O O N N"),
        ],
    },
    "radiotherapy": {
        "fields": [
            M("components", E, "R R R N", per="arm", note="[{arm_id, technique, target, total_gy|range, fractions}]"),
            M("technique", E, "R O O N"),
            M("bed_eqd2", S, "O O O N", note="só se REPORTADO; derivado não vai para o card"),
            M("concurrent_systemic", U, "O O O N"),
            M("target_definition_imaging", U, "O O N N"),
            M("igrt_motion", S, "O N N N"),
        ],
        "aesi": [
            A("pneumonitis", "R O O N", {"op": "rt_site_in", "in": ["thorax"]}),
            A("esophagitis", "O O O N", {"op": "rt_site_in", "in": ["thorax"]}),
            A("gi_gu_late", "R O O N", {"op": "rt_site_in", "in": ["pelvis"]}),
            A("radionecrosis", "O O O N", {"op": "rt_site_in", "in": ["cns"]}),
        ],
    },
    "surgery": {
        "fields": [
            M("procedure", E, "R R R N", per="arm"),
            M("r0_rate", U, "O O O N", per="arm"),
            M("complications", U, "O O O N", per="arm"),
            M("perioperative_mortality", U, "O O O N", per="arm"),
        ],
        "aesi": [],
    },
    "locoregional": {
        "fields": [
            M("procedure", E, "R R R N", per="arm", note="TACE_c | TACE_DEB | HAIC | ablation | HIPEC | intravesical | other (TARE fica em radionuclide_therapy)"),
            M("schedule", U, "O O O N", per="arm"),
        ],
        "aesi": [],
    },
    "chemotherapy": {
        "fields": [
            M("regimen_label", U, "O O O N", per="arm"),
            M("agent_class", U, "O O O N", per="agent", note="inclui hypomethylating"),
            M("cycles", U, "O O O N", per="arm"),
            M("high_dose", E, "R R R N", {"op": "agent_class_in", "in": ["high_dose_with_autologous_rescue"]}),
        ],
        "aesi": [
            A("sos_vod", "R O O N", {"op": "agent_class_in", "in": ["high_dose_with_autologous_rescue"]}),
            A("febrile_neutropenia", "O O O N"),
        ],
    },
    "diagnostic": {
        "fields": [
            M("index_test", E, "R N N N"),
            M("reference_standard", E, "R N N N"),
            M("unit_of_analysis", E, "R N N N"),
            M("target", U, "O N N N"),
            M("interfering_medications", U, "O N N N"),
            M("readers", U, "O N N N"),
            M("acquisition", S, "O N N N"),
            M("management_impact", U, "O N N N"),
        ],
        "aesi": [],
    },
}

# ── estruturas compartilhadas (documentação + schema) ────────────────────────
ENDPOINT_MODEL = {
    "endpoint_id": "id único no registro",
    "code": "PFS | rPFS | OS | DFS | iDFS | EFS | RFS | MFS | ORR | CR | CRh | pCR | DoR | DCR | TTP | CBR | PSA50 | MRD | LC | TTUP | QoL | SENS | SPEC | PPV | NPV | DR | SAFETY | other",
    "definition": "texto (obrigatório para compostos)",
    "response_criteria": "RECIST1.1 | mRECIST | iRECIST | PCWG3 | RANO | Lugano | IMWG | ELN2017 | ELN2022 | …",
    "hierarchy": {
        "level": "primary | key_secondary | secondary | exploratory | post_hoc | safety",
        "primary_type": "sole | co_primary (todos precisam ser positivos) | dual_primary (qualquer um; α dividido)",
        "scope": "{cohort_id?, part_id?} — primário diferente por coorte/parte",
        "testing": "{family_id, order} — hierarquia sequencial/controle de multiplicidade via design.multiplicity",
        "history": "[{level, changed_at, reason: amendment|…, source}] — endpoint alterado por emenda",
    },
    "comparison_id": "ref design.comparisons (null em braço único/diagnóstico)",
    "population": "{label, biomarker_ref?, cohort_id?}",
    "measure": "{summary: median | rate | mean | proportion | hr_only | accuracy, analysis_role: protocol_primary_analysis | supportive | sensitivity}",
    "timepoint": "{type: median | landmark | cumulative | at_event, months?}",
    "assessment": "BICR | INV | central_path | …",
    "analysis_set": "{name: ITT | mITT | PP | safety | efficacy_evaluable, n?}",
    "analysis_method": "unadjusted | RPSFT | IPCW | stratified_cox | …",
    "arms_values": "[{arm_id | arm_group, value: QUALIFIED, ci?, n?}]",
    "estimate": "{value: QUALIFIED, ci?, n?} — desenho sem braço",
    "unit_of_analysis": "patient | region | lesion",
    "effect": "{measure: HR | OR | RR | risk_difference | rate_difference | none, value: QUALIFIED, ci?, p?, sided?, significance}",
    "maturity": "{analysis_ref, analysis_type, data_cutoff, follow_up_median_months, events, information_fraction, boundary_p}",
}

MULTIPLICITY_MODEL = {
    "families": "[{family_id, overall_alpha, procedure: fixed_sequence | graphical | bonferroni | holm | hochberg | fallback | alpha_split | none, members: [{endpoint_id, alpha?, order?}]}]",
    "regras": [
        "sole: exatamente 1 endpoint level=primary por (escopo, comparison_id)",
        "co_primary/dual_primary: ≥2 endpoints level=primary no mesmo escopo, todos com o mesmo primary_type",
        "dual_primary exige família de multiplicidade com α por membro e soma ≤ overall_alpha",
        "fixed_sequence exige order distinto e contíguo 1..n",
        "primário por coorte/parte: scope distingue; a regra 'sole' vale por escopo",
        "emenda: history[] guarda o nível anterior; o nível vigente é hierarchy.level",
        "um mesmo endpoint com duas medidas (taxa em landmark e mediana): dois endpoint_ids, mesmo code, measure.analysis_role distinto; só o protocol_primary_analysis conta como primário para 'sole'",
    ],
}

ANALYSIS_SIGNATURE = {
    "identity": ["trial_key", "cohort", "population", "comparison", "endpoint", "summary_measure",
                 "timepoint", "assessment_method", "analysis_set"],
    "ordering": ["analysis_type", "data_cutoff"],
    "maturity": ["follow_up_median", "sample_size", "events", "information_fraction"],
    "publication_role": ["primary_publication", "update", "final", "long_term", "secondary_analysis",
                         "key_secondary_primary_analysis", "subgroup",
                         "qol_pro", "safety", "translational", "pooled", "correction", "congress", "congress_abstract"],
    "conditional": "comparison='none' em braço único/diagnóstico (vem do desenho, não é inferido)",
    "consistency": "cada endpoint aponta (maturity.analysis_ref) para uma assinatura com o MESMO endpoint, summary_measure, "
                   "timepoint canônico ('median', 'landmark:6', 'at_event:6-10') e comparison; endpoints/medidas/tempos "
                   "diferentes exigem assinaturas próprias",
}

RELATIONSHIPS = {
    "parent_uid": "registro-pai (ex.: coorte → estudo; publicação filha → evidence_collection)",
    "child_uids": "filhos; recíproco de parent_uid",
    "links": "[{type: same_trial | follow_up_of | secondary_analysis_of | supersedes | member_of, target_uid}]",
    "regras": ["sem auto-referência", "grafo parent/child sem ciclo", "supersedes/follow_up_of/secondary_analysis_of sem ciclo",
               "parent_uid ↔ child_uids recíprocos quando os dois registros existem",
               "uid nunca é reutilizado: o card agregado vira evidence_collection com o MESMO uid; filhos recebem uids novos"],
}

VALIDATION_ERRORS = {
    "E_SCHEMA": "violação do JSON Schema",
    "E_PUBLICATION": "publication fora do $def (first_author ≠ authors[0], metadata_source proibida, pages e article_number juntos…)",
    "E_PUBLICATION_REF": "represented_publication aponta publication_id inexistente em identity.publications",
    "E_CITATION": "citation do card v1 ≠ projeção da publicação representada, ou citation em evidence_collection",
    "E_UID_IMMUTABLE": "uid do HEAD ausente no conjunto novo, ou nome de arquivo ≠ uid",
    "E_RECORD_TYPE": "record_type inválido",
    "E_MODULE": "módulo desconhecido ou papel inválido",
    "E_ARM_REF": "arm_id referenciado não existe em design.arms",
    "E_COMPARISON_REF": "comparison_id inexistente ou braços da comparação inexistentes",
    "E_COHORT_REF": "cohort_id/biomarker_ref inexistente",
    "E_STATE": "estado semântico inválido ou incoerente com o envelope",
    "E_ORIGIN": "present sem origin, ou origin=legacy fora de shadow/modeled",
    "E_PROV": "prov ausente ou apontando para proveniência inexistente",
    "E_DERIVED": "derived sem formula/assumptions/source_fields/version",
    "E_CONFLICT": "conflito sem ≥2 value_candidates ou sem locator",
    "E_SIGNATURE": "analysis_signature incompleta ou endpoint apontando para análise inexistente",
    "E_PRIMARY": "estrutura de primários incoerente (sole/co/dual/multiplicidade)",
    "E_REL": "relação inválida (auto-referência, ciclo, parent/child não recíproco)",
    "E_REQUIRED": "campo obrigatório (perfil, papel e ativação) ausente em registro curated",
    "E_NA_CONTRADICTION": "campo marcado not_applicable mas obrigatório e ativo",
    "E_HTML": "HTML em texto",
    "E_LEGACY": "registro sem legacy.v1 ou uid divergente",
    "E_EXTERNAL": "external_relationships com registro/identificador/URL inválidos",
    "E_CURATED_IN_SHADOW": "registro curated num diretório de sombra (CI)",
    "W_EXTERNAL_HAS_CARD": "estudo externo que já tem card: usar relationships.links",
    "E_VALUE": "valor numérico incoerente (IC invertido, efeito fora do IC)",
    "E_ENUM": "valor fora do vocabulário fechado",
    "W_REQUIRED": "lacuna de completude (shadow/modeled) — backlog, nunca inbox",
    "W_REQUIRED_ACK": "curated: obrigatório declarado unknown com fontes conferidas (a fonte não permite concluir)",
    "W_MODULE": "incoerência módulo × intervenção em registro não curado",
    "W_MODULE_MISSING": "módulo de contexto ativo mas ausente (ex.: ddr_hrd com biomarcador DDR)",
    "W_SAMPLE_SIZE": "soma dos braços maior que o total randomizado",
    "W_SIGNIFICANCE": "significância declarada sem p nem IC",
    "W_COMPARISON": "primário de estudo randomizado sem comparison_id (não curado)",
    "W_NOT_APPLICABLE_FILLED": "campo preenchido embora não se aplique ao perfil/papel",
    "W_REL_ORPHAN": "parent_uid aponta registro fora do conjunto validado",
}


# ── JSON Schema do registro canônico ────────────────────────────────────────
def json_schema() -> dict:
    qualified = {
        "type": "object",
        "properties": {
            "op": {"enum": ["=", "≈", "<", "≤", ">", "≥", "range", "not_reached", "not_evaluable", "direction_only"]},
            "value": {"type": "number"}, "low": {"type": "number"}, "high": {"type": "number"},
            "unit": {"type": "string"},
            "direction": {"enum": ["favors_exp", "favors_ctl", "no_difference"]},
        },
        "required": ["op"], "additionalProperties": False,
    }
    ci = {"type": "object", "properties": {"level": {"type": "number"}, "low": {"type": "number"},
                                           "high": {"type": ["number", "null"]},
                                           "high_not_reached": {"type": "boolean"}},
          "required": ["level", "low", "high"], "additionalProperties": False}
    envelope = {
        "type": "object",
        "properties": {
            "state": {"enum": STATES},
            "origin": {"enum": ORIGINS},
            "v": {},
            "prov": {"type": "string"},
            "conflict": {"enum": ["none", "explained", "within_source_conflict", "cross_source_conflict"]},
            "value_candidates": {"type": "array", "items": {
                "type": "object", "properties": {"value": {}, "locator": {"type": "object"}, "prov": {"type": "string"}},
                "required": ["value", "locator"]}},
            "resolution": {"type": "string"},
            "conflict_ref": {"type": "string"},
            "derivation": {"$ref": "#/$defs/derivation"},
            "checked_sources": {"type": "array", "items": {"type": "string"}},
            "expected": {"type": "string"},
            "decision_ref": {"type": "string"},
            "legacy_ref": {"type": "array", "items": {"type": "string"}},
            "note": {"type": "string"},
        },
        "required": ["state"], "additionalProperties": False,
    }
    endpoint = {
        "type": "object",
        "properties": {
            "endpoint_id": {"type": "string"}, "code": {"enum": ENDPOINT_CODES}, "definition": {"type": "string"},
            "definition_candidates": {"type": "array", "items": {"type": "object", "properties": {
                "definition": {"type": "string"}, "prov": {"type": "string"}}, "required": ["definition", "prov"]}},
            "decision_ref": {"type": "string"}, "expected": {"type": "string"}, "note": {"type": "string"},
            "response_criteria": {"type": "string"},
            "hierarchy": {"type": "object", "properties": {
                "level": {"enum": HIERARCHY_LEVELS}, "primary_type": {"enum": PRIMARY_TYPES},
                "scope": {"type": "object", "properties": {"cohort_id": {"type": "string"}, "part_id": {"type": "string"}},
                          "additionalProperties": False},
                "testing": {"type": "object", "properties": {"family_id": {"type": "string"}, "order": {"type": "integer"}},
                            "additionalProperties": False},
                "history": {"type": "array", "items": {"type": "object", "properties": {
                    "level": {"enum": HIERARCHY_LEVELS}, "changed_at": {"type": "string"}, "reason": {"type": "string"},
                    "source": {"type": "string"}}, "required": ["level", "reason"]}},
            }, "required": ["level"], "additionalProperties": False},
            "comparison_id": {"type": ["string", "null"]},
            "population": {"type": "object", "properties": {"label": {"type": "string"}, "biomarker_ref": {"type": "string"},
                                                            "cohort_id": {"type": "string"}},
                           "required": ["label"], "additionalProperties": False},
            "measure": {"type": "object", "properties": {
                "summary": {"enum": ["median", "rate", "mean", "proportion", "hr_only", "accuracy", "count"]},
                "analysis_role": {"enum": ANALYSIS_ROLES}}, "required": ["summary"], "additionalProperties": False},
            "timepoint": {"type": "object", "properties": {"type": {"enum": ["median", "landmark", "cumulative", "at_event", "best"]},
                                                           "months": {"type": "number"},
                                                           "window": {"type": "object", "properties": {
                                                               "low": {"type": "number"}, "high": {"type": "number"}},
                                                               "required": ["low", "high"], "additionalProperties": False}},
                          "required": ["type"], "additionalProperties": False},
            "assessment": {"type": "string"},
            "analysis_set": {"type": "object", "properties": {"name": {"type": "string"}, "n": {"type": "integer"}},
                             "required": ["name"], "additionalProperties": False},
            "analysis_method": {"type": "string"},
            "arms_values": {"type": "array", "items": {"type": "object", "properties": {
                "arm_id": {"type": "string"},
                "arm_group": {"type": "object", "properties": {"factor": {"type": "string"}, "level": {"type": "string"}},
                              "required": ["factor", "level"]},
                "value": {"$ref": "#/$defs/qualified"}, "ci": {"$ref": "#/$defs/ci"}, "n": {"type": "integer"},
                "events": {"type": "integer"},
                "flags": {"type": "array", "items": {"enum": ["pct_inconsistent_with_n", "ci_implausible", "rounding"]}}},
                "required": ["value"], "additionalProperties": False}},
            "estimate": {"type": "object", "properties": {"value": {"$ref": "#/$defs/qualified"}, "ci": {"$ref": "#/$defs/ci"},
                                                          "n": {"type": "integer"}},
                         "required": ["value"], "additionalProperties": False},
            "unit_of_analysis": {"enum": ["patient", "region", "lesion"]},
            "effect": {"type": "object", "properties": {
                "measure": {"enum": ["HR", "OR", "RR", "risk_difference", "rate_difference", "none"]},
                "value": {"$ref": "#/$defs/qualified"}, "ci": {"$ref": "#/$defs/ci"}, "p": {"type": "string"},
                "sided": {"enum": [1, 2]}, "significance": {"enum": SIGNIFICANCE},
                "favors": {"enum": ["exp", "ctl", "none"]}},
                "required": ["measure"], "additionalProperties": False},
            "maturity": {"type": "object", "properties": {
                "analysis_ref": {"type": "string"}, "analysis_type": {"type": "string"}, "data_cutoff": {"type": "string"},
                "follow_up_median_months": {"type": "number"}, "events": {"type": "integer"},
                "information_fraction": {"type": "number"}, "boundary_p": {"type": "number"}},
                "additionalProperties": False},
            "state": {"enum": STATES}, "origin": {"enum": ORIGINS}, "prov": {"type": "string"},
            "conflict": {"enum": ["none", "explained", "within_source_conflict", "cross_source_conflict"]},
            "value_candidates": {"type": "array"}, "conflict_ref": {"type": "string"},
        },
        "required": ["endpoint_id", "code", "hierarchy", "population", "state"],
        "additionalProperties": False,
    }
    intervention = {
        "type": "object",
        "properties": {
            "intervention_id": {"type": "string"}, "agent": {"type": "string"}, "agent_class": {"type": "string"},
            "module": {"enum": MODULES}, "role": {"enum": INTERVENTION_ROLES}, "phase": {"enum": INTERVENTION_PHASES},
            "dose": {"type": "object"}, "route": {"type": "string"}, "schedule": {"type": "string"},
            "duration": {"type": "string"}, "attributes": {"type": "object"},
            "supportive_care": {"type": "array", "items": {"type": "object"}},
        },
        "required": ["agent", "role"], "additionalProperties": False,
    }
    arm = {
        "type": "object",
        "properties": {
            "arm_id": {"type": "string", "pattern": "^[a-z0-9_]+$"}, "label": {"type": "string"},
            "role": {"enum": ARM_ROLES}, "status": {"enum": ["active", "closed_early"]}, "closed_at": {"type": "string"},
            "n": {"$ref": "#/$defs/qualified"}, "n_analyzed": {"$ref": "#/$defs/qualified"},
            "assignment": {"enum": ["randomized", "biomarker_assigned", "nonrandomized"]},
            "factor_levels": {"type": "object"},
            "interventions": {"type": "array", "items": {"$ref": "#/$defs/intervention"}},
            "choice": {"type": "object"},
            "proceeded_to_planned_therapy": {"type": "array", "items": {"type": "object", "properties": {
                "step": {"enum": ["surgery", "infusion", "asct", "rt", "other"]}, "pct": {"type": "number"},
                "n": {"type": "integer"}, "of": {"type": "integer"},
                "state": {"enum": STATES}, "origin": {"enum": ORIGINS}, "prov": {"type": "string"},
                "derivation": {"$ref": "#/$defs/derivation"},
                "checked_sources": {"type": "array", "items": {"type": "string"}}, "note": {"type": "string"}},
                "required": ["step"], "additionalProperties": False}},
            "cohort_id": {"type": "string"},
        },
        "required": ["arm_id", "role"], "additionalProperties": False,
    }
    comparison = {
        "type": "object",
        "properties": {
            "comparison_id": {"type": "string"}, "exp_arms": {"type": "array", "items": {"type": "string"}, "minItems": 1},
            "ctl_arms": {"type": "array", "items": {"type": "string"}},
            "hypothesis": {"enum": ["superiority", "non_inferiority", "equivalence", "descriptive"]},
            "ni_margin": {"type": "object", "properties": {"measure": {"type": "string"}, "value": {"type": "number"}},
                          "required": ["measure", "value"]},
            "alpha": {"type": "number"}, "alpha_sided": {"enum": [1, 2]}, "cohort_id": {"type": "string"},
            "ctl_type": {"enum": ["randomized", "contemporaneous_nonrandomized", "historical", "external"]},
        },
        "required": ["comparison_id", "exp_arms", "hypothesis"], "additionalProperties": False,
    }
    module_entry = {
        "type": "object",
        "properties": {
            "module": {"enum": MODULES}, "role": {"enum": ROLES + ["undetermined"]},
            "arm_ids": {"oneOf": [{"const": "all"}, {"type": "array", "items": {"type": "string"}}, {"type": "null"}]},
            "fields": {"type": "object", "additionalProperties": {"$ref": "#/$defs/envelope"}},
            "classification": {"type": "object", "properties": {
                "basis": {"enum": ["inferred", "curated"]}, "confidence": {"enum": ["high", "medium", "low"]},
                "evidence": {"type": "array", "items": {"type": "string"}}}, "required": ["basis"]},
        },
        "required": ["module", "role", "arm_ids"], "additionalProperties": False,
    }
    publication = {
        "type": "object",
        "properties": {
            "publication_id": {"type": "string", "pattern": r"^(pmid:\d+|doi:.+|ed:[a-z0-9_\-]+)$"},
            "role": {"enum": ANALYSIS_SIGNATURE["publication_role"] + ["undetermined"]},
            "pmid": {"type": "string", "pattern": r"^\d+$"}, "doi": {"type": "string"}, "pmcid": {"type": "string"},
            "authors": {"type": "array", "items": {"type": "object", "properties": {
                "family": {"type": "string", "minLength": 1}, "given_initials": {"type": "string"},
                "suffix": {"type": "string"}}, "required": ["family", "given_initials"], "additionalProperties": False}},
            "authors_total": {"type": "integer", "minimum": 0},
            "collective_name": {"type": ["string", "null"]},
            "first_author": {"type": ["string", "null"]},
            "title": {"type": "string", "minLength": 1}, "journal": {"type": ["string", "null"]},
            "journal_abbrev": {"type": ["string", "null"]}, "year": {"type": "integer", "minimum": 1900},
            "volume": {"type": ["string", "null"]}, "issue": {"type": ["string", "null"]},
            "pages": {"type": ["string", "null"]}, "article_number": {"type": ["string", "null"]},
            "publication_type": {"enum": ["journal_article", "guideline", "meta_analysis", "systematic_review", "review",
                                          "congress_abstract", "erratum", "other"]},
            "metadata_source": {"enum": ["pubmed_esummary", "crossref", "editorial"]},
            "retrieved_at": {"type": ["string", "null"]},
        },
        "required": ["publication_id", "role", "title", "year", "publication_type", "metadata_source"],
        "additionalProperties": False,
    }
    provenance = {
        "type": "object",
        "properties": {
            "source": {"type": "object", "properties": {
                "type": {"enum": ["publication", "registry", "registry_results", "regulatory", "guideline",
                                  "congress_abstract", "human_decision", "v1_legacy"]},
                "pmid": {"type": "string"}, "doi": {"type": "string"}, "pmcid": {"type": "string"},
                "nct": {"type": "string"}, "url": {"type": "string"}, "field": {"type": "string"}},
                "required": ["type"]},
            "locator": {"type": "object", "properties": {"section": {"type": "string"}, "table": {"type": "string"},
                                                         "figure": {"type": "string"}, "snippet": {"type": "string"}}},
            "extraction": {"enum": ["explicit", "derived", "human_confirmed", "lifted_v1"]},
            "evidence_confidence": {"enum": ["high", "moderate", "low"]},
            "reviewed_at": {"type": "string"}, "reviewed_by": {"type": "string"},
        },
        "required": ["source", "extraction", "evidence_confidence"], "additionalProperties": False,
    }
    biomarker_item = {"type": "object", "properties": {
        "id": {"type": "string"}, "biomarker": {"type": "string"}, "family": {"enum": BIOMARKER_FAMILIES},
        "rule": {"enum": ["required", "enriched", "stratified", "defines_arm", "excluded", "analyzed", "none"]},
        "timing": {"enum": ["baseline", "emergent", "at_progression"]}, "assay": {"type": "string"},
        "cutoff": {"type": "string"}, "sample": {"type": "string"}, "note": {"type": "string"}},
        "required": ["id", "family", "rule"], "additionalProperties": False}
    grupo_braço = {"type": "object", "properties": {"factor": {"type": "string"}, "level": {"type": "string"}},
                   "required": ["factor", "level"], "additionalProperties": False}
    safety_item = {"type": "object", "properties": {
        "arm_id": {"type": "string"}, "arm_group": grupo_braço, "term": {"type": "string"},
        "scope": {"enum": ["any", "g1", "g2", "g1_2", "g2plus", "g3", "g3_4", "g3plus", "g4", "g4plus", "g5",
                           "serious", "unspecified"]},
        "analysis_ref": {"type": "string"}, "conflict_ref": {"type": "string"},
        "value": {"$ref": "#/$defs/qualified"}, "label": {"type": "string"}, "organ": {"type": "string"},
        "reported_term": {"type": "string"}, "term_mapping": {"enum": ["exact", "broader", "narrower", "related"]},
        "attribution_method": {"enum": ["investigator", "adjudicated", "sponsor", "unspecified"]},
        "subtype": {"type": "string"}, "timing": {"enum": ["acute", "late", "any"]},
        "denominator": {"type": "integer"}, "comparison_id": {"type": "string"},
        "conflict": {"enum": ["none", "explained", "within_source_conflict", "cross_source_conflict"]},
        "value_candidates": {"type": "array"}, "prov": {"type": "string"},
        "n": {"type": "integer"}, "n_events": {"type": "integer"}, "type": {"enum": ["reduction", "interruption"]},
        "attribution": {"enum": ["any", "treatment_related", "unspecified"]}, "attribution_agent": {"type": "string"},
        "aesi_of": {"type": "array", "items": {"enum": MODULES}}, "adjudicated": {"type": "boolean"},
        "treatment_phase": {"type": "string"}, "grading_system": {"type": "string"},
        "causes": {"type": "array", "items": {"type": "string"}}, "irreversible": {"type": "boolean"},
        "state": {"enum": ["not_reported", "unknown", "not_yet_available"]}, "expected": {"type": "string"},
        "checked_sources": {"type": "array", "items": {"type": "string"}},
        "note": {"type": "string"}}, "additionalProperties": False}
    subgroup_item = {"type": "object", "properties": {
        "id": {"type": "string"}, "dimension": {"type": "string"},
        "family": {"enum": BIOMARKER_FAMILIES + ["clinical"]}, "biomarker_ref": {"type": "string"},
        "cohort_id": {"type": "string"}, "level": {"type": "string"},
        "levels": {"type": "array", "items": {"type": "string"}},
        "endpoint_ref": {"type": "string"}, "endpoint_refs": {"type": "array", "items": {"type": "string"}},
        "comparison_id": {"type": "string"}, "effect": {"type": "object"},
        "arms_values": {"type": "array"}, "prespecified": {"type": "boolean"}, "prov": {"type": "string"},
        "finding": {"type": "string", "minLength": 1}, "interaction_p": {"type": "string"}, "note": {"type": "string"}},
        "required": ["dimension"], "additionalProperties": False,
        "anyOf": [{"required": ["effect"]}, {"required": ["arms_values"]}, {"required": ["finding"]}]}
    cohort_item = {"type": "object", "properties": {
        "cohort_id": {"type": "string"}, "kind": {"enum": ["enrollment", "analysis_population", "part"]},
        "label": {"type": "string"}, "source_cohorts": {"type": "array", "items": {"type": "string"}},
        "biomarker_ref": {"type": "string"}, "setting": {"type": "string"}, "n": {"type": "integer"},
        "status": {"enum": ["active", "completed", "closed_early"]}, "parent_cohort": {"type": "string"}},
        "required": ["cohort_id", "kind"], "additionalProperties": False}
    multiplicity = {"type": "object", "properties": {"families": {"type": "array", "items": {
        "type": "object", "properties": {
            "family_id": {"type": "string"}, "overall_alpha": {"type": "number"},
            "alpha_sided": {"enum": [1, 2]}, "rollover": {"type": "boolean"}, "note": {"type": "string"},
            "procedure": {"enum": TESTING_PROCEDURES},
            "members": {"type": "array", "minItems": 1, "items": {"type": "object", "properties": {
                "endpoint_id": {"type": "string"}, "alpha": {"type": "number"}, "order": {"type": "integer"}},
                "required": ["endpoint_id"], "additionalProperties": False}}},
        "required": ["family_id", "procedure", "members"], "additionalProperties": False}}},
        "required": ["families"], "additionalProperties": False}
    tipado = {
        "design.arms": {"type": "array", "items": {"$ref": "#/$defs/arm"}},
        "design.comparisons": {"type": "array", "items": {"$ref": "#/$defs/comparison"}},
        "design.cohorts": {"type": "array", "items": cohort_item},
        "design.multiplicity": multiplicity,
        "population.biomarker_selection": {"type": "array", "items": biomarker_item},
        **{p: {"type": "array", "items": safety_item} for p in (
            "safety.grade3plus_any", "safety.serious_ae", "safety.discontinuation_ae", "safety.dose_modification",
            "safety.treatment_related_deaths", "safety.key_toxicities", "safety.late_effects")},
    }

    def prop(path):
        if path in tipado:
            return {"allOf": [{"$ref": "#/$defs/envelope"}], "properties": {"v": tipado[path]}}
        return {"$ref": "#/$defs/envelope"}

    block = lambda paths: {"type": "object",
                           "properties": {p.split(".", 1)[1]: prop(p) for p in paths},
                           "additionalProperties": False}
    grupos = {}
    for p in CORE_PATHS:
        if "." in p:
            grupos.setdefault(p.split(".")[0], []).append(p)
    props = {
        "schema": {"const": f"theratrials-db-v2/{VERSAO}"},
        "uid": {"type": "string", "minLength": 1},
        "record_type": {"enum": RECORD_TYPES},
        "curation": {"type": "object", "properties": {
            "level": {"enum": CURATION_LEVELS}, "lifted_at": {"type": "string"},
            "source_sha256": {"type": "string"}, "curated_at": {"type": "string"}, "curated_by": {"type": "string"},
            "record_type_basis": {"type": "object"},
            "uncertainty": {"type": "array", "items": {"type": "object"}},
            "suggestions": {"type": "array", "items": {"type": "object"}},
            "legacy_projection": {"type": "object", "additionalProperties": {"type": "string"}},
        }, "required": ["level"], "additionalProperties": False},
        "external_relationships": {"type": "array", "items": {"type": "object", "properties": {
            "registry": {"enum": list(EXTERNAL_REGISTRIES)}, "registry_id": {"type": "string", "minLength": 3},
            "relationship": {"enum": EXTERNAL_RELATIONS}, "url": {"type": "string"}, "label": {"type": "string"}},
            "required": ["registry", "registry_id", "relationship"], "additionalProperties": False}},
        "relationships": {"type": "object", "properties": {
            "parent_uid": {"type": ["string", "null"]},
            "child_uids": {"type": "array", "items": {"type": "string"}},
            "links": {"type": "array", "items": {"type": "object", "properties": {
                "type": {"enum": REL_LINKS}, "target_uid": {"type": "string"}}, "required": ["type", "target_uid"],
                "additionalProperties": False}},
        }, "additionalProperties": False},
        "modules": {"type": "array", "items": {"$ref": "#/$defs/module_entry"}},
        "endpoints": {"allOf": [{"$ref": "#/$defs/envelope"}],
                      "properties": {"v": {"type": "array", "items": {"$ref": "#/$defs/endpoint"}}}},
        "subgroups": {"allOf": [{"$ref": "#/$defs/envelope"}],
                      "properties": {"v": {"type": "array", "items": subgroup_item}}},
        "analyses": {"type": "array", "items": {"type": "object", "properties": {
            "analysis_id": {"type": "string"}, "signature": {"type": "object"},
            "analysis_type": {"type": "string"}, "data_cutoff": {"type": "string"},
            "publication_role": {"enum": ANALYSIS_SIGNATURE["publication_role"]},
            "prov": {"type": "string"}}, "required": ["analysis_id", "signature"], "additionalProperties": False}},
        "review": {"type": "object", "properties": {
            "editorial_status": {"enum": ["active", "in_review", "withheld"]},
            "integrity": {"type": "object", "properties": {"status": {"enum": INTEGRITY},
                                                           "reason": {"type": "string"},
                                                           "decision_ref": {"type": "string"}},
                          "required": ["status"], "additionalProperties": False},
            "last_reviewed": {"type": "string"},
            "corrections": {"type": "array", "items": {"type": "object"}},
        }, "required": ["editorial_status", "integrity"], "additionalProperties": False},
        "provenance": {"type": "object", "additionalProperties": {"$ref": "#/$defs/provenance"}},
        "legacy": {"type": "object", "properties": {"v1": {"type": "object"}, "position": {"type": "integer"}},
                   "required": ["v1", "position"], "additionalProperties": False},
    }
    for g, paths in grupos.items():
        props[g] = block(paths)
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"https://theratrials.com/schema/db-v2/{VERSAO}/record.json",
        "title": "TheraTrials Database v2 — registro canônico de um card",
        "type": "object",
        "properties": props,
        "required": ["schema", "uid", "record_type", "curation", "relationships", "modules", "review",
                     "provenance", "legacy"],
        "additionalProperties": False,
        "$defs": {"envelope": envelope, "qualified": qualified, "ci": ci, "endpoint": endpoint,
                  "intervention": intervention, "arm": arm, "comparison": comparison,
                  "module_entry": module_entry, "provenance": provenance, "publication": publication,
                  "derivation": {"type": "object", "properties": {
                      "formula": {"type": "string"}, "parameters": {"type": "object"},
                      "assumptions": {"type": "array", "items": {"type": "string"}, "minItems": 1},
                      "source_fields": {"type": "array", "items": {"type": "string"}, "minItems": 1},
                      "version": {"type": "string"}},
                      "required": ["formula", "assumptions", "source_fields", "version"], "additionalProperties": False}},
    }


def registry() -> dict:
    return {
        "schema": f"theratrials-db-v2-registry/{VERSAO}",
        "status": "fundação — nenhum card migrado",
        "record_types": RECORD_TYPES, "states": STATES, "enums": ENUMS, "endpoint_codes": ENDPOINT_CODES,
        "endpoint_synonyms": ENDPOINT_SYNONYMS, "origins": ORIGINS, "curation_levels": CURATION_LEVELS,
        "modules": MODULES, "module_roles": ROLES, "arm_roles": ARM_ROLES,
        "intervention_roles": INTERVENTION_ROLES, "intervention_phases": INTERVENTION_PHASES,
        "biomarker_families": BIOMARKER_FAMILIES,
        "core": CORE, "profiles": PROFILES, "single_arm_not_applicable": SINGLE_ARM_NA,
        "single_arm_optional": SINGLE_ARM_OPTIONAL,
        "module_fields": MODULE_FIELDS,
        "endpoint_model": ENDPOINT_MODEL, "multiplicity_model": MULTIPLICITY_MODEL,
        "analysis_signature": ANALYSIS_SIGNATURE, "relationships": RELATIONSHIPS,
        "external_registries": EXTERNAL_REGISTRIES, "external_relations": EXTERNAL_RELATIONS,
        "validation_errors": VALIDATION_ERRORS,
        "role_semantics": {
            "tested": "o módulo é a pergunta do estudo naquele(s) braço(s)",
            "backbone": "presente como base comum (em geral nos dois braços); não é a pergunta",
            "control": "presente só como comparador",
            "context": "não há agente administrado desse módulo; só campos de população (ex.: exposição prévia)",
        },
    }


def main():
    (AQUI / "registry_v2.json").write_text(json.dumps(registry(), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (AQUI / "schema_record_v2.json").write_text(json.dumps(json_schema(), ensure_ascii=False, indent=1) + "\n",
                                                encoding="utf-8")
    nf = sum(len(m["fields"]) for m in MODULE_FIELDS.values())
    na = sum(len(m["aesi"]) for m in MODULE_FIELDS.values())
    print(f"registry {VERSAO}: {len(CORE)} campos core, {len(MODULE_FIELDS)} módulos, {nf} campos de módulo, "
          f"{na} termos de AESI, {len(PROFILES)} perfis")


if __name__ == "__main__":
    main()
