// Review Center — interface local. Todo conteúdo dos outputs entra no DOM só como texto (textContent).
"use strict";

const E = { itens: [], meta: null, filtrados: [], atual: null };
const ROTULO = { PENDING: "PENDENTE", STALE: "STALE", APPROVE: "APPROVE", REJECT: "REJECT", DEFER: "DEFER" };
const TIPO = {
  delta: "Delta (trecho do card)", delta_hr: "Delta · revisão humana", update_sem_itens: "UPDATE sem trecho proposto",
  add_secondary: "Candidata a card secundário", human_review: "Revisão humana",
};
const $ = (id) => document.getElementById(id);

function el(tag, cls, texto) {
  const n = document.createElement(tag);
  if (cls) n.className = cls;
  if (texto !== undefined && texto !== null) n.textContent = String(texto);
  return n;
}
function chip(cls, texto) { return el("span", "chip " + cls, texto); }
function urlPubmed(pmid) { return /^\d{1,9}$/.test(String(pmid || "")) ? "https://pubmed.ncbi.nlm.nih.gov/" + pmid + "/" : null; }
function urlDoi(doi) {
  const d = String(doi || "");
  return /^10\.\d{4,9}\/\S+$/.test(d) ? "https://doi.org/" + d.split("/").map(encodeURIComponent).join("/") : null;
}
function link(url, texto) {
  if (!url) return el("span", "mono", texto || "—");
  const a = el("a", "mono", texto);
  a.href = url; a.target = "_blank"; a.rel = "noopener noreferrer";
  return a;
}
function pendente(it) { return it.status === "PENDING" || it.status === "STALE"; }

// ------------------------------------------------------------------ dados
async function carregar(manterId) {
  const r = await fetch("/api/items", { cache: "no-store" });
  const dados = await r.json();
  if (!r.ok) throw new Error(dados.erro || "falha ao carregar");
  E.itens = dados.itens; E.meta = dados.meta;
  const sel = $("f-bloco");
  if (sel.options.length === 1) {
    Object.keys(E.meta.blocos).forEach((b) => { const o = el("option", null, "Bloco " + b); o.value = b; sel.appendChild(o); });
  }
  aplicarFiltros(manterId || decodeURIComponent(location.hash.slice(1)));
}

function recontar() {
  const c = { PENDING: 0, STALE: 0, APPROVE: 0, REJECT: 0, DEFER: 0 };
  E.itens.forEach((i) => { c[i.status] += 1; });
  E.meta.contagens = c;
}

// ------------------------------------------------------------------ painel e filtros
function painel() {
  const c = E.meta.contagens, total = E.meta.total;
  const kpis = [["Total", total], ["Pendentes", c.PENDING + c.STALE], ["Aprovadas", c.APPROVE], ["Rejeitadas", c.REJECT],
    ["Adiadas", c.DEFER], ["Stale", c.STALE], ["Cards", E.meta.cards], ["Pacotes", E.meta.pacotes]];
  $("painel").replaceChildren(...kpis.map(([k, v]) => { const d = el("div", "kpi"); d.append(el("b", null, v), el("span", null, k)); return d; }));
  const feitas = c.APPROVE + c.REJECT + c.DEFER;
  $("barra").style.width = (total ? (100 * feitas / total) : 0).toFixed(1) + "%";
  $("progresso-txt").textContent = feitas + " / " + total + " revisadas · decisões em " + E.meta.arquivo_decisoes +
    (E.meta.orfas.length ? " · " + E.meta.orfas.length + " decisão(ões) sem item correspondente" : "");
}

function texto(it) {
  return [it.uid, it.trial, it.pmid, it.doi, it.title, it.field_path, it.relation, it.reason, it.current, it.proposed,
    it.human_review_reason, it.verifier_reason].filter(Boolean).join(" ").toLowerCase();
}

function aplicarFiltros(manterId) {
  const st = $("f-status").value, pac = $("f-pacote").value, ver = $("f-veredito").value, bl = $("f-bloco").value;
  const q = $("f-busca").value.trim().toLowerCase();
  E.filtrados = E.itens.filter((it) =>
    (!st || (st === "pendentes" ? pendente(it) : it.status === st)) && (!pac || it.pacote === pac) &&
    (!ver || it.verdict === ver) && (!bl || String(it.bloco) === bl) && (!q || texto(it).includes(q)));
  $("contagem-filtro").textContent = E.filtrados.length + " de " + E.itens.length + " itens";
  painel();
  lista();
  const alvo = E.filtrados.find((i) => i.decision_id === manterId) || E.filtrados[0] ||
    E.itens.find((i) => i.decision_id === manterId);       // o detalhe acompanha o filtro
  selecionar(alvo ? alvo.decision_id : null, false);
}

