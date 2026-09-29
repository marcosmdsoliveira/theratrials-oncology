#!/usr/bin/env python3
"""
db_integridade.py — backlog CANÔNICO de candidatos de integridade do Database.

`scripts/db_candidatos_integridade.json` é memória editorial versionada, não relatório de execução.
Saídas brutas de varreduras futuras vão para scripts/_db_* (ignorados) e só entram aqui por `mesclar()`.

    python3 scripts/db_integridade.py --validar     # invariantes do arquivo versionado
    python3 scripts/db_integridade.py --resumo      # distribuição por status/prioridade/tipo

Invariantes (validar()):
  • id único e estável ("INT-<uid>-<nnn>"); nunca reutilizado;
  • status ∈ open | confirmed | dismissed | resolved | deferred;
  • confirmed/resolved/dismissed exigem last_reviewed_at; dismissed exige human_decision;
  • resolved exige resolution.commit = SHA-1 completo (40 hex); não se consulta a rede;
  • dedupe_key = uid|issue_type|campos ordenados[|dedupe_discriminator] e é ÚNICA no backlog;
  • history só cresce (cada mudança de status deixa um evento).
dedupe_discriminator: opcional; só quando dois problemas distintos caem no mesmo uid|issue_type|campos.
Nomeia a diferença conceitual (slug estável, ex. "fatal_event_omitted"), nunca um contador.
Regras de mesclagem (mesclar()):
  • nunca apaga item; nunca rebaixa confirmed/resolved/dismissed;
  • candidato com a mesma dedupe_key NÃO cria item novo: se a descrição é parecida, acrescenta evidência e
    evento ao item existente (mesmo id); se é distinta, recusa — o problema novo precisa de dedupe_discriminator.
"""
from __future__ import annotations

import argparse
import collections
import difflib
import json
import re
import sys
import unicodedata
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
ARQUIVO = SCRIPTS / "db_candidatos_integridade.json"
SCHEMA = "theratrials-db-integridade/2"

STATUS = ["open", "confirmed", "dismissed", "resolved", "deferred"]
FINAIS = {"confirmed", "dismissed", "resolved"}          # nunca rebaixados por máquina
PRIORIDADE = ["high", "medium", "low"]
DETECCAO = ["primary_source_check", "card_internal_contradiction", "reviewer_prior_knowledge", "pipeline_signal",
            "production_review"]
ISSUE_TYPES = [
    "statistical_interpretation",   # significância/hipótese/NI lidas errado
    "arm_or_comparator",            # braço experimental/controle trocado ou descrito errado
    "design_misrepresentation",     # randomização, cegamento, sequência, fases
    "population_misrepresentation", # população/indicação/cenário
    "eligibility_mismatch",
    "endpoint_hierarchy",           # primário ausente/trocado, secundário como primário
    "numeric_mismatch",             # número divergente da fonte
    "safety_misattribution",        # toxicidade atribuída ao braço/estudo errado ou omitida
    "unsupported_claim",            # afirmação sem lastro na fonte
    "bibliographic_mismatch",       # ano, periódico, publicação representada, congresso
    "identifier_mismatch",          # NCT/PMID de outro estudo
    "category_misclassification",
    "aggregation",                  # card que agrega várias fontes
    "source_internal_inconsistency",  # erro/incoerência dentro da PRÓPRIA fonte (não do card)
    "cross_source_conflict",        # publicação × registro × outra publicação
    "publication_relationship",     # não está claro qual publicação o card representa (primária × update × final × coorte)
    "markup_or_format",
]


def norm_txt(t: str) -> str:
    t = unicodedata.normalize("NFKC", t or "").lower()
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s%.,<>≥≤=]", " ", t)).strip()


SHA_COMMIT = re.compile(r"^[0-9a-f]{40}$")
DISCRIMINADOR = re.compile(r"^[a-z][a-z0-9_]{3,}$")              # slug; contadores ("item_2") recusados abaixo
DISCRIMINADOR_GENERICO = re.compile(r"^(item|issue|problema|caso|outro|novo|dup|duplicado)?_?\d*$")


def bucket(item: dict) -> str:
    return f"{item['uid']}|{item['issue_type']}|{','.join(sorted(item.get('affected_fields') or []))}"


