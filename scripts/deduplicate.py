"""
TheraTrials Oncology — Deduplication Script
Merges 5 confirmed duplicate groups, preserving the richer entry
and enriching it with any unique info from the removed entry.

Groups:
1. PSMAfore: keep lupsma_prostata_2, remove teranostico_emergente_6
2. SPLASH: keep lupsma_prostata_3, remove teranostico_emergente_5
3. PACIFIC: keep rt_consolidacao_0, remove pacific-durvalumab-...
4. ADRIATIC: keep rt_consolidacao_4, remove adriatic-durva-...
5. PHEO/PGL: keep ppgl_0, remove ppgl_2
"""

import json
import re
import shutil
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parent.parent / "assets" / "js" / "data.js"

raw = DATA_FILE.read_text(encoding="utf-8")
lines = raw.split("\n")
header_lines = lines[:6]
data_line = lines[6]

json_str = re.sub(r"^window\.THERA_DATA\s*=\s*", "", data_line).rstrip(";").strip()
data = json.loads(json_str)

studies = data["studies"]
print(f"Total studies before dedup: {len(studies)}")

by_uid = {}
for i, s in enumerate(studies):
    by_uid[s["uid"]] = (i, s)

remove_uids = set()

# --- Group 1: PSMAfore ---
keeper_uid = "lupsma_prostata_2"
remove_uid = "teranostico_emergente_6"
if keeper_uid in by_uid and remove_uid in by_uid:
    keeper = by_uid[keeper_uid][1]
    removed = by_uid[remove_uid][1]
    if "Categoria 1 NCCN" not in keeper.get("impacto_reg", "") and "Categoria 1 NCCN" in removed.get("impacto_reg", ""):
        keeper["impacto_reg"] = keeper.get("impacto_reg", "") + " Categoria 1 NCCN para uso pre-taxano."
    excl = keeper.get("excl", "")
    if "insuficiencia renal" not in excl.lower() and "insufici" in removed.get("excl", "").lower():
        keeper["excl"] = excl + " Insuficiência renal ou medular grave."
    remove_uids.add(remove_uid)
    print(f"  Group 1 (PSMAfore): merging {remove_uid} -> {keeper_uid}")
else:
    print(f"  Group 1 (PSMAfore): SKIPPED - UIDs not found")

# --- Group 2: SPLASH ---
keeper_uid = "lupsma_prostata_3"
remove_uid = "teranostico_emergente_5"
if keeper_uid in by_uid and remove_uid in by_uid:
    keeper = by_uid[keeper_uid][1]
    removed = by_uid[remove_uid][1]
    sec = keeper.get("secundario", "")
    if "crossover" not in sec.lower() and "84%" in removed.get("secundario", ""):
        keeper["secundario"] = sec + " Crossover 84% no braço comparador."
    ind = keeper.get("indicacao", "")
    if "daro" not in ind.lower() and "daro" in removed.get("indicacao", "").lower():
        keeper["indicacao"] = ind.replace("pós-ARPi", "pós-ARPi (abi/enza/apa/daro)")
    remove_uids.add(remove_uid)
    print(f"  Group 2 (SPLASH): merging {remove_uid} -> {keeper_uid}")
else:
    print(f"  Group 2 (SPLASH): SKIPPED - UIDs not found")

# --- Group 3: PACIFIC ---
remove_uid_pacific = "pacific-durvalumab-p-s-crt-em-nsclc-est-gio-iii-n-o-ressec-vel"
keeper_uid_pacific = "rt_consolidacao_0"
if keeper_uid_pacific in by_uid and remove_uid_pacific in by_uid:
    keeper = by_uid[keeper_uid_pacific][1]
    removed = by_uid[remove_uid_pacific][1]
    prim = keeper.get("primario", "")
    if "7 anos" not in prim and "7y" not in prim.lower() and "7a" not in prim.lower():
        keeper["primario"] = prim + " OS 7 anos: 33% vs 22%."
    lim = removed.get("limit", "")
    klim = keeper.get("limit", "")
    if "14 dias" in lim and "14" not in klim:
        keeper["limit"] = klim + " Benefício de iniciar ≤14 dias pós-CRT." if klim else "Benefício de iniciar ≤14 dias pós-CRT."
    remove_uids.add(remove_uid_pacific)
    print(f"  Group 3 (PACIFIC): merging {remove_uid_pacific} -> {keeper_uid_pacific}")
else:
    print(f"  Group 3 (PACIFIC): SKIPPED - UIDs not found (keeper={keeper_uid_pacific in by_uid}, remove={remove_uid_pacific in by_uid})")

# --- Group 4: ADRIATIC ---
remove_uid_adriatic = "adriatic-durva-consolida-o-em-ls-sclc-p-s-qrt"
keeper_uid_adriatic = "rt_consolidacao_4"
if keeper_uid_adriatic in by_uid and remove_uid_adriatic in by_uid:
    keeper = by_uid[keeper_uid_adriatic][1]
    removed = by_uid[remove_uid_adriatic][1]
    tox_a = removed.get("tox_g3", "")
    tox_b = keeper.get("tox_g3", "")
    if "24.3%" in tox_a and "24.3" not in tox_b:
        keeper["tox_g3"] = tox_b + " EA G3+ 24.3% vs 24.2%." if tox_b else "EA G3+ 24.3% vs 24.2%."
    remove_uids.add(remove_uid_adriatic)
    print(f"  Group 4 (ADRIATIC): merging {remove_uid_adriatic} -> {keeper_uid_adriatic}")
else:
    print(f"  Group 4 (ADRIATIC): SKIPPED - UIDs not found (keeper={keeper_uid_adriatic in by_uid}, remove={remove_uid_adriatic in by_uid})")

# --- Group 5: PHEO/PGL ---
keeper_uid = "ppgl_0"
remove_uid = "ppgl_2"
if keeper_uid in by_uid and remove_uid in by_uid:
    keeper = by_uid[keeper_uid][1]
    removed = by_uid[remove_uid][1]
    ind = keeper.get("indicacao", "")
    if "MIBG" not in ind and "MIBG" in removed.get("indicacao", ""):
        keeper["indicacao"] = removed.get("indicacao", "")
    remove_uids.add(remove_uid)
    print(f"  Group 5 (PHEO/PGL): merging {remove_uid} -> {keeper_uid}")
else:
    print(f"  Group 5 (PHEO/PGL): SKIPPED - UIDs not found")

# Remove duplicates
if remove_uids:
    studies_clean = [s for s in studies if s["uid"] not in remove_uids]
    removed_count = len(studies) - len(studies_clean)
    print(f"\nRemoved {removed_count} duplicate entries")
    print(f"Total studies after dedup: {len(studies_clean)}")
    data["studies"] = studies_clean

    cat_counts = {}
    for s in studies_clean:
        cid = s.get("category_id", "")
        cat_counts[cid] = cat_counts.get(cid, 0) + 1
    for cat in data.get("categories", []):
        cid = cat["id"]
        if cid in cat_counts:
            cat["count"] = cat_counts[cid]

    if "metadata" in data:
        data["metadata"]["total_studies"] = len(studies_clean)

    backup = DATA_FILE.with_name("data.js.bak_pre_dedup")
    shutil.copy2(DATA_FILE, backup)
    print(f"Backup created: {backup}")

    header = "\n".join(header_lines)
    json_out = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    output = header + "\nwindow.THERA_DATA = " + json_out + ";\n"
    DATA_FILE.write_text(output, encoding="utf-8")
    print(f"File written: {DATA_FILE}")
    print("Done!")
else:
    print("No duplicates to remove.")
