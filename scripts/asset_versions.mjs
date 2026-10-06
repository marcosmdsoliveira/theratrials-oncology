#!/usr/bin/env node
/* ============================================================================
 * asset_versions.mjs — cache busting determinístico dos JS/CSS locais
 *
 * O sw.js serve HTML network-first e assets cache-first, com a query string
 * como parte da chave do cache. Com uma versão fixa (common.js?v=11), o
 * database.html novo chegava junto com um common.js antigo do cache na 1ª
 * visita após o deploy (TheraTrials.familyById is not a function).
 *
 * Aqui cada asset ganha ?v=<hash do conteúdo> (sha256, 10 hex):
 *   - arquivo que muda → URL nova → o cache antigo não tem → vem da rede;
 *   - arquivo que não muda → mesma URL → continua servido do cache.
 * Reescreve, de forma idempotente:
 *   1. src/href de assets locais em todas as páginas HTML publicadas;
 *   2. o mapa de versões dos dicionários (assets/lang/*.js) dentro do i18n.js,
 *      que os carrega dinamicamente;
 *   3. a lista de pré-cache CORE_ASSETS do sw.js (o offline continua igual).
 * A estratégia do service worker não muda.
 *
 * Roda no workflow bump-sw-version.yml (o robô commita junto com o
 * CACHE_VERSION) e localmente antes do commit.
 *
 *   node scripts/asset_versions.mjs           # aplica
 *   node scripts/asset_versions.mjs --check   # sai 1 se algo está desatualizado
 * ==========================================================================*/
import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync, readdirSync, statSync, existsSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const SITE = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const CHECK = process.argv.includes('--check');
const raizArg = process.argv.find((a) => a.startsWith('--root='));
const RAIZ = raizArg ? path.resolve(raizArg.slice(7)) : SITE;

// Pastas que não são páginas publicadas do site (ferramentas locais, dependências)
const IGNORAR = new Set(['.git', 'node_modules', 'scripts', 'app-data', 'docs', '.github', '.playwright-mcp']);
const ASSET_RE = /\.(?:js|css)$/;

export const hashConteudo = (buf) => createHash('sha256').update(buf).digest('hex').slice(0, 10);

function paginas(dir = RAIZ, acc = []) {
  for (const nome of readdirSync(dir)) {
    if (IGNORAR.has(nome) || nome.startsWith('.')) continue;
    const p = path.join(dir, nome);
    if (statSync(p).isDirectory()) { if (nome !== 'assets') paginas(p, acc); }
    else if (nome.endsWith('.html')) acc.push(p);
  }
  return acc.sort();
}

const lerVersao = (cache, rel) => {
  if (!cache.has(rel)) {
    const abs = path.join(RAIZ, rel);
    cache.set(rel, existsSync(abs) ? hashConteudo(readFileSync(abs)) : null);
  }
  return cache.get(rel);
};

const mudancas = [];
function gravar(abs, antes, depois) {
  if (antes === depois) return;
  mudancas.push(path.relative(RAIZ, abs));
  if (!CHECK) writeFileSync(abs, depois);
}

// ── 1. i18n.js: mapa de versões dos dicionários (antes de calcular o hash do i18n.js) ──
const versoes = new Map();
{
  const abs = path.join(RAIZ, 'assets', 'js', 'i18n.js');
  const antes = readFileSync(abs, 'utf8');
  const langs = readdirSync(path.join(RAIZ, 'assets', 'lang')).filter((f) => f.endsWith('.js')).sort();
  const mapa = Object.fromEntries(langs.map((f) => [f.replace(/\.js$/, ''), hashConteudo(readFileSync(path.join(RAIZ, 'assets', 'lang', f)))]));
  const linha = `  var LANG_VERSIONS = ${JSON.stringify(mapa)}; // gerado por scripts/asset_versions.mjs`;
  const re = /^ {2}var LANG_VERSIONS = .*$/m;
  if (!re.test(antes)) throw new Error('i18n.js sem a linha LANG_VERSIONS');
  const depois = antes.replace(re, linha);
  gravar(abs, antes, depois);
  // o hash do i18n.js é o do conteúdo FINAL (com o mapa novo)
  versoes.set('assets/js/i18n.js', hashConteudo(Buffer.from(depois)));
  for (const f of langs) versoes.set(`assets/lang/${f}`, mapa[f.replace(/\.js$/, '')]);
}

// ── 2. páginas HTML: src/href de assets locais ────────────────────────────
const ATTR = /\b(src|href)="((?:\.\.\/|\.\/|\/)*)(assets\/[^"?#]+?)(?:\?v=[^"#]*)?"/g;
for (const abs of paginas()) {
  const antes = readFileSync(abs, 'utf8');
  const depois = antes.replace(ATTR, (m, attr, prefixo, rel) => {
    if (!ASSET_RE.test(rel)) return m;
    // resolve relativo à página (../assets em subpastas, /assets absoluto)
    const alvo = prefixo.startsWith('/') ? rel : path.relative(RAIZ, path.resolve(path.dirname(abs), prefixo + rel)).split(path.sep).join('/');
    const v = lerVersao(versoes, alvo);
    return v ? `${attr}="${prefixo}${rel}?v=${v}"` : m;
  });
  gravar(abs, antes, depois);
}

// ── 3. sw.js: pré-cache com as mesmas URLs que as páginas pedem ───────────
{
  const abs = path.join(RAIZ, 'sw.js');
  const antes = readFileSync(abs, 'utf8');
  const ini = antes.indexOf('const CORE_ASSETS = [');
  const fim = antes.indexOf('];', ini);
  if (ini < 0 || fim < 0) throw new Error('sw.js sem CORE_ASSETS');
  const bloco = antes.slice(ini, fim).replace(/'\.\/(assets\/[^'?]+?)(?:\?v=[^']*)?'/g, (m, rel) => {
    if (!ASSET_RE.test(rel)) return m;
    const v = lerVersao(versoes, rel);
    return v ? `'./${rel}?v=${v}'` : m;
  });
  gravar(abs, antes, antes.slice(0, ini) + bloco + antes.slice(fim));
}

if (CHECK) {
  if (mudancas.length) {
    console.error(`asset_versions: ${mudancas.length} arquivo(s) com versão desatualizada:\n  ${mudancas.join('\n  ')}`);
    console.error('Rode: node scripts/asset_versions.mjs');
    process.exit(1);
  }
  console.log('asset_versions: em dia');
} else {
  console.log(mudancas.length ? `asset_versions: ${mudancas.length} arquivo(s) atualizado(s)` : 'asset_versions: em dia');
}
