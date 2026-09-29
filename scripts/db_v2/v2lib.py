"""Biblioteca comum do Database v2 (fundação). Somente leitura do Database publicado.

- leitura/serialização do data.js exatamente como o site o grava;
- validador de JSON Schema (subconjunto do draft 2020-12 usado por schema_record_v2.json),
  para não acrescentar dependência ao repositório;
- acesso a envelopes e avaliação das condições de ativação do registro.
"""
from __future__ import annotations

import json
import pathlib
import re

AQUI = pathlib.Path(__file__).resolve().parent
SCRIPTS = AQUI.parent
SITE = SCRIPTS.parent
DATA_JS = SITE / "assets" / "js" / "data.js"
SHADOW = SCRIPTS / "_db_v2_shadow"
REGISTRY = json.loads((AQUI / "registry_v2.json").read_text(encoding="utf-8"))
SCHEMA = json.loads((AQUI / "schema_record_v2.json").read_text(encoding="utf-8"))
SCHEMA_ID = SCHEMA["properties"]["schema"]["const"]


# ── data.js ─────────────────────────────────────────────────────────────────
def ler_data_js(texto: str) -> tuple[str, dict, str]:
    """(prefixo, objeto, sufixo). O objeto é o JSON entre o primeiro '{' e o último '}'."""
    i, j = texto.index("{"), texto.rindex("}") + 1
    return texto[:i], json.loads(texto[i:j]), texto[j:]


def serializar_data_js(prefixo: str, obj: dict, sufixo: str) -> str:
    return prefixo + json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + sufixo


def canonico(obj) -> str:
    """Forma canônica para comparação estrutural (independe de ordem de chaves)."""
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


# ── JSON Schema (subconjunto) ───────────────────────────────────────────────
_TIPOS = {
    "string": lambda x: isinstance(x, str),
    "number": lambda x: isinstance(x, (int, float)) and not isinstance(x, bool),
    "integer": lambda x: isinstance(x, int) and not isinstance(x, bool),
    "object": lambda x: isinstance(x, dict),
    "array": lambda x: isinstance(x, list),
    "boolean": lambda x: isinstance(x, bool),
    "null": lambda x: x is None,
}


def validar_schema(inst, schema: dict, raiz: dict | None = None, caminho: str = "$") -> list[str]:
    """Erros como 'caminho: motivo'. Palavras-chave: $ref, type, enum, const, properties, required,
    additionalProperties, items, minItems, minLength, pattern, allOf, anyOf, oneOf."""
    raiz = raiz or schema
    erros: list[str] = []
    if "$ref" in schema:
        alvo = raiz
        for parte in schema["$ref"].lstrip("#/").split("/"):
            alvo = alvo[parte]
        erros += validar_schema(inst, alvo, raiz, caminho)
    if "type" in schema:
        tipos = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
        if not any(_TIPOS[t](inst) for t in tipos):
            return erros + [f"{caminho}: tipo {type(inst).__name__} ≠ {tipos}"]
    if "enum" in schema and inst not in schema["enum"]:
        erros.append(f"{caminho}: {inst!r} fora de {schema['enum']}")
    if "const" in schema and inst != schema["const"]:
        erros.append(f"{caminho}: {inst!r} ≠ {schema['const']!r}")
    if isinstance(inst, str):
        if "minLength" in schema and len(inst) < schema["minLength"]:
            erros.append(f"{caminho}: texto curto")
        if "pattern" in schema and not re.search(schema["pattern"], inst):
            erros.append(f"{caminho}: {inst!r} não casa {schema['pattern']}")
    if isinstance(inst, dict):
        props = schema.get("properties", {})
        for req in schema.get("required", []):
            if req not in inst:
                erros.append(f"{caminho}: falta '{req}'")
        for k, v in inst.items():
            if k in props:
                erros += validar_schema(v, props[k], raiz, f"{caminho}.{k}")
            elif schema.get("additionalProperties") is False:
                erros.append(f"{caminho}: chave não permitida '{k}'")
            elif isinstance(schema.get("additionalProperties"), dict):
                erros += validar_schema(v, schema["additionalProperties"], raiz, f"{caminho}.{k}")
    if isinstance(inst, list):
        if "minItems" in schema and len(inst) < schema["minItems"]:
            erros.append(f"{caminho}: menos de {schema['minItems']} item(ns)")
        if "items" in schema:
            for n, item in enumerate(inst):
                erros += validar_schema(item, schema["items"], raiz, f"{caminho}[{n}]")
    for sub in schema.get("allOf", []):
        erros += validar_schema(inst, sub, raiz, caminho)
    if "anyOf" in schema and not any(not validar_schema(inst, s, raiz, caminho) for s in schema["anyOf"]):
        erros.append(f"{caminho}: nenhuma alternativa de anyOf")
    if "oneOf" in schema and sum(not validar_schema(inst, s, raiz, caminho) for s in schema["oneOf"]) != 1:
        erros.append(f"{caminho}: oneOf não casa exatamente uma alternativa")
    return erros


# ── envelopes ───────────────────────────────────────────────────────────────
def envelope(rec: dict, path: str) -> dict | None:
    """Envelope de um caminho do core ('design.arms', 'endpoints'). None = ausente (= unknown)."""
    if path == "endpoints" or path == "subgroups":
        return rec.get(path)
    grupo, campo = path.split(".", 1)
    return (rec.get(grupo) or {}).get(campo)


