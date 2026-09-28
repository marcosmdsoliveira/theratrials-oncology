#!/usr/bin/env python3
"""
db_freshness.py — freshness de alto sinal do Database (Fase 1). Só leitura.

Monta o registro de identidade (db_registro) sobre uma coleta nova e emite
alerta SÓ para:

  apresentado_publicado — card "Apresentado" que ganhou artigo revisado por
      pares ligado ao registro, publicado a partir do ano do congresso;
  publicado_sem_pmid — card "Publicado" sem `pubmed_url`, com relato de
      ensaio (tipado no PubMed) ligado ao registro;
  correcao — errata, expressão de preocupação ou retratação do artigo do
      card (PubMed CommentsCorrections e tipo "Retracted Publication";
      Crossref como complemento);
  ctgov — mudança relevante no registro contra o snapshot anterior:
      hasResults, resultsFirstPostDate, referência RESULT nova, status
      relevante. Sem snapshot anterior, só divergência clara com o card;
  inconsistencia_pmid_nct — o artigo do card declara outro NCT (DataBank),
      o mesmo PMID aparece em cards sem NCT em comum, o PMID não existe, o
      NCT não existe, ou o título é de outra coorte do NCT.

Todo o resto — follow-ups, análises secundárias, cards de desenho com
publicação, etc. — vai para o BASELINE BACKLOG na primeira fotografia
(scripts/db_backlog_baseline.json, criado uma vez e depois revisado à mão) e
nunca volta como alerta só por ser mais novo. Depois do baseline, artigo
novo sem sinal alto aparece uma vez no relatório como informativo.

Estados, separados de propósito:
  scripts/db_backlog_baseline.json — dívida editorial da primeira fotografia:
      sinais de alta prioridade daquele dia, itens do backlog (com campo
      `revisao` para a decisão humana), PMIDs conhecidos por uid, snapshot
      CT.gov. Nunca é sobrescrito.
  scripts/_db_estado.json — estado de máquina posterior: PMIDs vistos depois
      do baseline, snapshot CT.gov mais recente, chaves de alerta emitidas.
      Só avança numa execução completa (resposta parcial aborta antes).

Nenhum script db_* usa os arquivos de db_fontes.FONTES_PROIBIDAS.

Uso:
    python3 scripts/db_freshness.py                  # coleta nova; cria o baseline se não existir
    python3 scripts/db_freshness.py --reusar-coleta  # simulação: relatório sem baseline nem estado
    python3 scripts/db_freshness.py --sem-crossref   # não consulta a Crossref (complementar)
Saída: 0 = concluído; 2 = falha técnica (nada gravado).
"""
from __future__ import annotations

import json
import sys
import time
import urllib.error
from collections import Counter, defaultdict
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
import db_confianca as C  # noqa: E402
import db_registro as R  # noqa: E402
from br_ctgov import RespostaParcial  # noqa: E402

SAIDA = dict(R.SAIDA, **{
    "freshness": SCRIPTS / "_db_freshness.json",
    "freshness_md": SCRIPTS / "_db_freshness.md",
    "baseline_md": SCRIPTS / "_db_backlog_baseline.md",
    "estado": SCRIPTS / "_db_estado.json",
    "baseline_v1": SCRIPTS / "_db_backlog_baseline_v1.json",
    "prioridade": SCRIPTS / "_db_prioridade.json",
    "prioridade_md": SCRIPTS / "_db_prioridade.md",
})

CLASSES = {
    "apresentado_publicado": "\"Apresentado\" que ganhou artigo revisado por pares",
    "publicado_sem_pmid": "\"Publicado\" sem PMID, com publicação primária identificável",
    "correcao": "Correção, erratum ou retratação",
    "ctgov": "Mudança relevante no CT.gov",
    "inconsistencia_pmid_nct": "Inconsistência clara de PMID/NCT",
    "integridade": "Integridade do registro (uid)",
}
STATUS_RELEVANTE = {"COMPLETED", "TERMINATED", "WITHDRAWN", "SUSPENDED"}
GRAVIDADE_AVISO = {"retratacao": "crítica", "expressao_de_preocupacao": "crítica",
                   "corrigido_e_republicado": "alta", "republicado": "alta",
                   "errata": "média", "atualizacao": "média"}
ORDEM_GRAVIDADE = ["crítica", "alta", "média"]
INCONSISTENCIAS = ("databank_divergente", "pmid_compartilhado", "pmid_inexistente",
                   "nct_inexistente", "coorte_divergente")
RELACAO_NAO_PRIMARIA = ("secondary_analysis", "subgroup", "qol", "safety", "protocol",
                        "correction", "retraction")


def _ano(data: str) -> int:
    try:
        return int((data or "")[:4])
    except ValueError:
        return 0


def _item(pub: dict) -> dict:
    return {k: pub.get(k) for k in ("pmid", "doi", "titulo", "periodico", "data", "natureza",
                                    "relacao", "relacao_origem", "relacao_evidencia",
                                    "tipo_analise", "tipo_origem", "ligacao", "coorte")}


