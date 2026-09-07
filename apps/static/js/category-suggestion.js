(function () {
  // The transaction form arrives through an htmx swap, so this bundle can be evaluated more
  // than once per page load. The listeners below are delegated to the document and would
  // otherwise stack up.
  if (window.__yamsaCategorySuggestionReady) {
    return;
  }
  window.__yamsaCategorySuggestionReady = true;

  const FIELD_SELECTOR = "[data-category-field]";
  const DESCRIPTION_SELECTOR = "[name='description']";
  const HINT_SELECTOR = "[data-category-suggestion-hint]";
  const MINIMUM_KEYWORD_LENGTH = 3;
  const DEBOUNCE_MS = 200;

  // Mirrors normalize_keyword() in apps/transaction/services/category_suggestion_service.py.
  const normalize = (value) =>
    value
      .normalize("NFKD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLowerCase();

  const readIndex = (field) => {
    try {
      return JSON.parse(field.dataset.categorySuggestionIndex) || {};
    } catch (error) {
      return {};
    }
  };

  const findSuggestion = (index, description) => {
    const normalized = normalize(description);
    if (index[normalized]) {
      return index[normalized];
    }

    const tokens = normalized.split(/[^a-z0-9]+/).filter((token) => token.length >= MINIMUM_KEYWORD_LENGTH);
    // Longest first, so "supermarkt" wins over a shorter keyword that also appears.
    tokens.sort((first, second) => second.length - first.length);

    for (const token of tokens) {
      if (index[token]) {
        return index[token];
      }
    }
    return null;
  };

  // The hint is hidden through the attribute rather than a utility class: a class would leave
  // whichever framework the field is styled with in charge of whether the hint is visible.
  const toggleHint = (field, visible) => {
    const hint = field.querySelector(HINT_SELECTOR);
    if (hint) {
      hint.hidden = !visible;
    }
  };

  const markAsUserChoice = (field) => {
    field.dataset.categoryUserChoice = "true";
    delete field.dataset.categorySuggested;
    toggleHint(field, false);
  };

  const withdrawSuggestion = (field) => {
    const suggested = field.querySelector(`input[type='radio'][value='${field.dataset.categorySuggested}']`);
    if (suggested) {
      suggested.checked = false;
    }
    delete field.dataset.categorySuggested;
    toggleHint(field, false);
  };

  const suggestFor = (field, description) => {
    if (field.dataset.categoryUserChoice === "true") {
      return;
    }

    // A category that is checked but was not put there by this module comes from the user or
    // from a server round trip echoing their choice, and outranks any suggestion.
    const checked = field.querySelector("input[type='radio']:checked");
    if (checked && checked.value !== field.dataset.categorySuggested) {
      markAsUserChoice(field);
      return;
    }

    const categoryId = findSuggestion(readIndex(field), description);
    const radio =
      categoryId === null ? null : field.querySelector(`input[type='radio'][value='${categoryId}']`);

    if (!radio) {
      // The description no longer implies a category, so an earlier guess must not stand: it
      // would file the expense under something the user never picked.
      withdrawSuggestion(field);
      return;
    }

    radio.checked = true;
    field.dataset.categorySuggested = radio.value;
    toggleHint(field, true);
  };

  let debounceHandle = null;

  document.addEventListener("input", (event) => {
    const description = event.target.closest(DESCRIPTION_SELECTOR);
    if (!description || !description.form) {
      return;
    }

    const field = description.form.querySelector(FIELD_SELECTOR);
    if (!field) {
      return;
    }

    window.clearTimeout(debounceHandle);
    debounceHandle = window.setTimeout(() => suggestFor(field, description.value), DEBOUNCE_MS);
  });

  document.addEventListener("change", (event) => {
    const radio = event.target.closest("input[type='radio']");
    // Only a real click counts as a decision: checking a radio from script fires no change event.
    if (!radio || !event.isTrusted) {
      return;
    }

    const field = radio.closest(FIELD_SELECTOR);
    if (field) {
      markAsUserChoice(field);
    }
  });
})();
