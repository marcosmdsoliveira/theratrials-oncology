"""deterministic — itens de proposta gerados SEM LLM, a partir de fatos estruturados e de regras de cobertura.

"Silêncio não é resultado": o que as regras abaixo detectam entra na proposta do card como item explícito
(origin=deterministic), com evidência literal quando existe, e segue pelo mesmo verificador e classificador.

  ANO_PUB_MISMATCH          ano_pub ≠ ano da publicação representada (metadado PubMed)          → P3 bibliográfico
  STATUS_PUBLISHED          status 'Apresentado' com artigo publicado validado                 → P3 freshness
  MASKING_CROSS_SOURCE      mascaramento do registro × da publicação                            → CONFLICT, sem escolha
  BACKLOG_UNADDRESSED       item aberto/confirmado do backlog que o curator não tratou         → encaminhado (P2)
  SUMMARY_FIELD_REVIEW      update/follow-up no primario/secundario sem revisar resultado_chave → lembrete (WATCH)
  PRESENTED_UNSOURCED       'Apresentado' com número de resultado e sem publicação no pacote   → REVIEW
Nenhuma regra conhece estudo; todas leem só o pacote e a proposta.
"""
from __future__ import annotations

import re

try:
    from . import sources as S
except ImportError:
    import sources as S

# afirmação EXPLÍCITA de mascaramento no card ("placebo" sozinho não conta)
TERMOS_MASCARAMENTO = re.compile(r"\babert[oa]\b|open[- ]label|\bcego\b|duplo[- ]cego|blind|mascar|\bmask", re.I)


def _par(pasta, fonte: dict, padrao: str):
    for num, t in S.ler_paragrafos(pasta / fonte["path"]).items():
        if re.search(padrao, t, re.I):
            return num, re.sub(r"^\[[^\]]*\]\s*", "", t)
    return None, None


def _ev(fonte: dict, num: str, texto: str) -> dict:
    return {"source_id": fonte["source_id"], "source_type": fonte["source_type"], "locator": f"¶{num}",
            "snippet": texto, "retrieved_at": fonte.get("retrieved_at")}


