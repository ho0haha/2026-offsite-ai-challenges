#!/usr/bin/env python3
"""Tests for the waste_tracker module.

Participants must create a waste_tracker.py module that passes all these tests.
"""

import csv
import os
import tempfile
from datetime import date, datetime, timedelta

import pytest

from waste_tracker import WasteTracker


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tracker():
    """Return a fresh WasteTracker instance."""
    return WasteTracker()


@pytest.fixture
def populated_tracker():
    """Return a WasteTracker pre-loaded with sample data."""
    wt = WasteTracker()
    entries = [
        # Week 1 — moderate waste
        ("2025-01-06", "Chicken Wings", 5.0, "kg", "expired", "KFC"),
        ("2025-01-06", "Taco Shells", 2.0, "kg", "overproduction", "Taco Bell"),
        ("2025-01-07", "Pizza Dough", 3.5, "kg", "expired", "Pizza Hut"),
        ("2025-01-07", "Coleslaw", 1.5, "kg", "expired", "KFC"),
        ("2025-01-08", "Burrito Filling", 4.0, "kg", "overproduction", "Taco Bell"),
        ("2025-01-08", "Breadsticks", 2.0, "kg", "damaged", "Pizza Hut"),
        ("2025-01-09", "Chicken Breast", 6.0, "kg", "expired", "KFC"),
        ("2025-01-10", "Nachos", 1.0, "kg", "overproduction", "Taco Bell"),
        # Week 2 — higher waste
        ("2025-01-13", "Chicken Wings", 8.0, "kg", "expired", "KFC"),
        ("2025-01-14", "Pizza Dough", 5.0, "kg", "expired", "Pizza Hut"),
        ("2025-01-14", "Taco Shells", 3.0, "kg", "damaged", "Taco Bell"),
        ("2025-01-15", "Mashed Potatoes", 4.0, "kg", "overproduction", "KFC"),
        ("2025-01-16", "Cheese", 2.5, "kg", "expired", "Pizza Hut"),
        ("2025-01-17", "Chicken Breast", 7.0, "kg", "expired", "KFC"),
        # Week 3 — even higher waste
        ("2025-01-20", "Chicken Wings", 10.0, "kg", "expired", "KFC"),
        ("2025-01-21", "Pizza Dough", 6.0, "kg", "overproduction", "Pizza Hut"),
        ("2025-01-22", "Taco Shells", 5.0, "kg", "damaged", "Taco Bell"),
        ("2025-01-23", "Chicken Breast", 9.0, "kg", "expired", "KFC"),
        ("2025-01-24", "Burrito Filling", 6.0, "kg", "overproduction", "Taco Bell"),
    ]
    for entry in entries:
        wt.log_entry(
            date=entry[0],
            item=entry[1],
            quantity=entry[2],
            unit=entry[3],
            reason=entry[4],
            brand=entry[5],
        )
    return wt


# ---------------------------------------------------------------------------
# Test 1: Can create a WasteTracker instance
# ---------------------------------------------------------------------------

class TestCreateInstance:
    def test_create_instance(self, tracker):
        """WasteTracker can be instantiated."""
        assert tracker is not None
        assert isinstance(tracker, WasteTracker)


# ---------------------------------------------------------------------------
# Test 2: Can log a waste entry
# ---------------------------------------------------------------------------

class TestLogEntry:
    def test_log_single_entry(self, tracker):
        """Can log a waste entry with all required fields."""
        tracker.log_entry(
            date="2025-01-15",
            item="Chicken Wings",
            quantity=5.0,
            unit="kg",
            reason="expired",
            brand="KFC",
        )
        entries = tracker.get_entries()
        assert len(entries) == 1

    def test_log_multiple_entries(self, tracker):
        """Can log multiple entries."""
        tracker.log_entry(
            date="2025-01-15", item="Chicken Wings",
            quantity=5.0, unit="kg", reason="expired", brand="KFC",
        )
        tracker.log_entry(
            date="2025-01-15", item="Taco Shells",
            quantity=2.0, unit="kg", reason="overproduction", brand="Taco Bell",
        )
        tracker.log_entry(
            date="2025-01-16", item="Pizza Dough",
            quantity=3.5, unit="kg", reason="expired", brand="Pizza Hut",
        )
        entries = tracker.get_entries()
        assert len(entries) == 3

    def test_entry_contains_fields(self, tracker):
        """Logged entries contain all expected fields."""
        tracker.log_entry(
            date="2025-01-15",
            item="Chicken Wings",
            quantity=5.0,
            unit="kg",
            reason="expired",
            brand="KFC",
        )
        entries = tracker.get_entries()
        entry = entries[0]
        # Entry should be accessible as dict or have these attributes
        if isinstance(entry, dict):
            assert entry["item"] == "Chicken Wings"
            assert entry["quantity"] == 5.0
            assert entry["brand"] == "KFC"
            assert entry["reason"] == "expired"
        else:
            assert entry.item == "Chicken Wings"
            assert entry.quantity == 5.0
            assert entry.brand == "KFC"
            assert entry.reason == "expired"


