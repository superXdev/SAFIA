"""Tool schemas — JSON function definitions for all LLM tools."""
from services.tools.schemas.assets import SCHEMAS as ASSET_SCHEMAS
from services.tools.schemas.crypto_market import SCHEMAS as CRYPTO_MARKET_SCHEMAS
from services.tools.schemas.currency import SCHEMAS as CURRENCY_SCHEMAS
from services.tools.schemas.debts import SCHEMAS as DEBT_SCHEMAS
from services.tools.schemas.gold import SCHEMAS as GOLD_SCHEMAS
from services.tools.schemas.knowledge_search import SCHEMAS as KNOWLEDGE_SCHEMAS
from services.tools.schemas.memory import SCHEMAS as MEMORY_SCHEMAS
from services.tools.schemas.news_search import SCHEMAS as NEWS_SEARCH_SCHEMAS
from services.tools.schemas.prices import SCHEMAS as PRICE_SCHEMAS
from services.tools.schemas.records import SCHEMAS as RECORD_SCHEMAS
from services.tools.schemas.reminders import SCHEMAS as REMINDER_SCHEMAS
from services.tools.schemas.silver import SCHEMAS as SILVER_SCHEMAS

TOOLS = (
    RECORD_SCHEMAS + DEBT_SCHEMAS + ASSET_SCHEMAS + GOLD_SCHEMAS
    + SILVER_SCHEMAS + PRICE_SCHEMAS + CURRENCY_SCHEMAS + CRYPTO_MARKET_SCHEMAS
    + NEWS_SEARCH_SCHEMAS + KNOWLEDGE_SCHEMAS + REMINDER_SCHEMAS + MEMORY_SCHEMAS
)
