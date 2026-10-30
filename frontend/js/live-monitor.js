const LiveMonitor = (() => {
  let liveChart = null;
  let peakRx = 0;
  let peakTx = 0;

  function renderShell(container) {
    container.innerHTML = `
      <div class="live-hero">
        <div class="card live-speed-card rx">
          <div class="speed-value" id="live-rx">0 B/s</div>
          <div class="speed-label">Download</div>
        </div>
        <div class="card live-speed-card tx">
          <div class="speed-value" id="live-tx">0 B/s</div>
          <div class="speed-label">Upload</div>
        </div>
      </div>

      <div class="live-meta">
        <div class="card">
          <div class="card-title">Peak Down</div>
          <div class="card-value mono" id="live-peak-rx" style="font-size:16px">—</div>
        </div>
        <div class="card">
          <div class="card-title">Peak Up</div>
          <div class="card-value mono" id="live-peak-tx" style="font-size:16px">—</div>
        </div>
        <div class="card">
          <div class="card-title">Session Down</div>
          <div class="card-value mono" id="live-sess-rx" style="font-size:16px">—</div>
        </div>
        <div class="card">
          <div class="card-title">Session Up</div>
          <div class="card-value mono" id="live-sess-tx" style="font-size:16px">—</div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <span class="card-title">Bandwidth</span>
          <span class="text-muted" id="live-iface" style="font-size:12px"></span>
        </div>
        <div class="live-chart-wrap">
          <canvas id="live-chart"></canvas>
        </div>
      </div>
    `;

    const canvas = document.getElementById("live-chart");
    if (liveChart) liveChart.destroy();
    liveChart = Charts.createLiveChart(canvas, 60);
  }

  function update(stats) {
    const rxEl = document.getElementById("live-rx");
    const txEl = document.getElementById("live-tx");
    if (!rxEl) return;

    rxEl.textContent = formatSpeed(stats.rx_speed);
    txEl.textContent = formatSpeed(stats.tx_speed);

    peakRx = Math.max(peakRx, stats.peak_rx || stats.rx_speed || 0);
    peakTx = Math.max(peakTx, stats.peak_tx || stats.tx_speed || 0);

    document.getElementById("live-peak-rx").textContent = formatSpeed(peakRx);
    document.getElementById("live-peak-tx").textContent = formatSpeed(peakTx);
    document.getElementById("live-sess-rx").textContent = formatBytes(stats.session_rx);
    document.getElementById("live-sess-tx").textContent = formatBytes(stats.session_tx);

    const iface = document.getElementById("live-iface");
    if (iface) {
      iface.textContent = stats.interface
        ? `${stats.interface} · ${stats.connected ? "Connected" : "Disconnected"}`
        : "No interface selected";
    }

    if (liveChart) {
      liveChart.push(stats.rx_speed || 0, stats.tx_speed || 0);
    }
  }

  function load() {
    const container = document.getElementById("page-live");
    renderShell(container);
    peakRx = 0;
    peakTx = 0;
  }

  return { load, update };
})();