function lista() {
  const nav = $("lista");
  const grupos = [];
  E.filtrados.forEach((it) => {
    let g = grupos[grupos.length - 1];
    if (!g || g.uid !== it.uid) { g = { uid: it.uid, trial: it.trial, bloco: it.bloco, itens: [] }; grupos.push(g); }
    g.itens.push(it);
  });
  if (!grupos.length) { nav.replaceChildren(el("p", "vazio", "Nenhum item com estes filtros.")); return; }
  nav.replaceChildren(...grupos.map((g) => {
    const sec = el("section", "grupo");
    const h = el("h3", null, (g.trial || g.uid) + " ");
    h.append(el("small", null, g.uid + " · bloco " + g.bloco));
    sec.append(h);
    g.itens.forEach((it) => {
      const b = el("button", "linha");
      b.type = "button"; b.dataset.id = it.decision_id;
      b.addEventListener("click", () => selecionar(it.decision_id, true));
      const desc = it.field_path ? it.field_path + " · " + (it.current || it.human_review_reason || it.title || "") : (it.title || it.pub);
      const chips = el("span", "chips");
      chips.append(chip("v-" + it.verdict, it.verdict || "—"), chip("s-" + it.status, ROTULO[it.status]));
      b.append(chip("c-" + it.pacote, it.pacote.replace("_", " ")), el("span", "txt", desc), chips);
      sec.append(b);
    });
    return sec;
  }));
}

// ------------------------------------------------------------------ detalhe
function bloco(titulo, conteudo, cls) {
  const d = el("section", "bloco" + (cls ? " " + cls : ""));
  d.append(el("h4", null, titulo));
  const c = el("div", "conteudo");
  if (conteudo instanceof Node) c.append(conteudo); else c.textContent = conteudo == null || conteudo === "" ? "—" : String(conteudo);
  d.append(c);
  return d;
}
function meta(pares) {
  const dl = el("dl", "meta");
  pares.forEach(([k, v]) => {
    if (v === undefined) return;
    dl.append(el("dt", null, k));
    const dd = el("dd");
    if (v instanceof Node) dd.append(v); else dd.textContent = v == null || v === "" ? "—" : String(v);
    dl.append(dd);
  });
  return dl;
}
function evidencias(lista) {
  const f = document.createDocumentFragment();
  if (!lista || !lista.length) { f.append(el("p", "vazio", "Sem trecho-fonte registrado.")); return f; }
  lista.forEach((e) => {
    const d = el("div", "evid");
    d.append(el("div", null, e.snippet || "—"), el("div", "loc", [e.source_id, e.locator].filter(Boolean).join(" · ")));
    f.append(d);
  });
  return f;
}
function avisos(lista) {
  if (!lista || !lista.length) return el("span", "vazio", "Nenhum aviso.");
  const ul = el("ul", "avisos");
  lista.forEach((a) => ul.append(el("li", null, a)));
  return ul;
}
function veredictos(v) {
  const s = el("span", "cabeca");
  if (!v) return s;
  [["curator", v.curator], ["verifier", v.verifier], ["deterministic", v.deterministic], ["final", v.final]].forEach(([k, x]) => {
    if (x !== undefined) s.append(chip("v-" + x, k + ": " + (x || "—")));
  });
  return s;
}
function comparacao(c) {
  if (!c) return el("span", "vazio", "Sem tabela de comparação.");
  const t = el("table", "comp");
  Object.entries(c).forEach(([k, v]) => {
    const tr = el("tr");
    tr.append(el("td", null, k), el("td", null, (v && v.status ? v.status : "—") + (v && v.note ? " — " + v.note : "")));
    t.append(tr);
  });
  return t;
}
function publicacao(it) {
  const ids = el("span", "cabeca");
  ids.append(link(urlPubmed(it.pmid), it.pmid ? "PMID " + it.pmid : "sem PMID"), el("span", null, " · "),
    link(urlDoi(it.doi), it.doi ? "DOI " + it.doi : "sem DOI"));
  return ids;
}

