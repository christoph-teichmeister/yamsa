// The category breakdown's donut, one per currency. Rendered by charts.js rather than from an
// inline <script> in category_breakdown.html: idiomorph morphs such a script into the next page's
// instead of inserting it, and a morphed script never runs (#440). The container carries the
// strings and the bucket colour the template used to write into the script.



// getComputedTextLength() returns 0 while the SVG is not laid out (e.g. inside a
// hidden tab), which would collapse every label into a single overflowing line.
// Fall back to an average-glyph estimate so wrapping still happens.
const measureText = (probe, text, fontSize) => {
    probe.text(text).attr("font-size", fontSize);
    const measured = probe.node().getComputedTextLength();
    return measured || text.length * fontSize * 0.6;
};

// The amount and the share are single tokens: they cannot wrap, so they shrink instead.
const fitFontSize = (probe, text, fontSize, maxWidth) => {
    const measured = measureText(probe, text, fontSize);
    if (measured <= maxWidth) {
        return fontSize;
    }
    return Math.max(9, fontSize * (maxWidth / measured));
};

const splitIntoLines = (probe, text, fontSize, maxWidth) => {
    const words = text.split(/\s+/).filter(Boolean);
    const lines = [];
    let current = "";
    words.forEach(word => {
        const candidate = current ? `${current} ${word}` : word;
        if (current && measureText(probe, candidate, fontSize) > maxWidth) {
            lines.push(current);
            current = word;
        } else {
            current = candidate;
        }
    });
    if (current) {
        lines.push(current);
    }
    return lines.length ? lines : [text];
};

