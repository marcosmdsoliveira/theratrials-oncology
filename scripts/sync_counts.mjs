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
// Dois números, e o site nunca pode confundir um com o outro (2026-09):
//   brasil            = estudos MAPEADOS (todos os cards, qualquer status)
//   brasil_recrutando = brazil_status === 'RECRUITING': ≥1 centro brasileiro
//                       RECRUITING confirmado no ClinicalTrials.gov. É o número
//                       de destaque. Card em REVIEW_REQUIRED fica FORA, mesmo
//                       com o rótulo 'Recrutando' (ROSETTA RCC-201, 2026-09).
// Card sem brazil_status (anterior à auditoria) usa o `status` como antes.
// Até 2026-09 o site chamava os 259 mapeados de "ensaios clínicos ativos",
// e 54 deles não tinham recrutamento confirmado no Brasil.
const brasil = ensaios.length;
const recrutandoBR = (e) => (e.brazil_status
  ? e.brazil_status === 'RECRUITING'
  : (e.status || 'Recrutando') === 'Recrutando');
const recrutando = ensaios.filter(recrutandoBR);
const brasil_recrutando = recrutando.length;
// "áreas tumorais" e "centros recrutadores" contam só quem recruta: um centro
// de estudo encerrado não é centro recrutador. Neoplasias de fato
// representadas, não o tamanho da taxonomia.
const areas = new Set(recrutando.map((e) => e.neoplasia).filter(Boolean)).size;
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
for (const e of recrutando) {
  for (const c of e.centros ?? []) {
    const m = RE_CENTRO.exec(c.trim());
    if (!m) continue;
    cidades.add(`${m[2]}/${m[3]}`);
    if (m[1]) instituicoes.add(`${m[1]}@${m[2]}`);
  }
}
const centros = instituicoes.size;

