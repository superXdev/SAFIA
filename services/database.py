"""Async SQLAlchemy setup, user/meta/metrics helpers, and re-exports from split modules."""
from __future__ import annotations

import os
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import delete, func, select
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from config import DATABASE_URL
from services.db_session import AsyncSessionMaker, engine, get_session  # noqa: F401
from services.models import Base, DailyMetrics, KnowledgeDocument, Record, User


async def init_db() -> None:
    """Create all tables (run at startup). Also ensures the data directory exists for SQLite."""
    if DATABASE_URL.startswith("sqlite"):
        db_path = DATABASE_URL.replace("sqlite+aiosqlite:///", "")
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    async with engine.begin() as conn:
        if DATABASE_URL.startswith("sqlite"):
            await conn.run_sync(lambda c: c.exec_driver_sql("PRAGMA journal_mode=WAL"))
        try:
            await conn.run_sync(Base.metadata.create_all)
        except OperationalError:
            pass  # race: another worker already created tables


async def close_db() -> None:
    """Dispose DB engine (run at shutdown)."""
    await engine.dispose()


async def get_or_create_user(
    telegram_id: int,
    first_name: str | None,
    last_name: str | None,
    username: str | None,
) -> User:
    """Return existing user or create a new one."""
    async with AsyncSessionMaker() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()

        if user is None:
            user = User(
                telegram_id=telegram_id,
                first_name=first_name,
                last_name=last_name,
                username=username,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)

            await increment_daily_metrics(registrations_delta=1)

        return user


# ── Re-exports from split modules (backward compatible) ───────────────────

from services.db_records import (  # noqa: E402, F401
    _save_record,
    delete_records,
    get_records,
    save_expense_record,
    save_income_record,
)

from services.db_debts import (  # noqa: E402, F401
    delete_all_debts,
    delete_debts,
    get_debts,
    save_debt,
    settle_debt,
)

from services.db_assets import (  # noqa: E402, F401
    _asset_to_dict,
    delete_all_assets,
    delete_assets,
    get_asset,
    get_asset_by_id,
    get_asset_by_type_name,
    get_asset_rows,
    get_assets,
    save_asset,
    update_asset,
    upsert_asset,
)


# ── Daily metrics ──────────────────────────────────────────────────────────

async def increment_daily_metrics(
    *,
    registrations_delta: int = 0,
    messages_delta: int = 0,
    tokens_delta: int = 0,
    active_users_delta: int = 0,
) -> None:
    """Increment daily metrics counters for today."""
    if not any(
        (
            registrations_delta,
            messages_delta,
            tokens_delta,
            active_users_delta,
        )
    ):
        return

    today = date.today()
    async with AsyncSessionMaker() as session:
        result = await session.execute(
            select(DailyMetrics).where(DailyMetrics.date == today)
        )
        metrics = result.scalar_one_or_none()

        if metrics is None:
            metrics = DailyMetrics(
                date=today,
                registrations=0,
                total_messages=0,
                total_tokens=0,
                active_users=0,
            )
            session.add(metrics)

        metrics.registrations += registrations_delta
        metrics.total_messages += messages_delta
        metrics.total_tokens += tokens_delta
        metrics.active_users += active_users_delta

        await session.commit()


async def get_overall_metrics() -> dict:
    """Aggregate high-level metrics for the admin dashboard."""
    async with AsyncSessionMaker() as session:
        result = await session.execute(select(func.count(User.id)))
        total_users = int(result.scalar_one() or 0)

        today = date.today()
        yesterday = today - timedelta(days=1)

        result = await session.execute(
            select(
                func.coalesce(func.sum(DailyMetrics.active_users), 0),
                func.coalesce(func.sum(DailyMetrics.total_messages), 0),
                func.coalesce(func.sum(DailyMetrics.total_tokens), 0),
            ).where(DailyMetrics.date == today)
        )
        active_today, messages_today, tokens_today = result.one()

        result = await session.execute(
            select(func.coalesce(func.sum(DailyMetrics.active_users), 0)).where(
                DailyMetrics.date >= yesterday
            )
        )
        active_24h = int(result.scalar_one() or 0)

        avg_messages_per_user = 0.0
        if total_users > 0:
            avg_messages_per_user = float(messages_today) / float(total_users)

    return {
        "total_users": int(total_users),
        "active_24h": int(active_24h),
        "sessions_today": int(messages_today),
        "avg_messages_per_user": round(avg_messages_per_user, 2),
        "tokens_today": int(tokens_today),
    }


