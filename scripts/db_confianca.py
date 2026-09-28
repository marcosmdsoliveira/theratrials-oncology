#!/usr/bin/env python3
"""
db_confianca.py — Fase 1.5: verificação de identidade por máquina, automação
por domínio, prioridade dos sinais e inbox. Só leitura; não usa LLM.

NÍVEIS DE ORIGEM (do mais fraco ao mais forte para uso automático):
  inferred         regra do pipeline, sem verificação independente;
  explicit         a fonte diz (título, tipo de publicação, trecho literal);
  machine_verified fato de IDENTIDADE ou RELAÇÃO BIBLIOGRÁFICA demonstrado por
                   fontes estruturadas independentes, sem conflito entre elas.
                   Não é confirmação clínica e nunca vale para extração clínica;
  human_confirmed  decisão humana em db_decisoes.json.

FAMÍLIAS DE EVIDÊNCIA (independentes entre si):
  A  ligação PubMed: PMID em `NCT[si]`, NCT no DataBank do artigo ou referência
     DERIVED do CT.gov. As três saem do MESMO metadado do PubMed e contam como
     uma família só.
  B  ligação declarada pelo patrocinador: referência RESULT no CT.gov.
  C  o acrônimo do card está no registro do CT.gov (acrônimo ou título).
  D  ancoragem numérica forte: números do `primario` do card no abstract.
  E  o `titulo_full` do card é idêntico ao título do artigo no PubMed.
  F  o acrônimo do card está no título/abstract do artigo.

  C e F usam o NOME do estudo escrito pelo editor — independem do PMID. D e E
  NÃO: o `titulo_full` e os números costumam ter sido copiados do próprio
  artigo citado, e quando o PMID está errado eles vêm errados junto (a
  auditoria achou cards com o título do artigo de outro estudo). D e E provam
  que o conteúdo do card saiu daquele artigo, não que o artigo seja do estudo;
  por isso nenhuma regra de identidade usa D ou E sem C, F ou ligação.

REGRAS DE IDENTIDADE (conjunções explícitas; nenhuma nota numérica). Só se
aplicam sem conflito. Conflito = DataBank do artigo declara outro NCT, mesmo
PMID em cards sem NCT em comum, PMID ou NCT inexistente, título de outra
coorte, DOI divergente entre PubMed e ID Converter.
  MV-1  A ∧ B ∧ (C ∨ D ∨ E ∨ F)   duas ligações independentes + uma
                                  concordância do card
  MV-2  (A ∨ B) ∧ C ∧ (D ∨ E ∨ F)  ligação + card↔registro + card↔artigo
  MV-3  (A ∨ B) ∧ E ∧ D            ligação + card↔artigo por duas vias
  MV-4  ¬A ∧ ¬B ∧ C ∧ E ∧ (D ∨ F)  metadado sem ligação (artigo antigo), mas o
                                  card casa com o registro E com o artigo
  MV-5  sem registro ∧ E ∧ D       estudo não registrado: título idêntico +
                                  números
  MV-6  sem PMID ∧ C               card de desenho/abstract: o registro existe
                                  e é o do acrônimo do card

AUTOMAÇÃO POR DOMÍNIO — `autorizado` diz se o fato pode ser usado
automaticamente DENTRO do pipeline (arquivar, deduplicar, acompanhar). Nenhuma
escrita no Database publicado é autorizada nesta fase:
  identity, bibliographic_metadata, publication_relationship — autorizados só
    com machine_verified/human_confirmed e sem conflito;
  clinical_extraction — nunca autorizado nesta fase;
  published_write — nunca autorizado nesta fase.
"""
from __future__ import annotations

import re
from collections import Counter, defaultdict
from datetime import date, timedelta

import db_registro as R

MV, HUMAN, EXPLICIT, INFERRED = "machine_verified", "human_confirmed", "explicit", "inferred"
DOMINIOS = ("identity", "bibliographic_metadata", "publication_relationship",
            "clinical_extraction", "published_write")
CONFLITOS = ("databank_divergente", "pmid_compartilhado", "pmid_inexistente",
             "nct_inexistente", "coorte_divergente", "doi_divergente")

# Siglas genéricas que não identificam um estudo.
GENERICOS = {"PRRT", "SBRT", "SABR", "TARE", "SIRT", "TACE", "PSMA", "HCC", "NET", "NSCLC", "SCLC",
             "RCC", "ADT", "ARPI", "PET", "IMRT", "RLT", "CAR", "ORR", "PFS", "OS", "DLBCL", "AML",
             "LMA", "PPGL", "MIBG", "COG", "EORTC", "SWOG", "NRG", "RTOG", "ECOG", "UK", "EUA",
             "FDA", "EMA", "HNSCC", "TNBC", "HER2", "MSI", "NTRK", "BRAF", "EGFR", "ALK", "KRAS"}


# ── Utilidades ──────────────────────────────────────────────────────────────

def compacto(t: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(t or "").lower())


def acronimos(card: dict) -> list[str]:
    """Siglas do estudo tiradas de `estudo`/`acron`: segmentos antes de "(",
    separados por " — ", "/" ou "·"; cada um com dígito, ou ≥4 maiúsculas, ou
    palavra única com ≥2 maiúsculas (LuTectomy); fora de GENERICOS."""
    out = []
    for campo in (card.get("estudo"), card.get("acron")):
        base = re.split(r"\s*\(", str(campo or ""))[0]
        for parte in re.split(r"\s+[—–]\s+|\s*/\s*|\s*·\s*", base):
            parte = parte.strip(" .,:;")
            if not (3 <= len(parte) <= 30) or len(parte.split()) > 3:
                continue
            if parte.upper() in GENERICOS or not re.search(r"[A-Z]", parte):
                continue
            candidatos = [parte]
            primeiro = parte.split()[0]
            # "KEYNOTE-158 endométrio" → também "KEYNOTE-158". Só com dígito: "MGMT em
            # PPGL" daria "MGMT", que é nome de gene, não de estudo.
            if " " in parte and re.search(r"\d", primeiro) and re.search(r"[A-Za-z]", primeiro):
                candidatos.append(primeiro)
            for cand in candidatos:
                maius = sum(ch.isupper() for ch in cand)
                if cand.upper() in GENERICOS:
                    continue
                if re.search(r"\d", cand) and re.search(r"[A-Za-z]", cand) or maius >= 4 or \
                        (" " not in cand and maius >= 2):
                    if len(compacto(cand)) >= 4 and cand not in out:
                        out.append(cand)
    return out


