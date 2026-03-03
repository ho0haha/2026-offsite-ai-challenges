"""
Hypothesis property-based tests for the Fuzz Gauntlet challenge.

These tests generate 10,000+ random inputs per function and verify
that key invariants always hold. Your implementations in functions.py
must pass all of these.
"""

import math
from datetime import datetime, timedelta

import pytz
import pytest
from hypothesis import given, settings, assume, HealthCheck
from hypothesis import strategies as st

from functions import (
    calculate_bill,
    schedule_reservation,
    parse_order,
    reconcile_inventory,
)
from models import (
    BillResult,
    ParsedOrder,
    ParseError,
    Reservation,
    ScheduleResult,
    ReconciledInventory,
    AuditEntry,
)

# =====================================================================
# Strategies
# =====================================================================

# --- Bill strategies ---

reasonable_price = st.floats(min_value=0.0, max_value=10000.0, allow_nan=False, allow_infinity=False)
reasonable_quantity = st.integers(min_value=0, max_value=100)
reasonable_tax_rate = st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)

item_strategy = st.fixed_dictionaries({
    "name": st.text(min_size=1, max_size=30),
    "price": reasonable_price,
    "quantity": reasonable_quantity,
})

pct_coupon = st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False).map(
    lambda v: f"PCT:{v:.2f}"
)
fixed_coupon = st.floats(min_value=0.0, max_value=500.0, allow_nan=False, allow_infinity=False).map(
    lambda v: f"FIXED:{v:.2f}"
)
coupon_strategy = st.one_of(pct_coupon, fixed_coupon)

# --- Reservation strategies ---

SAFE_TIMEZONES = [
    "UTC", "US/Eastern", "US/Central", "US/Mountain", "US/Pacific",
    "Europe/London", "Europe/Paris", "Europe/Berlin", "Asia/Tokyo",
    "Asia/Kolkata", "Australia/Sydney", "America/New_York",
    "America/Chicago", "America/Denver", "America/Los_Angeles",
]

safe_timezone = st.sampled_from(SAFE_TIMEZONES)

# Build datetimes that avoid DST gaps: use summer months and afternoon hours
safe_datetime = st.builds(
    datetime,
    year=st.just(2025),
    month=st.sampled_from([1, 6, 7, 8]),
    day=st.integers(min_value=1, max_value=28),
    hour=st.integers(min_value=12, max_value=20),
    minute=st.sampled_from([0, 15, 30, 45]),
)

reservation_name = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N", "Zs"), min_codepoint=32, max_codepoint=126),
    min_size=1,
    max_size=30,
).filter(lambda s: s.strip() != "")


@st.composite
def reservation_strategy(draw):
    """Generate a valid Reservation with positive duration."""
    start = draw(safe_datetime)
    duration_minutes = draw(st.integers(min_value=30, max_value=180))
    end = start + timedelta(minutes=duration_minutes)
    party_size = draw(st.integers(min_value=1, max_value=20))
    tz = draw(safe_timezone)
    name = draw(reservation_name)
    return Reservation(start=start, end=end, party_size=party_size, timezone=tz, name=name)


# --- Order text strategies ---

menu_items = [
    "burger", "cheeseburger", "fries", "french fries", "coke", "pepsi",
    "water", "orange juice", "blt sandwich", "coffee", "espresso",
    "chicken", "salad", "sandwich", "wrap", "pizza", "pasta", "soup",
    "steak", "fish", "tacos",
]

modifier_list = [
    "no onion", "extra cheese", "well done", "medium rare", "no ice",
    "extra ice", "spicy", "mild", "no pickles", "extra pickles",
    "no mayo", "to go", "for here", "large", "small",
]


@st.composite
def valid_order_text(draw):
    """Generate a plausible order text string."""
    n_items = draw(st.integers(min_value=1, max_value=5))
    parts = []
    for _ in range(n_items):
        qty = draw(st.integers(min_value=1, max_value=10))
        item = draw(st.sampled_from(menu_items))
        if draw(st.booleans()):
            mod = draw(st.sampled_from(modifier_list))
            parts.append(f"{qty}x {item} {mod}")
        else:
            parts.append(f"{qty}x {item}")
    return ", ".join(parts)


# --- Inventory strategies ---

inventory_key = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N"), min_codepoint=48, max_codepoint=122),
    min_size=1,
    max_size=20,
)
inventory_qty = st.integers(min_value=0, max_value=10000)
inventory_source = st.dictionaries(inventory_key, inventory_qty, min_size=0, max_size=20)


