"""
Input validation functions for the restaurant management system.
"""

import re
from . import config


def validate_price(price: float) -> None:
    """Validate a menu item price."""
    if not isinstance(price, (int, float)):
        raise TypeError("Price must be a number")
    if price < config.MIN_MENU_ITEM_PRICE:
        raise ValueError(
            f"Price must be at least ${config.MIN_MENU_ITEM_PRICE:.2f}"
        )
    if price > config.MAX_MENU_ITEM_PRICE:
        raise ValueError(
            f"Price cannot exceed ${config.MAX_MENU_ITEM_PRICE:.2f}"
        )


def validate_email(email: str) -> None:
    """Validate an email address format."""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(pattern, email):
        raise ValueError(f"Invalid email format: {email}")


def validate_non_empty_string(value: str, field_name: str = "Field") -> None:
    """Validate that a string is not empty."""
    if not value or not value.strip():
        raise ValueError(f"{field_name} cannot be empty")


def validate_positive_integer(value: int, field_name: str = "Value") -> None:
    """Validate that a value is a positive integer."""
    if not isinstance(value, int) or value < 1:
        raise ValueError(f"{field_name} must be a positive integer")


def validate_party_size(size: int) -> None:
    """Validate a reservation party size."""
    validate_positive_integer(size, "Party size")
    if size > config.MAX_PARTY_SIZE:
        raise ValueError(
            f"Party size cannot exceed {config.MAX_PARTY_SIZE}"
        )


def validate_phone(phone: str) -> None:
    """Validate a phone number format (basic)."""
    cleaned = re.sub(r"[\s\-\(\)]", "", phone)
    if not cleaned.isdigit() or len(cleaned) < 10:
        raise ValueError(f"Invalid phone number: {phone}")


def validate_order_quantity(quantity: int) -> None:
    """Validate order item quantity."""
    if quantity < 1:
        raise ValueError("Quantity must be at least 1")
    if quantity > 100:
        raise ValueError("Quantity cannot exceed 100")


def validate_tip_percentage(percentage: float) -> None:
    """Validate a tip percentage."""
    if percentage < 0:
        raise ValueError("Tip percentage cannot be negative")
    if percentage > 1.0:
        raise ValueError("Tip percentage cannot exceed 100%")
