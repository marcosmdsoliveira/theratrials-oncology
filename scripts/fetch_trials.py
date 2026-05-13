#!/usr/bin/env python3
"""
TheraTrials Oncology — Pipeline RLT
===========================================================
Consulta a API v2 do ClinicalTrials.gov, agrega todos os estudos
de radiofármacos terapêuticos em oncologia, normaliza os campos,
classifica por isótopo / ligante / alvo / classe e gera o arquivo
estático que alimenta a página `pipeline.html`.

Saída:  site/assets/data/tracker.json
Stats:  imprime sumário no stdout.

Sem dependências externas — só stdlib (urllib + json).

Uso local:
    python scripts/fetch_trials.py

Uso CI (GitHub Action):
    Mesmo comando, commit do diff de tracker.json se houver mudança.
"""

from __future__ import annotations

import json
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# -----------------------------------------------------------------------------
# Configuração
# -----------------------------------------------------------------------------
API_BASE = "https://clinicaltrials.gov/api/v2/studies"
PAGE_SIZE = 200  # 1..1000 conforme docs
USER_AGENT = "TheraTrials-Oncology/1.0 (https://marcosmdsoliveira.github.io/theratrials-oncology)"

# Diretório onde o JSON é salvo (relativo à raiz do `site/`).
THIS_FILE = Path(__file__).resolve()
SITE_DIR = THIS_FILE.parent.parent  # site/
OUTPUT = SITE_DIR / "assets" / "data" / "pipeline.json"
OUTPUT_JS = SITE_DIR / "assets" / "data" / "pipeline.js"

# -----------------------------------------------------------------------------
# Queries (cobertura do "Pipeline RLT")
# Cada entrada é um termo de intervenção. A API faz match fuzzy
# e tolera sinônimos, então uma única query como "Lu-177" já pega
# Pluvicto, Lutathera, PSMA-617, DOTATATE, NeoB, etc.
# -----------------------------------------------------------------------------
INTERVENTION_QUERIES = [
    # Isótopos terapêuticos beta-
    "Lu-177", "Lutetium 177", "Lutetium Lu 177",
    # Isótopos alfa
    "Ac-225", "Actinium 225", "Actinium-225",
    "Pb-212", "Lead-212",
    "Bi-213", "Bismuth-213",
    "At-211", "Astatine-211",
    "Th-227", "Thorium-227",
    "Ra-223", "Radium-223", "Xofigo",
    # Outros isótopos
    "Y-90", "Yttrium 90", "Yttrium-90",
    "I-131", "Iodine 131", "MIBG", "iobenguane",
    "Tb-161", "Terbium-161",
    "Cu-67", "Copper-67",
    "Ho-166", "Holmium-166",
    "Re-188", "Rhenium-188",
    "Sm-153", "Samarium-153",
    "Sr-89", "Strontium-89",
    # Plataformas/produtos
    "PSMA-617", "PSMA-I&T", "Pluvicto",
    "DOTATATE", "DOTATOC", "DOTANOC", "Lutathera",
    "FAPI", "FAP-2286",
    "RYZ101", "RYZ401",
    "JNJ-69086420", "BAY 3546828",
    "Pentixather", "Pentixafor",
    "TheraSphere", "SIR-Spheres", "microspheres yttrium",
    "NeoB", "RM2", "GRPR radioligand",
    "TLX591", "TLX592", "TLX250", "TLX101",
    "AlphaMedix", "ABX",
    "Azedra",
]

