/**
 * Chart.js helpers with consistent NetScope styling.
 */
const Charts = (() => {
  const isDark = () => document.documentElement.dataset.theme !== "light";

  function colors() {
    return {
      grid: isDark() ? "rgba(255,255,255,0.04)" : "rgba(0,0,0,0.05)",
      text: isDark() ? "#9aa0a6" : "#6b7280",
      rx: isDark() ? "#2dd4bf" : "#0d9488",
      tx: isDark() ? "#60a5fa" : "#2563eb",
      rxFill: isDark() ? "rgba(45,212,191,0.12)" : "rgba(13,148,136,0.1)",
      txFill: isDark() ? "rgba(96,165,250,0.12)" : "rgba(37,99,235,0.1)",
    };
  }

  function baseOptions() {
    const c = colors();
    return {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      plugins: {
        legend: {
          labels: { color: c.text, boxWidth: 12, padding: 16, font: { size: 12 } },
        },
        tooltip: {
          backgroundColor: isDark() ? "#1e2430" : "#fff",
          titleColor: isDark() ? "#e8eaed" : "#111",
          bodyColor: isDark() ? "#9aa0a6" : "#4b5563",
          borderColor: isDark() ? "rgba(255,255,255,0.08)" : "rgba(0,0,0,0.08)",
          borderWidth: 1,
          padding: 10,
          callbacks: {
            label(ctx) {
              const v = ctx.parsed.y;
              return ` ${ctx.dataset.label}: ${formatBytes(v)}`;
            },
          },
        },
      },
      scales: {
        x: {
          grid: { color: c.grid, drawBorder: false },
          ticks: { color: c.text, font: { size: 11 }, maxRotation: 0 },
        },
        y: {
          grid: { color: c.grid, drawBorder: false },
          ticks: {
            color: c.text,
            font: { size: 11 },
            callback(v) {
              return formatBytes(v, 1);
            },
          },
          beginAtZero: true,
        },
      },
    };
  }

  function destroy(chart) {
    if (chart) chart.destroy();
  }

  function barChart(canvas, labels, datasets) {
    const c = colors();
    const ds = datasets.map((d, i) => ({
      label: d.label,
      data: d.data,
      backgroundColor: d.color || (i === 0 ? c.rx : c.tx),
      borderRadius: 3,
      barPercentage: 0.7,
      categoryPercentage: 0.8,
    }));
    return new Chart(canvas, {
      type: "bar",
      data: { labels, datasets: ds },
      options: baseOptions(),
    });
  }

  function lineChart(canvas, labels, datasets, opts = {}) {
    const c = colors();
    const ds = datasets.map((d, i) => ({
      label: d.label,
      data: d.data,
      borderColor: d.color || (i === 0 ? c.rx : c.tx),
      backgroundColor: d.fill || (i === 0 ? c.rxFill : c.txFill),
      fill: opts.fill !== false,
      tension: 0.3,
      pointRadius: opts.pointRadius ?? 0,
      pointHoverRadius: 4,
      borderWidth: 2,
    }));
    const options = baseOptions();
    if (opts.yCallback) {
      options.scales.y.ticks.callback = opts.yCallback;
    }
    if (opts.tooltipCallback) {
      options.plugins.tooltip.callbacks.label = opts.tooltipCallback;
    }
    return new Chart(canvas, {
      type: "line",
      data: { labels, datasets: ds },
      options,
    });
  }

  /** Live speed chart – keeps a rolling window of points. */
  function createLiveChart(canvas, maxPoints = 60) {
    const c = colors();
    const chart = new Chart(canvas, {
      type: "line",
      data: {
        labels: Array(maxPoints).fill(""),
        datasets: [
          {
            label: "Download",
            data: Array(maxPoints).fill(0),
            borderColor: c.rx,
            backgroundColor: c.rxFill,
            fill: true,
            tension: 0.35,
            pointRadius: 0,
            borderWidth: 1.5,
          },
          {
            label: "Upload",
            data: Array(maxPoints).fill(0),
            borderColor: c.tx,
            backgroundColor: c.txFill,
            fill: true,
            tension: 0.35,
            pointRadius: 0,
            borderWidth: 1.5,
          },
        ],
      },
      options: {
        ...baseOptions(),
        animation: false,
        plugins: {
          ...baseOptions().plugins,
          legend: { display: false },
          tooltip: {
            ...baseOptions().plugins.tooltip,
            callbacks: {
              label(ctx) {
                return ` ${ctx.dataset.label}: ${formatSpeed(ctx.parsed.y)}`;
              },
            },
          },
        },
        scales: {
          x: { display: false },
          y: {
            grid: { color: c.grid, drawBorder: false },
            ticks: {
              color: c.text,
              font: { size: 10 },
              callback(v) {
                return formatSpeed(v);
              },
            },
            beginAtZero: true,
          },
        },
      },
    });

    return {
      chart,
      push(rx, tx) {
        chart.data.datasets[0].data.push(rx);
        chart.data.datasets[0].data.shift();
        chart.data.datasets[1].data.push(tx);
        chart.data.datasets[1].data.shift();
        chart.update("none");
      },
      destroy() {
        chart.destroy();
      },
    };
  }

  return { barChart, lineChart, createLiveChart, destroy, colors };
})();
