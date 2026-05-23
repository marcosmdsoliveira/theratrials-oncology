#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
add_crosslinks.py — Add cross-links.js script tag to all radiofarmaco pages.
Inserts <script src="assets/js/cross-links.js" defer></script> before common.js.
"""
import os

site_dir = r"C:\Users\marco\Desktop\TheraTrials Oncology\site"
pages = [
    "lu-psma.html", "lu-dotatate.html", "ra-223.html",
    "y90.html", "mibg.html", "iodo-131.html", "novos-alfa.html"
]

script_tag = '<script src="assets/js/cross-links.js" defer></script>'
anchor = '<script src="assets/js/common.js" defer></script>'

for page in pages:
    path = os.path.join(site_dir, page)
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    if 'cross-links.js' in content:
        print(f"  SKIP {page} (already has cross-links.js)")
        continue

    if anchor in content:
        content = content.replace(anchor, script_tag + '\n' + anchor)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  OK   {page}")
    else:
        print(f"  WARN {page} — anchor not found")

print("Done.")
