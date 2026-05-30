# TheraTrials Oncology

> Plataforma de evidências clínicas em oncologia moderna — ensaios clínicos analisados, guidelines internacionais, dossiês de radiofármacos e ferramentas clínicas, organizados para uso em tumor boards, teranóstico e revisão científica rápida.

**Versão:** 1.3  
**Status:** repositório privado · uso educacional  
**Autor:** Dr. Marcos Oliveira — médico nuclear  
**Última atualização:** maio 2026

---

## Sobre o projeto

TheraTrials Oncology é uma PWA estática (HTML + JS vanilla, sem build step) que reúne **421 ensaios clínicos** distribuídos em **39 categorias**, com schema padronizado de **40 campos por estudo** (intervenção, dose, fase, endpoints, resultados-chave, biomarcadores, NCT/DOI etc.).

A plataforma foi concebida para o fluxo real de um médico nuclear / oncologista clínico em momentos de decisão: tumor board, segunda opinião, conferência de elegibilidade, ensino para residentes. O foco editorial é o **teranóstico** (próstata, NETs, HCC, MIBG, I-131, novos α-emissores), com cobertura plena de imunoterapia 1L, drivers moleculares e perioperatório (NSCLC, mama HER2+/HR+/TNBC).

### Números atuais

| Métrica | Valor |
|---------|-------|
| Ensaios clínicos analisados | **421** |
| Categorias terapêuticas | **39** |
| Ensaios ativos no Brasil | **79** (20 áreas tumorais) |
| Guidelines internacionais | **26** (EANM, SNMMI, ATA, IAEA, ACR) |
| Dossiês de radiofármacos | **7** páginas completas |
| Ferramentas clínicas | **12** (AJCC, CTCAE, calculadoras, BCLC, iRECIST) |
| Páginas HTML | **27** |

---

## Estrutura

