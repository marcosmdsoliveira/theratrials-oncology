// Captura um snapshot funcional completo de ferramentas.html.
// Uso: node snapshot.mjs <dir-do-site> <saida.json> [--app]
//
// Tudo que envolve cálculo é exercitado disparando os MESMOS eventos que o
// usuário dispara (input/change nos campos, click nos cards), para que a
// ligação HTML→handler também seja testada — não só as funções.
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import puppeteer from 'puppeteer-core';

// Registro de service worker neutralizado antes de qualquer script da página:
// sem Capacitor o pwa-install.js tentaria registrar (o que o app real nunca faz).
// Promessa que nunca resolve = nenhum SW, nenhum erro, nenhum .then disparado.
const SEM_SW = () => { if (window.ServiceWorkerContainer)
  ServiceWorkerContainer.prototype.register = function () { return new Promise(() => {}); }; };


// ROOT resolvido: a checagem abaixo compara com path.resolve, e um caminho
// relativo (como o ../.. do README) faria todo arquivo virar 404.
const ROOT = path.resolve(process.argv[2]);
const OUT = process.argv[3];
const CHROME = process.env.CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const TYPES = { '.html':'text/html; charset=utf-8', '.js':'text/javascript; charset=utf-8',
  '.css':'text/css', '.json':'application/json', '.png':'image/png', '.svg':'image/svg+xml',
  '.webp':'image/webp', '.woff2':'font/woff2', '.ico':'image/x-icon' };

const server = http.createServer((req, res) => {
  const p = decodeURIComponent(new URL(req.url, 'http://x').pathname);
  // Nunca servir o service worker: sem window.Capacitor, o pwa-install.js o
  // registraria (o que NUNCA ocorre dentro do app), e SW se instalando no meio
  // da bateria faz o Puppeteer perder a sessão do navegador.
  if (p === '/sw.js') { res.writeHead(404); return res.end(); }
  const f = path.join(ROOT, p === '/' ? 'index.html' : p);
  if (!f.startsWith(path.resolve(ROOT)) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) {
    res.writeHead(404); return res.end('404');
  }
  res.writeHead(200, { 'content-type': TYPES[path.extname(f)] || 'application/octet-stream',
                       'cache-control': 'no-store' });
  fs.createReadStream(f).pipe(res);
});
await new Promise(r => server.listen(0, '127.0.0.1', r));
const BASE = `http://127.0.0.1:${server.address().port}`;

const browser = await puppeteer.launch({ executablePath: CHROME, headless: 'new',
  args: ['--no-first-run', '--no-default-browser-check'] });
const sha = (s) => crypto.createHash('sha256').update(String(s)).digest('hex').slice(0, 16);

async function newPage(width = 1280, height = 900) {
  const ctx = await browser.createBrowserContext();
  const page = await ctx.newPage();
  await page.setViewport({ width, height });
  await page.setBypassServiceWorker(true);
  await page.evaluateOnNewDocument(SEM_SW);
  await page.setRequestInterception(true);
  page.on('request', r => {
    const u = r.url();
    // Umami fora: os testes não podem virar visitas na analytics real.
    if (u.includes('cloud.umami.is') || u.includes('fonts.googleapis.com') || u.includes('fonts.gstatic.com')) return r.abort();
    r.continue();
  });
  const errors = [];
  page.on('pageerror', e => errors.push('pageerror: ' + e.message));
  page.on('console', m => { if (m.type() === 'error') errors.push('console: ' + m.text()); });
  return { page, errors, ctx };
}

const snap = { errors: {} };

