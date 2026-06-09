"""Tool schemas for reminders."""

SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "reminder_create",
            "description": (
                "Buat pengingat otomatis untuk user. Jenis pengingat: "
                "price (cek harga aset), news (cari berita keuangan), "
                "note_expense/note_income (pengingat catat pengeluaran/pemasukan), "
                "portfolio_digest (ringkasan portofolio), custom (pesan kustom). "
                "Frekuensi: daily, weekly, monthly, atau interval. "
                "Untuk interval gunakan interval_hours (jam, boleh desimal: 0.5 = 30 menit)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "kind": {
                        "type": "string",
                        "enum": [
                            "price", "news", "note_expense",
                            "note_income", "portfolio_digest", "custom",
                        ],
                        "description": "Jenis pengingat.",
                    },
                    "title": {
                        "type": "string",
                        "description": "Judul/label singkat pengingat.",
                    },
                    "schedule_type": {
                        "type": "string",
                        "enum": ["daily", "weekly", "monthly", "interval"],
                        "description": "Tipe jadwal: daily, weekly, monthly, atau interval.",
                    },
                    "hour": {
                        "type": "integer",
                        "description": "Jam lokal WIB (0-23) untuk eksekusi. Default 8.",
                        "default": 8,
                    },
                    "minute": {
                        "type": "integer",
                        "description": "Menit (0-59). Default 0.",
                        "default": 0,
                    },
                    "day": {
                        "type": ["string", "null"],
                        "description": "Hari (untuk weekly): monday, tuesday, ..., sunday.",
                    },
                    "day_of_month": {
                        "type": ["integer", "null"],
                        "description": "Tanggal (untuk monthly): 1-28.",
                    },
                    "interval_hours": {
                        "type": ["number", "null"],
                        "description": (
                            "Interval dalam jam (wajib jika schedule_type=interval). "
                            "Boleh desimal, contoh: 1, 0.5 (30 menit), 0.25 (15 menit). Min ~0.017 (~1 menit)."
                        ),
                    },
                    "payload": {
                        "type": ["object", "null"],
                        "description": (
                            "Data tambahan sesuai jenis: "
                            'price → {"symbols": ["BTC", "AAPL"], "asset_types": ["crypto", "stock"]}; '
                            'news → {"query": "harga emas"}; '
                            'custom → {"message": "teks pesan"}. Opsional.'
                        ),
                    },
                },
                "required": ["kind", "title", "schedule_type"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "reminder_list",
            "description": "Lihat daftar semua pengingat user (aktif dan nonaktif).",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "reminder_pause",
            "description": (
                "Nonaktifkan pengingat (pause). Pengingat tidak akan dijalankan "
                "sampai diaktifkan kembali."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "reminder_id": {
                        "type": "integer",
                        "description": "ID pengingat yang ingin dinonaktifkan.",
                    },
                },
                "required": ["reminder_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "reminder_resume",
            "description": "Aktifkan kembali pengingat yang sudah di-pause.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reminder_id": {
                        "type": "integer",
                        "description": "ID pengingat yang ingin diaktifkan kembali.",
                    },
                },
                "required": ["reminder_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "reminder_delete",
            "description": "Hapus pengingat secara permanen.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reminder_id": {
                        "type": "integer",
                        "description": "ID pengingat yang ingin dihapus.",
                    },
                },
                "required": ["reminder_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "reminder_suggest_from_habits",
            "description": (
                "Analisis kebiasaan keuangan user (pola pencatatan, pembelian aset) "
                "dan sarankan pengingat otomatis yang relevan. User bisa konfirmasi "
                "saran yang diinginkan lalu buat dengan reminder_create."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
]
