"""
Tests for order_processor.py

Behavior tests verify correct calculations for various order scenarios.
Structural tests verify that the code has been properly refactored.

When ALL tests pass, your solution is auto-submitted to the CTF server.
"""

import pytest
import ast
import inspect
import importlib
import order_processor


# ============================================================
# BEHAVIOR TESTS - These test correct order processing logic
# ============================================================

class TestBasicOrders:
    """Test basic order processing."""

    def test_single_item_order(self):
        order = {
            "customer_id": "C001",
            "items": [{"name": "Burger", "quantity": 1}],
            "state": "OR",
        }
        result = order_processor.process_order(order)
        assert result["subtotal"] == 8.99
        assert result["discount"] == 0.0
        assert result["tax"] == 0.0  # Oregon has no sales tax
        assert result["total"] == 8.99
        assert result["loyalty_points_earned"] == 8

    def test_multiple_items_order(self):
        order = {
            "customer_id": "C002",
            "items": [
                {"name": "Burger", "quantity": 2},
                {"name": "Fries", "quantity": 1},
                {"name": "Soda", "quantity": 2},
            ],
            "state": "OR",
        }
        result = order_processor.process_order(order)
        # 2*8.99 + 1*3.99 + 2*1.99 = 17.98 + 3.99 + 3.98 = 25.95
        assert result["subtotal"] == 25.95

    def test_all_menu_items_exist(self):
        """Verify that all expected menu items can be ordered."""
        menu_items = [
            "Burger", "Cheeseburger", "Veggie Burger", "Fries", "Large Fries",
            "Onion Rings", "Soda", "Large Soda", "Milkshake", "Water",
            "Salad", "Chicken Wrap", "Fish Tacos", "Ice Cream", "Coffee", "Lemonade",
        ]
        for item_name in menu_items:
            order = {
                "customer_id": "C003",
                "items": [{"name": item_name, "quantity": 1}],
                "state": "OR",
            }
            result = order_processor.process_order(order)
            assert result["subtotal"] > 0


class TestBulkDiscount:
    """Test bulk discount (10% off 5+ of same item)."""

    def test_bulk_discount_applied(self):
        order = {
            "customer_id": "C010",
            "items": [{"name": "Burger", "quantity": 5}],
            "state": "OR",
        }
        result = order_processor.process_order(order)
        # 5 * 8.99 = 44.95 * 0.9 = 40.455 -> 40.46 (rounded)
        assert result["subtotal"] == 40.46
        assert result["items"][0]["discount_applied"] == "bulk_10_percent"

    def test_no_bulk_discount_under_5(self):
        order = {
            "customer_id": "C011",
            "items": [{"name": "Burger", "quantity": 4}],
            "state": "OR",
        }
        result = order_processor.process_order(order)
        # 4 * 8.99 = 35.96
        assert result["subtotal"] == 35.96
        assert result["items"][0]["discount_applied"] is None


class TestComboDiscounts:
    """Test combo meal discounts."""

    def test_burger_combo_discount(self):
        """Burger + Fries + Drink = 15% off one of each combo item."""
        order = {
            "customer_id": "C020",
            "items": [
                {"name": "Burger", "quantity": 1},
                {"name": "Fries", "quantity": 1},
                {"name": "Soda", "quantity": 1},
            ],
            "state": "OR",
        }
        result = order_processor.process_order(order)
        # subtotal: 8.99 + 3.99 + 1.99 = 14.97
        assert result["subtotal"] == 14.97
        # combo discount: 15% of (8.99 + 3.99 + 1.99) = 15% of each unit price
        # round(8.99*0.15,2) + round(3.99*0.15,2) + round(1.99*0.15,2) = 1.35 + 0.60 + 0.30 = 2.25
        assert result["combo_discount"] == 2.25

    def test_wrap_combo_discount(self):
        """Chicken Wrap + Salad + Drink = 10% off one of each combo item."""
        order = {
            "customer_id": "C021",
            "items": [
                {"name": "Chicken Wrap", "quantity": 1},
                {"name": "Salad", "quantity": 1},
                {"name": "Lemonade", "quantity": 1},
            ],
            "state": "OR",
        }
        result = order_processor.process_order(order)
        # subtotal: 8.49 + 7.99 + 2.49 = 18.97
        assert result["subtotal"] == 18.97
        # combo discount: 10% of each unit price
        # round(8.49*0.10,2) + round(7.99*0.10,2) + round(2.49*0.10,2) = 0.85 + 0.80 + 0.25 = 1.90
        assert result["combo_discount"] == 1.90


