#!/usr/bin/env node
/* ============================================================================
 * validate_trials_br.mjs — Trial Matcher (THERA_TRIALS_BR) integrity guard
 *
 * The Trial Matcher lists oncology trials OPEN IN BRAZIL. For each card:
 *   FAIL  - nct_url / contato_url point to a DIFFERENT NCT than `nct`
 *   FAIL  - the NCT does not exist on ClinicalTrials.gov (404)
 *   WARN  - CT.gov overallStatus is no longer recruiting (card says it is)
 *   WARN  - Brazil is not among CT.gov locations (card claims BR-open)
 *   NOTE  - card has no concrete NCT id (e.g. observational/unregistered)
 *
 * (Drug/intervention matching is NOT checked here: card drug names are in
 *  Portuguese — "Datopotamabe" vs CT.gov "Datopotamab" — so token overlap is
 *  unreliable. Drug↔trial correctness was verified at insertion time.)
 *
 * Exit 0 if no FAIL, else 1 (CI blocks). WARN never blocks unless --warn-fail.
 * Usage: node scripts/validate_trials_br.mjs [--json report.json] [--warn-fail]
 * ==========================================================================*/
import path from 'node:path';
import fs from 'node:fs';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DATA = path.join(__dirname, '..', 'assets', 'js', 'trials_br.js');
const args = process.argv.slice(2);
const jsonOut = args.includes('--json') ? args[args.indexOf('--json') + 1] : null;
const warnFail = args.includes('--warn-fail');

const require = createRequire(import.meta.url);
globalThis.window = {};
require(DATA);
const trials = globalThis.window.THERA_TRIALS_BR;

const sleep = ms => new Promise(r => setTimeout(r, ms));
const nctIn = u => (u || '').match(/NCT\d{8}/)?.[0] || null;
async function jget(u, t = 3) { for (let i = 0; i < t; i++) { try { const r = await fetch(u); if (r.status === 404) return { __nf: 1 }; if (r.ok) return await r.json(); } catch {} await sleep(500); } return null; }

(async () => {
  const results = [], notes = [];
  let i = 0;
  for (const tr of trials) {
    const nct = nctIn(tr.nct);
    if (!nct) { notes.push({ id: tr.id, nome: tr.nome, nct: tr.nct || '' }); continue; }
    const flags = [];
    if (tr.fonte_url && nctIn(tr.fonte_url) !== nct) flags.push({ lvl: 'FAIL', m: `fonte_url aponta p/ ${nctIn(tr.fonte_url)} ≠ ${nct}` });
    if (tr.contato_url && nctIn(tr.contato_url) !== nct) flags.push({ lvl: 'FAIL', m: `contato_url aponta p/ ${nctIn(tr.contato_url)} ≠ ${nct}` });
    const j = await jget('https://clinicaltrials.gov/api/v2/studies/' + nct + '?fields=protocolSection.identificationModule,protocolSection.statusModule,protocolSection.armsInterventionsModule,protocolSection.contactsLocationsModule');
    await sleep(140);
    if (!j) flags.push({ lvl: 'WARN', m: 'CT.gov fetch falhou (transitório?)' });
    else if (j.__nf) flags.push({ lvl: 'FAIL', m: `${nct} não existe no ClinicalTrials.gov` });
    else {
      const p = j.protocolSection || {};
      const st = (p.statusModule && p.statusModule.overallStatus) || '';
      const locs = (p.contactsLocationsModule && p.contactsLocationsModule.locations || []);
      const brazil = locs.some(l => /brazil|brasil/i.test(l.country || ''));
      if (st && !/RECRUITING/i.test(st)) flags.push({ lvl: 'WARN', m: `status CT.gov = ${st} (card: Recrutando)` });
      if (!brazil) flags.push({ lvl: 'WARN', m: 'Brasil não consta nos locais do CT.gov' });
    }
    results.push({ id: tr.id, nome: tr.nome, nct, flags });
    if (++i % 20 === 0) console.error(`  ${i}/${trials.length}`);
  }

  const fails = results.filter(r => r.flags.some(f => f.lvl === 'FAIL'));
  const warns = results.filter(r => r.flags.some(f => f.lvl === 'WARN') && !r.flags.some(f => f.lvl === 'FAIL'));
  if (notes.length) { console.error(`\n--- NOTE: ${notes.length} card(s) sem NCT concreto (não-registrado/observacional) ---`); notes.forEach(n => console.error(`  ${n.nome} | "${n.nct}"`)); }
  console.error(`\nRESULT  OK=${results.length - fails.length - warns.length}  WARN=${warns.length}  FAIL=${fails.length}  (de ${results.length} c/ NCT; +${notes.length} sem NCT)`);
  if (warns.length) { console.error('\n--- WARN (revisar — recrutamento/Brasil/intervenção) ---'); warns.forEach(r => r.flags.forEach(f => console.error(`  ${r.nome} | ${r.nct} | ${f.m}`))); }
  if (fails.length) { console.error('\n--- FAIL (link inválido/inconsistente) ---'); fails.forEach(r => r.flags.filter(f => f.lvl === 'FAIL').forEach(f => console.error(`  ${r.nome} | ${r.nct} | ${f.m}`))); }
  if (jsonOut) fs.writeFileSync(jsonOut, JSON.stringify({ results, notes }, null, 1));
  process.exit((fails.length + (warnFail ? warns.length : 0)) ? 1 : 0);
})();