async def get_daily_metrics(last_days: int = 30) -> list[dict]:
    """Return list of daily metrics for the last N days (inclusive)."""
    if last_days <= 0:
        last_days = 1

    start_date = date.today() - timedelta(days=last_days - 1)

    async with AsyncSessionMaker() as session:
        result = await session.execute(
            select(DailyMetrics)
            .where(DailyMetrics.date >= start_date)
            .order_by(DailyMetrics.date.asc())
        )
        rows = result.scalars().all()

    out: list[dict] = []
    for r in rows:
        out.append(
            {
                "date": r.date.isoformat(),
                "registrations": int(r.registrations),
                "active_users": int(r.active_users),
                "total_messages": int(r.total_messages),
                "total_tokens": int(r.total_tokens),
            }
        )
    return out


async def get_all_users_with_stats() -> list[dict]:
    """Return all users with record counts and activity status."""
    seven_days_ago = date.today() - timedelta(days=7)

    recent_count = (
        select(
            Record.user_id,
            func.count(Record.id).label("recent"),
        )
        .where(func.date(Record.created_at) >= seven_days_ago)
        .group_by(Record.user_id)
        .subquery()
    )

    total_count = (
        select(
            Record.user_id,
            func.count(Record.id).label("total"),
        )
        .group_by(Record.user_id)
        .subquery()
    )

    stmt = (
        select(
            User,
            func.coalesce(total_count.c.total, 0).label("total_records"),
            func.coalesce(recent_count.c.recent, 0).label("recent_records"),
        )
        .outerjoin(total_count, User.telegram_id == total_count.c.user_id)
        .outerjoin(recent_count, User.telegram_id == recent_count.c.user_id)
        .order_by(User.created_at.desc())
    )

    async with AsyncSessionMaker() as session:
        result = await session.execute(stmt)
        rows = result.all()

    out: list[dict] = []
    for user, total_records, recent_records in rows:
        name_parts = [user.first_name or "", user.last_name or ""]
        name = " ".join(p for p in name_parts if p) or "Unknown"
        status = "active" if int(recent_records) > 0 else "inactive"
        out.append(
            {
                "id": user.id,
                "telegram_id": user.telegram_id,
                "name": name,
                "username": user.username,
                "status": status,
                "records": int(total_records),
                "joined": user.created_at.strftime("%Y-%m-%d") if user.created_at else "",
            }
        )
    return out


# ── Knowledge base metadata ────────────────────────────────────────────────

async def kb_create_document(
    document_id: str,
    filename: str,
    mime_type: str,
    title: str = "",
    *,
    chunk_count: int = 0,
    status: str = "ready",
    error_message: str | None = None,
) -> KnowledgeDocument:
    async with AsyncSessionMaker() as session:
        row = KnowledgeDocument(
            document_id=document_id,
            title=(title or filename)[:255],
            filename=filename[:512],
            mime_type=(mime_type or "")[:128],
            status=status,
            chunk_count=chunk_count,
            error_message=error_message[:512] if error_message else None,
        )
        session.add(row)
        await session.commit()
        await session.refresh(row)
        return row


async def kb_list_documents() -> list[dict]:
    async with AsyncSessionMaker() as session:
        result = await session.execute(
            select(KnowledgeDocument).order_by(KnowledgeDocument.created_at.desc())
        )
        rows = result.scalars().all()
    return [
        {
            "id": r.id,
            "document_id": r.document_id,
            "title": r.title,
            "filename": r.filename,
            "mime_type": r.mime_type,
            "status": r.status,
            "chunk_count": r.chunk_count,
            "error_message": r.error_message or "",
            "created_at": r.created_at.isoformat() if r.created_at else "",
        }
        for r in rows
    ]


async def kb_get_by_id(row_id: int) -> KnowledgeDocument | None:
    async with AsyncSessionMaker() as session:
        result = await session.execute(
            select(KnowledgeDocument).where(KnowledgeDocument.id == row_id)
        )
        return result.scalar_one_or_none()


async def kb_delete_row(row_id: int) -> bool:
    """Delete metadata row by primary key. Returns True if a row was removed."""
    async with AsyncSessionMaker() as session:
        result = await session.execute(
            delete(KnowledgeDocument).where(KnowledgeDocument.id == row_id)
        )
        await session.commit()
        return (result.rowcount or 0) > 0
