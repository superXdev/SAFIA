"""App configuration from env and constants."""
import os

from config.prompt import SYSTEM_PROMPT

# -----------------------------------------------------------------------------
# Bot
# -----------------------------------------------------------------------------
# Optional for admin dashboard; mandatory for bot runtime.
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")

# -----------------------------------------------------------------------------
# AI Provider (Lunos / Groq / OpenAI / custom)
# -----------------------------------------------------------------------------
# LLM_PROVIDER: lunos (default), groq, openai, or custom
# For backward compat: if only GROQ_API_KEY is set without LLM_PROVIDER, default to groq.
_LLM_PROVIDER_EXPLICIT = "LLM_PROVIDER" in os.environ
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "lunos")
LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "")  # only for custom provider
LLM_MODEL = os.environ.get("LLM_MODEL", "openai/gpt-oss-120b")

# Legacy keys (kept for backward compat and Whisper)
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

# If user has GROQ_API_KEY but no explicit LLM_PROVIDER or LLM_API_KEY, stay on groq
if not _LLM_PROVIDER_EXPLICIT and GROQ_API_KEY and not LLM_API_KEY:
    LLM_PROVIDER = "groq"

# Resolve effective chat base URL
if LLM_PROVIDER == "lunos":
    LLM_CHAT_BASE_URL = "https://api.lunosrouter.com/v1"
elif LLM_PROVIDER == "groq":
    LLM_CHAT_BASE_URL = "https://api.groq.com/openai/v1"
elif LLM_PROVIDER == "openai":
    LLM_CHAT_BASE_URL = "https://api.openai.com/v1"
else:
    LLM_CHAT_BASE_URL = LLM_BASE_URL

# Effective chat API key (unified key, falls back to GROQ_API_KEY)
LLM_CHAT_API_KEY = LLM_API_KEY or GROQ_API_KEY

# -----------------------------------------------------------------------------
# Document vision — optional, for photo/document extraction.
# Uses the same LLM provider as chat (LLM_CHAT_BASE_URL + LLM_CHAT_API_KEY).
# -----------------------------------------------------------------------------
VISION_MODEL = os.environ.get("VISION_MODEL", "mistralai/mistral-small-3.2-24b-instruct")

# -----------------------------------------------------------------------------
# Cache TTLs and keys
# -----------------------------------------------------------------------------
# Gold/silver price — 6 hours
PRICE_CACHE_TTL_SECONDS = 6 * 60 * 60
PRICE_CACHE_KEY_GOLD = "safia:price:gold"
PRICE_CACHE_KEY_SILVER = "safia:price:silver"

# Currency rate — 1 hour per pair
RATE_CACHE_TTL_SECONDS = 60 * 60
RATE_CACHE_KEY_PREFIX = "safia:rate:"
USDIDR_CACHE_TTL_SECONDS = RATE_CACHE_TTL_SECONDS
PRICE_CACHE_KEY_USDIDR = "safia:price:usdidr"

# Market data (stock / forex / crypto)
MARKET_CACHE_TTL_STOCK_SECONDS = 10 * 60   # 10 min
MARKET_CACHE_TTL_FOREX_SECONDS = 5 * 60    # 5 min
MARKET_CACHE_TTL_CRYPTO_SECONDS = 2 * 60   # 2 min
COINGECKO_CACHE_TTL_MARKETS = 5 * 60       # 5 min
COINGECKO_CACHE_TTL_COIN = 10 * 60         # 10 min
COINGECKO_CACHE_TTL_TRENDING = 15 * 60     # 15 min
COINGECKO_CACHE_TTL_SEARCH = 60 * 60       # 1 hour

# -----------------------------------------------------------------------------
# Chat history
# -----------------------------------------------------------------------------
MAX_CHAT_MESSAGES = 10   # 5 user + 5 assistant
HISTORY_TTL_SECONDS = 2 * 60 * 60  # 2 hours

# -----------------------------------------------------------------------------
# Rate limiting
# -----------------------------------------------------------------------------
DAILY_MESSAGE_LIMIT = 1000
RATE_LIMIT_KEY_PREFIX = "safia:rate:"

# -----------------------------------------------------------------------------
# Database
# -----------------------------------------------------------------------------
# Database — defaults to SQLite at data/safia.db (zero-config).
# For PostgreSQL: postgresql+asyncpg://user:pass@host:5432/safia
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///data/safia.db")

