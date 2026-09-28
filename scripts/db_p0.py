#!/usr/bin/env python3
"""
db_p0.py — propostas de reparo para os P0 de integridade (Fase 1.6). EM CÓPIA.

Não escreve em data.js. Gera scripts/_db_propostas_p0.{json,md}: para cada P0
humano, um relatório e uma proposta campo a campo com
  campo · valor_atual · valor_proposto · fonte · identificador · evidencia ·
  confianca · natureza (bibliográfica/factual × clínica) · acao
Campo clínico nunca é "corrigido" por semelhança de título ou sigla: a
proposta clínica só aponta a divergência e a fonte; quem decide é humano.

Os casos vêm da análise de integridade (db_confianca.analisar_integridade) e
dos avisos graves dos cards — nenhum estudo está codificado aqui:
  NCT errado com candidato       → auditoria do NCT e dos campos que dependem dele;
  PMID errado com candidato      → auditoria do card inteiro contra as publicações;
  PMID indevido em card de desenho → estado coerente sem publicação;
  sem substituto e sem registro  → busca da fonte real; quarentena se não houver;
  expressão de preocupação/retratação → conteúdo da nota, campos afetados, integrity_hold;
  erro de metadado da fonte      → decisão para db_decisoes.json.
"""
from __future__ import annotations

import json
import re
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
import db_confianca as C  # noqa: E402
import db_correcoes as K  # noqa: E402
import db_fontes as F  # noqa: E402
import db_registro as R  # noqa: E402
from br_ctgov import http_json  # noqa: E402

SAIDA_JSON = SCRIPTS / "_db_propostas_p0.json"
SAIDA_MD = SCRIPTS / "_db_propostas_p0.md"
BIB, CLIN = "bibliográfica/factual", "clínica"
CAMPOS_CLINICOS = ("primario", "secundario", "resultado_chave", "takehome", "tox_g3", "tox_interesse",
                   "subgrupo", "basal", "n", "estatistica", "analises", "esquema", "cumul", "impacto_reg",
                   "limit", "indicacao", "incl", "excl", "molecular", "biomarc", "comparador", "linha")


# ── Fontes ──────────────────────────────────────────────────────────────────

def ctgov_completo(nct: str) -> dict:
    p = http_json(f"https://clinicaltrials.gov/api/v2/studies/{nct}")["protocolSection"]
    locs = p.get("contactsLocationsModule", {}).get("locations", [])
    return {
        "nct": nct, "acronimo": p["identificationModule"].get("acronym") or "",
        "titulo": p["identificationModule"].get("briefTitle") or "",
        "titulo_oficial": p["identificationModule"].get("officialTitle") or "",
        "sponsor": p.get("sponsorCollaboratorsModule", {}).get("leadSponsor", {}).get("name"),
        "fase": p.get("designModule", {}).get("phases"),
        "n": (p.get("designModule", {}).get("enrollmentInfo") or {}),
        "inicio": p["statusModule"].get("startDateStruct", {}).get("date"),
        "conclusao_primaria": p["statusModule"].get("primaryCompletionDateStruct", {}).get("date"),
        "status": p["statusModule"].get("overallStatus"),
        "locais": len(locs), "paises": sorted({l.get("country") for l in locs if l.get("country")}),
        "intervencoes": [f"{i.get('name')}: {(i.get('description') or '')[:200]}"
                         for i in p.get("armsInterventionsModule", {}).get("interventions", [])],
        "referencias": [r.get("pmid") for r in p.get("referencesModule", {}).get("references", []) if r.get("pmid")],
    }


