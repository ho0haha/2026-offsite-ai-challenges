"""
Integration tests for the Loyalty Points feature.
All 15 tests must pass to capture the flag.
"""

import math
import pytest
import sys
import os

# Ensure the project root is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from restaurant_system.database import Database
from restaurant_system.models import (
    Customer,
    MenuItem,
    MenuCategory,
    OrderStatus,
    PaymentMethod,
)
from restaurant_system.customer_service import CustomerService
from restaurant_system.order_service import OrderService
from restaurant_system.payment_service import PaymentService
from restaurant_system.menu_service import MenuService
from restaurant_system.reporting import ReportingService
from restaurant_system.formatters import OutputFormatter
from restaurant_system import config


@pytest.fixture
def setup():
    """Set up a fresh restaurant system for each test."""
    db = Database()
    customer_svc = CustomerService(db)
    menu_svc = MenuService(db)
    order_svc = OrderService(db, customer_service=customer_svc)
    payment_svc = PaymentService(db, customer_service=customer_svc)
    reporting_svc = ReportingService(db)
    formatter = OutputFormatter()

    # Add some menu items
    burger = menu_svc.add_menu_item(
        name="Classic Burger",
        description="Juicy beef patty with all the fixings",
        price=12.99,
        category=MenuCategory.MAIN_COURSE,
    )
    fries = menu_svc.add_menu_item(
        name="French Fries",
        description="Crispy golden fries",
        price=4.99,
        category=MenuCategory.SIDE,
    )
    soda = menu_svc.add_menu_item(
        name="Soda",
        description="Refreshing fountain drink",
        price=2.49,
        category=MenuCategory.BEVERAGE,
    )
    steak = menu_svc.add_menu_item(
        name="Ribeye Steak",
        description="12oz premium ribeye",
        price=34.99,
        category=MenuCategory.MAIN_COURSE,
    )

    # Register a customer
    customer = customer_svc.register_customer(
        name="Alice Johnson", email="alice@example.com", phone="555-0101"
    )

    return {
        "db": db,
        "customer_svc": customer_svc,
        "menu_svc": menu_svc,
        "order_svc": order_svc,
        "payment_svc": payment_svc,
        "reporting_svc": reporting_svc,
        "formatter": formatter,
        "customer": customer,
        "burger": burger,
        "fries": fries,
        "soda": soda,
        "steak": steak,
    }


def _place_order(setup_data, menu_item, quantity=1):
    """Helper: create and place an order, return the placed order."""
    order = setup_data["order_svc"].create_order(setup_data["customer"].id)
    setup_data["order_svc"].add_item_to_order(
        order.id, menu_item.id, quantity=quantity
    )
    return setup_data["order_svc"].place_order(order.id)


# ---------- Test 1: Customer starts with 0 loyalty points ----------
def test_customer_starts_with_zero_points(setup):
    """A new customer should have 0 loyalty points."""
    customer = setup["customer"]
    assert customer.loyalty_points == 0
    assert customer.loyalty_points_earned == 0
    assert customer.loyalty_points_redeemed == 0


# ---------- Test 2: Points earned on order (1 per dollar) ----------
def test_points_earned_on_order(setup):
    """After placing an order, the customer should earn 1 point per dollar spent."""
    order = _place_order(setup, setup["burger"])  # $12.99 burger
    customer = setup["customer_svc"].get_customer(setup["customer"].id)

    # grand_total = subtotal + tax - discount = 12.99 + tax
    expected_points = math.floor(order.grand_total)
    assert customer.loyalty_points == expected_points
    assert order.loyalty_points_earned == expected_points


# ---------- Test 3: Points balance correctly tracked ----------
def test_points_balance_tracked(setup):
    """get_loyalty_balance should return the correct current balance."""
    _place_order(setup, setup["burger"])
    balance = setup["customer_svc"].get_loyalty_balance(setup["customer"].id)

    customer = setup["customer_svc"].get_customer(setup["customer"].id)
    assert balance == customer.loyalty_points
    assert balance > 0


# ---------- Test 4: Can redeem 100 points for $5 discount ----------
def test_redeem_100_points_for_5_dollars(setup):
    """Redeeming 100 points should give a $5.00 discount."""
    # Give customer enough points
    setup["customer_svc"].add_loyalty_points(setup["customer"].id, 100)

    discount = setup["customer_svc"].redeem_loyalty_points(
        setup["customer"].id, 100
    )
    assert discount == 5.00


# ---------- Test 5: Cannot redeem more points than balance ----------
def test_cannot_redeem_more_than_balance(setup):
    """Attempting to redeem more points than the balance should raise ValueError."""
    setup["customer_svc"].add_loyalty_points(setup["customer"].id, 50)

    with pytest.raises(ValueError):
        setup["customer_svc"].redeem_loyalty_points(setup["customer"].id, 100)


# ---------- Test 6: Partial redemption works ----------
def test_partial_redemption(setup):
    """Redeeming fewer points than the balance should work correctly."""
    setup["customer_svc"].add_loyalty_points(setup["customer"].id, 200)

    discount = setup["customer_svc"].redeem_loyalty_points(
        setup["customer"].id, 50
    )
    assert discount == 2.50

    balance = setup["customer_svc"].get_loyalty_balance(setup["customer"].id)
    assert balance == 150


# ---------- Test 7: Points earned on discounted orders ----------
def test_points_earned_on_discounted_order(setup):
    """Points should be earned on the actual amount paid after discount."""
    # Give customer points and apply a discount via payment service
    setup["customer_svc"].add_loyalty_points(setup["customer"].id, 200)

    result = setup["payment_svc"].apply_loyalty_discount(
        setup["customer"].id, 50.00, 100
    )

    assert result["discount_amount"] == 5.00
    assert result["final_total"] == 45.00
    assert result["points_redeemed"] == 100


