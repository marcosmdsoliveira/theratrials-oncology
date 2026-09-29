# Pipeline do Database (`data.js`)

Manutenção do Database com fonte primária e revisão humana. Estão implementadas:
- Fase 0: registro de identidade;
- Fase 1: freshness de alto sinal;
- Fase 1.5: verificação por máquina, automação por domínio, prioridade e inbox;
- Fase 1.6: texto das notas de correção, `integrity_hold` e propostas para os P0 de integridade.

Ainda não existem curador, QA de propostas, aplicação, workflow nem notificação.

**Nada neste pipeline escreve em `assets/js/data.js`.** A única porta de escrita é
`db_registro.gravar()`. Ela aceita só `scripts/_db_*` (ignorados pelo git) e,
uma única vez, `scripts/db_backlog_baseline.json`.

## Fontes

| Fonte | Papel | Obrigatória |
|---|---|---|
| PubMed E-utilities | Publicações ligadas ao registro (`NCT…[si]`, `ISRCTN…[si]`) e registro de cada artigo (efetch XML): tipo de publicação, DOI, PMCID, DataBank, CommentsCorrections | Sim |
| ClinicalTrials.gov v2 | Status, `hasResults`, datas de resultado e referências RESULT/DERIVED | Sim |
| NCBI ID Converter | PMCID e DOI dos artigos no PMC | Sim |
| Crossref | Complementar: correções e retratações do DOI do card (`updated-by`, que inclui o Retraction Watch). Se falhar, a coleta segue e o relatório diz "Crossref incompleta". Pode ser desligada com `--sem-crossref` | Não |

### Fontes proibidas

`assets/data/tracker.json` e `assets/data/explorer.json` (e os `.js`
correspondentes) estão **proibidos** para o Database até uma auditoria
específica. Nenhum script `db_*` pode usá-los para descoberta, identidade,
validação, enriquecimento ou proveniência.

Os motivos:
- a auditoria de 2026-09-28 achou 42 dos 53 NCTs do tracker apontando para outro estudo;
- o Explorer é índice de descoberta do site, não fonte clínica.

Como a proibição é garantida:
- a lista está em `db_fontes.FONTES_PROIBIDAS`;
- `garantir_fonte_permitida()` recusa a leitura;
- `test_db_freshness.py` falha se o código de qualquer `db_*.py` mencionar esses arquivos fora da lista.

## Arquivos

| Arquivo | Versionado | Conteúdo |
|---|---|---|
| `db_fontes.py` | sim | Coleta (só leitura) |
| `db_registro.py` | sim | Fase 0: registro de identidade |
| `db_freshness.py` | sim | Fase 1: sinais de alta prioridade, baseline, estado, relatório de prioridade |
| `db_correcoes.py` | sim | Fase 1.6: recupera e classifica o texto das notas de correção (`--reclassificar` roda sem rede) |
| `db_migracao_p0_2026_09.py` | sim | Reparos P0 aprovados em 2026-09-28 (seis cards, inclusive a neutralização do `ppgl_8`). Gera a cópia em `_db_copia/`; a cópia validada foi aplicada ao `data.js` em commit próprio |
| `db_conflitos_fonte.json` | sim | Achados de conflito dentro da mesma fonte. **Estado canônico, não saída**: nenhum script escreve nele (só `db_registro.construir` lê). Cada achado vem da leitura humana do texto completo (trecho, seção e contexto de cada ocorrência), que o pipeline não reproduz; sem o arquivo versionado, um `WITHIN_SOURCE_CONFLICT` confirmado deixaria de bloquear o campo na execução seguinte |
| `db_p0.py` | sim | Fase 1.6: propostas campo a campo para os P0, em cópia (`_db_propostas_p0.{json,md}`) |
| `db_confianca.py` | sim | Fase 1.5: famílias de evidência, `machine_verified`, domínios de automação, P0–P3/WATCH, integridade PMID/NCT, simulação do inbox |
| `test_db_freshness.py` + `fixtures/db_pubmed_*.xml` | sim | Testes offline |
| `db_decisoes.json` | sim | Memória editorial. Pequeno. Guarda as decisões humanas pelo `id` estável do item (chave do sinal ou `uid:pmid` do baseline). Tipos: `ignore`, `approve`, `defer` (com `ate`) e `classificacao` (`uid`, `pmid`, `campo`, `valor`; vale só enquanto o card citar o mesmo PMID). Nenhum script escreve nele |
| `db_backlog_baseline.json` | sim | Fotografia do dia zero (schema v2), **imutável** e sem campo de decisão. `gravar()` recusa sobrescrever; só aceitou uma migração v1 → v2 porque o v1 não tinha nenhuma decisão |
| `db_candidatos_integridade.json` + `db_integridade.py` | sim | **Backlog canônico de integridade** (memória editorial, não relatório). Cada item: `id` estável `INT-<uid>-<nnn>`, `issue_type`, campos afetados, evidência, prioridade, `status` (open, confirmed, dismissed, resolved, deferred), datas, decisão humana, resolução (commit) e `history`. Regras: nada é apagado; `confirmed`/`resolved`/`dismissed` não são rebaixados por máquina; `resolved` exige commit; redetecção não cria outro id (`mesclar()` por `dedupe_key` + similaridade); ids retirados nunca voltam. Varreduras gravam em `_db_*` e só entram aqui por `mesclar()`. Testes: `test_db_integridade.py` |
| `_db_prioridade.{json,md}` | não | Relatório da Fase 1.5 |
| `_db_coleta.json`, `_db_registro.{json,md}`, `_db_freshness.{json,md}`, `_db_backlog_baseline.md` | não | Saídas de cada execução |
| `_db_estado.json` | não | Estado de máquina posterior ao baseline |

