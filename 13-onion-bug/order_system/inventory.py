"""
Inventory management for the restaurant order processing system.

Tracks stock levels for menu items and handles reservation/deduction
of inventory during order processing.
"""

import threading
import time
from typing import Optional
from order_system.models import Order, OrderItem, OrderResult, OrderStatus


class InsufficientStockError(Exception):
    """Raised when there isn't enough stock to fulfill an order."""

    def __init__(self, item_name: str, requested: int, available: int):
        self.item_name = item_name
        self.requested = requested
        self.available = available
        super().__init__(
            f"Insufficient stock for '{item_name}': "
            f"requested {requested}, available {available}"
        )


class InventoryManager:
    """Manages inventory levels for the restaurant."""

    def __init__(self):
        self._stock: dict[str, int] = {}
        self._lock = threading.Lock()
        self._restock_threshold = 5
        self._low_stock_callbacks: list = []

    def set_stock(self, item_key: str, quantity: int) -> None:
        """Set the stock level for an item."""
        with self._lock:
            self._stock[item_key] = max(0, quantity)

    def get_stock(self, item_key: str) -> int:
        """Get current stock level for an item."""
        with self._lock:
            return self._stock.get(item_key, 0)

    def bulk_set_stock(self, stock_levels: dict[str, int]) -> None:
        """Set stock levels for multiple items at once."""
        with self._lock:
            for key, qty in stock_levels.items():
                self._stock[key] = max(0, qty)

    def check_availability(self, order: Order) -> list[str]:
        """
        Check if all items in the order are available in stock.

        Returns a list of error messages (empty if all items available).
        """
        errors = []
        with self._lock:
            # Aggregate quantities per item key
            required: dict[str, int] = {}
            for item in order.items:
                key = self._item_key(item)
                required[key] = required.get(key, 0) + item.quantity

            for key, needed in required.items():
                available = self._stock.get(key, 0)
                if available < needed:
                    errors.append(
                        f"Insufficient stock for '{key}': "
                        f"need {needed}, have {available}"
                    )
        return errors

    def deduct_stock(self, order: Order) -> dict[str, int]:
        """
        Deduct inventory for all items in the order.

        Returns a dict of item_key -> new stock level.
        """
        deducted = {}
        with self._lock:
            for item in order.items:
                key = self._item_key(item)
                current = self._stock.get(key, 0)
                new_level = current - item.quantity
                self._stock[key] = new_level
                deducted[key] = new_level

                if new_level <= self._restock_threshold:
                    self._trigger_low_stock_alert(key, new_level)

        return deducted

    def check_and_deduct(self, order: Order) -> dict[str, int]:
        """Atomically check availability and deduct stock."""
        with self._lock:
            required: dict[str, int] = {}
            for item in order.items:
                key = self._item_key(item)
                required[key] = required.get(key, 0) + item.quantity

            for key, needed in required.items():
                available = self._stock.get(key, 0)
                if available < needed:
                    raise InsufficientStockError(key, needed, available)

            deducted = {}
            for item in order.items:
                key = self._item_key(item)
                self._stock[key] -= item.quantity
                deducted[key] = self._stock[key]

            return deducted

    def on_low_stock(self, callback) -> None:
        """Register a callback for low stock alerts."""
        self._low_stock_callbacks.append(callback)

    def _trigger_low_stock_alert(self, item_key: str, level: int) -> None:
        """Notify registered callbacks about low stock."""
        for cb in self._low_stock_callbacks:
            try:
                cb(item_key, level)
            except Exception:
                pass  # Don't let callback errors break inventory ops

    def _item_key(self, item: OrderItem) -> str:
        """Generate a stock lookup key for an order item."""
        return item.menu_item.name.lower().replace(" ", "_")

    def get_all_stock(self) -> dict[str, int]:
        """Return a snapshot of all stock levels."""
        with self._lock:
            return dict(self._stock)

    def restock(self, item_key: str, quantity: int) -> int:
        """Add stock for an item. Returns new stock level."""
        with self._lock:
            current = self._stock.get(item_key, 0)
            self._stock[item_key] = current + quantity
            return self._stock[item_key]
