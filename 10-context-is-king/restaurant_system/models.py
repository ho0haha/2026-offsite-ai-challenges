"""
Data models for the restaurant management system.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional
import uuid


class OrderStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    READY = "ready"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class PaymentMethod(Enum):
    CASH = "cash"
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    LOYALTY_POINTS = "loyalty_points"


class MenuCategory(Enum):
    APPETIZER = "appetizer"
    MAIN_COURSE = "main_course"
    DESSERT = "dessert"
    BEVERAGE = "beverage"
    SIDE = "side"


@dataclass
class MenuItem:
    id: str = ""
    name: str = ""
    description: str = ""
    price: float = 0.0
    category: MenuCategory = MenuCategory.MAIN_COURSE
    is_available: bool = True
    prep_time_minutes: int = 15
    calories: int = 0

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:8]


@dataclass
class Customer:
    id: str = ""
    name: str = ""
    email: str = ""
    phone: str = ""
    created_at: datetime = None
    total_spent: float = 0.0
    order_count: int = 0
    loyalty_points: int = 0
    loyalty_points_earned: int = 0
    loyalty_points_redeemed: int = 0

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:8]
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class OrderItem:
    menu_item_id: str = ""
    menu_item_name: str = ""
    quantity: int = 1
    unit_price: float = 0.0
    special_instructions: str = ""

    @property
    def subtotal(self) -> float:
        return self.unit_price * self.quantity


@dataclass
class Order:
    id: str = ""
    customer_id: str = ""
    items: List[OrderItem] = field(default_factory=list)
    status: OrderStatus = OrderStatus.PENDING
    created_at: datetime = None
    total: float = 0.0
    tax: float = 0.0
    tip: float = 0.0
    discount: float = 0.0
    payment_method: Optional[PaymentMethod] = None
    is_paid: bool = False
    notes: str = ""
    loyalty_points_earned: int = 0

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:8]
        if self.created_at is None:
            self.created_at = datetime.now()

    @property
    def subtotal(self) -> float:
        return sum(item.subtotal for item in self.items)

    @property
    def grand_total(self) -> float:
        return self.subtotal + self.tax + self.tip - self.discount


@dataclass
class Payment:
    id: str = ""
    order_id: str = ""
    amount: float = 0.0
    method: PaymentMethod = PaymentMethod.CASH
    processed_at: datetime = None
    is_successful: bool = False

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:8]
        if self.processed_at is None:
            self.processed_at = datetime.now()


@dataclass
class Reservation:
    id: str = ""
    customer_id: str = ""
    party_size: int = 2
    reservation_time: datetime = None
    notes: str = ""
    is_confirmed: bool = False

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:8]