## Origem das classificações

- **`explicit`**: a fonte diz. Pode ser o título do artigo ("final overall survival"), o tipo de publicação do PubMed, um trecho literal do abstract, uma referência do CT.gov ou o texto do próprio card (endpoints).
- **`inferred`**: uma regra do pipeline. Por exemplo, "primeiro relato ligado ao registro, da fase do card" ⇒ publicação primária. Fica registrado, mas **não autoriza nem bloqueia** atualização automática (`autoriza_automacao: false`).
- **`machine_verified`**: fato de identidade ou de relação bibliográfica demonstrado por fontes estruturadas independentes, sem conflito. **Não é confirmação clínica.**
- **`human_confirmed`**: veio de `db_decisoes.json` (tipo `classificacao`).

### Famílias de evidência e regras (`db_confianca.py`)

| Família | O que prova |
|---|---|
| A | Ligação PubMed: `NCT[si]`, DataBank do artigo, DERIVED do CT.gov. São **uma** família, porque saem do mesmo metadado |
| B | RESULT declarado pelo patrocinador no CT.gov |
| C | O nome do estudo (sigla do card) está no registro do CT.gov |
| F | O nome do estudo está no título ou abstract do artigo |
| G | Autor e ano do nome do card ("Hadoux, 2014") confirmados no PubMed |
| D | Números do `primario` no abstract |
| E | `titulo_full` idêntico ao título do PubMed |

C, F e G usam o que o editor escreveu, e por isso independem do PMID.

D e E não independem: o título e os números do card costumam ter sido copiados do artigo citado, e quando o PMID está errado eles vêm errados junto (a auditoria achou cards com o título do artigo de outro estudo). D e E só complementam.

As regras de identidade valem só **sem conflito**:

| Regra | Condição | Em palavras |
|---|---|---|
| MV-1 | A ∧ B ∧ (C∨F∨D∨E) | Ligação no PubMed e declaração do patrocinador, mais alguma concordância do card |
| MV-2 | (A∨B) ∧ C ∧ (F∨D∨E) | Ligação, nome do estudo no registro e alguma concordância com o artigo |
| MV-3 | (A∨B) ∧ F ∧ (D∨E) | Ligação, nome do estudo no artigo e conteúdo do card saído do artigo |
| MV-3b | (A∨B) ∧ card sem nome de estudo ∧ D ∧ E | Card sem sigla, mas ligado e com título e números saídos do artigo |
| MV-4 | ¬A ∧ ¬B ∧ C ∧ F ∧ (D∨E) | Artigo antigo, sem ligação nos metadados, mas com o nome do estudo no registro e no artigo |
| MV-5 | sem registro ∧ G ∧ (D∨E) | Estudo não registrado, com autor e ano confirmados |
| MV-6 | sem PMID ∧ C | Card de desenho ou abstract cuja sigla está no registro |

São conflitos:
- o DataBank do artigo declara outro NCT;
- o mesmo PMID aparece em cards sem NCT em comum;
- o PMID ou o NCT não existe;
- o título é de outra coorte do NCT;
- o DOI diverge entre o PubMed e o ID Converter.

### Automação por domínio

Cada card traz `automation.{identity, bibliographic_metadata, publication_relationship, clinical_extraction, published_write}`. `autorizado` significa uso automático **dentro do pipeline**: arquivar, deduplicar, acompanhar. `clinical_extraction` e `published_write` nunca são autorizados nesta fase.

### Prioridade

Todo candidato tem `evidence_confidence` e `clinical_materiality` em eixos separados. Alta confiança com baixa materialidade não vai para decisão.

