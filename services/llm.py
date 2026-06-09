"""LLM client and chat completion with tool calling."""
import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Awaitable, Callable

import httpx
from openai import (
    APIError,
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    AsyncOpenAI,
    BadRequestError,
    RateLimitError,
)

from config import GROQ_API_KEY, GROQ_BASE_URL, LLM_CHAT_API_KEY, LLM_CHAT_BASE_URL, LLM_MODEL as MODEL
from services.chat_history import mark_user_active_today
from services.database import increment_daily_metrics
from services.summaries import get_financial_summary, get_portfolio_summary
from services.tools import TOOLS, run_tool

_client: AsyncOpenAI | None = None
_groq_client: AsyncOpenAI | None = None

MAX_TOOL_ROUNDS = 5


class _SafeTransport(httpx.AsyncHTTPTransport):
    """Transport that neutralizes headers blocked by certain AI providers (e.g. Lunos)."""

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        # Lunos blocks requests carrying OpenAI SDK's default UA and Accept headers.
        request.headers["user-agent"] = "SAFIA/1.0"
        request.headers["x-app-id"] = "SAFIA"
        request.headers.pop("accept", None)
        return await super().handle_async_request(request)


def _make_httpx_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        transport=_SafeTransport(),
        timeout=httpx.Timeout(600.0, connect=10.0),
    )

# WIB = UTC+7
WIB = timezone(timedelta(hours=7))

REMINDER_POLISH_MAX_INPUT_CHARS = 4000
REMINDER_POLISH_MAX_OUTPUT_TOKENS = 380

_REMINDER_POLISH_SYSTEM = """Kamu adalah SAFIA — asisten keuangan di Telegram.
Tugas: ubah "isi mentah pengingat" jadi satu pesan singkat untuk user. Balas dalam bahasa yang sama dengan isi mentah pengingat.

Aturan:
- Santai dan natural, 2–5 kalimat ATAU paling banyak 6 bullet (• atau -), satu ide per baris.
- Jangan ulang heading kaku seperti template; boleh satu **label** pendek di awal jika perlu.
- Pertahankan angka, harga, simbol, dan fakta dari isi mentah. Jangan tambah janji imbal hasil atau saran investasi baru.
- **Format angka**: Rupiah pakai titik ribuan (Rp 1.500.000). USD tetap gaya internasional ($67,350). Crypto kecil boleh desimal panjang (0,00045 BTC). Persen dua desimal (12,50%).
- Tanpa tabel Markdown (|). Tanpa # heading. Tanpa boilerplate "Hai" panjang.
- Hanya keluarkan teks pesan siap kirim, tanpa penjelasan di luar pesan."""

_REMINDER_KIND_LABEL_ID: dict[str, str] = {
    "price": "pengingat cek harga aset",
    "news": "pengingat ringkasan berita",
    "note_expense": "pengingat catat pengeluaran",
    "note_income": "pengingat catat pemasukan",
    "portfolio_digest": "pengingat ringkasan portofolio",
    "custom": "pengingat kustom",
}

_EXTERNAL_TOOL_STATUS_TEXT: dict[str, str] = {
    "news_search_macro": "Searching latest news...",
    "knowledge_search": "Searching documents...",
    "get_stock_price": "Fetching stock price...",
    "get_forex_price": "Fetching forex rate...",
    "get_crypto_price": "Fetching crypto price...",
    "get_top_crypto_market_cap": "Fetching crypto market data...",
    "get_coin_detail": "Fetching coin details...",
    "get_trending_crypto": "Fetching trending crypto...",
    "search_crypto": "Searching crypto assets...",
    "get_gold_price": "Fetching gold price...",
    "get_silver_price": "Fetching silver price...",
    "get_currency_rate": "Fetching exchange rate...",
    "expense_record": "Logging expense...",
    "income_record": "Logging income...",
    "asset_record": "Recording asset...",
    "asset_sell": "Processing sale...",
    "debt_record": "Logging debt...",
    "reminder_create": "Setting up reminder...",
}


def _tool_status_text(tool_name: str) -> str:
    return _EXTERNAL_TOOL_STATUS_TEXT.get(tool_name, "Processing...")


async def _build_financial_context(user_id: int) -> str:
    """Fetch and format a compact financial snapshot for injection into the system prompt.
    Returns empty string if there is no data or on error."""
    try:
        fin = await get_financial_summary(user_id)
        port = await get_portfolio_summary(user_id)
        parts: list[str] = []

        if fin["total_income"] > 0 or fin["total_expense"] > 0:
            balance = fin["total_balance"]
            parts.append(
                f"Balance: Rp {fin['total_balance']:,.0f} "
                f"(income Rp {fin['total_income']:,.0f}, expense Rp {fin['total_expense']:,.0f})"
            )
            if fin["per_category"]:
                top = sorted(fin["per_category"].items(), key=lambda x: x[1], reverse=True)[:5]
                cats = ", ".join(f"{c}: Rp {v:,.0f}" for c, v in top)
                parts.append(f"Top categories: {cats}")
            if fin["total_lent_outstanding"] > 0:
                parts.append(f"Outstanding lent: Rp {fin['total_lent_outstanding']:,.0f}")
            if fin["total_borrowed_outstanding"] > 0:
                parts.append(f"Outstanding borrowed: Rp {fin['total_borrowed_outstanding']:,.0f}")

        port_summary = port.get("summary", {})
        if port_summary.get("total_value", 0) > 0:
            alloc = ", ".join(
                f"{k}: {v}%" for k, v in port_summary.get("allocation_percent", {}).items()
            )
            parts.append(
                f"Portfolio: Rp {port_summary['total_value']:,.0f} "
                f"in {port_summary.get('asset_count', 0)} assets ({alloc})"
            )

        if not parts:
            return ""
        return "\n\n**Your current financial snapshot (use this to personalize responses):**\n" + "\n".join(f"- {p}" for p in parts)
    except Exception:
        logging.debug("Failed to build financial context for user %s", user_id)
        return ""


