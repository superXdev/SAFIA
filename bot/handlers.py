"""Telegram message handlers."""
import logging
import tempfile
from pathlib import Path
from time import monotonic
from typing import Awaitable, Callable

from aiogram import F, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.enums import ParseMode

from services.llm import chat as llm_chat, transcribe
from services.chat_history import (
    check_and_increment_rate_limit,
    clear_history,
    get_history,
    save_history,
)
from services.database import get_or_create_user
from services.db_settings import is_user_allowed
from services.document_vision import extract_document_text, parse_final_amount
from config import LLM_CHAT_API_KEY


async def _check_access(user_id: int) -> bool:
    """Return True if user is allowed. Send rejection message if not."""
    if await is_user_allowed(user_id):
        return True
    return False


async def _reject_unauthorized(message: Message) -> None:
    uid = message.from_user.id if message.from_user else "unknown"
    await message.answer(
        "Access denied — you are not authorized to use this bot.\n\n"
        f"Your Telegram ID: `{uid}`\n\n"
        "Share this ID with the bot owner to request access.",
        parse_mode=ParseMode.MARKDOWN,
    )


def _build_status_updater(progress_message: Message) -> Callable[[str], Awaitable[None]]:
    last_text = ""
    last_at = 0.0

    async def _update(text: str) -> None:
        nonlocal last_text, last_at
        now = monotonic()
        if not text or text == last_text:
            return
        if now - last_at < 0.6:
            return
        try:
            await progress_message.edit_text(text, parse_mode=ParseMode.MARKDOWN)
            last_text = text
            last_at = now
        except Exception:
            logging.debug("Status update edit failed (message may have been deleted)")

    return _update


async def handle_start(message: Message) -> None:
    if not await _check_access(message.from_user.id):
        await _reject_unauthorized(message)
        return

    await clear_history(message.chat.id)

    user = message.from_user
    if user:
        await get_or_create_user(
            telegram_id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            username=user.username,
        )

    first_name = user.first_name if user and user.first_name else None
    name_part = f" {first_name}" if first_name else ""

    text = (
        f"Hi{name_part}! I'm *SAFIA*, your personal finance chat companion.\n\n"
        "*What can I do?*\n"
        "- Track income, expenses, and investments (stocks, gold, crypto, etc.)\n"
        "- Check *prices* or *exchange rates* (e.g. gold today, Bitcoin, USD to IDR)\n"
        "- Help with *debt*, savings, financial news, education, and *reminders*\n\n"
        "*How to use?* Send text, voice, or a clear photo of a receipt/payslip.\n\n"
        "/start = restart conversation\n"
        "/bantuan = quick info & limits\n\n"
        "Got questions? Just send a message 🙂"
    )

    await message.answer(text, parse_mode=ParseMode.MARKDOWN)


async def handle_bantuan(message: Message) -> None:
    text = (
        "*SAFIA Help*\n\n"
        "*Commands*\n"
        "/start — restart conversation\n"
        "/bantuan — this message\n\n"
        "*Send*\n"
        "- *Text* — ask about money, investments, prices, exchange rates, etc.\n"
        "- *Voice* — transcribed to text, then answered like a regular chat\n"
        "- *Photo* — clear receipt or payslip (I'll read the contents)\n\n"
        "*Limit:* max *25 messages per day* per account (resets daily).\n\n"
        "*Tip:* write amounts and dates clearly for accurate records."
    )
    await message.answer(text, parse_mode=ParseMode.MARKDOWN)


