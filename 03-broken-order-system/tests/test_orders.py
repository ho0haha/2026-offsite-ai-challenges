"""Tests for the restaurant ordering API.

DO NOT MODIFY THESE TESTS.
The tests are correct - fix the bugs in the app/ directory.

When all 20 tests pass, the flag is printed.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.routes import reset_db

client = TestClient(app)

FLAG = "FLAG{broken_orders_5_bugs_fixed}"


@pytest.fixture(autouse=True)
def clean_db():
    """Reset the database before each test."""
    reset_db()
    yield
    reset_db()


# --- Helper ---

def create_sample_order(**overrides):
    """Create a sample order payload."""
    payload = {
        "customer_name": "Alice",
        "items": [
            {"name": "Burger", "quantity": 2, "unit_price": 12.99},
            {"name": "Fries", "quantity": 1, "unit_price": 4.99},
        ],
        "table_number": 5,
    }
    payload.update(overrides)
    return payload


# =====================================================================
# Test 1-4: Basic CRUD
# =====================================================================

def test_create_order_returns_201():
    """BUG #2: Creating an order should return HTTP 201 Created."""
    payload = create_sample_order()
    response = client.post("/orders", json=payload)
    assert response.status_code == 201, (
        f"Expected 201 Created, got {response.status_code}"
    )


def test_create_order_response_body():
    """Verify the response body of a created order."""
    payload = create_sample_order()
    response = client.post("/orders", json=payload)
    data = response.json()
    assert data["customer_name"] == "Alice"
    assert data["id"] == 1
    assert len(data["items"]) == 2
    assert data["status"] == "pending"


