"""Move decay-calc section to position #04 (after dose-calc) and renumber sections."""
import re

FILE = r"C:\Users\marco\Desktop\TheraTrials Oncology\site\ferramentas.html"

with open(FILE, "r", encoding="utf-8") as f:
    html = f.read()

# 1. Find and extract the decay-calc section (from <section ... id="decay-calc" to its closing </section>)
# The section includes its <script> block before the closing </section>
decay_start_pattern = r'(\n    <section class="tool" id="decay-calc")'
match_start = re.search(decay_start_pattern, html)
if not match_start:
    raise ValueError("Could not find decay-calc section start")

start_idx = match_start.start()

# Find the closing </section> for this section
# Count nested <section> tags to find the right closing tag
pos = match_start.end()
depth = 1
while depth > 0 and pos < len(html):
    next_open = html.find('<section', pos)
    next_close = html.find('</section>', pos)
    if next_close == -1:
        raise ValueError("Could not find closing </section>")
    if next_open != -1 and next_open < next_close:
        depth += 1
        pos = next_open + 8
    else:
        depth -= 1
        if depth == 0:
            end_idx = next_close + len('</section>')
        pos = next_close + len('</section>')

decay_section = html[start_idx:end_idx]
print(f"Extracted decay-calc section: {len(decay_section)} chars, lines ~{html[:start_idx].count(chr(10))+1} to ~{html[:end_idx].count(chr(10))+1}")

# 2. Remove decay-calc section from original position
html_without_decay = html[:start_idx] + html[end_idx:]

# 3. Find insertion point: after the dose-calc section (id="dose-calc")
dose_start_pattern = r'<section class="tool" id="dose-calc"'
dose_match = re.search(dose_start_pattern, html_without_decay)
if not dose_match:
    raise ValueError("Could not find dose-calc section")

# Find the closing </section> for dose-calc
pos = dose_match.end()
depth = 1
while depth > 0 and pos < len(html_without_decay):
    next_open = html_without_decay.find('<section', pos)
    next_close = html_without_decay.find('</section>', pos)
    if next_close == -1:
        raise ValueError("Could not find closing </section> for dose-calc")
    if next_open != -1 and next_open < next_close:
        depth += 1
        pos = next_open + 8
    else:
        depth -= 1
        if depth == 0:
            insert_idx = next_close + len('</section>')
        pos = next_close + len('</section>')

print(f"Inserting after dose-calc section at char index {insert_idx}")

# 4. Insert decay-calc after dose-calc
html_reordered = html_without_decay[:insert_idx] + decay_section + html_without_decay[insert_idx:]

# 5. Renumber tool-num divs in sections
# Map: section id -> new number
renumber_map = {
    'ajcc': '01',
    'ctcae': '02',
    'dose-calc': '03',
    'decay-calc': '04',
    'psma': '05',
    'petct': '06',
    'tne': '07',
    'imuno': '08',
    'anatomica': '09',
    'hcc': '10',
    'clinica': '11',
}

for section_id, new_num in renumber_map.items():
    # Find the section tag and its tool-num div (within ~5 lines)
    pattern = rf'(<section class="tool" id="{section_id}"[^>]*>\s*<div class="tool-head">\s*<div class="tool-num"[^>]*>)\d{{2}}(</div>)'
    match = re.search(pattern, html_reordered, re.DOTALL)
    if match:
        html_reordered = html_reordered[:match.start()] + match.group(1) + new_num + match.group(2) + html_reordered[match.end():]
        print(f"  Renumbered section '{section_id}' -> {new_num}")
    else:
        print(f"  WARNING: Could not find tool-num for section '{section_id}'")

# 6. Write result
with open(FILE, "w", encoding="utf-8") as f:
    f.write(html_reordered)

print("\nDone! Decay-calc moved to position #04 and all sections renumbered.")
