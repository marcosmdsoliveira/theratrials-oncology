"""checks — verificações DETERMINÍSTICAS de um item de proposta contra as fontes do pacote.

Rodam antes de qualquer LLM (no curator, como pré-checagem; no verifier, de novo e de forma independente, lendo as
fontes do disco). Resultado: lista de achados {code, verdict, detail}. O pior veredito manda:
FAIL > CONFLICT > UNSUPPORTED > PASS.

Nada aqui corrige a proposta; só classifica.
"""
from __future__ import annotations

import ast
import operator
import pathlib
import re
import unicodedata

try:
    from . import agent_types as T
    from . import sources as S
except ImportError:
    import agent_types as T
    import sources as S

ORDEM = {"PASS": 0, "UNSUPPORTED": 1, "CONFLICT": 2, "FAIL": 3}


def pior(vs) -> str:
    vs = list(vs)
    return max(vs, key=lambda v: ORDEM[v]) if vs else "PASS"


def norm(t: str) -> str:
    t = unicodedata.normalize("NFKC", str(t or "")).lower()
    t = t.replace("⋅", ".").replace("·", ".").replace(" ", " ").replace(" ", " ")
    t = re.sub(r"[‐‑‒–—−]", "-", t)
    t = re.sub(r"[“”″]", '"', t)
    t = re.sub(r"[‘’′]", "'", t)
    t = re.sub(r"(\|\s*)+", "| ", t)
    return re.sub(r"\s+", " ", t).strip()


NUM = re.compile(r"(?<![\w.])(\d+(?:[.,]\d+)?)(?![\w])")
# números que costumam ser rótulo, não dado: grau, fase, linha, versão CTCAE, "1L", ordinais pequenos
ROTULO = re.compile(r"(grau|grade|g|fase|phase|linha|line|ctcae v|v|ciclo|cycle|braço|arm|step|tipo|type|coorte|cohort)"
                    r"\s*[≥≤<>=]*\s*$", re.I)


DATA = re.compile(r"\b(?:\d{4}-\d{2}(?:-\d{2})?|\d{1,2}/\d{1,2}/\d{2,4}|\d{1,2}/\d{4}|\d{4}/\d{1,2})\b")
IDENTIFICADOR = re.compile(r"\b[A-Za-z][A-Za-z0-9]*-\d+[A-Za-z]?\b|\b(?:LBA|abstract|resumo|NCT|PMID)\s*\d+", re.I)


def numeros(texto: str) -> list[str]:
    """Números que exigem lastro. Datas, identificadores (NOME-123, LBA/NCT/PMID nnn), anos e rótulos ficam de fora:
    a semântica deles é conferida pelo verifier."""
    out = []
    t = IDENTIFICADOR.sub(" ", DATA.sub(" ", str(texto or "")))
    for m in NUM.finditer(t):
        antes = t[max(0, m.start() - 12):m.start()]
        v = m.group(1).replace(",", ".")
        if ROTULO.search(antes) or re.match(r"^\d$", v) or re.fullmatch(r"(19|20)\d\d", v):
            continue                                     # rótulo, dígito isolado ou ano: não exigido na evidência
        out.append(v)
    return out


def _num_no_texto(v: str, t: str) -> bool:
    alvo = {v, v.replace(".", ",")}
    if "." in v:
        inteiro, dec = v.split(".")
        alvo |= {f"{inteiro}.{dec.rstrip('0')}".rstrip("."), f"{inteiro}⋅{dec}", f"{inteiro}·{dec}"}
        if inteiro == "0":                                # grafia de periódico: "P = .04", "·04"
            alvo |= {f".{dec}", f"·{dec}"}
    return any(re.search(rf"(?<![\d]){re.escape(a)}(?![\d])", t) for a in alvo)


_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv}


def avaliar(regra: str, vals: dict[str, float]) -> float:
    """Avalia a regra aritmética da derivação (só + − × ÷ e nomes de operandos)."""
    expr = regra.split("=")[0].strip()

    def ev(n):
        if isinstance(n, ast.Expression):
            return ev(n.body)
        if isinstance(n, ast.BinOp) and type(n.op) in _OPS:
            return _OPS[type(n.op)](ev(n.left), ev(n.right))
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
            return n.value
        if isinstance(n, ast.Name) and n.id in vals:
            return vals[n.id]
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.USub):
            return -ev(n.operand)
        raise ValueError(f"expressão não permitida: {ast.dump(n)[:60]}")
    return float(ev(ast.parse(expr, mode="eval")))


