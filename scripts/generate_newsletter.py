#!/usr/bin/env python3
"""
TheraTrials Oncology — Newsletter Generator
===========================================================
Gera o conteúdo da newsletter mensal comparando o estado atual
dos dados com o snapshot anterior (salvo em newsletters/last_snapshot.json).

O script:
  1. Carrega explorer.json, tracker.json, trials_br.js, guidelines-data.js
  2. Compara com o snapshot anterior (se existir)
  3. Gera:
     - newsletters/YYYY-MM.html (arquivo público no site)
     - newsletters/YYYY-MM.md   (corpo do email para Buttondown)
  4. Salva novo snapshot para a próxima comparação

Sem dependências externas — só stdlib.

Uso local:
    python scripts/generate_newsletter.py

Uso CI (GitHub Action):
    Mesmo comando. O workflow faz commit + push do newsletters/ se houver mudança.
"""

from __future__ import annotations

import json
import re
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# -----------------------------------------------------------------------------
# Paths
# -----------------------------------------------------------------------------
THIS_FILE = Path(__file__).resolve()
SITE_DIR = THIS_FILE.parent.parent  # site/
SCRIPTS_DIR = THIS_FILE.parent

EXPLORER_JSON = SITE_DIR / "assets" / "data" / "explorer.json"
TRACKER_JSON = SITE_DIR / "assets" / "data" / "tracker.json"
TRIALS_BR_JS = SITE_DIR / "assets" / "js" / "trials_br.js"
GUIDELINES_JS = SITE_DIR / "assets" / "js" / "guidelines-data.js"

NEWSLETTERS_DIR = SITE_DIR / "newsletters"
SNAPSHOT_FILE = NEWSLETTERS_DIR / "last_snapshot.json"

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def load_json(path: Path) -> dict | list | None:
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_js_array(path: Path, var_pattern: str) -> list:
    """Extrai array JS de um arquivo .js usando regex simples."""
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    # Tenta extrair o JSON array do arquivo
    # Padrão: const VARIABLE = [...];
    match = re.search(rf'{var_pattern}\s*=\s*(\[[\s\S]*?\]);', text)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    return []


def count_ncts_in_js(path: Path) -> set:
    """Extrai NCTs de um arquivo JS."""
    if not path.exists():
        return set()
    text = path.read_text(encoding="utf-8")
    return set(re.findall(r'NCT\d{8}', text))


def get_explorer_stats(data: dict | None) -> dict:
    if not data:
        return {"total": 0, "ncts": set(), "phases": {}, "isotopes": {}}
    trials = data.get("trials", [])
    ncts = {t.get("nct", "") for t in trials if t.get("nct")}
    phases = {}
    isotopes = {}
    for t in trials:
        phase = t.get("phase", "Outro")
        phases[phase] = phases.get(phase, 0) + 1
        iso = t.get("isotope", "Outro")
        isotopes[iso] = isotopes.get(iso, 0) + 1
    return {
        "total": len(trials),
        "ncts": ncts,
        "phases": phases,
        "isotopes": isotopes,
    }


def get_tracker_stats(data: dict | None) -> dict:
    if not data:
        return {"total": 0, "ncts": set(), "facets": {}}
    # Tracker has totals.trials and a trials[] array (or facets only in seed)
    total = 0
    ncts = set()
    facets = {}
    if "totals" in data:
        total = data["totals"].get("trials", 0)
    if "trials" in data and isinstance(data["trials"], list):
        ncts = {t.get("nct", "") for t in data["trials"] if t.get("nct")}
    if "facets" in data:
        facets = data["facets"]
    return {"total": total, "ncts": ncts, "facets": facets}


# -----------------------------------------------------------------------------
# Newsletter content generation
# -----------------------------------------------------------------------------

MONTHS_PT = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
    5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
    9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro",
}