def padrao(sigla: str) -> re.Pattern:
    """Sigla só de letras (CLEAR, LASER, TITAN) pode ser palavra comum: casa
    sensível a maiúsculas, como escrita no card. Com dígito ou hífen, não."""
    partes = re.findall(r"[A-Za-z0-9]+", sigla)
    flags = 0 if re.fullmatch(r"[A-Za-z]+", sigla) else re.I
    return re.compile(r"(?<![A-Za-z0-9])" + r"[\s\-–:/]*".join(map(re.escape, partes))
                      + r"(?![A-Za-z0-9])", flags)


def sigla_em(siglas: list[str], texto: str, acronimo_registro: str = "") -> str | None:
    for s in siglas:
        if acronimo_registro and compacto(s) == compacto(acronimo_registro):
            return s
        if padrao(s).search(texto or ""):
            return s
    return None


def sigla_no_registro(siglas: list[str], c: dict | None) -> str | None:
    c = c or {}
    return sigla_em(siglas, f"{c.get('titulo_breve', '')} {c.get('titulo_oficial', '')}",
                    c.get("acronimo", ""))


def autor_ano(card: dict, art: dict) -> str | None:
    """G: o nome do card traz "(Sobrenome, AAAA)" e o PubMed confirma o
    primeiro autor e o ano — âncora escrita pelo editor, independente do PMID."""
    m = re.search(r"\(([A-ZÀ-Ý][\w'\-]+)[^)]*?(19|20)(\d\d)", str(card.get("estudo") or ""))
    autor = compacto(art.get("primeiro_autor"))
    if m and autor and compacto(m.group(1)) == autor and (art.get("data") or "")[:4] == m.group(2) + m.group(3):
        return f"autor/ano do nome do card ({m.group(1)}, {m.group(2)}{m.group(3)}) confirmados no PubMed"
    return None


def titulo_igual(card: dict, art: dict | None) -> bool:
    a, b = compacto(card.get("titulo_full")), compacto((art or {}).get("titulo"))
    return len(a) >= 20 and a == b


def texto_ctgov(c: dict | None) -> str:
    c = c or {}
    return " ".join([c.get("acronimo", ""), c.get("titulo_breve", ""), c.get("titulo_oficial", "")])


# ── Conflito dentro da mesma fonte ──────────────────────────────────────────

WSC = "WITHIN_SOURCE_CONFLICT"
DIMENSOES_CONTEXTO = ("populacao", "denominador", "endpoint", "timepoint", "metodo")


def _decimais(v) -> int:
    s = str(v)
    return len(s.split(".")[1]) if "." in s else 0


def arredondamento(valores: list) -> bool:
    """Todos os valores numéricos coincidem quando arredondados à precisão do
    menos preciso (5,9 e 6 → sim; 17,4 e 17,6 → não)."""
    try:
        nums = [float(v) for v in valores]
    except (TypeError, ValueError):
        return False
    d = min(_decimais(v) for v in valores)
    return len({round(x, d) for x in nums}) == 1


def avaliar_conflito_na_fonte(ocorrencias: list[dict]) -> dict:
    """Duas ou mais partes da MESMA fonte primária dão valores para a mesma
    medida. Classe:
      CONSISTENTE            — mesmo valor;
      EXPLICADA              — contexto diferente (população, denominador,
                               endpoint, timepoint ou método) ou arredondamento:
                               registra o contexto, não bloqueia;
      WITHIN_SOURCE_CONFLICT — mesmo contexto em tudo e valores incompatíveis:
                               bloqueia aquele campo para automação clínica e
                               o card não pode apresentar um dos valores como fato.
    Nunca autoriza atualização clínica automática, em nenhuma classe."""
    valores = [o["valor"] for o in ocorrencias]
    if len({str(v) for v in valores}) == 1:
        return {"classe": "CONSISTENTE", "valores": valores, "diferencas": [], "bloqueia_campo": False}
    faltam = [d for d in DIMENSOES_CONTEXTO if any(o.get(d) in (None, "") for o in ocorrencias)]
    if faltam:
        return {"classe": WSC, "valores": valores, "diferencas": [], "bloqueia_campo": True,
                "motivo": f"contexto não documentado para: {', '.join(faltam)} — comparar antes de explicar"}
    diferencas = [d for d in DIMENSOES_CONTEXTO if len({str(o[d]) for o in ocorrencias}) > 1]
    if diferencas:
        return {"classe": "EXPLICADA", "valores": valores, "diferencas": diferencas, "bloqueia_campo": False,
                "motivo": "medidas diferentes: " + "; ".join(
                    f"{d}: " + " × ".join(str(o[d]) for o in ocorrencias) for d in diferencas)}
    if arredondamento(valores):
        return {"classe": "EXPLICADA", "valores": valores, "diferencas": ["arredondamento"],
                "bloqueia_campo": False, "motivo": "mesma medida, precisões diferentes"}
    return {"classe": WSC, "valores": valores, "diferencas": [], "bloqueia_campo": True,
            "motivo": "mesma população, denominador, endpoint, timepoint e método, com valores incompatíveis"}


def aplicar_conflitos_na_fonte(registro: dict, achados: list[dict]) -> None:
    """Achados de db_conflitos_fonte.json, válidos enquanto o card citar a
    mesma publicação. Um WITHIN_SOURCE_CONFLICT bloqueia só o campo afetado."""
    regs = {r["uid"]: r for r in registro["cards"]}
    for a in achados:
        reg = regs.get(a["uid"])
        if not reg or str(a.get("pmid")) != str(reg["pmid_atual"]):
            continue
        res = avaliar_conflito_na_fonte(a["ocorrencias"])
        reg.setdefault("conflitos_na_fonte", []).append({"id": a["id"], "campos": a["campos"],
                                                         "medida": a["medida"], **res})
        if res["bloqueia_campo"]:
            ce = reg["automation"]["clinical_extraction"]
            ce["autorizado"] = False
            ce.setdefault("campos_bloqueados", [])
            for c in a["campos"]:
                if c not in ce["campos_bloqueados"]:
                    ce["campos_bloqueados"].append(c)


