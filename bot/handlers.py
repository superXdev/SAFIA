"""Telegram message handlers."""
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
from services.document_vision import extract_document_text, parse_final_amount
from config import LLM_CHAT_API_KEY


def _build_status_updater(progress_message: Message) -> Callable[[str], Awaitable[None]]:
    last_text = ""
    last_at = 0.0

    async def _update(text: str) -> None:
        nonlocal last_text, last_at
        now = monotonic()
        if not text or text == last_text:
            return
        # avoid rapid edit bursts when multiple tools run quickly
        if now - last_at < 0.8:
            return
        try:
            await progress_message.edit_text(text, parse_mode=ParseMode.MARKDOWN)
            last_text = text
            last_at = now
        except Exception:
            return

    return _update


async def handle_start(message: Message) -> None:
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
        f"Halo{name_part}! Aku *SAFIA*, teman chat untuk urusan *uang kamu*.\n\n"
        "*Bisa apa?*\n"
        "• Catat pemasukan, pengeluaran, dan investasi (saham, emas, crypto, dll.)\n"
        "• Tanya *harga* atau *kurs* (contoh: emas hari ini, Bitcoin, dollar ke rupiah)\n"
        "• Bantu *hutang*, tabungan, tanya seputar berita/edukasi uang, sampai *pengingat* rutin\n\n"
        "*Gimana pakainya?* Ketik teks, kirim suara, atau foto struk/slip yang jelas.\n\n"
        "/start = mulai ulang dari awal\n"
        "/bantuan = info singkat & batas pemakaian\n\n"
        "Ada pertanyaan atau mau cerita? Langsung kirim saja 🙂"
    )

    await message.answer(text, parse_mode=ParseMode.MARKDOWN)


async def handle_bantuan(message: Message) -> None:
    text = (
        "*Bantuan SAFIA*\n\n"
        "*Perintah*\n"
        "/start — mulai ulang percakapan\n"
        "/bantuan — pesan ini\n\n"
        "*Kirim pesan*\n"
        "• *Teks* — tanya atau cerita soal uang, investasi, harga, kurs, dll.\n"
        "• *Suara* — direkam jadi teks, lalu dibalas seperti chat biasa\n"
        "• *Foto* — struk atau slip yang jelas (aku bantu baca isinya)\n\n"
        "*Batas:* maksimal *25 pesan per hari* per akun (reset tiap hari).\n\n"
        "*Tip:* tulis jumlah uang dan tanggal dengan jelas supaya catatan tepat."
    )
    await message.answer(text, parse_mode=ParseMode.MARKDOWN)


async def handle_message(message: Message) -> None:
    allowed, remaining = await check_and_increment_rate_limit(message.from_user.id)
    if not allowed:
        await message.answer(
            "Kamu sudah mencapai batas 25 pesan hari ini.\n"
            "Coba lagi besok ya, atau reset percakapan jika perlu.",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    history = await get_history(message.chat.id)
    history.append({"role": "user", "content": message.text or ""})

    typing = await message.answer("Berpikir...", parse_mode=ParseMode.MARKDOWN)
    reply = await llm_chat(
        history,
        message.from_user.id,
        status_callback=_build_status_updater(typing),
    )
    history.append({"role": "assistant", "content": reply})
    await save_history(message.chat.id, history)

    await typing.edit_text(reply, parse_mode=ParseMode.MARKDOWN)


async def handle_voice(message: Message) -> None:
    allowed, remaining = await check_and_increment_rate_limit(message.from_user.id)
    if not allowed:
        await message.answer(
            "Kamu sudah mencapai batas 25 pesan hari ini.\n"
            "Coba lagi besok ya, atau reset percakapan jika perlu.",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    typing = await message.answer("Mendengarkan...", parse_mode=ParseMode.MARKDOWN)

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
            "Maaf, tidak bisa mengenali suara. Coba lagi.",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    history = await get_history(message.chat.id)
    history.append({"role": "user", "content": text})

    await typing.edit_text("Berpikir...", parse_mode=ParseMode.MARKDOWN)
    reply = await llm_chat(
        history,
        message.from_user.id,
        status_callback=_build_status_updater(typing),
    )
    history.append({"role": "assistant", "content": reply})
    await save_history(message.chat.id, history)

    await typing.edit_text(reply, parse_mode=ParseMode.MARKDOWN)


async def handle_photo(message: Message) -> None:
    if not LLM_CHAT_API_KEY:
        await message.answer(
            "Fitur foto dokumen belum diaktifkan. Hubungi admin.",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    allowed, remaining = await check_and_increment_rate_limit(message.from_user.id)
    if not allowed:
        await message.answer(
            "Kamu sudah mencapai batas 25 pesan hari ini.\n"
            "Coba lagi besok ya, atau reset percakapan jika perlu.",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    typing = await message.answer("Memproses gambar...", parse_mode=ParseMode.MARKDOWN)

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
            "Tidak bisa membaca dokumen dari foto ini. Kirim foto invoice, slip gaji, atau catatan yang jelas.",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    # Parse calculated final amount so we record the correct number (net salary, receipt total after discounts, etc.)
    final_amount = parse_final_amount(extracted)
    amount_hint = ""
    if final_amount is not None and final_amount > 0:
        amount_hint = f"\n\n**Gunakan angka ini saat mencatat (jumlah final yang sudah dihitung): Rp {final_amount:,.0f}**. Jangan pakai subtotal atau total kotor."
    # Use extracted text as user context and get SAFIA's reply
    user_context = f"[Isi dokumen dari foto yang dikirim user]\n{extracted}{amount_hint}"
    history = await get_history(message.chat.id)
    history.append({"role": "user", "content": user_context})

    await typing.edit_text("Berpikir...", parse_mode=ParseMode.MARKDOWN)
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
