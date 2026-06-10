"""Safe message sending helpers with Markdown sanitization via telegramify-markdown."""
import logging
from typing import Any

from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message
from telegramify_markdown import markdownify


def _sanitize(text: str) -> str:
    """Convert standard markdown to Telegram MarkdownV2, escaping broken syntax."""
    try:
        return markdownify(text, normalize_whitespace=True)
    except Exception:
        logging.debug("telegramify-markdown failed, returning raw text")
        return text


async def safe_reply(message: Message, text: str, **kwargs: Any) -> Message:
    safe = _sanitize(text)
    try:
        return await message.answer(safe, parse_mode=ParseMode.MARKDOWN_V2, **kwargs)
    except TelegramBadRequest:
        logging.debug("MarkdownV2 parse error in reply, falling back to plain text")
        return await message.answer(text, **kwargs)


async def safe_edit(message: Message, text: str, **kwargs: Any) -> Message:
    safe = _sanitize(text)
    try:
        return await message.edit_text(safe, parse_mode=ParseMode.MARKDOWN_V2, **kwargs)
    except TelegramBadRequest:
        logging.debug("MarkdownV2 parse error in edit, falling back to plain text")
        try:
            return await message.edit_text(text, **kwargs)
        except TelegramBadRequest:
            return message


async def safe_send(bot: Any, chat_id: int, text: str, **kwargs: Any) -> Message:
    safe = _sanitize(text)
    try:
        return await bot.send_message(chat_id, safe, parse_mode=ParseMode.MARKDOWN_V2, **kwargs)
    except TelegramBadRequest:
        logging.debug("MarkdownV2 parse error in send, falling back to plain text")
        return await bot.send_message(chat_id, text, **kwargs)
