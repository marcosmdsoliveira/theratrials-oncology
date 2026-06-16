#!/usr/bin/env node
/* ============================================================================
 * validate_pubmed.mjs — TheraTrials Oncology data integrity guard
 *
 * Detects FABRICATED / hallucinated `pubmed_url` PMIDs (valid numbers that
 * resolve to UNRELATED papers). This is the permanent guard against the
 * pubmed_url contamination audited & fixed in 2026-06.
 *
 * Only direct PubMed article links are validated:
 *     https://pubmed.ncbi.nlm.nih.gov/<PMID>/
 * Publisher/DOI links (nejm.org, doi.org, …), PMC links, PubMed *search*
 * links (?term=), "—" and empty values are NOT PMID-validatable and are
 * reported separately (not failures).
 *
 * Per PMID-link study, relatedness is judged against the trial's real
 * identity using two independent signals:
 *   1. PubMed `NCT[si]` — is the PMID linked to this study's trial?
 *   2. Token overlap between the stored article title and the trial's
 *      ClinicalTrials.gov officialTitle + conditions (English vs English).
 *   OK   = [si]-linked OR overlap>=2 OR (oncology term AND overlap>=1)
 *   WARN = oncology term but no [si] link and overlap<1  (review)
 *   FAIL = title unrelated to the trial (fabricated/wrong PMID), or PMID
 *          returns no PubMed record.
 *
 * Exit 0 if no FAIL, else 1 (so CI can block). WARN never blocks unless
 * --warn-fail is passed.
 *
 * Usage: node scripts/validate_pubmed.mjs [--json report.json] [--warn-fail]
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
const ONC = /cancer|carcinom|tumou?r|oncolog|prostat|breast|mama|lung|pulm|lymphom|leukem|leucem|myelom|melanoma|neoplas|metasta|chemo|radio|luteti|psma|dota|sarcom|glioma|neuroblast|thyroid|hepatocell|colorect|pancrea|gastric|ovari|cervic|endometri|renal|bladder|urothel|nsclc|sclc|crpc|her2|egfr|braf|kras|immun|antibod|radioligand|theranost|fap|mibg|octreot|paragangli|pheochrom|estrogen|androgen|brachy|sbrt|radiation|yttrium|actinium|radium|survival|adjuvant|neoadjuvant|leukaemia|menin|hodgkin|rectal|microsatellite|\baml\b|\bidh\b|lobectomy|esophag|oesophag|cisplatin|carboplatin|gemcitabine|oxaliplatin|fluorouracil|docetaxel|paclitaxel/i;
const STOP = new Set('a an the of for in on with versus vs and or to as plus study trial phase randomized randomised open label double blind placebo controlled multicenter multicentre prospective patients participants subjects treatment therapy efficacy safety evaluate evaluating comparing comparison combination dose advanced metastatic locally newly diagnosed progressive high low grade'.split(/\s+/));

/* Manually verified-correct PMIDs that the heuristics flag as WARN only
 * because the article is not tagged with NCT[si] in PubMed (older/landmark
 * trials) and its wording diverges from the ClinicalTrials.gov title.
 * Each was confirmed by hand to be the trial's real publication. Adding a
 * PMID here suppresses its WARN; NEVER add a PMID you have not verified. */
const KNOWN_GOOD = new Set([
  '40829092', // PRRT em PHEO/PGL — 177Lu-DOTATATE phase II (ppgl_0)
  '33739462', // LEGACY — Y-90 radioembolization solitary HCC
  '35617978', // RASER — radiation segmentectomy early HCC
  '22551127', // ESTIMABL — radioiodine ablation low-risk thyroid (NEJM 2012)
  '25549723', // Rothenberg — dabrafenib redifferentiation BRAF PTC
  '22646630', // CROSS — preoperative chemoradiotherapy esophageal (NEJM 2012)
  '17227978', // CONKO-001 — adjuvant gemcitabine pancreatic
  '41119954', // AlphaBet — 177Lu-PSMA-I&T + radium-223 mCRPC
  '17960013', // TAX 324 — TPF induction head & neck (NEJM 2007)
]);

