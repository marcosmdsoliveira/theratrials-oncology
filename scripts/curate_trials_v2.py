"""
Curate v2 — validates neoplasia by checking trial conditions/title,
fixes JS escaping, maps cities to states.
"""
import json
import re
from collections import defaultdict

RAW_PATH = r"C:\Users\marco\Desktop\TheraTrials Oncology\site\scripts\brazil_trials_raw.json"
OUTPUT_PATH = r"C:\Users\marco\Desktop\TheraTrials Oncology\site\scripts\curated_trials_v2.js"

with open(RAW_PATH, "r", encoding="utf-8") as f:
    raw = json.load(f)

# City -> State mapping for Brazil
CITY_STATE = {
    "São Paulo": "SP", "Barretos": "SP", "São José do Rio Preto": "SP",
    "São Jose Do Rio Preto": "SP", "Santo André": "SP", "Sorocaba": "SP",
    "Taubaté": "SP", "Jaú": "SP", "Jau": "SP", "Campinas": "SP",
    "Ribeirão Preto": "SP", "Presidente Prudente": "SP", "Liberdade": "SP",
    "Morumbi": "SP",
    "Belo Horizonte": "MG",
    "Rio de Janeiro": "RJ",
    "Porto Alegre": "RS", "Passo Fundo": "RS", "Pelotas": "RS",
    "Ijuí": "RS", "Lages": "RS",
    "Curitiba": "PR", "Blumenau": "SC", "Joinville": "SC",
    "Itajaí": "PR", "Itajal": "PR",
    "Brasília": "DF", "Brasília": "DF",
    "Salvador": "BA", "Bahia": "BA",
    "Recife": "PE",
    "Natal": "RN",
    "Fortaleza": "CE",
    "São Luís": "MA", "São Luís": "MA",
    "Belém": "PA", "Belém": "PA",
    "Vitória": "ES", "Vitória": "ES",
    "Goiânia": "GO",
    "Santa Cruz do Sul": "RS",
    "Rio Grande": "RS",
}

# Neoplasia validation keywords (must appear in title, official_title, or conditions)
NEO_VALIDATION = {
    "prostata": ["prostate", "prostatic", "próstata", "prostát"],
    "mama": ["breast", "mama"],
    "rim": ["renal", "kidney", "rim"],
    "melanoma": ["melanoma"],
    "mieloma": ["myeloma", "mieloma"],
    "linfoma": ["lymphoma", "linfoma"],
    "urotelial": ["urothelial", "bladder", "bexiga", "urotelial", "intravesical"],
    "pancreas": ["pancrea"],
    "endometrio": ["endometri"],
    "cervix": ["cervic", "cervix", "cérvix"],
    "hcc": ["hepatocellular", "hepatocarcinoma", "liver cancer", "hcc"],
}

# Reclassify cross-contaminated trials
def validate_neoplasia(trial):
    """Check if trial actually matches its assigned neoplasia group."""
    text = (trial.get("title", "") + " " + trial.get("official_title", "") + " " + trial.get("summary", "")).lower()
    assigned = trial["neoplasia_group"]
    keywords = NEO_VALIDATION.get(assigned, [])
    return any(kw in text for kw in keywords)

def find_correct_neoplasia(trial):
    """Try to find the correct neoplasia for a misclassified trial."""
    text = (trial.get("title", "") + " " + trial.get("official_title", "") + " " + trial.get("summary", "")).lower()
    for neo, keywords in NEO_VALIDATION.items():
        if any(kw in text for kw in keywords):
            return neo
    # Check for other common ones
    if any(kw in text for kw in ["head and neck", "squamous cell", "hnscc", "cabeça"]):
        return "cabeca_pescoco"
    if any(kw in text for kw in ["gastric", "gastroesophageal", "gástrico", "esophageal"]):
        return "gastrico"
    if any(kw in text for kw in ["colorectal", "colorretal", "colon"]):
        return "colorretal"
    if any(kw in text for kw in ["ovarian", "ovário"]):
        return "ovario"
    if any(kw in text for kw in ["sarcoma"]):
        return "sarcoma"
    if any(kw in text for kw in ["solid tumor", "advanced tumor", "pan tumor"]):
        return "pan_tumor"
    return None

# --- Filter pipeline ---
# 1. Remove theranostic
THERA_KW = ["psma-617", "lu-177", "177lu", "225ac", "ac-225", "actinium",
    "radium-223", "radium 223", "ra-223", "radioligand", "lutetium",
    "dotatate", "mibg", "y-90", "yttrium", "pluvicto", "aaa817"]

def is_theranostic(t):
    text = (t.get("title","") + " " + t.get("official_title","") +
            " " + t.get("summary","") + " " + " ".join(t.get("interventions",[]))).lower()
    return any(kw in text for kw in THERA_KW)

# 2. Remove low-priority
def is_low_priority(t):
    combined = (t.get("title","") + " " + t.get("official_title","")).lower()
    return any(kw in combined for kw in ["rollover", "extension study", "long-term safety",
        "real-world", "observational", "pharmacogenetics", "ctdna assessment", "pan tumor"])

