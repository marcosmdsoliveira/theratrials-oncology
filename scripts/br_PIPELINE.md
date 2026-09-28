# Pipeline do Trial Matcher

Mantém `assets/js/trials_br.js` alinhado ao ClinicalTrials.gov. **Dado objetivo
vem da API, comparado por código. IA só interpreta, e só na curadoria.**

## Os quatro papéis

| papel | script | IA? | o que faz |
|---|---|---|---|
| trial-status-auditor | `br_auditar.py` | não | os NCTs publicados ainda recrutam **no Brasil**? |
| trial-discovery | `br_discover.py` + `br_ciclo.py` | não | estudos novos no CT.gov, triados em faixas |
| trial-curator | `br_curate.py` + agente `.claude/agents/trial-curator.md` | **sim** | normaliza os recomendados para a taxonomia |
| trial-qa | `br_qa.py` | não | atual × proposto, e roda os validadores numa cópia |

`br_ctgov.py` é o módulo comum: acesso à API e a regra de recrutamento no Brasil.
`br_ciclo.py` encadeia tudo, menos a curadoria.

## `brazil_status`: a regra de "recrutando no Brasil"

Recrutar no mundo não basta. Toda comparação de status usa igualdade exata ou
um conjunto explícito (`br_ctgov.py`). Até 2026-09 o teste era
`"RECRUITING" in status`, que também casa com `ACTIVE_NOT_RECRUITING` e
`NOT_YET_RECRUITING`. O front-end tinha o mesmo erro em português:
`indexOf('recrut')` também pega "Ainda não recrutando".

Regras em ordem; a primeira que casar decide:

| # | situação no registro | `brazil_status` | status proposto no card |
|---|---|---|---|
| 1 | status global encerrado | `STUDY_CLOSED` | Encerrado |
| 2 | status global fora de RECRUITING/NOT_YET_RECRUITING | `REVIEW_REQUIRED` | — |
| 3 | nenhum centro no Brasil | `REVIEW_REQUIRED` | — |
| 4 | ≥1 centro BR `RECRUITING` (global `RECRUITING`) | `RECRUITING` | Recrutando |
| 5 | algum centro BR sem status | `REVIEW_REQUIRED` | — |
| 6 | ≥1 centro BR `NOT_YET_RECRUITING` | `NOT_YET_RECRUITING` | Ainda não recrutando |
| 7 | todos os centros BR fechados, estudo aberto no mundo | `CLOSED_IN_BRAZIL` | — (decisão pendente) |
| 8 | qualquer outra combinação | `REVIEW_REQUIRED` | — |

Cada card traz o campo `brazil_status`, gravado pela auditoria. É ele, e não
o `status`, que decide o que conta como "recrutando no Brasil": o filtro
padrão do Trial Matcher e o número da home usam `brazil_status ===
'RECRUITING'`. Card em `REVIEW_REQUIRED` mantém o `status` que tinha (o
ROSETTA RCC-201 segue "Recrutando") e sai do padrão até a auditoria
encontrar um centro brasileiro recrutando.

`brazil_status` → `status` do card (THERA_TRIALS_BR_META):
`RECRUITING` → Recrutando · `NOT_YET_RECRUITING` → Ainda não recrutando ·
`CLOSED_IN_BRAZIL` → Recrutamento encerrado no Brasil · `STUDY_CLOSED` →
Encerrado · `REVIEW_REQUIRED` → nada muda. O Trial Matcher mostra por padrão só
**Recrutando**; os demais status ficam no filtro. O site conta "recrutando no
Brasil" (`status === 'Recrutando'`) separado de "estudos mapeados" (todos). A
frase "ensaios clínicos ativos" é barrada pelo `sync_counts.mjs`.

## Biomarcadores: `biomarcadores` + `biomarcadores_criterios`

`biomarcadores` continua uma lista de strings. O app já publicado lê esse
campo, então o tipo não muda. A regra é que ali só entra o que o paciente
**precisa ter**: positivo, presente, mutado ou no estado exigido. É o que o
filtro usa.

`biomarcadores_criterios` (opcional) é o detalhe. Quando existe, é a fonte, e
`biomarcadores` é derivado dele (os `requerido`, na ordem):