def pubmed(pmids: list[str]) -> dict:
    xml = F.http_texto(F._ncbi_url("efetch.fcgi", db="pubmed", retmode="xml", id=",".join(pmids)))
    time.sleep(F.PAUSA_NCBI)
    out = {}
    for a in ET.fromstring(xml).findall("PubmedArticle"):
        mc, art = a.find("MedlineCitation"), a.find("MedlineCitation/Article")
        j = art.find("Journal")
        out[mc.findtext("PMID")] = {
            "pmid": mc.findtext("PMID"), "titulo": "".join(art.find("ArticleTitle").itertext()),
            "revista": j.findtext("ISOAbbreviation"), "ano": j.findtext("JournalIssue/PubDate/Year") or "",
            "volume": j.findtext("JournalIssue/Volume") or "", "paginas": art.findtext("Pagination/MedlinePgn") or "",
            "primeiro_autor": art.findtext("AuthorList/Author/LastName") or "",
            "doi": next((x.text for x in a.findall("PubmedData/ArticleIdList/ArticleId")
                         if x.get("IdType") == "doi"), None),
            "resumo": " ".join("".join(t.itertext()) for t in art.findall("Abstract/AbstractText")),
            "pubtypes": [p.text for p in art.findall("PublicationTypeList/PublicationType")],
            "registros": [n.text for n in mc.findall("Article/DataBankList/DataBank/AccessionNumberList/AccessionNumber")],
        }
    return out


def prop(campo, atual, proposto, fonte, ident, evidencia, confianca, natureza, acao="propor alteração"):
    return {"campo": campo, "valor_atual": atual, "valor_proposto": proposto, "fonte": fonte,
            "identificador": ident, "evidencia": evidencia, "confianca": confianca, "natureza": natureza,
            "acao": acao}


def faixas_unidade(t: str) -> set[str]:
    """"25-50 Gy", "15 mCi/kg", "200 mg" — números com unidade de dose."""
    return {re.sub(r"\s+", "", m.group(0)).lower() for m in
            re.finditer(r"\d+(?:[.,]\d+)?(?:\s*[-–]\s*\d+(?:[.,]\d+)?)?\s*(?:Gy|mg|GBq|MBq|mCi)", t or "")}


def numeros(t: str) -> set[str]:
    return R.numeros_card(t) | {R._num(x) for x in re.findall(r"(?<![\d.,])\d+[.,]\d+", t or "")}


def citacoes_no_ref(ref: str) -> list[dict]:
    """"… Int J Mol Sci 2020;21(4):1273" → ECitMatch. Revista = trecho logo antes
    de "ano;volume:página"; autor = "Sobrenome XX et al." mais próximo antes."""
    out = []
    for m in re.finditer(r"((?:19|20)\d\d)\s*;\s*(\d+)(?:\([^)]*\))?\s*:\s*(\d+)", ref or ""):
        antes = ref[max(0, m.start() - 220):m.start()]
        revista = re.split(r"\.\s+|;\s*|:\s+", antes.strip().rstrip("."))[-1].strip()
        autores = re.findall(r"([A-Z][\w'\-]+) [A-Z]{1,3}\b(?:,| et al)", antes)
        cit = f"{revista}. {m.group(1)};{m.group(2)}:{m.group(3)}"
        pmid, via = K.ecitmatch(cit), "ECitMatch"
        if not pmid and autores:          # fallback estruturado: 1º autor + volume + página + ano
            d = F._ncbi_json("esearch.fcgi", db="pubmed", retmax="3",
                             term=f"{autores[-1]}[1au] AND {m.group(2)}[vi] AND {m.group(3)}[pg] AND {m.group(1)}[dp]")
            ids = d.get("esearchresult", {}).get("idlist", [])
            pmid, via = (ids[0], "autor+volume+página+ano") if len(ids) == 1 else (None, "não resolvida")
        out.append({"citacao": f"{revista} {m.group(0)}", "autor_citado": autores[-1] if autores else None,
                    "pmid": pmid, "via": via})
    return out


# ── Casos ───────────────────────────────────────────────────────────────────

