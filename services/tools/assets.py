"""Asset tools — record, list, summary, rebalance suggestion, delete. Supports stock, crypto, gold, etc."""
import asyncio
import json
from typing import Any

from services.currency_rate import get_currency_rate
from services.database import (
    delete_all_assets,
    delete_assets,
    get_asset_rows,
    get_assets,
    get_asset,
    save_asset,
    update_asset,
)
from services.summaries import build_assets_summary, build_rebalance_suggestion

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


def _round_quantity_by_type(asset_type: str, qty: float) -> float:
    """Round quantity by asset type (stock/crypto/gold/silver/forex)."""
    at = (asset_type or "").strip().lower()
    if at == "crypto":
        return round(qty, 8)
    # stock, gold, silver, forex, others: 2 decimals
    return round(qty, 2)


async def handle_asset_record(arguments: dict[str, Any], user_id: int) -> str:
    from services.market_prices import get_asset_unit_price_idr

    asset_id = arguments.get("asset_id")
    asset_type = (arguments.get("asset_type") or "").strip() or "lainnya"
    name = (arguments.get("name") or "").strip()
    if not name:
        return json.dumps({"tool": "asset_record", "error": "name required"}, ensure_ascii=False)

    quantity = arguments.get("quantity")
    unit_value = arguments.get("unit_value")
    amount_idr = arguments.get("amount_idr")
    amount_usd = arguments.get("amount_usd")
    notes = (arguments.get("notes") or "").strip()

    quantity = float(quantity) if quantity is not None else 0.0
    unit_value = float(unit_value) if unit_value is not None else 0.0

    # Amount-based: user gave nominal (e.g. "beli saham Tesla 8 juta") → resolve price and compute quantity
    if (amount_idr is not None and float(amount_idr) > 0) or (amount_usd is not None and float(amount_usd) > 0):
        if quantity > 0 and unit_value > 0:
            # Both amount and qty/unit_value provided — prefer qty/unit_value
            pass
        else:
            price_idr = await asyncio.to_thread(get_asset_unit_price_idr, asset_type, name)
            if price_idr is None or price_idr <= 0:
                return json.dumps(
                    {
                        "tool": "asset_record",
                        "error": f"Tidak bisa mengambil harga real-time untuk {asset_type}/{name}. Sebutkan quantity dan unit_value manual.",
                    },
                    ensure_ascii=False,
                )
            amount_idr_val = amount_idr
            if amount_idr_val is None or float(amount_idr_val) <= 0:
                rate = await asyncio.to_thread(get_currency_rate, "USD", "IDR")
                if rate is None:
                    return json.dumps(
                        {"tool": "asset_record", "error": "Kurs USD/IDR tidak tersedia. Coba lagi."},
                        ensure_ascii=False,
                    )
                amount_idr_val = float(amount_usd) * rate
            else:
                amount_idr_val = float(amount_idr_val)
            quantity = amount_idr_val / price_idr
            unit_value = price_idr
            quantity = _round_quantity_by_type(asset_type, quantity)

    if asset_id is not None:
        ok = await update_asset(
            user_id, int(asset_id),
            quantity=quantity,
            unit_value=unit_value,
            notes=notes if notes else None,
        )
        if not ok:
            return json.dumps({"tool": "asset_record", "error": "asset_id not found"}, ensure_ascii=False)
        asset = await get_asset(user_id, int(asset_id))
        return json.dumps({"tool": "asset_record", "data": asset, "updated": True}, ensure_ascii=False)

    if quantity <= 0 or unit_value <= 0:
        return json.dumps(
            {
                "tool": "asset_record",
                "error": "Perlu quantity dan unit_value, atau amount_idr/amount_usd agar sistem hitung dari harga real-time.",
            },
            ensure_ascii=False,
        )

    asset = await save_asset(
        user_id, asset_type, name, quantity, unit_value, notes
    )
    return json.dumps({"tool": "asset_record", "data": asset}, ensure_ascii=False)


