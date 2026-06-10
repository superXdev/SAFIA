"""Record tools — expense, income, get, summary, delete."""
import json
from typing import Any

from services.database import (
    delete_records,
    get_debts,
    get_records,
    save_expense_record,
    save_income_record,
)
from services.summaries import build_records_summary
from services.tools._helpers import parse_date

MAX_DESC_LEN = 500
MAX_CATEGORY_LEN = 100


def _build_record_confirm(
    amount: float,
    kind: str,
    category: str,
    description: str,
) -> dict[str, Any]:
    return {
        "type": kind,
        "amount": amount,
        "category": category or "",
        "description": description or "",
        "status": "recorded",
    }


def _parse_filters(arguments: dict[str, Any]) -> dict[str, Any]:
    return {
        "kind": (arguments.get("kind") or "").strip() or None,
        "category": (arguments.get("category") or "").strip() or None,
        "min_amount": arguments.get("min_amount"),
        "max_amount": arguments.get("max_amount"),
        "from_date": parse_date(arguments.get("from_date")),
        "to_date": parse_date(arguments.get("to_date")),
    }


async def handle_expense_record(arguments: dict[str, Any], user_id: int) -> str:
    amount = float(arguments.get("amount", 0))
    if amount <= 0:
        return json.dumps({"tool": "expense_record", "error": "amount must be positive"}, ensure_ascii=False)
    description = (arguments.get("description") or "").strip()[:MAX_DESC_LEN]
    category = (arguments.get("category") or "").strip()[:MAX_CATEGORY_LEN]
    await save_expense_record(user_id, amount, description, category)
    payload = _build_record_confirm(amount, "expense", category, description)
    return json.dumps({"tool": "expense_record", "data": payload}, ensure_ascii=False)


async def handle_income_record(arguments: dict[str, Any], user_id: int) -> str:
    amount = float(arguments.get("amount", 0))
    if amount <= 0:
        return json.dumps({"tool": "income_record", "error": "amount must be positive"}, ensure_ascii=False)
    description = (arguments.get("description") or "").strip()[:MAX_DESC_LEN]
    category = (arguments.get("category") or "").strip()[:MAX_CATEGORY_LEN]
    await save_income_record(user_id, amount, description, category)
    payload = _build_record_confirm(amount, "income", category, description)
    return json.dumps({"tool": "income_record", "data": payload}, ensure_ascii=False)


async def handle_get_records(arguments: dict[str, Any], user_id: int) -> str:
    f = _parse_filters(arguments)
    records = await get_records(
        user_id,
        kind=f["kind"],
        category=f["category"],
        min_amount=float(f["min_amount"]) if f["min_amount"] is not None else None,
        max_amount=float(f["max_amount"]) if f["max_amount"] is not None else None,
        from_date=f["from_date"],
        to_date=f["to_date"],
    )
    payload = {
        "filters": {
            "kind": f["kind"],
            "category": f["category"],
            "min_amount": f["min_amount"],
            "max_amount": f["max_amount"],
            "from_date": arguments.get("from_date"),
            "to_date": arguments.get("to_date"),
        },
        "records": records,
    }
    return json.dumps({"tool": "get_records", "data": payload}, ensure_ascii=False)


async def handle_get_records_summary(arguments: dict[str, Any], user_id: int) -> str:
    f = _parse_filters(arguments)
    records = await get_records(
        user_id,
        kind=f["kind"],
        category=f["category"],
        min_amount=float(f["min_amount"]) if f["min_amount"] is not None else None,
        max_amount=float(f["max_amount"]) if f["max_amount"] is not None else None,
        from_date=f["from_date"],
        to_date=f["to_date"],
    )
    debts = await get_debts(user_id)
    payload = {
        "filters": {
            "kind": f["kind"],
            "category": f["category"],
            "min_amount": f["min_amount"],
            "max_amount": f["max_amount"],
            "from_date": arguments.get("from_date"),
            "to_date": arguments.get("to_date"),
        },
        "summary": build_records_summary(records, debts),
    }
    return json.dumps({"tool": "get_records_summary", "data": payload}, ensure_ascii=False)


async def handle_delete_records(arguments: dict[str, Any], user_id: int) -> str:
    record_ids = arguments.get("record_ids") or None
    kind = (arguments.get("kind") or "").strip() or None
    category = (arguments.get("category") or "").strip() or None
    from_date = parse_date(arguments.get("from_date"))
    to_date = parse_date(arguments.get("to_date"))

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
            "kind": kind,
            "category": category,
            "from_date": arguments.get("from_date"),
            "to_date": arguments.get("to_date"),
        },
        "deleted_count": deleted,
    }
    return json.dumps({"tool": "delete_records", "data": payload}, ensure_ascii=False)


async def handle_reset_records(arguments: dict[str, Any], user_id: int) -> str:
    deleted = await delete_records(user_id)
    payload = {"deleted_count": deleted}
    return json.dumps({"tool": "reset_records", "data": payload}, ensure_ascii=False)


HANDLERS: dict[str, Any] = {
    "expense_record": handle_expense_record,
    "income_record": handle_income_record,
    "get_records": handle_get_records,
    "get_records_summary": handle_get_records_summary,
    "delete_records": handle_delete_records,
    "reset_records": handle_reset_records,
}