class TestCouponCodes:
    """Test coupon code discounts."""

    def test_save10_coupon(self):
        order = {
            "customer_id": "C030",
            "items": [{"name": "Burger", "quantity": 1}],
            "state": "OR",
            "coupon_code": "SAVE10",
        }
        result = order_processor.process_order(order)
        # 10% off 8.99 = 0.90
        assert result["coupon_discount"] == 0.90

    def test_save5_coupon_over_20(self):
        order = {
            "customer_id": "C031",
            "items": [
                {"name": "Burger", "quantity": 2},
                {"name": "Fries", "quantity": 1},
            ],
            "state": "OR",
            "coupon_code": "SAVE5",
        }
        result = order_processor.process_order(order)
        # subtotal = 2*8.99 + 3.99 = 21.97 (>= 20)
        assert result["coupon_discount"] == 5.0

    def test_save5_coupon_under_20(self):
        order = {
            "customer_id": "C032",
            "items": [{"name": "Soda", "quantity": 1}],
            "state": "OR",
            "coupon_code": "SAVE5",
        }
        result = order_processor.process_order(order)
        assert result["coupon_discount"] == 0.0

    def test_bogo50_coupon(self):
        order = {
            "customer_id": "C033",
            "items": [
                {"name": "Burger", "quantity": 1},
                {"name": "Fries", "quantity": 1},
            ],
            "state": "OR",
            "coupon_code": "BOGO50",
        }
        result = order_processor.process_order(order)
        # 50% off cheapest item (Fries 3.99) = 2.00 (rounded)
        assert result["coupon_discount"] == 2.0

    def test_invalid_coupon_raises(self):
        order = {
            "customer_id": "C034",
            "items": [{"name": "Burger", "quantity": 1}],
            "state": "OR",
            "coupon_code": "FAKECODE",
        }
        with pytest.raises(ValueError, match="Invalid coupon code"):
            order_processor.process_order(order)


class TestTaxCalculation:
    """Test state-based tax calculations."""

    def test_california_tax(self):
        order = {
            "customer_id": "C040",
            "items": [{"name": "Burger", "quantity": 1}],
            "state": "CA",
        }
        result = order_processor.process_order(order)
        # 7.25% of 8.99 = 0.65
        assert result["tax"] == round(8.99 * 0.0725, 2)

    def test_new_york_tax(self):
        order = {
            "customer_id": "C041",
            "items": [{"name": "Burger", "quantity": 1}],
            "state": "NY",
        }
        result = order_processor.process_order(order)
        # 8% of 8.99 = 0.72
        assert result["tax"] == round(8.99 * 0.08, 2)

    def test_default_tax_unknown_state(self):
        order = {
            "customer_id": "C042",
            "items": [{"name": "Burger", "quantity": 1}],
            "state": "ZZ",
        }
        result = order_processor.process_order(order)
        # default 5% of 8.99 = 0.45
        assert result["tax"] == round(8.99 * 0.05, 2)


class TestLoyaltyPoints:
    """Test loyalty points discount and earning."""

    def test_loyalty_discount_applied(self):
        order = {
            "customer_id": "C050",
            "items": [{"name": "Fish Tacos", "quantity": 2}],
            "state": "OR",
            "loyalty_points": 100,
        }
        result = order_processor.process_order(order)
        # subtotal = 2 * 10.99 = 21.98
        # 100 points // 10 = $10 max from points
        # max loyalty = 50% of 21.98 = 10.99
        # 10.0 < 10.99 so loyalty_discount = 10.0
        assert result["loyalty_discount"] == 10.0
        assert result["loyalty_points_used"] == 100

    def test_loyalty_capped_at_50_percent(self):
        order = {
            "customer_id": "C051",
            "items": [{"name": "Burger", "quantity": 1}],
            "state": "OR",
            "loyalty_points": 500,
        }
        result = order_processor.process_order(order)
        # subtotal = 8.99
        # 500 points // 10 = $50 potential discount
        # max loyalty = 50% of 8.99 = round(4.495, 2) = 4.50 (but rounding: 4.5)
        # 4.50 < 50 so loyalty_discount = 4.50
        assert result["loyalty_discount"] == round(8.99 * 0.50, 2)
        # points used = int(4.50 * 10) = 45 (since capped)
        assert result["loyalty_points_used"] == int(round(8.99 * 0.50, 2) * 10)

    def test_loyalty_points_earned(self):
        order = {
            "customer_id": "C052",
            "items": [{"name": "Burger", "quantity": 1}],
            "state": "OR",
        }
        result = order_processor.process_order(order)
        # total = 8.99, points earned = int(8.99) = 8
        assert result["loyalty_points_earned"] == 8


