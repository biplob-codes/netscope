/**
 * Thin wrapper around pywebview.api with error handling and readiness wait.
 */
const Api = (() => {
  let ready = false;
  const queue = [];

  function onReady() {
    ready = true;
    queue.forEach((fn) => fn());
    queue.length = 0;
  }

  if (window.pywebview && window.pywebview.api) {
    onReady();
  } else {
    window.addEventListener("pywebviewready", onReady);
  }

  function waitReady() {
    return new Promise((resolve) => {
      if (ready) resolve();
      else queue.push(resolve);
    });
  }

  async function call(method, ...args) {
    await waitReady();
    try {
      const result = await window.pywebview.api[method](...args);
      return result;
    } catch (err) {
      console.error(`API.${method} failed:`, err);
      return { error: err.message || String(err) };
    }
  }

  return {
    getDashboard: () => call("get_dashboard_data"),
    getLiveStats: () => call("get_live_stats"),
    getInterfaces: () => call("get_interfaces"),
    setInterface: (name) => call("set_selected_interface", name),
    getUsageHistory: (period, limit) => call("get_usage_history", period, limit),
    getComparison: () => call("get_comparison"),
    getInsights: () => call("get_insights"),
    getPeakDays: (limit) => call("get_peak_days", limit),
    getQuotaStatus: () => call("get_quota_status"),
    getQuotaSettings: () => call("get_quota_settings"),
    saveQuotaSettings: (data) => call("save_quota_settings", data),
    getSettings: () => call("get_settings"),
    saveSettings: (data) => call("save_settings", data),
    checkNotifications: () => call("check_notifications"),
    testNotification: () => call("test_notification"),
    exportUsage: (period, fmt, limit) => call("export_usage", period, fmt, limit),
    bytesToHuman: (n) => call("bytes_to_human", n),
    checkVnstat: () => call("check_vnstat"),
  };
})();

/** Format bytes client-side for speed (avoids round-trips). */
function formatBytes(bytes, precision = 2) {
  if (bytes == null || isNaN(bytes)) return "—";
  bytes = Number(bytes);
  const units = ["B", "KB", "MB", "GB", "TB", "PB"];
  let i = 0;
  while (Math.abs(bytes) >= 1024 && i < units.length - 1) {
    bytes /= 1024;
    i++;
  }
  if (i === 0) return `${Math.round(bytes)} ${units[i]}`;
  return `${bytes.toFixed(precision)} ${units[i]}`;
}

function formatSpeed(bytesPerSec) {
  if (bytesPerSec == null || isNaN(bytesPerSec)) return "—";
  return formatBytes(bytesPerSec) + "/s";
}

function toast(message, type = "info") {
  const container = document.getElementById("toasts");
  const el = document.createElement("div");
  el.className = `toast ${type}`;
  el.textContent = message;
  container.appendChild(el);
  setTimeout(() => {
    el.style.opacity = "0";
    el.style.transition = "opacity 0.3s";
    setTimeout(() => el.remove(), 300);
  }, 3500);
}
