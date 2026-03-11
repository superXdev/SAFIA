"""LLM client and chat completion."""
import logging

from openai import AsyncOpenAI

from config import LLM_API_KEY, LLM_BASE_URL, MODEL


_client: AsyncOpenAI | None = None


def get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(base_url=LLM_BASE_URL, api_key=LLM_API_KEY)
    return _client


async def chat(messages: list[dict]) -> str:
    """Send messages to LLM and return assistant reply. On error returns user-friendly message."""
    try:
        response = await get_client().chat.completions.create(
            model=MODEL,
            messages=messages,
        )
        return response.choices[0].message.content or "..."
    except Exception:
        logging.exception("LLM request failed")
        return "Maaf, terjadi kesalahan. Coba lagi nanti."