async def handle_asset_sell(arguments: dict[str, Any], user_id: int) -> str:
    asset_type = (arguments.get("asset_type") or "").strip().lower() or None
    name = (arguments.get("name") or "").strip()
    quantity_sold = float(arguments.get("quantity_sold", 0))
    if not asset_type or not name:
        return json.dumps(
            {"tool": "asset_sell", "error": "asset_type and name required"},
            ensure_ascii=False,
        )
    if quantity_sold <= 0:
        return json.dumps(
            {"tool": "asset_sell", "error": "quantity_sold must be positive"},
            ensure_ascii=False,
        )
    rows = await get_asset_rows(user_id, asset_type, name)
    total_held = sum(r.quantity for r in rows)
    if total_held <= 0:
        return json.dumps(
            {"tool": "asset_sell", "error": f"Tidak ada posisi {asset_type}/{name}."},
            ensure_ascii=False,
        )
    remaining_to_sell = quantity_sold
    lots_updated = 0
    lots_closed = 0
    for r in rows:
        if remaining_to_sell <= 0:
            break
        deduct = min(r.quantity, remaining_to_sell)
        remaining_to_sell -= deduct
        if deduct >= r.quantity:
            await delete_assets(user_id, [r.id])
            lots_closed += 1
        else:
            await update_asset(user_id, r.id, quantity=r.quantity - deduct)
            lots_updated += 1
    actual_sold = quantity_sold - remaining_to_sell
    payload = {
        "asset_type": asset_type,
        "name": name,
        "quantity_sold": actual_sold,
        "total_held_before": total_held,
        "remaining_held": total_held - actual_sold,
        "lots_updated": lots_updated,
        "lots_closed": lots_closed,
    }
    if remaining_to_sell > 0:
        payload["note"] = f"Yang tersedia hanya {total_held}; tercatat jual {actual_sold}."
    return json.dumps({"tool": "asset_sell", "data": payload}, ensure_ascii=False)


async def handle_get_assets(arguments: dict[str, Any], user_id: int) -> str:
    asset_type = (arguments.get("asset_type") or "").strip() or None
    assets = await get_assets(user_id, asset_type=asset_type)
    payload = {"filters": {"asset_type": asset_type}, "assets": assets}
    return json.dumps({"tool": "get_assets", "data": payload}, ensure_ascii=False)


async def handle_get_assets_summary(arguments: dict[str, Any], user_id: int) -> str:
    assets = await get_assets(user_id)
    summary = build_assets_summary(assets)
    payload = {"summary": summary, "assets": assets}
    return json.dumps({"tool": "get_assets_summary", "data": payload}, ensure_ascii=False)


async def handle_rebalance_suggestion(arguments: dict[str, Any], user_id: int) -> str:
    raw = (arguments.get("target_allocation") or "{}").strip()
    try:
        target = json.loads(raw)
        if not isinstance(target, dict):
            target = {}
        target = {str(k).strip().lower(): float(v) for k, v in target.items()}
    except (json.JSONDecodeError, ValueError):
        target = {}
    assets = await get_assets(user_id)
    result = build_rebalance_suggestion(assets, target)
    return json.dumps(
        {"tool": "rebalance_suggestion", "data": result},
        ensure_ascii=False,
    )


async def handle_delete_assets(arguments: dict[str, Any], user_id: int) -> str:
    asset_ids = arguments.get("asset_ids") or []
    asset_ids = [int(x) for x in asset_ids if isinstance(x, (int, float))]
    deleted = await delete_assets(user_id, asset_ids)
    payload = {"deleted_count": deleted}
    return json.dumps({"tool": "delete_assets", "data": payload}, ensure_ascii=False)


async def handle_reset_portfolio(arguments: dict[str, Any], user_id: int) -> str:
    deleted = await delete_all_assets(user_id)
    payload = {"deleted_count": deleted}
    return json.dumps({"tool": "reset_portfolio", "data": payload}, ensure_ascii=False)


HANDLERS: dict[str, Any] = {
    "asset_record": handle_asset_record,
    "asset_sell": handle_asset_sell,
    "get_assets": handle_get_assets,
    "get_assets_summary": handle_get_assets_summary,
    "rebalance_suggestion": handle_rebalance_suggestion,
    "delete_assets": handle_delete_assets,
    "reset_portfolio": handle_reset_portfolio,
}
