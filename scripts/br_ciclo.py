#!/usr/bin/env python3
"""
br_ciclo.py — um ciclo completo de manutenção do Trial Matcher, só em modo relatório.

    auditoria  →  descoberta  →  banco proposto  →  QA  →  relatório de diferenças

  1. trial-status-auditor (br_auditar.py): os NCTs publicados ainda recrutam
     no Brasil?
  2. trial-discovery (br_discover.py + priorização daqui): o que há de novo
     no CT.gov, e o que merece curadoria.
  3. banco proposto: cópia do trials_br.js com as correções FACTUAIS de status
     (e, se pedido, de centros e os rascunhos já curados). O original não é
     tocado.
  4. trial-qa (br_qa.py): compara atual × proposto e roda os validadores na
     cópia.
  5. relatório: scripts/_br_relatorio.md (+ .json).

A curadoria (trial-curator) é a única etapa com IA e NÃO roda aqui: ela
consome a lista de recomendados que este ciclo grava em _br_discovery.json.
Ver scripts/br_PIPELINE.md.

Nada aqui faz commit, push, nem remove estudo. Aplicar o proposto é decisão
humana: `cp scripts/_br_proposto/trials_br.js assets/js/trials_br.js`, revisar
o diff e seguir o fluxo normal (sync_counts, export_app_data, validadores).

Uso:
    python3 scripts/br_ciclo.py                    # ciclo completo
    python3 scripts/br_ciclo.py --sem-descoberta   # só auditoria + QA
    python3 scripts/br_ciclo.py --centros          # propõe também os centros
    python3 scripts/br_ciclo.py --com-curadoria    # inclui _br_curated.json
    python3 scripts/br_ciclo.py --gravar-estado    # atualiza br_estado.json

Saída: 0 = QA OK · 3 = QA bloqueou (relatório gerado, motivo na seção 7) ·
qualquer outro código = falha técnica (API, rede, resposta parcial): não há
relatório confiável e o estado anterior não é tocado. O workflow distingue os
dois casos por este código.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import br_auditar  # noqa: E402
import br_ctgov as ct  # noqa: E402

SCRIPTS = Path(__file__).resolve().parent
# Código de saída de QA bloqueado. Diferente de 1, que é o de exceção não
# tratada do Python — assim o workflow separa QA de falha técnica.
QA_BLOQUEADO = 3

PROPOSTO = SCRIPTS / "_br_proposto" / "trials_br.js"
RELATORIO_MD = SCRIPTS / "_br_relatorio.md"
RELATORIO_JSON = SCRIPTS / "_br_relatorio.json"
DISCOVERY = SCRIPTS / "_br_discovery.json"
# Decisões humanas que contrariam o registro. Só 'primary_purpose', só o NCT
# listado e só enquanto o registro trouxer o valor anotado. Ver ler_aprovados().
APROVADOS = SCRIPTS / "br_aprovados.json"
TIPOS_OVERRIDE = {"primary_purpose"}
CAMPOS_OVERRIDE = ("nct", "tipo", "valor_registro", "decisao", "motivo", "aprovado_em")
CURATED = SCRIPTS / "_br_curated.json"

# Intervenções de tratamento sistêmico — a prioridade do Trial Matcher.
# RADIATION/PROCEDURE continuam candidatos, mas numa faixa abaixo.
SISTEMICO = {"DRUG", "BIOLOGICAL", "GENETIC", "COMBINATION_PRODUCT"}

# Extensão/roll-over só recebe quem já estava num estudo-mãe: não serve para o
# médico que procura estudo para um paciente novo. Pelo título, porque o
# registro não tem campo estruturado para isso — por isso vai para "revisar",
# não para descarte.
# Escopo editorial (2026-09-27): o Trial Matcher principal é para estudos cujo
# objetivo primário é tratar o tumor ou modificar diretamente a doença. Suporte,
# sintoma, caquexia, prevenção, rastreamento, reabilitação e toxicidade não
# entram automaticamente. Termos no título ou nas condições mandam o estudo para
# "revisar" — nunca para descarte: o termo pode aparecer num estudo antitumoral,
# e quem decide é uma pessoa (ou o curador, com `escopo: limitrofe`).
ESCOPO_NAO_ANTITUMORAL = re.compile(
    r"cachexi|caquexi|carcinoid syndrome|s[ií]ndrome carcinoide|anorexia|weight loss"
    r"|mucositis|nausea|vomiting|neuropath|cardiotoxic|cardioprotect|hot flash"
    r"|fatigue|\bpain\b|xerostomia|dermatitis|alopecia|hand-foot|lymphedema"
    r"|\banemia\b|anaemia|transfusion|neutropeni|thrombocytopeni|febrile"
    r"|infection|prophyla|prevent|screening|early detection|rehabilitat|exercise"
    r"|quality of life|supportive|symptom|palliative care|toxicit|-induced|complication",
    re.I)

EXTENSAO = re.compile(r"\bextension\b|roll-?over|continued access|continuation study", re.I)


# ── 2. descoberta ─────────────────────────────────────────────────────────────

def ler_aprovados(caminho: Path | None = None) -> tuple[dict[str, dict], list[str]]:
    """Overrides humanos válidos, por NCT, e avisos sobre as entradas recusadas.

    Entrada inválida não quebra o ciclo nem vale: é ignorada e aparece no
    relatório. Válida = todos os CAMPOS_OVERRIDE preenchidos, `tipo` em
    TIPOS_OVERRIDE, `decisao` TREATMENT, NCT no formato, data AAAA-MM-DD e um
    único override por NCT.
    """
    caminho = caminho or APROVADOS
    if not caminho.exists():
        return {}, []
    try:
        d = json.loads(caminho.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return {}, [f"{caminho.name} ilegível ({e}) — nenhum override aplicado"]
    validos, avisos = {}, []
    for i, a in enumerate(d.get("aprovados", [])):
        rot = f"{caminho.name}[{i}] {a.get('nct', '?')}"
        falta = [c for c in CAMPOS_OVERRIDE if not str(a.get(c, "")).strip()]
        if falta:
            avisos.append(f"{rot}: ignorado — faltam {', '.join(falta)}")
        elif a["tipo"] not in TIPOS_OVERRIDE:
            avisos.append(f"{rot}: ignorado — tipo {a['tipo']!r} não é aceito "
                          f"(só {', '.join(sorted(TIPOS_OVERRIDE))})")
        elif a["decisao"] != "TREATMENT":
            avisos.append(f"{rot}: ignorado — decisao {a['decisao']!r} (só TREATMENT)")
        elif not re.fullmatch(r"NCT\d{8}", a["nct"]):
            avisos.append(f"{rot}: ignorado — NCT malformado")
        elif not re.fullmatch(r"\d{4}-\d{2}-\d{2}", a["aprovado_em"]):
            avisos.append(f"{rot}: ignorado — aprovado_em fora de AAAA-MM-DD")
        elif a["nct"] in validos:
            avisos.append(f"{rot}: ignorado — segundo override para o mesmo NCT")
        else:
            validos[a["nct"]] = a
    return validos, avisos


def descobrir(publicados: set[str]) -> dict:
    """Busca no CT.gov e classifica em faixas. Determinístico, sem IA."""
    import br_curate
    import br_discover as bd

    brutos = bd.buscar()
    recusados = br_curate.ja_descartados()
    aprovados, avisos_aprovados = ler_aprovados()
    overrides, vistos = [], {}
    faixas: dict[str, list] = {
        "recomendado": [], "rt_cirurgia": [], "aguardando_brasil": [],
        "revisar": [],
    }
    # Teranósticos seguem a triagem normal desde 2026-09; esta lista só os
    # registra, com a faixa em que caíram, para auditoria no relatório.
    teranosticos = []
    descartes = Counter()
    achatados_recomendados = []

    for s in brutos:
        p = s.get("protocolSection", {})
        e = bd.achatar(s)
        if not e["nct"] or e["nct"] in publicados:
            continue
        if not bd.eh_oncologico(e):
            descartes["condição não oncológica"] += 1
            continue
        if not bd.eh_tratamento(e):
            descartes["suporte/reabilitação (tipo de intervenção)"] += 1
            continue
        if e["nct"] in recusados:
            descartes["já recusado antes (br_descartados.json)"] += 1
            continue

        rb = ct.recrutamento_brasil(p)
        tipos = {i.get("tipo") for i in e["intervencoes"]}
        proposito = p.get("designModule", {}).get("designInfo", {}).get("primaryPurpose", "")
        item = {
            "nct": e["nct"], "acronimo": e["acronimo"], "titulo": e["titulo_breve"],
            "fases": e["fases"], "overall_status": rb["overall_status"],
            "brazil_status": rb["brazil_status"],
            "centros_br_recrutando": rb["centros_br_recrutando"],
            "patrocinador": e["patrocinador"], "condicoes": e["condicoes"][:3],
            "tipos_intervencao": sorted(t for t in tipos if t), "proposito": proposito,
            "teranostico": bd.eh_teranostico(e),
        }
        e["teranostico"] = item["teranostico"]   # vai ao curador via _br_discovery.json
        if item["teranostico"]:
            teranosticos.append(item)

        # Override humano: só troca o propósito declarado, e só se o registro
        # ainda disser exatamente o que a pessoa conferiu. As checagens de
        # status no Brasil e extensão vêm ANTES e não são contornadas; escopo e
        # tipo de intervenção vêm DEPOIS e continuam valendo.
        ov = aprovados.get(e["nct"])
        proposito_aprovado = bool(ov and proposito and proposito != "TREATMENT"
                                  and ov["valor_registro"] == proposito)
        if ov:
            vistos[e["nct"]] = item

        if (rb["brazil_status"] == ct.BR_NOT_YET_RECRUITING
              or rb["overall_status"] == "NOT_YET_RECRUITING"):
            item["motivo"] = "ainda não abriu no Brasil — volta sozinho quando abrir"
            faixas["aguardando_brasil"].append(item)
        elif rb["brazil_status"] in (ct.CLOSED_IN_BRAZIL, ct.STUDY_CLOSED):
            descartes[f"sem recrutamento no Brasil ({rb['brazil_status']})"] += 1
            item["motivo"] = f"fora: sem recrutamento no Brasil ({rb['brazil_status']})"
            continue
        elif rb["brazil_status"] != ct.BR_RECRUITING:
            item["motivo"] = f"{rb['brazil_status']}: {rb['motivo']}"
            faixas["revisar"].append(item)
        elif EXTENSAO.search(e["titulo_breve"] + " " + e["titulo_oficial"]):
            item["motivo"] = "extensão/roll-over — só para quem já está em estudo-mãe"
            faixas["revisar"].append(item)
        elif proposito and proposito != "TREATMENT" and not proposito_aprovado:
            item["motivo"] = f"propósito declarado: {proposito}"
            if ov:
                item["motivo"] += (f" (override em {APROVADOS.name} não vale: anotado "
                                   f"{ov['valor_registro']!r}, registro diz {proposito!r})")
            faixas["revisar"].append(item)
        else:
            if proposito_aprovado:
                item["override"] = {k: ov[k] for k in CAMPOS_OVERRIDE}
                e["override_proposito"] = item["override"]   # o curador vê a decisão
                overrides.append(item)
            if (termo := ESCOPO_NAO_ANTITUMORAL.search(
                    " ".join([e["titulo_breve"], e["titulo_oficial"], *e["condicoes"]]))):
                item["motivo"] = (f"escopo: possível suporte/sintomático ('{termo.group(0)}') "
                                  "— objetivo antitumoral a confirmar")
                faixas["revisar"].append(item)
            elif not tipos & SISTEMICO:
                item["motivo"] = "só radioterapia/procedimento"
                faixas["rt_cirurgia"].append(item)
            else:
                item["motivo"] = "tratamento sistêmico, recrutando no Brasil"
                faixas["recomendado"].append(item)
                e["brazil_status"] = rb["brazil_status"]   # vai para o card via _factual
                achatados_recomendados.append(e)
            if proposito_aprovado:
                item["motivo"] += (f" · override humano: propósito {proposito} → TREATMENT "
                                   f"({APROVADOS.name}, {ov['aprovado_em']})")

    # Fase III primeiro, depois mais centros brasileiros: é a ordem em que a
    # curadoria rende mais para quem procura estudo para o paciente.
    peso = lambda x: (-("PHASE3" in x["fases"]), -x["centros_br_recrutando"])  # noqa: E731
    for v in faixas.values():
        v.sort(key=peso)
    # Override registrado que não teve efeito nesta rodada — auditável também.
    aplicados = {x["nct"] for x in overrides}
    nao_aplicados = []
    for nct, ov in aprovados.items():
        if nct in aplicados:
            continue
        if nct in publicados:
            por_que = "já publicado no Trial Matcher — override sem efeito"
        elif nct in vistos:
            por_que = vistos[nct].get("motivo", "não passou da triagem")
        else:
            por_que = "não veio na busca desta rodada"
        nao_aplicados.append({"nct": nct, "tipo": ov["tipo"], "motivo": por_que})
    return {"total_ctgov": len(brutos), "faixas": faixas, "descartes": dict(descartes),
            "teranosticos": teranosticos,
            "overrides": {"aplicados": overrides, "nao_aplicados": nao_aplicados,
                          "avisos": avisos_aprovados},
            "_achatados": achatados_recomendados}


def gravar_discovery(desc: dict, publicados: set[str]) -> None:
    """_br_discovery.json no formato que o br_curate.py lê, só com os recomendados.

    Assim a curadoria (local ou Batch) trabalha exatamente sobre a lista que o
    relatório recomendou, e não sobre tudo o que a busca trouxe.
    """
    DISCOVERY.write_text(json.dumps({
        "gerado_em": datetime.now(timezone.utc).isoformat(),
        "origem": "br_ciclo.py (só recomendados)",
        "total_ctgov": desc["total_ctgov"],
        "ja_publicados": len(publicados),
        "novos": desc["_achatados"],
        "mudou_status": [], "inalterados": [], "teranosticos": [], "sumiram": [],
        "nao_oncologicos": [], "suporte": [],
    }, ensure_ascii=False, indent=1), encoding="utf-8")


# ── 3. banco proposto ─────────────────────────────────────────────────────────

def blocos_por_nct(texto: str) -> dict[str, tuple[int, int]]:
    """Posição de cada card no texto, do `nct:` até o `nct:` seguinte.

    Mesma delimitação do br_centros.py: janela fixa ou vazava para o vizinho ou
    não alcançava o campo em card longo.
    """
    marcas = [(m.start(), re.search(r"NCT\d{8}", m.group(1)))
              for m in re.finditer(r"""\bnct\s*:\s*'([^']*)'""", texto)]
    marcas = [(pos, m.group(0)) for pos, m in marcas if m]
    out = {}
    for i, (pos, nct) in enumerate(marcas):
        fim = marcas[i + 1][0] if i + 1 < len(marcas) else len(texto)
        out[nct] = (pos, fim)
    return out


