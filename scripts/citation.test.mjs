// Testes do renderer de citação do Database (assets/js/citation.js). Offline, sem dependências.
//   node --test scripts/citation.test.mjs
// Casos genéricos: nenhum teste depende de um estudo específico.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const C = require('../assets/js/citation.js');
const FORMATOS = ['vancouver', 'ama', 'abnt', 'plain'];

const autor = (family, given_initials, suffix) => (suffix ? { family, given_initials, suffix } : { family, given_initials });
const cit = (extra = {}) => ({
  publication_id: 'pmid:11111111', role: 'undetermined', pmid: '11111111', doi: '10.1000/xyz',
  authors: [autor('Autor', 'AB'), autor('Segundo', 'C')], authors_total: 2, first_author: 'Autor AB',
  title: 'A randomised trial of something', journal: 'Journal of Testing', journal_abbrev: 'J Test',
  year: 2024, volume: '12', issue: '3', pages: '100-110', publication_type: 'journal_article',
  metadata_source: 'pubmed_esummary', retrieved_at: '2026-09-29', ...extra,
});
const card = (extra = {}) => ({
  uid: 'c1', estudo: 'ESTUDO (2024)', acron: 'ESTUDO — teste', status: 'Publicado', ano_pub: 2022,
  sponsor: 'Patrocinador | PI: Fulano Beltrano (Hospital Central)', ref: 'Referência editorial do card, 2024.',
  pubmed_url: 'https://pubmed.ncbi.nlm.nih.gov/11111111/', nct: 'NCT00000001',
  nct_url: 'https://clinicaltrials.gov/study/NCT00000001', ...extra,
});
const todas = (s) => FORMATOS.map((f) => C.format(s, f));
const semSponsor = (s) => todas(s).forEach((t) => {
  for (const tok of ['Beltrano', 'Fulano', 'Hospital', 'Central', 'Investigadores']) assert.ok(!t.includes(tok), `${tok} em: ${t}`);
});

test('citação estruturada: autoria da publicação, nunca do PI (instituição entre parênteses)', () => {
  const s = card({ citation: cit() });
  assert.equal(C.kind(s), 'structured');
  assert.equal(C.format(s, 'vancouver'),
    'Autor AB, Segundo C. A randomised trial of something. J Test. 2024;12(3):100-110. doi:10.1000/xyz. PMID: 11111111.');
  semSponsor(s);
});

test('múltiplos PIs e PI diferente do primeiro autor não aparecem', () => {
  semSponsor(card({ sponsor: 'X | PI: Fulano Beltrano / Hospital Central', citation: cit() }));
  semSponsor(card({ sponsor: 'X | PI: Beltrano', citation: undefined }));        // fallback: ref literal
});

test('sobrenome composto e sufixo Jr.', () => {
  const s = card({ citation: cit({ authors: [autor('de Bono', 'JS'), autor('Wells', 'SA', 'Jr')], first_author: 'de Bono JS' }) });
  assert.match(C.format(s, 'vancouver'), /^de Bono JS, Wells SA Jr\. /);
  assert.match(C.format(s, 'abnt'), /^DE BONO, J\. S\.; WELLS JUNIOR, S\. A\. A randomised trial of something\. J Test, v\. 12, n\. 3, p\. 100-110, 2024\./);
});

test('autor coletivo sem autores pessoais', () => {
  const s = card({ citation: cit({ authors: [], authors_total: 0, collective_name: 'ESMO Guidelines Committee', first_author: 'ESMO Guidelines Committee', publication_type: 'guideline' }) });
  for (const t of todas(s)) assert.ok(t.startsWith('ESMO Guidelines Committee.'), t);
});

test('et al.: Vancouver 6, AMA 3 (>6), ABNT 1 (>3)', () => {
  const muitos = Array.from({ length: 6 }, (_, i) => autor(`Aut${i}`, 'X'));
  const s = card({ citation: cit({ authors: muitos, authors_total: 25, first_author: 'Aut0 X' }) });
  assert.match(C.format(s, 'vancouver'), /^Aut0 X, Aut1 X, Aut2 X, Aut3 X, Aut4 X, Aut5 X, et al\. /);
  assert.match(C.format(s, 'ama'), /^Aut0 X, Aut1 X, Aut2 X, et al\. /);
  assert.match(C.format(s, 'abnt'), /^AUT0, X\. et al\. /);
  const tres = card({ citation: cit({ authors: muitos.slice(0, 3), authors_total: 3, first_author: 'Aut0 X' }) });
  assert.match(C.format(tres, 'abnt'), /^AUT0, X\.; AUT1, X\.; AUT2, X\. /);
});

