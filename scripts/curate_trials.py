"""
Curate raw trial data into structured JS objects for trials_br.js.
Filters out theranostic/radioligand trials, prioritizes Phase III,
and generates properly formatted JavaScript.
"""
import json
import re
import textwrap

RAW_PATH = r"C:\Users\marco\Desktop\TheraTrials Oncology\site\scripts\brazil_trials_raw.json"
OUTPUT_PATH = r"C:\Users\marco\Desktop\TheraTrials Oncology\site\scripts\curated_trials_output.js"

with open(RAW_PATH, "r", encoding="utf-8") as f:
    raw = json.load(f)

# Filter out theranostic / radioligand trials
THERANOSTIC_KEYWORDS = [
    "psma-617", "lu-177", "177lu", "225ac", "ac-225", "actinium",
    "radium-223", "radium 223", "ra-223", "radioligand", "lutetium",
    "dotatate", "mibg", "y-90", "yttrium", "pluvicto", "aaa817",
]

def is_theranostic(trial):
    text = (trial.get("title", "") + " " + trial.get("official_title", "") +
            " " + trial.get("summary", "") + " " + " ".join(trial.get("interventions", []))).lower()
    return any(kw in text for kw in THERANOSTIC_KEYWORDS)

# Filter
filtered = [t for t in raw if not is_theranostic(t)]
removed = [t for t in raw if is_theranostic(t)]
print(f"Removed {len(removed)} theranostic trials:")
for t in removed:
    print(f"  {t['nct']}: {t['title'][:80]}")

print(f"\nRemaining: {len(filtered)} non-theranostic trials")

# Also filter out rollover/extension/observational/pan-tumor studies
def is_low_priority(trial):
    title_lower = trial.get("title", "").lower()
    official_lower = trial.get("official_title", "").lower()
    combined = title_lower + " " + official_lower
    skip_keywords = ["rollover", "extension study", "long-term safety", "real-world", "observational", "pharmacogenetics", "ctdna assessment"]
    return any(kw in combined for kw in skip_keywords)

high_priority = [t for t in filtered if not is_low_priority(t)]
low_removed = [t for t in filtered if is_low_priority(t)]
print(f"\nRemoved {len(low_removed)} rollover/extension/observational:")
for t in low_removed:
    print(f"  {t['nct']}: {t['title'][:80]}")

print(f"\nFinal candidates: {len(high_priority)}")

# Sort by phase (III first, then II, then others) and by number of Brazil cities
def phase_rank(trial):
    phase = trial.get("phase", "").lower()
    if "3" in phase or "iii" in phase: return 0
    if "2" in phase or "ii" in phase: return 1
    if "1" in phase or "i" in phase: return 2
    return 3

high_priority.sort(key=lambda t: (phase_rank(t), -len(t.get("brazil_cities", []))))

# Group by neoplasia
from collections import defaultdict
by_neo = defaultdict(list)
for t in high_priority:
    by_neo[t["neoplasia_group"]].append(t)

print("\nTrials per neoplasia:")
for neo, trials in sorted(by_neo.items()):
    print(f"  {neo}: {len(trials)} trials")

# Select top trials per category (max 5-6 per category for balance)
MAX_PER_CAT = 6
selected = []
for neo in sorted(by_neo.keys()):
    trials = by_neo[neo]
    selected.extend(trials[:MAX_PER_CAT])

print(f"\nSelected for output: {len(selected)} trials")

# --- Generate JS ---
# Neoplasia label mapping
NEO_LABELS = {
    "prostata": "Próstata",
    "mama": "Mama",
    "rim": "Rim · ccRCC",
    "melanoma": "Melanoma",
    "mieloma": "Mieloma Múltiplo",
    "linfoma": "Linfoma",
    "urotelial": "Bexiga / Urotelial",
    "pancreas": "Pâncreas",
    "endometrio": "Endométrio",
    "cervix": "Cérvix",
    "hcc": "Hepatocarcinoma · CHC",
}

