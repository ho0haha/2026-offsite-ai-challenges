"""
Data models for the restaurant order processing system.

Defines the core domain objects used throughout the pipeline:
MenuItem, OrderItem, Order, OrderResult, and related enums.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional
import uuid
from datetime import datetime


class OrderStatus(Enum):
    """Possible states for an order in the processing pipeline."""
    PENDING = "pending"
    VALIDATED = "validated"
    PRICED = "priced"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ItemCategory(Enum):
    """Menu item categories for pricing and tax rules."""
    ENTREE = "entree"
    APPETIZER = "appetizer"
    DESSERT = "dessert"
    BEVERAGE = "beverage"
    GIFT_CARD = "gift_card"
    ALCOHOL = "alcohol"
    SIDE = "side"


@dataclass
class MenuItem:
    """Represents a single item on the restaurant menu."""
    name: str
    base_price: float
    category: ItemCategory
    tax_exempt: bool = False
    available: bool = True
    prep_time_minutes: int = 10
    allergens: list[str] = field(default_factory=list)

    def __post_init__(self):
        if self.category == ItemCategory.GIFT_CARD:
            self.tax_exempt = True
        if self.base_price < 0:
            raise ValueError(f"Price cannot be negative: {self.base_price}")


@dataclass
class OrderItem:
    """An item within a customer order, with quantity and modifiers."""
    menu_item: MenuItem
    quantity: int = 1
    modifiers: Optional[dict[str, Any]] = None
    special_instructions: Optional[str] = None

    @property
    def line_total(self) -> float:
        """Calculate the base line total before discounts/tax."""
        modifier_upcharge = self._calculate_modifier_upcharge()
        return (self.menu_item.base_price + modifier_upcharge) * self.quantity

    def _calculate_modifier_upcharge(self) -> float:
        """Calculate additional charges from modifiers."""
        if not self.modifiers:
            return 0.0
        upcharge = 0.0
        flat = self.modifiers.get("upcharges", {})
        for _, amount in flat.items():
            if isinstance(amount, (int, float)):
                upcharge += amount
        return upcharge


def flatten_modifiers(modifiers: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    """
    Flatten a nested modifier dictionary into a single-level dict with
    dot-separated keys for storage and display.

    Example:
        {"add": {"extra": {"cheese": True}}} -> {"add.extra.cheese": True}
    """
    result = {}
    for key, value in modifiers.items():
        full_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            nested = flatten_modifiers(value, full_key)
            result.update(nested)
        else:
            result[full_key] = value
    return result


@dataclass
class Order:
    """Represents a complete customer order."""
    order_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    customer_name: str = ""
    items: list[OrderItem] = field(default_factory=list)
    special_instructions: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    table_number: Optional[int] = None
    is_takeout: bool = False

    @property
    def subtotal(self) -> float:
        """Calculate order subtotal before discounts and tax."""
        return sum(item.line_total for item in self.items)

    @property
    def item_count(self) -> int:
        """Total number of individual items in the order."""
        return sum(item.quantity for item in self.items)

    def add_item(self, item: OrderItem) -> None:
        """Add an item to the order."""
        self.items.append(item)

    def remove_item(self, index: int) -> Optional[OrderItem]:
        """Remove an item by index, returns the removed item or None."""
        if 0 <= index < len(self.items):
            return self.items.pop(index)
        return None


@dataclass
class OrderResult:
    """
    Result of processing an order through the full pipeline.
    Contains pricing breakdown, status, and confirmation details.
    """
    order_id: str
    status: OrderStatus
    subtotal: float = 0.0
    discount_amount: float = 0.0
    tax_amount: float = 0.0
    total: float = 0.0
    items_summary: list[str] = field(default_factory=list)
    confirmation_number: str = field(
        default_factory=lambda: f"GF-{uuid.uuid4().hex[:6].upper()}"
    )
    error_message: Optional[str] = None
    processed_at: datetime = field(default_factory=datetime.now)

    @property
    def discount_percentage(self) -> float:
        """Calculate the effective discount percentage."""
        if self.subtotal == 0:
            return 0.0
        return (self.discount_amount / self.subtotal) * 100

    def to_dict(self) -> dict:
        """Serialize result to a dictionary."""
        return {
            "order_id": self.order_id,
            "status": self.status.value,
            "subtotal": round(self.subtotal, 2),
            "discount": round(self.discount_amount, 2),
            "tax": round(self.tax_amount, 2),
            "total": round(self.total, 2),
            "confirmation": self.confirmation_number,
            "items": self.items_summary,
            "error": self.error_message,
        }


# -- Menu catalog for the restaurant --

MENU_CATALOG: dict[str, MenuItem] = {
    "classic_burger": MenuItem(
        name="Classic Burger",
        base_price=12.99,
        category=ItemCategory.ENTREE,
        prep_time_minutes=15,
        allergens=["gluten", "dairy"],
    ),
    "jalapeno_burger": MenuItem(
        name="Jalape{n}o Burger",
        base_price=14.99,
        category=ItemCategory.ENTREE,
        prep_time_minutes=15,
        allergens=["gluten", "dairy"],
    ),
    "caesar_salad": MenuItem(
        name="Caesar Salad",
        base_price=9.99,
        category=ItemCategory.APPETIZER,
        prep_time_minutes=8,
        allergens=["dairy", "fish"],
    ),
    "truffle_fries": MenuItem(
        name="Truffle Fries",
        base_price=7.99,
        category=ItemCategory.SIDE,
        prep_time_minutes=10,
        allergens=["gluten"],
    ),
    "chocolate_cake": MenuItem(
        name="Chocolate Lava Cake",
        base_price=8.99,
        category=ItemCategory.DESSERT,
        prep_time_minutes=12,
        allergens=["gluten", "dairy", "eggs"],
    ),
    "craft_ipa": MenuItem(
        name="Craft IPA",
        base_price=7.50,
        category=ItemCategory.ALCOHOL,
        prep_time_minutes=2,
    ),
    "lemonade": MenuItem(
        name="Fresh Lemonade",
        base_price=3.99,
        category=ItemCategory.BEVERAGE,
        prep_time_minutes=3,
    ),
    "gift_card_25": MenuItem(
        name="Gift Card $25",
        base_price=25.00,
        category=ItemCategory.GIFT_CARD,
        tax_exempt=True,
        prep_time_minutes=0,
    ),
    "gift_card_50": MenuItem(
        name="Gift Card $50",
        base_price=50.00,
        category=ItemCategory.GIFT_CARD,
        tax_exempt=True,
        prep_time_minutes=0,
    ),
}