def caso_nct_errado(card, reg, integ, coleta):
    errado, certo = reg["identidade"]["nct"][0], integ["nct_candidato"][0]
    ce, cc = ctgov_completo(errado), ctgov_completo(certo)
    art = pubmed([reg["pmid_atual"]])[reg["pmid_atual"]]
    si_certo = F.pmids_ligados(certo)
    confirma = []
    if certo in art["registros"]:
        confirma.append(f"PubMed DataBank do PMID {reg['pmid_atual']} declara {certo}")
    if re.search(certo, art["resumo"]):
        confirma.append(f"o abstract diz: registrado como {certo}")
    if reg["pmid_atual"] in si_certo:
        confirma.append(f"PubMed {certo}[si] devolve o PMID do card")
    if C.sigla_no_registro(C.acronimos(card), {"acronimo": cc["acronimo"], "titulo_breve": cc["titulo"],
                                               "titulo_oficial": cc["titulo_oficial"]}):
        confirma.append(f"CT.gov {certo}: nome do estudo no registro ({cc['acronimo'] or cc['titulo'][:60]})")
    if reg["pmid_atual"] in cc["referencias"]:
        confirma.append(f"CT.gov {certo} cita o PMID do card")
    propostas = [
        prop("nct", card["nct"], certo, "PubMed + CT.gov", certo, "; ".join(confirma), "alta", BIB),
        prop("nct_url", card["nct_url"], f"https://clinicaltrials.gov/study/{certo}", "CT.gov", certo,
             "segue o NCT", "alta", BIB),
    ]
    # Campos que podem ter vindo do registro errado.
    ano = lambda d: (d or "")[:4]  # noqa: E731
    if ano(ce["inicio"]) and ano(ce["inicio"]) in card.get("periodo", "") and ano(cc["inicio"]) not in card.get("periodo", ""):
        propostas.append(prop("periodo", card["periodo"],
                              f"início {cc['inicio']} (registro {certo}); {card['periodo'].split(';', 1)[-1].strip()}",
                              "CT.gov", certo, f"o ano de início no card ({ano(ce['inicio'])}) é o do registro "
                              f"errado {errado}; o registro certo começa em {cc['inicio']}", "alta", BIB))
    else:
        propostas.append(prop("periodo", card["periodo"], card["periodo"], "publicação / CT.gov", certo,
                              f"não depende do registro errado (início certo {cc['inicio']}, errado {ce['inicio']})",
                              "média", BIB, "manter"))
    locais = re.findall(r"(\d+)\s*(?:centros|locais|sites)", card.get("centros", ""))
    paises_card = re.findall(r"(\d+)\s*pa[ií]ses", card.get("centros", ""))
    if locais or paises_card:
        diverge = (paises_card and int(paises_card[0]) != len(cc["paises"]))
        propostas.append(prop(
            "centros", card["centros"],
            f"{', '.join(cc['paises'])} (registro {certo}: {cc['locais']} locais)" if diverge else card["centros"],
            "CT.gov", certo, f"registro certo: {cc['locais']} locais em {len(cc['paises'])} países "
            f"({', '.join(cc['paises'])}); registro errado: {ce['locais']} locais em {len(ce['paises'])} países",
            "média" if diverge else "alta", BIB, "decisão humana" if diverge else "manter"))
    n_card = re.findall(r"\d+", card.get("n", ""))
    propostas.append(prop("n", card["n"], card["n"], "publicação", reg["pmid_atual"],
                          f"N do card vem da publicação (randomizados), não do registro "
                          f"(certo: {cc['n'].get('count')} {cc['n'].get('type')}; errado: {ce['n'].get('count')})"
                          + ("" if n_card and n_card[0] in art["resumo"] else " — N não encontrado no abstract"),
                          "alta" if n_card and n_card[0] in art["resumo"] else "média", CLIN, "manter"))
    menciona = [k for k, v in card.items() if isinstance(v, str) and errado in v and k not in ("nct", "nct_url")]
    return {"tipo": "NCT errado", "registro_errado": ce, "registro_certo": cc,
            "confirmacoes_independentes": confirma, "outros_campos_com_o_nct_errado": menciona,
            "propostas": propostas}


