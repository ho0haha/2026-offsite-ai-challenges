"""Test suite for Challenge 1: Hello AI. Do not modify this file."""
import pytest
from starter import parse_order, format_receipt, analyze_sales

# --- parse_order tests ---

class TestParseOrder:
    def test_single_item(self):
        result = parse_order("1xSoda@1.99")
        assert result == {
            "items": [{"name": "Soda", "quantity": 1, "price": 1.99}],
            "total": 1.99,
        }

    def test_multiple_items(self):
        result = parse_order("2xBurger@5.99,1xFries@2.49,3xSoda@1.99")
        assert len(result["items"]) == 3
        assert result["items"][0] == {"name": "Burger", "quantity": 2, "price": 5.99}
        assert result["items"][1] == {"name": "Fries", "quantity": 1, "price": 2.49}
        assert result["items"][2] == {"name": "Soda", "quantity": 3, "price": 1.99}
        assert result["total"] == 20.44

    def test_empty_string(self):
        result = parse_order("")
        assert result == {"items": [], "total": 0.0}


# --- format_receipt tests ---

class TestFormatReceipt:
    def test_basic_receipt(self):
        order = parse_order("2xBurger@5.99,1xFries@2.49")
        receipt = format_receipt(order)
        assert "RECEIPT" in receipt
        assert "Burger" in receipt
        assert "Fries" in receipt
        assert "$14.47" in receipt  # subtotal
        assert "8.0%" in receipt

    def test_receipt_totals(self):
        order = parse_order("2xBurger@5.99,1xFries@2.49")
        receipt = format_receipt(order)
        # Tax: 14.47 * 0.08 = 1.1576 -> 1.16
        assert "$1.16" in receipt  # tax
        assert "$15.63" in receipt  # total

    def test_empty_order_receipt(self):
        order = parse_order("")
        receipt = format_receipt(order)
        assert "$0.00" in receipt


# --- analyze_sales tests ---

class TestAnalyzeSales:
    def test_multiple_orders(self):
        orders = [
            parse_order("2xBurger@5.99,1xFries@2.49"),
            parse_order("1xBurger@5.99,2xSoda@1.99"),
        ]
        result = analyze_sales(orders)
        assert result["total_revenue"] == 24.44
        assert result["average_order"] == 12.22
        assert result["most_popular_item"] == "Burger"
        assert result["item_breakdown"]["Burger"] == 3
        assert result["item_breakdown"]["Fries"] == 1
        assert result["item_breakdown"]["Soda"] == 2

    def test_empty_orders(self):
        result = analyze_sales([])
        assert result == {
            "total_revenue": 0.0,
            "average_order": 0.0,
            "most_popular_item": "",
            "item_breakdown": {},
        }

    def test_tie_most_popular(self):
        orders = [
            parse_order("2xAlpha@1.00,2xBeta@1.00"),
        ]
        result = analyze_sales(orders)
        # Tie: Alpha and Beta both have qty 2, Alpha comes first alphabetically
        assert result["most_popular_item"] == "Alpha"


# --- Flag output ---

def test_flag():
    """This test runs last. If all above tests pass, print the flag."""
    # Verify all functions work end-to-end
    order = parse_order("3xChicken@8.99,2xRice@3.49,1xDrink@2.49")
    assert order["total"] == 36.44

    receipt = format_receipt(order, tax_rate=0.10)
    assert "10.0%" in receipt

    orders = [order, parse_order("1xChicken@8.99")]
    stats = analyze_sales(orders)
    assert stats["most_popular_item"] == "Chicken"
    assert stats["item_breakdown"]["Chicken"] == 4

    print("\n" + "=" * 50)
    print("  ALL TESTS PASSED!")
    print("  FLAG{hello_ai_w3lc0me_2_th3_ctf}")
    print("=" * 50)
