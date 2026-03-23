"""Analyze user financial habits for reminder suggestions."""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from services.database import get_assets, get_records

_DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
_DAYS_ID = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]


async def analyze_user_habits(user_id: int) -> list[dict[str, Any]]:
    """Return suggested reminders based on the user's record and asset patterns."""
    from_date = date.today() - timedelta(days=90)
    records = await get_records(user_id, from_date=from_date)
    assets = await get_assets(user_id)

    suggestions: list[dict[str, Any]] = []

    # Record frequency by day of week
    dow_counts: dict[int, int] = {}
    for r in records:
        at = r.get("at")
        if not at:
            continue
        try:
            dt = datetime.fromisoformat(at)
            dow_counts[dt.weekday()] = dow_counts.get(dt.weekday(), 0) + 1
        except ValueError:
            continue

    if dow_counts:
        avg = sum(dow_counts.values()) / 7
        for dow, count in sorted(dow_counts.items(), key=lambda x: -x[1]):
            if count >= 3 and count > avg * 1.5:
                suggestions.append({
                    "kind": "note_expense",
                    "title": f"Catat pengeluaran hari {_DAYS_ID[dow]}",
                    "schedule_type": "weekly",
                    "day": _DAYS[dow],
                    "hour": 20,
                    "minute": 0,
                    "reason": (
                        f"Kamu mencatat ~{count} transaksi di hari "
                        f"{_DAYS_ID[dow]} dalam 90 hari terakhir."
                    ),
                })
                if len(suggestions) >= 2:
                    break

    # Asset purchase patterns by day of week
    asset_dow: dict[str, dict[int, int]] = {}
    for a in assets:
        at = a.get("created_at")
        if not at:
            continue
        try:
            dt = datetime.fromisoformat(at)
            key = f"{a.get('asset_type', '')}:{a.get('name', '')}"
            if key not in asset_dow:
                asset_dow[key] = {}
            asset_dow[key][dt.weekday()] = asset_dow[key].get(dt.weekday(), 0) + 1
        except ValueError:
            continue

    for asset_key, dow_map in asset_dow.items():
        for dow, count in dow_map.items():
            if count >= 3:
                parts = asset_key.split(":", 1)
                atype = parts[0] if len(parts) > 1 else ""
                name = parts[1] if len(parts) > 1 else asset_key
                suggestions.append({
                    "kind": "price",
                    "title": f"Cek harga {name} sebelum beli",
                    "schedule_type": "weekly",
                    "day": _DAYS[dow],
                    "hour": 7,
                    "minute": 0,
                    "payload": {"symbols": [name], "asset_types": [atype]},
                    "reason": (
                        f"Kamu biasa membeli {name} di hari "
                        f"{_DAYS_ID[dow]} ({count}x dalam 90 hari)."
                    ),
                })

    # Portfolio digest for users with meaningful holdings
    if len(assets) >= 3:
        suggestions.append({
            "kind": "portfolio_digest",
            "title": "Ringkasan portofolio mingguan",
            "schedule_type": "weekly",
            "day": "monday",
            "hour": 8,
            "minute": 0,
            "reason": (
                f"Kamu punya {len(assets)} aset. "
                f"Ringkasan mingguan membantu monitor investasi."
            ),
        })

    return suggestions[:5]