// ── 1. carga, estrutura e dados ────────────────────────────────────────────
{
  const { page, errors, ctx } = await newPage();
  await page.goto(`${BASE}/ferramentas.html`, { waitUntil: 'networkidle0' });
  Object.assign(snap, await page.evaluate(() => {
    const txt = (el) => (el ? el.innerText.replace(/\s+/g, ' ').trim() : null);
    return {
      title: document.title,
      sections: [...document.querySelectorAll('section.tool')].map(s => s.id),
      hub: [...document.querySelectorAll('a.tool-link')].map(a => [a.getAttribute('href'), txt(a)]),
      // `const` de topo em script clássico não vai para window, mas é visível
      // pelo nome no escopo global — é exatamente o que o evaluate enxerga.
      data: {
        TNM:   typeof TNM_DATA   !== 'undefined' ? JSON.stringify(TNM_DATA)   : null,
        CTCAE: typeof CTCAE_DATA !== 'undefined' ? JSON.stringify(CTCAE_DATA) : null,
        CRIT:  typeof CRIT_DATA  !== 'undefined' ? JSON.stringify(CRIT_DATA)  : null,
      },
      keys: {
        TNM:   typeof TNM_DATA   !== 'undefined' ? Object.keys(TNM_DATA)   : null,
        CTCAE: typeof CTCAE_DATA !== 'undefined' ? Object.keys(CTCAE_DATA) : null,
        CRIT:  typeof CRIT_DATA  !== 'undefined' ? Object.keys(CRIT_DATA)  : null,
      },
      globals: ['openTNM','openCTCAE','openCrit','calcDose','calcRenal','calcAlbi','calcMeld',
                'calcChildPugh','hexToRgbStr','toolsApp','_dcCalc']
               .map(n => [n, (() => { try { return typeof eval(n); } catch (e) { return 'ERR'; } })()]),
      sectionText: Object.fromEntries([...document.querySelectorAll('section.tool')]
                     .map(s => [s.id, s.innerText.replace(/\s+/g, ' ').trim()])),
    };
  }));
  snap.data = Object.fromEntries(Object.entries(snap.data).map(([k, v]) => [k, v && { sha: sha(v), len: v.length }]));
  snap.sectionText = Object.fromEntries(Object.entries(snap.sectionText).map(([k, v]) => [k, sha(v)]));
  snap.errors.load = errors.slice();
  await ctx.close();
}

// ── 2. todos os modais, clicando no botão real ─────────────────────────────
{
  const { page, errors, ctx } = await newPage();
  await page.goto(`${BASE}/ferramentas.html`, { waitUntil: 'networkidle0' });
  snap.modals = await page.evaluate(async () => {
    const out = {};
    const btns = [...document.querySelectorAll('button[onclick^="open"]')];
    for (const b of btns) {
      const call = b.getAttribute('onclick');
      b.click();
      await new Promise(r => requestAnimationFrame(() => r()));
      const dlg = [...document.querySelectorAll('dialog')].find(d => d.open);
      if (!dlg) { out[call] = 'NENHUM MODAL ABERTO'; continue; }
      const body = dlg.querySelector('[id$="-modal-body"]');
      out[call] = {
        dialog: dlg.id,
        title: (dlg.querySelector('[id$="-modal-title"]') || {}).textContent,
        ed: (dlg.querySelector('[id$="-modal-ed"]') || {}).textContent,
        body: body ? body.innerHTML : null,
      };
      dlg.close();
    }
    return out;
  });
  for (const k in snap.modals) if (snap.modals[k].body) snap.modals[k].body = snap.modals[k].body.length + ':' + (await sha256(snap.modals[k].body));
  snap.errors.modals = errors.slice();
  await ctx.close();
}
async function sha256(s) { return sha(s); }

