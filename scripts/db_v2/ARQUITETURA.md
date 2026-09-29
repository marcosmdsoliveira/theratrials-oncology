# Database v2 — arquitetura clínica e de dados (PROPOSTA)

Status: **arquitetura APROVADA (28/set/2026); fundação técnica implementada (registro 1.0). Nenhum card migrado.** Nenhum card migrado; `data.js`, `app-data/`,
`secondary-cards.js` e frontend intocados. Registro de campos: `registry_v2.json` e JSON Schema `schema_record_v2.json` (ambos gerados por
`registry_v2.py`). Resultado do teste com cards reais: seção 9 (os artefatos brutos do teste ficaram fora do repositório).

---

## 1. Diagnóstico semântico do schema v1

Base: `data.js` em `4b25f18` (503 cards, 40 categorias). Contagens feitas no próprio arquivo.

### 1.1 Achados estruturais

| # | Achado | Evidência |
|---|---|---|
| D1 | O schema é plano: 40 campos de texto livre, iguais para todo estudo | todos os campos são `str` (exceto `ano_pub`, `tumors`, `modalities`) |
| D2 | `radiofarmaco` virou "intervenção" | 292 cards sem radionuclídeo usam o campo (ex.: `D-VRd`, `Sunitinib adjuvante`, `T-DXd 5,4 mg/kg q3w`); o próprio frontend já o rotula "Intervenção" (`compareFields`, modal com `isRadioStudy`) e `modalidades.html` classifica por regex sobre ele |
| D3 | `cumul` mistura 6 conceitos | vazio 338; atividade (GBq/mCi/kBq) 55; duração/nº de ciclos 44; marcador de ausência em texto ("Variável", "Não publicado") 30; dose de fármaco 10; dose RT em Gy 9; **BED/EQD2 9** (sem dizer se reportado ou calculado); outros 8 |
| D4 | `preparo` traz conteúdo que NÃO vem do estudo | vazio 311; **"Prática de classe…" em 79 cards** (orientação genérica, sem fonte do ensaio); texto do protocolo 109; ausência em texto 4 |
| D5 | `status` mistura 4 eixos | 39 valores distintos: estágio da evidência (Publicado/Apresentado/Em andamento), veículo (ASCO 2026, LBA…), regulatório ("aprovado pelo FDA"), desfecho ("negativo", "primário não atingido") e integridade ("Em revisão editorial") |
| D6 | `fase` mistura fase, desenho e geografia | 228 valores distintos ("Fase 3, asiática, randomizada, aberta"); `filters.phases` herda essa sujeira |
| D7 | `linha` mistura cenário e linha | "Adjuvante", "2L+", "mCRPC pós-ARPI pré-taxano", "Alto risco (consolidação)"; 20 cards sem o campo |
| D8 | Endpoints são strings | `primario` com HR em 327, IC em 206, p em 312 cards — mas sem braço, população, método de avaliação, timepoint ou maturidade estruturados; 257 `secundario` trazem OS/PFS/ORR como texto. Foi assim que o SINDAS chegou com a ordem dos braços ambígua |
| D9 | "—" significa pelo menos cinco coisas | 952 ocorrências de "—" + "por publicar" 69, "em andamento" 65, "não informado" 62, "não descrito" 61, "não aplicável" 22, "variável" 14… no mesmo campo, sem distinção entre "não se aplica", "não relatado", "ainda não existe" e "não curado" |
| D10 | `acron` não é sigla | mediana de 74 caracteres: é o título de exibição; a sigla está em `estudo` |
| D11 | `molecular` × `biomarc` se sobrepõem | seleção molecular, biomarcador de acompanhamento (PSA, CEA) e critério PET espalhados nos dois |
| D12 | `analises` mistura conjunto de análise e histórico de publicação | "ITT primária. 5-yr update Larkin 2023"; "Fase 1 reportada SNMMI 2024" |
| D13 | `impacto_reg` mistura regulatório, diretriz e importância histórica | "FDA Jun/2022 … Categoria 1 NCCN. Compete com axi-cel" |
| D14 | Nem todo registro é ensaio | ≈39 cards não são ensaio: diretrizes (ATA 2025, ENETS/ESMO), meta-análises, coortes retrospectivas, classificação molecular (WHO, ppgl_11), estudos diagnósticos (FES-PET, DOTATATE-PET) — forçados no mesmo formulário |
| D15 | Metadados de curadoria dispersos | `grau_confianca`, `fonte_principal`, `status_curadoria`, `ultima_revisao` em só 3 cards; proveniência real vive fora (`_db_proveniencia_p0.jsonl`) |
| D16 | Modalidade não é inferível do texto | o classificador por léxico marcou CheckMate 76K como radioligante e ANBL1531 como terapia celular; `studyModality()` do frontend é heurístico; `modalities[]` existe em só 48 cards |
| D17 | Tipos inconsistentes | `ano_pub` string em 20 cards, 0 em 23 (convenção de card de desenho) |

### 1.2 Campo a campo

Legenda da ação: **M** manter no core · **R** renomear · **D** dividir · **Mo** mover para módulo · **Dv** tornar derivado · **X** depreciar.

| Campo v1 | Preenchido¹ | Significado real hoje | Faz sentido em | Sem sentido em | Mistura conceitos? | Ação |
|---|---|---|---|---|---|---|
| `uid` | 503 | chave estável | todos | — | não | **M** (imutável) |
| `estudo` | 503 | nome curto/sigla | todos | — | não | **R** `identity.short_name` |
| `acron` | 503 | título de exibição | todos | — | não | **R** `identity.display_title` |
| `nct` / `nct_url` | 492 / 451 | registro | ensaios | diretriz, classificação | não | **D** `identity.registrations[]`; url **Dv** |
| `sponsor` | 501 | patrocinador | todos | — | às vezes grupo cooperativo + indústria | **M** + `sponsor_class` |
| `fase` | 502 | fase + desenho + geografia | ensaios | não-ensaios | **sim** | **D** `identity.phase` (enum) + `design.*` |
| `desenho` | 503 | narrativa do desenho | todos | — | sim (alocação, cegamento, braços, população) | **D** `design.*`; narrativa curta opcional |
| `centros` | 491 | nº de centros/países | ensaios | diretriz | não | **M** `identity.centers` |
| `periodo` | 471 | recrutamento ou publicação | ensaios | — | às vezes ("publicação Lancet Oncol Out/2020") | **M** `identity.enrollment_period` |
| `indicacao` | 503 | doença + cenário + linha | todos | — | sim | **D** `population.disease/histology/setting/line` |
| `incl` / `excl` | 495 / 420 | critérios principais | ensaios | diretriz | não | **M** listas curtas (USEFUL) |
| `estrat` | 397 | fatores de estratificação | randomizados | braço único, coorte | não; "—" em 90 | **M** `design.stratification[]` (estado N/A em braço único) |
| `basal` | 461 | características basais | ensaios/coortes | diretriz | não | **M** `population.baseline` |
| `n` | 500 | N + distribuição por braço + coortes | todos | — | sim | **D** `design.sample_size` + `arms[].n` |
| `molecular` | 476 | critério de seleção molecular/PET | alvo, IO, RLT | QT pura | sim, com `biomarc` | **D** `population.biomarker_selection[]` + módulo |
| `biomarc` | 449 | biomarcador de seleção **ou** de acompanhamento | idem | idem | **sim** | **D** idem; acompanhamento (PSA/CEA) sai |
| `radiofarmaco` | 438 | intervenção (292 não-radio) | RLT (nome real) | todo não-radio | **sim** | **D** `design.arms[].interventions` + `<módulo>.agent/target` |
| `esquema` | 495 | dose, ciclos, via, duração | todos | — | sim | **D** `arms[].interventions` (+ módulo: atividade, Gy) |
| `cumul` | 165 | atividade/dose/duração/BED | RLT (atividade), RT (dose) | IO, alvo, ADC, endócrina | **sim (6)** | **D/Mo** `radionuclide_therapy.cumulative_activity`, `radiotherapy.dose`; BED só se reportado; resto vira estado |
| `comparador` | 459 | braço controle | randomizados | braço único | não | **Dv** de `design.arms[role=control]` + `design.control` |
| `estatistica` | 489 | hipótese, poder, α, endpoint primário | randomizados | coorte descritiva | sim ("ORR." sozinho) | **D** `design.hypothesis` + `design.statistical_plan` |
| `analises` | 480 | conjunto de análise + histórico | todos | — | **sim** | **D** `endpoints[].analysis_set` + `analyses[]` |
| `primario` | 503 | endpoint + resultado em texto | todos | — | sim (definição + valores + HR) | **D** `endpoints[hierarchy=primary]` |
| `secundario` | 475 | idem para secundários | todos | — | sim | **D** `endpoints[hierarchy≠primary]` |
| `subgrupo` | 425 | subgrupos em texto | randomizados | braço único pequeno | sim (pré-especificado × exploratório) | **D** `subgroups[]` |
| `tox_g3` | 457 | toxicidade ≥G3 (222 por braço) | todos com intervenção | diretriz, classificação | sim (≥3, G4/G5, SAE) | **D** `safety.*` |
| `tox_interesse` | 448 | AESI | todos com intervenção | idem | sim | **Mo** painéis de AESI dos módulos → `safety.key_toxicities[]` |
| `impacto_reg` | 502 | regulatório + diretriz + importância | todos | — | **sim (3)** | **D** `interpretation.regulatory[]`, `guideline_impact[]`, `clinical_impact` |
| `limit` | 489 | limitações | todos | — | às vezes inclui maturidade | **M** `interpretation.limitations[]` |
| `ref` | 503 | citação formatada | todos | — | às vezes cita 2 publicações | **Dv** de `identity.represented_publication` + `publications[]` |
| `preparo` | 192 | preparo do paciente/pré-medicação/"prática de classe" | RLT, CAR-T, TCE | IO, alvo, QT, endócrina | **sim** | **Mo** módulos (RLT/celular/biespecífico); "prática de classe" **X** do card (vai para o dossiê do radiofármaco) |
| `status` | 503 | 4 eixos (D5) | todos | — | **sim** | **D** `evidence_stage` + `registry_status` + `outcome` + `regulatory[]` + `review.editorial_status` |
| `linha` | 483 | cenário + linha (D7) | tratamento | diagnóstico, diretriz | sim | **D** `population.setting` + `population.line` |
| `takehome` | 482 | mensagem editorial | todos | — | não | **M** `interpretation.takehome` (origin editorial) |
| `resultado_chave` | 455 | resumo numérico | com resultado | card de desenho | não | **M** `interpretation.key_result`; números validados contra `endpoints[]` |
| `titulo_full` | 486 | título do artigo ou do registro | todos | — | não | **Dv** da publicação/registro |
| `pubmed_url` / `ano_pub` | 451 / 480 | publicação representada | publicados | card de desenho | não | **Dv** de `represented_publication` |
| `category_*` | 503 | categoria + cor/nome repetidos | todos | — | não | `category_id` **M**; nome/cor **Dv** de `categories[]` |
| `tumors` / `modalities` | 87 / 48 | taxonomias parciais | — | — | não | substituídos por `identity.tumors[]` e `modules[]` |
| `fonte_principal`, `grau_confianca`, `status_curadoria`, `ultima_revisao` | 3 | curadoria ad hoc | — | — | — | **X** → proveniência + `review.*` |

