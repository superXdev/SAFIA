"""Market price fetchers — Indonesia stocks, forex, crypto via TradingView screener. Cached with TTL; USD→IDR for forex/crypto."""
import math

from tvscreener import (
    StockScreener,
    StockField,
    Market,
    CryptoScreener,
    CryptoField,
    ForexScreener,
    ForexField,
)

from config import (
    MARKET_CACHE_TTL_STOCK_SECONDS,
    MARKET_CACHE_TTL_FOREX_SECONDS,
    MARKET_CACHE_TTL_CRYPTO_SECONDS,
)
from services.price_cache import get_cached, set_cached
from services.currency_rate import get_usd_idr_rate

# Cache key prefixes
_MARKET_KEY_STOCK = "safia:market:stock:"
_MARKET_KEY_FOREX = "safia:market:forex:"
_MARKET_KEY_CRYPTO = "safia:market:crypto:"

# Column labels that are USD amounts (get _IDR copy)
_FOREX_USD_KEYS = ("Price", "Open", "High", "Low", "Change")
_CRYPTO_USD_KEYS = ("Price", "Open", "High", "Low", "Change", "Volume", "Volume 24h in USD")


def _df_to_list(df):
    """Convert screener DataFrame to list of dicts. NaN → None for JSON."""
    if df.empty:
        return []
    data = df.to_dict(orient="records")
    for row in data:
        for k, v in list(row.items()):
            if v is not None and isinstance(v, float) and math.isnan(v):
                row[k] = None
            elif hasattr(v, "item"):
                try:
                    x = v.item()
                    row[k] = None if isinstance(x, float) and math.isnan(x) else x
                except (ValueError, AttributeError):
                    row[k] = str(v)
    return data


def _enrich_usd_to_idr(rows: list[dict], rate: float, usd_keys: tuple[str, ...]) -> None:
    """Add *_IDR keys for numeric USD columns. Mutates rows in place."""
    for row in rows:
        for key in usd_keys:
            val = row.get(key)
            if val is None:
                continue
            try:
                num = float(val)
                if not math.isfinite(num):
                    continue
                row[f"{key}_IDR"] = round(num * rate, 2)
            except (TypeError, ValueError):
                continue


def get_stock_price_indonesia(query: str | None = None, limit: int = 50) -> list[dict]:
    """Fetch Indonesia stock prices from TradingView screener. Cached 10 min. Optional search query (e.g. bank, BBCA)."""
    cache_key = f"{_MARKET_KEY_STOCK}{query or ''}:{limit}"
    cached = get_cached(cache_key)
    if cached is not None:
        return cached
    ss = StockScreener()
    ss.set_markets(Market.INDONESIA)
    ss.set_range(0, limit)
    ss.select(
        StockField.NAME,
        StockField.PRICE,
        StockField.CHANGE,
        StockField.CHANGE_PERCENT,
        StockField.OPEN,
        StockField.HIGH,
        StockField.LOW,
        StockField.VOLUME,
        StockField.AVERAGE_VOLUME_10_DAY,
        StockField.RELATIVE_VOLUME,
        StockField.MARKET_CAPITALIZATION,
        StockField.PRICE_TO_EARNINGS_RATIO_TTM,
        StockField.WEEK_HIGH_52,
        StockField.WEEK_LOW_52,
        StockField.SECTOR,
        StockField.INDUSTRY,
        StockField.RELATIVE_STRENGTH_INDEX_14,
        StockField.MACD_LEVEL_12_26,
        StockField.MACD_SIGNAL_12_26,
        StockField.MOVING_AVERAGES_RATING,
        StockField.WEEKLY_PERFORMANCE,
        StockField.MONTHLY_PERFORMANCE,
        StockField.YTD_PERFORMANCE,
    )
    if query:
        ss.search(query)
    df = ss.get()
    data = _df_to_list(df)
    set_cached(cache_key, data, ttl_seconds=MARKET_CACHE_TTL_STOCK_SECONDS)
    return data


def get_forex_price(symbol: str | None = None, limit: int = 50) -> dict:
    """Fetch forex pair prices from TradingView. Cached 5 min. USD values get Price_IDR etc. using real-time rate."""
    cache_key = f"{_MARKET_KEY_FOREX}{symbol or ''}:{limit}"
    cached = get_cached(cache_key)
    if cached is not None:
        data = cached
    else:
        fs = ForexScreener()
        fs.set_range(0, limit)
        fs.select(
            ForexField.NAME,
            ForexField.PRICE,
            ForexField.CHANGE,
            ForexField.CHANGE_PERCENT,
            ForexField.OPEN,
            ForexField.HIGH,
            ForexField.LOW,
            ForexField.WEEKLY_PERFORMANCE,
            ForexField.MONTHLY_PERFORMANCE,
        )
        if symbol:
            fs.search(symbol)
        df = fs.get()
        data = _df_to_list(df)
        set_cached(cache_key, data, ttl_seconds=MARKET_CACHE_TTL_FOREX_SECONDS)
    rate = get_usd_idr_rate()
    out = [dict(row) for row in data]
    if rate is not None:
        _enrich_usd_to_idr(out, rate, _FOREX_USD_KEYS)
    return {"data": out, "usd_idr_rate": rate}


def get_crypto_price(symbol: str | None = None, limit: int = 50) -> dict:
    """Fetch crypto prices from TradingView. Cached 2 min. USD values get Price_IDR etc. using real-time rate."""
    cache_key = f"{_MARKET_KEY_CRYPTO}{symbol or ''}:{limit}"
    cached = get_cached(cache_key)
    if cached is not None:
        data = cached
    else:
        cs = CryptoScreener()
        cs.set_range(0, limit)
        cs.select(
            CryptoField.NAME,
            CryptoField.PRICE,
            CryptoField.CHANGE,
            CryptoField.CHANGE_PERCENT,
            CryptoField.OPEN,
            CryptoField.HIGH,
            CryptoField.LOW,
            CryptoField.VOLUME,
            CryptoField.VOLUME_24H_IN_USD,
            CryptoField.WEEKLY_PERFORMANCE,
            CryptoField.MONTHLY_PERFORMANCE,
        )
        if symbol:
            cs.search(symbol)
        df = cs.get()
        data = _df_to_list(df)
        set_cached(cache_key, data, ttl_seconds=MARKET_CACHE_TTL_CRYPTO_SECONDS)
    rate = get_usd_idr_rate()
    out = [dict(row) for row in data]
    if rate is not None:
        _enrich_usd_to_idr(out, rate, _CRYPTO_USD_KEYS)
    return {"data": out, "usd_idr_rate": rate}
