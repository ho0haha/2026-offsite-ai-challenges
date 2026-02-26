"""
Customer management service.
Handles customer registration, lookup, and profile management.
"""

from typing import List, Optional
from .models import Customer
from .database import Database
from .validators import validate_email, validate_non_empty_string


class CustomerService:
    """Service for managing restaurant customers."""

    def __init__(self, db: Database):
        self.db = db

    def register_customer(
        self, name: str, email: str = "", phone: str = ""
    ) -> Customer:
        """Register a new customer."""
        validate_non_empty_string(name, "Customer name")
        if email:
            validate_email(email)

        customer = Customer(name=name, email=email, phone=phone)
        return self.db.add_customer(customer)

    def get_customer(self, customer_id: str) -> Optional[Customer]:
        """Get a customer by ID."""
        return self.db.get_customer(customer_id)

    def get_all_customers(self) -> List[Customer]:
        """Get all customers."""
        return self.db.get_all_customers()

    def find_customer_by_email(self, email: str) -> Optional[Customer]:
        """Find a customer by email address."""
        for customer in self.db.get_all_customers():
            if customer.email.lower() == email.lower():
                return customer
        return None

    def find_customers_by_name(self, name: str) -> List[Customer]:
        """Find customers by name (partial match)."""
        name_lower = name.lower()
        return [
            c for c in self.db.get_all_customers() if name_lower in c.name.lower()
        ]

    def update_customer_info(
        self,
        customer_id: str,
        name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
    ) -> Customer:
        """Update customer profile information."""
        customer = self.db.get_customer(customer_id)
        if not customer:
            raise ValueError(f"Customer {customer_id} not found")

        if name is not None:
            validate_non_empty_string(name, "Customer name")
            customer.name = name

        if email is not None:
            if email:
                validate_email(email)
            customer.email = email

        if phone is not None:
            customer.phone = phone

        return self.db.update_customer(customer)

    def get_top_customers(self, limit: int = 10) -> List[Customer]:
        """Get top customers by total spent."""
        customers = self.db.get_all_customers()
        return sorted(customers, key=lambda c: c.total_spent, reverse=True)[:limit]

    def delete_customer(self, customer_id: str) -> bool:
        """Delete a customer."""
        return self.db.delete_customer(customer_id)

    # --- Loyalty Points Methods ---
    # TODO: Implement the following methods for the loyalty points feature:
    #
    # get_loyalty_balance(customer_id: str) -> int
    #   Returns the customer's current loyalty points balance.
    #
    # add_loyalty_points(customer_id: str, points: int) -> int
    #   Adds points to the customer's balance and earned history.
    #   Returns the new balance.
    #
    # redeem_loyalty_points(customer_id: str, points: int) -> float
    #   Redeems points for a dollar discount.
    #   Updates balance and redeemed history.
    #   Returns the dollar discount amount.
    #   Raises ValueError if insufficient balance.
