"""
Merge curated new trials into trials_br.js and update META.
"""

TRIALS_PATH = r"C:\Users\marco\Desktop\TheraTrials Oncology\site\assets\js\trials_br.js"
NEW_TRIALS_PATH = r"C:\Users\marco\Desktop\TheraTrials Oncology\site\scripts\curated_trials_v2.js"

with open(TRIALS_PATH, "r", encoding="utf-8") as f:
    original = f.read()

with open(NEW_TRIALS_PATH, "r", encoding="utf-8") as f:
    new_trials = f.read()

# Find the closing of the trials array: "\n];\n"
marker = "\n];\n"
idx = original.find(marker)
if idx == -1:
    raise ValueError("Could not find end of THERA_TRIALS_BR array")

# Insert new trials before the closing bracket
updated = original[:idx] + "\n" + new_trials + "\n" + original[idx:]

# Update META with new neoplasia types
NEW_META_NEOS = """  neoplasias: [
    { id: 'pulmao',         label: 'Pulmão',                  color: '#22d3ee' },
    { id: 'cabeca_pescoco', label: 'Cabeça e pescoço',        color: '#a855f7' },
    { id: 'colorretal',     label: 'Colorretal',              color: '#fb923c' },
    { id: 'gastrico',       label: 'Gástrico / GEJ',          color: '#f87171' },
    { id: 'vias_biliares',  label: 'Vias biliares',           color: '#facc15' },
    { id: 'sarcoma',        label: 'Sarcoma ósseo',           color: '#94a3b8' },
    { id: 'ovario',         label: 'Ovário',                  color: '#c084fc' },
    { id: 'mama',           label: 'Mama',                    color: '#ec4899' },
    { id: 'penis',          label: 'Pênis',                   color: '#fbbf24' },
    { id: 'prostata',       label: 'Próstata',                color: '#FF8400' },
    { id: 'melanoma',       label: 'Melanoma',                color: '#f97316' },
    { id: 'mieloma',        label: 'Mieloma Múltiplo',        color: '#e879f9' },
    { id: 'linfoma',        label: 'Linfoma',                 color: '#818cf8' },
    { id: 'urotelial',      label: 'Bexiga / Urotelial',      color: '#2dd4bf' },
    { id: 'pancreas',       label: 'Pâncreas',                color: '#a3e635' },
    { id: 'endometrio',     label: 'Endométrio',              color: '#fb7185' },
    { id: 'cervix',         label: 'Cérvix',                  color: '#f472b6' },
    { id: 'hcc',            label: 'Hepatocarcinoma · CHC',   color: '#fbbf24' },
    { id: 'rim',            label: 'Rim · ccRCC',             color: '#34d399' },
  ],"""

# Replace old neoplasias block
import re
old_neo_pattern = r'  neoplasias: \[.*?\],'
updated = re.sub(old_neo_pattern, NEW_META_NEOS, updated, flags=re.DOTALL)

# Update modalidades to include bispecífico and CAR-T
NEW_MODALIDADES = """  modalidades: [
    { id: 'terapia-alvo',     label: 'Terapia-alvo' },
    { id: 'imunoterapia',     label: 'Imunoterapia' },
    { id: 'ADC',              label: 'ADC' },
    { id: 'bispecífico',      label: 'Bispecífico' },
    { id: 'CAR-T',            label: 'CAR-T' },
    { id: 'quimioterapia',    label: 'Quimioterapia' },
    { id: 'combinação',       label: 'Combinação' },
    { id: 'vacina',           label: 'Vacina' },
    { id: 'anti-angiogênico', label: 'Anti-angiogênico' },
    { id: 'cirurgia_rt',      label: 'Cirurgia / radioterapia' },
  ],"""

old_mod_pattern = r'  modalidades: \[.*?\],'
updated = re.sub(old_mod_pattern, NEW_MODALIDADES, updated, flags=re.DOTALL)

# Update linhas to include new ones
NEW_LINHAS = """  linhas: [
    { id: '1ª linha',                              label: '1ª linha' },
    { id: '2ª linha',                              label: '2ª linha' },
    { id: '3ª+ linha',                             label: '3ª+ linha' },
    { id: 'Recidivado / refratário',               label: 'Recidivado / refratário' },
    { id: 'Avançado / metastático',                label: 'Avançado / metastático' },
    { id: 'Perioperatório',                        label: 'Perioperatório' },
    { id: 'Perioperatório / consolidação',         label: 'Perioperatório / consolidação' },
    { id: 'Manutenção',                            label: 'Manutenção' },
    { id: '2ª linha pós-CDK4/6',                   label: '2ª linha (pós-CDK4/6)' },
    { id: 'Avançada (até 1 linha sistêmica prévia permitida)', label: 'Avançada (até 1 linha prévia)' },
    { id: 'Conforme protocolo',                    label: 'Conforme protocolo' },
  ],"""

old_linhas_pattern = r'  linhas: \[.*?\],'
updated = re.sub(old_linhas_pattern, NEW_LINHAS, updated, flags=re.DOTALL)

# Update biomarcadores
NEW_BIO = """  biomarcadores: [
    'KRAS G12C', 'HER2', 'EGFR', 'ALK', 'BRCA',
    'PD-L1', 'CPS', 'MSI-H', 'SSTR', 'PSMA',
    'CLDN18.2', 'IDH1', 'PIK3CA', 'HPV16',
    'TROP-2', 'ESR1', 'LGR5', 'BCMA', 'GPRC5D',
    'CD20', 'FGFR', 'VHL', 'TNBC', 'RET', 'dMMR',
  ],"""

old_bio_pattern = r'  biomarcadores: \[.*?\],'
updated = re.sub(old_bio_pattern, NEW_BIO, updated, flags=re.DOTALL)

# Update header comment
updated = updated.replace(
    "Última atualização da curadoria: 2026-05",
    "Última atualização da curadoria: 2026-05-19"
)

with open(TRIALS_PATH, "w", encoding="utf-8") as f:
    f.write(updated)

# Count total trials
count = updated.count("nct: '")
print(f"Done! Total trials in file: {count}")
print(f"Original: 14 + New: 45 = Expected: 59")
