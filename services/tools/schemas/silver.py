"""Tool schemas for silver."""

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
