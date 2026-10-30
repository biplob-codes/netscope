const SettingsPage = (() => {
  async function load() {
    const container = document.getElementById("page-settings");
    container.innerHTML = `<div class="state-msg"><p>Loading…</p></div>`;

    const settings = await Api.getSettings();
    const vn = await Api.checkVnstat();

    container.innerHTML = `
      <div class="section">
        <h3 class="section-title">Appearance</h3>
        <div class="card">
          <div class="form-group">
            <label>Theme</label>
            <select id="set-theme">
              <option value="dark" ${settings.theme === "dark" ? "selected" : ""}>Dark</option>
              <option value="light" ${settings.theme === "light" ? "selected" : ""}>Light</option>
            </select>
          </div>
        </div>
      </div>

      <div class="section">
        <h3 class="section-title">Notifications</h3>
        <div class="card">
          <div class="form-group">
            <label class="toggle">
              <input type="checkbox" id="set-notif" ${settings.notifications_enabled !== false ? "checked" : ""} />
              <span class="toggle-track"></span>
              <span>Enable desktop notifications</span>
            </label>
          </div>
          <button class="btn btn-ghost" id="btn-test-notif">Send test notification</button>
        </div>
      </div>

      <div class="section">
        <h3 class="section-title">System</h3>
        <div class="card">
          <div class="form-group">
            <label>vnStat status</label>
            <p style="font-size:13px">
              ${
                vn.available
                  ? `<span class="badge badge-success">Available</span> · Interfaces: ${(vn.interfaces || []).join(", ") || "none"}`
                  : `<span class="badge badge-danger">Unavailable</span> · ${vn.error || ""}`
              }
            </p>
          </div>
          <div class="form-group">
            <label>Live refresh interval</label>
            <select id="set-refresh">
              <option value="1" ${settings.refresh_interval_sec == 1 ? "selected" : ""}>1 second</option>
              <option value="2" ${settings.refresh_interval_sec == 2 ? "selected" : ""}>2 seconds</option>
              <option value="5" ${settings.refresh_interval_sec == 5 ? "selected" : ""}>5 seconds</option>
            </select>
          </div>
        </div>
      </div>

      <button class="btn btn-primary" id="btn-save-settings">Save Settings</button>
    `;

    document.getElementById("btn-save-settings").addEventListener("click", save);
    document.getElementById("btn-test-notif").addEventListener("click", async () => {
      const res = await Api.testNotification();
      toast(res.success ? "Notification sent" : "Could not send notification (is notify-send installed?)", res.success ? "success" : "error");
    });

    document.getElementById("set-theme").addEventListener("change", (e) => {
      document.documentElement.dataset.theme = e.target.value;
    });
  }

  async function save() {
    const data = {
      theme: document.getElementById("set-theme").value,
      notifications_enabled: document.getElementById("set-notif").checked,
      refresh_interval_sec: parseInt(document.getElementById("set-refresh").value, 10),
    };
    const res = await Api.saveSettings(data);
    if (res.error) {
      toast(res.error, "error");
      return;
    }
    document.documentElement.dataset.theme = data.theme;
    toast("Settings saved", "success");
    // Update live interval if App exposes it
    if (window.NetScopeApp) window.NetScopeApp.setRefreshInterval(data.refresh_interval_sec);
  }

  return { load };
})();