def get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            base_url=LLM_CHAT_BASE_URL,
            api_key=LLM_CHAT_API_KEY,
            http_client=_make_httpx_client(),
        )
    return _client


def get_groq_client() -> AsyncOpenAI:
    """Whisper transcription client — always uses Groq (requires GROQ_API_KEY)."""
    global _groq_client
    if _groq_client is None:
        _groq_client = AsyncOpenAI(base_url=GROQ_BASE_URL, api_key=GROQ_API_KEY)
    return _groq_client


async def polish_reminder_message(draft: str, *, kind: str, title: str = "") -> str:
    """Rewrite reminder draft text to be short and natural for Telegram. No tools."""
    text = (draft or "").strip()
    if not text:
        return text
    if not LLM_CHAT_API_KEY:
        return text

    if len(text) > REMINDER_POLISH_MAX_INPUT_CHARS:
        text = text[: REMINDER_POLISH_MAX_INPUT_CHARS].rstrip() + "\n…"

    kind_label = _REMINDER_KIND_LABEL_ID.get(kind, kind)
    user_content = (
        f"Jenis: {kind_label}\n"
        f"Judul pengingat: {title or '-'}\n\n"
        f"Isi mentah:\n{text}"
    )

    try:
        client = get_client()
        response = await client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": _REMINDER_POLISH_SYSTEM},
                {"role": "user", "content": user_content},
            ],
            max_tokens=REMINDER_POLISH_MAX_OUTPUT_TOKENS,
            temperature=0.55,
        )
        out = (response.choices[0].message.content or "").strip()
        return out if out else draft
    except (AuthenticationError, RateLimitError, APIConnectionError, APITimeoutError) as e:
        logging.warning("Reminder polish skipped (API error): %s", e)
        return draft
    except Exception:
        logging.exception("Reminder polish unexpected error")
        return draft


async def transcribe(audio_path: Path) -> str:
    """Transcribe audio file to text using Groq Whisper."""
    if not GROQ_API_KEY:
        logging.warning("Transcription skipped: GROQ_API_KEY not set")
        return ""
    try:
        client = get_groq_client()
        with open(audio_path, "rb") as f:
            result = await client.audio.transcriptions.create(
                file=f,
                model="whisper-large-v3",
            )
        return result.text
    except (AuthenticationError, RateLimitError, APIConnectionError, APITimeoutError) as e:
        logging.error("Transcription API error: %s", e)
        return ""
    except Exception:
        logging.exception("Transcription unexpected error")
        return ""


async def chat(
    messages: list[dict],
    user_id: int,
    status_callback: Callable[[str], Awaitable[None]] | None = None,
) -> str:
    """Send messages to LLM; run tools if requested; return final assistant reply."""
    client = get_client()
    current = list(messages)
    total_tokens = 0

    # Inject current date/time and financial context into system message
    if current and current[0].get("role") == "system":
        now = datetime.now(WIB)
        time_line = f"\n\nCurrent date and time: {now.strftime('%A, %d %B %Y, %H:%M')} WIB (UTC+7)."
        ctx = await _build_financial_context(user_id)
        current[0] = {"role": "system", "content": current[0].get("content") + time_line + ctx}

    try:
        for round_num in range(1, MAX_TOOL_ROUNDS + 1):
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
            last_status: str | None = None

            for tc in msg.tool_calls:
                name = tc.function.name
                if status_callback:
                    status = _tool_status_text(name)
                    if status != last_status:
                        await status_callback(status)
                        last_status = status

                try:
                    args = json.loads(tc.function.arguments or "{}")
                except json.JSONDecodeError:
                    current.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps({"error": "Invalid arguments JSON"}),
                    })
                    continue

                result = await run_tool(name, args, user_id)
                current.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result,
                })

        return "I need more steps to complete this. Could you simplify or break down your request?"

    except AuthenticationError:
        logging.error("LLM authentication failed — check LLM_API_KEY")
        return "I'm having trouble authenticating. Please contact the admin to verify the API key."
    except RateLimitError:
        logging.warning("LLM rate limited")
        return "I'm receiving too many requests right now. Give me a moment and try again."
    except APITimeoutError:
        logging.error("LLM request timed out")
        return "The request timed out. The service might be busy — please try again."
    except APIConnectionError as e:
        logging.error("LLM connection error: %s", e)
        return "I can't reach the AI service right now. Please check your network or try again later."
    except BadRequestError as e:
        logging.error("LLM bad request: %s", e)
        return "Something went wrong with the request format. The admin may need to adjust settings."
    except Exception:
        logging.exception("LLM unexpected error")
        return "An unexpected error occurred. Please try again."
