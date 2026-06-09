"""Tool schemas for crypto_market."""

SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_top_crypto_market_cap",
            "description": (
                "Get the top crypto list by market cap from CoinGecko. "
                "Returns ranking, name, symbol, price, 24h change, market cap, volume. "
                "Use when user asks about top crypto, highest market cap, crypto ranking, "
                "or crypto list by market capitalization."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "vs_currency": {
                        "type": "string",
                        "description":                         "Target currency for price (e.g. usd, idr, eur). Default: usd.",
                        "default": "usd",
                    },
                    "limit": {
                        "type": "integer",
                        "description":                         "Number of coins to display (default 10, max 250).",
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
                "Get full details of a single crypto coin from CoinGecko by coin ID. "
                "Returns description, price, market cap, ATH/ATL, supply, 24h/7d/30d changes, categories, and links. "
                "Use when user asks for details about a specific coin like bitcoin, ethereum, solana, etc. "
                "Coin ID is usually lowercase, e.g.: bitcoin, ethereum, solana, ripple, dogecoin, cardano."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "coin_id": {
                        "type": "string",
                        "description":                         "CoinGecko coin ID (lowercase). e.g.: bitcoin, ethereum, solana, ripple, dogecoin, binancecoin.",
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
                "Get the list of trending (most searched) crypto on CoinGecko in the last 24 hours. "
                "Returns top 15 trending coins with price, market cap, and 24h change. "
                "Use when user asks what crypto is trending, viral, gaining popularity, or currently popular."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_crypto",
            "description": (
                "Search crypto name or symbol to get the correct CoinGecko coin ID. "
                "Important to use if 'get_coin_detail' fails due to incorrect coin ID (e.g.: user types 'BNB', the correct ID is 'binancecoin'). "
                "Returns a list of top coin predictions matching the searched name or symbol."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description":                         "Coin name or symbol to search. e.g.: bnb, xrp, shiba inu, doge.",
                    },
                },
                "required": ["query"],
            },
        },
    },
]