def classify_modalidade(trial):
    """Infer modalidade from intervention types and names."""
    mods = set()
    interv_text = " ".join(trial.get("interventions", [])).lower()
    types = [t.lower() for t in trial.get("intervention_types", [])]
    summary = trial.get("summary", "").lower()

    if "biological" in types:
        mods.add("imunoterapia")
    if any(kw in interv_text for kw in ["pembrolizumab", "nivolumab", "atezolizumab",
            "durvalumab", "ipilimumab", "cemiplimab", "dostarlimab", "rilvegos",
            "tremelimumab", "relatlimab", "autogene cevumeran"]):
        mods.add("imunoterapia")
    if any(kw in interv_text for kw in ["deruxtecan", "t-dxd", "sacituzumab",
            "trastuzumab deruxtecan", "dato-dxd", "enfortumab", "loncastuximab",
            "belantamab", "tisotumab", "polatuzumab", "ifinatamab", "patritumab",
            "sacituzumab tirumotecan", "sac-tmt"]):
        mods.add("ADC")
    if any(kw in interv_text for kw in ["teclistamab", "talquetamab", "elranatamab",
            "glofitamab", "epcoritamab", "mosunetuzumab", "petosemtamab",
            "petosentamab", "amivantamab", "pumitamig"]):
        mods.add("bispecífico")
    if any(kw in interv_text for kw in ["car-t", "ciltacabtagene", "idecabtagene",
            "lifileucel", "cilta-cel", "ide-cel"]):
        mods.add("CAR-T")
    if any(kw in interv_text for kw in ["enzalutamide", "abiraterone", "darolutamide",
            "olaparib", "talazoparib", "niraparib", "saruparib", "capivasertib",
            "alpelisib", "inavolisib", "ribociclib", "abemaciclib", "palbociclib",
            "tucatinib", "erdafitinib", "selpercatinib", "sotorasib", "lenvatinib",
            "cabozantinib", "belzutifan", "mevrometostat", "opevesostat", "vorasidenib",
            "fulvestrant", "elacestrant", "camizestrant", "vepugratinib",
            "luxdegalutamide", "zanzalintinib", "rly-2608"]):
        mods.add("terapia-alvo")
    if any(kw in interv_text for kw in ["vaccine", "vacina", "bnt113", "mrna"]):
        mods.add("vacina")
    if any(kw in interv_text for kw in ["nab-paclitaxel", "gemcitabine", "carboplatin",
            "folfiri", "folfox", "cisplatin", "paclitaxel", "docetaxel",
            "pomalidomide", "lenalidomide"]):
        mods.add("quimioterapia")
    if any(kw in interv_text for kw in ["bevacizumab"]):
        mods.add("anti-angiogênico")
    if len(mods) > 1:
        mods.add("combinação")
    if not mods:
        mods.add("terapia-alvo")
    return sorted(list(mods))

def infer_biomarcadores(trial):
    """Infer biomarkers from title, summary, eligibility."""
    bms = set()
    text = (trial.get("title", "") + " " + trial.get("official_title", "") +
            " " + trial.get("summary", "") + " " + trial.get("eligibility_snippet", "")).lower()

    mapping = {
        "brca": "BRCA", "pd-l1": "PD-L1", "her2": "HER2", "egfr": "EGFR",
        "kras g12c": "KRAS G12C", "kras": "KRAS", "msi-h": "MSI-H",
        "mmr": "dMMR", "pik3ca": "PIK3CA", "esr1": "ESR1",
        "cldn18": "CLDN18.2", "fgfr": "FGFR", "bcma": "BCMA",
        "gprc5d": "GPRC5D", "cd20": "CD20", "cd19": "CD19",
        "trop-2": "TROP-2", "trop2": "TROP-2", "psma": "PSMA",
        "ret ": "RET", "alk": "ALK", "vhl": "VHL",
        "hr+": "HR+", "hr-positive": "HR+",
        "hormone receptor-negative": "HR-",
        "triple-negative": "TNBC",
    }

    for keyword, label in mapping.items():
        if keyword in text:
            bms.add(label)

    return sorted(list(bms))

def infer_phase(trial):
    """Clean phase string."""
    phase = trial.get("phase", "")
    phase = phase.replace("Fase ", "")
    if "3" in phase: return "III"
    if "2" in phase and "1" in phase: return "Ib/II"
    if "2" in phase: return "II"
    if "1" in phase: return "I"
    return phase

def make_id(trial):
    """Generate a short ID from the trial title/NCT."""
    title = trial.get("title", "").lower()
    # Try to find a study name like MEVPRO-3, DESTINY, etc.
    match = re.search(r'\b([A-Z][A-Za-z]+-?\d*)\b', trial.get("official_title", ""))
    if match:
        return match.group(1).lower().replace(" ", "-")
    # Fallback to NCT
    return trial.get("nct", "unknown").lower()

def infer_line(trial):
    """Infer therapeutic line."""
    text = (trial.get("title", "") + " " + trial.get("official_title", "") +
            " " + trial.get("summary", "") + " " + trial.get("eligibility_snippet", "")).lower()
    if "first-line" in text or "first line" in text or "1l " in text or "previously untreated" in text or "treatment-naïve" in text or "treatment-naive" in text:
        return "1ª linha"
    if "second-line" in text or "second line" in text or "2l " in text:
        return "2ª linha"
    if "third-line" in text or "third line" in text or "3l " in text:
        return "3ª+ linha"
    if "relapsed" in text or "refractory" in text:
        return "Recidivado / refratário"
    if "adjuvant" in text or "neoadjuvant" in text or "perioperative" in text:
        return "Perioperatório"
    if "maintenance" in text:
        return "Manutenção"
    if "metastatic" in text or "advanced" in text:
        return "Avançado / metastático"
    return "Conforme protocolo"