def caso_pmid_errado(card, reg, integ, coleta):
    errado = reg["pmid_atual"]
    cand = [x["pmid"] for x in integ["candidatos"]]
    citados = [x["pmid"] for x in citacoes_no_ref(card.get("ref", "")) if x["pmid"]]
    citados += re.findall(r"PMID\s*(\d{6,9})", card.get("ref", ""))
    todos = list(dict.fromkeys([errado] + cand + citados))
    pubs = pubmed(todos)
    e = pubs[errado]
    termos_errados = {w.lower() for w in re.findall(r"[A-Za-z][A-Za-z0-9\-]{3,}", e["titulo"])} - \
        {w.lower() for p in cand + citados if p in pubs for w in re.findall(r"[A-Za-z][A-Za-z0-9\-]{3,}", pubs[p]["titulo"])} - \
        {"with", "after", "prior", "therapies", "patients", "cancer", "advanced", "trial", "study", "results", "from"}
    auditoria, propostas = [], []
    for campo, valor in card.items():
        if not isinstance(valor, str) or not valor.strip() or campo in ("uid", "category_id", "category_name",
                                                                          "category_short", "category_color"):
            continue
        ns = numeros(valor)
        onde = {p: sorted(ns & numeros(pubs[p]["resumo"])) for p in todos if p in pubs}
        marcas = sorted(t for t in termos_errados if re.search(rf"\b{re.escape(t)}\b", valor, re.I))
        contaminado = bool(marcas) or (onde.get(errado) and not any(onde.get(p) for p in todos if p != errado))
        auditoria.append({"campo": campo, "valor": valor[:220], "numeros": sorted(ns),
                          "numeros_por_fonte": {p: v for p, v in onde.items() if v},
                          "termos_do_artigo_errado": marcas, "contaminado": bool(contaminado)})
    principal = cand[0] if cand else None
    for p in citados:
        if p != principal and p in pubs:
            atualizacao = p
            break
    else:
        atualizacao = None
    # Qual publicação sustenta os números do primario?
    ns_prim = numeros(card.get("primario", "")) | numeros(card.get("resultado_chave", ""))
    cobertura = {p: sorted(ns_prim & numeros(pubs[p]["resumo"])) for p in [principal, atualizacao] if p}
    c = pubs[principal]
    propostas.append(prop("pubmed_url", card["pubmed_url"], f"https://pubmed.ncbi.nlm.nih.gov/{principal}/",
                          "PubMed", principal,
                          f"o artigo atual ({errado}) é '{e['titulo'][:70]}…' e declara {e['registros']}; o candidato "
                          f"declara {c['registros']} e é a citação do ref ({c['revista']} {c['ano']};{c['volume']}:"
                          f"{c['paginas']})", "alta", BIB, "decisão humana (ver representação abaixo)"))
    propostas.append(prop("titulo_full", card["titulo_full"], c["titulo"], "PubMed", principal,
                          "o titulo_full atual é o título do artigo errado (cópia)", "alta", BIB))
    propostas.append(prop("ano_pub", card["ano_pub"], int(c["ano"]) if c["ano"] else card["ano_pub"], "PubMed",
                          principal, "ano da publicação escolhida", "alta", BIB,
                          "manter" if str(card["ano_pub"]) == c["ano"] else "propor alteração"))
    representacao = {
        "pergunta": "qual publicação o card representa?",
        "opcoes": [{"pmid": p, "titulo": pubs[p]["titulo"], "revista": f"{pubs[p]['revista']} {pubs[p]['ano']}",
                    "numeros_do_primario_no_abstract": cobertura.get(p, [])} for p in cobertura],
        "observacao": "números de análises diferentes no mesmo campo exigem atribuição explícita",
    }
    for campo in ("primario", "resultado_chave"):
        a = next(x for x in auditoria if x["campo"] == campo)
        fontes = [p for p, v in a["numeros_por_fonte"].items() if v and p != errado]
        if len(fontes) > 1:
            propostas.append(prop(campo, card[campo], "atribuir cada número à sua publicação ou alinhar a uma só",
                                  "PubMed", ", ".join(fontes),
                                  "; ".join(f"{p}: {a['numeros_por_fonte'][p]}" for p in fontes),
                                  "alta", CLIN, "decisão humana"))
    if atualizacao and pubs[atualizacao]["ano"] and pubs[atualizacao]["ano"] not in card.get("ref", ""):
        propostas.append(prop("ref", card["ref"], f"ano da atualização {pubs[atualizacao]['ano']} "
                              f"({pubs[atualizacao]['revista']} {pubs[atualizacao]['ano']};{pubs[atualizacao]['volume']}:"
                              f"{pubs[atualizacao]['paginas']})", "PubMed", atualizacao,
                              "o ref cita a atualização com outro ano", "alta", BIB))
    return {"tipo": "PMID de outro estudo", "artigo_errado": {k: e[k] for k in ("pmid", "titulo", "revista", "ano", "registros")},
            "publicacoes": {p: {k: pubs[p][k] for k in ("titulo", "revista", "ano", "volume", "paginas",
                                                          "primeiro_autor", "registros")} for p in todos if p in pubs},
            "representacao": representacao,
            "campos_contaminados": [a["campo"] for a in auditoria if a["contaminado"]],
            "auditoria": auditoria, "propostas": propostas}


