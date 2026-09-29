"""agent_types — vocabulário, assinatura de análise e schemas do sistema database-curator / database-verifier.

MODO SOMBRA: nada neste pacote escreve em assets/js/data.js, app-data/ ou frontend. Não existe caminho de apply.

    python3 scripts/db_v2/agents/agent_types.py     # regrava agents/schemas/*.json a partir deste arquivo

Fonte única: os schemas JSON versionados em agents/schemas/ são gerados daqui (test_agentes confere a sincronia).
"""
from __future__ import annotations

import json
import pathlib

AQUI = pathlib.Path(__file__).resolve().parent
SCHEMAS = AQUI / "schemas"
VERSAO = "1"

# ── classificação da proposta (por card e por campo) ──────────────────────────────────────────────────────────
PROPOSAL_TYPES = ["INTEGRITY_FIX", "SAME_ANALYSIS_UPDATE", "LONG_TERM_FOLLOWUP", "SECONDARY_ANALYSIS", "SUBGROUP",
                  "NEW_COHORT", "NEW_PUBLICATION_RELATIONSHIP", "BIBLIOGRAPHIC_FIX", "EDITORIAL_ONLY", "WATCH",
                  "NO_ACTION"]
# P0 integridade · P1 atualização clínica material · P2 secundário/watch · P3 bibliográfico/editorial
PRIORITY_OF_TYPE = {"INTEGRITY_FIX": "P0", "SAME_ANALYSIS_UPDATE": "P1", "LONG_TERM_FOLLOWUP": "P1",
                    "NEW_COHORT": "P1", "SECONDARY_ANALYSIS": "P2", "SUBGROUP": "P2",
                    "NEW_PUBLICATION_RELATIONSHIP": "P2", "WATCH": "P2", "BIBLIOGRAPHIC_FIX": "P3",
                    "EDITORIAL_ONLY": "P3", "NO_ACTION": None}
PRIORITIES = ["P0", "P1", "P2", "P3"]
# a prioridade FINAL não é do curator: priority.py a calcula do defeito declarado, do veredito e do estado do valor atual
# (o `priority` do curator vira só sugestão, guardada e ignorada)

# defeito que o curator declara em cada item (fato estruturado, não opinião) — o verifier confere
DEFECTS = ["identifier_mismatch", "represented_publication_wrong", "arm_role_inverted", "arm_attribution",
           "endpoint_wrong", "denominator_wrong", "safety_misattribution", "significance_or_direction",
           "numeric_contradiction", "human_decision_or_quarantine_violation",          # ↑ candidatos a P0
           "unsupported_claim", "imprecision", "newer_data_same_analysis", "enrichment", "stale_status",
           "bibliographic_format", "editorial", "within_source_conflict", "cross_source_conflict"]
P0_DEFECTS = set(DEFECTS[:10])
CURRENT_VALUE_STATUS = ["CONTRADICTED", "SUPPORTED", "NOT_ADDRESSED", "UNSUPPORTED"]
SUPPORT_LEVELS = ["explicit", "partial", "inferred", "none"]
ORIGINS = ["curator", "deterministic"]

VERDICTS = ["PASS", "FAIL", "UNSUPPORTED", "CONFLICT"]
VALUE_ORIGIN = ["reported", "derived", "editorial"]
CHANGE_KINDS = ["replace", "append", "remove", "none"]
EDITORIAL_IMPACT = ["high", "moderate", "low", "none"]

# fontes aceitas como verdade do Database (as proibidas nunca entram num pacote de evidência)
SOURCE_TYPES = ["pubmed_metadata", "pubmed_abstract", "pmc_fulltext", "europepmc_fulltext", "ctgov_record",
                "ctgov_results", "crossref_metadata", "registered_primary_source", "human_decision"]
FORBIDDEN_SOURCES = ["tracker.json", "explorer", "secondary_snippet", "model_memory", "card_v1_text"]

# ── confiança por domínio (nunca um escore global) ───────────────────────────────────────────────────────────
DOMAINS = {
    "identity": ["machine_verified", "conflict", "unverified"],
    "bibliographic_metadata": ["machine_verified", "blocked_by_backlog", "unverified", "not_applicable"],
    "publication_relationship": ["verified", "human_decision", "undetermined", "conflict"],
    "clinical_extraction": ["verifier_pass", "verifier_partial", "verifier_fail", "not_applicable", "withheld"],
    "published_write": ["human_required"],          # nesta fase, SEMPRE humano; nenhum domínio autoriza escrita
}

# ── analysis_signature (completa) ─────────────────────────────────────────────────────────────────────────────
# identidade da análise: duas medidas só são "a mesma análise" se TODOS estes campos coincidem
SIGNATURE_IDENTITY = ["trial_key", "registry_ids", "cohort", "population", "disease_state", "treatment_line",
                      "arms", "analysis_set", "endpoint", "endpoint_hierarchy", "summary_measure", "comparison",
                      "timepoint", "assessment_method"]
