#!/usr/bin/env python3
"""Add Open Graph + Twitter Card meta tags to all TheraTrials HTML pages."""

import re, os

SITE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BASE = "https://theratrials.com"
OG_IMG = f"{BASE}/assets/img/og-cover.png"

# Page metadata: filename -> (og:title, og:description)
PAGES = {
    "index.html": (
        "TheraTrials Oncology · Evidências em terapia oncológica avançada",
        "Plataforma de evidências clínicas em oncologia moderna: teranóstico, terapias-alvo, imunoterapia, biomarcadores e imagem molecular."
    ),
    "database.html": (
        "Database · TheraTrials Oncology",
        "Banco interativo de 421 estudos selecionados em oncologia moderna. Filtre por tumor, modalidade, fase e linha terapêutica."
    ),
    "tracker.html": (
        "Radiopharmaceutical Therapy Tracker · TheraTrials Oncology",
        "Pipeline global de radiofármacos terapêuticos em oncologia, alimentado pela API do ClinicalTrials.gov v2 com atualização mensal."
    ),
    "explorer.html": (
        "TheraTrials Explorer · TheraTrials Oncology",
        "Tracker ativo de radioligantes terapêuticos em oncologia. Filtre por isótopo, ligante, fase, neoplasia, sponsor e país."
    ),
    "trial-matcher.html": (
        "Trial Matcher · TheraTrials Oncology",
        "Encontre ensaios clínicos relevantes para seu paciente. Filtre por tumor, biomarcador, linha terapêutica e modalidade."
    ),
    "radiofarmacos.html": (
        "Radiofármacos Terapêuticos · TheraTrials Oncology",
        "Dossiês completos dos radiofármacos terapêuticos: 177Lu-PSMA-617, DOTATATE, 223Ra, 90Y, MIBG, 131I e novos α-emissores."
    ),
    "lu-psma.html": (
        "177Lu-PSMA-617 · TheraTrials Oncology",
        "Dossiê completo do 177Lu-PSMA-617: mecanismo, esquema VISION/TheraP/PSMAfore, dosimetria e perspectivas alfa no câncer de próstata."
    ),
    "lu-dotatate.html": (
        "177Lu-DOTATATE (PRRT) · TheraTrials Oncology",
        "Dossiê completo da PRRT com 177Lu-DOTATATE: mecanismo SSTR2, NETTER-1/2, dosimetria, nefroproteção e perspectivas alfa em NETs."
    ),
    "ra-223.html": (
        "223Ra-Cloreto (Xofigo) · TheraTrials Oncology",
        "Dossiê do 223Ra-Cloreto: mecanismo cálcio-mimético, esquema ALSYMPCA, PEACE-3, dosimetria e uso em metástases ósseas."
    ),
    "y90.html": (
        "90Y-Microesferas (TARE) · TheraTrials Oncology",
        "Radioembolização hepática com 90Y: microesferas de vidro vs resina, mapeamento MAA, dosimetria personalizada e ensaios clínicos."
    ),
    "mibg.html": (
        "131I-MIBG (Azedra) · TheraTrials Oncology",
        "Dossiê do 131I-MIBG: mecanismo NET, neuroblastoma e PPGL maligno, bloqueio tireoidiano e ensaios MIBG-MIDAS."
    ),
    "iodo-131.html": (
        "131I-Iodeto de sódio · TheraTrials Oncology",
        "O radiofármaco fundador da medicina nuclear terapêutica: mecanismo NIS, CDT, hipertireoidismo e radioproteção CNEN."
    ),
    "novos-alfa.html": (
        "Novos α-emissores · TheraTrials Oncology",
        "Próxima geração em teranóstico: 225Ac-PSMA, 161Tb, 212Pb-DOTAMTATE, 227Th e 211At. Comparativo β vs α e ensaios clínicos."
    ),
    "guidelines.html": (
        "Guidelines em Teranóstico · TheraTrials Oncology",
        "Mapa prático dos principais guidelines internacionais em teranóstico, PRRT, PSMA-RLT, TARE, radioiodoterapia e dosimetria."
    ),
    "guideline-detail.html": (
        "Guideline Teranóstico · TheraTrials Oncology",
        "Detalhes completos do guideline: escopo, indicações, pontos-chave, radiofármacos, aspectos práticos e referência."
    ),
    "modalidades.html": (
        "Modalidades Terapêuticas · TheraTrials Oncology",
        "Evidências clínicas por modalidade: teranóstico, terapias-alvo, PARP, ARPi, quimioterapia e imunoterapia em oncologia."
    ),
    "ensaios-clinicos.html": (
        "Ensaios Clínicos Ativos no Brasil · TheraTrials Oncology",
        "Banco selecionado de ensaios clínicos em recrutamento ativo no Brasil. Filtre por neoplasia, modalidade, fase e biomarcador."
    ),
    "tumor-boards.html": (
        "Tumor Boards · TheraTrials Oncology",
        "Evidências organizadas por tipo tumoral para uso em tumor boards multidisciplinares em oncologia."
    ),
    "ferramentas.html": (
        "Ferramentas Clínicas · TheraTrials Oncology",
        "Estadiamento AJCC TNM e tabela de eventos adversos CTCAE v6.0 para uso em oncologia teranóstica."
    ),
    "fundamentos.html": (
        "Fundamentos em Pesquisa Clínica Oncológica · TheraTrials Oncology",
        "Guia visual: fases de ensaios, endpoints, estatística, teranóstico, biossimilares e leitura crítica de estudos clínicos."
    ),
    "dashboard-analise.html": (
        "Dashboard de Análise · TheraTrials Oncology",
        "Visualização analítica do banco de estudos TheraTrials: distribuição por modalidade, tumor, fase e linha terapêutica."
    ),
    "eventos.html": (
        "Eventos Científicos · TheraTrials Oncology",
        "Próximos congressos, simpósios e webinars em medicina nuclear, teranóstica e oncologia."
    ),
    "newsletter.html": (
        "Newsletter · TheraTrials Oncology",
        "Curadoria mensal de novidades em teranóstica, ensaios clínicos e medicina nuclear. Inscreva-se gratuitamente."
    ),
    "about.html": (
        "Sobre o TheraTrials Oncology",
        "Missão, metodologia, fontes e glossário da plataforma TheraTrials Oncology — evidências em oncologia moderna."
    ),
    "privacidade.html": (
        "Política de Privacidade · TheraTrials Oncology",
        "Política de privacidade do TheraTrials Oncology: minimização de dados, sem cadastro, conformidade com a LGPD."
    ),
    "termos-uso.html": (
        "Termos de Uso · TheraTrials Oncology",
        "Termos de uso da plataforma TheraTrials Oncology — condições, escopo educacional e limitações de responsabilidade."
    ),
    "direitos-autorais.html": (
        "Direitos Autorais · TheraTrials Oncology",
        "Aviso de direitos autorais do TheraTrials Oncology: titularidade, atribuição de fontes, fair use educacional e licenças."
    ),
}

