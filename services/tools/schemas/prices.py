"""Tool schemas for prices."""

SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_stock_price",
            "description": (
                "Check Indonesian stock prices (IDX) from TradingView. "
                "Can filter by keyword (e.g.: bank, BBCA, TLKM). "
                "Returns a list of stocks with price, change %, volume, market cap, sector, etc. "
                "Use when user asks about Indonesian stock prices, IDX stocks, or checking a specific stock."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": ["string", "null"],
                        "description":                         "Search keyword (issuer name or sector), optional. e.g.: bank, BBCA, telkom.",
                    },
                    "limit": {
                        "type": "integer",
                        "description":                         "Maximum number of results (default 20).",
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
                "Check forex pair prices from TradingView. "
                "Can filter by symbol (e.g.: USD, EURUSD, GBPUSD). "
                "Returns a list of pairs with price, change %, open, high, low, weekly/monthly performance. "
                "Use when user asks about forex prices, exchange rates, or a specific pair."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": ["string", "null"],
                        "description":                         "Pair symbol filter, optional. e.g.: USD, EURUSD, GBPUSD.",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (default 15).",
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
                "Check crypto prices from TradingView. "
                "Can filter by symbol (e.g.: BTC, ETH, BNB). "
                "Returns a list of cryptos with price, change %, volume, weekly/monthly performance. "
                "Use when user asks about crypto prices, bitcoin, ethereum, or other cryptos."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": ["string", "null"],
                        "description":                         "Crypto symbol filter, optional. e.g.: BTC, ETH, BNB.",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (default 15).",
                        "default": 15,
                    },
                },
            },
        },
    },
]
