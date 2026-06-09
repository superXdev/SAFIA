"""News search tool — thin wrapper around services.news."""
from typing import Any

from services.news import fetch_and_analyze_article, search_financial_news


async def handle_news_search_macro(arguments: dict[str, Any], user_id: int) -> str:
    question = (arguments.get("question") or "").strip()
    return await search_financial_news(question)


async def handle_fetch_article(arguments: dict[str, Any], user_id: int) -> str:
    url = (arguments.get("url") or "").strip()
    question = (arguments.get("question") or "").strip()
    if not url:
        return "No URL provided."
    return await fetch_and_analyze_article(url, question)


HANDLERS: dict[str, Any] = {
    "news_search_macro": handle_news_search_macro,
    "fetch_article": handle_fetch_article,
}
