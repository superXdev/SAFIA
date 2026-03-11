import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.enums import ParseMode
from dotenv import load_dotenv
from openai import AsyncOpenAI
import os

load_dotenv()

logging.basicConfig(level=logging.INFO)

bot = Bot(token=os.environ["TELEGRAM_BOT_TOKEN"])
dp = Dispatcher()

llm = AsyncOpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.environ["LLM_API_KEY"],
)

MODEL = "openai/gpt-oss-120b"
SYSTEM_PROMPT = "Kamu adalah SAFIA, asisten AI yang ramah dan helpful di Telegram. Selalu jawab dalam Bahasa Indonesia yang fasih dan natural. Jawab dengan ringkas dan jelas. Format respons selalu dalam Markdown (bold, italic, list, code, dll) agar mudah dibaca di Telegram."

chat_histories: dict[int, list[dict]] = {}


def get_history(chat_id: int) -> list[dict]:
    if chat_id not in chat_histories:
        chat_histories[chat_id] = [{"role": "system", "content": SYSTEM_PROMPT}]
    return chat_histories[chat_id]


@dp.message(F.text == "/start")
async def handle_start(message: Message):
    chat_histories.pop(message.chat.id, None)
    await message.answer(
        "Halo! Aku *SAFIA*, asisten AI kamu. Kirim pesan apa saja dan aku akan membantu kamu.",
        parse_mode=ParseMode.MARKDOWN,
    )


@dp.message(F.text == "/reset")
async def handle_reset(message: Message):
    chat_histories.pop(message.chat.id, None)
    await message.answer(
        "Percakapan telah direset.",
        parse_mode=ParseMode.MARKDOWN,
    )


@dp.message(F.text)
async def handle_message(message: Message):
    history = get_history(message.chat.id)
    history.append({"role": "user", "content": message.text})

    typing = await message.answer("Thinking...", parse_mode=ParseMode.MARKDOWN)

    try:
        response = await llm.chat.completions.create(
            model=MODEL,
            messages=history,
        )
        reply = response.choices[0].message.content or "..."
        is_error = False
    except Exception as e:
        logging.exception("LLM request failed")
        reply = f"Maaf, terjadi kesalahan: {e}"
        is_error = True

    history.append({"role": "assistant", "content": reply})

    if len(history) > 41:
        history[:] = [history[0]] + history[-40:]

    await typing.edit_text(
        reply,
        parse_mode=ParseMode.MARKDOWN if not is_error else None,
    )


async def main():
    logging.info("Starting SAFIA bot...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