def test_get_order_by_id():
    """Retrieve an order by its ID."""
    client.post("/orders", json=create_sample_order())
    response = client.get("/orders/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["customer_name"] == "Alice"


def test_get_order_not_found():
    """Requesting a nonexistent order returns 404."""
    response = client.get("/orders/999")
    assert response.status_code == 404


# =====================================================================
# Test 5-8: Pagination
# =====================================================================

def test_pagination_page_one():
    """BUG #1: First page should return the first batch of orders."""
    # Create 5 orders
    for i in range(5):
        client.post("/orders", json=create_sample_order(customer_name=f"Customer_{i}"))

    response = client.get("/orders?page=1&limit=3")
    assert response.status_code == 200
    data = response.json()
    assert len(data["orders"]) == 3
    assert data["orders"][0]["customer_name"] == "Customer_0"
    assert data["orders"][1]["customer_name"] == "Customer_1"
    assert data["orders"][2]["customer_name"] == "Customer_2"


def test_pagination_page_two():
    """Second page should return the next batch."""
    for i in range(5):
        client.post("/orders", json=create_sample_order(customer_name=f"Customer_{i}"))

    response = client.get("/orders?page=2&limit=3")
    data = response.json()
    assert len(data["orders"]) == 2
    assert data["orders"][0]["customer_name"] == "Customer_3"
    assert data["orders"][1]["customer_name"] == "Customer_4"


def test_pagination_metadata():
    """Pagination metadata should be correct."""
    for i in range(7):
        client.post("/orders", json=create_sample_order(customer_name=f"C_{i}"))

    response = client.get("/orders?page=1&limit=3")
    data = response.json()
    assert data["total"] == 7
    assert data["total_pages"] == 3
    assert data["page"] == 1
    assert data["limit"] == 3


def test_pagination_empty():
    """Empty database should return empty page."""
    response = client.get("/orders?page=1&limit=10")
    data = response.json()
    assert data["orders"] == []
    assert data["total"] == 0


# =====================================================================
# Test 9-12: Order Summary & Tax
# =====================================================================

def test_order_summary_subtotal():
    """Subtotal should be sum of (quantity * unit_price) for all items."""
    payload = create_sample_order(items=[
        {"name": "Burger", "quantity": 2, "unit_price": 10.00},
        {"name": "Soda", "quantity": 3, "unit_price": 2.50},
    ])
    client.post("/orders", json=payload)
    response = client.get("/orders/1/summary")
    data = response.json()
    # 2*10 + 3*2.5 = 27.50
    assert data["subtotal"] == 27.50


def test_order_summary_tax():
    """BUG #4: Tax should be 8.5% of subtotal."""
    payload = create_sample_order(items=[
        {"name": "Steak", "quantity": 1, "unit_price": 100.00},
    ])
    client.post("/orders", json=payload)
    response = client.get("/orders/1/summary")
    data = response.json()
    # Tax = 100.00 * 0.085 = 8.50
    assert data["tax"] == 8.50, f"Expected tax of 8.50, got {data['tax']}"


def test_order_summary_total():
    """Total should be subtotal + tax."""
    payload = create_sample_order(items=[
        {"name": "Steak", "quantity": 1, "unit_price": 100.00},
    ])
    client.post("/orders", json=payload)
    response = client.get("/orders/1/summary")
    data = response.json()
    # 100.00 + 8.50 = 108.50
    assert data["total"] == 108.50


def test_order_summary_item_count():
    """Item count should be the number of distinct items."""
    payload = create_sample_order(items=[
        {"name": "A", "quantity": 5, "unit_price": 1.00},
        {"name": "B", "quantity": 3, "unit_price": 2.00},
        {"name": "C", "quantity": 1, "unit_price": 3.00},
    ])
    client.post("/orders", json=payload)
    response = client.get("/orders/1/summary")
    data = response.json()
    assert data["item_count"] == 3
    assert data["total_items_quantity"] == 9


# =====================================================================
# Test 13-16: Validation
# =====================================================================

def test_reject_empty_items():
    """BUG #5: Orders with no items should be rejected with 400."""
    payload = create_sample_order(items=[])
    response = client.post("/orders", json=payload)
    assert response.status_code == 400, (
        f"Expected 400 for empty items, got {response.status_code}"
    )


def test_reject_zero_quantity():
    """BUG #3: Items with quantity 0 should be rejected."""
    payload = create_sample_order(items=[
        {"name": "Burger", "quantity": 0, "unit_price": 12.99},
    ])
    response = client.post("/orders", json=payload)
    assert response.status_code == 400, (
        f"Expected 400 for zero quantity, got {response.status_code}"
    )


def test_reject_negative_quantity():
    """BUG #3: Items with negative quantity should be rejected."""
    payload = create_sample_order(items=[
        {"name": "Burger", "quantity": -1, "unit_price": 12.99},
    ])
    response = client.post("/orders", json=payload)
    assert response.status_code == 400, (
        f"Expected 400 for negative quantity, got {response.status_code}"
    )


def test_valid_order_with_notes():
    """Orders with optional fields should be accepted."""
    payload = create_sample_order(
        special_instructions="No onions",
        items=[
            {"name": "Burger", "quantity": 1, "unit_price": 12.99, "notes": "Well done"},
        ],
    )
    response = client.post("/orders", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["special_instructions"] == "No onions"
    assert data["items"][0]["notes"] == "Well done"


# =====================================================================
# Test 17-20: Edge Cases & Average Price
# =====================================================================

def test_average_item_price():
    """Average item price should be the mean of unit prices."""
    payload = create_sample_order(items=[
        {"name": "A", "quantity": 1, "unit_price": 10.00},
        {"name": "B", "quantity": 1, "unit_price": 20.00},
        {"name": "C", "quantity": 1, "unit_price": 30.00},
    ])
    client.post("/orders", json=payload)
    response = client.get("/orders/1/summary")
    data = response.json()
    assert data["average_item_price"] == 20.00


def test_single_item_order():
    """An order with one item should work correctly."""
    payload = create_sample_order(items=[
        {"name": "Coffee", "quantity": 1, "unit_price": 4.50},
    ])
    client.post("/orders", json=payload)
    response = client.get("/orders/1/summary")
    data = response.json()
    assert data["subtotal"] == 4.50
    assert data["average_item_price"] == 4.50
    assert data["item_count"] == 1


def test_multiple_orders_independent():
    """Multiple orders should be independent."""
    client.post("/orders", json=create_sample_order(customer_name="Alice"))
    client.post("/orders", json=create_sample_order(customer_name="Bob"))

    r1 = client.get("/orders/1").json()
    r2 = client.get("/orders/2").json()
    assert r1["customer_name"] == "Alice"
    assert r2["customer_name"] == "Bob"
    assert r1["id"] != r2["id"]


def test_health_check():
    """Health endpoint should return ok."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# =====================================================================
# Flag printer
# =====================================================================

def test_zz_print_flag(capsys):
    """If this test runs last and everything passed, print the flag.

    This test always passes - it just prints the flag as a reward.
    The flag only means something if ALL other tests also passed.
    """
    print(f"\n{'='*50}")
    print(f"  ALL TESTS PASSED!")
    print(f"  {FLAG}")
    print(f"{'='*50}\n")
