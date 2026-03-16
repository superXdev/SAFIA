"""Debt tools — record, list, settle, delete."""
import json
from typing import Any

from services.database import delete_all_debts, delete_debts, get_debts, save_debt, settle_debt

SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "debt_record",
            "description": (
                "Catat utang atau piutang user. Panggil ketika user menyebut meminjam uang dari "
                "seseorang (utang/borrowed) atau meminjamkan uang ke seseorang (piutang/lent). "
                "Tool ini menyimpan data dan mengembalikan JSON."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "direction": {
                        "type": "string",
                        "enum": ["lent", "borrowed"],
                        "description": "'lent' jika user meminjamkan uang ke orang lain (piutang), 'borrowed' jika user meminjam dari orang lain (utang).",
                    },
                    "person": {
                        "type": "string",
                        "description": "Nama orang yang terkait utang/piutang.",
                    },
                    "amount": {"type": "number", "description": "Jumlah uang (angka)"},
                    "description": {
                        "type": ["string", "null"],
                        "description": "Keterangan (opsional)",
                    },
                },
                "required": ["direction", "person", "amount"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_debts",
            "description": (
                "Ambil daftar utang/piutang user. Gunakan ketika user minta lihat daftar "
                "utang atau piutang, siapa yang berutang, atau berapa total utang/piutang."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "direction": {
                        "type": ["string", "null"],
                        "enum": ["lent", "borrowed", None],
                        "description": "Filter: 'lent' (piutang) atau 'borrowed' (utang). Opsional.",
                    },
                    "person": {
                        "type": ["string", "null"],
                        "description": "Filter berdasarkan nama orang. Opsional.",
                    },
                    "is_settled": {
                        "type": ["boolean", "null"],
                        "description": "Filter: true = sudah lunas, false = belum lunas. Opsional.",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "settle_debt",
            "description": (
                "Tandai utang/piutang sebagai lunas. Gunakan ketika user menyebut sudah "
                "membayar utang atau sudah menerima pembayaran piutang."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "debt_ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "Daftar ID utang/piutang yang ingin dilunasi.",
                    },
                },
                "required": ["debt_ids"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_debt",
            "description": (
                "Hapus catatan utang/piutang user. Gunakan ketika user minta hapus "
                "catatan utang/piutang tertentu."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "debt_ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "Daftar ID utang/piutang yang ingin dihapus.",
                    },
                },
                "required": ["debt_ids"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "reset_debts",
            "description": (
                "Hapus semua data utang/piutang user (reset/erase seluruh database utang). "
                "Gunakan hanya ketika user dengan tegas minta reset atau hapus semua utang/piutang. "
                "Konfirmasi dulu sebelum memanggil."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
]


async def handle_debt_record(arguments: dict[str, Any], user_id: int) -> str:
    direction = arguments["direction"]
    person = arguments["person"].strip()
    amount = float(arguments.get("amount", 0))
    description = (arguments.get("description") or "").strip()
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
    payload = {"debt_ids": debt_ids, "settled_count": settled}
    return json.dumps({"tool": "settle_debt", "data": payload}, ensure_ascii=False)


async def handle_delete_debt(arguments: dict[str, Any], user_id: int) -> str:
    debt_ids = arguments["debt_ids"]
    deleted = await delete_debts(user_id, debt_ids)
    payload = {"debt_ids": debt_ids, "deleted_count": deleted}
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
