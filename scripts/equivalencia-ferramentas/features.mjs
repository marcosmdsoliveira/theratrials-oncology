// Testes das funcionalidades NOVAS do acesso rápido. Uso:
//   node features.mjs <dir-do-site> <native-guards.js> <pasta-de-screenshots>
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import puppeteer from 'puppeteer-core';

// Registro de service worker neutralizado antes de qualquer script da página:
// sem Capacitor o pwa-install.js tentaria registrar (o que o app real nunca faz).
// Promessa que nunca resolve = nenhum SW, nenhum erro, nenhum .then disparado.
const SEM_SW = () => { if (window.ServiceWorkerContainer)
  ServiceWorkerContainer.prototype.register = function () { return new Promise(() => {}); }; };


const ROOT = path.resolve(process.argv[2]);
const [, , , NATIVE_GUARDS, SHOTS] = process.argv;
fs.mkdirSync(SHOTS, { recursive: true });
const CHROME = process.env.CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const TYPES = { '.html':'text/html; charset=utf-8', '.js':'text/javascript; charset=utf-8', '.css':'text/css',
  '.json':'application/json', '.png':'image/png', '.svg':'image/svg+xml', '.webp':'image/webp' };

// Modo "app": injeta o native-guards.js REAL no <head>, como no bundle iOS.
let appMode = false;
const server = http.createServer((req, res) => {
  const p = decodeURIComponent(new URL(req.url, 'http://x').pathname);
  if (p === '/__native-guards.js') { res.writeHead(200, { 'content-type': TYPES['.js'] }); return res.end(fs.readFileSync(NATIVE_GUARDS)); }
  // Nunca servir o service worker: sem window.Capacitor, o pwa-install.js o
  // registraria (o que NUNCA ocorre dentro do app), e SW se instalando no meio
  // da bateria faz o Puppeteer perder a sessão do navegador.
  if (p === '/sw.js') { res.writeHead(404); return res.end(); }
  const f = path.join(ROOT, p === '/' ? 'index.html' : p);
  if (!fs.existsSync(f) || fs.statSync(f).isDirectory()) { res.writeHead(404); return res.end(); }
  let body = fs.readFileSync(f);
  if (appMode && p === '/ferramentas.html')
    body = Buffer.from(body.toString().replace('<head>', '<head>\n<script src="/__native-guards.js"></script>'));
  res.writeHead(200, { 'content-type': TYPES[path.extname(f)] || 'application/octet-stream', 'cache-control': 'no-store' });
  res.end(body);
});
await new Promise(r => server.listen(0, '127.0.0.1', r));
const BASE = `http://127.0.0.1:${server.address().port}`;
const browser = await puppeteer.launch({ executablePath: CHROME, headless: 'new' });

let falhas = 0;
const ok = (c, msg) => { console.log(`${c ? '  ✓' : '  ✗'} ${msg}`); if (!c) falhas++; };

async function page(opts = {}) {
  const ctx = await browser.createBrowserContext();
  const pg = await ctx.newPage();
  await pg.setViewport(opts.viewport || { width: 1280, height: 900 });
  if (opts.mobile) { await pg.setUserAgent('Mozilla/5.0 (iPhone; CPU iPhone OS 26_0 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148'); }
  await pg.setBypassServiceWorker(true);
  await pg.evaluateOnNewDocument(SEM_SW);
  await pg.setRequestInterception(true);
  pg.on('request', r => { const u = r.url();
    if (u.includes('cloud.umami.is') || u.includes('fonts.g')) return r.abort(); r.continue(); });
  const errs = [];
  pg.on('pageerror', e => errs.push(e.message));
  pg.on('console', m => { if (m.type() === 'error' && !/ERR_FAILED/.test(m.text())) errs.push(m.text()); });
  if (opts.capacitor) await pg.evaluateOnNewDocument(() => { window.Capacitor = { isNativePlatform: () => true }; });
  return { pg, errs, ctx };
}
const openDialog = (pg) => pg.evaluate(() => {
  const d = [...document.querySelectorAll('dialog')].find(x => x.open);
  return d ? { id: d.id, title: (d.querySelector('[id$="-modal-title"]') || {}).textContent } : null;
});
const hash = (pg) => pg.evaluate(() => location.hash);
async function search(pg, q) {
  await pg.evaluate(() => { const i = document.getElementById('ftb-q'); i.value = ''; i.dispatchEvent(new Event('input')); i.focus(); });
  if (q) await pg.type('#ftb-q', q);
  return pg.evaluate(() => [...document.querySelectorAll('#ftb-panel .ftb-opt')].map(o => o.querySelector('.ftb-t').textContent));
}
const closeAll = (pg) => pg.evaluate(() => document.querySelectorAll('dialog[open]').forEach(d => d.close()));

