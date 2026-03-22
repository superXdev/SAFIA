"""RAG tool: semantic search over admin-uploaded documents in Qdrant."""
import logging
from typing import Any

from config import EMBEDDING_API_KEY
from services.knowledge.embeddings import embed_query
from services.knowledge.qdrant_kb import search_chunks

SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "knowledge_search",
            "description": (
                "Cari cuplikan teks relevan dari knowledge base (dokumen yang diunggah admin). "
                "Gunakan ketika user bertanya tentang kebijakan produk, FAQ internal, prosedur, "
                "atau fakta yang kemungkinan ada di dokumen tersebut — bukan untuk harga pasar "
                "real-time atau berita terkini (pakai tool lain). "
                "Hasil berupa teks mentah untuk kamu rangkum ke user dengan bahasa natural."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Pertanyaan atau kata kunci pencarian dalam bahasa yang sama dengan user",
                    },
                },
                "required": ["query"],
            },
        },
    },
]


async def handle_knowledge_search(arguments: dict[str, Any], user_id: int) -> str:
    _ = user_id
    query = (arguments.get("query") or "").strip()
    if not query:
        return "Parameter query kosong."

    if not EMBEDDING_API_KEY:
        return (
            "Knowledge base tidak dikonfigurasi (set EMBEDDING_API_KEY atau OPENROUTER_API_KEY "
            "dan QDRANT_URL)."
        )

    try:
        vec = await embed_query(query)
        hits = await search_chunks(vec, limit=6, score_threshold=None)
    except Exception:
        logging.exception("knowledge_search failed")
        return "Gagal mencari knowledge base. Coba lagi nanti."

    if not hits:
        return "Tidak ada cuplikan yang cocok di knowledge base untuk pertanyaan ini."

    parts: list[str] = []
    for h in hits:
        fn = h.get("filename") or "dokumen"
        idx = h.get("chunk_index", 0)
        score = h.get("score", 0.0)
        text = (h.get("text") or "").strip()
        if not text:
            continue
        parts.append(
            f"[Sumber: {fn} · segmen {idx} · skor {float(score):.3f}]\n{text}"
        )

    if not parts:
        return "Cuplikan ditemukan tetapi teksnya kosong."

    return "\n\n---\n\n".join(parts)


HANDLERS = {
    "knowledge_search": handle_knowledge_search,
}
