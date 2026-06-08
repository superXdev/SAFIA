"""Tests for schedule computation (pure function)."""
from datetime import date, datetime, timedelta, timezone

import pytest

from services.schedule import compute_next_run

# Use a fixed reference for deterministic results
REF = datetime(2026, 6, 8, 12, 0, 0, tzinfo=timezone.utc)
UTC = timezone.utc


class TestComputeNextRun:
    def test_daily_schedule(self):
        schedule = '{"type": "daily", "hour": 8, "minute": 0}'
        result = compute_next_run(schedule, "UTC", after=REF)
        expected = datetime(2026, 6, 9, 8, 0, 0, tzinfo=UTC)
        assert result == expected

    def test_daily_same_day_before(self):
        schedule = '{"type": "daily", "hour": 14, "minute": 30}'
        result = compute_next_run(schedule, "UTC", after=REF)
        expected = datetime(2026, 6, 8, 14, 30, 0, tzinfo=UTC)
        assert result == expected

    def test_daily_same_day_exact_time(self):
        schedule = '{"type": "daily", "hour": 12, "minute": 0}'
        result = compute_next_run(schedule, "UTC", after=REF)
        expected = datetime(2026, 6, 9, 12, 0, 0, tzinfo=UTC)
        assert result == expected

    def test_weekly_specific_day(self):
        # REF is Monday. "day": "wednesday"
        schedule = '{"type": "weekly", "day": "wednesday", "hour": 9, "minute": 0}'
        result = compute_next_run(schedule, "UTC", after=REF)
        expected = datetime(2026, 6, 10, 9, 0, 0, tzinfo=UTC)  # Wednesday
        assert result == expected

    def test_weekly_same_day_but_later(self):
        # REF is Monday 12:00. "day": "monday", hour 14
        schedule = '{"type": "weekly", "day": "monday", "hour": 14, "minute": 0}'
        result = compute_next_run(schedule, "UTC", after=REF)
        expected = datetime(2026, 6, 8, 14, 0, 0, tzinfo=UTC)
        assert result == expected

    def test_weekly_same_day_earlier_next_week(self):
        # REF is Monday 12:00. "day": "monday", "hour": 8
        schedule = '{"type": "weekly", "day": "monday", "hour": 8, "minute": 0}'
        result = compute_next_run(schedule, "UTC", after=REF)
        expected = datetime(2026, 6, 15, 8, 0, 0, tzinfo=UTC)
        assert result == expected

    def test_monthly_specific_day(self):
        schedule = '{"type": "monthly", "day_of_month": 15, "hour": 10, "minute": 0}'
        result = compute_next_run(schedule, "UTC", after=REF)
        # Jun 08 12:00 → next 15th at 10:00 = Jun 15 10:00
        expected = datetime(2026, 6, 15, 10, 0, 0, tzinfo=UTC)
        assert result == expected

    def test_monthly_day_passed_this_month(self):
        schedule = '{"type": "monthly", "day_of_month": 5, "hour": 10, "minute": 0}'
        result = compute_next_run(schedule, "UTC", after=REF)
        # Jun 05 already passed → Jul 05
        expected = datetime(2026, 7, 5, 10, 0, 0, tzinfo=UTC)
        assert result == expected

    def test_monthly_clamped_to_28(self):
        # day_of_month is clamped to max 28
        schedule = '{"type": "monthly", "day_of_month": 31, "hour": 10, "minute": 0}'
        result = compute_next_run(schedule, "UTC", after=REF)
        # Clamped to 28 → Jun 28 10:00 (since 28 > 8)
        expected = datetime(2026, 6, 28, 10, 0, 0, tzinfo=UTC)
        assert result == expected

    def test_interval_schedule(self):
        schedule = '{"type": "interval", "hours": 1.5}'
        result = compute_next_run(schedule, "UTC", after=REF)
        expected = datetime(2026, 6, 8, 13, 30, 0, tzinfo=UTC)
        assert result == expected

    def test_interval_long(self):
        schedule = '{"type": "interval", "hours": 24}'
        result = compute_next_run(schedule, "UTC", after=REF)
        expected = datetime(2026, 6, 9, 12, 0, 0, tzinfo=UTC)
        assert result == expected

    def test_unknown_type_falls_back_next_day(self):
        schedule = '{"type": "unknown", "hour": 6, "minute": 30}'
        result = compute_next_run(schedule, "UTC", after=REF)
        # Falls to: now_utc + 1 day
        expected = REF + timedelta(days=1)
        assert result == expected

    def test_no_after_uses_now(self):
        schedule = '{"type": "daily", "hour": 0, "minute": 0}'
        result = compute_next_run(schedule, "UTC")
        assert result is not None
        assert isinstance(result, datetime)
        assert result.tzinfo is not None

    def test_default_missing_type_is_daily(self):
        schedule = '{"hour": 10, "minute": 30}'
        result = compute_next_run(schedule, "UTC", after=REF)
        # Defaults to daily → next 10:30
        expected = datetime(2026, 6, 9, 10, 30, 0, tzinfo=UTC)
        assert result == expected

    def test_interval_min_hours(self):
        schedule = '{"type": "interval", "hours": 0.001}'
        result = compute_next_run(schedule, "UTC", after=REF)
        assert result > REF
        # clamped to min 1/60 hours (1 minute)
        diff = (result - REF).total_seconds()
        assert diff >= 60