const VALORES = { brasil, brasil_recrutando, areas, database, categorias, centros };

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
  { re: /\d+(?="[^>]*>0<\/span>\s*<span class="counter-label" data-i18n="home\.statBRTrials")/g, valor: 'brasil_recrutando' },
  { re: /\d+(?="[^>]*>0<\/span>\s*<span class="counter-label" data-i18n="home\.statCenters")/g, valor: 'centros' },

  { re: /\d+(?= ensaios recrutando no Brasil)/g, valor: 'brasil_recrutando' },
  { re: /\d+(?= trials recruiting in Brazil)/g,  valor: 'brasil_recrutando' },
  { re: /\d+(?= estudos mapeados)/g,             valor: 'brasil' },
  { re: /\d+(?= studies mapped)/g,               valor: 'brasil' },
  { re: /\d+(?= áreas tumorais)/g,               valor: 'areas' },
  { re: /\d+(?= tumor types)/g,                  valor: 'areas' },
  { re: /\d+(?= ensaios clínicos analisados)/g,  valor: 'database' },
  { re: /\d+(?= curated clinical trials)/g,      valor: 'database' },
  { re: /(?<=ensaios clínicos analisados em )\d+(?= categorias)/g, valor: 'categorias' },
  { re: /(?<=curated clinical trials in )\d+(?= categories)/g,     valor: 'categorias' },

  // Rodapés, metatags e chamadas do database. São 37 ocorrências em 10
  // arquivos, e ficaram em 483 depois da curadoria de agosto porque nenhuma
  // regra daqui casava com estas frases.
  //
  // "estudos analisados" NÃO é seguro em qualquer arquivo: newsletters/2026-05
  // registra "421 estudos analisados", que é o retrato de maio e não pode ser
  // reescrito. A proteção é a lista ARQUIVOS abaixo — newsletters/ fica fora.
  // Pelo mesmo motivo assets/js/data.js e assets/data/explorer.js nunca entram:
  // lá "483" é n de randomizados, página de revista e valor de série.
  { re: /\d+(?= estudos analisados)/g,   valor: 'database' },
  { re: /\d+(?= studies analyzed)/g,     valor: 'database' },
  { re: /\d+(?= estudos selecionados)/g, valor: 'database' },
  { re: /\d+(?= selected studies)/g,     valor: 'database' },
  { re: /\d+(?= curated studies)/g,      valor: 'database' },

  // "Mais de N ensaios · M categorias" e a variante com "ensaios clínicos".
  // Os dois lados do separador são sincronizados.
  { re: /(?<=Mais de )\d+(?= ensaios(?: clínicos)? · )/g,  valor: 'database' },
  { re: /(?<=Over )\d+(?= (?:clinical )?trials · )/g,      valor: 'database' },
  { re: /(?<= ensaios(?: clínicos)? · )\d+(?= categorias)/g, valor: 'categorias' },
  { re: /(?<= (?:clinical )?trials · )\d+(?= categories)/g,  valor: 'categorias' },

  { re: /\d+(?= ensaios clínicos em \d+ categorias terapêuticas)/g, valor: 'database' },
  { re: /\d+(?= clinical trials in \d+ therapeutic categories)/g,   valor: 'database' },
  { re: /(?<=ensaios clínicos em )\d+(?= categorias terapêuticas)/g, valor: 'categorias' },
  { re: /(?<=clinical trials in )\d+(?= therapeutic categories)/g,   valor: 'categorias' },
];

// newsletters/ está deliberadamente fora: cada edição é um retrato datado.
const ARQUIVOS = ['index.html', 'trial-matcher.html', 'about.html',
                  'database.html', 'guidelines.html', 'guideline-detail.html',
                  'eventos.html', 'newsletter.html', 'lu-psma.html',
                  'assets/lang/pt-br.js', 'assets/lang/en.js'];

let defasados = 0;
let corrigidos = 0;
let violacoes = 0;

// ── Travas que nenhuma reescrita resolve ────────────────────────────────────
// 1. Frase proibida: o site não pode chamar os estudos mapeados de "ativos".
const PROIBIDAS = [/ensaios clínicos ativos/i, /active clinical trials/i, /ensaios ativos BR/i];
for (const rel of ARQUIVOS) {
  let texto;
  try { texto = readFileSync(join(RAIZ, rel), 'utf-8'); } catch { continue; }
  for (const re of PROIBIDAS) {
    const m = re.exec(texto);
    if (m) {
      violacoes++;
      const linha = texto.slice(0, m.index).split('\n').length;
      console.log(`  ${rel}:${linha}  frase proibida "${m[0]}" — use "recrutando no Brasil" ou "estudos mapeados"`);
    }
  }
}
// 2. Vitrine da home: cada card fixo tem de existir, ter o NCT do card e estar
//    'Recrutando'. Em 2026-09 ela anunciava como "Recrutando" um estudo
//    encerrado, um card inexistente e 4 NCTs de outros estudos.
{
  const porId = new Map(ensaios.map((e) => [e.id, e]));
  const home = readFileSync(join(RAIZ, 'index.html'), 'utf-8');
  const RE_SPOT = /<a href="trial-matcher\.html#([\w-]+)" class="ea-spot-card"[\s\S]*?<span class="nct">([^<]*)<\/span>/g;
  let n = 0;
  for (const [, id, nct] of home.matchAll(RE_SPOT)) {
    n++;
    const c = porId.get(id);
    const erro = !c ? 'card não existe no trials_br.js'
      : c.nct !== nct ? `NCT ${nct} ≠ ${c.nct} do card`
      : !recrutandoBR(c) ? `brazil_status '${c.brazil_status || c.status}' — a vitrine diz Recrutando`
      : '';
    if (erro) { violacoes++; console.log(`  index.html vitrine #${id}: ${erro}`); }
  }
  if (!n) { violacoes++; console.log('  index.html: vitrine não encontrada (o padrão mudou?)'); }
}

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

console.log(`\nvalores de referência: ${brasil_recrutando} recrutando no Brasil de ${brasil} mapeados · ${centros} centros ` +
            `em ${cidades.size} cidades · ${areas} áreas tumorais · ` +
            `${database} estudos no database · ${categorias} categorias`);

if (violacoes) {
  console.error(`\nFALHA: ${violacoes} problema(s) que a reescrita automática não resolve (acima).`);
  process.exit(1);
}

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
