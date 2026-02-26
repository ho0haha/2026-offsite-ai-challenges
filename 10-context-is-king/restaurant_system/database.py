"""
In-memory database and repository layer for the restaurant system.
Provides CRUD operations for all data models.
"""

from typing import Dict, List, Optional
from .models import Customer, MenuItem, Order, Payment, Reservation


class Database:
    """In-memory database that stores all restaurant data."""

    def __init__(self):
        self._customers: Dict[str, Customer] = {}
        self._menu_items: Dict[str, MenuItem] = {}
        self._orders: Dict[str, Order] = {}
        self._payments: Dict[str, Payment] = {}
        self._reservations: Dict[str, Reservation] = {}

    def clear(self):
        """Clear all data from the database."""
        self._customers.clear()
        self._menu_items.clear()
        self._orders.clear()
        self._payments.clear()
        self._reservations.clear()

    # --- Customer operations ---

    def add_customer(self, customer: Customer) -> Customer:
        self._customers[customer.id] = customer
        return customer

    def get_customer(self, customer_id: str) -> Optional[Customer]:
        return self._customers.get(customer_id)

    def get_all_customers(self) -> List[Customer]:
        return list(self._customers.values())

    def update_customer(self, customer: Customer) -> Customer:
        if customer.id not in self._customers:
            raise ValueError(f"Customer {customer.id} not found")
        self._customers[customer.id] = customer
        return customer

    def delete_customer(self, customer_id: str) -> bool:
        if customer_id in self._customers:
            del self._customers[customer_id]
            return True
        return False

    # --- Menu Item operations ---

    def add_menu_item(self, item: MenuItem) -> MenuItem:
        self._menu_items[item.id] = item
        return item

    def get_menu_item(self, item_id: str) -> Optional[MenuItem]:
        return self._menu_items.get(item_id)

    def get_all_menu_items(self) -> List[MenuItem]:
        return list(self._menu_items.values())

    def update_menu_item(self, item: MenuItem) -> MenuItem:
        if item.id not in self._menu_items:
            raise ValueError(f"Menu item {item.id} not found")
        self._menu_items[item.id] = item
        return item

    def delete_menu_item(self, item_id: str) -> bool:
        if item_id in self._menu_items:
            del self._menu_items[item_id]
            return True
        return False

    # --- Order operations ---

    def add_order(self, order: Order) -> Order:
        self._orders[order.id] = order
        return order

    def get_order(self, order_id: str) -> Optional[Order]:
        return self._orders.get(order_id)

    def get_all_orders(self) -> List[Order]:
        return list(self._orders.values())

    def get_orders_by_customer(self, customer_id: str) -> List[Order]:
        return [o for o in self._orders.values() if o.customer_id == customer_id]

    def update_order(self, order: Order) -> Order:
        if order.id not in self._orders:
            raise ValueError(f"Order {order.id} not found")
        self._orders[order.id] = order
        return order

    # --- Payment operations ---

    def add_payment(self, payment: Payment) -> Payment:
        self._payments[payment.id] = payment
        return payment

    def get_payment(self, payment_id: str) -> Optional[Payment]:
        return self._payments.get(payment_id)

    def get_payments_by_order(self, order_id: str) -> List[Payment]:
        return [p for p in self._payments.values() if p.order_id == order_id]

    # --- Reservation operations ---

    def add_reservation(self, reservation: Reservation) -> Reservation:
        self._reservations[reservation.id] = reservation
        return reservation

    def get_reservation(self, reservation_id: str) -> Optional[Reservation]:
        return self._reservations.get(reservation_id)

    def get_reservations_by_customer(self, customer_id: str) -> List[Reservation]:
        return [r for r in self._reservations.values() if r.customer_id == customer_id]
