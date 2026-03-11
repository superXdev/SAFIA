"""In-memory expense/income records per chat (for testing)."""
from datetime import datetime, timezone

# chat_id -> list of {"type", "amount", "description", "category", "at"}
_records: dict[int, list[dict]] = {}


def expense_record(chat_id: int, amount: float, description: str = "", category: str = "") -> None:
    """Record an expense for the chat."""
    if chat_id not in _records:
        _records[chat_id] = []
    _records[chat_id].append({
        "type": "expense",
        "amount": amount,
        "description": description or "",
        "category": category or "",
        "at": datetime.now(timezone.utc).isoformat(),
    })


def income_record(chat_id: int, amount: float, description: str = "", category: str = "") -> None:
    """Record an income for the chat."""
    if chat_id not in _records:
        _records[chat_id] = []
    _records[chat_id].append({
        "type": "income",
        "amount": amount,
        "description": description or "",
        "category": category or "",
        "at": datetime.now(timezone.utc).isoformat(),
    })


def get_records(chat_id: int) -> list[dict]:
    """Return all expense/income records for the chat."""
    return _records.get(chat_id, []).copy()