// ── 3. calculadoras de página ──────────────────────────────────────────────
{
  const { page, errors, ctx } = await newPage();
  await page.goto(`${BASE}/ferramentas.html`, { waitUntil: 'networkidle0' });
  snap.calc = await page.evaluate(() => {
    const $ = (id) => document.getElementById(id);
    const set = (id, v, ev = ['input', 'change']) => {
      const el = $(id); if (!el) return false;
      if (el.type === 'checkbox') el.checked = !!v; else el.value = v;
      ev.forEach(e => el.dispatchEvent(new Event(e, { bubbles: true })));
      return true;
    };
    const grab = (ids) => ids.map(id => { const e = $(id); return e ? [e.className, e.innerHTML] : null; });
    const R = {};

    // Dose diagnóstica — todos os radiofármacos × pesos, incluindo bordas.
    R.dose = [];
    if ($('dose-radio')) {
      const radios = [...$('dose-radio').options].map(o => o.value);
      for (const r of radios) for (const w of ['3','10','20','35','50','70','100','150','0','-5','']) {
        set('dose-radio', r); set('dose-weight', w);
        R.dose.push([r, w, grab(['eanm-dose','eanm-min','eanm-detail','na-dose','na-range','na-detail'])]);
      }
    }

    // Decaimento PET/CT — isótopos × atividade × intervalo × horário × captação × fator.
    R.decay = [];
    if (window._dcCalc && $('dc-isotope')) {
      const isos = [...$('dc-isotope').options].map(o => o.value);
      for (const iso of isos) for (const a0 of ['5','21.6','40']) for (const iv of ['15','25','60'])
      for (const t0 of ['07:30','08:00','13:15']) for (const up of ['45','60']) for (const fa of ['0.09','0.1']) {
        set('dc-isotope', iso, ['change']);
        if (iso === 'custom') set('dc-hl', '30');
        set('dc-a0', a0); set('dc-interval', iv); set('dc-t0', t0); set('dc-uptake', up); set('dc-factor', fa);
        R.decay.push([iso, a0, iv, t0, up, fa, grab(['dc-tbody','dc-summary-consumed','dc-summary-remaining'])]);
      }
      // Pacientes com peso individual
      set('dc-isotope', '109.77', ['change']); set('dc-a0', '21.6'); set('dc-interval', '25');
      for (let k = 0; k < 3; k++) window._dcCalc.addPatient && window._dcCalc.addPatient();
      [...document.querySelectorAll('[id^="dc-w-"]')].forEach((el, i) => { el.value = String(55 + i * 12);
        el.dispatchEvent(new Event('input', { bubbles: true })); });
      R.decayPatients = grab(['dc-tbody','dc-summary-consumed','dc-summary-remaining']);
    }

    // Função renal — idade × sexo × peso × altura × creatinina.
    R.renal = [];
    if ($('renal-cr')) {
      for (const age of ['18','40','60','85']) for (const sex of ['M','F']) for (const w of ['45','70','110'])
      for (const h of ['150','170','190']) for (const cr of ['0.5','1.0','1.8','4.0']) {
        set('renal-age', age); set('renal-sex', sex); set('renal-weight', w); set('renal-height', h); set('renal-cr', cr);
        R.renal.push([age, sex, w, h, cr, grab(['ckdepi-val','ckdepi-stage','cg-val','cg-bsa','mdrd-val','mdrd-stage','renal-ckd-bar'])]);
      }
    }
    return R;
  });
  snap.errors.calc = errors.slice();
  await ctx.close();
}