| Classe | Exemplos | Ação padrão |
|---|---|---|
| P0_INTEGRITY | Retratação, expressão de preocupação, PMID/NCT errado, publicação de outro ensaio | Humana. Metadado errado na fonte ou card dono legítimo do PMID: arquivar |
| P1_CLINICAL_UPDATE | Abstract que ganhou artigo; análise final ou atualização madura explícita no título, sem diferença de comparabilidade; correção com potencial clínico | Humana |
| P2_SECONDARY_OR_WATCH | Subgrupo, QoL, segurança, post hoc; follow-up não comparável; errata de impacto **indeterminado** | Acompanhar. Errata indeterminada: humana, porque nunca é presumida benigna |
| P3_BIBLIOGRAPHIC | DOI, ano, protocolo, outra coorte, errata administrativa | Arquivar |
| WATCH_PUBLICATION_PENDING | `hasResults` ou RESULT sem publicação adequada | Acompanhar; a busca continua nas próximas execuções |

### Notas de correção (Fase 1.6, `db_correcoes.py`)

A fonte é a própria nota do periódico. Os canais servem só para recuperar o texto e valem apenas com PMID ou DOI idênticos aos da nota. Eles são tentados nesta ordem:
1. PMC full text XML;
2. Europe PMC (resumo do registro ou texto completo em acesso aberto);
3. Crossref/Crossmark, só para identidade e relação (`update-to`);
4. sem texto: `UNRESOLVED`.

Uma nota citada só pela referência é identificada antes pelo ECitMatch.

A classificação é feita **frase a frase**, depois de retirada a citação do artigo corrigido:

| Resultado | Quando | Ação |
|---|---|---|
| CLINICAL_DATA | Alguma frase clínica ou de mudança de dado em figura/tabela | P1, humana |
| ADMINISTRATIVE ou PRESENTATIONAL | Todas as frases são administrativas, de apresentação ou neutras | P3, arquivada |
| UNRESOLVED | Sem texto, ou o texto não diz o que mudou | Acompanhada. Fica no baseline e não entra no inbox |

Retratação e expressão de preocupação são sempre P0 e ligam o `integrity_hold` do card: nenhuma automação clínica enquanto a decisão `approve` com id `integrity_hold:<uid>` não for registrada.

### Decisões de integridade

`db_decisoes.json` aceita `classificacao` com `campo: "integridade"` em dois valores, ambos com `evidencia` obrigatória:

- **`SOURCE_METADATA_ERROR`:** exige `evidencia.nct_declarado_pelo_artigo` e só resolve **esse** conflito, enquanto o card citar o mesmo PMID.
- **`EDITORIAL_QUARANTINE`:** liga o `integrity_hold` do card e arquiva os sinais dele. É interna ao pipeline: não altera o `data.js` nem o frontend.

Outros tipos aceitos:

- **`campo: "publicacao_primaria"`:** fixa a primária do estudo, que passa a `human_confirmed`.
- **`approve` com `id: "integrity_hold:<uid>"`:** libera o hold. A ocorrência permanece em `integrity_hold.historico`.

Um artigo que é a publicação representada de **outro** card, sem NCT em comum, nunca é a primária inferida.

### Conflito dentro da mesma fonte (`WITHIN_SOURCE_CONFLICT`)

Aplica-se quando duas partes da **mesma** publicação (abstract, texto, tabela) dão valores diferentes para a mesma medida. Os achados ficam em `db_conflitos_fonte.json`, versionado como estado canônico (ver Arquivos): cada ocorrência traz trecho, seção, valor, população, denominador, endpoint, timepoint e método.

`db_confianca.avaliar_conflito_na_fonte` compara as ocorrências:

| Resultado | Quando | Efeito |
|---|---|---|
| EXPLICADA | Algum contexto difere, ou é só arredondamento | Registra o contexto; não bloqueia |
| WITHIN_SOURCE_CONFLICT | Todo o contexto é igual e os valores são incompatíveis, **ou** falta documentar o contexto | Bloqueia **só** os campos listados (`clinical_extraction.campos_bloqueados`). O card não pode apresentar um dos valores como fato |

Nenhuma das classes autoriza atualização clínica automática. O achado vale enquanto o card citar o mesmo PMID.

### Quarentena editorial por neutralização

É a opção aplicada ao `ppgl_8`.

- **Muda:** o conteúdo clínico sem fonte vira o aviso "Em revisão editorial — conteúdo temporariamente retirado até verificação das fontes primárias.", e o `status` passa a "Em revisão editorial".
- **Fica:** uid, categoria, contagem, links, favoritos e notas.
- **Pipeline:** a decisão `EDITORIAL_QUARANTINE` (com `pmid: "*"`) mantém o `integrity_hold` ligado.

