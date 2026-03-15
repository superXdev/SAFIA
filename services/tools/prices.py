"""Price check tools — stock (Indonesia), forex, crypto via TradingView."""
import asyncio
import json
from typing import Any

from services.market_prices import (
    get_stock_price_indonesia,
    get_forex_price,
    get_crypto_price,
)


SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_stock_price",
            "description": (
                "Cek harga saham Indonesia (IDX) dari TradingView. "
                "Bisa filter dengan kata kunci (misal: bank, BBCA, TLKM). "
                "Mengembalikan daftar saham dengan price, change %, volume, market cap, sector, dll. "
                "Gunakan ketika user tanya harga saham Indonesia, saham IDX, atau cek saham tertentu."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Kata kunci pencarian (nama emiten atau sektor), opsional. Contoh: bank, BBCA, telkom.",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Jumlah hasil maksimal (default 20).",
                        "default": 20,
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_forex_price",
            "description": (
                "Cek harga pasangan forex (valas) dari TradingView. "
                "Bisa filter dengan simbol (misal: USD, EURUSD, GBPUSD). "
                "Mengembalikan daftar pair dengan price, change %, open, high, low, weekly/monthly performance. "
                "Gunakan ketika user tanya harga forex, kurs valas, atau pair tertentu."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Filter simbol pair, opsional. Contoh: USD, EURUSD, GBPUSD.",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Jumlah hasil maksimal (default 15).",
                        "default": 15,
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_crypto_price",
            "description": (
                "Cek harga kripto dari TradingView. "
                "Bisa filter dengan simbol (misal: BTC, ETH, BNB). "
                "Mengembalikan daftar kripto dengan price, change %, volume, weekly/monthly performance. "
                "Gunakan ketika user tanya harga crypto, bitcoin, ethereum, atau kripto lainnya."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Filter simbol kripto, opsional. Contoh: BTC, ETH, BNB.",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Jumlah hasil maksimal (default 15).",
                        "default": 15,
                    },
                },
            },
        },
    },
]


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
