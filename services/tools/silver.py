"""Silver price tool — fetch current IDR silver prices from harga-emas.org/perak."""
import asyncio
import json
from typing import Any

from services.silver_price import fetch_silver_price_idr


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
