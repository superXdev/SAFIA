"""Tool schemas for knowledge_search."""

SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "knowledge_search",
            "description": (
                "Search relevant text snippets from the knowledge base (admin-uploaded documents). "
                "Use when user asks about product policies, internal FAQs, procedures, "
                "or facts likely found in those documents — not for real-time "
                "market prices or current news (use other tools). "
                "Results are raw text for you to summarize to the user in natural language."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description":                         "Search query or keyword in the same language as the user",
                    },
                },
                "required": ["query"],
            },
        },
    },
]
