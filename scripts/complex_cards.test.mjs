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

// ── RAMPART: plataforma MAMS, duas comparações apresentadas em congresso ───
/* RAMPART (NCT03288532 · ISRCTN53348826): plataforma MAMS 3:2:2 — A monitoramento ativo;
 * B durvalumabe; C durvalumabe + tremelimumabe. C vs A: ESMO 2025 LBA93 (Ann Oncol 2025;36:S1635);
 * B vs A: ASCO 2026 LBA4511 (J Clin Oncol 2026;44(17_suppl)). Os dois são abstracts de congresso,
 * sem publicação completa. O uid antigo (durvalumabe + tremelimumabe) ficou com C vs A. */
const RC = 'rampart-durvalumabe-tremelimumabe-adjuvante-rcc';
const RB = 'rampart-durvalumabe-monoterapia-adjuvante-rcc';
const famR = () => D.families.find((f) => f.family_id === 'rampart');

test('RAMPART: family platform_mams com três braços, dois cards e sem resultado clínico', () => {
  const f = famR();
  assert.ok(f);
  assert.equal(f.design_type, 'platform_mams');
  assert.deepEqual(js(f.registry_ids), ['NCT03288532', 'ISRCTN53348826']);
  assert.deepEqual(js(f.arms.map((a) => a.arm)), ['A', 'B', 'C']);
  assert.match(f.arms[0].treatment, /^Monitoramento ativo/);
  assert.match(f.arms[1].treatment, /^Durvalumabe 1\.500 mg/);
  assert.match(f.arms[2].treatment, /tremelimumabe 75 mg nos ciclos 1 e 2/);
  assert.deepEqual(js(f.arms.map((a) => a.card_uids)), [[], [RB], [RC]]);
  assert.equal(f.arms[1].publication.doi, '10.1200/JCO.2026.44.17_suppl.LBA4511');
  assert.equal(f.arms[2].publication.doi, '10.1016/j.annonc.2025.09.110');
  assert.match(f.design_summary, /multi-arm multi-stage \(MAMS\), randomizado 3:2:2/);
  assert.match(f.i18n.en.design_summary, /multi-arm multi-stage \(MAMS\) platform trial randomised 3:2:2/);
  assert.doesNotMatch(JSON.stringify(f), /HR |IC95%|DFS em \d|0,65|0,74|84%|78%/, 'family sem eficácia');
  assert.equal(T.familyUnitKind(D, f), 'arm', 'mesma UX do STAMPEDE: braços do protocolo');
  for (const u of [RC, RB]) {
    assert.equal(card(u).family_id, 'rampart', u);
    assert.equal(card(u).family_relation, 'comparison', u);
    assert.equal(card(u).nct, 'NCT03288532', u);
  }
});

test('RAMPART: títulos, fonte (DOI de abstract de congresso) e status de evidência', () => {
  const c = card(RC), b = card(RB);
  assert.equal(T.studyTitle(c.estudo), 'RAMPART · Durvalumabe + tremelimumabe vs monitoramento ativo — RCC adjuvante');
  assert.equal(T.studyTitle(b.estudo), 'RAMPART · Durvalumabe vs monitoramento ativo — RCC adjuvante');
  assert.match(c.ref, /Ann Oncol 2025;36\(suppl\):S1635 \(abstract de congresso, ESMO 2025; DOI 10\.1016\/j\.annonc\.2025\.09\.110\)/);
  assert.match(b.ref, /J Clin Oncol 2026;44\(17_suppl\):LBA4511 \(abstract de congresso, ASCO 2026; DOI 10\.1200\/JCO\.2026\.44\.17_suppl\.LBA4511\)/);
  for (const x of [c, b]) {
    assert.equal(x.citation, undefined, 'convenção dos cards de congresso: sem citation (o v2 exige PMID)');
    assert.equal(x.pubmed_url, '', 'abstract sem PMID');
    assert.match(x.status, /^Apresentado \((ESMO 2025, LBA93|ASCO 2026, LBA4511)\) · publicação completa ainda não disponível$/);
    assert.match(x.limit, /^Resultado de abstract de congresso; publicação completa da análise primária ainda não disponível/);
    assert.match(x.ref, /abstract de congresso/);
    assert.doesNotMatch(JSON.stringify(x), /cancernetwork|por publicar|NEGATIVO/i);
  }
  assert.equal(c.ano_pub, 2025);
  assert.equal(b.ano_pub, 2026);
});