| situação | `biomarcadores_criterios` | entra em `biomarcadores`? |
|---|---|---|
| HER2+ | `{HER2, requerido, 'IHQ 3+ ou ISH+'}` | HER2 |
| HER2-low | `{HER2-low, requerido, 'IHQ 1+ ou 2+/ISH−'}` | HER2-low |
| HER2− | `{HER2, excluido, 'positivo'}` | — |
| PD-L1 ≥ corte | `{PD-L1, requerido, 'TPS ≥ 50%'}` | PD-L1 |
| PD-L1 só avaliável | `{PD-L1, avaliado}` | — |
| EGFR mutado | `{EGFR, requerido, 'mutação sensibilizante'}` | EGFR |
| KRAS G12C | `{KRAS G12C, requerido}` | KRAS G12C |
| BRCA1/2 | `{BRCA, requerido, 'BRCA1/2 germinativo'}` | BRCA |
| selvagem exigido | `{EGFR, excluido, 'mutação'}` | — |

Estudo com coortes de critérios diferentes: cada critério leva `coorte`, e o
conflito requerido × excluído só conta dentro da mesma coorte (BREAKER-101:
HER2 exigido em 'Mama HER2+' e excluído em 'Mama HR+/HER2−').

**Alvo não é critério.** `alvos` (lista de strings, opcional) guarda o alvo
molecular da intervenção: TROP-2 de um anti-TROP-2, EGFR/HER3 de um
biespecífico. Aparece na ficha e não entra no filtro. Um marcador pode estar
nos dois, como CLDN18.2 no LUCERNA, que é alvo do zolbetuximabe e critério de
entrada. Cards antigos ainda misturam alvo e critério: a lista de suspeitos
está em `scripts/_br_alvos_a_revisar.md`. O trial-qa **bloqueia** um token de negatividade em `biomarcadores`
('HER2-', 'wild-type'), HER2 exigido em card HER2-negativo, um marcador
requerido e excluído ao mesmo tempo, e `biomarcadores` diferente dos
`requerido`. O curador não preenche `biomarcadores`: o script deriva.

## Escopo editorial

O Trial Matcher principal inclui estudos cujo objetivo primário é
**tratamento antineoplásico ou modificação direta da doença tumoral**. Não
entram automaticamente estudos só de:
- suporte;
- sintoma;
- caquexia;
- prevenção;
- rastreamento;
- reabilitação;
- toxicidade ou complicação do tratamento.

Síndrome carcinoide entra só com objetivo antitumoral.

- **Descoberta:** termos de suporte no título ou nas condições mandam o
  estudo para "revisar", nunca para descarte.
- **Curador:** campo `escopo` (`antineoplasico` | `suporte_ou_sintomatico` |
  `limitrofe`).
  - `suporte_ou_sintomatico` é descarte **explícito**: registrado, com o motivo.
  - `limitrofe` vai para a lista `revisao`, nunca para descarte, e volta na
    rodada seguinte até alguém decidir.

### Teranósticos (radioligantes), desde 2026-09

Entram no Trial Matcher como qualquer outro tratamento antineoplásico. Cada
fonte tem um papel:
- **Database (`data.js`):** evidência;
- **Trial Matcher:** recrutamento no Brasil;
- **Explorer:** radar global. Nunca é fonte de card, porque deduz o isótopo
  pelo título e já errou (AAA817 e RYZ101 aparecem como ¹⁷⁷Lu; são ²²⁵Ac).

- **Descoberta:** `eh_teranostico()` só **marca** (`teranostico: true`). O
  estudo segue a triagem normal, e o relatório lista os marcados com a faixa
  em que caíram. A marca vem do título e das intervenções (nome, descrição e
  `otherNames`), nunca do resumo. No título, trechos de tratamento prévio
  ("after 177Lu-PSMA") são removidos antes. PSMA ou SSTR sozinhos não marcam:
  anti-PSMA biespecífico e seleção por PET não são RLT.
- **META:** a modalidade `radioligante` (label "Radioligante (RLT / PRRT)")
  entrou por `br_migracao_rlt_2026_09.py`, via `--permitir-meta`.
