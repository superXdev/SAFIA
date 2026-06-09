# SAFIA

An AI-powered Telegram bot for personal finance. Chat naturally to track expenses, manage debts, monitor investments, get market data, and search financial news — all in one place.

Runs entirely on your machine: SQLite for data, Qdrant on-disk for document search, ONNX for local embeddings. No cloud dependencies besides the LLM API and Firecrawl.

## Features

- **Expense & income tracking** — record, filter, and review financial transactions via natural chat
- **Debt management** — track money lent/borrowed with settlement status
- **Investment portfolio** — record and manage stocks, crypto, gold, and other assets with real-time pricing
- **Portfolio rebalancing** — get suggestions based on target allocation percentages
- **Market data** — live gold, silver, crypto, and currency exchange rates
- **Financial news** — search relevant Indonesian financial news
- **Auto reminders** — scheduled price alerts, news digests, portfolio summaries (daily/weekly/monthly/interval)
- **Habit-based suggestions** — reminder suggestions inferred from user behavior patterns
- **Document scanning** — send photos of receipts to auto-extract and record amounts
- **Voice messages** — speak instead of type, powered by Whisper (Groq)
- **Daily rate limiting** — 1000 messages per user per day (configurable)
- **Admin dashboard** — web UI with metrics, user registry, and knowledge base management
- **Knowledge base (RAG)** — upload PDF/TXT/DOCX for document-grounded responses

## Quick Install

**Linux / macOS:**

```bash
curl -fsSL https://raw.githubusercontent.com/superXdev/SAFIA/main/install.sh | bash
```

The installer handles everything: Git, uv, Python 3.12, Redis (auto-installed if missing), dependencies, and the `safia` CLI command. **No Docker required.**

**Windows (PowerShell):**

```powershell
iex (irm https://raw.githubusercontent.com/superXdev/SAFIA/main/install.ps1)
```

The installer checks for Git, Python, uv (auto-installs uv if missing), and Redis. **Redis must be installed separately** — use [Memurai](https://memurai.com/), [WSL](https://learn.microsoft.com/windows/wsl/install), or Docker (`docker run -d -p 6379:6379 --name safia-redis redis:7-alpine`).

After install:

```bash
safia setup      # Interactive wizard — creates .env
safia start      # Start bot + admin dashboard as background daemons
```

The daemon auto-starts on reboot (systemd on Linux, launchd on macOS, Scheduled Tasks on Windows).

## `safia` CLI

| Command | Description |
|---|---|
| `safia setup` | Run the interactive setup wizard |
| `safia config` | View and edit configuration |
| `safia start` | Start bot + admin dashboard daemons |
| `safia stop` | Stop both daemons |
| `safia restart` | Restart both daemons |
| `safia status` | Show daemon status |
| `safia logs [N]` | Show recent logs (default 30 lines) |
| `safia test` | Run the test suite |
| `safia update` | Pull latest changes, update deps, restart |
| `safia uninstall` | Remove SAFIA completely |

## Architecture — local-first

SAFIA runs entirely on your machine. No cloud dependencies for core features:

| Component | Technology | Location |
|---|---|---|
| LLM chat | Lunos / Groq / OpenAI / Custom | Remote API |
| Speech-to-text | Whisper (Groq) | Remote API |
| Embeddings | fastembed + ONNX (384d, multilingual) | **Local** — `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` |
| Vector storage | Qdrant on-disk | **Local** — `data/qdrant/` |
| Database | SQLite (default) or PostgreSQL | **Local** |
| Cache & rate limiting | Redis | **Local** — auto-installed by installer |
| Admin UI | Flask + Chart.js | **Local** — `http://127.0.0.1:5454` |
| Bot daemon | systemd / launchd / Scheduled Tasks | **Local** — auto-start on boot |

The embedding model (~120 MB) downloads once and runs on CPU via ONNX Runtime. Qdrant stores vectors directly to disk — no separate server or Docker container needed.

For remote Qdrant, set `QDRANT_URL` in `.env`. To use a remote embedding API, set `EMBEDDING_LOCAL=false`.

## Manual Setup

If you prefer not to use the installer:

```bash
git clone https://github.com/superXdev/SAFIA.git
cd SAFIA
uv sync
uv run python scripts/setup.py
```

Create `.env` manually:

```
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
LLM_PROVIDER=lunos
LLM_API_KEY=your-api-key
DATABASE_URL=sqlite+aiosqlite:///data/safia.db
REDIS_URL=redis://localhost:6379/0
```

**Knowledge base** works out of the box with local defaults — no extra config needed. To customize:

```
# Optional: switch to remote Qdrant
QDRANT_URL=http://127.0.0.1:6333

# Optional: switch to remote embeddings
EMBEDDING_LOCAL=false
EMBEDDING_BASE_URL=https://openrouter.ai/api/v1
EMBEDDING_API_KEY=your-key
EMBEDDING_MODEL=openai/text-embedding-3-small
EMBEDDING_VECTOR_SIZE=1536

# Chunking (word-based)
KB_CHUNK_WORDS=450
KB_CHUNK_OVERLAP_WORDS=70
```

**Admin dashboard auth:**

```
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-strong-password
FLASK_SECRET_KEY=random-string
```

## Running Manually

```bash
uv run python main.py              # Bot
uv run python admin_dashboard.py   # Admin UI (http://127.0.0.1:5454)
uv run python run_dev.py           # Dev mode with auto-reload
```

## Commands

| Command | Description |
|---|---|
| `/start` | Start bot and reset chat |

All other interactions happen through natural conversation — just chat normally.

## Tech Stack

| Component | Technology |
|---|---|
| Bot framework | aiogram 3.x |
| LLM | Lunos / Groq / OpenAI / Custom (OpenAI-compatible API) |
| Vision | LLM provider (same as chat) |
| Speech-to-text | Whisper (Groq) |
| Database | SQLite / PostgreSQL + SQLAlchemy (async) |
| Cache / rate limit | Redis |
| Admin UI | Flask + Chart.js |
| Embeddings | fastembed (ONNX, local) |
| Vector DB | Qdrant (on-disk, local) |
| Package manager | uv |

## License

GNU Affero General Public License v3.0 (AGPL-3.0) or any later version.
