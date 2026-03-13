import * as d3 from "d3";

// Expose d3 globally for legacy inline scripts so they can continue to draw before a module loader runs.
window.d3 = d3;

export default d3;
