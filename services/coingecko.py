"""CoinGecko API client — fetch top crypto market data."""
import logging
import os
import re
from typing import Any

import requests

from config import (
    COINGECKO_CACHE_TTL_COIN,
    COINGECKO_CACHE_TTL_MARKETS,
    COINGECKO_CACHE_TTL_SEARCH,
    COINGECKO_CACHE_TTL_TRENDING,
)
from services.price_cache import get_cached, set_cached

COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"
COINGECKO_API_KEY = os.environ.get("COINGECKO_API_KEY")  # optional Demo tier key


def _headers() -> dict[str, str]:
    h: dict[str, str] = {}
    if COINGECKO_API_KEY:
        h["x-cg-demo-api-key"] = COINGECKO_API_KEY
    return h


def _fmt_num(value: float | int | None) -> str:
    """Format large numbers into human-readable strings (e.g. 1.23T, 456.78B)."""
    if value is None:
        return "N/A"
    if value >= 1_000_000_000_000:
        return f"${value / 1_000_000_000_000:.2f}T"
    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:.2f}B"
    if value >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    return f"${value:,.2f}"


def get_top_market_cap(
    vs_currency: str = "usd",
    per_page: int = 10,
    page: int = 1,
) -> list[dict[str, Any]]:
    """Return top coins by market cap from CoinGecko /coins/markets.

    Each item in the returned list contains a curated subset of fields:
    rank, name, symbol, current_price, price_change_24h_pct, market_cap,
    market_cap_formatted, total_volume, total_volume_formatted, high_24h,
    low_24h, image.
    """
    params = {
        "vs_currency": vs_currency,
        "order": "market_cap_desc",
        "per_page": min(per_page, 250),
        "page": page,
        "sparkline": "false",
        "price_change_percentage": "24h",
    }

    cache_key = f"safia:cg:markets:{vs_currency}:{per_page}:{page}"
    cached = get_cached(cache_key)
    if cached:
        return cached

    resp = requests.get(
        f"{COINGECKO_BASE_URL}/coins/markets",
        params=params,
        headers=_headers(),
        timeout=30,
    )
    resp.raise_for_status()
    raw: list[dict] = resp.json()

    results: list[dict[str, Any]] = []
    for coin in raw:
        results.append(
            {
                "rank": coin.get("market_cap_rank"),
                "name": coin.get("name"),
                "symbol": (coin.get("symbol") or "").upper(),
                "current_price": coin.get("current_price"),
                "price_change_24h_pct": coin.get("price_change_percentage_24h"),
                "market_cap": coin.get("market_cap"),
                "market_cap_formatted": _fmt_num(coin.get("market_cap")),
                "total_volume": coin.get("total_volume"),
                "total_volume_formatted": _fmt_num(coin.get("total_volume")),
                "high_24h": coin.get("high_24h"),
                "low_24h": coin.get("low_24h"),
                "image": coin.get("image"),
            }
        )
    
    set_cached(cache_key, results, COINGECKO_CACHE_TTL_MARKETS)
    return results


def search_crypto(query: str) -> list[dict[str, Any]]:
    """Search for coins by name or symbol via CoinGecko /search.

    Returns a list of matching coins with id, name, symbol, and market_cap_rank.
    """
    cache_key = f"safia:cg:search:{query.lower()}"
    cached = get_cached(cache_key)
    if cached:
        return cached

    resp = requests.get(
        f"{COINGECKO_BASE_URL}/search",
        params={"query": query},
        headers=_headers(),
        timeout=30,
    )
    resp.raise_for_status()
    raw: dict = resp.json()

    results: list[dict[str, Any]] = []
    for coin in (raw.get("coins") or [])[:10]:
        results.append(
            {
                "id": coin.get("id"),
                "name": coin.get("name"),
                "symbol": (coin.get("symbol") or "").upper(),
                "market_cap_rank": coin.get("market_cap_rank"),
                "image": coin.get("large"),
            }
        )
    
    set_cached(cache_key, results, COINGECKO_CACHE_TTL_SEARCH)
    return results


def _resolve_coin_id(query: str) -> str | None:
    """Resolve a user query (name/symbol/id) to a valid CoinGecko coin ID."""
    results = search_crypto(query)
    if not results:
        return None
    q = query.strip().lower()
    # Exact match on id, symbol, or name
    for coin in results:
        if coin["id"] == q or coin["symbol"].lower() == q or (coin["name"] or "").lower() == q:
            return coin["id"]
    # Fallback to the top result (highest market cap)
    return results[0]["id"]


def _fetch_coin_detail(coin_id: str) -> dict | None:
    """Fetch raw coin detail by exact coin ID. Returns None on 404."""
    cache_key = f"safia:cg:coin_raw:{coin_id}"
    cached = get_cached(cache_key)
    if cached:
        return cached

    params = {
        "localization": "false",
        "tickers": "false",
        "market_data": "true",
        "community_data": "false",
        "developer_data": "false",
        "sparkline": "false",
    }
    resp = requests.get(
        f"{COINGECKO_BASE_URL}/coins/{coin_id}",
        params=params,
        headers=_headers(),
        timeout=30,
    )
    if resp.status_code == 404:
        # Cache negative result briefly to avoid spamming 404s
        set_cached(cache_key, {"error": "not_found"}, 60)
        return None
    resp.raise_for_status()
    raw = resp.json()
    set_cached(cache_key, raw, COINGECKO_CACHE_TTL_COIN)
    return raw


