"""Financial news search and summarization service."""
import asyncio
import ipaddress
import logging
import os
import socket
from urllib.parse import urlparse

import httpx
from openai import AsyncOpenAI

from firecrawl import FirecrawlApp

from config import (
    FIRECRAWL_API_KEY,
    LLM_CHAT_API_KEY,
    LLM_CHAT_BASE_URL,
    LLM_MODEL,
)

MAX_PAGE_CHARS = 6000

_groq_client: AsyncOpenAI | None = None


def _is_safe_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return False
    try:
        ip = ipaddress.ip_address(socket.gethostbyname(parsed.hostname or ""))
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast:
            return False
    except Exception:
        return False
    return True


class _SafeTransport(httpx.AsyncHTTPTransport):
    """Transport that neutralizes headers blocked by certain AI providers (e.g. Lunos)."""

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        request.headers["user-agent"] = "SAFIA/1.0"
        request.headers.pop("accept", None)
        return await super().handle_async_request(request)


def _get_groq_client() -> AsyncOpenAI | None:
    global _groq_client
    if _groq_client is None and LLM_CHAT_API_KEY:
        _groq_client = AsyncOpenAI(
            base_url=LLM_CHAT_BASE_URL,
            api_key=LLM_CHAT_API_KEY,
            http_client=httpx.AsyncClient(
                transport=_SafeTransport(),
                timeout=httpx.Timeout(600.0, connect=10.0),
            ),
        )
    return _groq_client


def _firecrawl_search(query: str, limit: int = 5) -> list[dict]:
    """Search web via Firecrawl. Returns list of {title, url, content}."""
    if not FIRECRAWL_API_KEY:
        return []
    try:
        app = FirecrawlApp(api_key=FIRECRAWL_API_KEY)
        result = app.search(
            query,
            limit=limit,
            scrape_options={"formats": ["markdown"], "onlyMainContent": True},
        )
        web = getattr(result, "web", []) or []
        if isinstance(web, list):
            return [
                {
                    "title": getattr(r, "title", "") or "",
                    "url": getattr(r, "url", "") or "",
                    "content": getattr(r, "markdown", "")
                    or getattr(r, "content", "")
                    or (r.get("markdown", "") if isinstance(r, dict) else ""),
                }
                for r in web
            ]
        return []
    except Exception:
        logging.exception("Firecrawl search failed")
        return []


async def _summarize_article(
    client: AsyncOpenAI, text: str, question: str, source_url: str
) -> str:
    if not text or not text.strip():
        return f"[No content from {source_url}]"
    truncated = text[:4000] if len(text) > 4000 else text
    prompt = (
        f"Summarize this article excerpt in 2-4 sentences for financial/macro context. "
        f"Focus on facts relevant to: {question}\n\n---\n{truncated}"
    )
    try:
        resp = await client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
        )
        return (resp.choices[0].message.content or "").strip() or truncated[:500]
    except Exception:
        return truncated[:500]


async def _answer_from_summaries(
    client: AsyncOpenAI, question: str, summaries: list[tuple[str, str]]
) -> str:
    context = "\n\n".join(
        f"Source: {url}\nSummary: {summary}" for url, summary in summaries
    )
    prompt = (
        f"Based on the following summaries from recent articles, answer the user's question. "
        f"Be concise and mention sources when relevant. If the summaries are insufficient, say so.\n\n"
        f"Question: {question}\n\n---\n{context}"
    )
    try:
        resp = await client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception:
        return "Unable to generate answer from summaries."


async def search_financial_news(question: str) -> str:
    """Search web for financial/macro news, summarize top results, return answer string."""
    if not question.strip():
        return "Empty question. Ask about asset/financial/macro events."
    if not FIRECRAWL_API_KEY:
        return "News search is not configured (FIRECRAWL_API_KEY not set)."
    if not LLM_CHAT_API_KEY:
        return "News summarization is not enabled (API Key not set)."

    try:
        results = await asyncio.to_thread(_firecrawl_search, question, 5)
        if not results:
            return "No search results for that question."

        client = _get_groq_client()
        if not client:
            return "API Key not set. News summary unavailable."

        summaries = await asyncio.gather(
            *[
                _summarize_article(client, r.get("content", ""), question, r.get("url", ""))
                for r in results
            ]
        )
        summary_tuples = [
            (r.get("url", ""), s) for r, s in zip(results, summaries, strict=True)
        ]
        return await _answer_from_summaries(client, question, summary_tuples)
    except Exception:
        logging.exception("News search failed")
        return "Failed to search or summarize news. Try again later."


async def fetch_and_analyze_article(url: str, question: str) -> str:
    """Fetch a single URL and return a summary or extracted info based on the question."""
    if not url.strip():
        return "Empty URL."
    if not _is_safe_url(url):
        return "URL is not allowed. Only public http/https URLs are supported."
    if not LLM_CHAT_API_KEY:
        return "Article analysis is not enabled (API Key not set)."

    try:
        if FIRECRAWL_API_KEY:
            app = FirecrawlApp(api_key=FIRECRAWL_API_KEY)
            doc = app.scrape_url(url, formats=["markdown"], onlyMainContent=True)
            if isinstance(doc, dict):
                data = doc.get("data", {})
                text = data.get("markdown", "")
            else:
                text = getattr(doc, "markdown", "") or ""
        else:
            text = ""
    except Exception:
        text = ""

    if not text:
        return f"Unable to fetch content from {url}. The site may block access or the content is empty."

    if len(text) > 8000:
        text = text[:8000]

    client = _get_groq_client()
    if not client:
        return text[:1000]

    prompt = (
        f"Web page content:\n\n---\n{text}\n\n---\n\n"
        f"User question: {question}\n\n"
        f"Answer the user's question based on the content above. "
        f"Be concise, informative, and mention key relevant points. "
        f"If the content is not relevant, say so."
    )
    try:
        resp = await client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=600,
        )
        return (resp.choices[0].message.content or "").strip() or text[:500]
    except Exception:
        logging.exception("fetch_and_analyze_article failed for %s", url)
        return f"Failed to analyze article from {url}."
