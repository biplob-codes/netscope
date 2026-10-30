const QuotaPage = (() => {
  async function load() {
    const container = document.getElementById("page-quota");
    container.innerHTML = `<div class="state-msg"><p>Loading…</p></div>`;

    const [settings, status] = await Promise.all([
      Api.getQuotaSettings(),
      Api.getQuotaStatus(),
    ]);

    const allowanceGB =
      settings.monthly_allowance_bytes > 0
        ? (settings.monthly_allowance_bytes / (1024 ** 3)).toFixed(1)
        : "";

    container.innerHTML = `
      ${status.enabled ? renderStatus(status) : ""}

      <div class="section">
        <h3 class="section-title">Configure Data Limit</h3>
        <div class="card">
          <div class="form-group">
            <label class="toggle">
              <input type="checkbox" id="quota-enabled" ${settings.enabled ? "checked" : ""} />
              <span class="toggle-track"></span>
              <span>Enable monthly data limit tracking</span>
            </label>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>Monthly allowance (GB)</label>
              <input type="number" id="quota-allowance" min="0" step="0.1" value="${allowanceGB}" placeholder="e.g. 100" />
            </div>
            <div class="form-group">
              <label>Billing cycle start day</label>
              <input type="number" id="quota-day" min="1" max="28" value="${settings.billing_day || 1}" />
              <p class="hint">Day of the month when your plan renews (1–28)</p>
            </div>
          </div>

          <div class="form-group">
            <label>Quota calculation</label>
            <select id="quota-type">
              <option value="combined" ${settings.quota_type === "combined" ? "selected" : ""}>Download + Upload</option>
              <option value="download" ${settings.quota_type === "download" ? "selected" : ""}>Download only</option>
            </select>
          </div>

          <div class="form-group">
            <label>Warning thresholds (%)</label>
            <input type="text" id="quota-thresholds" value="${(settings.warning_thresholds || [50,75,90,100]).join(", ")}" />
            <p class="hint">Comma-separated percentages, e.g. 50, 75, 90, 100</p>
          </div>

          <button class="btn btn-primary" id="btn-save-quota">Save</button>
        </div>
      </div>
    `;

    document.getElementById("btn-save-quota").addEventListener("click", save);
  }

  function renderStatus(q) {
    const pct = q.percent || 0;
    let barClass = "";
    if (pct >= 90) barClass = "danger";
    else if (pct >= 75) barClass = "warn";

    return `
      <div class="card quota-card" style="margin-bottom:24px">
        <div class="quota-header">
          <span class="card-title">Current Cycle</span>
          <span class="quota-percent">${pct.toFixed(1)}%</span>
        </div>
        <div class="progress"><div class="progress-bar ${barClass}" style="width:${Math.min(100, pct)}%"></div></div>
        <div class="quota-meta">
          <div class="quota-meta-item"><span>Used</span><strong>${formatBytes(q.used)}</strong></div>
          <div class="quota-meta-item"><span>Remaining</span><strong>${formatBytes(q.remaining)}</strong></div>
          <div class="quota-meta-item"><span>Allowance</span><strong>${formatBytes(q.allowance)}</strong></div>
          <div class="quota-meta-item"><span>Cycle</span><strong>${q.billing_start} → ${q.billing_end}</strong></div>
          <div class="quota-meta-item"><span>Days left</span><strong>${q.days_remaining}</strong></div>
          <div class="quota-meta-item"><span>Recommended / day</span><strong>${formatBytes(q.recommended_daily)}</strong></div>
        </div>
      </div>`;
  }

  async function save() {
    const enabled = document.getElementById("quota-enabled").checked;
    const gb = parseFloat(document.getElementById("quota-allowance").value) || 0;
    const day = parseInt(document.getElementById("quota-day").value, 10) || 1;
    const type = document.getElementById("quota-type").value;
    const thrRaw = document.getElementById("quota-thresholds").value;
    const thresholds = thrRaw
      .split(",")
      .map((s) => parseInt(s.trim(), 10))
      .filter((n) => !isNaN(n) && n > 0 && n <= 100);

    const data = {
      enabled,
      monthly_allowance_bytes: Math.round(gb * 1024 ** 3),
      billing_day: day,
      quota_type: type,
      warning_thresholds: thresholds.length ? thresholds : [50, 75, 90, 100],
    };

    const res = await Api.saveQuotaSettings(data);
    if (res.error) {
      toast(res.error, "error");
      return;
    }
    toast("Quota settings saved", "success");
    load();
  }

  return { load };
})();