def generate_content(now: datetime) -> tuple[str, str, dict]:
    """
    Retorna (markdown_body, html_page, new_snapshot).
    """
    month_name = MONTHS_PT[now.month]
    year = now.year
    edition_title = f"TheraTrials Newsletter — {month_name} {year}"

    # --- Load current data ---
    explorer = load_json(EXPLORER_JSON)
    tracker = load_json(TRACKER_JSON)
    br_ncts = count_ncts_in_js(TRIALS_BR_JS)
    gl_ncts = count_ncts_in_js(GUIDELINES_JS)

    explorer_stats = get_explorer_stats(explorer)
    tracker_stats = get_tracker_stats(tracker)

    # --- Load previous snapshot ---
    prev = load_json(SNAPSHOT_FILE) or {}
    prev_explorer_ncts = set(prev.get("explorer_ncts", []))
    prev_br_ncts = set(prev.get("br_ncts", []))
    prev_tracker_ncts = set(prev.get("tracker_ncts", []))
    prev_explorer_total = prev.get("explorer_total", 0)
    prev_br_total = prev.get("br_total", 0)
    prev_tracker_total = prev.get("tracker_total", 0)

    # --- Compute deltas ---
    new_explorer_ncts = explorer_stats["ncts"] - prev_explorer_ncts
    new_br_ncts = br_ncts - prev_br_ncts
    new_tracker_ncts = tracker_stats["ncts"] - prev_tracker_ncts

    delta_explorer = len(new_explorer_ncts)
    delta_br = len(new_br_ncts)
    delta_tracker = max(tracker_stats["total"] - prev_tracker_total, 0)

    # --- Build sections ---
    sections_md = []
    sections_md.append(f"# {edition_title}\n")
    sections_md.append(f"*Edição {month_name} {year} · gerada automaticamente em {now.strftime('%d/%m/%Y')}*\n")
    sections_md.append("---\n")

    # Summary
    sections_md.append("## Resumo do mês\n")
    sections_md.append(f"| Métrica | Atual | Novos este mês |")
    sections_md.append(f"|---------|-------|---------------|")
    sections_md.append(f"| Explorer (pipeline RLT global) | **{explorer_stats['total']}** estudos | +{delta_explorer} |")
    sections_md.append(f"| Ensaios ativos no Brasil | **{len(br_ncts)}** estudos | +{delta_br} |")
    sections_md.append(f"| Tracker (radiofármacos) | **{tracker_stats['total']}** itens | +{delta_tracker} |")
    sections_md.append("")

    # Explorer highlights
    if delta_explorer > 0:
        sections_md.append("## Novos ensaios no Explorer\n")
        sections_md.append(f"Foram adicionados **{delta_explorer} novos estudos** ao pipeline global de radioligantes terapêuticos.\n")
        # Top isotopes (filter out empty keys)
        if explorer_stats["isotopes"]:
            filtered_iso = {k: v for k, v in explorer_stats["isotopes"].items() if k.strip()}
            top_iso = sorted(filtered_iso.items(), key=lambda x: -x[1])[:5]
            if top_iso:
                sections_md.append("**Isótopos mais representados no pipeline:**\n")
                for iso, count in top_iso:
                    sections_md.append(f"- {iso}: {count} estudos")
                sections_md.append("")

    # Brazil trials
    if delta_br > 0:
        sections_md.append("## Ensaios com recrutamento no Brasil\n")
        sections_md.append(f"**{delta_br} novos ensaios** com recrutamento aberto foram identificados em centros brasileiros.\n")
        sections_md.append(f"Total atual: {len(br_ncts)} estudos em recrutamento ativo.\n")

    # Tracker
    if delta_tracker > 0:
        sections_md.append("## Atualizações no Tracker\n")
        sections_md.append(f"**{delta_tracker} novos ensaios** no rastreador de radiofármacos terapêuticos.\n")
        # Show top facets if available
        facets = tracker_stats.get("facets", {})
        if facets.get("isotope"):
            top_tracker_iso = sorted(facets["isotope"].items(), key=lambda x: -x[1])[:3]
            sections_md.append("Isótopos no tracker: " + ", ".join(f"{k} ({v})" for k, v in top_tracker_iso))
            sections_md.append("")

    # No changes fallback
    if delta_explorer == 0 and delta_br == 0 and delta_tracker == 0:
        sections_md.append("## Status\n")
        sections_md.append("Nenhuma alteração significativa nos dados neste período. ")
        sections_md.append("A próxima atualização automática do pipeline ocorre no dia 1 do próximo mês.\n")

    # Footer
    sections_md.append("---\n")
    sections_md.append("## Acesse a plataforma\n")
    sections_md.append("- [Database](https://marcosmdsoliveira.github.io/theratrials-oncology/database.html) — 421 estudos curados")
    sections_md.append("- [Explorer](https://marcosmdsoliveira.github.io/theratrials-oncology/explorer.html) — Pipeline RLT global")
    sections_md.append("- [Ensaios BR](https://marcosmdsoliveira.github.io/theratrials-oncology/ensaios-clinicos.html) — Recrutamento aberto no Brasil")
    sections_md.append("- [Guidelines](https://marcosmdsoliveira.github.io/theratrials-oncology/guidelines.html) — 26 guidelines internacionais")
    sections_md.append("")
    sections_md.append("---\n")
    sections_md.append("*TheraTrials Oncology · Plataforma de evidências clínicas em oncologia*")
    sections_md.append("*Curadoria: Dr. Marcos Oliveira — Médico nuclear*\n")

    markdown_body = "\n".join(sections_md)

    # --- HTML archive page ---
    html_page = generate_archive_html(edition_title, month_name, year, now, markdown_body,
                                       explorer_stats, delta_explorer, br_ncts, delta_br,
                                       tracker_stats, delta_tracker)

    # --- New snapshot ---
    new_snapshot = {
        "generated_at": now.isoformat(),
        "explorer_total": explorer_stats["total"],
        "explorer_ncts": sorted(explorer_stats["ncts"]),
        "br_total": len(br_ncts),
        "br_ncts": sorted(br_ncts),
        "tracker_total": tracker_stats["total"],
        "tracker_ncts": sorted(tracker_stats["ncts"]),
    }

    return markdown_body, html_page, new_snapshot


