"""Debt CRUD — money lent/borrowed tracking."""
from sqlalchemy import delete, func, select, update

from services.db_session import AsyncSessionMaker
from services.models import Debt

__all__ = [
    "save_debt", "get_debts", "settle_debt",
    "delete_debts", "delete_all_debts",
]


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


async def delete_all_debts(user_id: int) -> int:
    """Delete all debts for a user. Returns count deleted."""
    async with AsyncSessionMaker() as session:
        stmt = delete(Debt).where(Debt.user_id == user_id)
        result = await session.execute(stmt)
        await session.commit()
        return result.rowcount
