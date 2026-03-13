"""SAFIA Telegram bot — entry point."""
import asyncio
import logging

from dotenv import load_dotenv

load_dotenv()

from aiogram import Bot, Dispatcher

from config import TELEGRAM_BOT_TOKEN
from bot.handlers import register_handlers
from services.storage import close_redis
from services.db import close_db, init_db

logging.basicConfig(level=logging.INFO)


async def main() -> None:
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    dp = Dispatcher()
    register_handlers(dp)

    logging.info("Starting SAFIA bot...")
    try:
        await init_db()
        await dp.start_polling(bot)
    finally:
        await close_redis()
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())
