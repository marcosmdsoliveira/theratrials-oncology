"""priority — classificador DETERMINÍSTICO da prioridade final, depois do curator e do verifier.

O curator não escolhe prioridade (a dele é só sugestão, ignorada). A prioridade final sai de fatos verificados:
o defeito declarado, o veredito final do item, o estado do valor ATUAL segundo o verifier (contradito pela fonte?),
a política do campo e as decisões humanas.

  P0 integridade  — só com o valor publicado VERIFICADAMENTE contradito (current_value_status=CONTRADICTED) e defeito
                    de integridade no campo em que ele importa (CAMPOS_P0): identidade/publicação em qualquer campo;
                    braço, desfecho, denominador, direção/significância e número contradito só em campo de resultado
                    ou segurança; toxicidade mal atribuída só em campo de toxicidade/resumo. Ou CONFLICT factual em
                    campo de resultado/segurança, ou dentro da mesma fonte em campo clínico (valor inseguro).
                    Conflito entre fontes em campo de detalhe (esquema, critérios…) é P1;
  P1 atualização  — dado mais maduro da mesma análise em campo de resultado, erro verificado fora de campo de
                    resultado, afirmação clínica sem lastro;
  P2 contexto     — secundária, subgrupo, nova coorte, watch, UNSUPPORTED, campo human-only, pedido de revisão de
                    decisão humana;
  P3 editorial    — bibliografia, formatação, status 'Apresentado'→publicado sem mudança clínica.
Regras duras: freshness sozinho nunca dá P0; decisão humana tem precedência (campo protegido nunca vira P0/P1
automático); FAIL sai da fila (log de qualidade do curator), EXCETO se o valor atual de campo clínico foi
verificado como contradito (P1) ou se o item declarava conflito (P2): FAIL da proposta não apaga o problema.
Orçamento semanal humano: só P0 e P1. P2/P3 vão para um resumo periódico, fora do orçamento por padrão.
"""
from __future__ import annotations

try:
    from . import agent_types as T, sufficiency as SF
except ImportError:
    import agent_types as T
    import sufficiency as SF

ORDEM = {"P0": 0, "P1": 1, "P2": 2, "P3": 3, None: 9}
ORCAMENTO = {"P0", "P1"}
# campos em que o card afirma resultado, comparação ou segurança: só aqui um erro verificado de braço, desfecho,
# denominador, direção/significância ou número vira P0. Fora deles, o mesmo defeito confirmado é P1 (clínico) ou P3.
CAMPOS_RESULTADO = {"primario", "secundario", "resultado_chave", "takehome", "tox_g3", "tox_interesse", "comparador",
                    "estatistica", "analises", "subgrupo", "desenho", "n"}
CAMPOS_P0 = {
    "identifier_mismatch": None, "represented_publication_wrong": None,           # None = qualquer campo
    "human_decision_or_quarantine_violation": None,
    "safety_misattribution": {"tox_g3", "tox_interesse", "resultado_chave", "takehome"},
    **{d: CAMPOS_RESULTADO for d in ("arm_role_inverted", "arm_attribution", "endpoint_wrong", "denominator_wrong",
                                     "significance_or_direction", "numeric_contradiction")},
}


def _p0_elegivel(defeito: str, campo: str) -> bool:
    campos = CAMPOS_P0.get(defeito, set())
    return campos is None or campo in campos


def classificar(item: dict, veredito: str, cvs: str | None, pacote: dict) -> tuple[str | None, str]:
    """(prioridade final | None = fora da fila, motivo)."""
    campo = item.get("field", "")
    defeito = item.get("defect")
    tipo = item.get("proposal_type")
    clinico = campo in SF.CAMPOS_CLINICOS
    freshness = any(a.get("code") == "FRESHNESS_PRESENTED_BUT_PUBLISHED" for a in pacote.get("deterministic_findings", []))
    if item.get("origin") == "deterministic":
        return item.get("_det_priority", "P3"), item.get("_det_reason", "item determinístico")
    if campo in set(pacote.get("human_decision_protected_fields") or []):
        return "P2", "campo definido por decisão humana registrada: pedido de revisão, nunca correção automática"
    if SF.classe(campo) == "human":
        return "P2", "campo human-only nesta fase: WATCH"
    if veredito == "FAIL":
        # a proposta caiu, mas o que ela apontava pode continuar de pé: nada some em silêncio
        if cvs == "CONTRADICTED" and clinico:
            return "P1", "proposta rejeitada (FAIL), mas o verifier confirma o valor ATUAL contradito: reescrita humana"
        if item.get("conflict"):
            return "P2", "conflito declarado contestado pelo verifier: fica visível, sem escolha automática"
        return None, "FAIL no verifier: sai da fila (log de qualidade do curator)"
    if veredito == "UNSUPPORTED":
        return "P2", "UNSUPPORTED: WATCH, sem alteração factual"
    if veredito == "CONFLICT":
        if campo in CAMPOS_RESULTADO or (clinico and defeito == "within_source_conflict"):
            return "P0", "conflito factual em campo de resultado/segurança (ou na própria fonte): valor publicado inseguro"
        if clinico:
            return "P1", "conflito entre fontes em campo de detalhe (ex.: registro × publicação): adjudicação humana"
        return "P2", "conflito em campo não clínico"
    # PASS
    if defeito == "stale_status" or (freshness and campo == "status"):
        return "P3", "status/freshness sem mudança clínica"
    if defeito in T.P0_DEFECTS:
        if cvs == "CONTRADICTED":
            if tipo == "BIBLIOGRAPHIC_FIX" and defeito not in ("identifier_mismatch", "represented_publication_wrong"):
                return "P3", "bibliográfico sem erro de identidade"
            if _p0_elegivel(defeito, campo):
                return "P0", f"valor publicado contradito pela fonte ({defeito})"
            return ("P1" if clinico else "P3"), f"erro verificado ({defeito}) fora de campo de resultado/segurança"
        if cvs == "SUPPORTED":
            return ("P2" if clinico else "P3"), "defeito alegado, mas o verifier achou o valor atual sustentado"
        return ("P1" if clinico else "P3"), "defeito de integridade não confirmado como contradição do valor atual"
    if tipo in ("SAME_ANALYSIS_UPDATE", "LONG_TERM_FOLLOWUP") or defeito == "newer_data_same_analysis":
        if campo in CAMPOS_RESULTADO:
            return "P1", "dado mais maduro da mesma análise"
        return "P2", "atualização fora de campo de resultado: contexto"
    if tipo in ("SECONDARY_ANALYSIS", "SUBGROUP", "NEW_COHORT", "WATCH", "NEW_PUBLICATION_RELATIONSHIP"):
        return "P2", f"{tipo}: material contextual"
    if tipo in ("BIBLIOGRAPHIC_FIX", "EDITORIAL_ONLY") or defeito in ("bibliographic_format", "editorial"):
        return "P3", "bibliográfico/editorial"
    if defeito == "unsupported_claim" and cvs == "CONTRADICTED" and clinico:
        return "P1", "afirmação clínica sem lastro na fonte"
    return ("P2" if clinico else "P3"), "enriquecimento/imprecisão sem contradição verificada"


def do_card(prioridades: list[str | None]) -> str | None:
    ps = [p for p in prioridades if p]
    return min(ps, key=lambda p: ORDEM[p]) if ps else None