def _parse_coin_detail(raw: dict) -> dict[str, Any]:
    """Extract only the most important fields from a raw coin detail response."""
    md = raw.get("market_data") or {}

    desc_en = (raw.get("description") or {}).get("en") or ""
    desc_clean = re.sub(r"<[^>]+>", "", desc_en).replace("\r\n", " ").strip()
    desc_snippet = desc_clean[:300] + ("..." if len(desc_clean) > 300 else "")

    links = raw.get("links") or {}
    homepage = [u for u in (links.get("homepage") or []) if u]
    explorers = [u for u in (links.get("blockchain_site") or []) if u][:2]

    return {
        "id": raw.get("id"),
        "name": raw.get("name"),
        "symbol": (raw.get("symbol") or "").upper(),
        "image": (raw.get("image") or {}).get("large"),
        "description": desc_snippet,
        "market_cap_rank": raw.get("market_cap_rank"),
        "genesis_date": raw.get("genesis_date"),
        "categories": (raw.get("categories") or [])[:5],
        "current_price_usd": (md.get("current_price") or {}).get("usd"),
        "current_price_idr": (md.get("current_price") or {}).get("idr"),
        "market_cap_usd": (md.get("market_cap") or {}).get("usd"),
        "market_cap_formatted": _fmt_num((md.get("market_cap") or {}).get("usd")),
        "total_volume_usd": (md.get("total_volume") or {}).get("usd"),
        "price_change_24h_pct": md.get("price_change_percentage_24h"),
        "price_change_7d_pct": md.get("price_change_percentage_7d"),
        "price_change_30d_pct": md.get("price_change_percentage_30d"),
        "ath_usd": (md.get("ath") or {}).get("usd"),
        "ath_date": (md.get("ath_date") or {}).get("usd"),
        "ath_change_pct": (md.get("ath_change_percentage") or {}).get("usd"),
        "atl_usd": (md.get("atl") or {}).get("usd"),
        "atl_date": (md.get("atl_date") or {}).get("usd"),
        "circulating_supply": md.get("circulating_supply"),
        "total_supply": md.get("total_supply"),
        "max_supply": md.get("max_supply"),
        "homepage": homepage[:1],
        "explorers": explorers,
    }


def get_coin_detail(coin_id: str) -> dict[str, Any]:
    """Return essential detail for a single coin.

    Tries direct lookup by coin_id first. If 404, falls back to /search
    to resolve the query (name/symbol) to the correct ID and retries.
    """
    # 1) Try direct lookup
    raw = _fetch_coin_detail(coin_id)
    if raw is not None:
        return _parse_coin_detail(raw)

    # 2) Fallback: search to resolve the correct ID
    logging.info("Coin ID '%s' not found, searching...", coin_id)
    resolved_id = _resolve_coin_id(coin_id)
    if not resolved_id:
        return {"error": f"Coin '{coin_id}' not found on CoinGecko."}

    raw = _fetch_coin_detail(resolved_id)
    if raw is None:
        return {"error": f"Coin '{coin_id}' (resolved to '{resolved_id}') not found."}

    return _parse_coin_detail(raw)


def get_trending_crypto() -> list[dict[str, Any]]:
    """Return the top trending coins from CoinGecko /search/trending.

    Only the most important fields per coin are returned.
    """
    cache_key = "safia:cg:trending"
    cached = get_cached(cache_key)
    if cached:
        return cached

    resp = requests.get(
        f"{COINGECKO_BASE_URL}/search/trending",
        headers=_headers(),
        timeout=30,
    )
    resp.raise_for_status()
    raw: dict = resp.json()

    results: list[dict[str, Any]] = []
    for item in raw.get("coins") or []:
        coin = item.get("item") or {}
        results.append(
            {
                "rank": coin.get("score", 0) + 1,  # score is 0-indexed
                "name": coin.get("name"),
                "symbol": (coin.get("symbol") or "").upper(),
                "market_cap_rank": coin.get("market_cap_rank"),
                "price_btc": coin.get("price_btc"),
                "image": coin.get("small"),
                # data subobject has USD-based fields
                "current_price_usd": (coin.get("data") or {}).get("price"),
                "market_cap": (coin.get("data") or {}).get("market_cap"),
                "market_cap_formatted": (coin.get("data") or {}).get("market_cap"),
                "total_volume": (coin.get("data") or {}).get("total_volume"),
                "price_change_24h_pct": (coin.get("data") or {}).get("price_change_percentage_24h", {}).get("usd"),
            }
        )
    
    set_cached(cache_key, results, COINGECKO_CACHE_TTL_TRENDING)
    return results