def propor(auditoria: dict, com_centros: bool, com_curadoria: bool,
           publicados: set[str], base: Path = ct.TRIALS_JS) -> dict:
    """Escreve _br_proposto/trials_br.js. Só troca valores; não remove card.

    `base` é o arquivo sobre o qual as correções entram — o banco publicado,
    ou uma cópia já migrada (ver br_migracao_2026_09.py).
    """
    from br_centros import js_arr

    texto = base.read_text(encoding="utf-8")
    blocos = blocos_por_nct(texto)
    edicoes = []  # (pos, fim, novo_bloco)
    aplicadas = {"status": [], "centros": [], "curadoria": []}

    for x in auditoria["estudos"]:
        if x["nct"] not in blocos:
            continue
        ini, fim = blocos[x["nct"]]
        bloco = texto[ini:fim]
        novo = bloco
        # brazil_status vai para TODO card auditado, inclusive os em revisão:
        # é ele que tira do "Recrutando" padrão quem não tem centro brasileiro
        # confirmado, sem reescrever o `status` (rótulo) do card.
        bs = x.get("brazil_status") or ct.REVIEW_REQUIRED
        if re.search(r"\bbrazil_status\s*:", novo):
            novo = re.sub(r"(\bbrazil_status\s*:\s*)'[^']*'", lambda m: m.group(1) + f"'{bs}'", novo, count=1)
        else:
            novo = re.sub(r"^(\s*)(status\s*:\s*'[^']*',\n)", lambda m: m.group(1) + m.group(2) + m.group(1) + f"brazil_status: '{bs}',\n",
                          novo, count=1, flags=re.M)
        if novo != bloco:
            aplicadas.setdefault("brazil_status", []).append(x["nct"])
        if x.get("revisao"):
            if novo != bloco:
                edicoes.append((ini, fim, novo))
            continue
        if x.get("status_proposto"):
            novo, n = re.subn(r"(\bstatus\s*:\s*)'[^']*'",
                              lambda m: m.group(1) + "'" + x["status_proposto"] + "'",
                              novo, count=1)
            if n:
                aplicadas["status"].append(x["nct"])
        # Centros só de estudo que recruta no Brasil: de estudo encerrado a
        # lista fica como registro histórico até alguém decidir o destino do card.
        if (com_centros and x.get("brazil_status") == ct.BR_RECRUITING
                and (x.get("centros_a_incluir") or x.get("centros_a_retirar"))):
            locais = x["locais_recrutando"]
            valores = {
                "centros": x["centros_recrutando"],
                "cidades": sorted({l["cidade"] for l in locais}),
                "estados": sorted({l["uf"] for l in locais} - {""}),
            }
            for chave, v in valores.items():
                novo = re.sub(rf"(\b{chave}\s*:\s*)\[.*?\]",
                              lambda m, v=v: m.group(1) + js_arr(v), novo,
                              count=1, flags=re.S)
            aplicadas["centros"].append(x["nct"])
        if novo != bloco:
            edicoes.append((ini, fim, novo))

    for ini, fim, novo in sorted(edicoes, reverse=True):
        texto = texto[:ini] + novo + texto[fim:]

    if com_curadoria and CURATED.exists():
        import br_merge
        cards = [c for c in json.loads(CURATED.read_text(encoding="utf-8")).get("cards", [])
                 if c.get("_factual", {}).get("nct") not in publicados]
        if cards:
            bloco = (f"\n  // ============== NOVOS ESTUDOS ({datetime.now():%Y-%m-%d}) "
                     f"— RASCUNHO, revisar antes de publicar ==============\n\n")
            bloco += "\n".join(br_merge.card_js(c) for c in cards)
            fecho = re.search(r"\n\];\s*\n", texto)
            if fecho:
                texto = texto[:fecho.start()] + "\n" + bloco + texto[fecho.start():]
                aplicadas["curadoria"] = [c["_factual"]["nct"] for c in cards]

    PROPOSTO.parent.mkdir(exist_ok=True)
    PROPOSTO.write_text(texto, encoding="utf-8")
    return aplicadas


