(function () {
  // Delegated from the document: dialogs live inside parts that htmx swaps in and out, so a
  // listener bound to an element would be lost with the first swap and stack up with the next.
  if (window.__yamsaDialogReady) {
    return;
  }
  window.__yamsaDialogReady = true;

  const DIALOG_SELECTOR = "[data-dialog]";

  // Keyed by dialog id, not element: a swap replaces the dialog element, and the opener may be
  // replaced along with it.
  const openers = new Map();

  document.addEventListener("click", (event) => {
    const trigger = event.target.closest("[data-dialog-open], [data-dialog-close]");

    if (trigger && trigger.matches("[data-dialog-open]")) {
      const dialog = document.getElementById(trigger.dataset.dialogOpen);
      if (dialog) {
        openers.set(dialog.id, trigger);
        dialog.showModal();
      }
      return;
    }

    if (trigger) {
      const dialog = trigger.closest(DIALOG_SELECTOR);
      if (dialog) {
        dialog.close();
      }
      return;
    }

    // A click on the backdrop lands on the dialog element itself, never on its content.
    if (event.target.matches && event.target.matches(DIALOG_SELECTOR)) {
      event.target.close();
    }
  });

  // The browser returns focus to the opener itself, but only while that element is still in the
  // document; when a swap removed it, focus would fall to <body> and a keyboard user loses their place.
  // `close` does not bubble, hence the capture phase.
  document.addEventListener(
    "close",
    (event) => {
      const dialog = event.target;
      if (!dialog.matches || !dialog.matches(DIALOG_SELECTOR) || dialog.open) {
        return; // Open again: the re-open below closed it on purpose.
      }
      const opener = openers.get(dialog.id);
      openers.delete(dialog.id);
      if (opener && opener.isConnected) {
        return;
      }
      const fallback = document.getElementById("base-content");
      if (fallback) {
        fallback.setAttribute("tabindex", "-1");
        fallback.focus({ preventScroll: true });
      }
    },
    true,
  );

  // A swap that replaces a dialog brings it back with the `open` attribute when it has to stay
  // open — which does not put it in the top layer, leaving the backdrop and Escape dead. Re-open
  // it properly; `:modal` is what tells a top-layer dialog from an inline one.
  document.addEventListener("htmx:afterSwap", (event) => {
    if (!event.target.querySelectorAll) {
      return;
    }
    event.target.querySelectorAll(DIALOG_SELECTOR).forEach((dialog) => {
      if (dialog.hasAttribute("open") && !dialog.matches(":modal")) {
        dialog.close();
        dialog.showModal();
      }
    });
  });
})();