def build_og_block(filename, title, desc):
    url = f"{BASE}/" if filename == "index.html" else f"{BASE}/{filename}"
    return f"""<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:type" content="website">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{OG_IMG}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{desc}">
<meta name="twitter:image" content="{OG_IMG}">"""

def process_file(filename, title, desc):
    filepath = os.path.join(SITE, filename)
    if not os.path.exists(filepath):
        return f"SKIP {filename} — not found"

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    og_block = build_og_block(filename, title, desc)

    # Check if OG tags already exist (tracker.html, explorer.html)
    if '<meta property="og:title"' in content:
        # Remove existing OG/Twitter block and replace
        content = re.sub(
            r'<meta property="og:title"[^>]*>\s*\n'
            r'<meta property="og:description"[^>]*>\s*\n'
            r'<meta property="og:type"[^>]*>\s*\n'
            r'(<meta property="og:url"[^>]*>\s*\n)?'
            r'<meta property="og:image"[^>]*>\s*\n'
            r'<meta name="twitter:card"[^>]*>'
            r'(\s*\n<meta name="twitter:title"[^>]*>)?'
            r'(\s*\n<meta name="twitter:description"[^>]*>)?'
            r'(\s*\n<meta name="twitter:image"[^>]*>)?',
            og_block,
            content
        )
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return f"UPDATED {filename} — replaced existing OG block"

    # Find insertion point: after <meta name="description" ...>
    desc_match = re.search(r'(<meta name="description"[^>]*>)', content)
    if desc_match:
        insert_pos = desc_match.end()
        content = content[:insert_pos] + "\n" + og_block + content[insert_pos:]
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return f"ADDED {filename} — after <meta description>"

    # Fallback: after <title>...</title>
    title_match = re.search(r'(</title>)', content)
    if title_match:
        insert_pos = title_match.end()
        # Also add a description meta tag
        meta_desc = f'\n<meta name="description" content="{desc}">'
        content = content[:insert_pos] + meta_desc + "\n" + og_block + content[insert_pos:]
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return f"ADDED {filename} — after <title> (+ added meta description)"

    return f"FAILED {filename} — no insertion point found"


if __name__ == "__main__":
    print(f"Processing {len(PAGES)} pages...\n")
    results = []
    for fn, (title, desc) in PAGES.items():
        result = process_file(fn, title, desc)
        results.append(result)
        print(result)

    added = sum(1 for r in results if "ADDED" in r or "UPDATED" in r)
    print(f"\nDone: {added}/{len(PAGES)} pages processed successfully.")