test('DOI e article number (e-page)', () => {
  const s = card({ citation: cit({ pages: undefined, article_number: 'e005755' }) });
  assert.match(C.format(s, 'vancouver'), /2024;12\(3\):e005755\./);
  assert.match(C.format(s, 'abnt'), /art\. e005755/);
  assert.ok(!C.format(card({ citation: cit({ doi: undefined }) }), 'vancouver').includes('doi:'));
});

test('metadados incompletos são omitidos, não inventados', () => {
  const s = card({ citation: cit({ volume: undefined, issue: undefined, pages: undefined, doi: undefined }) });
  assert.equal(C.format(s, 'vancouver'),
    'Autor AB, Segundo C. A randomised trial of something. J Test. 2024. PMID: 11111111.');
  assert.ok(!/undefined|null|NaN|\(\)|;:/.test(todas(s).join(' ')));
});

test('ano da citação = ano da publicação representada, não o ano_pub do card (follow-up / represented ≠ primary)', () => {
  const s = card({ ano_pub: 2019, citation: cit({ year: 2025, role: 'long_term' }) });
  for (const t of todas(s)) { assert.ok(t.includes('2025'), t); assert.ok(!t.includes('2019'), t); }
});

test('guideline e meta-análise usam o mesmo formato estruturado', () => {
  for (const tipo of ['guideline', 'meta_analysis']) {
    const t = C.format(card({ citation: cit({ publication_type: tipo }) }), 'ama');
    assert.match(t, /^Autor AB, Segundo C\. A randomised trial of something\. J Test\. 2024;12\(3\):100-110\./);
  }
});

test('sem citation estruturada (inclui ref/PubMed em conflito, bloqueado): ref literal, sem autor inventado', () => {
  const s = card({ ref: 'Congresso X 2026, resumo LBA1.' });
  assert.equal(C.kind(s), 'reference');
  assert.equal(C.format(s, 'vancouver'), 'Congresso X 2026, resumo LBA1. [NCT00000001]');
  assert.ok(!todas(s).some((t) => t.includes('11111111')), 'PMID não validado não é anexado ao ref');
  assert.ok(!/et al/i.test(todas(s).join(' ')));
  semSponsor(s);
});

test('sem PMID mas publicado/apresentado: ref literal', () => {
  const s = card({ pubmed_url: '', status: 'Apresentado (ASCO 2026)', ref: 'Apresentado na ASCO 2026 (LBA1).' });
  assert.equal(C.kind(s), 'reference');
  assert.equal(C.format(s, 'abnt'), 'Apresentado na ASCO 2026 (LBA1). [NCT00000001]');
  semSponsor(s);
});

test('estudo sem publicação: referência do registro, sem autor', () => {
  const s = card({ pubmed_url: '', status: 'Em andamento', ref: 'ClinicalTrials.gov NCT00000001' });
  assert.equal(C.kind(s), 'registry');
  assert.equal(C.format(s, 'vancouver'),
    'ESTUDO — teste. ClinicalTrials.gov: NCT00000001. Estudo sem publicação indexada. Disponível em: https://clinicaltrials.gov/study/NCT00000001.');
  semSponsor(s);
});

test('quarentena editorial: nenhuma citação principal', () => {
  const s = card({ status: 'Em revisão editorial', citation: cit() });
  for (const t of todas(s)) assert.equal(t, 'Referência em revisão editorial.');
});

test('evidence_collection: nunca escolhe um autor principal', () => {
  const s = card({ record_type: 'evidence_collection', citation: cit() });
  assert.equal(C.kind(s), 'reference');
  assert.ok(!todas(s).some((t) => t.includes('Autor AB')));
});

test('nenhuma autoria vem do sponsor em nenhum formato e nenhum tipo de card', () => {
  const casos = [card({ citation: cit() }), card(), card({ pubmed_url: '', status: 'Em andamento' }),
    card({ status: 'Em revisão editorial' }), card({ record_type: 'evidence_collection', citation: cit() })];
  casos.forEach(semSponsor);
});
