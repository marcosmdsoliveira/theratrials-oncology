#!/usr/bin/env node
/* ============================================================================
 * validate_nct.mjs — TheraTrials Oncology data integrity guard (ClinicalTrials)
 *
 * Verifies that every study's `nct_url` / `nct` NCT id resolves on
 * ClinicalTrials.gov AND that the resolved trial actually matches the card
 * (drug + disease), catching WRONG / FABRICATED NCTs that resolve to an
 * unrelated trial (e.g. the 5 found in `ref` fields earlier).
 *
 * Per study with a concrete NCT id:
 *   - fetch CT.gov v2 study (officialTitle, briefTitle, acronym, conditions,
 *     interventions, status).
 *       • not found / 404 ................................. FAIL (invalid NCT)
 *   - relatedness vs the card's English anchor (titulo_full when present,
 *     else estudo + acron) via token overlap + acronym match:
 *       • acronym matches OR overlap>=2 ................... OK
 *       • overlap==1 ..................................... WARN
 *       • overlap==0 and no acronym match ................ FAIL (wrong trial)
 *
 * Studies whose nct field is a non-id placeholder ("NCT não confirmado",
 * "Múltiplos", "Em planejamento", "—", empty) are listed as NOTE (no NCT to
 * validate), never failures.
 *
 * Exit 0 if no FAIL, else 1 (CI blocks). WARN never blocks unless --warn-fail.
 * Usage: node scripts/validate_nct.mjs [--json report.json] [--warn-fail]
 * ==========================================================================*/
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DATA = path.join(__dirname, '..', 'assets', 'js', 'data.js');
const args = process.argv.slice(2);
const jsonOut = args.includes('--json') ? args[args.indexOf('--json') + 1] : null;
const warnFail = args.includes('--warn-fail');

const sleep = ms => new Promise(r => setTimeout(r, ms));
const norm = t => String(t || '').toLowerCase().replace(/[^a-z0-9α ]/g, ' ');
const STOP = new Set('a an the of for in on with versus vs and or to as plus study trial phase randomized randomised open label double blind placebo controlled multicenter multicentre prospective patients participants subjects treatment therapy efficacy safety evaluate evaluating comparing comparison combination dose advanced metastatic locally newly diagnosed progressive high low grade study2 patient cancer tumor tumour'.split(/\s+/));
const sig = t => new Set(norm(t).split(/\s+/).filter(w => w.length >= 4 && !STOP.has(w)));
function overlap(a, b) { const A = sig(a), B = sig(b); let n = 0; A.forEach(w => { if (B.has(w)) n++; }); return n; }

/* Verified-correct NCTs that fail the heuristic (CT.gov wording diverges a lot
 * from the publication title and no shared acronym). Add only after manual
 * confirmation that the NCT is the right trial. */
const KNOWN_GOOD = new Set([
  'NCT03206060', // PRRT PHEO/PGL — Lu-177-DOTATATE inoperable pheochromocytoma/paraganglioma (ppgl_0); low token overlap (plural/hyphen) but verified correct
]);

function loadStudies() {
  const raw = fs.readFileSync(DATA, 'utf8');
  const m = raw.match(/window\.THERA_DATA\s*=\s*(\{[\s\S]*\});?\s*$/m);
  if (!m) throw new Error('Could not parse window.THERA_DATA from data.js');
  return JSON.parse(m[1]).studies;
}
const nctOf = s => (s.nct_url || '').match(/NCT\d{8}/)?.[0] || (s.nct || '').match(/NCT\d{8}/)?.[0] || null;
function acronymOf(estudo) {
  let k = String(estudo).split(' (')[0].split(' / ')[0].split(' — ')[0].split(' – ')[0].split(' - ')[0];
  k = k.replace(/\s+(em|no|na|de|para|com)\s.*$/i, '').trim();
  return k.length >= 3 ? k.toLowerCase().replace(/[^a-z0-9]/g, '') : null;
}
async function jget(url, tries = 3) {
  for (let i = 0; i < tries; i++) {
    try { const r = await fetch(url); if (r.status === 404) return { __notfound: true }; if (r.ok) return await r.json(); } catch {}
    await sleep(500);
  }
  return null;
}

