"""Chat history storage and rate limiting (in-memory + SQLite, replaces Redis)."""
from datetime import datetime, time, timedelta, timezone

from config import (
    DAILY_MESSAGE_LIMIT,
    HISTORY_TTL_SECONDS,
    MAX_CHAT_MESSAGES,
    SYSTEM_PROMPT,
)
from services.memory_store import (
    _chat_key,
    _rate_key,
    adelete,
    aget,
    aincr,
    aset,
    mark_user_active,
    shutdown as _shutdown,
    startup as _startup,
)


async def startup() -> None:
    await _startup()


async def shutdown() -> None:
    await _shutdown()


async def get_history(chat_id: int) -> list[dict]:
    raw = await aget(_chat_key(chat_id))
    if raw is not None:
        return raw
    return [{"role": "system", "content": SYSTEM_PROMPT}]


async def save_history(chat_id: int, history: list[dict]) -> None:
    if len(history) > 1 + MAX_CHAT_MESSAGES:
        history = [history[0]] + history[-MAX_CHAT_MESSAGES:]
    await aset(
        _chat_key(chat_id),
        history,
        ttl_seconds=HISTORY_TTL_SECONDS,
    )


async def clear_history(chat_id: int) -> None:
    await adelete(_chat_key(chat_id))


async def check_and_increment_rate_limit(user_id: int) -> tuple[bool, int]:
    now = datetime.now(timezone.utc)
    day = now.date().isoformat()
    key = _rate_key(user_id, day)

    tomorrow_date = now.date() + timedelta(days=1)
    midnight_tomorrow = datetime.combine(tomorrow_date, time.min, tzinfo=timezone.utc)
    seconds_until_reset = int((midnight_tomorrow - now).total_seconds())
    if seconds_until_reset <= 0:
        seconds_until_reset = 1

    new_count = await aincr(key, 1, ttl_seconds=seconds_until_reset)

    remaining = max(DAILY_MESSAGE_LIMIT - new_count, 0)
    allowed = new_count <= DAILY_MESSAGE_LIMIT
    return allowed, remaining


async def mark_user_active_today(user_id: int) -> bool:
    now = datetime.now(timezone.utc)
    date_str = now.date().isoformat()
    return mark_user_active(user_id, date_str)
