# SAFIA

Personal finance AI assistant on Telegram, built for Indonesian users. Tracks expenses, manages investment portfolios, and provides financial education — all in casual Bahasa Indonesia.

Built with [aiogram 3](https://docs.aiogram.dev/), [Groq](https://groq.com/), and PostgreSQL.

## Features

- **Expense & income tracking** — record, filter, and review financial transactions via natural chat
- **Debt management** — track money lent/borrowed with settlement status
- **Investment portfolio** — record and manage stocks, crypto, gold, and other assets with real-time pricing
- **Portfolio rebalancing** — get suggestions based on target allocation percentages
- **Market data** — live gold, silver, crypto, and currency exchange rates
- **Financial news** — search relevant Indonesian financial news
- **Document scanning** — send photos of receipts, invoices, or pay slips to auto-extract and record amounts
- **Voice messages** — speak instead of type, powered by Whisper transcription
- **Daily rate limiting** — 25 messages per user per day (configurable)
- **Admin dashboard** — web UI with user registry, daily metrics, and usage charts
- **Knowledge base (RAG)** — upload PDF/TXT/DOCX in the admin UI; chunks are embedded and stored in **Qdrant**; the bot can call `knowledge_search` to answer from those documents

## Setup

1. Install dependencies:

   ```bash
   uv sync
   ```

2. Create a `.env` file:

   ```
   TELEGRAM_BOT_TOKEN=your-telegram-bot-token
   GROQ_API_KEY=your-groq-api-key
   OPENROUTER_API_KEY=your-openrouter-api-key
   DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/safia
   SERPAPI_KEY=your-serpapi-key
   ```

   **Knowledge base (optional):** run [Qdrant](https://qdrant.tech/) (for example `docker run -p 6333:6333 qdrant/qdrant`) and set:

   ```
   QDRANT_URL=http://127.0.0.1:6333
   QDRANT_API_KEY=
   EMBEDDING_BASE_URL=https://openrouter.ai/api/v1
   EMBEDDING_API_KEY=your-openrouter-key
   EMBEDDING_MODEL=openai/text-embedding-3-small
   EMBEDDING_VECTOR_SIZE=1536
   ```

   `EMBEDDING_API_KEY` defaults to `OPENROUTER_API_KEY` if unset. Adjust `EMBEDDING_MODEL` / `EMBEDDING_VECTOR_SIZE` to match your provider. Chunks are **word-based** (default **450** words per chunk, **70** word overlap); tune with `KB_CHUNK_WORDS` and `KB_CHUNK_OVERLAP_WORDS`. Protect the admin UI with HTTP Basic Auth:

   ```
   ADMIN_USERNAME=admin
   ADMIN_PASSWORD=your-strong-password
   FLASK_SECRET_KEY=random-string-for-flash-messages
   ```

3. Run the bot:

   ```bash
   uv run python main.py
   ```

4. Run the admin dashboard (optional):

   ```bash
   uv run python admin_dashboard.py
   ```

   Opens at `http://127.0.0.1:5454`.

## Commands

| Command  | Description              |
|----------|--------------------------|
| `/start` | Start bot and reset chat |

All other interactions happen through natural conversation — just chat normally.

## Tech Stack

| Component       | Technology                          |
|-----------------|-------------------------------------|
| Bot framework   | aiogram 3.x                        |
| LLM             | Groq (OpenAI-compatible API)        |
| Vision          | OpenRouter                          |
| Speech-to-text  | Whisper (via Groq)                  |
| Database        | PostgreSQL + SQLAlchemy (async)     |
| Cache / rate limit | Redis                            |
| Admin UI        | Flask + Chart.js                    |
| Knowledge RAG   | Qdrant + OpenAI-compatible embeddings |
| Package manager | uv                                  |

## License

This project is licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0)** or any later version.

See the `LICENSE` file for details.