def snapshot_ctgov(coleta: dict) -> dict:
    return {n: {"status": c["status"], "has_results": c["has_results"],
                "results_first_post": c["results_first_post"],
                "result_refs": sorted(r["pmid"] for r in c["referencias"] if r["tipo"] == "RESULT")}
            for n, c in coleta["ctgov"].items() if c}


# ── Sinais de alta prioridade ───────────────────────────────────────────────

def sinais(registro: dict, dados: dict, coleta: dict, ctg_ant: dict | None,
           elegiveis: dict[str, set[str]] | None) -> list[dict]:
    """Puro. `elegiveis` = {uid: PMIDs novos}; None na primeira fotografia
    (todos elegíveis). `ctg_ant` = snapshot anterior do CT.gov ou None."""
    cards = {s["uid"]: s for s in dados["studies"]}
    out: list[dict] = []

    def alerta(classe, reg, chave, gravidade, motivo, **kw):
        out.append(dict(classe=classe, uid=reg["uid"], estudo=reg["estudo"],
                        categoria=reg["categoria"], chave=f"{classe}:{reg['uid']}:{chave}",
                        gravidade=gravidade, motivo=motivo, **kw))

    for reg in registro["cards"]:
        card, uid, st, pmid = cards[reg["uid"]], reg["uid"], reg["status_categoria"], reg["pmid_atual"]
        novos = None if elegiveis is None else elegiveis.get(uid, set())
        ano_ref = R.ano_de_referencia(card)
        relatos = [p for p in reg["publicacoes"] if p["pmid"] != pmid
                   and p["natureza"] in ("relato_de_ensaio", "artigo")
                   and p["relacao"] not in RELACAO_NAO_PRIMARIA and p["coorte"] is True
                   and p["ligacao"] and (novos is None or p["pmid"] in novos)]

        if st == "apresentado":
            for p in relatos:
                if not ano_ref or _ano(p["data"]) >= ano_ref:
                    alerta("apresentado_publicado", reg, p["pmid"], "alta",
                           f"card {reg['status_card']!r}; artigo ligado ao registro "
                           f"({', '.join(p['ligacao'])}) publicado em {p['data']}",
                           candidato=_item(p))

        if st == "publicado" and not pmid:
            cands = [p for p in relatos if p["natureza"] == "relato_de_ensaio"
                     and (not ano_ref or _ano(p["data"]) >= ano_ref)]
            cands.sort(key=lambda p: ("ctgov_result" not in p["ligacao"],
                                      p["relacao"] != "primary_publication", p["data"]))
            if cands:
                alerta("publicado_sem_pmid", reg, "|".join(p["pmid"] for p in cands), "alta",
                       "status Publicado e pubmed_url vazio; relatos de ensaio ligados ao registro, "
                       "em ordem de prioridade", candidatos=[_item(p) for p in cands[:5]])

        if reg["avisos"]:
            grav = min((GRAVIDADE_AVISO.get(a["tipo"], "alta") for a in reg["avisos"]),
                       key=ORDEM_GRAVIDADE.index)
            tipos = Counter(a["tipo"] for a in reg["avisos"])
            alerta("correcao", reg, "|".join(a["chave"] for a in reg["avisos"]), grav,
                   f"artigo do card (PMID {pmid}): "
                   + ", ".join(f"{n}× {t}" for t, n in sorted(tipos.items())),
                   avisos=reg["avisos"])

        for m in reg["motivos_revisao"]:
            if m.startswith(INCONSISTENCIAS):
                alerta("inconsistencia_pmid_nct", reg, m.split(":")[0], "alta", m)

        for nct in reg["identidade"]["nct"]:
            atual = coleta["ctgov"].get(nct)
            if not atual:
                continue
            ant = (ctg_ant or {}).get(nct)
            if ant:
                if atual["has_results"] and not ant.get("has_results"):
                    alerta("ctgov", reg, f"{nct}:has_results", "alta", f"{nct}: hasResults passou a true")
                if atual["results_first_post"] and not ant.get("results_first_post"):
                    alerta("ctgov", reg, f"{nct}:results_first_post", "alta",
                           f"{nct}: resultsFirstPostDate = {atual['results_first_post']}")
                if atual["status"] != ant.get("status") and (
                        atual["status"] in STATUS_RELEVANTE or ant.get("status") in STATUS_RELEVANTE):
                    alerta("ctgov", reg, f"{nct}:status:{atual['status']}", "média",
                           f"{nct}: status {ant.get('status')} → {atual['status']}"
                           + (f" ({atual['why_stopped']})" if atual["why_stopped"] else ""))
                novas = {r["pmid"] for r in atual["referencias"] if r["tipo"] == "RESULT"} \
                    - set(ant.get("result_refs", []))
                for p in sorted(novas):
                    alerta("ctgov", reg, f"{nct}:result:{p}", "alta",
                           f"{nct}: referência RESULT nova (PMID {p})")
            elif ctg_ant is None or nct not in ctg_ant:
                if atual["has_results"] and (st == "apresentado" or not pmid):
                    alerta("ctgov", reg, f"{nct}:has_results", "alta",
                           f"{nct}: resultados depositados no CT.gov "
                           f"({atual['results_first_post'] or 'data não informada'}), mas o card é "
                           f"{reg['status_card']!r} sem artigo")
                if st == "em_andamento" and atual["status"] in STATUS_RELEVANTE:
                    alerta("ctgov", reg, f"{nct}:status:{atual['status']}", "média",
                           f"{nct}: card diz {reg['status_card']!r}, CT.gov diz {atual['status']}"
                           + (f" ({atual['why_stopped']})" if atual["why_stopped"] else ""))
    return out