# =====================================================================
# 1. calculate_bill property tests
# =====================================================================

class TestCalculateBill:

    @settings(max_examples=10000, suppress_health_check=[HealthCheck.too_slow])
    @given(
        items=st.lists(item_strategy, min_size=0, max_size=10),
        coupons=st.lists(coupon_strategy, min_size=0, max_size=5),
        tax_rate=reasonable_tax_rate,
    )
    def test_total_is_non_negative(self, items, coupons, tax_rate):
        """The total must always be >= 0, no matter how many coupons."""
        result = calculate_bill(items, coupons, tax_rate)
        assert result.total >= 0

    @settings(max_examples=10000, suppress_health_check=[HealthCheck.too_slow])
    @given(
        items=st.lists(item_strategy, min_size=0, max_size=10),
        coupons=st.lists(coupon_strategy, min_size=0, max_size=5),
        tax_rate=reasonable_tax_rate,
    )
    def test_tax_applied_after_discounts(self, items, coupons, tax_rate):
        """Tax must be computed on the discounted subtotal, not the original."""
        result = calculate_bill(items, coupons, tax_rate)
        discounted = round(result.subtotal - result.discount_total, 2)
        discounted = max(discounted, 0.0)
        expected_tax = round(discounted * tax_rate, 2)
        assert abs(result.tax - expected_tax) < 0.02

    @settings(max_examples=10000, suppress_health_check=[HealthCheck.too_slow])
    @given(
        items=st.lists(item_strategy, min_size=0, max_size=10),
        coupons=st.lists(coupon_strategy, min_size=0, max_size=5),
        tax_rate=reasonable_tax_rate,
    )
    def test_total_equals_discounted_plus_tax(self, items, coupons, tax_rate):
        """total == (subtotal - discount_total) + tax (clamped to >= 0)."""
        result = calculate_bill(items, coupons, tax_rate)
        discounted = max(round(result.subtotal - result.discount_total, 2), 0.0)
        expected_total = round(discounted + result.tax, 2)
        assert abs(result.total - expected_total) < 0.02

    @settings(max_examples=10000, suppress_health_check=[HealthCheck.too_slow])
    @given(tax_rate=reasonable_tax_rate)
    def test_empty_items_zero_total(self, tax_rate):
        """An empty items list must always yield a zero bill."""
        result = calculate_bill([], [], tax_rate)
        assert result.subtotal == 0.0
        assert result.discount_total == 0.0
        assert result.tax == 0.0
        assert result.total == 0.0

    @settings(max_examples=10000, suppress_health_check=[HealthCheck.too_slow])
    @given(
        items=st.lists(item_strategy, min_size=1, max_size=5),
        tax_rate=reasonable_tax_rate,
    )
    def test_subtotal_is_sum_of_line_items(self, items, tax_rate):
        """Subtotal must equal the sum of individual line totals."""
        result = calculate_bill(items, [], tax_rate)
        line_sum = sum(li["line_total"] for li in result.line_items)
        assert abs(result.subtotal - round(line_sum, 2)) < 0.02

    @settings(max_examples=10000, suppress_health_check=[HealthCheck.too_slow])
    @given(
        items=st.lists(item_strategy, min_size=0, max_size=5),
        tax_rate=reasonable_tax_rate,
    )
    def test_line_items_count_matches(self, items, tax_rate):
        """Number of line items in result must match input items count."""
        result = calculate_bill(items, [], tax_rate)
        assert len(result.line_items) == len(items)

    @settings(max_examples=10000, suppress_health_check=[HealthCheck.too_slow])
    @given(
        items=st.lists(item_strategy, min_size=1, max_size=5),
        coupons=st.lists(coupon_strategy, min_size=0, max_size=5),
        tax_rate=reasonable_tax_rate,
    )
    def test_discount_does_not_exceed_subtotal(self, items, coupons, tax_rate):
        """The effective discount should not exceed the subtotal."""
        result = calculate_bill(items, coupons, tax_rate)
        assert result.discount_total <= result.subtotal + 0.01

    def test_nan_price_raises(self):
        """NaN price must raise ValueError."""
        with pytest.raises(ValueError):
            calculate_bill([{"name": "x", "price": float("nan"), "quantity": 1}], [], 0.1)

    def test_inf_price_raises(self):
        """Inf price must raise ValueError."""
        with pytest.raises(ValueError):
            calculate_bill([{"name": "x", "price": float("inf"), "quantity": 1}], [], 0.1)

    def test_negative_price_raises(self):
        """Negative price must raise ValueError."""
        with pytest.raises(ValueError):
            calculate_bill([{"name": "x", "price": -5.0, "quantity": 1}], [], 0.1)

    def test_negative_quantity_raises(self):
        """Negative quantity must raise ValueError."""
        with pytest.raises(ValueError):
            calculate_bill([{"name": "x", "price": 5.0, "quantity": -1}], [], 0.1)

    def test_nan_tax_rate_raises(self):
        """NaN tax_rate must raise ValueError."""
        with pytest.raises(ValueError):
            calculate_bill([], [], float("nan"))

    def test_tax_rate_above_one_raises(self):
        """tax_rate > 1 must raise ValueError."""
        with pytest.raises(ValueError):
            calculate_bill([], [], 1.5)

    def test_tax_rate_negative_raises(self):
        """Negative tax_rate must raise ValueError."""
        with pytest.raises(ValueError):
            calculate_bill([], [], -0.1)


