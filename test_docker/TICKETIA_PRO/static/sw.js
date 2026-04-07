// Service Worker for Ticketia PWA (v2 - Improved Cache Strategy)
const CACHE_NAME = 'ticketia-v2-cache';
const STATIC_ASSETS = [
    '/static/manifest.json',
    '/static/logo_zeptai.png',
    'https://cdn.tailwindcss.com',
    'https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap'
];

self.addEventListener('install', (event) => {
    // Force immediate activation
    self.skipWaiting();
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => cache.addAll(STATIC_ASSETS))
    );
});

self.addEventListener('activate', (event) => {
    // Clean old caches
    event.waitUntil(
        caches.keys().then((keys) => {
            return Promise.all(
                keys.filter((key) => key !== CACHE_NAME)
                    .map((key) => caches.delete(key))
            );
        }).then(() => self.clients.claim()) // Take control of open pages
    );
});

self.addEventListener('fetch', (event) => {
    const url = new URL(event.request.url);

    // 1. Static Assets & Fonts (Cache First)
    if (url.pathname.startsWith('/static/') || 
        url.hostname.includes('fonts.googleapis.com') || 
        url.hostname.includes('cdn.tailwindcss.com')) {
        event.respondWith(
            caches.match(event.request).then((cachedResponse) => {
                return cachedResponse || fetch(event.request).then((networkResponse) => {
                    return caches.open(CACHE_NAME).then((cache) => {
                        cache.put(event.request, networkResponse.clone());
                        return networkResponse;
                    });
                });
            })
        );
        return;
    }

    // 2. API & Dynamic Pages (Network First -> Fallback to Cache if offline)
    // Avoid caching POST requests
    if (event.request.method === 'GET') {
        event.respondWith(
            fetch(event.request)
                .then((networkResponse) => {
                    // Update cache with fresh version
                    const clone = networkResponse.clone();
                    caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
                    return networkResponse;
                })
                .catch(() => {
                    // Fallback to cache if offline
                    return caches.match(event.request);
                })
        );
    } else {
        // POST/PUT/DELETE always network
        event.respondWith(fetch(event.request));
    }
});