#!/usr/bin/env python3
"""
db_correcoes.py — texto e classificação das notas de correção (Fase 1.6).

A FONTE é sempre a própria nota publicada pelo periódico (Correction, Erratum,
Department of Error, Expression of Concern). PMC e Europe PMC são só CANAIS de
recuperação desse texto, e só valem quando o identificador do documento
devolvido é o da nota — PMID ou DOI idênticos. Nada de busca web genérica.

Ordem dos canais:
  1. PubMed → PMCID (registro da nota ou ID Converter) → PMC full text XML
     (E-utilities efetch db=pmc). O XML precisa trazer o PMID ou o DOI da nota.
  2. Europe PMC REST: registro da nota por EXT_ID (PMID) ou DOI; texto pelo
     resumo do registro ou pelo fullTextXML do PMCID, com os mesmos
     identificadores conferidos.
  3. Crossref/Crossmark: só identidade e relação (`update-to` aponta o artigo
     corrigido). Não fornece texto.
  4. Sem texto → UNRESOLVED.
Nota citada só pela referência ("J Clin Oncol. 2013;31(24):3049") é
identificada antes pelo ECitMatch do PubMed (citação estruturada → PMID).

CLASSES:
  ADMINISTRATIVE — autor, afiliação, funding, agradecimentos, referência,
                   declaração de conflito: arquivável;
  PRESENTATIONAL — legenda, rótulo, formatação, grafia, ou figura/tabela com
                   declaração explícita de que os dados não mudaram: arquivável;
  CLINICAL_DATA  — N, denominadores, HR, IC95%, p, medianas, endpoint,
                   eficácia, segurança, resultados ou conclusão: escala;
  UNRESOLVED     — sem texto, ou texto que não diz o que mudou. Fica no
                   baseline; não entra no inbox só por existir.
Nunca se conclui ADMINISTRATIVE ou PRESENTATIONAL sem ler o texto: a
classificação roda sobre o corpo da nota, depois de retirada a citação do
artigo corrigido (que traz "survival", "randomised" etc. no próprio título).
"""
from __future__ import annotations

import json
import re
import sys
import time
import urllib.error
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
import db_fontes as F  # noqa: E402
from br_ctgov import RespostaParcial, http_json  # noqa: E402

EPMC = "https://www.ebi.ac.uk/europepmc/webservices/rest"
ADMINISTRATIVE, PRESENTATIONAL, CLINICAL, UNRESOLVED = (
    "ADMINISTRATIVE", "PRESENTATIONAL", "CLINICAL_DATA", "UNRESOLVED")

R_CLINICO = re.compile(
    r"hazard ratio|\bHR\b|odds ratio|confidence interval|\b9[05]% ?CI\b|\bCI\b|p ?[=<>≤] ?0?[.·]\d|"
    r"\bp value|\bmedian\b|survival|response rate|objective response|progression|end ?point|efficacy|"
    r"safety|adverse event|toxicit|grade [1-5]|\bn ?= ?\d|number of (patients|participants|events)|"
    r"denominator|\d+(\.\d+)? ?%|results? (section|were|was|should)|conclusion|\bdose\b|dosage|"
    r"\bmg\b|\bGBq\b|\bevents?\b|incidence|deaths?|randomi[sz]ed (patients|participants)", re.I)
R_ADMIN = re.compile(
    r"\bauthor|affiliation|funding|funder|grant|acknowledg|disclosure|conflict(s)? of interest|"
    r"competing interest|orcid|byline|reference|investigator(s)? list|collaborator|contributor|"
    r"e-?mail|corresponding|academic degree|trial registration number|data sharing|open access|"
    r"licen[cs]e|copyright|\bname\b|misspell|spelled|spelt|middle initial", re.I)
R_APRESENTACAO = re.compile(r"legend|caption|label|formatting|format\b|typographical|typo|layout|"
                            r"heading|abbreviation|font|colou?r|alignment|axis title|spelling", re.I)
R_SEM_MUDANCA = re.compile(r"(do(es)?|did) not (affect|change|alter)|no (effect|impact|change)s? on|"
                           r"(results|data|conclusions?) (are|were|remain) (unchanged|unaffected|correct)|"
                           r"not affect(ed)? the (results|data|conclusions)", re.I)
R_FIG_TAB = re.compile(r"\bfig(ure)?s?\b|\btables?\b|appendix|supplementary", re.I)


# ── Texto ────────────────────────────────────────────────────────────────────

def _texto_xml(no) -> str:
    return re.sub(r"\s+", " ", "".join(no.itertext())).strip() if no is not None else ""


