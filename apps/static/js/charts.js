// Draws the d3 charts of the category breakdown and "Who paid what" wherever they turn up, on a
// full page load or after any htmx swap - the spending timeline arrives by one of its own. Loaded
// once from base.html; d3 itself is only fetched once a page actually carries a chart.
import { renderCategoryBreakdownCharts } from "./charts/category-breakdown-chart.js";
import { renderSpendingTrendChart } from "./charts/spending-trend-chart.js";

(function () {
  if (window.__yamsaChartsReady) {
    return;
  }
  window.__yamsaChartsReady = true;

  const CHART_SELECTOR = "[data-transaction-category-chart], #trend-line-chart";
  let d3Loading = null;

  const renderCharts = () => {
    if (!document.querySelector(CHART_SELECTOR)) {
      return;
    }
    d3Loading = d3Loading || import(/* webpackChunkName: "d3" */ "d3");
    d3Loading.then((d3) => {
      renderCategoryBreakdownCharts(d3);
      renderSpendingTrendChart(d3);
    });
  };

  document.addEventListener("htmx:afterSwap", renderCharts);
  document.addEventListener("htmx:historyRestore", renderCharts);

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", renderCharts);
  } else {
    renderCharts();
  }
})();
