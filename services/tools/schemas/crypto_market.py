"""Tool schemas for crypto_market."""

SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_top_crypto_market_cap",
            "description": (
                "Ambil daftar kripto teratas berdasarkan market cap dari CoinGecko. "
                "Mengembalikan ranking, nama, simbol, harga, perubahan 24 jam, market cap, volume. "
                "Gunakan ketika user tanya top crypto, market cap tertinggi, ranking kripto, "
                "atau daftar crypto berdasarkan kapitalisasi pasar."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "vs_currency": {
                        "type": "string",
                        "description": "Mata uang target untuk harga (e.g. usd, idr, eur). Default: usd.",
                        "default": "usd",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Jumlah koin yang ditampilkan (default 10, max 250).",
                        "default": 10,
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_coin_detail",
            "description": (
                "Ambil detail lengkap satu koin kripto dari CoinGecko berdasarkan coin ID. "
                "Mengembalikan deskripsi, harga, market cap, ATH/ATL, supply, perubahan 24h/7d/30d, kategori, dan link. "
                "Gunakan ketika user tanya detail tentang koin tertentu seperti bitcoin, ethereum, solana, dll. "
                "Coin ID biasanya lowercase, contoh: bitcoin, ethereum, solana, ripple, dogecoin, cardano."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "coin_id": {
                        "type": "string",
                        "description": "CoinGecko coin ID (lowercase). Contoh: bitcoin, ethereum, solana, ripple, dogecoin, binancecoin.",
                    },
                },
                "required": ["coin_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_trending_crypto",
            "description": (
                "Ambil daftar kripto yang sedang trending (paling banyak dicari) di CoinGecko dalam 24 jam terakhir. "
                "Mengembalikan top 15 koin trending beserta harga, market cap, dan perubahan 24 jam. "
                "Gunakan ketika user tanya crypto apa yang lagi trending, viral, naik daun, atau populer saat ini."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_crypto",
            "description": (
                "Cari nama atau simbol kripto untuk mendapatkan CoinGecko coin ID yang tepat. "
                "Penting digunakan jika 'get_coin_detail' gagal karena coin ID tidak tepat (misal: user ketik 'BNB', ID yang benar adalah 'binancecoin'). "
                "Mengembalikan daftar prediksi koin teratas yang cocok dengan nama atau simbol yang dicari."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Nama atau simbol koin yang dicari. Contoh: bnb, xrp, shiba inu, doge.",
                    },
                },
                "required": ["query"],
            },
        },
    },
]
