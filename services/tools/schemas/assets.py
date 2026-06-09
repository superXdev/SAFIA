"""Tool schemas for assets."""

SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "asset_record",
            "description": (
                "Catat atau perbarui aset investasi user (saham, crypto, emas, reksadana, dll). "
                "Setiap panggilan tanpa asset_id = tambah posisi/lot baru. Dengan asset_id = update posisi tersebut. "
                "Nilai dalam IDR. Jika user hanya menyebut nominal (misal: beli saham Tesla 8 juta rupiah tanpa jumlah lot), "
                "isi amount_idr; sistem akan ambil harga real-time dan hitung jumlah unit otomatis. "
                "Summary dan rebalancing menjumlah semua lot per jenis aset dengan benar."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "asset_id": {
                        "type": ["integer", "null"],
                        "description": "ID aset dari get_assets. Isi hanya saat ingin update satu posisi tertentu; kosongkan untuk tambah lot baru.",
                    },
                    "asset_type": {
                        "type": "string",
                        "description": "Jenis aset: stock, crypto, gold, silver (perak), forex, reksadana, deposito, lainnya.",
                    },
                    "name": {
                        "type": "string",
                        "description": "Nama atau simbol aset, misal: Tesla, TSLA, BTC, BBCA, Emas Antam.",
                    },
                    "quantity": {
                        "type": ["number", "null"],
                        "description": "Jumlah unit (lot, koin, gram). Kosongkan jika pakai amount_idr/amount_usd.",
                    },
                    "unit_value": {
                        "type": ["number", "null"],
                        "description": "Nilai per unit dalam IDR. Kosongkan jika pakai amount_idr/amount_usd.",
                    },
                    "amount_idr": {
                        "type": ["number", "null"],
                        "description": "Total nominal beli dalam IDR (misal 8000000). Sistem hitung quantity dari harga real-time.",
                    },
                    "amount_usd": {
                        "type": ["number", "null"],
                        "description": "Total nominal beli dalam USD. Sistem konversi ke IDR lalu hitung quantity dari harga real-time.",
                    },
                    "notes": {
                        "type": ["string", "null"],
                        "description": "Catatan opsional.",
                    },
                },
                "required": ["asset_type", "name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "asset_sell",
            "description": (
                "Catat penjualan aset: sebutkan jenis dan nama aset plus jumlah yang dijual. "
                "Sistem akan mengurangi dari total kepemilikan (gabungan semua lot) tanpa perlu ID atau harga. "
                "Gunakan ketika user bilang jual aset (misal: jual 5 AAPL, jual 0.5 BTC)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "asset_type": {
                        "type": "string",
                        "description": "Jenis aset: stock, crypto, gold, reksadana, dll (sama seperti saat catat).",
                    },
                    "name": {
                        "type": "string",
                        "description": "Nama/simbol aset yang dijual, misal: AAPL, BTC, Emas Antam.",
                    },
                    "quantity_sold": {
                        "type": "number",
                        "description": "Jumlah unit yang dijual (lot, koin, gram, dll).",
                    },
                },
                "required": ["asset_type", "name", "quantity_sold"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_assets",
            "description": (
                "Ambil daftar aset investasi user. Bisa filter per jenis (stock, crypto, gold, dll). "
                "Gunakan ketika user minta lihat portofolio atau daftar aset."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "asset_type": {
                        "type": ["string", "null"],
                        "description": "Filter jenis aset: stock, crypto, gold, reksadana, dll. Kosongkan untuk semua.",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_assets_summary",
            "description": (
                "Ringkasan portofolio: total nilai per jenis aset, total nilai keseluruhan, dan "
                "persentase alokasi saat ini. Untuk investor yang mau lihat overview atau alokasi."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "rebalance_suggestion",
            "description": (
                "Saran rebalancing portofolio: bandingkan alokasi saat ini dengan target (%), "
                "lalu berikan rekomendasi beli/jual per jenis aset agar mendekati target. "
                "Target dalam persen (total 100). Contoh: stock 40%, crypto 30%, gold 30%."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "target_allocation": {
                        "type": "string",
                        "description": (
                            "JSON object: jenis aset ke target persen. Contoh: "
                            '{"stock": 40, "crypto": 30, "gold": 30}. Key harus sama dengan asset_type yang dipakai user.'
                        ),
                    },
                },
                "required": ["target_allocation"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_assets",
            "description": (
                "Hapus catatan aset user berdasarkan ID. Gunakan ketika user minta hapus "
                "posisi aset tertentu. Sebutkan ID dari get_assets."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "asset_ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "Daftar ID aset yang ingin dihapus.",
                    },
                },
                "required": ["asset_ids"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "reset_portfolio",
            "description": (
                "Hapus semua data portofolio/aset user (reset/erase seluruh database aset investasi). "
                "Gunakan hanya ketika user dengan tegas minta reset atau hapus semua portofolio/aset. "
                "Konfirmasi dulu sebelum memanggil."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
]