def dedupe_key(item: dict) -> str:
    d = item.get("dedupe_discriminator")
    return f"{bucket(item)}|{d}" if d else bucket(item)


def commit_valido(resolucao) -> bool:
    return isinstance(resolucao, dict) and isinstance(resolucao.get("commit"), str) and bool(
        SHA_COMMIT.match(resolucao["commit"]))


def similar(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, norm_txt(a), norm_txt(b)).ratio()


def carregar(caminho: Path = ARQUIVO) -> dict:
    return json.loads(caminho.read_text(encoding="utf-8"))


def gravar(doc: dict, caminho: Path = ARQUIVO) -> None:
    doc["itens"].sort(key=lambda x: (x["uid"], x["id"]))
    caminho.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def proximo_id(doc: dict, uid: str) -> str:
    usados = [int(m.group(1)) for x in doc["itens"] if x["uid"] == uid
              for m in [re.search(r"-(\d{3})$", x["id"])] if m]
    usados += [int(m.group(1)) for i in doc.get("ids_retirados", []) if i.startswith(f"INT-{uid}-")
               for m in [re.search(r"-(\d{3})$", i)] if m]
    return f"INT-{uid}-{(max(usados) + 1 if usados else 1):03d}"


def validar(doc: dict) -> list[str]:
    erros = []
    if doc.get("schema") != SCHEMA:
        erros.append(f"schema {doc.get('schema')!r} ≠ {SCHEMA}")
    ids = [x["id"] for x in doc["itens"]]
    for i, n in collections.Counter(ids).items():
        if n > 1:
            erros.append(f"id duplicado: {i}")
    for i in set(ids) & set(doc.get("ids_retirados", [])):
        erros.append(f"id retirado reutilizado: {i}")
    obrig = ["id", "uid", "card", "issue_type", "description", "affected_fields", "evidence", "priority",
             "detection_method", "status", "first_detected_at", "last_reviewed_at", "human_decision",
             "resolution", "history", "dedupe_key"]
    for x in doc["itens"]:
        c = x.get("id", "?")
        for k in obrig:
            if k not in x:
                erros.append(f"{c}: falta {k}")
        if x.get("status") not in STATUS:
            erros.append(f"{c}: status {x.get('status')!r}")
        if x.get("priority") not in PRIORIDADE:
            erros.append(f"{c}: priority {x.get('priority')!r}")
        if x.get("issue_type") not in ISSUE_TYPES:
            erros.append(f"{c}: issue_type {x.get('issue_type')!r}")
        if x.get("detection_method") not in DETECCAO:
            erros.append(f"{c}: detection_method {x.get('detection_method')!r}")
        if x.get("status") == "resolved" and not commit_valido(x.get("resolution")):
            erros.append(f"{c}: resolved sem resolution.commit válido (SHA completo de 40 hex)")
        if "dedupe_discriminator" in x:
            d = x["dedupe_discriminator"]
            if not (isinstance(d, str) and DISCRIMINADOR.match(d)
                    and not DISCRIMINADOR_GENERICO.match(d)):
                erros.append(f"{c}: dedupe_discriminator {d!r} não é um slug conceitual estável")
        if x.get("status") == "dismissed" and not x.get("human_decision"):
            erros.append(f"{c}: dismissed sem decisão humana")
        if x.get("status") in FINAIS and not x.get("last_reviewed_at"):
            erros.append(f"{c}: {x['status']} sem last_reviewed_at")
        if x.get("dedupe_key") and x["dedupe_key"] != dedupe_key(x):
            erros.append(f"{c}: dedupe_key desatualizada")
        if not x.get("history"):
            erros.append(f"{c}: history vazio")
    for k, n in collections.Counter(x.get("dedupe_key") for x in doc["itens"]).items():
        if n > 1:
            erros.append(f"dedupe_key duplicada ({n}x): {k}")
    return erros


