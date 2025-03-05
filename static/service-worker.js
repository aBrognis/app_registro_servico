const CACHE_NAME = "servicos-cache-v1";
const urlsToCache = [
    "/",
    "/static/styles.css",
    "/static/manifest.json",
    "/static/icons/icon-192x192.png",
    "/static/icons/icon-512x512.png"
];

// Instalar o Service Worker e armazenar no cache
self.addEventListener("install", (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll(urlsToCache);
        })
    );
});

// Interceptar requisições e servir do cache
self.addEventListener("fetch", (event) => {
    event.respondWith(
        caches.match(event.request).then((response) => {
            return response || fetch(event.request);
        })
    );
});

// Atualizar cache quando necessário
self.addEventListener("activate", (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cache) => {
                    if (cache !== CACHE_NAME) {
                        return caches.delete(cache);
                    }
                })
            );
        })
    );
});