def format_centers(trial):
    """Format Brazil centers."""
    facilities = trial.get("brazil_facilities", [])
    if not facilities:
        cities = trial.get("brazil_cities", [])
        states = trial.get("brazil_states", [])
        return [f"{c}" for c in cities]
    # Clean up facilities
    cleaned = []
    seen = set()
    for f in facilities:
        # Remove "Novartis Investigative Site" etc.
        f = re.sub(r'(Novartis|Pfizer|Merck|Lilly|Roche|AstraZeneca|Bristol|Gilead|Amgen|BeiGene|Johnson)\s*(Investigative\s*Site|Clinical\s*Site|Research\s*Site)\s*·?\s*', '', f)
        f = f.strip(" ·/")
        if f and f not in seen:
            seen.add(f)
            cleaned.append(f)
    return cleaned[:5]  # Max 5 centers

# Generate JS objects
js_lines = []

current_neo = ""
for trial in selected:
    neo = trial["neoplasia_group"]
    if neo != current_neo:
        current_neo = neo
        label = NEO_LABELS.get(neo, neo.upper())
        js_lines.append(f"\n  // ============== {label.upper()} ==============")

    trial_id = make_id(trial)
    phase = infer_phase(trial)
    mods = classify_modalidade(trial)
    bms = infer_biomarcadores(trial)
    line = infer_line(trial)
    centers = format_centers(trial)
    cities = list(set(trial.get("brazil_cities", [])))
    states = list(set(trial.get("brazil_states", [])))

    # Build name from official title
    name_match = re.search(r'\(([A-Z][A-Za-z0-9\-]+(?:\s*\d*)?)\)', trial.get("official_title", ""))
    nome = name_match.group(1) if name_match else trial.get("nct", "")

    # Clean title
    titulo = trial.get("title", "").strip()
    if len(titulo) > 200:
        titulo = titulo[:197] + "..."

    # Interventions as string
    intervs = trial.get("interventions", [])
    intervencao = " + ".join([i for i in intervs if i.lower() not in ["placebo", "standard of care", "investigator's choice"]])
    comparador_list = [i for i in intervs if i.lower() in ["placebo", "standard of care", "investigator's choice"]]
    comparador = comparador_list[0] if comparador_list else "Braço controle conforme protocolo"

    # Summary as racional
    racional = trial.get("summary", "")[:250].strip()
    if len(trial.get("summary", "")) > 250:
        racional += "..."

    obj = f"""  {{
    id: '{trial.get("nct", "").lower()}',
    nome: '{nome}',
    titulo: '{titulo.replace(chr(39), "\\'")}',
    nct: '{trial.get("nct", "")}',
    fase: '{phase}',
    status: 'Recrutando',
    neoplasia: '{neo}',
    neoplasia_label: '{NEO_LABELS.get(neo, neo)}',
    subtipo: '',
    linha_terapeutica: '{line}',
    cenario_clinico: '{line}',
    modalidade: {json.dumps(mods, ensure_ascii=False)},
    biomarcadores: {json.dumps(bms, ensure_ascii=False)},
    testes_fornecidos: 'Conforme protocolo do estudo',
    intervencao: '{intervencao.replace(chr(39), "\\'")}',
    comparador: '{comparador.replace(chr(39), "\\'")}',
    racional: '{racional.replace(chr(39), "\\'")}',
    criterios_principais: [],
    criterios_exclusao: [],
    centros: {json.dumps(centers, ensure_ascii=False)},
    estados: {json.dumps(states, ensure_ascii=False)},
    cidades: {json.dumps(cities, ensure_ascii=False)},
    patrocinador: '{trial.get("sponsor", "").replace(chr(39), "\\'")}',
    fonte_url: '{trial.get("url", "")}',
    contato_url: '{trial.get("url", "")}',
    data_atualizacao: '2026-05-19',
  }},"""

    js_lines.append(obj)

output = "\n".join(js_lines)

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    f.write(output)

print(f"\nGenerated {len(selected)} trial objects")
print(f"Output: {OUTPUT_PATH}")

# Summary
print("\nFinal selection by neoplasia:")
neo_count = defaultdict(int)
for t in selected:
    neo_count[t["neoplasia_group"]] += 1
for neo, count in sorted(neo_count.items()):
    print(f"  {NEO_LABELS.get(neo, neo)}: {count}")
