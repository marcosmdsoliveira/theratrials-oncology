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
 * 4. `pubmed_url` aponta MESMO para o PubMed. Link de editora abre e leva ao
 *    artigo, então ninguém percebe — mas fica fora do `validate_pubmed.mjs`,
 *    que só sabe conferir PMID contra ensaio. Eram 62 assim até 2026-08-05, e
 *    dois deles tinham DOI INEXISTENTE (404 no doi.org). Ver FONTE_NAO_PUBMED.
 *
 * 5. `linha` curta o bastante para o chip.
 *    O campo `aprovacao` saiu do schema em 2026-08-09, e a checagem de formato
 *    saiu junto. A caixa "Aprovação regulatória" tinha deixado de ser
 *    renderizada em 2026-08-05 por repetir em forma pobre o que o
 *    `impacto_reg` já diz em prosa; verificou-se depois que nem o site nem o
 *    app iOS liam o campo, e que os 238 cards com ano em `aprovacao` já
 *    traziam esse mesmo ano no `impacto_reg`, no `limit` ou no `ref` — ou
 *    seja, remover não perdeu informação nenhuma.
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
  // A lista está VAZIA desde 2026-08-09, e as duas dívidas foram quitadas
  // corrigindo o card — não afrouxando a regra:
  //
  // net_gep_18 (SANET): o `resultado_chave` passou a dizer p<0,0001 no braço
  //   extrapancreático, igual ao `primario` e à publicação (Xu N et al.,
  //   Lancet Oncol 2020).
  //
  // neuroblastoma_14 (ANBL1232): o card anunciava como resultado ("OS até 3
  //   anos ~99%") o que o protocolo declara como META, e descrevia uma
  //   desescalada "2-4 ciclos vs 8" que não existe no desenho. Reescrito
  //   contra o NCT02176967 — o ensaio segue ACTIVE_NOT_RECRUITING, com
  //   conclusão primária estimada set/2026 e nenhum resultado depositado, e o
  //   `resultado_chave` agora diz exatamente isso.
};

/* `pubmed_url` que NÃO aponta para o PubMed.
 *
 * Até 2026-08-05 havia 62 assim — 45 nejm.org, 8 thelancet.com, 5 ascopubs,
 * 3 PMC, 1 jnm. O link abria e o leitor chegava ao artigo, então ninguém
 * percebeu; mas o `validate_pubmed.mjs` só sabe conferir PMID contra ensaio, e
 * esses 62 nunca passaram por guard nenhum. Dois deles eram DOI INEXISTENTE
 * (404 no doi.org): DESTINY-Breast06 e NATALEE, com identificador NEJM
 * plausível e artigo que nunca existiu — o mesmo padrão de link alucinado que
 * o §9 do PROJECT_MEMORY diz ter sido corrigido em junho de 2026.
 *
 * Todos foram resolvidos para PMID e confirmados um a um. Como o número é
 * zero, isto pode ser FAIL: link de editora não volta a entrar em silêncio.
 * Para autorizar um, liste o uid aqui com data e motivo — mesmo mecanismo do
 * EXCECOES_SEM_NCT do validate_trials_br.mjs, que o revisor clínico definiu.
 * A lista começa VAZIA de propósito. */
