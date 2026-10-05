"""validate_v2 — validador dos registros do Database v2.

    python3 scripts/db_v2/validate_v2.py                       # sombra (scripts/_db_v2_shadow)
    python3 scripts/db_v2/validate_v2.py --dir PASTA           # outra pasta de registros
    python3 scripts/db_v2/validate_v2.py --json relatorio.json

Níveis de curadoria:
  shadow   lift automático; origin=legacy permitido; lacunas de obrigatoriedade = W_REQUIRED (backlog)
  modeled  estruturado a partir do legado, sem verificação; idem shadow para obrigatoriedade
  curated  canônico; lacuna de obrigatoriedade ativa = E_REQUIRED; origin=legacy proibido

Saída: 0 sem erro (avisos permitidos); 1 com erro.
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import subprocess
import sys

import bibliografia as B
import v2lib as L

R = L.REGISTRY
import re

MODFIELDS = R["module_fields"]
EXT = R["external_registries"]


def tempo_canonico(tp: dict | None) -> str | None:
    """'median' | 'landmark:6' | 'at_event:6-10' — forma usada na analysis_signature."""
    if not tp:
        return None
    s = tp["type"]
    if "months" in tp:
        s += f":{tp['months']:g}"
    if "window" in tp:
        s += f":{tp['window']['low']:g}-{tp['window']['high']:g}"
    return s
ENUMS = R["enums"]
ID_KEYS = set(R["analysis_signature"]["identity"])


class Relatorio:
    def __init__(self):
        self.itens = []

    def add(self, uid, codigo, caminho, msg):
        self.itens.append({"uid": uid, "codigo": codigo, "caminho": caminho, "msg": msg})

    def erros(self):
        return [i for i in self.itens if i["codigo"].startswith("E_")]


def _envelopes(rec):
    """(caminho, envelope) de todo o core + endpoints/subgroups + campos de módulo."""
    for g in ("identity", "population", "design", "safety", "interpretation", "guideline", "collection"):
        for campo, env in (rec.get(g) or {}).items():
            yield f"{g}.{campo}", env
    for k in ("endpoints", "subgroups"):
        if k in rec:
            yield k, rec[k]
    for n, m in enumerate(rec.get("modules", [])):
        for campo, env in (m.get("fields") or {}).items():
            yield f"modules[{n}:{m['module']}].{campo}", env


def checar_envelope(rep, uid, nivel, caminho, env, prov, item=False):
    """item=True: objeto de lista (endpoint) cujo conteúdo é o próprio valor — não tem 'v'."""
    st, origin = env.get("state"), env.get("origin")
    if st == "present":
        if "v" in env and env["v"] in ("", [], {}, None):
            rep.add(uid, "E_STATE", caminho, "present com valor vazio")
        if "v" not in env and not item:
            rep.add(uid, "E_STATE", caminho, "present sem 'v'")
        if not origin:
            rep.add(uid, "E_ORIGIN", caminho, "present sem origin")
        if not env.get("prov") and origin != "editorial":
            rep.add(uid, "E_PROV", caminho, "present sem prov")
    else:
        if "v" in env or (item and (env.get("arms_values") or env.get("estimate") or env.get("effect"))):
            rep.add(uid, "E_STATE", caminho, f"{st} com valor 'v' (valor só existe em present)")
        if origin:
            rep.add(uid, "E_STATE", caminho, f"{st} com origin")
        if env.get("conflict") not in (None, "none"):
            rep.add(uid, "E_CONFLICT", caminho, "conflito só existe em valor present")
    if origin == "legacy" and nivel == "curated":
        rep.add(uid, "E_ORIGIN", caminho, "origin=legacy em registro curated")
    p = env.get("prov")
    if p is not None:
        if p not in prov:
            rep.add(uid, "E_PROV", caminho, f"prov '{p}' inexistente")
        else:
            src, ext = prov[p]["source"]["type"], prov[p]["extraction"]
            if origin == "legacy" and ext != "lifted_v1":
                rep.add(uid, "E_PROV", caminho, "origin=legacy exige extraction=lifted_v1")
            if origin == "reported" and (src == "v1_legacy" or ext not in ("explicit", "human_confirmed")):
                rep.add(uid, "E_PROV", caminho, "reported exige fonte primária e extraction explicit/human_confirmed")
            if origin == "derived" and ext != "derived":
                rep.add(uid, "E_PROV", caminho, "derived exige extraction=derived")
    if origin == "derived" and not env.get("derivation"):
        rep.add(uid, "E_DERIVED", caminho, "derived sem derivation")
    if env.get("derivation") and origin != "derived":
        rep.add(uid, "E_DERIVED", caminho, "derivation em valor não derivado")
    if env.get("conflict") in ("within_source_conflict", "cross_source_conflict"):
        cands = env.get("value_candidates") or []
        if len(cands) < 2 or any(not c.get("locator") for c in cands):
            rep.add(uid, "E_CONFLICT", caminho, "conflito exige ≥2 value_candidates com locator")
    if st == "not_reported" and nivel == "curated" and not env.get("checked_sources"):
        rep.add(uid, "E_STATE", caminho, "not_reported exige checked_sources (texto completo conferido)")
    if st == "withheld_due_to_integrity" and not env.get("decision_ref"):
        rep.add(uid, "E_STATE", caminho, "withheld exige decision_ref")


def _qualificados(obj, caminho="$"):
    if isinstance(obj, dict):
        if "op" in obj and obj.get("op") in ("=", "≈", "<", "≤", ">", "≥", "range", "not_reached", "not_evaluable",
                                             "direction_only"):
            yield caminho, obj
        for k, v in obj.items():
            yield from _qualificados(v, f"{caminho}.{k}")
    elif isinstance(obj, list):
        for n, v in enumerate(obj):
            yield from _qualificados(v, f"{caminho}[{n}]")


def checar_referencias(rep, uid, rec):
    for caminho, q in _qualificados({k: v for k, v in rec.items() if k != "legacy"}):
        if q["op"] == "range" and ("low" not in q or "high" not in q or q["low"] > q["high"]):
            rep.add(uid, "E_VALUE", caminho, "range sem low/high válidos")
        if q["op"] in ("=", "≈", "<", "≤", ">", "≥") and "value" not in q:
            rep.add(uid, "E_VALUE", caminho, f"op '{q['op']}' sem value")
    braços = L.arms(rec)
    ids = [a["arm_id"] for a in braços]
    if len(ids) != len(set(ids)):
        rep.add(uid, "E_ARM_REF", "design.arms", "arm_id duplicado")
    ids = set(ids)
    for a in braços:
        for i in a.get("interventions", []):
            if i.get("module") and i["module"] not in L.REGISTRY["modules"]:
                rep.add(uid, "E_MODULE", f"design.arms[{a['arm_id']}]", f"intervenção com módulo inválido {i['module']}")
    comps = {c["comparison_id"]: c for c in L.valor(L.envelope(rec, "design.comparisons")) or []}
    for c in comps.values():
        for a in c["exp_arms"] + c.get("ctl_arms", []):
            if a not in ids:
                rep.add(uid, "E_COMPARISON_REF", f"design.comparisons[{c['comparison_id']}]", f"braço {a} inexistente")
        if c["hypothesis"] == "non_inferiority" and not c.get("ni_margin"):
            rep.add(uid, "E_COMPARISON_REF", f"design.comparisons[{c['comparison_id']}]", "NI sem ni_margin")
    coortes = {c["cohort_id"] for c in L.valor(L.envelope(rec, "design.cohorts")) or []}
    bms = {b["id"] for b in L.biomarcadores(rec)}
    analises = {a["analysis_id"]: a for a in rec.get("analyses", [])}
    for n, m in enumerate(rec.get("modules", [])):
        aid = m.get("arm_ids")
        if m["role"] == "undetermined" or aid is None:
            if rec["curation"]["level"] == "curated":
                rep.add(uid, "E_MODULE", f"modules[{n}]", "papel/braços indeterminados em registro curated")
            continue
        if aid != "all":
            for a in aid:
                if a not in ids:
                    rep.add(uid, "E_ARM_REF", f"modules[{n}:{m['module']}]", f"módulo aponta braço {a} inexistente")
        for campo in m.get("fields") or {}:
            if campo not in {f["field"] for f in MODFIELDS[m["module"]]["fields"]}:
                rep.add(uid, "E_MODULE", f"modules[{n}:{m['module']}].{campo}", "campo fora do registro do módulo")
    nivel = rec["curation"]["level"]
    randomizado = L.valor(L.envelope(rec, "design.allocation")) == "randomized"
    for ep in L.endpoints(rec):
        c = f"endpoints[{ep['endpoint_id']}]"
        cid = ep.get("comparison_id")
        h = ep["hierarchy"]
        so_direcao = all((q.get("value") or {}).get("op") == "direction_only"
                         for q in [ep.get("effect") or {}] + ep.get("arms_values", []) if q)
        if ep.get("state") == "present" and not so_direcao:
            for k in ("measure", "timepoint"):
                if k not in ep:
                    rep.add(uid, "E_STATE", c, f"endpoint present sem {k}")
        if nivel == "curated" and (h["level"] == "unspecified" or h.get("primary_type") == "multiple_unspecified"):
            rep.add(uid, "E_PRIMARY", c, "hierarquia não especificada em registro curated")
        if randomizado and comps and h["level"] == "primary" and cid is None \
                and not (h.get("scope") or {}).get("cohort_id"):
            rep.add(uid, "E_COMPARISON_REF" if nivel == "curated" else "W_COMPARISON", c,
                    "primário de estudo randomizado sem comparison_id")
        ef = ep.get("effect") or {}
        for alvo, rot in ((ef, "effect"), *((av, f"arms_values[{av.get('arm_id')}]") for av in ep.get("arms_values", []))):
            ci = alvo.get("ci")
            if ci and ci.get("high") is not None and ci["low"] > ci["high"]:
                rep.add(uid, "E_VALUE", c, f"{rot}: IC invertido")
            val = (alvo.get("value") or {})
            if ci and ci.get("high") is not None and val.get("op") == "=" and "value" in val \
                    and not (ci["low"] <= val["value"] <= ci["high"]):
                rep.add(uid, "E_VALUE", c, f"{rot}: valor {val['value']} fora do IC")
        if ef.get("significance") in ("met", "not_met") and not ef.get("p") and not ef.get("ci"):
            rep.add(uid, "W_SIGNIFICANCE", c, "significância sem p nem IC")
        if cid is not None and cid not in comps:
            rep.add(uid, "E_COMPARISON_REF", c, f"comparison_id {cid} inexistente")
        for av in ep.get("arms_values", []):
            if "arm_id" in av and av["arm_id"] not in ids:
                rep.add(uid, "E_ARM_REF", c, f"arms_values com braço {av['arm_id']} inexistente")
            if "arm_id" in av and cid in comps:
                cmp_ = comps[cid]
                if av["arm_id"] not in cmp_["exp_arms"] + cmp_.get("ctl_arms", []):
                    rep.add(uid, "E_ARM_REF", c, f"braço {av['arm_id']} fora da comparação {cid}")
            if "arm_group" in av:
                fatores = {f.get("factor"): f.get("levels", []) for f in L.valor(L.envelope(rec, "design.factors")) or []}
                g = av["arm_group"]
                if g["level"] not in fatores.get(g["factor"], []):
                    rep.add(uid, "E_ARM_REF", c, f"arm_group {g} não existe em design.factors")
            if "arm_id" not in av and "arm_group" not in av:
                rep.add(uid, "E_ARM_REF", c, "arms_values sem arm_id nem arm_group")
        pop = ep.get("population") or {}
        if pop.get("biomarker_ref") and pop["biomarker_ref"] not in bms:
            rep.add(uid, "E_COHORT_REF", c, f"biomarker_ref {pop['biomarker_ref']} inexistente")
        for k in (pop.get("cohort_id"), (ep["hierarchy"].get("scope") or {}).get("cohort_id"),
                  (ep["hierarchy"].get("scope") or {}).get("part_id")):
            if k and k not in coortes:
                rep.add(uid, "E_COHORT_REF", c, f"cohort_id {k} inexistente")
        ar = (ep.get("maturity") or {}).get("analysis_ref")
        if ar and ar not in analises:
            rep.add(uid, "E_SIGNATURE", c, f"analysis_ref {ar} inexistente")
        checar_envelope(rep, uid, rec["curation"]["level"], c, ep, rec.get("provenance", {}), item=True)
    prov = rec.get("provenance", {})
    eids = {e["endpoint_id"] for e in L.endpoints(rec)}
    fatores = {f.get("factor"): f.get("levels", []) for f in L.valor(L.envelope(rec, "design.factors")) or []}
    for campo in ("grade3plus_any", "serious_ae", "discontinuation_ae", "dose_modification",
                  "treatment_related_deaths", "key_toxicities", "late_effects"):
        for x in L.valor(L.envelope(rec, f"safety.{campo}")) or []:
            if "arm_id" in x and x["arm_id"] not in ids:
                rep.add(uid, "E_ARM_REF", f"safety.{campo}", f"braço {x['arm_id']} inexistente")
            g = x.get("arm_group")
            if g and g["level"] not in fatores.get(g["factor"], []):
                rep.add(uid, "E_ARM_REF", f"safety.{campo}", f"arm_group {g} inexistente")
    for sg in L.valor(rec.get("subgroups")) or []:
        for er in ([sg["endpoint_ref"]] if sg.get("endpoint_ref") else []) + sg.get("endpoint_refs", []):
            if er not in eids:
                rep.add(uid, "E_COHORT_REF", "subgroups", f"endpoint_ref {er} inexistente")
        if sg.get("comparison_id") and sg["comparison_id"] not in comps:
            rep.add(uid, "E_COMPARISON_REF", "subgroups", f"comparison_id {sg['comparison_id']} inexistente")
    for caminho, env in list(_envelopes(rec)) + [(f"endpoints[{e['endpoint_id']}]", e) for e in L.endpoints(rec)]:
        for cand in (env or {}).get("value_candidates") or []:
            if cand.get("prov") and cand["prov"] not in prov:
                rep.add(uid, "E_PROV", caminho, f"value_candidate com prov {cand['prov']} inexistente")
            v = cand.get("value")
            if isinstance(v, dict) and v.get("arm_id") and v["arm_id"] not in ids:
                rep.add(uid, "E_ARM_REF", caminho, f"value_candidate com braço {v['arm_id']} inexistente")
    for ep in L.endpoints(rec):
        ar = (ep.get("maturity") or {}).get("analysis_ref")
        if not ar or ar not in analises:
            continue
        sig, c = analises[ar]["signature"], f"endpoints[{ep['endpoint_id']}]→analyses[{ar}]"
        esperado = {"endpoint": ep["code"], "summary_measure": (ep.get("measure") or {}).get("summary"),
                    "timepoint": tempo_canonico(ep.get("timepoint")), "comparison": ep.get("comparison_id") or "none"}
        for k, v in esperado.items():
            if v is not None and sig.get(k) != v:
                rep.add(uid, "E_SIGNATURE", c, f"assinatura {k}={sig.get(k)!r} ≠ endpoint {v!r} (uma assinatura por endpoint/medida/tempo)")
    for x in rec.get("external_relationships", []):
        c = f"external_relationships[{x['registry']}:{x['registry_id']}]"
        spec = EXT.get(x["registry"], {})
        if spec.get("pattern") and not re.match(spec["pattern"], x["registry_id"]):
            rep.add(uid, "E_EXTERNAL", c, f"identificador fora do formato {spec['pattern']}")
        if x["registry"] == "other" and not x.get("label"):
            rep.add(uid, "E_EXTERNAL", c, "registry=other exige label")
        if x.get("url"):
            if not x["url"].startswith("https://") or (spec.get("host") and spec["host"] not in x["url"]):
                rep.add(uid, "E_EXTERNAL", c, "url não é https do registro declarado")
            elif spec.get("host") and x["registry_id"] not in x["url"]:
                rep.add(uid, "E_EXTERNAL", c, "url não contém o identificador")
    for a in braços:
        for pt in a.get("proceeded_to_planned_therapy", []):
            if pt.get("prov") and pt["prov"] not in prov:
                rep.add(uid, "E_PROV", f"design.arms[{a['arm_id']}].proceeded_to_planned_therapy", f"prov {pt['prov']} inexistente")
            if pt.get("origin") == "derived" and not pt.get("derivation"):
                rep.add(uid, "E_DERIVED", f"design.arms[{a['arm_id']}].proceeded_to_planned_therapy", "derived sem derivation")
    for a in analises.values():
        if a.get("prov") and a["prov"] not in prov:
            rep.add(uid, "E_PROV", f"analyses[{a['analysis_id']}]", f"prov {a['prov']} inexistente")
    for co in L.valor(L.envelope(rec, "design.cohorts")) or []:
        if co.get("biomarker_ref") and co["biomarker_ref"] not in bms:
            rep.add(uid, "E_COHORT_REF", f"design.cohorts[{co['cohort_id']}]", f"biomarker_ref {co['biomarker_ref']} inexistente")
    for n, m in enumerate(rec.get("modules", [])):
        f = m.get("fields") or {}
        c = f"modules[{n}:{m['module']}]"
        for item in L.valor(f.get("target_expression")) or []:
            if isinstance(item, dict) and item.get("biomarker_ref") and item["biomarker_ref"] not in bms:
                rep.add(uid, "E_COHORT_REF", c + ".target_expression", f"biomarker_ref {item['biomarker_ref']} inexistente")
        ra = L.valor(f.get("required_alteration"))
        if isinstance(ra, str) and ra not in bms:
            rep.add(uid, "E_COHORT_REF", c + ".required_alteration", f"'{ra}' não é id de population.biomarker_selection")
        for e in L.valor(f.get("stratified_results")) or []:
            if isinstance(e, str) and e not in eids:
                rep.add(uid, "E_COHORT_REF", c + ".stratified_results", f"endpoint {e} inexistente")
    # coerência módulo × braço × intervenção
    papeis = collections.defaultdict(set)
    declarados = {m["module"] for m in rec.get("modules", [])}
    usa_modulo = any(i.get("module") for a in braços for i in a.get("interventions", []))
    cod_mod = "E_MODULE" if nivel == "curated" else "W_MODULE"
    for a in braços:
        for i in a.get("interventions", []):
            if i.get("module") and i["module"] not in declarados:
                rep.add(uid, cod_mod, f"design.arms[{a['arm_id']}]", f"intervenção com módulo {i['module']} ausente de modules[]")
    for m in rec.get("modules", []):
        if m["role"] == "undetermined" or m.get("arm_ids") is None:
            continue
        contexto_bio = MODFIELDS[m["module"]].get("biomarker_context")
        for a in L.modulo_arms(rec, m):
            papeis[(m["module"], a["arm_id"])].add(m["role"])
            if usa_modulo and not contexto_bio and m["role"] in ("tested", "control", "backbone") and a.get("interventions") \
                    and not any(i.get("module") == m["module"] for i in a["interventions"]) \
                    and m.get("arm_ids") != "all":
                rep.add(uid, cod_mod, f"modules[{m['module']}]", f"braço {a['arm_id']} sem intervenção do módulo")
    for m in rec.get("modules", []):
        if m["role"] == "tested" and m.get("arm_ids") not in (None, "all"):
            papeis_braço = {a["role"] for a in L.modulo_arms(rec, m)}
            if papeis_braço and papeis_braço <= {"control"}:
                rep.add(uid, "E_MODULE", f"modules[{m['module']}]", "módulo tested aponta só braço de controle")
    for x in L.valor(L.envelope(rec, "safety.key_toxicities")) or []:
        for mm in x.get("aesi_of") or []:
            if mm not in declarados:
                rep.add(uid, cod_mod, "safety.key_toxicities", f"aesi_of {mm} ausente de modules[]")
    for (mod_, arm), ps in papeis.items():
        if {"tested", "control"} <= ps:
            rep.add(uid, "E_MODULE", f"modules[{mod_}]", f"braço {arm} é tested e control no mesmo módulo")
    for c_ in comps.values():
        for a in c_["exp_arms"]:
            if next((x["role"] for x in braços if x["arm_id"] == a), None) == "control":
                rep.add(uid, "E_COMPARISON_REF", f"design.comparisons[{c_['comparison_id']}]", f"braço controle {a} em exp_arms")
    ss = L.valor(L.envelope(rec, "design.sample_size")) or {}
    soma = sum(a["n"]["value"] for a in braços if isinstance(a.get("n"), dict) and a["n"].get("op") == "="
               and isinstance(a["n"].get("value"), (int, float)))
    if isinstance(ss, dict) and isinstance(ss.get("randomized"), (int, float)) and soma > ss["randomized"]:
        rep.add(uid, "W_SAMPLE_SIZE", "design.sample_size", f"soma dos braços {soma} > randomizados {ss['randomized']}")
    for a in analises.values():
        faltam = ID_KEYS - set(a["signature"])
        if faltam:
            rep.add(uid, "E_SIGNATURE", f"analyses[{a['analysis_id']}]", f"assinatura sem {sorted(faltam)}")
        sig = a["signature"]
        if sig.get("endpoint") and L.endpoints(rec) and sig["endpoint"] not in {e["code"] for e in L.endpoints(rec)}:
            rep.add(uid, "E_SIGNATURE", f"analyses[{a['analysis_id']}]", f"endpoint {sig['endpoint']} sem endpoint correspondente")
        if sig.get("cohort") and sig["cohort"] not in coortes:
            rep.add(uid, "E_SIGNATURE", f"analyses[{a['analysis_id']}]", f"cohort {sig['cohort']} inexistente")
        cmp_ = a["signature"].get("comparison")
        if cmp_ not in (None, "none") and cmp_ not in comps:
            rep.add(uid, "E_SIGNATURE", f"analyses[{a['analysis_id']}]", f"comparison {cmp_} inexistente")


def checar_primarios(rep, uid, rec):
    eps = L.endpoints(rec)
    familias = {f["family_id"]: f for f in (L.valor(L.envelope(rec, "design.multiplicity")) or {}).get("families", [])}
    for f in familias.values():
        for m in f["members"]:
            if m["endpoint_id"] not in {e["endpoint_id"] for e in eps}:
                rep.add(uid, "E_PRIMARY", f"design.multiplicity[{f['family_id']}]", f"membro {m['endpoint_id']} inexistente")
        if f["procedure"] == "fixed_sequence":
            por_ep = {e["endpoint_id"]: (e["hierarchy"].get("testing") or {}).get("order") for e in eps}
            for m in f["members"]:
                if por_ep.get(m["endpoint_id"]) not in (None, m.get("order")):
                    rep.add(uid, "E_PRIMARY", f"design.multiplicity[{f['family_id']}]",
                            f"ordem de {m['endpoint_id']} diverge entre família e endpoint")
            ordens = sorted(m.get("order", 0) for m in f["members"])
            if ordens != list(range(1, len(ordens) + 1)):
                rep.add(uid, "E_PRIMARY", f"design.multiplicity[{f['family_id']}]", "fixed_sequence exige order 1..n")
        if f["procedure"] == "alpha_split" and f.get("overall_alpha") is not None:
            soma = sum(m.get("alpha", 0) for m in f["members"])
            if soma - f["overall_alpha"] > 1e-9:
                rep.add(uid, "E_PRIMARY", f"design.multiplicity[{f['family_id']}]", f"α dividido {soma} > {f['overall_alpha']}")
    grupos = collections.defaultdict(list)
    todos_prim = collections.defaultdict(list)
    for e in eps:
        h = e["hierarchy"]
        if h["level"] != "primary":
            continue
        escopo = (tuple(sorted((h.get("scope") or {}).items())), e.get("comparison_id"),
                  (e.get("maturity") or {}).get("analysis_ref"))
        todos_prim[escopo].append(e)
        if (e.get("measure") or {}).get("analysis_role", "protocol_primary_analysis") != "protocol_primary_analysis":
            continue
        grupos[escopo].append(e)
        fam = (h.get("testing") or {}).get("family_id")
        if fam and fam not in familias:
            rep.add(uid, "E_PRIMARY", f"endpoints[{e['endpoint_id']}]", f"família de teste {fam} inexistente")
    # "só apoio" e co/dual são avaliados ATRAVÉS das análises (coprimários podem sair em publicações diferentes);
    # "único" é avaliado POR análise (o mesmo primário reaparece em cada atualização)
    sem_analise = lambda k: k[:2]
    com_protocolo = {sem_analise(k) for k in grupos}
    for k in {sem_analise(k) for k in todos_prim} - com_protocolo:
        rep.add(uid, "E_PRIMARY", f"escopo {k}", "primário só com medida de apoio (falta protocol_primary_analysis)")
    por_escopo = collections.defaultdict(list)
    for k, es in grupos.items():
        por_escopo[sem_analise(k)] += es
    for escopo, es in por_escopo.items():
        tipos = {e["hierarchy"].get("primary_type", "sole") for e in es}
        if tipos & {"co_primary", "dual_primary", "multiple_unspecified"}:
            if len({e["code"] + str(e.get("measure")) for e in es}) < 2 and len(es) < 2:
                rep.add(uid, "E_PRIMARY", f"escopo {escopo}", f"{sorted(tipos)} com um só endpoint")
    for escopo, es in por_escopo.items():
        tipos = {e["hierarchy"].get("primary_type", "sole") for e in es}
        if len(tipos) > 1:
            rep.add(uid, "E_PRIMARY", f"escopo {escopo}", f"primary_type misturado {sorted(tipos)}")
            continue
        t = tipos.pop()
        # o mesmo endpoint repetido em atualizações conta uma vez; endpoints distintos não podem ser "sole"
        distintos = {(e["code"], (e.get("measure") or {}).get("summary"), tempo_canonico(e.get("timepoint"))) for e in es}
        if t == "sole" and len(distintos) > 1:
            rep.add(uid, "E_PRIMARY", f"escopo {escopo}", f"{len(distintos)} primários distintos marcados sole")
        # (contagem mínima de co/dual já avaliada através das análises)
        if t == "dual_primary":
            fams = {(e["hierarchy"].get("testing") or {}).get("family_id") for e in es}
            if None in fams or not all(familias.get(f, {}).get("procedure") in ("alpha_split", "graphical", "bonferroni",
                                                                                  "holm", "hochberg", "fallback")
                                       for f in fams):
                rep.add(uid, "E_PRIMARY", f"escopo {escopo}", "dual_primary exige família de multiplicidade com α dividido")
            else:
                for f in fams:
                    membros = {m["endpoint_id"]: m for m in familias[f]["members"]}
                    if any("alpha" not in membros.get(e["endpoint_id"], {}) for e in es):
                        rep.add(uid, "E_PRIMARY", f"escopo {escopo}", "dual_primary sem α por membro")


def _lacuna(rep, uid, nivel, caminho, env, msg):
    """curated: campo obrigatório AUSENTE é erro; unknown DECLARADO com fontes conferidas é lacuna reconhecida
    (a fonte disponível não permite afirmar nem not_reported). shadow/modeled: sempre lacuna de backlog."""
    if nivel != "curated":
        rep.add(uid, "W_REQUIRED", caminho, msg)
    elif env is not None and env.get("state") == "unknown" and env.get("checked_sources"):
        rep.add(uid, "W_REQUIRED_ACK", caminho, msg + " (unknown declarado com fontes conferidas)")
    else:
        rep.add(uid, "E_REQUIRED", caminho, msg + " — em curated, declare o estado (unknown exige checked_sources)")


def checar_obrigatoriedade(rep, uid, rec):
    nivel = rec["curation"]["level"]
    cod = "E_REQUIRED" if nivel == "curated" else "W_REQUIRED"
    perfil = R["profiles"][rec["record_type"]]
    single = L.estado(L.envelope(rec, "design.allocation")) == "present" and \
        L.valor(L.envelope(rec, "design.allocation")) == "single_arm"
    na = set(perfil["not_applicable"]) | (set(R["single_arm_not_applicable"]) if single else set())
    opcionais = set(R["single_arm_optional"]) if single else set()
    for p in perfil["required"]:
        if p in na or p in opcionais:
            continue
        env = L.envelope(rec, p)
        st = L.estado(env)
        if st == "unknown":
            _lacuna(rep, uid, nivel, p, env, "obrigatório pelo perfil e ausente/unknown")
        elif st == "not_applicable":
            rep.add(uid, "E_NA_CONTRADICTION", p, f"obrigatório pelo perfil {rec['record_type']} mas not_applicable")
        if p == "endpoints" and st == "present" and not any(e["hierarchy"]["level"] == "primary" for e in L.endpoints(rec)):
            rep.add(uid, cod, p, "nenhum endpoint primário")
    for p in na:
        if L.estado(L.envelope(rec, p)) == "present":
            rep.add(uid, "W_NOT_APPLICABLE_FILLED", p, "preenchido embora não se aplique ao perfil")
    presentes = {m["module"] for m in rec.get("modules", [])}
    for nome, spec in MODFIELDS.items():
        if spec.get("warn_if_absent") and nome not in presentes and rec["modules"] \
                and L.ativo(spec["activation_module"], rec, None):
            rep.add(uid, "W_MODULE_MISSING", "modules", f"{nome} ativo pelo conteúdo mas ausente")
    for n, m in enumerate(rec.get("modules", [])):
        papel = m["role"]
        if papel == "undetermined":
            continue
        spec = MODFIELDS[m["module"]]
        ativo_mod = L.ativo(spec["activation_module"], rec, m) if "activation_module" in spec else True
        overrides = {(o["field"], o["role"]): o["activation"] for o in spec.get("required_overrides", [])}
        for f in spec["fields"]:
            env = (m.get("fields") or {}).get(f["field"])
            req = L.requisito(f, papel)
            if (f["field"], papel) in overrides and L.ativo(overrides[(f["field"], papel)], rec, m):
                req = "required"
            on = ativo_mod and L.ativo(f["activation"], rec, m)
            c = f"modules[{n}:{m['module']}].{f['field']}"
            if req == "required" and on and L.estado(env) == "unknown":
                _lacuna(rep, uid, nivel, c, env, f"obrigatório quando {papel} e ativo")
            if req == "required" and on and L.estado(env) == "not_applicable":
                rep.add(uid, "E_NA_CONTRADICTION", c, f"obrigatório quando {papel} e ativo, mas not_applicable")
            if req == "not_applicable" and L.estado(env) == "present":
                rep.add(uid, "W_NOT_APPLICABLE_FILLED", c, f"não se aplica ao papel {papel}")
        if "safety.key_toxicities" in na:
            continue  # perfil sem segurança (coleção, diretriz, diagnóstico): AESI não é cobrado
        toxs = L.valor(L.envelope(rec, "safety.key_toxicities")) or []
        braços = {a["arm_id"] for a in L.modulo_arms(rec, m)}
        for t in spec["aesi"]:
            if L.requisito(t, papel) != "required" or not (ativo_mod and L.ativo(t["activation"], rec, m)):
                continue
            achou = [x for x in toxs if isinstance(x, dict) and x.get("term") == t["term"]
                     and m["module"] in (x.get("aesi_of") or [])
                     and (not braços or x.get("arm_id") in braços or "arm_group" in x)
                     and ("value" in x or "n" in x or x.get("state") in ("not_reported", "unknown"))]
            if not achou:
                rep.add(uid, cod, f"safety.key_toxicities[{t['term']}]",
                        f"AESI obrigatório de {m['module']} ({papel}) ausente nos braços {sorted(braços)}")
            elif nivel == "curated" and all(x.get("state") == "unknown" for x in achou):
                if all(x.get("checked_sources") for x in achou):
                    rep.add(uid, "W_REQUIRED_ACK", f"safety.key_toxicities[{t['term']}]", "AESI unknown declarado")
                else:
                    rep.add(uid, "E_REQUIRED", f"safety.key_toxicities[{t['term']}]", "AESI unknown sem checked_sources")


_SNAPSHOT: dict | None = None


def _snapshot() -> dict:
    global _SNAPSHOT
    if _SNAPSHOT is None:
        _SNAPSHOT = B.carregar_snapshot() if B.SNAPSHOT.exists() else {}
    return _SNAPSHOT


def checar_bibliografia(rep, uid, rec):
    """publications no $def; represented_publication → publication_id existente; `citation` do v1 = projeção da
    publicação representada = projeção do snapshot PubMed do PMID do card; evidence_collection sem citação principal."""
    env = L.envelope(rec, "identity.publications") or {}
    pubs = L.valor(env) if env.get("state") == "present" else []
    ids = set()
    for i, p in enumerate(pubs or []):
        if not isinstance(p, dict) or "publication_id" not in p:
            continue                                   # lista livre legada (pré-$def): não é citação estruturada
        c = f"identity.publications[{i}]"
        for e in L.validar_schema(p, L.SCHEMA["$defs"]["publication"], L.SCHEMA):
            rep.add(uid, "E_PUBLICATION", c, e)
        for e in B.validar_publicacao(p):
            rep.add(uid, "E_PUBLICATION", c, e)
        ids.add(p["publication_id"])
    rp = L.valor(L.envelope(rec, "identity.represented_publication"))
    rp_id = rp.get("publication_id") if isinstance(rp, dict) else None
    if rp_id and rp_id not in ids:
        rep.add(uid, "E_PUBLICATION_REF", "identity.represented_publication", f"{rp_id} não está em identity.publications")
    cit = ((rec.get("legacy") or {}).get("v1") or {}).get("citation")
    if cit is None:
        return
    if rec.get("record_type") == "evidence_collection":
        rep.add(uid, "E_CITATION", "legacy.v1.citation", "evidence_collection não tem citação principal única")
        return
    alvo = next((p for p in pubs or [] if isinstance(p, dict) and p.get("publication_id") == rp_id), None)
    if alvo is None:
        rep.add(uid, "E_CITATION", "legacy.v1.citation", "citation sem publicação representada estruturada")
    elif B.citation_v1(alvo) != cit:
        rep.add(uid, "E_CITATION", "legacy.v1.citation", "citation ≠ projeção da publicação representada")
    pmid = B.pmid_do_card(rec["legacy"]["v1"])
    if cit.get("pmid") != pmid:
        rep.add(uid, "E_CITATION", "legacy.v1.citation", f"citation.pmid {cit.get('pmid')} ≠ PMID do card {pmid}")
    elif pmid in _snapshot():
        esperado = B.citation_v1(B.publicacao_de_snapshot(_snapshot()[pmid], role=cit.get("role", "undetermined")))
        if esperado != cit:
            dif = sorted(k for k in set(esperado) | set(cit) if esperado.get(k) != cit.get(k))
            rep.add(uid, "E_CITATION", "legacy.v1.citation", f"citation diverge do snapshot PubMed em {dif}")
    else:
        rep.add(uid, "E_CITATION", "legacy.v1.citation", f"PMID {pmid} fora do snapshot bibliográfico")


def checar_relacoes(rep, recs: dict):
    pai = {}
    arestas = collections.defaultdict(lambda: collections.defaultdict(set))
    for uid, r in recs.items():
        rel = r.get("relationships") or {}
        p = rel.get("parent_uid")
        if p == uid:
            rep.add(uid, "E_REL", "relationships.parent_uid", "auto-referência")
        if p:
            pai[uid] = p
            if p not in recs:
                rep.add(uid, "W_REL_ORPHAN", "relationships.parent_uid", f"pai {p} fora do conjunto validado")
            if p in recs and uid not in (recs[p].get("relationships") or {}).get("child_uids", []):
                rep.add(uid, "E_REL", "relationships.parent_uid", f"{p} não lista {uid} em child_uids")
        for c in rel.get("child_uids", []):
            if c == uid:
                rep.add(uid, "E_REL", "relationships.child_uids", "auto-referência")
            if c in recs and (recs[c].get("relationships") or {}).get("parent_uid") != uid:
                rep.add(uid, "E_REL", "relationships.child_uids", f"{c} não aponta {uid} como parent")
        for l in rel.get("links", []):
            if l["target_uid"] == uid:
                rep.add(uid, "E_REL", "relationships.links", f"{l['type']} auto-referente")
            arestas[l["type"]][uid].add(l["target_uid"])
    for uid in pai:
        vistos, cur = set(), uid
        while cur in pai:
            if cur in vistos:
                rep.add(uid, "E_REL", "relationships.parent_uid", "ciclo parent/child")
                break
            vistos.add(cur)
            cur = pai[cur]
    for tipo in ("supersedes", "follow_up_of", "secondary_analysis_of"):
        g = arestas[tipo]
        cor = {}

        def dfs(u):
            cor[u] = 1
            for v in g.get(u, ()):
                if cor.get(v) == 1:
                    return True
                if cor.get(v) is None and dfs(v):
                    return True
            cor[u] = 2
            return False
        for u in list(g):
            if cor.get(u) is None and dfs(u):
                rep.add(u, "E_REL", f"relationships.links[{tipo}]", "ciclo")
                break


def uids_head(ref: str = "HEAD") -> set[str] | None:
    """uids do data.js em `ref` (no CI: HEAD^, o commit anterior). None se o ref não existir."""
    try:
        txt = subprocess.run(["git", "-C", str(L.SITE), "show", f"{ref}:assets/js/data.js"], capture_output=True,
                             text=True, check=True).stdout
        return {s["uid"] for s in L.ler_data_js(txt)[1]["studies"]}
    except Exception:
        return None


def uids_aposentados(txt: str | None = None) -> set[str]:
    """uids que deixaram de ser card e viraram alias de uma família de estudo (families[].legacy_uids).

    O uid não é reutilizado nem some: o deep link `database.html#<uid>` passa a abrir a família."""
    txt = txt if txt is not None else L.DATA_JS.read_text(encoding="utf-8")
    obj = L.ler_data_js(txt)[1]
    return {u for f in obj.get("families") or [] for u in f.get("legacy_uids") or []}


def validar(recs: dict, arquivos: dict | None = None, head: set | None = None,
            atuais: dict | None = None, aposentados: set | None = None) -> Relatorio:
    """atuais: {uid: card do data.js atual}; o legado de registro não migrado tem de ser idêntico."""
    rep = Relatorio()
    for uid, card in (atuais or {}).items():
        r = recs.get(uid)
        if r and r["curation"]["level"] != "curated" and r["legacy"]["v1"] != card:
            rep.add(uid, "E_LEGACY", "legacy.v1", "legado diverge do card atual no data.js")
    for uid, rec in recs.items():
        for e in L.validar_schema(rec, L.SCHEMA):
            rep.add(uid, "E_SCHEMA", e.split(":")[0], e)
        if arquivos and arquivos.get(uid) and arquivos[uid] != f"{uid}.json":
            rep.add(uid, "E_UID_IMMUTABLE", "uid", f"arquivo {arquivos[uid]} ≠ uid")
        if (rec.get("legacy") or {}).get("v1", {}).get("uid") != uid:
            rep.add(uid, "E_LEGACY", "legacy.v1.uid", "uid do legado diverge do registro")
        if rec.get("record_type") not in R["record_types"]:
            continue
        nivel = rec["curation"]["level"]
        prov = rec.get("provenance", {})
        for caminho, env in _envelopes(rec):
            if isinstance(env, dict):
                checar_envelope(rep, uid, nivel, caminho, env, prov)
                if caminho in ENUMS and env.get("state") == "present":
                    vals = env["v"] if isinstance(env["v"], list) else [env["v"]]
                    fora = [v for v in vals if v not in ENUMS[caminho]]
                    if fora:
                        rep.add(uid, "E_ENUM", caminho, f"{fora} fora de {ENUMS[caminho]}")
        try:
            checar_referencias(rep, uid, rec)
            checar_primarios(rep, uid, rec)
            checar_obrigatoriedade(rep, uid, rec)
            checar_bibliografia(rep, uid, rec)
        except (KeyError, TypeError) as ex:
            rep.add(uid, "E_SCHEMA", "?", f"estrutura inesperada: {ex!r}")
        for caminho, t in L.textos({k: v for k, v in rec.items() if k != "legacy"}):
            if L.HTML.search(t):
                rep.add(uid, "E_HTML", caminho, "HTML em texto")
    checar_relacoes(rep, recs)
    # estudo externo que na verdade já tem card: deveria ser relação interna por uid
    por_registro = {}
    for u, r in recs.items():
        for reg in L.valor(L.envelope(r, "identity.registrations")) or []:
            if isinstance(reg, dict) and reg.get("id"):
                por_registro.setdefault(reg["id"], set()).add(u)
    for u, r in recs.items():
        for x in r.get("external_relationships", []):
            donos = por_registro.get(x["registry_id"], set()) - {u}
            if donos:
                rep.add(u, "W_EXTERNAL_HAS_CARD", "external_relationships",
                        f"{x['registry_id']} já tem card ({sorted(donos)[0]}): usar relationships.links")
    if head is not None:
        for u in sorted(head - set(recs) - (aposentados or set())):
            rep.add(u, "E_UID_IMMUTABLE", "uid", "uid do HEAD ausente no conjunto v2")
    return rep


def carregar(pasta: pathlib.Path):
    recs, arqs = {}, {}
    for f in sorted(pasta.glob("*.json")):
        if f.name.startswith("_"):
            continue
        r = json.loads(f.read_text(encoding="utf-8"))
        recs[r["uid"]] = r
        arqs[r["uid"]] = f.name
    return recs, arqs


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=str(L.SHADOW))
    ap.add_argument("--json")
    ap.add_argument("--sem-head", action="store_true", help="não conferir uids contra o HEAD (fixtures)")
    a = ap.parse_args(argv)
    recs, arqs = carregar(pathlib.Path(a.dir))
    atuais = None if a.sem_head else {c["uid"]: c for c in L.ler_data_js(L.DATA_JS.read_text(encoding="utf-8"))[1]["studies"]}
    rep = validar(recs, arqs, None if a.sem_head else uids_head(), atuais,
                  None if a.sem_head else uids_aposentados())
    c = collections.Counter(i["codigo"] for i in rep.itens)
    niveis = collections.Counter(r["curation"]["level"] for r in recs.values())
    top = collections.Counter(i["caminho"] for i in rep.itens if i["codigo"] == "W_REQUIRED").most_common(8)
    print(json.dumps({"registros": len(recs), "niveis": dict(niveis), "codigos": dict(sorted(c.items())),
                      "erros": len(rep.erros()), "lacunas_mais_frequentes": top}, ensure_ascii=False, indent=1))
    for i in rep.erros()[:25]:
        print(f"  {i['codigo']} {i['uid']} {i['caminho']}: {i['msg']}")
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps(rep.itens, ensure_ascii=False, indent=1), encoding="utf-8")
    return 1 if rep.erros() else 0


if __name__ == "__main__":
    sys.exit(main())