def generate_archive_html(title: str, month: str, year: int, now: datetime,
                           md_body: str, explorer_stats: dict, delta_explorer: int,
                           br_ncts: set, delta_br: int, tracker_stats: dict,
                           delta_tracker: int) -> str:
    """Gera página HTML standalone para arquivo da newsletter."""

    date_str = now.strftime("%d/%m/%Y")

    stats_cards = f"""
    <div class="nl-stats">
      <div class="nl-stat-card">
        <div class="nl-stat-number">{explorer_stats['total']}</div>
        <div class="nl-stat-label">Estudos RLT (Explorer)</div>
        <div class="nl-stat-delta">+{delta_explorer} este mês</div>
      </div>
      <div class="nl-stat-card">
        <div class="nl-stat-number">{len(br_ncts)}</div>
        <div class="nl-stat-label">Ensaios ativos no Brasil</div>
        <div class="nl-stat-delta">+{delta_br} este mês</div>
      </div>
      <div class="nl-stat-card">
        <div class="nl-stat-number">{tracker_stats['total']}</div>
        <div class="nl-stat-label">Radiofármacos (Tracker)</div>
        <div class="nl-stat-delta">+{delta_tracker} este mês</div>
      </div>
    </div>"""

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Inter:wght@300;400;500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="../assets/css/theratrials.css">
<style>
.nl-container {{ max-width: 720px; margin: 0 auto; padding: 3rem 1.25rem; }}
.nl-header {{ text-align: center; margin-bottom: 3rem; }}
.nl-header h1 {{ font-family: 'Outfit', sans-serif; font-size: clamp(1.5rem, 3.5vw, 2.25rem); font-weight: 700; color: #F5F6F7; margin: 0 0 0.5rem; }}
.nl-header h1 .accent {{ color: #FF8400; }}
.nl-header .nl-date {{ color: #8E949C; font-size: 0.85rem; }}
.nl-stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem; margin: 2rem 0; }}
.nl-stat-card {{ background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06); border-radius: 12px; padding: 1.25rem; text-align: center; }}
.nl-stat-number {{ font-family: 'Outfit', sans-serif; font-size: 1.75rem; font-weight: 700; color: #FF8400; }}
.nl-stat-label {{ color: #F5F6F7; font-size: 0.82rem; margin-top: 0.25rem; }}
.nl-stat-delta {{ color: #0EA5B7; font-size: 0.75rem; font-weight: 500; margin-top: 0.4rem; }}
.nl-body {{ color: #C8CCD0; line-height: 1.75; font-size: 0.95rem; }}
.nl-body h2 {{ font-family: 'Outfit', sans-serif; font-size: 1.25rem; font-weight: 600; color: #F5F6F7; margin: 2rem 0 0.75rem; border-bottom: 1px solid rgba(255,255,255,0.06); padding-bottom: 0.5rem; }}
.nl-body ul {{ padding-left: 1.25rem; }}
.nl-body li {{ margin-bottom: 0.4rem; }}
.nl-body a {{ color: #FF8400; text-decoration: none; }}
.nl-body a:hover {{ text-decoration: underline; }}
.nl-body table {{ width: 100%; border-collapse: collapse; margin: 1rem 0; font-size: 0.85rem; }}
.nl-body th, .nl-body td {{ padding: 0.5rem 0.75rem; border: 1px solid rgba(255,255,255,0.08); text-align: left; }}
.nl-body th {{ background: rgba(255,132,0,0.08); color: #FF8400; font-weight: 600; }}
.nl-back {{ display: inline-flex; align-items: center; gap: 0.5rem; color: #8E949C; text-decoration: none; font-size: 0.85rem; margin-top: 2rem; }}
.nl-back:hover {{ color: #F5F6F7; }}
</style>
</head>
<body>
<div class="nl-container">
  <div class="nl-header">
    <h1>TheraTrials <span class="accent">Newsletter</span></h1>
    <div class="nl-date">{month} {year} &middot; Gerada em {date_str}</div>
  </div>

  {stats_cards}

  <div class="nl-body" id="nl-content">
    <!-- Content is rendered from markdown by the archive page -->
    <noscript>Conteúdo requer JavaScript habilitado.</noscript>
  </div>

  <a href="../newsletter.html" class="nl-back">&larr; Voltar para Newsletter</a>
</div>

<script>
// Simple markdown-to-HTML for archive display
(function() {{
  var md = {json.dumps(md_body, ensure_ascii=False)};
  var html = md
    .replace(/^# (.+)$/gm, '')  // skip h1, already in header
    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/\\*\\*(.+?)\\*\\*/g, '<strong>$1</strong>')
    .replace(/\\*(.+?)\\*/g, '<em>$1</em>')
    .replace(/^- (.+)$/gm, '<li>$1</li>')
    .replace(/(<li>.*<\\/li>)/s, '<ul>$1</ul>')
    .replace(/\\[(.+?)\\]\\((.+?)\\)/g, '<a href="$2">$1</a>')
    .replace(/^\\|(.+)$/gm, function(line) {{
      if (line.match(/^\\|[-\\s|]+\\|$/)) return '';
      var cells = line.split('|').filter(function(c){{ return c.trim(); }});
      var tag = line.indexOf('**') > -1 ? 'td' : 'td';
      return '<tr>' + cells.map(function(c){{ return '<td>' + c.trim() + '</td>'; }}).join('') + '</tr>';
    }})
    .replace(/---/g, '<hr>')
    .replace(/\\n\\n/g, '<br><br>');
  document.getElementById('nl-content').innerHTML = html;
}})();
</script>
</body>
</html>"""
    return html


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

def main():
    now = datetime.now(timezone.utc)
    edition_key = now.strftime("%Y-%m")

    print(f"[newsletter] Gerando edição: {edition_key}")
    print(f"[newsletter] Site dir: {SITE_DIR}")

    ensure_dir(NEWSLETTERS_DIR)

    markdown_body, html_page, new_snapshot = generate_content(now)

    # Save markdown (for email sending)
    md_path = NEWSLETTERS_DIR / f"{edition_key}.md"
    md_path.write_text(markdown_body, encoding="utf-8")
    print(f"[newsletter] Markdown salvo: {md_path}")

    # Save HTML archive page
    html_path = NEWSLETTERS_DIR / f"{edition_key}.html"
    html_path.write_text(html_page, encoding="utf-8")
    print(f"[newsletter] HTML arquivo salvo: {html_path}")

    # Save snapshot for next comparison
    with open(SNAPSHOT_FILE, "w", encoding="utf-8") as f:
        json.dump(new_snapshot, f, ensure_ascii=False, indent=1)
    print(f"[newsletter] Snapshot atualizado: {SNAPSHOT_FILE}")

    # Output for GitHub Actions
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a") as f:
            f.write(f"edition={edition_key}\n")
            f.write(f"md_path={md_path}\n")
            f.write(f"has_changes={'true' if (new_snapshot.get('explorer_total', 0) != new_snapshot.get('explorer_total', 0)) else 'true'}\n")

    print(f"\n[newsletter] Concluído com sucesso!")
    print(f"  Explorer: {new_snapshot['explorer_total']} estudos")
    print(f"  Brasil:   {new_snapshot['br_total']} ensaios")
    print(f"  Tracker:  {new_snapshot['tracker_total']} itens")

    return 0


if __name__ == "__main__":
    sys.exit(main())
