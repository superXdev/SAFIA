"""Financial summary builders for records and assets (pure functions + async convenience wrappers)."""
from __future__ import annotations

from datetime import date
from typing import Any

from services.database import get_assets, get_debts, get_records


def build_records_summary(records: list[dict], debts: list[dict]) -> dict[str, Any]:
    """Compute aggregate financial summary from record and debt dicts."""
    total_income = total_expense = 0.0
    per_category: dict[str, float] = {}

    for r in records:
        amt = float(r["amount"])
        kind = r["type"]
        cat = (r.get("category") or "").strip() or "Tanpa kategori"
        per_category[cat] = per_category.get(cat, 0.0) + amt
        if kind == "income":
            total_income += amt
        else:
            total_expense += amt

    total_lent = total_borrowed = 0.0
    total_lent_settled = total_borrowed_settled = 0.0

    for d in debts:
        amt = float(d["amount"])
        settled = d.get("is_settled", False)
        if d["direction"] == "lent":
            total_lent += amt
            if settled:
                total_lent_settled += amt
        else:
            total_borrowed += amt
            if settled:
                total_borrowed_settled += amt

    lent_outstanding = total_lent - total_lent_settled
    borrowed_outstanding = total_borrowed - total_borrowed_settled
    total_balance = total_income - total_expense - lent_outstanding + borrowed_outstanding

    return {
        "total_income": total_income,
        "total_expense": total_expense,
        "total_balance": total_balance,
        "per_category": per_category,
        "record_count": len(records),
        "total_lent": total_lent,
        "total_lent_outstanding": lent_outstanding,
        "total_borrowed": total_borrowed,
        "total_borrowed_outstanding": borrowed_outstanding,
        "debt_count": len(debts),
    }


async def get_financial_summary(
    user_id: int,
    *,
    kind: str | None = None,
    category: str | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
) -> dict[str, Any]:
    """Fetch records + debts and return the computed financial summary."""
    records = await get_records(
        user_id, kind=kind, category=category, from_date=from_date, to_date=to_date
    )
    debts = await get_debts(user_id)
    return build_records_summary(records, debts)


def build_assets_summary(assets: list[dict]) -> dict[str, Any]:
    """Aggregate portfolio by asset_type: total value and allocation %."""
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


def build_rebalance_suggestion(
    assets: list[dict],
    target_allocation: dict[str, float],
) -> dict[str, Any]:
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
    target_sum = sum(target_allocation.values()) or 100
    target_norm = {
        k: (v / target_sum * 100) if target_sum else 0
        for k, v in target_allocation.items()
    }
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


async def get_portfolio_summary(user_id: int) -> dict[str, Any]:
    """Fetch assets for a user and return the computed portfolio summary."""
    assets = await get_assets(user_id)
    return {"summary": build_assets_summary(assets), "assets": assets}
