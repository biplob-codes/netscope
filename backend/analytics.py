"""Usage analytics and insights derived from vnStat data."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Any

from . import vnstat
from .interface_manager import get_selected_interface


def get_usage_history(
    period: str = "daily",
    interface: str | None = None,
    limit: int | None = None,
) -> dict[str, Any]:
    """Return historical usage for charts."""
    iface = interface or get_selected_interface()
    try:
        if period == "hourly":
            data = vnstat.get_hourly(iface)
            return {"period": "hourly", "data": data, "error": None}
        if period == "daily":
            lim = limit or 30
            data = vnstat.get_daily(iface, limit=lim)
            return {"period": "daily", "data": data, "error": None}
        if period == "monthly":
            lim = limit or 12
            data = vnstat.get_monthly(iface, limit=lim)
            return {"period": "monthly", "data": data, "error": None}
        if period == "yearly":
            data = vnstat.get_yearly(iface)
            return {"period": "yearly", "data": data, "error": None}
        return {"period": period, "data": [], "error": f"Unknown period: {period}"}
    except Exception as e:
        return {"period": period, "data": [], "error": str(e)}


def get_comparison(interface: str | None = None) -> dict[str, Any]:
    """Compare current month vs previous month, this week vs last week, etc."""
    iface = interface or get_selected_interface()
    result: dict[str, Any] = {"error": None}

    try:
        months = vnstat.get_monthly(iface, limit=2)
        if len(months) >= 2:
            curr, prev = months[-1], months[-2]
            result["month"] = {
                "current": curr,
                "previous": prev,
                "rx_change_pct": _pct_change(prev["rx"], curr["rx"]),
                "tx_change_pct": _pct_change(prev["tx"], curr["tx"]),
                "total_change_pct": _pct_change(prev["total"], curr["total"]),
            }
        elif len(months) == 1:
            result["month"] = {"current": months[0], "previous": None}

        days = vnstat.get_daily(iface, limit=14)
        today = date.today()
        this_week_start = today - timedelta(days=today.weekday())
        last_week_start = this_week_start - timedelta(days=7)
        last_week_end = this_week_start - timedelta(days=1)

        this_week = {"rx": 0, "tx": 0, "total": 0}
        last_week = {"rx": 0, "tx": 0, "total": 0}
        for d in days:
            dd = date.fromisoformat(d["date"])
            if dd >= this_week_start:
                this_week["rx"] += d["rx"]
                this_week["tx"] += d["tx"]
                this_week["total"] += d["total"]
            elif last_week_start <= dd <= last_week_end:
                last_week["rx"] += d["rx"]
                last_week["tx"] += d["tx"]
                last_week["total"] += d["total"]

        result["week"] = {
            "current": this_week,
            "previous": last_week,
            "total_change_pct": _pct_change(last_week["total"], this_week["total"]),
        }
    except Exception as e:
        result["error"] = str(e)

    return result


def get_insights(interface: str | None = None) -> list[dict[str, str]]:
    """Generate simple, data-driven insights. Returns empty list if insufficient data."""
    iface = interface or get_selected_interface()
    insights: list[dict[str, str]] = []

    try:
        days = vnstat.get_daily(iface, limit=30)
        if len(days) < 3:
            return insights

        # Average daily
        avg = sum(d["total"] for d in days) / len(days)
        insights.append(
            {
                "type": "average",
                "title": "Average daily usage",
                "text": f"Your average daily consumption over the last {len(days)} days is {vnstat.bytes_to_human(avg)}.",
            }
        )

        # Highest day
        peak = max(days, key=lambda d: d["total"])
        insights.append(
            {
                "type": "peak_day",
                "title": "Highest usage day",
                "text": f"Your highest usage day was {peak['date']} with {vnstat.bytes_to_human(peak['total'])}.",
            }
        )

        # Weekday vs weekend
        weekday_totals = []
        weekend_totals = []
        for d in days:
            dd = date.fromisoformat(d["date"])
            if dd.weekday() >= 5:
                weekend_totals.append(d["total"])
            else:
                weekday_totals.append(d["total"])
        if weekday_totals and weekend_totals:
            w_avg = sum(weekday_totals) / len(weekday_totals)
            we_avg = sum(weekend_totals) / len(weekend_totals)
            if we_avg > w_avg * 1.15:
                insights.append(
                    {
                        "type": "weekend",
                        "title": "Weekend usage",
                        "text": f"Your weekend usage is higher than weekdays ({vnstat.bytes_to_human(we_avg)} vs {vnstat.bytes_to_human(w_avg)} on average).",
                    }
                )
            elif w_avg > we_avg * 1.15:
                insights.append(
                    {
                        "type": "weekday",
                        "title": "Weekday usage",
                        "text": f"Your weekday usage is higher than weekends ({vnstat.bytes_to_human(w_avg)} vs {vnstat.bytes_to_human(we_avg)} on average).",
                    }
                )

        # Day-of-week pattern
        by_dow: dict[int, list[int]] = defaultdict(list)
        for d in days:
            dd = date.fromisoformat(d["date"])
            by_dow[dd.weekday()].append(d["total"])
        if by_dow:
            avg_by_dow = {k: sum(v) / len(v) for k, v in by_dow.items()}
            busiest = max(avg_by_dow, key=avg_by_dow.get)  # type: ignore
            day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            insights.append(
                {
                    "type": "busy_day",
                    "title": "Busiest day of week",
                    "text": f"On average, {day_names[busiest]} is your highest-usage day ({vnstat.bytes_to_human(avg_by_dow[busiest])}).",
                }
            )

        # Month projection
        months = vnstat.get_monthly(iface, limit=1)
        if months:
            curr = months[-1]
            today = date.today()
            if curr.get("month") == today.month and curr.get("year") == today.year:
                days_in_month = 30  # approximate
                elapsed = today.day
                if elapsed > 0:
                    projected = (curr["total"] / elapsed) * days_in_month
                    insights.append(
                        {
                            "type": "projection",
                            "title": "Monthly projection",
                            "text": f"At the current rate you are projected to use about {vnstat.bytes_to_human(projected)} this month.",
                        }
                    )

        # Week-over-week
        if len(days) >= 14:
            recent = sum(d["total"] for d in days[-7:])
            previous = sum(d["total"] for d in days[-14:-7])
            if previous > 0:
                change = ((recent - previous) / previous) * 100
                direction = "increased" if change > 0 else "decreased"
                insights.append(
                    {
                        "type": "trend",
                        "title": "Weekly trend",
                        "text": f"Your usage has {direction} by {abs(change):.0f}% compared with the previous week.",
                    }
                )

    except Exception:
        pass

    return insights


def get_peak_days(interface: str | None = None, limit: int = 5) -> list[dict]:
    iface = interface or get_selected_interface()
    try:
        days = vnstat.get_daily(iface, limit=60)
        sorted_days = sorted(days, key=lambda d: d["total"], reverse=True)
        return sorted_days[:limit]
    except Exception:
        return []


def _pct_change(old: float, new: float) -> float | None:
    if old == 0:
        return None
    return round(((new - old) / old) * 100, 1)
