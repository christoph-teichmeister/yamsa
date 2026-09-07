(function () {
  // A sheet arrives through an htmx swap, so this bundle can be evaluated more than once per page
  // load. The listeners below are delegated to the document and would otherwise stack up.
  if (window.__yamsaSheetReady) {
    return;
  }
  window.__yamsaSheetReady = true;

  const SHEET_SELECTOR = "[data-sheet]";
  const ACTION_SELECTOR = "[data-sheet-save], [data-sheet-discard]";

  // Every field of the sheet is editable at all times; what the actions need to know is whether
  // anything differs from what was rendered. FormData reflects exactly what a submit would send.
  const snapshot = (sheet) => {
    const form = sheet.matches("form") ? sheet : sheet.querySelector("form");
    if (!form) {
      return null;
    }
    return new URLSearchParams(new FormData(form)).toString();
  };

  const pristineValues = new WeakMap();

  const syncActions = (sheet) => {
    const pristine = pristineValues.get(sheet);
    const changed = pristine !== undefined && snapshot(sheet) !== pristine;

    sheet.querySelectorAll(ACTION_SELECTOR).forEach((action) => {
      action.disabled = !changed;
    });
  };

  const remember = (sheet) => {
    pristineValues.set(sheet, snapshot(sheet));
    syncActions(sheet);
  };

  // The buttons render enabled: a disabled submit would make the sheet unsubmittable whenever this
  // bundle never runs, which is the one state the server cannot detect.
  const rememberEverySheet = (root) => {
    if (!root.querySelectorAll) {
      return;
    }
    if (root.matches && root.matches(SHEET_SELECTOR)) {
      remember(root);
    }
    root.querySelectorAll(SHEET_SELECTOR).forEach(remember);
  };

  document.addEventListener("input", (event) => {
    const sheet = event.target.closest && event.target.closest(SHEET_SELECTOR);
    if (sheet) {
      syncActions(sheet);
    }
  });

  document.addEventListener("change", (event) => {
    const sheet = event.target.closest && event.target.closest(SHEET_SELECTOR);
    if (sheet) {
      syncActions(sheet);
    }
  });

  document.addEventListener("click", (event) => {
    const discard = event.target.closest("[data-sheet-discard]");
    if (!discard) {
      return;
    }

    const sheet = discard.closest(SHEET_SELECTOR);
    if (!sheet) {
      return;
    }

    const form = sheet.matches("form") ? sheet : sheet.querySelector("form");
    if (form) {
      form.reset();
    }
    syncActions(sheet);
  });

  // A saved sheet is swapped back in and is pristine again by definition.
  document.addEventListener("htmx:afterSwap", (event) => rememberEverySheet(event.target));

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => rememberEverySheet(document));
  } else {
    rememberEverySheet(document);
  }
})();
