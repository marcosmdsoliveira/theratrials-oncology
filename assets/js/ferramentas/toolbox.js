/* ============================================================================
 * ferramentas/toolbox.js — acesso rápido às ferramentas clínicas
 *
 *   • busca por nome, sigla, sinônimo ou finalidade (sem acento, várias palavras)
 *   • filtros por finalidade clínica
 *   • link direto para cada ferramenta: #recist, #deauville, #ajcc-prostata,
 *     #ctcae-hema, #ckd-epi … — outras páginas podem abrir a ferramenta certa
 *   • "/" ou Ctrl/Cmd+K focam a busca de qualquer ponto da página
 *
 * Três decisões que protegem o que já funciona:
 *
 * 1. Para abrir um modal, este arquivo CLICA NO BOTÃO ORIGINAL. Não existe
 *    segunda implementação de abertura: busca, link direto e clique manual
 *    passam pelo mesmo openTNM/openCTCAE/openCrit.
 *
 * 2. O índice é lido do DOM VIVO a cada uso, não de uma lista fixa. No app
 *    iOS o native-guards.js remove #dose-calc e #decay-calc (Guideline 1.4.1);
 *    lendo o DOM, elas somem da busca e dos links sem nenhum caso especial.
 *
 * 3. Nada aqui altera fórmula, dado ou texto de ferramenta. A única coisa
 *    editorial é a tabela CATS/KW abaixo: a que finalidade cada ferramenta
 *    atende e por quais sinônimos ela é procurada.
 * ==========================================================================*/