# =====================================================================
# 2. schedule_reservation property tests
# =====================================================================

class TestScheduleReservation:

    @settings(max_examples=10000, suppress_health_check=[HealthCheck.too_slow])
    @given(
        existing=st.lists(reservation_strategy(), min_size=0, max_size=5),
        new=reservation_strategy(),
    )
    def test_result_contains_all_reservations(self, existing, new):
        """The result must contain all existing reservations plus the new one."""
        result = schedule_reservation(existing, new)
        assert len(result.reservations) == len(existing) + 1

    @settings(max_examples=10000, suppress_health_check=[HealthCheck.too_slow])
    @given(new=reservation_strategy())
    def test_no_conflicts_when_empty(self, new):
        """With no existing reservations, there should be no conflicts."""
        result = schedule_reservation([], new)
        assert len(result.conflicts) == 0
        assert len(result.reservations) == 1

    @settings(max_examples=10000, suppress_health_check=[HealthCheck.too_slow])
    @given(
        existing=st.lists(reservation_strategy(), min_size=0, max_size=5),
        new=reservation_strategy(),
    )
    def test_conflicts_involve_new_reservation(self, existing, new):
        """Every conflict tuple must involve the new reservation."""
        result = schedule_reservation(existing, new)
        for ex, n in result.conflicts:
            assert n is new or n == new

    @settings(max_examples=10000, suppress_health_check=[HealthCheck.too_slow])
    @given(new=reservation_strategy())
    def test_reservations_is_list(self, new):
        """Result reservations must be a list."""
        result = schedule_reservation([], new)
        assert isinstance(result.reservations, list)

    def test_invalid_timezone_raises(self):
        """Invalid timezone string must raise ValueError."""
        r = Reservation(
            start=datetime(2025, 6, 15, 14, 0),
            end=datetime(2025, 6, 15, 15, 0),
            party_size=2,
            timezone="Not/A/Timezone",
            name="Test",
        )
        with pytest.raises(ValueError):
            schedule_reservation([], r)

    def test_zero_party_size_raises(self):
        """party_size < 1 must raise ValueError."""
        r = Reservation(
            start=datetime(2025, 6, 15, 14, 0),
            end=datetime(2025, 6, 15, 15, 0),
            party_size=0,
            timezone="UTC",
            name="Test",
        )
        with pytest.raises(ValueError):
            schedule_reservation([], r)

    def test_negative_duration_raises(self):
        """end <= start must raise ValueError."""
        r = Reservation(
            start=datetime(2025, 6, 15, 15, 0),
            end=datetime(2025, 6, 15, 14, 0),
            party_size=2,
            timezone="UTC",
            name="Test",
        )
        with pytest.raises(ValueError):
            schedule_reservation([], r)

    def test_dst_gap_raises(self):
        """A reservation in a DST spring-forward gap must raise ValueError."""
        # US/Eastern springs forward at 2:00 AM on 2025-03-09
        r = Reservation(
            start=datetime(2025, 3, 9, 2, 30),
            end=datetime(2025, 3, 9, 3, 30),
            party_size=2,
            timezone="US/Eastern",
            name="Test",
        )
        with pytest.raises(ValueError):
            schedule_reservation([], r)

    def test_empty_name_raises(self):
        """Empty or whitespace-only name must raise ValueError."""
        r = Reservation(
            start=datetime(2025, 6, 15, 14, 0),
            end=datetime(2025, 6, 15, 15, 0),
            party_size=2,
            timezone="UTC",
            name="   ",
        )
        with pytest.raises(ValueError):
            schedule_reservation([], r)

    def test_overlap_detected(self):
        """Two clearly overlapping reservations must produce a conflict."""
        existing = [Reservation(
            start=datetime(2025, 6, 15, 14, 0),
            end=datetime(2025, 6, 15, 16, 0),
            party_size=2,
            timezone="UTC",
            name="First",
        )]
        new = Reservation(
            start=datetime(2025, 6, 15, 15, 0),
            end=datetime(2025, 6, 15, 17, 0),
            party_size=3,
            timezone="UTC",
            name="Second",
        )
        result = schedule_reservation(existing, new)
        assert len(result.conflicts) == 1


