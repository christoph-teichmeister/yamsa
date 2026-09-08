(function () {
  if (window.__yamsaHideOnScrollInitialized) {
    return;
  }
  window.__yamsaHideOnScrollInitialized = true;

  const TARGET_SELECTOR = '[data-hide-on-scroll]';
  const HIDDEN_ATTRIBUTE = 'data-scroll-hidden';
  // Trackpads and touch screens emit sub-pixel scroll events in both directions, so a single
  // event's sign is not a direction. Only a run of movement past this many pixels is one.
  const DIRECTION_THRESHOLD = 8;
  // Within these zones the element stays put whatever the direction: at the very top it has
  // nothing to make room for, and at the very bottom the reader has arrived and wants it.
  const TOP_REVEAL_ZONE = 24;
  const BOTTOM_REVEAL_ZONE = 48;
  // A lazy-loading list puts its sentinel at the end of what is loaded, so the reader crosses
  // that end on the way to every further batch. While one is pending, the end of the page is not
  // the end of the list, and treating it as one makes the element blink at every batch.
  const PENDING_CONTENT_SELECTOR = '[hx-trigger~="revealed"]';

  let lastScrollY = 0;
  let travelledSinceDirectionChange = 0;
  let frameRequested = false;

  const getTargets = () => document.querySelectorAll(TARGET_SELECTOR);

  const getMaxScrollY = () => {
    const doc = document.documentElement;
    const scrollHeight = Math.max(
      doc ? doc.scrollHeight : 0,
      document.body ? document.body.scrollHeight : 0
    );

    return Math.max(scrollHeight - window.innerHeight, 0);
  };

  // Overscroll bounce reports a scrollY outside the document, and the way back from it looks like
  // a direction change that never happened.
  const getScrollY = () => Math.min(Math.max(window.scrollY || 0, 0), getMaxScrollY());

  const setHidden = (hidden) => {
    getTargets().forEach((target) => {
      if (hidden) {
        target.setAttribute(HIDDEN_ATTRIBUTE, '');
      } else {
        target.removeAttribute(HIDDEN_ATTRIBUTE);
      }
    });
  };

  const reveal = () => {
    travelledSinceDirectionChange = 0;
    setHidden(false);
  };

  const update = () => {
    frameRequested = false;

    const maxScrollY = getMaxScrollY();
    const scrollY = getScrollY();
    const delta = scrollY - lastScrollY;
    lastScrollY = scrollY;

    // A page that does not scroll cannot express a direction, and its element must not disappear.
    if (maxScrollY <= TOP_REVEAL_ZONE) {
      reveal();
      return;
    }

    const atEndOfPage = scrollY >= maxScrollY - BOTTOM_REVEAL_ZONE;
    const hasPendingContent = document.querySelector(PENDING_CONTENT_SELECTOR) !== null;

    if (scrollY <= TOP_REVEAL_ZONE || (atEndOfPage && !hasPendingContent)) {
      reveal();
      return;
    }

    if (delta === 0) {
      return;
    }

    const reversed = (delta > 0) !== (travelledSinceDirectionChange > 0);
    travelledSinceDirectionChange = reversed ? delta : travelledSinceDirectionChange + delta;

    if (travelledSinceDirectionChange >= DIRECTION_THRESHOLD) {
      setHidden(true);
    } else if (travelledSinceDirectionChange <= -DIRECTION_THRESHOLD) {
      setHidden(false);
    }
  };

  const requestUpdate = () => {
    if (frameRequested) {
      return;
    }

    if (typeof window.requestAnimationFrame !== 'function') {
      update();
      return;
    }

    frameRequested = true;
    window.requestAnimationFrame(update);
  };

  // A hidden element keeps its place in the tab order, so focus has to bring it back — otherwise
  // it takes keyboard focus while invisible.
  const handleFocusIn = (event) => {
    if (event.target && event.target.closest && event.target.closest(TARGET_SELECTOR)) {
      reveal();
    }
  };

  const containsTarget = (element) => {
    if (!element || typeof element.querySelector !== 'function') {
      return false;
    }

    return (element.matches && element.matches(TARGET_SELECTOR)) || element.querySelector(TARGET_SELECTOR) !== null;
  };

  // A swapped-in page starts at the top (navigation.js scrolls there) and idiomorph can carry the
  // hidden attribute across, so the state has to be reset — but only for a swap that brought the
  // element with it. The transaction feed swaps its own batches in while the reader scrolls, and
  // resetting on those would pop the element back up on every loaded page.
  const handleSwap = (event) => {
    const detail = event ? event.detail : null;
    const target = detail && detail.target ? detail.target : null;

    if (target && !containsTarget(target)) {
      return;
    }

    lastScrollY = getScrollY();
    reveal();
  };

  lastScrollY = getScrollY();
  window.addEventListener('scroll', requestUpdate, { passive: true });
  window.addEventListener('resize', requestUpdate, { passive: true });
  document.addEventListener('focusin', handleFocusIn);
  document.addEventListener('htmx:afterSwap', handleSwap);
  document.addEventListener('htmx:historyRestore', handleSwap);
  requestUpdate();
})();