# ── Baseline backlog ────────────────────────────────────────────────────────

def itens_backlog(registro: dict, dados: dict, coleta: dict, alertas: list[dict]) -> list[dict]:
    """Dívida editorial da primeira fotografia: publicações ligadas ao
    registro, mais novas que a publicação do card (ou que o ano de
    referência, quando não há PMID), que não viraram sinal de alta prioridade."""
    cards = {s["uid"]: s for s in dados["studies"]}
    arts = coleta["artigos"]
    em_sinal = {(a["uid"], p["pmid"]) for a in alertas
                for p in ([a["candidato"]] if a.get("candidato") else []) + a.get("candidatos", [])}
    out = []
    for reg in registro["cards"]:
        card, pmid = cards[reg["uid"]], reg["pmid_atual"]
        rep = reg["publicacao_representada"] or {}
        limite = rep.get("data") or (str(R.ano_de_referencia(card) or "") if not pmid else "")
        for p in reg["publicacoes"]:
            if p["pmid"] == pmid or p["natureza"] not in ("relato_de_ensaio", "artigo", "protocolo"):
                continue
            if (limite and p["data"] < limite) or (reg["uid"], p["pmid"]) in em_sinal:
                continue
            destino = ("secondary-cards (candidata)" if p["relacao"] in
                       ("secondary_analysis", "subgroup", "qol", "safety")
                       else "outra coorte do NCT" if p["coorte"] is False
                       else "protocolo (sem ação)" if p["relacao"] == "protocol"
                       else "já citado no ref: conferir se incorporado"
                       if R.citado_no_ref(card, arts[p["pmid"]])
                       else "possível atualização: comparar com a representada"
                       if p["relacao"] == "follow_up" or p["tipo_analise"] in ("final", "long-term update")
                       else "revisar")
            pri = C.priorizar_publicacao(p, reg, card, coleta)
            out.append({
                "id": f"{reg['uid']}:{p['pmid']}", "uid": reg["uid"], "estudo": reg["estudo"],
                "categoria": reg["categoria"], "destino": destino,
                "representada": {"pmid": pmid, "tipo": reg["analise"]["tipo"],
                                 "origem": reg["analise"]["tipo_origem"], "data": rep.get("data")},
                "comparabilidade": R.comparabilidade(card, arts.get(pmid), arts[p["pmid"]], p)
                if destino.startswith("possível atualização") else None,
                **_item(p),
                "prioridade": {k: pri[k] for k in ("classe", "evidence_confidence",
                                                   "clinical_materiality", "acao", "motivo")},
            })
    return out


def criar_baseline(registro: dict, dados: dict, coleta: dict, alertas: list[dict],
                   criado_em: str | None = None) -> dict:
    return {
        "schema": "theratrials-db-backlog-baseline/2",
        "sobre": "Fotografia do dia zero do Database no pipeline de freshness: dívida editorial "
                 "existente, separada do que for detectado depois. IMUTÁVEL — não tem campo de "
                 "decisão; as decisões humanas ficam em db_decisoes.json, pelo `id` estável de "
                 "cada item. Nada aqui volta como alerta semanal. Reconstruível a partir da "
                 "coleta de `coleta_em` com as regras de `regras`.",
        "criado_em": criado_em or time.strftime("%Y-%m-%d", time.gmtime()),
        "coleta_em": coleta.get("gerado_em"),
        "complemento_em": coleta.get("complemento_em"),
        "regras": "db_registro/2 + db_confianca (Fase 1.5)",
        "crossref": coleta.get("crossref_status", "completa"),
        "sinais_alta_prioridade": alertas,
        "itens": itens_backlog(registro, dados, coleta, alertas),
        "pmids_por_uid": {c["uid"]: sorted({p["pmid"] for p in c["publicacoes"]}, key=int)
                          for c in registro["cards"]},
        "ctgov": snapshot_ctgov(coleta),
    }


# ── Execução ────────────────────────────────────────────────────────────────

