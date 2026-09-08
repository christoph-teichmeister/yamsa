/*
 * Offline behaviour that belongs to the page rather than to the service worker.
 *
 * Three jobs: tell the worker which account the cached pages belong to, ask it to warm the room's
 * other pages, and say on the page itself when what is on screen came out of the cache.
 */
import {OUTBOX_SYNC_TAG, buildEntry, putEntry, readEntries} from './outbox.js';

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
  const QUEUEABLE_FORM_SELECTOR = 'form[data-offline-queue]';
  const PENDING_SELECTOR = '[data-outbox-pending]';
  const PENDING_LIST_SELECTOR = '[data-outbox-pending-list]';
  const PENDING_HEADLINE_SELECTOR = '[data-outbox-pending-headline]';
  const PENDING_ROW_TEMPLATE_SELECTOR = '[data-outbox-pending-row]';
  const MANUAL_SEND_HINT_SELECTOR = '[data-outbox-manual-send-hint]';

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

  const showToast = (state, messageKey) => {
    const message = state.dataset[messageKey];
    if (!message) {
      return;
    }

    document.body.dispatchEvent(
      new CustomEvent('triggerToast', {
        detail: {message, type: state.dataset.toastInfoClass || ''},
      })
    );
  };

  const summarize = (form) => {
    const description = form.querySelector('[name="description"]');
    const value = form.querySelector('[name="value"]');
    const parts = [description && description.value, value && value.value].filter(Boolean);
    return parts.join(' · ');
  };

  /*
   * Take a submission the app could not send and answer as if it had gone through.
   *
   * The stored body is the same one the form would have posted, replayed later against the same
   * view - there is no second write path to keep in step with this one. It carries the submission's
   * client_request_id, which is what keeps the expense booked once if the first attempt turns out
   * to have reached the server after all.
   */
  const queueSubmission = async (form) => {
    const state = readState();
    if (!state) {
      return false;
    }

    try {
      await putEntry(
        buildEntry({
          form,
          url: form.getAttribute('action') || window.location.href,
          roomSlug: form.dataset.offlineQueueRoom || '',
          scope: state.dataset.pwaScope || '',
          summary: summarize(form),
        })
      );
    } catch (error) {
      // Without a queue there is nothing to promise, so let the failure be visible rather than
      // telling the visitor their expense is safe.
      console.error('Unable to queue the submission', error);
      return false;
    }

    showToast(state, 'queuedMessage');

    // Background Sync drains the queue without a tab open. Where it does not exist - every browser
    // on iOS - the queue waits for the app to be opened again, which is what the online listener
    // and the load-time replay below cover.
    if ('SyncManager' in window && navigator.serviceWorker) {
      try {
        const registration = await navigator.serviceWorker.ready;
        await registration.sync.register(OUTBOX_SYNC_TAG);
      } catch (error) {
        // Registration is a nicety; the queue drains on the next visit either way.
      }
    }

    return true;
  };

  const renderPending = async () => {
    const container = document.querySelector(PENDING_SELECTOR);
    const rowTemplate = document.querySelector(PENDING_ROW_TEMPLATE_SELECTOR);
    if (!container || !rowTemplate) {
      return;
    }

    let entries = [];
    try {
      entries = await readEntries();
    } catch (error) {
      container.hidden = true;
      return;
    }

    const roomSlug = container.dataset.outboxRoom || '';
    const mine = entries.filter((entry) => entry.roomSlug === roomSlug);
    const list = container.querySelector(PENDING_LIST_SELECTOR);
    const headline = container.querySelector(PENDING_HEADLINE_SELECTOR);

    if (!mine.length || !list || !headline) {
      container.hidden = true;
      return;
    }

    headline.textContent =
      mine.length === 1
        ? container.dataset.outboxHeadlineOne
        : `${mine.length} ${container.dataset.outboxHeadlineMany}`;
    list.replaceChildren(
      ...mine.map((entry) => {
        const row = rowTemplate.content.cloneNode(true);
        row.querySelector('[data-outbox-row-summary]').textContent = entry.summary;
        row.querySelector('[data-outbox-row-state]').textContent =
          entry.status === 'rejected' ? container.dataset.outboxRejected : container.dataset.outboxWaiting;
        return row;
      })
    );
    const manualSendHint = container.querySelector(MANUAL_SEND_HINT_SELECTOR);
    if (manualSendHint) {
      manualSendHint.hidden = 'SyncManager' in window;
    }

    container.hidden = false;
  };

  const askWorkerToReplay = () => postToWorker({type: 'yamsa:replay'});

  const refresh = () => {
    const state = readState();
    if (!state) {
      return;
    }

    renderBanner();
    renderPending();
    reportScope(state);
    requestWarmUp(state);
  };

  const queueableFormOf = (event) => {
    const element = event.detail && event.detail.elt ? event.detail.elt : event.target;
    if (!element || typeof element.closest !== 'function') {
      return null;
    }

    return element.closest(QUEUEABLE_FORM_SELECTOR);
  };

  const leaveForm = (form) => {
    const destination = form.dataset.offlineQueueRedirect;
    if (destination) {
      // A full navigation rather than an htmx swap: offline it is the service worker that answers
      // it, out of the pages it saved.
      window.location.assign(destination);
    }
  };

  const init = () => {
    setConnectionState(navigator.onLine);
    refresh();

    window.addEventListener('online', () => {
      setConnectionState(true);
      askWorkerToReplay();
    });
    window.addEventListener('offline', () => setConnectionState(false));

    // Held back rather than sent and mourned: the request cannot reach the server, and letting it
    // fail first would only cost the visitor the error toast on the way to the same queue.
    document.addEventListener('htmx:confirm', (event) => {
      const form = queueableFormOf(event);
      if (!form || navigator.onLine) {
        return;
      }

      event.preventDefault();
      queueSubmission(form).then((queued) => {
        if (queued) {
          leaveForm(form);
        }
      });
    });

    // A failed send outranks navigator.onLine, which reports a network the device is attached to
    // rather than one that reaches the server.
    document.addEventListener('htmx:sendError', (event) => {
      setConnectionState(false);

      const form = queueableFormOf(event);
      if (!form) {
        return;
      }

      queueSubmission(form).then((queued) => {
        if (queued) {
          leaveForm(form);
        }
      });
    });

    // Every swap replaces #base-content, and with it the markup this module writes into.
    document.body.addEventListener('htmx:afterSwap', refresh);
    document.body.addEventListener('htmx:historyRestore', refresh);

    if (navigator.serviceWorker) {
      // Before a worker controls the page there is nobody to report the scope to, and the load
      // right after a registration is when the account is most likely to have changed.
      navigator.serviceWorker.addEventListener('controllerchange', refresh);

      navigator.serviceWorker.addEventListener('message', (event) => {
        const data = event.data || {};
        if (data.type !== 'yamsa:outbox-changed') {
          return;
        }

        const state = readState();
        if (state && data.sent) {
          showToast(state, 'sentMessage');
        }
        if (state && data.rejected) {
          showToast(state, 'rejectedMessage');
        }
        renderPending();
      });

      askWorkerToReplay();
    }
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
