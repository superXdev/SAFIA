"""Price check tools — stock (Indonesia), forex, crypto via TradingView."""
import asyncio
import json
from typing import Any

from services.market_prices import (
    get_stock_price_indonesia,
    get_forex_price,
    get_crypto_price,
)


async def handle_get_stock_price(arguments: dict[str, Any], user_id: int) -> str:
    query = arguments.get("query") or None
    limit = arguments.get("limit", 20)
    limit = min(max(1, int(limit)), 50)
    data = await asyncio.to_thread(get_stock_price_indonesia, query=query, limit=limit)
    return json.dumps(
        {"tool": "get_stock_price", "data": {"source": "TradingView", "stocks": data}},
        ensure_ascii=False,
    )


async def handle_get_forex_price(arguments: dict[str, Any], user_id: int) -> str:
    symbol = arguments.get("symbol") or None
    limit = arguments.get("limit", 15)
    limit = min(max(1, int(limit)), 50)
    result = await asyncio.to_thread(get_forex_price, symbol=symbol, limit=limit)
    return json.dumps(
        {
            "tool": "get_forex_price",
            "data": {
                "source": "TradingView",
                "pairs": result["data"],
                "usd_idr_rate": result.get("usd_idr_rate"),
            },
        },
        ensure_ascii=False,
    )


async def handle_get_crypto_price(arguments: dict[str, Any], user_id: int) -> str:
    symbol = arguments.get("symbol") or None
    limit = arguments.get("limit", 15)
    limit = min(max(1, int(limit)), 50)
    result = await asyncio.to_thread(get_crypto_price, symbol=symbol, limit=limit)
    return json.dumps(
        {
            "tool": "get_crypto_price",
            "data": {
                "source": "TradingView",
                "cryptos": result["data"],
                "usd_idr_rate": result.get("usd_idr_rate"),
            },
        },
        ensure_ascii=False,
    )


HANDLERS: dict[str, Any] = {
    "get_stock_price": handle_get_stock_price,
    "get_forex_price": handle_get_forex_price,
    "get_crypto_price": handle_get_crypto_price,
}
