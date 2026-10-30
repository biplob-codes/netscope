"""Application-level settings."""

from __future__ import annotations

from typing import Any

from . import database

DEFAULTS = {
    "theme": "dark",
    "notifications_enabled": True,
    "refresh_interval_sec": 1,
    "selected_interface": None,
    "start_on_login": False,
    "minimize_to_tray": False,
}


def get_settings() -> dict[str, Any]:
    stored = database.get_all_settings()
    result = DEFAULTS.copy()
    result.update(stored)
    # Also pull selected interface consistently
    result["selected_interface"] = database.get_setting("selected_interface", None)
    return result


def save_settings(data: dict[str, Any]) -> dict[str, Any]:
    allowed = set(DEFAULTS.keys())
    for key, value in data.items():
        if key in allowed:
            database.set_setting(key, value)
    return {"success": True, "settings": get_settings()}