# ── Evidência e identidade ──────────────────────────────────────────────────

def evidencias(reg: dict, card: dict, coleta: dict) -> dict:
    """Famílias A–F e conflitos de um card. Cada família traz o porquê."""
    ids, pmid = reg["identidade"], reg["pmid_atual"]
    art = coleta["artigos"].get(pmid) if pmid else None
    rep = reg["publicacao_representada"] or {}
    lig = set(rep.get("ligacao") or [])
    siglas = acronimos(card)
    ev: dict[str, str | None] = {k: None for k in "ABCDEF"}
    if lig & {"pubmed_si", "databank", "ctgov_derived"}:
        ev["A"] = "ligação PubMed: " + ", ".join(sorted(lig & {"pubmed_si", "databank", "ctgov_derived"}))
    if "ctgov_result" in lig:
        ev["B"] = "RESULT declarado no CT.gov"
    for n in ids["nct"]:
        s = sigla_no_registro(siglas, coleta["ctgov"].get(n))
        if s:
            ev["C"] = f"{s!r} no registro {n}"
            break
    if (reg["analise"].get("ancoragem") or {}).get("nivel") == "forte":
        a = reg["analise"]["ancoragem"]
        ev["D"] = f"{a['achados']}/{a['numeros_card']} números do primario no abstract"
    if titulo_igual(card, art):
        ev["E"] = "titulo_full idêntico ao título do PubMed"
    if art:
        s = sigla_em(siglas, f"{art.get('titulo', '')} {art.get('resumo', '')}")
        if s:
            ev["F"] = f"{s!r} no título/abstract do artigo"
    if art:
        g = autor_ano(card, art)
        if g:
            ev["G"] = g
    ev["_siglas"] = bool(siglas)
    conflitos = [m for m in reg["motivos_revisao"] if m.startswith(CONFLITOS)]
    if pmid and art:
        d_idconv = coleta["idconv"].get(pmid, {}).get("doi")
        if d_idconv and art.get("doi") and d_idconv.lower() != art["doi"].lower():
            conflitos.append(f"doi_divergente: PubMed {art['doi']} × ID Converter {d_idconv}")
    return {"familias": ev, "siglas": siglas, "conflitos": conflitos}


REGRAS_IDENTIDADE = [
    ("MV-1", "ligação PubMed e RESULT do CT.gov (duas ligações independentes) + concordância do card",
     lambda e, reg: e["A"] and e["B"] and (e["C"] or e["F"] or e["D"] or e["E"])),
    ("MV-2", "ligação de registro + nome do estudo no registro + card↔artigo",
     lambda e, reg: (e["A"] or e["B"]) and e["C"] and (e["F"] or e["D"] or e["E"])),
    ("MV-3", "ligação de registro + nome do estudo no artigo + conteúdo do card saído do artigo",
     lambda e, reg: (e["A"] or e["B"]) and e["F"] and (e["D"] or e["E"])),
    ("MV-3b", "ligação ao NCT do card + conteúdo do card saído do artigo (card sem nome de estudo)",
     lambda e, reg: (e["A"] or e["B"]) and not e.get("_siglas") and e["D"] and e["E"]),
    ("MV-4", "sem ligação nos metadados (artigo antigo), mas nome do estudo no registro E no artigo",
     lambda e, reg: not e["A"] and not e["B"] and e["C"] and e["F"] and (e["D"] or e["E"])),
    ("MV-5", "estudo sem registro: autor/ano do nome do card no PubMed + conteúdo saído do artigo",
     lambda e, reg: reg["identidade"]["situacao"] not in ("nct_unico", "nct_multiplo", "isrctn")
     and e.get("G") and (e["D"] or e["E"])),
    ("MV-6", "card sem PMID: acrônimo do card no registro",
     lambda e, reg: not reg["pmid_atual"] and e["C"]),
]


def identidade(reg: dict, ev: dict) -> dict:
    f = ev["familias"]
    if ev["conflitos"]:
        return {"nivel": "conflito", "regra": None, "autorizado": False,
                "evidencias": {k: v for k, v in f.items() if v and not k.startswith("_")},
                "conflitos": ev["conflitos"]}
    if not reg["pmid_atual"] and reg["identidade"]["situacao"] not in ("nct_unico", "nct_multiplo", "isrctn"):
        return {"nivel": "insuficiente", "regra": None, "autorizado": False,
                "evidencias": {}, "conflitos": [], "falta": "card sem PMID e sem registro"}
    visiveis = {k: v for k, v in f.items() if v and not k.startswith("_")}
    for rid, descr, cond in REGRAS_IDENTIDADE:
        if cond(f, reg):
            return {"nivel": MV, "regra": f"{rid}: {descr}", "autorizado": True,
                    "evidencias": visiveis, "conflitos": []}
    presentes = sorted(visiveis)
    return {"nivel": "insuficiente", "regra": None, "autorizado": False,
            "evidencias": visiveis, "conflitos": [],
            "falta": razao_insuficiente(reg, presentes)}


def razao_insuficiente(reg: dict, presentes: list[str]) -> str:
    """A razão exata, para agrupar o que sobra."""
    reg_ok = reg["identidade"]["situacao"] in ("nct_unico", "nct_multiplo", "isrctn")
    lig = "A" in presentes or "B" in presentes
    card_reg = "C" in presentes
    card_art = [x for x in presentes if x in "DEF"]
    if not reg_ok:
        return "sem registro e sem autor/ano do nome do card confirmado no PubMed"
    if lig and not card_reg and "F" not in presentes and not card_art:
        return "ligado ao registro, mas nada no card concorda com registro ou artigo"
    if lig and not card_reg and "F" not in presentes:
        return "ligado ao registro; conteúdo do card saiu do artigo, mas o nome do estudo não aparece no registro nem no artigo"
    if lig and not card_reg:
        return "ligado ao registro, nome do estudo no artigo, mas conteúdo do card não confere com o abstract"
    if lig and card_reg:
        return "ligado ao registro e sigla no registro, mas nada no card concorda com o artigo"
    if not lig and card_reg:
        return "PMID sem ligação ao registro nos metadados; card casa com o registro, mas não com o artigo por duas vias"
    return "PMID sem ligação ao registro e card sem sigla no registro"


