#!/usr/bin/env node
/* ============================================================================
 * validate_cards.mjs — guard OFFLINE dos cards do Database (THERA_DATA)
 *
 * Os três validadores existentes conferem LINKS batendo em NCBI e CT.gov: são
 * ~400 chamadas de rede e 4-8 minutos. Nenhum deles olha o que o card DIZ.
 * Este olha, sem tocar a rede — roda em menos de um segundo e por isso vem
 * antes dos outros no CI, como o sync_counts.
 *
 * O que ele guarda, e por que cada regra existe:
 *
 * 1. `resultado_chave` é condensação FIEL do `primario` (regra §7.1 do
 *    PROJECT_MEMORY). Todo número da manchete tem de existir no desfecho.
 *    Em dois níveis, porque nem toda divergência é do mesmo tamanho:
 *      FAIL - o número não existe em NENHUM campo do card. É o padrão de
 *             número inventado: a manchete afirma o que o card não sustenta.
 *      WARN - o número existe em outro campo, mas não no `primario`. A
 *             condensação escorregou para um secundário ou um subgrupo.
 *    Escrevi essa checagem de improviso DUAS VEZES na auditoria de
 *    2026-08-05, e nas duas ela barrou erro meu antes de gravar. Virou este
 *    arquivo para não precisar de uma terceira.
 *
 * 2. Integridade estrutural — `metadata.total_studies` contra
 *    `studies.length`, soma e sincronia dos `categories[].count`, `uid`
 *    duplicado, estudo em categoria não declarada, e `category_name`/`short`/
 *    `color` divergindo do registro da categoria. O gotcha nº 5 do
 *    PROJECT_MEMORY é exatamente a primeira: "metadata.total_studies pode
 *    dessincronizar de studies.length". Nada quebra quando dessincroniza —
 *    o site só passa a mentir o número.
 *
 * 3. Os 40 campos do núcleo estão CONGELADOS (§7). Campo que some não dá
 *    erro em lugar nenhum: o modal simplesmente deixa de renderizar a seção.
 *
 * 4. `aprovacao` no formato travado e `linha` curta o bastante para o chip.
 *
 * ARMADILHA DE NÚMERO, aprendida apanhando duas vezes na mesma noite:
 * comparar dígito por dígito exige normalizar os DOIS lados igual.
 *   - `IC 95%` e `IC95%` são o mesmo intervalo. Um lookbehind de letra
 *     (`(?<![A-Za-z])`) mata o 95 do segundo e não do primeiro, e o guard
 *     acusa divergência onde há só espaço.
 *   - `p53` não contém o número 53. Nem BRCA1, PD-L1, HER2, CD45, 177Lu.
 * A saída é remover os MARCADORES antes de extrair, com o mesmo filtro nos
 * dois lados — não um lookbehind cego. Ver MARCADORES abaixo.
 *
 * Exit 0 se não houver FAIL, senão 1 (trava o CI). WARN nunca trava, salvo
 * --warn-fail. NOTE é só informe.
 * Uso: node scripts/validate_cards.mjs [--json report.json] [--warn-fail]
 * ==========================================================================*/
import path from 'node:path';
import fs from 'node:fs';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DATA = path.join(__dirname, '..', 'assets', 'js', 'data.js');
const args = process.argv.slice(2);
const jsonOut = args.includes('--json') ? args[args.indexOf('--json') + 1] : null;
const warnFail = args.includes('--warn-fail');

/* Exceções conhecidas da regra §7.1, com data e motivo — mesmo mecanismo do
 * KNOWN_GOOD dos validadores de link. Entrada aqui é uma DÍVIDA registrada,
 * não um perdão: cada uma diz o que fazer para poder sair da lista. */
const CONHECIDOS = {
  neuroblastoma_14: {
    desde: '2026-08-05',
    motivo:
      'ANBL1232. O `resultado_chave` diz "(2-4 ciclos vs 8)", que descreve a ' +
      'desescalada, não o desfecho. Os números não aparecem em nenhum outro ' +
      'campo. Para sair da lista: acrescentar o esquema de ciclos ao campo ' +
      '`esquema`, que hoje só diz "Redução de número de ciclos".',
  },
  net_gep_18: {
    desde: '2026-08-05',
    motivo:
      'SANET. O `resultado_chave` diz "p<0,001" para o braço extrapancreático; ' +
      'o `primario` diz "p<0,0001". A manchete subestima a precisão da fonte. ' +
      'Para sair da lista: alinhar os dois com a publicação.',
  },
};

/* Siglas que CONTÊM dígito sem que o dígito seja uma medida. Sem isto, o
 * guard lê o 53 de p53 e o 2 de HER2 como resultado. */
