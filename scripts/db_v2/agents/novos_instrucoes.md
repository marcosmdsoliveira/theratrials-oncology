# Modo NOVOS ENSAIOS (expansão de cobertura) — instruções para database-curator e database-verifier

Componente separado do discovery e do delta (versão própria em `new_trial_discovery.py`). A tarefa começa com
"MODO NOVOS ENSAIOS". Valem as mesmas regras de fonte das definições dos agentes: só as fontes do pacote contam como
evidência. Memória, web, Explorer, tracker e o texto de cards do TheraTrials como evidência são proibidos.

Pergunta central: **este ensaio representa um estudo relevante que ainda não tem card no Database?**

O card do TheraTrials é uma **síntese clínica concisa**. Nesta fase **não se redige card**. A saída é só a
proposta de entrada, com os dados mínimos para uma decisão humana.

## Entrada (pasta `state/novos/<cand_id>/`)
- `packet.json`:
  - `candidate`: dados do registro (NCT, título, fases, alocação, status, condições, intervenções, patrocinador);
  - `publications`: publicações ligadas (PMID, título, tipo);
  - `primary_publication_guess`: palpite determinístico da publicação primária;
  - `dedup`: resultado da deduplicação contra o Database. Só chegam aqui candidatos `NEW_STUDY_CANDIDATE`;
  - `database_context`: cards existentes do mesmo grupo tumoral. É **contexto de cobertura**, nunca evidência:
    serve para julgar se o ensaio acrescenta cobertura real ou se repete algo que o Database já tem. A lista traz
    no máximo 8 cards por grupo; o total de cards de cada grupo está em `database_coverage_by_group`. Não afirme
    que o Database "não tem" um tumor ou cenário quando o grupo tem cards que não aparecem na lista.
- `fontes/*.txt`: registro do CT.gov e resumos do PubMed, um parágrafo por linha (`¶0012 [Seção] texto`).

## Política editorial (adotada pelo editor; vale para curator e verifier)

**Fase 3 randomizado**: NEW_CARD quando a pergunta terapêutica ainda não está representada no Database. Resultado
positivo ou negativo pode entrar; estudo negativo relevante não se descarta por ser negativo.
→ `fase3_pergunta_nao_representada`

**Fase 2 randomizado**: NEW_CARD só com relevância clínica clara: comparação terapeuticamente útil, nova
classe/modalidade, doença rara ou cenário sem fase 3, potencial regulatório, resultado que possa alterar ou informar
conduta. → `fase2_randomizado_relevancia_clara`. **Fase 2 negativo**: por padrão WATCH ou NO_ACTION; NEW_CARD só se o
resultado negativo tiver valor clínico/editorial relevante → `fase2_negativo_relevante`.

**Fase 2 de braço único**: não entra por padrão. Exceções: radioligante/teranóstico, tumor-agnóstico, doença rara,
estudo registracional/aceleração regulatória, cenário sem comparador razoável →
`excecao_braco_unico_radioligante` / `_tumor_agnostico` / `_doenca_rara` / `_registracional` / `_sem_comparador`.

**Fase 1**: só excepcionalmente (first-in-class, radioligante, tumor-agnóstico, relevância regulatória ou clínica
clara) → `excecao_fase1`.

**Situações especiais**
- Comparador não padrão / análise não comparativa: não excluir automaticamente; descreva a limitação em
  `editorial_limitation`. Quando a falta de comparador adequado ou a natureza não comparativa da análise **afetar
  materialmente a interpretação do resultado → HUMAN_REVIEW obrigatório**. Ser fase 2 randomizado não basta para
  NEW_CARD direto (ex.: randomização só entre esquemas do mesmo fármaco, com resultado de análise não comparativa).
  As exceções de braço único (radioligante, tumor-agnóstico, doença rara, registracional, sem comparador razoável)
  continuam valendo.
- Técnica cirúrgica: fase 3 randomizado com desfecho oncológico clinicamente relevante → pode ser NEW_CARD
  (`cirurgia_randomizada_relevante`); **fase 2 randomizado de técnica cirúrgica → HUMAN_REVIEW**; estudo
  predominantemente técnico/perioperatório sem impacto oncológico relevante → NO_ACTION.
- Formulação subcutânea: NEW_CARD se registracional/não inferioridade com impacto real em administração, logística
  ou prática (`formulacao_sc_registracional`); caso contrário RELATED_TO_EXISTING ou NO_ACTION.
- Extensão regional: por padrão RELATED_TO_EXISTING / WATCH / NO_ACTION; NEW_CARD só se responder questão
  populacional/regulatória própria e clinicamente relevante (`extensao_regional_questao_propria`).
- Nova categoria de tumor: ausência de categoria no Database não é motivo de inclusão nem de exclusão; um estudo que
  cumpra os critérios pode inaugurar categoria.
- Congresso: fase 3 com resultado primário clinicamente relevante pode ser NEW_CARD com `maturity`
  `congress_provisional` (`congresso_fase3_provisorio`); fase 2 sem publicação madura tende a WATCH.
- Publicação sem NCT: a triagem tenta resolver a identidade; se o pacote indicar que pode ser o mesmo estudo de outro
  candidato ou de um card, use HUMAN_REVIEW — nunca dois NEW_CARD para o mesmo estudo.

