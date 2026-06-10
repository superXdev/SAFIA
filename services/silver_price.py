"""Fetch silver (perak) price in IDR from bullion-rates.com (IDR spot price table)."""
import re
import logging
from typing import Any

import requests

from config import PRICE_CACHE_KEY_SILVER, SILVER_PRICE_URL
from services.price_cache import get_cached, set_cached

BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "id,en;q=0.9",
}

# Rows: <td class="rate">43.895</td><td class="Unit">Gram</td> (price in IDR, dot = thousand sep)
_RATE_UNIT_RE = re.compile(
    r'<td\s+class="rate">\s*([\d.,]+)\s*</td>\s*<td\s+class="Unit">\s*(Gram|Ounce|Kilo)\s*</td>',
    re.IGNORECASE,
)


def _parse_idr_number(s: str) -> float:
    """Parse IDR number: dot as thousand separator (43.895 -> 43895, 1.365.288 -> 1365288)."""
    s = (s or "").strip().replace(" ", "").replace(".", "").replace(",", ".")
    try:
        return float(s) if s else 0.0
    except ValueError:
        return 0.0


def parse_silver_table(html: str) -> dict[str, Any]:
    """
    Parse silver spot table from bullion-rates.com. Returns dict with:
    idr_per_gram, idr_per_oz, idr_per_kilo (and legacy usd keys as 0).
    """
    result = {
        "idr_per_gram": 0.0,
        "idr_per_oz": 0.0,
        "idr_per_kilo": 0.0,
        "usd_per_gram": 0.0,
        "usd_per_oz": 0.0,
        "idr_per_gram_change": "",
        "idr_per_oz_change": "",
        "idr_per_kilo_change": "",
    }
    for m in _RATE_UNIT_RE.finditer(html):
        price_str = (m.group(1) or "").strip()
        unit = (m.group(2) or "").strip().lower()
        val = _parse_idr_number(price_str)
        if unit == "gram":
            result["idr_per_gram"] = val
        elif unit == "ounce":
            result["idr_per_oz"] = val
        elif unit == "kilo":
            result["idr_per_kilo"] = val
    return result


def fetch_silver_price_idr() -> dict[str, Any]:
    """Fetch silver price from bullion-rates.com (IDR per gram, oz, kilo). Cached in memory for 6 hours."""
    cached = get_cached(PRICE_CACHE_KEY_SILVER)
    if cached is not None:
        return cached
    try:
        resp = requests.get(SILVER_PRICE_URL, headers=BROWSER_HEADERS, timeout=15)
        resp.raise_for_status()
        html = resp.text
    except Exception:
        logging.exception("Silver price fetch failed")
        return parse_silver_table("")
    data = parse_silver_table(html)
    if data and (data.get("idr_per_gram") or data.get("idr_per_oz")):
        set_cached(PRICE_CACHE_KEY_SILVER, data)
    return data
