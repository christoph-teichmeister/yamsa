// "Who paid what"'s spending timeline, one series per currency. Rendered by charts.js rather than
// from an inline <script>: idiomorph morphs such a script into the next page's instead of
// inserting it, and a morphed script never runs (#440). The container carries the string the
// template used to write into the script.

const TREND_SERIES_RGB_VARS = [
    "--yamsa-brand-rgb",
    "--yamsa-success-rgb",
    "--yamsa-warning-rgb",
    "--yamsa-danger-rgb",
]
// Above this many expenses the dots stop being readable and only bloat the DOM.
const TREND_MAX_DOTS = 60

export const renderSpendingTrendChart = (d3) => {
    const container = document.getElementById("trend-line-chart")
    const dataNode = document.getElementById("trend-chart-data")
    // See renderCategoryBreakdownCharts: the attribute goes with the chart on the next swap.
    if (!container || !dataNode || container.dataset.chartRendered === "true") {
        return
    }
    container.dataset.chartRendered = "true"

    const notEnoughDataMessage = container.dataset.notEnoughDataMessage || ""
    const payload = JSON.parse(dataNode.textContent || "{}")
    const parseMoment = d3.utcParse("%Y-%m-%dT%H:%M:%S")

    const series = (payload.series || [])
        .map(entry => ({
            currency: entry.currency || "",
            points: (entry.points || [])
                .map(point => ({ ...point, date: parseMoment(point.date) }))
                .filter(point => point.date)
                .sort((a, b) => d3.ascending(a.date, b.date)),
        }))
        .filter(entry => entry.points.length)

    container.innerHTML = ""

    if (!series.length) {
        container.innerHTML = "<p class='m-0 text-sm text-ink-muted'>" + notEnoughDataMessage + "</p>"
        return
    }

    // Every series shares the selected range on the x axis, so the charts stay comparable.
    const rangeStart = parseMoment(payload.rangeStart) || series[0].points[0].date
    const rangeEnd = parseMoment(payload.rangeEnd) || series[0].points[series[0].points.length - 1].date

    const width = container.clientWidth || container.parentElement?.clientWidth || 640
    const height = Math.max(180, Math.min(260, width * 0.45))
    const margin = { top: 10, right: 20, bottom: 70, left: 64 }
    const innerWidth = width - margin.left - margin.right
    const innerHeight = height - margin.top - margin.bottom

    series.forEach((entry, seriesIndex) => {
        const currency = entry.currency
        const data = entry.points
        const rgbVar = TREND_SERIES_RGB_VARS[seriesIndex % TREND_SERIES_RGB_VARS.length]

        const section = d3.select(container).append("div").attr("class", "trend-series")
        if (series.length > 1) {
            section
                .append("p")
                .attr("class", "trend-series-label mb-1 text-sm text-ink-muted")
                .style("color", `rgb(var(${rgbVar}))`)
                .text(currency)
        }

        const svg = section
            .append("svg")
            .attr("viewBox", `0 0 ${width} ${height}`)
            .attr("preserveAspectRatio", "xMidYMid meet")

        const gradientId = `trend-area-gradient-${seriesIndex}`
        const gradient = svg
            .append("defs")
            .append("linearGradient")
            .attr("id", gradientId)
            .attr("x1", "0%")
            .attr("y1", "0%")
            .attr("x2", "0%")
            .attr("y2", "100%")
        gradient.append("stop").attr("offset", "0%").style("stop-color", `rgb(var(${rgbVar}), 0.4)`)
        gradient.append("stop").attr("offset", "100%").style("stop-color", `rgb(var(${rgbVar}), 0)`)

        const chart = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`)

        const x = d3.scaleUtc().domain([rangeStart, rangeEnd]).range([0, innerWidth])
        const y = d3
            .scaleLinear()
            .domain([0, d3.max(data, d => d.value) || 0])
            .nice()
            .range([innerHeight, 0])

        const xAxis = g => {
            g.attr("transform", `translate(0,${innerHeight})`)
                .call(d3.axisBottom(x).ticks(6).tickFormat(d3.utcFormat("%d %b")))
                .call(g => g.select(".domain").style("stroke", "var(--yamsa-line-strong)"))
                .call(g => g.selectAll(".tick line").style("stroke", "var(--yamsa-line)"))
            g.selectAll("text")
                .attr("text-anchor", "end")
                .attr("transform", "rotate(-90)")
                .attr("dx", "-0.8em")
                .attr("dy", "-0.35em")
        }

        const numberFormatter = new Intl.NumberFormat("de-DE", {
            minimumFractionDigits: 0,
            maximumFractionDigits: 1,
        })
        const amountFormatter = new Intl.NumberFormat("de-DE", {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        })

        const yAxis = g =>
            g
                .call(
                    d3
                        .axisLeft(y)
                        .ticks(5)
                        .tickSize(-innerWidth)
                        .tickFormat(value => `${currency}${numberFormatter.format(value)}`)
                )
                .call(g => g.select(".domain").style("stroke", "var(--yamsa-line-strong)"))
                .call(g => g.selectAll(".tick line").style("stroke", "var(--yamsa-line)"))

        chart.append("g").call(xAxis)
        chart.append("g").call(yAxis)

        // A running total only ever changes at the moment an expense is booked, so it steps
        // instead of sloping - an interpolated curve would show spending on days without any.
        const area = d3
            .area()
            .x(d => x(d.date))
            .y0(innerHeight)
            .y1(d => y(d.value))
            .curve(d3.curveStepAfter)

        const line = d3
            .line()
            .x(d => x(d.date))
            .y(d => y(d.value))
            .curve(d3.curveStepAfter)

        chart
            .append("path")
            .datum(data)
            .attr("class", "trend-line-area")
            .attr("fill", `url(#${gradientId})`)
            .attr("d", area)

        chart
            .append("path")
            .datum(data)
            .attr("class", "trend-line-path")
            .style("stroke", `rgb(var(${rgbVar}), 0.9)`)
            .attr("d", line)

        const dots = data.filter(d => d.delta > 0)
        if (dots.length && dots.length <= TREND_MAX_DOTS) {
            chart
                .selectAll(".trend-line-dot")
                .data(dots)
                .enter()
                .append("circle")
                .attr("class", "trend-line-dot")
                .attr("r", 3)
                .style("stroke", `rgb(var(${rgbVar}), 0.9)`)
                .attr("cx", d => x(d.date))
                .attr("cy", d => y(d.value))
                .append("title")
                .text(
                    d =>
                        `+${currency}${amountFormatter.format(d.delta)} → ${currency}${amountFormatter.format(d.value)} · ${d.label}`
                )
        }
    })
}
