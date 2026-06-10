"""Safe message sending helpers with HTML fallback."""
import logging
from typing import Any

from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message


async def safe_reply(message: Message, text: str, **kwargs: Any) -> Message:
    """Reply with HTML, fallback to plain text on parse error."""
    try:
        return await message.answer(text, parse_mode=ParseMode.HTML, **kwargs)
    except TelegramBadRequest:
        logging.debug("HTML parse error in reply, falling back to plain text")
        return await message.answer(text, **kwargs)


async def safe_edit(message: Message, text: str, **kwargs: Any) -> Message:
    """Edit with HTML, fallback to plain text on parse error."""
    try:
        return await message.edit_text(text, parse_mode=ParseMode.HTML, **kwargs)
    except TelegramBadRequest:
        logging.debug("HTML parse error in edit, falling back to plain text")
        try:
            return await message.edit_text(text, **kwargs)
        except TelegramBadRequest:
            return message


async def safe_send(bot: Any, chat_id: int, text: str, **kwargs: Any) -> Message:
    """Send with HTML, fallback to plain text on parse error."""
    try:
        return await bot.send_message(chat_id, text, parse_mode=ParseMode.HTML, **kwargs)
    except TelegramBadRequest:
        logging.debug("HTML parse error in send, falling back to plain text")
        return await bot.send_message(chat_id, text, **kwargs)
