"""signature — relação entre duas análises pela analysis_signature (determinístico).

Responde "esta publicação é a mesma análise atualizada, um follow-up longo, uma análise secundária, um subgrupo, outra
coorte ou outro estudo?" comparando os campos da assinatura — nunca pelo PMID ou ano mais recente.

Regra de ouro: campo necessário ausente → UNDETERMINED (vai para humano/verifier), nunca um palpite.
"""
from __future__ import annotations

import re
import unicodedata
from datetime import date

try:
    from . import agent_types as T
except ImportError:                      # execução direta dentro de agents/
    import agent_types as T

# campos que, divergindo, tornam a medida outra análise do mesmo estudo
_MEDIDA = ["endpoint", "summary_measure", "comparison", "timepoint", "assessment_method", "analysis_set", "arms"]
_PAPEIS_SECUNDARIOS = {"secondary_analysis", "qol_pro", "safety", "translational", "pooled"}
_PAPEIS_LONGOS = {"long_term", "final"}


def _norm(v):
    if v is None:
        return None
    if isinstance(v, list):
        return tuple(sorted(_norm(x) for x in v if x is not None))
    if isinstance(v, dict):
        return tuple(sorted((k, _norm(x)) for k, x in v.items() if k != "n"))   # n do braço é maturidade
    t = unicodedata.normalize("NFKD", str(v)).lower()
    return re.sub(r"[^a-z0-9<>=.%]+", " ", "".join(c for c in t if not unicodedata.combining(c))).strip() or None


def _ids(s: dict) -> set:
    ids = {_norm(x) for x in (s.get("registry_ids") or [])}
    if s.get("trial_key"):
        ids.add(_norm(s["trial_key"]))
    return {i for i in ids if i}


def _data(s: str | None):
    if not s:
        return None
    m = re.match(r"(\d{4})(?:-(\d{2}))?(?:-(\d{2}))?", s)
    return date(int(m.group(1)), int(m.group(2) or 6), int(m.group(3) or 15)) if m else None


def _diferente(a, b, campo) -> bool | None:
    """True/False quando os dois têm o campo; None quando falta em algum (indeterminado)."""
    va, vb = _norm(a.get(campo)), _norm(b.get(campo))
    if va is None or vb is None or va == () or vb == ():
        return None
    return va != vb


def relacao(atual: dict, candidata: dict) -> tuple[str, str]:
    """(relação, motivo) da análise `candidata` em relação à `atual` (a que o card representa hoje)."""
    ia, ib = _ids(atual), _ids(candidata)
    if not ia or not ib:
        return "UNDETERMINED", "identificador do estudo ausente numa das assinaturas"
    if not ia & ib:
        return "DIFFERENT_STUDY", f"registros sem interseção: {sorted(ia)} × {sorted(ib)}"
    d = _diferente(atual, candidata, "cohort")
    if d:
        return "NEW_COHORT", f"coorte {atual.get('cohort')!r} × {candidata.get('cohort')!r}"
    if d is None and (atual.get("cohort") or candidata.get("cohort")):
        return "UNDETERMINED", "coorte informada só numa das assinaturas"
    for campo in ("population", "disease_state", "treatment_line"):
        if _diferente(atual, candidata, campo):
            return "SUBGROUP", f"{campo} {atual.get(campo)!r} × {candidata.get(campo)!r}"
    if candidata.get("publication_role") == "subgroup":
        return "SUBGROUP", "publication_role=subgroup"
    difs = [c for c in _MEDIDA if _diferente(atual, candidata, c)]
    if difs:
        return "SECONDARY_ANALYSIS", "medida diferente: " + ", ".join(difs)
    if candidata.get("publication_role") in _PAPEIS_SECUNDARIOS or \
            candidata.get("endpoint_hierarchy") in ("exploratory",) and atual.get("endpoint_hierarchy") != "exploratory":
        return "SECONDARY_ANALYSIS", f"papel {candidata.get('publication_role')} / hierarquia {candidata.get('endpoint_hierarchy')}"
    faltam = [c for c in ("endpoint", "summary_measure", "comparison") if _norm(atual.get(c)) is None
              or _norm(candidata.get(c)) is None]
    if faltam:
        return "UNDETERMINED", "assinatura incompleta: " + ", ".join(faltam)
    # mesma análise: a maturidade decide entre repetição, atualização e follow-up longo
    ca, cb = _data(atual.get("data_cutoff")), _data(candidata.get("data_cutoff"))
    fa, fb = atual.get("follow_up_median_months"), candidata.get("follow_up_median_months")
    if ca and cb:
        if cb <= ca:
            return "SAME_ANALYSIS", "mesmo corte ou corte anterior: não é atualização"
        longo = (cb - ca).days >= 365 or candidata.get("analysis_type") in ("long_term", "final") or \
            candidata.get("publication_role") in _PAPEIS_LONGOS
        return ("LONG_TERM_FOLLOWUP" if longo else "SAME_ANALYSIS_UPDATE"), f"corte {ca} → {cb}"
    if fa is not None and fb is not None:
        if fb <= fa:
            return "SAME_ANALYSIS", "seguimento igual ou menor"
        return ("LONG_TERM_FOLLOWUP" if fb - fa >= 12 else "SAME_ANALYSIS_UPDATE"), f"seguimento {fa} → {fb} meses"
    if candidata.get("publication_role") in _PAPEIS_LONGOS:
        return "LONG_TERM_FOLLOWUP", "papel declarado long_term/final (sem data de corte)"
    return "UNDETERMINED", "sem data de corte nem seguimento comparáveis"