def itens(pacote: dict, proposta: dict, pasta) -> list[dict]:
    fontes = {f["source_id"]: f for f in pacote.get("sources", [])}
    card = pacote.get("card", {})
    out, n = [], 0

    def novo(**kw):
        nonlocal n
        n += 1
        base = {"proposal_id": f"D{n}", "origin": "deterministic", "value_origin": "reported", "evidence": [],
                "reason": kw.pop("reason"), "analysis_signature_ref": None}
        base.update(kw)
        out.append(base)

    for a in pacote.get("deterministic_findings", []):
        if a["code"] == "ANO_PUB_MISMATCH" and a.get("source_id") in fontes:
            num, txt = _par(pasta, fontes[a["source_id"]], r"^\[PubDate\]")
            if num:
                novo(field="ano_pub", current_value=card.get("ano_pub"), proposed_value=a["proposed"],
                     change_kind="replace", proposal_type="BIBLIOGRAPHIC_FIX", defect="bibliographic_format",
                     evidence=[_ev(fontes[a["source_id"]], num, txt)], reason=a["detail"],
                     _det_priority="P3", _det_reason="ano_pub diverge da publicação representada")
        elif a["code"] == "FRESHNESS_PRESENTED_BUT_PUBLISHED":
            meta = next((f for f in fontes.values() if f["source_type"] == "pubmed_metadata"), None)
            num, txt = _par(pasta, meta, r"^\[PublicationType\]") if meta else (None, None)
            if num:
                novo(field="status", current_value=card.get("status"), proposed_value="Publicado",
                     change_kind="replace", proposal_type="EDITORIAL_ONLY", defect="stale_status",
                     evidence=[_ev(meta, num, txt)], reason=a["detail"],
                     _det_priority="P3", _det_reason="freshness: artigo publicado disponível, sem mudança clínica")
        elif a["code"] == "MASKING_CROSS_SOURCE":
            reg = fontes.get(f"nct:{a['registry']}:registry")
            pub = fontes.get(a["pub_source"])
            if reg and pub:
                nr, tr = _par(pasta, reg, r"maskingInfo\.masking\]")
                tp = re.sub(r"^\[[^\]]*\]\s*", "", S.ler_paragrafos(pasta / pub["path"]).get(a["pub_par"], ""))
                if nr and tp:
                    toca = bool(TERMOS_MASCARAMENTO.search(str(card.get("desenho") or "")))
                    novo(field="desenho", current_value=card.get("desenho"), proposed_value=None, change_kind="none",
                         proposal_type="INTEGRITY_FIX", defect="cross_source_conflict",
                         evidence=[_ev(reg, nr, tr), _ev(pub, a["pub_par"], tp)],
                         conflict={"description": a["detail"],
                                   "candidates": [{"value": f"registro: {a['masking']}", "evidence_index": 0},
                                                  {"value": f"publicação: {a['pub_match']}", "evidence_index": 1}]},
                         reason=a["detail"],
                         _det_priority="P0" if toca else "P2",
                         _det_reason=("o card afirma o mascaramento e as fontes divergem: valor publicado inseguro"
                                      if toca else "fontes divergem sobre mascaramento; o card não o afirma"))
    tratados = {it["field"] for it in proposta.get("proposals") or []} | set(proposta.get("no_action_fields") or [])
    tratados |= {it["field"] for it in out}
    for b in pacote.get("backlog", []):
        if b.get("status") in ("open", "confirmed") and not set(b.get("affected_fields") or []) & tratados:
            novo(field=(b.get("affected_fields") or ["?"])[0], current_value=card.get((b.get("affected_fields") or [""])[0]),
                 proposed_value=None, change_kind="none", proposal_type="WATCH", defect="unsupported_claim",
                 reason=f"item do backlog {b['id']} não tratado pelo curator: {b.get('description', '')[:160]}",
                 _det_priority="P2", _det_reason=f"backlog {b['id']} encaminhado (sem silêncio)")
    atualiza = [it for it in proposta.get("proposals") or [] if it.get("field") in ("primario", "secundario")
                and (it.get("proposal_type") in ("SAME_ANALYSIS_UPDATE", "LONG_TERM_FOLLOWUP")
                     or it.get("defect") in ("newer_data_same_analysis", "numeric_contradiction"))]
    # no_action do curator NÃO dispensa o campo-resumo: dado novo no primario/secundario muda a base do resumo
    propostos = {it["field"] for it in proposta.get("proposals") or []} | {it["field"] for it in out}
    if atualiza and "resultado_chave" not in propostos and card.get("resultado_chave") not in (None, "", "—"):
        novo(field="resultado_chave", current_value=card.get("resultado_chave"), proposed_value=None,
             change_kind="none", proposal_type="SAME_ANALYSIS_UPDATE", defect="newer_data_same_analysis",
             reason="lembrete: primario/secundario mudam; conferir se o resumo resultado_chave acompanha",
             _det_priority="P2", _det_reason="lembrete de campo-resumo (WATCH), nunca P1 sozinho",
             _automation="WATCH",
             _depends_on=[it["proposal_id"] for it in atualiza])   # só vale se alguma delas passar no verifier
    # card 'Apresentado' com número de resultado e nenhuma publicação no pacote: REVIEW, sem tentar corrigir
    niveis = {f.get("text_level") for f in fontes.values()}
    if "apresent" in str(card.get("status") or "").lower() and not niveis & {"abstract", "fulltext"}:
        com_numero = [c for c in ("primario", "resultado_chave", "secundario", "tox_g3")
                      if re.search(r"\d", str(card.get(c) or ""))]
        if com_numero:
            novo(field=com_numero[0], current_value=card.get(com_numero[0]), proposed_value=None, change_kind="none",
                 proposal_type="WATCH", defect="unsupported_claim",
                 reason=f"card 'Apresentado' com números de resultado em {', '.join(com_numero)} e nenhuma publicação "
                        "no pacote: conferência humana da fonte, sem correção automática",
                 _det_priority="P1", _det_reason="resultado sem fonte no pacote (Apresentado)", _automation="REVIEW")
    return out