# ── 5. relatório ──────────────────────────────────────────────────────────────

def secao_overrides(desc: dict) -> list[str]:
    """Seção do relatório com toda exceção humana: aplicada, sem efeito ou recusada."""
    ov = desc.get("overrides") or {}
    ap, nao, av = ov.get("aplicados", []), ov.get("nao_aplicados", []), ov.get("avisos", [])
    link = lambda n: f"[{n}](https://clinicaltrials.gov/study/{n})"  # noqa: E731
    md = [f"### Overrides humanos aplicados ({len(ap)}) — `{APROVADOS.name}`", "",
          "Exceção registrada por uma pessoa contra um campo do registro. Só troca o "
          "propósito declarado; status no Brasil, escopo, curadoria e QA continuam valendo.", ""]
    md += _tab([[link(x["nct"]), x["acronimo"] or "—", x["override"]["tipo"],
                 f"{x['override']['valor_registro']} → {x['override']['decisao']}",
                 x["override"]["aprovado_em"], x["override"]["motivo"][:140]] for x in ap],
               ["NCT", "acrônimo", "tipo", "registro → decisão", "aprovado em", "motivo"])
    if nao:
        md += ["Registrados, sem efeito nesta rodada:", ""]
        md += [f"- {link(x['nct'])} ({x['tipo']}): {x['motivo']}" for x in nao] + [""]
    if av:
        md += ["Entradas recusadas no arquivo:", ""] + [f"- {a}" for a in av] + [""]
    return md