// ═══ 1. busca ═══════════════════════════════════════════════════════════════
console.log('== busca ==');
{
  const { pg, errs, ctx } = await page();
  await pg.goto(`${BASE}/ferramentas.html`, { waitUntil: 'networkidle0' });
  const casos = [
    ['deauv', 'Deauville Score (5-PS)'],
    ['recist', 'RECIST 1.1'],
    ['ckd', 'CKD-EPI 2021'],
    ['tfg', 'CKD-EPI 2021'],                         // sinônimo em português
    ['figado child', 'Child-Pugh Score'],            // sem acento + duas palavras
    ['fígado child', 'Child-Pugh Score'],            // com acento
    ['tnm prostata', 'Próstata'],
    ['ki67', 'Ki-67 Proliferation Index'],           // sigla colada
    ['cockcroft', 'Cockcroft-Gault'],
    ['lutathera', 'Krenning Score (clássico) e Modified Krenning'],
    ['toxicidade renal', 'Renal'],
    ['linfoma', null],
  ];
  for (const [q, esperado] of casos) {
    const r = await search(pg, q);
    if (esperado) ok(r[0] === esperado, `"${q}" → 1º resultado "${r[0]}"${r[0] === esperado ? '' : ` (esperado "${esperado}")`}`);
    else ok(r.some(t => /Deauville/.test(t)) && r.some(t => /Lugano/.test(t)), `"${q}" → inclui Deauville e Lugano (${r.length} resultados)`);
  }
  const tp = await search(pg, 'theranostics psma');
  ok(['PROMISE v2 / miTNM','PSMA-RADS v2.0','RECIP 1.0'].every(t => tp.slice(0,4).includes(t)),
     `"theranostics psma" (finalidade em inglês) → PROMISE, PSMA-RADS e RECIP entre os 4 primeiros (${tp.slice(0,4).join(', ')})`);
  const vazio = await search(pg, 'xyzzy inexistente');
  ok(vazio.length === 0 && await pg.$eval('#ftb-panel', p => /Nenhuma ferramenta/.test(p.textContent)), 'termo inexistente → mensagem de vazio, sem erro');

  // Enter abre a ferramenta pelo caminho original
  await search(pg, 'deauv');
  await pg.keyboard.press('Enter');
  await new Promise(r => setTimeout(r, 150));
  const d = await openDialog(pg);
  ok(d && d.id === 'crit-modal' && d.title === 'Deauville Score (5-PS)', `Enter abre o modal certo (${d && d.title})`);
  ok(await hash(pg) === '#deauville', `URL passa a ser #deauville (${await hash(pg)})`);
  await closeAll(pg);
  await pg.waitForFunction(() => location.hash === '#petct', { timeout: 1500 }).catch(() => {});
  ok(await hash(pg) === '#petct', `ao fechar, URL volta ao grupo #petct (${await hash(pg)})`);

  // Estado vazio = índice dos 12 grupos, com contagem correta
  await search(pg, '');
  const grupos = await pg.evaluate(() => [...document.querySelectorAll('#ftb-panel .ftb-opt')].map(o =>
    [o.querySelector('.ftb-t').textContent, (o.querySelector('.ftb-tag') || {}).textContent]));
  ok(grupos.length === 12, `campo vazio mostra os 12 grupos (${grupos.length})`);
  const renal = grupos.find(g => /renal/i.test(g[0]));
  ok(renal && renal[1] === '3 ferramentas', `grupo Função renal conta as 3 subcalculadoras ("${renal && renal[1]}")`);

  // Teclado
  await pg.evaluate(() => { document.activeElement.blur(); window.scrollTo(0, 3000); });
  await pg.keyboard.press('/');
  ok(await pg.evaluate(() => document.activeElement.id) === 'ftb-q', '"/" foca a busca de qualquer ponto da página');
  await pg.keyboard.press('Escape');
  ok(await pg.$eval('#ftb-panel', p => p.hidden), 'Esc fecha o painel');
  await pg.evaluate(() => document.activeElement.blur());
  await pg.keyboard.down('Control'); await pg.keyboard.press('k'); await pg.keyboard.up('Control');
  ok(await pg.evaluate(() => document.activeElement.id) === 'ftb-q', 'Ctrl+K foca a busca');
  await search(pg, 'meld');
  await pg.keyboard.press('ArrowDown'); await pg.keyboard.press('ArrowUp');
  ok(await pg.evaluate(() => document.getElementById('ftb-q').getAttribute('aria-activedescendant')) === 'ftb-opt-0', 'setas movem a seleção (aria-activedescendant)');

  // "/" dentro de um campo de calculadora NÃO pode ser sequestrado
  await pg.evaluate(() => { document.querySelectorAll('dialog[open]').forEach(d=>d.close()); document.getElementById('renal-age').focus(); });
  await pg.keyboard.press('/');
  ok(await pg.evaluate(() => document.activeElement.id) === 'renal-age', '"/" digitado dentro de um campo não rouba o foco');

  ok(errs.length === 0, `nenhum erro de página${errs.length ? ': ' + errs.join(' | ') : ''}`);
  await ctx.close();
}

