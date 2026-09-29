"""export_legacy — gera o data.js legado a partir dos registros v2 e prova equivalência.

    python3 scripts/db_v2/export_legacy.py                 # compara com assets/js/data.js (não escreve nada)
    python3 scripts/db_v2/export_legacy.py --out ARQ       # grava a saída em ARQ (nunca no data.js real)

Estratégia C (migração progressiva por card):
- card NÃO migrado (shadow/modeled): o legado é legacy.v1, literal;
- card MIGRADO (curation.level = curated): cada campo listado em curation.legacy_projection é GERADO a partir
  do caminho v2 indicado; os demais campos v1 continuam vindo de legacy.v1.
A comparação com o data.js atual é o bloqueio de divergência: se um card migrado for editado à mão no
data.js (ou o registro mudar sem regenerar o legado), a saída difere e o código de saída é 1.

Saída: 0 = idêntico byte a byte; 1 = divergência; 2 = erro de uso.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import re
import json
import pathlib
import sys

import bibliografia as B
import v2lib as L

AVISO_WITHHELD = "Em revisão editorial — conteúdo temporariamente retirado até verificação das fontes primárias."


def _texto(v) -> str:
    if isinstance(v, str):
        return v
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return num(v)
    if isinstance(v, dict) and "op" in v:
        return qual(v)
    if isinstance(v, list):
        return "; ".join(_texto(x) for x in v)
    if isinstance(v, dict):
        for k in ("text", "id", "label", "value"):
            if k in v:
                return _texto(v[k])
    return json.dumps(v, ensure_ascii=False)


def render(env: dict | None, campo_v1: str):
    """Envelope v2 → valor legado. '—' é só renderização (o frontend atual o oculta)."""
    st = L.estado(env)
    if st == "present":
        v = env["v"]
        if env.get("conflict") in ("within_source_conflict", "cross_source_conflict") and env.get("value_candidates"):
            return " vs ".join(f"{_texto(c['value'])} ({c['locator'].get('section', '?')})"
                               for c in env["value_candidates"])
        if campo_v1 == "nct":   # o campo legado é de NCT: outros registros (EudraCT, ISRCTN) não entram
            regs = v if isinstance(v, list) else [v]
            ncts = [r["id"] for r in regs if isinstance(r, dict) and r.get("registry") == "NCT"]
            outros = [r["id"] for r in regs if isinstance(r, dict) and r.get("registry") == "ISRCTN"]
            return ", ".join(ncts or outros) or "—"
        if campo_v1 == "nct_url":
            regs = [r for r in (v if isinstance(v, list) else [v]) if isinstance(r, dict) and r.get("registry") == "NCT"]
            return f"https://clinicaltrials.gov/study/{regs[0]['id']}" if regs else ""
        if campo_v1 == "pubmed_url":
            return f"https://pubmed.ncbi.nlm.nih.gov/{v['pmid']}/" if isinstance(v, dict) and v.get("pmid") else ""
        if campo_v1 == "ano_pub":
            return v.get("year", 0) if isinstance(v, dict) else 0
        return _texto(v)
    if st == "not_reported":
        return "Não relatado."
    if st == "not_yet_available":
        return "Aguardando dados." + (f" Previsão: {env['expected']}." if env.get("expected") else "")
    if st == "withheld_due_to_integrity":
        return AVISO_WITHHELD
    return "—"  # not_applicable / unknown


# ── projetores: estrutura v2 → texto do campo legado ────────────────────────
def num(x) -> str:
    """Número em formato brasileiro, sem zeros supérfluos."""
    if isinstance(x, int) or (isinstance(x, float) and x.is_integer()):
        return str(int(x))
    return f"{x:.3f}".rstrip("0").rstrip(".").replace(".", ",")


def qual(q: dict | None, unid: str = "") -> str:
    if q is None or q == {}:
        return "—"
    if isinstance(q, (int, float)) and not isinstance(q, bool):
        q = {"op": "=", "value": q}
    op = q.get("op")
    u = {"months": " m", "month": " m", "percent": "%", "%": "%", "weeks": " sem", "years": " anos"}.get(
        q.get("unit"), (" " + q["unit"]) if q.get("unit") else unid)
    if op == "not_reached":
        return "não atingida"
    if op == "not_evaluable":
        return "não avaliável"
    if op == "direction_only":
        return {"favors_exp": "favorece o braço experimental", "favors_ctl": "favorece o controle",
                "no_difference": "diferença não significativa"}.get(q.get("direction"), "direção relatada")
    if op == "range":
        return f"{num(q['low'])}–{num(q['high'])}{u}"
    pref = {"=": "", "≈": "~", "<": "<", "≤": "≤", ">": ">", "≥": "≥"}.get(op, "")
    return re.sub(r"\s{2,}", " ", f"{pref}{num(q['value'])}{u}")


UNID = {"median": " m", "rate": "%", "proportion": "%", "accuracy": "%"}
ROTULO = {"median": "mediana", "rate": "taxa", "proportion": "", "accuracy": "", "mean": "média", "hr_only": ""}


def _braco(rec, aid):
    return next((a.get("label") or aid for a in L.arms(rec) if a["arm_id"] == aid), aid)


def _p(p: str) -> str:
    """'<.0001' → '<0,0001'; '0.004' → '=0,004'."""
    op = p[0] if p[:1] in "<>=≤≥" else "="
    v = p[1:] if p[:1] in "<>=≤≥" else p
    v = v.strip()
    if v.startswith("."):
        v = "0" + v
    return f"{op}{v.replace('.', ',')}"


def _da_publicacao_representada(rec: dict, eps: list) -> list:
    """Só endpoints das análises da publicação representada (evita misturar atualização com primária)."""
    rp = L.valor(L.envelope(rec, "identity.represented_publication")) or {}
    pmid = rp.get("pmid") if isinstance(rp, dict) else None
    if not pmid:
        return eps
    prov, an = rec.get("provenance", {}), {a["analysis_id"]: a for a in rec.get("analyses", [])}
    def pm(e):
        a = an.get((e.get("maturity") or {}).get("analysis_ref"))
        pid = (a or {}).get("prov") or e.get("prov")
        return ((prov.get(pid) or {}).get("source") or {}).get("pmid")
    sel = [e for e in eps if pm(e) == pmid]
    return sel or eps


def render_endpoint(rec: dict, e: dict) -> str:
    if e.get("state") == "withheld_due_to_integrity":
        return AVISO_WITHHELD
    if e.get("state") == "not_yet_available":
        return f"{e['code']}: aguardando dados" + (f" (previsão: {e['expected']})" if e.get("expected") else "")
    if e.get("state") != "present":
        return f"{e['code']}: —"
    summ = (e.get("measure") or {}).get("summary", "")
    tp = e.get("timepoint") or {}
    tempo = f" em {num(tp['months'])} meses" if tp.get("type") == "landmark" and "months" in tp else ""
    nome = e["code"] if e["code"] != "other" else (e.get("definition") or "desfecho")
    cab = " ".join(x for x in (nome, ROTULO.get(summ, ""), tempo.strip()) if x)
    extras = [x for x in (e.get("assessment"), (e.get("population") or {}).get("label")) if x and x != "ITT"]
    if extras:
        cab += f" ({', '.join(extras)})"
    u = UNID.get(summ, "")
    partes = []
    if e.get("conflict") in ("within_source_conflict", "cross_source_conflict") and e.get("value_candidates"):
        rotulo = "divergência na publicação" if e["conflict"] == "within_source_conflict" else "divergência entre fontes"
        partes.append(f"{rotulo}: " + " vs ".join(
            f"{_texto(c['value'])} ({c['locator'].get('section', '?')})" for c in e["value_candidates"]))
    if e.get("arms_values"):
        partes.append(" vs ".join(f"{qual(av['value'], u)} ({_braco(rec, av['arm_id']) if 'arm_id' in av else av['arm_group']['level']})"
                                  for av in e["arms_values"]))
    if e.get("estimate"):
        t = qual(e["estimate"]["value"], u)
        ci = e["estimate"].get("ci")
        if ci:
            alto = "NA" if ci.get("high") is None else num(ci["high"])
            t += f" (IC {num(ci['level'])}% {num(ci['low'])}–{alto})"
        partes.append(t)
    ef = e.get("effect") or {}
    if not ef.get("value") and ef.get("p"):   # efeito sem número mas com p: não perder o p
        partes.append(f"p{_p(ef['p'])}")
    if ef.get("value") and ef.get("measure") not in (None, "none"):
        medida = {"rate_difference": "diferença", "risk_difference": "diferença"}.get(ef["measure"], ef["measure"])
        t = f"{medida} {qual(ef['value'])}" if ef["value"].get("op") != "direction_only" else qual(ef["value"])
        if ef.get("ci"):
            alto = "NA" if ef["ci"].get("high") is None else num(ef["ci"]["high"])
            t += f" (IC {num(ef['ci']['level'])}% {num(ef['ci']['low'])}–{alto})"
        if ef.get("p"):
            t += f"; p{_p(ef['p'])}"
        partes.append(t)
    return f"{cab}: " + "; ".join(partes) if partes else cab


def _envs_texto(env) -> str | None:
    st = L.estado(env)
    if st == "present":
        return _texto(env["v"])
    return None if st in ("unknown", "not_applicable") else render(env, "")


def proj_primario(rec):
    eps = _da_publicacao_representada(rec, [e for e in L.endpoints(rec) if e["hierarchy"]["level"] == "primary"])
    eps.sort(key=lambda e: (e.get("measure") or {}).get("analysis_role", "protocol_primary_analysis") != "protocol_primary_analysis")
    return " · ".join(render_endpoint(rec, e) for e in eps) or None


def proj_secundario(rec):
    eps = _da_publicacao_representada(rec, [e for e in L.endpoints(rec)
                                            if e["hierarchy"]["level"] in ("key_secondary", "secondary")])
    return " · ".join(render_endpoint(rec, e) for e in eps[:5]) or None


def proj_tox(rec):
    partes = []
    g3 = L.valor(L.envelope(rec, "safety.grade3plus_any"))
    if g3:
        rel = all(x.get("attribution") == "treatment_related" for x in g3 if "arm_id" in x)
        partes.append(("EA grau ≥3 relacionados: " if rel else "EA grau ≥3: ") + " vs ".join(f"{qual(x.get('value'), '%')} ({_braco(rec, x['arm_id'])})"
                                                  for x in g3 if "arm_id" in x and x.get("value")))
    obitos = L.valor(L.envelope(rec, "safety.treatment_related_deaths"))
    if obitos:
        todos_qualquer = all(x.get("attribution") == "any" for x in obitos)
        partes.append(("óbitos em tratamento (qualquer causa): " if todos_qualquer else "óbitos relacionados: ") + " vs ".join(
            f"{x.get('n', qual(x.get('value')))} ({_braco(rec, x['arm_id'])})" for x in obitos if "arm_id" in x))
    rotulos = {"g3plus": "G≥3", "g3": "G3", "g3_4": "G3-4", "g4plus": "G≥4", "g5": "G5", "any": "qualquer grau",
               "g1": "G1", "g2": "G2", "g1_2": "G1-2", "g2plus": "G≥2", "serious": "graves"}
    termos_aesi = {x["term"] for x in L.valor(L.envelope(rec, "safety.key_toxicities")) or [] if x.get("aesi_of")}
    aesi = collections.OrderedDict()
    for x in L.valor(L.envelope(rec, "safety.key_toxicities")) or []:
        if x["term"] not in termos_aesi or "value" not in x or "arm_id" not in x:
            continue   # AESI: todos os braços do mesmo termo (o controle também), para comparação
        chave = (x["term"], x.get("scope", "any"), x.get("subtype"))
        aesi.setdefault(chave, []).append(f"{qual(x['value'], '%')} ({_braco(rec, x['arm_id'])})")
    outros = collections.OrderedDict()   # toxicidades-chave que não são AESI de módulo (depois dos AESI)
    for x in L.valor(L.envelope(rec, "safety.key_toxicities")) or []:
        if x["term"] in termos_aesi or "value" not in x or "arm_id" not in x:
            continue
        outros.setdefault((x["term"], x.get("scope", "any"), x.get("subtype")), []).append(
            f"{qual(x['value'], '%')} ({_braco(rec, x['arm_id'])})")
    aesi.update(outros)
    for (termo, esc, sub), vals in list(aesi.items())[:10]:
        nome = TERMO_PT.get(termo, termo.replace("_", " "))
        if sub:
            nome += f" ({sub})"
        partes.append(f"{nome} {rotulos.get(esc, esc)}: " + " vs ".join(vals))
    return "; ".join(p for p in partes if p) or None


TERMO_PT = {"crs": "SRC", "icans": "ICANS", "ild_pneumonitis": "DPI/pneumonite", "hematologic": "toxicidade hematológica",
            "renal": "toxicidade renal", "xerostomia_salivary": "xerostomia", "mds_aml": "SMD/LMA", "anemia": "anemia",
            "stomatitis": "estomatite", "ocular_surface": "toxicidade ocular de superfície", "lvef_decline": "queda da FEVE",
            "peripheral_neuropathy": "neuropatia periférica", "neutropenia": "neutropenia", "infections": "infecções",
            "cytopenias": "citopenias", "prolonged_cytopenias": "citopenias prolongadas",
            "immune_related_g3plus": "EA imunomediados", "pneumonitis": "pneumonite", "esophagitis": "esofagite",
            "gi_gu_late": "toxicidade GI/GU tardia", "liver_reild": "REILD", "sos_vod": "SOS/VOD", "vte": "TEV",
            "dry_eye": "olho seco", "hypertension": "hipertensão", "hand_foot_syndrome": "síndrome mão-pé",
            "hyperglycemia": "hiperglicemia", "fatigue": "fadiga", "diarrhea": "diarreia", "thrombocytopenia": "trombocitopenia",
            "lymphopenia": "linfopenia", "nausea": "náusea", "rash": "rash", "hypogammaglobulinemia": "hipogamaglobulinemia", "delayed_neurotoxicity": "neurotoxicidade tardia"}


def proj_subgrupo(rec):
    itens = []
    codigo = {e["endpoint_id"]: e["code"] for e in L.endpoints(rec)}
    for sg in L.valor(rec.get("subgroups")) or []:
        nome = f"{sg['dimension']}" + (f" {sg['level']}" if sg.get("level") else "")
        refs = [codigo[r] for r in ([sg["endpoint_ref"]] if sg.get("endpoint_ref") else []) + (sg.get("endpoint_refs") or [])
                if r in codigo]
        if refs:
            nome += f" ({', '.join(dict.fromkeys(refs))})"
        if sg.get("finding"):
            itens.append(f"{nome}: {sg['finding']}")
        elif sg.get("effect") and sg["effect"].get("value"):
            ef = sg["effect"]
            t = f"{nome}: {ef.get('measure', 'efeito')} {qual(ef['value'])}"
            if ef.get("ci") and ef["ci"].get("high") is not None:
                t += f" (IC {num(ef['ci']['level'])}% {num(ef['ci']['low'])}–{num(ef['ci']['high'])})"
            itens.append(t)
    return " · ".join(itens[:6]) or None


def proj_n(rec):
    ss = L.valor(L.envelope(rec, "design.sample_size")) or {}
    tot = ss.get("randomized") or ss.get("enrolled")
    braços = [a for a in L.arms(rec) if isinstance(a.get("n"), dict)]
    det = " vs ".join(f"{qual(a['n'])} {a.get('label', a['arm_id'])}" for a in braços) if len(braços) > 1 else ""
    rot = "randomizados" if ss.get("randomized") else "incluídos"
    txt = f"{tot} {rot}" + (f" ({det})" if det else "") if tot else None
    anal = ss.get("analyzed")
    if txt and anal and anal != tot:
        txt += f"; {anal} analisados"
    if txt and ss.get("planned") and ss["planned"] != tot:
        txt += f"; planejados {ss['planned']}"
    return txt


def _intervencao(i: dict) -> str:
    d = i.get("dose") or {}
    dose = ""
    if isinstance(d, dict) and d.get("value") is not None:
        v = d["value"]
        dose = f" {num(v) if isinstance(v, (int, float)) else v}" + (f" {d['unit']}" if d.get("unit") else "") \
            + (f" {d['frequency']}" if d.get("frequency") else "")
    extra = ", ".join(x for x in (i.get("route"), i.get("schedule")) if x)
    return f"{i['agent']}{dose}" + (f" ({extra})" if extra else "")


def proj_comparador(rec):
    ctl = [a for a in L.arms(rec) if a["role"] == "control"]
    out = []
    for a in ctl:
        ints = [i for i in a.get("interventions", []) if i.get("role") in ("control", "backbone", "investigational")]
        det = "; ".join(_intervencao(i) for i in ints if i.get("dose") or i.get("schedule") or len(ints) > 1)
        out.append((a.get("label") or a["arm_id"]) + (f" — {det}" if det else ""))
    return " | ".join(out) or None


FASE = {"randomized": "randomizado", "nonrandomized": "não randomizado", "single_arm": "braço único",
        "open": "aberto", "double_blind": "duplo-cego", "single_blind": "cego simples"}


def proj_fase(rec):
    ph = L.valor(L.envelope(rec, "identity.phase"))
    partes = [f"Fase {ph}" if ph and ph not in ("not_applicable",) else None,
              FASE.get(L.valor(L.envelope(rec, "design.allocation"))), FASE.get(L.valor(L.envelope(rec, "design.masking")))]
    return ", ".join(p for p in partes if p) or None


STATUS = {"published_primary": "Publicado", "published_final": "Publicado", "published_long_term": "Publicado",
          "published_interim": "Publicado (análise interina)", "presented": "Apresentado", "ongoing": "Em andamento",
          "registered": "Registrado"}


def proj_status(rec):
    if rec["review"]["editorial_status"] == "withheld":
        return "Em revisão editorial"
    return STATUS.get(L.valor(L.envelope(rec, "identity.evidence_stage")))


def proj_citation(rec):
    """`citation` do v1 = projeção da publicação representada; nunca em evidence_collection; sem ela, None
    (mantém o legado — e o legado sem `citation` faz o frontend cair no `ref` literal, sem autor inferido)."""
    if rec.get("record_type") == "evidence_collection":
        return None
    rp = L.valor(L.envelope(rec, "identity.represented_publication"))
    pubs = L.valor(L.envelope(rec, "identity.publications")) or []
    alvo = next((p for p in pubs if isinstance(p, dict) and isinstance(rp, dict)
                 and p.get("publication_id") == rp.get("publication_id")), None)
    return B.citation_v1(alvo) if alvo else None


def _campo(caminho):
    return lambda rec: _envs_texto(L.envelope(rec, caminho))


PROJETORES = {
    "primario": proj_primario, "secundario": proj_secundario, "tox_g3": proj_tox, "n": proj_n,
    "comparador": proj_comparador, "fase": proj_fase, "status": proj_status, "subgrupo": proj_subgrupo,
    "indicacao": _campo("population.disease"), "resultado_chave": _campo("interpretation.key_result"),
    "takehome": _campo("interpretation.takehome"), "limit": _campo("interpretation.limitations"),
    "impacto_reg": _campo("interpretation.clinical_impact"), "estudo": _campo("identity.short_name"),
    "acron": _campo("identity.display_title"), "citation": proj_citation,
}


def _pegar(rec: dict, caminho: str):
    """Caminho v2 → envelope. Aceita 'modules.<nome>.<campo>'."""
    if caminho.startswith("modules."):
        _, nome, campo = caminho.split(".", 2)
        for m in rec.get("modules", []):
            if m["module"] == nome:
                return (m.get("fields") or {}).get(campo)
        return None
    return L.envelope(rec, caminho)


def projetar(rec: dict) -> dict:
    """Card legado a partir do registro. Preserva a ordem de chaves do v1."""
    card = dict(rec["legacy"]["v1"])
    if rec["curation"]["level"] != "curated":
        return card
    for campo_v1, caminho in (rec["curation"].get("legacy_projection") or {}).items():
        if campo_v1 == "uid":
            raise ValueError("uid nunca é projetado: é imutável")
        if caminho == "auto":
            if campo_v1 not in PROJETORES:
                raise ValueError(f"sem projetor automático para {campo_v1}")
            valor = PROJETORES[campo_v1](rec)
            if valor is not None:           # projeção sem conteúdo curado mantém o legado (nunca apaga)
                card[campo_v1] = valor
        else:
            card[campo_v1] = render(_pegar(rec, caminho), campo_v1)
    return card


def carregar_sombra(pasta: pathlib.Path) -> tuple[dict, list[dict]]:
    meta = json.loads((pasta / "_dataset.json").read_text(encoding="utf-8"))
    recs = {}
    for f in pasta.glob("*.json"):
        if f.name.startswith("_"):
            continue
        r = json.loads(f.read_text(encoding="utf-8"))
        recs[r["uid"]] = r
    faltam = [u for u in meta["study_order"] if u not in recs]
    if faltam:
        raise SystemExit(f"registros ausentes na sombra: {faltam[:5]}")
    novos = sorted((r for u, r in recs.items() if u not in set(meta["study_order"])),
                   key=lambda r: r["legacy"]["position"])
    return meta, [recs[u] for u in meta["study_order"]] + novos


def exportar(pasta: pathlib.Path) -> str:
    meta, recs = carregar_sombra(pasta)
    obj = {}
    for k in meta["top_keys"]:
        obj[k] = [projetar(r) for r in recs] if k == "studies" else meta["other"][k]
    return L.serializar_data_js(meta["prefix"], obj, meta["suffix"])


def comparar(gerado: str, atual: str) -> dict:
    _, a, _ = L.ler_data_js(atual)
    _, g, _ = L.ler_data_js(gerado)
    ua, ug = [s["uid"] for s in a["studies"]], [s["uid"] for s in g["studies"]]
    difs = []
    for sa, sg in zip(a["studies"], g["studies"]):
        if sa != sg:
            difs.append({"uid": sa["uid"], "campos": sorted(k for k in set(sa) | set(sg) if sa.get(k) != sg.get(k)),
                         "ordem_de_chaves_igual": list(sa) == list(sg)})
    return {
        "bytes_identicos": gerado == atual,
        "sha256_atual": hashlib.sha256(atual.encode()).hexdigest(),
        "sha256_gerado": hashlib.sha256(gerado.encode()).hexdigest(),
        "estrutura_canonica_igual": L.canonico(a) == L.canonico(g),
        "cards": [len(ua), len(ug)], "uids_iguais": set(ua) == set(ug), "ordem_igual": ua == ug,
        "top_level_igual": {k: a.get(k) == g.get(k) for k in a if k != "studies"},
        "cards_divergentes": difs,
    }


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--shadow", default=str(L.SHADOW))
    ap.add_argument("--atual", default=str(L.DATA_JS))
    ap.add_argument("--out")
    ap.add_argument("--check", action="store_true", help="só compara (padrão); nunca escreve")
    a = ap.parse_args(argv)
    # recusas ANTES de qualquer trabalho: não dependem de sombra existir
    if a.out and a.check:
        print("--check não escreve arquivo", file=sys.stderr)
        return 2
    if a.out and pathlib.Path(a.out).resolve() == L.DATA_JS.resolve():
        print("recusado: export_legacy não grava no data.js publicado nesta fase", file=sys.stderr)
        return 2
    gerado = exportar(pathlib.Path(a.shadow))
    if a.out:
        pathlib.Path(a.out).resolve().write_text(gerado, encoding="utf-8")
    rel = comparar(gerado, pathlib.Path(a.atual).read_text(encoding="utf-8"))
    print(json.dumps({k: v for k, v in rel.items() if k != "cards_divergentes"}, ensure_ascii=False, indent=1))
    if rel["cards_divergentes"]:
        print(json.dumps(rel["cards_divergentes"][:20], ensure_ascii=False, indent=1))
    return 0 if rel["bytes_identicos"] else 1


if __name__ == "__main__":
    sys.exit(main())
