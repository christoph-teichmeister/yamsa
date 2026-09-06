(function () {
  // The sheet arrives through an htmx swap, so this bundle can be evaluated more than once per
  // page load. The listeners below are delegated to the document and would otherwise stack up.
  if (window.__yamsaProfileSheetReady) {
    return;
  }
  window.__yamsaProfileSheetReady = true;

  const SHEET_SELECTOR = "[data-profile-sheet]";
  // Every control of the sheet except the CSRF token, which must stay enabled to be posted.
  const FIELD_SELECTOR = "input:not([type='hidden']), select, textarea";
  const PREVIEW_SELECTOR = "[data-profile-picture-preview]";
  const PLACEHOLDER_SELECTOR = "[data-profile-picture-placeholder]";

  // A select cannot be readonly and a disabled field is not submitted — so read mode disables the
  // controls that have no readonly state and relies on readonly for the rest.
  const lock = (field, locked) => {
    if (field.tagName === "SELECT" || field.type === "checkbox" || field.type === "file") {
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

  const resetPicturePreview = (sheet) => {
    const preview = sheet.querySelector(PREVIEW_SELECTOR);
    const placeholder = sheet.querySelector(PLACEHOLDER_SELECTOR);
    if (!preview) {
      return;
    }

    const originalSource = preview.dataset.originalSrc;
    if (originalSource) {
      preview.src = originalSource;
      preview.hidden = false;
    } else {
      preview.removeAttribute("src");
      preview.hidden = true;
    }
    if (placeholder) {
      placeholder.hidden = Boolean(originalSource);
    }
  };

  document.addEventListener("click", (event) => {
    const trigger = event.target.closest("[data-profile-edit], [data-profile-cancel]");
    if (!trigger) {
      return;
    }

    const sheet = trigger.closest(SHEET_SELECTOR);
    if (!sheet) {
      return;
    }

    if (trigger.matches("[data-profile-cancel]")) {
      sheet.reset();
      resetPicturePreview(sheet);
      setMode(sheet, "reading");
      return;
    }

    setMode(sheet, "editing");
  });

  document.addEventListener("change", (event) => {
    const fileInput = event.target;
    if (!fileInput.matches("input[type='file']") || !fileInput.closest(SHEET_SELECTOR)) {
      return;
    }

    const sheet = fileInput.closest(SHEET_SELECTOR);
    const preview = sheet && sheet.querySelector(PREVIEW_SELECTOR);
    if (!preview) {
      return;
    }

    const file = fileInput.files && fileInput.files[0];
    if (!file) {
      resetPicturePreview(sheet);
      return;
    }

    const placeholder = sheet.querySelector(PLACEHOLDER_SELECTOR);
    const reader = new FileReader();
    reader.onload = (loadEvent) => {
      const dataUrl = loadEvent.target && loadEvent.target.result;
      if (!dataUrl) {
        return;
      }

      preview.src = dataUrl;
      preview.hidden = false;
      if (placeholder) {
        placeholder.hidden = true;
      }
    };
    reader.readAsDataURL(file);
  });
})();