def avaliar(registro: dict, dados: dict, coleta: dict, baseline: dict | None,
            estado: dict | None) -> dict:
    """Puro: não faz rede nem grava.

    Sem baseline: esta é a primeira fotografia — todos os sinais valem, o
    resto vira itens do baseline e o estado nasce vazio.
    Com baseline: só PMIDs que não estão no baseline nem no estado disparam
    sinais de artigo; sinais de card (correção, inconsistência, CT.gov) são
    deduplicados pelas chaves já emitidas."""
    uids = [c["uid"] for c in registro["cards"]]
    integridade = C.analisar_integridade(registro, dados, coleta)
    if baseline is None:
        alertas = sinais(registro, dados, coleta, None, None)
        priorizar(alertas, registro, dados, coleta, integridade)
        base = criar_baseline(registro, dados, coleta, alertas)
        est = {"schema": "theratrials-db-estado/1", "baseline_criado_em": base["criado_em"],
               "gerado_em": coleta.get("gerado_em"), "uids": uids, "vistos_pos_baseline": {},
               "ctgov": base["ctgov"], "alertas": sorted(a["chave"] for a in alertas)}
        return {"primeira_fotografia": True, "baseline": base, "alertas_novos": alertas,
                "alertas_pendentes": [], "novos_sem_alerta": [], "cards_novos": [],
                "integridade": integridade, "estado_novo": est}

    est_ant = estado or {"uids": list(baseline["pmids_por_uid"]), "vistos_pos_baseline": {},
                         "ctgov": baseline["ctgov"], "alertas": []}
    emitidos = set(est_ant["alertas"]) | {a["chave"] for a in baseline["sinais_alta_prioridade"]}
    conhecidos: dict[str, set] = defaultdict(set)
    for u, ps in list(baseline["pmids_por_uid"].items()) + list(est_ant["vistos_pos_baseline"].items()):
        conhecidos[u] |= set(ps)

    cards_novos, elegiveis, novos_pmids = [], {}, {}
    for c in registro["cards"]:
        atuais = {p["pmid"] for p in c["publicacoes"]}
        if c["uid"] not in baseline["pmids_por_uid"] and c["uid"] not in est_ant["vistos_pos_baseline"]:
            cards_novos.append(c["uid"])          # card entrou depois: registra sem alertar artigos
            novos_pmids[c["uid"]], elegiveis[c["uid"]] = atuais, set()
        else:
            novos_pmids[c["uid"]] = atuais - conhecidos[c["uid"]]
            elegiveis[c["uid"]] = novos_pmids[c["uid"]]

    alertas = sinais(registro, dados, coleta, est_ant["ctgov"], elegiveis)
    priorizar(alertas, registro, dados, coleta, integridade)
    for u in sorted(set(est_ant["uids"]) - set(uids)):
        alertas.append(dict(classe="integridade", uid=u, estudo="", categoria="",
                            chave=f"integridade:{u}:removido", gravidade="crítica",
                            motivo="uid da execução anterior ausente do data.js — deep links, "
                                   "favoritos e parentUid quebram"))
    em_sinal = {(a["uid"], p["pmid"]) for a in alertas
                for p in ([a["candidato"]] if a.get("candidato") else []) + a.get("candidatos", [])}
    novos_sem_alerta = [
        dict(uid=c["uid"], estudo=c["estudo"], categoria=c["categoria"], **_item(p))
        for c in registro["cards"] for p in c["publicacoes"]
        if p["pmid"] in novos_pmids[c["uid"]] and c["uid"] not in cards_novos
        and (c["uid"], p["pmid"]) not in em_sinal]

    vistos = {u: list(ps) for u, ps in est_ant["vistos_pos_baseline"].items()}
    for u, ps in novos_pmids.items():
        if ps:
            vistos[u] = sorted(set(vistos.get(u, [])) | ps, key=int)
    est = {"schema": "theratrials-db-estado/1", "baseline_criado_em": baseline["criado_em"],
           "gerado_em": coleta.get("gerado_em"), "uids": uids, "vistos_pos_baseline": vistos,
           "ctgov": snapshot_ctgov(coleta),
           "alertas": sorted(set(est_ant["alertas"]) | {a["chave"] for a in alertas})}
    return {"primeira_fotografia": False, "baseline": None,
            "alertas_novos": [a for a in alertas if a["chave"] not in emitidos],
            "alertas_pendentes": [a for a in alertas if a["chave"] in emitidos],
            "novos_sem_alerta": novos_sem_alerta, "cards_novos": cards_novos,
            "integridade": integridade, "estado_novo": est}


def priorizar(alertas: list[dict], registro: dict, dados: dict, coleta: dict, integridade: dict) -> None:
    """Acrescenta a cada sinal os itens priorizados (P0–P3/WATCH), com os
    eixos evidence_confidence e clinical_materiality separados."""
    cards = {s["uid"]: s for s in dados["studies"]}
    regs = {r["uid"]: r for r in registro["cards"]}
    for a in alertas:
        if a["uid"] not in regs:
            a["prioridade"] = [dict(uid=a["uid"], classe=C.P0, evidence_confidence="alta",
                                    clinical_materiality="alta", acao="humana", motivo=a["motivo"],
                                    id=a["chave"])]
            continue
        itens = C.priorizar_sinal(a, regs[a["uid"]], cards[a["uid"]], coleta, integridade)
        liberados = {h["nota"] for h in (regs[a["uid"]].get("integrity_hold") or {}).get("historico", [])
                     if h.get("liberado_por")}
        for it in itens:
            av = it.get("aviso") or {}
            if it["classe"] == C.P0 and av.get("tipo") in ("expressao_de_preocupacao", "retratacao") and \
                    (av.get("doi") or av.get("pmid")) in liberados:
                it.update(acao="arquivar", motivo=f"{av['tipo']} registrada no histórico; hold liberado por "
                          "decisão humana")
        if regs[a["uid"]].get("quarentena_editorial"):
            for it in itens:
                it.update(acao="arquivar", motivo="card em quarentena editorial por decisão humana — "
                          + it["motivo"], quarentena=regs[a["uid"]]["quarentena_editorial"]["id"])
        for it in itens:
            it["id"] = a["chave"] + (f"|{it['aviso']['chave']}" if it.get("aviso") else "")
        a["prioridade"] = itens