const MARCADORES =
  /\b(p53|tp53|brca ?1\/?2?|brca[12]|pd-?l?-?1|pdl1|her2|her3|cd\d+|ki-?67|g12[cdv]|idh[12]|fgfr[1-4]|ntrk[1-3]|pole|akt1|pik3ca|erbb2|hla-a\*?02|il-?2|ch14\.18|3f8|hu3f8|177lu|225ac|212pb|223ra|161tb|131i|90y|68ga|64cu|67cu|18f|99mtc|124i|111in|213bi|221fr|1\/2|i&t)\b/gi;

const NUCLEO = [
  'estudo', 'acron', 'nct', 'sponsor', 'fase', 'desenho', 'centros', 'periodo',
  'indicacao', 'incl', 'excl', 'estrat', 'basal', 'n', 'molecular', 'biomarc',
  'radiofarmaco', 'esquema', 'cumul', 'comparador', 'estatistica', 'analises',
  'primario', 'secundario', 'subgrupo', 'tox_g3', 'tox_interesse', 'impacto_reg',
  'limit', 'ref', 'category_id', 'preparo', 'nct_url', 'pubmed_url', 'ano_pub',
  'status', 'category_name', 'category_short', 'category_color', 'uid',
];

/* Campos onde um número do `resultado_chave` ainda pode ter origem legítima.
 * Não inclui `ref` nem `titulo_full`: ano de publicação e número de volume
 * não são desfecho. */
const CORPO = [
  'primario', 'secundario', 'subgrupo', 'tox_g3', 'tox_interesse', 'n',
  'esquema', 'desenho', 'basal', 'impacto_reg', 'estatistica', 'cumul',
  'periodo', 'molecular', 'comparador',
];

const APROVACAO_OK = /^(Investigacional|FDA (—|\d{4}[^·]*) · EMA (—|[^·]+) · ANVISA —)$/;
const LINHA_MAX = 80;   // hoje o maior é 63; a folga é para pegar disparada

const vazio = (v) => v === undefined || v === null || String(v).trim() === '' || String(v).trim() === '—';
const norm = (t) => String(t ?? '').toLowerCase().replace(/[·]/g, '.').replace(/[–—−]/g, '-').replace(MARCADORES, ' ');
const numeros = (t) => [...norm(t).matchAll(/\d+(?:[.,]\d+)?/g)].map((m) => m[0].replace(',', '.'));

// ── carregar ──────────────────────────────────────────────────────────────
global.window = {};
require(DATA);
const D = global.window.THERA_DATA;
if (!D || !Array.isArray(D.studies)) {
  console.error('FAIL: window.THERA_DATA.studies não carregou de ' + path.relative(process.cwd(), DATA));
  process.exit(1);
}
const S = D.studies;

const fails = [], warns = [], notes = [];
const F = (uid, m) => fails.push({ uid, m });
const W = (uid, m) => warns.push({ uid, m });

// ── 1. integridade estrutural ─────────────────────────────────────────────
if (D.metadata?.total_studies !== S.length) {
  F('(metadata)', `metadata.total_studies = ${D.metadata?.total_studies} ≠ studies.length = ${S.length}`);
}
if (D.metadata?.total_categories !== D.categories.length) {
  F('(metadata)', `metadata.total_categories = ${D.metadata?.total_categories} ≠ categories.length = ${D.categories.length}`);
}
const soma = D.categories.reduce((n, c) => n + (c.count ?? 0), 0);
if (soma !== S.length) F('(categorias)', `soma de categories[].count = ${soma} ≠ studies.length = ${S.length}`);

const porCat = new Map();
for (const s of S) porCat.set(s.category_id, (porCat.get(s.category_id) ?? 0) + 1);
for (const c of D.categories) {
  const real = porCat.get(c.id) ?? 0;
  if (c.count !== real) F('(categorias)', `${c.id}: count declarado ${c.count} ≠ ${real} estudos`);
}
const vistos = new Set();
for (const s of S) {
  if (vistos.has(s.uid)) F(s.uid, 'uid duplicado');
  vistos.add(s.uid);
}
const decl = new Map(D.categories.map((c) => [c.id, c]));
for (const s of S) {
  const c = decl.get(s.category_id);
  if (!c) { F(s.uid, `category_id "${s.category_id}" não está declarado em categories[]`); continue; }
  if (s.category_name !== c.name) F(s.uid, `category_name "${s.category_name}" ≠ "${c.name}" da categoria`);
  if (s.category_short !== c.short) F(s.uid, `category_short "${s.category_short}" ≠ "${c.short}"`);
  if (s.category_color !== c.color) F(s.uid, `category_color "${s.category_color}" ≠ "${c.color}"`);
}

// ── 2. schema núcleo congelado ────────────────────────────────────────────
for (const s of S) {
  const faltando = NUCLEO.filter((f) => !(f in s));
  if (faltando.length) F(s.uid, `campo(s) do núcleo ausente(s): ${faltando.join(', ')}`);
}

