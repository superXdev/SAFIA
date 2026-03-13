"""Async SQLAlchemy setup and simple helpers."""
from __future__ import annotations

from datetime import date

from sqlalchemy import Boolean, DateTime, Float, Integer, String, delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from config import DATABASE_URL
from services.models import Base, Debt, Record, User


engine = create_async_engine(
    DATABASE_URL,
    echo=False,
)

AsyncSessionMaker = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_session() -> AsyncSession:
    """Yield an async DB session (use as async generator)."""
    async with AsyncSessionMaker() as session:
        yield session


async def init_db() -> None:
    """Create all tables (run at startup)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


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

        return user


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
            "id": r.id,
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


async def save_debt(
    user_id: int,
    direction: str,
    person: str,
    amount: float,
    description: str = "",
) -> None:
    async with AsyncSessionMaker() as session:
        debt = Debt(
            user_id=user_id,
            direction=direction,
            person=person,
            amount=amount,
            description=description or "",
        )
        session.add(debt)
        await session.commit()


async def get_debts(
    user_id: int,
    *,
    direction: str | None = None,
    person: str | None = None,
    is_settled: bool | None = None,
) -> list[dict]:
    async with AsyncSessionMaker() as session:
        stmt = select(Debt).where(Debt.user_id == user_id)

        if direction:
            stmt = stmt.where(Debt.direction == direction)
        if person:
            stmt = stmt.where(func.lower(Debt.person) == person.strip().lower())
        if is_settled is not None:
            stmt = stmt.where(Debt.is_settled == is_settled)

        stmt = stmt.order_by(Debt.created_at.asc())
        result = await session.execute(stmt)
        rows = result.scalars().all()

    return [
        {
            "id": d.id,
            "direction": d.direction,
            "person": d.person,
            "amount": d.amount,
            "description": d.description,
            "is_settled": d.is_settled,
            "at": d.created_at.isoformat() if d.created_at else "",
        }
        for d in rows
    ]


async def settle_debt(user_id: int, debt_ids: list[int]) -> int:
    async with AsyncSessionMaker() as session:
        stmt = (
            update(Debt)
            .where(Debt.user_id == user_id, Debt.id.in_(debt_ids))
            .values(is_settled=True)
        )
        result = await session.execute(stmt)
        await session.commit()
        return result.rowcount


async def delete_debts(user_id: int, debt_ids: list[int]) -> int:
    async with AsyncSessionMaker() as session:
        stmt = delete(Debt).where(Debt.user_id == user_id, Debt.id.in_(debt_ids))
        result = await session.execute(stmt)
        await session.commit()
        return result.rowcount

