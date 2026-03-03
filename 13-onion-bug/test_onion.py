"""
Test suite for the Onion Bug challenge.

7 test groups, each targeting one layer of bugs.
Groups are designed so that layer N tests only pass once layers 1..N-1 are fixed.
"""

import sys
import threading
import time
import unittest
from unittest.mock import patch

from order_system.models import (
    MenuItem,
    OrderItem,
    Order,
    OrderResult,
    OrderStatus,
    ItemCategory,
    MENU_CATALOG,
    flatten_modifiers,
)
from order_system.processor import process_order, reset_inventory_manager
from order_system.pricing import apply_discount, calculate_total, calculate_tax
from order_system.validators import validate_order
from order_system.inventory import InventoryManager


# =====================================================================
# Helper: build a standard valid order (with special_instructions set)
# =====================================================================
def _make_order(
    items=None,
    customer="Alice",
    table=5,
    special_instructions="No nuts please",
    is_takeout=False,
):
    """Build a valid Order with sensible defaults."""
    if items is None:
        burger = MENU_CATALOG["classic_burger"]
        items = [OrderItem(menu_item=burger, quantity=1)]
    return Order(
        customer_name=customer,
        items=items,
        table_number=table,
        special_instructions=special_instructions,
        is_takeout=is_takeout,
    )


def _setup_inventory(inv, order, extra=5):
    """Set stock for every item in the order."""
    for item in order.items:
        key = item.menu_item.name.lower().replace(" ", "_")
        inv.set_stock(key, item.quantity + extra)


# =====================================================================
# LAYER 1: process_order returns OrderResult (not a string)
# =====================================================================
class TestLayer1_ReturnType(unittest.TestCase):
    """Layer 1: process_order must return an OrderResult dataclass."""

    def setUp(self):
        self.inv = reset_inventory_manager()

    def test_return_type_is_order_result(self):
        """process_order should return an OrderResult, not a string."""
        order = _make_order()
        _setup_inventory(self.inv, order)
        result = process_order(order, self.inv)
        self.assertIsInstance(
            result, OrderResult,
            f"Expected OrderResult, got {type(result).__name__}: {result!r}"
        )

    def test_result_has_status(self):
        """The returned OrderResult should have a valid status."""
        order = _make_order()
        _setup_inventory(self.inv, order)
        result = process_order(order, self.inv)
        self.assertIsInstance(result, OrderResult)
        self.assertEqual(result.status, OrderStatus.CONFIRMED)

    def test_result_has_total(self):
        """The returned OrderResult should contain a numeric total."""
        order = _make_order()
        _setup_inventory(self.inv, order)
        result = process_order(order, self.inv)
        self.assertIsInstance(result, OrderResult)
        self.assertGreater(result.total, 0)


# =====================================================================
# LAYER 2: Discount boundary conditions (>= not >)
# =====================================================================
class TestLayer2_DiscountBoundary(unittest.TestCase):
    """Layer 2: Discount tiers should include boundary values (>=)."""

    def test_exact_50_gets_discount(self):
        """An order of exactly $50 should receive the 10% discount."""
        discount = apply_discount(50.0)
        self.assertAlmostEqual(discount, 5.0, places=2,
            msg="$50.00 order should get 10% ($5.00) discount")

    def test_exact_100_gets_discount(self):
        """An order of exactly $100 should receive the 15% discount."""
        discount = apply_discount(100.0)
        self.assertAlmostEqual(discount, 15.0, places=2,
            msg="$100.00 order should get 15% ($15.00) discount")

    def test_exact_25_gets_discount(self):
        """An order of exactly $25 should receive the 5% discount."""
        discount = apply_discount(25.0)
        self.assertAlmostEqual(discount, 1.25, places=2,
            msg="$25.00 order should get 5% ($1.25) discount")


# =====================================================================
# LAYER 3: None handling for optional special_instructions
# =====================================================================
class TestLayer3_NullInstructions(unittest.TestCase):
    """Layer 3: validate_order must handle None special_instructions."""

    def test_none_special_instructions_no_crash(self):
        """Order with None special_instructions should not raise an error."""
        order = _make_order(special_instructions=None)
        # Should not raise AttributeError
        errors = validate_order(order)
        # With valid items and customer, there should be no errors
        self.assertIsInstance(errors, list)

    def test_empty_string_instructions(self):
        """Order with empty string instructions should validate cleanly."""
        order = _make_order(special_instructions="")
        errors = validate_order(order)
        self.assertIsInstance(errors, list)
        self.assertEqual(len(errors), 0)