def caso_desenho(card, reg, integ, coleta):
    nct = reg["identidade"]["nct"][0]
    cc = ctgov_completo(nct)
    outro = pubmed([reg["pmid_atual"]])[reg["pmid_atual"]]
    propostas = [
        prop("pubmed_url", card["pubmed_url"], "", "convenção do banco para ensaio sem publicação de resultado",
             reg["pmid_atual"], f"o PMID é de '{outro['titulo'][:80]}…' ({outro['revista']} {outro['ano']}), "
             f"relato de outro estudo; {nct} está {cc['status']} sem resultados", "alta", BIB),
        prop("titulo_full", card["titulo_full"], cc["titulo_oficial"] or cc["titulo"], "CT.gov", nct,
             "card de desenho usa o título oficial do registro; o atual é o título do outro artigo", "alta", BIB),
    ]
    if cc["inicio"] and cc["inicio"][:4] not in card.get("periodo", ""):
        propostas.append(prop("periodo", card["periodo"], f"{cc['inicio'][:4]} - em recrutamento ({cc['status']})",
                              "CT.gov", nct, f"início no registro: {cc['inicio']}", "alta", BIB))
    m = re.search(r"(20\d\d)(?:\s*-\s*(20\d\d))?", card.get("impacto_reg", ""))
    if m and cc["conclusao_primaria"] and m.group(1) < cc["conclusao_primaria"][:4]:
        propostas.append(prop("impacto_reg", card["impacto_reg"],
                              f"retirar a data esperada de resultado ou alinhar ao registro "
                              f"(conclusão primária estimada {cc['conclusao_primaria']})", "CT.gov", nct,
                              f"o card espera resultado em {m.group(0)}; o registro estima {cc['conclusao_primaria']}",
                              "alta", CLIN, "decisão humana"))
    n_card = re.findall(r"\d+", card.get("n", ""))
    propostas.append(prop("n", card["n"], card["n"], "CT.gov", nct,
                          f"registro: {cc['n'].get('count')} ({cc['n'].get('type')})", "alta", BIB, "manter"))
    sigla_outro = C.acronimos({"estudo": next((c["estudo"] for c in coleta.get("_cards", [])
                                                if c.get("pubmed_url", "").rstrip("/").endswith(reg["pmid_atual"])
                                                and c["uid"] != reg["uid"]), "")})
    padroes = [re.escape(outro["titulo"][:30])] + [re.escape(x) for x in sigla_outro]
    menciona = {k: v[:200] for k, v in card.items() if isinstance(v, str) and k not in ("titulo_full",)
                and re.search("|".join(padroes), v)}
    doses_card = {k: sorted(faixas_unidade(v)) for k, v in menciona.items() if faixas_unidade(v)}
    doses_outro = sorted(faixas_unidade(outro["resumo"]))
    del n_card
    return {"tipo": "PMID de outro estudo em card de desenho", "registro": cc,
            "artigo_indevido": {k: outro[k] for k in ("pmid", "titulo", "revista", "ano", "registros")},
            "campos_com_mencao_ao_outro_estudo": menciona,
            "doses_atribuidas_ao_outro_estudo": {"no_card": doses_card, "no_abstract_do_outro": doses_outro,
                                                 "observacao": "o abstract lista os níveis testados; que um deles "
                                                 "tenha sido 'definido' não é verificável só pelo abstract"},
            "nota": "menções em prosa ao estudo anterior como BASE DO DESENHO (dose, intervalo) são legítimas "
                    "pela convenção do banco; não são resultado deste estudo",
            "propostas": propostas}


