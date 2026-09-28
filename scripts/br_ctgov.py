#!/usr/bin/env python3
"""
br_ctgov.py — acesso ao ClinicalTrials.gov e regra de "recrutando no Brasil".

Módulo comum do pipeline do Trial Matcher. Não usa IA e não grava nada: só lê
a API v2 oficial e classifica. Quem decide o que fazer com o resultado são o
br_auditar.py, o br_ciclo.py e o br_qa.py.

A regra central mora aqui, num lugar só, porque errá-la custa caro. Até
2026-09 o validador e a descoberta testavam `"RECRUITING" in status`, e essa
substring também está em ACTIVE_NOT_RECRUITING e NOT_YET_RECRUITING. Com isso,
26 estudos globalmente encerrados e 13 que já não recrutavam no Brasil
continuavam publicados como "Recrutando", e nenhum validador avisava.

Recrutar globalmente NÃO basta. O estudo só conta como aberto no Brasil se
pelo menos um centro brasileiro estiver com status de centro RECRUITING.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://clinicaltrials.gov/api/v2/studies"
UA = {"User-Agent": "TheraTrials/1.0 (+https://theratrials.com)"}
SITE = Path(__file__).resolve().parent.parent
TRIALS_JS = SITE / "assets" / "js" / "trials_br.js"

# Só o necessário para auditar: status, datas e locais. O registro inteiro tem
# ~70 KB por estudo; isto fica perto de 10 KB.
CAMPOS_AUDITORIA = "|".join([
    "protocolSection.identificationModule.nctId",
    "protocolSection.identificationModule.acronym",
    "protocolSection.statusModule",
    "protocolSection.contactsLocationsModule.locations",
])

# ── Conjuntos explícitos de status do CT.gov ─────────────────────────────────
# Toda comparação de status passa por estes conjuntos ou por igualdade exata.
# Nunca `"RECRUITING" in status`: a substring está em ACTIVE_NOT_RECRUITING e
# em NOT_YET_RECRUITING.

# Status global em que o estudo não aceita mais inclusão em lugar nenhum.
ENCERRADO_GLOBAL = frozenset({"ACTIVE_NOT_RECRUITING", "COMPLETED", "TERMINATED", "WITHDRAWN"})
# Status global em que ainda faz sentido olhar os centros brasileiros.
ABERTO_GLOBAL = frozenset({"RECRUITING", "NOT_YET_RECRUITING"})
# Status de centro que significa "este centro não inclui mais".
CENTRO_FECHADO = ENCERRADO_GLOBAL

# ── brazil_status: taxonomia determinística ──────────────────────────────────
# Separa o que acontece no Brasil do status global. Um estudo que segue
# RECRUITING no mundo e fechou os centros brasileiros é CLOSED_IN_BRAZIL, não
# STUDY_CLOSED: para o médico brasileiro o efeito é o mesmo, mas é outro fato,
# e o registro pode reabrir centros aqui.
BR_RECRUITING = "RECRUITING"                 # ≥1 centro BR com status RECRUITING
BR_NOT_YET_RECRUITING = "NOT_YET_RECRUITING" # nenhum BR recrutando, ≥1 BR ainda não aberto
CLOSED_IN_BRAZIL = "CLOSED_IN_BRAZIL"        # aberto no mundo, todos os centros BR fechados
STUDY_CLOSED = "STUDY_CLOSED"                # encerrado no mundo (status global)
REVIEW_REQUIRED = "REVIEW_REQUIRED"          # o registro não permite afirmar; ver `motivo`

BRAZIL_STATUS = (BR_RECRUITING, BR_NOT_YET_RECRUITING, CLOSED_IN_BRAZIL,
                 STUDY_CLOSED, REVIEW_REQUIRED)

# Rótulo público de cada valor (a interface usa o `label` da META).
ROTULO_PUBLICO = {
    BR_RECRUITING: "Recrutando no Brasil",
    BR_NOT_YET_RECRUITING: "Ainda não recrutando no Brasil",
    CLOSED_IN_BRAZIL: "Recrutamento encerrado no Brasil",
    STUDY_CLOSED: "Encerrado",
}

# brazil_status -> valor de `status` na THERA_TRIALS_BR_META.
# CLOSED_IN_BRAZIL tem valor próprio (aprovado em 2026-09-27): virar
# "Encerrado" apagaria a diferença entre fechado no Brasil e fechado no mundo.
# REVIEW_REQUIRED nunca gera proposta.
STATUS_CARD = {
    BR_RECRUITING: "Recrutando",
    BR_NOT_YET_RECRUITING: "Ainda não recrutando",
    CLOSED_IN_BRAZIL: "Recrutamento encerrado no Brasil",
    STUDY_CLOSED: "Encerrado",
}


def http_json(url: str, tentativas: int = 4) -> dict:
    """GET com backoff. A API do CT.gov devolve 429 sob rajada."""
    for n in range(tentativas):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA),
                                        timeout=60) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:  # noqa: BLE001 — repetir em qualquer falha de rede
            # 4xx (menos 429) não melhora com nova tentativa: 404 é resposta.
            if isinstance(e, urllib.error.HTTPError) and 400 <= e.code < 500 and e.code != 429:
                raise
            if n == tentativas - 1:
                raise
            espera = 2 ** n
            print(f"[ctgov] {e} — nova tentativa em {espera}s", file=sys.stderr)
            time.sleep(espera)
    raise RuntimeError("inalcançável")


class RespostaParcial(RuntimeError):
    """A API respondeu 200, mas sem parte do que foi pedido. Falha técnica:
    seguir adiante transformaria estudos em REVIEW_REQUIRED por engano."""


def _lote(parte: list[str], lote: int) -> dict[str, dict]:
    q = urllib.parse.urlencode({
        "filter.ids": "|".join(parte),
        "fields": CAMPOS_AUDITORIA,
        "pageSize": str(lote * 2),
    })
    out = {}
    for s in http_json(f"{API}?{q}").get("studies", []):
        p = s.get("protocolSection", {})
        nct = p.get("identificationModule", {}).get("nctId", "")
        if nct in parte:
            out[nct] = p
    return out


def _um(nct: str) -> dict | None:
    """Consulta individual. None só se a API disser 404 — ausência confirmada."""
    try:
        d = http_json(f"{API}/{nct}?{urllib.parse.urlencode({'fields': CAMPOS_AUDITORIA})}")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise
    if not d.get("protocolSection"):
        raise RespostaParcial(f"{nct}: consulta individual respondeu 200 sem o registro")
    return d["protocolSection"]


def buscar_por_ids(ncts: list[str], lote: int = 50) -> dict[str, dict]:
    """protocolSection de cada NCT.

    No lote, a API omite em silêncio o NCT que não acha — e omite igual quando
    responde pela metade. Então: lote incompleto é repetido uma vez; se ainda
    faltar mais de um NCT, é resposta parcial e o ciclo aborta. Um único
    ausente é consultado sozinho: 404 confirma que saiu do registro (fica fora
    do dicionário e o auditor manda para revisão); qualquer outra coisa aborta.
    """
    out: dict[str, dict] = {}
    for i in range(0, len(ncts), lote):
        parte = ncts[i:i + lote]
        achados = _lote(parte, lote)
        faltam = [n for n in parte if n not in achados]
        if faltam:
            print(f"[ctgov] lote {i // lote + 1}: {len(faltam)} de {len(parte)} não voltaram "
                  f"— nova tentativa", file=sys.stderr)
            time.sleep(3)
            achados.update(_lote(faltam, lote))
            faltam = [n for n in parte if n not in achados]
        if len(faltam) > 1:
            raise RespostaParcial(
                f"lote {i // lote + 1}: {len(faltam)} de {len(parte)} NCTs não voltaram da API "
                f"mesmo após nova tentativa ({', '.join(faltam[:5])}{'…' if len(faltam) > 5 else ''})")
        for nct in faltam:
            p = _um(nct)
            if p is None:
                print(f"[ctgov] {nct}: 404 na consulta individual — ausente do registro",
                      file=sys.stderr)
            elif p.get("identificationModule", {}).get("nctId") == nct:
                achados[nct] = p
            else:
                raise RespostaParcial(f"{nct}: consulta individual devolveu registro inesperado")
        out.update(achados)
        print(f"[ctgov] {min(i + lote, len(ncts))}/{len(ncts)}", file=sys.stderr)
        time.sleep(0.4)
    return out


def status_do_centro(local: dict, global_: str) -> str:
    """Status efetivo de um centro.

    Registro de estudo encerrado costuma vir com o status dos centros em branco.
    Em branco + estudo encerrado = centro encerrado. Em branco + estudo aberto
    NÃO vira RECRUITING: devolve '' e o chamador trata como indeterminado —
    confirmar recrutamento exige o status explícito.
    """
    st = (local.get("status") or "").upper()
    if st:
        return st
    return global_ if global_ in ENCERRADO_GLOBAL else ""


def centro_recrutando(local: dict, global_: str) -> bool:
    """Igualdade exata. Nunca `"RECRUITING" in status` — ver o cabeçalho."""
    return status_do_centro(local, global_) == "RECRUITING"


def recrutamento_brasil(p: dict) -> dict:
    """Classifica o recrutamento no Brasil (`brazil_status`) a partir do registro.

    Regras em ordem; a primeira que casar decide:
      1. status global encerrado                      -> STUDY_CLOSED
      2. status global fora de RECRUITING/NOT_YET     -> REVIEW_REQUIRED
      3. nenhum centro no Brasil                      -> REVIEW_REQUIRED
      4. ≥1 centro BR RECRUITING (e global RECRUITING)-> RECRUITING
      5. algum centro BR sem status                   -> REVIEW_REQUIRED
      6. ≥1 centro BR NOT_YET_RECRUITING              -> NOT_YET_RECRUITING
      7. todos os centros BR em CENTRO_FECHADO        -> CLOSED_IN_BRAZIL
      8. qualquer outra combinação                    -> REVIEW_REQUIRED
    """
    status = p.get("statusModule", {})
    global_ = status.get("overallStatus", "")
    locs = p.get("contactsLocationsModule", {}).get("locations", []) or []
    br = [l for l in locs if l.get("country") == "Brazil"]
    efetivos = [status_do_centro(l, global_) for l in br]
    motivo = ""

    if global_ in ENCERRADO_GLOBAL:
        bs = STUDY_CLOSED
    elif global_ not in ABERTO_GLOBAL:
        bs, motivo = REVIEW_REQUIRED, f"status global {global_ or '(vazio)'}"
    elif not br:
        bs, motivo = REVIEW_REQUIRED, "o registro não lista nenhum centro no Brasil"
    elif "RECRUITING" in efetivos:   # pertinência em lista: igualdade por item
        if global_ == "RECRUITING":
            bs = BR_RECRUITING
        else:
            bs, motivo = REVIEW_REQUIRED, "centro BR RECRUITING com estudo NOT_YET_RECRUITING"
    elif "" in efetivos:
        bs, motivo = REVIEW_REQUIRED, "centro BR sem status explícito"
    elif "NOT_YET_RECRUITING" in efetivos:
        bs = BR_NOT_YET_RECRUITING
    elif set(efetivos) <= CENTRO_FECHADO:
        bs = CLOSED_IN_BRAZIL
    else:
        bs, motivo = REVIEW_REQUIRED, "centros BR com status " + "/".join(sorted(set(efetivos)))

    contagem: dict[str, int] = {}
    for e in efetivos:
        contagem[e or "(vazio)"] = contagem.get(e or "(vazio)", 0) + 1

    return {
        "brazil_status": bs,
        "motivo": motivo,
        "overall_status": global_,
        "centros_br_total": len(br),
        "centros_br_recrutando": sum(1 for e in efetivos if e == "RECRUITING"),
        "status_centros_br": dict(sorted(contagem.items())),
        "last_update_posted": status.get("lastUpdatePostDateStruct", {}).get("date", ""),
        "last_verified": status.get("statusVerifiedDate", ""),
        "primary_completion": status.get("primaryCompletionDateStruct", {}).get("date", ""),
    }


def locais_recrutando(p: dict) -> list[dict]:
    """Centros brasileiros RECRUITING, no mesmo formato que o card usa.

    Reaproveita a normalização de cidade e a resolução de instituição do
    br_discover/br_instituicoes, para que a comparação com `centros` do card
    seja entre strings produzidas pela mesma regra.
    """
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from br_discover import CIDADE_UF, normalizar_cidade  # noqa: PLC0415
    from br_instituicoes import resolver  # noqa: PLC0415

    global_ = p.get("statusModule", {}).get("overallStatus", "")
    nomeados: set[tuple[str, str]] = set()
    anonimas: set[str] = set()
    for l in p.get("contactsLocationsModule", {}).get("locations", []) or []:
        if l.get("country") != "Brazil" or not centro_recrutando(l, global_):
            continue
        cidade = normalizar_cidade(l.get("city") or "")
        if not cidade:
            continue
        nome, _ = resolver(l.get("facility") or "", cidade)
        if nome:
            nomeados.add((nome, cidade))
        else:
            anonimas.add(cidade)
    locais = [{"instituicao": n, "cidade": c, "uf": CIDADE_UF.get(c, "")}
              for n, c in nomeados]
    for c in sorted(anonimas - {c for _, c in nomeados}):
        locais.append({"instituicao": "", "cidade": c, "uf": CIDADE_UF.get(c, "")})
    locais.sort(key=lambda x: (x["uf"], x["cidade"], x["instituicao"]))
    return locais


def rotulo_centro(l: dict) -> str:
    """'Instituição — Cidade / UF', como o br_merge e o br_centros escrevem."""
    onde = f"{l['cidade']} / {l['uf']}" if l.get("uf") else l["cidade"]
    return f"{l['instituicao']} — {onde}" if l.get("instituicao") else onde


def carregar_trials(caminho: Path = TRIALS_JS) -> tuple[list[dict], dict]:
    """Executa o trials_br.js no node e devolve (THERA_TRIALS_BR, META).

    Parse de verdade, não regex: é o mesmo caminho que o navegador e o
    export_app_data percorrem, então o que passa aqui é o que o site vê.
    """
    js = (f"global.window={{}};require({json.dumps(str(Path(caminho).resolve()))});"
          "process.stdout.write(JSON.stringify({t:window.THERA_TRIALS_BR,"
          "m:window.THERA_TRIALS_BR_META}));")
    r = subprocess.run(["node", "-e", js], capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        raise SystemExit(f"não consegui carregar {caminho}: {r.stderr.strip()[:400]}")
    d = json.loads(r.stdout)
    if not isinstance(d.get("t"), list):
        raise SystemExit(f"{caminho}: THERA_TRIALS_BR não é array")
    return d["t"], d.get("m") or {}
