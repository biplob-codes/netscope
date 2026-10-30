"""vnStat integration – historical network usage data."""

from __future__ import annotations

import json
import subprocess
from datetime import date, datetime
from typing import Any


class VnStatError(Exception):
    """Raised when vnStat is unavailable or returns invalid data."""


def _run(args: list[str]) -> dict[str, Any]:
    """Run vnstat --json with the given arguments."""
    cmd = ["vnstat", "--json"] + args
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
    except FileNotFoundError:
        raise VnStatError(
            "vnStat is not installed. Install it with your package manager "
            "(e.g. sudo dnf install vnstat / sudo apt install vnstat)."
        )
    except subprocess.TimeoutExpired:
        raise VnStatError("vnStat command timed out.")

    if result.returncode != 0:
        err = (result.stderr or result.stdout or "").strip()
        if "No such file" in err or "does not exist" in err.lower():
            raise VnStatError(
                "vnStat database not initialized. Run: sudo vnstat --add -i <interface> "
                "and ensure the vnstat service is running."
            )
        raise VnStatError(err or "vnStat command failed.")

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as e:
        raise VnStatError(f"Invalid JSON from vnStat: {e}")


def is_available() -> dict[str, Any]:
    """Check whether vnStat is installed and usable."""
    try:
        data = _run([])
        interfaces = [i["name"] for i in data.get("interfaces", [])]
        return {"available": True, "interfaces": interfaces, "error": None}
    except VnStatError as e:
        return {"available": False, "interfaces": [], "error": str(e)}


def get_interfaces() -> list[dict[str, Any]]:
    """Return list of interfaces known to vnStat with basic info."""
    data = _run([])
    result = []
    for iface in data.get("interfaces", []):
        traffic = iface.get("traffic", {})
        total = traffic.get("total", {})
        result.append(
            {
                "name": iface.get("name", ""),
                "alias": iface.get("alias") or iface.get("name", ""),
                "created": iface.get("created"),
                "updated": iface.get("updated"),
                "rx_total": total.get("rx", 0),
                "tx_total": total.get("tx", 0),
            }
        )
    return result


def _pick_interface(data: dict, interface: str | None) -> dict:
    interfaces = data.get("interfaces", [])
    if not interfaces:
        raise VnStatError("No interfaces found in vnStat database.")
    if interface:
        for iface in interfaces:
            if iface.get("name") == interface:
                return iface
        raise VnStatError(f"Interface '{interface}' not found in vnStat.")
    return interfaces[0]


def get_daily(interface: str | None = None, limit: int = 30) -> list[dict]:
    """Daily traffic for the last `limit` days. Values in bytes."""
    args = ["d", str(limit)]
    if interface:
        args = ["-i", interface] + args
    data = _run(args)
    iface = _pick_interface(data, interface)
    days = iface.get("traffic", {}).get("day", [])
    result = []
    for day in days[-limit:]:
        d = day.get("date", {})
        day_date = date(d["year"], d["month"], d["day"])
        rx = day.get("rx", 0)
        tx = day.get("tx", 0)
        result.append(
            {
                "date": day_date.isoformat(),
                "rx": rx,
                "tx": tx,
                "total": rx + tx,
            }
        )
    return result


def get_monthly(interface: str | None = None, limit: int = 12) -> list[dict]:
    """Monthly traffic. Values in bytes."""
    args = ["m", str(limit)]
    if interface:
        args = ["-i", interface] + args
    data = _run(args)
    iface = _pick_interface(data, interface)
    months = iface.get("traffic", {}).get("month", [])
    result = []
    for m in months[-limit:]:
        d = m.get("date", {})
        rx = m.get("rx", 0)
        tx = m.get("tx", 0)
        result.append(
            {
                "year": d.get("year"),
                "month": d.get("month"),
                "date": f"{d.get('year')}-{d.get('month'):02d}",
                "rx": rx,
                "tx": tx,
                "total": rx + tx,
            }
        )
    return result


def get_hourly(interface: str | None = None) -> list[dict]:
    """Hourly traffic for the current day (or last 24h depending on vnStat version)."""
    args = ["h"]
    if interface:
        args = ["-i", interface] + args
    data = _run(args)
    iface = _pick_interface(data, interface)
    hours = iface.get("traffic", {}).get("hour", [])
    result = []
    for h in hours:
        d = h.get("date", {})
        t = h.get("time", {})
        rx = h.get("rx", 0)
        tx = h.get("tx", 0)
        hour_str = f"{d.get('year')}-{d.get('month'):02d}-{d.get('day'):02d}T{t.get('hour', 0):02d}:00:00"
        result.append(
            {
                "datetime": hour_str,
                "hour": t.get("hour", 0),
                "rx": rx,
                "tx": tx,
                "total": rx + tx,
            }
        )
    return result


def get_yearly(interface: str | None = None) -> list[dict]:
    """Yearly traffic."""
    args = ["y"]
    if interface:
        args = ["-i", interface] + args
    data = _run(args)
    iface = _pick_interface(data, interface)
    years = iface.get("traffic", {}).get("year", [])
    result = []
    for y in years:
        d = y.get("date", {})
        rx = y.get("rx", 0)
        tx = y.get("tx", 0)
        result.append(
            {
                "year": d.get("year"),
                "rx": rx,
                "tx": tx,
                "total": rx + tx,
            }
        )
    return result


def get_today(interface: str | None = None) -> dict:
    """Today's usage."""
    days = get_daily(interface=interface, limit=1)
    if not days:
        return {"date": date.today().isoformat(), "rx": 0, "tx": 0, "total": 0}
    today = date.today().isoformat()
    for d in days:
        if d["date"] == today:
            return d
    # Fallback to most recent day
    return days[-1] if days else {"date": today, "rx": 0, "tx": 0, "total": 0}


def get_yesterday(interface: str | None = None) -> dict:
    days = get_daily(interface=interface, limit=2)
    today = date.today().isoformat()
    for d in reversed(days):
        if d["date"] != today:
            return d
    return {"date": "", "rx": 0, "tx": 0, "total": 0}


def get_current_month(interface: str | None = None) -> dict:
    months = get_monthly(interface=interface, limit=1)
    if not months:
        now = date.today()
        return {"year": now.year, "month": now.month, "date": f"{now.year}-{now.month:02d}", "rx": 0, "tx": 0, "total": 0}
    return months[-1]


def get_total(interface: str | None = None) -> dict:
    """All-time total from vnStat."""
    data = _run(["-i", interface] if interface else [])
    iface = _pick_interface(data, interface)
    total = iface.get("traffic", {}).get("total", {})
    return {
        "rx": total.get("rx", 0),
        "tx": total.get("tx", 0),
        "total": total.get("rx", 0) + total.get("tx", 0),
    }


def get_traffic_since(start: date, interface: str | None = None) -> dict:
    """Sum daily traffic from start date inclusive to today."""
    days = get_daily(interface=interface, limit=90)
    rx = tx = 0
    for d in days:
        dd = date.fromisoformat(d["date"])
        if dd >= start:
            rx += d["rx"]
            tx += d["tx"]
    return {"rx": rx, "tx": tx, "total": rx + tx, "from": start.isoformat()}


def bytes_to_human(num: int | float, precision: int = 2) -> str:
    """Convert bytes to human-readable string."""
    num = float(num)
    for unit in ["B", "KB", "MB", "GB", "TB", "PB"]:
        if abs(num) < 1024.0:
            if unit == "B":
                return f"{int(num)} {unit}"
            return f"{num:.{precision}f} {unit}"
        num /= 1024.0
    return f"{num:.{precision}f} EB"
