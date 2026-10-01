# Modo DELTA (UPDATE_CARD) — instruções para database-curator e database-verifier

Componente separado do discovery (versão própria em `delta.py`). A tarefa começa com "MODO DELTA".
Mesmas regras de fonte das definições dos agentes: só valem as fontes do pacote; memória, web e o texto do card
como evidência de si mesmo são proibidos.

O card primário é uma **síntese clínica concisa** do estudo, não um repositório de todos os dados publicados.

## Entrada (pasta `state/delta/<delta_id>/`)
- `packet.json`: a publicação que o discovery classificou como UPDATE_CARD (`candidate`), a relação aprovada, a
  publicação que o card representa hoje e `card_fields`: o texto ATUAL dos campos visíveis editáveis
  (`primario`, `secundario`, `resultado_chave`, `tox_g3`, `subgrupo`). `card_fields` diz o que o card mostra; não é
  evidência.
- `fontes/*.txt`: um parágrafo por linha, `¶0012 [Seção] texto`.

## database-curator — o que produzir
JSON no schema `theratrials-db-delta-curator/1` (`agents/schemas/delta.schema.json`). Para cada informação que o
card **já exibe** e que a publicação nova atualiza, um item:
- `field_path`: um dos campos de `card_fields`;
- `segment_current`: o trecho **literal** do campo atual que muda (copie exatamente; só o pedaço que muda);
- `segment_proposed`: o texto que substitui esse trecho, no mesmo estilo e tamanho; nada de contexto novo;
- `endpoint`: o desfecho a que o trecho se refere (ex.: OS, PFS, ORR, G≥3);
- `reason`: uma frase objetiva (ex.: "corte posterior, seguimento mediano maior");
- `evidence`: trecho(s) literal(is) da publicação nova, com `¶`, contendo cada número do `segment_proposed`;
- `decision`: `DELTA`.

Compare com os **campos visíveis**, não com o endpoint principal da análise: se o card representa PFS mas também
exibe OS, uma publicação que atualiza OS gera delta **só** no trecho de OS.

Proibido:
- reescrever o campo inteiro ou o card; gerar nova versão do card;
- acrescentar endpoint, subgrupo, toxicidade ou qualquer dado que o card ainda não exibe;
- expandir contexto, interpretação ou limitações;
- número sem trecho literal.

Se a informação nova não corresponde com segurança a um trecho existente (o card não exibe aquele endpoint, o
trecho atual é ambíguo, a população/corte diverge), não proponha texto: item com `decision: "HUMAN_REVIEW"`,
`segment_current`/`segment_proposed` nulos e `human_review_reason` objetivo, sem texto clínico novo.
Se nada do que o card exibe muda, `items: []` e explique em `notes_for_human`.

## database-verifier — o que conferir
Entrada `verifier_input.json` (itens sem o `reason` do curator). Para cada item `DELTA`, tente derrubar:
- o `segment_current` existe literalmente no campo `field_path` de `card_fields`;
- o `segment_proposed` é sustentado pelo trecho: cada número, braço, endpoint, medida, população e corte;
- o trecho é da mesma análise que o card exibe naquele trecho (não outro subgrupo, coorte ou endpoint);
- o `segment_proposed` não acrescenta informação que o trecho atual não tinha (nada de expansão).
Itens `HUMAN_REVIEW`: confira só que a dúvida é objetiva e não traz texto clínico novo.
Veredito por item: PASS / FAIL / UNSUPPORTED / CONFLICT, motivo e trecho. Nunca proponha outro texto.
Saída no schema `theratrials-db-delta-verification/1` (`agents/schemas/delta_verification.schema.json`).
