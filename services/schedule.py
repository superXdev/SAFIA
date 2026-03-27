"""Schedule computation — next run time from schedule JSON + timezone."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo


def compute_next_run(
    schedule_json: str, tz_name: str, after: datetime | None = None
) -> datetime:
    """Compute the next run time (UTC) from a schedule JSON and timezone.

    Supported schedule types:
    - daily:    {"type": "daily",   "hour": 8, "minute": 0}
    - weekly:   {"type": "weekly",  "day": "monday", "hour": 8, "minute": 0}
    - monthly:  {"type": "monthly", "day_of_month": 1, "hour": 8, "minute": 0}
    - interval: {"type": "interval", "hours": 12}  # hours may be fractional (e.g. 0.5 = 30 min)
    """
    schedule = json.loads(schedule_json)
    try:
        tz = ZoneInfo(tz_name)
    except (KeyError, Exception):
        tz = ZoneInfo("Asia/Jakarta")
    now_utc = after or datetime.now(timezone.utc)
    now_local = now_utc.astimezone(tz)

    stype = schedule.get("type", "daily")
    hour = int(schedule.get("hour", 8))
    minute = int(schedule.get("minute", 0))

    if stype == "daily":
        candidate = now_local.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if candidate <= now_local:
            candidate += timedelta(days=1)
        return candidate.astimezone(timezone.utc)

    if stype == "weekly":
        day_name = schedule.get("day", "monday").lower()
        days_map = [
            "monday", "tuesday", "wednesday", "thursday",
            "friday", "saturday", "sunday",
        ]
        target_dow = days_map.index(day_name) if day_name in days_map else 0
        candidate = now_local.replace(hour=hour, minute=minute, second=0, microsecond=0)
        days_ahead = target_dow - candidate.weekday()
        if days_ahead < 0 or (days_ahead == 0 and candidate <= now_local):
            days_ahead += 7
        candidate += timedelta(days=days_ahead)
        return candidate.astimezone(timezone.utc)

    if stype == "monthly":
        dom = max(1, min(28, int(schedule.get("day_of_month", 1))))
        candidate = now_local.replace(
            day=dom, hour=hour, minute=minute, second=0, microsecond=0
        )
        if candidate <= now_local:
            if candidate.month == 12:
                candidate = candidate.replace(year=candidate.year + 1, month=1)
            else:
                candidate = candidate.replace(month=candidate.month + 1)
        return candidate.astimezone(timezone.utc)

    if stype == "interval":
        try:
            hours = float(schedule.get("hours", 24))
        except (TypeError, ValueError):
            hours = 24.0
        hours = max(1.0 / 60.0, hours)
        return now_utc + timedelta(hours=hours)

    # Fallback
    return now_utc + timedelta(days=1)
