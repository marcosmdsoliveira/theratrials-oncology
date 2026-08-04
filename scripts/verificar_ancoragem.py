#!/usr/bin/env python3
"""
Verificação de ancoragem: cada critério escrito precisa estar amarrado ao texto
oficial do registro. Não confia na saída do modelo — extrai âncoras verificáveis
(números, siglas de gene, escalas, nomes de fármaco) e confere se aparecem na
elegibilidade do CT.gov.

Uma âncora que não aparece é candidata a invenção e vai para revisão manual.
"""
import json, re, sys, unicodedata
from pathlib import Path

import argparse
_ap = argparse.ArgumentParser(description=__doc__)
_ap.add_argument("--dir", required=True, help="pasta com recurar_*.json e curadoria_*.json")
P = Path(_ap.parse_args().dir)
fonte = {a["nct"]: a for a in json.loads((P / "recurar_76.json").read_text(encoding="utf-8"))}
cur = json.loads((P / "curadoria_76.json").read_text(encoding="utf-8"))

def dea(s):
    s = unicodedata.normalize("NFD", s.lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")

def norm_num(s):
    """1.500 e 1,500 são o mesmo número; 0,5 e 0.5 também."""
    return s.replace(".", "").replace(",", "").lstrip("0") or "0"

# O registro escreve número por extenso onde a curadoria usa algarismo:
# "AJCC eighth edition" -> "AJCC 8ª edição", "first-line" -> "1ª linha".
# Sem isso o verificador acusa invenção onde só houve tradução.
POR_EXTENSO = {
 "1": ["first", "one"], "2": ["second", "two"], "3": ["third", "three"],
 "4": ["fourth", "four"], "5": ["fifth", "five"], "6": ["sixth", "six"],
 "7": ["seventh", "seven"], "8": ["eighth", "eight"], "9": ["ninth", "nine"],
 "10": ["tenth", "ten"], "12": ["twelve"], "18": ["eighteen"],
}

# Siglas/escala que precisam existir no texto de origem se eu as citei.
SIGLAS = re.compile(
    r"\b(EGFR|ALK|ROS1|BRAF|RET|MET|NTRK|HER2|HER3|KRAS|PIK3CA|AKT1|PTEN|ESR1|BRCA1?|BRCA2|"
    r"PALB2|BCMA|GPRC5D|CD38|CD20|CD3|CD137|GPC3|MTAP|FGFR3?|TROP-?2|DLL3|PD-L1|PD-1|PD-L2|"
    r"CTLA-4|LAG-3|TIGIT|CPS|TPS|MSI-H|dMMR|pMMR|HRD|VHL|CDK4/6|CYP3A4/5|CYP3A4|SIRP|"
    r"ECOG|RECIST|NYHA|Lansky|Karnofsky|Child-Pugh|BCLC|AJCC|FIGO|IMWG|ASCO|CAP|CTCAE|"
    r"QTcF|QTc|FEVE|LVEF|DLCO|HbA1c|POEMS|ICANS|HBsAg|HBV|HCV|HIV|BCG|CIS|NMIBC|NSCLC|"
    r"IHQ|ISH|FFPE|ADC|PARP|SERD|LHRH|GnRH|177Lu|PSMA|MUGA|ctDNA|ALT|AST|G12C|G12R|V600E?|"
    r"T790M|L858R|Mobitz|DPOC|COPD|TARV|ART)\b", re.I)

# Uma sigla conta como ancorada se o registro traz a sigla OU a forma por
# extenso. O CT.gov frequentemente escreve "Eastern Cooperative Oncology Group"
# sem nunca abreviar para ECOG — abreviar na curadoria é prática clínica
# normal, não invenção. Sem esse mapa a verificação acusava 29 falsos positivos.
EXPANSOES = {
 "ecog": ["eastern cooperative oncology group"],
 "karnofsky": ["kps", "karnofsky"],
 "lansky": ["lansky"],
 "msi-h": ["microsatellite instability", "msi"],
 "dmmr": ["mismatch repair deficiency", "mismatch repair deficient", "dmmr"],
 "pmmr": ["proficient mismatch repair", "pmmr"],
 "cldn18.2": ["claudin18.2", "claudin 18.2", "cldn18.2"],
 "kit": ["kit"],
 "pdgfra": ["platelet-derived growth factor receptor", "pdgfr"],
 "ajcc": ["american joint committee on cancer"],
 "who": ["world health organization", "who"],
 "recist": ["recist"],
 "nyha": ["new york heart association"],
 "asco": ["american society of clinical oncology"],
 "cap":  ["college of american pathologists"],
 "feve": ["lvef", "left ventricular ejection fraction", "fracao de ejecao"],
 "lvef": ["left ventricular ejection fraction"],
 "ihq":  ["ihc", "immunohistochemistry"],
 "ish":  ["in situ hybridization"],
 "adc":  ["antibody drug conjugate", "antibody-drug conjugate"],
 "pd-1": ["programmed cell death 1", "programmed cell death protein 1", "pd)-1", "pd-1/l1"],
 "pd-l1":["programmed cell death ligand 1", "programmed death ligand 1", "pd-1/l1", "pd-l1"],
 "pd-l2":["programmed cell death ligand 2", "programmed cell death-ligand 2"],
 "cps":  ["combined positive score"],
 "tps":  ["tumor proportion score"],
 "trop-2":["trophoblast cell surface antigen 2", "trophoblast antigen 2", "trop2"],
 "hbsag":["hepatitis b surface antigen"],
 "alk":  ["anaplastic lymphoma kinase"],
 "ros1": ["proto-oncogene tyrosine-protein kinase ros"],
 "ntrk": ["neurotrophic tyrosine receptor kinase"],
 "ret":  ["rearranged during transfection"],
 "met":  ["mesenchymal-epithelial transition"],
 "braf": ["v-raf murine sarcoma viral oncogene"],
 "egfr": ["epidermal growth factor receptor", "estimated glomerular filtration rate"],
 "her2": ["human epidermal growth factor receptor 2"],
 "her3": ["human epidermal growth factor receptor 3"],
 "bcma": ["b cell maturation antigen", "b-cell maturation antigen"],
 "gpc3": ["glypican-3"],
 "cd137":["4-1bb", "t-cell costimulatory receptor 4-1bb"],
 "ctla-4":["cytotoxic t-lymphocyte", "cytotoxic t lymphocyte"],
 "dpoc": ["copd", "chronic obstructive pulmonary disease"],
 "tarv": ["antiretroviral therapy", "art"],
 "parp": ["poly (adp-ribose) polymerase", "poly adp-ribose polymerase"],
 "imwg": ["international myeloma working group"],
 "ctcae":["common terminology criteria for adverse events"],
 "mtap": ["methylthioadenosine phosphorylase"],
 "fgfr": ["fibroblast growth factor receptor"],
 "fgfr3":["fibroblast growth factor receptor 3"],
 "vhl":  ["von hippel"],
 "dlco": ["dlco", "diffusing capacity"],
 "icans":["immune effector cell-associated neurotoxicity"],
 "poems":["polyneuropathy, organomegaly, endocrinopathy"],
 "177lu":["177lu", "lutetium"],
 "psma": ["psma", "prostate-specific membrane"],
 "ctdna":["ctdna", "circulating tumor dna"],
 "hrd":  ["hrd", "homologous recombination"],
 "bcg":  ["bcg", "bacillus calmette"],
 "cis":  ["cis", "carcinoma in situ"],
 "muga": ["multigated acquisition", "muga"],
 "lhrh": ["lhrh", "luteinizing hormone-releasing"],
 "gnrh": ["gnrh", "gonadotropin"],
}

falhas, ok_total, por_card = [], 0, {}
for nct, dados in cur.items():
    src = fonte.get(nct, {}).get("elegibilidade", "")
    src_d = dea(src)
    src_nums = set()
    for x in re.findall(r"\d[\d.,]*", src):
        src_nums.add(norm_num(x))
        # "sub-study 1,2,3" é um token só para a regex, mas contém três
        # números — sem separar, o "3" da curadoria não era encontrado.
        for parte in re.split(r"[.,]", x):
            if parte:
                src_nums.add(norm_num(parte))
    ruins = []
    n_anc = 0
    for chave in ("inc", "exc"):
        for crit in dados.get(chave, []):
            # âncoras numéricas
            for num in re.findall(r"\d[\d.,]*", crit):
                n_anc += 1
                n = norm_num(num)
                if n in src_nums:
                    continue
                if any(w in src_d for w in POR_EXTENSO.get(n, [])):
                    continue
                ruins.append((chave, num, crit[:70]))
            # âncoras de sigla
            for sig in SIGLAS.findall(crit):
                n_anc += 1
                chave_s = dea(sig)
                s = chave_s.replace("-", "").replace("/", "")
                corpo = src_d.replace("-", "").replace("/", "")
                achou = s in corpo
                if not achou:
                    for exp in EXPANSOES.get(chave_s, []):
                        if dea(exp).replace("-", "").replace("/", "") in corpo:
                            achou = True; break
                if not achou:
                    ruins.append((chave, sig, crit[:70]))
    ok_total += n_anc - len(ruins)
    por_card[nct] = (n_anc, len(ruins))
    if ruins:
        falhas.append((nct, fonte.get(nct, {}).get("nome", "?"), ruins))

tot_anc = sum(v[0] for v in por_card.values())
print(f"âncoras verificadas ......... {tot_anc}")
print(f"  confirmadas no registro ... {ok_total}")
print(f"  NÃO encontradas ........... {tot_anc - ok_total}")
print(f"cards com alguma divergência: {len(falhas)} de {len(cur)}")
import sys as _s
if falhas:
    print("\n--- revisar ---")
    for nct, nome, ruins in falhas:
        print(f"\n{nome} ({nct}) — {len(ruins)}")
        for chave, anc, ctx in ruins[:8]:
            print(f"   [{chave}] '{anc}' não achado | {ctx}")

sys.exit(1 if falhas else 0)
