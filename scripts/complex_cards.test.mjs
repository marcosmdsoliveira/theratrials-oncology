#!/usr/bin/env node --test
/* ============================================================================
 * complex_cards.test.mjs — auditorias de cards complexos isolados
 *
 * Cards que não pertencem a uma família de estudo, mas que já misturaram
 * ensaios ou publicações diferentes. Cada bloco fixa a proveniência auditada
 * nas fontes primárias para impedir a regressão.
 *
 *   node --test scripts/complex_cards.test.mjs
 * ==========================================================================*/
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';

const SITE = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
const ctx = vm.createContext({ document: { addEventListener() {}, querySelectorAll() { return []; } }, console });
vm.runInContext('var window = globalThis;', ctx);
vm.runInContext(readFileSync(path.join(SITE, 'assets', 'js', 'data.js'), 'utf8'), ctx);
vm.runInContext(readFileSync(path.join(SITE, 'assets', 'js', 'common.js'), 'utf8'), ctx);
const D = ctx.THERA_DATA;
const T = ctx.TheraTrials;
const card = (uid) => D.studies.find((s) => s.uid === uid);
const js = (x) => JSON.parse(JSON.stringify(x));
const busca = (q) => D.studies.filter((s) => T.studySearchText(s).includes(q.toLowerCase()));

// ── DESTINY-Lung01 × DESTINY-Lung02 ────────────────────────────────────────
/* Ensaios distintos: Lung01 (NCT03505710, fase 2, coorte HER2-mutado com 6,4 mg/kg; NEJM 2022)
 * e Lung02 (NCT04644237, fase 2 randomizado 5,4 vs 6,4 mg/kg; JCO 2023). O card antigo
 * misturava os dois; o uid antigo ficou com o Lung01 e o Lung02 ganhou card próprio. */
const L01 = 'destiny-lung-t-dxd-em-nsclc-her2-mutado';
const L02 = 'destiny-lung02-t-dxd-5-4-vs-6-4-nsclc-her2-mutado';

test('DESTINY-Lung: dois cards, NCT, PMID e títulos distintos; sem família', () => {
  const a = card(L01), b = card(L02);
  assert.ok(a && b);
  assert.equal(a.nct, 'NCT03505710');
  assert.equal(b.nct, 'NCT04644237');
  assert.equal(a.citation.pmid, '34534430');
  assert.equal(b.citation.pmid, '37694347');
  assert.equal(a.pubmed_url, 'https://pubmed.ncbi.nlm.nih.gov/34534430/');
  assert.equal(b.pubmed_url, 'https://pubmed.ncbi.nlm.nih.gov/37694347/');
  assert.equal(a.ano_pub, 2022);
  assert.equal(b.ano_pub, 2023);
  assert.match(T.studyTitle(a.estudo), /^DESTINY-Lung01 · /);
  assert.match(T.studyTitle(b.estudo), /^DESTINY-Lung02 · /);
  assert.equal(a.family_id, undefined);
  assert.equal(b.family_id, undefined);
  assert.equal(D.studies.length, D.metadata.total_studies);
});

test('DESTINY-Lung: dose, desenho e n de cada estudo', () => {
  const a = card(L01), b = card(L02);
  assert.match(a.esquema, /6,4 mg\/kg/);
  assert.doesNotMatch(a.esquema + a.radiofarmaco, /5,4/);
  assert.match(a.n, /^91/);
  assert.match(a.fase, /Fase 2/);
  assert.match(b.esquema, /5,4 mg\/kg ou 6,4 mg\/kg/);
  assert.match(b.fase, /Fase 2, randomizado 2:1/);
  assert.doesNotMatch(b.fase + a.fase, /[Ff]ase 3/, 'nenhum dos dois é fase 3');
  assert.match(b.n, /^152/);
});

test('DESTINY-Lung: biomarcador = mutação de HER2 (não superexpressão) nos dois', () => {
  for (const u of [L01, L02]) {
    const c = card(u);
    assert.match(c.molecular, /^Requerido: mutação (ativadora )?de HER2/, u);
    assert.match(c.biomarc, /Mutação de HER2.*não superexpressão/, u);
  }
  assert.match(card(L01).desenho, /coorte HER2-mutado/);
});

