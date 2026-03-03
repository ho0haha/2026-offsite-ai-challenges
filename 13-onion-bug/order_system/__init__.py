"""
Restaurant Order Processing System
===================================
A full-featured order processing pipeline for "The Golden Fork" restaurant.
Handles order validation, pricing with tiered discounts, tax calculation,
inventory management, and order confirmation.
"""

from order_system.models import (
    MenuItem,
    OrderItem,
    Order,
    OrderResult,
    OrderStatus,
)
from order_system.processor import process_order
from order_system.pricing import calculate_total, apply_discount, calculate_tax
from order_system.validators import validate_order
from order_system.inventory import InventoryManager

__version__ = "2.4.1"
__all__ = [
    "MenuItem",
    "OrderItem",
    "Order",
    "OrderResult",
    "OrderStatus",
    "process_order",
    "calculate_total",
    "apply_discount",
    "calculate_tax",
    "validate_order",
    "InventoryManager",
]
