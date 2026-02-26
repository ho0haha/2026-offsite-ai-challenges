"""
Payment processing service.
Handles payment collection and transaction management.
"""

from typing import Optional
from .models import Order, Payment, PaymentMethod, OrderStatus
from .database import Database


class PaymentService:
    """Service for processing restaurant payments."""

    def __init__(self, db: Database, customer_service=None):
        self.db = db
        self.customer_service = customer_service

    def process_payment(
        self, order_id: str, method: PaymentMethod, amount: Optional[float] = None
    ) -> Payment:
        """Process a payment for an order."""
        order = self.db.get_order(order_id)
        if not order:
            raise ValueError(f"Order {order_id} not found")

        if order.is_paid:
            raise ValueError("Order is already paid")

        if order.status == OrderStatus.CANCELLED:
            raise ValueError("Cannot pay for a cancelled order")

        payment_amount = amount if amount is not None else order.grand_total

        if payment_amount <= 0:
            raise ValueError("Payment amount must be positive")

        if payment_amount < order.grand_total:
            raise ValueError("Payment amount is less than order total")

        payment = Payment(
            order_id=order_id,
            amount=payment_amount,
            method=method,
            is_successful=True,
        )

        order.is_paid = True
        order.payment_method = method
        self.db.update_order(order)

        return self.db.add_payment(payment)

    def get_payment(self, payment_id: str) -> Optional[Payment]:
        """Get a payment by ID."""
        return self.db.get_payment(payment_id)

    def get_payments_for_order(self, order_id: str):
        """Get all payments for an order."""
        return self.db.get_payments_by_order(order_id)

    def calculate_change(self, order_id: str, amount_tendered: float) -> float:
        """Calculate change for a cash payment."""
        order = self.db.get_order(order_id)
        if not order:
            raise ValueError(f"Order {order_id} not found")

        change = amount_tendered - order.grand_total
        if change < 0:
            raise ValueError("Insufficient payment amount")

        return round(change, 2)

    def add_tip(self, order_id: str, tip_amount: float) -> Order:
        """Add a tip to an order."""
        order = self.db.get_order(order_id)
        if not order:
            raise ValueError(f"Order {order_id} not found")

        if tip_amount < 0:
            raise ValueError("Tip cannot be negative")

        order.tip = tip_amount
        return self.db.update_order(order)

    # --- Loyalty Points Payment ---
    # TODO: Implement apply_loyalty_discount method
    #
    # apply_loyalty_discount(customer_id: str, order_total: float, points_to_redeem: int) -> dict
    #   Applies a loyalty points discount to an order.
    #   Returns dict with: discount_amount, final_total, points_redeemed
    #   The discount cannot exceed the order total.
    #   Must validate that the customer has enough points.