function detalhe(it) {
  const art = $("detalhe");
  if (!it) { art.replaceChildren(el("p", "vazio", "Nenhum item selecionado.")); return; }
  const f = document.createDocumentFragment();
  const cab = el("div", "cabeca");
  cab.append(chip("c-" + it.pacote, it.pacote), chip("s-" + it.status, ROTULO[it.status]), chip("v-" + it.verdict, "veredito: " + (it.verdict || "—")),
    el("span", "registro", TIPO[it.tipo] + " · bloco " + it.bloco));
  f.append(cab, el("h2", null, it.trial || it.uid), el("p", "sub", it.uid));
  if (it.status === "STALE") f.append(el("div", "stale", "STALE: o conteúdo deste item mudou depois da decisão registrada. Revise de novo."));

  const comum = [["Publicação", it.title], ["Periódico / data", [it.journal, it.date].filter(Boolean).join(" · ")],
    ["Identificadores", publicacao(it)], ["Relação", [it.relation, it.temporal_marker].filter(Boolean).join(" · ")],
    ["Discovery", veredictos(it.discovery_verdicts)]];

  if (it.tipo === "delta" || it.tipo === "delta_hr") {
    f.append(meta([...comum, ["Campo", el("span", "mono", it.field_path)], ["Endpoint", it.endpoint],
      ["Delta", veredictos(it.delta_verdicts)], ["safe_delta", it.tipo === "delta_hr" ? "não se aplica (item de revisão humana, sem texto proposto)" : it.safe_delta ? "true — passou em todas as checagens" : "false — não passou em todas as checagens"]]));
    if (it.tipo === "delta") {
      f.append(bloco("Atual", it.current, "atual"), bloco("Proposto", it.proposed, "proposto"));
      f.append(bloco("Evidência (trecho literal)", evidencias(it.source)));
      f.append(bloco("Motivo do curator", it.delta_reason));
    } else {
      f.append(bloco("Dúvida objetiva (sem texto proposto)", it.human_review_reason));
      f.append(bloco("Evidência", evidencias(it.source)));
    }
    f.append(bloco("Verifier do delta", it.delta_verifier_reason), bloco("Avisos", avisos(it.avisos)));
    const det = el("details");
    det.append(el("summary", null, "Contexto: campo inteiro no data.js de hoje (somente leitura)"),
      bloco(it.field_path || "campo", it.campo_hoje));
    f.append(det);
  } else if (it.tipo === "update_sem_itens") {
    f.append(meta(comum));
    f.append(bloco("Nota do delta (nenhum trecho proposto)", it.notes_for_human), bloco("Evidência do discovery", evidencias(it.evidence)),
      bloco("Verifier do discovery", it.verifier_reason), bloco("Avisos", avisos(it.avisos)));
  } else if (it.tipo === "add_secondary") {
    f.append(el("div", "pergunta", "Esta publicação merece um card secundário próprio? (Aprovar não cria o card.)"));
    const sig = it.signature || {}, cmp = it.comparison || {};
    f.append(meta([["Estudo pai", (it.trial || "") + " · " + it.uid], ...comum,
      ["População", [sig.population, cmp.population && cmp.population.note].filter(Boolean).join(" — ")],
      ["Endpoint / análise", [sig.endpoint, sig.analysis_type, sig.analysis_set, cmp.endpoint && cmp.endpoint.note].filter(Boolean).join(" · ")]]));
    f.append(bloco("Motivo da proposta", it.reason), bloco("Evidência", evidencias(it.evidence)),
      bloco("Verifier", it.verifier_reason), bloco("Avisos", avisos(it.avisos)));
    const det = el("details");
    det.append(el("summary", null, "Comparação com a publicação representada"), comparacao(it.comparison));
    f.append(det);
  } else {
    f.append(meta([...comum, ["Ação original", it.acao_original], ["Origem", it.origin]]));
    f.append(bloco("Dúvida objetiva", it.reason), bloco("Verifier", it.verifier_reason),
      bloco("Conflitos e avisos", avisos(it.avisos)), bloco("Evidência", evidencias(it.evidence)));
    const det = el("details");
    det.append(el("summary", null, "Comparação com a publicação representada"), comparacao(it.comparison));
    f.append(det);
  }
  f.append(painelDecisao(it));
  art.replaceChildren(f);
  art.scrollTop = 0;
}

