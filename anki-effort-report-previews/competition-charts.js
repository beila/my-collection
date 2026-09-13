(() => {
  const data = window.ankiCompetition;
  const svgNs = "http://www.w3.org/2000/svg";

  const sum = values => values.reduce((total, value) => total + value, 0);
  const cumulative = values => {
    let total = 0;
    return values.map(value => (total += value));
  };
  const rounded = value => Math.round(value * 10) / 10;

  data.competitors.forEach(competitor => {
    competitor.activeDays = competitor.periodActiveDays ?? competitor.reviews.filter(Boolean).length;
    competitor.totalReviews = competitor.periodReviews ?? sum(competitor.reviews);
    competitor.totalMinutes = competitor.periodMinutes ?? rounded(sum(competitor.minutes));
    competitor.cumulativeReviews = cumulative(competitor.reviews);
    competitor.cumulativeMinutes = cumulative(competitor.minutes);
  });

  const svgElement = (name, attributes = {}) => {
    const node = document.createElementNS(svgNs, name);
    Object.entries(attributes).forEach(([key, value]) => node.setAttribute(key, value));
    return node;
  };

  const addText = (svg, text, x, y, attributes = {}) => {
    const node = svgElement("text", { x, y, ...attributes });
    node.textContent = text;
    svg.append(node);
    return node;
  };

  const niceMax = metric => metric === "minutes" ? 600 : 900;
  const metricValues = (competitor, metric) =>
    metric === "minutes" ? competitor.cumulativeMinutes : competitor.cumulativeReviews;

  const renderRaceChart = root => {
    const metric = root.dataset.metric || "reviews";
    const width = Math.max(340, Math.round(root.clientWidth));
    const mobile = width < 620;
    const height = mobile ? 286 : 350;
    const margin = mobile
      ? { top: 22, right: 14, bottom: 38, left: 38 }
      : { top: 24, right: 24, bottom: 42, left: 50 };
    const plotWidth = width - margin.left - margin.right;
    const plotHeight = height - margin.top - margin.bottom;
    const max = niceMax(metric);
    const svg = svgElement("svg", {
      viewBox: `0 0 ${width} ${height}`,
      role: "img",
      "aria-label": `Cumulative ${metric} competition from 8 August to 13 September`
    });

    const lastIndex = data.days.length - 1;
    const x = index => margin.left + (index / lastIndex) * plotWidth;
    const y = value => margin.top + plotHeight - (value / max) * plotHeight;

    [0, 0.25, 0.5, 0.75, 1].forEach(fraction => {
      const value = max * fraction;
      const lineY = y(value);
      svg.append(svgElement("line", {
        x1: margin.left,
        y1: lineY,
        x2: width - margin.right,
        y2: lineY,
        class: "chart-grid"
      }));
      addText(svg, Math.round(value), margin.left - 8, lineY + 4, {
        class: "chart-axis-label",
        "text-anchor": "end"
      });
    });

    const tickIndices = mobile ? [0, 9, 18, 27, lastIndex] : [0, 7, 14, 21, 28, lastIndex];
    tickIndices.forEach(index => {
      addText(svg, data.days[index], x(index), height - 12, {
        class: "chart-axis-label",
        "text-anchor": index === 0 ? "start" : index === lastIndex ? "end" : "middle"
      });
    });

    if (metric === "reviews") {
      const eventIndex = 13;
      const eventX = x(eventIndex);
      svg.append(svgElement("line", {
        x1: eventX,
        y1: margin.top,
        x2: eventX,
        y2: margin.top + plotHeight,
        class: "chart-event-line"
      }));
      addText(svg, mobile ? "HAREN +174 · AUG 21" : "HAREN'S BIGGEST DAY · +174 · AUG 21", eventX + 7, margin.top + 13, {
        class: "chart-event-label",
        "text-anchor": "start"
      });
    }

    data.competitors.forEach(competitor => {
      const values = metricValues(competitor, metric);
      const pathData = values
        .map((value, index) => `${index === 0 ? "M" : "L"} ${x(index)} ${y(value)}`)
        .join(" ");
      svg.append(svgElement("path", {
        d: pathData,
        fill: "none",
        stroke: competitor.color,
        "stroke-width": mobile ? 2.5 : 3,
        "stroke-linecap": "round",
        "stroke-linejoin": "round",
        class: "chart-race-line"
      }));

      const seriesLastIndex = values.length - 1;
      svg.append(svgElement("circle", {
        cx: x(seriesLastIndex),
        cy: y(values[seriesLastIndex]),
        r: mobile ? 4 : 5,
        fill: competitor.color,
        class: "chart-endpoint"
      }));
    });

    const focus = svgElement("g", { class: "chart-focus", visibility: "hidden" });
    const focusLine = svgElement("line", {
      y1: margin.top,
      y2: margin.top + plotHeight,
      class: "chart-focus-line"
    });
    const focusLabel = svgElement("text", {
      y: margin.top + 18,
      class: "chart-focus-label"
    });
    focus.append(focusLine, focusLabel);
    svg.append(focus);

    const overlay = svgElement("rect", {
      x: margin.left,
      y: margin.top,
      width: plotWidth,
      height: plotHeight,
      fill: "transparent",
      class: "chart-overlay"
    });
    const updateFocus = event => {
      const bounds = svg.getBoundingClientRect();
      const pointerX = ((event.clientX - bounds.left) / bounds.width) * width;
      const index = Math.max(0, Math.min(lastIndex, Math.round(((pointerX - margin.left) / plotWidth) * lastIndex)));
      const focusX = x(index);
      focus.setAttribute("visibility", "visible");
      focusLine.setAttribute("x1", focusX);
      focusLine.setAttribute("x2", focusX);
      focusLabel.setAttribute("x", Math.min(width - 160, Math.max(margin.left + 5, focusX + 8)));
      const values = data.competitors
        .map(competitor => {
          const value = metricValues(competitor, metric)[index];
          return `${competitor.name} ${Math.round(value)}`;
        })
        .join(" · ");
      focusLabel.textContent = `${data.days[index]} · ${values}`;
    };
    overlay.addEventListener("pointermove", updateFocus);
    overlay.addEventListener("pointerleave", () => focus.setAttribute("visibility", "hidden"));
    overlay.addEventListener("pointerdown", updateFocus);
    svg.append(overlay);

    root.replaceChildren(svg);
  };

  const renderWeeklyChart = root => {
    const groups = [
      { label: "AUG 8–14", start: 0, end: 6 },
      { label: "AUG 15–21", start: 7, end: 13 },
      { label: "AUG 22–28", start: 14, end: 20 },
      { label: "AUG 29–SEP 4", start: 21, end: 27 },
      { label: "SEP 5–11", start: 28, end: 34 },
      { label: "SEP 12–13", start: 35, end: 36 }
    ];
    const rows = groups.map(group => ({
      ...group,
      values: data.competitors.map(competitor => ({
        ...competitor,
        value: sum(competitor.reviews.slice(group.start, group.end + 1))
      }))
    }));
    const max = Math.max(...rows.flatMap(row => row.values.map(value => value.value)));

    const content = rows.map((row, index) => {
      const winner = [...row.values].sort((a, b) => b.value - a.value)[0];
      const bars = row.values.map(value => `
        <div class="weekly-bar-row">
          <span class="weekly-dot" style="--series:${value.color}"></span>
          <span class="weekly-name">${value.name}</span>
          <span class="weekly-track"><i style="--series:${value.color};--value:${(value.value / max) * 100}%"></i></span>
          <b>${value.value}</b>
        </div>
      `).join("");
      return `
        <section class="weekly-round">
          <header>
            <span>ROUND ${index + 1}</span>
            <strong>${row.label}</strong>
            <em style="--winner:${winner.color}">${winner.name} wins</em>
          </header>
          ${bars}
        </section>
      `;
    }).join("");
    root.innerHTML = content;
  };

  const renderStandings = root => {
    const categories = [
      { id: "reviews", label: "Reviews", value: competitor => competitor.totalReviews, suffix: "" },
      { id: "days", label: "Active days", value: competitor => competitor.activeDays, suffix: "d" },
      { id: "minutes", label: "Logged minutes", value: competitor => competitor.totalMinutes, suffix: "m" }
    ];
    root.innerHTML = categories.map(category => {
      const ranked = [...data.competitors].sort((a, b) => category.value(b) - category.value(a));
      const max = category.value(ranked[0]);
      return `
        <section class="standing-category">
          <header><span>${category.label}</span><b>${ranked[0].name} leads</b></header>
          ${ranked.map((competitor, index) => `
            <div class="standing-row">
              <span class="standing-rank">0${index + 1}</span>
              <span class="standing-name">${competitor.name}</span>
              <span class="standing-track"><i style="--series:${competitor.color};--value:${(category.value(competitor) / max) * 100}%"></i></span>
              <strong>${rounded(category.value(competitor))}${category.suffix}</strong>
            </div>
          `).join("")}
        </section>
      `;
    }).join("");
  };

  const renderSummary = root => {
    const sorted = [...data.competitors].sort((a, b) => b.totalReviews - a.totalReviews);
    root.innerHTML = sorted.map((competitor, index) => `
      <article class="summary-person" style="--series:${competitor.color}">
        <span class="summary-rank">0${index + 1}</span>
        <div>
          <h3>${competitor.name}</h3>
          <p>${competitor.activeDays} active days · ${competitor.totalMinutes} min</p>
        </div>
        <strong>${competitor.totalReviews}</strong>
      </article>
    `).join("");
  };

  const renderAll = () => {
    document.querySelectorAll("[data-race-chart]").forEach(renderRaceChart);
    document.querySelectorAll("[data-weekly-chart]").forEach(renderWeeklyChart);
    document.querySelectorAll("[data-standings]").forEach(renderStandings);
    document.querySelectorAll("[data-summary]").forEach(renderSummary);
  };

  let resizeTimer;
  window.addEventListener("resize", () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(renderAll, 120);
  });
  window.addEventListener("DOMContentLoaded", renderAll);
})();
