const AnalyticsPage = (() => {
  let historyChart = null;

  async function loadHistory() {
    const container = document.getElementById("page-history");
    container.innerHTML = `
      <div class="chart-toolbar">
        <div class="tabs" id="hist-tabs">
          <button class="tab active" data-period="daily">Daily</button>
          <button class="tab" data-period="hourly">Hourly</button>
          <button class="tab" data-period="monthly">Monthly</button>
          <button class="tab" data-period="yearly">Yearly</button>
        </div>
      </div>
      <div class="card">
        <div class="chart-container" style="height:320px">
          <canvas id="hist-chart"></canvas>
        </div>
      </div>
      <div class="section" style="margin-top:20px">
        <div class="table-wrap">
          <table class="data-table" id="hist-table">
            <thead><tr><th>Date</th><th>Download</th><th>Upload</th><th>Total</th></tr></thead>
            <tbody></tbody>
          </table>
        </div>
      </div>
    `;

    document.querySelectorAll("#hist-tabs .tab").forEach((tab) => {
      tab.addEventListener("click", () => {
        document.querySelectorAll("#hist-tabs .tab").forEach((t) => t.classList.remove("active"));
        tab.classList.add("active");
        fetchAndRender(tab.dataset.period);
      });
    });

    await fetchAndRender("daily");
  }

  async function fetchAndRender(period) {
    const result = await Api.getUsageHistory(period, period === "daily" ? 30 : period === "monthly" ? 12 : null);
    const tbody = document.querySelector("#hist-table tbody");
    const canvas = document.getElementById("hist-chart");

    if (result.error) {
      tbody.innerHTML = `<tr><td colspan="4" class="text-muted">${result.error}</td></tr>`;
      Charts.destroy(historyChart);
      historyChart = null;
      return;
    }

    const data = result.data || [];
    if (!data.length) {
      tbody.innerHTML = `<tr><td colspan="4" class="text-muted">No data available</td></tr>`;
      Charts.destroy(historyChart);
      historyChart = null;
      return;
    }

    // Table
    let html = "";
    const reversed = [...data].reverse();
    for (const row of reversed) {
      const label = row.date || row.datetime || row.year || "—";
      html += `<tr>
        <td>${label}</td>
        <td>${formatBytes(row.rx)}</td>
        <td>${formatBytes(row.tx)}</td>
        <td><strong>${formatBytes(row.total)}</strong></td>
      </tr>`;
    }
    tbody.innerHTML = html;

    // Chart
    const labels = data.map((r) => {
      if (r.date) {
        const d = new Date(r.date + "T00:00:00");
        return d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
      }
      if (r.datetime) return r.hour + ":00";
      if (r.year) return String(r.year);
      return "";
    });

    Charts.destroy(historyChart);
    historyChart = Charts.barChart(canvas, labels, [
      { label: "Download", data: data.map((r) => r.rx) },
      { label: "Upload", data: data.map((r) => r.tx) },
    ]);
  }

  async function loadInsights() {
    const container = document.getElementById("page-insights");
    container.innerHTML = `<div class="state-msg"><p>Loading insights…</p></div>`;

    const [insights, comparison, peaks] = await Promise.all([
      Api.getInsights(),
      Api.getComparison(),
      Api.getPeakDays(5),
    ]);

    let html = "";

    if (insights && insights.length) {
      html += `<div class="section"><h3 class="section-title">Insights</h3><div class="insight-list">`;
      for (const ins of insights) {
        html += `
          <div class="insight-card">
            <div class="insight-icon">◈</div>
            <div class="insight-body">
              <h4>${escapeHtml(ins.title)}</h4>
              <p>${escapeHtml(ins.text)}</p>
            </div>
          </div>`;
      }
      html += `</div></div>`;
    } else {
      html += `<div class="state-msg"><p>Not enough historical data yet to generate insights.</p></div>`;
    }

    if (peaks && peaks.length) {
      html += `<div class="section"><h3 class="section-title">Peak Usage Days</h3>
        <div class="card"><table class="data-table"><thead><tr><th>Date</th><th>Download</th><th>Upload</th><th>Total</th></tr></thead><tbody>`;
      for (const p of peaks) {
        html += `<tr><td>${p.date}</td><td>${formatBytes(p.rx)}</td><td>${formatBytes(p.tx)}</td><td><strong>${formatBytes(p.total)}</strong></td></tr>`;
      }
      html += `</tbody></table></div></div>`;
    }

    if (comparison && comparison.month) {
      const m = comparison.month;
      if (m.current && m.previous) {
        const ch = m.total_change_pct;
        const dir = ch > 0 ? "up" : "down";
        html += `<div class="section"><h3 class="section-title">Month Comparison</h3>
          <div class="grid grid-2">
            <div class="card"><div class="card-title">This Month</div><div class="card-value">${formatBytes(m.current.total)}</div></div>
            <div class="card"><div class="card-title">Previous Month</div><div class="card-value">${formatBytes(m.previous.total)}</div>
              <div class="card-sub">${ch != null ? `${Math.abs(ch)}% ${dir}` : ""}</div></div>
          </div></div>`;
      }
    }

    container.innerHTML = html || `<div class="state-msg"><p>No insights available.</p></div>`;
  }

  async function loadReports() {
    const container = document.getElementById("page-reports");
    container.innerHTML = `
      <div class="section">
        <h3 class="section-title">Export Usage Data</h3>
        <div class="card">
          <div class="form-row">
            <div class="form-group">
              <label>Period</label>
              <select id="export-period">
                <option value="daily">Daily</option>
                <option value="monthly">Monthly</option>
                <option value="yearly">Yearly</option>
                <option value="hourly">Hourly</option>
              </select>
            </div>
            <div class="form-group">
              <label>Format</label>
              <select id="export-fmt">
                <option value="csv">CSV</option>
                <option value="json">JSON</option>
              </select>
            </div>
          </div>
          <button class="btn btn-primary" id="btn-export">Export</button>
        </div>
      </div>
    `;

    document.getElementById("btn-export").addEventListener("click", async () => {
      const period = document.getElementById("export-period").value;
      const fmt = document.getElementById("export-fmt").value;
      const result = await Api.exportUsage(period, fmt);
      if (result.error) {
        toast(result.error, "error");
        return;
      }
      // Trigger download via data URI
      const blob = new Blob([result.content], { type: result.mime || "text/plain" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = result.filename || "export.txt";
      a.click();
      URL.revokeObjectURL(url);
      toast("Export downloaded", "success");
    });
  }

  function escapeHtml(s) {
    const d = document.createElement("div");
    d.textContent = s;
    return d.innerHTML;
  }

  return { loadHistory, loadInsights, loadReports };
})();