def pmc_texto(pmcid: str, pmid: str | None, doi: str | None) -> dict | None:
    """Canal 1. Só aceita o XML se ele trouxer o PMID ou o DOI da nota."""
    F.CHAMADAS["pmc"] += 1
    xml = F.http_texto(F._ncbi_url("efetch.fcgi", db="pmc", retmode="xml",
                                   id=pmcid.replace("PMC", "")))
    time.sleep(F.PAUSA_NCBI)
    raiz = ET.fromstring(xml)
    art = raiz.find(".//article")
    if art is None:
        return None
    ids = {e.get("pub-id-type"): (e.text or "").strip().lower() for e in art.iter("article-id")}
    if not ((pmid and ids.get("pmid") == pmid) or (doi and ids.get("doi") == doi.lower())):
        return {"rejeitado": f"PMC {pmcid}: identificadores {ids} não são os da nota"}
    corpo = " ".join(_texto_xml(n) for n in art.findall(".//abstract") + art.findall(".//body"))
    return {"canal": "PMC full text XML", "identificador": pmcid, "texto": corpo} if corpo else None


def epmc_registro(pmid: str | None, doi: str | None) -> dict | None:
    q = f"EXT_ID:{pmid} AND SRC:MED" if pmid else f'DOI:"{doi}"'
    F.CHAMADAS["europepmc"] += 1
    d = http_json(f"{EPMC}/search?{urllib.parse.urlencode({'query': q, 'format': 'json', 'resultType': 'core'})}")
    time.sleep(0.2)
    res = (d.get("resultList") or {}).get("result") or []
    for r in res:                     # identidade inequívoca: PMID ou DOI idênticos
        if (pmid and r.get("pmid") == pmid) or (doi and (r.get("doi") or "").lower() == doi.lower()):
            return r
    return None


def epmc_texto(reg: dict) -> dict | None:
    """Canal 2. Resumo do registro, ou fullTextXML do PMCID (só acesso aberto)."""
    if reg.get("abstractText"):
        return {"canal": "Europe PMC (registro da nota)", "identificador": reg.get("pmid") or reg.get("doi"),
                "texto": re.sub(r"<[^>]+>", " ", reg["abstractText"])}
    if reg.get("pmcid") and reg.get("inEPMC") == "Y":
        F.CHAMADAS["europepmc"] += 1
        try:
            xml = F.http_texto(f"{EPMC}/{reg['pmcid']}/fullTextXML")
        except urllib.error.HTTPError:
            return None
        finally:
            time.sleep(0.2)
        try:
            raiz = ET.fromstring(xml)
        except ET.ParseError:
            return None
        corpo = " ".join(_texto_xml(n) for n in raiz.findall(".//abstract") + raiz.findall(".//body"))
        if corpo:
            return {"canal": "Europe PMC full text XML", "identificador": reg["pmcid"], "texto": corpo}
    return None


def ecitmatch(ref: str) -> str | None:
    """"J Clin Oncol. 2013 Aug 20;31(24):3049" → PMID pela citação estruturada."""
    m = re.match(r"\s*(.+?)\.\s+((?:19|20)\d\d)[^;]*;\s*(\d+)(?:\([^)]*\))?:\s*([A-Za-z]?\d+)", ref or "")
    if not m:
        return None
    campos = "|".join([m.group(1), m.group(2), m.group(3), m.group(4), "", "k", ""])
    F.CHAMADAS["pubmed"] += 1
    txt = F.http_texto(F._ncbi_url("ecitmatch.cgi", db="pubmed", retmode="xml", bdata=campos))
    time.sleep(F.PAUSA_NCBI)
    ult = txt.strip().split("|")[-1].strip()
    return ult if ult.isdigit() else None


def crossref_relacao(doi: str) -> dict | None:
    """Canal 3: só identidade e relação (`update-to`)."""
    F.CHAMADAS["crossref"] += 1
    try:
        d = http_json(f"{F.CROSSREF}{urllib.parse.quote(doi, safe='/()')}")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise
    finally:
        time.sleep(F.PAUSA_CROSSREF)
    m = d.get("message") or {}
    return {"doi": m.get("DOI"), "tipo": m.get("type"), "titulo": (m.get("title") or [""])[0],
            "update_to": [{"tipo": u.get("type"), "doi": (u.get("DOI") or "").lower()}
                          for u in m.get("update-to", []) or []]}


# ── Classificação ───────────────────────────────────────────────────────────

