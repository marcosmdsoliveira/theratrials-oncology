# Review Center

Página **local** para a revisão humana dos resultados do discovery editorial e do delta. Ela registra decisões e não
aplica nada.

```bash
python3 scripts/db_v2/review_center.py          # http://127.0.0.1:8765  (Ctrl+C encerra)
```

Opções: `--porta`, `--state <pasta>` (padrão `scripts/db_v2/state`), `--decisoes <arquivo>` (padrão
`scripts/db_v2/review/decisions.json`). Não existe opção de host: o servidor só escuta em `127.0.0.1`.

## O que lê (somente leitura)

| Fonte | Uso |
|---|---|
| `state/discovery/fila_humana_blocoN.json` | Fila oficial por card (blocos com relatório correspondente; pilotos ficam de fora) |
| `state/discovery/relatorio_blocoN.json` | Linha completa de cada publicação: relação, vereditos, evidência, comparação, checagens |
| `state/discovery/<uid>/packet.json`, `estado.json` | Periódico do candidato e versão do pipeline do card |
| `state/delta/relatorio_blocoN.json`, `state/delta/<delta_id>/` | Itens do delta (`current` → `proposed`, trecho-fonte, vereditos) e `item_id` do curator |
| `assets/js/data.js` | Campo atual do card, para avisar quando o trecho ATUAL não existe mais |

## O que mostra

Só os pacotes que exigem decisão, organizados por card. Primeiro vêm os cards com UPDATE_CARD, depois HUMAN_REVIEW,
depois ADD_SECONDARY.

- **UPDATE_CARD**: um item por trecho do delta, com campo, ATUAL, PROPOSTO, evidência literal, `safe_delta`, os
  vereditos do discovery e do delta, a relação e os avisos. Itens HUMAN_REVIEW do delta vêm sem texto proposto. Nunca
  há reescrita do card.
- **ADD_SECONDARY**: card-pai, publicação, periódico e data, PMID/DOI, relação, população, endpoint/análise, motivo,
  evidência e vereditos. A pergunta é se a publicação merece card próprio. O card não é criado.
- **HUMAN_REVIEW**: ação HUMAN_REVIEW e qualquer item sem PASS. Mostra a dúvida objetiva, o verifier, os conflitos e a
  evidência.

O veredito exibido para um trecho do delta é o pior entre o do discovery e o do delta.

## Decisões

`APPROVE`, `REJECT` ou `DEFER`, com comentário opcional. O registro vai para `scripts/db_v2/review/`, que fica fora do
`state/` e é ignorado pelo Git:

- `decisions.json`: decisão atual por `decision_id`. Cada registro guarda uid, publicação, pacote, ação original,
  `delta_id`, `field_path`, `item_id`, versões do pipeline, decisão, comentário, data, revisão e `fingerprint`.
- `history.jsonl`: histórico append-only. Cada mudança é uma linha nova, com a decisão anterior.

O `decision_id` é calculado de forma determinística a partir de uid, publicação, pacote, campo e item. O
`fingerprint` resume o conteúdo revisado. Se o item mudar depois (novo run ou card editado), a decisão fica **STALE**
e volta a exigir revisão. A API recusa decisões enviadas sobre um conteúdo desatualizado (HTTP 409).

**Decisão ≠ aplicação.** Nada aqui altera `data.js`, `secondary-cards.js`, `app-data/` ou `state/`. A ferramenta não
cria card, não commita, não chama LLM nem API externa e não executa comandos.

## Segurança

- Bind fixo em `127.0.0.1`. O cabeçalho `Host` precisa ser `127.0.0.1:<porta>` ou `localhost:<porta>`, o que protege
  contra DNS rebinding.
- Rotas fixas: `/`, `/app.js`, `/app.css`, `/api/items` e `POST /api/decision`. Nenhum caminho de arquivo vem da URL.
- O POST exige `Content-Type: application/json`, o cabeçalho `X-Review-Center: 1` e `Origin` local quando presente.
- Respostas com CSP restrita, `nosniff` e `no-store`. O JSON escapa `<`, `>` e `&`. A interface insere conteúdo só
  com `textContent`.
- Os links usam só os identificadores existentes: PubMed (PMID numérico) e doi.org (DOI `10.x/...`).

## Testes

```bash
cd scripts/db_v2/agents && python3 -m unittest tests.test_review_center -v
```

São 17 testes, que rodam também no CI dentro da suíte dos agentes. Eles usam um state sintético e um arquivo de
decisões temporário. O teste com os blocos reais é pulado quando o state local não existe.