def aplicar_decisoes(itens: list[dict], decisoes: list[dict], hoje: str) -> tuple[list, list]:
    """(itens que ainda pedem decisão, itens resolvidos por decisão humana)."""
    por_id = {}
    for d in decisoes:
        if d["tipo"] in ("ignore", "approve") or (d["tipo"] == "defer" and d["ate"] >= hoje):
            por_id[d["id"]] = d
    abertos, resolvidos = [], []
    for it in itens:
        (resolvidos if it["id"] in por_id else abertos).append(it)
    return abertos, resolvidos


# ── Relatórios ──────────────────────────────────────────────────────────────

def _fmt_pub(p: dict) -> str:
    return (f"PMID {p['pmid']} · {p['data']} · {p['periodico']} · {p['relacao']}"
            f"{' (' + p['relacao_origem'] + ')' if p.get('relacao_origem') else ''} — "
            f"{(p['titulo'] or '')[:140]}")


def md_freshness(res: dict, reg: dict, coleta: dict) -> str:
    L = [f"# Freshness do Database — {reg['gerado_em'][:10]}", "",
         "Gerado por `scripts/db_freshness.py`. Somente leitura: nada foi alterado no `data.js`. "
         "Todo sinal é CANDIDATO — a decisão é humana, contra a fonte primária.", ""]
    if res["primeira_fotografia"]:
        L += ["**Primeira fotografia (baseline).** Os sinais abaixo são dívida existente de alta "
              "prioridade. O resto está em `db_backlog_baseline.json` (visão em "
              "`_db_backlog_baseline.md`) e não volta como alerta. Mudanças no CT.gov só são "
              "detectáveis a partir da próxima execução; aqui, só divergências claras com o card.", ""]
    cont = Counter(a["classe"] for a in res["alertas_novos"])
    L += ["| Sinal | Novos |", "|---|---|"] + [f"| {CLASSES[c]} | {cont.get(c, 0)} |" for c in CLASSES]
    L += ["", f"Pendentes (já emitidos): {len(res['alertas_pendentes'])} · novos sem alerta: "
          f"{len(res['novos_sem_alerta'])} · cards novos: {len(res['cards_novos'])}",
          f"Coleta {coleta.get('gerado_em')} · {coleta.get('duracao_s')} s · chamadas "
          f"{coleta.get('chamadas')} · Crossref {coleta.get('crossref_status', 'completa')}", ""]
    for classe in CLASSES:
        itens = [a for a in res["alertas_novos"] if a["classe"] == classe]
        if not itens:
            continue
        L += [f"## {CLASSES[classe]} ({len(itens)})", ""]
        for a in sorted(itens, key=lambda a: (ORDEM_GRAVIDADE.index(a["gravidade"]), a["categoria"], a["uid"])):
            L += [f"- **`{a['uid']}`** — {a['estudo']} · gravidade {a['gravidade']}  ", f"  {a['motivo']}"]
            if a.get("candidato"):
                L.append(f"  - candidato: {_fmt_pub(a['candidato'])}")
            for c in a.get("candidatos", []):
                L.append(f"  - candidato: {_fmt_pub(c)}")
            for v in a.get("avisos", []):
                L.append(f"  - {v['tipo']} · {v['doi'] or 'PMID ' + str(v['pmid'])} · "
                         f"{v['ref'] or v['data']} · fontes: {', '.join(v['fontes'])}")
        L.append("")
    if res["novos_sem_alerta"]:
        L += [f"## Novos depois do baseline, sem sinal alto ({len(res['novos_sem_alerta'])})", ""]
        L += [f"- `{x['uid']}` — {_fmt_pub(x)}" for x in res["novos_sem_alerta"]]
    return "\n".join(L) + "\n"


