# AGENTS.md

## Quick commands

```bash
# First-time setup wizard
uv run python scripts/setup.py

# Manage configuration (change token, provider, model, etc.)
uv run python scripts/config.py

# Dev mode (auto-reload on file changes)
uv run python run_dev.py

# Bot directly
uv run python main.py

# Admin dashboard (http://127.0.0.1:5454)
uv run python admin_dashboard.py

# Production admin dashboard (gunicorn)
./scripts/start_admin_dashboard_prod.sh
```

No tests, linter, formatter, or typechecker are configured.

## Runtime prerequisites

- **Redis** — **required**. Used for chat history storage and rate limiting. The bot will fail at startup without a running Redis instance.
- **SQLite** (default, zero-config) or **PostgreSQL** — database is auto-created at startup via `init_db()`. Defaults to `data/safia.db`; set `DATABASE_URL` to use PostgreSQL instead.
- **Qdrant** — optional. Only needed for the knowledge base (RAG) feature.
- `.env` file — **required**. Must exist before running. `main.py` and `admin_dashboard.py` both call `load_dotenv()` as their first action.

## Architecture

```
main.py              → Telegram bot entrypoint (aiogram 3.x polling)
admin_dashboard.py   → Flask admin web UI entrypoint
config/__init__.py   → all env vars and constants (edit, not .env, to change defaults)
config/prompt.py     → SYSTEM_PROMPT strings (model-agnostic, edit for bot behavior)
bot/handlers.py      → Telegram message/voice/photo handlers
services/llm.py      → Chat completions (provider-agnostic via LLM_PROVIDER), tool-calling loop (max 5 rounds), Whisper transcription
services/tools/      → LLM function-calling tool definitions and handlers (11 modules)
services/database.py → async SQLAlchemy helpers (CRUD for users, records, debts, assets, metrics, KB)
services/models.py   → SQLAlchemy ORM models (declarative, all in one file)
services/chat_history.py → Redis-backed history + rate limiting (25 msg/user/day, UTC midnight reset)
services/reminder_runner.py → background asyncio task (runs in bot process, polls REMINDER_TICK_SECONDS)
services/schedule.py → computes next run from daily/weekly/monthly/interval schedule JSON
services/knowledge/  → Qdrant vector ingest/search, word-based chunking
admin/routes.py      → Flask blueprint (HTTP Basic Auth, KB upload, metrics dashboard)
admin/templates/     → Jinja templates for admin UI
```

Key patterns:
- The bot process runs everything: polling, reminder loop (asyncio task), tool execution. No separate workers.
- Admin dashboard uses its own asyncio event loop (`_loop` in `admin/routes.py:32`) for DB calls.
- `load_dotenv()` must be called **before importing config** — both entrypoints do this.
- Database functions use `AsyncSessionMaker()` directly as a context manager. `get_session()` exists but is rarely used.
- The LLM tool loop (`services/llm.py:132`) prepends date/time to the system message each turn so the model knows "today."
- SQLite engine uses `check_same_thread=False` and WAL journal mode (set at startup in `init_db()`).
- `update_asset()` manually sets `updated_at` — SQLite has no server-side `ON UPDATE` support.

## Conventions

- **Language**: All user-facing text is in Bahasa Indonesia. System prompt, tool output, and replies use IDR format with dot thousands (Rp 1.500.000).
- **KISS**: This is a rapid-development project. No premature abstractions, no design patterns. Prefer simple solutions. See `.cursor/rules/coding-principles.mdc` for full guidelines.
- **aiogram v3 only** — never use v2 APIs.
- **Fully async** — all I/O uses `async/await`.
- **Import order**: stdlib → third-party → local, separated by blank lines.
- **Type hints** on function signatures, skip on obvious locals.
- **Error handling**: try/except only around external calls; log with `logging.exception()`; return user-friendly fallback strings, never tracebacks.

## Environment variables

### AI Provider (new unified system)

`LLM_PROVIDER` (`lunos`|`groq`|`openai`|`custom`, default=`lunos`) selects the chat/completions backend.
`LLM_API_KEY` is the unified key for the chosen provider.
`LLM_BASE_URL` is required only for `custom`.

Backward compat: if only `GROQ_API_KEY` is set (no `LLM_PROVIDER`), the system auto-defaults to `groq`.

Model selection: `LLM_MODEL` (default `openai/gpt-oss-120b`).

**Whisper transcription** always uses Groq (`GROQ_API_KEY`). Without it, voice messages are disabled.
**Document vision** uses the same provider as chat (`LLM_CHAT_API_KEY`). Without an API key, photo scanning is disabled.

### All env vars

Critical: `TELEGRAM_BOT_TOKEN`, `LLM_API_KEY`, `DATABASE_URL`, `REDIS_URL`.
Optional for voice: `GROQ_API_KEY`.
Optional for photos: `VISION_MODEL` (default `mistralai/mistral-small-3.2-24b-instruct`).
Optional for admin: `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `FLASK_SECRET_KEY`.
Optional for Qdrant/RAG: `QDRANT_URL`, `EMBEDDING_BASE_URL`, `EMBEDDING_API_KEY`, `EMBEDDING_MODEL`, `EMBEDDING_VECTOR_SIZE`.
Reminder tuning: `REMINDER_ENABLED`, `REMINDER_MAX_PER_USER`, `REMINDER_MAX_SENDS_PER_DAY`, `REMINDER_TICK_SECONDS`.

## Rate limiting

25 messages per user per day. Counted in Redis (`safia:rate:{user_id}:{date}`), expires at UTC midnight. The handler rejects before processing; the `check_and_increment_rate_limit` call counts the message regardless.

## Reminders

- Run as a background `asyncio.create_task` inside the bot process (not a separate worker).
- `REMINDER_TICK_SECONDS` (default 30) controls how often the loop checks for due reminders.
- After 5 consecutive failures, a reminder auto-disables.
- Reminders use `dedupe_key` (unique constraint) to prevent duplicates.
- The `polish_reminder_message` call rewrites raw reminder output through the LLM for natural Telegram formatting.

## Knowledge base

- Chunks are word-based (default 450 words, 70 word overlap), not character/token-based.
- Only `.pdf`, `.txt`, `.docx` accepted. Max upload 200 MB (configurable).
- Vector storage in Qdrant; metadata in PostgreSQL (`kb_documents` table).
- Deleting a document requires removing both the Qdrant vectors and PostgreSQL metadata row.