TIPO_DA_RELACAO = {"SAME_ANALYSIS_UPDATE": "SAME_ANALYSIS_UPDATE", "LONG_TERM_FOLLOWUP": "LONG_TERM_FOLLOWUP",
                   "SECONDARY_ANALYSIS": "SECONDARY_ANALYSIS", "SUBGROUP": "SUBGROUP", "NEW_COHORT": "NEW_COHORT",
                   "SAME_ANALYSIS": "NO_ACTION", "DIFFERENT_STUDY": "NO_ACTION", "UNDETERMINED": "WATCH"}

# só estas relações podem substituir valores da análise principal do card; as demais viram campo próprio/watch
PODE_SUBSTITUIR = {"SAME_ANALYSIS_UPDATE", "LONG_TERM_FOLLOWUP"}


def validar(s: dict) -> list[str]:
    e = [f"falta {k}" for k in T.SIGNATURE_SCHEMA["required"] if s.get(k) in (None, "")]
    if s.get("endpoint_hierarchy") and s["endpoint_hierarchy"] not in T.ENDPOINT_HIERARCHY:
        e.append(f"endpoint_hierarchy {s['endpoint_hierarchy']!r}")
    if s.get("analysis_type") and s["analysis_type"] not in T.ANALYSIS_TYPES:
        e.append(f"analysis_type {s['analysis_type']!r}")
    if s.get("publication_role") and s["publication_role"] not in T.PUBLICATION_ROLES:
        e.append(f"publication_role {s['publication_role']!r}")
    papeis = [a.get("role") for a in s.get("arms") or []]
    if "experimental" in papeis and "control" not in papeis and len(papeis) > 1:
        e.append("braços com experimental sem controle declarado")
    return e


TIPOS_UPDATE = {"SAME_ANALYSIS_UPDATE", "LONG_TERM_FOLLOWUP"}


def update_compativel(item: dict, proposta: dict) -> tuple[bool, str]:
    """Um update só é aceito como update se a assinatura do dado novo é compatível com a da análise do card em
    trial, população, coorte, conjunto de análise, braços/comparação e desfecho. Qualquer divergência OU dúvida
    (campo ausente, assinatura não distinta) → False: vai para REVIEW, nunca como update automático."""
    sigs = {s.get("signature_id"): s for s in proposta.get("analysis_signatures") or []}
    nova = sigs.get(item.get("analysis_signature_ref"))
    rep = (proposta.get("represented_publication") or {}).get("publication_id")
    base = [s for s in sigs.values() if s is not nova and s.get("publication_id") == rep] or \
           [s for s in sigs.values() if s is not nova and s.get("publication_role") == "primary_publication"]
    if not nova or not base:
        return False, "sem assinatura distinta da análise do card e do dado novo: compatibilidade não demonstrável"
    b = base[0]
    if _ids(b) and _ids(nova) and not (_ids(b) & _ids(nova)):
        return False, "trial diferente"
    if _norm(b.get("trial_key")) != _norm(nova.get("trial_key")):
        return False, "trial_key diferente ou ausente"
    for k in ("population", "analysis_set", "endpoint", "comparison"):
        if b.get(k) in (None, "") or nova.get(k) in (None, ""):
            return False, f"{k} ausente: dúvida"
        if _norm(b[k]) != _norm(nova[k]):
            return False, f"{k} diverge: '{b[k]}' × '{nova[k]}'"
    if _norm(b.get("cohort")) != _norm(nova.get("cohort")):
        return False, "coorte diverge"
    papeis = lambda s: sorted(a.get("role") for a in s.get("arms") or [])  # noqa: E731
    if not papeis(b) or papeis(b) != papeis(nova):
        return False, "braços divergem ou ausentes"
    return True, "assinaturas compatíveis"
