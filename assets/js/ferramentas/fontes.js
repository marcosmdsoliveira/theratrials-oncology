/* ============================================================================
 * ferramentas/fontes.js — rodapé "Fonte e versão" de cada ficha
 *
 * Ao abrir uma ficha (modal), acrescenta ao fim do corpo um bloco com:
 *   • a fonte primária do critério — citação completa e link (PubMed/DOI ou a
 *     página oficial), quando a ficha tem entrada em FT_FONTES;
 *   • a versão do critério e a data da última revisão editorial;
 *   • o lembrete de uso: material de referência para profissionais de saúde.
 *
 * FT_FONTES só recebe o que foi CONFERIDO na fonte (PMID/DOI vistos no PubMed
 * ou página oficial aberta) e aprovado pela curadoria — nada de referência
 * montada de memória. Ficha sem entrada mostra a referência curta que já
 * consta no cabeçalho e o lembrete, sem link e sem data.
 *
 *   'slug': {
 *     fontes: [ { cit: 'Autor A, et al. Título. Revista. Ano;vol(n):pp.',
 *                 pmid: '12345678', doi: '10.…', url: 'https://…' } ],
 *     versao: '1.1',
 *     revisado: '2026-11-16'        // AAAA-MM-DD — data da revisão editorial
 *   }
 *
 * O slug é o do link direto: 'recist', 'ajcc-prostata', 'ctcae-hema'.
 * Nada aqui altera o conteúdo da ficha: o bloco é acrescentado depois dele.
 * ==========================================================================*/
(function () {
  'use strict';

  var FT_FONTES = window.FT_FONTES = window.FT_FONTES || {};

  var OPENERS = { openTNM: 'ajcc-', openCTCAE: 'ctcae-', openCrit: '' };
  var atual = null;     // slug da ficha aberta por último

  function T(key, fb) {
    try { var v = window.t ? window.t(key, fb) : fb; return (v && v !== key) ? v : fb; } catch (e) { return fb; }
  }
  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function slugDe(btn) {
    var m = /^\s*(openTNM|openCTCAE|openCrit)\(\s*'([^']+)'\s*\)/.exec(btn.getAttribute('onclick') || '');
    return m ? OPENERS[m[1]] + m[2] : null;
  }
  function dataLocal(iso) {
    var p = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso || '');
    if (!p) return '';
    var d = new Date(+p[1], +p[2] - 1, +p[3]);
    var lang = (document.documentElement.lang || 'pt-BR').toLowerCase().indexOf('en') === 0 ? 'en-GB' : 'pt-BR';
    try { return d.toLocaleDateString(lang, { day: '2-digit', month: 'short', year: 'numeric' }); }
    catch (e) { return iso; }
  }
  function linkDe(f) {
    if (f.pmid) return { href: 'https://pubmed.ncbi.nlm.nih.gov/' + encodeURIComponent(f.pmid) + '/', rot: 'PubMed' };
    if (f.doi) return { href: 'https://doi.org/' + encodeURI(f.doi), rot: 'DOI' };
    if (f.url) return { href: f.url, rot: T('fr.fonteAbrir', 'Abrir fonte') };
    return null;
  }

  function montar(dlg) {
    var corpo = dlg.querySelector('.tnm-modal-body');
    if (!corpo || corpo.querySelector('[data-ft-fonte]')) return;
    var info = (atual && FT_FONTES[atual]) || null;
    var html = '<div class="ft-fonte-h">' + esc(T('fr.fonteTitulo', 'Fonte e versão')) + '</div>';

    if (info && info.fontes && info.fontes.length) {
      html += '<ul class="ft-fonte-lista">' + info.fontes.map(function (f) {
        var l = linkDe(f);
        return '<li><span class="ft-fonte-cit">' + esc(f.cit) + '</span>' +
          (l ? ' <a class="ft-fonte-link" href="' + esc(l.href) + '" target="_blank" rel="noopener">' + esc(l.rot) + ' ↗</a>' : '') + '</li>';
      }).join('') + '</ul>';
    } else {
      // Sem entrada conferida: repete a referência curta do cabeçalho da ficha.
      var ed = dlg.querySelector('.tnm-modal-head .ed');
      var curta = ed ? ed.textContent.replace(/\s+/g, ' ').trim() : '';
      if (curta) html += '<p class="ft-fonte-cit">' + esc(curta) + '</p>';
    }

    var meta = '';
    if (info && info.versao) meta += '<div><dt>' + esc(T('fr.fonteVersao', 'Versão do critério')) + '</dt><dd>' + esc(info.versao) + '</dd></div>';
    if (info && info.revisado) meta += '<div><dt>' + esc(T('fr.fonteRevisao', 'Revisão editorial')) + '</dt><dd>' + esc(dataLocal(info.revisado)) + '</dd></div>';
    if (meta) html += '<dl class="ft-fonte-meta">' + meta + '</dl>';

    html += '<p class="ft-fonte-aviso">' + esc(T('fr.fonteAviso',
      'Material de referência para profissionais de saúde. Confira a fonte original e a versão exigida pelo protocolo do estudo; a decisão clínica é do médico assistente.')) + '</p>';

    var bloco = document.createElement('aside');
    bloco.className = 'ft-fonte';
    bloco.setAttribute('data-ft-fonte', '');
    bloco.innerHTML = html;
    corpo.appendChild(bloco);
  }

  function init() {
    // Captura: guarda o slug antes de o onclick inline montar a ficha. A busca
    // e os links diretos do toolbox.js passam por aqui, pois clicam no botão.
    document.addEventListener('click', function (ev) {
      var b = ev.target.closest && ev.target.closest('button[onclick^="open"]');
      if (b) atual = slugDe(b) || atual;
    }, true);

    ['tnm-modal', 'ctcae-modal', 'crit-modal'].forEach(function (id) {
      var dlg = document.getElementById(id);
      var corpo = dlg && dlg.querySelector('.tnm-modal-body');
      if (!corpo) return;
      // O corpo é reescrito a cada abertura; o bloco entra depois disso.
      new MutationObserver(function () { montar(dlg); }).observe(corpo, { childList: true });
    });

    // Troca de idioma com a ficha aberta: o bloco é refeito no novo idioma.
    window.addEventListener('langchange', function () {
      var dlg = document.querySelector('dialog.tnm-modal[open]');
      if (!dlg) return;
      var b = dlg.querySelector('[data-ft-fonte]');
      if (b) b.remove();
      montar(dlg);
    });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
