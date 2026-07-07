#!/usr/bin/env node
/* ============================================================================
 * export_app_data.mjs — Gerador de JSONs públicos para o app iOS
 *
 * Objetivo (Fase 0):
 *   O site https://theratrials.com é a fonte oficial dos dados. Este gerador
 *   lê os datasets FINAIS existentes (os .js que hoje alimentam o site) e
 *   produz JSONs estruturados que o app iOS poderá baixar remotamente.
 *   O app consome JSON — nunca JavaScript remoto. A lógica permanece no bundle.
 *
 * Regras que este script respeita:
 *   - NÃO modifica nenhum dataset original (.js). Apenas lê.
 *   - Executa os datasets baseados em `window.*` num sandbox `vm` isolado,
 *     sem acesso a require/process/fs/fetch — só um objeto `window` inerte.
 *   - NÃO executa glossario.js (adiado nesta fase; depende de DOM/runtime).
 *   - NÃO inclui `tracker` (não há dataset/global próprio — apenas página).
 *   - explorer.json NÃO é regerado: é referenciado no manifest pela URL
 *     canônica /assets/data/explorer.json (já é JSON servido pelo site).
 *
 * Saídas (geradas somente quando o script é executado diretamente):
 *   app-data/data.json
 *   app-data/guidelines-data.json
 *   app-data/trials_br.json
 *   app-data/secondary-cards.json
 *   app-data/manifest.json   (URL pública, versão/data, SHA-256, bytes, global)
 *
 * Uso (quando autorizado a rodar):
 *   node scripts/export_app_data.mjs
 *
 * Nota: importar este módulo NÃO gera nada. A geração só ocorre quando ele é
 *       invocado como script (ver guarda no final).
 * ==========================================================================*/

import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.join(__dirname, '..');        // .../site
const OUT_DIR = path.join(ROOT, 'app-data');    // destino dos JSONs gerados

// URL base pública (fonte oficial dos dados).
const SITE_URL = 'https://theratrials.com';

// Datasets gerados a partir dos .js atuais.
// `globals` lista as globais `window.*` a extrair (a primeira é a principal).
//   - 1 global  -> o JSON é o valor dessa global (mantém o shape original).
//   - N globais -> o JSON é um objeto { <nomeGlobal>: <valor>, ... }.
const DATASETS = [
  {
    name: 'data',
    source: 'assets/js/data.js',
    out: 'data.json',
    globals: ['THERA_DATA'],
  },
  {
    name: 'guidelines-data',
    source: 'assets/js/guidelines-data.js',
    out: 'guidelines-data.json',
    globals: ['GUIDELINES_DATA'],
  },
  {
    name: 'trials_br',
    source: 'assets/js/trials_br.js',
    out: 'trials_br.json',
    // trials_br expõe os dados + metadados; preservamos ambos.
    globals: ['THERA_TRIALS_BR', 'THERA_TRIALS_BR_META'],
  },
  {
    name: 'secondary-cards',
    source: 'assets/js/secondary-cards.js',
    out: 'secondary-cards.json',
    globals: ['THERA_SECONDARY'],
  },
];

// explorer.json: já é JSON servido pelo site. Apenas REFERENCIADO no manifest
// pela URL canônica — não é regerado nem copiado.
const EXPLORER = {
  name: 'explorer',
  source: 'assets/data/explorer.json',
  publicPath: '/assets/data/explorer.json',
};

/**
 * Executa um dataset `.js` num sandbox `vm` isolado e devolve as globais pedidas.
 * O sandbox expõe apenas um `window` inerte (sem require/process/fs/fetch), de
 * modo que datasets puramente declarativos (`window.X = {...}`) funcionam, mas
 * qualquer dependência de DOM/runtime falha de forma explícita — nunca silenciosa.
 */
function loadGlobals(sourceRel, globalNames) {
  const abs = path.join(ROOT, sourceRel);
  const code = fs.readFileSync(abs, 'utf8');

  const windowObj = {};
  const sandbox = { window: windowObj };
  sandbox.self = windowObj;        // no topo do browser, window === self
  sandbox.globalThis = sandbox;    // referências a globalThis apontam ao contexto

  const context = vm.createContext(sandbox);
  vm.runInContext(code, context, { filename: abs, timeout: 5000 });

  const out = {};
  for (const g of globalNames) {
    if (!(g in windowObj)) {
      throw new Error(`Global window.${g} não encontrada em ${sourceRel}`);
    }
    out[g] = windowObj[g];
  }
  return out;
}

/** Monta o payload JSON preservando o shape original (ver DATASETS). */
function buildPayload(globalsObj, globalNames) {
  if (globalNames.length === 1) return globalsObj[globalNames[0]];
  const obj = {};
  for (const g of globalNames) obj[g] = globalsObj[g];
  return obj;
}

const sha256 = (buf) => crypto.createHash('sha256').update(buf).digest('hex');

/**
 * Gera todos os JSONs + o manifest.
 * Só é chamado quando o script roda diretamente (não ao ser importado).
 */
function main() {
  const generatedAt = new Date().toISOString();

  fs.mkdirSync(OUT_DIR, { recursive: true });

  const datasets = {};

  // 1) Datasets gerados a partir dos .js (via sandbox vm).
  for (const ds of DATASETS) {
    const globalsObj = loadGlobals(ds.source, ds.globals);
    const payload = buildPayload(globalsObj, ds.globals);
    const buf = Buffer.from(JSON.stringify(payload), 'utf8'); // compacto e determinístico

    fs.writeFileSync(path.join(OUT_DIR, ds.out), buf);

    datasets[ds.name] = {
      url: `${SITE_URL}/app-data/${ds.out}`,
      file: `app-data/${ds.out}`,
      global: ds.globals.length === 1 ? ds.globals[0] : ds.globals,
      bytes: buf.length,
      sha256: sha256(buf),
      version: generatedAt,
      generatedAt,
    };
    console.log(`[export] ${ds.out} — ${buf.length} bytes`);
  }

  // 2) explorer.json: apenas referenciado pela URL canônica.
  const exAbs = path.join(ROOT, EXPLORER.source);
  const exBuf = fs.readFileSync(exAbs);
  datasets[EXPLORER.name] = {
    url: `${SITE_URL}${EXPLORER.publicPath}`,
    file: EXPLORER.source,
    bytes: exBuf.length,
    sha256: sha256(exBuf),
    version: generatedAt,
    generatedAt,
    referenced: true, // não regerado; servido diretamente pelo site
  };
  console.log(`[export] explorer.json — referenciado (${exBuf.length} bytes)`);

  // 3) Manifest.
  const manifest = {
    schema: 'theratrials-app-data/1',
    site: SITE_URL,
    generatedAt,
    // glossario e tracker ficam de fora nesta fase (ver cabeçalho).
    datasets,
  };
  fs.writeFileSync(
    path.join(OUT_DIR, 'manifest.json'),
    JSON.stringify(manifest, null, 2),
  );
  console.log(`[export] manifest.json — ${Object.keys(datasets).length} entradas`);
}

// Guarda de entrada: só gera quando invocado como script (nunca ao importar).
const invokedDirectly =
  process.argv[1] && fileURLToPath(import.meta.url) === path.resolve(process.argv[1]);
if (invokedDirectly) main();

export { DATASETS, EXPLORER, loadGlobals, buildPayload, main };