# ---------------------------------------------------------------------------
# Test 3: Can retrieve entries by date range
# ---------------------------------------------------------------------------

class TestGetByDateRange:
    def test_get_entries_by_date_range(self, populated_tracker):
        """Can filter entries within a date range."""
        entries = populated_tracker.get_entries_by_date_range("2025-01-06", "2025-01-10")
        # Week 1 has 8 entries (Jan 6-10)
        assert len(entries) == 8

    def test_date_range_subset(self, populated_tracker):
        """Date range correctly filters to a subset."""
        entries = populated_tracker.get_entries_by_date_range("2025-01-13", "2025-01-14")
        # Jan 13: 1 entry, Jan 14: 2 entries = 3
        assert len(entries) == 3

    def test_date_range_no_results(self, populated_tracker):
        """Date range with no matching entries returns empty."""
        entries = populated_tracker.get_entries_by_date_range("2025-03-01", "2025-03-31")
        assert len(entries) == 0


# ---------------------------------------------------------------------------
# Test 4: Can retrieve entries by brand
# ---------------------------------------------------------------------------

class TestGetByBrand:
    def test_get_kfc_entries(self, populated_tracker):
        """Can filter entries for KFC."""
        entries = populated_tracker.get_entries_by_brand("KFC")
        assert len(entries) == 7

    def test_get_taco_bell_entries(self, populated_tracker):
        """Can filter entries for Taco Bell."""
        entries = populated_tracker.get_entries_by_brand("Taco Bell")
        assert len(entries) == 6

    def test_get_pizza_hut_entries(self, populated_tracker):
        """Can filter entries for Pizza Hut."""
        entries = populated_tracker.get_entries_by_brand("Pizza Hut")
        assert len(entries) == 6

    def test_brand_not_found(self, populated_tracker):
        """Unknown brand returns empty list."""
        entries = populated_tracker.get_entries_by_brand("Wendy's")
        assert len(entries) == 0


# ---------------------------------------------------------------------------
# Test 5: Can calculate total waste by category/reason
# ---------------------------------------------------------------------------

class TestTotalByReason:
    def test_total_by_reason(self, populated_tracker):
        """Can calculate total waste grouped by reason."""
        totals = populated_tracker.total_waste_by_reason()
        # totals should be a dict: reason -> total quantity
        assert isinstance(totals, dict)
        assert "expired" in totals
        assert "overproduction" in totals
        assert "damaged" in totals

    def test_expired_total(self, populated_tracker):
        """Expired total is correct."""
        totals = populated_tracker.total_waste_by_reason()
        # expired entries: 5 + 3.5 + 1.5 + 6 + 8 + 5 + 2.5 + 7 + 10 + 9 = 57.5
        assert abs(totals["expired"] - 57.5) < 0.01

    def test_overproduction_total(self, populated_tracker):
        """Overproduction total is correct."""
        totals = populated_tracker.total_waste_by_reason()
        # overproduction: 2 + 4 + 1 + 4 + 6 + 6 = 23.0
        assert abs(totals["overproduction"] - 23.0) < 0.01

    def test_damaged_total(self, populated_tracker):
        """Damaged total is correct."""
        totals = populated_tracker.total_waste_by_reason()
        # damaged: 2 + 3 + 5 = 10.0
        assert abs(totals["damaged"] - 10.0) < 0.01


# ---------------------------------------------------------------------------
# Test 6: Can calculate daily average waste
# ---------------------------------------------------------------------------

class TestDailyAverage:
    def test_daily_average(self, populated_tracker):
        """Daily average waste is calculated correctly."""
        avg = populated_tracker.daily_average_waste()
        # Total waste = 57.5 + 23.0 + 10.0 = 90.5
        # Unique days: Jan 6,7,8,9,10, 13,14,15,16,17, 20,21,22,23,24 = 15 days
        expected = 90.5 / 15
        assert abs(avg - expected) < 0.1

    def test_daily_average_empty(self, tracker):
        """Daily average on empty tracker returns 0."""
        avg = tracker.daily_average_waste()
        assert avg == 0.0


# ---------------------------------------------------------------------------
# Test 7: Can identify top wasted items
# ---------------------------------------------------------------------------

