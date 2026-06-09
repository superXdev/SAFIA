"""Record CRUD — expense and income transactions."""
from __future__ import annotations

from datetime import date

from sqlalchemy import delete, func, select

from services.db_session import AsyncSessionMaker
from services.models import Record

__all__ = [
    "_save_record", "save_expense_record", "save_income_record",
    "get_records", "delete_records",
]


async def _save_record(
    user_id: int,
    kind: str,
    amount: float,
    description: str = "",
    category: str = "",
) -> None:
    async with AsyncSessionMaker() as session:
        record = Record(
            user_id=user_id,
            kind=kind,
            amount=amount,
            description=description or "",
            category=category or "",
        )
        session.add(record)
        await session.commit()


async def save_expense_record(
    user_id: int,
    amount: float,
    description: str = "",
    category: str = "",
) -> None:
    await _save_record(user_id, "expense", amount, description, category)


async def save_income_record(
    user_id: int,
    amount: float,
    description: str = "",
    category: str = "",
) -> None:
    await _save_record(user_id, "income", amount, description, category)


async def get_records(
    user_id: int,
    *,
    kind: str | None = None,
    category: str | None = None,
    min_amount: float | None = None,
    max_amount: float | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
) -> list[dict]:
    """Return expense/income records for a user as simple dicts, with optional filters."""
    from datetime import date

    async with AsyncSessionMaker() as session:
        stmt = select(Record).where(Record.user_id == user_id)

        if kind:
            stmt = stmt.where(Record.kind == kind)
        if category:
            stmt = stmt.where(
                func.lower(Record.category) == category.strip().lower()
            )
        if min_amount is not None:
            stmt = stmt.where(Record.amount >= min_amount)
        if max_amount is not None:
            stmt = stmt.where(Record.amount <= max_amount)
        if from_date is not None:
            stmt = stmt.where(func.date(Record.created_at) >= from_date)
        if to_date is not None:
            stmt = stmt.where(func.date(Record.created_at) <= to_date)

        stmt = stmt.order_by(Record.created_at.asc())
        result = await session.execute(stmt)
        rows = result.scalars().all()

    return [
        {
            "type": r.kind,
            "amount": r.amount,
            "description": r.description,
            "category": r.category,
            "at": r.created_at.isoformat() if r.created_at else "",
        }
        for r in rows
    ]


async def delete_records(
    user_id: int,
    *,
    record_ids: list[int] | None = None,
    kind: str | None = None,
    category: str | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
) -> int:
    """Delete records for a user matching the given filters. Returns count deleted."""
    from datetime import date

    async with AsyncSessionMaker() as session:
        stmt = delete(Record).where(Record.user_id == user_id)

        if record_ids:
            stmt = stmt.where(Record.id.in_(record_ids))
        if kind:
            stmt = stmt.where(Record.kind == kind)
        if category:
            stmt = stmt.where(
                func.lower(Record.category) == category.strip().lower()
            )
        if from_date is not None:
            stmt = stmt.where(func.date(Record.created_at) >= from_date)
        if to_date is not None:
            stmt = stmt.where(func.date(Record.created_at) <= to_date)

        result = await session.execute(stmt)
        await session.commit()
        return result.rowcount
