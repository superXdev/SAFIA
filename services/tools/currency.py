"""Currency converter tool — get exchange rate or convert amount between any two currencies."""
import asyncio
import json
from typing import Any

from services.currency_rate import get_currency_rate


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


async def handle_get_currency_rate(arguments: dict[str, Any], user_id: int) -> str:
    from_currency = (arguments.get("from_currency") or "").strip()
    to_currency = (arguments.get("to_currency") or "").strip()
    amount = arguments.get("amount")
    if not from_currency or not to_currency:
        return json.dumps(
            {"tool": "get_currency_rate", "error": "from_currency dan to_currency wajib diisi."},
            ensure_ascii=False,
        )
    rate = await asyncio.to_thread(get_currency_rate, from_currency, to_currency)
    if rate is None:
        return json.dumps(
            {
                "tool": "get_currency_rate",
                "error": f"Tidak bisa mengambil kurs {from_currency} ke {to_currency}. Cek kode mata uang (3 huruf).",
            },
            ensure_ascii=False,
        )
    payload = {
        "from_currency": from_currency.upper()[:3],
        "to_currency": to_currency.upper()[:3],
        "rate": rate,
        "description": f"1 {from_currency.upper()[:3]} = {rate} {to_currency.upper()[:3]}",
    }
    if amount is not None:
        try:
            amt = float(amount)
            payload["amount"] = amt
            payload["converted"] = round(amt * rate, 2)
        except (TypeError, ValueError):
            pass
    return json.dumps({"tool": "get_currency_rate", "data": payload}, ensure_ascii=False)


HANDLERS: dict[str, Any] = {
    "get_currency_rate": handle_get_currency_rate,
}
