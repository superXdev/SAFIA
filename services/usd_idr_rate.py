"""Backward compat: USD/IDR and universal currency rates live in currency_rate."""
from services.currency_rate import get_usd_idr_rate, get_currency_rate

__all__ = ["get_usd_idr_rate", "get_currency_rate"]
