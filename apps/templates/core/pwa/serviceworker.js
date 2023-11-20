// Base Service Worker implementation

const offlineFile = "/offline/"
const staticCacheName = "yamsa-cache-v" + new Date().getTime();
const filesToCache = [
  offlineFile,
  "static/images/favicon.ico",
  "static/images/favicon-16x16.png",
  "static/images/favicon-32x32.png",
  "static/images/apple-touch-icon.png",
  "static/images/android-chrome-192x192.png",
  "static/images/android-chrome-512x512.png"
// TODO CT: Add splash images here
];

// Cache on install
self.addEventListener("install", event => {
  this.skipWaiting();
  event.waitUntil(
    caches.open(staticCacheName)
      .then(cache => {
        return cache.addAll(filesToCache);
      })
  )
});

// Clear cache on activate
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames
          .filter(cacheName => (cacheName.startsWith("yamsa-cache-")))
          .filter(cacheName => (cacheName !== staticCacheName))
          .map(cacheName => caches.delete(cacheName))
      );
    })
  );
});

// Serve from Cache
self.addEventListener("fetch", event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        return response || fetch(event.request);
      })
      .catch(() => {
        return caches.match(offlineFile);
      })
  )
});