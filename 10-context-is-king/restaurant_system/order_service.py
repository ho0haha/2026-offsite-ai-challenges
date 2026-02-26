"""
Order processing service.
Handles order creation, status updates, and order management.
"""

import math
from typing import List, Optional, Tuple
from .models import Order, OrderItem, OrderStatus, MenuCategory
from .database import Database
from .config import TAX_RATE, MIN_ORDER_AMOUNT, MAX_ORDER_ITEMS


class OrderService:
    """Service for managing restaurant orders."""

    def __init__(self, db: Database, customer_service=None):
        self.db = db
        self.customer_service = customer_service

    def create_order(self, customer_id: str) -> Order:
        """Create a new empty order for a customer."""
        customer = self.db.get_customer(customer_id)
        if not customer:
            raise ValueError(f"Customer {customer_id} not found")

        order = Order(customer_id=customer_id)
        return self.db.add_order(order)

    def add_item_to_order(
        self,
        order_id: str,
        menu_item_id: str,
        quantity: int = 1,
        special_instructions: str = "",
    ) -> Order:
        """Add a menu item to an existing order."""
        order = self.db.get_order(order_id)
        if not order:
            raise ValueError(f"Order {order_id} not found")

        if order.status != OrderStatus.PENDING:
            raise ValueError("Cannot modify a non-pending order")

        menu_item = self.db.get_menu_item(menu_item_id)
        if not menu_item:
            raise ValueError(f"Menu item {menu_item_id} not found")

        if not menu_item.is_available:
            raise ValueError(f"Menu item {menu_item.name} is not available")

        if quantity < 1:
            raise ValueError("Quantity must be at least 1")

        if len(order.items) >= MAX_ORDER_ITEMS:
            raise ValueError(f"Order cannot have more than {MAX_ORDER_ITEMS} items")

        order_item = OrderItem(
            menu_item_id=menu_item_id,
            menu_item_name=menu_item.name,
            quantity=quantity,
            unit_price=menu_item.price,
            special_instructions=special_instructions,
        )
        order.items.append(order_item)
        self._recalculate_order(order)
        return self.db.update_order(order)

    def remove_item_from_order(self, order_id: str, item_index: int) -> Order:
        """Remove an item from an order by index."""
        order = self.db.get_order(order_id)
        if not order:
            raise ValueError(f"Order {order_id} not found")

        if order.status != OrderStatus.PENDING:
            raise ValueError("Cannot modify a non-pending order")

        if item_index < 0 or item_index >= len(order.items):
            raise ValueError("Invalid item index")

        order.items.pop(item_index)
        self._recalculate_order(order)
        return self.db.update_order(order)

    def place_order(self, order_id: str) -> Order:
        """Finalize and place an order."""
        order = self.db.get_order(order_id)
        if not order:
            raise ValueError(f"Order {order_id} not found")

        if order.status != OrderStatus.PENDING:
            raise ValueError("Order is not in pending status")

        if not order.items:
            raise ValueError("Cannot place an empty order")

        if order.subtotal < MIN_ORDER_AMOUNT:
            raise ValueError(
                f"Order total must be at least ${MIN_ORDER_AMOUNT:.2f}"
            )

        order.status = OrderStatus.CONFIRMED
        self._recalculate_order(order)

        # Update customer stats
        customer = self.db.get_customer(order.customer_id)
        if customer:
            customer.total_spent += order.grand_total
            customer.order_count += 1
            self.db.update_customer(customer)

        # TODO: Award loyalty points after successful order
        # Calculate points based on amount paid (grand_total) and award them
        # using customer_service.add_loyalty_points()
        # Store earned points on the order's loyalty_points_earned field

        return self.db.update_order(order)

    def update_order_status(self, order_id: str, new_status: OrderStatus) -> Order:
        """Update the status of an order."""
        order = self.db.get_order(order_id)
        if not order:
            raise ValueError(f"Order {order_id} not found")

        valid_transitions = {
            OrderStatus.PENDING: [OrderStatus.CONFIRMED, OrderStatus.CANCELLED],
            OrderStatus.CONFIRMED: [OrderStatus.PREPARING, OrderStatus.CANCELLED],
            OrderStatus.PREPARING: [OrderStatus.READY, OrderStatus.CANCELLED],
            OrderStatus.READY: [OrderStatus.DELIVERED],
            OrderStatus.DELIVERED: [],
            OrderStatus.CANCELLED: [],
        }

        if new_status not in valid_transitions.get(order.status, []):
            raise ValueError(
                f"Cannot transition from {order.status.value} to {new_status.value}"
            )

        order.status = new_status
        return self.db.update_order(order)

    def apply_discount(self, order_id: str, discount_amount: float) -> Order:
        """Apply a discount to an order."""
        order = self.db.get_order(order_id)
        if not order:
            raise ValueError(f"Order {order_id} not found")

        if discount_amount < 0:
            raise ValueError("Discount cannot be negative")

        if discount_amount > order.subtotal:
            raise ValueError("Discount cannot exceed order subtotal")

        order.discount = discount_amount
        self._recalculate_order(order)
        return self.db.update_order(order)

    def get_order(self, order_id: str) -> Optional[Order]:
        """Get an order by ID."""
        return self.db.get_order(order_id)

    def get_customer_orders(self, customer_id: str) -> List[Order]:
        """Get all orders for a customer."""
        return self.db.get_orders_by_customer(customer_id)

    def _recalculate_order(self, order: Order):
        """Recalculate order totals."""
        order.total = order.subtotal
        order.tax = round(order.subtotal * TAX_RATE, 2)
