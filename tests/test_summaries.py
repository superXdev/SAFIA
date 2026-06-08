"""Tests for financial summary builders (pure functions)."""
from datetime import date

import pytest

from services.summaries import (
    build_assets_summary,
    build_rebalance_suggestion,
    build_records_summary,
)


class TestBuildRecordsSummary:
    def test_empty(self):
        result = build_records_summary([], [])
        assert result["total_income"] == 0.0
        assert result["total_expense"] == 0.0
        assert result["total_balance"] == 0.0
        assert result["per_category"] == {}
        assert result["record_count"] == 0
        assert result["debt_count"] == 0

    def test_income_only(self):
        records = [
            {"amount": 5000000.0, "type": "income", "category": "Gaji"},
            {"amount": 2000000.0, "type": "income", "category": "Freelance"},
        ]
        result = build_records_summary(records, [])
        assert result["total_income"] == 7000000.0
        assert result["total_expense"] == 0.0
        assert result["total_balance"] == 7000000.0
        assert result["record_count"] == 2

    def test_expense_only(self):
        records = [
            {"amount": 500000.0, "type": "expense", "category": "Makanan"},
            {"amount": 300000.0, "type": "expense", "category": "Transportasi"},
            {"amount": 200000.0, "type": "expense", "category": "Makanan"},
        ]
        result = build_records_summary(records, [])
        assert result["total_income"] == 0.0
        assert result["total_expense"] == 1000000.0
        assert result["total_balance"] == -1000000.0
        assert result["per_category"]["Makanan"] == 700000.0
        assert result["per_category"]["Transportasi"] == 300000.0

    def test_mixed_income_expense(self):
        records = [
            {"amount": 10000000.0, "type": "income", "category": "Gaji"},
            {"amount": 3000000.0, "type": "expense", "category": "Makanan"},
            {"amount": 1500000.0, "type": "expense", "category": "Cicilan"},
        ]
        result = build_records_summary(records, [])
        assert result["total_income"] == 10000000.0
        assert result["total_expense"] == 4500000.0
        assert result["total_balance"] == 5500000.0

    def test_no_category_defaults(self):
        records = [{"amount": 100000.0, "type": "expense", "category": ""}]
        result = build_records_summary(records, [])
        assert "Tanpa kategori" in result["per_category"]

    def test_with_debts_lent(self):
        debts = [
            {"amount": 2000000.0, "direction": "lent", "person": "Budi", "is_settled": False},
            {"amount": 1000000.0, "direction": "lent", "person": "Ani", "is_settled": True},
        ]
        records = [{"amount": 5000000.0, "type": "income", "category": "Gaji"}]
        result = build_records_summary(records, debts)
        assert result["total_lent"] == 3000000.0
        assert result["total_lent_outstanding"] == 2000000.0
        assert result["total_balance"] == 3000000.0  # 5M - 2M outstanding
        assert result["debt_count"] == 2

    def test_with_debts_borrowed(self):
        debts = [
            {"amount": 500000.0, "direction": "borrowed", "person": "Bank", "is_settled": False},
        ]
        records = [{"amount": 2000000.0, "type": "income", "category": "Gaji"}]
        result = build_records_summary(records, debts)
        assert result["total_borrowed"] == 500000.0
        assert result["total_borrowed_outstanding"] == 500000.0
        assert result["total_balance"] == 2500000.0  # 2M + 500k borrowed

    def test_complex_scenario(self):
        records = [
            {"amount": 8000000.0, "type": "income", "category": "Gaji"},
            {"amount": 1000000.0, "type": "expense", "category": "Makanan"},
            {"amount": 500000.0, "type": "expense", "category": "Transportasi"},
            {"amount": 2000000.0, "type": "expense", "category": "Cicilan"},
        ]
        debts = [
            {"amount": 1000000.0, "direction": "lent", "person": "Budi", "is_settled": False},
            {"amount": 3000000.0, "direction": "borrowed", "person": "KPR", "is_settled": False},
        ]
        result = build_records_summary(records, debts)
        assert result["total_income"] == 8000000.0
        assert result["total_expense"] == 3500000.0
        # 8M - 3.5M - 1M lent + 3M borrowed = 6.5M
        assert result["total_balance"] == 6500000.0


