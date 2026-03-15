"""LLM client and chat completion with tool calling."""
import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

from openai import AsyncOpenAI

from config import LLM_API_KEY, LLM_BASE_URL, MODEL
from services.tools import TOOLS, run_tool

_client: AsyncOpenAI | None = None

MAX_TOOL_ROUNDS = 5

# WIB = UTC+7
WIB = timezone(timedelta(hours=7))


def get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(base_url=LLM_BASE_URL, api_key=LLM_API_KEY)
    return _client


async def transcribe(audio_path: Path) -> str:
    """Transcribe audio file to text using Groq Whisper."""
    try:
        client = get_client()
        with open(audio_path, "rb") as f:
            result = await client.audio.transcriptions.create(
                file=f,
                model="whisper-large-v3",
                language="id",
            )
        return result.text
    except Exception:
        logging.exception("Transcription failed")
        return ""


async def chat(messages: list[dict], user_id: int) -> str:
    """Send messages to LLM; run tools if requested; return final assistant reply."""
    try:
        client = get_client()
        current = list(messages)
        # Inject current date/time into system message so the model knows "today" (once per turn)
        if current and current[0].get("role") == "system":
            now = datetime.now(WIB)
            time_line = f"\n\n**Tanggal dan waktu saat ini (untuk konteks):** {now.strftime('%d %B %Y, %H:%M')} WIB."
            current[0] = {"role": "system", "content": (current[0].get("content") or "") + time_line}

        for _ in range(MAX_TOOL_ROUNDS):
            response = await client.chat.completions.create(
                model=MODEL,
                messages=current,
                tools=TOOLS,
            )
            msg = response.choices[0].message

            if not msg.tool_calls:
                return msg.content or "..."

            current.append(msg)
            for tc in msg.tool_calls:
                name = tc.function.name
                args = json.loads(tc.function.arguments or "{}")
                result = await run_tool(name, args, user_id)
                current.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result,
                    }
                )

        return "Maaf, terlalu banyak langkah. Coba lagi."
    except Exception:
        logging.exception("LLM request failed")
        return "Maaf, terjadi kesalahan. Coba lagi nanti."