filtered = [t for t in raw if not is_theranostic(t) and not is_low_priority(t)]
print(f"After filtering: {len(filtered)} trials")

# 3. Validate and reclassify neoplasia
reclassified = []
for t in filtered:
    if validate_neoplasia(t):
        reclassified.append(t)
    else:
        correct_neo = find_correct_neoplasia(t)
        if correct_neo and correct_neo != "pan_tumor":
            print(f"  Reclassified {t['nct']}: {t['neoplasia_group']} -> {correct_neo} ({t['title'][:60]})")
            t["neoplasia_group"] = correct_neo
            reclassified.append(t)
        else:
            print(f"  DROPPED {t['nct']}: no clear neoplasia ({t['title'][:60]})")

print(f"\nAfter validation: {len(reclassified)} trials")

# 4. Sort and select
def phase_rank(t):
    phase = t.get("phase", "").lower()
    if "3" in phase: return 0
    if "2" in phase: return 1
    return 2

reclassified.sort(key=lambda t: (phase_rank(t), -len(t.get("brazil_cities", []))))

by_neo = defaultdict(list)
for t in reclassified:
    by_neo[t["neoplasia_group"]].append(t)

MAX_PER_CAT = 5
selected = []
for neo in sorted(by_neo.keys()):
    trials = by_neo[neo]
    selected.extend(trials[:MAX_PER_CAT])

print(f"\nSelected: {len(selected)} trials")
for neo in sorted(by_neo.keys()):
    count = len(by_neo[neo][:MAX_PER_CAT])
    print(f"  {neo}: {count}")

# --- Generate JS ---
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
    "cabeca_pescoco": "Cabeça e pescoço · CEC",
    "gastrico": "Gástrico / GEJ",
    "colorretal": "Colorretal",
    "ovario": "Ovário",
}

def escape_js(s):
    """Escape string for JS single quotes, remove newlines."""
    s = s.replace("\\", "\\\\").replace("'", "\\'")
    s = s.replace("\n", " ").replace("\r", " ")
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def get_states(cities):
    states = set()
    for c in cities:
        st = CITY_STATE.get(c)
        if st:
            states.add(st)
    return sorted(list(states))

def get_centers(trial):
    cities = trial.get("brazil_cities", [])
    states_for_cities = {c: CITY_STATE.get(c, "") for c in cities}
    centers = []
    seen = set()
    for c in cities:
        st = states_for_cities.get(c, "")
        label = f"{c} / {st}" if st else c
        if label not in seen:
            seen.add(label)
            centers.append(label)
    return centers[:8]

def classify_modalidade(trial):
    mods = set()
    interv_text = " ".join(trial.get("interventions", [])).lower()

    if any(kw in interv_text for kw in ["pembrolizumab", "nivolumab", "atezolizumab",
            "durvalumab", "ipilimumab", "cemiplimab", "dostarlimab", "rilvegos",
            "tremelimumab", "relatlimab", "autogene cevumeran", "imc-f106c"]):
        mods.add("imunoterapia")
    if any(kw in interv_text for kw in ["deruxtecan", "t-dxd", "sacituzumab",
            "enfortumab", "loncastuximab", "belantamab", "tisotumab", "polatuzumab",
            "ifinatamab", "patritumab", "tirumotecan", "sac-tmt", "mk-2870"]):
        mods.add("ADC")
    if any(kw in interv_text for kw in ["teclistamab", "talquetamab", "elranatamab",
            "glofitamab", "epcoritamab", "mosunetuzumab", "petosemtamab",
            "petosentamab", "amivantamab", "pumitamig", "jnj-79635322"]):
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
            "luxdegalutamide", "zanzalintinib", "rly-2608", "gdc-4198",
            "bgb-16673", "bms-986365", "bms-986504", "pf-06821497"]):
        mods.add("terapia-alvo")
    if any(kw in interv_text for kw in ["vaccine", "vacina", "bnt113", "mrna", "voyager"]):
        mods.add("vacina")
    if any(kw in interv_text for kw in ["nab-paclitaxel", "gemcitabine", "carboplatin",
            "cisplatin", "paclitaxel", "docetaxel", "folfiri", "fluorouracil",
            "pomalidomide", "lenalidomide", "5-fluro"]):
        mods.add("quimioterapia")
    if any(kw in interv_text for kw in ["bevacizumab"]):
        mods.add("anti-angiogênico")
    if len(mods) > 1:
        mods.add("combinação")
    if not mods:
        mods.add("terapia-alvo")
    return sorted(list(mods))