¹ preenchido = diferente de vazio e de "—".

### 1.3 Usos semanticamente inadequados (tipo SINDAS/`cumul`)

1. **`cumul` com BED** (9 cards): valor dependente de α/β, sem marcar se foi reportado ou calculado.
2. **`cumul` com duração** ("Até 24 meses de durvalumab", "Plano de 17 ciclos"): o rótulo exibido é "Dose cumulativa típica".
3. **`preparo` com "prática de classe"** (79 cards): recomendação genérica exibida como se fosse do ensaio.
4. **`radiofarmaco` em estudo sem radiofármaco** (292): o dado está certo, o nome do campo está errado; o frontend compensa com `isRadioStudy`.
5. **`status` com juízo de resultado** ("— negativo"): o desfecho deveria derivar do primário estruturado.
6. **`biomarc` com biomarcador de acompanhamento** (PSA, CEA, Tg): não é critério de seleção.
7. **`analises` com histórico de publicação**: a relação entre publicações deveria estar em `analyses[]`.
8. **Texto de ausência dentro do valor** ("Não publicado.", "Variável"): indistinguível de conteúdo.

---

## 2. `oncology_core`

Detalhe campo a campo (tipo, nível, automação, origem v1) em `registry_v2.json`. Resumo:

### 2.1 Tipo de registro

`record_type`: `trial` · `trial_cohort` (coorte de basket/plataforma com card próprio) · `pooled_analysis` ·
`meta_analysis` · `cohort_study` · `case_series` · `diagnostic_study` · `guideline` · `molecular_classification` ·
`translational`.

**O `record_type` define um PERFIL de obrigatoriedade** (`profiles` em `registry_v2.json`). O v0.1 obrigava todo
registro a ter braços, endpoints e segurança de ensaio; o teste mostrou ≈20 campos `not_applicable` forçados em
diretriz e em FES-PET. No v0.2:
- `trial` / `trial_cohort`: core inteiro (`trial_cohort` exige ainda `parent_trial` e `safety.population`).
- `cohort_study` / `case_series`: sem randomização/cegamento; exige `design.observational` (exposição, comparador,
  ajuste de confundimento). Um registro por série publicada — agregação de várias séries vai para o dossiê do agente.
- `diagnostic_study` / `meta_analysis`: módulo `diagnostic` + endpoints de acurácia; sem braços nem segurança.
- `guideline`: bloco `guideline{}` (emissor, versão, data, metodologia, status current/superseded, recomendações
  com força e nível). Um registro por documento-versão.
- Regra automática: `allocation=single_arm` ⇒ máscara, razão, estratificação, crossover e controle viram
  `not_applicable` sem curadoria.

### 2.1b Módulos com papel e escopo por braço

O teste derrubou a ideia de módulo "do card inteiro": ESOPEC tem RT só no controle; TRANSFORM compara CAR-T com
QT + ASCT; ESTIMABL e DOSISPHERE **randomizam** exatamente o que o módulo guarda (atividade, dosimetria); em
ASCENT-04 o pembrolizumabe está nos dois braços. Por isso:

```json
"modules": [
  {"module": "adc",            "role": "tested",   "arm_ids": ["exp"]},
  {"module": "immunotherapy",  "role": "backbone", "arm_ids": "all"},
  {"module": "chemotherapy",   "role": "control",  "arm_ids": ["ctl"]},
  {"module": "endocrine",      "role": "context",  "arm_ids": "all"}
]
```

- **Dois níveis**: atributos **do agente** (alvo, payload, radionuclídeo, atividade, dose, esquema) moram na
  intervenção do braço (`design.arms[].interventions[].attributes`); **contexto do estudo** (seleção por PD-L1, IO
  prévia, seleção por imagem) mora no módulo. Isso resolve STRIDE (CTLA-4 dose única + PD-L1 contínuo) e os estudos
  que randomizam dose/atividade.
- `role=context` traz só campos de população (ex.: exposição prévia a iCDK4/6 no DESTINY-Breast06, sem terapia
  endócrina administrada).
- Cada intervenção tem `role` (investigational/backbone/control/supportive) e `phase` (neoadjuvant, adjuvant,
  induction, bridging, conditioning, consolidation, maintenance).
- `design.control = {type, backbone}` cobre "placebo sobre backbone ativo" (PAOLA-1, MONALEESA-3, AGILE).
- `design.comparisons[]` substitui a hipótese única: HIMALAYA tem superioridade (STRIDE × sorafenibe) **e** não
  inferioridade com margem (durvalumabe × sorafenibe); cada endpoint aponta seu `comparison_id`.
- A escolha do investigador (`choice {options, distribution}`) subiu para o braço no core: o controle do PROfound é
  troca de ARPI e o do CARTITUDE-4 é DPd/PVd — não é quimioterapia.
- `design.arms[].proceeded_to_planned_therapy[]` generaliza "quem chegou à cirurgia / infusão / ASCT / RT" —
  decisivo para ler ITT em CAR-T e perioperatório.

### 2.2 Blocos