test('DESTINY-Lung: nenhum card traz texto ou número do estudo irmão', () => {
  const a = JSON.stringify(card(L01)), b = JSON.stringify(card(L02));
  assert.doesNotMatch(a, /Lung0?2|NCT04644237|37694347|49%|16,8|9,9 m|5,4 mg/, 'Lung01 sem Lung02');
  assert.doesNotMatch(b, /Lung0?1\b|NCT03505710|34534430|55% \(50\/91|9,3 m/, 'Lung02 sem Lung01');
  // doença pulmonar intersticial por estudo/dose
  assert.match(card(L01).tox_interesse, /26% \(24\/91\).*G5 2/);
  assert.match(card(L02).tox_interesse, /12,9% \(13\/101.*28,0% \(14\/50/);
  assert.doesNotMatch(a, /2,6%/, 'fatal 2,6% não confere com 2/91');
});

test('DESTINY-Lung: resultado principal por estudo', () => {
  assert.match(card(L01).primario, /ORR 55% \(50\/91; IC95% 44–65\)/);
  assert.match(card(L01).primario, /DoR mediana 9,3 m/);
  assert.match(card(L02).primario, /49,0% \(IC95% 39,0–59,1\) com 5,4 mg\/kg e 56,0% \(41,3–70,0\) com 6,4 mg\/kg/);
});

test('DESTINY-Lung: busca, filtro de categoria e deep links', () => {
  assert.ok(busca('DESTINY-Lung01').some((s) => s.uid === L01));
  assert.ok(busca('DESTINY-Lung02').some((s) => s.uid === L02));
  assert.ok(!busca('DESTINY-Lung02').some((s) => s.uid === L01));
  for (const u of [L01, L02]) {
    assert.equal(card(u).category_id, 'nsclc_alvo');
    assert.deepEqual(js(T.tumorTypes.filter((t) => t.match(card(u))).map((t) => t.id)), ['pulmao'], u);
    assert.equal(T.familyForHash(D, u), null, `#${u} abre o card`);
  }
  const cat = D.categories.find((c) => c.id === 'nsclc_alvo');
  assert.equal(cat.count, D.studies.filter((s) => s.category_id === 'nsclc_alvo').length);
});

test('DESTINY-Lung: app-data leva os dois cards', () => {
  const app = JSON.parse(readFileSync(path.join(SITE, 'app-data', 'data.json'), 'utf8'));
  for (const u of [L01, L02]) assert.ok(app.studies.some((s) => s.uid === u), u);
  assert.equal(app.studies.length, D.studies.length);
});

// ── PEACE-1: fatorial 2×2 (abiraterona × radioterapia) ─────────────────────
/* PEACE-1 (NCT01957436) é fatorial 2×2, não plataforma: SOC / SOC + RT / SOC + abiraterona /
 * SOC + RT + abiraterona. A comparação da abiraterona (Lancet 2022) e a da radioterapia
 * (Lancet 2024) são perguntas e publicações distintas; o uid antigo ficou com a abiraterona. */
const PABI = 'prostata_contexto_5';
const PRT = 'peace-1-radioterapia-prostata-mhspc-de-novo';

test('PEACE-1: dois cards, mesmo NCT, PMIDs e títulos distintos; fatorial 2×2, sem "plataforma"', () => {
  const a = card(PABI), r = card(PRT);
  assert.ok(a && r);
  for (const c of [a, r]) {
    assert.equal(c.nct, 'NCT01957436');
    assert.match(c.fase, /fatorial 2×2/);
    assert.doesNotMatch(JSON.stringify(c), /plataforma|platform/i);
    assert.match(c.desenho, /SOC; SOC \+ radioterapia; SOC \+ abiraterona; SOC \+ radioterapia \+ abiraterona/);
    assert.equal(c.family_id, 'peace-1', 'comparações da família fatorial PEACE-1');
    assert.equal(c.family_relation, 'comparison');
    assert.equal(c.molecular, 'Sem critério molecular.');
  }
  assert.equal(a.citation.pmid, '35405085');
  assert.equal(r.citation.pmid, '39580202');
  assert.equal(a.ano_pub, 2022);
  assert.equal(r.ano_pub, 2024);
  assert.match(T.studyTitle(a.estudo), /^PEACE-1 · Abiraterona/);
  assert.match(T.studyTitle(r.estudo), /^PEACE-1 · Radioterapia/);
});

test('PEACE-1: cada card só traz a sua comparação', () => {
  const a = card(PABI), r = card(PRT);
  assert.match(a.primario, /rPFS HR 0,54.*OS HR 0,82.*rPFS HR 0,50.*OS HR 0,75/);
  assert.match(a.comparador, /sem abiraterona/);
  assert.doesNotMatch(JSON.stringify(a), /RT prostática: ganho|HR (ajustado )?0,65|HR 0,98|74 Gy|39580202/, 'abiraterona sem resultado da RT');
  assert.doesNotMatch(JSON.stringify(a), /HR 0,47|HR 0,72|HR 0,58|alto volume \+ Abi/, 'subgrupos não verificados removidos');
  assert.match(r.primario, /interação qualitativa radioterapia × abiraterona \(p=0,026\)/);
  assert.match(r.primario, /HR ajustado 0,65/);
  assert.match(r.primario, /HR 0,98/);
  assert.match(r.comparador, /sem radioterapia/);
  assert.doesNotMatch(JSON.stringify(r), /HR 0,54|HR 0,82|HR 0,50|HR 0,75|35405085/, 'RT sem resultado da abiraterona');
  assert.doesNotMatch(JSON.stringify(r), /STAMPEDE/, 'nada importado do STAMPEDE RT');
});

test('PEACE-1: tripleta descrita como efeito da randomização da abiraterona, não como comparação de tripletas', () => {
  const a = card(PABI);
  assert.match(a.impacto_reg, /pergunta randomizada é a adição de abiraterona/);
  assert.match(a.limit, /docetaxel não foi randomizado/);
  assert.match(a.limit, /não compara tripletas entre si/);
  assert.match(a.esquema, /prednisona 5 mg VO 2×\/dia/);
});

test('PEACE-1: busca, categoria e deep links', () => {
  for (const u of [PABI, PRT]) {
    assert.ok(busca('PEACE-1').some((s) => s.uid === u), u);
    assert.equal(card(u).category_id, 'prostata_contexto');
    assert.deepEqual(js(T.tumorTypes.filter((t) => t.match(card(u))).map((t) => t.id)), ['prostata'], u);
    assert.equal(T.familyForHash(D, u), null, `#${u} abre o card`);
  }
  assert.ok(busca('radioterapia da próstata').some((s) => s.uid === PRT));
  const cat = D.categories.find((c) => c.id === 'prostata_contexto');
  assert.equal(cat.count, D.studies.filter((s) => s.category_id === 'prostata_contexto').length);
  const app = JSON.parse(readFileSync(path.join(SITE, 'app-data', 'data.json'), 'utf8'));
  for (const u of [PABI, PRT]) assert.ok(app.studies.some((s) => s.uid === u), u);
});

// ── Natalie Trial: cabozantinibe em PPGL (sem NCI-MATCH) ───────────────────
/* ppgl_5 = Natalie Trial (NCT02302833): fase 2, braço único, centro único no MD Anderson
 * (NCI só como colaborador); Jimenez, Lancet Oncol 2024 (PMID 38608693). O card dizia
 * "NCI-MATCH/MD Anderson", mas o NCI-MATCH (NCT02465060) não tem subprotocolo de
 * cabozantinibe nem PPGL; faixas sem fonte (ORR 25-35%, PFS 12-16 m, DE ~50%) foram removidas. */
const NAT = 'ppgl_5';

test('Natalie: NCT, PMID, título e desenho de um único estudo; sem NCI-MATCH; sem família', () => {
  const c = card(NAT);
  assert.equal(c.nct, 'NCT02302833');
  assert.equal(c.nct_url, 'https://clinicaltrials.gov/study/NCT02302833');
  assert.equal(c.citation.pmid, '38608693');
  assert.equal(c.pubmed_url, 'https://pubmed.ncbi.nlm.nih.gov/38608693/');
  assert.equal(c.ano_pub, 2024);
  assert.match(T.studyTitle(c.estudo), /^Natalie Trial · Cabozantinibe em PPGL/);
  assert.match(c.fase, /Fase 2, braço único, aberto, centro único/);
  assert.match(c.centros, /^Centro único: MD Anderson/);
  assert.doesNotMatch(c.fase + c.centros, /multic[eê]ntric|expansão/i);
  assert.doesNotMatch(JSON.stringify(c), /NCI-MATCH|EAY131|NCT02465060/);
  assert.match(c.sponsor, /colaborador: National Cancer Institute/);
  assert.equal(c.family_id, undefined);
  assert.equal(T.familyForHash(D, NAT), null, '#ppgl_5 abre o card');
});

test('Natalie: população, n, dose e biomarcador conforme registro/protocolo', () => {
  const c = card(NAT);
  assert.match(c.n, /^17 \(16 avaliáveis/);
  assert.match(c.incl, /progressão por RECIST 1\.1 nos 12 meses anteriores; ECOG 0–2/);
  assert.match(c.esquema, /^Cabozantinibe 60 mg VO 1×\/dia, em jejum/);
  assert.match(c.esquema, /40 e 20 mg\/dia/);
  assert.equal(c.molecular, 'Sem critério molecular de inclusão.');
  assert.doesNotMatch(c.molecular + c.biomarc + c.incl, /SDH|RET|VHL|NF1/, 'sem seleção molecular atribuída');
  assert.doesNotMatch(JSON.stringify(c), /SDHB\+ ~45%|60% PGL|Ga-DOTATATE|futilidade/, 'basais/estatística sem fonte removidos');
});

test('Natalie: eficácia e toxicidade só do próprio estudo, sem faixas sem fonte', () => {
  const c = card(NAT);
  assert.equal(c.primario, 'ORR avaliada pelo investigador (RECIST 1.1): 25,0% (IC95% 7,3–52,4; 4/16).');
  assert.equal(c.resultado_chave, 'ORR 25,0% (4/16; IC95% 7,3–52,4)');
  assert.doesNotMatch(JSON.stringify(c), /25-35%|12-16 m|~50%|~60%|HFS 15-20%/);
  assert.match(c.tox_g3, /Sete eventos adversos G3 em seis pacientes/);
  assert.match(c.tox_g3, /Sem eventos G4 e sem óbitos no estudo/);
  assert.match(c.tox_interesse, /^Resultados postados no ClinicalTrials\.gov \(20 tratados/);
  assert.match(c.limit, /20 pacientes tratados, número diferente do publicado/);
  assert.doesNotMatch(c.impacto_reg + c.takehome, /pós-sunitinibe|SDHB/);
  assert.match(c.takehome, /não evidência confirmatória/);
  // referência com a lista real de autores (PubMed 38608693)
  assert.match(c.ref, /Bassett R, Dantzer R, Balderrama-Brondani V, Varghese J, Lu Y\./);
  assert.doesNotMatch(c.ref, /Fojo|Waguespack|Subbiah/);
});

test('Natalie: busca, filtro de tumor, categoria e app-data', () => {
  for (const q of ['Natalie', 'cabozantinibe', 'NCT02302833']) assert.ok(busca(q).some((s) => s.uid === NAT), q);
  assert.ok(!busca('NCI-MATCH').some((s) => s.uid === NAT));
  assert.equal(card(NAT).category_id, 'ppgl');
  assert.deepEqual(js(T.tumorTypes.filter((t) => t.match(card(NAT))).map((t) => t.id)), ['pheo_pgl']);
  const cat = D.categories.find((c) => c.id === 'ppgl');
  assert.equal(cat.count, D.studies.filter((s) => s.category_id === 'ppgl').length);
  const app = JSON.parse(readFileSync(path.join(SITE, 'app-data', 'data.json'), 'utf8'));
  assert.deepEqual(app.studies.find((s) => s.uid === NAT).primario, card(NAT).primario);
});