function loadStudies() {
  const raw = fs.readFileSync(DATA, 'utf8');
  const m = raw.match(/window\.THERA_DATA\s*=\s*(\{[\s\S]*\});?\s*$/m);
  if (!m) throw new Error('Could not parse window.THERA_DATA from data.js');
  return JSON.parse(m[1]).studies;
}
function classify(url) {
  if (url == null || url === '' || url === '—') return { kind: 'none' };
  const art = url.match(/pubmed\.ncbi\.nlm\.nih\.gov\/(\d{6,9})\/?(?:$|[?#])/);
  if (art) return { kind: 'pmid', pmid: art[1] };
  if (/pubmed\.ncbi\.nlm\.nih\.gov\/\?term=/.test(url)) return { kind: 'search' };
  if (/pmc\.ncbi\.nlm\.nih\.gov/.test(url)) return { kind: 'pmc' };
  if (/doi\.org|nejm\.org|nature\.com|sciencedirect|thelancet|jamanetwork|ascopubs|annalsofoncology|jnm\.snmjournals|wiley|springer|oup|sagepub/.test(url)) return { kind: 'doi' };
  return { kind: 'other' };
}
const nctOf = s => (s.nct_url || '').match(/NCT\d{8}/)?.[0] || (s.nct || '').match(/NCT\d{8}/)?.[0] || null;

async function jget(url, tries = 3) {
  for (let i = 0; i < tries; i++) { try { const r = await fetch(url); if (r.ok) return await r.json(); } catch {} await sleep(600); }
  return null;
}
const sig = t => new Set(norm(t).split(/\s+/).filter(w => w.length >= 4 && !STOP.has(w)));
function overlap(a, b) { const A = sig(a), B = sig(b); let n = 0; A.forEach(w => { if (B.has(w)) n++; }); return n; }

async function titles(ids) {
  const out = {};
  for (let i = 0; i < ids.length; i += 100) {
    const b = ids.slice(i, i + 100);
    const j = await jget('https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&retmode=json&id=' + b.join(','));
    b.forEach(id => out[id] = (j && j.result && j.result[id] && j.result[id].title) || '');
    await sleep(350);
  }
  // Re-fetch empties individually: distinguishes a transient batch failure
  // (network/rate-limit) from a genuinely dead PMID, so CI does not flake.
  const empties = ids.filter(id => !out[id]);
  for (const id of empties) {
    const j = await jget('https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&retmode=json&id=' + id, 4);
    out[id] = (j && j.result && j.result[id] && j.result[id].title) || '';
    await sleep(300);
  }
  return out;
}

(async () => {
  const studies = loadStudies();
  const tagged = studies.map(s => ({ s, c: classify(s.pubmed_url), nct: nctOf(s) }));
  const pmidStudies = tagged.filter(t => t.c.kind === 'pmid');
  const kinds = tagged.reduce((a, t) => (a[t.c.kind] = (a[t.c.kind] || 0) + 1, a), {});
  console.error(`URL kinds: ${JSON.stringify(kinds)}`);
  console.error(`Validating ${pmidStudies.length} direct PubMed article links...`);

  const storedTitle = await titles(pmidStudies.map(t => t.c.pmid));

  // cache per-NCT [si] sets and ctgov officialTitle
  const siCache = {}, ctCache = {};
  async function siSet(nct) {
    if (siCache[nct]) return siCache[nct];
    const j = await jget('https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&retmode=json&retmax=80&term=' + encodeURIComponent(nct + '[si]'));
    await sleep(300);
    return siCache[nct] = new Set((j && j.esearchresult && j.esearchresult.idlist) || []);
  }
  async function ctTitle(nct) {
    if (ctCache[nct] !== undefined) return ctCache[nct];
    const j = await jget('https://clinicaltrials.gov/api/v2/studies/' + nct + '?fields=protocolSection.identificationModule,protocolSection.conditionsModule');
    await sleep(120);
    const p = j && j.protocolSection || {};
    const t = (p.identificationModule && (p.identificationModule.officialTitle || p.identificationModule.briefTitle)) || '';
    const c = (p.conditionsModule && p.conditionsModule.conditions || []).join(' ');
    return ctCache[nct] = (t + ' ' + c).trim();
  }

  const results = [];
  let i = 0;
  for (const { s, c, nct } of pmidStudies) {
    const st = storedTitle[c.pmid] || '';
    let status, detail = '', ov = null, linked = null;
    if (!st) { status = 'FAIL'; detail = 'PMID returns no PubMed record'; }
    else if (KNOWN_GOOD.has(c.pmid)) { status = 'OK'; detail = 'allowlisted (verified)'; }
    else {
      if (nct) {
        linked = (await siSet(nct)).has(c.pmid);
        const ct = await ctTitle(nct);
        ov = overlap(st, ct);
        if (linked) status = 'OK';
        else if (ov >= 2) status = 'OK';
        else if (ONC.test(st) && ov >= 1) status = 'OK';
        else if (ONC.test(st)) { status = 'WARN'; detail = `not in ${nct}[si], overlap ${ov} w/ CT.gov title (onco but unconfirmed)`; }
        else { status = 'FAIL'; detail = `not in ${nct}[si], overlap ${ov}, title not oncological`; }
      } else {
        status = ONC.test(st) ? 'OK' : 'FAIL';
        if (status === 'FAIL') detail = 'no NCT; stored title not oncological';
      }
    }
    results.push({ uid: s.uid, estudo: s.estudo, pmid: c.pmid, nct, status, detail, linked, overlap: ov, storedTitle: st });
    if (++i % 40 === 0) console.error(`  ${i}/${pmidStudies.length}`);
  }

  const by = results.reduce((a, r) => (a[r.status] = (a[r.status] || 0) + 1, a), {});
  const fails = results.filter(r => r.status === 'FAIL');
  const warns = results.filter(r => r.status === 'WARN');
  console.error(`\nRESULT  OK=${by.OK || 0}  WARN=${by.WARN || 0}  FAIL=${by.FAIL || 0}  (non-PMID links: search=${kinds.search || 0} doi=${kinds.doi || 0} pmc=${kinds.pmc || 0} none=${kinds.none || 0} other=${kinds.other || 0})`);
  if (warns.length) { console.error('\n--- WARN (review) ---'); warns.forEach(r => console.error(`  ${r.uid} | ${r.estudo} | PMID ${r.pmid} | ${r.detail}\n      ${r.storedTitle.slice(0, 90)}`)); }
  if (fails.length) { console.error('\n--- FAIL (fabricated / wrong PMID) ---'); fails.forEach(r => console.error(`  ${r.uid} | ${r.estudo} | PMID ${r.pmid} | ${r.detail}\n      ${r.storedTitle.slice(0, 90)}`)); }
  if (jsonOut) fs.writeFileSync(jsonOut, JSON.stringify(results, null, 1));
  process.exit((fails.length + (warnFail ? warns.length : 0)) ? 1 : 0);
})();
