"""Tool handlers for user memory."""
import json
import logging
from typing import Any

from services.memory import delete_memory, list_memories, search_memories, store_memory

logger = logging.getLogger(__name__)


async def _remember_fact(arguments: dict[str, Any], user_id: int) -> str:
    fact = (arguments.get("fact") or "").strip()
    if not fact:
        return json.dumps({"error": "fact is required"})

    category = (arguments.get("category") or "general").strip().lower()
    valid = {"personal", "preference", "habit", "goal", "finance", "general", "other"}
    if category not in valid:
        category = "general"

    try:
        await store_memory(user_id, fact, category)
        logger.info("Stored memory for user %s: %s (%s)", user_id, fact[:80], category)
        return json.dumps({"ok": True, "category": category})
    except Exception:
        logger.exception("Failed to store memory for user %s", user_id)
        return json.dumps({"error": "Failed to store memory"})


async def _recall_memories(arguments: dict[str, Any], user_id: int) -> str:
    query = (arguments.get("query") or "").strip()
    if not query:
        results = await list_memories(user_id)
    else:
        results = await search_memories(user_id, query)

    if not results:
        return json.dumps({"memories": [], "hint": "No memories found for this user."})

    items = [
        {"fact": r["fact"], "category": r.get("category", "general")}
        for r in results
    ]
    return json.dumps({"memories": items})


async def _forget_fact(arguments: dict[str, Any], user_id: int) -> str:
    query = (arguments.get("query") or "").strip()
    if not query:
        return json.dumps({"error": "query is required"})

    results = await search_memories(user_id, query, limit=1)
    if not results or results[0]["score"] < 0.6:
        return json.dumps({"ok": False, "hint": "No matching memory found."})

    point_id = results[0]["id"]
    ok = await delete_memory(point_id)
    return json.dumps({"ok": ok})


HANDLERS: dict[str, Any] = {
    "remember_fact": _remember_fact,
    "recall_memories": _recall_memories,
    "forget_fact": _forget_fact,
}
