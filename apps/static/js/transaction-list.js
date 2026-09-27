// The transaction list's feed loader and its #transaction-<id> highlight. Loaded from base.html
// rather than inline in list.html: idiomorph morphs an inline <script> of the page it leaves into
// list.html's instead of inserting a new one, and a morphed script never runs - arriving from the
// category breakdown or "Who paid what" left the feed on its skeleton. See also #440.
(function () {
  if (window.__yamsaTransactionListReady) {
    return;
  }
  window.__yamsaTransactionListReady = true;

  // A transaction linked with #transaction-<id> has to be found and pointed out after the
  // feed has been swapped in, which is why this cannot be a scroll-margin and a :target rule.
  function highlightTransactionRow(target) {
    if (!target) {
      return;
    }

    // The attribute, not a class: the row's own utilities decide what a highlight looks like.
    target.removeAttribute('data-highlight');
    // force reflow
    void target.offsetWidth;
    target.setAttribute('data-highlight', '');

    window.setTimeout(function () {
      target.removeAttribute('data-highlight');
    }, 2400);
  }

  function getScrollOffset() {
    var fixedHeader = document.querySelector('nav.navbar.fixed-top');
    var headerHeight = fixedHeader ? fixedHeader.offsetHeight : 0;
    var safetyGap = 16;

    return headerHeight + safetyGap;
  }

  function focusTransactionFromHash() {
    var hash = window.location.hash;

    if (!hash || hash === '#') {
      return;
    }

    var target = document.querySelector(hash) || document.querySelector('[name="' + hash.slice(1) + '"]');

    if (target) {
      var offset = target.getBoundingClientRect().top + window.scrollY - getScrollOffset();

      window.scrollTo({
        top: Math.max(offset, 0),
        behavior: 'smooth'
      });

      highlightTransactionRow(target);
    }
  }

  function triggerTransactionFocus() {
    window.requestAnimationFrame(focusTransactionFromHash);
  }

  // idiomorph matches #transaction-feed by id and morphs it in place instead of replacing
  // it, so htmx never sees it as newly inserted and its `load` trigger (a one-shot,
  // per-node signal) never fires again - re-picking the tab you're already on left the feed
  // stuck on its unfetched skeleton markup. Firing the same GET manually on every #body swap
  // covers both that case and a genuinely fresh navigation into the tab.
  function isBodySwapTarget(target) {
    if (!target) {
      return false;
    }
    if (target === document.body) {
      return true;
    }
    var targetId = typeof target.id === 'string' ? target.id.toLowerCase() : '';
    return targetId === 'body';
  }

  function loadTransactionFeed(event) {
    if (event) {
      var detail = event.detail || {};
      if (!isBodySwapTarget(detail.target)) {
        return;
      }
    }

    var feed = document.getElementById('transaction-feed');
    // Two #body swaps in quick succession would otherwise send two requests racing for the
    // same target.
    // window.htmx, never the bare name: webpack's ProvidePlugin would bundle a second htmx
    // instance for it, without the morph extension the page's own instance has registered.
    if (!feed || !window.htmx || feed.dataset.feedReloading === 'true') {
      return;
    }

    feed.dataset.feedReloading = 'true';
    window.htmx.ajax('GET', feed.getAttribute('hx-get'), {
      source: feed,
      target: feed,
      swap: 'innerHTML',
    }).finally(function () {
      delete feed.dataset.feedReloading;
    });
  }

  document.addEventListener('htmx:afterSwap', triggerTransactionFocus);
  document.addEventListener('htmx:historyRestore', triggerTransactionFocus);
  document.addEventListener('htmx:afterSwap', loadTransactionFeed);
  document.addEventListener('htmx:historyRestore', function () {
    loadTransactionFeed(null);
  });

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () {
      triggerTransactionFocus();
      loadTransactionFeed(null);
    });
  } else {
    triggerTransactionFocus();
    loadTransactionFeed(null);
  }
})();
