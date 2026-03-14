"""Fetch gold price in IDR from harga-emas.org (table: Satuan, USD, IDR)."""
import re
import logging
from typing import Any

import requests

from config import PRICE_CACHE_KEY_GOLD
from services.price_cache import get_cached, set_cached

GOLD_URL = "https://harga-emas.org/"

BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "id,en;q=0.9",
}

# Table row: Satuan | USD (num + span change) | IDR (num + span change)
_ROW_RE = re.compile(
    r"<tr>\s*<td>([^<]+)</td>\s*<td>([\d.,]+)\s*<span[^>]*>\(([^)]*)\)</span>\s*</td>\s*<td>([\d.,]+)\s*<span[^>]*>\(([^)]*)\)</span>",
    re.IGNORECASE | re.DOTALL,
)


def _parse_idr_number(s: str) -> float:
    """Parse IDR-style number: 85.068.886,39 -> 85068886.39."""
    s = (s or "").strip().replace(" ", "")
    s = s.replace(".", "").replace(",", ".")
    try:
        return float(s) if s else 0.0
    except ValueError:
        return 0.0


def _clean_change(s: str) -> str:
    """Remove HTML comments from change string, e.g. '<!-- -->-75,64<!-- -->' -> '-75,64'."""
    return re.sub(r"<!--.*?-->", "", (s or "").strip()).strip()


def _parse_usd_number(s: str) -> float:
    """Parse USD-style number: 5.020 or 161,4 -> float."""
    s = (s or "").strip().replace(" ", "")
    s = s.replace(",", ".")
    try:
        return float(s) if s else 0.0
    except ValueError:
        return 0.0


def parse_gold_table(html: str) -> list[dict[str, Any]]:
    """
    Parse gold price table from HTML (Satuan | USD | IDR rows). Returns list of dicts
    with unit, usd, usd_change, idr, idr_change.
    """
    results = []
    for m in _ROW_RE.finditer(html):
        unit_raw = m.group(1).strip()
        usd_str = m.group(2).strip()
        usd_change = m.group(3).strip()
        idr_str = m.group(4).strip()
        idr_change = m.group(5).strip()
        # Skip header row (Satuan, USD, IDR)
        if unit_raw.lower() in ("satuan", "unit"):
            continue
        results.append({
            "unit": unit_raw,
            "usd": _parse_usd_number(usd_str),
            "usd_change": _clean_change(usd_change),
            "idr": _parse_idr_number(idr_str),
            "idr_change": _clean_change(idr_change),
        })
        if len(results) >= 3:  # Ounce, Gram, Kilogram
            break
    return results


def fetch_gold_price_idr() -> list[dict[str, Any]]:
    """
    Fetch gold price table from harga-emas.org. Returns list of rows with keys:
    unit (e.g. "Ounce (oz)"), usd, usd_change, idr, idr_change.
    Cached in Redis for 6 hours.
    """
    cached = get_cached(PRICE_CACHE_KEY_GOLD)
    if cached is not None:
        return cached
    try:
        resp = requests.get(GOLD_URL, headers=BROWSER_HEADERS, timeout=15)
        resp.raise_for_status()
        html = resp.text
    except Exception:
        logging.exception("Gold price fetch failed")
        return []
    data = parse_gold_table(html)
    if data:
        set_cached(PRICE_CACHE_KEY_GOLD, data)
    return data