# =====================================================================
# 3. parse_order property tests
# =====================================================================

class TestParseOrder:

    @settings(max_examples=10000, suppress_health_check=[HealthCheck.too_slow])
    @given(text=st.text(min_size=0, max_size=500))
    def test_never_raises(self, text):
        """parse_order must NEVER raise an exception, no matter the input."""
        result = parse_order(text)
        assert isinstance(result, (ParsedOrder, ParseError))

    @settings(max_examples=10000, suppress_health_check=[HealthCheck.too_slow])
    @given(text=valid_order_text())
    def test_valid_order_has_items(self, text):
        """A well-formed order should parse into at least one item."""
        result = parse_order(text)
        if isinstance(result, ParsedOrder):
            assert len(result.items) >= 1

    @settings(max_examples=10000, suppress_health_check=[HealthCheck.too_slow])
    @given(text=valid_order_text())
    def test_items_and_quantities_same_length(self, text):
        """items and quantities lists must always be the same length."""
        result = parse_order(text)
        if isinstance(result, ParsedOrder):
            assert len(result.items) == len(result.quantities)

    @settings(max_examples=10000, suppress_health_check=[HealthCheck.too_slow])
    @given(text=valid_order_text())
    def test_quantities_are_positive(self, text):
        """All quantities must be >= 1."""
        result = parse_order(text)
        if isinstance(result, ParsedOrder):
            for q in result.quantities:
                assert q >= 1

    @settings(max_examples=10000, suppress_health_check=[HealthCheck.too_slow])
    @given(text=valid_order_text())
    def test_raw_text_preserved(self, text):
        """The raw_text field must contain the original input."""
        result = parse_order(text)
        if isinstance(result, ParsedOrder):
            assert result.raw_text == text

    @settings(max_examples=10000, suppress_health_check=[HealthCheck.too_slow])
    @given(text=st.text(min_size=0, max_size=200))
    def test_unicode_safety(self, text):
        """Arbitrary unicode must not crash the parser."""
        result = parse_order(text)
        assert isinstance(result, (ParsedOrder, ParseError))

    @settings(max_examples=10000, suppress_health_check=[HealthCheck.too_slow])
    @given(
        text=st.sampled_from([
            "<script>alert('xss')</script>",
            "'; DROP TABLE orders; --",
            "burger\x00\x00fries",
            "\ud800 invalid surrogate",
            "A" * 10000,
            "\n\n\n\n\n",
            "1x \t\t\t burger",
        ])
    )
    def test_injection_safety(self, text):
        """Injection-like inputs must not crash the parser."""
        result = parse_order(text)
        assert isinstance(result, (ParsedOrder, ParseError))

    def test_empty_string_returns_error(self):
        """Empty string must return ParseError."""
        result = parse_order("")
        assert isinstance(result, ParseError)

    def test_whitespace_only_returns_error(self):
        """Whitespace-only string must return ParseError."""
        result = parse_order("   \t\n  ")
        assert isinstance(result, ParseError)

    @settings(max_examples=10000, suppress_health_check=[HealthCheck.too_slow])
    @given(text=valid_order_text())
    def test_items_are_strings(self, text):
        """All parsed item names must be strings."""
        result = parse_order(text)
        if isinstance(result, ParsedOrder):
            for item in result.items:
                assert isinstance(item, str)
                assert len(item) > 0

    @settings(max_examples=10000, suppress_health_check=[HealthCheck.too_slow])
    @given(text=valid_order_text())
    def test_modifiers_are_strings(self, text):
        """All parsed modifiers must be strings."""
        result = parse_order(text)
        if isinstance(result, ParsedOrder):
            for mod in result.modifiers:
                assert isinstance(mod, str)


