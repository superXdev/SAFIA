"""News search tool — macro/financial events via Google search and LLM summarization."""
import asyncio
import logging
import os
from typing import Any

import requests
from openai import AsyncOpenAI
from scrapling.fetchers import Fetcher

from config import GROQ_API_KEY

SERPAPI_KEY = os.environ.get("SERPAPI_KEY")
SERPAPI_BASE = "https://serpapi.com/search"
NEWS_SUMMARY_MODEL = "openai/gpt-oss-120b"
MAX_PAGE_CHARS = 6000

_groq_client: AsyncOpenAI | None = None


def _get_groq_client() -> AsyncOpenAI | None:
    global _groq_client
    if _groq_client is None and GROQ_API_KEY:
        _groq_client = AsyncOpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=GROQ_API_KEY,
        )
    return _groq_client


SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "news_search_macro",
            "description": (
                "Cari berita terkini tentang peristiwa aset, keuangan, atau makro ekonomi. "
                "HANYA gunakan tool ini untuk topik terkait pasar keuangan, investasi, aset (emas, saham, crypto, dll), "
                "mata uang/kurs, inflasi, suku bunga, kebijakan bank sentral, atau kondisi ekonomi makro. "
                "JANGAN gunakan untuk berita umum/non-keuangan. "
                "Tool ini mencari di web, memilih 5 sumber relevan, meringkas, lalu menjawab."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "Pertanyaan user tentang peristiwa aset/keuangan/makro (bahasa user).",
                    },
                },
                "required": ["question"],
            },
        },
    },
]


def _serpapi_search(query: str, num: int = 10) -> list[dict]:
    """Sync: run Google search via SerpAPI. Returns list of {title, link, snippet}."""
    if not SERPAPI_KEY:
        return []
    params = {
        "engine": "google",
        "q": query,
        "api_key": SERPAPI_KEY,
        "num": min(num, 100),
        "gl": "id",
        "hl": "id",
    }
    resp = requests.get(SERPAPI_BASE, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json().get("organic_results", [])


def _fetch_page_text(url: str) -> str:
    """Sync: fetch URL with scrapling Fetcher and return main text, truncated for LLM."""
    try:
        page = Fetcher.get(url)
        parts = page.css("body ::text").getall()
        if not parts:
            parts = page.css("::text").getall()
        text = " ".join(p.strip() for p in parts if p and p.strip())
        text = " ".join(text.split())
        return text[:MAX_PAGE_CHARS] if len(text) > MAX_PAGE_CHARS else text
    except Exception:
        return ""


async def _pick_five_relevant(
    client: AsyncOpenAI, question: str, results: list[dict]
) -> list[dict]:
    if len(results) <= 5:
        return results[:5]
    numbered = "\n".join(
        f"{i}. {r.get('title', '')} | {r.get('link', '')} | {r.get('snippet', '')}"
        for i, r in enumerate(results[:10], 1)
    )
    prompt = (
        f"Question: {question}\n\nSearch results (title | link | snippet):\n{numbered}\n\n"
        "Output only the 5 most relevant result numbers, comma-separated (e.g. 1,4,7,2,9). No explanation."
    )
    try:
        resp = await client.chat.completions.create(
            model=NEWS_SUMMARY_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=50,
        )
        raw = (resp.choices[0].message.content or "").strip()
        indices = []
        for part in raw.replace(",", " ").split():
            try:
                n = int(part)
                if 1 <= n <= len(results):
                    indices.append(n - 1)
            except ValueError:
                continue
        if len(indices) >= 5:
            indices = indices[:5]
        else:
            indices = list(range(min(5, len(results))))
        return [results[i] for i in indices]
    except Exception:
        return results[:5]


async def _summarize(
    client: AsyncOpenAI, text: str, question: str, source_url: str
) -> str:
    if not text or not text.strip():
        return f"[Tidak ada konten dari {source_url}]"
    truncated = text[:4000] if len(text) > 4000 else text
    prompt = (
        f"Ringkas cuplikan artikel berikut dalam 2–4 kalimat untuk konteks makro/keuangan. "
        f"Fokus pada fakta yang relevan dengan: {question}\n\n---\n{truncated}"
    )
    try:
        resp = await client.chat.completions.create(
            model="openai/gpt-oss-20b",
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
        f"Sumber: {url}\nRingkasan: {summary}" for url, summary in summaries
    )
    prompt = (
        f"Berdasarkan ringkasan berikut dari artikel terkini, jawab pertanyaan user. "
        f"Singkat dan sebut sumber bila relevan. Jika ringkasan tidak cukup, katakan saja.\n\n"
        f"Pertanyaan: {question}\n\n---\n{context}"
    )
    try:
        resp = await client.chat.completions.create(
            model=NEWS_SUMMARY_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception:
        return "Tidak dapat menghasilkan jawaban dari ringkasan."


async def handle_news_search_macro(arguments: dict[str, Any], user_id: int) -> str:
    question = (arguments.get("question") or "").strip()
    if not question:
        return "Pertanyaan kosong. Berikan pertanyaan tentang peristiwa aset/keuangan/makro."

    if not SERPAPI_KEY:
        return "Pencarian berita belum diaktifkan (SERPAPI_KEY tidak diset)."
    if not GROQ_API_KEY:
        return "Ringkasan berita belum diaktifkan (GROQ_API_KEY tidak diset)."

    try:
        results = await asyncio.to_thread(_serpapi_search, question, 10)
        if not results:
            return "Tidak ada hasil pencarian untuk pertanyaan tersebut."

        client = _get_groq_client()
        if not client:
            return "GROQ_API_KEY tidak diset. Ringkasan berita tidak tersedia."
        chosen = await _pick_five_relevant(client, question, results)
        urls = [r.get("link") for r in chosen if r.get("link")]
        if not urls:
            return "Tidak ada tautan yang bisa diambil."

        texts = await asyncio.gather(
            *[asyncio.to_thread(_fetch_page_text, u) for u in urls]
        )
        summaries = await asyncio.gather(
            *[
                _summarize(client, text, question, url)
                for url, text in zip(urls, texts, strict=True)
            ]
        )
        summary_tuples = list(zip(urls, summaries, strict=True))
        answer = await _answer_from_summaries(client, question, summary_tuples)
        return answer
    except Exception:
        logging.exception("News search failed")
        return "Gagal mencari atau meringkas berita. Coba lagi nanti."


HANDLERS: dict[str, Any] = {
    "news_search_macro": handle_news_search_macro,
}
