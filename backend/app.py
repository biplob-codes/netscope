"""Main API class exposed to JavaScript via PyWebView."""

from __future__ import annotations

from typing import Any

from . import (
    analytics,
    database,
    export_manager,
    interface_manager,
    network_monitor,
    notification_manager,
    quota_manager,
    settings_manager,
    vnstat,
)


class Api:
    """JavaScript ↔ Python bridge. All public methods are callable from JS."""

    def __init__(self) -> None:
        database.init_db()
        # Ensure live monitor has an interface
        interface_manager.ensure_monitor_interface()

    # ── Dashboard ──────────────────────────────────────────────

    def get_dashboard_data(self) -> dict[str, Any]:
        iface = interface_manager.get_selected_interface()
        try:
            today = vnstat.get_today(iface)
            yesterday = vnstat.get_yesterday(iface)
            month = vnstat.get_current_month(iface)
            total = vnstat.get_total(iface)
            days = vnstat.get_daily(iface, limit=14)
        except Exception as e:
            return {"error": str(e)}

        live = network_monitor.monitor.get_stats()
        quota = quota_manager.get_quota_status(iface)

        # Daily average (last 14 days)
        avg_daily = 0
        if days:
            avg_daily = sum(d["total"] for d in days) / len(days)

        # Simple estimated month from average
        estimated_month = int(avg_daily * 30)

        return {
            "today": today,
            "yesterday": yesterday,
            "month": month,
            "total": total,
            "recent_days": days,
            "live": {
                "rx_speed": live["rx_speed"],
                "tx_speed": live["tx_speed"],
                "interface": live["interface"],
                "connected": live["connected"],
            },
            "quota": quota,
            "avg_daily": int(avg_daily),
            "estimated_month": estimated_month,
            "interface": iface,
            "error": None,
        }

    # ── Live monitor ───────────────────────────────────────────

    def get_live_stats(self) -> dict[str, Any]:
        return network_monitor.monitor.get_stats()

    # ── Interfaces ─────────────────────────────────────────────

    def get_interfaces(self) -> dict[str, Any]:
        return interface_manager.get_all_interfaces()

    def set_selected_interface(self, name: str | None) -> dict[str, Any]:
        return interface_manager.set_selected_interface(name)

    # ── Analytics ──────────────────────────────────────────────

    def get_usage_history(
        self, period: str = "daily", limit: int | None = None
    ) -> dict[str, Any]:
        return analytics.get_usage_history(period=period, limit=limit)

    def get_comparison(self) -> dict[str, Any]:
        return analytics.get_comparison()

    def get_insights(self) -> list[dict[str, str]]:
        return analytics.get_insights()

    def get_peak_days(self, limit: int = 5) -> list[dict]:
        return analytics.get_peak_days(limit=limit)

    # ── Quota ──────────────────────────────────────────────────

    def get_quota_status(self) -> dict[str, Any]:
        return quota_manager.get_quota_status()

    def get_quota_settings(self) -> dict[str, Any]:
        return quota_manager.get_quota_settings()

    def save_quota_settings(self, data: dict) -> dict[str, Any]:
        return quota_manager.save_quota_settings(data)

    # ── Settings ───────────────────────────────────────────────

    def get_settings(self) -> dict[str, Any]:
        return settings_manager.get_settings()

    def save_settings(self, data: dict) -> dict[str, Any]:
        return settings_manager.save_settings(data)

    # ── Notifications ──────────────────────────────────────────

    def check_notifications(self) -> list[dict[str, Any]]:
        return notification_manager.check_quota_notifications()

    def test_notification(self) -> dict[str, Any]:
        return notification_manager.test_notification()

    # ── Export ─────────────────────────────────────────────────

    def export_usage(
        self, period: str = "daily", fmt: str = "csv", limit: int | None = None
    ) -> dict[str, Any]:
        return export_manager.export_data(period=period, fmt=fmt, limit=limit)

    # ── Utilities ──────────────────────────────────────────────

    def bytes_to_human(self, num: int | float) -> str:
        return vnstat.bytes_to_human(num)

    def check_vnstat(self) -> dict[str, Any]:
        return vnstat.is_available()
