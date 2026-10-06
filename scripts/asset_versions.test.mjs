#!/usr/bin/env node --test
/* ============================================================================
 * asset_versions.test.mjs — cache busting dos JS/CSS contra o service worker real
 *
 * Reproduz o incidente de 2026-10-06: o sw.js serve HTML network-first e assets
 * cache-first (a query string faz parte da chave). Com common.js?v=11 fixo, o
 * database.html novo chegava com o common.js antigo do cache na 1ª visita após
 * o deploy → "TheraTrials.familyById is not a function".
 *
 * O sw.js de verdade roda num vm com Cache API, fetch e servidor simulados:
 *   deploy antigo (SW antigo ativo, common.js antigo no cache) → deploy novo →
 *   1º carregamento ainda sob o SW antigo → atualização do SW → 2º carregamento
 *   → offline. Um controle com ?v fixo prova que o teste pega o bug.
 * Tudo numa cópia temporária do site, versionada pelo próprio script.
 *
 *   node --test scripts/asset_versions.test.mjs
 * ==========================================================================*/
import test from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { mkdtempSync, cpSync, readFileSync, writeFileSync, readdirSync, rmSync, statSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import vm from 'node:vm';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';

const SITE = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
const ORIGEM = 'https://theratrials.com';
const SCRIPT = path.join(SITE, 'scripts', 'asset_versions.mjs');

// ── cópia temporária do site publicado (páginas + assets + sw.js) ─────────
const RAIZ = mkdtempSync(path.join(tmpdir(), 'asset-versions-'));
test.after(() => rmSync(RAIZ, { recursive: true, force: true }));
for (const nome of readdirSync(SITE)) {
  if (nome.endsWith('.html') || ['assets', 'sw.js', 'newsletters', 'app', 'proposta', 'manifest.json'].includes(nome)) {
    cpSync(path.join(SITE, nome), path.join(RAIZ, nome), { recursive: true });
  }
}
const versionar = (...args) => spawnSync('node', [SCRIPT, `--root=${RAIZ}`, ...args], { encoding: 'utf8' });
assert.equal(versionar().status, 0);
const ler = (rel) => readFileSync(path.join(RAIZ, rel), 'utf8');

// ── servidor, Cache API e service worker simulados ────────────────────────
class Resp {
  constructor(body, status = 200) { this.body = body; this.status = status; this.ok = status >= 200 && status < 300; }
  clone() { return new Resp(this.body, this.status); }
  async text() { return this.body; }
}
class Req {
  constructor(url, init = {}) {
    this.url = new URL(typeof url === 'string' ? url : url.url, `${ORIGEM}/`).href;
    this.method = 'GET'; this.mode = init.mode || 'no-cors';
    const accept = init.accept || '';
    this.headers = { get: (h) => (h.toLowerCase() === 'accept' ? accept : null) };
  }
}
const semQuery = (u) => u.split('?')[0];

function criarAmbiente() {
  const servidor = new Map();          // pathname (+query ignorada) → conteúdo publicado
  const amb = { servidor, offline: false, pedidosRede: [] };
  const caches = new Map();
  const cacheDe = (nome) => {
    if (!caches.has(nome)) {
      const itens = new Map();
      caches.set(nome, {
        itens,
        async match(req, op = {}) {
          const u = typeof req === 'string' ? new URL(req, `${ORIGEM}/`).href : req.url;
          if (itens.has(u)) return itens.get(u).clone();
          if (op.ignoreSearch) for (const [k, v] of itens) if (semQuery(k) === semQuery(u)) return v.clone();
          return undefined;
        },
        async put(req, res) { itens.set(typeof req === 'string' ? new URL(req, `${ORIGEM}/`).href : req.url, res); },
        async add(url) { const r = await amb.fetch(new Req(url)); if (!r.ok) throw new Error('404 ' + url); itens.set(new URL(url, `${ORIGEM}/`).href, r); },
      });
    }
    return caches.get(nome);
  };
  amb.caches = {
    open: async (n) => cacheDe(n),
    keys: async () => [...caches.keys()],
    delete: async (n) => caches.delete(n),
    match: async (req, op) => { for (const c of caches.values()) { const r = await c.match(req, op); if (r) return r; } return undefined; },
  };
  amb.cachesInternos = caches;
  amb.fetch = async (req) => {
    const u = new URL(typeof req === 'string' ? req : req.url, `${ORIGEM}/`);
    if (amb.offline) throw new TypeError('Failed to fetch');
    amb.pedidosRede.push(u.pathname + u.search);
    let p = u.pathname.replace(/^\//, '') || 'index.html';
    if (p.endsWith('/')) p += 'index.html';
    return servidor.has(p) ? new Resp(servidor.get(p)) : new Resp('not found', 404);
  };
  return amb;
}

// instala e ativa um sw.js (texto) no ambiente; devolve o handler de fetch
async function instalarSW(amb, swTexto) {
  const ouvintes = {};
  const self = {
    location: { origin: ORIGEM },
    addEventListener: (t, f) => { ouvintes[t] = f; },
    skipWaiting: () => {}, clients: { claim: async () => {} },
  };
  const ctx = vm.createContext({ self, caches: amb.caches, fetch: amb.fetch, URL, Response: Resp, console: { warn() {}, log() {} } });
  vm.runInContext(swTexto, ctx);
  const esperar = async (tipo) => { let p; ouvintes[tipo]({ waitUntil: (x) => { p = x; } }); await p; };
  await esperar('install');
  await esperar('activate');
  return async (req) => {
    let resp;
    ouvintes.fetch({ request: req, respondWith: (p) => { resp = p; } });
    return resp ? resp : amb.fetch(req);          // sem respondWith → o navegador busca direto
  };
}

// Carrega uma página como o navegador: navegação + todos os <script src> locais (+ dicionário do i18n)
async function carregarPagina(sw, pagina, lang = 'en') {
  const html = await (await sw(new Req(pagina, { mode: 'navigate', accept: 'text/html' }))).text();
  const base = new URL(pagina, `${ORIGEM}/`);
  const scripts = [...html.matchAll(/<script[^>]*\bsrc="([^"]+)"/g)].map((m) => new URL(m[1], base))
    .filter((u) => u.origin === ORIGEM);
  const corpos = {};
  for (const u of scripts) corpos[u.pathname.slice(1)] = { url: u.pathname + u.search, body: await (await sw(new Req(u.href))).text() };
  const i18n = corpos['assets/js/i18n.js'];
  if (i18n) {
    const mapa = JSON.parse((i18n.body.match(/var LANG_VERSIONS = (\{[^;]*\});/) || [, '{}'])[1]);
    const u = new URL(`assets/lang/${lang}.js${mapa[lang] ? '?v=' + mapa[lang] : ''}`, base);
    corpos[`assets/lang/${lang}.js`] = { url: u.pathname + u.search, body: await (await sw(new Req(u.href))).text() };
  }
  return { html, corpos };
}

// Executa data.js + common.js servidos e devolve a API TheraTrials resultante
function api(corpos) {
  const ctx = vm.createContext({ document: { addEventListener() {}, querySelectorAll() { return []; } }, console });
  vm.runInContext('var window = globalThis;', ctx);
  for (const k of ['assets/js/data.js', 'assets/js/common.js']) if (corpos[k]) vm.runInContext(corpos[k].body, ctx);
  return ctx.TheraTrials;
}

// ── deploy antigo: SW antigo (mesma estratégia, pré-cache sem versão) e common.js sem famílias ──
const COMMON_ANTIGO = 'window.TheraTrials = window.TheraTrials || {}; TheraTrials.studyTitle = function (e) { return e; };';
const SW_NOVO = ler('sw.js');
const SW_ANTIGO = SW_NOVO.replace(/const CACHE_VERSION = '[^']*'/, "const CACHE_VERSION = 'theratrials-v2026.01.01-antigo'")
  .replace(/(\.\/assets\/[^'?]+)\?v=[^']*/g, '$1');
const HTML_FIXO = (html) => html.replace(/(assets\/js\/common\.js)\?v=[^"]*/g, '$1?v=11');

function publicar(amb, { antigo }) {
  amb.servidor.clear();
  const andar = (dir) => {
    for (const nome of readdirSync(path.join(RAIZ, dir))) {
      const rel = dir ? `${dir}/${nome}` : nome;
      if (statSync(path.join(RAIZ, rel)).isDirectory()) andar(rel);
      else if (/\.(html|js|css|json)$/.test(nome)) amb.servidor.set(rel, readFileSync(path.join(RAIZ, rel), 'utf8'));
    }
  };
  andar('');
  if (antigo) {
    amb.servidor.set('assets/js/common.js', COMMON_ANTIGO);
    amb.servidor.set('sw.js', SW_ANTIGO);
    for (const [k, v] of amb.servidor) if (k.endsWith('.html')) amb.servidor.set(k, HTML_FIXO(v));
  }
}

async function cenarioPosDeploy({ htmlNovo }) {
  const a = await ambienteComVisitaAntiga();
  publicar(a.amb, { antigo: false });                        // deploy novo
  if (htmlNovo) a.amb.servidor.set('database.html', htmlNovo(a.amb.servidor.get('database.html')));
  const pagina = await carregarPagina(a.swAntigo, 'database.html');   // 1º carregamento: SW antigo ainda controla
  return { ...a, pagina };
}
async function ambienteComVisitaAntiga() {
  const amb = criarAmbiente();
  publicar(amb, { antigo: true });
  const swAntigo = await instalarSW(amb, SW_ANTIGO);
  const visita = await carregarPagina(swAntigo, 'database.html');    // visitante antigo: common.js?v=11 no cache
  assert.equal(visita.corpos['assets/js/common.js'].body, COMMON_ANTIGO);
  return { amb, swAntigo };
}

// ── testes ─────────────────────────────────────────────────────────────────
test('controle: com ?v fixo, o 1º carregamento pós-deploy recebe o common.js antigo (bug reproduzido)', async () => {
  const { pagina } = await cenarioPosDeploy({ htmlNovo: HTML_FIXO });
  assert.equal(pagina.corpos['assets/js/common.js'].body, COMMON_ANTIGO);
  assert.equal(typeof api(pagina.corpos).familyById, 'undefined');
});

test('1º carregamento pós-deploy (SW antigo, cache antigo): Database recebe o JS novo e funciona', async () => {
  const { pagina } = await cenarioPosDeploy({});
  const T = api(pagina.corpos);
  assert.equal(typeof T.familyById, 'function', 'TheraTrials.familyById is not a function');
  assert.equal(typeof T.familyUnitKind, 'function');
  assert.equal(typeof T.familiesToShow, 'function');
  // HTML e JS do mesmo deploy: cada script servido é exatamente o arquivo publicado
  for (const [rel, { url, body }] of Object.entries(pagina.corpos)) {
    assert.equal(body, ler(rel), `${url} veio de outro deploy`);
    assert.match(url, /\?v=[0-9a-f]{10}$/, `${rel} sem versão`);
  }
});

test('atualização normal do SW: pré-cache versionado, caches antigos removidos, 2º carregamento do cache', async () => {
  const { amb } = await cenarioPosDeploy({});
  const swNovo = await instalarSW(amb, SW_NOVO);
  const nomes = [...amb.cachesInternos.keys()];
  assert.ok(nomes.every((n) => !n.includes('antigo')), `cache antigo sobrou: ${nomes}`);
  amb.pedidosRede.length = 0;
  const pagina = await carregarPagina(swNovo, 'database.html');
  assert.equal(typeof api(pagina.corpos).familyById, 'function');
  for (const [rel, { body }] of Object.entries(pagina.corpos)) assert.equal(body, ler(rel), rel);
  // os assets vieram do cache (a rede só revalida em segundo plano)
  const estatico = [...amb.cachesInternos.entries()].find(([n]) => n.endsWith('-static'))[1];
  for (const { url } of Object.values(pagina.corpos)) assert.ok(estatico.itens.has(ORIGEM + url), `${url} fora do pré-cache`);
});

test('offline depois da atualização: página e todos os scripts versionados saem do cache', async () => {
  const { amb } = await cenarioPosDeploy({});
  const swNovo = await instalarSW(amb, SW_NOVO);
  // pré-cache cobre os assets compartilhados com a mesma URL versionada que as páginas pedem
  const estatico = [...amb.cachesInternos.entries()].find(([n]) => n.endsWith('-static'))[1];
  for (const rel of ['assets/js/data.js', 'assets/js/common.js', 'assets/js/i18n.js', 'assets/lang/en.js', 'assets/css/theratrials.css']) {
    assert.ok([...estatico.itens.keys()].some((k) => k.startsWith(`${ORIGEM}/${rel}?v=`)), `${rel} fora do pré-cache versionado`);
  }
  // uma visita online com o SW novo (o glossario.js, fora do CORE_ASSETS desde antes, entra no cache aqui)
  for (const lang of ['pt-br', 'en']) await carregarPagina(swNovo, 'database.html', lang);
  amb.offline = true;
  for (const lang of ['pt-br', 'en']) {
    const pagina = await carregarPagina(swNovo, 'database.html', lang);
    assert.match(pagina.html, /<title>/);
    for (const [rel, { url, body }] of Object.entries(pagina.corpos)) assert.equal(body, ler(rel), `offline: ${url}`);
    assert.equal(typeof api(pagina.corpos).familyById, 'function');
  }
});

test('todas as páginas: todo JS/CSS local tem ?v=<hash do conteúdo atual>', () => {
  const hashConteudo = (abs) => createHash('sha256').update(readFileSync(abs)).digest('hex').slice(0, 10);
  const vistos = new Map();
  const paginas = [];
  const andar = (dir) => { for (const n of readdirSync(path.join(RAIZ, dir))) { const r = dir ? `${dir}/${n}` : n; if (statSync(path.join(RAIZ, r)).isDirectory()) { if (n !== 'assets') andar(r); } else if (n.endsWith('.html')) paginas.push(r); } };
  andar('');
  assert.ok(paginas.length >= 27);
  for (const p of paginas) {
    for (const m of ler(p).matchAll(/\b(?:src|href)="((?:\.\.\/|\/)*)(assets\/[^"?]+\.(?:js|css))(\?v=([^"]*))?"/g)) {
      const rel = m[1].startsWith('/') ? m[2] : path.posix.normalize(path.posix.join(path.posix.dirname(p), m[1] + m[2]));
      if (!vistos.has(rel)) vistos.set(rel, hashConteudo(path.join(RAIZ, rel)));
      assert.equal(m[4], vistos.get(rel), `${p}: ${m[2]}`);
    }
  }
  assert.ok(vistos.has('assets/js/common.js') && vistos.has('assets/js/i18n.js') && vistos.has('assets/css/theratrials.css'));
});

test('versionamento é idempotente e só muda a URL do arquivo que mudou', () => {
  assert.equal(versionar('--check').status, 0, 'segunda passada não pode mudar nada');
  const antes = ler('index.html');
  const v = (html, f) => (html.match(new RegExp(`assets/js/${f}\\?v=([0-9a-f]+)`)) || [])[1];
  writeFileSync(path.join(RAIZ, 'assets/js/common.js'), ler('assets/js/common.js') + '\n// mudança\n');
  assert.equal(versionar('--check').status, 1, '--check acusa versão desatualizada');
  assert.equal(versionar().status, 0);
  const depois = ler('index.html');
  assert.notEqual(v(depois, 'common.js'), v(antes, 'common.js'));
  for (const f of ['data.js', 'i18n.js', 'pwa-install.js']) assert.equal(v(depois, f), v(antes, f), `${f} não mudou e manteve a URL`);
  assert.match(ler('sw.js'), new RegExp(`assets/js/common\\.js\\?v=${v(depois, 'common.js')}`));
});
