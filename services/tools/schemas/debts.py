"""Tool schemas for debts."""

SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "debt_record",
            "description": (
                "Catat utang atau piutang user. Panggil ketika user menyebut meminjam uang dari "
                "seseorang (utang/borrowed) atau meminjamkan uang ke seseorang (piutang/lent). "
                "Tool ini menyimpan data dan mengembalikan JSON."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "direction": {
                        "type": "string",
                        "enum": ["lent", "borrowed"],
                        "description": "'lent' jika user meminjamkan uang ke orang lain (piutang), 'borrowed' jika user meminjam dari orang lain (utang).",
                    },
                    "person": {
                        "type": "string",
                        "description": "Nama orang yang terkait utang/piutang.",
                    },
                    "amount": {"type": "number", "description": "Jumlah uang (angka)"},
                    "description": {
                        "type": ["string", "null"],
                        "description": "Keterangan (opsional)",
                    },
                },
                "required": ["direction", "person", "amount"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_debts",
            "description": (
                "Ambil daftar utang/piutang user. Gunakan ketika user minta lihat daftar "
                "utang atau piutang, siapa yang berutang, atau berapa total utang/piutang."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "direction": {
                        "type": ["string", "null"],
                        "enum": ["lent", "borrowed", None],
                        "description": "Filter: 'lent' (piutang) atau 'borrowed' (utang). Opsional.",
                    },
                    "person": {
                        "type": ["string", "null"],
                        "description": "Filter berdasarkan nama orang. Opsional.",
                    },
                    "is_settled": {
                        "type": ["boolean", "null"],
                        "description": "Filter: true = sudah lunas, false = belum lunas. Opsional.",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "settle_debt",
            "description": (
                "Tandai utang/piutang sebagai lunas. Gunakan ketika user menyebut sudah "
                "membayar utang atau sudah menerima pembayaran piutang."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "debt_ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "Daftar ID utang/piutang yang ingin dilunasi.",
                    },
                },
                "required": ["debt_ids"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_debt",
            "description": (
                "Hapus catatan utang/piutang user. Gunakan ketika user minta hapus "
                "catatan utang/piutang tertentu."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "debt_ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "Daftar ID utang/piutang yang ingin dihapus.",
                    },
                },
                "required": ["debt_ids"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "reset_debts",
            "description": (
                "Hapus semua data utang/piutang user (reset/erase seluruh database utang). "
                "Gunakan hanya ketika user dengan tegas minta reset atau hapus semua utang/piutang. "
                "Konfirmasi dulu sebelum memanggil."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
]
