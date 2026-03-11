# SAFIA

A simple AI-powered Telegram chatbot that responds in fluent Indonesian, built with [aiogram](https://docs.aiogram.dev/) and [Groq](https://groq.com/).

## Setup

1. **Clone the repo** and install dependencies:

   ```bash
   uv sync
   ```

2. **Configure environment variables** — copy `.env.example` or create a `.env` file:

   ```
   LLM_API_KEY=your-groq-api-key
   TELEGRAM_BOT_TOKEN=your-telegram-bot-token
   ```

   - Get a Groq API key at [console.groq.com](https://console.groq.com/)
   - Get a Telegram bot token from [@BotFather](https://t.me/BotFather)

3. **Run the bot:**

   ```bash
   uv run main.py
   ```

## Commands

| Command  | Description                        |
|----------|------------------------------------|
| `/start` | Start the bot and reset chat       |
| `/reset` | Clear conversation history         |

## License

MIT