// ── 4. calculadoras dentro dos modais de CHC ───────────────────────────────
{
  const { page, errors, ctx } = await newPage();
  await page.goto(`${BASE}/ferramentas.html`, { waitUntil: 'networkidle0' });
  snap.hcc = await page.evaluate(async () => {
    const $ = (id) => document.getElementById(id);
    const set = (id, v) => { const el = $(id); if (!el) return;
      if (el.type === 'checkbox') el.checked = !!v; else el.value = v;
      ['input','change'].forEach(e => el.dispatchEvent(new Event(e, { bubbles: true }))); };
    const open = async (key) => { const b = document.querySelector(`button[onclick="openCrit('${key}')"]`);
      b.click(); await new Promise(r => requestAnimationFrame(r)); };
    const close = () => document.querySelectorAll('dialog[open]').forEach(d => d.close());
    const res = (id) => { const e = $(id); return e ? [e.className, e.innerHTML] : null; };
    const R = { albi: [], meld: [], cp: [] };

    await open('albi');
    R.albi.push(['vazio', res('albi-result')]);
    for (const b of ['0.5','1.2','3','8']) for (const bu of ['mgdl','umol']) for (const a of ['2.5','3.5','4.5','35']) for (const au of ['gdl','gl']) {
      set('albi-bili-u', bu); set('albi-alb-u', au); set('albi-bili', b); set('albi-alb', a);
      R.albi.push([b, bu, a, au, res('albi-result')]);
    }
    close();

    await open('meld');
    R.meld.push(['vazio', res('meld-result')]);
    for (const b of ['0.8','2','6']) for (const cr of ['0.7','1.5','3.5']) for (const inr of ['1.0','1.8','3.0'])
    for (const na of ['','128','140']) for (const al of ['','2.5','3.8']) for (const sx of ['M','F']) for (const di of [false, true]) {
      set('meld-sex', sx); set('meld-dialysis', di); set('meld-bili', b); set('meld-cr', cr);
      set('meld-inr', inr); set('meld-na', na); set('meld-alb', al);
      R.meld.push([b, cr, inr, na, al, sx, di, res('meld-result')]);
    }
    close();

    await open('child-pugh');
    R.cp.push(['vazio', res('cp-result')]);
    for (const b of ['1','2.5','4']) for (const a of ['3.8','3.0','2.5']) for (const inr of ['1.2','2.0','2.6'])
    for (const as of ['1','2','3']) for (const en of ['1','2','3']) {
      set('cp-ascites', as); set('cp-enceph', en); set('cp-bili', b); set('cp-alb', a); set('cp-inr', inr);
      R.cp.push([b, a, inr, as, en, res('cp-result')]);
    }
    close();
    return R;
  });
  snap.errors.hcc = errors.slice();
  await ctx.close();
}

// ── 5. troca de idioma (i18n) ──────────────────────────────────────────────
{
  const { page, errors, ctx } = await newPage();
  await page.goto(`${BASE}/ferramentas.html`, { waitUntil: 'networkidle0' });
  snap.i18n = await page.evaluate(async () => {
    const t = () => [...document.querySelectorAll('.ft-hero, .tools-hub')].map(e => e.innerText.replace(/\s+/g,' ').trim()).join('|');
    const pt = t();
    if (typeof toggleLang === 'function') toggleLang();
    await new Promise(r => setTimeout(r, 400));
    const en = t();
    return { pt, en, mudou: pt !== en };
  });
  snap.i18n = { pt: sha(snap.i18n.pt), en: sha(snap.i18n.en), mudou: snap.i18n.mudou };
  snap.errors.i18n = errors.slice();
  await ctx.close();
}

// resumo de tamanhos para conferência humana
snap.counts = {
  modais: Object.keys(snap.modals).length,
  dose: snap.calc.dose.length, decay: snap.calc.decay.length, renal: snap.calc.renal.length,
  albi: snap.hcc.albi.length, meld: snap.hcc.meld.length, cp: snap.hcc.cp.length,
};
// hash de cada bateria de cálculo (a comparação campo-a-campo fica no JSON)
snap.hashes = {
  dose: sha(JSON.stringify(snap.calc.dose)), decay: sha(JSON.stringify(snap.calc.decay)),
  decayPatients: sha(JSON.stringify(snap.calc.decayPatients)), renal: sha(JSON.stringify(snap.calc.renal)),
  albi: sha(JSON.stringify(snap.hcc.albi)), meld: sha(JSON.stringify(snap.hcc.meld)), cp: sha(JSON.stringify(snap.hcc.cp)),
  modals: sha(JSON.stringify(snap.modals)),
};

fs.writeFileSync(OUT, JSON.stringify(snap, null, 1));
await browser.close(); server.close();
console.log(JSON.stringify({ counts: snap.counts, hashes: snap.hashes, data: snap.data,
  errors: Object.fromEntries(Object.entries(snap.errors).map(([k, v]) => [k, v.length])) }, null, 1));
