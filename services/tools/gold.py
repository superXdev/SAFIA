"""Gold price tool — fetch current IDR gold prices from harga-emas.org."""
import asyncio
import json
from typing import Any

from services.gold_price import fetch_gold_price_idr


SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_gold_price",
            "description": (
                "Ambil harga emas hari ini dalam IDR (dan USD) dari sumber spot dunia. "
                "Mengembalikan harga per Ounce, per Gram, dan per Kilogram. "
                "Gunakan ketika user tanya harga emas, kurs emas, atau gold price."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
]


async def handle_get_gold_price(arguments: dict[str, Any], user_id: int) -> str:
    # Fetch in thread to avoid blocking (requests is sync)
    rows = await asyncio.to_thread(fetch_gold_price_idr)
    payload = {
        "source": "harga-emas.org",
        "prices": rows,
    }
    return json.dumps({"tool": "get_gold_price", "data": payload}, ensure_ascii=False)


HANDLERS: dict[str, Any] = {
    "get_gold_price": handle_get_gold_price,
}
