(function () {
  // The sheet arrives through an htmx swap, so this bundle can be evaluated more than once per
  // page load. The listeners below are delegated to the document and would otherwise stack up.
  if (window.__yamsaProfileSheetReady) {
    return;
  }
  window.__yamsaProfileSheetReady = true;

  const SHEET_SELECTOR = "[data-profile-sheet]";
  // Every control of the sheet except the CSRF token, which must stay enabled to be posted, and
  // the photo's file input, which belongs to the photo's own cycle rather than to edit mode.
  const FIELD_SELECTOR = "input:not([type='hidden']):not([type='file']), select, textarea";
  const DIALOG_SELECTOR = "[data-profile-photo-dialog]";

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
    sheet.dataset.profileMode = mode;
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
    const trigger = event.target.closest(
      "[data-profile-edit], [data-profile-cancel], [data-profile-photo-open], [data-profile-photo-close]",
    );
    if (!trigger) {
      return;
    }

    if (trigger.matches("[data-profile-photo-open]")) {
      const dialog = trigger.closest("#profile-photo").querySelector(DIALOG_SELECTOR);
      if (dialog) {
        dialog.showModal();
      }
      return;
    }

    if (trigger.matches("[data-profile-photo-close]")) {
      const dialog = trigger.closest(DIALOG_SELECTOR);
      if (dialog) {
        dialog.close();
      }
      return;
    }

    const sheet = trigger.closest(SHEET_SELECTOR);
    if (!sheet) {
      return;
    }

    if (trigger.matches("[data-profile-cancel]")) {
      sheet.reset();
      setMode(sheet, "reading");
      return;
    }

    setMode(sheet, "editing");
  });

  // A click on the backdrop lands on the dialog element itself, never on its content.
  document.addEventListener("click", (event) => {
    const dialog = event.target;
    if (dialog.matches && dialog.matches(DIALOG_SELECTOR)) {
      dialog.close();
    }
  });

  // The swap that answers an upload or a delete replaces the dialog, so a dialog that has to stay
  // open comes back with the `open` attribute — which does not put it in the top layer. Re-open it
  // properly so the backdrop and Escape keep working.
  document.addEventListener("htmx:afterSwap", (event) => {
    const dialog = event.target.querySelector && event.target.querySelector(DIALOG_SELECTOR);
    if (dialog && dialog.hasAttribute("open") && !dialog.matches(":modal")) {
      dialog.close();
      dialog.showModal();
    }
  });
})();
