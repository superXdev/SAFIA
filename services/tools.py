"""Tool execution for expense/income recording."""
import json
import logging
from datetime import date, datetime
from typing import Any

from services.database import (
    delete_records,
    get_records,
    save_expense_record,
    save_income_record,
)
from services.tools_schema import TOOLS


def _build_record_confirm(
    amount: float,
    kind: str,
    category: str,
    description: str,
) -> dict[str, Any]:
    """Build confirmation payload for expense/income record."""
    return {
        "type": kind,
        "amount": amount,
        "category": category or "",
        "description": description or "",
        "status": "recorded",
    }


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    value = value.strip()
    if not value:
        return None
    # Expect simple YYYY-MM-DD; fall back to fromisoformat if needed.
    try:
        return datetime.fromisoformat(value).date()
    except ValueError:
        return None


def _build_summary(records: list[dict]) -> dict[str, Any]:
    """Build aggregate summary payload for a list of records."""
    if not records:
        return {
            "total_income": 0.0,
            "total_expense": 0.0,
            "net": 0.0,
            "per_category": {},
            "count": 0,
        }
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

    net = total_income - total_expense

    return {
        "total_income": total_income,
        "total_expense": total_expense,
        "net": net,
        "per_category": per_category,
        "count": len(records),
    }


async def run_tool(name: str, arguments: dict[str, Any], user_id: int) -> str:
    """Execute a tool by name and return result string for the LLM."""
    try:
        if name == "expense_record":
            amount = float(arguments.get("amount", 0))
            description = (arguments.get("description") or "").strip()
            category = (arguments.get("category") or "").strip()
            await save_expense_record(user_id, amount, description, category)
            payload = _build_record_confirm(amount, "expense", category, description)
            return json.dumps({"tool": "expense_record", "data": payload}, ensure_ascii=False)
        if name == "income_record":
            amount = float(arguments.get("amount", 0))
            description = (arguments.get("description") or "").strip()
            category = (arguments.get("category") or "").strip()
            await save_income_record(user_id, amount, description, category)
            payload = _build_record_confirm(amount, "income", category, description)
            return json.dumps({"tool": "income_record", "data": payload}, ensure_ascii=False)
        if name == "get_records":
            kind = (arguments.get("kind") or "").strip() or None
            category = (arguments.get("category") or "").strip() or None
            min_amount = arguments.get("min_amount")
            max_amount = arguments.get("max_amount")
            from_date = _parse_date(arguments.get("from_date"))
            to_date = _parse_date(arguments.get("to_date"))

            records = await get_records(
                user_id,
                kind=kind,
                category=category,
                min_amount=float(min_amount) if min_amount is not None else None,
                max_amount=float(max_amount) if max_amount is not None else None,
                from_date=from_date,
                to_date=to_date,
            )
            payload = {
                "filters": {
                    "kind": kind,
                    "category": category,
                    "min_amount": min_amount,
                    "max_amount": max_amount,
                    "from_date": arguments.get("from_date"),
                    "to_date": arguments.get("to_date"),
                },
                "records": records,
            }
            return json.dumps({"tool": "get_records", "data": payload}, ensure_ascii=False)
        if name == "get_records_summary":
            kind = (arguments.get("kind") or "").strip() or None
            category = (arguments.get("category") or "").strip() or None
            min_amount = arguments.get("min_amount")
            max_amount = arguments.get("max_amount")
            from_date = _parse_date(arguments.get("from_date"))
            to_date = _parse_date(arguments.get("to_date"))

            records = await get_records(
                user_id,
                kind=kind,
                category=category,
                min_amount=float(min_amount) if min_amount is not None else None,
                max_amount=float(max_amount) if max_amount is not None else None,
                from_date=from_date,
                to_date=to_date,
            )
            payload = {
                "filters": {
                    "kind": kind,
                    "category": category,
                    "min_amount": min_amount,
                    "max_amount": max_amount,
                    "from_date": arguments.get("from_date"),
                    "to_date": arguments.get("to_date"),
                },
                "summary": _build_summary(records),
            }
            return json.dumps({"tool": "get_records_summary", "data": payload}, ensure_ascii=False)
        if name == "delete_records":
            record_ids = arguments.get("record_ids") or None
            kind = (arguments.get("kind") or "").strip() or None
            category = (arguments.get("category") or "").strip() or None
            from_date = _parse_date(arguments.get("from_date"))
            to_date = _parse_date(arguments.get("to_date"))

            deleted = await delete_records(
                user_id,
                record_ids=record_ids,
                kind=kind,
                category=category,
                from_date=from_date,
                to_date=to_date,
            )
            payload = {
                "filters": {
                    "record_ids": record_ids,
                    "kind": kind,
                    "category": category,
                    "from_date": arguments.get("from_date"),
                    "to_date": arguments.get("to_date"),
                },
                "deleted_count": deleted,
            }
            return json.dumps({"tool": "delete_records", "data": payload}, ensure_ascii=False)
    except Exception:
        logging.exception("Tool execution failed")
        return "Error saat menjalankan tool."
    return "Unknown tool."
