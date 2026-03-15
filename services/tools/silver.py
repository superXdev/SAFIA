"""Silver price tool — fetch current IDR silver prices from harga-emas.org/perak."""
import asyncio
import json
from typing import Any

from services.silver_price import fetch_silver_price_idr


SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_silver_price",
            "description": (
                "Ambil harga perak (silver) spot hari ini dalam IDR dari bullion-rates.com. "
                "Mengembalikan harga per gram, per ounce, dan per kilo. "
                "Gunakan ketika user tanya harga perak, silver price, atau perak hari ini."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
]


async def handle_get_silver_price(arguments: dict[str, Any], user_id: int) -> str:
    data = await asyncio.to_thread(fetch_silver_price_idr)
    payload = {
        "source": "bullion-rates.com/silver/IDR",
        "prices": data,
    }
    return json.dumps({"tool": "get_silver_price", "data": payload}, ensure_ascii=False)


HANDLERS: dict[str, Any] = {
    "get_silver_price": handle_get_silver_price,
}