// ═══ 2. chips ═══════════════════════════════════════════════════════════════
console.log('\n== filtros por finalidade ==');
{
  const { pg, errs, ctx } = await page();
  await pg.goto(`${BASE}/ferramentas.html`, { waitUntil: 'networkidle0' });
  const contagem = {};
  const reset = () => pg.evaluate(() => { const c = document.querySelector('.ftb-clear'); if (!c.hidden) c.click();
    document.getElementById('ftb-q').dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true })); });
  for (const c of ['est','resp','pet','tera','calc','tox','perf','renal','fig','pat']) {
    await reset();
    await pg.click(`#ftb-chips .ftb-chip[data-chip="${c}"]`);
    contagem[c] = await pg.evaluate(() => [...document.querySelectorAll('#ftb-panel .ftb-opt')].map(o => o.querySelector('.ftb-t').textContent));
  }
  await reset();
  console.log('    ' + Object.entries(contagem).map(([k, v]) => `${k}=${v.length}`).join('  '));
  ok(contagem.calc.length === 8 && ['CKD-EPI 2021','Cockcroft-Gault','MDRD','ALBI Grade','MELD Score','Child-Pugh Score'].every(t => contagem.calc.includes(t)),
     `Calculadoras: as 8 interativas (${contagem.calc.join(', ')})`);
  ok(['CKD-EPI 2021','Cockcroft-Gault','MDRD','Renal'].every(t => contagem.renal.includes(t)), `Função renal: CKD-EPI, CG, MDRD e CTCAE renal`);
  ok(contagem.tox.length === 10, `Toxicidade: 9 categorias CTCAE + NCI-CTCAE (${contagem.tox.length})`);
  ok(contagem.perf.every(t => /ECOG|Karnofsky/.test(t)) && contagem.perf.length === 2, `Performance: só ECOG e Karnofsky (Charlson fica fora, por ser comorbidade)`);
  ok(contagem.est.length >= 15, `Estadiamento inclui os 15 TNM (${contagem.est.length})`);
  // chip + texto = E lógico
  await pg.click('#ftb-chips .ftb-chip[data-chip="resp"]');
  await pg.type('#ftb-q', 'fdg');
  const combo = await pg.evaluate(() => [...document.querySelectorAll('#ftb-panel .ftb-opt')].map(o => o.querySelector('.ftb-t').textContent));
  ok(combo.length > 0 && combo.every(t => /PERCIST|EORTC|Deauville|Lugano|PERCIMT|imPERCIST/i.test(t)), `Resposta + "fdg" → só critérios metabólicos (${combo.join(', ')})`);
  ok(errs.length === 0, `nenhum erro de página${errs.length ? ': ' + errs.join(' | ') : ''}`);
  await ctx.close();
}

