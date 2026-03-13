"""App configuration from env and constants."""
import os

# Bot
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]

# LLM (Groq)
LLM_API_KEY = os.environ["LLM_API_KEY"]
LLM_BASE_URL = "https://api.groq.com/openai/v1"
MODEL = "openai/gpt-oss-120b"
SYSTEM_PROMPT = (
    "Kamu adalah SAFIA, asisten AI yang ramah dan helpful di Telegram. "
    "Selalu jawab dalam Bahasa Indonesia yang fasih dan natural. "
    "Jawab dengan ringkas dan jelas. Format respons selalu dalam Markdown "
    "(bold, italic, list, code, dll) agar mudah dibaca di Telegram. "
    "Setelah memanggil tool (catat pemasukan/pengeluaran atau tampilkan riwayat), "
    "wajib beri respons singkat ke user yang relevan dengan hasil tool (misal konfirmasi atau ringkasan). "
    "Saat menampilkan catatan keuangan (riwayat pemasukan/pengeluaran), gunakan hanya format list sederhana (bullet • atau -). Jangan gunakan tabel."
)

# Redis chat history
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
CHAT_KEY_PREFIX = "safia:chat:"
MAX_CHAT_MESSAGES = 10  # 5 conversations (5 user + 5 assistant)
HISTORY_TTL_SECONDS = 2 * 60 * 60  # 2 hours

# Database (PostgreSQL via async SQLAlchemy)
# Example: postgresql+asyncpg://user:password@localhost:5432/safia
DATABASE_URL = os.environ["DATABASE_URL"]
