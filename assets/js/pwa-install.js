/* =============================================================================
   TheraTrials Oncology — PWA Install Helper
   v1.1.0
   - Registra o service worker
   - Mostra banner "Adicionar à tela inicial" no iOS Safari
   - Mostra prompt nativo de instalação no Android Chrome
   - Lembra dismissal via localStorage por 14 dias
   ============================================================================= */

(function() {
  'use strict';

  /* ------------------ Service worker ------------------ */
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      // Calcula path do SW relativo ao site root
      const swPath = new URL('sw.js', document.baseURI).href;
      navigator.serviceWorker.register(swPath, { scope: './' })
        .then(reg => {
          // Auto-update: se houver SW novo aguardando, ativa imediatamente
          if (reg.waiting) reg.waiting.postMessage({ type: 'SKIP_WAITING' });
          reg.addEventListener('updatefound', () => {
            const nw = reg.installing;
            if (!nw) return;
            nw.addEventListener('statechange', () => {
              if (nw.state === 'installed' && navigator.serviceWorker.controller) {
                // Há uma versão nova esperando — mostra toast (opcional)
                showUpdateToast();
              }
            });
          });
        })
        .catch(err => console.warn('[PWA] SW registration failed', err));

      // Reload automático quando o SW tomar controle
      let refreshing = false;
      navigator.serviceWorker.addEventListener('controllerchange', () => {
        if (refreshing) return;
        refreshing = true;
        // não recarrega na primeira instalação para não interromper UX
      });
    });
  }

  /* ------------------ Helpers ------------------ */
  const LS_KEY = 'thera_pwa_dismissed_at';
  const DISMISS_DAYS = 14;
  const DISMISS_MS = DISMISS_DAYS * 24 * 60 * 60 * 1000;

  function isIOS() {
    return /iPhone|iPad|iPod/i.test(navigator.userAgent)
      && !window.MSStream;
  }
  function isStandalone() {
    return window.matchMedia('(display-mode: standalone)').matches
      || window.navigator.standalone === true;
  }
  function recentlyDismissed() {
    const ts = +localStorage.getItem(LS_KEY) || 0;
    return ts && (Date.now() - ts) < DISMISS_MS;
  }
  function markDismissed() {
    localStorage.setItem(LS_KEY, String(Date.now()));
  }

  /* ------------------ Banner iOS ------------------ */
  function injectStyles() {
    if (document.getElementById('pwa-install-styles')) return;
    const style = document.createElement('style');
    style.id = 'pwa-install-styles';
    style.textContent = `
      .pwa-install-banner {
        position: fixed;
        left: 50%; bottom: 16px;
        transform: translateX(-50%) translateY(140%);
        z-index: 9999;
        width: calc(100% - 24px); max-width: 420px;
        background: rgba(20, 22, 27, 0.96);
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        border: 1px solid rgba(255, 132, 0, 0.35);
        border-radius: 14px;
        padding: 14px 14px 14px 14px;
        color: #F5F6F7;
        font-family: 'Outfit', system-ui, -apple-system, sans-serif;
        box-shadow: 0 16px 40px rgba(0,0,0,0.45), 0 0 30px rgba(255,132,0,0.08);
        opacity: 0;
        transition: transform 320ms cubic-bezier(.22,.94,.34,1), opacity 220ms;
        pointer-events: none;
        padding-bottom: max(14px, env(safe-area-inset-bottom));
      }
      .pwa-install-banner.show {
        transform: translateX(-50%) translateY(0);
        opacity: 1;
        pointer-events: auto;
      }
      .pwa-install-banner .row { display: flex; gap: 12px; align-items: flex-start; }
      .pwa-install-banner .icon {
        flex-shrink: 0;
        width: 44px; height: 44px;
        border-radius: 10px;
        background: linear-gradient(135deg, #FFA640 0%, #FF8400 100%);
        display: flex; align-items: center; justify-content: center;
        color: #0E0F12; font-weight: 700; font-size: 13px;
      }
      .pwa-install-banner .body { flex: 1; min-width: 0; }
      .pwa-install-banner .title {
        font-size: 14px; font-weight: 600; line-height: 1.25;
        margin: 0 0 2px;
      }
      .pwa-install-banner .title .acc { color: #FF8400; }
      .pwa-install-banner .desc {
        font-size: 12px; color: #B5BBC2; line-height: 1.4;
        margin: 0;
      }
      .pwa-install-banner .close {
        background: transparent; border: none; color: #8E949C;
        font-size: 22px; line-height: 1; cursor: pointer;
        padding: 0 4px; margin: -2px -4px 0 0;
        flex-shrink: 0;
      }
      .pwa-install-banner .close:hover { color: #F5F6F7; }

      .pwa-install-banner .ios-steps {
        margin-top: 10px;
        padding: 10px 12px;
        background: rgba(255, 132, 0, 0.06);
        border: 1px solid rgba(255, 132, 0, 0.18);
        border-radius: 10px;
        font-size: 12px; color: #F5F6F7; line-height: 1.5;
      }
      .pwa-install-banner .ios-steps b { color: #FF8400; }
      .pwa-install-banner .ios-steps .share-icon {
        display: inline-block;
        vertical-align: -3px;
        margin: 0 2px;
      }

      .pwa-install-banner .actions {
        display: flex; gap: 8px; margin-top: 10px;
      }
      .pwa-install-banner .btn {
        flex: 1; padding: 8px 10px;
        border-radius: 8px; font-size: 12.5px; font-weight: 600;
        font-family: inherit;
        border: 1px solid rgba(143,148,156,0.25);
        background: transparent; color: #F5F6F7;
        cursor: pointer; transition: all 0.15s;
      }
      .pwa-install-banner .btn:hover { border-color: #8E949C; }
      .pwa-install-banner .btn.primary {
        background: #FF8400; color: #0E0F12; border-color: #FF8400;
      }
      .pwa-install-banner .btn.primary:hover { background: #FFA640; border-color: #FFA640; }

      .pwa-update-toast {
        position: fixed; right: 16px; bottom: 16px;
        z-index: 9998;
        background: rgba(20, 22, 27, 0.96);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(14, 165, 183, 0.4);
        border-radius: 10px; padding: 10px 14px;
        color: #F5F6F7; font-size: 13px;
        font-family: 'Outfit', system-ui, sans-serif;
        display: flex; align-items: center; gap: 10px;
        box-shadow: 0 12px 30px rgba(0,0,0,0.4);
        opacity: 0; transform: translateY(20px);
        transition: all 0.3s; pointer-events: none;
      }
      .pwa-update-toast.show { opacity: 1; transform: translateY(0); pointer-events: auto; }
      .pwa-update-toast button {
        background: #0EA5B7; color: #0E0F12; border: none;
        padding: 5px 10px; border-radius: 6px; font-weight: 600;
        font-size: 12px; cursor: pointer; font-family: inherit;
      }
    `;
    document.head.appendChild(style);
  }

  function buildIOSBanner() {
    const el = document.createElement('div');
    el.className = 'pwa-install-banner';
    el.setAttribute('role', 'dialog');
    el.setAttribute('aria-label', 'Instalar TheraTrials no iPhone');
    el.innerHTML = `
      <div class="row">
        <div class="icon">Tt</div>
        <div class="body">
          <p class="title">Instale o <span class="acc">TheraTrials</span> no iPhone</p>
          <p class="desc">Adicione à tela inicial e abra como um app — sem barra do Safari, com modo offline.</p>
        </div>
        <button class="close" aria-label="Fechar">&times;</button>
      </div>
      <div class="ios-steps">
        Toque em
        <svg class="share-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M12 3v12m0-12l-4 4m4-4l4 4M5 14v5a2 2 0 002 2h10a2 2 0 002-2v-5" stroke="#FF8400" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <b>Compartilhar</b> e depois <b>Adicionar à Tela de Início</b>.
      </div>
      <div class="actions">
        <button class="btn" data-action="later">Depois</button>
        <button class="btn primary" data-action="ok">Entendi</button>
      </div>
    `;
    document.body.appendChild(el);

    el.querySelector('.close').onclick = () => hide(el);
    el.querySelector('[data-action="later"]').onclick = () => hide(el);
    el.querySelector('[data-action="ok"]').onclick = () => hide(el);
    requestAnimationFrame(() => el.classList.add('show'));
    return el;
  }

  function hide(el) {
    el.classList.remove('show');
    markDismissed();
    setTimeout(() => el.remove(), 350);
  }

  /* ------------------ Android Chrome (beforeinstallprompt) ------------------ */
  let deferredPrompt = null;
  window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    if (recentlyDismissed() || isStandalone()) return;
    showAndroidBanner();
  });

  function showAndroidBanner() {
    injectStyles();
    const el = document.createElement('div');
    el.className = 'pwa-install-banner';
    el.innerHTML = `
      <div class="row">
        <div class="icon">Tt</div>
        <div class="body">
          <p class="title">Instale o <span class="acc">TheraTrials</span></p>
          <p class="desc">Acesso rápido à tela inicial com modo offline e sem barra do navegador.</p>
        </div>
        <button class="close" aria-label="Fechar">&times;</button>
      </div>
      <div class="actions">
        <button class="btn" data-action="later">Depois</button>
        <button class="btn primary" data-action="install">Instalar</button>
      </div>
    `;
    document.body.appendChild(el);
    el.querySelector('.close').onclick = () => hide(el);
    el.querySelector('[data-action="later"]').onclick = () => hide(el);
    el.querySelector('[data-action="install"]').onclick = async () => {
      if (deferredPrompt) {
        deferredPrompt.prompt();
        const { outcome } = await deferredPrompt.userChoice;
        deferredPrompt = null;
      }
      hide(el);
    };
    requestAnimationFrame(() => el.classList.add('show'));
  }

  /* ------------------ iOS install banner trigger ------------------ */
  function maybeShowIOSBanner() {
    if (!isIOS() || isStandalone() || recentlyDismissed()) return;
    injectStyles();
    // Espera 2s para não atropelar o load inicial
    setTimeout(() => buildIOSBanner(), 2000);
  }

  /* ------------------ Update toast ------------------ */
  function showUpdateToast() {
    injectStyles();
    const t = document.createElement('div');
    t.className = 'pwa-update-toast';
    t.innerHTML = `<span>Nova versão disponível</span><button>Atualizar</button>`;
    document.body.appendChild(t);
    requestAnimationFrame(() => t.classList.add('show'));
    t.querySelector('button').onclick = () => {
      navigator.serviceWorker.getRegistration().then(reg => {
        if (reg && reg.waiting) reg.waiting.postMessage({ type: 'SKIP_WAITING' });
        location.reload();
      });
    };
    setTimeout(() => { t.classList.remove('show'); setTimeout(() => t.remove(), 400); }, 8000);
  }

  // Boot
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', maybeShowIOSBanner);
  } else {
    maybeShowIOSBanner();
  }

  // Expor utilitário global
  window.TheraPWA = {
    isInstalled: isStandalone,
    isIOS,
    promptInstall: () => deferredPrompt && deferredPrompt.prompt(),
    forceShowIOSHelp: () => { localStorage.removeItem(LS_KEY); maybeShowIOSBanner(); }
  };
})();
