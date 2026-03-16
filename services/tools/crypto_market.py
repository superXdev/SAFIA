"""CoinGecko crypto tools — market cap, coin detail, trending."""
import asyncio
import json
from typing import Any

from services.coingecko import get_top_market_cap, get_coin_detail, get_trending_crypto, search_crypto


SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_top_crypto_market_cap",
            "description": (
                "Ambil daftar kripto teratas berdasarkan market cap dari CoinGecko. "
                "Mengembalikan ranking, nama, simbol, harga, perubahan 24 jam, market cap, volume. "
                "Gunakan ketika user tanya top crypto, market cap tertinggi, ranking kripto, "
                "atau daftar crypto berdasarkan kapitalisasi pasar."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "vs_currency": {
                        "type": "string",
                        "description": "Mata uang target untuk harga (e.g. usd, idr, eur). Default: usd.",
                        "default": "usd",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Jumlah koin yang ditampilkan (default 10, max 250).",
                        "default": 10,
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_coin_detail",
            "description": (
                "Ambil detail lengkap satu koin kripto dari CoinGecko berdasarkan coin ID. "
                "Mengembalikan deskripsi, harga, market cap, ATH/ATL, supply, perubahan 24h/7d/30d, kategori, dan link. "
                "Gunakan ketika user tanya detail tentang koin tertentu seperti bitcoin, ethereum, solana, dll. "
                "Coin ID biasanya lowercase, contoh: bitcoin, ethereum, solana, ripple, dogecoin, cardano."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "coin_id": {
                        "type": "string",
                        "description": "CoinGecko coin ID (lowercase). Contoh: bitcoin, ethereum, solana, ripple, dogecoin, binancecoin.",
                    },
                },
                "required": ["coin_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_trending_crypto",
            "description": (
                "Ambil daftar kripto yang sedang trending (paling banyak dicari) di CoinGecko dalam 24 jam terakhir. "
                "Mengembalikan top 15 koin trending beserta harga, market cap, dan perubahan 24 jam. "
                "Gunakan ketika user tanya crypto apa yang lagi trending, viral, naik daun, atau populer saat ini."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_crypto",
            "description": (
                "Cari nama atau simbol kripto untuk mendapatkan CoinGecko coin ID yang tepat. "
                "Penting digunakan jika 'get_coin_detail' gagal karena coin ID tidak tepat (misal: user ketik 'BNB', ID yang benar adalah 'binancecoin'). "
                "Mengembalikan daftar prediksi koin teratas yang cocok dengan nama atau simbol yang dicari."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Nama atau simbol koin yang dicari. Contoh: bnb, xrp, shiba inu, doge.",
                    },
                },
                "required": ["query"],
            },
        },
    },
]


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
