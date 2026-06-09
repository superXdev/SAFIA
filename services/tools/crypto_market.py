"""CoinGecko crypto tools — market cap, coin detail, trending."""
import asyncio
import json
from typing import Any

from services.coingecko import get_top_market_cap, get_coin_detail, get_trending_crypto, search_crypto


async def handle_get_top_crypto_market_cap(arguments: dict[str, Any], user_id: int) -> str:
    vs_currency = arguments.get("vs_currency", "usd") or "usd"
    limit = arguments.get("limit", 10)
    limit = min(max(1, int(limit)), 250)

    data = await asyncio.to_thread(get_top_market_cap, vs_currency=vs_currency, per_page=limit)
    return json.dumps(
        {
            "tool": "get_top_crypto_market_cap",
            "data": {
                "source": "CoinGecko",
                "vs_currency": vs_currency,
                "coins": data,
            },
        },
        ensure_ascii=False,
    )


async def handle_get_coin_detail(arguments: dict[str, Any], user_id: int) -> str:
    coin_id = (arguments.get("coin_id") or "").strip().lower()
    if not coin_id:
        return json.dumps({"error": "coin_id is required"}, ensure_ascii=False)

    data = await asyncio.to_thread(get_coin_detail, coin_id=coin_id)
    return json.dumps(
        {
            "tool": "get_coin_detail",
            "data": {"source": "CoinGecko", "coin": data},
        },
        ensure_ascii=False,
    )


async def handle_get_trending_crypto(arguments: dict[str, Any], user_id: int) -> str:
    data = await asyncio.to_thread(get_trending_crypto)
    return json.dumps(
        {
            "tool": "get_trending_crypto",
            "data": {"source": "CoinGecko", "coins": data},
        },
        ensure_ascii=False,
    )


async def handle_search_crypto(arguments: dict[str, Any], user_id: int) -> str:
    query = (arguments.get("query") or "").strip()
    if not query:
        return json.dumps({"error": "query is required"}, ensure_ascii=False)

    data = await asyncio.to_thread(search_crypto, query=query)
    return json.dumps(
        {
            "tool": "search_crypto",
            "data": {"source": "CoinGecko", "results": data},
        },
        ensure_ascii=False,
    )


HANDLERS: dict[str, Any] = {
    "get_top_crypto_market_cap": handle_get_top_crypto_market_cap,
    "get_coin_detail": handle_get_coin_detail,
    "get_trending_crypto": handle_get_trending_crypto,
    "search_crypto": handle_search_crypto,
}