def bibliografico(reg: dict, card: dict, coleta: dict) -> dict:
    """PMID↔DOI↔periódico↔data. MV-B: DOI do PubMed confirmado por outra
    fonte (Crossref resolveu o DOI ou o ID Converter devolveu o mesmo DOI)."""
    pmid = reg["pmid_atual"]
    if not pmid:
        return {"nivel": "nao_aplicavel", "autorizado": False, "divergencias": []}
    art = coleta["artigos"].get(pmid) or {}
    div = []
    ano_art = (art.get("data") or "")[:4]
    try:
        ano_card = int(card.get("ano_pub") or 0)
    except (TypeError, ValueError):
        ano_card = 0
    if ano_card and ano_art and abs(ano_card - int(ano_art)) > 1:
        div.append(f"ano_pub {ano_card} × PubMed {ano_art}")
    if reg["identidade"]["situacao"] not in ("nct_unico", "nct_multiplo", "isrctn"):
        declarados = [r for r in art.get("registros", []) if r.startswith(("NCT", "ISRCTN"))]
        if declarados:
            div.append(f"card sem registro; o artigo declara {', '.join(declarados)}")
    doi = art.get("doi")
    confirmacoes = []
    if doi and doi in coleta.get("crossref", {}) and coleta["crossref"][doi] is not None:
        confirmacoes.append("Crossref resolve o DOI")
    if doi and coleta["idconv"].get(pmid, {}).get("doi", "").lower() == doi.lower():
        confirmacoes.append("ID Converter devolve o mesmo DOI")
    conflito = [c for c in [coleta["idconv"].get(pmid, {}).get("doi")] if c and doi and c.lower() != doi.lower()]
    if conflito:
        return {"nivel": "conflito", "autorizado": False, "divergencias": div,
                "conflitos": [f"DOI PubMed {doi} × ID Converter {conflito[0]}"]}
    if doi and confirmacoes:
        return {"nivel": MV, "regra": "MV-B: DOI do PubMed confirmado por " + " e ".join(confirmacoes),
                "autorizado": True, "divergencias": div}
    return {"nivel": EXPLICIT if doi else "insuficiente", "autorizado": False, "divergencias": div,
            "falta": None if doi else "PubMed sem DOI"}


def relacao(reg: dict, ident: dict) -> dict:
    """Relação da publicação representada com o estudo.
    MV-R1: identidade verificada ∧ relação explícita (tipo de publicação ou título).
    MV-R2: identidade verificada ∧ primeiro relato TIPADO como ensaio ligado ao
           registro ∧ nenhum artigo ligado anterior que pudesse ser relato."""
    rep = reg["publicacao_representada"]
    if not rep or not rep.get("pmid"):
        return {"nivel": "nao_aplicavel", "autorizado": False}
    rel, origem = rep["relacao"], rep["relacao_origem"]
    if ident["nivel"] not in (MV, HUMAN):
        return {"nivel": origem or "insuficiente", "valor": rel, "autorizado": False,
                "falta": "identidade não verificada"}
    if origem == EXPLICIT:
        return {"nivel": MV, "valor": rel, "regra": "MV-R1: identidade verificada + relação explícita",
                "autorizado": True}
    if origem == HUMAN:
        return {"nivel": HUMAN, "valor": rel, "autorizado": True}
    if rel == "primary_publication":
        pubs = reg["publicacoes"]
        idx = next(i for i, p in enumerate(pubs) if p["pmid"] == rep["pmid"])
        anteriores = [p for p in pubs[:idx] if p["ligacao"] and p["natureza"] in ("relato_de_ensaio", "artigo")
                      and p["relacao"] not in ("protocol", "secondary_analysis", "subgroup", "qol", "safety")
                      and p["coorte"] is not False]
        rep_pub = pubs[idx]
        if rep_pub["natureza"] == "relato_de_ensaio" and not anteriores:
            return {"nivel": MV, "valor": rel, "autorizado": True,
                    "regra": "MV-R2: identidade verificada + primeiro relato tipado, sem relato ligado anterior"}
        return {"nivel": INFERRED, "valor": rel, "autorizado": False,
                "falta": "relato sem tipo indexado" if rep_pub["natureza"] != "relato_de_ensaio"
                else f"{len(anteriores)} artigo(s) ligado(s) anterior(es) sem classificação"}
    return {"nivel": origem or "insuficiente", "valor": rel, "autorizado": False}


def clinico(reg: dict) -> dict:
    a = reg["analise"]
    return {"nivel": reg["origem_classificacao"], "tipo": a["tipo"], "maturidade": a["maturidade"],
            "populacao": a["populacao"], "endpoint": (a["endpoint"] or {}).get("valores"),
            "autorizado": False, "motivo": "extração clínica não é automatizada nesta fase"}


# ── Revisão por domínio ─────────────────────────────────────────────────────

CLINICO_SOB_DEMANDA = ("tipo_indeterminado", "maturidade_indeterminada", "ref_cita_outra_publicacao",
                       "populacao_indeterminada")
EDITORIAL = ("pmid_e_", "pmid_nao_e_relato", "status_x_pmid", "registro_parcial")
WATCH = ("desenho_com_publicacao", "resultados_no_ctgov")


def separar_revisao(reg: dict, ident: dict) -> dict:
    """Reparte os motivos do registro por domínio. Só `agora` pede decisão."""
    out = {"agora": [], "identidade_insuficiente": [], "clinico_sob_demanda": [], "editorial": [],
           "watch": []}
    for m in reg["motivos_revisao"]:
        if m.startswith(CONFLITOS) or m.startswith("publicado_sem_pmid"):
            out["agora"].append(m)
        elif m.startswith(("pmid_nao_ligado", "sem_ancoragem")):
            (out["clinico_sob_demanda"] if ident["nivel"] in (MV, HUMAN)
             else out["identidade_insuficiente"]).append(m)
        elif m.startswith(CLINICO_SOB_DEMANDA):
            out["clinico_sob_demanda"].append(m)
        elif m.startswith(EDITORIAL):
            out["editorial"].append(m)
        elif m.startswith(WATCH):
            out["watch"].append(m)
        else:
            out["agora"].append(m)
    if ident["nivel"] == "insuficiente" and not out["identidade_insuficiente"]:
        out["identidade_insuficiente"].append(f"identidade: {ident.get('falta')}")
    return out


