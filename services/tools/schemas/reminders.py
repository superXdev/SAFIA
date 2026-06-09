"""Tool schemas for reminders."""

SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "reminder_create",
            "description": (
                "Create an automatic reminder for user. Reminder types: "
                "price (check asset prices), news (search financial news), "
                "note_expense/note_income (reminder to record expenses/income), "
                "portfolio_digest (portfolio summary), custom (custom message). "
                "Frequency: daily, weekly, monthly, or interval. "
                "For interval use interval_hours (hours, accepts decimals: 0.5 = 30 minutes)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "kind": {
                        "type": "string",
                        "enum": [
                            "price", "news", "note_expense",
                            "note_income", "portfolio_digest", "custom",
                        ],
                        "description":                         "Reminder type.",
                    },
                    "title": {
                        "type": "string",
                        "description":                         "Short title/label for the reminder.",
                    },
                    "schedule_type": {
                        "type": "string",
                        "enum": ["daily", "weekly", "monthly", "interval"],
                        "description":                         "Schedule type: daily, weekly, monthly, or interval.",
                    },
                    "hour": {
                        "type": "integer",
                        "description":                         "Local time hour in WIB (0-23) for execution. Default 8.",
                        "default": 8,
                    },
                    "minute": {
                        "type": "integer",
                        "description":                         "Minute (0-59). Default 0.",
                        "default": 0,
                    },
                    "day": {
                        "type": ["string", "null"],
                        "description":                         "Day (for weekly): monday, tuesday, ..., sunday.",
                    },
                    "day_of_month": {
                        "type": ["integer", "null"],
                        "description":                         "Day of month (for monthly): 1-28.",
                    },
                    "interval_hours": {
                        "type": ["number", "null"],
                        "description": (
                        "Interval in hours (required if schedule_type=interval). "
                        "Accepts decimals, e.g.: 1, 0.5 (30 minutes), 0.25 (15 minutes). Min ~0.017 (~1 minute)."
                        ),
                    },
                    "payload": {
                        "type": ["object", "null"],
                        "description": (
                        "Additional data by type: "
                        'price → {"symbols": ["BTC", "AAPL"], "asset_types": ["crypto", "stock"]}; '
                        'news → {"query": "harga emas"}; '
                        'custom → {"message": "message text"}. Optional.'
                        ),
                    },
                },
                "required": ["kind", "title", "schedule_type"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "reminder_list",
            "description": "View all user reminders (active and inactive).",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "reminder_pause",
            "description": (
                "Deactivate a reminder (pause). The reminder will not run "
                "until reactivated."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "reminder_id": {
                        "type": "integer",
                        "description":                         "ID of the reminder to deactivate.",
                    },
                },
                "required": ["reminder_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "reminder_resume",
            "description": "Reactivate a paused reminder.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reminder_id": {
                        "type": "integer",
                        "description":                         "ID of the reminder to reactivate.",
                    },
                },
                "required": ["reminder_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "reminder_delete",
            "description": "Permanently delete a reminder.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reminder_id": {
                        "type": "integer",
                        "description":                         "ID of the reminder to delete.",
                    },
                },
                "required": ["reminder_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "reminder_suggest_from_habits",
            "description": (
                "Analyze user's financial habits (recording patterns, asset purchases) "
                "and suggest relevant automatic reminders. User can confirm "
                "desired suggestions then create them with reminder_create."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
]
