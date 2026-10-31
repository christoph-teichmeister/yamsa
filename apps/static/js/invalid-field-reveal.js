// iOS Safari blocks a submit that fails constraint validation (required, min, step...) without
// showing anything, so the submit button looks dead. This takes over the reporting for every
// browser: the first invalid field is revealed, focused and explained inline, and every invalid
// field stays marked until it is corrected.
(function () {
  // Loaded through the navigation bundle, which htmx can evaluate again on a swap; a second set of
  // listeners would report every field twice.
  if (window.__yamsaInvalidFieldRevealReady) {
    return;
  }
  window.__yamsaInvalidFieldRevealReady = true;

  const MESSAGE_ATTRIBUTE = "data-invalid-field-message";
  // Literal class strings so Tailwind's @source scan of this file generates them. A ring rather
  // than a border colour: it cannot lose to the field's own border utility.
  const FIELD_INVALID_CLASSES = ["ring-2", "ring-danger-text"];
  const MESSAGE_CLASSES = "mt-1.5 mb-0 text-sm text-danger-text";

  let revealedThisRound = false;
  let messageCount = 0;

  const isRadio = (field) => field.type === "radio";

  // Where the message goes, always right after the returned element: a radio's message belongs to
  // its whole group, so it follows the smallest element holding every option; a field inside a
  // `.relative` wrapper (currency sign, chevron) gets it below the wrapper, not inside the
  // positioned box.
  const messageAnchor = (field) => {
    if (isRadio(field)) {
      const group = groupOf(field);
      let container = field.parentElement;
      while (container.parentElement && !group.every((member) => container.contains(member))) {
        container = container.parentElement;
      }
      return container;
    }
    const wrapper = field.parentElement;
    return wrapper && wrapper.classList.contains("relative") ? wrapper : field;
  };

  const messageKey = (field) => (isRadio(field) ? `radio:${field.name}` : field.id || field.name);

  const findMessage = (field) => {
    const form = field.form || document;
    return Array.from(form.querySelectorAll(`[${MESSAGE_ATTRIBUTE}]`)).find(
      (element) => element.getAttribute(MESSAGE_ATTRIBUTE) === messageKey(field),
    );
  };

  const groupOf = (field) => {
    if (!isRadio(field) || !field.form) {
      return [field];
    }
    return Array.from(field.form.elements).filter((element) => element.name === field.name);
  };

  const showMessage = (field) => {
    const message = findMessage(field) || document.createElement("p");
    message.setAttribute(MESSAGE_ATTRIBUTE, messageKey(field));
    message.className = MESSAGE_CLASSES;
    if (!message.id) {
      messageCount += 1;
      message.id = `invalid-field-message-${messageCount}`;
    }
    // The browser's own message is already in the visitor's language.
    message.textContent = field.validationMessage;

    const anchor = messageAnchor(field);
    if (!message.isConnected) {
      anchor.insertAdjacentElement("afterend", message);
    }

    groupOf(field).forEach((member) => {
      member.setAttribute("aria-invalid", "true");
      member.setAttribute("aria-describedby", message.id);
      if (!isRadio(member)) {
        member.classList.add(...FIELD_INVALID_CLASSES);
      }
    });
  };

  const clearMessage = (field) => {
    const message = findMessage(field);
    if (message) {
      message.remove();
    }
    groupOf(field).forEach((member) => {
      member.removeAttribute("aria-invalid");
      member.removeAttribute("aria-describedby");
      member.classList.remove(...FIELD_INVALID_CLASSES);
    });
  };

  const reveal = (field) => {
    // A closed <details> keeps its fields in the form but makes them unfocusable and invisible.
    let details = field.closest("details");
    while (details) {
      details.open = true;
      details = details.parentElement && details.parentElement.closest("details");
    }
    const target = isRadio(field) ? messageAnchor(field) : field;
    target.scrollIntoView({ block: "center", behavior: "smooth" });
    field.focus({ preventScroll: true });
  };

  // `invalid` does not bubble, hence the capture phase.
  document.addEventListener(
    "invalid",
    (event) => {
      const field = event.target;
      if (!(field instanceof HTMLElement) || !field.form) {
        return;
      }
      // Replaces the native bubble, which iOS never shows and which would otherwise appear next
      // to the inline message everywhere else.
      event.preventDefault();
      showMessage(field);

      // One submit attempt fires `invalid` once per invalid field, synchronously; only the first
      // of them is scrolled to.
      if (!revealedThisRound) {
        revealedThisRound = true;
        reveal(field);
        window.setTimeout(() => {
          revealedThisRound = false;
        }, 0);
      }
    },
    true,
  );

  const recheck = (event) => {
    const field = event.target;
    if (!(field instanceof HTMLElement) || field.getAttribute("aria-invalid") !== "true") {
      return;
    }
    if (field.validity.valid) {
      clearMessage(field);
    } else {
      showMessage(field);
    }
  };

  document.addEventListener("input", recheck);
  document.addEventListener("change", recheck);
})();
