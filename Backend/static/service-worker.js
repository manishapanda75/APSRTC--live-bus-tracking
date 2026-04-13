// ═══════════════════════════════════════════════════════
// APSRTC Live — Service Worker (PWA Offline Support)
// ═══════════════════════════════════════════════════════

const CACHE_NAME = 'apsrtc-live-v11';
const STATIC_ASSETS = [
    '/',
    '/static/style.css',
    '/static/leaflet.css',
    '/static/leaflet.js',
    '/static/js/translations.js',
    '/static/favicon.ico',
    '/static/manifest.json',
    '/offline'
];

// Install — cache static assets
self.addEventListener('install', (event) => {
    console.log('[SW] Installing Service Worker v11...');
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            console.log('[SW] Caching static assets');
            return cache.addAll(STATIC_ASSETS).catch(err => {
                console.warn('[SW] Some assets failed to cache:', err);
            });
        })
    );
    self.skipWaiting();
});

// Activate — clean up old caches
self.addEventListener('activate', (event) => {
    console.log('[SW] Activating Service Worker v11...');
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.filter(name => name !== CACHE_NAME).map(name => {
                    console.log('[SW] Deleting old cache:', name);
                    return caches.delete(name);
                })
            );
        })
    );
    self.clients.claim();
});

// Fetch — Network First for API, Stale-While-Revalidate for static assets
self.addEventListener('fetch', (event) => {
    const url = new URL(event.request.url);

    // Skip non-GET requests
    if (event.request.method !== 'GET') return;

    // API calls — Network first, fallback to cache
    if (url.pathname.startsWith('/api/')) {
        event.respondWith(
            fetch(event.request)
                .then(response => {
                    if (response.status === 200) {
                        const clone = response.clone();
                        caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
                    }
                    return response;
                })
                .catch(() => caches.match(event.request).then(cached => {
                    return cached || new Response(JSON.stringify({ error: 'Offline' }), {
                        headers: { 'Content-Type': 'application/json' }
                    });
                }))
        );
        return;
    }

    // Static assets — Stale-While-Revalidate
    // Serve from cache if available, but always fetch from network to update cache
    event.respondWith(
        caches.match(event.request).then(cachedResponse => {
            const fetchPromise = fetch(event.request).then(networkResponse => {
                if (networkResponse.status === 200) {
                    const clone = networkResponse.clone();
                    caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
                }
                return networkResponse;
            }).catch(() => {
                // Return offline page for HTML requests if both fail
                if (event.request.headers.get('accept')?.includes('text/html')) {
                    return caches.match('/offline');
                }
            });

            return cachedResponse || fetchPromise;
        })
    );
});
