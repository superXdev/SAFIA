"""Fetch silver (perak) price in IDR from harga-emas.org/perak (OneGramParekTable)."""
import re
import logging
from typing import Any

import requests

from config import PRICE_CACHE_KEY_SILVER
from services.price_cache import get_cached, set_cached

SILVER_URL = "https://harga-emas.org/perak"

BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "id,en;q=0.9",
}

# Unit block: <span class="...units...">LABEL</span><br>PRICE<br><span ...>CHANGE</span>
_UNIT_BLOCK_RE = re.compile(
    r'OneGramParekTable_units[^>]*>([^<]+)</span>\s*<br>\s*([^<]+)\s*<br>\s*<span[^>]*>([^<]*)</span>',
    re.IGNORECASE | re.DOTALL,
)


def _parse_idr(s: str) -> float:
    """Parse IDR string like Rp43.918 or Rp1.365.349 -> float."""
    s = (s or "").strip().replace("Rp", "").replace(" ", "").replace(".", "").replace(",", ".")
    try:
        return float(s) if s else 0.0
    except ValueError:
        return 0.0


def _parse_usd(s: str) -> float:
    """Parse USD string like $2.59 or $80.61 -> float."""
    s = (s or "").strip().replace("$", "").replace(" ", "").replace(",", ".")
    try:
        return float(s) if s else 0.0
    except ValueError:
        return 0.0


def parse_silver_table(html: str) -> dict[str, Any]:
    """
    Parse silver price from OneGramParekTable. Returns dict with:
    idr_per_gram, idr_per_oz, usd_per_gram, usd_per_oz, kurs (optional),
    and change strings for each.
    """
    result = {
        "idr_per_gram": 0.0,
        "idr_per_oz": 0.0,
        "usd_per_gram": 0.0,
        "usd_per_oz": 0.0,
        "idr_per_gram_change": "",
        "idr_per_oz_change": "",
        "usd_per_gram_change": "",
        "usd_per_oz_change": "",
        "kurs": 0.0,
        "kurs_change": "",
    }
    for m in _UNIT_BLOCK_RE.finditer(html):
        label = (m.group(1) or "").strip().upper()
        price_str = (m.group(2) or "").strip()
        change_str = (m.group(3) or "").strip()
        if "IDR/G" in label:
            result["idr_per_gram"] = _parse_idr(price_str)
            result["idr_per_gram_change"] = change_str
        elif "IDR/OZ" in label:
            result["idr_per_oz"] = _parse_idr(price_str)
            result["idr_per_oz_change"] = change_str
        elif "USD/G" in label:
            result["usd_per_gram"] = _parse_usd(price_str)
            result["usd_per_gram_change"] = change_str
        elif "USD/OZ" in label:
            result["usd_per_oz"] = _parse_usd(price_str)
            result["usd_per_oz_change"] = change_str
        elif "KURS" in label:
            result["kurs"] = _parse_idr(price_str)
            result["kurs_change"] = change_str
    return result


def fetch_silver_price_idr() -> dict[str, Any]:
    """Fetch silver price table from harga-emas.org/perak. Returns parsed dict. Cached in Redis for 6 hours."""
    cached = get_cached(PRICE_CACHE_KEY_SILVER)
    if cached is not None:
        return cached
    try:
        resp = requests.get(SILVER_URL, headers=BROWSER_HEADERS, timeout=15)
        resp.raise_for_status()
        print(resp.status_code)
        html = resp.text
    except Exception:
        logging.exception("Silver price fetch failed")
        return parse_silver_table("")  # return empty structure
    data = parse_silver_table(html)
    if data and (data.get("idr_per_gram") or data.get("usd_per_gram")):
        set_cached(PRICE_CACHE_KEY_SILVER, data)
    return data