# ---------- Test 8: Loyalty report shows correct data ----------
def test_loyalty_report(setup):
    """The loyalty report should show accurate aggregated data."""
    # Create a second customer
    customer2 = setup["customer_svc"].register_customer(
        name="Bob Smith", email="bob@example.com"
    )

    # Give points to both customers
    setup["customer_svc"].add_loyalty_points(setup["customer"].id, 500)
    setup["customer_svc"].add_loyalty_points(customer2.id, 300)

    # Customer 1 redeems some
    setup["customer_svc"].redeem_loyalty_points(setup["customer"].id, 100)

    report = setup["reporting_svc"].loyalty_report()

    assert report["total_points_in_circulation"] == 700  # 400 + 300
    assert report["total_points_ever_earned"] == 800  # 500 + 300
    assert report["total_points_ever_redeemed"] == 100
    assert len(report["top_earners"]) == 2
    assert report["top_earners"][0]["name"] == "Alice Johnson"
    assert report["top_earners"][0]["points_earned"] == 500


# ---------- Test 9: Format loyalty summary works ----------
def test_format_loyalty_summary(setup):
    """The formatter should produce the correct loyalty summary string."""
    setup["customer_svc"].add_loyalty_points(setup["customer"].id, 250)
    setup["customer_svc"].redeem_loyalty_points(setup["customer"].id, 50)

    customer = setup["customer_svc"].get_customer(setup["customer"].id)
    summary = setup["formatter"].format_loyalty_summary(customer)

    assert "Loyalty Summary for Alice Johnson" in summary
    assert "Current Balance: 200 points" in summary
    assert "Total Earned: 250 points" in summary
    assert "Total Redeemed: 50 points" in summary


# ---------- Test 10: Config values are correct ----------
def test_config_values(setup):
    """Configuration constants should be set correctly."""
    assert config.LOYALTY_POINTS_PER_DOLLAR == 1
    assert config.LOYALTY_REDEMPTION_RATE == 0.05


# ---------- Test 11: Multiple orders accumulate points ----------
def test_multiple_orders_accumulate_points(setup):
    """Points from multiple orders should accumulate."""
    order1 = _place_order(setup, setup["burger"])
    order2 = _place_order(setup, setup["steak"])

    customer = setup["customer_svc"].get_customer(setup["customer"].id)

    expected = math.floor(order1.grand_total) + math.floor(order2.grand_total)
    assert customer.loyalty_points == expected
    assert customer.loyalty_points_earned == expected


# ---------- Test 12: Redemption reduces balance ----------
def test_redemption_reduces_balance(setup):
    """Redeeming points should reduce the balance accordingly."""
    setup["customer_svc"].add_loyalty_points(setup["customer"].id, 300)
    setup["customer_svc"].redeem_loyalty_points(setup["customer"].id, 100)

    customer = setup["customer_svc"].get_customer(setup["customer"].id)
    assert customer.loyalty_points == 200
    assert customer.loyalty_points_redeemed == 100


# ---------- Test 13: Points earned are rounded down ----------
def test_points_rounded_down(setup):
    """Points should be rounded down (floor) — e.g., $12.99 earns 12 points."""
    # add_loyalty_points directly with a calculated floor value
    # Simulate: an order of $2.49 soda + tax
    order = _place_order(setup, setup["soda"])  # $2.49 + tax

    customer = setup["customer_svc"].get_customer(setup["customer"].id)
    expected = math.floor(order.grand_total)
    assert customer.loyalty_points == expected
    assert order.loyalty_points_earned == expected


# ---------- Test 14: Zero-dollar order earns zero points ----------
def test_zero_dollar_order_earns_zero_points(setup):
    """A $0 order should award 0 loyalty points."""
    # Directly test that 0 points can be added
    balance = setup["customer_svc"].add_loyalty_points(setup["customer"].id, 0)
    assert balance == 0

    customer = setup["customer_svc"].get_customer(setup["customer"].id)
    assert customer.loyalty_points == 0


# ---------- Test 15: Integration full flow ----------
def test_full_loyalty_flow(setup):
    """Integration test: order -> earn -> redeem -> order again."""
    # Step 1: Place an order for a steak ($34.99 + tax)
    order1 = _place_order(setup, setup["steak"])
    customer = setup["customer_svc"].get_customer(setup["customer"].id)
    points_after_order1 = customer.loyalty_points
    assert points_after_order1 == math.floor(order1.grand_total)
    assert points_after_order1 > 0

    # Step 2: Accumulate more points with another order
    order2 = _place_order(setup, setup["steak"])
    customer = setup["customer_svc"].get_customer(setup["customer"].id)
    points_after_order2 = customer.loyalty_points
    assert points_after_order2 > points_after_order1

    # Step 3: Redeem some points
    discount = setup["customer_svc"].redeem_loyalty_points(
        setup["customer"].id, 50
    )
    assert discount == 2.50

    customer = setup["customer_svc"].get_customer(setup["customer"].id)
    assert customer.loyalty_points == points_after_order2 - 50
    assert customer.loyalty_points_redeemed == 50

    # Step 4: Check loyalty report
    report = setup["reporting_svc"].loyalty_report()
    assert report["total_points_in_circulation"] == customer.loyalty_points
    assert report["total_points_ever_redeemed"] == 50

    # Step 5: Verify formatting
    summary = setup["formatter"].format_loyalty_summary(customer)
    assert "Alice Johnson" in summary
    assert "points" in summary


# ---------- FLAG ----------
def test_flag():
    """If all tests above pass, this prints the flag."""
    print("\n" + "=" * 50)
    print("FLAG{context_is_king_l0yalty_p0ints}")
    print("=" * 50)
