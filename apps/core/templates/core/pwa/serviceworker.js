const OFFLINE_URL = "{{ offline_url }}";
const STATIC_CACHE_NAME = "{{ cache_name }}";
const PAGES_CACHE_PREFIX = "{{ pages_cache_prefix }}";
const CACHE_PREFIX = "{{ cache_prefix }}";
const STATIC_URL_PREFIX = "{{ static_url_prefix }}";
const MAX_CACHED_PAGES = {{ max_cached_pages }};
const SCOPE_HEADER = "{{ scope_header }}";
const CACHED_AT_HEADER = "{{ cached_at_header }}";
const PREFETCH_HEADER = "{{ prefetch_header }}";
const SESSION_URL = "{{ session_url }}";
const LOGIN_PATH = "{{ login_path }}";

// Mirrors apps/static/js/offline outbox module. The page writes this store and this worker
// replays it, and a worker rendered by Django cannot import a webpack bundle to share them.
const OUTBOX_DATABASE = "yamsa-outbox";
const OUTBOX_STORE = "entries";
const OUTBOX_VERSION = 1;
const OUTBOX_SYNC_TAG = "yamsa-outbox";
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

const isOwnCache = (name) => name.startsWith(CACHE_PREFIX);
const isCurrentCache = (name) => name === STATIC_CACHE_NAME || name.startsWith(PAGES_CACHE_PREFIX);

const purgeLegacyCaches = async () => {
  const names = await caches.keys();
  const deletions = names
    .filter((name) => isOwnCache(name) && !isCurrentCache(name))
    .map((name) => caches.delete(name));
  return Promise.all(deletions);
};

self.addEventListener("activate", (event) => {
  // Claimed so the scope the open page reports reaches this worker right away. Until it controls
  // a page, nothing tells the worker that the visitor changed, and the previous visitor's pages
  // stay in the cache.
  event.waitUntil(purgeLegacyCaches().then(() => self.clients.claim()));
});

const pagesCacheNameFor = (scope) => `${PAGES_CACHE_PREFIX}${scope}`;

const findPagesCacheName = async () => {
  const names = await caches.keys();
  return names.find((name) => name.startsWith(PAGES_CACHE_PREFIX)) || null;
};

/*
 * Keep exactly the page cache of the given scope and drop every other one.
 *
 * Cache storage is shared by everyone who uses this browser profile, so a page cache that outlives
 * its visitor is readable by the next one. The worker has no session of its own to check against,
 * which is why the single surviving cache is what identifies the current visitor offline.
 */
const adoptPagesScope = async (scope) => {
  const wanted = pagesCacheNameFor(scope);
  const names = await caches.keys();
  await Promise.all(
    names
      .filter((name) => name.startsWith(PAGES_CACHE_PREFIX) && name !== wanted)
      .map((name) => caches.delete(name))
  );
  return caches.open(wanted);
};

const purgePagesCaches = async () => {
  const names = await caches.keys();
  return Promise.all(
    names.filter((name) => name.startsWith(PAGES_CACHE_PREFIX)).map((name) => caches.delete(name))
  );
};

/*
 * Rebuild a response so it can be stored and later served for a navigation.
 *
 * Two reasons, both about what the Cache API refuses to hand back: a response whose `redirected`
 * flag is set cannot answer a navigation request at all, and response headers are immutable, so
 * the read timestamp the page shows in its offline banner cannot be attached to the original.
 */
const asCacheablePage = async (response) => {
  const headers = new Headers(response.headers);
  headers.set(CACHED_AT_HEADER, new Date().toISOString());

  return new Response(await response.blob(), {
    status: response.status,
    statusText: response.statusText,
    headers,
  });
};

const enforcePageBudget = async (cache) => {
  const keys = await cache.keys();
  const excess = keys.length - MAX_CACHED_PAGES;
  if (excess <= 0) {
    return;
  }

  await Promise.all(keys.slice(0, excess).map((request) => cache.delete(request)));
};

const storePage = async (request, response) => {
  const scope = response.headers.get(SCOPE_HEADER);
  // No scope means no middleware vouched for this response, and the worker has nowhere safe to
  // put it.
  if (!scope) {
    return;
  }

  const cache = await adoptPagesScope(scope);
  const page = await asCacheablePage(response);

  // Below the budget a plain put is enough, and it replaces the entry in place - leaving no moment
  // in which the page is in neither state. Only once eviction is in play does the order of
  // `cache.keys()` matter, and re-inserting is the only way to make that order say "last visited".
  if ((await cache.keys()).length >= MAX_CACHED_PAGES) {
    await cache.delete(request);
  }

  await cache.put(request, page);
  await enforcePageBudget(cache);
};

