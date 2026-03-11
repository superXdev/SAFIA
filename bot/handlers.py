"""Telegram message handlers."""
from aiogram import F, Dispatcher
from aiogram.types import Message
from aiogram.enums import ParseMode

from services.llm import chat as llm_chat
from services.storage import clear_history, get_history, save_history


async def handle_start(message: Message) -> None:
    await clear_history(message.chat.id)
    await message.answer(
        "Halo! Aku *SAFIA*, asisten AI kamu. Kirim pesan apa saja dan aku akan membantu kamu.",
        parse_mode=ParseMode.MARKDOWN,
    )


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
    reply = await llm_chat(history)
    history.append({"role": "assistant", "content": reply})
    await save_history(message.chat.id, history)

    await typing.edit_text(reply, parse_mode=ParseMode.MARKDOWN)


def register_handlers(dp: Dispatcher) -> None:
    dp.message.register(handle_start, F.text == "/start")
    dp.message.register(handle_reset, F.text == "/reset")
    dp.message.register(handle_message, F.text)
