/* ============================================================
   TheraTrials Oncology — i18n Engine
   Lightweight internationalization for static HTML pages.

   Usage:
     HTML:  <span data-i18n="hero.title">Texto original</span>
            <input data-i18n-placeholder="search.hint" placeholder="...">
            <meta data-i18n-content="meta.desc" content="...">
     JS:    window.t('hero.title')  // returns translated string
     JS:    window.setLang('en')    // switch language
   ============================================================ */

(function () {
  'use strict';

  var STORAGE_KEY = 'theratrials-lang';
  var DEFAULT_LANG = 'pt-br';
  var SUPPORTED = ['pt-br', 'en'];
  var translations = {};
  var currentLang = DEFAULT_LANG;

  // ── Detect preferred language ──
  function detectLang() {
    // 1. Explicit URL param: ?lang=en
    var params = new URLSearchParams(window.location.search);
    var urlLang = params.get('lang');
    if (urlLang && SUPPORTED.indexOf(urlLang.toLowerCase()) > -1) {
      return urlLang.toLowerCase();
    }
    // 2. Stored preference
    try {
      var stored = localStorage.getItem(STORAGE_KEY);
      if (stored && SUPPORTED.indexOf(stored) > -1) return stored;
    } catch (e) {}
    // 3. Browser language
    var nav = (navigator.language || navigator.userLanguage || '').toLowerCase();
    if (nav.indexOf('pt') === 0) return 'pt-br';
    if (nav.indexOf('en') === 0) return 'en';
    // 4. Default
    return DEFAULT_LANG;
  }

  // ── Load translation file ──
  function loadTranslations(lang, callback) {
    // Check if already loaded
    if (translations[lang]) { callback(); return; }

    var script = document.createElement('script');
    script.src = getBasePath() + 'assets/lang/' + lang + '.js';
    script.onload = function () { callback(); };
    script.onerror = function () {
      console.warn('[i18n] Failed to load ' + lang + '.js');
      callback();
    };
    document.head.appendChild(script);
  }

  // ── Register translations (called by lang files) ──
  window._i18nRegister = function (lang, data) {
    translations[lang] = data;
  };

  // ── Get base path (handles subdirectories) ──
  function getBasePath() {
    var path = window.location.pathname;
    // If in a subdirectory like /newsletters/, go up
    if (path.indexOf('/newsletters/') > -1) return '../';
    return '';
  }

  // ── Translate single key ──
  function t(key, fallback) {
    var dict = translations[currentLang] || {};
    // Support nested keys: "hero.title" → dict.hero.title
    var parts = key.split('.');
    var val = dict;
    for (var i = 0; i < parts.length; i++) {
      if (val && typeof val === 'object' && parts[i] in val) {
        val = val[parts[i]];
      } else {
        return fallback || key;
      }
    }
    return (typeof val === 'string') ? val : (fallback || key);
  }
  window.t = t;

  // ── Apply translations to DOM ──
  function applyTranslations() {
    // Text content
    var els = document.querySelectorAll('[data-i18n]');
    for (var i = 0; i < els.length; i++) {
      var key = els[i].getAttribute('data-i18n');
      var val = t(key);
      if (val !== key) els[i].textContent = val;
    }
    // Placeholders
    var phs = document.querySelectorAll('[data-i18n-placeholder]');
    for (var j = 0; j < phs.length; j++) {
      var phKey = phs[j].getAttribute('data-i18n-placeholder');
      var phVal = t(phKey);
      if (phVal !== phKey) phs[j].placeholder = phVal;
    }
    // HTML content (for elements with markup)
    var htmlEls = document.querySelectorAll('[data-i18n-html]');
    for (var k = 0; k < htmlEls.length; k++) {
      var hKey = htmlEls[k].getAttribute('data-i18n-html');
      var hVal = t(hKey);
      if (hVal !== hKey) htmlEls[k].innerHTML = hVal;
    }
    // Update toggle button state
    updateToggleUI();
    // Update html lang attribute
    document.documentElement.lang = (currentLang === 'en') ? 'en' : 'pt-BR';
  }

  // ── Update language toggle UI ──
  function updateToggleUI() {
    var toggles = document.querySelectorAll('.lang-toggle');
    for (var i = 0; i < toggles.length; i++) {
      var btn = toggles[i];
      var label = btn.querySelector('.lang-label');
      if (label) label.textContent = currentLang === 'en' ? 'PT' : 'EN';
      btn.setAttribute('title', currentLang === 'en' ? 'Mudar para Português' : 'Switch to English');
    }
  }

  // ── Set language ──
  function setLang(lang) {
    if (SUPPORTED.indexOf(lang) === -1) return;
    currentLang = lang;
    try { localStorage.setItem(STORAGE_KEY, lang); } catch (e) {}
    loadTranslations(lang, function () {
      applyTranslations();
      // Dispatch event for JS components that need to react
      window.dispatchEvent(new CustomEvent('langchange', { detail: { lang: lang } }));
    });
  }
  window.setLang = setLang;

  // ── Toggle language ──
  window.toggleLang = function () {
    setLang(currentLang === 'pt-br' ? 'en' : 'pt-br');
  };

  // ── Get current language ──
  window.getLang = function () { return currentLang; };

  // ── Initialize ──
  //
  // Os dicionários são carregados SOB DEMANDA (loadTranslations injeta o <script>).
  // Até 2026-08 as páginas traziam pt-br.js E en.js em tags estáticas — 154 KB gzip
  // em toda visita, sendo que ninguém usa dois idiomas ao mesmo tempo.
  //
  // Hoje:
  //   • visitante pt-BR  → NENHUM dicionário. O HTML já está em português e as
  //     chamadas em runtime são todas t(chave, fallbackEmPortuguês).
  //   • visitante inglês → só en.js.
  //   • ao trocar de idioma → setLang() carrega o que faltar, uma única vez.
  function init() {
    currentLang = detectLang();
    if (currentLang !== 'pt-br') {
      loadTranslations(currentLang, function () {
        applyTranslations();
      });
    } else {
      // Nada a baixar: o conteúdo em pt-BR já está no HTML.
      updateToggleUI();
    }
  }

  // Run on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
