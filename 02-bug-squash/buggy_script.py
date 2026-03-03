"""
Restaurant Order Processor — Bug Squash Challenge
This script processes restaurant orders and prints a summary.
There are 3 bugs hidden in this code. Find and fix them all!
"""


def calculate_item_total(price: float, quantity: int, discount_percent: float = 0) -> float:
    """Calculate the total for a single item after discount."""
    discount = price * quantity * (discount_percent / 100)
    total = price * quantity + discount
    return round(total, 2)


def get_order_summary(items: list[dict]) -> dict:
    """Generate a summary of all items in the order.

    Each item dict has: name, price, quantity, discount_percent (optional)
    Returns a dict with: items (list), subtotal, item_count
    """
    processed = []
    subtotal = 0.0

    for item in items:
        total = calculate_item_total(
            item["price"],
            item["quantity"],
            item.get("discount_percent", 0),
        )
        processed.append({
            "name": item["name"],
            "quantity": item["quantity"],
            "line_total": total,
        })
        subtotal += total

    summary = {
        "items": processed,
        "subtotal": round(subtotal, 2),
        "item_count": sum(item["quantity"] for item in items),
    }


def apply_tax_and_tip(subtotal: float, tax_rate: float = 0.08, tip_rate: float = 0.18) -> dict:
    """Apply tax and tip to the subtotal."""
    tax = round(subtotal * tax_rate, 2)
    tip = round(subtotal * tip_rate, 2)
    total = round(subtotal + tax + tip, 2)
    return {"tax": tax, "tip": tip, "total": total}


def format_order_number(order_id: int, total_orders: int) -> str:
    """Format order as 'Order X of Y' (1-indexed for display).

    Args:
        order_id: 0-based index of the order
        total_orders: total number of orders
    """
    display_number = order_id
    return f"Order {display_number} of {total_orders}"


def process_orders(orders: list[list[dict]]) -> None:
    """Process multiple orders and print a summary for each."""
    grand_total = 0.0
    total_items = 0

    for i, order_items in enumerate(orders):
        order_label = format_order_number(i, len(orders))
        summary = get_order_summary(order_items)

        print(f"\n{'='*40}")
        print(f"  {order_label}")
        print(f"{'='*40}")

        for item in summary["items"]:
            print(f"  {item['name']:<20s} x{item['quantity']}  ${item['line_total']:.2f}")

        financials = apply_tax_and_tip(summary["subtotal"])

        print(f"  {'─'*36}")
        print(f"  {'Subtotal':<28s} ${summary['subtotal']:.2f}")
        print(f"  {'Tax':<28s} ${financials['tax']:.2f}")
        print(f"  {'Tip':<28s} ${financials['tip']:.2f}")
        print(f"  {'TOTAL':<28s} ${financials['total']:.2f}")

        grand_total += financials["total"]
        total_items += summary["item_count"]

    return grand_total, total_items


# ─── Main ────────────────────────────────────────

if __name__ == "__main__":
    sample_orders = [
        [
            {"name": "Classic Burger", "price": 9.99, "quantity": 2, "discount_percent": 10},
            {"name": "Fries", "price": 3.49, "quantity": 2},
            {"name": "Milkshake", "price": 5.99, "quantity": 1},
        ],
        [
            {"name": "Chicken Sandwich", "price": 8.49, "quantity": 1},
            {"name": "Onion Rings", "price": 4.29, "quantity": 1},
            {"name": "Soda", "price": 1.99, "quantity": 3},
        ],
        [
            {"name": "Veggie Wrap", "price": 7.99, "quantity": 2, "discount_percent": 15},
            {"name": "Side Salad", "price": 4.49, "quantity": 2},
            {"name": "Iced Tea", "price": 2.49, "quantity": 2},
        ],
    ]

    print("🍔 RESTAURANT ORDER PROCESSOR")
    print("=" * 40)

    grand_total, total_items = process_orders(sample_orders)

    print(f"\n{'='*40}")
    print(f"  GRAND TOTAL: ${grand_total:.2f}")
    print(f"  TOTAL ITEMS: {total_items}")
    print(f"{'='*40}")

    # Validation — run this script to check your fixes
    import sys, os, hashlib
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    import ctf_helper

    order_label_check = format_order_number(0, 3)
    fingerprint = f"{round(grand_total, 2)}|{total_items}|{order_label_check}"
    expected_hash = "2f93e2eeb67d3060ffdbb31ca64baf10f7e338581c25a7369d380b8dd90abf62"

    if hashlib.sha256(fingerprint.encode()).hexdigest() == expected_hash:
        print(f"\n✅ All calculations correct!")
        ctf_helper.submit(2, ["buggy_script.py"])
    else:
        print(f"\n❌ Something is still wrong — keep debugging!")