// ═══ 3. link direto para TODAS as ferramentas ═══════════════════════════════
console.log('\n== links diretos ==');
{
  const { pg, errs, ctx } = await page();
  await pg.goto(`${BASE}/ferramentas.html`, { waitUntil: 'networkidle0' });
  const alvos = await pg.evaluate(() => [...document.querySelectorAll('button[onclick^="open"]')].map(b => {
    const m = /(openTNM|openCTCAE|openCrit)\('([^']+)'\)/.exec(b.getAttribute('onclick'));
    const slug = ({ openTNM: 'ajcc-', openCTCAE: 'ctcae-', openCrit: '' })[m[1]] + m[2];
    return { slug, fn: m[1], card: b.querySelector('.tnm-card-title').textContent.trim() };
  }));
  await ctx.close();
  let certos = 0; const erradas = [];
  for (const a of alvos) {
    const { pg, ctx } = await page();
    await pg.goto(`${BASE}/ferramentas.html#${a.slug}`, { waitUntil: 'networkidle0' });
    const d = await openDialog(pg);
    const bate = d && (d.title === a.card || (a.fn === 'openCTCAE' && d.id === 'ctcae-modal' && d.title.startsWith('CTCAE v6.0 · ' + a.card)) || (a.fn === 'openTNM' && d.id === 'tnm-modal'));
    if (bate) certos++; else erradas.push(`${a.slug}→${d ? d.title : 'nada'}`);
    await ctx.close();
  }
  ok(certos === alvos.length, `${certos}/${alvos.length} links #slug abrem o modal certo ao carregar a página${erradas.length ? ' — ' + erradas.join(', ') : ''}`);

  const { pg: p2, errs: e2, ctx: c2 } = await page();
  for (const [slug, id] of [['ckd-epi','ckdepi-val'], ['cockcroft-gault','cg-val'], ['mdrd','mdrd-val']]) {
    await p2.goto(`${BASE}/ferramentas.html#${slug}`, { waitUntil: 'networkidle0' });
    await new Promise(r => setTimeout(r, 900));
    const r = await p2.evaluate((id) => {
      const renal = document.getElementById('renal').getBoundingClientRect();
      const card = document.getElementById(id).parentElement.parentElement;
      return { top: Math.round(renal.top), flash: card.classList.contains('ftb-flash'), foco: document.activeElement.id };
    }, id);
    ok(r.top >= 0 && r.top < 260 && r.flash, `#${slug} → rola até Função renal (topo em ${r.top}px) e destaca o card`);
  }
  await p2.goto(`${BASE}/ferramentas.html#nao-existe`, { waitUntil: 'networkidle0' });
  ok(!(await openDialog(p2)), '#nao-existe → não abre nada e não quebra');
  await p2.goto(`${BASE}/ferramentas.html#dose-calc`, { waitUntil: 'networkidle0' });
  await new Promise(r => setTimeout(r, 300));
  ok(await p2.evaluate(() => Math.round(document.getElementById('dose-calc').getBoundingClientRect().top)) < 200, '#dose-calc (âncora nativa) continua funcionando');

  // clique MANUAL num card também gera URL própria
  await p2.goto(`${BASE}/ferramentas.html`, { waitUntil: 'networkidle0' });
  await p2.click(`button[onclick="openCrit('meld')"]`);
  ok(await hash(p2) === '#meld', `clique manual no card também atualiza a URL (${await hash(p2)})`);
  ok(e2.length === 0, `nenhum erro de página${e2.length ? ': ' + e2.join(' | ') : ''}`);
  await c2.close();
}

