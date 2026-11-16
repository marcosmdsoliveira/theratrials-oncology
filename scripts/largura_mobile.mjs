#!/usr/bin/env node
/* ============================================================================
 * largura_mobile.mjs — nenhuma página pode pedir rolagem lateral no celular
 *
 * Abre cada página em Chrome real, em largura de iPhone, e acusa:
 *   • página mais larga que a tela (com o elemento que estoura);
 *   • contêiner com rolagem lateral (tabela larga, barra de atalhos em linha);
 *   • em Ferramentas: cada grupo e cada uma das fichas (modais);
 *   • em Tumor Boards: cada mapa aberto.
 *
 * Precisa do Google Chrome e do puppeteer-core do harness de equivalência
 * (cd scripts/equivalencia-ferramentas && npm install). Sirva o site antes:
 *
 *   python3 -m http.server 8765 &
 *   W=390 node scripts/largura_mobile.mjs http://127.0.0.1:8765 *.html
 *   W=320 node scripts/largura_mobile.mjs http://127.0.0.1:8765 *.html
 *
 * Sai com código 1 se alguma página ou visão tiver pendência.
 * ==========================================================================*/
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';
const require = createRequire(path.join(path.dirname(fileURLToPath(import.meta.url)), 'equivalencia-ferramentas') + path.sep);
const puppeteer = require('puppeteer-core');
const BASE = process.argv[2];
const PAGES = process.argv.slice(3);
const W = +(process.env.W || 390);
const browser = await puppeteer.launch({ executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: 'new', args: ['--no-first-run'] });
const measure = () => {
  const vw = document.documentElement.clientWidth;
  const vis = (e) => { const r = e.getBoundingClientRect(); const cs = getComputedStyle(e); return r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none'; };
  const label = (e) => { let s = e.tagName.toLowerCase(); if (e.id) s += '#' + e.id; const c = String(e.className && e.className.baseVal !== undefined ? e.className.baseVal : e.className || '').trim().split(/\s+/).filter(Boolean).slice(0, 2).join('.'); if (c) s += '.' + c; return s; };
  const path = (e) => { const p = []; for (let x = e, i = 0; x && x !== document.body && i < 4; x = x.parentElement, i++) p.unshift(label(x)); return p.join(' > '); };
  const clipped = (e) => { for (let x = e.parentElement; x && x !== document.body && x !== document.documentElement; x = x.parentElement) { const o = getComputedStyle(x).overflowX; if (o !== 'visible') return true; } return false; };
  const out = { pageOverflow: document.documentElement.scrollWidth - vw, wide: [], scrollers: [] };
  const seenW = new Map(), seenS = new Map();
  for (const e of document.querySelectorAll('body *')) {
    if (!vis(e)) continue;
    const r = e.getBoundingClientRect(), cs = getComputedStyle(e);
    if (cs.position === 'fixed' && !e.closest('dialog')) continue;
    if ((cs.overflowX === 'auto' || cs.overflowX === 'scroll') && e.scrollWidth > e.clientWidth + 1) {
      const k = path(e); const v = seenS.get(k) || { n: 0, max: 0 }; v.n++; v.max = Math.max(v.max, e.scrollWidth - e.clientWidth); seenS.set(k, v);
    }
    const pr = e.parentElement ? e.parentElement.getBoundingClientRect() : { right: 0 };
    // o mais externo que estoura: ele passa da tela e o pai não (ou o pai é mais estreito que ele)
    if (out.pageOverflow > 1 && r.right > vw + 1 && !clipped(e) && (pr.right <= vw + 1 || r.right > pr.right + 1)) {
      const k = path(e); const v = seenW.get(k) || { n: 0, max: 0 }; v.n++; v.max = Math.max(v.max, Math.round(r.right - vw)); seenW.set(k, v);
    }
  }
  out.wide = [...seenW].sort((a, b) => b[1].max - a[1].max).slice(0, 6).map(([k, v]) => `${k} ×${v.n} (+${v.max}px)`);
  out.scrollers = [...seenS].sort((a, b) => b[1].max - a[1].max).slice(0, 12).map(([k, v]) => `${k} ×${v.n} (+${v.max}px)`);
  return out;
};
let falhas = 0;
const show = (name, m) => {
  const bad = m.pageOverflow > 1 || m.scrollers.length;
  if (bad) falhas++;
  console.log(`${bad ? '✗' : '✓'} ${name}${m.pageOverflow > 1 ? `  página +${m.pageOverflow}px` : ''}`);
  for (const w of m.wide) console.log('     largo: ' + w);
  for (const s of m.scrollers) console.log('     rolagem lateral: ' + s);
};
for (const p of PAGES) {
  const ctx = await browser.createBrowserContext(); const pg = await ctx.newPage();
  await pg.setViewport({ width: W, height: 844, deviceScaleFactor: 2, isMobile: true, hasTouch: true });
  await pg.setRequestInterception(true);
  pg.on('request', (r) => (/umami|buttondown/.test(r.url()) ? r.abort() : r.continue()));
  await pg.goto(`${BASE}/${p}`, { waitUntil: 'networkidle2', timeout: 60000 }).catch(() => {});
  await new Promise((r) => setTimeout(r, 900));
  show(p, await pg.evaluate(measure));
  if (p.startsWith('tumor-boards')) {
    const ids = await pg.evaluate(() => [...document.querySelectorAll('article.tumor-map-card[id^="hub-"]')].map((a) => a.id));
    for (const id of ids) {
      await pg.evaluate((id) => document.getElementById(id).click(), id); await new Promise((r) => setTimeout(r, 700));
      show(`  mapa ${id.slice(4)}`, await pg.evaluate(measure));
      await pg.evaluate(() => { const el = document.querySelector('[x-data]'); const d = el && el._x_dataStack && el._x_dataStack[0]; if (d) d.openMap = null; }); await new Promise((r) => setTimeout(r, 200));
    }
  }
  if (p.startsWith('ferramentas')) {
    const groups = await pg.evaluate(() => [...document.querySelectorAll('section.tool[id]')].map((s) => s.id));
    for (const g of groups) {
      await pg.evaluate((g) => window.FTView && window.FTView.show(g), g); await new Promise((r) => setTimeout(r, 250));
      show(`  grupo ${g}`, await pg.evaluate(measure));
      const calls = await pg.evaluate((g) => [...document.querySelectorAll(`#${g} button[onclick^="open"]`)].map((b) => b.getAttribute('onclick')), g);
      const badM = [];
      for (const c of calls) {
        const m = await pg.evaluate(async (c, measureSrc) => {
          const b = [...document.querySelectorAll('button[onclick]')].find((x) => x.getAttribute('onclick') === c); b.click();
          await new Promise((r) => setTimeout(r, 120));
          const d = document.querySelector('dialog[open]'); if (!d) return null;
          const body = d.querySelector('.tnm-modal-body');
          const tables = [...d.querySelectorAll('table')].map((t) => Math.round(t.getBoundingClientRect().width));
          const r = { over: body.scrollWidth - body.clientWidth, bodyW: body.clientWidth, tables };
          d.close(); return r;
        }, c);
        if (m && m.over > 1) badM.push(`${c} +${m.over}px (tabelas ${m.tables.join('/')} em ${m.bodyW}px)`);
      }
      if (badM.length) { falhas++; console.log(`   ✗ ${badM.length}/${calls.length} fichas com rolagem lateral:`); badM.forEach((x) => console.log('       ' + x)); }
      else if (calls.length) console.log(`   ✓ ${calls.length} fichas sem rolagem lateral`);
    }
  }
  await ctx.close();
}
await browser.close();
if (falhas) { console.error(`\n✗ ${falhas} página(s)/visão(ões) com rolagem lateral`); process.exit(1); }
console.log('\n✓ nenhuma página pede rolagem lateral');