(function () {
  'use strict';

  // ── Finalidade clínica de cada ferramenta (chips) ─────────────────────────
  // Uma ferramenta pode ter várias. Charlson fica sem chip de propósito: é
  // índice de comorbidade, e rotulá-lo "Performance" seria impreciso — segue
  // encontrável pela busca e pelo grupo "Oncologia clínica".
  var CATS = {
    'ajcc-hcc': 'est fig',
    'ctcae-renal': 'tox renal', 'ctcae-hepato': 'tox fig', 'ctcae-radio': 'tox tera',
    'promise': 'est pet tera', 'psma-rads': 'pet tera', 'primary': 'pet',
    'recip': 'resp pet tera', 'pcwg': 'resp',
    'gleason': 'pat', 'isup': 'pat', 'damico': 'est',
    'percist': 'resp pet', 'eortc-pet': 'resp pet', 'deauville': 'resp pet', 'lugano': 'est resp pet',
    'krenning': 'pet tera', 'netpet': 'pet tera', 'sstr-rads': 'pet tera',
    'who-net': 'pat', 'ki67': 'pat', 'enets': 'est',
    'irecist': 'resp', 'irrecist': 'resp', 'percimt': 'resp pet', 'impercist': 'resp pet',
    'recist': 'resp', 'mrecist': 'resp', 'choi': 'resp',
    'bclc': 'est fig', 'child-pugh': 'fig calc', 'albi': 'fig calc', 'meld': 'fig calc',
    'li-rads': 'fig', 'lr-tr': 'resp fig', 'easl': 'resp fig', 'mrecist-hcc': 'resp fig',
    'ecog': 'perf', 'karnofsky': 'perf', 'ctcae-link': 'tox',
    'dose-calc': 'calc pet', 'decay-calc': 'calc pet',
    'ckd-epi': 'calc renal', 'cockcroft-gault': 'calc renal', 'mdrd': 'calc renal'
  };
  // Prefixos: todo ajcc-* é estadiamento; todo ctcae-* é toxicidade.
  function catsOf(slug) {
    var c = (CATS[slug] || '').split(' ').filter(Boolean);
    if (/^ajcc-/.test(slug) && c.indexOf('est') < 0) c.push('est');
    if (/^ctcae-/.test(slug) && c.indexOf('tox') < 0) c.push('tox');
    return c;
  }

  // Ferramentas com cálculo interativo recebem a etiqueta "Calculadora".
  var CALC = { 'child-pugh': 1, 'albi': 1, 'meld': 1, 'dose-calc': 1, 'decay-calc': 1,
               'ckd-epi': 1, 'cockcroft-gault': 1, 'mdrd': 1 };

  // ── Como cada ferramenta é procurada (siglas, sinônimos, PT e EN) ─────────
  var KW = {
    'ajcc': 'tnm estadiamento staging ajcc 8a 9a edicao',
    'ajcc-prostata': 'prostata prostate psa grupo prognostico',
    'ajcc-mama': 'mama breast her2 receptor hormonal',
    'ajcc-nsclc': 'pulmao lung nsclc nao pequenas celulas',
    'ajcc-hcc': 'hepatocarcinoma chc hcc figado liver',
    'ajcc-net': 'neuroendocrino net gep pancreas intestino',
    'ajcc-rcc': 'rim renal kidney carcinoma de celulas claras ccrcc',
    'ajcc-crc': 'colorretal colon reto crc colorectal',
    'ajcc-gastric': 'estomago gastrico gastric jeg gej juncao',
    'ajcc-bexiga': 'bexiga urotelial bladder',
    'ajcc-tireoide': 'tireoide thyroid papilifero folicular',
    'ajcc-hnscc': 'cabeca pescoco head neck orofaringe hpv laringe',
    'ajcc-esofago': 'esofago esophagus juncao esofagogastrica',
    'ajcc-pancreas': 'pancreas adenocarcinoma',
    'ajcc-linfoma': 'linfoma lymphoma ann arbor lugano',
    'ajcc-melanoma': 'melanoma pele skin breslow',
    'ctcae': 'toxicidade efeitos adversos eventos adversos adverse events grau',
    'ctcae-hema': 'hematologica neutropenia plaquetopenia trombocitopenia anemia mielotoxicidade',
    'ctcae-gi': 'gastrointestinal diarreia nausea vomito mucosite',
    'ctcae-hepato': 'hepatotoxicidade transaminases bilirrubina tgo tgp ast alt',
    'ctcae-renal': 'nefrotoxicidade creatinina lesao renal aguda lra',
    'ctcae-irae': 'imunomediado irae pneumonite colite tireoidite hepatite imunoterapia',
    'ctcae-derm': 'dermatologico pele rash dermatite prurido',
    'ctcae-radio': 'radioligante xerostomia boca seca lutecio lu psma prrt',
    'ctcae-crs': 'crs icans liberacao de citocinas car t biespecifico neurotoxicidade',
    'ctcae-sist': 'sistemico geral fadiga febre',
    'dose-calc': 'dose atividade mci mbq pediatrico adulto eanm north american consensus fdg ga68 diagnostico',
    'decay-calc': 'decaimento meia vida agenda fracionamento f18 ga68 c11 fluor galio residual',
    'psma': 'psma prostata prostate lutecio',
    'promise': 'mitnm mipsma psma pet laudo relatorio',
    'psma-rads': 'psma rads laudo lesao indeterminada',
    'primary': 'primary score biopsia intraprostatico cspca',
    'recip': 'resposta psma lutecio lu psma pluvicto vtv volume tumoral',
    'pcwg': 'pcwg3 pcwg4 progressao psa mcrpc regra 2 2 cintilografia ossea',
    'gleason': 'gleason histologia padrao',
    'isup': 'isup grade group grupo de grau',
    'damico': 'damico d amico risco localizado',
    'petct': 'pet ct fdg resposta metabolica',
    'percist': 'percist fdg sul sulpeak resposta metabolica',
    'eortc-pet': 'eortc suvmax resposta metabolica',
    'deauville': 'deauville 5ps linfoma lymphoma hodgkin pet interim',
    'lugano': 'lugano linfoma lymphoma estadiamento resposta ann arbor',
    'tne': 'neuroendocrino net tne neuroendocrine',
    'krenning': 'krenning octreoscan sstr somatostatina prrt lutathera dotatate captacao',
    'netpet': 'netpet fdg dotatate dual tracer',
    'sstr-rads': 'sstr rads somatostatina laudo',
    'who-net': 'oms who grau grade net g1 g2 g3 carcinoma neuroendocrino',
    'ki67': 'ki67 ki 67 indice proliferativo mitoses',
    'enets': 'enets tnm neuroendocrino',
    'imuno': 'imunoterapia immunotherapy checkpoint',
    'irecist': 'irecist imunoterapia pseudoprogressao iupd icpd',
    'irrecist': 'irrecist imunoterapia',
    'percimt': 'percimt imunoterapia pet',
    'impercist': 'impercist imunoterapia pet',
    'anatomica': 'resposta anatomica tc rm',
    'recist': 'recist 1 1 lesao alvo tumor solido resposta anatomica tc',
    'mrecist': 'mrecist realce arterial viavel',
    'choi': 'choi gist densidade hounsfield imatinibe',
    'hcc': 'chc hepatocarcinoma hcc radioembolizacao y90 tare figado liver',
    'bclc': 'bclc barcelona estadiamento chc',
    'child-pugh': 'child pugh cirrose reserva hepatica',
    'albi': 'albi albumina bilirrubina funcao hepatica y90',
    'meld': 'meld meld na meld 3 0 transplante cirrose sodio',
    'li-rads': 'lirads li rads nodulo hepatico',
    'lr-tr': 'lr tr lirads resposta tratamento locorregional',
    'easl': 'easl necrose resposta',
    'mrecist-hcc': 'mrecist chc realce arterial',
    'clinica': 'oncologia clinica',
    'ecog': 'ecog performance status ps zubrod',
    'karnofsky': 'karnofsky kps performance status',
    'ctcae-link': 'ctcae nci eventos adversos toxicidade',
    'charlson': 'charlson comorbidade comorbidity cci',
    'renal': 'funcao renal kidney tfg gfr clearance creatinina rim',
    'ckd-epi': 'ckd epi 2021 tfg gfr egfr filtracao glomerular creatinina kdigo estagio drc',
    'cockcroft-gault': 'cockcroft gault clearance de creatinina clcr crcl ajuste de dose',
    'mdrd': 'mdrd tfg gfr'
  };

  // Chips, na ordem em que aparecem.
  var CHIPS = [
    ['est', 'fr.tbChEst', 'Estadiamento'], ['resp', 'fr.tbChResp', 'Resposta'],
    ['pet', 'fr.tbChPet', 'PET/CT'], ['tera', 'fr.tbChTera', 'Teranóstico'],
    ['calc', 'fr.tbChCalc', 'Calculadoras'], ['tox', 'fr.tbChTox', 'Toxicidade'],
    ['perf', 'fr.tbChPerf', 'Performance'], ['renal', 'fr.tbChRenal', 'Função renal'],
    ['fig', 'fr.tbChFig', 'Fígado'], ['pat', 'fr.tbChPat', 'Patologia']
  ];

  // Subcalculadoras renais: a seção #renal calcula as três ao mesmo tempo, a
  // partir dos mesmos campos. O link direto leva à seção e destaca o card.
  var RENAL = [
    ['ckd-epi', 'CKD-EPI 2021', 'ckdepi-val'],
    ['cockcroft-gault', 'Cockcroft-Gault', 'cg-val'],
    ['mdrd', 'MDRD', 'mdrd-val']
  ];

  var OPENERS = { openTNM: 'ajcc-', openCTCAE: 'ctcae-', openCrit: '' };
  var TAGS = { openTNM: 'TNM', openCTCAE: 'CTCAE' };

  // ── utilitários ───────────────────────────────────────────────────────────
  function T(key, fb) {
    try { var v = window.t ? window.t(key, fb) : fb; return (v && v !== key) ? v : fb; } catch (e) { return fb; }
  }
  function norm(s) {
    return String(s || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '')
      .replace(/[^a-z0-9]+/g, ' ').trim();
  }
  function text(el) { return el ? el.textContent.replace(/\s+/g, ' ').trim() : ''; }
  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  var reduced = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  var coarse = window.matchMedia && matchMedia('(pointer: coarse)').matches;

  function parseOpener(btn) {
    var m = /^\s*(openTNM|openCTCAE|openCrit)\(\s*'([^']+)'\s*\)\s*;?\s*$/.exec(btn.getAttribute('onclick') || '');
    return m ? { fn: m[1], key: m[2], slug: OPENERS[m[1]] + m[2] } : null;
  }

  function setHash(slug) {
    try { history.replaceState(history.state, '', location.pathname + location.search + '#' + slug); } catch (e) {}
  }

  // ── índice, lido do DOM vivo ──────────────────────────────────────────────
  function buildIndex() {
    var out = [];
    var secs = document.querySelectorAll('section.tool[id]');
    Array.prototype.forEach.call(secs, function (sec, si) {
      var gid = sec.id;
      var gtitle = text(sec.querySelector('.tool-head h2')) || gid;
      var color = getComputedStyle(sec).getPropertyValue('--tool-accent').trim() || '#FF8400';
      var btns = sec.querySelectorAll('button[onclick^="open"]');
      var isCalc = !!CALC[gid];

      out.push(entry({ slug: gid, kind: isCalc ? 'calc' : 'group', title: gtitle, meta: '',
        group: gid, gtitle: gtitle, color: color, order: si * 1000, count: btns.length,
        tag: isCalc ? 'calc' : '' }));

      Array.prototype.forEach.call(btns, function (b, bi) {
        var p = parseOpener(b);
        if (!p) return;
        out.push(entry({ slug: p.slug, kind: 'modal', el: b,
          title: text(b.querySelector('.tnm-card-title')) || p.key,
          meta: text(b.querySelector('.tnm-card-ed')),
          tag: TAGS[p.fn] || (CALC[p.slug] ? 'calc' : ''),
          group: gid, gtitle: gtitle, color: color, order: si * 1000 + bi + 1 }));
      });

      if (gid === 'renal') RENAL.forEach(function (r, ri) {
        if (!document.getElementById(r[2])) return;
        out.push(entry({ slug: r[0], kind: 'calc', title: r[1], meta: gtitle, flash: r[2],
          tag: 'calc', group: gid, gtitle: gtitle, color: color, order: si * 1000 + 900 + ri }));
      });
    });
    // Contagem por grupo a partir do índice pronto — inclui as subcalculadoras
    // renais, que não são botões de modal.
    out.forEach(function (g) {
      if (g.kind === 'group') g.count = out.filter(function (x) { return x.group === g.slug && x !== g; }).length;
    });
    return out;
  }
  // A finalidade também é termo de busca: quem digita "fígado" ou "toxicity"
  // precisa achar as mesmas ferramentas que o chip correspondente mostra.
  var CAT_WORDS = {
    est: 'estadiamento staging', resp: 'resposta response', pet: 'pet ct',
    tera: 'teranostico theranostics radioligante', calc: 'calculadora calculator',
    tox: 'toxicidade toxicity', perf: 'performance', renal: 'funcao renal renal function rim kidney',
    fig: 'figado liver hepatico', pat: 'patologia pathology histologia'
  };
  function entry(e) {
    e.cats = catsOf(e.slug);
    e._t = norm(e.title);
    e._tq = e._t.replace(/ /g, '');
    e._k = norm((KW[e.slug] || '') + ' ' + (e.tag === 'calc' ? '' : e.tag) + ' ' + e.slug + ' ' +
      e.cats.map(function (c) { return CAT_WORDS[c] || ''; }).join(' '));
    e._all = norm([e.title, e.meta, e.gtitle, KW[e.slug] || '', e.tag, e.slug].join(' '));
    e._allq = e._all.replace(/ /g, '');
    // Grupos só entram em filtro de chip quando o próprio grupo é a ferramenta.
    e.isTool = e.kind !== 'group';
    return e;
  }
  function find(slug) {
    var idx = buildIndex();
    for (var i = 0; i < idx.length; i++) if (idx[i].slug === slug) return idx[i];
    return null;
  }

  // ── busca e ranqueamento ──────────────────────────────────────────────────
  // Toda palavra digitada precisa casar em algum lugar (E lógico); o peso
  // favorece início de título, depois início de palavra, sinônimo e meta.
  function score(e, toks) {
    var total = 0;
    for (var i = 0; i < toks.length; i++) {
      var tk = toks[i], best = 0;
      if (e._t.indexOf(tk) === 0) best = 12;
      else if ((' ' + e._t).indexOf(' ' + tk) >= 0) best = 8;
      else if (e._tq.indexOf(tk) >= 0) best = 6;
      else if ((' ' + e._k).indexOf(' ' + tk) >= 0) best = 4;
      else if (e._all.indexOf(tk) >= 0 || e._allq.indexOf(tk) >= 0) best = 2;
      if (!best) return 0;
      total += best;
    }
    return total - (e.kind === 'group' ? 1 : 0);
  }
  function query(idx, q, chip) {
    var toks = norm(q).split(' ').filter(Boolean);
    var res = [];
    idx.forEach(function (e) {
      if (chip && (!e.isTool || e.cats.indexOf(chip) < 0)) return;
      var s = toks.length ? score(e, toks) : 1;
      if (s > 0) res.push({ e: e, s: s });
    });
    res.sort(function (a, b) { return (b.s - a.s) || (a.e.order - b.e.order); });
    return res.map(function (r) { return r.e; });
  }

  // ── ação: levar o usuário até a ferramenta ────────────────────────────────
  var lastGroup = null;

  function activate(e) {
    closePanel();
    if (e.kind === 'modal') {
      // Rola até o grupo ANTES de abrir: ao fechar o modal, o usuário já está
      // no contexto da ferramenta, não no topo da página.
      var sec = document.getElementById(e.group);
      if (sec) sec.scrollIntoView({ block: 'start' });
      e.el.click();
      return;
    }
    // Grupo, calculadora de página ou subcalculadora renal: o alvo é sempre a
    // seção (para grupos, e.group === e.slug).
    var target = document.getElementById(e.group);
    if (!target) return;
    target.scrollIntoView({ behavior: reduced ? 'auto' : 'smooth', block: 'start' });
    setHash(e.slug);
    if (e.flash) {
      var v = document.getElementById(e.flash);
      var card = v && v.parentElement && v.parentElement.parentElement;
      if (card) {
        card.classList.remove('ftb-flash'); void card.offsetWidth; card.classList.add('ftb-flash');
        setTimeout(function () { card.classList.remove('ftb-flash'); }, 2000);
      }
    }
    // Calculadora: foco no primeiro campo. Não em tela de toque — lá o foco
    // abriria o teclado e esconderia justamente o resultado.
    if (e.kind === 'calc' && !coarse) {
      var f = target.querySelector('input:not([type="hidden"]), select');
      if (f) setTimeout(function () { f.focus({ preventScroll: true }); }, reduced ? 0 : 450);
    }
  }

  // Link direto na chegada e em mudanças de hash. Âncoras que já existem no
  // DOM (as 12 seções) continuam com o comportamento nativo do navegador.
  function resolveHash() {
    var id;
    try { id = decodeURIComponent((location.hash || '').slice(1)); } catch (e) { return; }
    if (!id || document.getElementById(id)) return;
    var e = find(id);
    if (e) activate(e);
  }

  // ── UI ────────────────────────────────────────────────────────────────────
  var root, bar, input, panel, clearBtn, chipsInline;
  var state = { q: '', chip: null, list: [], active: -1, open: false };

  function chipHTML(inPanel) {
    return CHIPS.map(function (c) {
      return '<button type="button" class="ftb-chip" data-chip="' + c[0] + '" aria-pressed="' +
        (state.chip === c[0]) + '"' + (inPanel ? ' tabindex="-1"' : '') + '>' + esc(T(c[1], c[2])) + '</button>';
    }).join('');
  }
  function syncChips() {
    document.querySelectorAll('.ftb-chip[data-chip]').forEach(function (b) {
      b.setAttribute('aria-pressed', String(b.getAttribute('data-chip') === state.chip));
    });
  }

  function optHTML(e, i, agrupado) {
    var tag = '';
    if (e.tag === 'calc') tag = '<span class="ftb-tag is-calc">' + esc(T('fr.tbCalc', 'Calculadora')) + '</span>';
    else if (e.tag) tag = '<span class="ftb-tag">' + esc(e.tag) + '</span>';
    else if (e.kind === 'group') tag = '<span class="ftb-tag">' + e.count + ' ' + esc(e.count === 1 ? T('fr.tbTool', 'ferramenta') : T('fr.tbTools', 'ferramentas')) + '</span>';
    var meta = e.kind === 'group' ? '' : [e.meta, agrupado ? '' : e.gtitle].filter(function (x, k, a) { return x && a.indexOf(x) === k; }).join(' · ');
    return '<div class="ftb-opt" role="option" id="ftb-opt-' + i + '" data-i="' + i + '" aria-selected="false" style="--c:' + esc(e.color) + '">' +
      '<span class="ftb-dot" aria-hidden="true"></span><span class="ftb-t">' + esc(e.title) + '</span>' + tag +
      (meta ? '<span class="ftb-m">' + esc(meta) + '</span>' : '') + '</div>';
  }

  function render() {
    var idx = buildIndex();
    var html = '<div class="ftb-pchips" role="group" aria-label="' + esc(T('fr.tbChipsAria', 'Filtrar por finalidade')) + '">' + chipHTML(true) + '</div>';
    var list = [];

    if (!state.q && !state.chip) {
      // Sem busca: índice dos grupos — navegação pela página longa.
      list = idx.filter(function (e) { return e.slug === e.group; });
      html += '<div class="ftb-h">' + esc(T('fr.tbGroups', 'Ir para o grupo')) + '</div>';
      html += list.map(function (e, i) { return optHTML(e, i); }).join('');
      if (!coarse) html += '<div class="ftb-hint">' + T('fr.tbHint', 'Dica: <kbd>/</kbd> abre a busca de qualquer ponto da página.') + '</div>';
    } else {
      list = query(idx, state.q, state.chip);
      var chipLabel = state.chip ? T(CHIPS.filter(function (c) { return c[0] === state.chip; })[0][1],
        CHIPS.filter(function (c) { return c[0] === state.chip; })[0][2]) : '';
      html += '<div class="ftb-status"><span>' + esc(chipLabel || T('fr.tbResults', 'Resultados')) + '</span><span>' +
        list.length + ' ' + esc(list.length === 1 ? T('fr.tbTool', 'ferramenta') : T('fr.tbTools', 'ferramentas')) + '</span></div>';
      if (!list.length) {
        html += '<div class="ftb-empty"><strong>' + esc(T('fr.tbEmpty', 'Nenhuma ferramenta encontrada.')) + '</strong><br>' +
          esc(T('fr.tbEmptyHint', 'Tente o nome da escala (ex.: RECIST, Deauville, CKD-EPI) ou escolha uma finalidade.')) + '</div>';
      } else if (!state.q) {
        // Só chip: agrupado por grupo, na ordem da página — mais fácil de varrer.
        var cur = null, parts = [];
        list.forEach(function (e, i) {
          if (e.group !== cur) { cur = e.group; parts.push('<div class="ftb-h">' + esc(e.gtitle) + '</div>'); }
          parts.push(optHTML(e, i, true));
        });
        html += parts.join('');
      } else {
        html += list.map(function (e, i) { return optHTML(e, i); }).join('');
      }
    }
    panel.innerHTML = html;
    state.list = list;
    setActive(list.length ? 0 : -1);
  }

  function setActive(i) {
    state.active = i;
    var opts = panel.querySelectorAll('.ftb-opt');
    opts.forEach(function (o) { o.setAttribute('aria-selected', String(+o.getAttribute('data-i') === i)); });
    if (i >= 0 && opts[i]) {
      input.setAttribute('aria-activedescendant', opts[i].id);
      var o = opts[i], top = o.offsetTop, bot = top + o.offsetHeight;
      if (top < panel.scrollTop) panel.scrollTop = top - 8;
      else if (bot > panel.scrollTop + panel.clientHeight) panel.scrollTop = bot - panel.clientHeight + 8;
    } else input.removeAttribute('aria-activedescendant');
  }

  // Altura útil do painel = o que sobra abaixo da barra. Evita um painel que
  // continua fora da tela quando a barra ainda não está grudada no topo.
  function fitPanel() {
    if (!state.open) return;
    var room = window.innerHeight - bar.getBoundingClientRect().bottom - 16;
    panel.style.maxHeight = Math.max(220, Math.min(room, 560)) + 'px';
  }

  function openPanel() {
    if (!state.open) {
      state.open = true; panel.hidden = false;
      input.setAttribute('aria-expanded', 'true');
    }
    render(); fitPanel();
  }
  function closePanel() {
    if (!state.open) return;
    state.open = false; panel.hidden = true;
    input.setAttribute('aria-expanded', 'false');
    input.removeAttribute('aria-activedescendant');
  }
  function syncClear() {
    var has = !!(state.q || state.chip);
    clearBtn.hidden = !has;
    bar.classList.toggle('has-value', has);
  }
  function setChip(c, focusInput) {
    state.chip = state.chip === c ? null : c;
    syncChips(); syncClear(); openPanel();
    if (focusInput && !coarse) input.focus({ preventScroll: true });
  }

  function labels() {
    input.setAttribute('aria-label', T('fr.tbAria', 'Buscar ferramenta'));
    clearBtn.setAttribute('aria-label', T('fr.tbClear', 'Limpar busca'));
    panel.setAttribute('aria-label', T('fr.tbResults', 'Resultados'));
    if (chipsInline) chipsInline.setAttribute('aria-label', T('fr.tbChipsAria', 'Filtrar por finalidade'));
  }

  // A barra está grudada quando o topo dela coincide com o do sticky.
  function syncStuck() {
    var top = parseFloat(getComputedStyle(root).top) || 0;
    root.classList.toggle('is-stuck', root.getBoundingClientRect().top <= top + 1 && window.scrollY > 0);
  }
  function syncHeader() {
    var h = document.querySelector('.site-header');
    document.documentElement.style.setProperty('--ft-header-h', (h ? Math.round(h.getBoundingClientRect().height) : 64) + 'px');
  }

  function init() {
    root = document.getElementById('ftb');
    if (!root) return;
    bar = root.querySelector('.ftb-bar');
    input = document.getElementById('ftb-q');
    panel = document.getElementById('ftb-panel');
    clearBtn = root.querySelector('.ftb-clear');
    chipsInline = document.getElementById('ftb-chips');

    syncHeader(); labels();
    window.addEventListener('resize', function () { syncHeader(); fitPanel(); });
    var tick = false;
    window.addEventListener('scroll', function () {
      if (tick) return; tick = true;
      requestAnimationFrame(function () { tick = false; syncStuck(); if (state.open) fitPanel(); });
    }, { passive: true });
    syncStuck();
    window.addEventListener('langchange', function () { labels(); if (state.open) render(); });

    input.addEventListener('focus', openPanel);
    input.addEventListener('input', function () { state.q = input.value; syncClear(); openPanel(); });
    input.addEventListener('keydown', function (ev) {
      var n = state.list.length;
      if (ev.key === 'ArrowDown') { ev.preventDefault(); if (!state.open) openPanel(); else if (n) setActive((state.active + 1) % n); }
      else if (ev.key === 'ArrowUp') { ev.preventDefault(); if (n) setActive((state.active - 1 + n) % n); }
      else if (ev.key === 'Home' && state.open && n) { ev.preventDefault(); setActive(0); }
      else if (ev.key === 'End' && state.open && n) { ev.preventDefault(); setActive(n - 1); }
      else if (ev.key === 'Enter') {
        if (state.open && state.active >= 0 && state.list[state.active]) { ev.preventDefault(); activate(state.list[state.active]); }
      } else if (ev.key === 'Escape') {
        if (state.open) { ev.preventDefault(); closePanel(); }
        else if (state.q || state.chip) { input.value = state.q = ''; state.chip = null; syncChips(); syncClear(); }
        else input.blur();
      }
    });
    clearBtn.addEventListener('click', function () {
      input.value = state.q = ''; state.chip = null; syncChips(); syncClear();
      input.focus(); openPanel();
    });

    panel.addEventListener('mousedown', function (ev) { ev.preventDefault(); }); // mantém o foco no campo
    panel.addEventListener('mousemove', function (ev) {
      var o = ev.target.closest('.ftb-opt'); if (o && +o.getAttribute('data-i') !== state.active) setActive(+o.getAttribute('data-i'));
    });
    panel.addEventListener('click', function (ev) {
      var c = ev.target.closest('.ftb-chip'); if (c) { setChip(c.getAttribute('data-chip'), true); return; }
      var o = ev.target.closest('.ftb-opt'); if (o && state.list[+o.getAttribute('data-i')]) activate(state.list[+o.getAttribute('data-i')]);
    });
    if (chipsInline) chipsInline.addEventListener('click', function (ev) {
      var c = ev.target.closest('.ftb-chip'); if (c) setChip(c.getAttribute('data-chip'), true);
    });

    document.addEventListener('pointerdown', function (ev) {
      if (!state.open) return;
      if (root.contains(ev.target) || (chipsInline && chipsInline.contains(ev.target))) return;
      closePanel();
    });

    // "/" e Ctrl/Cmd+K: busca de qualquer ponto, exceto quando já se digita
    // em outro campo ou um modal está aberto.
    document.addEventListener('keydown', function (ev) {
      if (ev.defaultPrevented || document.querySelector('dialog[open]')) return;
      var a = document.activeElement, typing = a && (/^(INPUT|TEXTAREA|SELECT)$/.test(a.tagName) || a.isContentEditable);
      var slash = ev.key === '/' && !typing && !ev.metaKey && !ev.ctrlKey && !ev.altKey;
      var cmdk = (ev.key === 'k' || ev.key === 'K') && (ev.metaKey || ev.ctrlKey);
      if (!slash && !cmdk) return;
      ev.preventDefault();
      input.focus(); input.select(); openPanel();
    });

    // Todo modal aberto — pela busca ou clicando no card — passa a ter URL
    // própria. Captura: roda antes do onclick inline, sem substituí-lo.
    document.addEventListener('click', function (ev) {
      var b = ev.target.closest && ev.target.closest('button[onclick^="open"]');
      if (!b) return;
      var p = parseOpener(b); if (!p) return;
      var sec = b.closest('section.tool');
      lastGroup = sec ? sec.id : null;
      setHash(p.slug);
    }, true);
    ['tnm-modal', 'ctcae-modal', 'crit-modal'].forEach(function (id) {
      var d = document.getElementById(id);
      if (d) d.addEventListener('close', function () { if (lastGroup) setHash(lastGroup); });
    });

    window.addEventListener('hashchange', resolveHash);
    resolveHash();
  }

  // DOMContentLoaded: no app, o native-guards.js registrou o próprio listener
  // antes (está no <head>) e já terá removido as calculadoras de dose.
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
