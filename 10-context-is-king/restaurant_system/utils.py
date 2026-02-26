"""
Utility functions for the restaurant management system.
"""

import math
from datetime import datetime, timedelta
from typing import List, Any


def round_currency(amount: float) -> float:
    """Round a currency amount to 2 decimal places."""
    return round(amount, 2)


def calculate_tax(subtotal: float, tax_rate: float) -> float:
    """Calculate tax on a subtotal."""
    return round_currency(subtotal * tax_rate)


def calculate_tip(subtotal: float, tip_percentage: float) -> float:
    """Calculate tip on a subtotal."""
    return round_currency(subtotal * tip_percentage)


def generate_receipt_number() -> str:
    """Generate a receipt number based on timestamp."""
    now = datetime.now()
    return f"RCP-{now.strftime('%Y%m%d%H%M%S')}"


def format_currency(amount: float) -> str:
    """Format a number as currency string."""
    return f"${amount:,.2f}"


def format_datetime(dt: datetime) -> str:
    """Format a datetime for display."""
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def format_date(dt: datetime) -> str:
    """Format a date for display."""
    return dt.strftime("%Y-%m-%d")


def paginate(items: List[Any], page: int, page_size: int = 10) -> List[Any]:
    """Paginate a list of items."""
    if page < 1:
        page = 1
    start = (page - 1) * page_size
    end = start + page_size
    return items[start:end]


def truncate_string(text: str, max_length: int = 50) -> str:
    """Truncate a string with ellipsis."""
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


def calculate_percentage(part: float, whole: float) -> float:
    """Calculate percentage with safety for division by zero."""
    if whole == 0:
        return 0.0
    return round((part / whole) * 100, 1)


def is_within_business_hours(hour: int, opening: int, closing: int) -> bool:
    """Check if a given hour is within business hours."""
    return opening <= hour < closing


def time_until_closing(current_hour: int, closing_hour: int) -> int:
    """Calculate hours until closing."""
    if current_hour >= closing_hour:
        return 0
    return closing_hour - current_hour
