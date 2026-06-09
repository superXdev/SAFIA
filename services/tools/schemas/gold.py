"""Tool schemas for gold."""

SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_gold_price",
            "description": (
                "Get today's gold price in IDR (and USD) from global spot sources. "
                "Returns price per Ounce, per Gram, and per Kilogram. "
                "Use when user asks about gold price, gold rate, or gold price."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
]
