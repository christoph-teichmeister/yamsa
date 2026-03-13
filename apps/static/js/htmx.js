import htmx from "htmx.org";

window.htmx = htmx;

await import("idiomorph/dist/idiomorph-ext.min.js");
htmx.process(document.body);
