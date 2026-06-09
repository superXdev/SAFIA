"""Tool schemas for silver."""

SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_silver_price",
            "description": (
                "Get today's spot silver price in IDR from bullion-rates.com. "
                "Returns price per gram, per ounce, and per kilo. "
                "Use when user asks about silver price or today's silver rate."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
]
