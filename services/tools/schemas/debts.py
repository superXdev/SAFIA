"""Tool schemas for debts."""

SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "debt_record",
            "description": (
                "Record a user's debt or lent money. Call when user mentions borrowing money from "
                "someone (debt/borrowed) or lending money to someone (lent). "
                "This tool stores data and returns JSON."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "direction": {
                        "type": "string",
                        "enum": ["lent", "borrowed"],
                        "description":                         "'lent' if user lends money to someone else (piutang), 'borrowed' if user borrows from someone else (utang).",
                    },
                    "person": {
                        "type": "string",
                        "description":                         "Name of the person related to the debt/lent.",
                    },
                    "amount": {"type": "number", "description": "Amount of money (number)"},
                    "description": {
                        "type": ["string", "null"],
                        "description":                         "Description (optional)",
                    },
                },
                "required": ["direction", "person", "amount"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_debts",
            "description": (
                "Get the user's debt/lent list. Use when user asks to see their "
                "debt or lent list, who owes money, or total debt/lent."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "direction": {
                        "type": ["string", "null"],
                        "enum": ["lent", "borrowed", None],
                        "description":                         "Filter: 'lent' or 'borrowed' (debt). Optional.",
                    },
                    "person": {
                        "type": ["string", "null"],
                        "description":                         "Filter by person name. Optional.",
                    },
                    "is_settled": {
                        "type": ["boolean", "null"],
                        "description":                         "Filter: true = settled, false = not settled. Optional.",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "settle_debt",
            "description": (
                "Mark debt/lent as settled. Use when user mentions having "
                "paid a debt or received a lent payment."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "debt_ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description":                         "List of debt/lent IDs to settle.",
                    },
                },
                "required": ["debt_ids"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_debt",
            "description": (
                "Delete a user's debt/lent record. Use when user asks to delete "
                "a specific debt/lent record."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "debt_ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description":                         "List of debt/lent IDs to delete.",
                    },
                },
                "required": ["debt_ids"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "reset_debts",
            "description": (
                "Delete all user debt/lent data (reset/erase entire debt database). "
                "Use only when user explicitly asks to reset or delete all debts/lent. "
                "Confirm first before calling."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
]