| Bloco | Conteúdo |
|---|---|
| **Identidade** | `uid` (imutável), `record_type`, `short_name`, `display_title`, `acronym`, `registrations[]` (NCT, ISRCTN, EudraCT, jRCT, ChiCTR…), `phase` (enum), `sponsor`/`sponsor_class`, `centers` (n, países, **participação do Brasil**), `enrollment_period`, `represented_publication` (PMID, DOI, ano, periódico, `analysis_ref`), `publications[]`, `category_id`, `tumors[]`, `evidence_stage`, `registry_status` |
| **População** | `disease`, `histology`, `setting` (enum), `line` {min, max}, `disease_extent`, `risk_classification[]` (genérico: INRG, R-ISS, ELN, IMDC, BCLC, CHAARTED…), `biomarker_selection[]` {biomarcador, regra required/enriched/excluded, assay, cutoff, amostra}, `prior_therapy[]`, `key_inclusion[]`, `key_exclusion[]`, `performance_status`, `baseline` |
| **Desenho** | `structure` (single_cohort/basket/umbrella/platform/factorial), `cohorts[]`, `allocation`, `masking`, `control`, `hypothesis` (superioridade/não inferioridade), `ratio`, `arms[]` {arm_id, rótulo, papel, n, `interventions[]` {agente, classe, dose, via, esquema, duração}}, `sample_size`, `stratification[]`, `crossover`, `statistical_plan` |
| **Endpoints** | `endpoints[]` (2.3) e `subgroups[]` |
| **Segurança** | `grade3plus_any[]`, `serious_ae[]`, `discontinuation_ae[]`, `dose_modification[]`, `treatment_related_deaths[]`, `key_toxicities[]` {termo, escopo any/≥3/G5, braço, %, adjudicada, `aesi_of`} |
| **Interpretação** | `key_result`, `takehome`, `outcome` (derivado do primário), `limitations[]`, `clinical_impact`, `regulatory[]` {agência, status, data, indicação}, `guideline_impact[]` |
| **Revisão** | `last_reviewed`, `editorial_status` (active/in_review/withheld), `integrity_hold` (do pipeline) |

`evidence_stage` (enum): `registered` · `ongoing` · `presented` · `published_interim` · `published_primary` ·
`published_final` · `published_long_term`. Congresso e regulatório **não** entram aqui.

### 2.3 Endpoints estruturados

Um objeto por (endpoint × população × análise):

```json
{
  "endpoint_id": "e1",
  "code": "PFS",
  "definition": "RECIST 1.1, BICR",
  "hierarchy": "primary",
  "cohort_id": null,
  "population": "ITT",
  "analysis_set": "ITT",
  "assessment": "BICR",
  "timepoint": {"type": "median"},
  "arms_values": [
    {"arm_id": "exp", "value": 20.2, "unit": "months", "ci95": [17.9, 22.5], "n": 68},
    {"arm_id": "ctl", "value": 12.5, "unit": "months", "ci95": [11.6, 13.4], "n": 65}
  ],
  "effect": {"measure": "HR", "value": 0.22, "ci95": [0.17, 0.46], "p": "<0.001", "sided": 2,
             "significance": "met"},
  "maturity": {"analysis_type": "interim", "data_cutoff": null, "follow_up_median_months": 23.6,
               "events": null, "information_fraction": 0.68},
  "analysis_ref": "a1",
  "state": "present", "origin": "reported", "prov": "p17"
}
```

- `code` é vocabulário controlado: PFS, rPFS, OS, DFS, EFS, RFS, MFS, iDFS, ORR, CR, CRh, pCR, DoR, DCR, TTP, CBR,
  PSA50, MRD, LC, TTUP, QoL, SENS/SPEC/PPV/NPV/DR (diagnóstico)… Um estudo carrega **só os que tem**; nenhum é
  obrigatório.
- Ajustes do v0.2 (vindos do teste):
  - `ci = {level, low, high}` no lugar de `ci95` (VISION reporta IC 99,2 %; COMRADE e HYPO-RT-PC, IC 90 %);
  - valor **qualificado** `{op: = | ≈ | < | > | range | not_reached, value, low, high}` ("não atingida", "~0,71",
    "300–600 kBq/kg");
  - `definition` e `response_criteria` (RECIST 1.1, mRECIST, PCWG3, Lugano, IMWG, ELN 2022…) — obrigatórios para
    compostos (EFS da LMA, pCR ypT0/Tis ypN0, sucesso de ablação, FFS);
  - `analysis_method` (não ajustado, RPSFT, IPCW) — OS do PROfound;
  - `comparison_id`, `cohort_id`, `analysis_set {name, n}`, `source_ref` (congresso × revisado por pares);
  - `maturity` com `information_fraction` e `boundary_p` (PSMAddition: 74,4 % de informação, limiar p = 0,0092).
- **Regra subgrupo × endpoint**: população definida por biomarcador com valores por braço (medianas HRD+ do PAOLA-1,
  HER2-ultralow do DESTINY-Breast06) vai em `endpoints[]` com `population=<biomarker id>` e hierarquia própria;
  `subgroups[]` fica só para efeito de forest plot.
- `hierarchy`: `primary` · `co_primary` · `key_secondary` · `secondary` · `exploratory` · `post_hoc`.
- Braços são referenciados por `arm_id`, **nunca por posição no texto** — elimina a ambiguidade de ordem do SINDAS.
- Taxas em landmark usam `timepoint {type: "landmark", months: 6}`; medianas, `{type: "median"}`.
- "Resultado principal" no card = `endpoints[hierarchy ∈ {primary, co_primary}]` da análise representada.

---

## 3. Estados semânticos

| Estado | Significado | Armazenamento | Exibição no card | Comparação |
|---|---|---|---|---|
| `present` | há valor; `origin` = `reported` · `derived` · `editorial` | `{"state":"present","origin":…,"v":…,"prov":…}` | o valor; `derived` ganha selo "calculado pelo TheraTrials" | valor |
| `not_reported` | fonte(s) conferida(s) e silenciosa(s) | + `checked_sources[]` | ESSENTIAL: "Não relatado na publicação"; demais: oculto | "não relatado" |
| `not_applicable` | não se aplica ao desenho | só o estado | **oculto** | "n/a" |
| `unknown` | ainda não curado | ausência da chave = `unknown` | **oculto** (nunca afirmado) | "—" com dica "não curado" |
| `not_yet_available` | existirá depois | + `expected` opcional (ex.: conclusão primária 2030-09) | "Aguardando dados (previsão: …)" | "aguardando" |
| `withheld_due_to_integrity` | havia valor; suprimido | + `decision_ref` | faixa "Em revisão editorial" | "em revisão" |