### Rechecagem das correções UNRESOLVED

A rechecagem roda por `python3 scripts/db_correcoes.py --rechecar-unresolved` e é **mensal**; `--forcar` ignora o intervalo.

- Só as notas UNRESOLVED voltam aos canais.
- O estado fica em `_db_estado.json → correcoes` e só avança numa rechecagem completa.
- Uma errata volta ao inbox **apenas** na transição UNRESOLVED → CLINICAL_DATA.
- UNRESOLVED → ADMINISTRATIVE/PRESENTATIONAL é arquivada.
- UNRESOLVED → UNRESOLVED segue estacionada, sem alerta.

### Migrações (`db_migracao_*`)

Aplicam decisões humanas sobre estudos nomeados, sempre numa **cópia** (`scripts/_db_copia/data.js`).

- Cada troca confere o valor atual exato; se algum divergir, nada é gravado.
- A serialização é idêntica à do publicado, e o `uid` não muda.
- Cada troca gera uma linha em `_db_proveniencia_*.jsonl`.
- Por citarem estudos, ficam fora da trava de "nenhuma regra específica" dos módulos de detecção.

### Baseline × prioridade

O baseline guarda os fatos do dia zero. A prioridade é recalculada a cada relatório com as regras e as decisões vigentes, e o baseline não é reescrito.

O que não é determinável com segurança fica `null`, com `requires_review: true` e o motivo.

## Regra de maturidade

A ordem é: press release < abstract < artigo com análise interina < publicação da análise primária < análise final ou atualização madura.

Uma publicação só poderia substituir a representada, numa proposta futura, quando todas estas condições valem:
- a análise é **comparável**: mesma população (ITT × subgrupo, global × biomarcador), mesmo endpoint (primário × secundário, PFS × PFS2), mesma avaliação (BICR × investigador) e mesma metodologia;
- a maturidade é igual ou superior;
- a origem é `explicit` ou `human_confirmed`.

`db_registro.comparabilidade()` só anota:
- `comparavel` é `False` quando há diferença detectada;
- nos outros casos é `None`, porque não achar diferença não prova que as análises sejam comparáveis;
- na dúvida, a decisão é humana.

## Fase 1: sinais de alta prioridade

Só estes geram alerta:
1. `apresentado_publicado`: card "Apresentado" com artigo revisado por pares ligado ao registro, publicado a partir do ano do congresso.
2. `publicado_sem_pmid`: card "Publicado" sem `pubmed_url`, com relato de ensaio tipado no PubMed e ligado ao registro.
3. `correcao`: errata, expressão de preocupação ou retratação do artigo do card.
4. `ctgov`: mudança relevante contra o snapshot anterior (`hasResults`, `resultsFirstPostDate`, referência RESULT nova, status COMPLETED/TERMINATED/WITHDRAWN/SUSPENDED). Sem snapshot anterior, só uma divergência clara com o card.
5. `inconsistencia_pmid_nct`: pode ser qualquer um destes casos:
   - o artigo declara outro NCT no DataBank;
   - o mesmo PMID aparece em cards sem NCT em comum;
   - o PMID não existe;
   - o NCT não existe;
   - o título é de outra coorte do NCT.

Todo o resto vai para o baseline na primeira fotografia e não volta como alerta. Depois do baseline, um artigo novo sem sinal alto aparece uma vez no relatório como informativo e passa a constar em `_db_estado.json`.

## Segurança da coleta

- Resposta malformada ou incompleta do PubMed, do CT.gov ou do ID Converter: nova tentativa; se persistir, aborta com código 2 e não grava relatório, baseline nem estado.
- Ausência só é aceita quando a fonte a confirma (404 no CT.gov, erro explícito do esummary).
- `--reusar-coleta` é simulação: gera relatórios, mas não cria baseline nem avança o estado.

## Uso

```
python3 scripts/db_freshness.py                 # coleta nova, registro, sinais; cria o baseline se não existir
python3 scripts/db_freshness.py --reusar-coleta # simulação sobre a última coleta
python3 scripts/db_freshness.py --reusar-coleta --migrar-baseline-v1  # uma vez: v1 sem decisões → v2
python3 scripts/db_registro.py                  # só o registro de identidade
python3 scripts/test_db_freshness.py
```

As variáveis `NCBI_API_KEY` e `DB_CONTATO` são opcionais e servem para usar limites maiores no NCBI e o pool educado da Crossref. Sem elas, uma execução completa leva cerca de 15 minutos.