def anotar(registro: dict, dados: dict, coleta: dict, decisoes: list[dict] | None = None) -> None:
    """Acrescenta `automation`, `evidencia` e `revisao` a cada card."""
    cards = {s["uid"]: s for s in dados["studies"]}
    for reg in registro["cards"]:
        card = cards[reg["uid"]]
        ev = evidencias(reg, card, coleta)
        ident = identidade(reg, ev)
        reg["evidencia"] = {"siglas": ev["siglas"],
                            "familias": {k: v for k, v in ev["familias"].items() if not k.startswith("_")}}
        reg["automation"] = {
            "identity": ident,
            "bibliographic_metadata": bibliografico(reg, card, coleta),
            "publication_relationship": relacao(reg, ident),
            "clinical_extraction": clinico(reg),
            "published_write": {"autorizado": False,
                                "motivo": "nenhuma escrita no Database publicado nesta fase"},
        }
        reg["revisao"] = separar_revisao(reg, ident)
        graves = [a for a in reg["avisos"] if a["tipo"] in ("retratacao", "expressao_de_preocupacao")]
        liberacao = next((d for d in (decisoes or []) if d["id"] == f"integrity_hold:{reg['uid']}"
                          and d["tipo"] == "approve"), None)
        quarentena = reg.get("quarentena_editorial")
        motivos = [f"{a['tipo']} ({a.get('doi') or a.get('pmid')})" for a in graves] if not liberacao else []
        if quarentena:
            motivos.append(f"quarentena editorial ({quarentena['id']})")
        reg["integrity_hold"] = {
            "ativo": bool(motivos),
            "motivo": "; ".join(motivos) or None,
            "efeito": "nenhuma automação clínica neste card enquanto ativo" if motivos else None,
            # A ocorrência fica na história mesmo depois de liberada.
            "historico": [{"tipo": a["tipo"], "nota": a.get("doi") or a.get("pmid"),
                           "liberado_por": (liberacao or {}).get("id"),
                           "liberado_em": (liberacao or {}).get("decidido_em"),
                           "motivo_liberacao": (liberacao or {}).get("motivo")} for a in graves]}
        if reg["integrity_hold"]["ativo"]:
            reg["automation"]["clinical_extraction"].update(
                autorizado=False, motivo="integrity_hold: " + reg["integrity_hold"]["motivo"])
        reg["requires_review"] = bool(reg["revisao"]["agora"])
        reg["analise"].pop("autoriza_automacao", None)


# ── Erratas ─────────────────────────────────────────────────────────────────

R_ADMIN = re.compile(r"author|affiliation|\bname\b|spelling|misspell|typograph|funding|grant|acknowledg|"
                     r"disclosure|conflict of interest|orcid|byline|reference|citation|licen[cs]e|"
                     r"open access|copyright|e-?mail|corresponding|degree", re.I)
R_CLIN = re.compile(r"result|\bdata\b|table|figure|value|hazard|ratio|confidence interval|survival|"
                    r"\bdose|\bmg\b|gbq|percent|%|p value|end ?point|efficacy|toxicit|adverse|"
                    r"number of patients|abstract", re.I)


def nota_de(coleta: dict, uid: str, aviso: dict) -> dict | None:
    """Resultado do db_correcoes para esta nota deste card, se houver."""
    for k, n in (coleta.get("notas") or {}).items():
        if n["uid"] == uid and n["aviso"].get("chave") == aviso.get("chave") and \
                (n["aviso"].get("ref") or "") == (aviso.get("ref") or ""):
            return n
    return None


def classe_correcao(aviso: dict, coleta: dict, uid: str) -> dict:
    """ADMINISTRATIVE / PRESENTATIONAL / CLINICAL_DATA / UNRESOLVED (Fase 1.6).
    Sem texto lido pelos canais aprovados, é UNRESOLVED — nunca benigna."""
    n = nota_de(coleta, uid, aviso)
    if not n:
        return {"classe": "UNRESOLVED", "base": "nota ainda não processada por db_correcoes", "canal": None}
    return {"classe": n["classe"], "base": n["base"], "canal": n.get("canal"),
            "nota_pmid": n.get("nota_pmid"), "nota_doi": n.get("nota_doi")}


def impacto_aviso(aviso: dict, coleta: dict) -> dict:
    """administrativa / potencialmente_clinica / indeterminada. Sem texto da
    nota, é indeterminada — nunca benigna por padrão."""
    if aviso["tipo"] in ("retratacao", "expressao_de_preocupacao"):
        return {"impacto": "integridade", "base": aviso["tipo"]}
    nota = coleta.get("avisos", {}).get(aviso.get("pmid") or "")
    texto = " ".join(x for x in ((nota or {}).get("titulo", ""), (nota or {}).get("resumo", "")) if x)
    genericos = re.fullmatch(r"\s*(correction to .*|department of error\.?|errat(a|um)\.?|"
                             r"correction\.?|.*\.)\s*", texto or "", re.I)
    corpo = (nota or {}).get("resumo", "")
    if not corpo:
        return {"impacto": "indeterminada",
                "base": "nota sem texto no PubMed" if nota else "nota só na Crossref, sem texto"}
    if R_CLIN.search(corpo):
        return {"impacto": "potencialmente_clinica", "base": f"texto da nota: {R_CLIN.search(corpo).group(0)!r}"}
    if R_ADMIN.search(corpo):
        return {"impacto": "administrativa", "base": f"texto da nota: {R_ADMIN.search(corpo).group(0)!r}"}
    del genericos
    return {"impacto": "indeterminada", "base": "texto da nota não permite classificar"}


# ── Prioridade ──────────────────────────────────────────────────────────────

P0, P1, P2, P3, WATCH_PUB = ("P0_INTEGRITY", "P1_CLINICAL_UPDATE", "P2_SECONDARY_OR_WATCH",
                             "P3_BIBLIOGRAPHIC", "WATCH_PUBLICATION_PENDING")
ACAO = {"humana": "exige decisão", "acompanhar": "acompanhado automaticamente",
        "arquivar": "resolvido/arquivado automaticamente"}


def _candidato_forte(p: dict, reg: dict, card: dict, coleta: dict) -> bool:
    """Candidato ligado ao registro por uma família independente, da coorte
    certa, e que concorda com o card (sigla no artigo ou título idêntico)."""
    art = coleta["artigos"].get(p["pmid"]) or {}
    return bool(p.get("ligacao")) and p.get("coorte") is True and bool(
        sigla_em(acronimos(card), f"{art.get('titulo', '')} {art.get('resumo', '')}")
        or titulo_igual(card, art))


