"""SAFIA Telegram bot — entry point."""
import asyncio
import logging

from dotenv import load_dotenv

load_dotenv()

from aiogram import Bot, Dispatcher

from config import REMINDER_ENABLED, TELEGRAM_BOT_TOKEN
from bot.handlers import register_handlers
from services.chat_history import close_redis
from services.database import close_db, init_db

logging.basicConfig(level=logging.INFO)


async def main() -> None:
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    dp = Dispatcher()
    register_handlers(dp)

    logging.info("Starting SAFIA bot...")
    reminder_task = None
    try:
        await init_db()

        if REMINDER_ENABLED:
            from services.reminder_runner import run_reminder_loop
            reminder_task = asyncio.create_task(run_reminder_loop(bot))

        await dp.start_polling(
            bot,
            handle_as_tasks=True,
            tasks_concurrency_limit=None,
        )
    finally:
        if reminder_task:
            reminder_task.cancel()
        await close_redis()
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())