- **Curador** (regra 12):
  - o radiofármaco vai em `intervencao`;
  - o alvo vai em `alvos`;
  - PET PSMA/SSTR só é `requerido` se a positividade for exigida;
  - tratamento prévio com radioligante vai em `criterios_principais`;
  - sem alvo no registro (rádio-223), `alvos_justificativa` diz por quê.
- **QA:** radioligante sem `alvos` e sem `alvos_justificativa` é FAIL. Alvo
  fora de `ALVOS_RLT` e card novo com radiofármaco na intervenção mas sem a
  modalidade são WARN.
- **Trial Matcher:** o filtro "Radioligante" compara `modalidade` por
  igualdade exata, e a opção só aparece se houver card.

### Linha terapêutica: regra canônica, desde 2026-09

`linha_terapeutica` é a linha sistêmica **dentro do estado clínico em que o
estudo recruta**. É a convenção que já predominava no banco. Por exemplo, 18
cards "1ª linha" de mama, endométrio, gástrico e pulmão aceitam adjuvante
prévio sem contá-lo.
- Terapias de estados anteriores não contam: neo/adjuvante e perioperatório
  não contam para a doença avançada/metastática; no mCRPC, o tratamento do
  mHSPC não conta.
- Exceção: o próprio protocolo trata explicitamente a recidiva precoce ou a
  terapia anterior como definidora da linha. Exemplos: IZABRIGHT (recidiva em
  até 12 meses após o perioperatório), HERTHENA-Breast04 (iCDK4/6 adjuvante)
  e o título "First-Line Treatment for mCRPC" do ICESP.
- Faixa de linhas, ou linha indeterminável com segurança: categoria genérica.
  Em tumor sólido, `Avançado / metastático`; em hematologia, `Recidivado /
  refratário`. Nunca se infere uma linha mais específica pelo número total de
  terapias prévias.
- Exemplos:
  - AcTFirst (ARPI no mHSPC, nada no mCRPC) → `1ª linha`;
  - ICESP (o registro diz "First-Line") → `1ª linha`;
  - PSMAcTION (ARPI, taxano e 177Lu-PSMA sem dizer em que estado) →
    `Avançado / metastático`;
  - PSMA-DC (oligometastático hormônio-sensível) fica em `Avançado /
    metastático` por decisão editorial: "linha" é pouco claro nesse cenário.

Está no prompt do curador (regra 13) e no agente `trial-curator`.

### Override humano: `scripts/br_aprovados.json`, desde 2026-09

Serve para decisões humanas que contrariam um campo do registro. É o oposto
do `br_descartados.json`. Existe **um único tipo**, `primary_purpose`: o
estudo cai em "revisar" só porque o registro declara um propósito diferente
de TREATMENT, e uma pessoa confere que ele é terapêutico. O primeiro caso é o
AcTFirst (NCT06855277): fase III com desfecho primário rPFS, registrado como
DIAGNOSTIC.

Cada entrada exige `nct`, `tipo`, `valor_registro`, `decisao` (TREATMENT),
`motivo` e `aprovado_em` (AAAA-MM-DD). Entrada inválida é ignorada e aparece
no relatório. A exceção vale:
- só para o NCT listado;
- só enquanto o registro trouxer exatamente o `valor_registro` anotado (se o
  patrocinador corrigir o campo, o override perde o efeito sozinho);
- só no ponto da triagem que olha o propósito.

As checagens de status no Brasil e de extensão vêm antes. As de escopo e de
tipo de intervenção vêm depois, e curadoria, merge e QA não leem este
arquivo. O relatório tem a seção "Overrides humanos aplicados" e lista também
os registrados sem efeito e as entradas recusadas.

Testes: `python3 scripts/test_br_aprovados.py`. Rodam offline, com o registro
do AcTFirst em `scripts/fixtures/`.

## Aplicar uma atualização (fluxo seguro)

```bash
mkdir -p scripts/_br_base && cp assets/js/trials_br.js scripts/_br_base/trials_br.js
python3 scripts/br_migracao_2026_09.py scripts/_br_base/trials_br.js    # META + biomarcadores
python3 scripts/br_ciclo.py --base scripts/_br_base/trials_br.js --permitir-meta
# revisar scripts/_br_relatorio.md e o diff; QA OK → aplicar (decisão humana):
cp scripts/_br_proposto/trials_br.js assets/js/trials_br.js
node scripts/sync_counts.mjs && node scripts/export_app_data.mjs && node scripts/validate_app_data.mjs
# e espelhar no app: index.html e assets/lang/*.js (os números do bundle)
```

