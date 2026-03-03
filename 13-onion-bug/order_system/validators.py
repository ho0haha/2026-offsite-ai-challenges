"""
Order validation module for the restaurant order processing system.

Validates orders before they enter the processing pipeline, checking
item availability, quantity limits, customer info, and special instructions.
"""

from typing import Optional
from order_system.models import (
    Order,
    OrderItem,
    MenuItem,
    ItemCategory,
    flatten_modifiers,
)


# Validation constants
MAX_QUANTITY_PER_ITEM = 20
MAX_ITEMS_PER_ORDER = 50
MAX_SPECIAL_INSTRUCTIONS_LENGTH = 500
MAX_MODIFIER_DEPTH = 10
ALCOHOL_CUTOFF_HOUR = 22  # No alcohol orders after 10 PM
MIN_TABLE_NUMBER = 1
MAX_TABLE_NUMBER = 60


class ValidationError(Exception):
    """Raised when order validation fails."""

    def __init__(self, message: str, field: Optional[str] = None):
        self.message = message
        self.field = field
        super().__init__(self.message)


def validate_order(order: Order) -> list[str]:
    """
    Validate an order through all validation checks.

    Returns a list of validation error messages. An empty list means
    the order is valid.
    """
    errors = []

    # Check that the order has items
    if not order.items:
        errors.append("Order must contain at least one item")
        return errors

    # Check total item count
    if len(order.items) > MAX_ITEMS_PER_ORDER:
        errors.append(
            f"Order exceeds maximum of {MAX_ITEMS_PER_ORDER} line items"
        )

    # Validate customer name
    if not order.customer_name or not order.customer_name.strip():
        errors.append("Customer name is required")

    # Validate table number for dine-in orders
    if not order.is_takeout:
        if order.table_number is None:
            errors.append("Table number is required for dine-in orders")
        elif not (MIN_TABLE_NUMBER <= order.table_number <= MAX_TABLE_NUMBER):
            errors.append(
                f"Table number must be between {MIN_TABLE_NUMBER} and {MAX_TABLE_NUMBER}"
            )

    # Validate special instructions at order level
    cleaned_instructions = order.special_instructions.strip()
    if len(cleaned_instructions) > MAX_SPECIAL_INSTRUCTIONS_LENGTH:
        errors.append(
            f"Special instructions exceed {MAX_SPECIAL_INSTRUCTIONS_LENGTH} characters"
        )

    # Validate each item in the order
    for i, item in enumerate(order.items):
        item_errors = _validate_order_item(item, i)
        errors.extend(item_errors)

    return errors


def _validate_order_item(item: OrderItem, index: int) -> list[str]:
    """Validate a single order item."""
    errors = []
    prefix = f"Item {index + 1} ({item.menu_item.name})"

    # Check availability
    if not item.menu_item.available:
        errors.append(f"{prefix}: Item is currently unavailable")

    # Check quantity
    if item.quantity < 1:
        errors.append(f"{prefix}: Quantity must be at least 1")
    elif item.quantity > MAX_QUANTITY_PER_ITEM:
        errors.append(
            f"{prefix}: Quantity exceeds maximum of {MAX_QUANTITY_PER_ITEM}"
        )

    # Check price sanity
    if item.menu_item.base_price <= 0:
        errors.append(f"{prefix}: Invalid price")

    # Validate modifiers if present
    if item.modifiers:
        mod_errors = _validate_modifiers(item.modifiers, prefix)
        errors.extend(mod_errors)

    # Validate item-level special instructions
    if item.special_instructions is not None:
        if len(item.special_instructions.strip()) > MAX_SPECIAL_INSTRUCTIONS_LENGTH:
            errors.append(
                f"{prefix}: Special instructions too long"
            )

    # Alcohol time restrictions
    if item.menu_item.category == ItemCategory.ALCOHOL:
        _check_alcohol_restrictions(item, prefix, errors)

    return errors


def _validate_modifiers(
    modifiers: dict, prefix: str, depth: int = 0
) -> list[str]:
    """
    Validate modifier dictionary structure and values.
    """
    errors = []

    if depth > MAX_MODIFIER_DEPTH:
        errors.append(f"{prefix}: Modifier nesting exceeds maximum depth")
        return errors

    for key, value in modifiers.items():
        if not isinstance(key, str):
            errors.append(f"{prefix}: Modifier keys must be strings")
            continue

        if isinstance(value, dict):
            nested_errors = _validate_modifiers(value, prefix, depth + 1)
            errors.extend(nested_errors)
        elif isinstance(value, (list, tuple)):
            for element in value:
                if isinstance(element, dict):
                    nested_errors = _validate_modifiers(
                        element, prefix, depth + 1
                    )
                    errors.extend(nested_errors)

    return errors


def _check_alcohol_restrictions(
    item: OrderItem, prefix: str, errors: list[str]
) -> None:
    """Check time-based restrictions for alcohol orders."""
    from datetime import datetime

    current_hour = datetime.now().hour
    if current_hour >= ALCOHOL_CUTOFF_HOUR:
        errors.append(
            f"{prefix}: Alcohol orders not accepted after {ALCOHOL_CUTOFF_HOUR}:00"
        )


def validate_menu_item(item: MenuItem) -> list[str]:
    """Validate a menu item definition."""
    errors = []

    if not item.name or not item.name.strip():
        errors.append("Menu item name is required")

    if item.base_price < 0:
        errors.append("Price cannot be negative")

    if item.prep_time_minutes < 0:
        errors.append("Prep time cannot be negative")

    return errors
