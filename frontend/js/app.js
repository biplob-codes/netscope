/**
 * Application bootstrap and live polling.
 */
const NetScopeApp = (() => {
  let pollTimer = null;
  let refreshSec = 1;

  function setRefreshInterval(sec) {
    refreshSec = sec || 1;
    startPolling();
  }

  function startPolling() {
    if (pollTimer) clearInterval(pollTimer);
    pollTimer = setInterval(tick, refreshSec * 1000);
  }

  async function tick() {
    try {
      const stats = await Api.getLiveStats();
      if (!stats || stats.error) return;

      // Sidebar indicator
      const ind = document.getElementById("sidebar-live");
      if (ind) {
        ind.classList.toggle("connected", !!stats.connected);
        const txt = ind.querySelector(".live-text");
        if (txt) {
          txt.textContent = stats.interface
            ? `↓ ${formatSpeed(stats.rx_speed)}  ↑ ${formatSpeed(stats.tx_speed)}`
            : "No interface";
        }
      }

      // Update open pages
      if (Navigation.current === "dashboard") Dashboard.updateLive(stats);
      if (Navigation.current === "live") LiveMonitor.update(stats);
    } catch (e) {
      console.error("Poll error", e);
    }
  }

  async function checkNotifs() {
    try {
      await Api.checkNotifications();
    } catch (_) {}
  }

  function init() {
    Navigation.init();
    Navigation.register("dashboard", Dashboard.load);
    Navigation.register("live", LiveMonitor.load);
    Navigation.register("history", AnalyticsPage.loadHistory);
    Navigation.register("insights", AnalyticsPage.loadInsights);
    Navigation.register("reports", AnalyticsPage.loadReports);
    Navigation.register("interfaces", InterfacesPage.load);
    Navigation.register("quota", QuotaPage.load);
    Navigation.register("settings", SettingsPage.load);

    document.getElementById("btn-refresh").addEventListener("click", () => {
      const page = Navigation.current;
      if (page === "dashboard") Dashboard.load();
      else if (page === "live") LiveMonitor.load();
      else if (page === "history") AnalyticsPage.loadHistory();
      else if (page === "insights") AnalyticsPage.loadInsights();
      else if (page === "interfaces") InterfacesPage.load();
      else if (page === "quota") QuotaPage.load();
      else if (page === "settings") SettingsPage.load();
    });

    // Load settings for theme + interval
    Api.getSettings().then((s) => {
      if (s.theme) document.documentElement.dataset.theme = s.theme;
      if (s.refresh_interval_sec) refreshSec = s.refresh_interval_sec;
      startPolling();
    });

    // Initial page
    window.addEventListener("pywebviewready", () => {
      Dashboard.load();
      tick();
      checkNotifs();
      // Check notifications every 5 minutes
      setInterval(checkNotifs, 5 * 60 * 1000);
    });

    // Fallback if event already fired
    if (window.pywebview && window.pywebview.api) {
      Dashboard.load();
      tick();
      startPolling();
    }
  }

  return { init, setRefreshInterval };
})();

document.addEventListener("DOMContentLoaded", () => {
  NetScopeApp.init();
});

window.NetScopeApp = NetScopeApp;