# =====================================================================
# LAYER 4: Tax-exempt items get double-taxed after discount fix
# =====================================================================
class TestLayer4_TaxExemption(unittest.TestCase):
    """
    Layer 4: Tax-exempt items (gift cards) should never be taxed,
    even when a discount is applied.

    This only manifests after Layer 2 is fixed because the discount
    path changes the proportional factor used in tax calculation.
    """

    def test_gift_card_no_tax_with_discount(self):
        """Gift card in a $50+ order should have zero tax contribution."""
        gift_card = MENU_CATALOG["gift_card_25"]
        burger = MENU_CATALOG["classic_burger"]
        # 25 + 12.99 + 12.99 = 50.98 -> qualifies for 10% discount
        items = [
            OrderItem(menu_item=gift_card, quantity=1),
            OrderItem(menu_item=burger, quantity=1),
            OrderItem(menu_item=burger, quantity=1),
        ]
        order = _make_order(items=items)

        pricing = calculate_total(order)

        # Calculate what tax SHOULD be: only burgers taxed at 8%
        burger_subtotal = 12.99 * 2
        discount_rate = 0.10  # 10% tier
        discounted_burgers = burger_subtotal * (1 - discount_rate)
        expected_tax = round(discounted_burgers * 0.08, 2)

        # Tax should only be on the burgers, not the gift card
        self.assertAlmostEqual(
            pricing["tax_amount"], expected_tax, places=1,
            msg=f"Tax should be ~${expected_tax} (burgers only), "
                f"got ${pricing['tax_amount']} (gift card is being taxed)"
        )

    def test_gift_card_only_order_no_tax(self):
        """An order with only gift cards should have zero tax."""
        gc50 = MENU_CATALOG["gift_card_50"]
        gc25 = MENU_CATALOG["gift_card_25"]
        # 50 + 25 = 75.00 -> qualifies for 10% discount
        items = [
            OrderItem(menu_item=gc50, quantity=1),
            OrderItem(menu_item=gc25, quantity=1),
        ]
        order = _make_order(items=items)
        pricing = calculate_total(order)
        self.assertAlmostEqual(
            pricing["tax_amount"], 0.0, places=2,
            msg="Gift-card-only order should have zero tax"
        )

    def test_mixed_order_tax_excludes_exempt(self):
        """In a mixed order, only non-exempt items should contribute to tax."""
        gift_card = MENU_CATALOG["gift_card_50"]
        fries = MENU_CATALOG["truffle_fries"]
        # 50 + 7.99 = 57.99 -> qualifies for 10% discount
        items = [
            OrderItem(menu_item=gift_card, quantity=1),
            OrderItem(menu_item=fries, quantity=1),
        ]
        order = _make_order(items=items)
        pricing = calculate_total(order)

        # Only fries should be taxed
        discounted_fries = 7.99 * 0.90  # 10% discount applied
        max_reasonable_tax = discounted_fries * 0.08 * 1.05  # 5% tolerance
        self.assertLess(
            pricing["tax_amount"], max_reasonable_tax,
            msg=f"Tax ${pricing['tax_amount']} is too high; "
                f"gift card appears to be taxed"
        )


# =====================================================================
# LAYER 5: Recursion depth limit in flatten_modifiers
# =====================================================================
class TestLayer5_ModifierRecursion(unittest.TestCase):
    """
    Layer 5: flatten_modifiers must handle deeply nested dicts without
    hitting Python's recursion limit.

    Only manifests after Layer 3 is fixed because orders with nested
    modifiers previously crashed during validation (None handling bug).
    """

    def test_deeply_nested_modifiers(self):
        """Deeply nested modifiers should not cause RecursionError."""
        # Build a dict nested 200 levels deep
        deep = {"value": True}
        for i in range(200):
            deep = {"level": deep}

        # This should handle gracefully, not hit recursion limit
        try:
            result = flatten_modifiers(deep)
            # If it returns, it should be a flat dict
            self.assertIsInstance(result, dict)
        except RecursionError:
            self.fail(
                "flatten_modifiers hit RecursionError on deeply nested input. "
                "Needs a depth limit."
            )

    def test_order_with_nested_modifiers_processes(self):
        """An order with deeply nested modifiers should process without crash."""
        deep_mod = {"topping": True}
        for _ in range(150):
            deep_mod = {"add": deep_mod}

        burger = MENU_CATALOG["classic_burger"]
        items = [OrderItem(menu_item=burger, quantity=1, modifiers=deep_mod)]
        order = _make_order(items=items)

        inv = reset_inventory_manager()
        _setup_inventory(inv, order)

        try:
            result = process_order(order, inv)
        except RecursionError:
            self.fail(
                "process_order crashed with RecursionError on nested modifiers"
            )