`policy_basis` é obrigatório: o critério acima que sustenta a ação (`nao_se_aplica` para WATCH/NO_ACTION/HUMAN_REVIEW
sem critério específico).

## database-curator — o que produzir
JSON no schema `theratrials-db-novos-curator/1` (`agents/schemas/novos.schema.json`). Campos:

**Identificação**
- `study`: nome curto do estudo, com o acrônimo se houver.
- `nct`: o NCT do candidato.
- `main_publication`: `{pmid, doi}` da publicação primária, ou `null` se não houver.

**Descrição clínica**
- `tumor`: tumor e cenário, por exemplo "CHC avançado, 1ª linha".
- `intervention` e `comparator`: o que foi testado contra o quê.
- `phase`: fase e desenho, por exemplo "fase 3 randomizado aberto".
- `primary_endpoint`: o desfecho primário, como registrado ou publicado.

**Resultado**
- `main_result`: o resultado principal **com números copiados de um trecho-fonte citado**, em uma frase curta
  (por exemplo "OS mediana 16,4 vs 13,8 m; HR 0,78").
  - Ensaio sem resultados: `null`.
  - Nenhum número sem trecho em `evidence`.
- `maturity`:
  - `published_primary`: artigo primário com resultados;
  - `published_secondary_only`: só publicações secundárias;
  - `registry_results_only`: resultados só no CT.gov;
  - `ongoing_no_results`;
  - `undetermined`.

**Decisão**
- `action`:
  - `NEW_CARD`: merece **proposta de entrada** no Database, porque acrescenta cobertura real: ensaio relevante
    (fase 3, ou fase 2 randomizado com impacto) num cenário, droga ou indicação que o Database não cobre, ou que
    cobre só por outro ensaio.
  - `RELATED_TO_EXISTING`: na verdade é extensão, coorte, subestudo ou atualização de um ensaio que já tem card.
    Informe `related_card_uid`.
  - `WATCH`: relevante, mas imaturo (sem resultados, ou só abstract/congresso), ou dependente de publicação.
  - `NO_ACTION`: fora do escopo, sem relevância clínica, ou redundante.
  - `HUMAN_REVIEW`: dúvida objetiva, como uma possível duplicata não detectada ou fontes conflitantes.
- `reason`: por que a ação, em 1–3 frases, mencionando a lacuna de cobertura quando for NEW_CARD.
- `related_card_uid`: só quando houver relação; deve existir em `database_context`.
- `evidence`: trechos **literais** do pacote (`source_id`, `source_type`, `locator` com `¶NNNN`, `snippet`), que
  sustentam o desenho, o desfecho primário e o resultado principal. O `snippet` é só o texto: sem o prefixo
  `¶NNNN`, que vai no `locator`.
- `policy_basis`: o critério da política editorial (acima) que sustenta a ação.
- `comparison_type`: `randomizado_vs_padrao` (comparador padrão de tratamento), `randomizado_vs_nao_padrao`
  (comparador fraco/não padrão), `randomizado_nao_comparativo` (randomização sem comparação formal, ou resultado
  principal de análise não comparativa), `braco_unico`, `nao_se_aplica`.
- `editorial_limitation`: limitação que o editor precisa ver (comparador não padrão, endpoint substituto, extensão
  regional, maturidade de congresso), ou `null`.
- `notes_for_human`: o que o editor precisa saber, por exemplo "resultado só em abstract", "endpoint substituto"
  ou "fase 2 sem controle".

Regras:
- Não invente número, IC, p ou data. O que não está nas fontes fica `null`.
- Não descreva o card nem redija texto de card. Nada de takehome, limitações ou interpretação longa.
- Relevância não se presume pelo nome da droga. Use o desenho, o comparador, o desfecho e a maturidade descritos
  nas fontes.
- Fase 2 de braço único só é NEW_CARD com justificativa explícita (por exemplo, radioligante ou aprovação
  regulatória citada na fonte). Caso contrário, WATCH ou NO_ACTION.

## database-verifier — o que produzir
JSON no schema `theratrials-db-novos-verification/1` (`agents/schemas/novos_verification.schema.json`). Tente
**derrubar** a proposta. Você não recebe o `reason` do curator.
- `evidence_verdict`:
  - PASS: os trechos existem literalmente e sustentam desenho, desfecho e resultado;
  - FAIL: um número ou dado está errado;
  - UNSUPPORTED: falta suporte;
  - CONFLICT: as fontes discordam.
- `action_verdict`: a ação proposta se sustenta pelas fontes, pelo contexto de cobertura e pela **política editorial**
  acima (inclusive o `policy_basis` declarado)? Exemplos de reprovação: NEW_CARD para um ensaio imaturo, NEW_CARD
  que repete um card existente, fase 2 negativo como NEW_CARD sem valor clínico relevante, braço único sem exceção,
  RELATED sem relação real.
- `verdict`: o pior dos dois.
- `reason`: objetivo, citando `¶` quando possível.

Não corrija, não reescreva e não proponha texto. Ausência de evidência é UNSUPPORTED, nunca PASS.
