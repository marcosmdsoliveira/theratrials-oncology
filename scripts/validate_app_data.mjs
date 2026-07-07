#!/usr/bin/env node
/* ============================================================================
 * validate_app_data.mjs — Validador dos JSONs públicos do app iOS
 *
 * Garante, de forma repetível (e pronto para CI), que os arquivos em app-data/
 * estão íntegros e coerentes com o manifest e com os datasets originais.
 *
 * Reaproveita a MESMA lógica do gerador (loadGlobals/buildPayload/DATASETS/
 * EXPLORER importados de export_app_data.mjs), de modo que a "regeneração-
 * espelho" percorre exatamente o mesmo caminho de código da geração.
 * Importar o gerador NÃO gera nada (ele tem guarda de entrada).
 *
 * Este validador é READ-ONLY: não escreve, não move e não altera nenhum
 * arquivo. Confirma inclusive que nenhum .js original mudou durante a execução.
 *
 * Verificações:
 *   - cada app-data/*.json faz parse válido;
 *   - manifest.json faz parse e tem schema/site/generatedAt/datasets;
 *   - para cada dataset gerado: sha256 e bytes do manifest conferem com o
 *     arquivo real, e o payload recomputado em memória (sandbox vm) é idêntico
 *     ao JSON publicado (detecta drift entre .js fonte e JSON commitado);
 *   - cada dataset tem url/version/sha256/bytes (e global quando aplicável);
 *   - explorer aponta para a URL canônica e seu sha256/bytes batem com
 *     assets/data/explorer.json;
 *   - o manifest NÃO inclui glossario nem tracker;
 *   - nenhum .js original foi alterado durante a validação.
 *
 * Exit 0 se tudo ok; exit 1 se qualquer falha.
 * Uso: node scripts/validate_app_data.mjs
 * ==========================================================================*/

import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';

import { DATASETS, EXPLORER, loadGlobals, buildPayload } from './export_app_data.mjs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.join(__dirname, '..');
const OUT_DIR = path.join(ROOT, 'app-data');

const sha256 = (buf) => crypto.createHash('sha256').update(buf).digest('hex');

let failures = 0;
let checks = 0;
const ok = (msg) => { checks++; console.log(`  PASS  ${msg}`); };
const fail = (msg) => { checks++; failures++; console.log(`  FAIL  ${msg}`); };
const check = (cond, msg) => (cond ? ok(msg) : fail(msg));

// --- 0) Hash dos .js originais ANTES (para provar que nada muda) --------------
const sourceFiles = [
  ...DATASETS.map((d) => d.source),
  'assets/js/glossario.js',
  EXPLORER.source,
];
const before = new Map();
for (const rel of sourceFiles) {
  before.set(rel, sha256(fs.readFileSync(path.join(ROOT, rel))));
}

// --- 1) Manifest existe, faz parse e tem estrutura básica ---------------------
console.log('\n[1] Manifest');
const manifestPath = path.join(OUT_DIR, 'manifest.json');
let manifest;
try {
  manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
  ok('manifest.json faz parse');
} catch (e) {
  fail(`manifest.json não faz parse: ${e.message}`);
  console.log('\nAbortando: manifest inválido.');
  process.exit(1);
}
check(typeof manifest.schema === 'string', 'manifest.schema presente');
check(typeof manifest.site === 'string' && manifest.site.startsWith('https://'),
  `manifest.site é https (${manifest.site})`);
check(typeof manifest.generatedAt === 'string', 'manifest.generatedAt presente');
check(manifest.datasets && typeof manifest.datasets === 'object', 'manifest.datasets presente');

const SITE = manifest.site;
const ds = manifest.datasets || {};

// --- 2) Exclusões obrigatórias nesta fase -------------------------------------
console.log('\n[2] Exclusões (glossario / tracker)');
check(!('glossario' in ds), 'manifest NÃO inclui glossario');
check(!('tracker' in ds), 'manifest NÃO inclui tracker');

// --- 3) Datasets gerados: parse, campos, sha256/bytes e regeneração-espelho ---
console.log('\n[3] Datasets gerados');
for (const d of DATASETS) {
  const entry = ds[d.name];
  if (!entry) { fail(`${d.name}: ausente no manifest`); continue; }

  // campos obrigatórios
  check(['url', 'version', 'sha256', 'bytes'].every((k) => k in entry),
    `${d.name}: tem url/version/sha256/bytes`);
  const expectGlobal = d.globals.length === 1 ? d.globals[0] : d.globals;
  check(JSON.stringify(entry.global) === JSON.stringify(expectGlobal),
    `${d.name}: global correto (${JSON.stringify(entry.global)})`);
  check(entry.url === `${SITE}/app-data/${d.out}`,
    `${d.name}: url pública correta (${entry.url})`);

  // arquivo real faz parse
  const filePath = path.join(OUT_DIR, d.out);
  let raw;
  try {
    raw = fs.readFileSync(filePath);
    JSON.parse(raw.toString('utf8'));
    ok(`${d.name}: ${d.out} faz parse`);
  } catch (e) {
    fail(`${d.name}: ${d.out} não faz parse: ${e.message}`);
    continue;
  }

  // sha256 + bytes reais vs manifest
  check(raw.length === entry.bytes, `${d.name}: bytes conferem (${raw.length})`);
  check(sha256(raw) === entry.sha256, `${d.name}: sha256 confere`);

  // regeneração-espelho: recomputa a partir do .js fonte e compara byte-a-byte
  try {
    const globalsObj = loadGlobals(d.source, d.globals);
    const payload = buildPayload(globalsObj, d.globals);
    const regen = Buffer.from(JSON.stringify(payload), 'utf8');
    check(sha256(regen) === sha256(raw),
      `${d.name}: JSON publicado == regeneração do .js fonte (sem drift)`);
  } catch (e) {
    fail(`${d.name}: regeneração-espelho falhou: ${e.message}`);
  }
}

// --- 4) Explorer: referenciado pela URL canônica, sha256/bytes do arquivo real -
console.log('\n[4] Explorer (referenciado)');
const ex = ds.explorer;
if (!ex) {
  fail('explorer: ausente no manifest');
} else {
  check(ex.url === `${SITE}${EXPLORER.publicPath}`,
    `explorer: URL canônica (${ex.url})`);
  check(!('global' in ex), 'explorer: sem global (é JSON, não window.*)');
  const exBuf = fs.readFileSync(path.join(ROOT, EXPLORER.source));
  check(exBuf.length === ex.bytes, `explorer: bytes conferem (${exBuf.length})`);
  check(sha256(exBuf) === ex.sha256, 'explorer: sha256 confere');
  try {
    JSON.parse(exBuf.toString('utf8'));
    ok('explorer: arquivo faz parse');
  } catch (e) {
    fail(`explorer: não faz parse: ${e.message}`);
  }
}

// --- 5) Nenhum .js original foi alterado durante a validação ------------------
console.log('\n[5] Integridade dos originais');
for (const rel of sourceFiles) {
  const after = sha256(fs.readFileSync(path.join(ROOT, rel)));
  check(after === before.get(rel), `${rel}: inalterado durante a validação`);
}

// --- Resultado ----------------------------------------------------------------
console.log(`\n${'='.repeat(60)}`);
console.log(`Checks: ${checks} | Falhas: ${failures}`);
if (failures === 0) {
  console.log('RESULTADO: OK — app-data/ íntegro e coerente com o manifest.');
  process.exit(0);
} else {
  console.log('RESULTADO: FALHA — ver itens marcados FAIL acima.');
  process.exit(1);
}