def priorizar_sinal(sinal: dict, reg: dict, card: dict, coleta: dict, integridade: dict) -> list[dict]:
    """Um sinal da Fase 1 → um ou mais itens priorizados (correção vira um item
    por nota). Cada item: classe, evidence_confidence, clinical_materiality, acao."""
    base = {"uid": sinal["uid"], "estudo": sinal["estudo"], "categoria": sinal["categoria"],
            "origem_sinal": sinal["classe"], "chave": sinal["chave"]}
    c = sinal["classe"]
    if c in ("apresentado_publicado", "publicado_sem_pmid"):
        cands = [sinal["candidato"]] if sinal.get("candidato") else sinal.get("candidatos", [])
        forte = any(_candidato_forte(p, reg, card, coleta) for p in cands)
        return [dict(base, classe=P1, evidence_confidence="alta" if forte else "média",
                     clinical_materiality="alta", acao="humana",
                     motivo=sinal["motivo"], candidatos=[p["pmid"] for p in cands])]
    if c == "correcao":
        out = []
        for a in sinal["avisos"]:
            cc = classe_correcao(a, coleta, sinal["uid"])
            if a["tipo"] in ("retratacao", "expressao_de_preocupacao"):
                out.append(dict(base, classe=P0, evidence_confidence="alta", clinical_materiality="alta",
                                acao="humana", motivo=f"{a['tipo']} do artigo do card", aviso=a, correcao=cc))
            elif cc["classe"] == "CLINICAL_DATA":
                out.append(dict(base, classe=P1, evidence_confidence="alta", clinical_materiality="alta",
                                acao="humana", motivo="correção de dado clínico (texto da nota lido)",
                                aviso=a, correcao=cc))
            elif cc["classe"] in ("ADMINISTRATIVE", "PRESENTATIONAL"):
                out.append(dict(base, classe=P3, evidence_confidence="alta", clinical_materiality="baixa",
                                acao="arquivar", motivo=f"correção {cc['classe'].lower()} (texto da nota lido)",
                                aviso=a, correcao=cc))
            else:
                out.append(dict(base, classe=P2, evidence_confidence="média",
                                clinical_materiality="indeterminada", acao="acompanhar",
                                motivo="CORRECTION_UNRESOLVED: texto inacessível ou não diz o que mudou; "
                                       "fica no baseline e o texto é procurado de novo nas próximas execuções",
                                aviso=a, correcao=cc))
        return out
    if c == "ctgov":
        if "resultados depositados" in sinal["motivo"] or "hasResults" in sinal["motivo"] or \
                "RESULT" in sinal["motivo"] or "resultsFirstPostDate" in sinal["motivo"]:
            return [dict(base, classe=WATCH_PUB, evidence_confidence="alta", clinical_materiality="média",
                         acao="acompanhar", motivo=sinal["motivo"])]
        return [dict(base, classe=P2, evidence_confidence="alta", clinical_materiality="média",
                     acao="acompanhar", motivo=sinal["motivo"])]
    if c == "inconsistencia_pmid_nct":
        analise = integridade.get(reg["uid"], {})
        cls = analise.get("classificacao")
        # Metadado errado na fonte, ou card que é o dono legítimo: nada a mudar
        # no Database. O resto pede decisão (e é dívida do dia zero).
        acao = "arquivar" if cls in ("SOURCE_METADATA_ERROR", "MACHINE_VERIFIED_CORRECT") else "humana"
        return [dict(base, classe=P0, evidence_confidence="alta" if cls in (
            "MACHINE_VERIFIED_ERROR", "SOURCE_METADATA_ERROR", "MACHINE_VERIFIED_CORRECT") else "baixa",
            clinical_materiality="baixa" if acao == "arquivar" else "alta", acao=acao,
            motivo=sinal["motivo"], integridade=cls)]
    if c == "integridade":
        return [dict(base, classe=P0, evidence_confidence="alta", clinical_materiality="alta",
                     acao="humana", motivo=sinal["motivo"])]
    return [dict(base, classe=P2, evidence_confidence="baixa", clinical_materiality="indeterminada",
                 acao="humana", motivo=sinal["motivo"])]


def priorizar_publicacao(p: dict, reg: dict, card: dict, coleta: dict) -> dict:
    """Artigo novo ligado a um card (item de baseline ou novidade semanal)."""
    rel, orig = p["relacao"], p.get("relacao_origem")
    base = {"uid": reg["uid"], "pmid": p["pmid"], "relacao": rel}
    if p.get("coorte") is False:
        return dict(base, classe=P3, evidence_confidence="alta", clinical_materiality="baixa",
                    acao="arquivar", motivo="artigo de outra coorte do mesmo NCT")
    if rel == "protocol" or p["natureza"] not in ("relato_de_ensaio", "artigo"):
        return dict(base, classe=P3, evidence_confidence="alta" if orig == EXPLICIT else "média",
                    clinical_materiality="baixa", acao="arquivar",
                    motivo=f"{p['natureza']}/{rel}: não atualiza o card")
    if rel in ("secondary_analysis", "subgroup", "qol", "safety"):
        return dict(base, classe=P2, evidence_confidence="alta" if orig == EXPLICIT else "média",
                    clinical_materiality="baixa" if orig == EXPLICIT else "média",
                    acao="acompanhar", motivo=f"{rel} → candidata a secondary-cards")
    art = coleta["artigos"].get(p["pmid"]) or {}
    if R.citado_no_ref(card, art):
        return dict(base, classe=P3, evidence_confidence="média", clinical_materiality="baixa",
                    acao="arquivar", motivo="o ref do card já cita este periódico e ano")
    st = reg["status_categoria"]
    sem_pub = not reg["pmid_atual"] and st in ("apresentado", "em_andamento", "concluido", "encerrado")
    if sem_pub and p.get("coorte") is True and p.get("ligacao"):
        forte = _candidato_forte(p, reg, card, coleta)
        return dict(base, classe=P1, evidence_confidence="alta" if forte else "média",
                    clinical_materiality="alta", acao="humana" if forte else "acompanhar",
                    motivo="card sem artigo; relato ligado ao registro")
    tipo = p.get("tipo_analise")
    if tipo in ("final", "long-term update") and p.get("tipo_origem") == EXPLICIT:
        rep_art = coleta["artigos"].get(reg["pmid_atual"] or "")
        comp = R.comparabilidade(card, rep_art, art, p)
        if comp["comparavel"] is False:
            return dict(base, classe=P2, evidence_confidence="alta", clinical_materiality="média",
                        acao="acompanhar", motivo="follow-up não comparável: " + "; ".join(comp["diferencas"]),
                        comparabilidade=comp)
        ident_ok = reg["automation"]["identity"]["nivel"] in (MV, HUMAN)
        return dict(base, classe=P1, evidence_confidence="alta" if ident_ok and p.get("ligacao") else "média",
                    clinical_materiality="alta", acao="humana",
                    motivo=f"{tipo} explícito no título, sem diferença detectada com a representada",
                    comparabilidade=comp)
    return dict(base, classe=P2, evidence_confidence="baixa", clinical_materiality="indeterminada",
                acao="acompanhar", motivo="artigo ligado sem tipo declarado: acompanhar")