# -----------------------------------------------------------------------------
# Taxonomia derivada (regex sobre intervenções/título/sponsor)
# -----------------------------------------------------------------------------
ISOTOPE_RULES = [
    ("177Lu", r"\b(177\s*Lu|Lu[-\s]?177|lutetium[-\s]?177|lutetium\s*Lu\s*177)\b"),
    ("225Ac", r"\b(225\s*Ac|Ac[-\s]?225|actinium[-\s]?225|actinium\s*Ac\s*225)\b"),
    ("212Pb", r"\b(212\s*Pb|Pb[-\s]?212|lead[-\s]?212)\b"),
    ("213Bi", r"\b(213\s*Bi|Bi[-\s]?213|bismuth[-\s]?213)\b"),
    ("211At", r"\b(211\s*At|At[-\s]?211|astatine[-\s]?211)\b"),
    ("227Th", r"\b(227\s*Th|Th[-\s]?227|thorium[-\s]?227)\b"),
    ("223Ra", r"\b(223\s*Ra|Ra[-\s]?223|radium[-\s]?223|xofigo)\b"),
    ("90Y",   r"\b(90\s*Y|Y[-\s]?90|yttrium[-\s]?90)\b"),
    ("131I",  r"\b(131\s*I|I[-\s]?131|iodine[-\s]?131|iodide\s*I\s*131|MIBG|iobenguane|azedra)\b"),
    ("161Tb", r"\b(161\s*Tb|Tb[-\s]?161|terbium[-\s]?161)\b"),
    ("67Cu",  r"\b(67\s*Cu|Cu[-\s]?67|copper[-\s]?67)\b"),
    ("166Ho", r"\b(166\s*Ho|Ho[-\s]?166|holmium[-\s]?166|quiremspheres|quirem)\b"),
    ("188Re", r"\b(188\s*Re|Re[-\s]?188|rhenium[-\s]?188)\b"),
    ("153Sm", r"\b(153\s*Sm|Sm[-\s]?153|samarium[-\s]?153|quadramet)\b"),
    ("89Sr",  r"\b(89\s*Sr|Sr[-\s]?89|strontium[-\s]?89|metastron)\b"),
]

LIGAND_RULES = [
    ("PSMA-617",   r"PSMA[-\s]?617|pluvicto|vipivotide"),
    ("PSMA-I&T",   r"PSMA[-\s]?I[\s&]*T|PSMA[-\s]?I-T"),
    ("rh-PSMA",    r"rh[-\s]?PSMA"),
    ("PSMA-other", r"\bPSMA\b"),
    ("DOTATATE",   r"DOTA[-\s]?TATE|DOTATATE|lutathera|RYZ401"),
    ("DOTATOC",    r"DOTA[-\s]?TOC|DOTATOC"),
    ("DOTANOC",    r"DOTA[-\s]?NOC|DOTANOC"),
    ("FAPI",       r"FAPI|FAP-2286|FAP[-\s]?targeted"),
    ("GRPR/NeoB",  r"\bNeoB\b|RM2|RM-2|bombesin|GRPR"),
    ("CXCR4",      r"pentixather|pentixafor|CXCR4"),
    ("MIBG",       r"\bMIBG\b|iobenguane|azedra"),
    ("Microspheres", r"theraspheres?|SIR[-\s]?spheres?|quiremspheres?|microsphere"),
    ("anti-CD20",  r"zevalin|ibritumomab|bexxar|tositumomab"),
    ("HER2",       r"trastuzumab.*lu|her2.*radioligand"),
    ("CAIX",       r"girentuximab|TLX250"),
    ("GPC3",       r"glypican|GPC3"),
    ("IGF-1R",     r"TLX101|IGF[-\s]?1R"),
]

TARGET_FROM_LIGAND = {
    "PSMA-617": "PSMA", "PSMA-I&T": "PSMA", "rh-PSMA": "PSMA", "PSMA-other": "PSMA",
    "DOTATATE": "SSTR", "DOTATOC": "SSTR", "DOTANOC": "SSTR",
    "FAPI": "FAP", "GRPR/NeoB": "GRPR", "CXCR4": "CXCR4",
    "MIBG": "NET (norepinephrine)", "Microspheres": "Vascular (intra-arterial)",
    "anti-CD20": "CD20", "HER2": "HER2", "CAIX": "CAIX", "GPC3": "GPC3", "IGF-1R": "IGF-1R",
}

