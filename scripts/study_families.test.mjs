#!/usr/bin/env node --test
/* ============================================================================
 * study_families.test.mjs — famílias de estudo (THERA_DATA.families)
 *
 * Uma família descreve só o protocolo compartilhado (aqui, a plataforma STAMPEDE);
 * cada comparação continua sendo um card clínico normal. Estes testes guardam:
 *   - a estrutura da família e o deep link do uid antigo (prostata_contexto_2);
 *   - busca, filtros e abertura dos cards-membro;
 *   - que o STAMPEDE2 é outro protocolo;
 *   - as correções científicas da migração (nada de Ra-223, tripletas, "Arm K"…);
 *   - que o validador reprova famílias malformadas (injeção de defeito, cópia temporária);
 *   - links dos Tumor Boards e paridade com o app-data.
 *
 *   node --test scripts/study_families.test.mjs
 * ==========================================================================*/
import test from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { mkdtempSync, mkdirSync, copyFileSync, writeFileSync, readFileSync, readdirSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const SITE = path.join(__dirname, '..');
const DATA = path.join(SITE, 'assets', 'js', 'data.js');

// data.js + common.js num contexto em que window === globalThis, como no navegador
const ctx = vm.createContext({ document: { addEventListener() {}, querySelectorAll() { return []; } }, console });
vm.runInContext('var window = globalThis;', ctx);
vm.runInContext(readFileSync(DATA, 'utf8'), ctx);
vm.runInContext(readFileSync(path.join(SITE, 'assets', 'js', 'common.js'), 'utf8'), ctx);
const D = ctx.THERA_DATA;
const T = ctx.TheraTrials;
const card = (uid) => D.studies.find((s) => s.uid === uid);
const js = (x) => JSON.parse(JSON.stringify(x));   // arrays do contexto vm vêm de outro realm
const busca = (q) => D.studies.filter((s) => T.studySearchText(s).includes(q.toLowerCase()));

const MEMBROS = ['stampede-docetaxel-m1', 'stampede-abiraterona-m1', 'stampede-abi-enza-m0-alto-risco',
  'rt_sbrt_oligo_4', 'stampede-abi-enza-m1', 'stampede-metformina-m1'];
const PMIDS = {
  'stampede-docetaxel-m1': '31560068', 'stampede-abiraterona-m1': '37142371', 'stampede-abi-enza-m1': '37142371',
  'stampede-abi-enza-m0-alto-risco': '34953525', 'stampede-metformina-m1': '40639383', rt_sbrt_oligo_4: '30355464',
};
const STAMPEDE = T.familyById(D, 'stampede');
const textoFamilia = () => JSON.stringify([STAMPEDE, ...MEMBROS.map(card)]);

// ── família e deep link ────────────────────────────────────────────────────
test('família stampede: plataforma MAMS com os registros do protocolo original', () => {
  assert.ok(STAMPEDE);
  assert.equal(STAMPEDE.design_type, 'platform_mams');
  assert.deepEqual(js(STAMPEDE.registry_ids), ['NCT00268476', 'ISRCTN78818544']);
  assert.ok(T.FAMILY_TYPES.includes(STAMPEDE.design_type));
  assert.deepEqual(js(STAMPEDE.arms.map((a) => a.arm)), ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'J', 'K', 'L']);
});

test('deep link legado #prostata_contexto_2 abre a família, e o uid não é mais card clínico', () => {
  assert.equal(card('prostata_contexto_2'), undefined);
  assert.equal(T.familyForHash(D, 'prostata_contexto_2').family_id, 'stampede');
  assert.equal(T.familyForHash(D, 'stampede').family_id, 'stampede');
  assert.equal(T.familyForHash(D, 'uid-que-nao-existe'), null);
});

test('membros da família abrem individualmente, na ordem dos braços', () => {
  const m = T.familyMembers(D, STAMPEDE).map((s) => s.uid);
  assert.deepEqual(js(m), MEMBROS);
  for (const u of MEMBROS) {
    const s = card(u);
    assert.ok(s, u);
    assert.equal(s.family_id, 'stampede');
    assert.equal(s.family_relation, 'comparison');
    assert.ok(s.comparison_label);
    assert.match(T.studyTitle(s.estudo), /^STAMPEDE · /, `título de lista de ${u}`);
  }
  assert.equal(new Set(MEMBROS.map((u) => T.studyTitle(card(u).estudo))).size, MEMBROS.length, 'títulos de lista distintos');
});

// ── busca e filtros ────────────────────────────────────────────────────────
test('busca "STAMPEDE" mostra a família e todos os membros', () => {
  assert.ok(T.familiesToShow(D, busca('stampede'), 'STAMPEDE', false).some((f) => f.family_id === 'stampede'));
  const achados = busca('stampede').map((s) => s.uid);
  for (const u of MEMBROS) assert.ok(achados.includes(u), u);
});

test('busca por "docetaxel" e por "radioterapia" encontra o card-filho', () => {
  assert.ok(busca('docetaxel').some((s) => s.uid === 'stampede-docetaxel-m1'));
  assert.ok(busca('radioterapia').some((s) => s.uid === 'rt_sbrt_oligo_4'));
});

test('sem busca e sem filtro, a família não ocupa o topo do Database; com filtro de tumor, aparece', () => {
  assert.equal(T.familiesToShow(D, D.studies, '', false).length, 0);
  const prostata = T.tumorTypes.find((t) => t.id === 'prostata');
  const filtrados = D.studies.filter((s) => prostata.match(s));
  assert.ok(T.familiesToShow(D, filtrados, '', true).some((f) => f.family_id === 'stampede'));
});

test('filtro por tumor (próstata) continua pegando todos os membros e o STAMPEDE2', () => {
  const prostata = T.tumorTypes.find((t) => t.id === 'prostata');
  for (const u of [...MEMBROS, 'lupsma_prostata_8']) assert.ok(prostata.match(card(u)), u);
});

test('dados sem `families` (frontend antigo, outro dataset) não quebram os helpers', () => {
  const semFam = { studies: D.studies };
  assert.deepEqual(js(T.familyList(semFam)), []);
  assert.equal(T.familyForHash(semFam, 'prostata_contexto_2'), null);
  assert.deepEqual(js(T.familiesToShow(semFam, D.studies, 'stampede', true)), []);
});

// ── identidade ─────────────────────────────────────────────────────────────
test('mesmo NCT entre membros da mesma família é legítimo (validador passa)', () => {
  const comNct = D.studies.filter((s) => s.nct === 'NCT00268476');
  assert.equal(comNct.length, MEMBROS.length);
  assert.ok(comNct.every((s) => s.family_id === 'stampede'));
});

test('STAMPEDE2 é outro protocolo: família própria, NCT próprio, fora do NCT00268476', () => {
  const lu = card('lupsma_prostata_8');
  assert.equal(lu.family_id, 'stampede2');
  assert.equal(lu.nct, 'NCT06320067');
  assert.ok(!STAMPEDE.registry_ids.includes('NCT06320067'));
  assert.ok(!T.familyMembers(D, STAMPEDE).some((s) => s.uid === 'lupsma_prostata_8'));
  assert.ok(!/STAMPEDE-?2/i.test(STAMPEDE.design_summary + STAMPEDE.arms.map((a) => a.treatment).join(' ')));
  assert.deepEqual(js(STAMPEDE.related.map((r) => [r.family_id, r.relation])), [['stampede2', 'successor']]);
  assert.deepEqual(js(T.familyById(D, 'stampede2').arms.map((a) => a.arm)), ['S', 'P']);
});

test('nenhum uid duplicado e nenhuma família com id de card', () => {
  const uids = D.studies.map((s) => s.uid);
  assert.equal(new Set(uids).size, uids.length);
  for (const f of D.families) assert.ok(!uids.includes(f.family_id), f.family_id);
});

// ── correções científicas ──────────────────────────────────────────────────
test('nada de Ra-223 / ERA 223 nos dados da família STAMPEDE', () => {
  assert.doesNotMatch(textoFamilia(), /Ra-?\s?223|223\s?Ra|ERA[\s-]?223|r[aá]dio-?223|radium/i);
});