# =====================================================================
# LAYER 6: TOCTOU race condition in inventory
# =====================================================================
class TestLayer6_InventoryRace(unittest.TestCase):
    """
    Layer 6: Inventory check-then-deduct must be atomic.

    This only manifests after L1+L4+L5 are working together, because
    the full pipeline must execute through to inventory deduction.
    The non-atomic check/deduct allows concurrent orders to over-deduct.
    """

    def test_concurrent_orders_no_negative_stock(self):
        """Two concurrent orders for last item should not both succeed with negative stock."""
        inv = reset_inventory_manager()
        burger = MENU_CATALOG["classic_burger"]

        # Only 1 burger in stock
        inv.set_stock("classic_burger", 1)

        order1 = _make_order(
            items=[OrderItem(menu_item=burger, quantity=1)],
            customer="Alice",
        )
        order2 = _make_order(
            items=[OrderItem(menu_item=burger, quantity=1)],
            customer="Bob",
        )

        results = []
        errors = []

        def place_order(order):
            try:
                r = process_order(order, inv)
                results.append(r)
            except Exception as e:
                errors.append(e)

        # Force the TOCTOU window by monkey-patching deduct_stock
        # to add a delay after check_availability
        original_check = inv.check_availability

        def slow_check(order):
            result = original_check(order)
            time.sleep(0.1)  # Widen the race window
            return result

        inv.check_availability = slow_check

        t1 = threading.Thread(target=place_order, args=(order1,))
        t2 = threading.Thread(target=place_order, args=(order2,))
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        # After both orders, stock should never go negative
        stock = inv.get_stock("classic_burger")
        self.assertGreaterEqual(
            stock, 0,
            f"Stock went negative ({stock}). "
            f"Inventory check and deduction are not atomic."
        )

    def test_concurrent_batch_respects_limits(self):
        """Batch of concurrent orders should not exceed available stock."""
        inv = reset_inventory_manager()
        salad = MENU_CATALOG["caesar_salad"]
        inv.set_stock("caesar_salad", 3)

        orders = []
        for i in range(5):
            orders.append(_make_order(
                items=[OrderItem(menu_item=salad, quantity=1)],
                customer=f"Customer_{i}",
            ))

        original_check = inv.check_availability

        def slow_check(order):
            result = original_check(order)
            time.sleep(0.05)
            return result

        inv.check_availability = slow_check

        threads = []
        results = []

        def place(o):
            try:
                r = process_order(o, inv)
                results.append(r)
            except Exception as e:
                results.append(e)

        for o in orders:
            t = threading.Thread(target=place, args=(o,))
            threads.append(t)

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        stock = inv.get_stock("caesar_salad")
        confirmed = sum(
            1 for r in results
            if isinstance(r, OrderResult) and r.status == OrderStatus.CONFIRMED
        )

        self.assertGreaterEqual(
            stock, 0,
            f"Stock went to {stock}. Race condition allows over-deduction."
        )
        self.assertLessEqual(
            confirmed, 3,
            f"Confirmed {confirmed} orders but only 3 in stock."
        )


# =====================================================================
# LAYER 7: f-string + .format() conflict with curly braces in names
# =====================================================================
class TestLayer7_ConfirmationTemplate(unittest.TestCase):
    """
    Layer 7: Confirmation email should handle item names with curly braces.

    Only manifests after all previous layers are fixed because the full
    pipeline must execute through confirmation generation.
    """

    def test_jalapeno_burger_confirmation(self):
        """Order with Jalape{n}o Burger should generate confirmation without error."""
        inv = reset_inventory_manager()
        jalapeno = MENU_CATALOG["jalapeno_burger"]
        items = [OrderItem(menu_item=jalapeno, quantity=1)]
        order = _make_order(items=items)
        _setup_inventory(inv, order)

        try:
            result = process_order(order, inv)
        except (KeyError, ValueError, IndexError) as e:
            self.fail(
                f"Confirmation generation failed with {type(e).__name__}: {e}. "
                f"Item names with curly braces break the template."
            )
        self.assertIsInstance(result, OrderResult)

    def test_mixed_order_with_braces_in_name(self):
        """Mixed order including curly-brace item name should confirm."""
        inv = reset_inventory_manager()
        jalapeno = MENU_CATALOG["jalapeno_burger"]
        fries = MENU_CATALOG["truffle_fries"]
        items = [
            OrderItem(menu_item=jalapeno, quantity=2),
            OrderItem(menu_item=fries, quantity=1),
        ]
        order = _make_order(items=items)
        _setup_inventory(inv, order)

        try:
            result = process_order(order, inv)
        except (KeyError, ValueError, IndexError) as e:
            self.fail(
                f"Confirmation template error: {type(e).__name__}: {e}"
            )
        self.assertIsInstance(result, OrderResult)
        self.assertEqual(result.status, OrderStatus.CONFIRMED)


# =====================================================================
# Collect test groups in order
# =====================================================================
TEST_GROUPS = [
    ("Layer 1: Return Type", TestLayer1_ReturnType),
    ("Layer 2: Discount Boundaries", TestLayer2_DiscountBoundary),
    ("Layer 3: Null Instructions", TestLayer3_NullInstructions),
    ("Layer 4: Tax Exemption", TestLayer4_TaxExemption),
    ("Layer 5: Modifier Recursion", TestLayer5_ModifierRecursion),
    ("Layer 6: Inventory Race Condition", TestLayer6_InventoryRace),
    ("Layer 7: Confirmation Template", TestLayer7_ConfirmationTemplate),
]

if __name__ == "__main__":
    unittest.main()
