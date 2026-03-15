"""SAFIA Telegram bot — entry point."""
import asyncio
import logging

from dotenv import load_dotenv

load_dotenv()

from aiogram import Bot, Dispatcher

from config import TELEGRAM_BOT_TOKEN
from bot.handlers import register_handlers
from services.chat_history import close_redis
from services.database import close_db, init_db

logging.basicConfig(level=logging.INFO)


async def main() -> None:
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    dp = Dispatcher()
    register_handlers(dp)

    logging.info("Starting SAFIA bot...")
    try:
        await init_db()
        # Each update runs in its own asyncio task; no concurrency limit so many users can be served in parallel.
        await dp.start_polling(
            bot,
            handle_as_tasks=True,
            tasks_concurrency_limit=None,
        )
    finally:
        await close_redis()
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())
