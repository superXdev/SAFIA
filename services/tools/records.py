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
from services.tools._helpers import parse_date

SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "expense_record",
            "description": (
                "Catat pengeluaran (expense) user. Panggil ketika user menyebut mengeluarkan uang "
                "atau pengeluaran. Tool ini hanya menyimpan data mentah dan mengembalikan JSON; "
                "kamu yang harus menjelaskan ke user dengan gaya yang natural."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {"type": "number", "description": "Jumlah uang (angka)"},
                    "description": {
                        "type": ["string", "null"],
                        "description": "Keterangan (opsional)",
                    },
                    "category": {
                        "type": ["string", "null"],
                        "description": "Nama kategori (opsional), misal: Makanan, Transport, Gaji, Bonus",
                    },
                },
                "required": ["amount"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "income_record",
            "description": (
                "Catat pemasukan (income) user. Panggil ketika user menyebut menerima uang atau "
                "pemasukan. Tool ini hanya menyimpan data mentah dan mengembalikan JSON; "
                "kamu yang harus menjelaskan ke user dengan gaya yang natural."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {"type": "number", "description": "Jumlah uang (angka)"},
                    "description": {
                        "type": ["string", "null"],
                        "description": "Keterangan (opsional)",
                    },
                    "category": {
                        "type": ["string", "null"],
                        "description": "Nama kategori (opsional), misal: Makanan, Transport, Gaji, Bonus",
                    },
                },
                "required": ["amount"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_records",
            "description": (
                "Ambil catatan pemasukan/pengeluaran user dengan filter opsional dan kembalikan "
                "data mentah dalam bentuk JSON. Gunakan ketika user minta lihat riwayat/laporan "
                "keuangan detail (misal berdasarkan rentang tanggal, jenis income/expense, kategori, "
                "atau rentang jumlah uang), lalu jelaskan hasilnya dengan bahasamu sendiri."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "kind": {
                        "type": ["string", "null"],
                        "description": "Jenis catatan yang ingin diambil: 'income' atau 'expense'. Opsional.",
                    },
                    "category": {
                        "type": ["string", "null"],
                        "description": "Filter berdasarkan kategori tertentu. Opsional.",
                    },
                    "min_amount": {
                        "type": ["number", "null"],
                        "description": "Jumlah minimum (>=). Opsional.",
                    },
                    "max_amount": {
                        "type": ["number", "null"],
                        "description": "Jumlah maksimum (<=). Opsional.",
                    },
                    "from_date": {
                        "type": ["string", "null"],
                        "description": "Tanggal mulai (YYYY-MM-DD). Opsional.",
                    },
                    "to_date": {
                        "type": ["string", "null"],
                        "description": "Tanggal akhir (YYYY-MM-DD). Opsional.",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_records_summary",
            "description": (
                "Ambil ringkasan agregat keuangan user: total pemasukan, total pengeluaran, "
                "saldo bersih (net), total_balance (saldo keseluruhan termasuk utang/piutang), "
                "ringkasan per kategori, serta total piutang dan utang yang belum lunas. "
                "Gunakan ketika user minta cek saldo, analisis kebiasaan keuangan, atau ringkasan "
                "periode tertentu, lalu jelaskan hasilnya dengan bahasamu sendiri."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "kind": {
                        "type": ["string", "null"],
                        "description": "Jenis catatan yang ingin diringkas: 'income' atau 'expense'. Opsional.",
                    },
                    "category": {
                        "type": ["string", "null"],
                        "description": "Filter berdasarkan kategori tertentu. Opsional.",
                    },
                    "min_amount": {
                        "type": ["number", "null"],
                        "description": "Jumlah minimum (>=). Opsional.",
                    },
                    "max_amount": {
                        "type": ["number", "null"],
                        "description": "Jumlah maksimum (<=). Opsional.",
                    },
                    "from_date": {
                        "type": ["string", "null"],
                        "description": "Tanggal mulai (YYYY-MM-DD). Opsional.",
                    },
                    "to_date": {
                        "type": ["string", "null"],
                        "description": "Tanggal akhir (YYYY-MM-DD). Opsional.",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_records",
            "description": (
                "Hapus catatan pemasukan/pengeluaran user. Bisa hapus berdasarkan ID spesifik, "
                "jenis (income/expense), kategori, atau rentang tanggal. Gunakan ketika user "
                "minta hapus catatan tertentu. Selalu konfirmasi dulu sebelum menghapus, dan "
                "laporkan berapa catatan yang terhapus."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "record_ids": {
                        "type": ["array", "null"],
                        "items": {"type": "integer"},
                        "description": "Daftar ID catatan yang ingin dihapus. Opsional.",
                    },
                    "kind": {
                        "type": ["string", "null"],
                        "description": "Jenis catatan yang ingin dihapus: 'income' atau 'expense'. Opsional.",
                    },
                    "category": {
                        "type": ["string", "null"],
                        "description": "Hapus catatan berdasarkan kategori tertentu. Opsional.",
                    },
                    "from_date": {
                        "type": ["string", "null"],
                        "description": "Tanggal mulai (YYYY-MM-DD). Opsional.",
                    },
                    "to_date": {
                        "type": ["string", "null"],
                        "description": "Tanggal akhir (YYYY-MM-DD). Opsional.",
                    },
                },
            },
        },
    },
]


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


def _build_summary(records: list[dict], debts: list[dict]) -> dict[str, Any]:
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
    # Lent = cash left pocket, borrowed = cash entered pocket
    # Settled lent = cash returned, settled borrowed = cash paid back
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
    description = (arguments.get("description") or "").strip()
    category = (arguments.get("category") or "").strip()
    await save_expense_record(user_id, amount, description, category)
    payload = _build_record_confirm(amount, "expense", category, description)
    return json.dumps({"tool": "expense_record", "data": payload}, ensure_ascii=False)


async def handle_income_record(arguments: dict[str, Any], user_id: int) -> str:
    amount = float(arguments.get("amount", 0))
    description = (arguments.get("description") or "").strip()
    category = (arguments.get("category") or "").strip()
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
        "summary": _build_summary(records, debts),
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
            "record_ids": record_ids,
            "kind": kind,
            "category": category,
            "from_date": arguments.get("from_date"),
            "to_date": arguments.get("to_date"),
        },
        "deleted_count": deleted,
    }
    return json.dumps({"tool": "delete_records", "data": payload}, ensure_ascii=False)


HANDLERS: dict[str, Any] = {
    "expense_record": handle_expense_record,
    "income_record": handle_income_record,
    "get_records": handle_get_records,
    "get_records_summary": handle_get_records_summary,
    "delete_records": handle_delete_records,
}
