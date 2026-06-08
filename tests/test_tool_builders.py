"""Tests for tool-level helper/builders and schema/constant validation."""
import json

from services.tools.records import _build_record_confirm, _parse_filters
from services.tools.reminders import _build_schedule_json, _reminder_to_dict


class TestBuildRecordConfirm:
    def test_expense_confirm(self):
        result = _build_record_confirm(150000, "expense", "Makanan", "Lunch at resto")
        assert result["amount"] == 150000
        assert result["type"] == "expense"
        assert result["category"] == "Makanan"
        assert result["description"] == "Lunch at resto"
        assert result["status"] == "recorded"

    def test_income_confirm(self):
        result = _build_record_confirm(5000000, "income", "Gaji", "June salary")
        assert result["amount"] == 5000000
        assert result["type"] == "income"
        assert result["category"] == "Gaji"

    def test_no_description(self):
        result = _build_record_confirm(100000, "expense", "Hiburan", None)
        assert result["description"] == ""


class TestParseFilters:
    def test_empty_arguments(self):
        f = _parse_filters({})
        assert f["kind"] is None
        assert f["category"] is None
        assert f["min_amount"] is None
        assert f["max_amount"] is None
        assert f["from_date"] is None
        assert f["to_date"] is None

    def test_with_all_filters(self):
        args = {
            "kind": "expense",
            "category": "Makanan",
            "min_amount": 100000,
            "max_amount": 500000,
            "from_date": "2026-06-01",
            "to_date": "2026-06-08",
        }
        f = _parse_filters(args)
        assert f["kind"] == "expense"
        assert f["category"] == "Makanan"
        assert f["min_amount"] == 100000  # numeric, passthrough
        assert f["max_amount"] == 500000
        assert f["from_date"] is not None
        assert f["to_date"] is not None

    def test_partial_filters(self):
        f = _parse_filters({"kind": "income"})
        assert f["kind"] == "income"
        assert f["category"] is None

    def test_strips_whitespace(self):
        f = _parse_filters({"kind": "  expense  ", "category": ""})
        assert f["kind"] == "expense"
        assert f["category"] is None

    def test_invalid_dates_become_none(self):
        f = _parse_filters({"from_date": "not-a-date"})
        assert f["from_date"] is None

    def test_zero_amount_passthrough(self):
        f = _parse_filters({"min_amount": 0, "max_amount": 0})
        assert f["min_amount"] == 0  # _parse_filters passes through exactly


class TestBuildScheduleJson:
    def test_daily_schedule(self):
        result = _build_schedule_json({"schedule_type": "daily", "hour": 8, "minute": 30})
        parsed = json.loads(result)
        assert parsed["type"] == "daily"
        assert parsed["hour"] == 8
        assert parsed["minute"] == 30

    def test_weekly_schedule(self):
        result = _build_schedule_json({"schedule_type": "weekly", "day": "wednesday", "hour": 9, "minute": 0})
        parsed = json.loads(result)
        assert parsed["type"] == "weekly"
        assert parsed["day"] == "wednesday"

    def test_monthly_schedule(self):
        result = _build_schedule_json({"schedule_type": "monthly", "day_of_month": 15, "hour": 10, "minute": 0})
        parsed = json.loads(result)
        assert parsed["type"] == "monthly"
        assert parsed["day_of_month"] == 15

    def test_interval_schedule(self):
        result = _build_schedule_json({"schedule_type": "interval", "interval_hours": 2.0})
        parsed = json.loads(result)
        assert parsed["type"] == "interval"
        assert parsed["hours"] == 2.0

    def test_default_hour_and_minute(self):
        result = _build_schedule_json({"schedule_type": "daily"})
        parsed = json.loads(result)
        assert parsed["hour"] == 8  # default
        assert parsed["minute"] == 0

    def test_default_interval(self):
        result = _build_schedule_json({"schedule_type": "interval"})
        parsed = json.loads(result)
        assert parsed["hours"] == 24.0  # default

    def test_interval_min_hours(self):
        result = _build_schedule_json({"schedule_type": "interval", "interval_hours": 0.001})
        parsed = json.loads(result)
        assert parsed["hours"] > 0  # clamped to min


class TestReminderToDict:
    def test_reminder_to_dict(self):
        from unittest.mock import MagicMock
        from datetime import datetime, timezone as tz
        mock_reminder = MagicMock()
        mock_reminder.kind = "price"
        mock_reminder.title = "BTC Price Check"
        mock_reminder.schedule = '{"type": "daily", "hour": 8}'
        mock_reminder.timezone = "Asia/Jakarta"
        mock_reminder.enabled = True
        mock_reminder.next_run_at = datetime(2026, 6, 9, 1, 0, 0, tzinfo=tz.utc)
        mock_reminder.last_run_at = datetime(2026, 6, 8, 1, 0, 0, tzinfo=tz.utc)
        mock_reminder.fail_count = 0
        mock_reminder.created_at = datetime(2026, 6, 1, 0, 0, 0, tzinfo=tz.utc)

        result = _reminder_to_dict(mock_reminder)
        assert result["kind"] == "price"
        assert result["title"] == "BTC Price Check"
        assert result["timezone"] == "Asia/Jakarta"
        assert result["enabled"] is True
        assert result["fail_count"] == 0
        assert "2026-06-09" in result["next_run_at"]

    def test_reminder_to_dict_null_dates(self):
        from unittest.mock import MagicMock
        mock_reminder = MagicMock()
        mock_reminder.kind = "custom"
        mock_reminder.title = "Test"
        mock_reminder.schedule = '{"type": "daily", "hour": 9}'
        mock_reminder.timezone = "UTC"
        mock_reminder.next_run_at = None
        mock_reminder.last_run_at = None
        mock_reminder.enabled = True
        mock_reminder.fail_count = 0
        mock_reminder.created_at = None

        result = _reminder_to_dict(mock_reminder)
        assert result["next_run_at"] == ""
        assert result["last_run_at"] == ""
        assert result["created_at"] == ""