def md_baseline(base: dict) -> str:
    por_cat: dict[str, list] = defaultdict(list)
    for b in base["itens"]:
        por_cat[b["categoria"]].append(b)
    destinos = sorted({b["destino"] for b in base["itens"]})
    L = [f"# Baseline backlog do Database — {base['criado_em']}", "", base["sobre"], "",
         f"Itens: {len(base['itens'])} · cards: {len({b['uid'] for b in base['itens']})} · "
         f"sinais de alta prioridade na fotografia: {len(base['sinais_alta_prioridade'])}", "",
         "| Categoria | Itens | " + " | ".join(destinos) + " |",
         "|---|---|" + "---|" * len(destinos)]
    for cat, itens in sorted(por_cat.items(), key=lambda kv: -len(kv[1])):
        d = Counter(i["destino"] for i in itens)
        L.append(f"| {cat} | {len(itens)} | " + " | ".join(str(d.get(x, 0)) for x in destinos) + " |")
    L.append("")
    for cat, itens in sorted(por_cat.items()):
        L += [f"## {cat} ({len(itens)})", ""]
        for i in sorted(itens, key=lambda i: (i["uid"], i["data"])):
            comp = i.get("comparabilidade") or {}
            extra = f" · diferenças: {'; '.join(comp['diferencas'])}" if comp.get("diferencas") else ""
            L.append(f"- `{i['uid']}` → {i['destino']} — {_fmt_pub(i)}{extra}")
        L.append("")
    return "\n".join(L)


def relatorio_prioridade(reg: dict, dados: dict, coleta: dict, baseline: dict, res: dict) -> dict:
    """Fase 1.5: confiança por domínio, redução da revisão, sinais por
    prioridade, integridade PMID/NCT e inbox (dia zero e semana normal)."""
    from datetime import date
    cards = reg["cards"]
    antes = [c for c in cards if c["motivos_revisao"]]          # requires_review da Fase 1
    decisoes, avisos_dec = R.ler_decisoes()
    hoje = date.today().isoformat()

    def nivel(c, d):
        return str(c["automation"][d].get("nivel"))

    def faixa(c):
        i, r = nivel(c, "identity"), nivel(c, "publication_relationship")
        if i == "conflito":
            return "conflito entre fontes"
        if i == C.MV and r == C.MV:
            return "identidade e relação verificadas por máquina"
        if i == C.MV:
            return "identidade verificada; relação só inferida ou n/a"
        return "identidade não verificada (sem conflito)"

    # O baseline guarda FATOS do dia zero; a prioridade é recalculada aqui com as
    # regras vigentes e as decisões registradas (o baseline não muda).
    regs = {c["uid"]: c for c in cards}
    sinais_base = [dict(a) for a in baseline["sinais_alta_prioridade"]]
    vigentes = [a for a in sinais_base if not (
        a["classe"] == "inconsistencia_pmid_nct" and a["uid"] in regs
        and not any(m.startswith(a["motivo"].split(":")[0]) for m in regs[a["uid"]]["motivos_revisao"]))]
    resolvidos_no_registro = [a["chave"] for a in sinais_base if a not in vigentes]
    priorizar(vigentes, reg, dados, coleta, res.get("integridade") or C.analisar_integridade(reg, dados, coleta))
    sinais_itens = [it for a in vigentes for it in a.get("prioridade", [])]
    abertos, resolvidos = aplicar_decisoes(sinais_itens, decisoes, hoje)
    cards_d = {x["uid"]: x for x in dados["studies"]}
    itens_bl = []
    for i in baseline["itens"]:
        pub = next((p for p in (regs.get(i["uid"]) or {}).get("publicacoes", []) if p["pmid"] == i["pmid"]), None)
        pri = C.priorizar_publicacao(pub, regs[i["uid"]], cards_d[i["uid"]], coleta) if pub and i["uid"] in regs \
            else i["prioridade"]
        itens_bl.append(dict({k: pri[k] for k in ("classe", "evidence_confidence", "clinical_materiality",
                                                  "acao", "motivo")}, id=i["id"], uid=i["uid"]))
    bl_abertos, bl_resolvidos = aplicar_decisoes(itens_bl, decisoes, hoje)
    return {
        "gerado_em": reg["gerado_em"], "baseline_criado_em": baseline["criado_em"],
        "decisoes_validas": len(decisoes), "avisos_decisoes": avisos_dec,
        "confianca": {
            "faixas": dict(Counter(faixa(c) for c in cards)),
            "identity": dict(Counter(nivel(c, "identity") for c in cards)),
            "identity_regra": dict(Counter((c["automation"]["identity"].get("regra") or "—").split(":")[0]
                                           for c in cards)),
            "bibliographic_metadata": dict(Counter(nivel(c, "bibliographic_metadata") for c in cards)),
            "publication_relationship": dict(Counter(nivel(c, "publication_relationship") for c in cards)),
            "clinical_extraction": dict(Counter(nivel(c, "clinical_extraction") for c in cards)),
            "autorizado": {d: sum(bool(c["automation"][d]["autorizado"]) for c in cards) for d in C.DOMINIOS},
            "divergencias_bibliograficas": [
                {"uid": c["uid"], "divergencias": c["automation"]["bibliographic_metadata"]["divergencias"]}
                for c in cards if c["automation"]["bibliographic_metadata"].get("divergencias")],
        },
        "reducao_revisao": {
            "antes": len(antes),
            "agora": sum(c["requires_review"] for c in cards),
            "dos_antes_identidade_machine_verified": sum(nivel(c, "identity") == C.MV for c in antes),
            "dos_antes_por_destino": dict(Counter(
                "decisão agora" if c["revisao"]["agora"] else
                "identidade não verificada, sem conflito" if c["revisao"]["identidade_insuficiente"] else
                "clínico sob demanda" if c["revisao"]["clinico_sob_demanda"] else
                "editorial (P3)" if c["revisao"]["editorial"] else "watch" for c in antes)),
            "restantes_por_razao": {
                "agora": dict(Counter(m.split(":")[0] for c in cards for m in c["revisao"]["agora"])),
                "identidade_insuficiente": dict(Counter(
                    c["automation"]["identity"].get("falta") or "?" for c in cards
                    if c["automation"]["identity"]["nivel"] == "insuficiente")),
                "clinico_sob_demanda": dict(Counter(m.split(":")[0] for c in cards
                                                    for m in c["revisao"]["clinico_sob_demanda"])),
                "editorial": dict(Counter(m.split(":")[0] for c in cards for m in c["revisao"]["editorial"])),
            },
        },
        "sinais": {
            "total_sinais": len(baseline["sinais_alta_prioridade"]),
            "resolvidos_no_registro_por_decisao": resolvidos_no_registro,
            "itens": len(sinais_itens),
            "por_classe": dict(Counter(i["classe"] for i in sinais_itens)),
            "por_classe_e_acao": dict(Counter(f"{i['classe']} → {i['acao']}" for i in sinais_itens)),
            "por_eixos": dict(Counter(f"evidência {i['evidence_confidence']} × materialidade "
                                      f"{i['clinical_materiality']}" for i in sinais_itens)),
            "itens_detalhe": sinais_itens,
        },
        "integridade": list(res.get("integridade", {}).values()),
        "inbox_dia_zero": {
            "sinais": dict(Counter(i["acao"] for i in abertos)),
            "sinais_resolvidos_por_decisao": len(resolvidos),
            "baseline": dict(Counter(i["acao"] for i in bl_abertos)),
            "baseline_por_classe": dict(Counter(f"{i['classe']} → {i['acao']}" for i in bl_abertos)),
            "baseline_resolvidos_por_decisao": len(bl_resolvidos),
        },
        "inbox_semanal": C.simular_inbox(reg, dados, coleta, date.fromisoformat(reg["gerado_em"][:10])),
    }


