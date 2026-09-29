"""sufficiency — matriz de suficiência de fonte por campo e política de automação (determinístico).

Regra central: a fonte disponível tem de sustentar EXPLICITAMENTE a afirmação proposta. Não se exige texto completo
por princípio; exige-se que o que foi proposto esteja escrito na fonte. O que não está → UNSUPPORTED/WATCH, nunca
inferência.

Classes de campo:
  metadata  — identidade/bibliografia/status: metadados estruturados (PubMed, registro) bastam e são conferidos
              deterministicamente;
  abstract  — o resumo basta SE o valor estiver explicitamente reportado nele (ORR, HR, medianas, n, desfecho
              primário, seguimento, EAs apresentados);
  detail    — exige evidência detalhada (critérios complexos, atribuição de toxicidade, esquema/dose/ciclos, α e
              hierarquia, crossover, análises por braço/subgrupo). Com só o resumo, passa apenas se o verifier
              marcar sustentação EXPLÍCITA de todo o valor proposto;
  human     — fora da automação nesta fase (ex.: impacto regulatório: exige fonte regulatória que o pacote não tem).
              Proposta vira WATCH, nunca alteração factual.
Afirmação de AUSÊNCIA ("sem X", remoção por falta de lastro) exige texto completo ou registro, em qualquer classe.
"""
from __future__ import annotations

CLASSE = {
    # metadados
    "ano_pub": "metadata", "pubmed_url": "metadata", "nct": "metadata", "titulo_full": "metadata",
    "ref": "metadata", "status": "metadata", "periodo": "metadata", "sponsor": "metadata", "centros": "metadata",
    "estudo": "metadata", "acron": "metadata",
    # resumo basta se explícito
    "primario": "abstract", "resultado_chave": "abstract", "n": "abstract", "secundario": "abstract",
    "tox_g3": "abstract", "indicacao": "abstract", "desenho": "abstract", "linha": "abstract", "fase": "abstract",
    # detalhe
    "incl": "detail", "excl": "detail", "esquema": "detail", "cumul": "detail", "estatistica": "detail",
    "analises": "detail", "subgrupo": "detail", "tox_interesse": "detail", "comparador": "detail",
    "estrat": "detail", "basal": "detail", "molecular": "detail", "biomarc": "detail", "preparo": "detail",
    "radiofarmaco": "detail", "limit": "detail", "takehome": "detail",
    # fora da automação nesta fase
    "impacto_reg": "human",
}
CAMPOS_CLINICOS = {"primario", "secundario", "resultado_chave", "tox_g3", "tox_interesse", "comparador",
                   "radiofarmaco", "esquema", "cumul", "n", "basal", "incl", "excl", "estatistica", "analises",
                   "subgrupo", "indicacao", "molecular", "biomarc", "desenho", "linha", "estrat", "takehome",
                   "preparo", "limit"}
NIVEL_FONTE = {"metadata": 0, "abstract": 1, "registry": 2, "fulltext": 2}


def classe(campo: str) -> str:
    return CLASSE.get(campo, "detail")


def avaliar(item: dict, fontes: dict[str, dict], semantico_support: str | None) -> tuple[str, str]:
    """(veredito máximo permitido pela suficiência, motivo). 'PASS' = sem restrição."""
    c = classe(item.get("field", ""))
    if c == "human":
        return "UNSUPPORTED", "campo fora da automação nesta fase (human-only): vira WATCH"
    niveis = [fontes[e["source_id"]]["text_level"] for e in item.get("evidence") or [] if e.get("source_id") in fontes]
    if item.get("change_kind") == "remove" or item.get("absence_checked_in"):
        base = [fontes[s]["text_level"] for s in item.get("absence_checked_in") or [] if s in fontes] or niveis
        if not base or all(NIVEL_FONTE.get(n, 0) < 2 for n in base):
            return "UNSUPPORTED", "afirmação de ausência exige texto completo ou registro"
    if semantico_support is not None and semantico_support != "explicit":
        return "UNSUPPORTED", f"verifier: sustentação {semantico_support}, não explícita"
    if c == "detail" and niveis and all(n in ("abstract", "metadata") for n in niveis) and semantico_support != "explicit":
        return "UNSUPPORTED", "campo de detalhe sustentado só pelo resumo, sem confirmação explícita"
    return "PASS", ""
