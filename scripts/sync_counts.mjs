#!/usr/bin/env node
/**
 * sync_counts.mjs — mantém as contagens escritas no texto do site iguais às
 * dos arquivos de dados.
 *
 * Números como "79 ensaios clínicos ativos" estavam fixos no HTML e nos dois
 * arquivos de idioma. Toda vez que a curadoria publicava um lote, o texto da
 * home passava a mentir — e ninguém percebia, porque nada quebra.
 *
 *   node scripts/sync_counts.mjs           # reescreve o que estiver defasado
 *   node scripts/sync_counts.mjs --check   # não escreve; sai 1 se houver defasagem (CI)
 *
 * Para acrescentar uma frase nova ao site, basta acrescentar a regra aqui.
 */
import { readFileSync, writeFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import { dirname, join, relative } from 'node:path';

const require = createRequire(import.meta.url);
const RAIZ = join(dirname(fileURLToPath(import.meta.url)), '..');
const conferir = process.argv.includes('--check');

// ── Fonte da verdade: os próprios arquivos de dados ────────────────────────
global.window = {};
require(join(RAIZ, 'assets/js/data.js'));
const database = global.window.THERA_DATA.studies.length;
const categorias = global.window.THERA_DATA.categories.length;

global.window = {};
require(join(RAIZ, 'assets/js/trials_br.js'));
const ensaios = global.window.THERA_TRIALS_BR;
const brasil = ensaios.length;
// "áreas tumorais" = neoplasias de fato representadas, não o tamanho da
// taxonomia: a META pode declarar uma neoplasia que ainda não tem estudo.
const areas = new Set(ensaios.map((e) => e.neoplasia).filter(Boolean)).size;

const VALORES = { brasil, areas, database, categorias };

// ── Regras ─────────────────────────────────────────────────────────────────
// O lookahead garante que só o número é substituído; a frase fica intacta e a
// paridade PT/EN é mantida por ter uma regra para cada idioma.
//
// ANCORE a frase inteira. Uma regra solta como /\d+(?= categorias)/ parece
// inofensiva e casa com "classifica cada lesão em 5 categorias" do PROMISE /
// PSMA-RADS — reescrever aquele 5 para 40 corromperia conteúdo clínico sem
// quebrar nada. Ao acrescentar regra, rode --check antes e leia os trechos.
const REGRAS = [
  { re: /\d+(?= ensaios clínicos ativos)/g,      valor: 'brasil' },
  { re: /\d+(?= active clinical trials)/g,       valor: 'brasil' },
  { re: /\d+(?= estudos · \d+ áreas tumorais)/g, valor: 'brasil' },
  { re: /\d+(?= studies · \d+ tumor types)/g,    valor: 'brasil' },
  { re: /\d+(?= áreas tumorais)/g,               valor: 'areas' },
  { re: /\d+(?= tumor types)/g,                  valor: 'areas' },
  { re: /\d+(?= ensaios clínicos analisados)/g,  valor: 'database' },
  { re: /\d+(?= curated clinical trials)/g,      valor: 'database' },
  { re: /(?<=ensaios clínicos analisados em )\d+(?= categorias)/g, valor: 'categorias' },
  { re: /(?<=curated clinical trials in )\d+(?= categories)/g,     valor: 'categorias' },
];

const ARQUIVOS = ['index.html', 'trial-matcher.html', 'about.html',
                  'assets/lang/pt-br.js', 'assets/lang/en.js'];

let defasados = 0;
let corrigidos = 0;

for (const rel of ARQUIVOS) {
  const caminho = join(RAIZ, rel);
  let texto;
  try {
    texto = readFileSync(caminho, 'utf-8');
  } catch {
    continue; // arquivo opcional
  }
  const antes = texto;

  for (const { re, valor } of REGRAS) {
    const esperado = String(VALORES[valor]);
    // `alvo` é a string sendo varrida agora — usar `antes` daria linha e
    // trecho errados assim que a primeira regra mudasse o tamanho do texto.
    const alvo = texto;
    texto = texto.replace(re, (achado, pos) => {
      if (achado === esperado) return achado;
      defasados++;
      const linha = alvo.slice(0, pos).split('\n').length;
      const inicio = alvo.lastIndexOf('\n', pos) + 1;
      const trecho = alvo.slice(inicio, inicio + 78).split('\n')[0].trim();
      console.log(`  ${relative(RAIZ, caminho)}:${linha}  ${achado} -> ${esperado}`);
      console.log(`      ${trecho}…`);
      return esperado;
    });
  }

  if (texto !== antes && !conferir) {
    writeFileSync(caminho, texto, 'utf-8');
    corrigidos++;
  }
}

console.log(`\nvalores de referência: ${brasil} ensaios BR · ${areas} áreas tumorais · ` +
            `${database} estudos no database · ${categorias} categorias`);

if (!defasados) {
  console.log('contagens no texto: em dia');
  process.exit(0);
}

if (conferir) {
  console.error(`\nFALHA: ${defasados} contagem(ns) defasada(s) no texto do site.`);
  console.error('Rode `node scripts/sync_counts.mjs` para corrigir.');
  process.exit(1);
}

console.log(`${defasados} contagem(ns) corrigida(s) em ${corrigidos} arquivo(s).`);