class TestValidationErrors:
    """Test input validation and error handling."""

    def test_none_order_raises(self):
        with pytest.raises(ValueError):
            order_processor.process_order(None)

    def test_empty_items_raises(self):
        with pytest.raises(ValueError):
            order_processor.process_order({"customer_id": "C060", "items": []})

    def test_unknown_item_raises(self):
        with pytest.raises(ValueError, match="Unknown menu item"):
            order_processor.process_order({
                "customer_id": "C061",
                "items": [{"name": "Pizza", "quantity": 1}],
            })

    def test_invalid_quantity_raises(self):
        with pytest.raises(ValueError):
            order_processor.process_order({
                "customer_id": "C062",
                "items": [{"name": "Burger", "quantity": 0}],
            })

    def test_quantity_over_99_raises(self):
        with pytest.raises(ValueError):
            order_processor.process_order({
                "customer_id": "C063",
                "items": [{"name": "Burger", "quantity": 100}],
            })


class TestSummaryAndMetadata:
    """Test output structure and summary."""

    def test_summary_format(self):
        order = {
            "customer_id": "C070",
            "items": [
                {"name": "Burger", "quantity": 2},
                {"name": "Fries", "quantity": 1},
            ],
            "state": "OR",
        }
        result = order_processor.process_order(order)
        assert result["summary"].startswith("Order for C070:")
        assert "3 items" in result["summary"]
        assert result["order_id"].startswith("ORD-")
        assert result["customer_id"] == "C070"

    def test_result_has_all_fields(self):
        order = {
            "customer_id": "C071",
            "items": [{"name": "Burger", "quantity": 1}],
            "state": "CA",
        }
        result = order_processor.process_order(order)
        required_fields = [
            "order_id", "customer_id", "items", "subtotal",
            "combo_discount", "coupon_discount", "discount",
            "tax", "loyalty_discount", "total",
            "loyalty_points_earned", "summary",
        ]
        for field in required_fields:
            assert field in result, f"Missing field: {field}"


# ============================================================
# STRUCTURAL TESTS - These verify the code is properly refactored
# ============================================================

class TestStructure:
    """Structural tests that verify the code has been refactored properly."""

    def test_no_function_exceeds_30_lines(self):
        """Every function in order_processor.py should be at most 30 lines."""
        source = inspect.getsource(order_processor)
        tree = ast.parse(source)

        long_functions = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Count lines from first to last line of the function body
                start = node.body[0].lineno
                end = node.body[-1].end_lineno
                length = end - start + 1
                if length > 30:
                    long_functions.append(f"{node.name} ({length} lines)")

        assert len(long_functions) == 0, (
            f"Functions exceeding 30 lines: {', '.join(long_functions)}. "
            f"Refactor into smaller functions."
        )

    def test_at_least_6_functions(self):
        """The module should have at least 6 top-level or nested functions."""
        source = inspect.getsource(order_processor)
        tree = ast.parse(source)

        function_count = 0
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                function_count += 1

        assert function_count >= 6, (
            f"Found only {function_count} function(s). "
            f"Need at least 6 functions for proper modularity."
        )

    def test_no_magic_numbers(self):
        """Module should define named constants instead of using magic numbers.

        Checks that at least 5 module-level UPPER_CASE constants are defined,
        covering prices, tax rates, and discount factors.
        """
        source = inspect.getsource(order_processor)
        tree = ast.parse(source)

        # Count module-level uppercase assignments (constants)
        constant_count = 0
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id.isupper():
                        constant_count += 1

        assert constant_count >= 5, (
            f"Found only {constant_count} module-level UPPER_CASE constant(s). "
            f"Need at least 5. Replace magic numbers with named constants "
            f"(e.g., TAX_RATES, MENU_PRICES, BULK_DISCOUNT_THRESHOLD, etc.)."
        )


# ============================================================
# FLAG
# ============================================================

class TestSubmit:
    """Auto-submit when all other tests have passed."""

    def test_submit(self):
        """This test always passes — submits the solution to the CTF server."""
        print("\n")
        print("=" * 50)
        print("  ALL TESTS PASSED!")
        print("=" * 50)
        print("\n")

        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
        import ctf_helper
        ctf_helper.submit(5, ["order_processor.py"])
