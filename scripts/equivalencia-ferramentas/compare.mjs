// Compara dois snapshots campo a campo. Sai com código 1 se houver QUALQUER
// diferença funcional. `sectionText` e `i18n` podem mudar de propósito
// quando a UI nova é inserida FORA das seções — por isso são reportados à
// parte e só contam como falha se a seção afetada for uma ferramenta.
import fs from 'node:fs';
const [, , A, B] = process.argv;
const a = JSON.parse(fs.readFileSync(A)), b = JSON.parse(fs.readFileSync(B));
let falhas = 0;
const ok = (c, msg) => { console.log(`${c ? '  ✓' : '  ✗'} ${msg}`); if (!c) falhas++; };
const eq = (x, y) => JSON.stringify(x) === JSON.stringify(y);

console.log('== dados (JSON completo de cada base) ==');
for (const k of ['TNM', 'CTCAE', 'CRIT']) ok(eq(a.data[k], b.data[k]), `${k}_DATA idêntico (${a.data[k]?.len} chars)`);
for (const k of ['TNM', 'CTCAE', 'CRIT']) ok(eq(a.keys[k], b.keys[k]), `${k}: mesmas ${a.keys[k]?.length} chaves, mesma ordem`);

console.log('\n== estrutura ==');
ok(eq(a.sections, b.sections), `mesmas ${a.sections.length} seções, mesma ordem`);
ok(eq(a.hub, b.hub), `mesmos ${a.hub.length} cards do hub (href + texto)`);
ok(eq(a.globals, b.globals), `mesmos tipos para ${a.globals.length} globais: ${b.globals.map(g => g[0] + '=' + g[1]).join(', ')}`);
const secDiff = a.sections.filter(id => a.sectionText[id] !== b.sectionText[id]);
ok(secDiff.length === 0, `texto de todas as seções de ferramenta idêntico${secDiff.length ? ' — DIFEREM: ' + secDiff : ''}`);

console.log('\n== modais (clique no botão real) ==');
const ka = Object.keys(a.modals), kb = Object.keys(b.modals);
ok(eq(ka, kb), `mesmos ${ka.length} botões de abertura`);
const md = ka.filter(k => !eq(a.modals[k], b.modals[k]));
ok(md.length === 0, `título, referência e corpo idênticos nos ${ka.length} modais${md.length ? ' — DIFEREM: ' + md.join(', ') : ''}`);

console.log('\n== calculadoras (resultado HTML + classe CSS, por combinação de entradas) ==');
const bat = (nome, xa, xb) => {
  const n = Math.max(xa.length, xb.length);
  const dif = [];
  for (let i = 0; i < n; i++) if (!eq(xa[i], xb[i])) dif.push(i);
  ok(dif.length === 0 && xa.length === xb.length, `${nome}: ${xb.length} de ${xa.length} combinações idênticas${dif.length ? ` — ${dif.length} DIFEREM (1ª: ${JSON.stringify(xa[dif[0]]).slice(0, 160)})` : ''}`);
};
bat('Dose diagnóstica', a.calc.dose, b.calc.dose);
bat('Decaimento PET/CT', a.calc.decay, b.calc.decay);
ok(eq(a.calc.decayPatients, b.calc.decayPatients), 'Decaimento com pesos individuais: idêntico');
bat('Função renal', a.calc.renal, b.calc.renal);
bat('ALBI', a.hcc.albi, b.hcc.albi);
bat('MELD', a.hcc.meld, b.hcc.meld);
bat('Child-Pugh', a.hcc.cp, b.hcc.cp);

console.log('\n== i18n ==');
ok(a.i18n.mudou === b.i18n.mudou, `troca PT→EN continua funcionando (mudou=${b.i18n.mudou})`);
console.log(`    textos de hero+hub ${a.i18n.pt === b.i18n.pt && a.i18n.en === b.i18n.en ? 'idênticos' : 'diferentes (esperado se a UI nova estiver dentro de .tools-hub/.ft-hero)'}`);

console.log('\n== erros de página ==');
for (const k of Object.keys(a.errors)) {
  const novos = b.errors[k].filter(e => !a.errors[k].includes(e));
  ok(novos.length === 0, `${k}: nenhum erro novo${novos.length ? ' — NOVOS: ' + novos.join(' | ') : ''}`);
}

const total = a.calc.dose.length + a.calc.decay.length + 1 + a.calc.renal.length + a.hcc.albi.length + a.hcc.meld.length + a.hcc.cp.length;
console.log(`\n${falhas ? '✗ ' + falhas + ' FALHA(S)' : '✓ EQUIVALÊNCIA TOTAL'} — ${ka.length} modais + ${total.toLocaleString('pt-BR')} avaliações de calculadora`);
process.exit(falhas ? 1 : 0);