def corpo_da_correcao(texto: str, titulo_original: str) -> str:
    """Tira do texto a citação do artigo corrigido (título, "Lancet 2024; 404:
    1227–39"), que não é conteúdo da correção."""
    t = texto or ""
    if titulo_original:
        t = re.sub(re.escape(titulo_original.rstrip(".")), " ", t, flags=re.I)
    t = re.sub(r"[A-Z][\w'\-]+ [A-Z]{1,3}(, [A-Z][\w'\-]+ [A-Z]{1,3})*,? et al\.?", " ", t)
    t = re.sub(r"\b[A-Z][\w .]+ (19|20)\d\d; ?\d+(\(\d+\))?: ?[\d–\-]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


R_DADO_FIG = re.compile(r"(fig(ure)?s?|tables?|appendix|supplement\w*)\b.*\b(rows? (have|has) been added|"
                        r"values?|numbers?|data|percentages?|results?|incorrect(ly)? (reported|stated))|"
                        r"\b(rows? (have|has) been added|values? (in|for) (the )?(fig|table))", re.I)
R_NEUTRA = re.compile(r"^(this is a )?correction to\b|^expression of concern to\b|"
                      r"journal (continues|is continuing) to investigate|^\W*(\w+\W*){1,3}$|has (now )?been (corrected|updated|amended) in the "
                      r"(html|pdf|online)|all changes appear|have been updated in the online|"
                      r"published online|the error has been corrected|^\W*$|^\[?this corrects", re.I)
R_TITULO = re.compile(r"\btitle (read|was|should read)|\bthe title\b", re.I)
R_APRESENTACAO_FRASE = re.compile(r"legend|caption|\blabel|formatting|typographical|typo\b|layout|"
                                  r"(row|column)? ?heading|abbreviation|font|alignment|spelling|"
                                  r"terminology|should read", re.I)


def frases(corpo: str) -> list[str]:
    """Divide em frases sem cortar em iniciais de nome ("Theodore W. Laetsch")."""
    protegido = re.sub(r"\b([A-Z])\.(?=\s)", r"\1§", corpo)
    partes = re.split(r"(?<=[.;])\s+(?=[A-Z“\"(\[])", protegido)
    return [f.replace("§", ".").strip() for f in partes if f.strip()]


def classificar(texto: str | None, titulo_original: str = "") -> dict:
    """Frase a frase. Qualquer frase clínica ou de dado em figura/tabela ⇒
    CLINICAL_DATA. Senão, se houver frase administrativa/de apresentação e
    todas as outras forem neutras ⇒ ADMINISTRATIVE ou PRESENTATIONAL. Texto
    que não diz o que mudou ⇒ UNRESOLVED. Nunca sem ler."""
    if not texto:
        return {"classe": UNRESOLVED, "base": "texto da nota inacessível pelos canais aprovados"}
    corpo = corpo_da_correcao(texto, titulo_original)
    tipos, trechos = [], []
    for f in frases(corpo):
        if R_CLINICO.search(f) or R_DADO_FIG.search(f):
            tipos.append("clinica")
            trechos.append(f[:160])
        elif R_ADMIN.search(f) or R_TITULO.search(f):
            tipos.append("admin")
        elif R_APRESENTACAO_FRASE.search(f) or (R_FIG_TAB.search(f) and R_SEM_MUDANCA.search(f)):
            tipos.append("apresentacao")
        elif R_NEUTRA.search(f):
            tipos.append("neutra")
        else:
            tipos.append("indeterminada")
            trechos.append(f[:160])
    if "clinica" in tipos:
        return {"classe": CLINICAL, "base": "frase com dado clínico ou mudança de dado em figura/tabela",
                "trechos": [t for t, k in zip(trechos, [x for x in tipos if x in ("clinica", "indeterminada")])
                            if k == "clinica"], "corpo": corpo[:800]}
    if "indeterminada" in tipos or not ({"admin", "apresentacao"} & set(tipos)):
        return {"classe": UNRESOLVED, "base": "texto lido, mas não diz o que foi alterado",
                "trechos": trechos, "corpo": corpo[:800]}
    classe = PRESENTATIONAL if "apresentacao" in tipos else ADMINISTRATIVE
    return {"classe": classe, "base": f"todas as frases são {'/'.join(sorted(set(tipos) - {'neutra'}))} "
            "ou neutras", "corpo": corpo[:800]}


# ── Execução sobre o registro ───────────────────────────────────────────────

def resolver(registro: dict, coleta: dict) -> dict:
    """{chave_da_nota: {...}} para cada aviso dos cards. Rede só aqui."""
    out = {}
    for card in registro["cards"]:
        art = coleta["artigos"].get(card["pmid_atual"] or "") or {}
        for a in card["avisos"]:
            chave = f"{card['uid']}|{a['chave']}|{a.get('ref', '')[:40]}"
            nota_pmid = a.get("pmid")
            origem_id = "PubMed CommentsCorrections" if nota_pmid else None
            if not nota_pmid and not a.get("doi") and a.get("ref"):
                nota_pmid = ecitmatch(a["ref"])
                origem_id = "ECitMatch da citação" if nota_pmid else None
            nota = (coleta.get("avisos") or {}).get(nota_pmid or "") or {}
            doi = (a.get("doi") or nota.get("doi") or "").lower() or None
            pmcid = nota.get("pmcid") or None
            tentativas, texto = [], None
            if nota_pmid and not pmcid:
                conv = F.converter_ids([nota_pmid]).get(nota_pmid, {})
                pmcid = conv.get("pmcid") or None
            if pmcid:
                r = pmc_texto(pmcid, nota_pmid, doi)
                tentativas.append({"canal": "PMC", "pmcid": pmcid,
                                   "resultado": "texto" if r and r.get("texto") else (r or {}).get("rejeitado", "sem texto")})
                texto = r if r and r.get("texto") else None
            if not texto and (nota_pmid or doi):
                reg = epmc_registro(nota_pmid, doi)
                if reg:
                    r = epmc_texto(reg)
                    tentativas.append({"canal": "Europe PMC", "id": reg.get("pmcid") or reg.get("pmid"),
                                       "resultado": "texto" if r else "sem texto (fora do acesso aberto)"})
                    texto = r
                else:
                    tentativas.append({"canal": "Europe PMC", "resultado": "registro não encontrado"})
            relacao = crossref_relacao(doi) if doi else None
            corrige = [u["doi"] for u in (relacao or {}).get("update_to", [])]
            cls = classificar((texto or {}).get("texto"), art.get("titulo", ""))
            if a["tipo"] in ("retratacao", "expressao_de_preocupacao"):
                cls = dict(cls, classe_integridade=a["tipo"])
            out[chave] = {
                "uid": card["uid"], "aviso": a, "tipo": a["tipo"], "nota_pmid": nota_pmid,
                "nota_doi": doi, "identificada_por": origem_id, "pmcid": pmcid,
                "artigo_do_card": {"pmid": card["pmid_atual"], "doi": card["doi"]},
                "crossref": relacao,
                "relacao_confirmada": bool(card["doi"] and card["doi"].lower() in corrige),
                "tentativas": tentativas,
                "texto": (texto or {}).get("texto", "")[:4000], "canal": (texto or {}).get("canal"),
                **cls,
            }
            print(f"[notas] {card['uid']} {a['tipo']} → {cls['classe']} ({(texto or {}).get('canal') or '—'})",
                  file=sys.stderr)
    return out


# ── Rechecagem das UNRESOLVED (cadência menor que a do freshness) ───────────

INTERVALO_RECHECAGEM_DIAS = 30


def precisa_rechecar(estado_correcoes: dict | None, hoje: str,
                     intervalo: int = INTERVALO_RECHECAGEM_DIAS) -> bool:
    """Mensal por padrão. Sem rechecagem anterior registrada, rechecar."""
    from datetime import date
    ultima = (estado_correcoes or {}).get("ultima_rechecagem")
    if not ultima:
        return True
    return (date.fromisoformat(hoje) - date.fromisoformat(ultima)).days >= intervalo


def transicoes(anteriores: dict[str, str], atuais: dict[str, str]) -> dict:
    """Compara a classe de cada nota entre duas rechecagens.
      UNRESOLVED → CLINICAL_DATA            ⇒ volta ao inbox (única porta);
      UNRESOLVED → ADMINISTRATIVE/PRESENTATIONAL ⇒ arquivada;
      UNRESOLVED → UNRESOLVED               ⇒ segue estacionada, sem alerta;
    Nota nova (sem classe anterior) não é transição: o fluxo normal a trata."""
    out = {"para_inbox": [], "arquivadas": [], "seguem_unresolved": []}
    for chave, antes in anteriores.items():
        if antes != UNRESOLVED or chave not in atuais:
            continue
        depois = atuais[chave]
        if depois == CLINICAL:
            out["para_inbox"].append(chave)
        elif depois in (ADMINISTRATIVE, PRESENTATIONAL):
            out["arquivadas"].append(chave)
        else:
            out["seguem_unresolved"].append(chave)
    return out


def estado_novo(estado_correcoes: dict | None, notas: dict, hoje: str) -> dict:
    """Só é gravado depois de uma rechecagem COMPLETA (resposta parcial aborta antes)."""
    return {"intervalo_dias": (estado_correcoes or {}).get("intervalo_dias", INTERVALO_RECHECAGEM_DIAS),
            "ultima_rechecagem": hoje,
            "classes": {k: n["classe"] for k, n in notas.items()}}


def reclassificar(coleta: dict) -> None:
    """Reaplica o classificador ao texto já recuperado (sem rede)."""
    for n in (coleta.get("notas") or {}).values():
        titulo = (coleta["artigos"].get(n["artigo_do_card"]["pmid"] or "") or {}).get("titulo", "")
        for k in ("classe", "base", "trechos", "corpo"):
            n.pop(k, None)
        n.update(classificar(n.get("texto") or None, titulo))


def main() -> int:
    import db_registro as R
    dados = R.carregar_dados()
    coleta = json.loads(R.SAIDA["coleta"].read_text(encoding="utf-8"))
    reg = R.construir(dados, coleta)
    F.CHAMADAS.clear()
    t0 = time.time()
    try:
        notas = resolver(reg, coleta)
    except (RespostaParcial, urllib.error.URLError, TimeoutError, OSError) as e:
        print(f"FALHA TÉCNICA: {e}\nNada foi gravado.", file=sys.stderr)
        return R.FALHA_TECNICA
    coleta["notas"] = notas
    coleta["notas_meta"] = {"em": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                            "chamadas": dict(F.CHAMADAS), "duracao_s": round(time.time() - t0, 1)}
    R.gravar(R.SAIDA["coleta"], json.dumps(coleta, ensure_ascii=False))
    from collections import Counter
    print(json.dumps({"notas": len(notas), "classes": dict(Counter(n["classe"] for n in notas.values())),
                      "com_texto": sum(bool(n["texto"]) for n in notas.values()),
                      **coleta["notas_meta"]}, ensure_ascii=False, indent=1))
    return 0


def rechecar_unresolved(forcar: bool = False) -> int:
    """Rechecagem mensal: só as notas UNRESOLVED voltam aos canais. Estado em
    scripts/_db_estado.json → "correcoes"; avança só se tudo correu bem."""
    import db_registro as R
    from datetime import date
    hoje = date.today().isoformat()
    estado_path = SCRIPTS / "_db_estado.json"
    estado = json.loads(estado_path.read_text(encoding="utf-8")) if estado_path.exists() else {}
    ec = estado.get("correcoes")
    if not forcar and not precisa_rechecar(ec, hoje):
        print(f"rechecagem não devida (última {ec['ultima_rechecagem']}, intervalo {ec['intervalo_dias']} dias)")
        return 0
    coleta = json.loads(R.SAIDA["coleta"].read_text(encoding="utf-8"))
    anteriores = (ec or {}).get("classes") or {k: n["classe"] for k, n in coleta.get("notas", {}).items()}
    dados = R.carregar_dados()
    reg = R.construir(dados, coleta)
    so_unresolved = {"cards": [dict(c, avisos=[a for a in c["avisos"]
                                               if anteriores.get(f"{c['uid']}|{a['chave']}|{a.get('ref', '')[:40]}")
                                               == UNRESOLVED]) for c in reg["cards"]]}
    try:
        novas = resolver(so_unresolved, coleta)
    except (RespostaParcial, urllib.error.URLError, TimeoutError, OSError) as e:
        print(f"FALHA TÉCNICA: {e}\nEstado não avançou.", file=sys.stderr)
        return R.FALHA_TECNICA
    notas = dict(coleta.get("notas", {}))
    notas.update(novas)
    t = transicoes(anteriores, {k: n["classe"] for k, n in notas.items()})
    coleta["notas"] = notas
    R.gravar(R.SAIDA["coleta"], json.dumps(coleta, ensure_ascii=False))
    estado["correcoes"] = estado_novo(ec, notas, hoje)
    R.gravar(estado_path, json.dumps(estado, ensure_ascii=False))
    print(json.dumps({k: len(v) for k, v in t.items()} | {"para_inbox_ids": t["para_inbox"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    if "--rechecar-unresolved" in sys.argv:
        sys.exit(rechecar_unresolved(forcar="--forcar" in sys.argv))
    if "--reclassificar" in sys.argv:
        import db_registro as R
        col = json.loads(R.SAIDA["coleta"].read_text(encoding="utf-8"))
        reclassificar(col)
        R.gravar(R.SAIDA["coleta"], json.dumps(col, ensure_ascii=False))
        from collections import Counter
        print(dict(Counter(n["classe"] for n in col["notas"].values())))
        sys.exit(0)
    sys.exit(main())
