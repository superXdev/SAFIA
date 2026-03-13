"""Tool registry — collects schemas and dispatches handlers."""
import logging
from typing import Any

from services.tools.debts import HANDLERS as DEBT_HANDLERS, SCHEMAS as DEBT_SCHEMAS
from services.tools.records import HANDLERS as RECORD_HANDLERS, SCHEMAS as RECORD_SCHEMAS

TOOLS = RECORD_SCHEMAS + DEBT_SCHEMAS

_HANDLERS: dict[str, Any] = {**RECORD_HANDLERS, **DEBT_HANDLERS}


async def run_tool(name: str, arguments: dict[str, Any], user_id: int) -> str:
    handler = _HANDLERS.get(name)
    if not handler:
        return "Unknown tool."
    try:
        return await handler(arguments, user_id)
    except Exception:
        logging.exception("Tool execution failed")
        return "Error saat menjalankan tool."