# Categoria clínica (neoplasia) — regex sobre conditions
NEOPLASIA_RULES = [
    ("Próstata",        r"prostat"),
    ("NET GEP",         r"neuroendocrine|gastroenteropancreatic|carcinoid|GEP[-\s]?NET"),
    ("NET pulmonar",    r"bronchial\s+neuroendocrine|lung\s+carcinoid|pulmonary\s+neuroendocrine"),
    ("PPGL",            r"pheochromocytoma|paraganglioma"),
    ("Neuroblastoma",   r"neuroblastoma"),
    ("Tireoide",        r"thyroid|differentiated\s+thyroid|medullary\s+thyroid|anaplastic\s+thyroid"),
    ("CHC",             r"hepatocellular|HCC|liver\s+cancer"),
    ("Metástase hepática", r"liver\s+metastas|hepatic\s+metastas|metastatic.*liver"),
    ("Mama",            r"breast"),
    ("Pulmão (NSCLC)",  r"non[-\s]?small.*cell.*lung|NSCLC"),
    ("Pulmão (SCLC)",   r"small\s+cell.*lung|SCLC"),
    ("Colorretal",      r"colorect|rectal|colon\s+cancer"),
    ("Pâncreas",        r"pancreatic\s+adeno|pancreatic\s+cancer|pancreatic\s+ductal"),
    ("Glioma/GBM",      r"glioma|glioblastoma|GBM|astrocytoma"),
    ("Cabeça e pescoço",r"head\s+and\s+neck|nasopharyn|oropharyn|laryngeal"),
    ("Ovário",          r"ovarian"),
    ("Linfoma",         r"lymphoma"),
    ("Mieloma",         r"myeloma"),
    ("Renal (ccRCC)",   r"renal\s+cell|RCC|clear[-\s]?cell\s+kidney"),
    ("Urotelial",       r"urotheli|bladder\s+cancer"),
    ("Melanoma",        r"melanoma"),
    ("Sarcoma",         r"sarcoma"),
    ("Ósseo (mets)",    r"bone\s+metastas|skeletal\s+metastas"),
    ("Sólidos avançados", r"advanced\s+solid|metastatic\s+solid|solid\s+tumou?rs?"),
]

CLASS_FROM_ISOTOPE = {
    "225Ac": "Alfa", "212Pb": "Alfa", "213Bi": "Alfa", "211At": "Alfa",
    "227Th": "Alfa", "223Ra": "Alfa",
    "177Lu": "Beta-", "90Y": "Beta-", "131I": "Beta-", "67Cu": "Beta-",
    "161Tb": "Beta-/Auger", "188Re": "Beta-", "153Sm": "Beta-",
    "166Ho": "Beta- (microsfera)", "89Sr": "Beta-",
}

