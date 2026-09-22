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
  // or removing a participant.
  const applyEqualSplit = (totalInput, referenceInput) => {
    const rowValueInputs = document.querySelectorAll(".split-row input[name='value']");
    if (rowValueInputs.length === 0) {
      return;
    }
    const shares = splitEvenly(totalInput.value, rowValueInputs.length);
    rowValueInputs.forEach((input, index) => {
      input.value = shares[index];
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

  document.addEventListener("input", handleTotalInputEvent);
  document.addEventListener("change", handleTotalInputEvent);
})();
