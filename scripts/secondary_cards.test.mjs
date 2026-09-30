#!/usr/bin/env node --test
/* ============================================================================
 * secondary_cards.test.mjs — resumo do card fechado das publicações secundárias
 *
 * - todo card auditado (auditStatus PASS) tem collapsedSummary curto (1–2 frases);
 * - collapsedSummary só existe em card auditado (nunca resumo fabricado);
 * - nenhum número do resumo fica fora dos campos já verificados do card;
 * - o card fechado do database.html não usa clinicalTakeaway (nem truncado)
 *   nem metadados bibliográficos longos.
 * ==========================================================================*/
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
const SITE = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
global.window = {};
require(path.join(SITE, 'assets', 'js', 'secondary-cards.js'));
const CARDS = window.THERA_SECONDARY;
const auditados = CARDS.filter(c => c.auditStatus && c.auditStatus.verification === 'PASS');
const frases = s => s.split(/(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÂÊÔÃÕÇ0-9])/).length;

test('todo card auditado tem collapsedSummary de 1–2 frases', () => {
  assert.ok(auditados.length > 0);
  for (const c of auditados) {
    assert.equal(typeof c.collapsedSummary, 'string', c.id);
    const s = c.collapsedSummary.trim();
    assert.ok(s.length >= 120 && s.length <= 260, `${c.id}: ${s.length} caracteres`);
    assert.ok(frases(s) <= 2, `${c.id}: ${frases(s)} frases`);
    assert.notEqual(s, c.clinicalTakeaway.trim(), `${c.id}: resumo igual ao takeaway`);
    assert.ok(!/(…|\.\.\.)$/.test(s), `${c.id}: resumo truncado`);
  }
});

test('collapsedSummary só existe em card auditado', () => {
  for (const c of CARDS) {
    if (!auditados.includes(c)) assert.equal(c.collapsedSummary, undefined, c.id);
  }
});

test('números do resumo existem nos campos verificados do card', () => {
  for (const c of auditados) {
    const corpus = JSON.stringify([c.title, c.parentTrialName, c.relationshipToParent, c.analysisType,
      c.evidenceMaturity, c.clinicalTakeaway, c.deep, c.analysis]);
    const novos = (c.collapsedSummary.match(/\d+(?:[.,]\d+)?/g) || []).filter(n => !corpus.includes(n));
    assert.deepEqual(novos, [], `${c.id}: números sem lastro nos campos verificados`);
  }
});

test('card fechado não usa clinicalTakeaway nem metadados longos', () => {
  const html = readFileSync(path.join(SITE, 'database.html'), 'utf8');
  const ini = html.indexOf('<template x-for="c in secondaryFor(selectedStudy.uid)"');
  assert.ok(ini > 0, 'template do card fechado não encontrado');
  const bloco = html.slice(ini, html.indexOf('</template>', ini));
  for (const proibido of ['clinicalTakeaway', 'titleOriginal', 'c.authors', 'analysisType', 'c.publicationStatus', '.slice(', 'substring(', 'truncate']) {
    assert.ok(!bloco.includes(proibido), `card fechado usa ${proibido}`);
  }
  assert.ok(bloco.includes('c.collapsedSummary'), 'card fechado não mostra collapsedSummary');
});