def invariantes_de_transicao(antes: dict, depois: dict) -> list[str]:
    """Compara duas versões do arquivo: nada some, nada final é rebaixado, history só cresce."""
    erros = []
    a = {x["id"]: x for x in antes["itens"]}
    d = {x["id"]: x for x in depois["itens"]}
    for i, x in a.items():
        if i not in d:
            erros.append(f"{i}: item apagado ({x['status']})")
            continue
        if x["status"] in FINAIS and d[i]["status"] not in FINAIS | {"resolved"}:
            erros.append(f"{i}: {x['status']} rebaixado para {d[i]['status']}")
        if len(d[i].get("history", [])) < len(x.get("history", [])):
            erros.append(f"{i}: history encolheu")
        if d[i]["history"][:len(x["history"])] != x["history"]:
            erros.append(f"{i}: history reescrito")
    return erros


def mesclar(doc: dict, candidato: dict, hoje: str, origem: str) -> tuple[str, str]:
    """Incorpora um candidato de varredura. Retorna (id, 'novo'|'existente').

    A dedupe_key é única: um candidato com a chave de um item existente é o mesmo problema (redetecção)
    ou, se a descrição for distinta, é recusado até ganhar um dedupe_discriminator próprio."""
    chave = dedupe_key(candidato)
    alvo = next((x for x in doc["itens"] if x["dedupe_key"] == chave), None)
    if alvo is not None:
        if similar(alvo["description"], candidato["description"]) < 0.6:
            raise ValueError(f"{chave}: já existe {alvo['id']} com outro problema; dê ao candidato um "
                             "dedupe_discriminator que nomeie a diferença")
        novas = [e for e in candidato.get("evidence", []) if e not in alvo["evidence"]]
        alvo["evidence"] += novas
        alvo["history"].append({"at": hoje, "event": "redetected", "by": origem,
                                "note": f"{len(novas)} evidência(s) nova(s)"})
        return alvo["id"], "existente"
    mesmos = [x for x in doc["itens"] if bucket(x) == bucket(candidato)]
    item = dict(candidato)
    item["id"] = proximo_id(doc, candidato["uid"])
    item["dedupe_key"] = chave
    item.setdefault("status", "open")
    item.setdefault("human_decision", None)
    item.setdefault("resolution", None)
    item.setdefault("first_detected_at", hoje)
    item.setdefault("last_reviewed_at", None)
    item["related_ids"] = sorted(set(item.get("related_ids", [])) | {x["id"] for x in mesmos})
    item["history"] = [{"at": hoje, "event": "detected", "by": origem}]
    doc["itens"].append(item)
    return item["id"], "novo"


def mudar_status(doc: dict, item_id: str, novo: str, hoje: str, por: str, nota: str = "",
                 decisao: dict | None = None, resolucao: dict | None = None) -> None:
    x = next(i for i in doc["itens"] if i["id"] == item_id)
    if novo not in STATUS:
        raise ValueError(novo)
    if x["status"] in FINAIS and novo in ("open", "deferred") and not decisao:
        raise ValueError(f"{item_id}: {x['status']} só volta a {novo} por decisão humana")
    if novo == "resolved" and not commit_valido(resolucao or x.get("resolution")):
        raise ValueError(f"{item_id}: resolved exige resolution.commit (SHA completo de 40 hex)")
    x["history"].append({"at": hoje, "event": f"status:{x['status']}→{novo}", "by": por, "note": nota})
    x["status"] = novo
    x["last_reviewed_at"] = hoje
    if decisao:
        x["human_decision"] = decisao
    if resolucao:
        x["resolution"] = resolucao


def resumo(doc: dict) -> dict:
    it = doc["itens"]
    return {"itens": len(it),
            "status": dict(collections.Counter(x["status"] for x in it)),
            "priority": dict(collections.Counter(x["priority"] for x in it)),
            "detection_method": dict(collections.Counter(x["detection_method"] for x in it)),
            "issue_type": dict(collections.Counter(x["issue_type"] for x in it).most_common()),
            "cards": len({x["uid"] for x in it})}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--validar", action="store_true")
    ap.add_argument("--resumo", action="store_true")
    a = ap.parse_args(argv)
    doc = carregar()
    erros = validar(doc)
    if a.resumo or not a.validar:
        print(json.dumps(resumo(doc), ensure_ascii=False, indent=1))
    for e in erros:
        print("ERRO", e, file=sys.stderr)
    return 1 if erros else 0


if __name__ == "__main__":
    sys.exit(main())
