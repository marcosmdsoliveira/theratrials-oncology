/* ============================================================================
 * ferramentas/home.js — tela inicial das Ferramentas
 *
 *   • contagem de fichas em cada grupo do índice, lida do DOM vivo (no app iOS
 *     o native-guards.js já removeu o que não vai — nada de número fixo);
 *   • "Recentes": as últimas fichas abertas, guardadas só neste aparelho
 *     (localStorage), para voltar a elas com um toque.
 *
 * Não abre modal por conta própria: clica no botão original da ficha, como o
 * toolbox.js. Nada aqui altera dado, fórmula ou texto de ferramenta.
 * ==========================================================================*/
(function () {
  'use strict';

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
          if (sec) sec.scrollIntoView({ block: 'start' });
          btn.click();
        }
        return;
      }
      var b = t.closest(OPENER);
      if (b && b.closest('section.tool')) { remember(b); render(); }
    }, true);

    window.addEventListener('langchange', render);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