class TestBuildAssetsSummary:
    def test_empty(self):
        result = build_assets_summary([])
        assert result["total_value"] == 0.0
        assert result["by_type"] == {}
        assert result["allocation_percent"] == {}
        assert result["asset_count"] == 0

    def test_single_asset(self):
        assets = [
            {"asset_type": "stocks", "name": "TLKM", "value": 5000000.0, "quantity": 100, "unit_value": 50000.0},
        ]
        result = build_assets_summary(assets)
        assert result["total_value"] == 5000000.0
        assert result["by_type"]["stocks"] == 5000000.0
        assert result["allocation_percent"]["stocks"] == 100.0
        assert result["asset_count"] == 1

    def test_multiple_assets_same_type(self):
        assets = [
            {"asset_type": "stocks", "name": "TLKM", "value": 3000000.0, "quantity": 100, "unit_value": 30000.0},
            {"asset_type": "stocks", "name": "BBCA", "value": 7000000.0, "quantity": 700, "unit_value": 10000.0},
        ]
        result = build_assets_summary(assets)
        assert result["total_value"] == 10000000.0
        assert result["by_type"]["stocks"] == 10000000.0
        assert result["allocation_percent"]["stocks"] == 100.0
        assert result["asset_count"] == 2

    def test_diversified_portfolio(self):
        assets = [
            {"asset_type": "stocks", "name": "TLKM", "value": 5000000.0, "quantity": 100, "unit_value": 50000.0},
            {"asset_type": "crypto", "name": "BTC", "value": 3000000.0, "quantity": 0.01, "unit_value": 300000000.0},
            {"asset_type": "gold", "name": "Antam", "value": 2000000.0, "quantity": 2, "unit_value": 1000000.0},
        ]
        result = build_assets_summary(assets)
        assert result["total_value"] == 10000000.0
        assert result["by_type"]["stocks"] == 5000000.0
        assert result["by_type"]["crypto"] == 3000000.0
        assert result["by_type"]["gold"] == 2000000.0
        # Check allocation percentages sum to ~100
        total_pct = sum(result["allocation_percent"].values())
        assert abs(total_pct - 100.0) < 0.1


class TestBuildRebalanceSuggestion:
    def test_single_type_already_at_target(self):
        assets = [{"asset_type": "stocks", "name": "TLKM", "value": 10000000.0, "quantity": 100, "unit_value": 100000.0}]
        target = {"stocks": 100.0}
        result = build_rebalance_suggestion(assets, target)
        assert len(result["suggestions"]) == 1
        s = result["suggestions"][0]
        assert s["action"] == "pertahankan"
        assert s["difference_idr"] == 0.0

    def test_needs_rebalancing(self):
        assets = [
            {"asset_type": "stocks", "name": "TLKM", "value": 7000000.0, "quantity": 100, "unit_value": 70000.0},
            {"asset_type": "crypto", "name": "BTC", "value": 3000000.0, "quantity": 0.01, "unit_value": 300000000.0},
        ]
        target = {"stocks": 50.0, "crypto": 30.0, "gold": 20.0}
        result = build_rebalance_suggestion(assets, target)
        suggestions = {s["asset_type"]: s for s in result["suggestions"]}
        assert suggestions["stocks"]["action"] == "jual"  # 70% > 50%
        assert suggestions["crypto"]["action"] == "pertahankan"  # 30% == 30%
        assert suggestions["gold"]["action"] == "beli"  # 0% < 20%
        assert suggestions["gold"]["current_value"] == 0.0
        assert suggestions["gold"]["target_value"] == 2000000.0

    def test_empty_portfolio(self):
        result = build_rebalance_suggestion([], {"stocks": 60.0, "crypto": 40.0})
        assert result["total_portfolio_value"] == 0.0

    def test_partial_types_in_target(self):
        assets = [
            {"asset_type": "stocks", "name": "TLKM", "value": 4000000.0, "quantity": 100, "unit_value": 40000.0},
            {"asset_type": "crypto", "name": "BTC", "value": 6000000.0, "quantity": 0.02, "unit_value": 300000000.0},
        ]
        target = {"stocks": 40.0, "crypto": 40.0, "gold": 20.0}
        result = build_rebalance_suggestion(assets, target)
        # Target sum = 40+40+20 = 100, normalized is same
        suggestions = {s["asset_type"]: s for s in result["suggestions"]}
        # stocks: 40% current == 40% target → pertahankan
        assert suggestions["stocks"]["action"] == "pertahankan"
        # crypto: 60% current > 40% target → jual
        assert suggestions["crypto"]["action"] == "jual"
        # gold: 0% < 20% target → beli
        assert suggestions["gold"]["action"] == "beli"
        assert suggestions["gold"]["target_value"] == 2000000.0