# ── Integridade PMID/NCT ────────────────────────────────────────────────────

def _posse(uid: str, card: dict, reg: dict, art: dict) -> tuple[list[str], list[str]]:
    """Evidência independente do PMID de que o artigo É do estudo do card, e
    evidência contra. O título copiado do artigo (E) não entra: prova só que o
    card foi preenchido a partir dele."""
    texto = f"{art.get('titulo', '')} {art.get('resumo', '')}"
    a_favor, contra = [], []
    comum = set(reg["identidade"]["nct"]) & set(art.get("registros", []))
    if comum:
        a_favor.append(f"NCT do card ({', '.join(sorted(comum))}) declarado no DataBank do artigo")
    s = sigla_em(acronimos(card), texto)
    if s:
        a_favor.append(f"nome do estudo {s!r} no título/abstract")
    g = autor_ano(card, art)
    if g:
        a_favor.append(g)
    if reg["status_categoria"] in ("em_andamento", "concluido") and \
            R.natureza(art) in ("relato_de_ensaio", "artigo"):
        contra.append(f"card {reg['status_card']!r} (sem resultado) citando artigo de resultado")
    pub = {"pubtypes": art.get("pubtypes", [])}
    if not R.fase_compativel(pub, R.fases_do_card(card)):
        contra.append("fase declarada pelo artigo difere da fase do card")
    return a_favor, contra


def _candidatos(uid: str, card: dict, reg: dict, coleta: dict, excluir: set[str]) -> list[dict]:
    """Publicação que poderia ser a correta: título idêntico ao `titulo_full`
    (busca por título) ou relato ligado ao NCT do card com o nome do estudo —
    e, havendo termo de tumor para a categoria, com esse tumor no título."""
    siglas = acronimos(card)
    tumor = R.termo_tumor(card.get("category_id", ""))
    vistos, out = set(excluir), []

    def ok_tumor(a):
        return not tumor or re.search(tumor, a.get("titulo", ""), re.I)

    for p in coleta.get("por_titulo", {}).get(uid, []):
        a = coleta["artigos"].get(p)
        if p not in vistos and a and titulo_igual(card, a) and ok_tumor(a):
            vistos.add(p)
            out.append({"pmid": p, "titulo": a["titulo"], "data": a["data"],
                        "por": "título idêntico ao titulo_full"})
    for n in reg["identidade"]["nct"]:
        for p in coleta["si"].get(n, []):
            a = coleta["artigos"].get(p)
            if p in vistos or not a or R.natureza(a) != "relato_de_ensaio" or not ok_tumor(a):
                continue
            if R.classificar_artigo(a)["relacao"] in ("secondary_analysis", "subgroup", "qol", "safety"):
                continue              # análise derivada não substitui a publicação do card
            if sigla_em(siglas, f"{a.get('titulo', '')} {a.get('resumo', '')}"):
                vistos.add(p)
                out.append({"pmid": p, "titulo": a["titulo"], "data": a["data"],
                            "por": f"relato ligado a {n} com o nome do estudo"})
    return out


