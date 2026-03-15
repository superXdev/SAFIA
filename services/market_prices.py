"""Market price fetchers — Indonesia stocks, forex, crypto via TradingView screener. Cached with TTL; USD→IDR for forex/crypto."""
import logging
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
from services.gold_price import fetch_gold_price_idr
from services.silver_price import fetch_silver_price_idr

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


def get_stock_price_america(query: str | None = None, limit: int = 10) -> list[dict]:
    """Fetch US/global stock prices from TradingView screener (Market.AMERICA). Price in USD. Cached 10 min."""
    cache_key = f"safia:market:stock_america:{query or ''}:{limit}"
    cached = get_cached(cache_key)
    if cached is not None:
        return cached
    try:
        ss = StockScreener()
        ss.set_markets(Market.AMERICA)
        ss.set_range(0, limit)
        ss.select(StockField.NAME, StockField.PRICE)
        if query:
            ss.search(query)
        df = ss.get()
        data = _df_to_list(df)
        set_cached(cache_key, data, ttl_seconds=MARKET_CACHE_TTL_STOCK_SECONDS)
        return data
    except Exception:
        logging.exception("Stock America fetch failed for query=%s", query)
        return []


def get_asset_unit_price_idr(asset_type: str, name: str) -> float | None:
    """
    Get current unit price in IDR for an asset (for amount-based recording).
    Uses TradingView screener only for stock and crypto; gold from harga-emas.
    Returns None if unsupported type or price not found.
    """
    at = (asset_type or "").strip().lower()
    nm = (name or "").strip()
    if not nm:
        return None

    if at == "stock":
        # Try Indonesia first (Price already IDR)
        id_data = get_stock_price_indonesia(query=nm, limit=5)
        for row in id_data:
            sym = str(row.get("Symbol") or "")
            label = str(row.get("Name") or "")
            if nm.upper() in (sym.upper(), label.upper()) or (nm.upper() in sym.upper() and ".JK" in sym):
                p = row.get("Price")
                if p is not None:
                    try:
                        return float(p)
                    except (TypeError, ValueError):
                        pass
        # US/global stocks: Price in USD → IDR
        us_data = get_stock_price_america(query=nm, limit=5)
        rate = get_usd_idr_rate()
        if not us_data or rate is None:
            return None
        p = us_data[0].get("Price")
        if p is not None:
            try:
                return round(float(p) * rate, 2)
            except (TypeError, ValueError):
                pass
        return None

    if at == "crypto":
        result = get_crypto_price(symbol=nm, limit=5)
        rows = result.get("data") or []
        rate = result.get("usd_idr_rate")
        if not rows:
            return None
        row = rows[0]
        price_idr = row.get("Price_IDR")
        if price_idr is not None:
            try:
                return float(price_idr)
            except (TypeError, ValueError):
                pass
        price_usd = row.get("Price")
        if price_usd is not None and rate is not None:
            try:
                return round(float(price_usd) * rate, 2)
            except (TypeError, ValueError):
                pass
        return None

    if at == "gold":
        rows = fetch_gold_price_idr()
        for r in rows:
            unit = (r.get("unit") or "").lower()
            if "gram" in unit or "gr" in unit:
                idr = r.get("idr")
                if idr is not None:
                    try:
                        return float(idr)
                    except (TypeError, ValueError):
                        pass
        if rows:
            idr = rows[0].get("idr")
            if idr is not None:
                try:
                    return float(idr)
                except (TypeError, ValueError):
                    pass
        return None

    if at == "silver" or at == "perak":
        data = fetch_silver_price_idr()
        idr = data.get("idr_per_gram")
        if idr is not None and idr > 0:
            try:
                return float(idr)
            except (TypeError, ValueError):
                pass
        return None

    if at == "forex":
        result = get_forex_price(symbol=nm, limit=5)
        rows = result.get("data") or []
        rate = result.get("usd_idr_rate")
        if not rows:
            return None
        row = rows[0]
        price_idr = row.get("Price_IDR")
        if price_idr is not None:
            try:
                return float(price_idr)
            except (TypeError, ValueError):
                pass
        price_usd = row.get("Price")
        if price_usd is not None and rate is not None:
            try:
                return round(float(price_usd) * rate, 2)
            except (TypeError, ValueError):
                pass
        return None

    return None
