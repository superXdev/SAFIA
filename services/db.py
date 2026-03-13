"""Async SQLAlchemy setup and User model."""
from __future__ import annotations

import os
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Float, Integer, String, func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from config import DATABASE_URL


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    first_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    username: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


class Record(Base):
    __tablename__ = "records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, index=True)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    kind: Mapped[str] = mapped_column(String(16))  # "income" or "expense"
    amount: Mapped[float] = mapped_column(Float)
    description: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    category: Mapped[str] = mapped_column(String(100), default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


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
    """Get a new async DB session."""
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
    chat_id: int,
    kind: str,
    amount: float,
    description: str = "",
    category: str = "",
    user_id: int | None = None,
) -> None:
    async with AsyncSessionMaker() as session:
        record = Record(
            chat_id=chat_id,
            user_id=user_id,
            kind=kind,
            amount=amount,
            description=description or "",
            category=category or "",
        )
        session.add(record)
        await session.commit()


async def save_expense_record(
    chat_id: int,
    amount: float,
    description: str = "",
    category: str = "",
    user_id: int | None = None,
) -> None:
    await _save_record(chat_id, "expense", amount, description, category, user_id)


async def save_income_record(
    chat_id: int,
    amount: float,
    description: str = "",
    category: str = "",
    user_id: int | None = None,
) -> None:
    await _save_record(chat_id, "income", amount, description, category, user_id)


async def get_records_for_chat(chat_id: int) -> list[dict]:
    """Return all expense/income records for a chat as simple dicts."""
    async with AsyncSessionMaker() as session:
        result = await session.execute(
            select(Record)
            .where(Record.chat_id == chat_id)
            .order_by(Record.created_at.asc())
        )
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