def infer_biomarcadores(trial):
    bms = set()
    text = (trial.get("title","") + " " + trial.get("official_title","") +
            " " + trial.get("summary","") + " " + trial.get("eligibility_snippet","")).lower()
    mapping = {
        "brca": "BRCA", "pd-l1": "PD-L1", "her2": "HER2", "egfr": "EGFR",
        "kras g12c": "KRAS G12C", "msi-h": "MSI-H", "pik3ca": "PIK3CA",
        "esr1": "ESR1", "cldn18": "CLDN18.2", "fgfr": "FGFR", "bcma": "BCMA",
        "gprc5d": "GPRC5D", "cd20": "CD20", "trop-2": "TROP-2", "trop2": "TROP-2",
        "vhl": "VHL", "triple-negative": "TNBC", "ret ": "RET",
    }
    for kw, label in mapping.items():
        if kw in text:
            bms.add(label)
    return sorted(list(bms))

def infer_phase(trial):
    phase = trial.get("phase", "")
    if "3" in phase: return "III"
    if "2" in phase and "1" in phase: return "Ib/II"
    if "2" in phase: return "II"
    if "1" in phase: return "I"
    return phase

def infer_line(trial):
    text = (trial.get("title","") + " " + trial.get("official_title","") +
            " " + trial.get("summary","") + " " + trial.get("eligibility_snippet","")).lower()
    if "first-line" in text or "first line" in text or "1l " in text or "previously untreated" in text:
        return "1ª linha"
    if "second-line" in text or "second line" in text or "2l " in text:
        return "2ª linha"
    if "relapsed" in text or "refractory" in text or "relapsed/refractory" in text:
        return "Recidivado / refratário"
    if "adjuvant" in text or "neoadjuvant" in text or "perioperative" in text:
        return "Perioperatório"
    if "maintenance" in text:
        return "Manutenção"
    return "Avançado / metastático"

def extract_study_name(trial):
    """Try to find acronym or study name from official title."""
    official = trial.get("official_title", "")
    # Look for parenthesized names like (MEVPRO-3), (MagnetisMM-32)
    m = re.search(r'\(([A-Z][A-Za-z0-9\-\s]+\d*)\)', official)
    if m:
        name = m.group(1).strip()
        if len(name) < 30 and not name.startswith("MK-") and not name.startswith("NCT"):
            return name
    # Look for study codes in title
    m = re.search(r'\b([A-Z]{2,}[\-\s]?\d{1,4})\b', trial.get("title", ""))
    if m:
        name = m.group(1)
        if len(name) < 20:
            return name
    return trial.get("nct", "")

# Generate
js_blocks = []
current_neo = ""

for trial in selected:
    neo = trial["neoplasia_group"]
    if neo != current_neo:
        current_neo = neo
        label = NEO_LABELS.get(neo, neo.upper())
        js_blocks.append(f"\n  // ============== {label.upper()} ==============")

    nct = trial["nct"]
    nome = extract_study_name(trial)
    titulo = escape_js(trial.get("title", "")[:200])
    phase = infer_phase(trial)
    mods = classify_modalidade(trial)
    bms = infer_biomarcadores(trial)
    line = infer_line(trial)
    cities = list(set(trial.get("brazil_cities", [])))
    states = get_states(cities)
    centers = get_centers(trial)
    sponsor = escape_js(trial.get("sponsor", ""))

    intervs = trial.get("interventions", [])
    active_drugs = [i for i in intervs if i.lower() not in ["placebo", "standard of care", "investigator's choice", "rescue medications"]]
    intervencao = escape_js(" + ".join(active_drugs[:4]))
    comparador_list = [i for i in intervs if i.lower() in ["placebo", "standard of care", "investigator's choice"]]
    comparador = escape_js(comparador_list[0]) if comparador_list else "Braço controle conforme protocolo"

    summary = escape_js(trial.get("summary", "")[:250])
    neo_label = NEO_LABELS.get(neo, neo)

    obj = f"""  {{
    id: '{nct.lower()}',
    nome: '{escape_js(nome)}',
    titulo: '{titulo}',
    nct: '{nct}',
    fase: '{phase}',
    status: 'Recrutando',
    neoplasia: '{neo}',
    neoplasia_label: '{neo_label}',
    subtipo: '',
    linha_terapeutica: '{escape_js(line)}',
    cenario_clinico: '{escape_js(line)}',
    modalidade: {json.dumps(mods, ensure_ascii=False)},
    biomarcadores: {json.dumps(bms, ensure_ascii=False)},
    testes_fornecidos: 'Conforme protocolo do estudo',
    intervencao: '{intervencao}',
    comparador: '{comparador}',
    racional: '{summary}',
    criterios_principais: [],
    criterios_exclusao: [],
    centros: {json.dumps(centers, ensure_ascii=False)},
    estados: {json.dumps(states, ensure_ascii=False)},
    cidades: {json.dumps(cities, ensure_ascii=False)},
    patrocinador: '{sponsor}',
    fonte_url: 'https://clinicaltrials.gov/study/{nct}',
    contato_url: 'https://clinicaltrials.gov/study/{nct}',
    data_atualizacao: '2026-05-19',
  }},"""

    js_blocks.append(obj)

output = "\n".join(js_blocks)
with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    f.write(output)

print(f"\nWrote {len(selected)} trials to {OUTPUT_PATH}")
