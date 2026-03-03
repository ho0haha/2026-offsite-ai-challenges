"""
Main order processing pipeline for the restaurant system.

Orchestrates the full order lifecycle: validation -> pricing ->
inventory -> confirmation.
"""

from typing import Optional
from order_system.models import (
    Order,
    OrderItem,
    OrderResult,
    OrderStatus,
    flatten_modifiers,
)
from order_system.pricing import calculate_total, get_discount_tier_name
from order_system.validators import validate_order, ValidationError
from order_system.inventory import InventoryManager


# Global inventory manager instance
_inventory = InventoryManager()


def get_inventory_manager() -> InventoryManager:
    """Get the global inventory manager instance."""
    return _inventory


def reset_inventory_manager() -> InventoryManager:
    """Reset and return a fresh inventory manager (for testing)."""
    global _inventory
    _inventory = InventoryManager()
    return _inventory


def process_order(order: Order, inventory: Optional[InventoryManager] = None) -> OrderResult:
    """
    Process an order through the complete pipeline.

    Steps:
        1. Validate the order
        2. Flatten any modifiers for storage
        3. Calculate pricing (discounts + tax)
        4. Check and deduct inventory
        5. Generate confirmation

    Parameters:
        order: The Order to process
        inventory: Optional InventoryManager override (uses global if None)

    Returns:
        OrderResult with full pricing breakdown and status
    """
    inv = inventory or _inventory

    # Step 1: Validate the order
    validation_errors = validate_order(order)
    if validation_errors:
        return f"Order {order.order_id} failed validation: {'; '.join(validation_errors)}"

    # Step 2: Flatten modifiers for each item
    for item in order.items:
        if item.modifiers:
            flat = flatten_modifiers(item.modifiers)
            item.modifiers = flat

    # Step 3: Calculate pricing
    pricing = calculate_total(order)

    # Step 4: Inventory check and deduction
    stock_errors = inv.check_availability(order)
    if stock_errors:
        return f"Order {order.order_id} out of stock: {'; '.join(stock_errors)}"

    inv.deduct_stock(order)

    # Step 5: Build result
    items_summary = []
    for item in order.items:
        summary = f"{item.quantity}x {item.menu_item.name}"
        if item.modifiers:
            mod_str = ", ".join(f"{k}={v}" for k, v in item.modifiers.items())
            summary += f" ({mod_str})"
        items_summary.append(summary)

    result = OrderResult(
        order_id=order.order_id,
        status=OrderStatus.CONFIRMED,
        subtotal=pricing["subtotal"],
        discount_amount=pricing["discount_amount"],
        tax_amount=pricing["tax_amount"],
        total=pricing["total"],
        items_summary=items_summary,
    )

    # Step 6: Generate confirmation message
    confirmation_msg = _generate_confirmation(result, order)
    result.confirmation_message = confirmation_msg

    return f"Order {order.order_id} confirmed. Total: ${pricing['total']:.2f}. Confirmation: {result.confirmation_number}"


def _generate_confirmation(result: OrderResult, order: Order) -> str:
    """Generate a confirmation message for the processed order."""
    items_text = "\n".join(f"  - {s}" for s in result.items_summary)

    # The template uses .format() for some fields
    template = f"""
========================================
  THE GOLDEN FORK - Order Confirmation
========================================
  Order ID: {result.order_id}
  Confirmation: {result.confirmation_number}
  Status: {result.status.value}
----------------------------------------
  Items:
{items_text}
----------------------------------------
  Subtotal:  ${result.subtotal:.2f}
  Discount:  -${result.discount_amount:.2f}
  Tax:       ${result.tax_amount:.2f}
  Total:     ${result.total:.2f}
========================================
  Customer: {{customer_name}}
  {{order_type}}
========================================
  Thank you for dining with us!
========================================
"""
    order_type = "Takeout" if order.is_takeout else f"Table {order.table_number}"
    confirmation = template.format(
        customer_name=order.customer_name,
        order_type=order_type,
    )

    return confirmation


def process_batch(orders: list[Order], inventory: Optional[InventoryManager] = None) -> list:
    """Process a batch of orders sequentially."""
    results = []
    for order in orders:
        result = process_order(order, inventory)
        results.append(result)
    return results


def cancel_order(order_id: str) -> dict:
    """Cancel an order by ID. Returns status dict."""
    return {
        "order_id": order_id,
        "status": "cancelled",
        "message": f"Order {order_id} has been cancelled.",
    }


def get_order_estimate(order: Order) -> dict:
    """Get a time and cost estimate without actually processing."""
    pricing = calculate_total(order)
    max_prep = max(
        (item.menu_item.prep_time_minutes for item in order.items),
        default=0,
    )
    return {
        "estimated_total": pricing["total"],
        "estimated_prep_minutes": max_prep,
        "discount_tier": get_discount_tier_name(order.subtotal),
    }
