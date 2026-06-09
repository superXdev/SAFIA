"""Tool registry — collects schemas from schemas/ and dispatches handlers."""
import json
import logging
from typing import Any

from services.tools.schemas import TOOLS

from services.tools.assets import HANDLERS as ASSET_HANDLERS
from services.tools.crypto_market import HANDLERS as CRYPTO_MARKET_HANDLERS
from services.tools.currency import HANDLERS as CURRENCY_HANDLERS
from services.tools.debts import HANDLERS as DEBT_HANDLERS
from services.tools.gold import HANDLERS as GOLD_HANDLERS
from services.tools.knowledge_search import HANDLERS as KNOWLEDGE_HANDLERS
from services.tools.memory import HANDLERS as MEMORY_HANDLERS
from services.tools.news_search import HANDLERS as NEWS_SEARCH_HANDLERS
from services.tools.prices import HANDLERS as PRICE_HANDLERS
from services.tools.records import HANDLERS as RECORD_HANDLERS
from services.tools.reminders import HANDLERS as REMINDER_HANDLERS
from services.tools.silver import HANDLERS as SILVER_HANDLERS

_HANDLERS: dict[str, Any] = {
    **RECORD_HANDLERS,
    **DEBT_HANDLERS,
    **ASSET_HANDLERS,
    **GOLD_HANDLERS,
    **SILVER_HANDLERS,
    **PRICE_HANDLERS,
    **CURRENCY_HANDLERS,
    **CRYPTO_MARKET_HANDLERS,
    **NEWS_SEARCH_HANDLERS,
    **KNOWLEDGE_HANDLERS,
    **REMINDER_HANDLERS,
    **MEMORY_HANDLERS,
}


async def run_tool(name: str, arguments: dict[str, Any], user_id: int) -> str:
    handler = _HANDLERS.get(name)
    if not handler:
        logging.warning("Unknown tool requested: %s", name)
        return json.dumps({"error": f"Unknown tool: {name}"})
    try:
        return await handler(arguments, user_id)
    except (ValueError, TypeError, KeyError) as e:
        logging.error("Tool %s argument error: %s", name, e)
        return json.dumps({"error": f"Invalid arguments for {name}"})
    except Exception:
        logging.exception("Tool %s execution failed", name)
        return json.dumps({"error": f"Tool {name} execution failed"})
