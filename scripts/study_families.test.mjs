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
const CHAVES = [...new Set([...BLOCOS_FAM.join('\n').matchAll(/tt\('db\.(\w+)'/g)].map((m) => m[1]))];

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
