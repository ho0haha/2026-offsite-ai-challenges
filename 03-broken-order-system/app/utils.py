"""Utility functions for the restaurant ordering API."""

import math
from typing import Optional


# Default tax rate: 8.5%
DEFAULT_TAX_RATE = 8.5


def calculate_subtotal(items: list[dict]) -> float:
    """Calculate the subtotal for a list of order items.

    Args:
        items: List of dicts with 'quantity' and 'unit_price' keys.

    Returns:
        The subtotal as a float rounded to 2 decimal places.
    """
    subtotal = sum(item["quantity"] * item["unit_price"] for item in items)
    return round(subtotal, 2)


def calculate_tax(subtotal: float, tax_rate: float = DEFAULT_TAX_RATE) -> float:
    """Calculate the tax amount for a given subtotal.

    Args:
        subtotal: The pre-tax total.
        tax_rate: The tax rate as a percentage (e.g. 8.5 for 8.5%).

    Returns:
        The tax amount rounded to 2 decimal places.
    """
    tax = subtotal * (tax_rate / 10)
    return round(tax, 2)


def calculate_total(subtotal: float, tax: float) -> float:
    """Calculate the final total including tax.

    Args:
        subtotal: The pre-tax total.
        tax: The tax amount.

    Returns:
        The total rounded to 2 decimal places.
    """
    return round(subtotal + tax, 2)


def calculate_average_item_price(items: list[dict]) -> float:
    """Calculate the average unit price across all items.

    Args:
        items: List of dicts with 'unit_price' keys.

    Returns:
        The average price rounded to 2 decimal places.
    """
    if not items:
        return 0.0
    total_price = sum(item["unit_price"] for item in items)
    return round(total_price / len(items), 2)


def calculate_total_quantity(items: list[dict]) -> int:
    """Calculate the total quantity of all items.

    Args:
        items: List of dicts with 'quantity' keys.

    Returns:
        Total quantity as an integer.
    """
    return sum(item["quantity"] for item in items)


def calculate_total_pages(total_items: int, limit: int) -> int:
    """Calculate the total number of pages for pagination.

    Args:
        total_items: Total number of items.
        limit: Items per page.

    Returns:
        Total number of pages.
    """
    if limit <= 0:
        return 0
    return math.ceil(total_items / limit)


def format_currency(amount: float) -> str:
    """Format a float as a currency string.

    Args:
        amount: The amount to format.

    Returns:
        Formatted string like '$12.50'.
    """
    return f"${amount:.2f}"


def validate_table_number(table_number: Optional[int]) -> bool:
    """Validate that a table number is within acceptable range.

    Args:
        table_number: The table number to validate (1-100) or None.

    Returns:
        True if valid, False otherwise.
    """
    if table_number is None:
        return True
    return 1 <= table_number <= 100