def conferir_item(item: dict, fontes: dict[str, dict], pasta: pathlib.Path) -> list[dict]:
    """fontes: {source_id: {source_type, path, text_level}} do pacote. Retorna achados."""
    achados = []

    def add(code, verdict, detail):
        achados.append({"code": code, "verdict": verdict, "detail": detail})

    evid = item.get("evidence") or []
    if item.get("conflict"):
        add("CONFLICT_DECLARED", "CONFLICT", item["conflict"].get("description", "conflito declarado"))
    if not evid and item.get("change_kind") != "none":
        if item.get("absence_checked_in"):
            fs = [fontes.get(s) for s in item["absence_checked_in"]]
            if not fs or any(f is None or f["text_level"] == "abstract" for f in fs):
                add("ABSENCE_WEAK", "UNSUPPORTED", "ausência só se verifica em texto completo ou registro do pacote")
            else:
                add("ABSENCE_CLAIM", "UNSUPPORTED" if item.get("value_origin") != "editorial" else "PASS",
                    "remoção por ausência na fonte: exige confirmação semântica do verifier")
        else:
            add("NO_EVIDENCE", "UNSUPPORTED", "proposta sem evidência")
    textos = []
    for i, e in enumerate(evid):
        f = fontes.get(e.get("source_id"))
        if e.get("source_type") in T.FORBIDDEN_SOURCES or (e.get("source_id") or "").lower().startswith(
                ("tracker", "explorer")):
            add("SOURCE_FORBIDDEN", "FAIL", f"evidência[{i}] usa fonte proibida {e.get('source_id')}")
            continue
        if f is None:
            add("SOURCE_UNKNOWN", "FAIL", f"evidência[{i}] cita fonte fora do pacote: {e.get('source_id')}")
            continue
        if e.get("source_type") != f["source_type"]:
            add("SOURCE_TYPE", "FAIL", f"evidência[{i}] declara {e.get('source_type')}, fonte é {f['source_type']}")
        pars = S.ler_paragrafos(pasta / f["path"])
        texto = norm(" ".join(pars.values()))
        partes = [norm(p) for p in re.split(r"…|\.\.\.", e.get("snippet") or "") if norm(p)]
        pos, ok = 0, bool(partes)
        for p in partes:
            j = texto.find(p, pos)
            if j < 0:
                ok = False
                break
            pos = j + len(p)
        if not ok:
            add("SNIPPET_NOT_FOUND", "FAIL", f"evidência[{i}]: trecho não está literalmente em {e['source_id']}")
            continue
        m = re.search(r"¶(\d{4})", e.get("locator") or "")
        if m:
            vizinhos = [pars.get(f"{int(m.group(1)) + d:04d}", "") for d in (-1, 0, 1)]
            if partes and partes[0] not in norm(" ".join(vizinhos)):
                add("LOCATOR_MISMATCH", "FAIL", f"evidência[{i}]: trecho não está em {m.group(0)} (±1)")
        else:
            add("LOCATOR_WEAK", "PASS", f"evidência[{i}]: localizador sem ¶ (aceito, menos preciso)")
        textos.append(norm(e.get("snippet")))
    der = item.get("derivation")
    if item.get("value_origin") == "derived":
        if not der:
            add("DERIVATION_MISSING", "FAIL", "valor derived sem operandos/regra/resultado")
        else:
            try:
                vals = {o["name"]: float(o["value"]) for o in der["operands"]}
                r = avaliar(der["rule"], vals)
                tol = max(0.05 * abs(der["result"]), 0.051)
                if abs(r - der["result"]) > tol:
                    add("DERIVATION_WRONG", "FAIL", f"regra dá {r:.4g}, resultado declarado {der['result']}")
                for o in der["operands"]:
                    k = o.get("evidence_index")
                    if k is None or k >= len(evid) or not _num_no_texto(f"{o['value']:g}".replace(",", "."),
                                                                      norm(evid[k].get("snippet"))):
                        add("OPERAND_UNSUPPORTED", "FAIL", f"operando {o['name']}={o['value']} não está na evidência {k}")
            except (ValueError, KeyError, SyntaxError, ZeroDivisionError) as ex:
                add("DERIVATION_UNEVALUABLE", "FAIL", f"regra não avaliável: {ex}")
    elif der:
        add("DERIVATION_ON_REPORTED", "FAIL", "derivation em valor declarado como reported/editorial")
    # sem evidência nenhuma já é UNSUPPORTED (NO_EVIDENCE)
    if evid and item.get("change_kind") in ("replace", "append") and item.get("proposed_value") not in (None, ""):
        base = " ".join(textos)
        extras = set()
        if der:
            extras = {f"{der['result']:g}", *(f"{o['value']:g}" for o in der["operands"])}
        falta = [v for v in numeros(item["proposed_value"] if isinstance(item["proposed_value"], str)
                                    else str(item["proposed_value"]))
                 if not _num_no_texto(v, base) and not any(abs(float(v) - float(x)) < 0.051 for x in extras)]
        if falta:
            # número fora dos trechos CITADOS = proveniência insuficiente (UNSUPPORTED); contradição é papel do FAIL
            add("NUMBER_UNSUPPORTED", "UNSUPPORTED", f"números sem lastro nos trechos citados: {sorted(set(falta))[:8]}")
    if not achados:
        add("DETERMINISTIC_OK", "PASS", "trechos literais, localizadores e números conferem")
    return achados
