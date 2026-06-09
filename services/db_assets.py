"""Asset CRUD — investment portfolio management."""
from datetime import datetime, timezone

from sqlalchemy import delete, func, select

from services.db_session import AsyncSessionMaker
from services.models import Asset

__all__ = [
    "save_asset", "_asset_to_dict", "get_assets", "get_asset_rows",
    "get_asset_by_id", "get_asset", "get_asset_by_type_name",
    "update_asset", "upsert_asset", "delete_assets", "delete_all_assets",
]


async def save_asset(
    user_id: int,
    asset_type: str,
    name: str,
    quantity: float,
    unit_value: float,
    notes: str = "",
) -> dict:
    """Insert new asset. Returns the created asset as dict."""
    async with AsyncSessionMaker() as session:
        asset = Asset(
            user_id=user_id,
            asset_type=asset_type.strip().lower(),
            name=name.strip(),
            quantity=quantity,
            unit_value=unit_value,
            notes=notes.strip() or "",
        )
        session.add(asset)
        await session.commit()
        await session.refresh(asset)
        return _asset_to_dict(asset)


def _asset_to_dict(a: Asset) -> dict:
    return {
        "asset_type": a.asset_type,
        "name": a.name,
        "quantity": a.quantity,
        "unit_value": a.unit_value,
        "value": a.quantity * a.unit_value,
        "notes": a.notes or "",
        "created_at": a.created_at.isoformat() if a.created_at else "",
        "updated_at": a.updated_at.isoformat() if a.updated_at else "",
    }


async def get_assets(
    user_id: int,
    *,
    asset_type: str | None = None,
) -> list[dict]:
    """Return assets for a user, optionally filtered by asset_type."""
    async with AsyncSessionMaker() as session:
        stmt = select(Asset).where(Asset.user_id == user_id)
        if asset_type:
            stmt = stmt.where(
                func.lower(Asset.asset_type) == asset_type.strip().lower()
            )
        stmt = stmt.order_by(Asset.asset_type.asc(), Asset.name.asc())
        result = await session.execute(stmt)
        rows = result.scalars().all()
    return [_asset_to_dict(r) for r in rows]


async def get_asset_rows(
    user_id: int,
    asset_type: str,
    name: str,
) -> list[Asset]:
    """Return raw Asset ORM objects matching (user, type, name), ordered by id (FIFO)."""
    async with AsyncSessionMaker() as session:
        stmt = (
            select(Asset)
            .where(
                Asset.user_id == user_id,
                func.lower(Asset.asset_type) == asset_type.strip().lower(),
                func.lower(Asset.name) == name.strip().lower(),
            )
            .order_by(Asset.id.asc())
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())


async def get_asset_by_id(user_id: int, asset_id: int) -> Asset | None:
    """Return single asset by id if it belongs to user."""
    async with AsyncSessionMaker() as session:
        result = await session.execute(
            select(Asset).where(
                Asset.user_id == user_id,
                Asset.id == asset_id,
            )
        )
        return result.scalar_one_or_none()


async def get_asset(user_id: int, asset_id: int) -> dict | None:
    """Return single asset as dict by id, or None."""
    a = await get_asset_by_id(user_id, asset_id)
    return _asset_to_dict(a) if a else None


async def get_asset_by_type_name(
    user_id: int,
    asset_type: str,
    name: str,
) -> Asset | None:
    """Return single asset by (asset_type, name) if it belongs to user."""
    async with AsyncSessionMaker() as session:
        result = await session.execute(
            select(Asset).where(
                Asset.user_id == user_id,
                func.lower(Asset.asset_type) == asset_type.strip().lower(),
                func.lower(Asset.name) == name.strip().lower(),
            )
        )
        return result.scalar_one_or_none()


async def update_asset(
    user_id: int,
    asset_id: int,
    *,
    quantity: float | None = None,
    unit_value: float | None = None,
    notes: str | None = None,
) -> bool:
    """Update asset by id. Returns True if updated."""
    async with AsyncSessionMaker() as session:
        result = await session.execute(
            select(Asset).where(
                Asset.user_id == user_id,
                Asset.id == asset_id,
            )
        )
        asset = result.scalar_one_or_none()
        if not asset:
            return False
        if quantity is not None:
            asset.quantity = quantity
        if unit_value is not None:
            asset.unit_value = unit_value
        if notes is not None:
            asset.notes = notes.strip() or ""
        asset.updated_at = datetime.now(timezone.utc)
        await session.commit()
        return True


async def upsert_asset(
    user_id: int,
    asset_type: str,
    name: str,
    quantity: float,
    unit_value: float,
    notes: str = "",
) -> dict:
    """Insert or update asset by (asset_type, name). Returns asset as dict."""
    existing = await get_asset_by_type_name(user_id, asset_type, name)
    if existing:
        await update_asset(
            user_id,
            existing.id,
            quantity=quantity,
            unit_value=unit_value,
            notes=notes if notes is not None else existing.notes,
        )
        out = await get_asset(user_id, existing.id)
        return out or _asset_to_dict(existing)
    return await save_asset(
        user_id, asset_type, name, quantity, unit_value, notes
    )


async def delete_assets(user_id: int, asset_ids: list[int]) -> int:
    """Delete assets by ids. Returns count deleted."""
    async with AsyncSessionMaker() as session:
        stmt = delete(Asset).where(
            Asset.user_id == user_id,
            Asset.id.in_(asset_ids),
        )
        result = await session.execute(stmt)
        await session.commit()
        return result.rowcount


async def delete_all_assets(user_id: int) -> int:
    """Delete all assets (portfolio) for a user. Returns count deleted."""
    async with AsyncSessionMaker() as session:
        stmt = delete(Asset).where(Asset.user_id == user_id)
        result = await session.execute(stmt)
        await session.commit()
        return result.rowcount
