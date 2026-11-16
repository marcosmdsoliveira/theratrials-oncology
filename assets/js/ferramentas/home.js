/* ============================================================================
 * ferramentas/home.js — tela inicial das Ferramentas
 *
 *   • contagem de fichas em cada grupo do índice, lida do DOM vivo (no app iOS
 *     o native-guards.js já removeu o que não vai — nada de número fixo);
 *   • "Recentes": as últimas fichas abertas, guardadas só neste aparelho
 *     (localStorage), para voltar a elas com um toque.
 *
 *   • um grupo por vez: ao escolher um grupo (pelo índice, pela busca, por
 *     "Recentes" ou por link direto), só ele fica na tela, com um botão para
 *     voltar à lista. O botão Voltar do navegador faz o mesmo caminho.
 *
 * Não abre modal por conta própria: clica no botão original da ficha, como o
 * toolbox.js. Nada aqui altera dado, fórmula ou texto de ferramenta.
 * ==========================================================================*/
(function () {
  'use strict';

  // ── um grupo por vez ──────────────────────────────────────────────────────
  // window.FTView existe desde a avaliação deste arquivo: o toolbox.js o chama
  // já no DOMContentLoaded, ao resolver um link direto.
  var root = document.documentElement;
  var pushed = false;   // a entrada atual do histórico foi criada por nós?

  function groupEl(id) {
    var el = id ? document.getElementById(id) : null;
    return el && el.matches && el.matches('section.tool') ? el : null;
  }
  function current() {
    var a = document.querySelector('section.tool.is-active');
    return a ? a.id : null;
  }
  function hashId() {
    try { return decodeURIComponent((location.hash || '').slice(1)); } catch (e) { return ''; }
  }
  function show(id) {
    var sec = groupEl(id);
    var was = current();
    document.querySelectorAll('section.tool[id]').forEach(function (s) {
      s.classList.toggle('is-active', s === sec);
    });
    root.classList.toggle('ft-group', !!sec);
    root.classList.remove('ft-boot');
    var back = document.getElementById('ft-back');
    if (back) back.hidden = !sec;
    if (sec) {
      sec.classList.add('in-view');            // sem esperar o fade do IntersectionObserver
      if (was !== sec.id) {
        // Vindo da lista sem hash: cria uma entrada, para o Voltar do navegador
        // devolver à lista em vez de sair da página.
        if (!was && !hashId()) {
          try { history.pushState(null, '', location.pathname + location.search + '#' + sec.id); pushed = true; } catch (e) {}
        }
        window.scrollTo(0, 0);
      }
    } else if (was) {
      window.scrollTo(0, 0);
    }
  }
  function home() {
    if (pushed) { pushed = false; history.back(); return; }   // o popstate chama sync()
    try { history.replaceState(null, '', location.pathname + location.search); } catch (e) {}
    show(null);
  }
  // Hash vazio → lista; hash de grupo → o grupo. Hash de ficha (#recist) é
  // assunto do toolbox.js, que abre o modal e chama show() pelo grupo.
  function sync() {
    var id = hashId();
    if (!id) { pushed = false; show(null); return; }
    if (groupEl(id)) show(id);
  }
  window.FTView = { show: show, home: home, current: current };

  var KEY = 'tt_ferramentas_recentes';
  var MAX = 6;
  var OPENER = 'button[onclick^="open"]';

  function text(el) { return el ? el.textContent.replace(/\s+/g, ' ').trim() : ''; }

  // ── contagem por grupo ────────────────────────────────────────────────────
  function counts() {
    document.querySelectorAll('.tools-hub .tool-link[href^="#"]').forEach(function (a) {
      var sec = document.getElementById(a.getAttribute('href').slice(1));
      if (!sec || a.querySelector('.tl-count')) return;
      var n = sec.querySelectorAll(OPENER).length;
      var s = document.createElement('span');
      s.className = 'tl-count';
      if (n) s.textContent = String(n);
      a.appendChild(s);
    });
  }

  // ── recentes ──────────────────────────────────────────────────────────────
  function load() {
    try { var v = JSON.parse(localStorage.getItem(KEY) || '[]'); return Array.isArray(v) ? v : []; }
    catch (e) { return []; }
  }
  function save(list) {
    try { localStorage.setItem(KEY, JSON.stringify(list.slice(0, MAX))); } catch (e) {}
  }
  function findOpener(call) {
    var all = document.querySelectorAll(OPENER);
    for (var i = 0; i < all.length; i++) if (all[i].getAttribute('onclick') === call) return all[i];
    return null;
  }

  function render() {
    var box = document.getElementById('ft-recents');
    var list = document.getElementById('ft-recents-list');
    if (!box || !list) return;
    // Só o que ainda existe na página (uma ficha pode sair numa versão futura).
    var items = load().filter(function (r) { return r && r.call && findOpener(r.call); });
    list.textContent = '';
    items.forEach(function (r) {
      var b = document.createElement('button');
      b.type = 'button';
      b.className = 'ft-recent';
      b.setAttribute('data-call', r.call);
      var btn = findOpener(r.call);
      var sec = btn.closest('section.tool');
      var color = sec ? getComputedStyle(sec).getPropertyValue('--tool-accent').trim() : '';
      if (color) b.style.setProperty('--accent', color);
      // Título lido da ficha viva: acompanha o idioma atual.
      b.textContent = text(btn.querySelector('.tnm-card-title')) || r.title || '';
      list.appendChild(b);
    });
    box.hidden = items.length === 0;
  }

  function remember(btn) {
    var call = btn.getAttribute('onclick');
    var list = load().filter(function (r) { return r && r.call !== call; });
    list.unshift({ call: call, title: text(btn.querySelector('.tnm-card-title')) });
    save(list);
  }

  function init() {
    counts();
    render();

    // Captura: registra a ficha antes do onclick inline abrir o modal. A busca
    // do toolbox.js também passa por aqui, porque ela clica no mesmo botão.
    document.addEventListener('click', function (ev) {
      var t = ev.target.closest ? ev.target : null;
      if (!t) return;
      var rec = t.closest('.ft-recent');
      if (rec) {
        var btn = findOpener(rec.getAttribute('data-call'));
        if (btn) {
          var sec = btn.closest('section.tool');
          if (sec) show(sec.id);
          btn.click();
        }
        return;
      }
      if (t.closest('#ft-back-btn')) { home(); return; }
      var hub = t.closest('.tools-hub a.tool-link[href^="#"]');
      if (hub) {
        var gid = hub.getAttribute('href').slice(1);
        if (groupEl(gid)) { ev.preventDefault(); show(gid); }
        return;
      }
      var b = t.closest(OPENER);
      if (b && b.closest('section.tool')) { show(b.closest('section.tool').id); remember(b); render(); }
    }, true);

    window.addEventListener('langchange', render);
    window.addEventListener('hashchange', sync);
    window.addEventListener('popstate', sync);

    // Chegada: o toolbox.js já resolveu um link de ficha (e chamou show()).
    // Resta o hash de grupo, o hash vazio e o hash que não existe.
    if (!current()) { if (groupEl(hashId())) show(hashId()); else show(null); }
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
