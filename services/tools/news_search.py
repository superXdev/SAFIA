"""News search tool — thin wrapper around services.news."""
from typing import Any

from services.news import search_financial_news

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


async def handle_news_search_macro(arguments: dict[str, Any], user_id: int) -> str:
    question = (arguments.get("question") or "").strip()
    return await search_financial_news(question)


HANDLERS: dict[str, Any] = {
    "news_search_macro": handle_news_search_macro,
}
