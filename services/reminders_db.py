"""Reminder persistence — CRUD, due query, caps."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import delete as sql_delete, func, select

from config import REMINDER_MAX_PER_USER
from services.database import AsyncSessionMaker
from services.models import Reminder
from services.schedule import compute_next_run


async def create_reminder(
    user_id: int,
    kind: str,
    title: str,
    payload: str,
    schedule: str,
    timezone_name: str,
    next_run_at: datetime,
    dedupe_key: str | None = None,
) -> Reminder | str:
    """Create a reminder. Returns the Reminder or an error string if cap exceeded / duplicate."""
    async with AsyncSessionMaker() as session:
        count_result = await session.execute(
            select(func.count(Reminder.id)).where(
                Reminder.user_id == user_id,
                Reminder.enabled == True,  # noqa: E712
            )
        )
        count = int(count_result.scalar_one() or 0)
        if count >= REMINDER_MAX_PER_USER:
            return f"Sudah mencapai batas maksimal {REMINDER_MAX_PER_USER} pengingat aktif."

        if dedupe_key:
            existing = await session.execute(
                select(Reminder).where(Reminder.dedupe_key == dedupe_key)
            )
            if existing.scalar_one_or_none():
                return "Pengingat serupa sudah ada."

        reminder = Reminder(
            user_id=user_id,
            kind=kind,
            title=title,
            payload=payload,
            timezone=timezone_name,
            schedule=schedule,
            next_run_at=next_run_at,
            enabled=True,
            fail_count=0,
            dedupe_key=dedupe_key,
        )
        session.add(reminder)
        await session.commit()
        await session.refresh(reminder)
        return reminder


async def get_user_reminders(user_id: int) -> list[Reminder]:
    """Return all reminders for a user (active and inactive)."""
    async with AsyncSessionMaker() as session:
        result = await session.execute(
            select(Reminder)
            .where(Reminder.user_id == user_id)
            .order_by(Reminder.created_at.desc())
        )
        return list(result.scalars().all())


async def get_reminder_by_id(user_id: int, reminder_id: int) -> Reminder | None:
    """Return a single reminder belonging to user_id, or None."""
    async with AsyncSessionMaker() as session:
        result = await session.execute(
            select(Reminder).where(
                Reminder.id == reminder_id,
                Reminder.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()


async def get_due_reminders() -> list[Reminder]:
    """Get all enabled reminders where next_run_at <= now."""
    now = datetime.now(timezone.utc)
    async with AsyncSessionMaker() as session:
        result = await session.execute(
            select(Reminder).where(
                Reminder.enabled == True,  # noqa: E712
                Reminder.next_run_at <= now,
            ).order_by(Reminder.next_run_at.asc())
        )
        return list(result.scalars().all())


async def mark_reminder_fired(reminder_id: int, next_run_at: datetime) -> None:
    """Mark a reminder as just fired: update last_run_at, reset fail_count, set next_run_at."""
    async with AsyncSessionMaker() as session:
        result = await session.execute(
            select(Reminder).where(Reminder.id == reminder_id)
        )
        reminder = result.scalar_one_or_none()
        if not reminder:
            return
        reminder.last_run_at = datetime.now(timezone.utc)
        reminder.next_run_at = next_run_at
        reminder.fail_count = 0
        await session.commit()


async def increment_reminder_fail_count(reminder_id: int) -> None:
    """Increment fail_count; disable after 5 consecutive failures; add 5-min backoff."""
    async with AsyncSessionMaker() as session:
        result = await session.execute(
            select(Reminder).where(Reminder.id == reminder_id)
        )
        reminder = result.scalar_one_or_none()
        if not reminder:
            return
        reminder.fail_count += 1
        if reminder.fail_count >= 5:
            reminder.enabled = False
        else:
            reminder.next_run_at = datetime.now(timezone.utc) + timedelta(minutes=5)
        await session.commit()


async def toggle_reminder(
    user_id: int, reminder_id: int, enabled: bool
) -> dict | None:
    """Toggle reminder enabled state. Returns info dict or None if not found."""
    async with AsyncSessionMaker() as session:
        result = await session.execute(
            select(Reminder).where(
                Reminder.id == reminder_id,
                Reminder.user_id == user_id,
            )
        )
        reminder = result.scalar_one_or_none()
        if not reminder:
            return None
        reminder.enabled = enabled
        if enabled:
            reminder.fail_count = 0
            reminder.next_run_at = compute_next_run(reminder.schedule, reminder.timezone)
        await session.commit()
        return {
            "enabled": reminder.enabled,
            "next_run_at": reminder.next_run_at.isoformat() if reminder.next_run_at else "",
        }


async def delete_reminder(user_id: int, reminder_id: int) -> bool:
    """Delete a reminder. Returns True if a row was removed."""
    async with AsyncSessionMaker() as session:
        result = await session.execute(
            sql_delete(Reminder).where(
                Reminder.id == reminder_id,
                Reminder.user_id == user_id,
            )
        )
        await session.commit()
        return (result.rowcount or 0) > 0
