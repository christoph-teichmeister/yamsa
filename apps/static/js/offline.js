/*
 * Offline behaviour that belongs to the page rather than to the service worker.
 *
 * Three jobs: tell the worker which account the cached pages belong to, ask it to warm the room's
 * other pages, and say on the page itself when what is on screen came out of the cache.
 */
(function () {
  if (window.__yamsaOfflineInitialized) {
    return;
  }
  window.__yamsaOfflineInitialized = true;

  const STATE_SELECTOR = '[data-offline-state]';
  const BANNER_SELECTOR = '[data-offline-banner]';
  const HINT_SELECTOR = '[data-offline-hint]';
  const STALE_SELECTOR = '[data-offline-stale]';
  const CACHED_AT_SELECTOR = '[data-offline-cached-at]';

  // A room is warmed once per document, not once per navigation: htmx keeps this script alive
  // across the whole visit, and re-warming on every swap would multiply every page view by the
  // size of the manifest.
  const warmedManifests = new Set();

  const readState = () => document.querySelector(STATE_SELECTOR);

  const controller = () => (navigator.serviceWorker ? navigator.serviceWorker.controller : null);

  const postToWorker = (message) => {
    const worker = controller();
    if (worker) {
      worker.postMessage(message);
    }
  };

  // The worker keeps one page cache and names it after the account it belongs to. Nothing else
  // tells it that the account changed - a sign-out is an htmx request, which the worker does not
  // mediate - so every page reports its own scope and the worker drops what does not match.
  const reportScope = (state) => {
    const scope = state.dataset.pwaScope;
    if (scope) {
      postToWorker({type: 'yamsa:scope', scope});
    }
  };

  const whenIdle = (callback) => {
    if (typeof window.requestIdleCallback === 'function') {
      window.requestIdleCallback(callback, {timeout: 5000});
      return;
    }

    window.setTimeout(callback, 1000);
  };

  const requestWarmUp = (state) => {
    const manifestUrl = state.dataset.offlineManifestUrl;
    if (!manifestUrl || !navigator.onLine || warmedManifests.has(manifestUrl)) {
      return;
    }

    warmedManifests.add(manifestUrl);
    whenIdle(() => postToWorker({type: 'yamsa:warm', manifestUrl}));
  };

  const formatCachedAt = (value) => {
    if (!value) {
      return null;
    }

    const cachedAt = new Date(value);
    if (Number.isNaN(cachedAt.getTime())) {
      return null;
    }

    const isToday = cachedAt.toDateString() === new Date().toDateString();
    return isToday
      ? cachedAt.toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'})
      : cachedAt.toLocaleString();
  };

  const readCachedAt = async (state) => {
    const headerName = state.dataset.cachedAtHeader;
    if (!headerName || !('caches' in window)) {
      return null;
    }

    try {
      // Same reason the worker ignores Vary when it reads this cache back: a warmed page was
      // fetched by the worker, not by this navigation, so the two never agree on Cookie or
      // Accept-Language.
      const cached = await caches.match(window.location.href, {ignoreVary: true});
      return cached ? cached.headers.get(headerName) : null;
    } catch (error) {
      // Reading cache storage throws rather than answering empty when the browser blocks site
      // data, which some private-browsing modes do.
      return null;
    }
  };

  const isOffline = () => document.documentElement.dataset.connection === 'offline';

  const renderBanner = async () => {
    const state = readState();
    const banner = document.querySelector(BANNER_SELECTOR);
    if (!state || !banner) {
      return;
    }

    if (!isOffline()) {
      banner.hidden = true;
      return;
    }

    const hint = banner.querySelector(HINT_SELECTOR);
    const stale = banner.querySelector(STALE_SELECTOR);
    const cachedAtElement = banner.querySelector(CACHED_AT_SELECTOR);
    const cachedAt = formatCachedAt(await readCachedAt(state));

    if (cachedAt && stale && cachedAtElement && hint) {
      cachedAtElement.textContent = cachedAt;
      cachedAtElement.setAttribute('datetime', cachedAt);
      stale.hidden = false;
      hint.hidden = true;
    }

    banner.hidden = false;
  };

  const setConnectionState = (online) => {
    document.documentElement.dataset.connection = online ? 'online' : 'offline';
    renderBanner();
  };

  const refresh = () => {
    const state = readState();
    if (!state) {
      return;
    }

    renderBanner();
    reportScope(state);
    requestWarmUp(state);
  };

  const init = () => {
    setConnectionState(navigator.onLine);
    refresh();

    window.addEventListener('online', () => setConnectionState(true));
    window.addEventListener('offline', () => setConnectionState(false));

    // A failed send outranks navigator.onLine, which reports a network the device is attached to
    // rather than one that reaches the server.
    document.addEventListener('htmx:sendError', () => setConnectionState(false));

    // Every swap replaces #base-content, and with it the markup this module writes into.
    document.body.addEventListener('htmx:afterSwap', refresh);
    document.body.addEventListener('htmx:historyRestore', refresh);

    if (navigator.serviceWorker) {
      // Before a worker controls the page there is nobody to report the scope to, and the load
      // right after a registration is when the account is most likely to have changed.
      navigator.serviceWorker.addEventListener('controllerchange', refresh);
    }
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
