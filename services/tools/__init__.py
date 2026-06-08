"""Tool registry — collects schemas and dispatches handlers."""
import json
import logging
from typing import Any

from services.tools.assets import HANDLERS as ASSET_HANDLERS, SCHEMAS as ASSET_SCHEMAS
from services.tools.crypto_market import HANDLERS as CRYPTO_MARKET_HANDLERS, SCHEMAS as CRYPTO_MARKET_SCHEMAS
from services.tools.currency import HANDLERS as CURRENCY_HANDLERS, SCHEMAS as CURRENCY_SCHEMAS
from services.tools.debts import HANDLERS as DEBT_HANDLERS, SCHEMAS as DEBT_SCHEMAS
from services.tools.gold import HANDLERS as GOLD_HANDLERS, SCHEMAS as GOLD_SCHEMAS
from services.tools.knowledge_search import HANDLERS as KNOWLEDGE_HANDLERS, SCHEMAS as KNOWLEDGE_SCHEMAS
from services.tools.news_search import HANDLERS as NEWS_SEARCH_HANDLERS, SCHEMAS as NEWS_SEARCH_SCHEMAS
from services.tools.prices import HANDLERS as PRICE_HANDLERS, SCHEMAS as PRICE_SCHEMAS
from services.tools.records import HANDLERS as RECORD_HANDLERS, SCHEMAS as RECORD_SCHEMAS
from services.tools.reminders import HANDLERS as REMINDER_HANDLERS, SCHEMAS as REMINDER_SCHEMAS
from services.tools.silver import HANDLERS as SILVER_HANDLERS, SCHEMAS as SILVER_SCHEMAS

TOOLS = (
    RECORD_SCHEMAS + DEBT_SCHEMAS + ASSET_SCHEMAS + GOLD_SCHEMAS
    + SILVER_SCHEMAS + PRICE_SCHEMAS + CURRENCY_SCHEMAS + CRYPTO_MARKET_SCHEMAS
    + NEWS_SEARCH_SCHEMAS + KNOWLEDGE_SCHEMAS + REMINDER_SCHEMAS
)

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
