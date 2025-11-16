(function () {
  const INPUT_TARGET_SELECTOR = "[data-suggested-guest-inputs-target]";
  const ADD_BUTTON_SELECTOR = "[data-suggested-guest-add]";
  const INPUT_NAME = "suggested_guest_emails";

  const buildButtonContent = (iconClass, label) => {
    return `<i class="bi ${iconClass} me-1"></i>${label}`;
  };

  const updateButtonState = (button, selected) => {
    const addLabel = button.dataset.addLabel || "Add";
    const addedLabel = button.dataset.addedLabel || "Added";

    button.setAttribute("aria-pressed", String(selected));
    button.classList.toggle("btn-success", selected);
    button.classList.toggle("btn-outline-primary", !selected);

    if (selected) {
      button.innerHTML = buildButtonContent("bi-check-circle", addedLabel);
    } else {
      button.innerHTML = buildButtonContent("bi-plus-circle", addLabel);
    }
  };

  const findContainer = () => document.querySelector(INPUT_TARGET_SELECTOR);

  document.addEventListener("click", (event) => {
    const button = event.target.closest(ADD_BUTTON_SELECTOR);
    if (!button) {
      return;
    }

    event.preventDefault();

    const email = button.dataset.suggestedGuestEmail;
    if (!email) {
      return;
    }

    const container = findContainer();
    if (!container) {
      return;
    }

    const existingInput = container.querySelector(`[data-suggested-guest-input="${email}"]`);
    if (existingInput) {
      existingInput.remove();
      updateButtonState(button, false);
      return;
    }

    const hiddenInput = document.createElement("input");
    hiddenInput.type = "hidden";
    hiddenInput.name = INPUT_NAME;
    hiddenInput.value = email;
    hiddenInput.dataset.suggestedGuestInput = email;
    container.appendChild(hiddenInput);

    updateButtonState(button, true);
  });
})();
