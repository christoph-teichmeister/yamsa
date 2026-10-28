// A second click while the first POST is in flight would send the form twice.
document.addEventListener("submit", (event) => {
  if (event.defaultPrevented) {
    return;
  }
  event.target.querySelectorAll("[data-disable-on-submit]").forEach((button) => {
    button.disabled = true;
  });
});

// The back button restores the page from bfcache with the button still disabled.
window.addEventListener("pageshow", (event) => {
  if (event.persisted) {
    document.querySelectorAll("[data-disable-on-submit]").forEach((button) => {
      button.disabled = false;
    });
  }
});