function painelDecisao(it) {
  const box = el("section", "decisao");
  const reg = it.registro;
  box.append(el("div", "registro", reg
    ? "Decisão registrada: " + reg.decision + " · " + reg.reviewed_at + " · revisão " + reg.revision + (it.status === "STALE" ? " · STALE" : "")
    : "Sem decisão registrada."));
  const com = el("textarea"); com.id = "comentario"; com.placeholder = "Comentário (opcional)"; com.maxLength = 4000;
  com.value = reg && reg.comment ? reg.comment : "";
  const bts = el("div", "botoes");
  [["APPROVE", "Aprovar"], ["REJECT", "Rejeitar"], ["DEFER", "Adiar"]].forEach(([d, rot]) => {
    const b = el("button", "btn " + d, rot + " (" + d + ")");
    b.type = "button";
    b.setAttribute("aria-pressed", reg && reg.decision === d && it.status !== "STALE" ? "true" : "false");
    b.addEventListener("click", () => decidir(it, d, com.value));
    bts.append(b);
  });
  const nav = el("div", "nav");
  [["← Anterior", () => mover(-1)], ["Próximo →", () => mover(1)], ["Próximo não revisado", proximoPendente]].forEach(([r, fn]) => {
    const b = el("button", "btn", r); b.type = "button"; b.addEventListener("click", fn); nav.append(b);
  });
  const msg = el("div", "msg"); msg.id = "msg";
  const acoes = el("div", "acoes");
  acoes.append(bts, nav);
  box.append(com, acoes, msg);
  return box;
}

// ------------------------------------------------------------------ navegação e decisão
function selecionar(id, rolar) {
  E.atual = id;
  document.querySelectorAll(".linha").forEach((b) => b.setAttribute("aria-current", b.dataset.id === id ? "true" : "false"));
  const it = E.itens.find((i) => i.decision_id === id);
  if (id && location.hash.slice(1) !== id) history.replaceState(null, "", "#" + id);
  detalhe(it);
  if (rolar !== false) {
    const b = document.querySelector('.linha[aria-current="true"]');
    if (b) b.scrollIntoView({ block: "nearest" });
  }
}
function mover(passo) {
  const i = E.filtrados.findIndex((x) => x.decision_id === E.atual);
  const j = Math.min(Math.max(i + passo, 0), E.filtrados.length - 1);
  if (E.filtrados[j]) selecionar(E.filtrados[j].decision_id, true);
}
function proximoPendente() {
  const base = E.filtrados.length ? E.filtrados : E.itens;
  const i = base.findIndex((x) => x.decision_id === E.atual);
  for (let k = 1; k <= base.length; k++) {
    const it = base[(i + k) % base.length];
    if (pendente(it)) { selecionar(it.decision_id, true); return; }
  }
  const m = $("msg"); if (m) { m.className = "msg ok"; m.textContent = "Não há itens pendentes neste filtro."; }
}
async function decidir(it, decisao, comentario) {
  const m = $("msg");
  m.className = "msg"; m.textContent = "Salvando…";
  try {
    const r = await fetch("/api/decision", {
      method: "POST", headers: { "Content-Type": "application/json", "X-Review-Center": "1" },
      body: JSON.stringify({ decision_id: it.decision_id, fingerprint: it.fingerprint, decision: decisao, comment: comentario }),
    });
    const d = await r.json();
    if (!r.ok) {
      if (r.status === 409) { await carregar(it.decision_id); }
      const m2 = $("msg"); m2.className = "msg erro"; m2.textContent = d.erro || "Falha ao salvar.";
      return;
    }
    it.status = d.status;
    it.registro = { decision: d.registro.decision, comment: d.registro.comment, reviewed_at: d.registro.reviewed_at, revision: d.registro.revision };
    recontar(); painel(); lista(); selecionar(it.decision_id, false);
    const m3 = $("msg"); m3.className = "msg ok"; m3.textContent = "Salvo: " + decisao + ". Nada foi aplicado ao Database.";
  } catch (e) {
    m.className = "msg erro"; m.textContent = "Falha ao salvar: " + e.message;
  }
}

["f-status", "f-pacote", "f-veredito", "f-bloco"].forEach((id) => $(id).addEventListener("change", () => aplicarFiltros(E.atual)));
$("f-busca").addEventListener("input", () => aplicarFiltros(E.atual));
carregar().catch((e) => { $("detalhe").replaceChildren(el("p", "msg erro", "Falha ao carregar: " + e.message)); });