class TestTopWastedItems:
    def test_top_items_returns_list(self, populated_tracker):
        """top_wasted_items returns a list."""
        top = populated_tracker.top_wasted_items(n=3)
        assert isinstance(top, list)
        assert len(top) == 3

    def test_top_item_is_chicken(self, populated_tracker):
        """The most wasted item is Chicken Wings or Chicken Breast."""
        top = populated_tracker.top_wasted_items(n=1)
        # Each element should be a tuple/list of (item_name, total_quantity) or similar
        if isinstance(top[0], (tuple, list)):
            top_item_name = top[0][0]
        elif isinstance(top[0], dict):
            top_item_name = top[0].get("item") or top[0].get("name")
        else:
            top_item_name = str(top[0])
        # Chicken Wings: 5 + 8 + 10 = 23  |  Chicken Breast: 6 + 7 + 9 = 22
        assert "Chicken Wings" in top_item_name

    def test_top_items_order(self, populated_tracker):
        """Top wasted items are ordered descending by quantity."""
        top = populated_tracker.top_wasted_items(n=5)
        quantities = []
        for item in top:
            if isinstance(item, (tuple, list)):
                quantities.append(item[1])
            elif isinstance(item, dict):
                quantities.append(item.get("quantity") or item.get("total"))
        # Verify descending order
        for i in range(len(quantities) - 1):
            assert quantities[i] >= quantities[i + 1]


# ---------------------------------------------------------------------------
# Test 8: Can calculate waste trend
# ---------------------------------------------------------------------------

class TestWasteTrend:
    def test_trend_increasing(self, populated_tracker):
        """Waste trend over the 3-week period is increasing."""
        trend = populated_tracker.waste_trend(
            start_date="2025-01-06",
            end_date="2025-01-24",
            period="weekly",
        )
        # trend should be a string like "increasing", "decreasing", or "stable"
        assert trend.lower() in ("increasing", "decreasing", "stable")
        # Our data is designed to be increasing week-over-week
        assert trend.lower() == "increasing"

    def test_trend_returns_string(self, populated_tracker):
        """waste_trend returns a string."""
        trend = populated_tracker.waste_trend(
            start_date="2025-01-06",
            end_date="2025-01-24",
            period="weekly",
        )
        assert isinstance(trend, str)


# ---------------------------------------------------------------------------
# Test 9: Can export data to CSV
# ---------------------------------------------------------------------------

class TestExportCSV:
    def test_export_creates_file(self, populated_tracker):
        """export_to_csv creates a CSV file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            path = f.name
        try:
            populated_tracker.export_to_csv(path)
            assert os.path.exists(path)
        finally:
            os.unlink(path)

    def test_export_has_header(self, populated_tracker):
        """Exported CSV has a header row."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            path = f.name
        try:
            populated_tracker.export_to_csv(path)
            with open(path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader)
            expected_fields = {"date", "item", "quantity", "unit", "reason", "brand"}
            header_lower = {h.lower().strip() for h in header}
            assert expected_fields.issubset(header_lower)
        finally:
            os.unlink(path)

    def test_export_row_count(self, populated_tracker):
        """Exported CSV has the correct number of data rows."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            path = f.name
        try:
            populated_tracker.export_to_csv(path)
            with open(path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                next(reader)  # skip header
                rows = list(reader)
            assert len(rows) == 19
        finally:
            os.unlink(path)


# ---------------------------------------------------------------------------
# Test 10: Handles edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_empty_entries(self, tracker):
        """get_entries on empty tracker returns empty list."""
        entries = tracker.get_entries()
        assert entries == [] or len(entries) == 0

    def test_negative_quantity_raises(self, tracker):
        """Logging a negative quantity raises ValueError."""
        with pytest.raises(ValueError):
            tracker.log_entry(
                date="2025-01-15",
                item="Chicken",
                quantity=-5.0,
                unit="kg",
                reason="expired",
                brand="KFC",
            )

    def test_invalid_date_raises(self, tracker):
        """Logging an invalid date raises ValueError."""
        with pytest.raises(ValueError):
            tracker.log_entry(
                date="not-a-date",
                item="Chicken",
                quantity=5.0,
                unit="kg",
                reason="expired",
                brand="KFC",
            )

    def test_zero_quantity_allowed(self, tracker):
        """Logging zero quantity is allowed (not negative)."""
        tracker.log_entry(
            date="2025-01-15",
            item="Chicken",
            quantity=0.0,
            unit="kg",
            reason="expired",
            brand="KFC",
        )
        entries = tracker.get_entries()
        assert len(entries) == 1

    def test_empty_date_range(self, tracker):
        """Date range query on empty tracker returns empty list."""
        entries = tracker.get_entries_by_date_range("2025-01-01", "2025-12-31")
        assert len(entries) == 0
