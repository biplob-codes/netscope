"""Export usage statistics to CSV / JSON."""

from __future__ import annotations

import csv
import io
import json
from typing import Any

from . import vnstat
from .interface_manager import get_selected_interface


def export_data(
    period: str = "daily",
    fmt: str = "csv",
    interface: str | None = None,
    limit: int | None = None,
) -> dict[str, Any]:
    """
    Return exported data as a string plus suggested filename.
    Frontend can trigger a download.
    """
    iface = interface or get_selected_interface()
    try:
        if period == "daily":
            data = vnstat.get_daily(iface, limit=limit or 90)
            fields = ["date", "rx", "tx", "total"]
        elif period == "monthly":
            data = vnstat.get_monthly(iface, limit=limit or 24)
            fields = ["date", "year", "month", "rx", "tx", "total"]
        elif period == "yearly":
            data = vnstat.get_yearly(iface)
            fields = ["year", "rx", "tx", "total"]
        elif period == "hourly":
            data = vnstat.get_hourly(iface)
            fields = ["datetime", "hour", "rx", "tx", "total"]
        else:
            return {"error": f"Unsupported period: {period}"}
    except Exception as e:
        return {"error": str(e)}

    if not data:
        return {"error": "No data available to export."}

    filename = f"netscope_{period}_{iface or 'all'}.{fmt}"

    if fmt == "json":
        content = json.dumps(data, indent=2)
        return {"content": content, "filename": filename, "mime": "application/json"}

    if fmt == "csv":
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in data:
            writer.writerow(row)
        return {"content": buf.getvalue(), "filename": filename, "mime": "text/csv"}

    return {"error": f"Unsupported format: {fmt}"}