def _tab(linhas: list[list[str]], cab: list[str]) -> list[str]:
    if not linhas:
        return ["_nenhum_", ""]
    esc = lambda s: str(s).replace("|", "\\|").replace("\n", " ")  # noqa: E731
    out = ["| " + " | ".join(cab) + " |", "|" + "---|" * len(cab)]
    out += ["| " + " | ".join(esc(c) for c in l) + " |" for l in linhas]
    return out + [""]


def relatorio(aud: dict, desc: dict | None, aplicadas: dict, qa: dict,
              com_centros: bool) -> str:
    e = aud["estudos"]
    link = lambda n: f"[{n}](https://clinicaltrials.gov/study/{n})"  # noqa: E731
    props = [x for x in e if x.get("status_proposto")]
    fechado_br = [x for x in e if x.get("overall_status") == "RECRUITING"
                  and x.get("brazil_status") != ct.BR_RECRUITING]
    revisao = [x for x in e if x.get("revisao")]
    alertas = [x for x in e if x.get("alertas")]
    c_estado = Counter(x.get("brazil_status") for x in e)
    eventos = aud["eventos"]

    md = [f"# Trial Matcher — relatório de diferenças",
          "", f"Gerado em {aud['gerado_em']} · modo relatório (nada foi publicado)", ""]
    md += ["## Resumo", ""]
    md += [f"- **{len(e)}** cards auditados contra o ClinicalTrials.gov"
           + (f" (+{len(aud['sem_nct'])} sem NCT)" if aud["sem_nct"] else "")]
    md += ["- `brazil_status`: " + ", ".join(f"{k} **{c_estado.get(k, 0)}**" for k in ct.BRAZIL_STATUS)]
    md += [f"- **{len(props)}** cards com status a corrigir · "
           f"**{len(revisao)}** exigem revisão manual (sem alteração automática)"]
    if desc:
        f = desc["faixas"]
        md += [f"- descoberta: **{len(f['recomendado'])}** recomendados para curadoria, "
               f"{sum(len(v) for v in f.values())} candidatos novos no total "
               f"({desc['total_ctgov']} estudos na busca); "
               f"{len(desc.get('teranosticos', []))} marcados como teranósticos; "
               f"**{len((desc.get('overrides') or {}).get('aplicados', []))}** override(s) "
               f"humano(s) aplicado(s)"]
    md += [f"- QA do banco proposto: **{'OK' if qa['ok'] else 'BLOQUEADO'}**", ""]

    md += ["## 1. Estudos cujo status mudou", ""]
    if aud["primeira_rodada"]:
        md += ["_Primeira rodada com estado salvo: não há base para \"desde a última vez\". "
               "A tabela abaixo compara o card publicado com o registro de hoje._", ""]
    else:
        mud = [ev for ev in eventos if ev["tipo"] in ("overall_status", "brazil_status")]
        md += ["### Desde a última auditoria", ""]
        md += _tab([[link(ev["nct"]), ev["tipo"], ev["de"], ev["para"]] for ev in mud],
                   ["NCT", "o quê", "antes", "agora"])
    md += ["### Card publicado × registro atual", ""]
    md += _tab([[link(x["nct"]), x["nome"], x["overall_status"], x["brazil_status"],
                 x["status_card"], f"**{x['status_proposto']}**"] for x in
                sorted(props, key=lambda x: x["status_proposto"])],
               ["NCT", "estudo", "status global", "Brasil", "card hoje", "proposto"])

    md += ["## 2. Recrutam no mundo, mas não no Brasil", "",
           "Continuam `RECRUITING` no CT.gov, e nenhum centro brasileiro está `RECRUITING`.", ""]
    md += _tab([[link(x["nct"]), x["nome"], x["brazil_status"],
                 ", ".join(f"{k}×{v}" for k, v in x["status_centros_br"].items()),
                 x.get("status_proposto") or "—"]
                for x in fechado_br],
               ["NCT", "estudo", "brazil_status", "status dos centros no Brasil", "proposta"])

    md += ["## 3. Centros brasileiros adicionados/removidos", ""]
    if not aud["primeira_rodada"]:
        cen = [ev for ev in eventos if ev["tipo"].startswith("centro_br_")]
        md += ["### Desde a última auditoria", ""]
        md += _tab([[link(ev["nct"]), "＋" if ev["para"] else "－", ev["para"] or ev["de"]]
                    for ev in cen], ["NCT", "", "centro"])
    rec = [x for x in e if x.get("brazil_status") == ct.BR_RECRUITING
           and (x.get("centros_a_incluir") or x.get("centros_a_retirar"))]
    md += ["### Card × centros RECRUITING no registro (só estudos abertos no Brasil)", "",
           "Parte da diferença é só grafia: nomes curados à mão ('Hospital de Base / FAMERP') "
           "contra o nome resolvido do registro ('Funfarme Sjrp'). "
           + ("Aplicado no banco proposto (`--centros`)." if com_centros
              else "**Não** aplicado no banco proposto; use `--centros` para propor."), ""]
    md += _tab([[link(x["nct"]), x["nome"],
                 "<br>".join("＋ " + c for c in x["centros_a_incluir"]) or "—",
                 "<br>".join("－ " + c for c in x["centros_a_retirar"]) or "—"]
                for x in rec], ["NCT", "estudo", "no registro, fora do card", "no card, fora do registro"])

    if desc:
        f = desc["faixas"]
        nomes = {"rt_cirurgia": "Só radioterapia/procedimento",
                 "aguardando_brasil": "Ainda não abertos no Brasil",
                 "revisar": "Precisam de olhar humano antes da curadoria"}
        md += ["## 4. Novos estudos candidatos", "",
               "Oncologia, intervencional, com centro no Brasil, fora do Trial Matcher. "
               "Descartados antes da triagem: "
               + ", ".join(f"{k} ({v})" for k, v in desc["descartes"].items()), ""]
        for k, titulo in nomes.items():
            md += [f"### {titulo} ({len(f[k])})", ""]
            md += _tab([[link(x["nct"]), x["acronimo"] or "—", x["titulo"][:90],
                         "/".join(p.replace("PHASE", "F") for p in x["fases"]) or "—",
                         x["motivo"]] for x in f[k]],
                       ["NCT", "acrônimo", "título", "fase", "motivo"])
        ter = desc.get("teranosticos", [])
        faixa_de = {id(x): k for k, v in f.items() for x in v}
        md += [f"### Teranósticos marcados ({len(ter)}) — seguem a triagem normal", "",
               "Marcados pelo título ou pelas intervenções (radioisótopo, ligante "
               "radiomarcado, radioligante/radioconjugado); tratamento prévio citado "
               "no resumo não conta. A marca não inclui nem exclui: só sinaliza para "
               "a curadoria, que usa a modalidade `radioligante`.", ""]
        md += _tab([[link(x["nct"]), x["acronimo"] or "—", x["titulo"][:80],
                     "/".join(p.replace("PHASE", "F") for p in x["fases"]) or "—",
                     x["brazil_status"], faixa_de.get(id(x), "descartado"),
                     x.get("motivo", "")] for x in ter],
                   ["NCT", "acrônimo", "título", "fase", "Brasil", "faixa", "motivo"])
        md += secao_overrides(desc)
        md += ["## 5. Recomendados para inclusão", "",
               f"{len(f['recomendado'])} estudos: tratamento sistêmico, `RECRUITING` global, "
               "≥1 centro brasileiro `RECRUITING`, propósito TREATMENT, nunca recusados. "
               "Ordem: fase III primeiro, depois mais centros no Brasil. "
               "Estão em `_br_discovery.json` para a curadoria.", ""]
        md += _tab([[link(x["nct"]), x["acronimo"] or "—", x["titulo"][:90],
                     "/".join(p.replace("PHASE", "F") for p in x["fases"]) or "—",
                     x["centros_br_recrutando"], x["patrocinador"][:30],
                     "sim" if x.get("teranostico") else ""]
                    for x in f["recomendado"]],
                   ["NCT", "acrônimo", "título", "fase", "centros BR", "patrocinador", "RLT"])

    md += ["## 6. Revisão manual", ""]
    md += _tab([[link(x["nct"]), x["nome"], "; ".join(x["revisao"])] for x in revisao],
               ["NCT", "estudo", "por quê"])
    if aud["sem_nct"]:
        md += ["Cards sem NCT (fora da auditoria): "
               + ", ".join(s["nome"] or s["id"] for s in aud["sem_nct"]), ""]
    md += [f"### Alertas ({len(alertas)}) — registro sem reverificação há mais de 1 ano", "",
           "Não bloqueiam a proposta. O CT.gov marca \"Unknown status\" aos 2 anos.", ""]
    md += _tab([[link(x["nct"]), x["nome"], x["last_verified"], x["brazil_status"]]
                for x in sorted(alertas, key=lambda x: x["last_verified"])],
               ["NCT", "estudo", "verificado em", "Brasil"])

    md += ["## 7. QA do banco proposto", "",
           f"`scripts/_br_proposto/trials_br.js` — {qa.get('total_atual')} → "
           f"{qa.get('total_proposto')} cards; status corrigidos: {len(aplicadas['status'])}; "
           f"brazil_status gravado/alterado: {len(aplicadas.get('brazil_status', []))}; "
           f"centros reescritos: {len(aplicadas['centros'])}; rascunhos novos: "
           f"{len(aplicadas['curadoria'])}.", ""]
    md += [f"- FAIL: {f}" for f in qa["falhas"]] or ["- nenhuma falha"]
    md += [f"- WARN: {a}" for a in qa["avisos"]]
    md += [f"- {'✓' if v['ok'] else '✗'} {v['etapa']}" for v in qa.get("validadores", [])]
    md += ["", "Para aplicar (decisão humana): copie o proposto sobre "
           "`assets/js/trials_br.js`, revise o diff, rode `node scripts/sync_counts.mjs`, "
           "`node scripts/export_app_data.mjs` e os validadores, e só então commite.", ""]
    return "\n".join(md)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sem-descoberta", action="store_true")
    ap.add_argument("--centros", action="store_true",
                    help="propõe também reescrever centros/cidades/estados dos abertos")
    ap.add_argument("--com-curadoria", action="store_true",
                    help="inclui no proposto os rascunhos de _br_curated.json")
    ap.add_argument("--sem-rede-qa", action="store_true",
                    help="QA sem o validate_trials_br (mais rápido)")
    ap.add_argument("--gravar-estado", action="store_true",
                    help="atualiza br_estado.json e br_eventos.jsonl")
    ap.add_argument("--base", type=Path, default=ct.TRIALS_JS,
                    help="arquivo de partida do proposto (padrão: o banco publicado)")
    ap.add_argument("--permitir-meta", action="store_true",
                    help="aceita mudança na META aprovada à mão (vira aviso no QA)")
    args = ap.parse_args()

    import br_qa

    trials, _ = ct.carregar_trials()
    publicados = {t["nct"] for t in trials if (t.get("nct") or "").startswith("NCT")}

    print("[ciclo] 1/5 auditoria dos publicados", file=sys.stderr)
    aud = br_auditar.auditar(trials, br_auditar.ler_estado())

    desc = None
    if not args.sem_descoberta:
        print("[ciclo] 2/5 descoberta", file=sys.stderr)
        desc = descobrir(publicados)
        gravar_discovery(desc, publicados)

    print("[ciclo] 3/5 banco proposto", file=sys.stderr)
    aplicadas = propor(aud, args.centros, args.com_curadoria, publicados, args.base.resolve())

    print("[ciclo] 4/5 QA", file=sys.stderr)
    qa = br_qa.executar(PROPOSTO, rede=not args.sem_rede_qa, permitir_meta=args.permitir_meta)

    print("[ciclo] 5/5 relatório", file=sys.stderr)
    RELATORIO_MD.write_text(relatorio(aud, desc, aplicadas, qa, args.centros), encoding="utf-8")
    RELATORIO_JSON.write_text(json.dumps({
        "auditoria": {k: v for k, v in aud.items() if not k.startswith("_")},
        "descoberta": {k: v for k, v in (desc or {}).items() if not k.startswith("_")},
        "aplicadas_no_proposto": aplicadas,
        "qa": qa,
    }, ensure_ascii=False, indent=1), encoding="utf-8")

    if args.gravar_estado:
        br_auditar.gravar_estado(aud)

    print(br_auditar.resumo(aud))
    if desc:
        print(f"descoberta: {len(desc['faixas']['recomendado'])} recomendados de "
              f"{sum(len(v) for v in desc['faixas'].values())} candidatos")
    print(f"QA: {'OK' if qa['ok'] else 'BLOQUEADO'}")
    print(f"relatório: {RELATORIO_MD.relative_to(ct.SITE)}")
    print(f"proposto:  {PROPOSTO.relative_to(ct.SITE)}")
    return 0 if qa["ok"] else QA_BLOQUEADO


if __name__ == "__main__":
    sys.exit(main())