// ═══ 4. mobile ══════════════════════════════════════════════════════════════
console.log('\n== mobile (390×844, toque) ==');
{
  const { pg, errs, ctx } = await page({ viewport: { width: 390, height: 844, isMobile: true, hasTouch: true, deviceScaleFactor: 2 }, mobile: true });
  await pg.goto(`${BASE}/ferramentas.html`, { waitUntil: 'networkidle0' });
  const r = await pg.evaluate(() => ({
    // clientWidth, não innerWidth: com conteúdo largo demais o Chrome mobile
    // estica a viewport de layout e innerWidth acompanha (foi assim que o teste
    // anterior deu "0px" com a página em 567px).
    overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
    ftbEstica: [...document.querySelectorAll('.ftb, .ftb-bar, .ftb-chips')].some(e => e.getBoundingClientRect().right > document.documentElement.clientWidth + 1),
    chipsWrap: getComputedStyle(document.getElementById('ftb-chips')).flexWrap,
    kbd: getComputedStyle(document.querySelector('.ftb-kbd')).display,
    fonte: getComputedStyle(document.getElementById('ftb-q')).fontSize,
  }));
  ok(!r.ftbEstica, 'barra e chips não esticam a página');
  ok(r.overflow <= 0, `largura da página = largura da tela (excesso ${r.overflow}px)`);
  ok(r.chipsWrap === 'nowrap', 'chips numa linha rolável, sem quebrar');
  ok(r.kbd === 'none', 'atalho "/" escondido em tela de toque');
  ok(parseFloat(r.fonte) >= 16, `campo com ${r.fonte} — evita o zoom automático do iOS ao focar`);
  await pg.screenshot({ path: `${SHOTS}/mobile-topo.png` });
  await pg.evaluate(() => window.scrollTo(0, 4000));
  await new Promise(r => setTimeout(r, 250));
  ok(await pg.evaluate(() => document.getElementById('ftb').classList.contains('is-stuck')), 'barra marca is-stuck ao grudar no topo');
  await pg.screenshot({ path: `${SHOTS}/mobile-grudada.png` });
  const sticky = await pg.evaluate(() => {
    const b = document.querySelector('.ftb-bar').getBoundingClientRect();
    const h = document.querySelector('.site-header').getBoundingClientRect();
    return { barTop: Math.round(b.top), headerBottom: Math.round(h.bottom), visivel: b.top >= 0 && b.bottom < innerHeight };
  });
  ok(sticky.visivel && sticky.barTop >= sticky.headerBottom - 1, `barra acompanha a rolagem logo abaixo do header (barra em ${sticky.barTop}px, header termina em ${sticky.headerBottom}px)`);
  await pg.tap('#ftb-q');
  await pg.type('#ftb-q', 'child');
  await new Promise(r => setTimeout(r, 100));
  const painel = await pg.evaluate(() => { const p = document.getElementById('ftb-panel').getBoundingClientRect(); return { bottom: Math.round(p.bottom), h: innerHeight }; });
  ok(painel.bottom <= painel.h, `painel cabe na tela (termina em ${painel.bottom}px de ${painel.h}px)`);
  await pg.screenshot({ path: `${SHOTS}/mobile-busca.png` });
  await pg.tap('#ftb-panel .ftb-opt');
  await new Promise(r => setTimeout(r, 200));
  const d = await openDialog(pg);
  ok(d && d.title === 'Child-Pugh Score', `toque no resultado abre o modal (${d && d.title})`);
  const dl = await pg.evaluate(() => Math.round(document.getElementById('crit-modal').getBoundingClientRect().left));
  ok(dl === 0, `modal abre centralizado na tela (margem esquerda ${dl}px)`);
  await pg.screenshot({ path: `${SHOTS}/mobile-modal.png` });
  ok(errs.length === 0, `nenhum erro de página${errs.length ? ': ' + errs.join(' | ') : ''}`);
  await ctx.close();
}

// ═══ 5. desktop — capturas para revisão visual ══════════════════════════════
{
  const { pg, ctx } = await page();
  await pg.goto(`${BASE}/ferramentas.html`, { waitUntil: 'networkidle0' });
  await pg.evaluate(() => window.scrollTo(0, 150));
  await pg.screenshot({ path: `${SHOTS}/desktop-topo.png` });
  await pg.click('#ftb-chips .ftb-chip[data-chip="resp"]');
  await new Promise(r => setTimeout(r, 100));
  await pg.screenshot({ path: `${SHOTS}/desktop-chip.png` });
  await ctx.close();
}

