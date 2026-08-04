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
// Instituições DISTINTAS, não a soma dos cards. Somar dava 1042 para ~170
// centros reais: São Paulo aparece em 128 estudos e entrava 128 vezes. O
// rótulo é "Centros recrutadores", então o número tem de ser de instituições.
//
// Cada entrada é 'Instituição — Cidade / UF' ou só 'Cidade / UF' (registro que
// não nomeia o centro). A chave inclui a cidade: "Oncoclínicas" em São Paulo e
// no Rio são duas casas. Os anônimos ficam de fora da contagem — não dá para
// saber se dois "Research Site" em Curitiba são o mesmo centro, e contá-los
// separadamente reintroduziria a inflação que este cálculo existe para evitar.
const RE_CENTRO = /^(?:(.*?)\s*—\s*)?(.*?)\s*\/\s*([A-Z]{2})$/;
const instituicoes = new Set();
const cidades = new Set();
for (const e of ensaios) {
  for (const c of e.centros ?? []) {
    const m = RE_CENTRO.exec(c.trim());
    if (!m) continue;
    cidades.add(`${m[2]}/${m[3]}`);
    if (m[1]) instituicoes.add(`${m[1]}@${m[2]}`);
  }
}
const centros = instituicoes.size;

const VALORES = { brasil, areas, database, categorias, centros };

// ── Regras ─────────────────────────────────────────────────────────────────
// O lookahead garante que só o número é substituído; a frase fica intacta e a
// paridade PT/EN é mantida por ter uma regra para cada idioma.
//
// ANCORE a frase inteira. Uma regra solta como /\d+(?= categorias)/ parece
// inofensiva e casa com "classifica cada lesão em 5 categorias" do PROMISE /
// PSMA-RADS — reescrever aquele 5 para 40 corromperia conteúdo clínico sem
// quebrar nada. Ao acrescentar regra, rode --check antes e leia os trechos.
const REGRAS = [
  // Contadores animados da home: o número vive num atributo, não na frase.
  // A âncora é o data-i18n do rótulo irmão, que vem logo depois no HTML —
  // por isso o lookahead atravessa o resto da tag e a abertura do <span>.
  { re: /\d+(?="[^>]*>0<\/span>\s*<span class="counter-label" data-i18n="home\.statStudies")/g,  valor: 'database' },
  { re: /\d+(?="[^>]*>0<\/span>\s*<span class="counter-label" data-i18n="home\.statCategories")/g, valor: 'categorias' },
  { re: /\d+(?="[^>]*>0<\/span>\s*<span class="counter-label" data-i18n="home\.statBRTrials")/g, valor: 'brasil' },
  { re: /\d+(?="[^>]*>0<\/span>\s*<span class="counter-label" data-i18n="home\.statCenters")/g, valor: 'centros' },

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

console.log(`\nvalores de referência: ${brasil} ensaios BR · ${centros} centros ` +
            `em ${cidades.size} cidades · ${areas} áreas tumorais · ` +
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
