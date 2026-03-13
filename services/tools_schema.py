"""Tool definitions (JSON schemas) for the LLM."""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "expense_record",
            "description": (
                "Catat pengeluaran (expense) user. Panggil ketika user menyebut mengeluarkan uang "
                "atau pengeluaran. Tool ini hanya menyimpan data mentah dan mengembalikan JSON; "
                "kamu yang harus menjelaskan ke user dengan gaya yang natural."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {"type": "number", "description": "Jumlah uang (angka)"},
                    "description": {
                        "type": "string",
                        "description": "Keterangan (opsional)",
                    },
                    "category": {
                        "type": "string",
                        "description": "Nama kategori (opsional), misal: Makanan, Transport, Gaji, Bonus",
                    },
                },
                "required": ["amount"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "income_record",
            "description": (
                "Catat pemasukan (income) user. Panggil ketika user menyebut menerima uang atau "
                "pemasukan. Tool ini hanya menyimpan data mentah dan mengembalikan JSON; "
                "kamu yang harus menjelaskan ke user dengan gaya yang natural."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {"type": "number", "description": "Jumlah uang (angka)"},
                    "description": {
                        "type": "string",
                        "description": "Keterangan (opsional)",
                    },
                    "category": {
                        "type": "string",
                        "description": "Nama kategori (opsional), misal: Makanan, Transport, Gaji, Bonus",
                    },
                },
                "required": ["amount"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_records",
            "description": (
                "Ambil catatan pemasukan/pengeluaran user dengan filter opsional dan kembalikan "
                "data mentah dalam bentuk JSON. Gunakan ketika user minta lihat riwayat/laporan "
                "keuangan detail (misal berdasarkan rentang tanggal, jenis income/expense, kategori, "
                "atau rentang jumlah uang), lalu jelaskan hasilnya dengan bahasamu sendiri."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "kind": {
                        "type": "string",
                        "description": "Jenis catatan yang ingin diambil: 'income' atau 'expense'. Opsional.",
                    },
                    "category": {
                        "type": "string",
                        "description": "Filter berdasarkan kategori tertentu. Opsional.",
                    },
                    "min_amount": {
                        "type": "number",
                        "description": "Jumlah minimum (>=). Opsional.",
                    },
                    "max_amount": {
                        "type": "number",
                        "description": "Jumlah maksimum (<=). Opsional.",
                    },
                    "from_date": {
                        "type": "string",
                        "description": "Tanggal mulai (YYYY-MM-DD). Opsional.",
                    },
                    "to_date": {
                        "type": "string",
                        "description": "Tanggal akhir (YYYY-MM-DD). Opsional.",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_records_summary",
            "description": (
                "Ambil ringkasan agregat catatan pemasukan/pengeluaran user (total pemasukan, "
                "total pengeluaran, saldo bersih, ringkasan per kategori) dan kembalikan dalam "
                "bentuk JSON. Gunakan ketika user minta analisis kebiasaan keuangan atau ringkasan "
                "periode tertentu, lalu jelaskan hasilnya dengan bahasamu sendiri."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "kind": {
                        "type": "string",
                        "description": "Jenis catatan yang ingin diringkas: 'income' atau 'expense'. Opsional.",
                    },
                    "category": {
                        "type": "string",
                        "description": "Filter berdasarkan kategori tertentu. Opsional.",
                    },
                    "min_amount": {
                        "type": "number",
                        "description": "Jumlah minimum (>=). Opsional.",
                    },
                    "max_amount": {
                        "type": "number",
                        "description": "Jumlah maksimum (<=). Opsional.",
                    },
                    "from_date": {
                        "type": "string",
                        "description": "Tanggal mulai (YYYY-MM-DD). Opsional.",
                    },
                    "to_date": {
                        "type": "string",
                        "description": "Tanggal akhir (YYYY-MM-DD). Opsional.",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_records",
            "description": (
                "Hapus catatan pemasukan/pengeluaran user. Bisa hapus berdasarkan ID spesifik, "
                "jenis (income/expense), kategori, atau rentang tanggal. Gunakan ketika user "
                "minta hapus catatan tertentu. Selalu konfirmasi dulu sebelum menghapus, dan "
                "laporkan berapa catatan yang terhapus."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "record_ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "Daftar ID catatan yang ingin dihapus. Opsional.",
                    },
                    "kind": {
                        "type": "string",
                        "description": "Jenis catatan yang ingin dihapus: 'income' atau 'expense'. Opsional.",
                    },
                    "category": {
                        "type": "string",
                        "description": "Hapus catatan berdasarkan kategori tertentu. Opsional.",
                    },
                    "from_date": {
                        "type": "string",
                        "description": "Tanggal mulai (YYYY-MM-DD). Opsional.",
                    },
                    "to_date": {
                        "type": "string",
                        "description": "Tanggal akhir (YYYY-MM-DD). Opsional.",
                    },
                },
            },
        },
    },
]

