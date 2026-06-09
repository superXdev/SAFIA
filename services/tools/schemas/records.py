"""Tool schemas for records."""

SCHEMAS = [
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
                        "type": ["string", "null"],
                        "description": "Keterangan (opsional)",
                    },
                    "category": {
                        "type": ["string", "null"],
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
                        "type": ["string", "null"],
                        "description": "Keterangan (opsional)",
                    },
                    "category": {
                        "type": ["string", "null"],
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
                        "type": ["string", "null"],
                        "description": "Jenis catatan yang ingin diambil: 'income' atau 'expense'. Opsional.",
                    },
                    "category": {
                        "type": ["string", "null"],
                        "description": "Filter berdasarkan kategori tertentu. Opsional.",
                    },
                    "min_amount": {
                        "type": ["number", "null"],
                        "description": "Jumlah minimum (>=). Opsional.",
                    },
                    "max_amount": {
                        "type": ["number", "null"],
                        "description": "Jumlah maksimum (<=). Opsional.",
                    },
                    "from_date": {
                        "type": ["string", "null"],
                        "description": "Tanggal mulai (YYYY-MM-DD). Opsional.",
                    },
                    "to_date": {
                        "type": ["string", "null"],
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
                "Ambil ringkasan agregat keuangan user: total pemasukan, total pengeluaran, "
                "saldo bersih (net), total_balance (saldo keseluruhan termasuk utang/piutang), "
                "ringkasan per kategori, serta total piutang dan utang yang belum lunas. "
                "Gunakan ketika user minta cek saldo, analisis kebiasaan keuangan, atau ringkasan "
                "periode tertentu, lalu jelaskan hasilnya dengan bahasamu sendiri."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "kind": {
                        "type": ["string", "null"],
                        "description": "Jenis catatan yang ingin diringkas: 'income' atau 'expense'. Opsional.",
                    },
                    "category": {
                        "type": ["string", "null"],
                        "description": "Filter berdasarkan kategori tertentu. Opsional.",
                    },
                    "min_amount": {
                        "type": ["number", "null"],
                        "description": "Jumlah minimum (>=). Opsional.",
                    },
                    "max_amount": {
                        "type": ["number", "null"],
                        "description": "Jumlah maksimum (<=). Opsional.",
                    },
                    "from_date": {
                        "type": ["string", "null"],
                        "description": "Tanggal mulai (YYYY-MM-DD). Opsional.",
                    },
                    "to_date": {
                        "type": ["string", "null"],
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
                        "type": ["array", "null"],
                        "items": {"type": "integer"},
                        "description": "Daftar ID catatan yang ingin dihapus. Opsional.",
                    },
                    "kind": {
                        "type": ["string", "null"],
                        "description": "Jenis catatan yang ingin dihapus: 'income' atau 'expense'. Opsional.",
                    },
                    "category": {
                        "type": ["string", "null"],
                        "description": "Hapus catatan berdasarkan kategori tertentu. Opsional.",
                    },
                    "from_date": {
                        "type": ["string", "null"],
                        "description": "Tanggal mulai (YYYY-MM-DD). Opsional.",
                    },
                    "to_date": {
                        "type": ["string", "null"],
                        "description": "Tanggal akhir (YYYY-MM-DD). Opsional.",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "reset_records",
            "description": (
                "Hapus semua catatan pemasukan/pengeluaran user (reset/erase seluruh database records). "
                "Gunakan hanya ketika user dengan tegas minta reset atau hapus semua catatan keuangan. "
                "Konfirmasi dulu sebelum memanggil."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
]
