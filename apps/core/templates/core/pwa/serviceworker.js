const offlineFile = "/offline/"
const staticCacheName = "yamsa-cache-v" + new Date().getTime();
const filesToCache = [
  offlineFile,
  "static/images/favicon.ico",
  "static/images/16x16.webp",
  "static/images/32x32.webp",
  "static/images/48x48.webp",
  "static/images/57x57-ios.webp",
  "static/images/60x60-ios.webp",
  "static/images/72x72-ios.webp",
  "static/images/76x76-ios.webp",
  "static/images/96x96.webp",
  "static/images/114x114-ios.webp",
  "static/images/120x120-ios.webp",
  "static/images/144x144.webp",
  "static/images/152x152-ios.webp",
  "static/images/180x180-ios.webp",
  "static/images/192x192.webp",
  "static/images/256x256.webp",
  "static/images/384x384.webp",
  "static/images/512x512.webp",
// TODO CT: Add splash images here
];

// Cache on install
self.addEventListener("install", event => {
  this.skipWaiting();
  event.waitUntil(caches.open(staticCacheName)
    .then(cache => {
      return cache.addAll(filesToCache);
    }))
});

// Clear cache on activate
self.addEventListener('activate', event => {
  event.waitUntil(caches.keys().then(cacheNames => {
    return Promise.all(cacheNames
      .filter(cacheName => (cacheName.startsWith("yamsa-cache-")))
      .filter(cacheName => (cacheName !== staticCacheName))
      .map(cacheName => caches.delete(cacheName)));
  }));
});

// Serve from Cache
self.addEventListener("fetch", event => {
  event.respondWith(caches.match(event.request)
    .then(response => {
      return response || fetch(event.request);
    })
    .catch(() => caches.match(offlineFile)))
});

// Register event listener for the 'push' event.
self.addEventListener('push', (event) => {
  // Retrieve the textual payload from event.data (a PushMessageData object).
  // Other formats are supported (ArrayBuffer, Blob, JSON), check out the documentation
  // on https://developer.mozilla.org/en-US/docs/Web/API/PushMessageData.
  const {head, ...options} = JSON.parse(event.data.text());

  // Keep the service worker alive until the notification is created.
  event.waitUntil(self.registration.showNotification(head, options));
});

// Function to get the URL for a specific action from a list of actionClickUrls
const getURLForAction = (action, actionClickUrls) => {
  for (const clickUrl of actionClickUrls) {
    if (clickUrl.action === action) {
      return clickUrl.url;
    }
  }
  // If no match is found, you may choose to return null or some other default value.
  return null;
};

// Function to navigate the client to a URL, handling different scenarios
const navigateClientToUrl = (event, url) => event.waitUntil(
  clients.matchAll({ includeUncontrolled: true, type: 'window' })
    .then(clientsArray => {
      if (clientsArray.length > 0) {
        // If multiple clients are available, choose the first one and navigate
        return clientsArray[0].navigate(url).then(client => client.focus());
      } else {
        // If no clients are available, open a new window
        return clients.openWindow(url);
      }
    })
);

// Event listener for the 'notificationclick' event
self.addEventListener('notificationclick', function (event) {
  // Close the notification popout
  event.notification.close();

  // Extract relevant data from the notification
  const {actionClickUrls, notificationClickUrl} = event.notification.data;

  // Check if an action was clicked
  if (!event.action) {
    // If no specific action was clicked,
    // navigate to the default notificationClickUrl
    navigateClientToUrl(event, notificationClickUrl);
    return;
  }

  // Handle different actions
  switch (event.action) {
    case 'click-me-action':
      // For the 'click-me-action', navigate to the corresponding URL
      navigateClientToUrl(event, getURLForAction('click-me-action', actionClickUrls));
      break;
    default:
      // Log unknown actions to the console
      console.log(`Unknown action clicked: '${event.action}'`);
      break;
  }
});