test('afirmações removidas não voltam (tripleta, Arm K, baixo volume ≤3, hipérboles)', () => {
  const t = textoFamilia();
  assert.doesNotMatch(t, /tripleta/i);
  assert.doesNotMatch(t, /Arm K[^"]{0,40}enza|Abi\s*\+\s*Enza[^"]{0,40}Arm K/i);
  assert.doesNotMatch(t, /≤\s?3 met/i);
  assert.doesNotMatch(t, /REVOLUCION|Bras[ãa]o|Perfil de perfil/i);
  // HR 0,78 do docetaxel (2016) é da população global M0+M1; o card M1 usa a análise madura (HR 0,81).
  // (0,78 aparece legitimamente no card de RT: PFS na baixa carga.)
  assert.doesNotMatch(JSON.stringify(card('stampede-docetaxel-m1')), /0,78/);
  assert.doesNotMatch(t, /0,65[^"]{0,30}vs (ADT\s*\+\s*)?Abi/i, 'HR 0,65 é abi+enza vs SOC, não vs abiraterona');
  // HR 0,63 (NEJM 2017) é da população total M0+M1; só pode aparecer com esse contexto
  for (const m of t.matchAll(/HR 0,63/g)) assert.match(t.slice(m.index, m.index + 80), /população total/);
});

test('PMID, pubmed_url e citation de cada card STAMPEDE batem com a publicação representada', () => {
  for (const [u, pmid] of Object.entries(PMIDS)) {
    const s = card(u);
    assert.equal(s.citation.pmid, pmid, u);
    assert.equal(s.pubmed_url, `https://pubmed.ncbi.nlm.nih.gov/${pmid}/`, u);
    assert.equal(s.nct, 'NCT00268476', u);
  }
});

test('família não traz resultado clínico', () => {
  for (const f of D.families) {
    assert.ok(!('resultado_chave' in f) && !('primario' in f), f.family_id);
    assert.doesNotMatch(JSON.stringify(f), /\bHR\b(?!-)|IC ?95|mediana/i, f.family_id);   // HR-NBL1 é nome de estudo
  }
});

// ── links e app-data ───────────────────────────────────────────────────────
test('todo link database.html#… das páginas abre um card ou uma família', () => {
  const html = readdirSync(SITE).filter((f) => f.endsWith('.html'));
  const js = readdirSync(path.join(SITE, 'assets', 'js')).filter((f) => f.endsWith('.js')).map((f) => path.join('assets', 'js', f));
  const quebrados = [];
  for (const f of [...html, ...js]) {
    for (const m of readFileSync(path.join(SITE, f), 'utf8').matchAll(/database\.html#([A-Za-z0-9_-]+)/g)) {
      if (!card(m[1]) && !T.familyForHash(D, m[1])) quebrados.push(`${f}: #${m[1]}`);
    }
  }
  assert.deepEqual(quebrados, []);
});

test('app-data/data.json leva as famílias e os mesmos cards do data.js', () => {
  const app = JSON.parse(readFileSync(path.join(SITE, 'app-data', 'data.json'), 'utf8'));
  assert.deepEqual(app.families, js(D.families));
  assert.deepEqual(app.studies.map((s) => s.uid), js(D.studies.map((s) => s.uid)));
});

// ── validador: injeção de defeito numa cópia ──────────────────────────────
const raiz = mkdtempSync(path.join(tmpdir(), 'study-families-'));
mkdirSync(path.join(raiz, 'scripts'));
mkdirSync(path.join(raiz, 'assets', 'js'), { recursive: true });
copyFileSync(path.join(SITE, 'scripts', 'validate_cards.mjs'), path.join(raiz, 'scripts', 'validate_cards.mjs'));
test.after(() => rmSync(raiz, { recursive: true, force: true }));
const bruto = readFileSync(DATA, 'utf8');
const CABECALHO = bruto.slice(0, bruto.indexOf('*/') + 3);
function validarCom(mutar) {
  const d = JSON.parse(JSON.stringify(D));
  mutar(d);
  writeFileSync(path.join(raiz, 'assets', 'js', 'data.js'), `${CABECALHO}window.THERA_DATA = ${JSON.stringify(d)};\n`);
  const r = spawnSync('node', [path.join(raiz, 'scripts', 'validate_cards.mjs')], { encoding: 'utf8' });
  return { code: r.status, saida: (r.stdout ?? '') + (r.stderr ?? '') };
}
const reprova = (nome, mutar, trecho) => test(`validador reprova: ${nome}`, () => {
  const r = validarCom(mutar);
  assert.equal(r.code, 1, r.saida);
  assert.match(r.saida, trecho);
});

test('validador aceita o data.js real (mesmo NCT entre membros, família sem resultado)', () => {
  assert.equal(validarCom(() => {}).code, 0);
});
reprova('family_id inexistente no card', (d) => { d.studies.find((s) => s.uid === 'stampede-docetaxel-m1').family_id = 'nao-existe'; }, /não existe em families/);
reprova('HR dentro da família', (d) => { d.families[0].design_summary += ' HR 0,81'; }, /resultado clínico/);
reprova('legacy_uid que ainda é card', (d) => { d.families[0].legacy_uids.push('prostata_contexto_3'); }, /ainda existe como card/);
reprova('membro fora de todos os braços', (d) => {
  for (const a of d.families[0].arms) a.card_uids = a.card_uids.filter((u) => u !== 'stampede-metformina-m1');
}, /não aparece em nenhum braço/);
reprova('braço apontando para card sem family_id', (d) => { d.families[0].arms[1].card_uids = ['prostata_contexto_3']; }, /não declara family_id/);
reprova('design_type desconhecido', (d) => { d.families[0].design_type = 'mega_card'; }, /design_type/);

// ── título M0 (refinamento editorial) ─────────────────────────────────────
test('card M0 descreve dois ensaios, sem sugerir um braço único "± enzalutamida"', () => {
  const m = card('stampede-abi-enza-m0-alto-risco');
  assert.equal(T.studyTitle(m.estudo), 'STAMPEDE · Intensificação com abiraterona — M0 alto risco');
  assert.doesNotMatch(m.estudo + m.comparison_label, /±/);
  assert.match(m.desenho, /34953525/);
  assert.match(m.desenho, /abiraterona\/prednisolona vs ADT/);
  assert.match(m.desenho, /abiraterona\/prednisolona \+ enzalutamida vs ADT/);
});

// ── i18n da interface de famílias ──────────────────────────────────────────
const DICT = {};
const regCtx = vm.createContext({ window: { _i18nRegister: (l, d) => { DICT[l] = d; } } });
for (const l of ['pt-br', 'en']) vm.runInContext(readFileSync(path.join(SITE, 'assets', 'lang', `${l}.js`), 'utf8'), regCtx);
const HTML_DB = readFileSync(path.join(SITE, 'database.html'), 'utf8');
const BLOCOS_FAM = [...HTML_DB.matchAll(/<!-- fam:ini[\s\S]*?<!-- fam:fim -->/g)].map((m) => m[0]);
// chaves diretas (tt('db.x')), chaves por tipo de família (famK: 'x' e 'xCohort') e as dos métodos de contagem/vínculo
const CHAVES = [...new Set([
  ...[...BLOCOS_FAM.join('\n').matchAll(/tt\('db\.(\w+)'/g)].map((m) => m[1]),
  ...[...BLOCOS_FAM.join('\n').matchAll(/famK\([^,]+, '(\w+)'\)/g)].flatMap((m) => [m[1], m[1] + 'Cohort', m[1] + 'Analysis', m[1] + 'Randomization', m[1] + 'Comparison']),
  'famComparisonsN', 'famComparisonsNOne', 'famPartOf_factorial', 'famFactorialDesign',
  'famRandomizations', 'famRandomizationsOne', 'famPartOf_master_protocol', 'famPartOf_multicohort',
  'famContributing', 'famOverlap', 'famPartOf_integrated_analysis', 'famArm_integrated_analysis', 'famTreatment_integrated_analysis',
  'famOpenProtocol_integrated_analysis', 'famSeeOthers_integrated_analysis', 'famNote_integrated_analysis',
  'famAnalyses', 'famAnalysesOne', 'famCohorts', 'famCohortsOne', 'famPartOf', 'famPartOfCohort', 'famPartOf_basket',
  'famSharedIntervention',
])];

test('interface de famílias usa chaves existentes em PT-BR e EN, com tradução de fato', () => {
  assert.ok(BLOCOS_FAM.length >= 4, 'blocos fam:ini/fam:fim');
  assert.ok(CHAVES.length >= 15, `chaves usadas: ${CHAVES.length}`);
  const tipos = Object.keys(DICT['pt-br'].db).filter((k) => /^famType(Short)?_/.test(k));
  for (const t of T.FAMILY_TYPES) assert.ok(tipos.includes('famType_' + t) && tipos.includes('famTypeShort_' + t), t);
  for (const k of [...CHAVES, ...tipos]) {
    assert.ok(DICT['pt-br'].db[k], `pt-br sem db.${k}`);
    assert.ok(DICT.en.db[k], `en sem db.${k}`);
  }
  const iguais = CHAVES.filter((k) => DICT['pt-br'].db[k] === DICT.en.db[k]);
  assert.deepEqual(iguais.filter((k) => k !== 'famStatus'), [], 'texto EN idêntico ao PT');
});

test('nenhum texto da interface de famílias fica fixo em português fora do i18n', () => {
  const ptTextos = Object.entries(DICT['pt-br'].db).filter(([k]) => k.startsWith('fam')).map(([, v]) => v);
  for (const bloco of BLOCOS_FAM) {
    const semI18n = bloco.replace(/tt\('db\.\w+',\s*'[^']*'\)/g, 'TT()').replace(/<!--[\s\S]*?-->/g, '');
    for (const v of ptTextos) assert.ok(!semI18n.includes(v), `texto fixo: "${v}"`);
    const textos = [...semI18n.matchAll(/>([^<>]+)</g)].map((m) => m[1].trim()).filter((x) => /[A-Za-zÀ-ú]/.test(x))
      .filter((x) => !['ClinicalTrials.gov'].includes(x));   // nome próprio, igual ao modal do card
    assert.deepEqual(textos, [], 'nó de texto fixo na interface de famílias');
  }
});

test('textos da interface de famílias recomputam quando o dicionário EN chega na 1ª visita', () => {
  const i18n = readFileSync(path.join(SITE, 'assets', 'js', 'i18n.js'), 'utf8');
  assert.match(i18n, /new CustomEvent\('langready'/);
  assert.match(HTML_DB, /addEventListener\('langready', \(\) => \{ this\.langTick\+\+; \}\)/);
  assert.match(HTML_DB, /tt\(k, f\) \{ this\.langTick;/);
});

// ── famílias basket: KEYNOTE-158, ROAR, DESTINY-PanTumor02 ─────────────────
/* Basket = protocolo com coortes independentes (uma população, uma intervenção, uma
 * publicação por card). A família liga as coortes; o resultado fica em cada card. */
const BASKET = {
  'keynote-158': { nct: 'NCT02628067', membros: ['hepatobiliar_32', 'endometrio_6', 'cervix_8'] },
  roar: { nct: 'NCT02034110', membros: ['hepatobiliar_34', 'tireoide_avancado_7'] },
  'destiny-pantumor02': { nct: 'NCT04482309', membros: ['hepatobiliar_35', 'urotelial_avancado_6'] },
};
const PMID_COORTE = {
  hepatobiliar_32: '31682550', endometrio_6: '39847999', cervix_8: '30943124', hepatobiliar_34: '32818466',
  tireoide_avancado_7: '35026411', hepatobiliar_35: '37870536', urotelial_avancado_6: '37870536',
};
const TODOS_BASKET = Object.values(BASKET).flatMap((b) => b.membros);
// KEYNOTE-158: só o colo do útero é coorte protocolar (E); BTC é recorte tumor-específico da população
// MSI-H/dMMR e endométrio junta as coortes D + K → "analysis".
const RELACAO = Object.fromEntries(TODOS_BASKET.map((u) => [u, 'cohort']));
Object.assign(RELACAO, { hepatobiliar_32: 'analysis', endometrio_6: 'analysis' });

test('vocabulário genérico da família: braços, coortes ou análises conforme os membros', () => {
  assert.equal(T.familyUnitKind(D, STAMPEDE), 'arm');
  assert.equal(T.familyUnitKind(D, T.familyById(D, 'keynote-158')), 'analysis');
  assert.equal(T.familyUnitKind(D, T.familyById(D, 'roar')), 'cohort');
  assert.equal(T.familyUnitKind(D, T.familyById(D, 'destiny-pantumor02')), 'cohort');
  const kn = T.familyById(D, 'keynote-158');
  assert.deepEqual(js(kn.cohorts.map((c) => [c.label, c.cohort])),
    [['Colangiocarcinoma MSI-H/dMMR', 'MSI-H/dMMR'], ['Endométrio MSI-H/dMMR', 'D + K'], ['Colo do útero', 'E']]);
  assert.match(kn.cohorts[0].selection, /^Análise tumor-específica da população MSI-H/);
  assert.match(kn.cohorts[1].selection, /^Coortes D \+ K/);
  assert.match(kn.cohorts[2].selection, /^Coorte E/);
});

test('3 famílias basket com coortes (não braços), registro próprio e member_uids coerente', () => {
  for (const [id, b] of Object.entries(BASKET)) {
    const f = T.familyById(D, id);
    assert.ok(f, id);
    assert.equal(f.design_type, 'basket');
    assert.deepEqual(js(f.registry_ids), [b.nct]);
    assert.equal(f.arms, undefined, `${id} não tem braços`);
    assert.ok(T.familyIsCohort(f));
    assert.deepEqual(js(f.member_uids), b.membros);
    assert.deepEqual(js(f.cohorts.flatMap((c) => c.card_uids)), b.membros);
    assert.ok(f.shared_intervention && f.design_summary && f.population, id);
    assert.equal(f.legacy_uids, undefined, `${id} não aposenta uid`);
  }
});

test('basket: membros abrem individualmente, com uid preservado e título distinto por coorte', () => {
  assert.equal(D.studies.length, D.metadata.total_studies);   // a migração não cria nem apaga card
  for (const [id, b] of Object.entries(BASKET)) {
    const f = T.familyById(D, id);
    assert.deepEqual(js(T.familyMembers(D, f).map((s) => s.uid)), b.membros);
    const titulos = b.membros.map((u) => T.studyTitle(card(u).estudo));
    assert.equal(new Set(titulos).size, titulos.length, `títulos distintos em ${id}`);
    for (const u of b.membros) {
      const s = card(u);
      assert.equal(s.family_id, id);
      assert.equal(s.family_relation, RELACAO[u], u);
      assert.ok(s.comparison_label, u);
      assert.ok(T.studyTitle(s.estudo).startsWith(f.family_name + ' · '), `título de ${u}`);
      assert.equal(T.familyForHash(D, u), null, `#${u} abre o card, não a família`);
    }
  }
});

test('basket: NCT compartilhado só dentro da família; o validador não acusa duplicata', () => {
  for (const [id, b] of Object.entries(BASKET)) {
    const comNct = D.studies.filter((s) => s.nct === b.nct);
    assert.deepEqual(js(comNct.map((s) => s.uid).sort()), [...b.membros].sort());
    assert.ok(comNct.every((s) => s.family_id === id));
  }
  const r = validarCom(() => {});
  for (const b of Object.values(BASKET)) assert.doesNotMatch(r.saida, new RegExp(`NCT ${b.nct} também está`));
});

test('validador: NCT repetido sem família em comum continua sendo apontado (não afrouxa)', () => {
  const r = validarCom((d) => { delete d.studies.find((s) => s.uid === 'cervix_8').family_id; });
  assert.match(r.saida, /NCT NCT02628067 também está em/);
  const outro = D.studies.find((s) => !s.family_id && /^NCT\d{8}$/.test(s.nct || '')).uid;
  const r2 = validarCom((d) => { d.studies.find((s) => s.uid === outro).nct = 'NCT02034110'; });
  assert.match(r2.saida, new RegExp(`${outro} \\| NCT NCT02034110 também está em hepatobiliar_34, tireoide_avancado_7`));
});
reprova('resultado clínico numa coorte da família', (d) => {
  d.families.find((f) => f.family_id === 'roar').cohorts[0].selection += ' (ORR 51%)';
}, /coorte BTC: resultado clínico/);
reprova('basket descrito com braços', (d) => {
  const f = d.families.find((x) => x.family_id === 'roar'); f.arms = f.cohorts; delete f.cohorts;
}, /basket descreve coortes/);
reprova('member_uids divergente', (d) => { d.families.find((f) => f.family_id === 'roar').member_uids.pop(); }, /member_uids não bate/);
reprova('membro de basket com family_relation de plataforma', (d) => {
  d.studies.find((s) => s.uid === 'urotelial_avancado_6').family_relation = 'comparison';
}, /family_relation "cohort"/);

test('busca pelo acrônimo mostra a família e as coortes', () => {
  for (const [q, id] of [['KEYNOTE-158', 'keynote-158'], ['ROAR', 'roar'], ['DESTINY-PanTumor02', 'destiny-pantumor02'], ['NCT04482309', 'destiny-pantumor02']]) {
    assert.ok(T.familiesToShow(D, busca(q), q, false).some((f) => f.family_id === id), q);
    for (const u of BASKET[id].membros) assert.ok(busca(q).some((s) => s.uid === u), `${q} → ${u}`);
  }
});

test('busca por tumor encontra a coorte direto, sem bloco de família', () => {
  for (const [q, u] of [['colangiocarcinoma', 'hepatobiliar_32'], ['endométrio', 'endometrio_6'], ['colo do útero', 'cervix_8'],
    ['vias biliares', 'hepatobiliar_34'], ['anaplásic', 'tireoide_avancado_7'], ['vias biliares', 'hepatobiliar_35'], ['urotelial', 'urotelial_avancado_6']]) {
    assert.ok(busca(q).some((s) => s.uid === u), `${q} → ${u}`);
  }
  assert.ok(!T.familiesToShow(D, busca('urotelial'), 'urotelial', false).some((f) => f.family_id in BASKET));
});

test('filtros de tumor e categoria das coortes continuam os mesmos', () => {
  const esperado = {
    hepatobiliar_32: ['hepatobiliar', 'colangiocarcinoma'], endometrio_6: ['endometrio', 'endometrio'], cervix_8: ['cervix', 'cervix'],
    hepatobiliar_34: ['hepatobiliar', 'colangiocarcinoma'], tireoide_avancado_7: ['tireoide_avancado', 'tireoide'],
    hepatobiliar_35: ['hepatobiliar', 'colangiocarcinoma'], urotelial_avancado_6: ['urotelial_avancado', 'urotelial'],
  };
  for (const [u, [cat, tumor]] of Object.entries(esperado)) {
    assert.equal(card(u).category_id, cat, u);
    assert.deepEqual(js(T.tumorTypes.filter((t) => t.match(card(u))).map((t) => t.id)), [tumor], u);
  }
});

test('basket: PMID, citation e pubmed_url batem com a publicação representada', () => {
  for (const [u, pmid] of Object.entries(PMID_COORTE)) {
    const s = card(u);
    assert.equal(s.citation.pmid, pmid, u);
    assert.equal(s.pubmed_url, `https://pubmed.ncbi.nlm.nih.gov/${pmid}/`, u);
    assert.equal(s.ano_pub, s.citation.year, `ano de ${u}`);
    assert.match(s.estudo, new RegExp(`\\(${s.citation.year}\\)$`), `ano no título de ${u}`);
  }
});

test('basket: correções científicas não regridem', () => {
  const t = JSON.stringify(TODOS_BASKET.map(card));
  assert.doesNotMatch(t, /<\/?strong>/, 'HTML cru');
  for (const u of TODOS_BASKET) assert.notEqual(card(u).radiofarmaco.trim(), '—', `intervenção vazia em ${u}`);
  assert.doesNotMatch(JSON.stringify(card('hepatobiliar_34')), /46-51|8,7 m|OS mediana 14 m/);   // ORR ambígua e números sem fonte
  const btc = JSON.stringify(card('hepatobiliar_35'));
  assert.doesNotMatch(btc, /Nat Med|~5%|~12 m/);                      // publicação inexistente; IHC 2+ e DoR errados
  assert.match(btc, /IHC 2\+ central \(n=14\): nenhuma resposta/);
  assert.match(JSON.stringify(card('hepatobiliar_32')), /PFS mediana 4,2 m/);
  assert.doesNotMatch(JSON.stringify(card('cervix_8')), /2,6%|11,0 m/);
  assert.doesNotMatch(JSON.stringify(card('urotelial_avancado_6')), /Ventana|44 centros/);
  assert.doesNotMatch(JSON.stringify(card('tireoide_avancado_7')), /Mediana 72a|pirexia 28%/);
});

test('contagem do family card: 1 análise / N análises, 1 coorte / N coortes', () => {
  const corpo = HTML_DB.match(/famCount\(f\) \{([\s\S]*?)\n    \},/)[1];
  const vm2 = { tt: (k, f) => (k.endsWith('One') ? 'U:' : 'P:') + f, famKind: (f) => T.familyUnitKind(D, f), familyMembers: (f) => T.familyMembers(D, f) };
  const famCount = new Function('f', corpo).bind(vm2);
  assert.equal(famCount(T.familyById(D, 'stampede2')), '1 U:análise no Database');
  assert.equal(famCount(STAMPEDE), '6 P:análises no Database');
  assert.equal(famCount(T.familyById(D, 'keynote-158')), '3 P:análises no Database');
  assert.equal(famCount(T.familyById(D, 'destiny-pantumor02')), '2 P:coortes no Database');
  assert.equal(famCount(T.familyById(D, 'roar')), '2 P:coortes no Database');
  for (const l of ['pt-br', 'en']) for (const k of ['famAnalyses', 'famAnalysesOne', 'famCohorts', 'famCohortsOne']) assert.ok(DICT[l].db[k], `${l} ${k}`);
  assert.equal(DICT.en.db.famAnalysesOne, 'analysis in the Database');
  assert.equal(DICT['pt-br'].db.famCohortsOne, 'coorte no Database');
  assert.equal(DICT['pt-br'].db.famArmsAnalysis, 'Análises representadas');
  assert.equal(DICT.en.db.famArmsAnalysis, 'Represented analyses');
  assert.equal(DICT.en.db.famAnalyses, 'analyses in the Database');
});

// ── famílias multicoorte: KRYSTAL-1 e LIBRETTO-001 ─────────────────────────
/* Multicoorte = um protocolo, várias coortes por tumor/biomarcador, cada uma com
 * publicação própria. Mesmo componente dos baskets; badge "Multicoorte". */
const MULTI = {
  'krystal-1': { nct: 'NCT03785249', membros: ['krystal-1-adagrasib-em-nsclc-kras-g12c', 'pancreas_8'] },
  'libretto-001': { nct: 'NCT03157128', membros: ['libretto-001-selpercatinib-em-nsclc-ret-rearranjado', 'tireoide_avancado_3'] },
};
const PMID_MULTI = {
  'krystal-1-adagrasib-em-nsclc-kras-g12c': '35658005', pancreas_8: '37099736',
  'libretto-001-selpercatinib-em-nsclc-ret-rearranjado': '32846060', tireoide_avancado_3: '32846061',
};
const TODOS_MULTI = Object.values(MULTI).flatMap((m) => m.membros);
// NSCLC KRYSTAL-1 é a coorte de registro; PDAC é recorte de 21 pacientes da coorte "outros tumores sólidos";
// os dois cards LIBRETTO-001 reúnem várias populações de eficácia → "analysis".
const RELACAO_MULTI = {
  'krystal-1-adagrasib-em-nsclc-kras-g12c': 'cohort', pancreas_8: 'analysis',
  'libretto-001-selpercatinib-em-nsclc-ret-rearranjado': 'analysis', tireoide_avancado_3: 'analysis',
};

test('princípio: design_type descreve o protocolo; family_relation descreve o card (um não implica o outro)', () => {
  // mesma arquitetura (multicoorte), relações diferentes entre membros da mesma família
  const kr = T.familyMembers(D, T.familyById(D, 'krystal-1')).map((s) => s.family_relation);
  assert.deepEqual(js(kr), ['cohort', 'analysis']);
  // arquiteturas diferentes (basket × multicoorte), mesmo vocabulário quando os membros são análises
  assert.equal(T.familyUnitKind(D, T.familyById(D, 'keynote-158')), 'analysis');
  assert.equal(T.familyUnitKind(D, T.familyById(D, 'libretto-001')), 'analysis');
  // multicoorte só de coortes protocolares fala em "coortes"; o vocabulário vem dos membros, não do design_type
  const f = { family_id: 'x', design_type: 'multicohort', cohorts: [{ cohort: 'A', card_uids: ['a'] }, { cohort: 'B', card_uids: ['b'] }] };
  const dx = (rel) => ({ families: [f], studies: [{ uid: 'a', family_id: 'x', family_relation: 'cohort' }, { uid: 'b', family_id: 'x', family_relation: rel }] });
  assert.equal(T.familyUnitKind(dx('cohort'), f), 'cohort');
  assert.equal(T.familyUnitKind(dx('analysis'), f), 'analysis');
  // o validador não aceita membro sem relação explícita, mesmo em família multicoorte
});
reprova('membro de multicoorte sem family_relation explícita', (d) => {
  delete d.studies.find((s) => s.uid === 'pancreas_8').family_relation;
}, /family_relation/);

test('2 famílias multicoorte: registro, coortes, member_uids e só coortes como membros', () => {
  for (const [id, m] of Object.entries(MULTI)) {
    const f = T.familyById(D, id);
    assert.ok(f, id);
    assert.equal(f.design_type, 'multicohort');
    assert.deepEqual(js(f.registry_ids), [m.nct]);
    assert.equal(f.arms, undefined);
    assert.deepEqual(js(f.member_uids), m.membros);
    assert.deepEqual(js(f.cohorts.flatMap((c) => c.card_uids)), m.membros);
    assert.equal(T.familyUnitKind(D, f), 'analysis', `${id}: há membro que é análise, não coorte protocolar`);
    assert.equal(f.legacy_uids, undefined, `${id} não aposenta uid`);
    for (const c of f.cohorts) assert.match(c.publication.pmid, /^\d+$/);
  }
});

test('multicoorte: filhos independentes, uid preservado, título distinto, relação declarada por card', () => {
  assert.equal(D.studies.length, D.metadata.total_studies);   // a migração não cria nem apaga card
  for (const id of Object.keys(MULTI)) assert.ok(D.families.some((f) => f.family_id === id), id);
  for (const [id, m] of Object.entries(MULTI)) {
    const f = T.familyById(D, id);
    assert.deepEqual(js(T.familyMembers(D, f).map((s) => s.uid)), m.membros);
    const titulos = m.membros.map((u) => T.studyTitle(card(u).estudo));
    assert.equal(new Set(titulos).size, titulos.length);
    for (const u of m.membros) {
      const s = card(u);
      assert.equal(s.family_id, id);
      assert.equal(s.family_relation, RELACAO_MULTI[u], u);
      assert.ok(T.studyTitle(s.estudo).startsWith(f.family_name + ' · '), u);
      assert.equal(T.familyForHash(D, u), null, `#${u} abre o card`);
      assert.equal(s.nct, m.nct);
    }
  }
  assert.equal(T.studyTitle(card('krystal-1-adagrasib-em-nsclc-kras-g12c').estudo), 'KRYSTAL-1 · NSCLC KRAS G12C');
  assert.equal(T.studyTitle(card('pancreas_8').estudo), 'KRYSTAL-1 · PDAC KRAS G12C');
});

test('multicoorte: NCT compartilhado dentro da família sai dos avisos; grupos não migrados continuam', () => {
  const r = validarCom(() => {});
  assert.doesNotMatch(r.saida, /NCT NCT03785249 também está|NCT NCT03157128 também está/);
});

test('multicoorte: busca pelo acrônimo mostra a família; busca por tumor acha o filho', () => {
  for (const [q, id] of [['KRYSTAL-1', 'krystal-1'], ['LIBRETTO-001', 'libretto-001'], ['NCT03157128', 'libretto-001']]) {
    assert.ok(T.familiesToShow(D, busca(q), q, false).some((f) => f.family_id === id), q);
    for (const u of MULTI[id].membros) assert.ok(busca(q).some((s) => s.uid === u), `${q} → ${u}`);
  }
  for (const [q, u] of [['adagrasibe', 'pancreas_8'], ['pâncreas', 'pancreas_8'], ['fusão RET', 'libretto-001-selpercatinib-em-nsclc-ret-rearranjado'],
    ['medular', 'tireoide_avancado_3'], ['KRAS G12C', 'krystal-1-adagrasib-em-nsclc-kras-g12c']]) {
    assert.ok(busca(q).some((s) => s.uid === u), `${q} → ${u}`);
  }
});

test('multicoorte: filtros de tumor e categoria inalterados', () => {
  const esperado = {
    'krystal-1-adagrasib-em-nsclc-kras-g12c': ['nsclc_alvo', 'pulmao'], pancreas_8: ['pancreas', 'pancreas'],
    'libretto-001-selpercatinib-em-nsclc-ret-rearranjado': ['nsclc_alvo', 'pulmao'], tireoide_avancado_3: ['tireoide_avancado', 'tireoide'],
  };
  for (const [u, [cat, tumor]] of Object.entries(esperado)) {
    assert.equal(card(u).category_id, cat, u);
    assert.deepEqual(js(T.tumorTypes.filter((t) => t.match(card(u))).map((t) => t.id)), [tumor], u);
  }
});

test('multicoorte: PMID, citation e ano batem com a publicação representada', () => {
  for (const [u, pmid] of Object.entries(PMID_MULTI)) {
    const s = card(u);
    assert.equal(s.citation.pmid, pmid, u);
    assert.equal(s.pubmed_url, `https://pubmed.ncbi.nlm.nih.gov/${pmid}/`, u);
    assert.equal(s.ano_pub, s.citation.year, u);
    assert.match(s.estudo, new RegExp(`\\(${s.citation.year}\\)$`), u);
  }
});

test('multicoorte: correções científicas não regridem (LIBRETTO-531 fora; números transportados fora)', () => {
  const tir = JSON.stringify(card('tireoide_avancado_3'));
  assert.doesNotMatch(tir, /LIBRETTO-531|Hadoux|NEJM 2024/, 'LIBRETTO-531 é outro ensaio');
  assert.doesNotMatch(tir, /n=27|DTC RET-fusion|Categoria 1/);
  assert.match(tir, /n=19/);
  const pdac = JSON.stringify(card('pancreas_8'));
  assert.doesNotMatch(card('pancreas_8').primario, /DOR|DoR/, 'DoR de 5,3 m é da coorte inteira, não do pâncreas');
  assert.match(pdac, /ECOG 0-1/);
  assert.doesNotMatch(pdac, /RMC-9805|basket trial/);
  const kn = JSON.stringify(card('krystal-1-adagrasib-em-nsclc-kras-g12c'));
  assert.doesNotMatch(kn, /DCR 80%|Náusea 71%|maior que sotorasib|aguarda fase 3/);
  const ln = JSON.stringify(card('libretto-001-selpercatinib-em-nsclc-ret-rearranjado'));
  assert.doesNotMatch(ln, /LIBRETTO-431|pós-platina 65%|ALT\/AST 9%/);
  for (const u of TODOS_MULTI) assert.notEqual(card(u).radiofarmaco.trim(), '—', u);
});

test('multicoorte: contagem 1/N, badge e rótulos em PT/EN', () => {
  const corpo = HTML_DB.match(/famCount\(f\) \{([\s\S]*?)\n    \},/)[1];
  const vm2 = { tt: (k, f) => (k.endsWith('One') ? 'U:' : 'P:') + f, famKind: (f) => T.familyUnitKind(D, f), familyMembers: (f) => T.familyMembers(D, f) };
  const famCount = new Function('f', corpo).bind(vm2);
  assert.equal(famCount(T.familyById(D, 'krystal-1')), '2 P:análises no Database');
  assert.equal(famCount(T.familyById(D, 'libretto-001')), '2 P:análises no Database');
  const umaCoorte = JSON.parse(JSON.stringify(T.familyById(D, 'krystal-1')));
  umaCoorte.family_id = 'x'; umaCoorte.cohorts = umaCoorte.cohorts.slice(0, 1);
  const dx = { studies: [{ ...js(card('krystal-1-adagrasib-em-nsclc-kras-g12c')), family_id: 'x' }], families: [umaCoorte] };
  const vm3 = { ...vm2, famKind: (f) => T.familyUnitKind(dx, f), familyMembers: (f) => T.familyMembers(dx, f) };
  assert.equal(new Function('f', corpo).bind(vm3)(umaCoorte), '1 U:coorte no Database');
  assert.equal(DICT['pt-br'].db.famType_multicohort, 'Multicoorte');
  assert.equal(DICT.en.db.famType_multicohort, 'Multicohort');
  assert.equal(DICT['pt-br'].db.famCohortsOne, 'coorte no Database');
  assert.equal(DICT.en.db.famCohorts, 'cohorts in the Database');
  assert.equal(DICT['pt-br'].db.famArmsCohort, 'Coortes representadas');
  assert.equal(DICT.en.db.famArmsCohort, 'Represented cohorts');
  assert.equal(DICT['pt-br'].db.famArmsAnalysis, 'Análises representadas');
  assert.equal(DICT['pt-br'].db.famAnalyses, 'análises no Database');
  assert.equal(DICT['pt-br'].db.famPartOf_multicohort, 'Parte do estudo multicoorte');
  assert.equal(DICT.en.db.famPartOf_multicohort, 'Part of the multicohort trial');
});

// ── master protocol: HR-NBL1/SIOPEN ────────────────────────────────────────
/* Master protocol = um protocolo de tratamento ao qual foram incorporadas randomizações (R0–R4) em
 * componentes e períodos diferentes — não fases sequenciais —, cada uma com elegíveis e publicação
 * próprios. A família lista todas as randomizações do protocolo;
 * os cards são as randomizações R1 (BuMel vs CEM) e R2 (dinutuximabe beta ± IL-2). */
const HRNBL = T.familyById(D, 'hr-nbl1-siopen');
const HR_MEMBROS = ['neuroblastoma_10', 'neuroblastoma_7'];

test('master protocol HR-NBL1/SIOPEN: randomizações R0–R4, só R1 e R2 com card, sem aposentar uid', () => {
  assert.ok(HRNBL);
  assert.equal(HRNBL.design_type, 'master_protocol');
  assert.deepEqual(js(HRNBL.registry_ids), ['NCT01704716']);
  assert.equal(HRNBL.arms, undefined);
  assert.equal(HRNBL.cohorts, undefined);
  assert.deepEqual(js(HRNBL.randomizations.map((x) => x.randomization)), ['R0', 'R1', 'R2', 'R3', 'R4']);
  assert.equal(HRNBL.stages, undefined);
  assert.match(HRNBL.design_summary, /Não são fases sequenciais/);
  assert.doesNotMatch(JSON.stringify(HRNBL), /\betapas?\b|sucessivas/i, 'randomizações não são etapas sequenciais');
  assert.deepEqual(js(HRNBL.randomizations.filter((x) => x.card_uids.length).map((x) => [x.randomization, x.card_uids[0]])), [['R1', 'neuroblastoma_10'], ['R2', 'neuroblastoma_7']]);
  assert.deepEqual(js(HRNBL.member_uids), HR_MEMBROS);
  assert.equal(HRNBL.legacy_uids, undefined);
  assert.ok(D.families.some((f) => f.family_id === 'hr-nbl1-siopen'));
});

test('master protocol: membros são randomizações; vocabulário vem da relação, não do design_type', () => {
  for (const u of HR_MEMBROS) assert.equal(card(u).family_relation, 'randomization', u);
  assert.equal(T.familyUnitKind(D, HRNBL), 'randomization');
  const f = { family_id: 'x', design_type: 'master_protocol', randomizations: [{ randomization: 'A', card_uids: ['a'] }, { randomization: 'B', card_uids: ['b'] }] };
  const dx = (rel) => ({ families: [f], studies: [{ uid: 'a', family_id: 'x', family_relation: 'randomization' }, { uid: 'b', family_id: 'x', family_relation: rel }] });
  assert.equal(T.familyUnitKind(dx('randomization'), f), 'randomization');
  assert.equal(T.familyUnitKind(dx('analysis'), f), 'analysis', 'mistura randomização + análise → análises');
});

test('master protocol: filhos independentes, títulos por randomização, links família ↔ card', () => {
  const titulos = HR_MEMBROS.map((u) => T.studyTitle(card(u).estudo));
  assert.deepEqual(js(titulos), ['HR-NBL1/SIOPEN · R1: BuMel vs CEM', 'HR-NBL1/SIOPEN · R2: dinutuximabe beta ± IL-2']);
  assert.deepEqual(js(T.familyMembers(D, HRNBL).map((s) => s.uid)), HR_MEMBROS);
  for (const u of HR_MEMBROS) {
    assert.equal(card(u).family_id, 'hr-nbl1-siopen');
    assert.equal(T.familyById(D, card(u).family_id).family_id, 'hr-nbl1-siopen');
    assert.equal(T.familyForHash(D, u), null, `#${u} abre o card`);
    assert.equal(card(u).nct, 'NCT01704716');
    assert.equal(card(u).category_id, 'neuroblastoma');
    assert.deepEqual(js(T.tumorTypes.filter((t) => t.match(card(u))).map((t) => t.id)), ['neuroblastoma'], u);
  }
  assert.equal(T.familyForHash(D, 'hr-nbl1-siopen').family_id, 'hr-nbl1-siopen');
});

test('master protocol: busca pelo acrônimo mostra a família; por tema acha o filho', () => {
  for (const q of ['HR-NBL1', 'SIOPEN', 'NCT01704716']) {
    assert.ok(T.familiesToShow(D, busca(q), q, false).some((f) => f.family_id === 'hr-nbl1-siopen'), q);
    for (const u of HR_MEMBROS) assert.ok(busca(q).some((s) => s.uid === u), `${q} → ${u}`);
  }
  for (const [q, u] of [['BuMel', 'neuroblastoma_10'], ['dinutuximabe', 'neuroblastoma_7'], ['IL-2', 'neuroblastoma_7'], ['neuroblastoma', 'neuroblastoma_10']]) {
    assert.ok(busca(q).some((s) => s.uid === u), `${q} → ${u}`);
  }
});

test('master protocol: NCT01704716 sai dos avisos de NCT compartilhado', () => {
  const r = validarCom(() => {});
  assert.equal(r.code, 0, r.saida);
  assert.doesNotMatch(r.saida, /NCT NCT01704716 também está/);
  const avisos = [...r.saida.matchAll(/NCT (NCT\d{8}) também está/g)].map((m) => m[1]);
  assert.ok(!avisos.includes('NCT01704716'));
});
reprova('master protocol sem randomizações (randomizations)', (d) => {
  const f = d.families.find((x) => x.family_id === 'hr-nbl1-siopen'); f.arms = f.randomizations; delete f.randomizations;
}, /master protocol descreve as randomizações/);
reprova('membro de master protocol com relação de coorte', (d) => {
  d.studies.find((s) => s.uid === 'neuroblastoma_7').family_relation = 'cohort';
}, /family_relation "randomization" ou "analysis"/);
reprova('HR de verdade numa randomização da família (HR-NBL1 no nome não conta)', (d) => {
  d.families.find((x) => x.family_id === 'hr-nbl1-siopen').randomizations[1].label += ' (HR 0,77)';
}, /randomização R1: resultado clínico/);

test('master protocol: PMID/citation da randomização representada e correções não regridem', () => {
  for (const [u, pmid, ano] of [['neuroblastoma_10', '28259608', 2017], ['neuroblastoma_7', '30442501', 2018]]) {
    const s = card(u);
    assert.equal(s.citation.pmid, pmid, u);
    assert.equal(s.pubmed_url, `https://pubmed.ncbi.nlm.nih.gov/${pmid}/`, u);
    assert.equal(s.ano_pub, ano);
    assert.equal(s.citation.year, ano);
  }
  const r2 = JSON.stringify(card('neuroblastoma_7'));
  assert.doesNotMatch(r2, /10 dias|infusão contínua|1\.000 mg|HR-NBL1\.5|não-inferioridade|32013055/, 'esquema de 10 dias é da R4; Cancers 2020 é outra análise');
  assert.match(card('neuroblastoma_7').esquema, /infusão de 8 h/);
  const r1 = JSON.stringify(card('neuroblastoma_10'));
  assert.doesNotMatch(r1, /HR 0,77|p=0,001|OS 3 anos|interina|<\/?strong>|defibrotide/);
  assert.match(card('neuroblastoma_10').primario, /p=0,0005/);
  assert.match(card('neuroblastoma_10').tox_g3, /4% \(BuMel\) vs 10% \(CEM\)/, 'BuMel teve MENOS toxicidade grave');
});

test('master protocol: contagem 1/N randomizações, badge e rótulos PT/EN', () => {
  const corpo = HTML_DB.match(/famCount\(f\) \{([\s\S]*?)\n    \},/)[1];
  const vm2 = { tt: (k, f) => (k.endsWith('One') ? 'U:' : 'P:') + f, famKind: (f) => T.familyUnitKind(D, f), familyMembers: (f) => T.familyMembers(D, f) };
  assert.equal(new Function('f', corpo).bind(vm2)(HRNBL), '2 P:randomizações no Database');
  const f1 = { ...js(HRNBL), family_id: 'y', randomizations: [{ randomization: 'R1', card_uids: ['neuroblastoma_10'] }] };
  const d1 = { families: [f1], studies: [{ ...js(card('neuroblastoma_10')), family_id: 'y' }] };
  const vm3 = { ...vm2, famKind: (f) => T.familyUnitKind(d1, f), familyMembers: (f) => T.familyMembers(d1, f) };
  assert.equal(new Function('f', corpo).bind(vm3)(f1), '1 U:randomização no Database');
  for (const l of ['pt-br', 'en']) assert.equal(DICT[l].db.famType_master_protocol, 'Master protocol', l);
  assert.equal(DICT['pt-br'].db.famRandomizations, 'randomizações no Database');
  assert.equal(DICT.en.db.famRandomizationsOne, 'randomization in the Database');
  assert.equal(DICT['pt-br'].db.famArmsRandomization, 'Randomizações do protocolo');
  assert.equal(DICT.en.db.famArmsRandomization, 'Protocol randomizations');
  assert.equal(DICT['pt-br'].db.famPartOf_master_protocol, 'Parte do master protocol');
  assert.equal(DICT.en.db.famPartOf_master_protocol, 'Part of the master protocol');
  assert.match(HTML_DB, /a\.arm \|\| a\.cohort \|\| a\.randomization/);
});

// ── análises integradas: entrectinibe e larotrectinibe ─────────────────────
/* Análise integrada ≠ protocolo: vários estudos contribuem pacientes e cada publicação seleciona
 * sua população (tumor/fusão). Os estudos ficam em `contributing_studies` (nome + registro, que
 * pode ser NCT ou EudraCT); os cards são análises (`analysis`). */
const ENT = T.familyById(D, 'entrectinib-integrated');
const LARO = T.familyById(D, 'larotrectinib-integrated');
const ENT_CARD = 'entrectinib-pooled-ros1-e-ntrk-em-nsclc';

test('2 análises integradas: estudos contribuidores com NCT e EudraCT, sem linhas de protocolo', () => {
  for (const f of [ENT, LARO]) {
    assert.ok(f);
    assert.equal(f.design_type, 'integrated_analysis');
    for (const k of ['arms', 'cohorts', 'randomizations']) assert.equal(f[k], undefined, `${f.family_id}.${k}`);
    assert.ok(f.registry_ids.length >= 3, 'vários registros, nenhum "principal"');
    assert.deepEqual(js(f.contributing_studies.map((c) => c.registry_id)), js(f.registry_ids));
    assert.match(f.design_summary, /Não é um protocolo único/);
    assert.ok(f.overlap_note, 'nota de sobreposição/proveniência');
    assert.equal(T.familyUnitKind(D, f), 'analysis');
  }
  assert.deepEqual(js(ENT.contributing_studies.map((c) => [c.study_name, c.registry_id])),
    [['ALKA-372-001', 'EudraCT 2012-000148-88'], ['STARTRK-1', 'NCT02097810'], ['STARTRK-2', 'NCT02568267']]);
  assert.deepEqual(js(LARO.contributing_studies.map((c) => [c.study_name, c.registry_id])),
    [['LOXO-TRK-14001', 'NCT02122913'], ['SCOUT', 'NCT02637687'], ['NAVIGATE', 'NCT02576431']]);
  assert.ok(!ENT.contributing_studies.some((c) => /STARTRK-NG|NCT02650401/.test(JSON.stringify(c))), 'STARTRK-NG só entrou na segurança');
  assert.deepEqual(js(ENT.member_uids), [ENT_CARD, 'pancreas_9']);
  assert.deepEqual(js(LARO.member_uids), ['tireoide_avancado_8']);
  for (const id of ['entrectinib-integrated', 'larotrectinib-integrated']) assert.ok(D.families.some((f) => f.family_id === id), id);
});

test('análise integrada: membros são análises; uids preservados; títulos inequívocos', () => {
  for (const u of [ENT_CARD, 'pancreas_9', 'tireoide_avancado_8']) {
    assert.equal(card(u).family_relation, 'analysis', u);
    assert.equal(T.familyForHash(D, u), null, `#${u} abre o card`);
  }
  assert.equal(card(ENT_CARD).family_id, 'entrectinib-integrated');
  assert.equal(card('pancreas_9').family_id, 'entrectinib-integrated');
  assert.equal(card('tireoide_avancado_8').family_id, 'larotrectinib-integrated');
  assert.equal(T.studyTitle(card(ENT_CARD).estudo), 'Entrectinibe · NSCLC ROS1+ — análise integrada');
  assert.equal(T.studyTitle(card('pancreas_9').estudo), 'Entrectinibe · Pâncreas NTRK+ — subgrupo da análise integrada');
  assert.equal(T.studyTitle(card('tireoide_avancado_8').estudo), 'Larotrectinibe · Tireoide NTRK+ — análise integrada');
  assert.equal(D.studies.length, D.metadata.total_studies);   // a migração não cria nem apaga card
});

test('análise integrada: PMID correto por card e números da publicação representada', () => {
  for (const [u, pmid, ano] of [[ENT_CARD, '31838015', 2020], ['pancreas_9', '31838007', 2020], ['tireoide_avancado_8', '35333737', 2022]]) {
    assert.equal(card(u).citation.pmid, pmid, u);
    assert.equal(card(u).pubmed_url, `https://pubmed.ncbi.nlm.nih.gov/${pmid}/`, u);
    assert.equal(card(u).ano_pub, ano, u);
  }
  assert.match(card(ENT_CARD).primario, /ORR 77% \(41\/53/);
  assert.match(card(ENT_CARD).primario, /24,6 m/);
  assert.match(card('pancreas_9').primario, /2 de 3 pacientes \(67%/);
  assert.match(card('tireoide_avancado_8').primario, /71%.*86%.*29%/);
});

test('análise integrada: correções não regridem (sem mistura de programas, ROS1 separado de NTRK)', () => {
  const ent = JSON.stringify(card(ENT_CARD));
  assert.doesNotMatch(ent, /NTRK\+: ORR 57%|N=54|31838007/, 'card ROS1 sem resultados NTRK pan-tumor');
  assert.match(card(ENT_CARD).nct, /NCT02097810/);
  assert.match(card(ENT_CARD).nct, /EudraCT 2012-000148-88/);
  const pan = JSON.stringify(card('pancreas_9'));
  assert.doesNotMatch(pan, /[Ll]arotrectin|NCT02122913|NCT02576431|NCT02637687|NAVIGATE|~70|n~10|Cabanillas/);
  assert.match(card('pancreas_9').limit, /n=3/);
  assert.match(card('pancreas_9').secundario, /não específico do pâncreas/);
  const tir = JSON.stringify(card('tireoide_avancado_8'));
  assert.doesNotMatch(tir, /\bDTC\b|Hong DS et al\. Lancet Oncol 2024|n=261|29466156/);
  assert.match(card('tireoide_avancado_8').basal, /anaplásico 7/);
});

test('análise integrada: NCT compartilhado só dentro da família; zero avisos sem afrouxar o detector', () => {
  const r = validarCom(() => {});
  assert.equal(r.code, 0, r.saida);
  for (const n of [...ENT.registry_ids, ...LARO.registry_ids].filter((x) => /^NCT/.test(x))) {
    assert.doesNotMatch(r.saida, new RegExp(`NCT ${n} também está`), n);
  }
  // o detector continua ativo: um NCT do programa larotrectinibe num card do entrectinibe volta a ser apontado
  const r2 = validarCom((d) => { d.studies.find((s) => s.uid === 'pancreas_9').nct += ' / NCT02122913'; });
  assert.match(r2.saida, /NCT NCT02122913 também está em/);
});
reprova('análise integrada com um único estudo contribuidor', (d) => {
  d.families.find((f) => f.family_id === 'larotrectinib-integrated').contributing_studies.splice(1);
}, /≥2 estudos contribuidores/);
reprova('estudo contribuidor com registro inválido', (d) => {
  d.families.find((f) => f.family_id === 'entrectinib-integrated').contributing_studies[0].registry_id = 'ALKA-372-001';
}, /registro inválido/);
reprova('membro de análise integrada com relação de coorte', (d) => {
  d.studies.find((s) => s.uid === 'pancreas_9').family_relation = 'cohort';
}, /family_relation "analysis"/);
reprova('resultado clínico na nota de sobreposição', (d) => {
  d.families.find((f) => f.family_id === 'entrectinib-integrated').overlap_note += ' ORR 57%.';
}, /overlap_note traz resultado clínico/);

test('análise integrada: busca, filtros e links família ↔ card', () => {
  for (const [q, id] of [['entrectinib', 'entrectinib-integrated'], ['STARTRK', 'entrectinib-integrated'], ['larotrectinib', 'larotrectinib-integrated'], ['NAVIGATE', 'larotrectinib-integrated']]) {
    assert.ok(T.familyMatchesQuery(T.familyById(D, id), q), q);
  }
  assert.ok(T.familiesToShow(D, busca('NCT02097810'), 'NCT02097810', false).some((f) => f.family_id === 'entrectinib-integrated'));
  for (const [q, u] of [['ROS1', ENT_CARD], ['pâncreas', 'pancreas_9'], ['tireoide', 'tireoide_avancado_8'], ['entrectinibe', 'pancreas_9']]) {
    assert.ok(busca(q).some((s) => s.uid === u), `${q} → ${u}`);
  }
  const esperado = { [ENT_CARD]: ['nsclc_alvo', 'pulmao'], pancreas_9: ['pancreas', 'pancreas'], tireoide_avancado_8: ['tireoide_avancado', 'tireoide'] };
  for (const [u, [cat, tumor]] of Object.entries(esperado)) {
    assert.equal(card(u).category_id, cat, u);
    assert.deepEqual(js(T.tumorTypes.filter((t) => t.match(card(u))).map((t) => t.id)), [tumor], u);
  }
  assert.deepEqual(js(T.familyMembers(D, ENT).map((s) => s.uid)), [ENT_CARD, 'pancreas_9']);
});

test('análise integrada: contagem 1/N análises, badge, seção de estudos e rótulos PT/EN', () => {
  const corpo = HTML_DB.match(/famCount\(f\) \{([\s\S]*?)\n    \},/)[1];
  const vm2 = { tt: (k, f) => (k.endsWith('One') ? 'U:' : 'P:') + f, famKind: (f) => T.familyUnitKind(D, f), familyMembers: (f) => T.familyMembers(D, f) };
  const famCount = new Function('f', corpo).bind(vm2);
  assert.equal(famCount(ENT), '2 P:análises no Database');
  assert.equal(famCount(LARO), '1 U:análise no Database');
  assert.equal(DICT['pt-br'].db.famType_integrated_analysis, 'Análise integrada');
  assert.equal(DICT.en.db.famType_integrated_analysis, 'Integrated analysis');
  assert.equal(DICT['pt-br'].db.famContributing, 'Estudos contribuidores');
  assert.equal(DICT.en.db.famContributing, 'Contributing studies');
  assert.equal(DICT['pt-br'].db.famPartOf_integrated_analysis, 'Parte da análise integrada de');
  assert.equal(DICT.en.db.famPartOf_integrated_analysis, 'Part of the integrated analysis of');
  assert.equal(DICT.en.db.famAnalysesOne, 'analysis in the Database');
  assert.match(HTML_DB, /tt\('db\.famContributing'/);
  // análise integrada não é protocolo: rótulos próprios, sem "protocolo"/"coorte"
  for (const k of ['famArm', 'famTreatment', 'famOpenProtocol', 'famSeeOthers', 'famNote']) {
    for (const l of ['pt-br', 'en']) assert.doesNotMatch(DICT[l].db[`${k}_integrated_analysis`], /protocol|coorte|cohort/i, `${l} ${k}`);
  }
  assert.match(HTML_DB, /a\.arm \|\| a\.cohort \|\| a\.randomization \|\| a\.analysis \|\| a\.comparison/);
});

test('análise integrada: nome do fármaco localizado (PT/EN) por famText, sem hardcode no componente', () => {
  assert.equal(ENT.family_name, 'Entrectinibe');
  assert.equal(LARO.family_name, 'Larotrectinibe');
  assert.equal(ENT.i18n.en.family_name, 'Entrectinib');
  assert.equal(LARO.i18n.en.family_name, 'Larotrectinib');
  const corpo = HTML_DB.match(/famText\(f, campo\) \{([\s\S]*?)\n    \},/)[1];
  for (const [lang, ent, laro] of [['pt-br', 'Entrectinibe', 'Larotrectinibe'], ['en', 'Entrectinib', 'Larotrectinib']]) {
    const famText = new Function('f', 'campo', `const window = { getLang: () => '${lang}' }; ${corpo}`).bind({ langTick: 0 });
    assert.equal(famText(ENT, 'family_name'), ent, lang);
    assert.equal(famText(LARO, 'family_name'), laro, lang);
    assert.equal(famText(STAMPEDE, 'family_name'), 'STAMPEDE', 'sem i18n: valor base');
  }
  // título, chip, callout, modal e nota de sobreposição usam famText
  for (const trecho of ["famText(f, 'family_name')", "famText(familyOf(selectedStudy), 'family_name')", "famText(selectedFamily, 'family_name')", "famText(selectedFamily, 'overlap_note')"]) {
    assert.ok(HTML_DB.includes(trecho), trecho);
  }
  assert.ok(T.familyMatchesQuery(ENT, 'Entrectinib') && T.familyMatchesQuery(LARO, 'Larotrectinib'));
});

test('análise integrada: nota de sobreposição do entrectinibe descreve populações distintas (PT/EN)', () => {
  assert.match(ENT.overlap_note, /populações distintas por tipo tumoral e alteração molecular/);
  assert.match(ENT.overlap_note, /podem reutilizar pacientes desses mesmos estudos/);
  assert.doesNotMatch(ENT.overlap_note, /não informam a sobreposição individual/);
  assert.match(ENT.i18n.en.overlap_note, /distinct populations defined by tumor type and molecular alteration/);
  assert.match(LARO.overlap_note, /grau exato de sobreposição com essas publicações não é quantificado na fonte/);
  assert.match(LARO.i18n.en.overlap_note, /not quantified in the source/);
});
reprova('i18n da família com resultado clínico', (d) => {
  d.families.find((f) => f.family_id === 'entrectinib-integrated').i18n.en.overlap_note += ' ORR 77%.';
}, /i18n\.en\.overlap_note traz resultado clínico/);
reprova('i18n da família com campo não estrutural', (d) => {
  d.families.find((f) => f.family_id === 'entrectinib-integrated').i18n.en.primario = 'x';
}, /não é campo estrutural traduzível/);

// ── fatorial: PEACE-1 ──────────────────────────────────────────────────────
/* Fatorial 2×2 ≠ plataforma: dois fatores cruzados (abiraterona × radioterapia), quatro células,
 * e cada fator é uma pergunta randomizada com publicação própria → membros `comparison`. */
const PEACE = T.familyById(D, 'peace-1');
const PEACE_MEMBROS = ['prostata_contexto_5', 'peace-1-radioterapia-prostata-mhspc-de-novo'];

test('fatorial PEACE-1: dois fatores, quatro células, duas comparações, sem "plataforma"', () => {
  assert.ok(PEACE);
  assert.equal(PEACE.design_type, 'factorial');
  assert.deepEqual(js(PEACE.registry_ids), ['NCT01957436']);
  assert.deepEqual(js(PEACE.factors.map((f) => [f.factor, f.levels])), [['Abiraterona', ['Sem', 'Com']], ['Radioterapia da próstata', ['Sem', 'Com']]]);
  assert.deepEqual(js(PEACE.cells.map((c) => c.label)), ['SOC', 'SOC + RT', 'SOC + abiraterona', 'SOC + RT + abiraterona']);
  assert.equal(new Set(PEACE.cells.map((c) => c.levels.join('|'))).size, 4);
  assert.deepEqual(js(PEACE.comparisons.map((c) => c.card_uids[0])), PEACE_MEMBROS);
  assert.deepEqual(js(PEACE.member_uids), PEACE_MEMBROS);
  for (const k of ['arms', 'cohorts', 'randomizations', 'analyses']) assert.equal(PEACE[k], undefined, k);
  assert.match(PEACE.design_summary, /fatorial 2×2/);
  assert.match(PEACE.design_summary, /não é um ensaio plataforma/);
  assert.doesNotMatch(JSON.stringify(PEACE).replace(/não é um ensaio plataforma|this is not a platform trial/g, ''), /plataforma|platform/i);
  assert.doesNotMatch(JSON.stringify([PEACE.factors, PEACE.cells, PEACE.comparisons]), /\bHR\b(?!-)|\d+(?:[.,]\d+)? ?%|mediana|IC ?95/i, 'sem resultado clínico');
  assert.equal(T.familyUnitKind(D, PEACE), 'comparison');
});

test('fatorial PEACE-1: dois cards independentes como comparações, NCT compartilhado legítimo', () => {
  for (const u of PEACE_MEMBROS) {
    assert.equal(card(u).family_id, 'peace-1');
    assert.equal(card(u).family_relation, 'comparison');
    assert.equal(card(u).nct, 'NCT01957436');
    assert.equal(T.familyForHash(D, u), null, `#${u} abre o card`);
  }
  assert.deepEqual(js(PEACE_MEMBROS.map((u) => card(u).comparison_label)), ['Adição de abiraterona', 'Adição de radioterapia da próstata']);
  assert.deepEqual(js(T.familyMembers(D, PEACE).map((s) => s.uid)), PEACE_MEMBROS);
  const r = validarCom(() => {});
  assert.equal(r.code, 0, r.saida);
  assert.doesNotMatch(r.saida, /NCT NCT01957436 também está/);
  assert.match(validarCom((d) => { delete d.studies.find((s) => s.uid === 'prostata_contexto_5').family_id; }).saida, /NCT NCT01957436 também está/, 'detector continua ativo');
});
reprova('fatorial sem fatores', (d) => { delete d.families.find((f) => f.family_id === 'peace-1').factors; }, /≥2 fatores/);
reprova('fatorial com célula faltando', (d) => { d.families.find((f) => f.family_id === 'peace-1').cells.pop(); }, /4 combinações de níveis, mas 3 células/);
reprova('fatorial com uma só comparação', (d) => {
  const f = d.families.find((x) => x.family_id === 'peace-1'); f.comparisons.pop(); f.member_uids.pop();
  delete d.studies.find((s) => s.uid === 'peace-1-radioterapia-prostata-mhspc-de-novo').family_id;
}, /≥2 comparações/);
reprova('membro de fatorial com relação de coorte', (d) => {
  d.studies.find((s) => s.uid === 'prostata_contexto_5').family_relation = 'cohort';
}, /family_relation "comparison"/);
reprova('resultado clínico numa célula do fatorial', (d) => {
  d.families.find((f) => f.family_id === 'peace-1').cells[0].label += ' (HR 0,54)';
}, /fatores\/células trazem resultado clínico/);

test('fatorial PEACE-1: badge 2×2 calculado, contagem 1/N comparações e rótulos PT/EN', () => {
  const corpo = HTML_DB.match(/famCount\(f\) \{([\s\S]*?)\n    \},/)[1];
  const vm2 = { tt: (k, f) => (k.endsWith('One') ? 'U:' : 'P:') + f, famKind: (f) => T.familyUnitKind(D, f), familyMembers: (f) => T.familyMembers(D, f) };
  assert.equal(new Function('f', corpo).bind(vm2)(PEACE), '2 P:comparações no Database');
  const f1 = { ...js(PEACE), family_id: 'z', comparisons: [PEACE.comparisons[0]] };
  const d1 = { families: [f1], studies: [{ ...js(card('prostata_contexto_5')), family_id: 'z' }] };
  const vm3 = { ...vm2, famKind: (f) => T.familyUnitKind(d1, f), familyMembers: (f) => T.familyMembers(d1, f) };
  assert.equal(new Function('f', corpo).bind(vm3)(f1), '1 U:comparação no Database');
  const tipo = HTML_DB.match(/famType\(f\) \{([\s\S]*?)\n    \},/)[1];
  for (const [l, esperado] of [['pt-br', 'Fatorial 2×2'], ['en', '2×2 factorial']]) {
    const famType = new Function('f', tipo).bind({ tt: (k, fb) => DICT[l].db[k.replace('db.', '')] || fb });
    assert.equal(famType(PEACE), esperado, l);
  }
  const partes = (l) => DICT[l].db.famPartOf_factorial.replace('{name}', 'PEACE-1');
  assert.equal(partes('pt-br'), 'Parte do estudo fatorial PEACE-1');
  assert.equal(partes('en'), 'Part of the PEACE-1 factorial trial');
  assert.equal(DICT['pt-br'].db.famArmsComparison, 'Comparações representadas');
  assert.equal(DICT.en.db.famArmsComparison, 'Represented comparisons');
  assert.equal(DICT.en.db.famComparisonsNOne, 'comparison in the Database');
  assert.match(HTML_DB, /famPartOfParts\(familyOf\(selectedStudy\)\)\[1\]/);
  assert.match(HTML_DB, /famCell\(selectedFamily, i1, i2\)/);
  // toda linha de família tem chave/rótulo no x-for (chave indefinida quebra a tabela do modal)
  for (const tipo of ['arm', 'cohort', 'randomization', 'analysis', 'comparison']) {
    assert.match(HTML_DB, new RegExp(`:key="a\\.arm(?: \\|\\| a\\.\\w+)*?\\b(?<=a\\.${tipo})\\b`), tipo);
    assert.match(HTML_DB, new RegExp(`x-text="a\\.arm(?: \\|\\| a\\.\\w+)*?\\b(?<=a\\.${tipo})\\b`), tipo);
  }
  assert.deepEqual(js(PEACE.i18n.en.factors.map((f) => f.factor)), ['Abiraterone', 'Prostate radiotherapy']);
});

test('fatorial PEACE-1: busca pelo acrônimo mostra a família; app-data leva a família', () => {
  assert.ok(T.familiesToShow(D, busca('PEACE-1'), 'PEACE-1', false).some((f) => f.family_id === 'peace-1'));
  for (const u of PEACE_MEMBROS) assert.ok(busca('PEACE-1').some((s) => s.uid === u), u);
  const app = JSON.parse(readFileSync(path.join(SITE, 'app-data', 'data.json'), 'utf8'));
  assert.ok(app.families.some((f) => f.family_id === 'peace-1' && f.design_type === 'factorial'));
});

test('callout em PT: fallback de famPartOf por design_type espelha pt-br.js (PT não carrega o dicionário)', () => {
  const m = HTML_DB.match(/const fb = (\{.*?\})\[f\.design_type\]/);
  assert.ok(m, 'mapa de fallback em famPartOf');
  const fb = vm.runInNewContext('(' + m[1] + ')');
  for (const tipo of ['basket', 'multicohort', 'factorial', 'master_protocol', 'integrated_analysis']) {
    assert.equal(fb[tipo], DICT['pt-br'].db['famPartOf_' + tipo], tipo);
  }
});

test('campos textuais da família passam por famText (i18n.en aparece em EN; sem i18n, cai no PT)', () => {
  for (const campo of ['design_summary', 'population']) {
    assert.doesNotMatch(HTML_DB, new RegExp(`x-text="(f|selectedFamily)\\.${campo}"`), campo);
    assert.match(HTML_DB, new RegExp(`famText\\(selectedFamily, '${campo}'\\)`), campo);
  }
  assert.match(HTML_DB, /famText\(f, 'design_summary'\)/);
});

// publicação de linha da família: PMID ou, sem PMID (abstract de congresso), DOI válido
reprova('linha com publicação sem PMID nem DOI', (d) => {
  d.families.find((f) => f.family_id === 'rampart').arms[1].publication = { label: 'abstract' };
}, /publicação sem PMID nem DOI válido/);
reprova('linha com PMID malformado', (d) => {
  d.families.find((f) => f.family_id === 'rampart').arms[1].publication = { pmid: 'LBA4511', label: 'abstract' };
}, /PMID inválido/);