def caso_fonte(card, reg, integ, coleta):
    cits = citacoes_no_ref(card.get("ref", ""))
    pubs = pubmed([c["pmid"] for c in cits if c["pmid"]] + [reg["pmid_atual"]])
    for c in cits:
        a = pubs.get(c["pmid"] or "")
        c["resolve_para"] = f"{a['primeiro_autor']} · {a['titulo'][:90]} · {'/'.join(a['pubtypes'][:2])}" if a else None
        c["autor_confere"] = bool(a and c["autor_citado"] and C.compacto(c["autor_citado"]) == C.compacto(a["primeiro_autor"]))
    # Busca montada só do card: primeiro termo do nome do estudo, as duas palavras
    # mais longas do título, e o intervalo de anos declarado no `periodo`.
    palavras = sorted(set(re.findall(r"[A-Za-z]{8,}", card.get("titulo_full", ""))), key=len, reverse=True)[:2]
    anos = re.findall(r"((?:19|20)\d\d)\s*[-–]\s*((?:19|20)\d\d)", card.get("periodo", ""))
    busca_termo = f'{card.get("estudo", "").split()[0]}[tiab]'
    if palavras:
        busca_termo += " AND (" + " OR ".join(f"{w}[tiab]" for w in palavras) + ")"
    if anos:
        busca_termo += f' AND ("{anos[-1][0]}"[dp] : "{anos[-1][1]}"[dp])'
    d = F._ncbi_json("esearch.fcgi", db="pubmed", term=busca_termo, retmax="50")
    achados = d["esearchresult"]["idlist"]
    arts = pubmed(achados) if achados else {}
    candidatos = [{"pmid": p, "titulo": a["titulo"][:110], "tipos": a["pubtypes"][:3], "ano": a["ano"],
                   "primeiro_autor": a["primeiro_autor"]} for p, a in arts.items()]
    inequivocos = [c for c in candidatos if not {"Case Reports", "Review"} & set(c["tipos"])]
    propostas = [prop("status (interno)", card["status"], "quarentena_editorial", "—", reg["pmid_atual"],
                      "sem fonte primária inequívoca para o conteúdo além do Hadoux 2014 (que é o card vizinho)",
                      "alta", CLIN, "decisão humana")]
    for campo in ("primario", "secundario", "subgrupo", "molecular", "n", "periodo", "sponsor", "impacto_reg"):
        propostas.append(prop(campo, card.get(campo, ""), "retirar do banco publicado até haver fonte, ou reduzir ao "
                              "que o Hadoux 2014 sustenta", "—", reg["pmid_atual"],
                              "afirmação sem fonte verificável nas referências citadas", "média", CLIN, "decisão humana"))
    return {"tipo": "fonte não verificável", "referencias_citadas": cits, "busca_estruturada": busca_termo,
            "candidatos": candidatos, "candidatos_primarios": inequivocos,
            "recomendacao": "QUARENTENA EDITORIAL" if not inequivocos else "avaliar candidatos",
            "propostas": propostas}


def caso_integridade_editorial(card, reg, coleta):
    notas = [n for n in (coleta.get("notas") or {}).values()
             if n["uid"] == reg["uid"] and n["tipo"] in ("expressao_de_preocupacao", "retratacao")]
    outras = [n for n in (coleta.get("notas") or {}).values()
              if n["uid"] == reg["uid"] and n["tipo"] not in ("expressao_de_preocupacao", "retratacao")]
    art = pubmed([reg["pmid_atual"]])[reg["pmid_atual"]]
    divergencias = []
    for campo in ("primario", "esquema", "tox_g3", "tox_interesse"):
        ns = numeros(card.get(campo, ""))
        faltam = sorted(n for n in ns - numeros(art["resumo"]) if n not in ("95",))
        doses = sorted(faixas_unidade(card.get(campo, "")) - faixas_unidade(art["resumo"]))
        if faltam or doses:
            divergencias.append({"campo": campo, "valor": card[campo][:200], "numeros_fora_do_abstract": faltam,
                                 "doses_fora_do_abstract": doses,
                                 "doses_no_abstract": sorted(faixas_unidade(art["resumo"]))})
    ci = re.search(r"IC 95% (\d+[.,]\d+)\s*[-–]\s*(\d+[.,]\d+);\s*p\s*<\s*0[.,]001", card.get("primario", ""))
    propostas = [prop("integrity_hold (interno)", "—", "ativo", "nota do periódico",
                      ", ".join(n["nota_doi"] or n["nota_pmid"] or "?" for n in notas),
                      " / ".join(n["texto"][:300] for n in notas), "alta", CLIN,
                      "aplicado no registro (nenhuma automação clínica)")]
    if ci and float(ci.group(2).replace(",", ".")) > 0.9:
        propostas.append(prop("primario", card["primario"], "conferir HR/IC/p no texto completo", "publicação",
                              reg["pmid_atual"], f"IC95% com limite superior {ci.group(2)} é incompatível com p<0,001; "
                              "o abstract não traz HR nem IC", "alta", CLIN, "decisão humana"))
    return {"tipo": "expressão de preocupação/retratação", "notas": [
                {"tipo": n["tipo"], "doi": n["nota_doi"], "pmid": n["nota_pmid"], "canal": n["canal"],
                 "texto": n["texto"][:1200], "classe_do_texto": n["classe"]} for n in notas],
            "outras_notas": [{"tipo": n["tipo"], "classe": n["classe"], "texto": n["texto"][:500]} for n in outras],
            "afeta_dados": "o texto trata de autoria, contribuições e declarações; não questiona dados nem resultados",
            "campos_potencialmente_afetados": {"sponsor": card.get("sponsor", ""), "ref": card.get("ref", "")},
            "auditoria_independente_contra_o_abstract": divergencias, "propostas": propostas}


