"""
add_canonical.py
Adds <meta name="robots"> and <link rel="canonical"> to all public HTML pages
in the TheraTrials Oncology site/ root directory.

Rules:
- Insert AFTER the <meta name="description" ...> line.
- Public pages  → robots index,follow + canonical tag.
- Skipped pages → robots noindex,nofollow only (no canonical).
- If the file already has <meta name="robots", skip it entirely.
"""

import os
import re

# ── Config ──────────────────────────────────────────────────────────────────
SITE_DIR = os.path.join(os.path.dirname(__file__), "..")   # …/site/
BASE_URL  = "https://theratrials.com/"

# Pages that must NOT be indexed (noindex, nofollow — no canonical)
NOINDEX_PAGES = {
    "offline.html",
    "privacidade.html",
    "termos-uso.html",
    "direitos-autorais.html",
    "guideline-detail.html",
}

# ── Helpers ──────────────────────────────────────────────────────────────────
def canonical_url(filename: str) -> str:
    """Return the canonical URL for a given HTML filename."""
    if filename == "index.html":
        return BASE_URL
    return BASE_URL + filename


def build_insertion(filename: str, indent: str) -> str:
    """Build the two (or one) tag lines to insert, preserving indentation."""
    if filename in NOINDEX_PAGES:
        return f'{indent}<meta name="robots" content="noindex, nofollow">\n'
    else:
        robots    = f'{indent}<meta name="robots" content="index, follow">\n'
        canonical = f'{indent}<link rel="canonical" href="{canonical_url(filename)}">\n'
        return robots + canonical


# ── Main ─────────────────────────────────────────────────────────────────────
modified = []
skipped_already_has_robots = []

# Only HTML files directly in site/ (not in sub-directories)
html_files = sorted(
    f for f in os.listdir(SITE_DIR)
    if f.lower().endswith(".html") and os.path.isfile(os.path.join(SITE_DIR, f))
)

for filename in html_files:
    filepath = os.path.join(SITE_DIR, filename)

    with open(filepath, encoding="utf-8") as fh:
        content = fh.read()

    # ── Guard: already has a robots tag ────────────────────────────────────
    if re.search(r'<meta\s+name=["\']robots["\']', content, re.IGNORECASE):
        skipped_already_has_robots.append(filename)
        continue

    # ── Find the description line ───────────────────────────────────────────
    desc_pattern = re.compile(r'^([ \t]*)<meta\s+name=["\']description["\'].*$',
                              re.MULTILINE | re.IGNORECASE)
    match = desc_pattern.search(content)
    if not match:
        # Fallback: insert after <title> tag (e.g. offline.html has no description)
        title_pattern = re.compile(r'^([ \t]*)<title>.*?</title>.*$',
                                   re.MULTILINE | re.IGNORECASE)
        match = title_pattern.search(content)
        if not match:
            print(f"  [WARN] No <meta name=\"description\"> or <title> found in {filename} — skipped")
            continue
        print(f"  [INFO] No description tag; inserting after <title> in {filename}")

    indent    = match.group(1)          # preserve leading whitespace
    insertion = build_insertion(filename, indent)

    # Insert AFTER the description line (after its newline)
    insert_pos = match.end()
    # Advance past the newline that terminates the description line
    if insert_pos < len(content) and content[insert_pos] == "\n":
        insert_pos += 1
    elif insert_pos < len(content) - 1 and content[insert_pos:insert_pos+2] == "\r\n":
        insert_pos += 2

    new_content = content[:insert_pos] + insertion + content[insert_pos:]

    with open(filepath, "w", encoding="utf-8") as fh:
        fh.write(new_content)

    modified.append(filename)

# ── Report ────────────────────────────────────────────────────────────────────
print("\n=== add_canonical.py — results ===\n")

if modified:
    print(f"Modified ({len(modified)} files):")
    for f in modified:
        tag = "noindex" if f in NOINDEX_PAGES else "index + canonical"
        print(f"  ✓  {f:<40} [{tag}]")
else:
    print("  No files modified.")

if skipped_already_has_robots:
    print(f"\nSkipped — already has <meta name=\"robots\"> ({len(skipped_already_has_robots)} files):")
    for f in skipped_already_has_robots:
        print(f"  –  {f}")

print()
