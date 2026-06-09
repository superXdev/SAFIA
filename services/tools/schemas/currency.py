"""Tool schemas for currency."""

SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_currency_rate",
            "description": (
                "Cek kurs (nilai tukar) antara dua mata uang, atau konversi jumlah ke mata uang lain. "
                "Contoh: USD ke IDR, EUR ke USD, IDR ke USD. "
                "Mengembalikan rate (1 from = X to) dan jika amount diberikan, juga hasil konversi. "
                "Gunakan ketika user tanya kurs, nilai tukar, konversi mata uang, atau berapa rupiah untuk X dolar."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "from_currency": {
                        "type": "string",
                        "description": "Kode mata uang asal (3 huruf). Contoh: USD, EUR, IDR, GBP.",
                    },
                    "to_currency": {
                        "type": "string",
                        "description": "Kode mata uang tujuan (3 huruf). Contoh: IDR, USD, EUR.",
                    },
                    "amount": {
                        "type": ["number", "null"],
                        "description": "Jumlah yang akan dikonversi (opsional). Jika tidak diisi, hanya mengembalikan rate.",
                    },
                },
                "required": ["from_currency", "to_currency"],
            },
        },
    },
]