(async () => {
  const studies = loadStudies();
  const withNct = studies.filter(s => nctOf(s));
  const noNct = studies.filter(s => !nctOf(s) && s.nct && !/^—?$/.test(s.nct.trim()));
  console.error(`Validating ${withNct.length} studies with a concrete NCT id...`);

  const results = [];
  let i = 0;
  for (const s of withNct) {
    const nct = nctOf(s);
    const j = await jget('https://clinicaltrials.gov/api/v2/studies/' + nct + '?fields=protocolSection.identificationModule,protocolSection.conditionsModule,protocolSection.armsInterventionsModule,protocolSection.statusModule');
    await sleep(130);
    let status, detail = '';
    if (!j) { status = 'WARN'; detail = 'CT.gov fetch failed (transient?)'; }
    else if (j.__notfound) { status = 'FAIL'; detail = `${nct} not found on ClinicalTrials.gov`; }
    else if (KNOWN_GOOD.has(nct)) { status = 'OK'; detail = 'allowlisted'; }
    else {
      const p = j.protocolSection || {};
      const idm = p.identificationModule || {};
      const cond = (p.conditionsModule && p.conditionsModule.conditions || []).join(' ');
      const intr = (p.armsInterventionsModule && p.armsInterventionsModule.interventions || []).map(x => x.name).join(' ');
      const ctText = [idm.officialTitle, idm.briefTitle, idm.acronym, cond, intr].join(' ');
      const anchor = s.titulo_full || (s.estudo + ' ' + (s.acron || ''));
      const acr = acronymOf(s.estudo);
      const acrMatch = acr && norm(ctText).replace(/[^a-z0-9]/g, '').includes(acr);
      const ov = overlap(ctText, anchor);
      if (acrMatch || ov >= 2) status = 'OK';
      else if (ov === 1) { status = 'WARN'; detail = `low match (overlap 1) — CT.gov: "${(idm.briefTitle || idm.officialTitle || '').slice(0, 70)}"`; }
      else { status = 'FAIL'; detail = `NCT resolves but does NOT match card — CT.gov: "${(idm.briefTitle || idm.officialTitle || '').slice(0, 80)}"`; }
    }
    results.push({ uid: s.uid, estudo: s.estudo, nct, status, detail });
    if (++i % 40 === 0) console.error(`  ${i}/${withNct.length}`);
  }

  const by = results.reduce((a, r) => (a[r.status] = (a[r.status] || 0) + 1, a), {});
  const fails = results.filter(r => r.status === 'FAIL');
  const warns = results.filter(r => r.status === 'WARN');
  if (noNct.length) { console.error(`\n--- NOTE: ${noNct.length} study(ies) with placeholder nct (no id to validate) ---`); noNct.forEach(s => console.error(`  ${s.uid} | ${s.estudo} | "${s.nct}"`)); }
  console.error(`\nRESULT  OK=${by.OK || 0}  WARN=${by.WARN || 0}  FAIL=${by.FAIL || 0}  (of ${withNct.length} with NCT id)`);
  if (warns.length) { console.error('\n--- WARN (review) ---'); warns.forEach(r => console.error(`  ${r.uid} | ${r.estudo} | ${r.nct} | ${r.detail}`)); }
  if (fails.length) { console.error('\n--- FAIL (wrong / invalid NCT) ---'); fails.forEach(r => console.error(`  ${r.uid} | ${r.estudo} | ${r.nct} | ${r.detail}`)); }
  if (jsonOut) fs.writeFileSync(jsonOut, JSON.stringify(results, null, 1));
  process.exit((fails.length + (warnFail ? warns.length : 0)) ? 1 : 0);
})();
