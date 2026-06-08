"""Tests for project helpers and utility functions."""
from datetime import date

import pytest

from services.chat_history import _chat_key, _rate_key
from services.database import _asset_to_dict
from services.document_vision import parse_final_amount
from services.tools._helpers import parse_date
from services.tools.assets import _round_quantity_by_type


class TestParseDate:
    def test_valid_iso_date(self):
        assert parse_date("2026-06-08") == date(2026, 6, 8)

    def test_datetime_string(self):
        assert parse_date("2026-06-08T12:30:00") == date(2026, 6, 8)

    def test_empty_string(self):
        assert parse_date("") is None

    def test_none_value(self):
        assert parse_date(None) is None

    def test_invalid_string(self):
        assert parse_date("not-a-date") is None

    def test_whitespace_only(self):
        assert parse_date("   ") is None


class TestParseFinalAmount:
    def test_standard_format(self):
        assert parse_final_amount("FINAL_AMOUNT: 1500000") == 1500000.0

    def test_with_dot_separator(self):
        assert parse_final_amount("FINAL_AMOUNT: 1.500.000") == 1500000.0

    def test_with_comma_decimal(self):
        result = parse_final_amount("FINAL_AMOUNT: 1,500,000.50")
        assert result is not None
        assert result >= 1500000.0

    def test_lowercase(self):
        assert parse_final_amount("final_amount: 750000") == 750000.0

    def test_case_insensitive(self):
        assert parse_final_amount("Final_Amount: 5000000") == 5000000.0

    def test_not_a_number(self):
        assert parse_final_amount("FINAL_AMOUNT: abc") is None

    def test_no_match(self):
        assert parse_final_amount("Just some text with no final amount") is None

    def test_in_multiline_text(self):
        text = "Some text\nSubtotal: 1000000\nFINAL_AMOUNT: 850000\nMore text"
        assert parse_final_amount(text) == 850000.0

    def test_zero_amount(self):
        assert parse_final_amount("FINAL_AMOUNT: 0") == 0.0


class TestChatHistoryKeys:
    def test_chat_key(self):
        assert _chat_key(12345) == "safia:chat:12345"
        assert _chat_key(0) == "safia:chat:0"

    def test_rate_key(self):
        assert _rate_key(999, "2026-06-08") == "safia:rate:999:2026-06-08"


class TestAssetToDict:
    def test_asset_to_dict(self):
        from unittest.mock import MagicMock
        from datetime import datetime, timezone as tz
        mock_asset = MagicMock()
        mock_asset.asset_type = "stocks"
        mock_asset.name = "TLKM"
        mock_asset.quantity = 50.0
        mock_asset.unit_value = 4500.0
        mock_asset.notes = "Telkom shares"
        mock_asset.created_at = datetime(2026, 1, 1, tzinfo=tz.utc)
        mock_asset.updated_at = datetime(2026, 6, 1, tzinfo=tz.utc)

        result = _asset_to_dict(mock_asset)
        assert result["asset_type"] == "stocks"
        assert result["name"] == "TLKM"
        assert result["quantity"] == 50.0
        assert result["unit_value"] == 4500.0
        assert result["value"] == 225000.0  # 50 * 4500
        assert result["notes"] == "Telkom shares"
        assert "2026-01-01" in result["created_at"]


class TestRoundQuantityByType:
    def test_crypto_rounds_8_decimals(self):
        assert _round_quantity_by_type("crypto", 1.123456789) == 1.12345679

    def test_stocks_rounds_2_decimals(self):
        assert _round_quantity_by_type("stocks", 100.5678) == 100.57

    def test_gold_rounds_2_decimals(self):
        assert _round_quantity_by_type("gold", 2.3456) == 2.35

    def test_unknown_type_rounds_2(self):
        assert _round_quantity_by_type("other", 10.999) == 11.0

    def test_int_unchanged(self):
        assert _round_quantity_by_type("stocks", 50) == 50.0
