const OFFLINE_URL = "{{ offline_url }}";
const STATIC_CACHE_NAME = "{{ cache_name }}";
const CACHE_PREFIX = "{{ cache_prefix }}";
const STATIC_URL_PREFIX = "{{ static_url_prefix }}";
const PRECACHE_URLS = JSON.parse('{{ precache_urls|escapejs }}');
const SAME_ORIGIN = self.location.origin;

const normalizeUrl = (url) => {
  try {
    return new URL(url, SAME_ORIGIN).href;
  } catch (error) {
    return url;
  }
};

const PRECACHE_URL_SET = new Set(PRECACHE_URLS.map(normalizeUrl));

const precacheResources = async () => {
  const cache = await caches.open(STATIC_CACHE_NAME);
  const results = await Promise.allSettled(
    PRECACHE_URLS.map((url) => cache.add(url))
  );

  results.forEach((result, index) => {
    if (result.status === "rejected") {
      console.warn(`Service worker precache skipped for ${PRECACHE_URLS[index]}`, result.reason);
    }
  });
};

self.addEventListener("install", (event) => {
  self.skipWaiting();
  event.waitUntil(precacheResources());
});

const purgeLegacyCaches = async () => {
  const names = await caches.keys();
  const deletions = names
    .filter((name) => name.startsWith(CACHE_PREFIX) && name !== STATIC_CACHE_NAME)
    .map((name) => caches.delete(name));
  return Promise.all(deletions);
};

self.addEventListener("activate", (event) => {
  event.waitUntil(purgeLegacyCaches());
});

const cacheFirst = async (request) => {
  const cache = await caches.open(STATIC_CACHE_NAME);
  const cachedResponse = await cache.match(request);

  if (cachedResponse) {
    return cachedResponse;
  }

  const networkResponse = await fetch(request);
  if (networkResponse && networkResponse.ok) {
    cache.put(request, networkResponse.clone());
  }
  return networkResponse;
};

const networkFirst = async (request) => {
  const cache = await caches.open(STATIC_CACHE_NAME);
  try {
    const networkResponse = await fetch(request);
    if (networkResponse && networkResponse.ok) {
      cache.put(request, networkResponse.clone());
    }
    return networkResponse;
  } catch (error) {
    const cachedResponse = await cache.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }

    if (request.mode === "navigate" || request.destination === "document") {
      const offlineResponse = await cache.match(OFFLINE_URL);
      if (offlineResponse) {
        return offlineResponse;
      }
    }

    throw error;
  }
};

self.addEventListener("fetch", (event) => {
  const {request} = event;

  if (request.method !== "GET") {
    return;
  }

  if (request.mode === "navigate" || request.destination === "document") {
    event.respondWith(networkFirst(request));
    return;
  }

  const normalisedRequestUrl = normalizeUrl(request.url);

  if (
    normalisedRequestUrl.startsWith(`${SAME_ORIGIN}${STATIC_URL_PREFIX}`) ||
    PRECACHE_URL_SET.has(normalisedRequestUrl)
  ) {
    event.respondWith(cacheFirst(request));
    return;
  }

  event.respondWith(
    fetch(request)
      .then((response) => response)
      .catch((error) => caches.match(request).then((cached) => cached || Promise.reject(error)))
  );
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