```
site/
├── index.html                     # Home · mapa da plataforma
├── database.html                  # 421 estudos · 39 categorias · favoritos · citações
├── explorer.html                  # TheraTrials Explorer · pipeline global RLT (ClinicalTrials.gov)
├── ensaios-clinicos.html          # 79 ensaios ativos no Brasil · recrutamento aberto
├── tumor-boards.html              # Visão por tumor · próstata, pulmão, mama, NET, HCC
├── modalidades.html               # Visão por modalidade terapêutica
├── ferramentas.html               # AJCC TNM · CTCAE v6.0 · PSMA · PET/CT · iRECIST · BCLC · calculadoras
├── fundamentos.html               # Educacional · como funcionam ensaios clínicos
├── guidelines.html                # 26 guidelines internacionais
├── guideline-detail.html          # Detalhe expandido de cada guideline (hash-based routing)
├── radiofarmacos.html             # Hub dos 7 dossiês de radiofármacos
├── lu-psma.html                   # ¹⁷⁷Lu-PSMA-617 · Radioligand therapy
├── lu-dotatate.html               # ¹⁷⁷Lu-DOTATATE · PRRT
├── ra-223.html                    # ²²³Ra-Cloreto · metástases ósseas
├── y90.html                       # ⁹⁰Y-Microesferas · TARE
├── mibg.html                      # ¹³¹I-MIBG · neuroblastoma / feocromocitoma
├── iodo-131.html                  # ¹³¹I-Iodeto · radioiodoterapia
├── novos-alfa.html                # Novos α-emissores · ²²⁵Ac, ²¹²Pb, ¹⁶¹Tb
├── eventos.html                   # Próximos eventos científicos (em construção)
├── newsletter.html                # Newsletter (em construção)
├── tracker.html                   # Radiopharmaceutical therapy tracker
├── dashboard-analise.html         # Dashboard de análise interna
├── about.html                     # Sobre · missão · metodologia editorial
├── offline.html                   # PWA fallback offline
├── termos-uso.html                # Termos de uso
├── privacidade.html               # Política de privacidade · LGPD
├── direitos-autorais.html         # Direitos autorais · atribuição
├── manifest.json                  # PWA manifest
├── sw.js                          # Service worker · cache strategies
├── deploy-pwa.ps1                 # Script de deploy
├── assets/
│   ├── css/
│   │   ├── theratrials.css        # Estilo global (629 linhas)
│   │   └── radiofarmaco.css       # Estilo dos dossiês de radiofármaco (506 linhas)
│   ├── js/
│   │   ├── data.js                # 421 estudos · schema 40 campos (minificado)
│   │   ├── trials_br.js           # 79 ensaios ativos no Brasil
│   │   ├── guidelines-data.js     # 26 guidelines · análise expandida
│   │   ├── cross-links.js         # Cross-linking bidirecional radiofármacos ↔ guidelines
│   │   ├── common.js              # Filtros · favoritos · export · tema
│   │   └── pwa-install.js         # Banner de instalação PWA
│   ├── data/
│   │   ├── explorer.json          # Pipeline RLT global (ClinicalTrials.gov)
│   │   ├── explorer.js            # Explorer data loader
│   │   ├── tracker.json           # Radiopharmaceutical therapy tracker data
│   │   └── tracker.js             # Tracker data loader
│   └── img/                       # 66 imagens · logos, ícones PWA, splash screens, diagramas
├── scripts/                       # 18 scripts Python · curação, pipeline ClinicalTrials.gov
│   ├── fetch_trials.py            # Fetch ClinicalTrials.gov API
│   ├── fetch_brazil_trials.py     # Fetch ensaios ativos no Brasil
│   ├── curate_trials.py           # Pipeline de curação de estudos
│   ├── fix_accents.py             # Correção automática de acentuação PT-BR
│   ├── add_crosslinks.py          # Inserção de cross-links nos radiofármacos
│   └── ...                        # + 13 scripts auxiliares
└── .github/workflows/
    ├── bump-sw-version.yml        # Auto-bump CACHE_VERSION no sw.js a cada push
    ├── update-tracker.yml         # Refresh mensal do tracker (ClinicalTrials.gov)
    └── update-explorer.yml        # Refresh mensal do explorer (ClinicalTrials.gov)
```

---

## Funcionalidades principais

### Database (421 estudos)
- Busca full-text com filtros por categoria, fase, modalidade, biomarcador
- Cards-resumo com expansão em modal `<dialog>` nativo
- Favoritos persistentes (localStorage)
- Export de citações (clipboard)
- 40 campos padronizados por estudo

### TheraTrials Explorer
- Pipeline global de radioligantes terapêuticos
- Dados do ClinicalTrials.gov via API (refresh mensal automatizado)
- Filtros por isótopo, alvo molecular, fase, status, sponsor, presença no Brasil
- Export CSV

### Ensaios clínicos ativos no Brasil
- 79 estudos com recrutamento aberto
- 20 áreas tumorais
- Geolocalização por centro de pesquisa

### Guidelines (26 documentos)
- EANM, SNMMI, ATA, IAEA, ACR, NANETS
- Análise expandida: escopo, indicações, pontos-chave, radiofármacos, aspectos práticos, limitações
- Cross-linking bidirecional com dossiês de radiofármacos
- Navegação sequencial (anterior/próximo)
- TOC lateral colapsável

### Dossiês de radiofármacos (7 páginas)
- ¹⁷⁷Lu-PSMA-617, ¹⁷⁷Lu-DOTATATE, ²²³Ra-Cloreto, ⁹⁰Y-Microesferas, ¹³¹I-MIBG, ¹³¹I-Iodeto, Novos α-emissores
- Mecanismo de ação, farmacologia, dosimetria, ensaios-chave, perspectivas
- Diagramas de mecanismo (SVG inline)
- Cross-links para guidelines relacionados