const renderSingleChart = (d3, container, dataset) => {
    const emptyBreakdownMessage = container.dataset.emptyMessage || "";
    const chartHintMessage = container.dataset.hintMessage || "";
    const CHART_BUCKET_COLOR = container.dataset.bucketColor || "";

    container.innerHTML = "";
    if (!dataset.length) {
        container.innerHTML = "<p class='m-0 text-sm text-ink-muted'>" + emptyBreakdownMessage + "</p>";
        return;
    }

    const width = container.clientWidth || container.parentElement?.clientWidth || 360;
    const height = Math.max(260, Math.min(360, width));
    const radius = Math.min(width, height) / 2;
    const innerRadius = radius * 0.55;
    const total = d3.sum(dataset, d => d.value);
    const svg = d3
        .select(container)
        .append("svg")
        .attr("viewBox", `0 0 ${width} ${height}`)
        .attr("preserveAspectRatio", "xMidYMid meet");
    const chartGroup = svg.append("g").attr("transform", `translate(${width / 2}, ${height / 2})`);
    const pie = d3.pie().value(d => d.value).sort(null);
    const arc = d3.arc().innerRadius(innerRadius).outerRadius(radius * 0.95);
    const activeArc = d3.arc().innerRadius(innerRadius).outerRadius(radius);

    const bucketPatternId = `${container.id}-small-slice-bucket`;
    const bucketPattern = svg
        .append("defs")
        .append("pattern")
        .attr("id", bucketPatternId)
        .attr("patternUnits", "userSpaceOnUse")
        .attr("patternTransform", "rotate(45)")
        .attr("width", 6)
        .attr("height", 6);
    bucketPattern.append("rect").attr("width", 6).attr("height", 6).attr("fill", CHART_BUCKET_COLOR);
    bucketPattern
        .append("line")
        .attr("x1", 0)
        .attr("y1", 0)
        .attr("x2", 0)
        .attr("y2", 6)
        .style("stroke", "var(--yamsa-surface)")
        .attr("stroke-width", 2);

    const slices = chartGroup
        .selectAll("path")
        .data(pie(dataset))
        .join("path")
        .attr("d", arc)
        // The bucket carries no slug; hatching keeps it apart from a category that
        // happens to be painted the same colour.
        .attr("fill", d => (d.data.slug === null ? `url(#${bucketPatternId})` : d.data.color))
        .style("stroke", "var(--yamsa-surface)")
        .attr("stroke-width", 2)
        .attr("cursor", "pointer")
        .attr("tabindex", 0)
        .attr("role", "button")
        .attr("aria-label", d => `${d.data.label}: ${d.data.amount_label}`);
    slices.append("title").text(d => `${d.data.label}: ${d.data.amount_label}`);

    const centerLabel = chartGroup
        .append("text")
        .attr("text-anchor", "middle")
        .attr("fill", "currentColor")
        .attr("pointer-events", "none");
    // Outside centerLabel: paintLabel wipes that node's children on every repaint.
    const probe = chartGroup.append("text").attr("visibility", "hidden").attr("aria-hidden", "true");
    // The label sits in the donut hole; lines away from the vertical center have a
    // shorter chord available, so stay well inside the hole's diameter.
    const maxLabelWidth = innerRadius * 1.45;
    const baseFontSize = Math.max(11, Math.min(16, radius * 0.12));

    const paintLabel = point => {
        centerLabel.selectAll("tspan").remove();

        const lines = [];
        if (point) {
            splitIntoLines(probe, point.label, baseFontSize, maxLabelWidth).forEach(text => {
                lines.push({
                    text: text,
                    // A category name can be one long word, which splitIntoLines cannot break.
                    size: fitFontSize(probe, text, baseFontSize, maxLabelWidth),
                    weight: 600,
                    opacity: 1,
                });
            });
            lines.push({
                text: point.amount_label,
                size: fitFontSize(probe, point.amount_label, baseFontSize, maxLabelWidth),
                weight: 600,
                opacity: 1,
            });
            const share = total > 0 ? (point.value / total) * 100 : 0;
            const shareText = `${share.toFixed(1)}%`;
            lines.push({
                text: shareText,
                size: fitFontSize(probe, shareText, baseFontSize * 0.85, maxLabelWidth),
                weight: 400,
                opacity: 0.65,
            });
        } else {
            splitIntoLines(probe, chartHintMessage, baseFontSize * 0.85, maxLabelWidth).forEach(text => {
                lines.push({text: text, size: baseFontSize * 0.85, weight: 400, opacity: 0.65});
            });
        }

        const lineHeight = baseFontSize * 1.25;
        const startY = -((lines.length - 1) * lineHeight) / 2;
        lines.forEach((line, index) => {
            centerLabel
                .append("tspan")
                .attr("x", 0)
                .attr("y", startY + index * lineHeight)
                .attr("dominant-baseline", "middle")
                .attr("font-size", line.size)
                .attr("font-weight", line.weight)
                .attr("opacity", line.opacity)
                .text(line.text);
        });
    };

    // Identified by the datum itself rather than by slug: the bucket slice that
    // collapses the small categories has no slug of its own.
    let selectedPoint = null;

    const applySelection = () => {
        slices
            .attr("d", d => (d.data === selectedPoint ? activeArc(d) : arc(d)))
            .attr("opacity", d => (!selectedPoint || d.data === selectedPoint ? 1 : 0.35))
            .attr("aria-pressed", d => d.data === selectedPoint);
        paintLabel(selectedPoint);
    };

    const toggleSlice = datum => {
        selectedPoint = selectedPoint === datum.data ? null : datum.data;
        applySelection();
    };

    slices
        .on("click", (event, datum) => {
            event.stopPropagation();
            toggleSlice(datum);
        })
        .on("keydown", (event, datum) => {
            if (event.key !== "Enter" && event.key !== " ") {
                return;
            }
            event.preventDefault();
            toggleSlice(datum);
        });

    svg.on("click", () => {
        if (!selectedPoint) {
            return;
        }
        selectedPoint = null;
        applySelection();
    });

    applySelection();
};

export const renderCategoryBreakdownCharts = (d3) => {
    document.querySelectorAll("[data-transaction-category-chart]").forEach((container) => {
        // An attribute, not a flag in this module: a morph onto a fresh page drops it together
        // with the old chart, so every new container is drawn exactly once.
        if (container.dataset.chartRendered === "true") {
            return;
        }
        const datasetId = container.dataset.transactionCategoryChartDatasetId;
        const dataNode = datasetId ? document.getElementById(datasetId) : null;
        const dataset = dataNode ? JSON.parse(dataNode.textContent || "[]") : [];
        renderSingleChart(d3, container, dataset);
        container.dataset.chartRendered = "true";
    });
};
