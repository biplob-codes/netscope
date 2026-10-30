"""Desktop notifications for quota thresholds and other events."""

from __future__ import annotations

import subprocess
from typing import Any

from . import database, quota_manager


def _notify(title: str, body: str, urgency: str = "normal") -> bool:
    """Send a desktop notification via notify-send (libnotify)."""
    try:
        subprocess.run(
            [
                "notify-send",
                "--app-name=NetScope",
                f"--urgency={urgency}",
                "--icon=network-transmit-receive",
                title,
                body,
            ],
            check=False,
            timeout=5,
            capture_output=True,
        )
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def check_quota_notifications() -> list[dict[str, Any]]:
    """
    Check current quota usage against thresholds and send notifications
    if needed. Returns list of notifications that were (or would be) sent.
    """
    status = quota_manager.get_quota_status()
    if not status.get("enabled"):
        return []

    notifications_enabled = database.get_setting("notifications_enabled", True)
    if not notifications_enabled:
        return []

    percent = status.get("percent", 0)
    thresholds = sorted(status.get("thresholds", [50, 75, 90, 100]))
    period = status.get("billing_start") or "unknown"
    sent = []

    for thr in thresholds:
        if percent >= thr and not database.was_notified(thr, period):
            title = "Data limit warning" if thr < 100 else "Data limit reached"
            body = (
                f"You have used {percent:.0f}% of your monthly data allowance "
                f"({_human(status['used'])} of {_human(status['allowance'])})."
            )
            urgency = "critical" if thr >= 90 else "normal"
            ok = _notify(title, body, urgency=urgency)
            database.mark_notified(thr, period)
            sent.append({"threshold": thr, "sent": ok, "title": title, "body": body})

    return sent


def _human(n: int) -> str:
    from . import vnstat

    return vnstat.bytes_to_human(n)


def test_notification() -> dict[str, Any]:
    ok = _notify(
        "NetScope",
        "Notifications are working correctly.",
        urgency="low",
    )
    return {"success": ok}