const matchStoredPage = async (request) => {
  const name = await findPagesCacheName();
  if (!name) {
    return null;
  }

  const cache = await caches.open(name);
  // Vary is ignored on purpose. Django answers these pages with `Vary: Cookie, Accept-Language`,
  // and a warmed page is fetched by this worker rather than by a navigation, so the two never
  // agree on those headers and every warmed page would miss. What Cookie separates is the account,
  // and the cache is already partitioned by exactly that.
  return (await cache.match(request, {ignoreVary: true})) || null;
};

const networkFirstPage = async (request) => {
  try {
    const networkResponse = await fetch(request);
    if (networkResponse && networkResponse.ok) {
      await storePage(request, networkResponse.clone());
    }
    return networkResponse;
  } catch (error) {
    const storedPage = await matchStoredPage(request);
    if (storedPage) {
      return storedPage;
    }

    const offlineResponse = await caches.match(OFFLINE_URL);
    if (offlineResponse) {
      return offlineResponse;
    }

    throw error;
  }
};

const networkFirstAsset = async (request) => {
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

    throw error;
  }
};

self.addEventListener("fetch", (event) => {
  const {request} = event;

  if (request.method !== "GET") {
    return;
  }

  const normalisedRequestUrl = normalizeUrl(request.url);
  const isDocument = request.mode === "navigate" || request.destination === "document";
  // Answering an app asset from the cache first would strand the client on it for good: the URLs
  // carry no content hash (render_bundle emits bundles/<name>.bundle.js in every environment), so
  // no later build can invalidate the entry. The cache is the offline fallback, not the source.
  const isAppAsset =
    normalisedRequestUrl.startsWith(`${SAME_ORIGIN}${STATIC_URL_PREFIX}`) ||
    PRECACHE_URL_SET.has(normalisedRequestUrl);

  // Documents and assets go to separate caches: an asset is the same for everyone, a document
  // carries whatever the signed-in visitor was allowed to see.
  if (isDocument) {
    event.respondWith(networkFirstPage(request));
    return;
  }

  // Anything else is left to the browser. Nothing puts such a request in the cache, so there is no
  // offline copy to fall back to, and mediating it would only stall responses that are meant to
  // stay open - the dev server's reload stream among them.
  if (isAppAsset) {
    event.respondWith(networkFirstAsset(request));
  }
});

/*
 * Fill the page cache with the room's other pages, so a room is readable offline in full rather
 * than only where the visitor happened to click while connected.
 *
 * The worker fetches them rather than the page: a fetch() the page makes is not a navigation, so
 * the fetch handler would not recognise it as a document, and a visitor who navigates away
 * mid-warm would cancel the rest.
 */
const hasWindowClient = async () => (await self.clients.matchAll({type: "window"})).length > 0;

const warmPagesFromManifest = async (manifestUrl) => {
  const prefetchInit = {credentials: "same-origin", headers: {[PREFETCH_HEADER]: "1"}};
  let urls = [];

  try {
    const manifestResponse = await fetch(manifestUrl, prefetchInit);
    if (!manifestResponse.ok) {
      return;
    }
    const manifest = await manifestResponse.json();
    urls = Array.isArray(manifest.urls) ? manifest.urls : [];
  } catch (error) {
    return;
  }

  for (const url of urls) {
    // Nobody is looking any more. The pages would be cached for a window that is gone, and until
    // the list runs out the server keeps answering on its behalf - against whatever is asking now.
    if (!(await hasWindowClient())) {
      return;
    }

    // Keyed on a plain request, so a later navigation to the same URL finds it.
    const request = new Request(normalizeUrl(url));
    try {
      const response = await fetch(request, prefetchInit);
      if (response.ok) {
        await storePage(request, response);
      }
    } catch (error) {
      // The connection went away; the remaining pages would fail the same way.
      return;
    }
  }
};

self.addEventListener("message", (event) => {
  const data = event.data || {};

  if (data.type === "yamsa:scope" && typeof data.scope === "string" && data.scope) {
    event.waitUntil(adoptPagesScope(data.scope));
    return;
  }

  if (data.type === "yamsa:warm" && typeof data.manifestUrl === "string" && data.manifestUrl) {
    event.waitUntil(warmPagesFromManifest(data.manifestUrl));
    return;
  }

  if (data.type === "yamsa:replay") {
    event.waitUntil(replayOutbox());
    return;
  }

  if (data.type === "yamsa:purge-pages") {
    event.waitUntil(purgePagesCaches());
  }
});

/*
 * Replaying what the page could not send.
 *
 * Here rather than on the page because a queue that only drains while a tab is open is not a queue:
 * the visitor writes the expense in a dead spot and puts the phone away.
 */
