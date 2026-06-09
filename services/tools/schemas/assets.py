"""Tool schemas for assets."""
SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "asset_record",
            "description": (
                "Record or update a user investment asset (stocks, crypto, gold, mutual funds, etc.). "
                "Without asset_id: add a new position/lot. With asset_id: update that position. "
                "Values in IDR. If the user only mentions a nominal amount (e.g. buy Tesla stock 8 million rupiah without quantity), "
                "fill amount_idr; the system fetches real-time prices and calculates units automatically. "
                "Summary and rebalancing correctly sum all lots per asset type."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "asset_id": {
                        "type": ["integer", "null"],
                        "description": "Asset ID from get_assets. Fill only to update an existing position; leave empty to add a new lot.",
                    },
                    "asset_type": {
                        "type": "string",
                        "description": "Asset type: stock, crypto, gold, silver, forex, reksadana (mutual fund), deposito (deposit), lainnya (other).",
                    },
                    "name": {
                        "type": "string",
                        "description": "Asset name or symbol, e.g. Tesla, TSLA, BTC, BBCA, Emas Antam.",
                    },
                    "quantity": {
                        "type": ["number", "null"],
                        "description": "Number of units (lots, coins, grams). Leave empty if using amount_idr/amount_usd.",
                    },
                    "unit_value": {
                        "type": ["number", "null"],
                        "description": "Value per unit in IDR. Leave empty if using amount_idr/amount_usd.",
                    },
                    "amount_idr": {
                        "type": ["number", "null"],
                        "description": "Total purchase nominal in IDR (e.g. 8000000). System fetches real-time price to calculate quantity.",
                    },
                    "amount_usd": {
                        "type": ["number", "null"],
                        "description": "Total purchase nominal in USD. System converts to IDR then calculates quantity from real-time price.",
                    },
                    "notes": {
                        "type": ["string", "null"],
                        "description": "Optional notes.",
                    },
                },
                "required": ["asset_type", "name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "asset_sell",
            "description": (
                "Record an asset sale: specify asset type, name, and quantity sold. "
                "The system deducts from total holdings (all lots combined) without needing ID or price. "
                "Use when user says they sold an asset (e.g. sell 5 AAPL, sell 0.5 BTC)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "asset_type": {
                        "type": "string",
                        "description": "Asset type: stock, crypto, gold, reksadana, etc. (same as when recorded).",
                    },
                    "name": {
                        "type": "string",
                        "description": "Name/symbol of asset sold, e.g. AAPL, BTC, Emas Antam.",
                    },
                    "quantity_sold": {
                        "type": "number",
                        "description": "Number of units sold (lots, coins, grams, etc.).",
                    },
                },
                "required": ["asset_type", "name", "quantity_sold"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_assets",
            "description": (
                "Get the user's investment asset list. Can filter by type (stock, crypto, gold, etc.). "
                "Use when the user asks to view their portfolio or asset list."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "asset_type": {
                        "type": ["string", "null"],
                        "description": "Filter by asset type: stock, crypto, gold, reksadana, etc. Leave empty for all.",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_assets_summary",
            "description": (
                "Portfolio summary: total value per asset type, overall total value, and "
                "current allocation percentages. For investors who want an overview or allocation view."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "rebalance_suggestion",
            "description": (
                "Portfolio rebalancing suggestions: compare current allocation with target (%), "
                "then recommend buy/sell per asset type to approach the target. "
                "Target in percent (total 100). Example: stock 40%, crypto 30%, gold 30%."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "target_allocation": {
                        "type": "string",
                        "description": (
                            "JSON object: asset type to target percent. Example: "
                            '{"stock": 40, "crypto": 30, "gold": 30}. Keys must match the asset_type used by the user.'
                        ),
                    },
                },
                "required": ["target_allocation"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_assets",
            "description": (
                "Delete user asset records by ID. Use when the user asks to delete "
                "a specific asset position. Provide IDs from get_assets."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "asset_ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "List of asset IDs to delete.",
                    },
                },
                "required": ["asset_ids"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "reset_portfolio",
            "description": (
                "Delete all user portfolio/asset data (reset/erase entire investment asset database). "
                "Use ONLY when the user explicitly requests reset or delete all portfolio/assets. "
                "Confirm first before calling."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
]
