"""Debt tools — record, list, settle, delete."""
import json
from typing import Any

from services.database import delete_all_debts, delete_debts, get_debts, save_debt, settle_debt

MAX_PERSON_LEN = 200
MAX_DESC_LEN = 500

async def handle_debt_record(arguments: dict[str, Any], user_id: int) -> str:
    direction = arguments["direction"]
    person = arguments["person"].strip()[:MAX_PERSON_LEN]
    amount = float(arguments.get("amount", 0))
    if amount <= 0:
        return json.dumps({"tool": "debt_record", "error": "amount must be positive"}, ensure_ascii=False)
    description = (arguments.get("description") or "").strip()[:MAX_DESC_LEN]
    await save_debt(user_id, direction, person, amount, description)
    payload = {
        "direction": direction,
        "person": person,
        "amount": amount,
        "description": description,
        "status": "recorded",
    }
    return json.dumps({"tool": "debt_record", "data": payload}, ensure_ascii=False)


async def handle_get_debts(arguments: dict[str, Any], user_id: int) -> str:
    direction = (arguments.get("direction") or "").strip() or None
    person = (arguments.get("person") or "").strip() or None
    is_settled = arguments.get("is_settled")
    debts = await get_debts(
        user_id,
        direction=direction,
        person=person,
        is_settled=is_settled,
    )
    payload = {
        "filters": {"direction": direction, "person": person, "is_settled": is_settled},
        "debts": debts,
    }
    return json.dumps({"tool": "get_debts", "data": payload}, ensure_ascii=False)


async def handle_settle_debt(arguments: dict[str, Any], user_id: int) -> str:
    debt_ids = arguments["debt_ids"]
    settled = await settle_debt(user_id, debt_ids)
    payload = {"settled_count": settled}
    return json.dumps({"tool": "settle_debt", "data": payload}, ensure_ascii=False)


async def handle_delete_debt(arguments: dict[str, Any], user_id: int) -> str:
    debt_ids = arguments["debt_ids"]
    deleted = await delete_debts(user_id, debt_ids)
    payload = {"deleted_count": deleted}
    return json.dumps({"tool": "delete_debt", "data": payload}, ensure_ascii=False)


async def handle_reset_debts(arguments: dict[str, Any], user_id: int) -> str:
    deleted = await delete_all_debts(user_id)
    payload = {"deleted_count": deleted}
    return json.dumps({"tool": "reset_debts", "data": payload}, ensure_ascii=False)


HANDLERS: dict[str, Any] = {
    "debt_record": handle_debt_record,
    "get_debts": handle_get_debts,
    "settle_debt": handle_settle_debt,
    "delete_debt": handle_delete_debt,
    "reset_debts": handle_reset_debts,
}
