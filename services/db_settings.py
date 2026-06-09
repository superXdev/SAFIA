"""Settings CRUD — key-value runtime configuration store."""
from datetime import datetime, timezone

from sqlalchemy import select

from services.db_session import AsyncSessionMaker
from services.models import Setting


async def get_setting(key: str, default: str = "") -> str:
    """Return setting value or default if not found."""
    async with AsyncSessionMaker() as session:
        result = await session.execute(
            select(Setting).where(Setting.key == key)
        )
        row = result.scalar_one_or_none()
    return row.value if row else default


async def set_setting(key: str, value: str) -> None:
    """Insert or update a setting value."""
    async with AsyncSessionMaker() as session:
        result = await session.execute(
            select(Setting).where(Setting.key == key)
        )
        row = result.scalar_one_or_none()
        if row:
            row.value = value
            row.updated_at = datetime.now(timezone.utc)
        else:
            session.add(Setting(key=key, value=value))
        await session.commit()


async def get_all_settings() -> list[dict]:
    """Return all settings as dicts."""
    async with AsyncSessionMaker() as session:
        result = await session.execute(
            select(Setting).order_by(Setting.key.asc())
        )
        rows = result.scalars().all()
    return [
        {
            "id": r.id,
            "key": r.key,
            "value": r.value,
            "updated_at": r.updated_at.isoformat() if r.updated_at else "",
        }
        for r in rows
    ]


async def delete_setting(key: str) -> bool:
    """Delete a setting by key. Returns True if deleted."""
    from sqlalchemy import delete

    async with AsyncSessionMaker() as session:
        result = await session.execute(
            delete(Setting).where(Setting.key == key)
        )
        await session.commit()
        return (result.rowcount or 0) > 0


# ── Access control helpers ──────────────────────────────────────────────────

DEFAULT_ACCESS_MODE = "all"


async def get_access_mode() -> str:
    """Return current access mode: 'all' or 'allowlist'."""
    return await get_setting("access_mode", DEFAULT_ACCESS_MODE)


async def set_access_mode(mode: str) -> None:
    """Set access mode."""
    if mode not in ("all", "allowlist"):
        raise ValueError("access_mode must be 'all' or 'allowlist'")
    await set_setting("access_mode", mode)


async def is_user_allowed(telegram_id: int) -> bool:
    """Check if a user is allowed to use the bot."""
    mode = await get_access_mode()
    if mode == "all":
        return True

    import json

    users_json = await get_setting("allowed_users", "[]")
    try:
        allowed = json.loads(users_json)
    except (json.JSONDecodeError, TypeError):
        allowed = []
    return telegram_id in allowed


async def get_allowed_users() -> list[int]:
    """Return list of allowed telegram IDs."""
    import json

    users_json = await get_setting("allowed_users", "[]")
    try:
        return json.loads(users_json)
    except (json.JSONDecodeError, TypeError):
        return []


async def add_allowed_user(telegram_id: int) -> None:
    """Add a telegram ID to the allowlist."""
    allowed = await get_allowed_users()
    if telegram_id not in allowed:
        allowed.append(telegram_id)
        import json

        await set_setting("allowed_users", json.dumps(allowed))


async def remove_allowed_user(telegram_id: int) -> None:
    """Remove a telegram ID from the allowlist."""
    allowed = await get_allowed_users()
    if telegram_id in allowed:
        allowed.remove(telegram_id)
        import json

        await set_setting("allowed_users", json.dumps(allowed))
