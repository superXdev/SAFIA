"""App configuration from env and constants."""
import os

from config.prompt import SYSTEM_PROMPT

# -----------------------------------------------------------------------------
# Bot
# -----------------------------------------------------------------------------
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]

# -----------------------------------------------------------------------------
# LLM (Groq)
# -----------------------------------------------------------------------------
LLM_API_KEY = os.environ["LLM_API_KEY"]
LLM_BASE_URL = "https://api.groq.com/openai/v1"
MODEL = "openai/gpt-oss-120b"

# -----------------------------------------------------------------------------
# Document vision (OpenRouter) — optional, for photo/document extraction
# -----------------------------------------------------------------------------
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
VISION_MODEL = os.environ.get("OPENROUTER_VISION_MODEL", "google/gemini-2.5-flash")

# -----------------------------------------------------------------------------
# Redis
# -----------------------------------------------------------------------------
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
CHAT_KEY_PREFIX = "safia:chat:"

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
# Database
# -----------------------------------------------------------------------------
# Example: postgresql+asyncpg://user:password@localhost:5432/safia
DATABASE_URL = os.environ["DATABASE_URL"]
