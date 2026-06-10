"""In-memory cache for gold/silver/currency prices (replaces Redis)."""
import logging
from typing import Any

from config import PRICE_CACHE_TTL_SECONDS
from services.memory_store import get, set_val

PRICE_CACHE_TTL = PRICE_CACHE_TTL_SECONDS


def get_cached(key: str) -> Any | None:
    try:
        return get(key)
    except Exception:
        logging.exception("Price cache get failed")
        return None


def set_cached(key: str, value: Any, ttl_seconds: int = PRICE_CACHE_TTL) -> None:
    try:
        set_val(key, value, ttl_seconds)
    except Exception:
        logging.exception("Price cache set failed")