# ordenação/maturidade: distinguem atualização, follow-up longo e análise final da MESMA análise
SIGNATURE_MATURITY = ["sample_size", "data_cutoff", "follow_up_median_months", "analysis_type", "publication_role"]
SIGNATURE_FIELDS = SIGNATURE_IDENTITY + SIGNATURE_MATURITY
ENDPOINT_HIERARCHY = ["primary", "co_primary", "key_secondary", "secondary", "exploratory", "safety", "undetermined"]
ANALYSIS_TYPES = ["interim", "primary", "updated", "final", "long_term", "post_hoc", "undetermined"]
PUBLICATION_ROLES = ["primary_publication", "update", "final", "long_term", "secondary_analysis", "subgroup",
                     "qol_pro", "safety", "translational", "pooled", "correction", "congress_abstract",
                     "undetermined"]
RELATIONS = ["SAME_ANALYSIS", "SAME_ANALYSIS_UPDATE", "LONG_TERM_FOLLOWUP", "SECONDARY_ANALYSIS", "SUBGROUP",
             "NEW_COHORT", "DIFFERENT_STUDY", "UNDETERMINED"]


def _enum(v):
    return {"enum": v}


STR = {"type": "string"}
NSTR = {"type": ["string", "null"]}

SIGNATURE_SCHEMA = {
    "type": "object",
    "properties": {
        "signature_id": STR,
        "trial_key": NSTR, "registry_ids": {"type": "array", "items": STR},
        "cohort": NSTR, "population": NSTR, "disease_state": NSTR, "treatment_line": NSTR,
        "arms": {"type": "array", "items": {"type": "object", "properties": {
            "arm_id": STR, "label": STR, "role": _enum(["experimental", "control", "single_arm", "other"]),
            "n": {"type": ["integer", "null"]}}, "required": ["label", "role"]}},
        "analysis_set": NSTR, "endpoint": NSTR, "endpoint_hierarchy": _enum(ENDPOINT_HIERARCHY),
        "summary_measure": NSTR, "comparison": NSTR, "timepoint": NSTR, "assessment_method": NSTR,
        "sample_size": {"type": ["integer", "null"]}, "data_cutoff": NSTR,
        "follow_up_median_months": {"type": ["number", "null"]}, "analysis_type": _enum(ANALYSIS_TYPES),
        "publication_role": _enum(PUBLICATION_ROLES), "publication_id": NSTR,
    },
    "required": ["signature_id", "trial_key", "endpoint", "endpoint_hierarchy", "analysis_type", "publication_role"],
}

EVIDENCE_SCHEMA = {
    "type": "object",
    "properties": {
        "source_id": STR, "source_type": _enum(SOURCE_TYPES), "publication_id": NSTR, "pmid": NSTR, "doi": NSTR,
        "nct": NSTR, "locator": STR, "snippet": {"type": "string", "minLength": 8}, "retrieved_at": NSTR,
    },
    "required": ["source_id", "source_type", "locator", "snippet"],
}

DERIVATION_SCHEMA = {
    "type": "object",
    "properties": {
        "operands": {"type": "array", "minItems": 1, "items": {"type": "object", "properties": {
            "name": STR, "value": {"type": "number"}, "evidence_index": {"type": "integer"}},
            "required": ["name", "value", "evidence_index"]}},
        "rule": {"type": "string", "minLength": 3}, "result": {"type": "number"},
    },
    "required": ["operands", "rule", "result"],
}

PROPOSAL_ITEM_SCHEMA = {
    "type": "object",
    "properties": {
        "proposal_id": STR, "field": STR, "current_value": {}, "proposed_value": {},
        "change_kind": _enum(CHANGE_KINDS), "proposal_type": _enum(PROPOSAL_TYPES), "priority": _enum(PRIORITIES),
        "defect": _enum(DEFECTS), "origin": _enum(ORIGINS),
        "value_origin": _enum(VALUE_ORIGIN), "evidence": {"type": "array", "items": EVIDENCE_SCHEMA},
        "absence_checked_in": {"type": "array", "items": STR},
        "derivation": DERIVATION_SCHEMA, "analysis_signature_ref": NSTR,
        "conflict": {"type": "object", "properties": {
            "description": STR, "candidates": {"type": "array", "minItems": 2, "items": {"type": "object", "properties": {
                "value": {}, "evidence_index": {"type": "integer"}}, "required": ["value", "evidence_index"]}}},
            "required": ["description", "candidates"]},
        # campos só do curator — o verifier NÃO os recebe
        "reason": STR, "confidence": {"type": "object"}, "editorial_impact": _enum(EDITORIAL_IMPACT),
    },
    "required": ["proposal_id", "field", "current_value", "proposed_value", "change_kind", "proposal_type",
                 "defect", "value_origin", "evidence", "reason"],
}

