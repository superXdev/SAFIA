"""Embedding client — local fastembed by default, remote API as fallback."""
import logging

from openai import AsyncOpenAI

from config import (
    EMBEDDING_API_KEY,
    EMBEDDING_BASE_URL,
    EMBEDDING_LOCAL,
    EMBEDDING_MODEL,
    KB_EMBED_BATCH_SIZE,
)
from services.knowledge.local_embed import (
    embed_query_local,
    embed_texts_local,
)

_client: AsyncOpenAI | None = None


def get_embedding_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            base_url=EMBEDDING_BASE_URL.rstrip("/"),
            api_key=EMBEDDING_API_KEY or "missing",
        )
    return _client


async def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []

    if EMBEDDING_LOCAL:
        return embed_texts_local(texts)

    if not EMBEDDING_API_KEY:
        raise RuntimeError("EMBEDDING_API_KEY is not set.")
    client = get_embedding_client()
    out: list[list[float]] = []
    batch_size = max(1, KB_EMBED_BATCH_SIZE)
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        try:
            resp = await client.embeddings.create(model=EMBEDDING_MODEL, input=batch)
        except Exception:
            logging.exception("Embedding API request failed")
            raise
        ordered = sorted(resp.data, key=lambda d: d.index)
        for row in ordered:
            if row.embedding is None:
                raise RuntimeError("Embedding response missing vector.")
            out.append(list(row.embedding))
    return out


async def embed_query(text: str) -> list[float]:
    if EMBEDDING_LOCAL:
        return embed_query_local(text)
    vecs = await embed_texts([text])
    return vecs[0]
