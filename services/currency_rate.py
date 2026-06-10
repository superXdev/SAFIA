"""Universal currency converter — real-time rates with in-memory cache per pair."""
import logging

import requests

from config import CURRENCY_RATE_URL, RATE_CACHE_KEY_PREFIX, RATE_CACHE_TTL_SECONDS
from services.price_cache import get_cached, set_cached



def _normalize_currency(code: str) -> str:
    """Normalize to 3-letter uppercase (e.g. idr → IDR, usd → USD)."""
    if not code or not code.strip():
        return ""
    c = code.strip().upper()
    return c[:3] if len(c) > 3 else c


def get_currency_rate(from_currency: str, to_currency: str) -> float | None:
    """
    Get exchange rate: 1 unit of from_currency = X units of to_currency.
    Cached per pair for 1 hour. Returns None on unsupported pair or error.
    """
    fr = _normalize_currency(from_currency)
    to = _normalize_currency(to_currency)
    if fr == to:
        return 1.0
    if not fr or not to:
        return None
    cache_key = f"{RATE_CACHE_KEY_PREFIX}{fr}:{to}"
    cached = get_cached(cache_key)
    if cached is not None and isinstance(cached, (int, float)):
        return float(cached)
    if isinstance(cached, dict) and "rate" in cached:
        return float(cached["rate"])
    try:
        resp = requests.get(
            CURRENCY_RATE_URL,
            params={"from": fr, "to": to},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        rate = data.get("rates", {}).get(to)
        if rate is None:
            return None
        rate = float(rate)
        set_cached(cache_key, rate, ttl_seconds=RATE_CACHE_TTL_SECONDS)
        return rate
    except Exception:
        logging.exception("Currency rate fetch failed for %s -> %s", fr, to)
        return None


def get_usd_idr_rate() -> float | None:
    """Convenience: USD to IDR rate (used by market_prices for forex/crypto)."""
    return get_currency_rate("USD", "IDR")