const openOutbox = () =>
  new Promise((resolve, reject) => {
    const request = indexedDB.open(OUTBOX_DATABASE, OUTBOX_VERSION);
    request.onupgradeneeded = () => {
      const database = request.result;
      if (!database.objectStoreNames.contains(OUTBOX_STORE)) {
        database.createObjectStore(OUTBOX_STORE, {keyPath: "id"});
      }
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });

const withOutbox = async (mode, work) => {
  const database = await openOutbox();
  try {
    return await new Promise((resolve, reject) => {
      const transaction = database.transaction(OUTBOX_STORE, mode);
      const result = work(transaction.objectStore(OUTBOX_STORE));
      transaction.oncomplete = () => resolve(result.value);
      transaction.onerror = () => reject(transaction.error);
      transaction.onabort = () => reject(transaction.error);
    });
  } finally {
    database.close();
  }
};

const readOutbox = () =>
  withOutbox("readonly", (store) => {
    const request = store.getAll();
    const result = {};
    request.onsuccess = () => {
      result.value = request.result || [];
    };
    return result;
  });

const writeEntry = (entry) =>
  withOutbox("readwrite", (store) => {
    store.put(entry);
    return {value: entry};
  });

const dropEntry = (id) =>
  withOutbox("readwrite", (store) => {
    store.delete(id);
    return {value: id};
  });

const recordAttempt = (entry, status, lastError) =>
  writeEntry({...entry, status, lastError, attempts: (entry.attempts || 0) + 1});

/*
 * What a queued submission needs before it may go out: a token minted for the session that exists
 * now, and the account that session belongs to.
 */
const readSessionContext = async () => {
  try {
    const response = await fetch(SESSION_URL, {credentials: "same-origin"});
    if (!response.ok) {
      return null;
    }
    return await response.json();
  } catch (error) {
    return null;
  }
};

const rebuildBody = (entry, csrfToken) => {
  const body = new FormData();
  for (const [name, value] of entry.body) {
    // The captured token belongs to the session that rendered the form. Any sign-in since then
    // replaced the secret behind it, and the submission would be refused on a technicality.
    body.append(name, name === "csrfmiddlewaretoken" ? csrfToken : value);
  }
  return body;
};

const wasAnsweredWithSignIn = (response) => {
  try {
    return new URL(response.url).pathname === LOGIN_PATH;
  } catch (error) {
    return false;
  }
};

const sendEntry = async (entry, context) => {
  const response = await fetch(entry.url, {
    method: "POST",
    body: rebuildBody(entry, context.csrf_token),
    credentials: "same-origin",
    headers: {"X-CSRFToken": context.csrf_token},
  });

  if (wasAnsweredWithSignIn(response)) {
    // Nothing wrong with the entry; it just has nobody to be filed under right now.
    await recordAttempt(entry, "queued", "signed out");
    return "blocked";
  }

  // The view answers a booked expense with a redirect to the room. A 200 means it came back with
  // the form and its errors instead.
  if (response.ok && response.redirected) {
    await dropEntry(entry.id);
    return "sent";
  }

  if (response.status >= 500) {
    await recordAttempt(entry, "queued", `server ${response.status}`);
    return "retry";
  }

  // A closed room, a member who left, a category that is gone. Kept rather than dropped: it is the
  // visitor's expense, and only they can decide what happens to it.
  await recordAttempt(entry, "rejected", `refused ${response.status}`);
  return "rejected";
};

const announceOutboxChange = async (counts) => {
  const windows = await self.clients.matchAll({includeUncontrolled: true, type: "window"});
  windows.forEach((client) => client.postMessage({type: "yamsa:outbox-changed", ...counts}));
};

const drainOutbox = async () => {
  const entries = (await readOutbox()).filter((entry) => entry.status !== "rejected");
  if (!entries.length) {
    return;
  }

  const context = await readSessionContext();
  if (!context) {
    return;
  }

  const counts = {sent: 0, rejected: 0};

  for (const entry of entries) {
    // Queue and cache both outlive a session. Replaying this under whoever is signed in now would
    // book one person's expense against another.
    if (entry.scope && context.scope && entry.scope !== context.scope) {
      continue;
    }

    let outcome;
    try {
      outcome = await sendEntry(entry, context);
    } catch (error) {
      await recordAttempt(entry, "queued", "no connection");
      break;
    }

    if (outcome === "sent") {
      counts.sent += 1;
    } else if (outcome === "rejected") {
      counts.rejected += 1;
    } else if (outcome === "blocked") {
      break;
    }
  }

  if (counts.sent || counts.rejected) {
    await announceOutboxChange(counts);
  }
};

// One drain at a time: a sync event and an open page asking at the same moment would otherwise
// both send the same entry, and only the second would be recognised as a replay.
let drainInFlight = null;

const replayOutbox = () => {
  if (!drainInFlight) {
    drainInFlight = drainOutbox().finally(() => {
      drainInFlight = null;
    });
  }

  return drainInFlight;
};

self.addEventListener("sync", (event) => {
  if (event.tag === OUTBOX_SYNC_TAG) {
    event.waitUntil(replayOutbox());
  }
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