def analisar_integridade(registro: dict, dados: dict, coleta: dict) -> dict:
    """Para cada card com databank_divergente ou pmid_compartilhado: identidade
    atual, motivo, fontes que concordam e divergem, candidato e classificação
    MACHINE_VERIFIED_ERROR | SOURCE_METADATA_ERROR | AMBIGUOUS |
    NO_REPLACEMENT_FOUND (erro demonstrado, sem substituto) — e
    MACHINE_VERIFIED_CORRECT para o card que é o dono legítimo de um PMID
    compartilhado."""
    cards = {s["uid"]: s for s in dados["studies"]}
    regs = {r["uid"]: r for r in registro["cards"]}
    out = {}
    for reg in registro["cards"]:
        motivos = [m for m in reg["motivos_revisao"]
                   if m.startswith(("databank_divergente", "pmid_compartilhado"))]
        if not motivos:
            continue
        uid, card, pmid = reg["uid"], cards[reg["uid"]], reg["pmid_atual"]
        art = coleta["artigos"].get(pmid) or {}
        siglas = acronimos(card)
        nct_card = reg["identidade"]["nct"]
        nct_art = [x for x in art.get("registros", []) if x.startswith("NCT")]
        a_favor, contra = _posse(uid, card, reg, art)
        concordam, divergem = list(a_favor), list(contra)
        sig_reg_card = [n for n in nct_card if sigla_no_registro(siglas, coleta["ctgov"].get(n))]
        sig_reg_art = [n for n in nct_art if n not in nct_card
                       and sigla_no_registro(siglas, coleta["ctgov"].get(n))]
        if nct_card:
            (concordam if sig_reg_card else divergem).append(
                f"CT.gov {', '.join(nct_card)}: nome do estudo {'presente' if sig_reg_card else 'ausente'}")
        for n in [x for x in nct_art if x not in nct_card]:
            (concordam if n in sig_reg_art else divergem).append(
                f"CT.gov {n} (declarado pelo artigo): nome do estudo "
                f"{'presente' if n in sig_reg_art else 'ausente'} — {texto_ctgov(coleta['ctgov'].get(n))[:80]!r}")
        if titulo_igual(card, art):
            divergem.append("titulo_full do card é cópia do título deste artigo (não prova o estudo)")
        excluir = {pmid}
        if motivos[0].startswith("databank_divergente"):
            if sig_reg_art and not sig_reg_card:
                cls, erro = "MACHINE_VERIFIED_ERROR", \
                    f"NCT do card errado: o artigo e o registro {', '.join(sig_reg_art)} têm o nome do estudo"
                cand_nct = sig_reg_art
            elif sig_reg_card and not sig_reg_art and a_favor and not contra:
                cls, erro, cand_nct = "SOURCE_METADATA_ERROR", \
                    "DataBank do PubMed aponta NCT de outro estudo; o artigo é do estudo do card", []
            elif sig_reg_card and not sig_reg_art and not a_favor:
                cand_nct = []
                cls, erro = "PMID_ERRADO", "o PMID do card é de outro estudo"
            else:
                cls, erro, cand_nct = "AMBIGUOUS", "as fontes não convergem", []
        else:
            outros = re.findall(r"também é o de ([\w\-, ]+), sem", motivos[0])[0].split(", ")
            grupo = [uid] + outros
            posse = {u: _posse(u, cards[u], regs[u], art) for u in grupo}
            donos = [u for u in grupo if posse[u][0]]
            if len(donos) > 1:
                donos = [u for u in donos if not posse[u][1]]
            cand_nct = []
            if donos == [uid]:
                cls, erro = "MACHINE_VERIFIED_CORRECT", \
                    f"o PMID é deste card; o erro está em {', '.join(outros)}"
            elif len(donos) == 1:
                cls, erro = "PMID_ERRADO", f"o PMID pertence a {donos[0]}"
                excluir |= {pmid}
            else:
                cls, erro = "AMBIGUOUS", "nenhum card do grupo tem evidência exclusiva de posse"
        cands = _candidatos(uid, card, reg, coleta, excluir) if cls == "PMID_ERRADO" else []
        if cls == "PMID_ERRADO":
            cls = "MACHINE_VERIFIED_ERROR" if cands else "NO_REPLACEMENT_FOUND"
        out[uid] = {
            "uid": uid, "estudo": reg["estudo"], "siglas": siglas,
            "identidade_atual": {"nct": nct_card, "pmid": pmid, "titulo_full": card.get("titulo_full", ""),
                                 "registro_ctgov": texto_ctgov(coleta["ctgov"].get(nct_card[0]))[:140]
                                 if nct_card else None,
                                 "artigo": art.get("titulo", ""), "nct_no_artigo": nct_art,
                                 "primeiro_autor": art.get("primeiro_autor", "")},
            "motivo": motivos, "classificacao": cls, "erro": erro,
            "nct_candidato": cand_nct, "candidatos": cands,
            "fontes_concordam": concordam, "fontes_divergem": divergem,
        }
    return out


# ── Inbox semanal ───────────────────────────────────────────────────────────

def _semana(d: str) -> date | None:
    try:
        partes = [int(x) for x in (d or "").split("-")]
        if len(partes) < 2:
            return None
        dia = date(partes[0], partes[1], partes[2] if len(partes) > 2 else 1)
    except ValueError:
        return None
    return dia - timedelta(days=dia.weekday())


def simular_inbox(registro: dict, dados: dict, coleta: dict, hoje: date, semanas: int = 52) -> dict:
    """Como teria sido cada uma das últimas `semanas` semanas depois do
    baseline: artigos ligados publicados na semana (mais novos que a
    publicação do card), notas de errata do artigo do card datadas na semana
    e resultados que apareceram no CT.gov na semana."""
    cards = {s["uid"]: s for s in dados["studies"]}
    inicio = _semana(hoje.isoformat()) - timedelta(weeks=semanas)
    por_semana: dict[date, Counter] = defaultdict(Counter)
    humanos: dict[date, list] = defaultdict(list)
    for reg in registro["cards"]:
        card = cards[reg["uid"]]
        limite = (reg["publicacao_representada"] or {}).get("data") or ""
        for p in reg["publicacoes"]:
            s = _semana(p["data"])
            if not s or s < inicio or p["pmid"] == reg["pmid_atual"] or (limite and p["data"] <= limite):
                continue
            it = priorizar_publicacao(p, reg, card, coleta)
            por_semana[s][it["acao"]] += 1
            if it["acao"] == "humana":
                humanos[s].append(f"{reg['uid']} · PMID {p['pmid']} · {it['classe']} · {it['motivo'][:60]}")
        for a in reg["avisos"]:
            nota = coleta.get("avisos", {}).get(a.get("pmid") or "")
            s = _semana((nota or {}).get("data") or a.get("data") or "")
            if not s or s < inicio:
                continue
            if a["tipo"] in ("retratacao", "expressao_de_preocupacao"):
                cls, acao = a["tipo"], "humana"
            else:
                cls = classe_correcao(a, coleta, reg["uid"])["classe"]
                acao = {"CLINICAL_DATA": "humana", "ADMINISTRATIVE": "arquivar",
                        "PRESENTATIONAL": "arquivar"}.get(cls, "acompanhar")
            por_semana[s][acao] += 1
            if acao == "humana":
                humanos[s].append(f"{reg['uid']} · {a['tipo']} · {cls}")
        for n in reg["identidade"]["nct"]:
            c = coleta["ctgov"].get(n)
            s = _semana((c or {}).get("results_first_post") or "")
            if s and s >= inicio:
                por_semana[s]["acompanhar"] += 1
    semanas_lista = [inicio + timedelta(weeks=i) for i in range(semanas)]
    serie = [{"semana": s.isoformat(), **{k: por_semana[s].get(k, 0) for k in ACAO}} for s in semanas_lista]
    h = sorted(x["humana"] for x in serie)
    return {"inicio": inicio.isoformat(), "semanas": semanas, "serie": serie,
            "totais": {k: sum(x[k] for x in serie) for k in ACAO},
            "humana_por_semana": {"mediana": h[len(h) // 2], "p75": h[int(len(h) * .75)],
                                  "p90": h[int(len(h) * .9)], "max": h[-1],
                                  "semanas_acima_de_5": sum(x > 5 for x in h)},
            "exemplos_humanos": {s.isoformat(): v for s, v in sorted(humanos.items())[-6:]}}
