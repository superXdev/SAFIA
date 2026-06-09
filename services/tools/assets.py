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