# =====================================================================
# 4. reconcile_inventory property tests
# =====================================================================

class TestReconcileInventory:

    @settings(max_examples=10000, suppress_health_check=[HealthCheck.too_slow])
    @given(
        source_a=inventory_source,
        source_b=inventory_source,
        source_c=inventory_source,
    )
    def test_all_items_present(self, source_a, source_b, source_c):
        """Every item from any source must appear in the result."""
        result = reconcile_inventory(source_a, source_b, source_c)
        all_keys = set(source_a) | set(source_b) | set(source_c)
        assert set(result.items.keys()) == all_keys

    @settings(max_examples=10000, suppress_health_check=[HealthCheck.too_slow])
    @given(
        source_a=inventory_source,
        source_b=inventory_source,
        source_c=inventory_source,
    )
    def test_quantities_non_negative(self, source_a, source_b, source_c):
        """All resolved quantities must be >= 0."""
        result = reconcile_inventory(source_a, source_b, source_c)
        for qty in result.items.values():
            assert qty >= 0

    @settings(max_examples=10000, suppress_health_check=[HealthCheck.too_slow])
    @given(
        source_a=inventory_source,
        source_b=inventory_source,
        source_c=inventory_source,
    )
    def test_deterministic(self, source_a, source_b, source_c):
        """Same inputs must always produce the same output."""
        r1 = reconcile_inventory(source_a, source_b, source_c)
        r2 = reconcile_inventory(source_a, source_b, source_c)
        assert r1.items == r2.items
        assert r1.conflicts == r2.conflicts

    @settings(max_examples=10000, suppress_health_check=[HealthCheck.too_slow])
    @given(
        source_a=inventory_source,
        source_b=inventory_source,
        source_c=inventory_source,
    )
    def test_audit_trail_complete(self, source_a, source_b, source_c):
        """Every item must have exactly one audit trail entry."""
        result = reconcile_inventory(source_a, source_b, source_c)
        audit_items = [entry.item for entry in result.audit_trail]
        assert len(audit_items) == len(result.items)
        assert set(audit_items) == set(result.items.keys())

    @settings(max_examples=10000, suppress_health_check=[HealthCheck.too_slow])
    @given(
        source_a=inventory_source,
        source_b=inventory_source,
        source_c=inventory_source,
    )
    def test_audit_trail_entries_valid(self, source_a, source_b, source_c):
        """Audit trail entries must have valid structure."""
        result = reconcile_inventory(source_a, source_b, source_c)
        for entry in result.audit_trail:
            assert isinstance(entry, AuditEntry)
            assert isinstance(entry.item, str)
            assert isinstance(entry.sources, dict)
            assert isinstance(entry.resolved_quantity, int)
            assert isinstance(entry.resolution_method, str)
            assert entry.resolved_quantity >= 0

    @settings(max_examples=10000, suppress_health_check=[HealthCheck.too_slow])
    @given(
        source_a=inventory_source,
        source_b=inventory_source,
        source_c=inventory_source,
    )
    def test_unanimous_no_conflict(self, source_a, source_b, source_c):
        """Items where all 3 sources agree should NOT be in conflicts."""
        result = reconcile_inventory(source_a, source_b, source_c)
        for entry in result.audit_trail:
            if entry.resolution_method == "unanimous":
                assert entry.item not in result.conflicts

    @settings(max_examples=10000, suppress_health_check=[HealthCheck.too_slow])
    @given(
        qty=st.integers(min_value=0, max_value=10000),
        key=inventory_key,
    )
    def test_identical_sources_unanimous(self, qty, key):
        """When all three sources have the same value, resolution is unanimous."""
        assume(len(key) > 0)
        src = {key: qty}
        result = reconcile_inventory(src, src.copy(), src.copy())
        assert result.items[key] == qty
        assert key not in result.conflicts

    def test_empty_sources(self):
        """Three empty sources should produce an empty result."""
        result = reconcile_inventory({}, {}, {})
        assert result.items == {}
        assert result.audit_trail == []
        assert result.conflicts == []

    @settings(max_examples=10000, suppress_health_check=[HealthCheck.too_slow])
    @given(
        source_a=inventory_source,
        source_b=inventory_source,
        source_c=inventory_source,
    )
    def test_conflicts_are_subset_of_items(self, source_a, source_b, source_c):
        """Conflict items must be a subset of the result items."""
        result = reconcile_inventory(source_a, source_b, source_c)
        assert set(result.conflicts).issubset(set(result.items.keys()))