PROPOSAL_SCHEMA = {
    "$id": f"theratrials-db-curator-proposal/{VERSAO}",
    "type": "object",
    "properties": {
        "schema": {"const": f"theratrials-db-curator-proposal/{VERSAO}"},
        "uid": STR, "packet_sha256": STR,
        "card_classification": {"type": "object", "properties": {
            "proposal_type": _enum(PROPOSAL_TYPES), "priority": {"enum": PRIORITIES + [None]}, "summary": STR},
            "required": ["proposal_type", "summary"]},
        "represented_publication": {"type": "object", "properties": {
            "publication_id": NSTR, "relation_to_primary": _enum(RELATIONS), "primary_publication_id": NSTR,
            "basis_evidence": {"type": "array", "items": EVIDENCE_SCHEMA}},
            "required": ["publication_id", "relation_to_primary"]},
        "analysis_signatures": {"type": "array", "items": SIGNATURE_SCHEMA},
        "proposals": {"type": "array", "items": PROPOSAL_ITEM_SCHEMA},
        "no_action_fields": {"type": "array", "items": STR},
        "watch": {"type": "array", "items": STR},
        "notes_for_human": STR,
    },
    "required": ["schema", "uid", "packet_sha256", "card_classification", "represented_publication",
                 "analysis_signatures", "proposals"],
}

# o que o verifier recebe de cada item (sem reason / confidence / editorial_impact do curator)
VERIFIER_VISIBLE = ["proposal_id", "field", "current_value", "proposed_value", "change_kind", "value_origin",
                    "defect", "evidence", "absence_checked_in", "derivation", "analysis_signature_ref", "conflict"]

VERIFICATION_SCHEMA = {
    "$id": f"theratrials-db-verifier-result/{VERSAO}",
    "type": "object",
    "properties": {
        "schema": {"const": f"theratrials-db-verifier-result/{VERSAO}"},
        "uid": STR, "proposal_sha256": STR,
        "relationship": {"type": "object", "properties": {
            "verdict": _enum(VERDICTS), "reason": STR,
            "evidence": {"type": "array", "items": EVIDENCE_SCHEMA}}, "required": ["verdict", "reason"]},
        "results": {"type": "array", "items": {"type": "object", "properties": {
            "proposal_id": STR, "field": STR, "verdict": _enum(VERDICTS),
            "current_value_status": _enum(CURRENT_VALUE_STATUS), "support": _enum(SUPPORT_LEVELS),
            "source_used": NSTR, "snippet": NSTR, "locator": NSTR, "analysis_signature_ref": NSTR,
            "reason": {"type": "string", "minLength": 5}},
            "required": ["proposal_id", "field", "verdict", "current_value_status", "support", "reason"]}},
    },
    "required": ["schema", "uid", "proposal_sha256", "results"],
}

# consenso do verifier duplo (só itens P0): dois contextos independentes, mesmo pacote, mesmas ferramentas
CONSENSUS_STATES = ["UNANIMOUS_PASS", "UNANIMOUS_FAIL", "UNANIMOUS_UNSUPPORTED", "UNANIMOUS_CONFLICT", "DISAGREEMENT",
                    "SINGLE_RUN"]          # SINGLE_RUN = segunda execução ainda não feita: também bloqueia aprovação

DECISION_PACKET_SCHEMA = {
    "$id": f"theratrials-db-decision-packet/{VERSAO}",
    "type": "object",
    "properties": {
        "schema": {"const": f"theratrials-db-decision-packet/{VERSAO}"},
        "uid": STR, "card": STR, "priority": {"enum": PRIORITIES + [None]}, "proposal_type": _enum(PROPOSAL_TYPES),
        "summary": STR,
        "fields": {"type": "array", "items": {"type": "object"}},
        "conflicts": {"type": "array"}, "sources": {"type": "array"},
        "clinical_impact": _enum(EDITORIAL_IMPACT),
        "verifier_summary": {"type": "object"},
        "domain_confidence": {"type": "object", "properties": {k: _enum(v) for k, v in DOMAINS.items()},
                              "required": list(DOMAINS)},
        "suggested_decision": _enum(["APPROVE", "REJECT", "DEFER", "WATCH", "NONE"]), "suggested_reason": STR,
        "human_required": {"type": "boolean"}, "counts_toward_weekly_budget": {"type": "boolean"},
        "verifier_consensus": {"type": "object", "additionalProperties": _enum(CONSENSUS_STATES)},
        "auto_approval_blocked": {"type": "boolean"},
        "final_decision": {"type": "null"},          # nunca preenchido por máquina
    },
    "required": ["schema", "uid", "priority", "proposal_type", "fields", "verifier_summary", "domain_confidence",
                 "suggested_decision", "human_required", "counts_toward_weekly_budget", "verifier_consensus",
                 "auto_approval_blocked", "final_decision"],
}


def schemas() -> dict[str, dict]:
    return {"proposal.schema.json": PROPOSAL_SCHEMA, "verification.schema.json": VERIFICATION_SCHEMA,
            "decision_packet.schema.json": DECISION_PACKET_SCHEMA,
            "analysis_signature.schema.json": {"$id": f"theratrials-db-analysis-signature/{VERSAO}",
                                               **SIGNATURE_SCHEMA}}


def main():
    SCHEMAS.mkdir(exist_ok=True)
    for nome, s in schemas().items():
        (SCHEMAS / nome).write_text(json.dumps(s, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(schemas())} schemas em {SCHEMAS}")


if __name__ == "__main__":
    main()
