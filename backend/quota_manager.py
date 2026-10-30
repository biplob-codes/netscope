"""Monthly data quota / allowance management."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from . import database, vnstat
from .interface_manager import get_selected_interface


def _billing_period_start(billing_day: int, ref: date | None = None) -> date:
    """Return the start date of the current billing cycle."""
    today = ref or date.today()
    day = max(1, min(28, billing_day))  # safe day
    if today.day >= day:
        return date(today.year, today.month, day)
    # Previous month
    if today.month == 1:
        return date(today.year - 1, 12, day)
    return date(today.year, today.month - 1, day)


def _billing_period_end(start: date) -> date:
    """Approximate end of billing cycle (day before next cycle)."""
    if start.month == 12:
        next_start = date(start.year + 1, 1, start.day)
    else:
        next_start = date(start.year, start.month + 1, start.day)
    return next_start - timedelta(days=1)


def get_quota_status(interface: str | None = None) -> dict[str, Any]:
    """Full quota status for the dashboard and quota page."""
    cfg = database.get_quota()
    iface = interface or get_selected_interface()

    if not cfg.get("enabled") or cfg.get("monthly_allowance_bytes", 0) <= 0:
        return {
            "enabled": False,
            "allowance": 0,
            "used": 0,
            "remaining": 0,
            "percent": 0.0,
            "days_remaining": 0,
            "days_elapsed": 0,
            "cycle_days": 0,
            "avg_daily": 0,
            "recommended_daily": 0,
            "projected": 0,
            "billing_start": None,
            "billing_end": None,
            "quota_type": cfg.get("quota_type", "combined"),
            "thresholds": cfg.get("warning_thresholds", []),
        }

    start = _billing_period_start(cfg["billing_day"])
    end = _billing_period_end(start)
    today = date.today()
    cycle_days = (end - start).days + 1
    days_elapsed = max(1, (today - start).days + 1)
    days_remaining = max(0, (end - today).days)

    try:
        traffic = vnstat.get_traffic_since(start, interface=iface)
    except Exception:
        traffic = {"rx": 0, "tx": 0, "total": 0}

    if cfg.get("quota_type") == "download":
        used = traffic["rx"]
    else:
        used = traffic["total"]

    allowance = cfg["monthly_allowance_bytes"]
    remaining = max(0, allowance - used)
    percent = (used / allowance * 100) if allowance else 0.0
    avg_daily = used / days_elapsed if days_elapsed else 0
    recommended = remaining / days_remaining if days_remaining > 0 else 0
    projected = avg_daily * cycle_days

    return {
        "enabled": True,
        "allowance": allowance,
        "used": used,
        "remaining": remaining,
        "percent": round(percent, 1),
        "days_remaining": days_remaining,
        "days_elapsed": days_elapsed,
        "cycle_days": cycle_days,
        "avg_daily": int(avg_daily),
        "recommended_daily": int(recommended),
        "projected": int(projected),
        "billing_start": start.isoformat(),
        "billing_end": end.isoformat(),
        "quota_type": cfg.get("quota_type", "combined"),
        "thresholds": cfg.get("warning_thresholds", [50, 75, 90, 100]),
        "billing_day": cfg.get("billing_day", 1),
    }


def get_quota_settings() -> dict[str, Any]:
    return database.get_quota()


def save_quota_settings(data: dict[str, Any]) -> dict[str, Any]:
    # Normalize
    allowance = data.get("monthly_allowance_bytes", 0)
    if isinstance(allowance, str):
        # Allow human input like "100 GB"
        allowance = _parse_size(allowance)
    data["monthly_allowance_bytes"] = int(allowance)
    data["billing_day"] = max(1, min(28, int(data.get("billing_day", 1))))
    data["quota_type"] = data.get("quota_type", "combined")
    if data["quota_type"] not in ("combined", "download"):
        data["quota_type"] = "combined"
    thresholds = data.get("warning_thresholds", [50, 75, 90, 100])
    data["warning_thresholds"] = [int(t) for t in thresholds]
    data["enabled"] = bool(data.get("enabled", False))

    database.save_quota(data)
    return {"success": True, "quota": database.get_quota()}


def _parse_size(s: str) -> int:
    s = s.strip().upper().replace(",", "")
    multipliers = {
        "B": 1,
        "KB": 1024,
        "MB": 1024**2,
        "GB": 1024**3,
        "TB": 1024**4,
    }
    for unit, mult in multipliers.items():
        if s.endswith(unit):
            try:
                return int(float(s[: -len(unit)].strip()) * mult)
            except ValueError:
                return 0
    try:
        return int(float(s))
    except ValueError:
        return 0
