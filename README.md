# TheraTrials Oncology

> Plataforma de evidências clínicas em oncologia moderna — ensaios clínicos curados de teranóstico, terapia-alvo e imunoterapia, organizados para uso em tumor boards e revisão científica rápida.

**Versão:** 1.0
**Status:** repositório privado · uso educacional
**Autor:** Marcos Oliveira — médico nuclear

---

## Sobre o projeto

TheraTrials Oncology é um site estático (HTML + JS vanilla, sem build step) que reúne **144 ensaios clínicos** distribuídos em **17 categorias**, com schema padronizado de **40 campos por estudo** (intervenção, dose, fase, endpoints, resultados-chave, biomarcadores, NCT/DOI etc.).

A plataforma foi concebida para o fluxo real de um médico nuclear / oncologista clínico em momentos de decisão: tumor board, segunda opinião, conferência de elegibilidade, ensino para residentes. O foco editorial é o **teranóstico** (próstata, NETs, HCC, MIBG, novos α-emissores), com cobertura plena de imunoterapia 1L, drivers moleculares e perioperatório (NSCLC, mama HER2+/HR+/TNBC).

## Estrutura

```
site/
├── index.html                  # Landing
├── database.html               # 144 estudos · 17 categorias
├── estudos-ativos.html         # 14 trials ativos no Brasil (BH)
├── tumor-boards.html           # Visão por tumor
├── modalidades.html            # Visão por modalidade
├── ferramentas.html            # AJCC TNM · CTCAE v6.0 · calculadoras
├── fundamentos.html            # Educacional sobre ensaios clínicos
├── about.html                  # Sobre / metodologia
├── lu-psma.html                # ¹⁷⁷Lu-PSMA-617 (página profunda)
├── lu-dotatate.html            # ¹⁷⁷Lu-DOTATATE
├── ra-223.html                 # ²²³Ra-Cloreto
├── y90.html                    # ⁹⁰Y-Microesferas (TARE)
├── mibg.html                   # ¹³¹I-MIBG
├── novos-alfa.html             # Novos α-emissores
├── termos-uso.html             # Esboço · termos de uso
├── privacidade.html            # Esboço · LGPD
├── direitos-autorais.html      # Esboço · atribuição de fontes
└── assets/
    ├── css/
    │   ├── theratrials.css     # estilo global
    │   └── radiofarmaco.css    # estilo das páginas de radiofármaco
    ├── js/
    │   ├── data.js             # 144 estudos · schema 40 campos
    │   ├── trials_br.js        # 14 estudos ativos no BR
    │   └── common.js           # filtros · favoritos · export
    └── img/
```

## Identidade visual

- **Cores:** Graphite `#0E0F12` · Amber `#FF8400` · Teal `#0EA5B7`
- **Tipografia:** Outfit (display) · Inter (body) · JetBrains Mono (mono)
- **Ícones:** Lucide
- **Conceito:** orbital · evidência como ferramenta clínica

## Stack

- HTML5 estático (sem build, sem framework de página)
- Alpine.js 3.13.5 — reatividade local em listas e modais
- Lucide — ícones
- IntersectionObserver — fade-in de seções
- Native `<dialog>` element — modais

## Como rodar localmente

```bash
# Opção 1: abrir direto no navegador
# Duplo-clique em index.html

# Opção 2: servidor local (recomendado para que fetches/relativos funcionem)
cd site
python -m http.server 8080
# acessar http://localhost:8080/
```

## Convenções de design

- **Listas detalháveis:** padrão = grade de cards-resumo + modal `<dialog>` nativo. Não usar `<details>` accordion.
- **Modal:** fecha sempre via 3 vias — botão X, tecla `Esc` (nativa), clique no backdrop via `e.target === dlg`.
- **Lucide:** chamadas a `lucide.createIcons()` em try/catch e sempre **depois** de `dlg.showModal()`.
- **Schema dos estudos:** 40 campos imutáveis (não alterar sem versão major).

## Licença e uso

Conteúdo de uso **educacional** para profissionais de saúde. Não substitui diretrizes oficiais, leitura primária dos artigos, julgamento clínico individualizado ou prescrição médica. Decisões assistenciais permanecem responsabilidade do médico assistente.

Reprodução comercial não autorizada é vedada. Citações em contexto educacional são permitidas mediante atribuição. Ver [Aviso de direitos autorais](direitos-autorais.html) e [Termos de uso](termos-uso.html).

## Roadmap

- [x] **v1.0** — 144 estudos, 17 categorias, 6 páginas de radiofármaco, ferramentas (AJCC TNM cards+modal, CTCAE), 14 estudos ativos no BR
- [ ] **v1.1** — Conteúdo final das 3 páginas legais
- [ ] **v1.2** — Bloco 4: Atlas visual e aprendizado interativo
- [ ] **v1.3** — Bloco 5: Changelog + calendário de congressos
- [ ] **v2.0** — Modo claro · quiz/flashcards · BibTeX/RIS export

## Contato

Marcos Oliveira — médico nuclear, foco em teranóstico, PET/CT e oncologia.
Email: marcosmdsoliveira@gmail.com

---

© 2026 TheraTrials Oncology · uso educacional · não substitui diretrizes oficiais ou leitura primária
