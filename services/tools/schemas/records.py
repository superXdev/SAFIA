"""Tool schemas for records."""

SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "expense_record",
            "description": (
                "Record a user's expense. Call when user mentions spending money "
                "or an expense. This tool only stores raw data and returns JSON; "
                "you must explain to the user in a natural tone."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {"type": "number", "description": "Amount of money (number)"},
                    "description": {
                        "type": ["string", "null"],
                        "description": "Description (optional)",
                    },
                    "category": {
                        "type": ["string", "null"],
                        "description": "Category name (optional), e.g.: Food, Transport, Salary, Bonus",
                    },
                },
                "required": ["amount"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "income_record",
            "description": (
                "Record a user's income. Call when user mentions receiving money or "
                "income. This tool only stores raw data and returns JSON; "
                "you must explain to the user in a natural tone."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {"type": "number", "description": "Amount of money (number)"},
                    "description": {
                        "type": ["string", "null"],
                        "description": "Description (optional)",
                    },
                    "category": {
                        "type": ["string", "null"],
                        "description": "Category name (optional), e.g.: Food, Transport, Salary, Bonus",
                    },
                },
                "required": ["amount"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_records",
            "description": (
                "Get the user's income/expense records with optional filters and return "
                "raw data as JSON. Use when user asks to see detailed financial "
                "history/report (e.g. by date range, income/expense type, category, "
                "or amount range), then explain the results in your own words."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "kind": {
                        "type": ["string", "null"],
                        "description":                         "Type of record to fetch: 'income' or 'expense'. Optional.",
                    },
                    "category": {
                        "type": ["string", "null"],
                        "description": "Filter by specific category. Optional.",
                    },
                    "min_amount": {
                        "type": ["number", "null"],
                        "description": "Minimum amount (>=). Optional.",
                    },
                    "max_amount": {
                        "type": ["number", "null"],
                        "description": "Maximum amount (<=). Optional.",
                    },
                    "from_date": {
                        "type": ["string", "null"],
                        "description": "Start date (YYYY-MM-DD). Optional.",
                    },
                    "to_date": {
                        "type": ["string", "null"],
                        "description": "End date (YYYY-MM-DD). Optional.",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_records_summary",
            "description": (
                "Get the user's aggregate financial summary: total income, total expense, "
                "net balance, total_balance (overall balance including debt/lent), "
                "summary per category, and total outstanding lent and debt. "
                "Use when user asks to check balance, analyze spending habits, or a summary "
                "for a specific period, then explain the results in your own words."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "kind": {
                        "type": ["string", "null"],
                        "description":                         "Type of record to summarize: 'income' or 'expense'. Optional.",
                    },
                    "category": {
                        "type": ["string", "null"],
                        "description": "Filter by specific category. Optional.",
                    },
                    "min_amount": {
                        "type": ["number", "null"],
                        "description": "Minimum amount (>=). Optional.",
                    },
                    "max_amount": {
                        "type": ["number", "null"],
                        "description": "Maximum amount (<=). Optional.",
                    },
                    "from_date": {
                        "type": ["string", "null"],
                        "description": "Start date (YYYY-MM-DD). Optional.",
                    },
                    "to_date": {
                        "type": ["string", "null"],
                        "description": "End date (YYYY-MM-DD). Optional.",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_records",
            "description": (
                "Delete user's income/expense records. Can delete by specific ID, "
                "type (income/expense), category, or date range. Use when user "
                "asks to delete specific records. Always confirm first before deleting, and "
                "report how many records were deleted."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "record_ids": {
                        "type": ["array", "null"],
                        "items": {"type": "integer"},
                        "description":                         "List of record IDs to delete. Optional.",
                    },
                    "kind": {
                        "type": ["string", "null"],
                        "description":                         "Type of record to delete: 'income' or 'expense'. Optional.",
                    },
                    "category": {
                        "type": ["string", "null"],
                        "description":                         "Delete records by specific category. Optional.",
                    },
                    "from_date": {
                        "type": ["string", "null"],
                        "description": "Start date (YYYY-MM-DD). Optional.",
                    },
                    "to_date": {
                        "type": ["string", "null"],
                        "description": "End date (YYYY-MM-DD). Optional.",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "reset_records",
            "description": (
                "Delete all user income/expense records (reset/erase entire records database). "
                "Use only when user explicitly asks to reset or delete all financial records. "
                "Confirm first before calling."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
]