def md_prioridade(r: dict) -> str:
    c, rd, sg, ib, sem = (r["confianca"], r["reducao_revisao"], r["sinais"], r["inbox_dia_zero"],
                          r["inbox_semanal"])
    L = [f"# Fase 1.5 — confiança, prioridade e inbox · {r['gerado_em'][:10]}", "",
         "Somente leitura. Nenhuma escrita no Database publicado é autorizada. `machine_verified` "
         "vale para identidade e relação bibliográfica, nunca para extração clínica.", "",
         "## Confiança por domínio (503 cards)", ""]
    for k in ("faixas", "identity", "identity_regra", "bibliographic_metadata", "publication_relationship",
              "clinical_extraction", "autorizado"):
        L.append(f"- **{k}**: {c[k]}")
    L += ["", f"Divergências bibliográficas (P3): {len(c['divergencias_bibliograficas'])}", ""]
    L += [f"  - `{d['uid']}`: {'; '.join(d['divergencias'])}" for d in c["divergencias_bibliograficas"]]
    L += ["", "## Revisão humana", "",
          f"- Antes (Fase 1): {rd['antes']} · agora: {rd['agora']}",
          f"- Dos {rd['antes']}, identidade machine_verified: {rd['dos_antes_identidade_machine_verified']}",
          f"- Destino dos {rd['antes']}: {rd['dos_antes_por_destino']}", ""]
    for k, v in rd["restantes_por_razao"].items():
        L.append(f"- **{k}**: {v}")
    L += ["", f"## Sinais do dia zero ({sg['total_sinais']} sinais → {sg['itens']} itens)", "",
          f"- por classe: {sg['por_classe']}", f"- por classe e ação: {sg['por_classe_e_acao']}",
          f"- eixos: {sg['por_eixos']}", ""]
    for i in sorted(sg["itens_detalhe"], key=lambda i: (i["classe"], i["acao"], i["uid"])):
        if i["acao"] == "humana" or i["classe"].startswith("P0"):
            L.append(f"- {i['classe']} · {i['acao']} · `{i['uid']}` — {i['motivo'][:110]} "
                     f"(evidência {i['evidence_confidence']}, materialidade {i['clinical_materiality']})")
    L += ["", "## Integridade PMID/NCT", ""]
    for a in r["integridade"]:
        L += [f"### `{a['uid']}` — {a['estudo']} → **{a['classificacao']}**", "",
              f"- identidade atual: NCT {a['identidade_atual']['nct'] or '—'} · PMID "
              f"{a['identidade_atual']['pmid']} · artigo declara {a['identidade_atual']['nct_no_artigo'] or '—'}",
              f"- artigo: {a['identidade_atual']['artigo'][:120]}",
              f"- motivo: {'; '.join(a['motivo'])}", f"- conclusão: {a['erro']}",
              f"- concordam: {'; '.join(a['fontes_concordam']) or '—'}",
              f"- divergem: {'; '.join(a['fontes_divergem']) or '—'}"]
        L += [f"- candidato: PMID {x['pmid']} ({x['data']}) — {x['titulo'][:100]} [{x['por']}]"
              for x in a["candidatos"]] or ["- candidato: nenhum encontrado"]
        L.append("")
    L += ["## Inbox", "", f"Dia zero — sinais: {ib['sinais']} · baseline: {ib['baseline']}",
          f"Baseline por classe: {ib['baseline_por_classe']}", "",
          f"Semana normal (simulação das últimas {sem['semanas']} semanas desde {sem['inicio']}): "
          f"totais {sem['totais']}", f"Decisões humanas por semana: {sem['humana_por_semana']}", ""]
    for s, v in sem["exemplos_humanos"].items():
        L += [f"- semana {s}:"] + [f"  - {x}" for x in v]
    return "\n".join(L) + "\n"