async def handle_message(message: Message) -> None:
    if not await _check_access(message.from_user.id):
        await _reject_unauthorized(message)
        return

    allowed, remaining = await check_and_increment_rate_limit(message.from_user.id)
    if not allowed:
        await message.answer(
            "You've reached the daily limit of 25 messages.\n"
            "Please try again tomorrow, or reset the conversation if needed.",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    history = await get_history(message.chat.id)
    history.append({"role": "user", "content": message.text or ""})

    thinking = await message.answer("Thinking...", parse_mode=ParseMode.MARKDOWN)
    reply = await llm_chat(
        history,
        message.from_user.id,
        status_callback=_build_status_updater(thinking),
    )
    history.append({"role": "assistant", "content": reply})
    await save_history(message.chat.id, history)
    await thinking.edit_text(reply, parse_mode=ParseMode.MARKDOWN)


async def handle_voice(message: Message) -> None:
    if not await _check_access(message.from_user.id):
        await _reject_unauthorized(message)
        return
    allowed, remaining = await check_and_increment_rate_limit(message.from_user.id)
    if not allowed:
        await message.answer(
            "You've reached the daily limit of 25 messages.\n"
            "Please try again tomorrow, or reset the conversation if needed.",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    typing = await message.answer("Listening...", parse_mode=ParseMode.MARKDOWN)

    file = await message.bot.get_file(message.voice.file_id)
    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
        tmp_path = Path(tmp.name)
        await message.bot.download_file(file.file_path, tmp_path)

    try:
        text = await transcribe(tmp_path)
    finally:
        tmp_path.unlink(missing_ok=True)

    if not text:
        await typing.edit_text(
            "Sorry, I couldn't understand the audio. Please try again.",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    history = await get_history(message.chat.id)
    history.append({"role": "user", "content": text})

    await typing.edit_text("Thinking...", parse_mode=ParseMode.MARKDOWN)
    reply = await llm_chat(
        history,
        message.from_user.id,
        status_callback=_build_status_updater(typing),
    )
    history.append({"role": "assistant", "content": reply})
    await save_history(message.chat.id, history)

    await typing.edit_text(reply, parse_mode=ParseMode.MARKDOWN)


async def handle_photo(message: Message) -> None:
    if not await _check_access(message.from_user.id):
        await _reject_unauthorized(message)
        return

    if not LLM_CHAT_API_KEY:
        await message.answer(
            "Document photo scanning is not enabled. Contact admin.",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    allowed, remaining = await check_and_increment_rate_limit(message.from_user.id)
    if not allowed:
        await message.answer(
            "You've reached the daily limit of 25 messages.\n"
            "Please try again tomorrow, or reset the conversation if needed.",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    typing = await message.answer("Scanning document...", parse_mode=ParseMode.MARKDOWN)

    # Telegram sends multiple sizes; use the largest
    photo = message.photo[-1]
    file = await message.bot.get_file(photo.file_id)
    suffix = ".jpg" if file.file_path and "png" not in file.file_path else ".png"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp_path = Path(tmp.name)
        await message.bot.download_file(file.file_path, tmp_path)

    try:
        extracted = await extract_document_text(tmp_path)
    finally:
        tmp_path.unlink(missing_ok=True)

    if not extracted or extracted.lower().startswith("not a document"):
        await typing.edit_text(
            "Couldn't read a document from this photo. Send a clear photo of an invoice, payslip, or receipt.",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    # Parse calculated final amount so we record the correct number (net salary, receipt total after discounts, etc.)
    final_amount = parse_final_amount(extracted)
    amount_hint = ""
    if final_amount is not None and final_amount > 0:
        amount_hint = f"\n\n**Use this calculated final amount when recording: Rp {final_amount:,.0f}**. Do not use subtotals or gross totals."
    # Use extracted text as user context and get SAFIA's reply
    user_context = f"[Document content extracted from photo]\n{extracted}{amount_hint}"
    history = await get_history(message.chat.id)
    history.append({"role": "user", "content": user_context})

    await typing.edit_text("Thinking...", parse_mode=ParseMode.MARKDOWN)
    reply = await llm_chat(
        history,
        message.from_user.id if message.from_user else 0,
        status_callback=_build_status_updater(typing),
    )
    history.append({"role": "assistant", "content": reply})
    await save_history(message.chat.id, history)

    await typing.edit_text(reply, parse_mode=ParseMode.MARKDOWN)


def register_handlers(dp: Dispatcher) -> None:
    dp.message.register(handle_start, F.text == "/start")
    dp.message.register(handle_bantuan, Command("bantuan"))
    dp.message.register(handle_voice, F.voice)
    dp.message.register(handle_photo, F.photo)
    dp.message.register(handle_message, F.text)
