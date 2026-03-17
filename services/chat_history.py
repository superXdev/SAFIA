"""Redis-backed chat history storage and simple rate limiting."""
import json
from datetime import datetime, time, timedelta, timezone

from redis.asyncio import Redis

from config import (
    CHAT_KEY_PREFIX,
    DAILY_MESSAGE_LIMIT,
    HISTORY_TTL_SECONDS,
    MAX_CHAT_MESSAGES,
    RATE_LIMIT_KEY_PREFIX,
    REDIS_URL,
    SYSTEM_PROMPT,
)

_redis: Redis | None = None


def _chat_key(chat_id: int) -> str:
    return f"{CHAT_KEY_PREFIX}{chat_id}"


def _rate_key(user_id: int, day: str) -> str:
    return f"{RATE_LIMIT_KEY_PREFIX}{user_id}:{day}"


async def get_redis() -> Redis:
    global _redis
    if _redis is None:
        _redis = Redis.from_url(REDIS_URL, decode_responses=True)
    return _redis


async def get_history(chat_id: int) -> list[dict]:
    r = await get_redis()
    raw = await r.get(_chat_key(chat_id))
    if raw:
        return json.loads(raw)
    return [{"role": "system", "content": SYSTEM_PROMPT}]


async def save_history(chat_id: int, history: list[dict]) -> None:
    if len(history) > 1 + MAX_CHAT_MESSAGES:
        history = [history[0]] + history[-MAX_CHAT_MESSAGES:]
    r = await get_redis()
    await r.set(_chat_key(chat_id), json.dumps(history), ex=HISTORY_TTL_SECONDS)


async def clear_history(chat_id: int) -> None:
    r = await get_redis()
    await r.delete(_chat_key(chat_id))


async def close_redis() -> None:
    global _redis
    if _redis:
        await _redis.aclose()
        _redis = None


async def check_and_increment_rate_limit(user_id: int) -> tuple[bool, int]:
    """Return (allowed, remaining) for today's message quota and increment if allowed."""
    now = datetime.now(timezone.utc)
    day = now.date().isoformat()
    key = _rate_key(user_id, day)

    r = await get_redis()
    pipe = r.pipeline()
    pipe.incr(key)
    # Expire at next UTC midnight (~per-day window)
    tomorrow_date = now.date() + timedelta(days=1)
    midnight_tomorrow = datetime.combine(tomorrow_date, time.min, tzinfo=timezone.utc)
    seconds_until_reset = int((midnight_tomorrow - now).total_seconds())
    if seconds_until_reset <= 0:
        seconds_until_reset = 1
    pipe.expire(key, seconds_until_reset)
    new_count, _ = await pipe.execute()

    remaining = max(DAILY_MESSAGE_LIMIT - int(new_count), 0)
    allowed = new_count <= DAILY_MESSAGE_LIMIT
    return allowed, remaining


async def mark_user_active_today(user_id: int) -> bool:
    """Add user to today's active set. Returns True if this is their first message today."""
    now = datetime.now(timezone.utc)
    day = now.date().isoformat()
    key = f"safia:active_users:{day}"

    r = await get_redis()
    added = await r.sadd(key, str(user_id))

    if added:
        tomorrow_date = now.date() + timedelta(days=1)
        midnight_tomorrow = datetime.combine(tomorrow_date, time.min, tzinfo=timezone.utc)
        ttl = int((midnight_tomorrow - now).total_seconds()) or 1
        await r.expire(key, ttl)

    return bool(added)
