"""Sync Redis cache for gold/silver price (used from sync fetch functions)."""
import json
import logging
from typing import Any

import redis

from config import PRICE_CACHE_TTL_SECONDS, REDIS_URL

_redis: redis.Redis | None = None


def _get_redis() -> redis.Redis:
    global _redis
    if _redis is None:
        _redis = redis.from_url(REDIS_URL, decode_responses=True)
    return _redis


def get_cached(key: str) -> Any | None:
    """Return cached JSON value or None if miss/error."""
    try:
        r = _get_redis()
        raw = r.get(key)
        if raw is None:
            return None
        return json.loads(raw)
    except Exception:
        logging.exception("Price cache get failed")
        return None


def set_cached(key: str, value: Any, ttl_seconds: int = PRICE_CACHE_TTL_SECONDS) -> None:
    """Store value as JSON with TTL."""
    try:
        r = _get_redis()
        r.set(key, json.dumps(value, ensure_ascii=False), ex=ttl_seconds)
    except Exception:
        logging.exception("Price cache set failed")