def carregar(caminho: Path) -> dict | None:
    return json.loads(caminho.read_text(encoding="utf-8")) if caminho.exists() else None


def executar(reusar: bool, usar_crossref: bool = True, migrar_baseline: bool = False) -> int:
    t0 = time.time()
    dados = R.carregar_dados()
    try:
        coleta = R.obter_coleta(dados, reusar, usar_crossref)
    except (RespostaParcial, urllib.error.URLError, TimeoutError, OSError) as e:
        print(f"FALHA TÉCNICA na coleta: {e}\nNada foi gravado: nem relatório, nem baseline, nem estado.",
              file=sys.stderr)
        return R.FALHA_TECNICA
    reg = R.construir(dados, coleta)
    baseline = carregar(R.BASELINE)
    if migrar_baseline:
        if not baseline or baseline.get("schema") != "theratrials-db-backlog-baseline/1":
            print("nada a migrar: não há baseline v1", file=sys.stderr)
            return 1
        if baseline.get("coleta_em") != coleta.get("gerado_em"):
            print("recusado: a coleta atual não é a do dia zero do baseline v1", file=sys.stderr)
            return 1
        v1 = baseline
        res = avaliar(reg, dados, coleta, None, None)
        res["baseline"]["criado_em"] = v1["criado_em"]
        R.gravar(SAIDA["baseline_v1"], json.dumps(v1, ensure_ascii=False))
        R.gravar(R.BASELINE, json.dumps(res["baseline"], ensure_ascii=False, indent=1),
                 migrar_baseline_v1=True)
        R.gravar(SAIDA["baseline_md"], md_baseline(res["baseline"]))
        R.gravar(SAIDA["estado"], json.dumps(res["estado_novo"], ensure_ascii=False))
        baseline = res["baseline"]
        print(f"baseline migrado v1 → v2 ({len(baseline['itens'])} itens); v1 guardado em "
              f"{SAIDA['baseline_v1'].name}", file=sys.stderr)
    res = avaliar(reg, dados, coleta, baseline, carregar(SAIDA["estado"])) if not migrar_baseline else res
    rel = relatorio_prioridade(reg, dados, coleta, baseline or res["baseline"], res)
    R.gravar(SAIDA["prioridade"], json.dumps(rel, ensure_ascii=False, indent=1))
    R.gravar(SAIDA["prioridade_md"], md_prioridade(rel))

    if not reusar:
        R.gravar(SAIDA["coleta"], json.dumps(coleta, ensure_ascii=False))
    R.gravar(SAIDA["registro"], json.dumps(reg, ensure_ascii=False, indent=1))
    R.gravar(SAIDA["registro_md"], R.md_registro(reg, coleta))
    corpo = {k: v for k, v in res.items() if k not in ("estado_novo", "baseline")}
    R.gravar(SAIDA["freshness"], json.dumps(corpo, ensure_ascii=False, indent=1))
    R.gravar(SAIDA["freshness_md"], md_freshness(res, reg, coleta))
    if res["baseline"] is not None:
        R.gravar(SAIDA["baseline_md"], md_baseline(res["baseline"]))
    if not reusar:          # baseline e estado só nascem/avançam de coleta nova e completa
        if res["baseline"] is not None:
            R.gravar(R.BASELINE, json.dumps(res["baseline"], ensure_ascii=False, indent=1),
                     criar_somente=True)
        R.gravar(SAIDA["estado"], json.dumps(res["estado_novo"], ensure_ascii=False))
    print(json.dumps({"registro": R.resumo(reg),
                      "alertas_novos": dict(Counter(a["classe"] for a in res["alertas_novos"])),
                      "pendentes": len(res["alertas_pendentes"]),
                      "baseline_itens": len(res["baseline"]["itens"]) if res["baseline"] else None,
                      "novos_sem_alerta": len(res["novos_sem_alerta"]),
                      "tempo_total_s": round(time.time() - t0, 1)}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(executar(reusar="--reusar-coleta" in a, usar_crossref="--sem-crossref" not in a,
                      migrar_baseline="--migrar-baseline-v1" in a))
