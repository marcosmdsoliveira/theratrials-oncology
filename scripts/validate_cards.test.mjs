#!/usr/bin/env node --test
/* ============================================================================
 * validate_cards.test.mjs — o guard tem de reprovar quando deve
 *
 * Um validador que nunca reprova nada não prova nada: passa a dar a sensação
 * de cobertura sem cobrir. Aqui cada regra do validate_cards.mjs é exercitada
 * por INJEÇÃO DE DEFEITO — quebra-se o data.js de um jeito específico e
 * confere-se que o guard vê.
 *
 * Trabalha sobre uma cópia em diretório temporário, com a estrutura de pastas
 * que o validador espera (scripts/ e assets/js/ irmãos). O data.js real nunca
 * é tocado.
 *
 *   node --test scripts/
 * ==========================================================================*/
import test from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { mkdtempSync, mkdirSync, copyFileSync, writeFileSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const SITE = path.join(__dirname, '..');
const DATA = path.join(SITE, 'assets', 'js', 'data.js');

global.window = {};
require(DATA);
const ORIGINAL = global.window.THERA_DATA;
const bruto = readFileSync(DATA, 'utf8');
const CABECALHO = bruto.slice(0, bruto.indexOf('*/') + 3);

const raiz = mkdtempSync(path.join(tmpdir(), 'validate-cards-'));
mkdirSync(path.join(raiz, 'scripts'));
mkdirSync(path.join(raiz, 'assets', 'js'), { recursive: true });
copyFileSync(path.join(SITE, 'scripts', 'validate_cards.mjs'), path.join(raiz, 'scripts', 'validate_cards.mjs'));
test.after(() => rmSync(raiz, { recursive: true, force: true }));

/* spawnSync e não execFileSync: o validador escreve TUDO em stderr, como os
 * outros validadores da casa, e o execFileSync descarta stderr no sucesso. */
function rodarCom(mutar) {
  const d = JSON.parse(JSON.stringify(ORIGINAL));
  if (mutar) mutar(d);
  writeFileSync(path.join(raiz, 'assets', 'js', 'data.js'), `${CABECALHO}window.THERA_DATA = ${JSON.stringify(d)};\n`);
  const r = spawnSync('node', [path.join(raiz, 'scripts', 'validate_cards.mjs')], { encoding: 'utf8' });
  return { code: r.status, saida: (r.stdout ?? '') + (r.stderr ?? '') };
}

const bloqueia = (nome, mutar, trecho) =>
  test(`FAIL: ${nome}`, () => {
    const r = rodarCom(mutar);
    assert.equal(r.code, 1, `esperava exit 1, veio ${r.code}\n${r.saida}`);
    if (trecho) assert.match(r.saida, trecho);
  });

const avisa = (nome, mutar, trecho) =>
  test(`WARN: ${nome}`, () => {
    const r = rodarCom(mutar);
    assert.equal(r.code, 0, `WARN não pode bloquear; veio exit ${r.code}\n${r.saida}`);
    assert.match(r.saida, /WARN=[1-9]/);
    if (trecho) assert.match(r.saida, trecho);
  });

test('o data.js real passa', () => {
  const r = rodarCom(null);
  assert.equal(r.code, 0, `o data.js versionado deveria passar\n${r.saida}`);
  assert.match(r.saida, /FAIL=0/);
});

// ── integridade estrutural ────────────────────────────────────────────────
bloqueia('metadata.total_studies dessincronizado', (d) => { d.metadata.total_studies = 999; }, /total_studies/);
bloqueia('soma de categories\\[\\].count errada', (d) => { d.categories[0].count += 3; }, /count declarado/);
bloqueia('uid duplicado', (d) => { d.studies[5].uid = d.studies[4].uid; }, /uid duplicado/);
bloqueia('estudo em categoria não declarada', (d) => { d.studies[7].category_id = 'categoria_fantasma'; }, /não está declarado/);
bloqueia('category_name divergindo da categoria', (d) => { d.studies[9].category_name = 'Nome Errado'; }, /category_name/);

// ── schema núcleo congelado ───────────────────────────────────────────────
bloqueia('campo do núcleo removido', (d) => { delete d.studies[11].preparo; }, /núcleo ausente/);

// ── §7.1, os dois níveis ──────────────────────────────────────────────────
bloqueia(
  'número do resultado_chave que não existe em NENHUM campo',
  (d) => {
    const s = d.studies.find((x) => x.uid === 'net_gep_1');
    s.resultado_chave = 'mPFS 22,8 vs 8,5 m · HR 0,28 · OS 91,7 m';   // 91,7 não existe no card
  },
  /não existe em NENHUM campo/
);
avisa(
  'número do resultado_chave vindo de campo secundário',
  (d) => {
    const s = d.studies.find((x) => x.uid === 'net_gep_1');
    s.resultado_chave = 'mPFS 22,8 vs 8,5 m · HR 0,28 · ORR 43,0%';   // 43,0 está em `secundario`
  },
  /fora do primario/
);

/* O guard não pode confundir sigla com medida: `p53` não contém o número 53,
 * e `IC 95%` e `IC95%` são o mesmo intervalo. Os dois erros aconteceram de
 * verdade ao escrever este validador. */
test('não confunde sigla com número nem se importa com o espaço do IC', () => {
  const r = rodarCom((d) => {
    const s = d.studies.find((x) => x.uid === 'net_gep_1');
    s.primario = 'OS em p53-anormal 52,7% (IC95% 40,8-68,1)';
    s.resultado_chave = 'OS em p53-anormal 52,7% (IC 95% 40,8-68,1)';
  });
  assert.equal(r.code, 0, `espaço no IC e "p53" não podem gerar FAIL\n${r.saida}`);
  assert.doesNotMatch(r.saida, /net_gep_1 \| resultado_chave/);
});

// ── formato ───────────────────────────────────────────────────────────────
/* O `aprovacao` saiu do schema em 2026-08-09 — nada o renderizava, nem no site
 * nem no app. Se voltar, é campo ressuscitado sem leitor, e o guard avisa. */
avisa('campo aprovacao ressuscitado', (d) => { d.studies[13].aprovacao = 'FDA 2024 · EMA — · ANVISA —'; }, /voltou ao dataset/);
avisa('linha longa demais para o chip', (d) => { d.studies[15].linha = 'x'.repeat(95); }, /caracteres/);

/* Link de editora abre e leva ao artigo, então passa despercebido — mas fica
 * fora do validate_pubmed.mjs. Foi assim que 62 se acumularam, dois deles com
 * DOI que dava 404. */
bloqueia(
  'pubmed_url apontando para editora em vez do PubMed',
  (d) => { d.studies[17].pubmed_url = 'https://www.nejm.org/doi/full/10.1056/NEJMoa1606774'; },
  /não para o PubMed/
);
bloqueia(
  'pubmed_url com URL inválida',
  (d) => { d.studies[19].pubmed_url = 'nao-e-uma-url'; },
  /URL inválida/
);

// ── o card é lido sozinho ─────────────────────────────────────────────────
/* Marcação de triagem do autor e recado para si mesmo chegavam à tela: sete
 * cards traziam "Não-radiofármaco", "N/A para radiofármaco" ou "Verificar
 * protocolo específico do estudo" no campo `preparo`. */
bloqueia(
  'marcação interna de triagem em campo de prosa',
  (d) => { d.studies.find((x) => x.uid === 'net_gep_0').preparo = 'Não-radiofármaco; ver protocolo.'; },
  /marcação interna de triagem/
);
bloqueia(
  'recado do autor para si mesmo no preparo',
  (d) => { d.studies.find((x) => x.uid === 'net_gep_0').preparo = 'Verificar protocolo específico do estudo.'; },
  /marcação interna de triagem/
);

/* "Mesma pré-medicação intensiva" aponta para o card anterior na ordem do
 * arquivo — que ninguém tem à vista, porque o card abre isolado, por busca ou
 * por link compartilhado. */
bloqueia(
  'campo que abre apontando para o card vizinho',
  (d) => { d.studies.find((x) => x.uid === 'net_gep_0').tox_interesse = 'Mesmas reações infusionais do estudo anterior.'; },
  /referência relativa/
);

/* No campo `radiofarmaco`, "Não-radiofármaco" é a RESPOSTA à pergunta do
 * campo, não uma marcação em campo errado — 25 cards de contexto legítimos
 * reprovaram quando a checagem varria esse campo também. */
test('"Não-radiofármaco" é resposta válida no campo radiofarmaco', () => {
  const r = rodarCom((d) => { d.studies.find((x) => x.uid === 'net_gep_0').radiofarmaco = 'Não-radiofármaco'; });
  assert.equal(r.code, 0, `o campo radiofarmaco tem de aceitar esse valor\n${r.saida}`);
});

/* ── tags de formatação ────────────────────────────────────────────────────
 * Desde 2026-08-09 o annotateAbbr reabre <strong>, <em> e <br> — sem
 * atributo. O que estiver fora desse conjunto continua escapado e chega ao
 * leitor com os sinais à mostra, então o guard barra na entrada. */

bloqueia(
  'tag que o renderizador nao reabre (aparece literal na tela)',
  (d) => { d.studies[21].impacto_reg = 'Estudo <p>negativo</p> — nao mudou a pratica.'; },
  /tag que o renderizador não aceita/
);

bloqueia(
  'tag permitida mas COM atributo — o reabridor so aceita sem atributo',
  (d) => { d.studies[21].impacto_reg = 'Estudo <strong class="x">negativo</strong>.'; },
  /tag que o renderizador não aceita/
);

bloqueia(
  'tentativa de injecao em campo de texto',
  (d) => { d.studies[21].impacto_reg = 'Estudo negativo <img src=x onerror="alert(1)">.'; },
  /tag que o renderizador não aceita/
);

test('as tres tags de formatacao sao aceitas sem atributo', () => {
  const r = rodarCom((d) => {
    d.studies[21].impacto_reg = 'Estudo <strong>NEGATIVO</strong>.<br>Analise <em>post hoc</em> favoravel.';
  });
  assert.equal(r.code, 0, `<strong>, <em> e <br> tem de passar\n${r.saida}`);
});