test('RAMPART C vs A: só dados do LBA93', () => {
  const c = card(RC), j = JSON.stringify(c);
  assert.equal(c.primario, 'DFS C vs A (n=565): HR 0,65 (IC95% 0,45–0,93; p unilateral 0,0094). DFS em 2 anos: 84% (C) vs 78% (A).');
  assert.match(c.subgrupo, /Maior risco \(alto \+ M1NED; n=311\): HR 0,52 \(IC95% 0,34–0,80; p=0,0016\); DFS em 2 anos 81% vs 67%/);
  assert.match(c.subgrupo, /Risco intermediário \(n=254\): HR 1,19 \(IC95% 0,61–2,32; p=0,309\)/);
  assert.match(c.subgrupo, /Interação tratamento × risco: HR 0,43 \(IC95% 0,19–0,95; p=0,019\)/);
  assert.match(c.basal, /intermediário 151 \/ 103 \(254\); alto 172 \/ 111 \(283\); M1NED 17 \/ 11 \(28\)/);
  assert.match(c.estatistica, /HR de DFS de 0,55 em C vs A/);
  assert.match(c.tox_interesse, /sinais de segurança inesperados/);
  assert.doesNotMatch(c.tox_g3 + c.tox_interesse, /\d+%/, 'sem percentuais de toxicidade');
  assert.doesNotMatch(j, /0,74|0,53–1,04|0,041|3 anos|0,77|0,30–1,34|0,60 em B/, 'sem números de B vs A');
});

test('RAMPART B vs A: só dados do LBA4511; sem "negativo"', () => {
  const b = card(RB), j = JSON.stringify(b);
  assert.equal(b.primario, 'DFS B vs A (n=565): HR 0,74 (IC95% 0,53–1,04; p unilateral 0,041), sem significância estatística convencional. DFS em 3 anos: 78% (B) vs 72% (A).');
  assert.match(b.subgrupo, /Maior risco \(n=312\): HR 0,77 \(IC95% 0,53–1,12\)/);
  assert.match(b.subgrupo, /Risco intermediário \(n=253\): HR 0,64 \(IC95% 0,30–1,34\)/);
  assert.match(b.subgrupo, /Sem evidência de interação/);
  assert.match(b.estatistica, /HR de DFS de 0,60 em B vs A/);
  assert.match(b.centros, /^80 centros; .*Espanha \(4%\)/);
  assert.equal(b.tox_g3, 'Não informada no abstract.');
  assert.doesNotMatch(j, /0,65|0,45–0,93|0,0094|2 anos|0,52|0,0016|0,43|1,19|0,55 em C/, 'sem números de C vs A');
});

test('RAMPART: busca, filtros, deep links (card e family) e app-data', () => {
  for (const q of ['RAMPART', 'NCT03288532']) for (const u of [RC, RB]) assert.ok(busca(q).some((s) => s.uid === u), `${q} → ${u}`);
  assert.ok(busca('tremelimumabe').some((s) => s.uid === RC));
  for (const u of [RC, RB]) {
    assert.equal(card(u).category_id, 'rcc_adjuvante_naocc');
    assert.deepEqual(js(T.tumorTypes.filter((t) => t.match(card(u))).map((t) => t.id)), ['ccrcc'], u);
    assert.equal(T.familyForHash(D, u), null, `#${u} abre o card`);
  }
  assert.equal(T.familyForHash(D, 'rampart').family_id, 'rampart');
  const cat = D.categories.find((c) => c.id === 'rcc_adjuvante_naocc');
  assert.equal(cat.count, D.studies.filter((s) => s.category_id === 'rcc_adjuvante_naocc').length);
  const app = JSON.parse(readFileSync(path.join(SITE, 'app-data', 'data.json'), 'utf8'));
  for (const u of [RC, RB]) assert.equal(app.studies.find((s) => s.uid === u).primario, card(u).primario, u);
  assert.ok((app.families || []).some((f) => f.family_id === 'rampart'));
});