## Uso

```bash
python3 scripts/br_ciclo.py                  # relatório completo (≈2 min)
python3 scripts/br_ciclo.py --centros        # propõe também os centros
python3 scripts/br_ciclo.py --gravar-estado  # grava o histórico (ver abaixo)
```

Saídas (fora do git, prefixo `_`):

- `scripts/_br_relatorio.md` / `.json`: o relatório de diferenças
- `scripts/_br_proposto/trials_br.js`: o banco proposto
- `scripts/_br_discovery.json`: só os recomendados, que é a entrada da curadoria

Curadoria dos recomendados, sem custo de API, numa sessão do Claude Code:

```bash
python3 scripts/br_curate.py --exportar      # gera _br_prompts.json
# peça: "use o agente trial-curator"
python3 scripts/br_ciclo.py --sem-descoberta --com-curadoria
```

Aplicar o proposto é decisão humana: copie-o sobre `assets/js/trials_br.js`,
revise o diff, rode `sync_counts.mjs`, `export_app_data.mjs` e os validadores,
e só então commite.

## Histórico, fora do contrato público

`trials_br.js` e `app-data/trials_br.json` **não mudam de formato**. O controle
interno fica ao lado, em arquivos que nem o site nem o app leem:

- `scripts/br_estado.json`: foto atual por NCT, com `overall_status`,
  `brazil_status`, `last_checked`, `last_update_posted`, `last_verified` (o
  `statusVerifiedDate` do CT.gov), `br_confirmado_em` (a última data em que um
  centro BR estava `RECRUITING`) e `centros_br_recrutando`.
- `scripts/br_eventos.jsonl`: log só de acréscimo, com uma linha por mudança
  (status, estado no Brasil, centro BR que entrou ou saiu, registro atualizado).

Os dois só são escritos com `--gravar-estado`. No GitHub Actions, passam de
uma run para a seguinte como artifact (`trials-br-estado`, 90 dias), sem
commit. Sem eles, o relatório compara o card com o registro de hoje. Com eles,
compara também com a rodada anterior.

## Travas

- Nenhum script do ciclo commita, faz push ou remove card. O QA **bloqueia** o
  proposto que remova card, mude a META, repita id ou NCT, ou use valor fora
  da taxonomia.
- Mudança em campo não factual de card existente (`racional`, critérios etc.)
  vira aviso: é interpretação clínica, e uma pessoa precisa olhar.
- Status só é proposto quando há tradução exata no vocabulário atual.
  `REVIEW_REQUIRED` vai para revisão manual; `CLOSED_IN_BRAZIL` fica como
  decisão pendente.
- Resposta parcial da API é falha técnica, não revisão. Quando um lote da
  auditoria volta incompleto, ele é repetido uma vez. Se ainda faltar mais
  de um NCT, o ciclo aborta. Um único ausente é consultado sozinho, e só o
  404 confirma que ele saiu do registro, indo para revisão manual. A
  descoberta confere o total coletado com o `totalCount` da API: repete a
  varredura uma vez e, se ainda divergir, aborta. Um estudo omitido pela API
  viraria `REVIEW_REQUIRED` e sumiria do filtro padrão, e o relatório diria
  "QA OK".
- Códigos de saída do `br_ciclo.py`: 0 = QA OK; 3 = QA bloqueou (com
  relatório); qualquer outro = falha técnica (sem relatório, e o estado da
  run anterior não é tocado).
- O workflow `trials-br-auditoria.yml` roda toda segunda às 09:17 UTC, tem
  permissão só de leitura e não usa secret. Separa "Falha técnica — veja o
  log" de "QA bloqueou" pelo código de saída.
- Pipeline único: os workflows mensais antigos (`trials-br-descobrir` e
  `trials-br-publicar`) ficaram em `.github/workflows-legado/`, onde o GitHub
  não os executa. O modo Batch do `br_curate.py` é legado.
