"""LLM client and chat completion with tool calling."""
import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

from openai import AsyncOpenAI

from config import GROQ_API_KEY, MODEL
from services.chat_history import mark_user_active_today
from services.database import increment_daily_metrics
from services.tools import TOOLS, run_tool

_client: AsyncOpenAI | None = None
_groq_client: AsyncOpenAI | None = None

MAX_TOOL_ROUNDS = 5

# WIB = UTC+7
WIB = timezone(timedelta(hours=7))


def get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(base_url="https://api.groq.com/openai/v1", api_key=GROQ_API_KEY)
    return _client


def get_groq_client() -> AsyncOpenAI:
    global _groq_client
    if _groq_client is None:
        _groq_client = AsyncOpenAI(base_url="https://api.groq.com/openai/v1", api_key=GROQ_API_KEY)
    return _groq_client


async def transcribe(audio_path: Path) -> str:
    """Transcribe audio file to text using Groq Whisper."""
    try:
        client = get_groq_client()
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
        total_tokens = 0
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

            usage = response.usage
            if usage is not None:
                if getattr(usage, "total_tokens", None) is not None:
                    total_tokens += int(usage.total_tokens)
                else:
                    prompt_tokens = getattr(usage, "prompt_tokens", 0) or 0
                    completion_tokens = getattr(usage, "completion_tokens", 0) or 0
                    total_tokens += int(prompt_tokens) + int(completion_tokens)
            msg = response.choices[0].message

            if not msg.tool_calls:
                is_new_today = await mark_user_active_today(user_id)
                await increment_daily_metrics(
                    messages_delta=1,
                    tokens_delta=total_tokens,
                    active_users_delta=1 if is_new_today else 0,
                )
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
