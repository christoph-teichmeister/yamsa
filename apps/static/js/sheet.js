(function () {
  // A sheet arrives through an htmx swap, so this bundle can be evaluated more than once per page
  // load. The listener below is delegated to the document and would otherwise stack up.
  if (window.__yamsaSheetReady) {
    return;
  }
  window.__yamsaSheetReady = true;

  const SHEET_SELECTOR = "[data-sheet]";
  // Every control of the sheet except hidden ones — the CSRF token has to stay enabled to be
  // posted — and file inputs, which belong to a sub-cycle of their own rather than to edit mode.
  const FIELD_SELECTOR = "input:not([type='hidden']):not([type='file']), select, textarea";

  // A select cannot be readonly and a disabled field is not submitted — so read mode disables the
  // controls that have no readonly state and relies on readonly for the rest.
  const lock = (field, locked) => {
    if (field.tagName === "SELECT" || field.type === "checkbox") {
      field.disabled = locked;
      return;
    }
    field.readOnly = locked;
  };

  const setMode = (sheet, mode) => {
    const editing = mode === "editing";
    sheet.dataset.sheetMode = mode;
    sheet.querySelectorAll(FIELD_SELECTOR).forEach((field) => lock(field, !editing));

    if (!editing) {
      return;
    }

    const firstField = sheet.querySelector(FIELD_SELECTOR);
    if (firstField) {
      // preventScroll: the fields are already on screen, jumping the page would only disorient.
      firstField.focus({ preventScroll: true });
    }
  };

  document.addEventListener("click", (event) => {
    const trigger = event.target.closest("[data-sheet-edit], [data-sheet-cancel]");
    if (!trigger) {
      return;
    }

    const sheet = trigger.closest(SHEET_SELECTOR);
    if (!sheet) {
      return;
    }

    if (trigger.matches("[data-sheet-cancel]")) {
      // The sheet is a form itself on the profile and holds one on the room, so reset whichever
      // of the two carries the fields.
      sheet.querySelectorAll("form").forEach((form) => form.reset());
      if (typeof sheet.reset === "function") {
        sheet.reset();
      }
      setMode(sheet, "reading");
      return;
    }

    setMode(sheet, "editing");
  });
})();
