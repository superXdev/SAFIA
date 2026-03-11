"""Redis-backed chat history storage."""
import json

from redis.asyncio import Redis

from config import (
    CHAT_KEY_PREFIX,
    HISTORY_TTL_SECONDS,
    MAX_CHAT_MESSAGES,
    REDIS_URL,
    SYSTEM_PROMPT,
)

_redis: Redis | None = None


def _chat_key(chat_id: int) -> str:
    return f"{CHAT_KEY_PREFIX}{chat_id}"


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
