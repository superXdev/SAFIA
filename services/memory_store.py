"""Hybrid in-memory + SQLite key-value store — replaces Redis.

Sync methods (get, set, delete, incr): in-memory only, thread-safe.
Async methods (aget, aset, adelete, aincr): in-memory + SQLite write-through.
Active-user tracking: in-memory sets, keyed by date.
"""
from __future__ import annotations

import json
import logging
import threading
import time
from typing import Any

from services.db_session import AsyncSessionMaker
from services.models import KvEntry

_MEMORY: dict[str, tuple[Any, float | None]] = {}  # key -> (value, expires_at)
_MEMORY_LOCK = threading.Lock()
_DB_LOADED = False
_ACTIVE_USERS: dict[str, set[str]] = {}  # date_str -> {user_id, ...}


# ---------------------------------------------------------------------------
# Sync helpers (in-memory only, thread-safe)
# ---------------------------------------------------------------------------
def _now() -> float:
    return time.time()


def _expired(expires_at: float | None) -> bool:
    return expires_at is not None and _now() > expires_at


def get(key: str) -> Any | None:
    with _MEMORY_LOCK:
        entry = _MEMORY.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if _expired(expires_at):
            del _MEMORY[key]
            return None
        return value


def set_val(key: str, value: Any, ttl_seconds: int | None = None) -> None:
    with _MEMORY_LOCK:
        expires_at = (_now() + ttl_seconds) if ttl_seconds else None
        _MEMORY[key] = (value, expires_at)


def delete(key: str) -> None:
    with _MEMORY_LOCK:
        _MEMORY.pop(key, None)


def incr(key: str, amount: int = 1, ttl_seconds: int | None = None) -> int:
    with _MEMORY_LOCK:
        entry = _MEMORY.get(key)
        if entry is None or _expired(entry[1]):
            new_val = amount
        else:
            new_val = int(entry[0]) + amount
        expires_at = (_now() + ttl_seconds) if ttl_seconds else None
        _MEMORY[key] = (new_val, expires_at)
        return new_val


# ---------------------------------------------------------------------------
# Async helpers (in-memory + SQLite write-through)
# ---------------------------------------------------------------------------
async def _ensure_loaded() -> None:
    global _DB_LOADED
    if _DB_LOADED:
        return
    async with AsyncSessionMaker() as session:
        from sqlalchemy import select

        result = await session.execute(select(KvEntry))
        now = _now()
        for row in result.scalars():
            if row.expires_at is not None and row.expires_at <= now:
                continue
            try:
                val = json.loads(row.value)
            except (json.JSONDecodeError, TypeError):
                val = row.value
            with _MEMORY_LOCK:
                _MEMORY[row.key] = (val, row.expires_at)
    _DB_LOADED = True


async def _persist(key: str, value: Any, expires_at: float | None) -> None:
    raw = json.dumps(value, ensure_ascii=False)
    async with AsyncSessionMaker() as session:
        row = await session.get(KvEntry, key)
        if row:
            row.value = raw
            row.expires_at = expires_at
        else:
            session.add(KvEntry(key=key, value=raw, expires_at=expires_at))
        await session.commit()


async def aget(key: str) -> Any | None:
    result = get(key)
    if result is not None:
        return result
    await _ensure_loaded()
    async with AsyncSessionMaker() as session:
        row = await session.get(KvEntry, key)
        if row is None:
            return None
        if row.expires_at is not None and row.expires_at <= _now():
            return None
        try:
            val = json.loads(row.value)
        except (json.JSONDecodeError, TypeError):
            val = row.value
        with _MEMORY_LOCK:
            _MEMORY[key] = (val, row.expires_at)
        return val


async def aset(key: str, value: Any, ttl_seconds: int | None = None) -> None:
    set_val(key, value, ttl_seconds)
    expires_at = (_now() + ttl_seconds) if ttl_seconds else None
    await _persist(key, value, expires_at)


async def adelete(key: str) -> None:
    delete(key)
    async with AsyncSessionMaker() as session:
        row = await session.get(KvEntry, key)
        if row:
            await session.delete(row)
            await session.commit()


async def aincr(key: str, amount: int = 1, ttl_seconds: int | None = None) -> int:
    new_val = incr(key, amount, ttl_seconds)
    expires_at = (_now() + ttl_seconds) if ttl_seconds else None
    try:
        await _persist(key, new_val, expires_at)
    except Exception:
        logging.exception("kv_store.aincr persist failed for key=%s", key)
    return new_val


# ---------------------------------------------------------------------------
# Active users tracking (in-memory sets)
# ---------------------------------------------------------------------------
def _active_users_key(date_str: str) -> str:
    return f"active:{date_str}"


def mark_user_active(user_id: int, date_str: str) -> bool:
    """Return True if this is the user's first message on date_str."""
    key = _active_users_key(date_str)
    with _MEMORY_LOCK:
        if key not in _ACTIVE_USERS:
            _ACTIVE_USERS[key] = set()
        s = _ACTIVE_USERS[key]
        uid = str(user_id)
        if uid in s:
            return False
        s.add(uid)
        return True


# ---------------------------------------------------------------------------
# Startup / shutdown
# ---------------------------------------------------------------------------
async def startup() -> None:
    await _ensure_loaded()


async def shutdown() -> None:
    pass


# ---------------------------------------------------------------------------
# Backward-compat exports (used by tests)
# ---------------------------------------------------------------------------
CHAT_KEY_PREFIX = "safia:chat:"
RATE_LIMIT_KEY_PREFIX = "safia:rate:"


def _chat_key(chat_id: int) -> str:
    return f"{CHAT_KEY_PREFIX}{chat_id}"


def _rate_key(user_id: int, day: str) -> str:
    return f"{RATE_LIMIT_KEY_PREFIX}{user_id}:{day}"
