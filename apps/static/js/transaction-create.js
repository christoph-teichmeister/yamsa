// Combined entry point for the transaction create page. Kept as a single bundle/script tag on
// purpose: idiomorph fails to morph #body cleanly when create.html carries more than one
// page-specific trailing <script> element that list.html (the page it morphs into after a
// submit) does not have a matching counterpart for - see #440. category-suggestion.js and
// transaction-split.js stay separate source files for readability; only their combined output
// is ever referenced from create.html.
import "./category-suggestion.js";
import "./transaction-split.js";
