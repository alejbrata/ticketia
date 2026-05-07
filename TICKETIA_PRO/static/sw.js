// Service Worker for Ticketia PWA (v4 - Web Push + Cache Strategy)
const CACHE_NAME = 'ticketia-v4-cache';
const STATIC_ASSETS = [
    '/static/manifest.json',
    '/static/logo_zeptai.png',
    'https://cdn.tailwindcss.com',
    'https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap'
];

// ── Install ────────────────────────────────────────────────────────────────────
self.addEventListener('install', (event) => {
    self.skipWaiting();
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => cache.addAll(STATIC_ASSETS))
    );
});

// ── Activate ───────────────────────────────────────────────────────────────────
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((keys) =>
            Promise.all(
                keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
            )
        ).then(() => self.clients.claim())
    );
});

// ── Fetch (Cache Strategy) ─────────────────────────────────────────────────────
self.addEventListener('fetch', (event) => {
    const url = new URL(event.request.url);

    // Static Assets & Fonts → Cache First
    if (url.pathname.startsWith('/static/') ||
        url.hostname.includes('fonts.googleapis.com') ||
        url.hostname.includes('cdn.tailwindcss.com')) {
        event.respondWith(
            caches.match(event.request).then((cached) =>
                cached || fetch(event.request).then((response) =>
                    caches.open(CACHE_NAME).then((cache) => {
                        cache.put(event.request, response.clone());
                        return response;
                    })
                )
            )
        );
        return;
    }

    // API & Dynamic Pages → Network First, fallback to cache (GET only)
    if (event.request.method === 'GET') {
        event.respondWith(
            fetch(event.request)
                .then((response) => {
                    const clone = response.clone();
                    caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
                    return response;
                })
                .catch(() => caches.match(event.request))
        );
    } else {
        event.respondWith(fetch(event.request));
    }
});

// ── Web Push ───────────────────────────────────────────────────────────────────
self.addEventListener('push', (event) => {
    let payload = { title: 'Ticketia', body: 'Tienes una nueva notificación.', url: '/dashboard' };

    if (event.data) {
        try {
            payload = { ...payload, ...JSON.parse(event.data.text()) };
        } catch (e) {
            payload.body = event.data.text();
        }
    }

    const options = {
        body: payload.body,
        icon: '/static/logo_zeptai.png',
        badge: '/static/logo_zeptai.png',
        data: { url: payload.url || '/dashboard' },
        vibrate: [200, 100, 200],
        requireInteraction: false
    };

    event.waitUntil(
        self.registration.showNotification(payload.title, options)
    );
});

// ── Notification Click ─────────────────────────────────────────────────────────
self.addEventListener('notificationclick', (event) => {
    event.notification.close();

    const targetUrl = (event.notification.data && event.notification.data.url) || '/dashboard';

    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
            // Si ya hay una pestaña abierta con la app, enfocarla y navegar
            for (const client of clientList) {
                if (client.url.includes(self.location.origin) && 'focus' in client) {
                    client.focus();
                    client.navigate(targetUrl);
                    return;
                }
            }
            // Si no hay pestaña abierta, abrir una nueva
            if (clients.openWindow) {
                return clients.openWindow(targetUrl);
            }
        })
    );
});
