"""Telegram message handlers."""
from aiogram import F, Dispatcher
from aiogram.types import Message
from aiogram.enums import ParseMode

from services.llm import chat as llm_chat
from services.chat_history import clear_history, get_history, save_history
from services.database import get_or_create_user


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
        f"Halo{name_part}! Aku *SAFIA*, asisten keuangan pribadi dan manajer kekayaan kamu. \n\n"
        "- Bantu catat pemasukan/pengeluaran harian.\n"
        "- Bantu catat dan rebalance aset (saham, emas, crypto, dll).\n"
        "- Bantu review kebiasaan belanja biar nggak boncos.\n"
        "- Jelasin konsep keuangan/investasi pakai referensi regulasi & berita yang kredibel.\n\n"
        "Tinggal ceritakan kondisi keuangan atau pertanyaan kamu, aku bantu pilihin langkah yang paling masuk akal. 🙂"
    )

    await message.answer(text, parse_mode=ParseMode.MARKDOWN)


async def handle_reset(message: Message) -> None:
    await clear_history(message.chat.id)
    await message.answer(
        "Percakapan telah direset.",
        parse_mode=ParseMode.MARKDOWN,
    )


async def handle_message(message: Message) -> None:
    history = await get_history(message.chat.id)
    history.append({"role": "user", "content": message.text or ""})

    typing = await message.answer("Thinking...", parse_mode=ParseMode.MARKDOWN)
    reply = await llm_chat(history, message.from_user.id)
    history.append({"role": "assistant", "content": reply})
    await save_history(message.chat.id, history)

    await typing.edit_text(reply, parse_mode=ParseMode.MARKDOWN)


def register_handlers(dp: Dispatcher) -> None:
    dp.message.register(handle_start, F.text == "/start")
    dp.message.register(handle_reset, F.text == "/reset")
    dp.message.register(handle_message, F.text)