// ── NOVA e MAGNITUDE: OS final substitui afirmações sem lastro ──────────────
/* NOVA (NCT01847274): PFS primária de Mirza NEJM 2016 (PMID 27717299) e OS final de Matulonis,
 * Gynecol Oncol 2025 (PMID 40139026), sem diferença em nenhuma coorte. MAGNITUDE (NCT03748641):
 * rPFS de Chi JCO 2023 (PMID 36952634), BRCA1/2 testado primeiro; OS final (PMID 40328571) sem diferença. */
test('NOVA: três comparações primárias de PFS, OS final sem diferença, sem "ganho de OS" em gBRCA', () => {
  const c = card('ovario_4'), j = JSON.stringify(c);
  assert.equal(c.citation.pmid, '27717299');
  assert.match(c.primario, /gBRCA: 21,0 vs 5,5 m \(HR 0,27; IC95% 0,17–0,41\)/);
  assert.match(c.primario, /HRD\+: 12,9 vs 3,8 m \(HR 0,38; IC95% 0,24–0,59\)/);
  assert.match(c.primario, /Não-gBRCA geral: 9,3 vs 3,9 m \(HR 0,45; IC95% 0,34–0,61\)/);
  assert.doesNotMatch(c.primario, /HRD−|HRD-/, 'HRD− não é comparação primária');
  assert.match(c.subgrupo, /HRD− \(exploratório/);
  assert.match(c.secundario, /gBRCA 40,9 vs 38,1 m \(HR 0,85; IC95% 0,61–1,20\); não-gBRCA 31,0 vs 34,8 m \(HR 1,06; IC95% 0,81–1,37\)/);
  assert.match(c.ref, /PMID 40139026/);
  assert.doesNotMatch(j, /HR 0,68|ASCO 2024|ganho de OS sustentado|8-yr/);
  assert.match(c.molecular, /define a coorte; não é requisito de inclusão/);
  assert.doesNotMatch(c.desenho, /ajustado por peso/, 'dose fixa de 300 mg no protocolo');
});

test('MAGNITUDE: rPFS BRCA primeiro, OS final 0,931/0,788 sem diferença, citation do JCO 2023', () => {
  const c = card('prostata_contexto_20'), j = JSON.stringify(c);
  assert.equal(c.citation.pmid, '36952634');
  assert.equal(c.ano_pub, 2023);
  assert.match(c.primario, /^rPFS BRCA1\/2: 16,6 vs 10,9 m \(HR 0,53; IC95% 0,36–0,79; p=0,001\)\. rPFS HRR\+: 16,5 vs 13,7 m \(HR 0,73; IC95% 0,56–0,96; p=0,022\)/);
  assert.match(c.secundario, /OS final: HRR\+ HR 0,931 \(IC95% 0,720–1,203; p=0,585\); BRCA1\/2 HR 0,788 \(IC95% 0,554–1,120; p nominal=0,183\), sem diferença/);
  assert.match(c.subgrupo, /HRR não-BRCA: rPFS HR 0,99 \(IC95% 0,68–1,44\), sem benefício demonstrado/);
  assert.doesNotMatch(j, /HR 0,55 favorável|OS HRR\+ ITT: HR 0,79|LBA12|magnitude menor|mais frequente que com olaparib/);
  assert.match(c.esquema, /prednisona 5 mg 2x\/dia/);
  assert.match(c.ref, /PMID 40328571/);
});

// ── POSEIDON: primário é D+QT vs QT; tripleta é secundário-chave ─────────────
/* POSEIDON (NCT03164616; Johnson JCO 2023, PMID 36327426): primários PFS e OS de D+QT vs QT
 * (OS HR 0,86; p=0,0758, não significativa); T+D+QT vs QT é secundário-chave com controle de alfa. */
test('POSEIDON: atribuição correta das comparações, toxicidade do comparador e estratificação', () => {
  const c = card('poseidon-durva-treme-qt-vs-qt-em-nsclc-1l'), j = JSON.stringify(c);
  assert.equal(c.citation.pmid, '36327426');
  assert.match(c.primario, /^Primários \(D\+QT vs QT\): PFS \(BICR\) 5,5 vs 4,8 m, HR 0,74 \(IC95% 0,62–0,89; p=0,0009\); OS 13,3 vs 11,7 m, HR 0,86 \(IC95% 0,72–1,02; p=0,0758\), não significativo/);
  assert.match(c.primario, /Secundários-chave com controle de alfa \(T\+D\+QT vs QT\): PFS 6,2 vs 4,8 m, HR 0,72/);
  assert.match(c.resultado_chave, /^D\+QT vs QT \(primário\)/);
  assert.match(c.tox_g3, /51,8% \(T\+D\+QT\) \/ 44,6% \(D\+QT\) \/ 44,4% \(QT\)/);
  assert.doesNotMatch(j, /41,6|custo-benefício/);
  assert.equal(c.estrat, 'PD-L1 (≥50% vs <50% das células tumorais), estádio (IVA vs IVB), histologia (escamosa vs não escamosa)');
  assert.match(c.secundario, /ORR confirmada \(post hoc\)/);
  assert.match(c.biomarc, /STK11\/KEAP1\/KRAS: análise exploratória posterior \(Skoulidis, Nature 2024; PMID 39385035\)/);
});

// ── FOENIX-CCA2, EMERALD-1, SunRISe-1 ───────────────────────────────────────
test('FOENIX-CCA2: iCCA FGFR2, sem inibidor de FGFR prévio; sem enquadramento pós-pemigatinib', () => {
  const c = card('hepatobiliar_18');
  assert.equal(c.citation.pmid, '36652354');
  assert.match(c.linha, /sem inibidor de FGFR prévio/);
  assert.doesNotMatch(c.linha + c.acron + c.takehome, /pós-pemigatinib|após resistência|reverter resistência/);
  assert.match(c.limit, /não informa eficácia após pemigatinib ou infigratinib/);
  assert.match(c.periodo, /^Inclusão 16\/abr\/2018–29\/nov\/2019/);
  assert.doesNotMatch(c.fase, /basket/i);
  assert.match(c.tox_g3, /aumento de AST 7%/);
  assert.doesNotMatch(JSON.stringify(c), /intra-hep 99%|AST 9%|coorte separada para retreatment|mais alta que pemigatinib/);
  assert.equal(c.primario.startsWith('ORR (revisão central): 42% (43/103; IC95% 32–52)'), true);
});

test('EMERALD-1: ref Lancet 2025, sequência TACE → durva + bev, estratificação, Vp1/Vp2, hemorragia 9%', () => {
  const c = card('hepatobiliar_26'), j = JSON.stringify(c);
  assert.equal(c.citation.pmid, '39798579');
  assert.equal(c.ano_pub, 2025);
  assert.match(c.ref, /Lancet 2025;405\(10474\):216-232/);
  assert.match(c.esquema, /A partir de ≥14 dias após a última TACE: durvalumabe 1120 mg q3w \+ bevacizumabe 15 mg\/kg/);
  assert.match(c.estrat, /^Modalidade de TACE .* região .* invasão portal/);
  assert.match(c.excl, /Vp1\/Vp2 permitidas/);
  assert.match(c.tox_g3, /Hemorragia G3–4: 9% \(D\+B\)/);
  assert.match(c.basal, /78% ♂/);
  assert.doesNotMatch(j, /1521-1536|Lancet 2024|hemorragia 3%|>5 cm|83% ♂|UTI-disponível|durva isolada após indução/);
  assert.match(c.primario, /HR 0,77 \(IC95% 0,61–0,98; p=0,032 bilateral\)/);
});

test('SunRISe-1: coorte 2, RC central vs investigador, toxicidade da coorte 2, sem referência inexistente', () => {
  const c = card('urotelial_periop_nmibc_6'), j = JSON.stringify(c);
  assert.equal(c.citation.pmid, '40737582');
  assert.equal(c.ano_pub, 2025);
  assert.match(c.primario, /^RC global confirmada centralmente: 82,4% \(70\/85; IC95% 72,6–89,8\); RC pelo investigador 83,5%/);
  assert.match(c.primario, /RC aos 3, 6 e 12 m: 78,8%, 58,8% e 45,9%\. DOR mediana 25,8 m/);
  assert.match(c.tox_g3, /^EAs relacionados G≥3: 12,9% \(11\/85\)/);
  assert.match(c.desenho, /randomizados 2:1:1/);
  assert.doesNotMatch(j, /Lancet Oncol 2024|ESMO 2024|73,3%|CR em 12 m: 50%|mDOR NR|Priority Review|aprovação esperada|TARIS/);
});

// ── Lote de biomarcadores: CheckMate-358, MajesTEC-1, EV-103 K, CheckMate-227 ──
test('CheckMate-358: fase 1/2, HPV não requerido, cérvix n=19, TRAE G3–4 21,1%', () => {
  const c = card('cervix_9');
  assert.match(c.fase, /^Fase 1\/2/);
  assert.doesNotMatch(c.fase, /basket/i);
  assert.match(c.biomarc, /^HPV não exigido: excluídos apenas tumores sabidamente HPV-negativos/);
  assert.doesNotMatch(c.indicacao + c.incl, /HPV\+/);
  assert.match(c.primario, /^Cérvix \(n=19\): ORR por investigador 26,3% \(IC95% 9,1–51,2; 5\/19\)/);
  assert.match(c.tox_g3, /TRAE G3–4 21,1% \(4\/19\)/);
  assert.doesNotMatch(c.sponsor, /Hollebecque/, 'PI sem lastro; ele é 2º autor na citation');
  assert.doesNotMatch(JSON.stringify(c), /n=24 cérvix|pós ≥1 linha/);
});

test('MajesTEC-1: triple-class exposed, NCT fase 1/fase 2, toxicidade do NEJM, sem q2w/profilaxia sem fonte', () => {
  const c = card('mieloma_6'), j = JSON.stringify(c);
  assert.equal(c.nct, 'NCT03145181 (fase 1) / NCT04557098 (fase 2)');
  assert.match(c.indicacao, /triple-class exposed/);
  assert.doesNotMatch(c.acron + c.indicacao + c.incl, /refratário a IMID|triple-class refractory/i);
  assert.match(c.basal, /triple-class refratário 77,6%/);
  assert.match(c.tox_g3, /^EA G3–4 \(qualquer causalidade\) 94,5%\. Neutropenia G3–4 64,2%, anemia 37,0%, trombocitopenia 21,2%/);
  assert.doesNotMatch(j, /88%|q2w|sulfa|fluconazol|IgG <400|profilaxia obrigatória|IGIV mensal/);
  assert.match(c.biomarc, /^Sem biomarcador de seleção/);
  assert.equal(c.primario, 'ORR 63,0% (IC95% 55,2–70,4; 104/165); ≥RC 39,4%.');
});

test('EV-103 coorte K: basal, estratificação, PD-L1 exploratório, sem comparação formal, neuropatia 2,6%', () => {
  const c = card('urotelial_avancado_9'), j = JSON.stringify(c);
  assert.equal(c.estrat, 'ECOG (0–1 vs 2) e metástase hepática (presente vs ausente)');
  assert.match(c.basal, /mediana 71a .* metástases viscerais 84,2% \(hepáticas 17,1%\); PD-L1 CPS <10 57,9%/);
  assert.match(c.molecular, /exploratórios$/);
  assert.match(c.resultado_chave, /sem comparação formal/);
  assert.match(c.tox_interesse, /neuropatia 2,6%/);
  assert.match(c.tox_g3, /3 óbitos relacionados \(3,9%/);
  assert.doesNotMatch(j, />22 m|12,7 m|neuropatia periférica 5%|Israel|Rosenberg/);
});

test('CheckMate-227: N 1189, estratificação por histologia, TMB atingido (não abandonado), PD-L1 <1% descritivo', () => {
  const c = card('checkmate-227-nivolumab-ipilimumab-em-nsclc-1l'), j = JSON.stringify(c);
  assert.equal(c.citation.pmid, '31562796');
  assert.match(c.n, /PD-L1 ≥1% n=1189/);
  assert.match(c.estrat, /^Histologia \(escamoso vs não escamoso\)/);
  assert.doesNotMatch(c.estrat, /sexo/);
  assert.match(c.limit, /atingido, não abandonado/);
  assert.match(c.secundario, /^PD-L1 <1% \(análise descritiva pré-especificada\)/);
  assert.match(c.impacto_reg, /PD-L1 ≥1% sem aberrações de EGFR\/ALK/);
  assert.match(c.biomarc, /^PD-L1 central obrigatório/);
  assert.doesNotMatch(j, /N=1166|abandonado;|pneumonite prévia|sobretudo em PD-L1 <1%/);
});