def decisao_metadado(card, reg, integ, coleta):
    art = coleta["artigos"][reg["pmid_atual"]]
    errado = integ["identidade_atual"]["nct_no_artigo"][0]
    reg_errado = coleta["ctgov"].get(errado) or {}
    return {
        "id": f"inconsistencia_pmid_nct:{reg['uid']}:databank_divergente",
        "tipo": "classificacao", "uid": reg["uid"], "pmid": reg["pmid_atual"], "campo": "integridade",
        "valor": "SOURCE_METADATA_ERROR",
        "evidencia": {
            "nct_declarado_pelo_artigo": errado,
            "registro_declarado": f"{errado}: {reg_errado.get('titulo_breve', '')!r} (sem relação com o estudo)",
            "nct_do_card": reg["identidade"]["nct"],
            "concordam": integ["fontes_concordam"],
            "artigo": art.get("titulo", ""),
        },
        "decidido_em": time.strftime("%Y-%m-%d"),
        "motivo": "O DataBank do PubMed atribui ao artigo um NCT de outro estudo; o nome do estudo está no "
                  "registro do card e no artigo. O card está correto; o erro é do metadado do PubMed.",
        "decidido_por": "usuário (aprovação explícita da Fase 1.6, 2026-09-28)",
    }


# ── Execução ────────────────────────────────────────────────────────────────

def main() -> int:
    dados = R.carregar_dados()
    coleta = json.loads(R.SAIDA["coleta"].read_text(encoding="utf-8"))
    reg = R.construir(dados, coleta)
    cards = {s["uid"]: s for s in dados["studies"]}
    regs = {r["uid"]: r for r in reg["cards"]}
    coleta["_cards"] = dados["studies"]
    integ = C.analisar_integridade(reg, dados, coleta)
    casos, decisoes = {}, []
    for uid, a in integ.items():
        card, r = cards[uid], regs[uid]
        if a["classificacao"] == "MACHINE_VERIFIED_ERROR" and a["nct_candidato"]:
            casos[uid] = caso_nct_errado(card, r, a, coleta)
        elif a["classificacao"] == "MACHINE_VERIFIED_ERROR" and a["candidatos"]:
            casos[uid] = caso_pmid_errado(card, r, a, coleta)
        elif a["classificacao"] == "NO_REPLACEMENT_FOUND" and r["status_categoria"] in ("em_andamento", "concluido"):
            casos[uid] = caso_desenho(card, r, a, coleta)
        elif a["classificacao"] == "NO_REPLACEMENT_FOUND":
            casos[uid] = caso_fonte(card, r, a, coleta)
        elif a["classificacao"] == "SOURCE_METADATA_ERROR":
            decisoes.append(decisao_metadado(card, r, a, coleta))
    for r in reg["cards"]:
        if any(x["tipo"] in ("expressao_de_preocupacao", "retratacao") for x in r["avisos"]):
            casos[r["uid"]] = caso_integridade_editorial(cards[r["uid"]], r, coleta)
    for uid, c in casos.items():
        c.update(uid=uid, estudo=cards[uid]["estudo"])
    R.gravar(SAIDA_JSON, json.dumps({"casos": casos, "decisoes_propostas": decisoes}, ensure_ascii=False, indent=1))
    R.gravar(SAIDA_MD, md(casos, decisoes))
    print(json.dumps({u: {"tipo": c["tipo"], "propostas": len(c["propostas"])} for u, c in casos.items()},
                     ensure_ascii=False, indent=1))
    return 0


