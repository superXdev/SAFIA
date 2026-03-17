"""Tool registry — collects schemas and dispatches handlers."""
import logging
from typing import Any

from services.tools.assets import HANDLERS as ASSET_HANDLERS, SCHEMAS as ASSET_SCHEMAS
from services.tools.crypto_market import HANDLERS as CRYPTO_MARKET_HANDLERS, SCHEMAS as CRYPTO_MARKET_SCHEMAS
from services.tools.currency import HANDLERS as CURRENCY_HANDLERS, SCHEMAS as CURRENCY_SCHEMAS
from services.tools.debts import HANDLERS as DEBT_HANDLERS, SCHEMAS as DEBT_SCHEMAS
from services.tools.gold import HANDLERS as GOLD_HANDLERS, SCHEMAS as GOLD_SCHEMAS
from services.tools.news_search import HANDLERS as NEWS_SEARCH_HANDLERS, SCHEMAS as NEWS_SEARCH_SCHEMAS
from services.tools.prices import HANDLERS as PRICE_HANDLERS, SCHEMAS as PRICE_SCHEMAS
from services.tools.records import HANDLERS as RECORD_HANDLERS, SCHEMAS as RECORD_SCHEMAS
from services.tools.silver import HANDLERS as SILVER_HANDLERS, SCHEMAS as SILVER_SCHEMAS

TOOLS = (
    RECORD_SCHEMAS + DEBT_SCHEMAS + ASSET_SCHEMAS + GOLD_SCHEMAS
    + SILVER_SCHEMAS + PRICE_SCHEMAS + CURRENCY_SCHEMAS + CRYPTO_MARKET_SCHEMAS
    + NEWS_SEARCH_SCHEMAS
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
}


async def run_tool(name: str, arguments: dict[str, Any], user_id: int) -> str:
    handler = _HANDLERS.get(name)
    if not handler:
        return "Unknown tool."
    try:
        return await handler(arguments, user_id)
    except Exception:
        logging.exception("Tool execution failed")
        return "Error saat menjalankan tool."