# -----------------------------------------------------------------------------
# Qdrant (knowledge base vectors) — local file storage by default
# -----------------------------------------------------------------------------
QDRANT_PATH = os.environ.get("QDRANT_PATH", "data/qdrant")
QDRANT_URL = os.environ.get("QDRANT_URL", "")
QDRANT_API_KEY = os.environ.get("QDRANT_API_KEY", "") or None
KB_COLLECTION_NAME = os.environ.get("KB_COLLECTION_NAME", "safia_kb")
MEMORY_COLLECTION_NAME = os.environ.get("MEMORY_COLLECTION_NAME", "safia_user_memories")
MEMORY_SEARCH_LIMIT = 5
MEMORY_SCORE_THRESHOLD = float(os.environ.get("MEMORY_SCORE_THRESHOLD", "0.45"))

# -----------------------------------------------------------------------------
# Embeddings — local (fastembed) by default; set EMBEDDING_LOCAL=false for remote
# -----------------------------------------------------------------------------
EMBEDDING_LOCAL = os.environ.get("EMBEDDING_LOCAL", "true").lower() in ("true", "1", "yes")
EMBEDDING_LOCAL_MODEL = os.environ.get(
    "EMBEDDING_LOCAL_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)
EMBEDDING_BASE_URL = os.environ.get("EMBEDDING_BASE_URL", "https://api.lunosrouter.com/v1")
EMBEDDING_API_KEY = os.environ.get("EMBEDDING_API_KEY", "") or os.environ.get("LLM_API_KEY", "")
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "openai/text-embedding-3-small")
EMBEDDING_VECTOR_SIZE = int(os.environ.get("EMBEDDING_VECTOR_SIZE", "384"))

# -----------------------------------------------------------------------------
# External API endpoints
# -----------------------------------------------------------------------------
GROQ_BASE_URL = os.environ.get("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
FIRECRAWL_API_KEY = os.environ.get("FIRECRAWL_API_KEY", "")
COINGECKO_BASE_URL = os.environ.get("COINGECKO_BASE_URL", "https://api.coingecko.com/api/v3")
COINGECKO_API_KEY = os.environ.get("COINGECKO_API_KEY", "")
GOLD_PRICE_URL = os.environ.get("GOLD_PRICE_URL", "https://harga-emas.org/")
SILVER_PRICE_URL = os.environ.get("SILVER_PRICE_URL", "https://id.bullion-rates.com/silver/IDR/spot-price.htm")
CURRENCY_RATE_URL = os.environ.get("CURRENCY_RATE_URL", "https://api.frankfurter.app/latest")

# -----------------------------------------------------------------------------
# Knowledge base ingest
# -----------------------------------------------------------------------------
# Knowledge chunks are word-based (split on whitespace), not characters.
KB_CHUNK_WORDS = int(os.environ.get("KB_CHUNK_WORDS", "450"))
KB_CHUNK_OVERLAP_WORDS = int(os.environ.get("KB_CHUNK_OVERLAP_WORDS", "70"))
KB_UPLOAD_DIR = os.environ.get("KB_UPLOAD_DIR", "data/kb_uploads")
KB_MAX_UPLOAD_MB = int(os.environ.get("KB_MAX_UPLOAD_MB", "200"))
KB_EMBED_BATCH_SIZE = int(os.environ.get("KB_EMBED_BATCH_SIZE", "32"))

# -----------------------------------------------------------------------------
# Reminders
# -----------------------------------------------------------------------------
REMINDER_ENABLED = os.environ.get("REMINDER_ENABLED", "true").lower() in ("true", "1", "yes")
REMINDER_MAX_PER_USER = int(os.environ.get("REMINDER_MAX_PER_USER", "10"))
REMINDER_MAX_SENDS_PER_DAY = int(os.environ.get("REMINDER_MAX_SENDS_PER_DAY", "15"))
REMINDER_TICK_SECONDS = int(os.environ.get("REMINDER_TICK_SECONDS", "30"))

# -----------------------------------------------------------------------------
# Admin HTTP Basic Auth (set both to protect the dashboard)
# -----------------------------------------------------------------------------
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")
