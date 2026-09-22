(function () {
  // The transaction form arrives through an htmx swap, so this bundle can be evaluated more
  // than once per page load. The listener below is delegated to the document and would
  // otherwise stack up. An inline <script> in create.html itself is not an option here: idiomorph
  // fails to morph a literal <script> element out of the DOM cleanly, which silently aborts the
  // #body morph that follows a create-form submission (see #440).
  if (window.__yamsaTransactionSplitReady) {
    return;
  }
  window.__yamsaTransactionSplitReady = true;

  const TOTAL_INPUT_SELECTOR = "#total_value_input";
  const REFERENCE_INPUT_SELECTOR = "#reference_total_value_input";
  const ROW_VALUE_INPUT_SELECTOR = ".split-row input[name='value']";

  const formatDecimal = (value) => {
    const parsed = parseFloat(value);
    return (Number.isNaN(parsed) ? 0 : parsed).toFixed(2);
  };

  // Mirrors split_amount_exact() in apps/transaction/utils.py (ROUND_HALF_UP, remainder
  // distributed one cent at a time starting at row 0) in integer cents, so the client-side
  // preview matches what the server persists on submit.
  const splitEvenly = (totalStr, shareCount) => {
    const totalCents = Math.round(parseFloat(totalStr) * 100) || 0;
    const perCents = Math.round(totalCents / shareCount);
    const cents = new Array(shareCount).fill(perCents);
    let remainder = totalCents - perCents * shareCount;
    const step = remainder > 0 ? 1 : -1;
    let i = 0;
    while (remainder !== 0) {
      cents[i] += step;
      remainder -= step;
      i = (i + 1) % shareCount;
    }
    return cents.map((cent) => (cent / 100).toFixed(2));
  };

  // Splits the total evenly across the current split-rows whenever it changes, so hand-edited
  // shares only ever get overwritten by a total the visitor entered on purpose - never by adding
  // or removing a participant. A total edit is a deliberate reset: every row (dirty or not) goes
  // back to an equal share, and none of them count as hand-edited anymore.
  const applyEqualSplit = (totalInput, referenceInput) => {
    const rowValueInputs = document.querySelectorAll(ROW_VALUE_INPUT_SELECTOR);
    if (rowValueInputs.length === 0) {
      return;
    }
    const shares = splitEvenly(totalInput.value, rowValueInputs.length);
    rowValueInputs.forEach((input, index) => {
      input.value = shares[index];
      delete input.dataset.dirty;
    });
    referenceInput.value = formatDecimal(totalInput.value);
  };

  // Playwright's fill() (and some assistive input methods) only ever dispatch "input", never
  // "change" - listening to both keeps the live preview from silently going stale.
  const handleTotalInputEvent = (event) => {
    const totalInput = event.target.closest(TOTAL_INPUT_SELECTOR);
    if (!totalInput || !totalInput.form) {
      return;
    }
    const referenceInput = totalInput.form.querySelector(REFERENCE_INPUT_SELECTOR);
    if (!referenceInput) {
      return;
    }
    applyEqualSplit(totalInput, referenceInput);
  };

  // A row a visitor actually typed into keeps its amount when a participant is added or removed;
  // an untouched row is fair game to rebalance - otherwise removing someone silently leaves their
  // share stuck on whoever is left, instead of folding back into what's still unaccounted for.
  const markRowDirty = (event) => {
    const rowInput = event.target.closest(ROW_VALUE_INPUT_SELECTOR);
    if (rowInput) {
      rowInput.dataset.dirty = "true";
    }
  };

  // Splits whatever the total doesn't already account for (the sum of hand-edited rows) evenly
  // across the rows nobody has touched yet. Mirrors split_amount_exact() the same way
  // applyEqualSplit() does, just over a subset of the rows.
  const redistributeAmongUntouchedRows = () => {
    const totalInput = document.querySelector(TOTAL_INPUT_SELECTOR);
    if (!totalInput) {
      return;
    }

    const rowValueInputs = document.querySelectorAll(ROW_VALUE_INPUT_SELECTOR);
    const untouchedInputs = [];
    let dirtyCents = 0;
    rowValueInputs.forEach((input) => {
      if (input.dataset.dirty === "true") {
        dirtyCents += Math.round((parseFloat(input.value) || 0) * 100);
      } else {
        untouchedInputs.push(input);
      }
    });
    if (untouchedInputs.length === 0) {
      return;
    }

    const totalCents = Math.round(parseFloat(totalInput.value) * 100) || 0;
    const remainderCents = Math.max(totalCents - dirtyCents, 0);
    const shares = splitEvenly((remainderCents / 100).toFixed(2), untouchedInputs.length);
    untouchedInputs.forEach((input, index) => {
      input.value = shares[index];
    });
  };

  document.addEventListener("input", handleTotalInputEvent);
  document.addEventListener("change", handleTotalInputEvent);
  document.addEventListener("input", markRowDirty);
  document.addEventListener("change", markRowDirty);

  // "Add participant" swaps a new (untouched) row in via htmx; letting the afterSwap event
  // settle first is what makes the new row queryable here.
  document.addEventListener("htmx:afterSwap", redistributeAmongUntouchedRows);
  // The remove button deletes its own .split-row via a plain DOM removal (see navigation.js),
  // not an htmx swap, so there is no htmx event to hook into - deferring to the next tick is what
  // guarantees that removal has already happened by the time this runs, regardless of listener order.
  document.addEventListener("click", (event) => {
    if (event.target.closest("[data-split-row-remove]")) {
      window.setTimeout(redistributeAmongUntouchedRows, 0);
    }
  });
})();
