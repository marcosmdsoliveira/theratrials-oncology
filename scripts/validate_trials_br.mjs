#!/usr/bin/env node
/* ============================================================================
 * validate_trials_br.mjs — Trial Matcher (THERA_TRIALS_BR) integrity guard
 *
 * The Trial Matcher lists oncology trials OPEN IN BRAZIL. For each card:
 *   FAIL  - card has no concrete NCT id (see below)
 *   FAIL  - nct_url / contato_url point to a DIFFERENT NCT than `nct`
 *   FAIL  - the NCT does not exist on ClinicalTrials.gov (404)
 *   WARN  - CT.gov overallStatus is no longer recruiting (card says it is)
 *   WARN  - Brazil is not among CT.gov locations (card claims BR-open)
 *
 * Card sem NCT era só NOTE, que não bloqueia nada — e foi assim que o LUCERNA
 * (`nct: 'NCT a confirmar'`) e o Beyond CRC (`nct: ''`) ficaram publicados
 * meses depois de encerrarem. Sem NCT não há como o validador checar se o
 * estudo ainda recruta, então o card envelhece sem ninguém perceber: o
 * paciente é mandado a um estudo fechado. Agora é FAIL e trava o CI.
 *
 * Regra do revisor clínico (2026-08-04): nenhum estudo sem NCT presente e
 * verificado fica no Trial Matcher sem autorização explícita dele. Para
 * publicar uma exceção, liste o id do card em EXCECOES_SEM_NCT abaixo, com a
 * data e o motivo — a lista é o registro dessa autorização.
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

// Dois cards com o mesmo NCT significam ou estudo curado em duplicata, ou um
// deles carregando o registro errado. Os dois casos já aconteceram e passaram
// batido: o card do SUNRAY-02 ficou publicado com o NCT do SUNRAY-01 (e por
// tabela herdou os centros dele), e havia dois pares de cards duplicados. Nada
// disso quebra — o estudo só aparece duas vezes, ou aponta para o registro
// errado. Verificação local, sem rede, roda antes de qualquer fetch.
// Cards autorizados pelo revisor a ficar sem NCT. Vazio de propósito: cada
// entrada precisa da data e do motivo, e só o revisor clínico acrescenta.
// Formato: { id: 'meu-card', desde: '2026-08-04', motivo: '...' }
const EXCECOES_SEM_NCT = [];

function checarSemNct(trials) {
  const liberados = new Set(EXCECOES_SEM_NCT.map(e => e.id));
  return trials.filter(t => !/NCT\d{8}/.test(t.nct || '') && !liberados.has(t.id));
}

function checarNctRepetido(trials) {
  const porNct = new Map();
  for (const t of trials) {
    const n = (t.nct || '').match(/NCT\d{8}/)?.[0];
    if (!n) continue;
    if (!porNct.has(n)) porNct.set(n, []);
    porNct.get(n).push(t.nome || t.id || '?');
  }
  return [...porNct.entries()].filter(([, nomes]) => nomes.length > 1);
}

(async () => {
  const semNct = checarSemNct(trials);
  if (semNct.length) {
    console.error('\n--- FAIL: card sem NCT concreto ---');
    for (const t of semNct) console.error(`  ${t.nome || t.id || '?'} | nct: "${t.nct || ''}"`);
    console.error('\nSem NCT não dá para verificar se o estudo ainda recruta, e o');
    console.error('card envelhece sem ninguém notar. Ou o card sai, ou o revisor');
    console.error('clínico autoriza a exceção em EXCECOES_SEM_NCT (com data e motivo).');
    process.exit(1);
  }

  const repetidos = checarNctRepetido(trials);
  if (repetidos.length) {
    console.error('\n--- FAIL: NCT usado por mais de um card ---');
    for (const [nct, nomes] of repetidos) console.error(`  ${nct} -> ${nomes.join(', ')}`);
    console.error('\nCada NCT deve pertencer a um único card. Verifique se são');
    console.error('duplicatas do mesmo estudo ou se um deles está com o NCT errado.');
    process.exit(1);
  }

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
  // Só chega aqui quem está em EXCECOES_SEM_NCT — o resto já saiu por FAIL.
  if (notes.length) { console.error(`\n--- NOTE: ${notes.length} card(s) sem NCT autorizados pelo revisor ---`); notes.forEach(n => console.error(`  ${n.nome} | "${n.nct}"`)); }
  console.error(`\nRESULT  OK=${results.length - fails.length - warns.length}  WARN=${warns.length}  FAIL=${fails.length}  (de ${results.length} c/ NCT; +${notes.length} sem NCT)`);
  if (warns.length) { console.error('\n--- WARN (revisar — recrutamento/Brasil/intervenção) ---'); warns.forEach(r => r.flags.forEach(f => console.error(`  ${r.nome} | ${r.nct} | ${f.m}`))); }
  if (fails.length) { console.error('\n--- FAIL (link inválido/inconsistente) ---'); fails.forEach(r => r.flags.filter(f => f.lvl === 'FAIL').forEach(f => console.error(`  ${r.nome} | ${r.nct} | ${f.m}`))); }
  if (jsonOut) fs.writeFileSync(jsonOut, JSON.stringify({ results, notes }, null, 1));
  process.exit((fails.length + (warnFail ? warns.length : 0)) ? 1 : 0);
})();