const FONTE_NAO_PUBMED = {
  // 'uid-do-card': { desde: 'AAAA-MM-DD', motivo: 'por que este não tem PMID' },
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

// ── 4. tamanho de linha ───────────────────────────────────────────────────
for (const s of S) {
  /* `aprovacao` saiu do schema em 2026-08-09; se voltar, é campo ressuscitado
   * sem quem o renderize, e o guard avisa em vez de deixar apodrecer de novo. */
  if (s.aprovacao !== undefined) {
    W(s.uid, 'campo `aprovacao` voltou ao dataset — saiu do schema em 2026-08-09 e nada o renderiza');
  }
  if (!vazio(s.linha) && String(s.linha).length > LINHA_MAX) {
    W(s.uid, `linha com ${String(s.linha).length} caracteres (máx ${LINHA_MAX}) — é chip na grade`);
  }
}

// ── 5. pubmed_url tem de ser do PubMed ────────────────────────────────────
let isentosFonte = 0;
for (const s of S) {
  if (vazio(s.pubmed_url)) continue;
  if (/pubmed\.ncbi\.nlm\.nih\.gov/.test(String(s.pubmed_url))) continue;
  if (FONTE_NAO_PUBMED[s.uid]) { isentosFonte++; continue; }
  let host = '(URL inválida)';
  try { host = new URL(String(s.pubmed_url)).hostname; } catch { /* mantém */ }
  F(s.uid, `pubmed_url aponta para ${host}, não para o PubMed — fica fora do validate_pubmed.mjs. Resolva o PMID ou autorize em FONTE_NAO_PUBMED`);
}

/* ── 6. o card é lido sozinho, e sem o autor junto ─────────────────────────
 * Duas coisas que só fazem sentido de dentro da planilha vazavam para a tela
 * na auditoria de 2026-08-05:
 *
 *   • marcação de triagem do autor — "Não-radiofármaco", "N/A para
 *     radiofármaco", "Verificar protocolo específico do estudo". Classifica o
 *     card ou é recado para si mesmo; não informa nada a quem lê.
 *
 *   • referência relativa — "Mesma pré-medicação intensiva", "Mesma
 *     preparação anti-dara". Aponta para o card vizinho na ordem do arquivo,
 *     que o leitor não tem à frente: cada card abre isolado, por busca ou por
 *     link compartilhado.
 *
 * "Não informado" é a saída legítima quando não há o que dizer. */
const RE_NOTA_INTERNA = /não-?radiof[áa]rmaco|\bN\/A para\b|verificar protocolo/i;
const RE_RELATIVA = /^mesm[ao]s?\b/i;
/* Todo campo de prosa que chega à tela, não só os que entram na §7.1: o
 * defeito apareceu em `preparo` e em `tox_interesse`, e não há razão para
 * supor que pare aí. Fora os campos que não são prosa. */
const NAO_PROSA = new Set(['uid', 'nct', 'nct_url', 'pubmed_url', 'category_id', 'category_name',
  'category_short', 'category_color', 'ano_pub', 'status', 'acron', 'ref']);
const PROSA = NUCLEO.filter((c) => !NAO_PROSA.has(c)).concat('takehome', 'resultado_chave', 'titulo_full');
for (const s of S) {
  for (const campo of PROSA) {
    const v = s[campo];
    if (typeof v !== 'string' || vazio(v)) continue;
    /* `radiofarmaco` fica de fora: ali "Não-radiofármaco" é a resposta certa à
     * pergunta do campo, e não uma marcação de triagem em campo errado. */
    const nota = campo === 'radiofarmaco' ? null : v.match(RE_NOTA_INTERNA);
    if (nota) F(s.uid, `${campo} traz marcação interna de triagem, que o leitor vê: "${nota[0]}" — descreva o conteúdo real do campo ou escreva "Não informado"`);
    if (RE_RELATIVA.test(v.trim())) F(s.uid, `${campo} começa com referência relativa ("${v.trim().slice(0, 24)}…") — o card é lido isolado, sem o vizinho à vista`);
  }
}

/* ── 7. tag HTML fora do conjunto que o renderizador aceita ────────────────
 * Desde 2026-08-09 o `annotateAbbr` (glossario.js) reabre <strong>, <em> e
 * <br> depois do escape — sem atributo, conjunto fechado. QUALQUER outra tag
 * continua escapada e chega ao leitor com os sinais à mostra, então entrar no
 * dataset é erro: `<p>`, `<span style=…>`, `<a href=…>` viram lixo visível, e
 * `<script>` ou `<img onerror=…>` seriam tentativa de injeção que o escape
 * neutraliza mas que não tem por que existir aqui.
 *
 * Atributo é barrado inclusive nas três permitidas: `<strong class="x">` não
 * é reaberto pelo renderizador, então também apareceria literal. */
const TAGS_OK = new Set(['strong', '/strong', 'em', '/em', 'br', 'br/']);
const RE_QUALQUER_TAG = /<(\/?[a-z][a-z0-9]*)((?:\s[^>]*)?)\s*(\/?)>/gi;
for (const s of S) {
  for (const [campo, v] of Object.entries(s)) {
    if (typeof v !== 'string' || !v.includes('<')) continue;
    for (const m of v.matchAll(RE_QUALQUER_TAG)) {
      const [inteira, nome, atributos, barraFinal] = m;
      const chave = (nome + (barraFinal || '')).toLowerCase();
      if (TAGS_OK.has(chave) && !atributos.trim()) continue;
      F(s.uid, `${campo} tem tag que o renderizador não aceita e o leitor vê literal: ${inteira} — só <strong>, <em> e <br>, sem atributo`);
    }
  }
}

/* ── 7a. campo cujo template usa x-text não pode carregar tag ──────────────
 * A regra 7 libera <strong>, <em> e <br> porque o `annotateAbbr` os reabre.
 * Isso só vale onde o template chama `annotateAbbr` — nos pontos que ainda
 * usam `x-text` do Alpine, a tag chega ao DOM como texto e o leitor a vê.
 *
 * Regra nascida de erro meu, e a segunda vez que a mesma lacuna me pega: em
 * 2026-08-09 escrevi `<em>Nature Medicine</em>` no `periodo` e `<strong>` no
 * `takehome` do BREAKWATER, o validador aprovou, e o site publicou as tags
 * literais. As três chamadas foram convertidas para `annotateAbbr` em
 * 2026-08-11; esta lista guarda as que ficaram.
 *
 * Ao converter uma chamada no template, tire o campo daqui — a lista é o
 * espelho do que o template ainda não sabe renderizar. */
const X_TEXT = {
  n:            'database.html — modal, campo "N"',
  radiofarmaco: 'database.html — modal, campo "Radiofármaco / Intervenção"',
  cumul:        'database.html — modal, campo "Atividade cumulativa típica"',
  ref:          'database.html — modal, campo "Referência principal"',
  sponsor:      'database.html — modal, linha de cabeçalho',
  titulo_full:  'database.html — modal, subtítulo',
};
const RE_FORMATACAO_TAG = /<\/?(?:strong|em|br)\s*\/?>/i;
for (const s of S) {
  for (const [campo, onde] of Object.entries(X_TEXT)) {
    const t = s[campo];
    if (typeof t !== 'string') continue;
    const m = t.match(RE_FORMATACAO_TAG);
    if (m) F(s.uid, `${campo} tem ${m[0]}, mas é renderizado com x-text (${onde}) — o leitor veria a tag literal. Tire a tag do dado ou converta a chamada para annotateAbbr`);
  }
}

/* ── 7b. entidade HTML escrita à mão no dado ───────────────────────────────
 * O `escHtml` do annotateAbbr escapa o `&` antes de tudo, então `&lt;` vira
 * `&amp;lt;` e o leitor vê a entidade CRUA na tela. Quem escreve o card deve
 * pôr o caractere direto — `<`, `>`, `&` — que o renderizador escapa sozinho.
 *
 * Regra nascida de erro meu: em 2026-08-09 escrevi `&lt; 12 meses` no `incl`
 * do ANBL1232 achando que protegia o sinal de menor, e publiquei "&lt; 12
 * meses" no ar. Os dois casos eram os únicos do dataset inteiro. */
const RE_ENTIDADE = /&(?:lt|gt|amp|nbsp|quot|#\d+);/i;
for (const s of S) {
  for (const [campo, v] of Object.entries(s)) {
    if (typeof v !== 'string') continue;
    const e = v.match(RE_ENTIDADE);
    if (e) F(s.uid, `${campo} tem entidade HTML "${e[0]}", que o leitor vê crua — escreva o caractere direto, o escape é do renderizador`);
  }
}

// ── 8. NOTE — informes que não bloqueiam ──────────────────────────────────

/* O marcador ⚠️ significava "rascunho não revisado pelo revisor clínico" e
 * saiu dos 464 takehome em 2026-08-05, com a aprovação dele — pendência aberta
 * desde junho de 2026. Se voltar a aparecer, é curadoria nova entrando sem
 * revisão, e o NOTE avisa. */
const comTake = S.filter((s) => !vazio(s.takehome));
const comMarcador = comTake.filter((s) => String(s.takehome).includes('⚠️'));
notes.push({
  tipo: 'takehome',
  total: comTake.length,
  detalhe: comMarcador.length
    ? `${comMarcador.length} ainda com o marcador ⚠️ de rascunho não revisado`
    : `nenhum com o marcador ⚠️ — todos revisados`,
  obs: 'o ⚠️ marca rascunho não revisado; sai só com aprovação do revisor clínico (§7.1)',
  uids: comMarcador.map((s) => s.uid),
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
if (isentosFonte) {
  console.error(`\n--- NOTE: ${isentosFonte} card(s) autorizados a citar fonte fora do PubMed ---`);
  for (const [uid, e] of Object.entries(FONTE_NAO_PUBMED)) console.error(`  ${uid} (desde ${e.desde}) — ${e.motivo}`);
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
