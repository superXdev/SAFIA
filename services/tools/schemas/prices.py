"""Tool schemas for prices."""

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
                        "type": ["string", "null"],
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
                        "type": ["string", "null"],
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
                        "type": ["string", "null"],
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
