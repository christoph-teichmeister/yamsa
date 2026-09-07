(function () {
  // Delegated from the document: the cards are swapped in and out by htmx when a friend is
  // toggled, so a listener bound to a button would be lost with the first swap.
  if (window.__yamsaSuggestedGuestsReady) {
    return;
  }
  window.__yamsaSuggestedGuestsReady = true;

  const INPUT_TARGET_SELECTOR = "[data-suggested-guest-inputs-target]";
  const INPUT_NAME = "suggested_guest_emails";

  document.addEventListener("click", (event) => {
    const button = event.target.closest("[data-suggested-guest-add]");
    if (!button) {
      return;
    }

    event.preventDefault();

    const email = button.dataset.suggestedGuestEmail;
    const container = document.querySelector(INPUT_TARGET_SELECTOR);
    if (!email || !container) {
      return;
    }

    const existingInput = container.querySelector(`[data-suggested-guest-input="${email}"]`);
    if (existingInput) {
      existingInput.remove();
      // aria-pressed is the whole state: both labels are already in the markup and the
      // group-aria-pressed variants pick the matching one, so nothing here assembles HTML.
      button.setAttribute("aria-pressed", "false");
      return;
    }

    const hiddenInput = document.createElement("input");
    hiddenInput.type = "hidden";
    hiddenInput.name = INPUT_NAME;
    hiddenInput.value = email;
    hiddenInput.dataset.suggestedGuestInput = email;
    container.appendChild(hiddenInput);

    button.setAttribute("aria-pressed", "true");
  });
})();
