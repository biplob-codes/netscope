const InterfacesPage = (() => {
  async function load() {
    const container = document.getElementById("page-interfaces");
    container.innerHTML = `<div class="state-msg"><p>Loading interfaces…</p></div>`;

    const data = await Api.getInterfaces();
    if (data.error) {
      container.innerHTML = `<div class="state-msg"><p>${data.error}</p></div>`;
      return;
    }

    const ifaces = data.interfaces || [];
    if (!ifaces.length) {
      container.innerHTML = `
        <div class="state-msg">
          <p>No network interfaces detected.</p>
          <p class="text-muted" style="margin-top:8px">Check that /sys/class/net is accessible.</p>
        </div>`;
      return;
    }

    let html = `
      <p class="text-secondary" style="margin-bottom:16px;font-size:13px">
        Select the interface you want NetScope to monitor. Prefer physical interfaces
        (ethernet / wifi) to avoid double-counting VPN or bridge traffic.
      </p>
      <div class="iface-list">`;

    for (const iface of ifaces) {
      const typeBadge = iface.type || "other";
      const upBadge = iface.up
        ? `<span class="badge badge-success">up</span>`
        : `<span class="badge badge-muted">down</span>`;
      const vnBadge = iface.in_vnstat
        ? `<span class="badge badge-accent">vnStat</span>`
        : "";
      const selected = iface.selected ? "selected" : "";

      html += `
        <div class="iface-card ${selected}" data-name="${escapeAttr(iface.name)}">
          <div class="iface-info">
            <div class="iface-name">${escapeHtml(iface.name)} ${upBadge} ${vnBadge}</div>
            <div class="iface-meta">${typeBadge}</div>
          </div>
          <div class="iface-stats">
            <div>↓ ${formatBytes(iface.rx_bytes || iface.rx_total || 0)}</div>
            <div>↑ ${formatBytes(iface.tx_bytes || iface.tx_total || 0)}</div>
          </div>
        </div>`;
    }
    html += `</div>`;

    if (data.vnstat_error) {
      html += `<p class="text-muted" style="margin-top:16px;font-size:12px">vnStat: ${escapeHtml(data.vnstat_error)}</p>`;
    }

    container.innerHTML = html;

    container.querySelectorAll(".iface-card").forEach((card) => {
      card.addEventListener("click", async () => {
        const name = card.dataset.name;
        const res = await Api.setInterface(name);
        if (res.error) {
          toast(res.error, "error");
          return;
        }
        toast(`Monitoring ${name}`, "success");
        load(); // refresh selection state
      });
    });
  }

  function escapeHtml(s) {
    const d = document.createElement("div");
    d.textContent = s;
    return d.innerHTML;
  }
  function escapeAttr(s) {
    return String(s).replace(/"/g, "&quot;");
  }

  return { load };
})();