def estado(env: dict | None) -> str:
    return (env or {}).get("state", "unknown")


def valor(env: dict | None):
    return env.get("v") if env and env.get("state") == "present" else None


def arms(rec: dict) -> list[dict]:
    return valor(envelope(rec, "design.arms")) or []


def arm_ids(rec: dict) -> set[str]:
    return {a["arm_id"] for a in arms(rec)}


def biomarcadores(rec: dict) -> list[dict]:
    return valor(envelope(rec, "population.biomarker_selection")) or []


def endpoints(rec: dict) -> list[dict]:
    return valor(rec.get("endpoints")) or []


def modulo_arms(rec: dict, mod: dict) -> list[dict]:
    if mod.get("arm_ids") == "all":
        return arms(rec)
    ids = set(mod.get("arm_ids") or [])
    return [a for a in arms(rec) if a["arm_id"] in ids]


# ── ativação ────────────────────────────────────────────────────────────────
def _familias_envolvidas(rec: dict) -> set[str]:
    ativos = [b for b in biomarcadores(rec) if b.get("rule") != "none"]  # "none" = sem biomarcador
    fam = {b["family"] for b in ativos}
    por_id = {b["id"]: b["family"] for b in ativos}
    for s in valor(envelope(rec, "design.stratification")) or []:
        if isinstance(s, dict) and s.get("family"):
            fam.add(s["family"])
    for ep in endpoints(rec):
        ref = (ep.get("population") or {}).get("biomarker_ref")
        if ref in por_id:
            fam.add(por_id[ref])
    for sg in valor(rec.get("subgroups")) or []:
        if isinstance(sg, dict) and sg.get("family"):
            fam.add(sg["family"])
    return fam


def _campo(rec: dict, mod: dict | None, campo: str):
    if campo.startswith("$module."):
        env = ((mod or {}).get("fields") or {}).get(campo.split(".", 1)[1])
    else:
        env = envelope(rec, campo)
    return env


def _valores(v) -> list:
    if isinstance(v, list):
        out = []
        for x in v:
            out += _valores(x)
        return out
    if isinstance(v, dict):
        return [v.get(k) for k in ("type", "value", "id", "family") if v.get(k) is not None] or [v]
    return [v]


def ativo(cond: dict, rec: dict, mod: dict | None = None) -> bool:
    """Avalia uma condição de ativação. Dado ausente/unknown ⇒ False (campo inativo não é cobrado)."""
    op = cond["op"]
    if op == "always":
        return True
    if op == "not":
        return not ativo(cond["cond"], rec, mod)
    if op == "any_of":
        return any(ativo(c, rec, mod) for c in cond["conds"])
    if op == "all_of":
        return all(ativo(c, rec, mod) for c in cond["conds"])
    if op == "biomarker_involved":
        return bool(_familias_envolvidas(rec) & set(cond["families"]))
    if op == "biomarker_matches_field":
        env = _campo(rec, mod, cond["field"])
        if estado(env) != "present":
            return False
        alvos = {str(x).lower() for x in _valores(env["v"])}
        return any(b["family"].lower() in alvos for b in biomarcadores(rec)
                   if b.get("rule") not in ("none", "excluded"))
    if op == "biomarker_rule_in":
        return any(b["rule"] in cond["in"] for b in biomarcadores(rec))
    if op == "subgroup_dimension_in":
        por_id = {b["id"]: b["family"] for b in biomarcadores(rec)}
        fams = {sg.get("family") for sg in valor(rec.get("subgroups")) or [] if isinstance(sg, dict)}
        fams |= {por_id.get((ep.get("population") or {}).get("biomarker_ref")) for ep in endpoints(rec)}
        return bool(fams & set(cond["in"]))
    if op == "field_in":
        env = _campo(rec, mod, cond["field"])
        return estado(env) == "present" and bool(set(map(str, _valores(env["v"]))) & set(cond["in"]))
    if op == "present":
        return estado(_campo(rec, mod, cond["field"])) == "present"
    if op == "agent_class_in":
        braços = modulo_arms(rec, mod) if mod else arms(rec)
        classes = {i.get("agent_class") for a in braços for i in a.get("interventions", [])
                   if not mod or i.get("module") in (None, mod["module"])}
        env = ((mod or {}).get("fields") or {}).get("agent_class")
        if estado(env) == "present":
            classes |= set(map(str, _valores(env["v"])))
        return bool(classes & set(cond["in"]))
    if op == "setting_in":
        env = envelope(rec, "population.setting")
        return estado(env) == "present" and bool(set(map(str, _valores(env["v"]))) & set(cond["in"]))
    if op == "rt_site_in":
        env = ((mod or {}).get("fields") or {}).get("components")
        sites = {c.get("site") for c in (valor(env) or []) if isinstance(c, dict)}
        return bool(sites & set(cond["in"]))
    raise ValueError(f"condição desconhecida: {op}")


def requisito(campo: dict, papel: str) -> str:
    return campo["requirement"].get(papel, "optional")


HTML = re.compile(r"</?[a-zA-Z][^>]*>")


def textos(obj, caminho="$"):
    """Todos os textos de um objeto, com caminho (para a checagem de HTML)."""
    if isinstance(obj, str):
        yield caminho, obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield from textos(v, f"{caminho}.{k}")
    elif isinstance(obj, list):
        for n, v in enumerate(obj):
            yield from textos(v, f"{caminho}[{n}]")
