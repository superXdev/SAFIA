"""Tool schemas for news_search."""
SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "news_search_macro",
            "description": (
                "Search latest news about asset, financial, or macro-economic events. "
                "ONLY use this tool for topics related to financial markets, investments, assets (gold, stocks, crypto, etc.), "
                "currency/exchange rates, inflation, interest rates, central bank policy, or macro-economic conditions. "
                "DO NOT use for general/non-financial news. "
                "This tool searches the web, selects 5 relevant sources, summarizes, then answers."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "User's question about asset/financial/macro events (in user's language).",
                    },
                },
                "required": ["question"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_article",
            "description": (
                "Fetch and extract the content of a specific URL/article. "
                "Use when the user provides a link and asks you to analyze, summarize, "
                "or extract information from that page. Works with news articles, blog posts, "
                "documentation pages, and most web content."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The full URL of the article/webpage to fetch.",
                    },
                    "question": {
                        "type": "string",
                        "description": "What the user wants to know about this page (in user's language).",
                    },
                },
                "required": ["url", "question"],
            },
        },
    },
]
