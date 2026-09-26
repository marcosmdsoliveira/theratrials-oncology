# Equivalência funcional — ferramentas.html

Prova, em Chrome real, que uma mudança em `ferramentas.html` não alterou nenhuma
ferramenta clínica. Criado na extração do JS inline (set/2026).

Não é carregado pelo site. Precisa de Node 20+ e do Google Chrome instalado
(`CHROME_PATH` aponta para outro binário, se necessário).

## O que cobre

| Arquivo | Verifica |
|---|---|
| `snapshot.mjs` | Captura o comportamento de uma versão da página: JSON completo de `TNM_DATA`, `CTCAE_DATA` e `CRIT_DATA`; os 61 modais, abertos **clicando no botão real**; e 2.747 combinações de entrada nas 6 calculadoras (dose, decaimento, função renal, ALBI, MELD, Child-Pugh), disparando os mesmos eventos `input`/`change` do usuário |
| `compare.mjs` | Compara dois snapshots campo a campo. Sai com código 1 em qualquer diferença |
| `features.mjs` | Testa o acesso rápido: busca, filtros, os 61 links `#slug`, teclado, mobile 390px e o app iOS simulado com o `native-guards.js` real |

O Umami é bloqueado durante os testes — as execuções não viram visitas na analytics.

## Como usar

```bash
cd scripts/equivalencia-ferramentas
npm install                                   # só na primeira vez

# 1. versão de referência: o HEAD, extraído para uma pasta temporária.
#    `-C ../..` é obrigatório: de dentro de uma subpasta, `git archive HEAD`
#    arquiva só a subpasta, e a referência sai vazia.
rm -rf /tmp/tt-ref && mkdir /tmp/tt-ref && git -C ../.. archive HEAD | tar -x -C /tmp/tt-ref
test -f /tmp/tt-ref/ferramentas.html || echo "ERRO: referência vazia

# 2. captura as duas versões e compara
node snapshot.mjs /tmp/tt-ref  /tmp/snap-ref.json
node snapshot.mjs ../..        /tmp/snap-atual.json
node compare.mjs  /tmp/snap-ref.json /tmp/snap-atual.json

# 3. funcionalidades do acesso rápido
node features.mjs ../.. ../../../../TheraTrials-iOS-exp/www/assets/js/native-guards.js /tmp/tt-shots
```

Rode `snapshot.mjs` duas vezes na mesma versão antes de confiar numa diferença:
as capturas são determinísticas (nenhuma calculadora usa data, hora ou aleatório),
e duas execuções seguidas devem produzir hashes idênticos.
