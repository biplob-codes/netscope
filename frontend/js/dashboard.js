const Dashboard = (() => {
  let chart = null;

  function render(container, data) {
    if (data.error) {
      container.innerHTML = `
        <div class="state-msg">
          <div class="state-icon">⚠</div>
          <p>${escapeHtml(data.error)}</p>
          <p class="text-muted" style="margin-top:12px">Make sure vnStat is installed and the service is running.</p>
        </div>`;
      return;
    }

    const q = data.quota || {};
    const live = data.live || {};

    container.innerHTML = `
      <div class="stat-grid">
        <div class="card stat-card">
          <div class="card-title">Today Download</div>
          <div class="card-value rx">${formatBytes(data.today?.rx)}</div>
        </div>
        <div class="card stat-card">
          <div class="card-title">Today Upload</div>
          <div class="card-value tx">${formatBytes(data.today?.tx)}</div>
        </div>
        <div class="card stat-card">
          <div class="card-title">Yesterday</div>
          <div class="card-value">${formatBytes(data.yesterday?.total)}</div>
          <div class="card-sub">↓ ${formatBytes(data.yesterday?.rx)} · ↑ ${formatBytes(data.yesterday?.tx)}</div>
        </div>
        <div class="card stat-card">
          <div class="card-title">This Month</div>
          <div class="card-value">${formatBytes(data.month?.total)}</div>
          <div class="card-sub">↓ ${formatBytes(data.month?.rx)} · ↑ ${formatBytes(data.month?.tx)}</div>
        </div>
      </div>

      <div class="stat-grid" style="grid-template-columns: repeat(3,1fr)">
        <div class="card stat-card">
          <div class="card-title">All Time</div>
          <div class="card-value">${formatBytes(data.total?.total)}</div>
        </div>
        <div class="card stat-card">
          <div class="card-title">Avg Daily</div>
          <div class="card-value">${formatBytes(data.avg_daily)}</div>
        </div>
        <div class="card stat-card">
          <div class="card-title">Est. Month</div>
          <div class="card-value">${formatBytes(data.estimated_month)}</div>
        </div>
      </div>

      ${q.enabled ? renderQuota(q) : ""}

      <div class="card chart-card">
        <div class="card-header">
          <span class="card-title">Recent Daily Usage</span>
          <div class="live-speeds">
            <div class="speed-item rx">
              <span class="label">Down</span>
              <span class="value" id="dash-rx">${formatSpeed(live.rx_speed)}</span>
            </div>
            <div class="speed-item tx">
              <span class="label">Up</span>
              <span class="value" id="dash-tx">${formatSpeed(live.tx_speed)}</span>
            </div>
          </div>
        </div>
        <div class="chart-container">
          <canvas id="dash-chart"></canvas>
        </div>
      </div>
    `;

    // Chart
    const days = data.recent_days || [];
    const labels = days.map((d) => {
      const dt = new Date(d.date + "T00:00:00");
      return dt.toLocaleDateString(undefined, { month: "short", day: "numeric" });
    });
    const canvas = document.getElementById("dash-chart");
    if (canvas && days.length) {
      Charts.destroy(chart);
      chart = Charts.barChart(canvas, labels, [
        { label: "Download", data: days.map((d) => d.rx) },
        { label: "Upload", data: days.map((d) => d.tx) },
      ]);
    }
  }

  function renderQuota(q) {
    const pct = q.percent || 0;
    let barClass = "";
    if (pct >= 90) barClass = "danger";
    else if (pct >= 75) barClass = "warn";

    return `
      <div class="card quota-card">
        <div class="quota-header">
          <span class="card-title">Monthly Data Allowance</span>
          <span class="quota-percent">${pct.toFixed(1)}%</span>
        </div>
        <div class="progress">
          <div class="progress-bar ${barClass}" style="width:${Math.min(100, pct)}%"></div>
        </div>
        <div class="quota-meta">
          <div class="quota-meta-item"><span>Used</span><strong>${formatBytes(q.used)}</strong></div>
          <div class="quota-meta-item"><span>Remaining</span><strong>${formatBytes(q.remaining)}</strong></div>
          <div class="quota-meta-item"><span>Allowance</span><strong>${formatBytes(q.allowance)}</strong></div>
          <div class="quota-meta-item"><span>Days left</span><strong>${q.days_remaining}</strong></div>
          <div class="quota-meta-item"><span>Recommended daily</span><strong>${formatBytes(q.recommended_daily)}</strong></div>
          <div class="quota-meta-item"><span>Projected</span><strong>${formatBytes(q.projected)}</strong></div>
        </div>
      </div>`;
  }

  async function load() {
    const container = document.getElementById("page-dashboard");
    container.innerHTML = `<div class="state-msg"><p>Loading…</p></div>`;
    const data = await Api.getDashboard();
    render(container, data);
  }

  function updateLive(stats) {
    const rx = document.getElementById("dash-rx");
    const tx = document.getElementById("dash-tx");
    if (rx) rx.textContent = formatSpeed(stats.rx_speed);
    if (tx) tx.textContent = formatSpeed(stats.tx_speed);
  }

  function escapeHtml(s) {
    const d = document.createElement("div");
    d.textContent = s;
    return d.innerHTML;
  }

  return { load, updateLive };
})();
