"""Network interface selection and management."""

from __future__ import annotations

from typing import Any

from . import database, network_monitor, vnstat


def get_all_interfaces() -> dict[str, Any]:
    """Combine system interfaces and vnStat interfaces."""
    system = network_monitor.monitor.list_system_interfaces()
    vn_ifaces = []
    vn_error = None
    try:
        vn_ifaces = vnstat.get_interfaces()
    except Exception as e:
        vn_error = str(e)

    selected = database.get_setting("selected_interface", None)

    # Build unified list
    by_name = {i["name"]: i for i in system}
    for v in vn_ifaces:
        name = v["name"]
        if name in by_name:
            by_name[name]["in_vnstat"] = True
            by_name[name]["rx_total"] = v.get("rx_total", 0)
            by_name[name]["tx_total"] = v.get("tx_total", 0)
        else:
            by_name[name] = {
                "name": name,
                "type": "unknown",
                "up": False,
                "rx_bytes": 0,
                "tx_bytes": 0,
                "in_vnstat": True,
                "rx_total": v.get("rx_total", 0),
                "tx_total": v.get("tx_total", 0),
            }

    interfaces = list(by_name.values())
    for i in interfaces:
        i["selected"] = i["name"] == selected
        i.setdefault("in_vnstat", False)

    return {
        "interfaces": interfaces,
        "selected": selected,
        "vnstat_error": vn_error,
    }


def set_selected_interface(name: str | None) -> dict[str, Any]:
    database.set_setting("selected_interface", name)
    network_monitor.monitor.set_interface(name)
    return {"success": True, "selected": name}


def get_selected_interface() -> str | None:
    return database.get_setting("selected_interface", None)


def ensure_monitor_interface() -> str | None:
    """Make sure the live monitor has a valid interface set."""
    selected = get_selected_interface()
    if selected:
        network_monitor.monitor.set_interface(selected)
        return selected

    # Auto-pick first up non-virtual interface
    ifaces = network_monitor.monitor.list_system_interfaces()
    preferred = None
    for i in ifaces:
        if i["up"] and i["type"] in ("ethernet", "wifi"):
            preferred = i["name"]
            break
    if not preferred and ifaces:
        preferred = ifaces[0]["name"]
    if preferred:
        network_monitor.monitor.set_interface(preferred)
    return preferred
