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
    assert.doesNotMatch(JSON.stringify(f), /\bHR\b|IC ?95|mediana/i, f.family_id);
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
  ...[...BLOCOS_FAM.join('\n').matchAll(/famK\([^,]+, '(\w+)'\)/g)].flatMap((m) => [m[1], m[1] + 'Cohort', m[1] + 'Analysis']),
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
  assert.equal(D.studies.length, 507);
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
  assert.equal(D.studies.length, 507);
  assert.equal(D.families.length, 7);
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
  assert.match(r.saida, /NCT NCT01704716 também está/);     // HR-NBL1/SIOPEN, ainda sem família
  assert.match(r.saida, /NCT NCT02568267 também está/);     // NTRK/ROS1, ainda sem família
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
