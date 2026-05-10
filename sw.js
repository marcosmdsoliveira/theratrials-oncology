/* =============================================================================
   TheraTrials Oncology — Service Worker
   v1.1.0 · 2026-05-10
   Estratégias:
     • HTML  → network-first com fallback em cache (e em última instância /offline.html)
     • Assets estáticos (CSS/JS/IMG/Fonts) → cache-first com revalidação background
     • Google Fonts / CDNs (Lucide, etc.) → stale-while-revalidate
   ============================================================================= */

const CACHE_VERSION = 'theratrials-v2026.05.10-897e31d';
const CACHE_STATIC  = `${CACHE_VERSION}-static`;
const CACHE_PAGES   = `${CACHE_VERSION}-pages`;
const CACHE_RUNTIME = `${CACHE_VERSION}-runtime`;

// Páginas core para pré-cache no install
const CORE_PAGES = [
  './',
  './index.html',
  './database.html',
  './estudos-ativos.html',
  './tumor-boards.html',
  './modalidades.html',
  './ferramentas.html',
  './fundamentos.html',
  './about.html',
  './lu-psma.html',
  './lu-dotatate.html',
  './ra-223.html',
  './y90.html',
  './mibg.html',
  './novos-alfa.html',
  './termos-uso.html',
  './privacidade.html',
  './direitos-autorais.html',
  './offline.html'
];

const CORE_ASSETS = [
  './assets/css/theratrials.css',
  './assets/css/radiofarmaco.css',
  './assets/js/data.js',
  './assets/js/common.js',
  './assets/js/trials_br.js',
  './assets/js/pwa-install.js',
  './assets/img/logo-app.png',
  './assets/img/logo-circular.png',
  './assets/img/logo-orbital.svg',
  './assets/img/hero-banner.png',
  './assets/img/hero-logo.png',
  './assets/img/hero-logo-dark.png',
  './assets/img/icons/icon-180.png',
  './assets/img/icons/icon-192.png',
  './assets/img/icons/icon-512.png',
  './manifest.json'
];

/* =====================  INSTALL  ===================== */
self.addEventListener('install', (event) => {
  event.waitUntil((async () => {
    const pageCache  = await caches.open(CACHE_PAGES);
    const assetCache = await caches.open(CACHE_STATIC);

    // Tolera 404 individual sem abortar o install
    await Promise.all(CORE_PAGES.map(async (url) => {
      try { await pageCache.add(url); } catch (e) { console.warn('[SW] skip page', url, e.message); }
    }));
    await Promise.all(CORE_ASSETS.map(async (url) => {
      try { await assetCache.add(url); } catch (e) { console.warn('[SW] skip asset', url, e.message); }
    }));

    self.skipWaiting();
  })());
});

/* =====================  ACTIVATE  ===================== */
self.addEventListener('activate', (event) => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(
      keys
        .filter(k => k.startsWith('theratrials-') && !k.startsWith(CACHE_VERSION))
        .map(k => caches.delete(k))
    );
    await self.clients.claim();
  })());
});

/* =====================  FETCH  ===================== */
self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;

  const url = new URL(req.url);
  const sameOrigin = url.origin === self.location.origin;

  // Navegação / HTML → network-first
  if (req.mode === 'navigate' || (req.headers.get('accept') || '').includes('text/html')) {
    event.respondWith(networkFirstHTML(req));
    return;
  }

  // Assets do mesmo domínio → cache-first com revalidação
  if (sameOrigin) {
    event.respondWith(cacheFirstWithRevalidate(req, CACHE_STATIC));
    return;
  }

  // CDNs (fonts, lucide) → stale-while-revalidate
  if (url.hostname.includes('fonts.googleapis.com')
   || url.hostname.includes('fonts.gstatic.com')
   || url.hostname.includes('unpkg.com')
   || url.hostname.includes('cdn.jsdelivr.net')) {
    event.respondWith(staleWhileRevalidate(req, CACHE_RUNTIME));
    return;
  }
});

/* =====================  STRATEGIES  ===================== */
async function networkFirstHTML(req) {
  const cache = await caches.open(CACHE_PAGES);
  try {
    const fresh = await fetch(req);
    if (fresh && fresh.ok) cache.put(req, fresh.clone());
    return fresh;
  } catch (err) {
    const cached = await cache.match(req, { ignoreSearch: true });
    if (cached) return cached;
    const offline = await cache.match('./offline.html');
    if (offline) return offline;
    return new Response('<h1>Offline</h1><p>Conecte-se à internet e tente novamente.</p>', {
      headers: { 'Content-Type': 'text/html; charset=utf-8' },
      status: 503
    });
  }
}

async function cacheFirstWithRevalidate(req, cacheName) {
  const cache = await caches.open(cacheName);
  const cached = await cache.match(req);
  const fetchPromise = fetch(req).then(res => {
    if (res && res.ok) cache.put(req, res.clone());
    return res;
  }).catch(() => cached);
  return cached || fetchPromise;
}

async function staleWhileRevalidate(req, cacheName) {
  const cache = await caches.open(cacheName);
  const cached = await cache.match(req);
  const network = fetch(req).then(res => {
    if (res && res.ok) cache.put(req, res.clone());
    return res;
  }).catch(() => null);
  return cached || network || new Response('', { status: 504 });
}

/* =====================  MENSAGEM (atualização forçada)  ===================== */
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') self.skipWaiting();
});
