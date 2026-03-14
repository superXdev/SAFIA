"""Asset tools — record, list, summary, rebalance suggestion, delete. Supports stock, crypto, gold, etc."""
import json
from typing import Any

from services.database import (
    delete_assets,
    get_assets,
    save_asset,
    update_asset,
    get_asset,
)

SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "asset_record",
            "description": (
                "Catat atau perbarui aset investasi user (saham, crypto, emas, reksadana, dll). "
                "Setiap panggilan tanpa asset_id = tambah posisi/lot baru (bisa banyak lot untuk aset sama, harga beda). "
                "Dengan asset_id = update posisi tersebut (quantity, unit_value). Nilai dalam IDR. "
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
                        "description": "Jenis aset: stock, crypto, gold, reksadana, deposito, lainnya.",
                    },
                    "name": {
                        "type": "string",
                        "description": "Nama atau simbol aset, misal: BTC, ETH, AAPL, Emas Antam.",
                    },
                    "quantity": {
                        "type": "number",
                        "description": "Jumlah unit (lot, koin, gram, dll).",
                    },
                    "unit_value": {
                        "type": "number",
                        "description": "Nilai per unit dalam IDR (harga beli atau harga pasar).",
                    },
                    "notes": {
                        "type": ["string", "null"],
                        "description": "Catatan opsional.",
                    },
                },
                "required": ["asset_type", "name", "quantity", "unit_value"],
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
]


def _build_summary(assets: list[dict]) -> dict:
    """Aggregate by asset_type: total value and allocation %."""
    total = sum(a["value"] for a in assets)
    by_type: dict[str, float] = {}
    for a in assets:
        t = a["asset_type"]
        by_type[t] = by_type.get(t, 0.0) + a["value"]
    allocation = {
        k: round(100.0 * v / total, 1) if total > 0 else 0.0
        for k, v in by_type.items()
    }
    return {
        "total_value": round(total, 2),
        "by_type": {k: round(v, 2) for k, v in by_type.items()},
        "allocation_percent": allocation,
        "asset_count": len(assets),
    }


def _rebalance(
    assets: list[dict],
    target_allocation: dict[str, float],
) -> dict:
    """Compute current allocation and suggested move per type (IDR)."""
    total = sum(a["value"] for a in assets)
    by_type: dict[str, float] = {}
    for a in assets:
        t = a["asset_type"]
        by_type[t] = by_type.get(t, 0.0) + a["value"]

    current_pct = {
        k: round(100.0 * v / total, 1) if total > 0 else 0.0
        for k, v in by_type.items()
    }
    # Normalize target to sum 100
    target_sum = sum(target_allocation.values()) or 100
    target_norm = {
        k: (v / target_sum * 100) if target_sum else 0
        for k, v in target_allocation.items()
    }
    # All types that appear in current or target
    all_types = set(by_type.keys()) | set(target_norm.keys())
    suggestions = []
    for t in sorted(all_types):
        current_val = by_type.get(t, 0.0)
        current_p = current_pct.get(t, 0.0)
        target_p = target_norm.get(t, 0.0)
        target_val = total * (target_p / 100.0) if total > 0 else 0.0
        diff = target_val - current_val
        suggestions.append({
            "asset_type": t,
            "current_value": round(current_val, 2),
            "current_percent": current_p,
            "target_percent": round(target_p, 1),
            "target_value": round(target_val, 2),
            "difference_idr": round(diff, 2),
            "action": "beli" if diff > 0 else "jual" if diff < 0 else "pertahankan",
        })
    return {
        "total_portfolio_value": round(total, 2),
        "current_allocation_percent": current_pct,
        "target_allocation_percent": target_norm,
        "suggestions": suggestions,
    }


async def handle_asset_record(arguments: dict[str, Any], user_id: int) -> str:
    asset_id = arguments.get("asset_id")
    asset_type = (arguments.get("asset_type") or "").strip() or "lainnya"
    name = (arguments.get("name") or "").strip()
    if not name:
        return json.dumps({"tool": "asset_record", "error": "name required"}, ensure_ascii=False)
    quantity = float(arguments.get("quantity", 0))
    unit_value = float(arguments.get("unit_value", 0))
    notes = (arguments.get("notes") or "").strip()

    if asset_id is not None:
        # Update existing lot by id (accurate for multi-lot: update one row only)
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

    # Insert new lot (allows multiple records for same stock/name at different prices)
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
    # Get all lots of this asset (asset_type + name), FIFO by id
    all_assets = await get_assets(user_id, asset_type=asset_type)
    matching = [a for a in all_assets if (a.get("name") or "").strip().lower() == name.lower()]
    matching.sort(key=lambda a: a["id"])
    total_held = sum(a["quantity"] for a in matching)
    if total_held <= 0:
        return json.dumps(
            {"tool": "asset_sell", "error": f"Tidak ada posisi {asset_type}/{name}."},
            ensure_ascii=False,
        )
    # Deduct from lots (FIFO), update or remove each lot
    remaining_to_sell = quantity_sold
    lots_updated = 0
    lots_closed = 0
    for a in matching:
        if remaining_to_sell <= 0:
            break
        qty = a["quantity"]
        deduct = min(qty, remaining_to_sell)
        remaining_to_sell -= deduct
        if deduct >= qty:
            await delete_assets(user_id, [a["id"]])
            lots_closed += 1
        else:
            await update_asset(user_id, a["id"], quantity=qty - deduct)
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
    summary = _build_summary(assets)
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
    result = _rebalance(assets, target)
    return json.dumps(
        {"tool": "rebalance_suggestion", "data": result},
        ensure_ascii=False,
    )


async def handle_delete_assets(arguments: dict[str, Any], user_id: int) -> str:
    asset_ids = arguments.get("asset_ids") or []
    asset_ids = [int(x) for x in asset_ids if isinstance(x, (int, float))]
    deleted = await delete_assets(user_id, asset_ids)
    payload = {"asset_ids": asset_ids, "deleted_count": deleted}
    return json.dumps({"tool": "delete_assets", "data": payload}, ensure_ascii=False)


HANDLERS: dict[str, Any] = {
    "asset_record": handle_asset_record,
    "asset_sell": handle_asset_sell,
    "get_assets": handle_get_assets,
    "get_assets_summary": handle_get_assets_summary,
    "rebalance_suggestion": handle_rebalance_suggestion,
    "delete_assets": handle_delete_assets,
}
