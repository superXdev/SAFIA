"""Tool schemas for user memory."""
SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "remember_fact",
            "description": (
                "Store a fact, preference, or personal information about the user into long-term memory. "
                "Use whenever the user shares information about themselves: name, hobbies, favorite assets, "
                "spending habits, financial goals, daily routines, investment preferences, etc. "
                "Keep facts concise (1-2 sentences). Categories: personal, preference, habit, goal, finance, other."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "fact": {
                        "type": "string",
                        "description": "Fact or preference about the user, at most 1-2 concise sentences.",
                    },
                    "category": {
                        "type": "string",
                        "description": "Category: personal, preference, habit, goal, finance, other",
                        "enum": ["personal", "preference", "habit", "goal", "finance", "other"],
                    },
                },
                "required": ["fact", "category"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "recall_memories",
            "description": (
                "Search long-term memory for facts about the user relevant to the query. "
                "Use when the user asks 'what do you remember about me?' "
                "or when you need to recall user preferences/facts before answering."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query, e.g. 'name', 'habits', 'financial goals'",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "forget_fact",
            "description": (
                "Delete a specific fact from the user's memory. Use when the user asks to "
                "remove or forget certain information."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Description of the fact to delete, for search matching.",
                    },
                },
                "required": ["query"],
            },
        },
    },
]
