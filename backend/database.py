"""SQLite database for application settings, quota config, and notification state."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

# Default location under user config
DB_DIR = Path.home() / ".config" / "netscope"
DB_PATH = DB_DIR / "netscope.db"


def get_connection() -> sqlite3.Connection:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create tables if they do not exist."""
    conn = get_connection()
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS quota (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                monthly_allowance_bytes INTEGER DEFAULT 0,
                billing_day INTEGER DEFAULT 1,
                quota_type TEXT DEFAULT 'combined',  -- 'combined' | 'download'
                warning_thresholds TEXT DEFAULT '[50,75,90,100]',
                enabled INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS notification_log (
                threshold INTEGER NOT NULL,
                billing_period TEXT NOT NULL,
                notified_at TEXT NOT NULL,
                PRIMARY KEY (threshold, billing_period)
            );

            CREATE TABLE IF NOT EXISTS app_state (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            INSERT OR IGNORE INTO quota (id) VALUES (1);
            """
        )
        conn.commit()
    finally:
        conn.close()


def get_setting(key: str, default: Any = None) -> Any:
    conn = get_connection()
    try:
        row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        if row is None:
            return default
        try:
            return json.loads(row["value"])
        except (json.JSONDecodeError, TypeError):
            return row["value"]
    finally:
        conn.close()


def set_setting(key: str, value: Any) -> None:
    conn = get_connection()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, json.dumps(value)),
        )
        conn.commit()
    finally:
        conn.close()


def get_all_settings() -> dict[str, Any]:
    conn = get_connection()
    try:
        rows = conn.execute("SELECT key, value FROM settings").fetchall()
        result = {}
        for row in rows:
            try:
                result[row["key"]] = json.loads(row["value"])
            except (json.JSONDecodeError, TypeError):
                result[row["key"]] = row["value"]
        return result
    finally:
        conn.close()


def get_quota() -> dict[str, Any]:
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM quota WHERE id = 1").fetchone()
        if not row:
            return {
                "monthly_allowance_bytes": 0,
                "billing_day": 1,
                "quota_type": "combined",
                "warning_thresholds": [50, 75, 90, 100],
                "enabled": False,
            }
        return {
            "monthly_allowance_bytes": row["monthly_allowance_bytes"] or 0,
            "billing_day": row["billing_day"] or 1,
            "quota_type": row["quota_type"] or "combined",
            "warning_thresholds": json.loads(row["warning_thresholds"] or "[50,75,90,100]"),
            "enabled": bool(row["enabled"]),
        }
    finally:
        conn.close()


def save_quota(data: dict[str, Any]) -> None:
    conn = get_connection()
    try:
        conn.execute(
            """
            UPDATE quota SET
                monthly_allowance_bytes = ?,
                billing_day = ?,
                quota_type = ?,
                warning_thresholds = ?,
                enabled = ?
            WHERE id = 1
            """,
            (
                int(data.get("monthly_allowance_bytes", 0)),
                int(data.get("billing_day", 1)),
                data.get("quota_type", "combined"),
                json.dumps(data.get("warning_thresholds", [50, 75, 90, 100])),
                1 if data.get("enabled") else 0,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def was_notified(threshold: int, billing_period: str) -> bool:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT 1 FROM notification_log WHERE threshold = ? AND billing_period = ?",
            (threshold, billing_period),
        ).fetchone()
        return row is not None
    finally:
        conn.close()


def mark_notified(threshold: int, billing_period: str) -> None:
    from datetime import datetime, timezone

    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT OR REPLACE INTO notification_log (threshold, billing_period, notified_at)
            VALUES (?, ?, ?)
            """,
            (threshold, billing_period, datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()
    finally:
        conn.close()


def get_state(key: str, default: Any = None) -> Any:
    conn = get_connection()
    try:
        row = conn.execute("SELECT value FROM app_state WHERE key = ?", (key,)).fetchone()
        if row is None:
            return default
        try:
            return json.loads(row["value"])
        except (json.JSONDecodeError, TypeError):
            return row["value"]
    finally:
        conn.close()


def set_state(key: str, value: Any) -> None:
    conn = get_connection()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO app_state (key, value) VALUES (?, ?)",
            (key, json.dumps(value)),
        )
        conn.commit()
    finally:
        conn.close()
