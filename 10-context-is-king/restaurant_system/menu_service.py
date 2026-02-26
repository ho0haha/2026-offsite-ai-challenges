"""
Menu management service.
Handles menu item CRUD and availability.
"""

from typing import List, Optional
from .models import MenuItem, MenuCategory
from .database import Database
from .validators import validate_price, validate_non_empty_string
from . import config


class MenuService:
    """Service for managing the restaurant menu."""

    def __init__(self, db: Database):
        self.db = db

    def add_menu_item(
        self,
        name: str,
        description: str,
        price: float,
        category: MenuCategory,
        prep_time_minutes: int = 15,
        calories: int = 0,
    ) -> MenuItem:
        """Add a new item to the menu."""
        validate_non_empty_string(name, "Menu item name")
        validate_price(price)

        item = MenuItem(
            name=name,
            description=description,
            price=price,
            category=category,
            prep_time_minutes=prep_time_minutes,
            calories=calories,
        )
        return self.db.add_menu_item(item)

    def get_menu_item(self, item_id: str) -> Optional[MenuItem]:
        """Get a menu item by ID."""
        return self.db.get_menu_item(item_id)

    def get_full_menu(self) -> List[MenuItem]:
        """Get all menu items."""
        return self.db.get_all_menu_items()

    def get_available_items(self) -> List[MenuItem]:
        """Get only available menu items."""
        return [item for item in self.db.get_all_menu_items() if item.is_available]

    def get_items_by_category(self, category: MenuCategory) -> List[MenuItem]:
        """Get menu items filtered by category."""
        return [
            item
            for item in self.db.get_all_menu_items()
            if item.category == category and item.is_available
        ]

    def update_price(self, item_id: str, new_price: float) -> MenuItem:
        """Update the price of a menu item."""
        validate_price(new_price)
        item = self.db.get_menu_item(item_id)
        if not item:
            raise ValueError(f"Menu item {item_id} not found")
        item.price = new_price
        return self.db.update_menu_item(item)

    def toggle_availability(self, item_id: str) -> MenuItem:
        """Toggle a menu item's availability."""
        item = self.db.get_menu_item(item_id)
        if not item:
            raise ValueError(f"Menu item {item_id} not found")
        item.is_available = not item.is_available
        return self.db.update_menu_item(item)

    def remove_menu_item(self, item_id: str) -> bool:
        """Remove a menu item from the menu."""
        return self.db.delete_menu_item(item_id)

    def search_menu(self, query: str) -> List[MenuItem]:
        """Search menu items by name or description."""
        query_lower = query.lower()
        return [
            item
            for item in self.db.get_all_menu_items()
            if query_lower in item.name.lower()
            or query_lower in item.description.lower()
        ]

    def get_items_under_price(self, max_price: float) -> List[MenuItem]:
        """Get available menu items under a certain price."""
        return [
            item
            for item in self.db.get_all_menu_items()
            if item.is_available and item.price <= max_price
        ]
