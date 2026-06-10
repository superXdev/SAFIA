"""Safe message sending helpers with Markdown fallback."""
import logging
from typing import Any

from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message


async def safe_reply(message: Message, text: str, **kwargs: Any) -> Message:
    """Reply with MARKDOWN, fallback to plain text on parse error."""
    try:
        return await message.answer(text, parse_mode=ParseMode.MARKDOWN, **kwargs)
    except TelegramBadRequest:
        logging.debug("Markdown parse error in reply, falling back to plain text")
        return await message.answer(text, **kwargs)


async def safe_edit(message: Message, text: str, **kwargs: Any) -> Message:
    """Edit with MARKDOWN, fallback to plain text on parse error."""
    try:
        return await message.edit_text(text, parse_mode=ParseMode.MARKDOWN, **kwargs)
    except TelegramBadRequest:
        logging.debug("Markdown parse error in edit, falling back to plain text")
        try:
            return await message.edit_text(text, **kwargs)
        except TelegramBadRequest:
            return message


async def safe_send(bot: Any, chat_id: int, text: str, **kwargs: Any) -> Message:
    """Send with MARKDOWN, fallback to plain text on parse error."""
    try:
        return await bot.send_message(chat_id, text, parse_mode=ParseMode.MARKDOWN, **kwargs)
    except TelegramBadRequest:
        logging.debug("Markdown parse error in send, falling back to plain text")
        return await bot.send_message(chat_id, text, **kwargs)
