(function () {
  // Password fields arrive with an htmx swap, so this bundle can be evaluated more than once per
  // page load. The listener below is delegated to the document and would otherwise stack up.
  if (window.__yamsaPasswordVisibilityReady) {
    return;
  }
  window.__yamsaPasswordVisibilityReady = true;

  document.addEventListener("click", (event) => {
    const toggle = event.target.closest("[data-password-toggle]");
    if (!toggle) {
      return;
    }

    const field = document.getElementById(toggle.dataset.passwordToggle);
    if (!field) {
      return;
    }

    const revealing = field.type === "password";
    field.type = revealing ? "text" : "password";
    // The label stays constant; aria-pressed carries the state, and the template swaps the icon
    // through group-aria-pressed.
    toggle.setAttribute("aria-pressed", String(revealing));
  });
})();