// ── 3. §7.1 — resultado_chave é condensação fiel do primario ──────────────
let checados = 0, isentos = 0;
for (const s of S) {
  if (vazio(s.resultado_chave)) continue;
  checados++;
  const noPrimario = new Set(numeros(s.primario));
  const orfaos = [...new Set(numeros(s.resultado_chave))].filter((n) => !noPrimario.has(n));
  if (!orfaos.length) continue;

  const noCard = new Set(CORPO.flatMap((c) => numeros(s[c])));
  const inventados = orfaos.filter((n) => !noCard.has(n));
  if (CONHECIDOS[s.uid]) { isentos++; continue; }
  if (inventados.length) {
    F(s.uid, `resultado_chave tem número que não existe em NENHUM campo do card: ${inventados.join(', ')}`);
  } else {
    W(s.uid, `resultado_chave tem número fora do primario (existe em outro campo): ${orfaos.join(', ')}`);
  }
}

// ── 4. formato de aprovacao e tamanho de linha ────────────────────────────
for (const s of S) {
  if (!vazio(s.aprovacao) && !APROVACAO_OK.test(String(s.aprovacao))) {
    W(s.uid, `aprovacao fora do formato travado: "${s.aprovacao}"`);
  }
  if (!vazio(s.linha) && String(s.linha).length > LINHA_MAX) {
    W(s.uid, `linha com ${String(s.linha).length} caracteres (máx ${LINHA_MAX}) — é chip na grade`);
  }
}

// ── 5. NOTE — informes que não bloqueiam ──────────────────────────────────
const foraPubmed = S.filter((s) => !vazio(s.pubmed_url) && !/pubmed\.ncbi\.nlm\.nih\.gov/.test(String(s.pubmed_url)));
if (foraPubmed.length) {
  const dominios = {};
  for (const s of foraPubmed) {
    let h = '(inválido)';
    try { h = new URL(String(s.pubmed_url)).hostname; } catch { /* mantém inválido */ }
    dominios[h] = (dominios[h] ?? 0) + 1;
  }
  notes.push({
    tipo: 'pubmed_url fora do PubMed',
    total: foraPubmed.length,
    detalhe: Object.entries(dominios).sort((a, b) => b[1] - a[1]).map(([h, n]) => `${n} ${h}`).join(' · '),
    obs: 'o link funciona para o leitor, mas o validate_pubmed.mjs não consegue conferi-lo contra o ensaio',
    uids: foraPubmed.map((s) => s.uid),
  });
}
const comTake = S.filter((s) => !vazio(s.takehome));
notes.push({
  tipo: 'takehome',
  total: comTake.length,
  detalhe: `${comTake.filter((s) => String(s.takehome).includes('⚠️')).length} com ⚠️ (rascunho não revisado) · ${comTake.filter((s) => !String(s.takehome).includes('⚠️')).length} aprovados`,
  obs: 'o ⚠️ sai só após aprovação do revisor clínico (§7.1)',
});
notes.push({
  tipo: 'linha',
  total: S.filter((s) => !vazio(s.linha)).length,
  detalhe: `${new Set(S.filter((s) => !vazio(s.linha)).map((s) => s.linha)).size} valores distintos`,
  obs: 'campo de texto livre, sem vocabulário controlado — só o comprimento é checado',
});

// ── saída ─────────────────────────────────────────────────────────────────
console.error(`Cards: ${S.length} · categorias: ${D.categories.length} · resultado_chave checados: ${checados}`);
for (const n of notes) console.error(`\n--- NOTE: ${n.tipo} (${n.total}) ---\n  ${n.detalhe}\n  ${n.obs}`);
if (isentos) {
  console.error(`\n--- NOTE: ${isentos} card(s) isentos da §7.1 por CONHECIDOS ---`);
  for (const [uid, e] of Object.entries(CONHECIDOS)) console.error(`  ${uid} (desde ${e.desde}) — ${e.motivo}`);
}
if (warns.length) {
  console.error(`\n--- WARN (revisar) ---`);
  for (const w of warns) console.error(`  ${w.uid} | ${w.m}`);
}
if (fails.length) {
  console.error(`\n--- FAIL (bloqueia) ---`);
  for (const f of fails) console.error(`  ${f.uid} | ${f.m}`);
}
console.error(`\nRESULT  OK=${S.length - fails.length - warns.length}  WARN=${warns.length}  FAIL=${fails.length}  (de ${S.length} cards)`);

if (jsonOut) fs.writeFileSync(jsonOut, JSON.stringify({ fails, warns, notes, conhecidos: CONHECIDOS }, null, 1));
process.exit((fails.length + (warnFail ? warns.length : 0)) ? 1 : 0);
