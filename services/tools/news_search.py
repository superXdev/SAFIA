"""News search tool — thin wrapper around services.news."""
from typing import Any

from services.news import search_financial_news

async def handle_news_search_macro(arguments: dict[str, Any], user_id: int) -> str:
    question = (arguments.get("question") or "").strip()
    return await search_financial_news(question)


HANDLERS: dict[str, Any] = {
    "news_search_macro": handle_news_search_macro,
}
