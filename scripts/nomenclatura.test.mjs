// Nomenclatura de radiofármacos: todo nome exibido leva o número de massa
// (¹⁷⁷Lu-PSMA, nunca Lu-PSMA). Pedido do Dr. Marcos em 17/nov/2026.
//   node --test scripts/nomenclatura.test.mjs
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, readdirSync, statSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const RAIZ = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
const LIGANTES = /(?:Lu|Ac)-(?:PSMA|DOTA-?TATE|DOTATOC|DOTA-Tyr|NeoB|FAP)|Ga-(?:DOTA-?TATE|DOTATOC|DOTANOC|PSMA|FAPI|PentixaFor|NeoB)|Tc-(?:MDP|MAA|MIBI|DTPA|MAG3|DMSA|HMPAO|IDA|Technegas)/g;
const COMPLETO = /(<span class="iso-up"[^>]*>\d+<\/span>|<sup>\d+m?<\/sup>|&#\d+;|\(\d{2,3}m?\)\s?|[0-9⁰¹²³⁴⁵⁶⁷⁸⁹ᵐ\])A-Za-z\-/_.[])$/;
const TITULO = /"(titulo_full|title|titulo_artigo|citation|cit)"\s*:\s*"[^"]*$/;
function incompletos(texto) {
  const achados = [];
  for (const m of texto.matchAll(LIGANTES)) {
    const antes = texto.slice(Math.max(0, m.index - 60), m.index);
    if (COMPLETO.test(antes)) continue;
    const linha = texto.slice(texto.lastIndexOf('\n', m.index) + 1, m.index);
    if (TITULO.test(linha)) continue;
    achados.push(texto.slice(Math.max(0, m.index - 30), m.index + 25).replace(/\s+/g, ' '));
  }
  return achados;
}

function arquivos(dir, fora = new Set(['vendor', 'data', 'fonts', 'img', 'icons', 'splash'])) {
  const out = [];
  for (const nome of readdirSync(dir)) {
    const p = path.join(dir, nome);
    if (statSync(p).isDirectory()) { if (!fora.has(nome)) out.push(...arquivos(p, fora)); }
    else if (/\.(html|js)$/.test(nome) && nome !== 'sw.js') out.push(p);
  }
  return out;
}

test('nenhum radiofármaco sem número de massa nas páginas e nos dados exibidos', () => {
  const lista = [
    ...readdirSync(RAIZ).filter((f) => f.endsWith('.html')).map((f) => path.join(RAIZ, f)),
    ...arquivos(path.join(RAIZ, 'assets', 'js')),
    ...arquivos(path.join(RAIZ, 'assets', 'lang')),
  ];
  const erros = [];
  for (const f of lista) for (const t of incompletos(readFileSync(f, 'utf8'))) erros.push(`${path.relative(RAIZ, f)}: …${t}…`);
  assert.deepEqual(erros, []);
});

test('Explorer: nome do radiofármaco com número de massa quando o elemento é inequívoco', () => {
  const d = JSON.parse(readFileSync(path.join(RAIZ, 'assets', 'data', 'explorer.json'), 'utf8'));
  const ruins = d.trials.filter((t) => /^(Lu|Ac|Sm|Ra|F)-[A-Za-z]|^Ga-(DOTA|PSMA|FAPI|Pentixa|NeoB)/i.test(t.drug)).map((t) => `${t.nct} ${t.drug}`);
  assert.deepEqual(ruins, []);
});
