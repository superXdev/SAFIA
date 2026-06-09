"""Tool schemas for news_search."""

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