# -----------------------------------------------------------------------------
# Helpers HTTP
# -----------------------------------------------------------------------------
def http_get_json(url: str, max_retries: int = 4) -> dict:
    """GET com retry exponencial. Lança em caso de falha definitiva."""
    last_err = None
    for attempt in range(1, max_retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:  # noqa: BLE001
            last_err = e
            wait = 1.5 * attempt
            print(f"  [retry {attempt}] {url[:90]}…  → {e}; aguardando {wait:.1f}s", file=sys.stderr)
            time.sleep(wait)
    raise RuntimeError(f"falha após {max_retries} tentativas: {url} | {last_err}")


def fetch_query(intr_term: str) -> list[dict]:
    """Pagina todos os estudos para uma intervenção. Retorna lista de studies."""
    studies: list[dict] = []
    page_token: str | None = None
    pages = 0
    while True:
        params = {
            "query.intr": intr_term,
            "pageSize": PAGE_SIZE,
            "format": "json",
            "countTotal": "true",
        }
        if page_token:
            params["pageToken"] = page_token
        url = f"{API_BASE}?{urllib.parse.urlencode(params)}"
        data = http_get_json(url)
        batch = data.get("studies", [])
        studies.extend(batch)
        pages += 1
        page_token = data.get("nextPageToken")
        if not page_token or not batch:
            break
        if pages > 20:  # safety cap (4 000 por query é mais que suficiente)
            break
    return studies


# -----------------------------------------------------------------------------
# Normalização de um study
# -----------------------------------------------------------------------------
def first_match(rules, text: str):
    for label, pat in rules:
        if re.search(pat, text, re.IGNORECASE):
            return label
    return None


def all_matches(rules, text: str) -> list[str]:
    out = []
    for label, pat in rules:
        if re.search(pat, text, re.IGNORECASE):
            out.append(label)
    return out


def normalize(study: dict) -> dict | None:
    """Reduz o objeto CT.gov ao schema do tracker. Retorna None se não for terapêutico oncológico."""
    proto = study.get("protocolSection", {}) or {}
    ident = proto.get("identificationModule", {}) or {}
    status_mod = proto.get("statusModule", {}) or {}
    design = proto.get("designModule", {}) or {}
    cond_mod = proto.get("conditionsModule", {}) or {}
    interv_mod = proto.get("armsInterventionsModule", {}) or {}
    sponsor_mod = proto.get("sponsorCollaboratorsModule", {}) or {}
    contacts_mod = proto.get("contactsLocationsModule", {}) or {}

    nct = ident.get("nctId")
    if not nct:
        return None

    brief_title = ident.get("briefTitle", "") or ""
    official_title = ident.get("officialTitle", "") or ""
    status = (status_mod.get("overallStatus") or "").upper()
    phases = design.get("phases") or []
    phase = " / ".join(p.replace("PHASE", "Phase ") for p in phases) if phases else "N/A"

    conditions = cond_mod.get("conditions") or []
    keywords = cond_mod.get("keywords") or []

    interv_list = interv_mod.get("interventions") or []
    interventions = []
    for iv in interv_list:
        name = (iv.get("name") or "").strip()
        itype = iv.get("type") or ""
        if name:
            interventions.append({"name": name, "type": itype})

    interv_names_str = " | ".join(iv["name"] for iv in interventions)
    cond_str = " | ".join(conditions + keywords)
    haystack = " ".join([brief_title, official_title, interv_names_str, cond_str])

    # Filtro de relevância: precisa ter algum isótopo OU produto teranóstico no texto
    isotope = first_match(ISOTOPE_RULES, haystack)
    ligand = first_match(LIGAND_RULES, haystack)
    if not isotope and not ligand:
        return None

    # Excluir trials puramente diagnósticos sem braço terapêutico óbvio.
    # Mantém quando aparecem isótopos tipicamente terapêuticos OU produtos teranósticos terapêuticos.
    therapeutic_isotopes = {"225Ac", "212Pb", "213Bi", "211At", "227Th", "223Ra",
                            "177Lu", "90Y", "131I", "67Cu", "161Tb", "188Re",
                            "153Sm", "166Ho", "89Sr"}
    if isotope and isotope not in therapeutic_isotopes:
        # ligand sem isótopo — pode ser diagnóstico; deixamos passar só se for teranóstico claro
        if not ligand or ligand in {"FAPI", "GRPR/NeoB", "CXCR4"} and not isotope:
            pass

    sponsor = (sponsor_mod.get("leadSponsor") or {}).get("name", "")
    sponsor_class = (sponsor_mod.get("leadSponsor") or {}).get("class", "")  # INDUSTRY/NIH/OTHER/...

    enrollment_info = design.get("enrollmentInfo") or {}
    enrollment = enrollment_info.get("count")

    locations = (contacts_mod.get("locations") or [])
    countries = sorted({(loc.get("country") or "").strip() for loc in locations if loc.get("country")})
    has_brazil = "Brazil" in countries

    start_date = (status_mod.get("startDateStruct") or {}).get("date", "")
    primary_completion = (status_mod.get("primaryCompletionDateStruct") or {}).get("date", "")
    last_update = (status_mod.get("lastUpdatePostDateStruct") or {}).get("date", "")

    # Categoria clínica (pega a primeira correspondência, mas guarda todas)
    neoplasia_list = all_matches(NEOPLASIA_RULES, cond_str + " | " + brief_title + " | " + official_title)
    neoplasia = neoplasia_list[0] if neoplasia_list else "Outro"

    drug_class = CLASS_FROM_ISOTOPE.get(isotope or "", "Outro")
    target = TARGET_FROM_LIGAND.get(ligand or "", "")

    # "Drug" — a melhor representação curta
    drug_display = pick_drug_display(brief_title, interventions, isotope, ligand)

    return {
        "nct": nct,
        "title": brief_title,
        "phase": phase,
        "status": status,
        "isotope": isotope or "",
        "ligand": ligand or "",
        "target": target,
        "drug_class": drug_class,
        "drug": drug_display,
        "sponsor": sponsor,
        "sponsor_class": sponsor_class,
        "conditions": conditions[:8],
        "neoplasia": neoplasia,
        "neoplasia_all": neoplasia_list,
        "interventions": [iv["name"] for iv in interventions][:6],
        "enrollment": enrollment,
        "countries": countries,
        "has_brazil": has_brazil,
        "start_date": start_date,
        "primary_completion": primary_completion,
        "last_update": last_update,
        "url": f"https://clinicaltrials.gov/study/{nct}",
    }


def pick_drug_display(title: str, interventions: list[dict], isotope: str | None, ligand: str | None) -> str:
    """Tenta isolar o radiofármaco principal a partir das intervenções; cai pra título se necessário."""
    drug_iv = [iv["name"] for iv in interventions if iv.get("type") == "DRUG" or iv.get("type") == "RADIATION"]
    candidates = drug_iv or [iv["name"] for iv in interventions]
    if isotope:
        for c in candidates:
            if re.search(re.escape(isotope.replace("-", "")), c.replace("-", ""), re.IGNORECASE):
                return c[:80]
        for c in candidates:
            if re.search(isotope[:3], c, re.IGNORECASE):
                return c[:80]
    if ligand:
        for c in candidates:
            if re.search(re.escape(ligand.split("/")[0].split("-")[0]), c, re.IGNORECASE):
                return c[:80]
    if candidates:
        return candidates[0][:80]
    return title[:80]


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
def main() -> int:
    print(f"[fetch_trials] iniciando · output → {OUTPUT}")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    raw_by_nct: dict[str, dict] = {}
    per_query_stats: dict[str, int] = {}

    for term in INTERVENTION_QUERIES:
        try:
            batch = fetch_query(term)
        except Exception as e:  # noqa: BLE001
            print(f"  ! query falhou: {term!r} — {e}", file=sys.stderr)
            continue
        new = 0
        for st in batch:
            nct = (((st.get("protocolSection") or {}).get("identificationModule") or {}).get("nctId"))
            if nct and nct not in raw_by_nct:
                raw_by_nct[nct] = st
                new += 1
        per_query_stats[term] = len(batch)
        print(f"  ▸ {term:<32}  {len(batch):4d} totais · {new:4d} novos · {len(raw_by_nct):4d} acumulados")

    print(f"\n[fetch_trials] consolidado: {len(raw_by_nct)} estudos únicos. Normalizando…")

    trials: list[dict] = []
    dropped = 0
    for st in raw_by_nct.values():
        n = normalize(st)
        if n:
            trials.append(n)
        else:
            dropped += 1
    print(f"[fetch_trials] mantidos: {len(trials)} · descartados (sem isótopo/ligante): {dropped}")

    # Ordenação: status (recrutando primeiro), depois fase decrescente, depois data
    status_rank = {
        "RECRUITING": 0, "NOT_YET_RECRUITING": 1, "ENROLLING_BY_INVITATION": 2,
        "ACTIVE_NOT_RECRUITING": 3, "COMPLETED": 4, "TERMINATED": 5,
        "WITHDRAWN": 6, "SUSPENDED": 7, "UNKNOWN": 8,
    }

    def phase_rank(p: str) -> int:
        if "Phase 3" in p or "PHASE3" in p:
            return 0
        if "Phase 2" in p or "PHASE2" in p:
            return 1
        if "Phase 1" in p or "PHASE1" in p:
            return 2
        return 3

    trials.sort(key=lambda t: (
        status_rank.get(t["status"], 99),
        phase_rank(t["phase"]),
        -(int(t["enrollment"]) if t["enrollment"] else 0),
        t["nct"],
    ))

    # Facetas pré-calculadas (acelera UI)
    def freq(key):
        out: dict[str, int] = {}
        for t in trials:
            v = t.get(key)
            if isinstance(v, list):
                for x in v:
                    if x:
                        out[x] = out.get(x, 0) + 1
            elif v:
                out[v] = out.get(v, 0) + 1
        return dict(sorted(out.items(), key=lambda kv: -kv[1]))

    facets = {
        "isotope": freq("isotope"),
        "ligand": freq("ligand"),
        "target": freq("target"),
        "drug_class": freq("drug_class"),
        "phase": freq("phase"),
        "status": freq("status"),
        "sponsor_class": freq("sponsor_class"),
        "neoplasia": freq("neoplasia"),
        "neoplasia_all": freq("neoplasia_all"),
    }

    output = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": "ClinicalTrials.gov API v2",
        "queries": INTERVENTION_QUERIES,
        "totals": {
            "trials": len(trials),
            "queries": len(INTERVENTION_QUERIES),
            "with_brazil": sum(1 for t in trials if t["has_brazil"]),
        },
        "facets": facets,
        "trials": trials,
    }

    OUTPUT.write_text(json.dumps(output, ensure_ascii=False, indent=1), encoding="utf-8")
    size_kb = OUTPUT.stat().st_size / 1024
    print(f"\n[fetch_trials] ✓ gravado: {OUTPUT}  ({size_kb:.1f} KB)")

    # Espelha em tracker.js (fallback para file:// e cac