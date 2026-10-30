"""Real-time network bandwidth monitoring using /sys/class/net/ counters."""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

SYS_NET = Path("/sys/class/net")


class NetworkMonitor:
    """Non-blocking real-time bandwidth calculator."""

    def __init__(self) -> None:
        self._interface: str | None = None
        self._prev_rx: int = 0
        self._prev_tx: int = 0
        self._prev_time: float = 0.0
        self._peak_rx: float = 0.0  # bytes/s
        self._peak_tx: float = 0.0
        self._session_rx: int = 0
        self._session_tx: int = 0
        self._session_start: float = time.time()

    def set_interface(self, interface: str | None) -> None:
        if interface != self._interface:
            self._interface = interface
            self._reset_counters()

    def _reset_counters(self) -> None:
        rx, tx = self._read_counters()
        self._prev_rx = rx
        self._prev_tx = tx
        self._prev_time = time.time()
        self._peak_rx = 0.0
        self._peak_tx = 0.0
        self._session_rx = 0
        self._session_tx = 0
        self._session_start = time.time()

    def _read_counters(self) -> tuple[int, int]:
        if not self._interface:
            return 0, 0
        rx_path = SYS_NET / self._interface / "statistics" / "rx_bytes"
        tx_path = SYS_NET / self._interface / "statistics" / "tx_bytes"
        try:
            rx = int(rx_path.read_text().strip())
            tx = int(tx_path.read_text().strip())
            return rx, tx
        except (OSError, ValueError):
            return 0, 0

    def get_stats(self) -> dict[str, Any]:
        """Return current speeds and counters. Call periodically (e.g. every 1s)."""
        now = time.time()
        rx, tx = self._read_counters()

        if self._prev_time == 0 or not self._interface:
            self._prev_rx = rx
            self._prev_tx = tx
            self._prev_time = now
            return {
                "interface": self._interface,
                "rx_speed": 0.0,
                "tx_speed": 0.0,
                "rx_bytes": rx,
                "tx_bytes": tx,
                "peak_rx": 0.0,
                "peak_tx": 0.0,
                "session_rx": 0,
                "session_tx": 0,
                "session_seconds": 0,
                "connected": self._is_up(),
            }

        dt = now - self._prev_time
        if dt <= 0:
            dt = 0.001

        drx = max(0, rx - self._prev_rx)
        dtx = max(0, tx - self._prev_tx)

        # Handle counter wrap (unlikely for 64-bit but possible on some systems)
        if rx < self._prev_rx:
            drx = rx
        if tx < self._prev_tx:
            dtx = tx

        rx_speed = drx / dt
        tx_speed = dtx / dt

        self._peak_rx = max(self._peak_rx, rx_speed)
        self._peak_tx = max(self._peak_tx, tx_speed)
        self._session_rx += drx
        self._session_tx += dtx

        self._prev_rx = rx
        self._prev_tx = tx
        self._prev_time = now

        return {
            "interface": self._interface,
            "rx_speed": rx_speed,
            "tx_speed": tx_speed,
            "rx_bytes": rx,
            "tx_bytes": tx,
            "peak_rx": self._peak_rx,
            "peak_tx": self._peak_tx,
            "session_rx": self._session_rx,
            "session_tx": self._session_tx,
            "session_seconds": int(now - self._session_start),
            "connected": self._is_up(),
        }

    def _is_up(self) -> bool:
        if not self._interface:
            return False
        operstate = SYS_NET / self._interface / "operstate"
        try:
            state = operstate.read_text().strip()
            return state == "up"
        except OSError:
            return False

    def list_system_interfaces(self) -> list[dict[str, Any]]:
        """List interfaces present in /sys/class/net."""
        result = []
        if not SYS_NET.exists():
            return result
        for entry in sorted(SYS_NET.iterdir()):
            if not entry.is_dir():
                continue
            name = entry.name
            if name == "lo":
                continue
            info: dict[str, Any] = {
                "name": name,
                "type": self._guess_type(name, entry),
                "up": False,
                "rx_bytes": 0,
                "tx_bytes": 0,
            }
            try:
                oper = (entry / "operstate").read_text().strip()
                info["up"] = oper == "up"
            except OSError:
                pass
            try:
                info["rx_bytes"] = int((entry / "statistics" / "rx_bytes").read_text().strip())
                info["tx_bytes"] = int((entry / "statistics" / "tx_bytes").read_text().strip())
            except (OSError, ValueError):
                pass
            result.append(info)
        return result

    def _guess_type(self, name: str, path: Path) -> str:
        name_l = name.lower()
        if name_l.startswith(("wl", "wlan", "wifi")):
            return "wifi"
        if name_l.startswith(("en", "eth", "eno", "ens", "enp")):
            return "ethernet"
        if name_l.startswith(("tun", "tap", "wg", "vpn", "ppp")):
            return "vpn"
        if name_l.startswith(("br", "docker", "veth", "virbr")):
            return "virtual"
        # Try type file
        type_file = path / "type"
        try:
            t = int(type_file.read_text().strip())
            # ARPHRD_ETHER = 1, etc. – rough mapping
            if t == 1:
                return "ethernet"
        except (OSError, ValueError):
            pass
        return "other"


# Singleton used by the API
monitor = NetworkMonitor()
