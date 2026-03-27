"""Background reminder execution loop."""
from __future__ import annotations

import asyncio
import json
import logging
from typing import TYPE_CHECKING

from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest

from config import REMINDER_TICK_SECONDS
from services.llm import polish_reminder_message
from services.reminders_db import (
    get_due_reminders,
    increment_reminder_fail_count,
    mark_reminder_fired,
)
from services.schedule import compute_next_run

if TYPE_CHECKING:
    from aiogram import Bot
    from services.models import Reminder


def _fmt_idr(value: int | float) -> str:
    """Format number as Indonesian Rupiah (dot thousands, e.g. Rp 1.500.000)."""
    return f"Rp {value:,.0f}".replace(",", ".")


async def _handle_price_reminder(payload: dict) -> str:
    """Fetch prices for requested symbols and format a digest."""
    from services.gold_price import fetch_gold_price_idr
    from services.market_prices import get_crypto_price, get_stock_price_indonesia
    from services.silver_price import fetch_silver_price_idr

    symbols = payload.get("symbols") or []
    asset_types = payload.get("asset_types") or []
    lines = ["**Pengingat Harga**"]

    for sym, atype in zip(symbols, asset_types):
        atype = (atype or "").lower()
        try:
            if atype == "gold":
                rows = await asyncio.to_thread(fetch_gold_price_idr)
                for r in rows:
                    if "gram" in (r.get("unit") or "").lower():
                        lines.append(f"• Emas: {_fmt_idr(r['idr'])}/gram")
                        break
            elif atype == "silver":
                data = await asyncio.to_thread(fetch_silver_price_idr)
                val = data.get("idr_per_gram", 0)
                if val:
                    lines.append(f"• Perak: {_fmt_idr(val)}/gram")
            elif atype == "crypto":
                result = await asyncio.to_thread(get_crypto_price, symbol=sym, limit=1)
                rows = result.get("data") or []
                if rows:
                    price_idr = rows[0].get("Price_IDR")
                    price_usd = rows[0].get("Price")
                    if isinstance(price_idr, (int, float)):
                        lines.append(f"• {sym}: {_fmt_idr(price_idr)}")
                    elif isinstance(price_usd, (int, float)):
                        lines.append(f"• {sym}: ${price_usd:,.2f}")
                    else:
                        lines.append(f"• {sym}: {price_idr or price_usd}")
            elif atype == "stock":
                rows = await asyncio.to_thread(get_stock_price_indonesia, query=sym, limit=1)
                if rows:
                    p = rows[0].get("Price", "N/A")
                    lines.append(f"• {sym}: {_fmt_idr(p)}" if isinstance(p, (int, float)) else f"• {sym}: {p}")
        except Exception:
            lines.append(f"• {sym}: gagal ambil harga")

    if len(lines) == 1:
        lines.append("Tidak ada simbol yang dikonfigurasi.")
    return "\n".join(lines)


async def _handle_news_reminder(payload: dict) -> str:
    from services.news import search_financial_news

    query = payload.get("query", "berita keuangan Indonesia hari ini")
    answer = await search_financial_news(query)
    return f"**Pengingat Berita**\n{answer}"


def _handle_note_reminder(title: str, kind: str) -> str:
    label = "pengeluaran" if kind == "note_expense" else "pemasukan"
    return (
        f"**Pengingat Catat {label.title()}**\n"
        f"Hai! Jangan lupa catat {label} kamu hari ini. "
        f"Cukup ketik nominal dan keterangan, aku bantu simpan."
    )


async def _handle_portfolio_reminder(user_id: int) -> str:
    from services.summaries import get_portfolio_summary

    data = await get_portfolio_summary(user_id)
    summary = data.get("summary", {})
    total = summary.get("total_value", 0)
    alloc = summary.get("allocation_percent", {})
    lines = [
        "**Ringkasan Portofolio**",
        f"Total nilai: {_fmt_idr(total)}",
    ]
    for atype, pct in alloc.items():
        lines.append(f"• {atype}: {pct}%")
    return "\n".join(lines)


async def _execute_reminder(reminder: Reminder) -> str | None:
    """Dispatch reminder by kind and return the message to send."""
    kind = reminder.kind
    payload = json.loads(reminder.payload or "{}")

    if kind == "price":
        return await _handle_price_reminder(payload)
    if kind == "news":
        return await _handle_news_reminder(payload)
    if kind in ("note_expense", "note_income"):
        return _handle_note_reminder(reminder.title, kind)
    if kind == "portfolio_digest":
        return await _handle_portfolio_reminder(reminder.user_id)
    if kind == "custom":
        return payload.get("message") or reminder.title
    return None


async def _process_due_reminders(bot: Bot) -> None:
    """Find and execute all due reminders."""
    reminders = await get_due_reminders()
    for reminder in reminders:
        try:
            message = await _execute_reminder(reminder)
            if message:
                message = await polish_reminder_message(
                    message,
                    kind=reminder.kind,
                    title=reminder.title or "",
                )
                try:
                    await bot.send_message(
                        chat_id=reminder.user_id,
                        text=message,
                        parse_mode=ParseMode.MARKDOWN,
                    )
                except TelegramBadRequest:
                    await bot.send_message(
                        chat_id=reminder.user_id,
                        text=message,
                    )
            next_run = compute_next_run(reminder.schedule, reminder.timezone)
            await mark_reminder_fired(reminder.id, next_run)
        except Exception:
            logging.exception("Reminder %d execution failed", reminder.id)
            await increment_reminder_fail_count(reminder.id)


async def run_reminder_loop(bot: Bot) -> None:
    """Background loop that checks and fires due reminders every tick."""
    logging.info("Reminder loop started (tick=%ds)", REMINDER_TICK_SECONDS)
    while True:
        try:
            await _process_due_reminders(bot)
        except Exception:
            logging.exception("Reminder tick failed")
        await asyncio.sleep(REMINDER_TICK_SECONDS)