Regras:
- **"—" nunca é armazenado.** É só renderização legada.
- **`not_reported` exige texto completo conferido.** Se só o resumo foi lido, o estado é `unknown` (ESOPEC: "não
  informado no resumo" não é "não relatado").
- `not_yet_available` é o estado certo para OS imatura (COMRADE, ASCENT-04, DESTINY-Breast06) — hoje é silêncio.
- Ausência da chave equivale a `unknown` — o v2 não obriga preencher estado em campo não curado (mantém o payload pequeno).
- Conflito é **atributo**, não estado: `conflict` ∈ `none` · `explained` · `within_source_conflict` · `cross_source_conflict`,
  com `value_candidates[]` (um por ocorrência, cada um com locator), `resolution` e `conflict_ref` para
  `db_conflitos_fonte.json`. Vale para qualquer campo, inclusive editorial e de identidade.
  Ex.: OS do braço só-TKI do SINDAS = `present`, `reported`, `conflict: within_source_conflict`,
  `value_candidates: [{17.4, abstract}, {17.6, Results}]`; o renderer mostra os dois com o selo
  "divergência na publicação". (O teste v0.1 marcou isso como irrepresentável porque o `registry_v2.json` ainda não
  trazia o atributo — só este documento. Corrigido no v0.2.)
- Exportação legada (`data.js`): `not_reported` → "Não relatado."; `not_yet_available` → "Aguardando dados.";
  `withheld` → aviso editorial; `not_applicable`/`unknown` → "—" (que o frontend atual já oculta via `fieldMeaningful`).

---

## 4. Módulos

Princípio: **módulo adiciona contexto e um painel de AESI; resultados continuam no core.** Eficácia vai para
`endpoints[]` e toxicidade para `safety.key_toxicities[]` com `aesi_of=<módulo>`. Isso evita duplicação e mantém a
comparação entre estudos uniforme. Um estudo pode ter vários módulos; nenhum é exclusivo.

| Módulo | Quando | Campos ESSENTIAL | Painel de AESI |
|---|---|---|---|
| `radionuclide_therapy` | RLT, RAI, Ra-223, MIBG, TARE, radioimunoconjugado | delivery, agent, radionuclide (β/α/cadeia α), activity_per_administration (valor ou faixa), cycles {min, max, condição}; **condicionais a ligante sistêmico**: target, imaging_selection {traçadores, escore} | hematológica, renal, salivar, SMD/LMA tardia, REILD e pneumonite actínica (TARE) |
| `adc` | conjugado anticorpo-fármaco | target, payload_class, target_expression (**lista** por coorte de expressão), prior_same_target | ILD/pneumonite (qualquer, ≥3, G5, adjudicada), ocular **de superfície** separada, neuropatia, estomatite, FEVE se alvo HER2 |
| `immunotherapy` | checkpoint, citocina, BCG, vírus oncolítico, vacina | target e agent **por agente**, pdl1 {assay, score, cutoff, seleção}, prior_io | imAE ≥3, pneumonite, colite, hepatite, endocrinopatias, miocardite |
| `targeted_therapy` | TKI, mAb não-IO, **iCDK4/6, iPARP**, IMiD, menina, IDH, SSA, **biespecífico não-TCE** | target, required_alteration (**condicional**: não se aplica a SSA, iCDK4/6, antiangiogênico), detection {método, amostra, CDx}, prior_targeted_therapy | condicionado a `agent_class` (iPARP → SMD/LMA, anemia, TEV) |
| `ddr_hrd` | contexto BRCA/HRR/HRD | genes, origin {testado em, distingue origem, permitido}, stratified_results — **ativado só** com seleção DDR ou resultado estratificado | — |
| `endocrine` | mama RH+, próstata, supressão ovariana | hormone_context, endocrine_resistance, prior_endocrine, prior_cdk46 (**campos condicionais** mama × próstata) | — |
| `t_cell_engager` | **só** engajadores de célula T (tarlatamabe, teclistamabe, epcoritamabe, tebentafusp) | targets {alvo tumoral, CD3} | SRC e ICANS (ASTCT), infecções, citopenias, hipogamaglobulinemia |
| `cellular` | CAR-T, TCR-T, TIL, TCTH **alogênico** (por braço) | product_type, target (condicional a CAR-T/TCR) | SRC, ICANS, neurotox. tardia, citopenias prolongadas, infecções, 2ª neoplasia de célula T |
| `radiotherapy` | RT externa, SBRT, braquiterapia | technique, **components[]** {braço, alvo, dose total ou faixa, frações} | por sítio: tórax, pelve (aguda × tardia), SNC |
| `surgery` | cirurgia como parte do tratamento em estudo | procedure (R0, complicações Clavien-Dindo e mortalidade são USEFUL) | — |
| `locoregional` | TACE, HAIC, ablação, HIPEC, intravesical | procedure | — |
| `chemotherapy` | só quando agrega | nenhum ESSENTIAL: regimen_label, agent_class (inclui **hipometilante**), cycles {pré, pós, % completo}, **high_dose** (QT em alta dose + resgate autólogo) | — |
| `diagnostic` | estudo de imagem/diagnóstico | index_test, reference_standard, unit_of_analysis[] | — |

Mudanças do v0.1 para o v0.2 por causa do teste:
- **`bispecific` → `t_cell_engager`.** No MARIPOSA, o gating de CRS/ICANS funcionou, mas o resto do módulo
  (step-up, internação) virou vazio enganoso: amivantamabe (EGFR×MET), ivonescimabe e zanidatamabe são
  biespecíficos de bloqueio, não engajadores. Eles vão para `targeted_therapy`/`immunotherapy` com
  `agent_class=bispecific_antibody`.
- **TCTH autólogo sai de `cellular`.** No HR-NBL1 (BuMel × CEM) a variável randomizada é o regime de alta dose; o
  resgate autólogo é igual nos dois braços. `cellular` fica para produtos celulares; alta dose + resgate vai para
  `chemotherapy.high_dose` (com SOS/VOD e mucosite no painel).
- **TARE não se repete em dois módulos.** Física e dosimetria (Gy por compartimento, vidro × resina, shunt pulmonar)
  ficam em `radionuclide_therapy.absorbed_dose`/`device`; função hepática e BCLC sobem para o core
  (`population.risk_classification[]`), porque HIMALAYA também precisa deles e não é locorregional.
- **PARPi continua sem módulo próprio** (confirmado em PAOLA-1 e PROfound), com três correções: `prior_parpi` sai de
  `ddr_hrd` (vive em `prior_therapy`), o painel de AESI vira condicional à classe e `ddr_hrd.origin` passa a
  distinguir "testado em tecido que não separa germinativo de somático".
- **iCDK4/6 = `targeted_therapy`**; `endocrine` só como contexto/backbone. Em SERENA-6 o iCDK4/6 **continuado** não é
  "prévio".
- **Hipometilante (azacitidina) = `chemotherapy.agent_class=hypomethylating`** — o léxico heurístico o punha em
  terapia-alvo.
- **Cirurgia prévia à randomização não ativa `surgery`**: é `population.prior_therapy` (NIVOPOSTOP, adjuvantes).
- **Hematologia** ganhou valores de cenário (newly_diagnosed, relapsed_refractory, transplant) e
  `population.fitness`.
- **Pré-medicação/profilaxia exigida pelo protocolo** passou a ter lugar: `interventions[].supportive_care[]`
  (colírio e exame oftalmológico no tisotumabe, profilaxia de TEV no amivantamabe, prednisona com abiraterona). Só o
  que o protocolo exige e muda a prática; "prática de classe" continua fora.

- Basket/plataforma **não é módulo**: é `design.structure` + `design.cohorts[]` + `cohort_id` nos endpoints.

---

## 5. Relevância clínica — ESSENTIAL / USEFUL / SPECIALIZED / DO_NOT_INCLUDE

Critérios: decisão clínica, comparação entre estudos, entender população, magnitude do benefício, segurança,
aplicabilidade. O nível de cada campo está em `registry_v2.json`. Resumo:

| Nível | Core | Módulos | Regra de exibição | Regra de curadoria |
|---|---|---|---|---|
| ESSENTIAL | 38 (parte condicional ao perfil) | 43 (parte condicional) | sempre visível quando `present`; `not_reported` visível | ausência gera item de **backlog** (não inbox) |
| USEFUL | 32 | 42 | visível quando `present` | pode ficar `unknown` indefinidamente |
| SPECIALIZED | 7 | 12 | recolhido ("detalhes") | só extraído quando o curator encontra |

**DO_NOT_INCLUDE** (deliberadamente fora do card):
- "Prática de classe" e orientação de preparo não descrita no estudo → dossiê do radiofármaco (`lu-psma.html` etc.).
- BED/EQD2 **derivado** → ferramenta de cálculo, não o card.
- DAR, detalhes de linker e construção molecular de ADC/biespecífico → dossiê do fármaco.
- Lista completa de critérios de elegibilidade → link para o registro (o card guarda os principais).
- Todos os subgrupos do forest plot → só pré-especificados relevantes ou os que mudam decisão.
- Biomarcadores de acompanhamento (PSA, CEA, Tg) como "biomarcador" → só como endpoint quando forem endpoint.
- Nome/cor da categoria repetidos em cada card → derivados.
- Investigador principal, co-alterações detalhadas, IGRT, tempo aférese→infusão → no máximo SPECIALIZED.

**Categoria não é classificação clínica.** O teste achou três cards em categoria que induz erro: DESTINY-Breast06
(HER2-low/ultralow) em "Mama · HER2+", TROPION-Lung01 (maioria sem driver) em "NSCLC alvo" e dois estudos de
tireoide de baixo risco (ESTIMABL, Nixon) em "tireoide avançado". No v2 `category_id` continua sendo navegação
editorial (human), mas filtros clínicos passam a usar `tumors[]`, `population.*` e `modules[]`.

---

## 6. `reported` × `derived` × `editorial`

- **reported**: valor literal da fonte (com locator).
- **derived**: calculado pelo TheraTrials. Exige:

```json
"derivation": {
  "formula": "BED = n·d·(1 + d/(α/β))",
  "parameters": {"alpha_beta": 10},
  "assumptions": ["α/β = 10 Gy para tumor"],
  "source_fields": ["modules.radiotherapy.dose"],
  "version": "bed@1"
}
```

- **editorial**: texto autoral do TheraTrials (`takehome`, `clinical_impact`, `key_result`). Não é "verificável" contra
  a fonte como um número; seus **números**, sim (regra atual do guard: todo número de `key_result` tem de existir em
  `endpoints[]`).

Regras:
1. Derivado **nunca** substitui reportado; se os dois existem, o reportado é exibido.
2. Derivados permitidos no card: somente os **triviais e sem suposição clínica** — dose por fração, atividade
   cumulativa *planejada* (atividade × ciclos), diferença absoluta entre braços quando ambos os valores são
   reportados. Sempre com selo "calculado".
3. Derivados com parâmetro clínico (BED/EQD2 com α/β, NNT, conversões de unidade com peso) → **não** entram no card;
   ficam nas ferramentas (`ferramentas.html`) com a fórmula exposta.
4. `interpretation.outcome` (positivo/negativo) é derivado de `endpoints[primary].effect.significance` — deixa de ser
   texto livre em `status`.

---

## 7. Proveniência por campo

### 7.1 Modelo

```json
"provenance": {
  "p17": {
    "source": {"type": "publication", "pmid": "35094066", "doi": "10.1093/jnci/djac015", "pmcid": "PMC10248839"},
    "locator": {"section": "Results", "table": null, "figure": null,
                "snippet": "median PFS was 12.5 months … vs 20.2 months (P < .001)"},
    "extraction": "explicit",
    "evidence_confidence": "high",
    "reviewed_at": "2026-09-28",
    "reviewed_by": "verifier|human:<id>",
    "conflict": "none"
  }
}
```

- `source.type`: `publication` · `registry` (CT.gov/ISRCTN) · `registry_results` · `regulatory` (label FDA/EMA) ·
  `guideline` · `congress_abstract` · `human_decision`.
- `extraction`: `explicit` · `derived` · `human_confirmed` (reuso direto da taxonomia do pipeline v1).
- `evidence_confidence`: `high` (literal, fonte primária, sem conflito) · `moderate` (literal em fonte secundária ou
  abstract sem texto completo) · `low` (inferido; nunca publicado sem humano).
- Proveniência referenciada por id (`prov`) em cada valor — um snippet serve a vários campos.

### 7.2 Duas camadas

| Camada | Onde | Conteúdo | Quem lê |
|---|---|---|---|
| **Canônica (interna)** | `db/v2/records/<uid>.json` (1 arquivo por card; versionado) | tudo: valores, estados, derivações, proveniência, conflitos, histórico de decisão | pipeline, curator, verifier, validadores |
| **Exportada (pública)** | `data.js`/`app-data/data.json` legados + futura projeção v2 enxuta | valores + estado + `origin` + selo de conflito + **fonte resumida** (PMID + seção); sem snippets | site e app |

Motivo da separação: a proveniência completa multiplicaria o payload (hoje 1,7 MB) e o app instalado **baixa todos os
datasets do manifest** (`remote-data-loader.js`, `syncAll`), com checagem de SHA-256. Snippets ficam em arquivo por
card, carregado sob demanda quando o usuário abre "Fontes".

---

## 8. `analysis_signature`

### 8.1 Componentes

| Componente | Exemplo | Papel |
|---|---|---|
| `trial_key` | NCT02035813 | identidade (obrigatório) |
| `cohort` | "endometrial MSI-H/dMMR" | identidade (obrigatório; `null` se coorte única) |
| `population` | ITT · "PD-L1 CPS≥10" · "BRCAm" | identidade (obrigatório) |
| `comparison` | {exp, ctl} (conjunto de arm_ids) | identidade (obrigatório) |
| `endpoint` | PFS | identidade (obrigatório) |
| `summary_measure` + `timepoint` | mediana · taxa em 6 meses | identidade (obrigatório) — sem isso a PFS em 6 meses e a PFS mediana do SINDAS colidem |
| `assessment_method` | BICR · INV | identidade (obrigatório) |
| `analysis_set` | ITT · mITT · PP · safety | identidade (obrigatório) |
| `endpoint_hierarchy` | primary | informativo (emendas de protocolo mudam) |
| `analysis_type` | interim · primary · final · updated · long_term · post_hoc · exploratory | ordenação |
| `data_cutoff` | 2024-03-01 | ordenação (obrigatório para dizer "mais nova") |
| `follow_up_median` | 23.6 m | maturidade |
| `sample_size` / `events` | 133 / 81 | maturidade; alerta se N cai sem explicação |
| `publication_role` | primary_publication · update · final · secondary_analysis · subgroup · qol_pro · safety · translational · pooled · correction | relação editorial |

### 8.2 Regras

- **Mesma análise clínica (linhagem)** ⇔ iguais em `trial_key + cohort + population + comparison + endpoint +
  summary_measure + timepoint + assessment_method + analysis_set`. Em braço único e diagnóstico, `comparison = none`
  (não é inferido: vem do desenho). As publicações diferem só em maturidade.
  - `data_cutoff` igual → **duplicata** (congresso + artigo, ou dois periódicos): mesma evidência.
  - `data_cutoff` posterior → **atualização** (`update`/`final`/`long_term`) — é o caso do KEYNOTE-158 endométrio
    (34990208 → 39847999).
- Muda `population` → **subgrupo** ou **análise secundária** (não substitui a primária).
- Muda `endpoint` → **análise secundária** (OS final publicada à parte, QoL/PRO, segurança).
- Muda `cohort` → **nova coorte** (basket): candidata a card próprio (`trial_cohort`).
- Muda `assessment_method` (BICR × investigador) → mesma linhagem **não**: é análise de sensibilidade.
- Sem `data_cutoff` → a ordenação cai para data de publicação e a relação fica `inferred` (nunca `machine_verified`).

O card representa **uma linhagem**: a do endpoint primário na população primária; o "resultado principal" é a análise
mais madura dessa linhagem. As demais publicações entram em `identity.publications[]` com seu `analysis_ref`.
Isso formaliza o que o pipeline v1 já faz com `classificar_artigo` e a decisão `tipo_analise`.

---

## 9. Teste com cards reais

35 cards (4 lotes estratificados por modalidade), mapeados campo a campo sem alterar nada: amostra de 1.541 mapeamentos de campo (artefato de estudo, fora do repositório). Depois, reteste dos 10 mais
difíceis contra o registro corrigido.

### 9.1 Amostra

| Modalidade | Cards |
|---|---|
| Radionuclídeo | VISION, PSMAddition, NETTER-1, 225Ac-PSMA-617 (Heidelberg), DOSISPHERE-01 (Y-90), COMRADE (Ra-223 + olaparibe), ESTIMABL (131I) |
| ADC | DESTINY-Breast06, TROPION-Lung01, InnovaTV-301, ASCENT-04 (ADC + IO), DESTINY-PanTumor02 BTC (basket) |
| Imunoterapia | KEYNOTE-158 endométrio (coorte de basket), KEYNOTE-522 (perioperatório), HIMALAYA (3 braços), NIVOPOSTOP (IO + QRT pós-cirurgia) |
| Alvo / iPARP / endócrina | LIBRETTO-001, CodeBreaK 200, AGILE (LMA), PAOLA-1, PROfound, MONALEESA-3, SERENA-6, MARIPOSA |
| Biespecífico / celular | DeLLphi-304, CARTITUDE-4, TRANSFORM |
| RT / QT / cirurgia / multimodal | SINDAS, HYPO-RT-PC, KEYNOTE-A18, HR-NBL1 (BuMel), ESOPEC, Nixon (coorte cirúrgica) |
| Não-ensaio | Diretriz ENETS/ESMO, FES-PET (diagnóstico/meta-análise) |

### 9.2 Resultado

| | v0.1 (35 cards) | Reteste dos 10 mais difíceis |
|---|---|---|
| cabe | 0 | 3 (HIMALAYA, TRANSFORM, DESTINY-Breast06) |
| cabe com ajustes | 32 | 5 (+ diretriz ENETS/ESMO, que antes não cabia) |
| não cabe | 3 | 2 (225Ac-PSMA Heidelberg, FES-PET) |

Mapeamento: 649 campos mapeados direto, 609 divididos, 178 descartados, 105 viraram estado. Campos v1 marcados "sem
sentido" com mais frequência: `cumul` (26 de 35), `radiofarmaco` (17), `biomarc` (7), `tox_interesse` (7), `preparo` (5).

**Os 2 que continuam sem caber não são falha do schema, são falha do card**: cada um agrega várias fontes num
registro só (225Ac: quatro séries e um PMID de 2016; FES-PET: aprovação regulatória + guia de uso apropriado da SNMMI
+ dois estudos de acurácia). O v2 exige **um registro por fonte primária**; o conteúdo de síntese pertence a um
dossiê do agente (as páginas `lu-psma.html`, `novos-alfa.html` etc. já cumprem esse papel). Recomendação: desmembrar
esses dois cards em revisão editorial antes de migrá-los — não criar "dossiê" dentro do Database.

### 9.3 O que o teste mudou no schema (v0.1 → v0.3)

1. Módulo com papel e escopo por braço; atributos do agente na intervenção (seção 2.1b).
2. `design.comparisons[]` com hipótese e margem de NI por comparação.
3. `record_type` define perfil de obrigatoriedade; blocos `guideline{}`, `design.observational`, meta-análise.
4. Endpoints: IC de nível variável, valor qualificado (inclusive "só direção"), `definition`, `response_criteria`,
   `analysis_method`, `estimate` para desenho sem braço, valores por nível de fator, `boundary_not_crossed`.
5. Conflito com `value_candidates` no próprio registro (SINDAS agora representável).
6. `bispecific` → `t_cell_engager`; TCTH autólogo → `chemotherapy.high_dose`; TARE sem duplicação; iCDK4/6 e iPARP em
   `targeted_therapy`; hipometilante em `chemotherapy`.
7. Precedência: biomarcador exigido e terapia prévia moram no core; módulos referenciam.
8. `interpretation.outcome` só é derivado com um primário e significância definida; senão é decisão humana
   (o SINDAS seria "negativo" pela PFS em 6 meses).
9. Proveniência estruturada, balde `legacy.v1` não exibido e regras de lift conservadoras.

### 9.4 Informação clinicamente importante ausente hoje (por modalidade)

| Modalidade | Ausente no v1 e capturável no v2 |
|---|---|
| Radionuclídeo | ciclos **recebidos** (não só planejados); dose absorvida prescrita × entregue e vidro × resina (TARE); fração de informação/limite da interina (PSMAddition); distribuição do ARPI no braço |
| ADC | expressão do alvo **por coorte** (HER2-low × ultralow); ILD G5 e adjudicação; composição do braço TPC; FEVE em anti-HER2; profilaxia ocular exigida |
| Imunoterapia | ensaio de PD-L1; IO prévia no curativo (pós-KEYNOTE-522); toxicidade imune irreversível; toxicidade por fase (neo × adjuvante); definição de pCR/EFS |
| Alvo / iPARP / endócrina | medianas por população de biomarcador (HRD+); método de ajuste de crossover na OS (PROfound); braço de contribuição (lazertinibe no MARIPOSA, 216 pacientes sem resultado); endpoint SNC; critérios de resposta hematológicos (ELN) e aptidão |
| Celular / TCE | **proporção infundida entre randomizados**; mortes antes da infusão; dose celular; internação no step-up; composição do controle |
| Radioterapia | dose por alvo e por braço; toxicidade aguda × tardia; parada precoce e sua base; margem de NI |
| Perioperatório | **quem chegou à cirurgia**, R0, pCR/ypN0 |
| Não-ensaio | emissor/versão/força de recomendação (diretriz); acurácia por unidade de análise e heterogeneidade (diagnóstico) |

### 9.5 Campos v1 inadequados (por modalidade)

| Modalidade | Campo v1 inadequado |
|---|---|
| Todas não-radio | `radiofarmaco` (é intervenção), `cumul` ("—", duração ou "Contínuo") |
| ADC / IO / alvo | `preparo` vazio ou com "prática de classe"; `molecular`/`biomarc` descrevendo o alvo em vez da seleção |
| Braço único | `comparador` ("Single-arm"), `estrat` |
| Celular / mieloma | `biomarc` com MRD (é desfecho) |
| Radioterapia | `cumul` com BED2 derivado e internamente inconsistente (HYPO-RT-PC) |
| Diretriz / diagnóstico | ~20 campos de ensaio preenchidos com "—" ou paráfrase |
| Vários | `linha` com extensão de doença ("Oligometastático"); `status` "Publicado" sem distinguir interina de final |

### 9.6 Possíveis erros de conteúdo achados no teste

Registrados à parte, fora da arquitetura: `scripts/db_candidatos_integridade.json` (34 candidatos, nenhum
verificado nem corrigido; 5 de prioridade alta: HYPO-RT-PC, MONALEESA-3, PROfound, 225Ac-PSMA). Seguem o fluxo
normal do pipeline (fonte primária → proposta em cópia → aprovação).

## 10. Renderer / UX (sem implementar)

### 10.1 Modal do estudo

1. **Cabeçalho**: título, sigla, fase, `evidence_stage`, chips de módulo (ex.: `ADC` `Imunoterapia`),
   "Atualizado em", selo de maturidade ("interina · seguimento 23,6 m"), faixa de revisão se houver.
2. **Resultado principal**: tabela do(s) endpoint(s) primário(s) — braço × valor × IC95 · efeito (HR/OR) · p ·
   maturidade; `key_result` e `takehome` logo acima.
3. **População** · **Desenho** (braços lado a lado) · **Intervenção** (por braço).
4. **Painéis dos módulos presentes** (só com ≥1 campo `present`).
5. **Segurança**: core + AESI dos módulos, com o nome do módulo como subtítulo.
6. **Limitações** · **Impacto** (regulatório com data; diretriz; impacto clínico).
7. **Publicações**: linha do tempo da linhagem (primária → atualizações) + análises secundárias.
8. **Fontes** (recolhido): PMID/NCT + seção por campo; snippet sob demanda.

Nunca mostrar seção vazia. `not_applicable` e `unknown` não aparecem.

### 10.2 Grade (cards)

Nome curto, título, fase, cenário/linha, até 2 chips de módulo (+n), `key_result`, `evidence_stage`, selo
"Nova análise" quando uma atualização entrou há ≤60 dias, faixa discreta "Em revisão".

### 10.3 Comparação

Linhas do core sempre. Linhas de módulo só quando **todos** os estudos comparados têm o módulo; caso contrário,
bloco "Específico de <módulo>" na coluna de quem tem. Endpoints alinhados por `code + population + timepoint`
(PFS × PFS; nunca PFS × rPFS sem aviso). Card com `withheld` entra com a faixa e sem valores.

### 10.4 Mobile

Modal em acordeão com "Resultado principal" aberto; comparação com no máximo 2 estudos, colunas deslizáveis e
rótulos fixos.

### 10.5 Filtros e busca

Filtros estruturados: módulo (classe terapêutica), `record_type`, `evidence_stage`, fase (enum limpo — substitui os
228 valores), cenário, linha, biomarcador obrigatório, randomizado, participação do Brasil. Busca indexa nome,
sigla, agentes, alvos, biomarcadores, NCT e PMID.

---

## 11. Compatibilidade e migração

| Critério | **A** `data.js` canônico + sidecar v2 | **B** v2 canônico → gera `data.js` | **C** progressiva por card (v1 + v2 convivem) |
|---|---|---|---|
| Risco | baixo no início; **alto a médio prazo** (duas verdades divergem) | alto: big-bang de 503 cards | baixo e localizado |
| Complexidade | baixa | alta de uma vez | média, distribuída |
| Rollback | trivial | difícil (reverter gerador + dados) | **por card** (flag) |
| App instalado | sem impacto | sem impacto se a saída for idêntica | sem impacto (legado continua) |
| Tumor Boards / `#uid` / favoritos / notas | intactos | intactos se uid preservado | intactos |
| Comparação | sem ganho | ganho total no fim | ganho gradual (v2 × v2) |
| `app-data` / manifest | inalterado | regenerado | regenerado a cada lote |
| Validadores | inalterados | reescritos | atuais no legado + `validate_v2` novo |

**Recomendação: C, com a mecânica de B por card.**

1. `data.js` continua sendo o que o site e o app consomem. Nenhum consumidor muda até o renderer v2 existir.
2. Cada card tem um de dois modos: **v1** (o card do `data.js` é a verdade) ou **v2** (existe
   `db/v2/records/<uid>.json` aprovado e os campos legados desse card são **gerados** a partir dele).
3. `export_legacy`: `data.js`_novo = `data.js`_atual com os cards v2 sobrescritos pela projeção legada. Idempotente.
4. CI: `export_legacy(data.js) == data.js` (drift de card v2 editado à mão quebra o build) + `validate_v2` + os
   validadores atuais, que continuam rodando sobre o legado.
5. Rollback de um card = apagar/mover seu registro v2 → volta ao modo v1 com o texto do último commit.
6. O `uid` é a chave do registro (nome do arquivo). Renomear é proibido pelo validador (conjunto de uids do HEAD ⊆
   conjunto novo).
7. **App**: o `data.json` legado permanece enquanto houver versão do app que o leia. A projeção v2 pública, quando
   existir, vai em **manifest separado** (ou dataset leve), porque o app atual baixa tudo que está no manifest.
8. `secondary-cards.js` não muda na transição; no fim, pode ser gerado de `publications[]`.

---

## 12. Contrato do futuro `database-curator` (não implementado)

**Entrada**
```json
{
  "uid": "…",
  "card_v1": {…},
  "record_v2": {… | null},
  "sources": [{"id": "s1", "type": "publication", "pmid": "…", "pmcid": "…", "text": "…", "tables": [...]},
              {"id": "s2", "type": "registry", "nct": "…", "json": {...}}],
  "schema": "theratrials-db-v2-registry/0.1",
  "modules_suggested": ["adc", "immunotherapy"],
  "analysis_signature_target": {…},
  "decisions": [/* db_decisoes.json aplicáveis ao uid */],
  "conflicts": [/* db_conflitos_fonte.json aplicáveis */]
}
```

**Saída**
```json
{
  "uid": "…",
  "record_type": "trial",
  "modules": [{"name": "adc", "rationale": "…"}],
  "fields": [
    {"path": "endpoints[e1].arms_values[exp].value", "value": 20.2, "state": "present", "origin": "reported",
     "source_id": "s1", "locator": {"section": "Results", "snippet": "…"}, "evidence_confidence": "high",
     "change": "new|unchanged|changed", "previous_value": null}
  ],
  "not_extractable": [{"path": "…", "reason": "fonte sem texto completo"}],
  "conflicts_found": [{"path": "…", "values": [...], "locators": [...]}],
  "questions": [{"path": "…", "question": "…"}]
}
```

Regras: nunca preencher campo sem `source_id` + `locator` (exceto `editorial`); nunca resolver conflito escolhendo
valor; nunca alterar `uid`; nunca usar tracker/explorer como fonte; `unknown` é resposta válida.

## 13. Contrato do futuro `database-verifier` (não implementado)

**Entrada**: `sources` (as mesmas), `card_v1`/`record_v2` original e a **proposta final** do curator
(`fields[]` com valores e locators). **Não recebe** raciocínio, rascunhos nem `questions` do curator.

**Saída**
```json
{
  "uid": "…",
  "verdicts": [
    {"path": "…", "verdict": "PASS|FAIL|UNSUPPORTED|CONFLICT",
     "found_locator": {"section": "…", "snippet": "…"},
     "observed": "o que a fonte diz, quando FAIL/CONFLICT",
     "note": "arm_mismatch | unit_mismatch | locator_mismatch | population_mismatch | rounding"}
  ],
  "module_check": [{"name": "adc", "verdict": "PASS|FAIL"}],
  "summary": {"PASS": 0, "FAIL": 0, "UNSUPPORTED": 0, "CONFLICT": 0}
}
```

- PASS: valor e contexto (braço, população, timepoint, unidade) conferem na fonte.
- FAIL: a fonte diz outra coisa. UNSUPPORTED: a fonte não sustenta. CONFLICT: a fonte sustenta mais de um valor.
- **Proibido**: devolver a proposta corrigida, preencher campos, mudar valores. `observed` é evidência, não patch.
- Checagem obrigatória de **mapeamento de braço** (a classe de erro do SINDAS) e de unidade.

---

## 14. Automação e carga humana (meta: ≤ 5 decisões/semana)

| Classe | Campos | Aceite |
|---|---|---|
| **machine** | registros, fase, patrocinador, centros, período, status do registro, PMID/DOI/ano/periódico, alocação/cegamento (CT.gov), `last_reviewed` | conferência automática contra CT.gov/PubMed/Crossref (MV-1…MV-6 do v1) |
| **verifier** | tudo extraído da publicação: endpoints, efeitos, N, seguimento, toxicidades, doses, atividades, biomarcadores, módulos | curator + verifier PASS ⇒ aceito **sem humano** |
| **human** | `takehome`, `clinical_impact`, `key_result` (texto), `category_id`, `record_type`, decisões de integridade, resolução/apresentação de conflito, neutralização | humano |
| **pode ficar ausente** | todo USEFUL/SPECIALIZED | `unknown` indefinidamente, sem inbox |

Regras para não aumentar a carga:
1. **A unidade da decisão humana é o card, não o campo.** Uma atualização de card = 1 decisão, com o diff inteiro.
2. Humano só entra quando: FAIL/UNSUPPORTED/CONFLICT em campo ESSENTIAL; mudança **material** em ESSENTIAL já
   publicado (direção/significância do primário, `evidence_stage`, `outcome`); texto editorial novo; integridade.
3. Campo **novo** (antes `unknown`) com PASS **não** gera decisão; entra no próximo lote aprovado em bloco.
4. Completar USEFUL/SPECIALIZED é backlog de fundo, nunca inbox.
5. A migração v1→v2 é orientada por **toque**: um card migra quando já vai ser atualizado (sinal P1 do freshness),
   não em campanha — a carga humana da migração se confunde com a da atualização que já existiria.

---

## 15. Riscos

| Risco | Mitigação |
|---|---|
| Schema enciclopédico → curadoria cara | níveis; USEFUL/SPECIALIZED podem ficar ausentes; unidade de decisão = card |
| Estruturar endpoints introduz erro de braço/unidade | `arm_id` explícito; verifier obrigado a checar braço e unidade |
| Módulo atribuído errado (heurística demonstrou falhar) | módulos explícitos no registro; heurística só sugere; verifier confere |
| Drift entre `data.js` editado à mão e registro v2 | CI de idempotência do `export_legacy` |
| App instalado baixa tudo do manifest | legado intocado; projeção v2 enxuta e em manifest separado |
| Payload cresce com proveniência | proveniência só na camada canônica; export leva fonte resumida |
| Derivado parecer publicado | `origin` obrigatório; selo; derivados com parâmetro clínico proibidos no card |
| Texto editorial não verificável | números do editorial validados contra `endpoints[]` (guard atual generalizado) |
| Registros não-ensaio distorcem filtros e contagens | `record_type`; discutir mover diretrizes para `guidelines.html` |
| Dois sistemas de modalidade (`modalities[]`, `studyModality()`, `modules[]`) | `modules[]` substitui ambos na projeção; os antigos viram derivados |
| i18n | enums estruturados permitem EN/PT sem traduzir dados; texto livre continua PT |
| Escopo cresce antes de o piloto provar valor | plano incremental com portão de aprovação por fase |

---

## 16. Plano incremental

| Fase | Entrega | Toca produção? |
|---|---|---|
| **v2.0 — fundação** | registro de campos, JSON Schema do registro, **perfis como mapas explícitos por caminho**, **proveniência estruturada**, **balde `legacy.v1`**, `validate_v2`, `lift_v1` conservador (503 cards → registros-sombra, tudo `unknown` + legado, ignorados pelo git), `export_legacy` com **prova de round-trip byte a byte** | não |
| v2.0b — pré-piloto | fechar no registro: tier por `role` de módulo, `applies_when` estruturado, visões de terapia prévia, regra de `outcome` com mais de um primário; desmembrar editorialmente 225Ac-PSMA e FES-PET | não (o desmembramento, sim, com aprovação) |
| v2.1 — piloto | 10 cards curados à mão com proveniência (os 6 P0 já auditados + 4 de módulos diferentes); `data.js` gerado muda só nesses cards; decisão humana por card | sim, 10 cards, com aprovação |
| v2.2 — agentes | curator + verifier implementados sobre o piloto; medir decisões humanas/semana | não |
| v2.3 — projeção pública | `data-v2` enxuto em manifest próprio; renderer v2 atrás de flag no site | sim, com flag |
| v2.4 — migração por toque | cards migram quando atualizados pelo freshness; categorias teranósticas primeiro | sim, incremental |
| v2.5 — desligar legado | quando nenhuma versão ativa do app ler só o legado | sim |

## 17. Decisões aprovadas (28/set/2026)

1. `radioligand` → `radionuclide_therapy` (RLT, PRRT, Ra-223, 131I, MIBG, Y-90); `bispecific` → `t_cell_engager`
   (só agentes que recrutam célula T). Biespecífico não-TCE vai para o módulo clinicamente adequado
   (`targeted_therapy`, `agent_class=bispecific_antibody`, múltiplos alvos).
2. Sem módulo PARPi: `targeted_therapy` (agente) + `ddr_hrd` (contexto; reutilizável por platina, RLT + iPARP etc.).
3. Migração C: não migrado ⇒ `data.js` canônico; migrado ⇒ registro v2 canônico e legado gerado; CI bloqueia
   divergência (`export_legacy` ≠ `data.js` ⇒ saída 1). `uid` absolutamente imutável.
4. Cards agregados (225Ac-PSMA Heidelberg, FES-PET): o card atual vira `evidence_collection` com o MESMO uid
   (links, favoritos e histórico preservados); os estudos/publicações filhos recebem uids novos, ligados por
   `parent_uid`/`child_uids`. Desmembramento em produção ainda não autorizado.

## 18. Fundação técnica (implementada, sem produção)

| Arquivo | Papel |
|---|---|
| `registry_v2.py` | fonte única: record_types, perfis, core, módulos (requisito por papel + ativação), AESI, modelo de endpoints/multiplicidade, assinatura, relações; gera os dois JSON abaixo |
| `registry_v2.json` | registro de campos (1.0) |
| `schema_record_v2.json` | JSON Schema draft 2020-12 do registro canônico |
| `v2lib.py` | leitura/serialização do data.js, validador de JSON Schema sem dependência, avaliação de ativação |
| `lift_v1.py` | 503 cards → `scripts/_db_v2_shadow/` (ignorado), conservador |
| `export_legacy.py` | sombra → data.js; prova byte a byte; bloqueio de divergência de card migrado |
| `validate_v2.py` | validador semântico |
| `fixtures_v2.py` + `fixtures/` | 22 registros sintéticos (um por cenário) |
| `test_db_v2.py` | testes offline |

### 18.1 Papel do módulo

| Papel | Significado | Exige |
|---|---|---|
| `tested` | o módulo é a pergunta do estudo naqueles braços | campos ESSENTIAL do módulo + AESI obrigatórios, se ativos |
| `backbone` | base comum (em geral nos dois braços) | identidade do agente (alvo) e o que define o componente (ex.: procedimento cirúrgico); AESI opcional |
| `control` | só como comparador | quase nada: o módulo existe para descrever o controle (ex.: RT só no controle do ESOPEC); AESI opcional |
| `context` | nenhum agente administrado; só população | campos de população (ex.: status hormonal, genes DDR); AESI nunca |

Cada campo de módulo tem `requirement = {tested, backbone, control, context}` ∈ {required, optional,
not_applicable}. Campo `not_applicable` preenchido gera só aviso; campo exigido mas inativo nunca é cobrado.

### 18.2 Ativação (estruturada, não prosa)

Predicados avaliados pelo validador: `always`, `biomarker_involved` (seleção, estratificação, população de
endpoint ou subgrupo), `biomarker_rule_in`, `subgroup_dimension_in`, `field_in` (campo do próprio módulo ou do
core), `present`, `agent_class_in`, `setting_in`, `rt_site_in`, `not`, `any_of`, `all_of`. Dado ausente ⇒
condição falsa ⇒ campo não cobrado. Exemplos:
- `immunotherapy.pdl1`: `biomarker_involved(PD-L1)`;
- `radionuclide_therapy.target` e `imaging_selection`: `field_in($module.delivery, [systemic_ligand, radioimmunoconjugate])`;
- `adc` AESI `ild_pneumonitis`: `field_in($module.payload_class, [topo1_inhibitor])`; `lvef_decline`: alvo HER2;
- `targeted_therapy.required_alteration`: não (SSA, iCDK4/6, antiangiogênico…) E biomarcador required/enriched;
- `t_cell_engager` AESI `crs`: required só para `tested`, e só nos braços do módulo.

### 18.3 Múltiplos endpoints primários

Cada endpoint: `endpoint_id`, `code`, `hierarchy {level, primary_type, scope {cohort_id, part_id},
testing {family_id, order}, history[]}`, `comparison_id`, `population`, `measure {summary, analysis_role}`,
`timepoint`, `assessment`, `analysis_set`, `maturity`. Multiplicidade em `design.multiplicity.families[]`.
- **único**: 1 primário por (escopo × comparação);
- **co-primário** (todos precisam ser positivos) e **dual-primário** (qualquer um; α dividido — o validador
  exige família com α por membro e soma ≤ α total);
- **hierarquia sequencial**: `fixed_sequence` com ordem 1..n;
- **primário por coorte/parte**: `scope`;
- **por comparação** (HIMALAYA): cada comparação tem seu primário/chave;
- **emenda**: `history[]` guarda o nível anterior;
- **mesmo endpoint, duas medidas** (SINDAS: taxa em 6 meses do protocolo + mediana de apoio): dois endpoint_ids,
  `analysis_role` distinto; só `protocol_primary_analysis` conta para "único".

### 18.4 Relações

`relationships {parent_uid, child_uids[], links[{type: same_trial | follow_up_of | secondary_analysis_of |
supersedes | member_of, target_uid}]}`. O validador proíbe auto-referência, ciclo parent/child e ciclos em
`supersedes`/`follow_up_of`/`secondary_analysis_of`, e exige reciprocidade parent ↔ child quando os dois existem.

### 18.5 Resultado da fundação (28/set/2026)

- `lift_v1`: 503 registros-sombra; 2.398 valores `present` (só identidade/navegação, origin=legacy) e 13.698
  `unknown`; 74 incertezas e 1.130 sugestões registradas; módulos só com evidência forte (papel `undetermined`).
- `export_legacy`: saída **idêntica byte a byte** ao `data.js` (SHA-256 `cd4bd842…`).
- `validate_v2`: 503 registros, 0 erros, 10.662 lacunas W_REQUIRED (backlog; nunca inbox).
- Testes: 96 (fixtures sintéticas + mutações negativas + regressão dos bugs achados na modelagem real).
- Reteste de representação dos 35 cards (+6 filhos das duas coleções): antes das correções, 20 cabem e 15 cabem
  com ajuste; 0 não cabem. Todos os ajustes pedidos entraram, exceto os listados em "abertos" abaixo. Depois da
  normalização mecânica, 0 erros de schema; restam 2 erros de modelagem (assinatura combinando dois endpoints;
  código DSS registrado como `other`).

### 18.6 Pontos abertos

- Estrutura de `guideline.recommendations` (hoje lista livre); avaliar se diretrizes saem do Database para
  `guidelines.html`.
- Link para estudo externo sem uid (ex.: NCT de ensaio confirmatório que não tem card).
- `interpretation.outcome` com mais de um primário continua decisão humana.
- Enums de `population.setting` misturam cenário e estado da doença quando o modelador tenta ser específico: o
  estado (CRPC, HSPC, extensão) mora em módulos/`disease_extent`; o teste confirmou que o enum barra a mistura.
- O léxico de módulos do lift é heurístico (sugestão); papel e braços só na curadoria.

## 19. Piloto v2.1 (28/set/2026) — 10 registros `curated` em scratch

- Cards: ASPEN, TROPION-Lung01, ANBL1531, KEYNOTE-158 endométrio, SINDAS, ppgl_8 (quarentena nativa) + ZUMA-7
  (CAR-T; só resumo + resultados do CT.gov), EPCORE NHL-1 (TCE braço único), MAGNITUDE (iPARP + ddr_hrd sobre AAP),
  LUNAR (177Lu-PSMA testado sobre SBRT backbone).
- validate_v2: 0 erros; 7 `W_REQUIRED_ACK` (unknown declarado com fontes). Proveniência: 385/385 trechos literais
  conferidos por máquina contra as fontes em cache (PMC, PubMed, CT.gov).
- Projeção v2 → legado: 75 diferenças = 51 A (representação) + 24 B-pendente (correção factual com fonte, ligada a
  candidato de integridade); 0 C, 0 D, 0 E.
- Regra que o piloto impôs: **a projeção só substitui campo cujo conteúdo o registro cobre com fonte igual ou melhor
  que a do v1** (fonte parcial não apaga conteúdo; texto aprovado não é reescrito sem decisão). Aplicada em ZUMA-7
  (tox_g3), MAGNITUDE (secundario, tox_g3) e SINDAS (primario, secundario).
- 58 novos candidatos de integridade (fora da arquitetura: `scripts/db_candidatos_integridade.json`, 92 no total).
- Nunca exercitados com dado real: record_types não-ensaio (guideline, diagnostic_study, meta_analysis,
  cohort_study, evidence_collection…), módulos `diagnostic` e `locoregional`, `design.factors`,
  `design.observational`, PD-L1, endócrino de mama, TARE/absorbed_dose e 32 campos de módulo.
