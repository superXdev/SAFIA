"""Tool schemas for currency."""

SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_currency_rate",
            "description": (
                "Check exchange rate between two currencies, or convert an amount to another currency. "
                "e.g.: USD to IDR, EUR to USD, IDR to USD. "
                "Returns the rate (1 from = X to) and if amount is given, also the conversion result. "
                "Use when user asks about exchange rate, currency conversion, or how much rupiah for X dollars."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "from_currency": {
                        "type": "string",
                        "description":                         "Source currency code (3 letters). e.g.: USD, EUR, IDR, GBP.",
                    },
                    "to_currency": {
                        "type": "string",
                        "description":                         "Target currency code (3 letters). e.g.: IDR, USD, EUR.",
                    },
                    "amount": {
                        "type": ["number", "null"],
                        "description":                         "Amount to convert (optional). If not provided, only returns the rate.",
                    },
                },
                "required": ["from_currency", "to_currency"],
            },
        },
    },
]
