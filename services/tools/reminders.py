"""Reminder tools — create, list, pause, resume, delete, habit suggestions."""
import hashlib
import json
from typing import Any

from services.habit_analysis import analyze_user_habits
from services.models import Reminder
from services.reminders_db import (
    create_reminder,
    delete_reminder,
    get_user_reminders,
    toggle_reminder,
)
from services.schedule import compute_next_run

def _build_schedule_json(arguments: dict[str, Any]) -> str:
    schedule_type = arguments.get("schedule_type", "daily")
    hour = int(arguments.get("hour", 8))
    minute = int(arguments.get("minute", 0))
    schedule: dict[str, Any] = {
        "type": schedule_type,
        "hour": max(0, min(23, hour)),
        "minute": max(0, min(59, minute)),
    }
    if schedule_type == "weekly":
        schedule["day"] = (arguments.get("day") or "monday").strip().lower()
    elif schedule_type == "monthly":
        schedule["day_of_month"] = int(arguments.get("day_of_month") or 1)
    elif schedule_type == "interval":
        raw = arguments.get("interval_hours")
        hours = float(raw) if raw is not None else 24.0
        # min 1 minute to avoid zero/negative; aligns with reminder tick granularity
        schedule["hours"] = max(1.0 / 60.0, hours)
    return json.dumps(schedule)


def _reminder_to_dict(r: Reminder) -> dict[str, Any]:
    return {
        "kind": r.kind,
        "title": r.title,
        "schedule": r.schedule,
        "timezone": r.timezone,
        "enabled": r.enabled,
        "next_run_at": r.next_run_at.isoformat() if r.next_run_at else "",
        "last_run_at": r.last_run_at.isoformat() if r.last_run_at else "",
        "fail_count": r.fail_count,
        "created_at": r.created_at.isoformat() if r.created_at else "",
    }


async def handle_reminder_create(arguments: dict[str, Any], user_id: int) -> str:
    kind = (arguments.get("kind") or "").strip()
    title = (arguments.get("title") or "").strip()
    if not kind or not title:
        return json.dumps({"error": "kind and title are required"}, ensure_ascii=False)

    schedule_json = _build_schedule_json(arguments)
    raw_payload = arguments.get("payload") or {}
    payload_json = (
        json.dumps(raw_payload, ensure_ascii=False)
        if isinstance(raw_payload, dict) else str(raw_payload)
    )
    tz_name = "Asia/Jakarta"

    dedupe_raw = f"{user_id}:{kind}:{schedule_json}:{payload_json}"
    dedupe_key = hashlib.sha256(dedupe_raw.encode()).hexdigest()[:64]

    next_run = compute_next_run(schedule_json, tz_name)
    result = await create_reminder(
        user_id=user_id,
        kind=kind,
        title=title,
        payload=payload_json,
        schedule=schedule_json,
        timezone_name=tz_name,
        next_run_at=next_run,
        dedupe_key=dedupe_key,
    )
    if isinstance(result, str):
        return json.dumps({"error": result}, ensure_ascii=False)
    return json.dumps(
        {"tool": "reminder_create", "data": _reminder_to_dict(result)},
        ensure_ascii=False,
    )


async def handle_reminder_list(arguments: dict[str, Any], user_id: int) -> str:
    reminders = await get_user_reminders(user_id)
    data = [_reminder_to_dict(r) for r in reminders]
    return json.dumps({"tool": "reminder_list", "data": data}, ensure_ascii=False)


async def handle_reminder_pause(arguments: dict[str, Any], user_id: int) -> str:
    rid = int(arguments.get("reminder_id", 0))
    result = await toggle_reminder(user_id, rid, enabled=False)
    if result is None:
        return json.dumps({"error": "Pengingat tidak ditemukan."}, ensure_ascii=False)
    return json.dumps(
        {"tool": "reminder_pause", "data": result}, ensure_ascii=False,
    )


async def handle_reminder_resume(arguments: dict[str, Any], user_id: int) -> str:
    rid = int(arguments.get("reminder_id", 0))
    result = await toggle_reminder(user_id, rid, enabled=True)
    if result is None:
        return json.dumps({"error": "Pengingat tidak ditemukan."}, ensure_ascii=False)
    return json.dumps(
        {"tool": "reminder_resume", "data": result}, ensure_ascii=False,
    )


async def handle_reminder_delete(arguments: dict[str, Any], user_id: int) -> str:
    rid = int(arguments.get("reminder_id", 0))
    ok = await delete_reminder(user_id, rid)
    if not ok:
        return json.dumps({"error": "Pengingat tidak ditemukan."}, ensure_ascii=False)
    return json.dumps(
        {"tool": "reminder_delete", "data": {"deleted": True}},
        ensure_ascii=False,
    )


async def handle_reminder_suggest(arguments: dict[str, Any], user_id: int) -> str:
    suggestions = await analyze_user_habits(user_id)
    return json.dumps(
        {"tool": "reminder_suggest_from_habits", "data": suggestions},
        ensure_ascii=False,
    )


HANDLERS: dict[str, Any] = {
    "reminder_create": handle_reminder_create,
    "reminder_list": handle_reminder_list,
    "reminder_pause": handle_reminder_pause,
    "reminder_resume": handle_reminder_resume,
    "reminder_delete": handle_reminder_delete,
    "reminder_suggest_from_habits": handle_reminder_suggest,
}
