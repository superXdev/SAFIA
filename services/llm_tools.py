"""LLM tool definitions and execution for expense/income recording."""
import logging

from services.db import (
    get_records_for_chat,
    save_expense_record,
    save_income_record,
)

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "expense_record",
            "description": "Catat pengeluaran (expense) user. Panggil ketika user menyebut mengeluarkan uang atau pengeluaran.",
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {"type": "number", "description": "Jumlah uang (angka)"},
                    "description": {"type": "string", "description": "Keterangan (opsional)"},
                    "category": {"type": "string", "description": "Nama kategori (opsional), misal: Makanan, Transport, Gaji, Bonus"},
                },
                "required": ["amount"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "income_record",
            "description": "Catat pemasukan (income) user. Panggil ketika user menyebut menerima uang atau pemasukan.",
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {"type": "number", "description": "Jumlah uang (angka)"},
                    "description": {"type": "string", "description": "Keterangan (opsional)"},
                    "category": {"type": "string", "description": "Nama kategori (opsional), misal: Makanan, Transport, Gaji, Bonus"},
                },
                "required": ["amount"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_records",
            "description": "Tampilkan ringkasan catatan pemasukan dan pengeluaran user. Panggil ketika user minta lihat riwayat/laporan keuangan. Saat menyampaikan hasil ke user, tampilkan dalam bentuk list sederhana (bullet), jangan pakai tabel.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]


def _format_record_confirm(amount: float, kind: str, category: str, description: str) -> str:
    """Build confirmation message for expense/income record."""
    label = "Pengeluaran" if kind == "expense" else "Pemasukan"
    parts = [f"{label} Rp{amount:,.0f}"]
    if category:
        parts.append(f"kategori {category}")
    if description:
        parts.append(f"({description})")
    return " ".join(parts) + " berhasil dicatat."


def _format_records_list(records: list[dict]) -> str:
    """Format get_records output as a simple list for the LLM."""
    lines = ["*Catatan keuangan:*"]
    total_income = total_expense = 0.0
    for r in records:
        amt = r["amount"]
        cat = r.get("category", "").strip()
        desc = (r.get("description") or "").strip()
        detail = " — ".join(filter(None, [cat, desc]))
        if r["type"] == "income":
            total_income += amt
            lines.append(f"• Pemasukan: Rp{amt:,.0f}" + (f" ({detail})" if detail else ""))
        else:
            total_expense += amt
            lines.append(f"• Pengeluaran: Rp{amt:,.0f}" + (f" ({detail})" if detail else ""))
    lines.append("")
    lines.append(f"Total pemasukan: Rp{total_income:,.0f}")
    lines.append(f"Total pengeluaran: Rp{total_expense:,.0f}")
    return "\n".join(lines)


async def run_tool(name: str, arguments: dict, chat_id: int) -> str:
    """Execute a tool by name and return result string for the LLM."""
    try:
        if name == "expense_record":
            amount = float(arguments.get("amount", 0))
            description = (arguments.get("description") or "").strip()
            category = (arguments.get("category") or "").strip()
            await save_expense_record(chat_id, amount, description, category)
            return _format_record_confirm(amount, "expense", category, description)
        if name == "income_record":
            amount = float(arguments.get("amount", 0))
            description = (arguments.get("description") or "").strip()
            category = (arguments.get("category") or "").strip()
            await save_income_record(chat_id, amount, description, category)
            return _format_record_confirm(amount, "income", category, description)
        if name == "get_records":
            records = await get_records_for_chat(chat_id)
            if not records:
                return "Belum ada catatan pemasukan/pengeluaran."
            return _format_records_list(records)
    except Exception:
        logging.exception("Tool execution failed")
        return "Error saat menjalankan tool."
    return "Unknown tool."