### Ferramentas clínicas (12)
- AJCC TNM 8ª edição (cards interativos + modal)
- CTCAE v6.0 (categorias expandidas)
- Calculadoras: atividade Lu-PSMA, cronograma de ciclos, decaimento radioativo
- PSMA-RADS, Deauville, Lugano, iRECIST, BCLC, Liver-RADS

### Tumor boards
- Visão integrada por tipo tumoral
- Próstata, pulmão, mama, NET, HCC, tireoide

---

## Identidade visual

| Elemento | Valor |
|----------|-------|
| **Background** | Graphite `#0E0F12` |
| **Accent primário** | Amber `#FF8400` |
| **Accent secundário** | Teal `#0EA5B7` |
| **Texto** | Off-white `#F5F6F7` |
| **Texto secundário** | Stone `#8E949C` |
| **Display font** | Outfit |
| **Body font** | Inter |
| **Mono font** | JetBrains Mono |
| **Ícones** | Lucide |
| **Conceito** | orbital · evidência como ferramenta clínica |

---

## Stack técnico

- **HTML5 estático** — sem build, sem framework, sem bundler
- **JavaScript vanilla** — ES5 compatível, sem dependências de runtime
- **CSS custom properties** — design system consistente
- **PWA completa** — manifest, service worker, splash screens iOS, offline fallback
- **Lucide** — iconografia SVG
- **GitHub Actions** — 3 workflows automatizados (cache bump, tracker, explorer)
- **Python 3** — scripts de curação e pipeline ClinicalTrials.gov
- **Umami Analytics** — analytics privacy-friendly

---

## Como rodar localmente

```bash
# Servidor local (recomendado)
cd site
python -m http.server 8080
# Acessar http://localhost:8080/
```

---

## Convenções de design

- **Listas detalháveis:** grade de cards-resumo + modal `<dialog>` nativo
- **Modal:** fecha via botão X, tecla `Esc` (nativa), clique no backdrop
- **Lucide:** `lucide.createIcons()` em try/catch, sempre após `showModal()`
- **Schema dos estudos:** 40 campos imutáveis (não alterar sem versão major)
- **Dados:** nunca inventar DOIs, NCTs, links, sociedades ou datas
- **Idioma:** PT-BR médico-científico em todo o conteúdo
- **Arquivos >100KB:** editar via scripts Python (não usar editors que truncam)

---

## Roadmap

- [x] **v1.0** — 144 estudos, 17 categorias, 6 dossiês de radiofármaco, ferramentas clínicas, 14 ensaios BR
- [x] **v1.1** — Expansão para 311 estudos, 34 categorias, TheraTrials Explorer, tracker, PWA completa
- [x] **v1.2** — 421 estudos, 39 categorias, 79 ensaios BR, 12 ferramentas, fundamentos expandidos
- [x] **v1.3** — 26 guidelines internacionais com análise expandida, cross-linking bidirecional, dossiê I-131, eventos e newsletter (em construção), correção de acentuação PT-BR
- [ ] **v1.4** — Conteúdo de eventos científicos e newsletter ativa
- [ ] **v2.0** — Modo claro · quiz/flashcards · BibTeX/RIS export

---

## Licença e uso

Conteúdo de uso **educacional** para profissionais de saúde. Não substitui diretrizes oficiais, leitura primária dos artigos, julgamento clínico individualizado ou prescrição médica. Decisões assistenciais permanecem responsabilidade do médico assistente.

Reprodução comercial não autorizada é vedada. Citações em contexto educacional são permitidas mediante atribuição. Ver [Termos de uso](termos-uso.html) e [Direitos autorais](direitos-autorais.html).

---

## Contato

**Dr. Marcos Oliveira** — Médico nuclear · PET/CT · teranóstico · oncologia  
Email: marcosmdsoliveira@gmail.com

---

© 2026 TheraTrials Oncology · uso educacional · não substitui diretrizes oficiais ou leitura primária