// ═══ 6. app iOS simulado: native-guards.js real + window.Capacitor ══════════
console.log('\n== app iOS simulado (native-guards.js real) ==');
{
  appMode = true;
  const { pg, errs, ctx } = await page({ capacitor: true });
  await pg.goto(`${BASE}/ferramentas.html`, { waitUntil: 'networkidle0' });
  const g = await pg.evaluate(() => ({ dose: !!document.getElementById('dose-calc'), decay: !!document.getElementById('decay-calc'),
    hubDose: !!document.querySelector('a.tool-link[href="#dose-calc"]') }));
  ok(!g.dose && !g.decay && !g.hubDose, 'native-guards continua removendo #dose-calc, #decay-calc e o card do hub');
  const r1 = await search(pg, 'dose');
  const r2 = await search(pg, 'decaimento');
  ok(!r1.some(t => /Calculadora de dose/i.test(t)) && !r2.some(t => /Decaimento/i.test(t)), `busca não oferece as calculadoras removidas ("dose"→${JSON.stringify(r1)}, "decaimento"→${JSON.stringify(r2)})`);
  await pg.evaluate(() => { const i = document.getElementById('ftb-q'); i.value = ''; i.dispatchEvent(new Event('input'));
    i.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true })); });
  await pg.click('#ftb-chips .ftb-chip[data-chip="calc"]');
  const calc = await pg.evaluate(() => [...document.querySelectorAll('#ftb-panel .ftb-opt')].map(o => o.querySelector('.ftb-t').textContent));
  ok(calc.length === 6, `chip Calculadoras no app: 6 (sem dose e decaimento) — ${calc.join(', ')}`);
  await pg.goto(`${BASE}/ferramentas.html#dose-calc`, { waitUntil: 'networkidle0' });
  ok(!(await openDialog(pg)) && !(await pg.evaluate(() => document.getElementById('dose-calc'))), '#dose-calc no app → nada (a seção não existe)');
  await pg.goto(`${BASE}/ferramentas.html#recist`, { waitUntil: 'networkidle0' });
  const d = await openDialog(pg);
  ok(d && d.title === 'RECIST 1.1', `link direto funciona no app (#recist → ${d && d.title})`);
  ok(errs.length === 0, `nenhum erro de página${errs.length ? ': ' + errs.join(' | ') : ''}`);
  await ctx.close();
  appMode = false;
}

// ═══ 7. idioma ══════════════════════════════════════════════════════════════
console.log('\n== i18n ==');
{
  const { pg, errs, ctx } = await page();
  await pg.goto(`${BASE}/ferramentas.html`, { waitUntil: 'networkidle0' });
  await pg.evaluate(() => toggleLang());
  await new Promise(r => setTimeout(r, 500));
  await pg.click('#ftb-chips .ftb-chip[data-chip="calc"]');
  const en = await pg.evaluate(() => ({ ph: document.getElementById('ftb-q').placeholder,
    chip: document.querySelector('#ftb-chips .ftb-chip[data-chip="calc"]').textContent,
    status: document.querySelector('#ftb-panel .ftb-status').textContent,
    tag: (document.querySelector('#ftb-panel .ftb-tag.is-calc') || {}).textContent }));
  ok(/Search/.test(en.ph) && en.chip === 'Calculators' && /tools/.test(en.status) && en.tag === 'Calculator',
     `EN: placeholder "${en.ph}", chip "${en.chip}", status "${en.status}", etiqueta "${en.tag}"`);
  ok(errs.length === 0, `nenhum erro de página${errs.length ? ': ' + errs.join(' | ') : ''}`);
  await ctx.close();
}

await browser.close(); server.close();
console.log(`\n${falhas ? '✗ ' + falhas + ' FALHA(S)' : '✓ TODAS AS FUNCIONALIDADES NOVAS OK'}`);
process.exit(falhas ? 1 : 0);
