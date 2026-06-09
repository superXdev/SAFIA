"""Tool schemas for knowledge_search."""

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