def md(casos: dict, decisoes: list) -> str:
    L = ["# Propostas de reparo — P0 de integridade (em cópia; nada aplicado ao data.js)", ""]
    for uid, c in casos.items():
        L += [f"## `{uid}` — {c['estudo']} · {c['tipo']}", ""]
        for k in ("confirmacoes_independentes", "campos_contaminados", "outros_campos_com_o_nct_errado",
                  "recomendacao", "afeta_dados", "nota"):
            if c.get(k):
                L.append(f"- **{k}**: {c[k]}")
        if c.get("representacao"):
            L.append(f"- **representação**: {c['representacao']['pergunta']}")
            for o in c["representacao"]["opcoes"]:
                L.append(f"  - PMID {o['pmid']} ({o['revista']}): números do primario no abstract = "
                         f"{o['numeros_do_primario_no_abstract']}")
        for n in c.get("notas", []):
            L.append(f"- **nota {n['tipo']}** ({n['doi']}, via {n['canal']}): {n['texto'][:400]}")
        for n in c.get("referencias_citadas", []):
            L.append(f"- referência `{n['citacao'][:70]}` → PMID {n['pmid']} · {n['resolve_para']} · "
                     f"autor confere: {n['autor_confere']}")
        if "candidatos" in c and c["tipo"] == "fonte não verificável":
            L.append(f"- busca estruturada: `{c['busca_estruturada']}` → "
                     + ("; ".join(f"{x['pmid']} {x['tipos']} {x['titulo'][:60]}" for x in c["candidatos"]) or "nada"))
        for d in c.get("auditoria_independente_contra_o_abstract", []):
            L.append(f"- auditoria: `{d['campo']}` — números fora do abstract: {d['numeros_fora_do_abstract']}"
                     + (f"; doses fora do abstract: {d['doses_fora_do_abstract']} (abstract: {d['doses_no_abstract']})"
                        if d.get("doses_fora_do_abstract") else ""))
        for n in c.get("outras_notas", []):
            L.append(f"- outra nota ({n['tipo']}, classificada {n['classe']}): {n['texto'][:300]}")
        if c.get("doses_atribuidas_ao_outro_estudo"):
            d = c["doses_atribuidas_ao_outro_estudo"]
            L.append(f"- doses citadas como do estudo anterior: {d['no_card']}; no abstract dele: "
                     f"{d['no_abstract_do_outro']} — {d['observacao']}")
        if c.get("campos_com_mencao_ao_outro_estudo"):
            L.append(f"- campos que mencionam o estudo anterior: {sorted(c['campos_com_mencao_ao_outro_estudo'])}")
        for a in c.get("auditoria", []):
            if a["numeros_por_fonte"] and a["campo"] not in ("titulo_full", "pubmed_url", "nct_url", "ref"):
                L.append(f"- proveniência `{a['campo']}`: " + "; ".join(
                    f"PMID {p}: {v}" for p, v in a["numeros_por_fonte"].items()))
        L += ["", "| campo | valor atual | proposto | fonte · id | evidência | confiança | natureza | ação |",
              "|---|---|---|---|---|---|---|---|"]
        for p in c["propostas"]:
            cel = lambda x: str(x).replace("|", "/").replace("\n", " ")[:160]  # noqa: E731
            L.append(f"| {p['campo']} | {cel(p['valor_atual'])} | {cel(p['valor_proposto'])} | {p['fonte']} · "
                     f"{p['identificador']} | {cel(p['evidencia'])} | {p['confianca']} | {p['natureza']} | {p['acao']} |")
        L.append("")
    if decisoes:
        L += ["## Decisões propostas para db_decisoes.json", ""]
        L += [f"```json\n{json.dumps(d, ensure_ascii=False, indent=1)}\n```" for d in decisoes]
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    sys.exit(main())
