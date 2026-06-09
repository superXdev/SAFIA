"""Tool schemas for gold."""

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
