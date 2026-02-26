"""
Restaurant Inventory Management System

Manages inventory items with quantities, reorder levels, pricing,
and expiration tracking. Supports CSV import/export and fuzzy search.
"""

import csv
import os
from datetime import datetime, timedelta
from difflib import SequenceMatcher


class InventoryError(Exception):
    """Custom exception for inventory-related errors."""
    pass


class InventoryItem:
    """Represents a single inventory item."""

    def __init__(self, name, quantity, unit, reorder_level, price, expiry_date=None):
        if not name or not isinstance(name, str):
            raise InventoryError("Item name must be a non-empty string")
        if not isinstance(quantity, (int, float)) or quantity < 0:
            raise InventoryError(f"Quantity must be a non-negative number, got {quantity}")
        if not unit or not isinstance(unit, str):
            raise InventoryError("Unit must be a non-empty string")
        if not isinstance(reorder_level, (int, float)) or reorder_level < 0:
            raise InventoryError("Reorder level must be a non-negative number")
        if not isinstance(price, (int, float)) or price < 0:
            raise InventoryError("Price must be a non-negative number")
        if expiry_date is not None and not isinstance(expiry_date, datetime):
            raise InventoryError("Expiry date must be a datetime object or None")

        self.name = name
        self.quantity = quantity
        self.unit = unit
        self.reorder_level = reorder_level
        self.price = price
        self.expiry_date = expiry_date
        self.created_at = datetime.now()
        self.last_updated = datetime.now()

    def __repr__(self):
        return (f"InventoryItem(name='{self.name}', qty={self.quantity} {self.unit}, "
                f"price=${self.price:.2f})")

    def is_expired(self):
        """Check if the item has passed its expiry date."""
        if self.expiry_date is None:
            return False
        return datetime.now() > self.expiry_date

    def is_low_stock(self):
        """Check if the item is below its reorder level."""
        return self.quantity <= self.reorder_level

    def to_dict(self):
        """Convert item to a dictionary."""
        return {
            "name": self.name,
            "quantity": self.quantity,
            "unit": self.unit,
            "reorder_level": self.reorder_level,
            "price": self.price,
            "expiry_date": self.expiry_date.isoformat() if self.expiry_date else "",
        }


class InventoryManager:
    """Manages the full restaurant inventory."""

    def __init__(self):
        self._items = {}

    def add_item(self, name, quantity, unit, reorder_level, price, expiry_date=None):
        """Add a new item to inventory. Raises if item already exists."""
        if name in self._items:
            raise InventoryError(f"Item '{name}' already exists. Use update_quantity instead.")
        item = InventoryItem(name, quantity, unit, reorder_level, price, expiry_date)
        self._items[name] = item
        return item

    def remove_item(self, name):
        """Remove an item from inventory. Raises if not found."""
        if name not in self._items:
            raise InventoryError(f"Item '{name}' not found in inventory")
        del self._items[name]

    def update_quantity(self, name, new_quantity):
        """Update the quantity of an existing item."""
        if name not in self._items:
            raise InventoryError(f"Item '{name}' not found in inventory")
        if not isinstance(new_quantity, (int, float)) or new_quantity < 0:
            raise InventoryError("New quantity must be a non-negative number")
        self._items[name].quantity = new_quantity
        self._items[name].last_updated = datetime.now()

    def get_item(self, name):
        """Get an item by name. Raises if not found."""
        if name not in self._items:
            raise InventoryError(f"Item '{name}' not found in inventory")
        return self._items[name]

    def list_items(self):
        """Return a list of all inventory items sorted by name."""
        return sorted(self._items.values(), key=lambda item: item.name)

    def check_reorder_needed(self):
        """Return a list of items that are at or below their reorder level."""
        reorder_list = []
        for item in self._items.values():
            if item.is_low_stock():
                reorder_list.append(item)
        return sorted(reorder_list, key=lambda x: x.quantity)

    def process_delivery(self, delivery_items):
        """Process a delivery, adding quantities to existing items.

        Args:
            delivery_items: list of dicts with 'name' and 'quantity' keys

        Raises:
            InventoryError: if delivery_items is not a list, or any item
                            is missing fields or has invalid quantity.
        """
        if not isinstance(delivery_items, list):
            raise InventoryError("Delivery items must be a list")
        if len(delivery_items) == 0:
            raise InventoryError("Delivery must contain at least one item")

        processed = []
        for entry in delivery_items:
            if not isinstance(entry, dict):
                raise InventoryError("Each delivery item must be a dictionary")
            if "name" not in entry or "quantity" not in entry:
                raise InventoryError("Each delivery item must have 'name' and 'quantity'")
            if not isinstance(entry["quantity"], (int, float)) or entry["quantity"] <= 0:
                raise InventoryError(f"Delivery quantity must be positive for '{entry['name']}'")

            name = entry["name"]
            qty = entry["quantity"]

            if name not in self._items:
                raise InventoryError(f"Cannot deliver '{name}': item not in inventory")

            self._items[name].quantity += qty
            self._items[name].last_updated = datetime.now()
            processed.append({"name": name, "new_quantity": self._items[name].quantity})

        return processed

    def process_order(self, order_items):
        """Process a customer order, reducing item quantities.

        Args:
            order_items: list of dicts with 'name' and 'quantity' keys

        Raises:
            InventoryError: if any item is not found, has insufficient stock,
                            or the order is invalid.
        """
        if not isinstance(order_items, list):
            raise InventoryError("Order items must be a list")
        if len(order_items) == 0:
            raise InventoryError("Order must contain at least one item")

        # Validate all items before processing any
        for entry in order_items:
            if not isinstance(entry, dict):
                raise InventoryError("Each order item must be a dictionary")
            if "name" not in entry or "quantity" not in entry:
                raise InventoryError("Each order item must have 'name' and 'quantity'")
            if not isinstance(entry["quantity"], (int, float)) or entry["quantity"] <= 0:
                raise InventoryError(f"Order quantity must be positive for '{entry['name']}'")

            name = entry["name"]
            qty = entry["quantity"]

            if name not in self._items:
                raise InventoryError(f"Item '{name}' not found in inventory")
            if self._items[name].quantity < qty:
                raise InventoryError(
                    f"Insufficient stock for '{name}': "
                    f"requested {qty}, available {self._items[name].quantity}"
                )

        # All validation passed, now deduct quantities
        processed = []
        total_cost = 0.0
        for entry in order_items:
            name = entry["name"]
            qty = entry["quantity"]
            self._items[name].quantity -= qty
            self._items[name].last_updated = datetime.now()
            item_cost = qty * self._items[name].price
            total_cost += item_cost
            processed.append({
                "name": name,
                "quantity": qty,
                "unit_price": self._items[name].price,
                "item_cost": round(item_cost, 2),
            })

        return {"items": processed, "total_cost": round(total_cost, 2)}

    def get_inventory_value(self):
        """Calculate the total value of all inventory items."""
        total = 0.0
        for item in self._items.values():
            total += item.quantity * item.price
        return round(total, 2)

    def generate_report(self):
        """Generate a formatted inventory report string."""
        if len(self._items) == 0:
            return "Inventory Report\n================\nNo items in inventory."

        lines = ["Inventory Report", "=" * 60]
        lines.append(f"{'Item':<20} {'Qty':>8} {'Unit':<8} {'Price':>10} {'Value':>12}")
        lines.append("-" * 60)

        total_value = 0.0
        for item in sorted(self._items.values(), key=lambda x: x.name):
            value = item.quantity * item.price
            total_value += value
            status = ""
            if item.is_expired():
                status = " [EXPIRED]"
            elif item.is_low_stock():
                status = " [LOW]"
            lines.append(
                f"{item.name:<20} {item.quantity:>8.1f} {item.unit:<8} "
                f"${item.price:>9.2f} ${value:>11.2f}{status}"
            )

        lines.append("-" * 60)
        lines.append(f"{'Total Value:':<40} ${total_value:>18.2f}")
        lines.append(f"Total Items: {len(self._items)}")

        reorder = self.check_reorder_needed()
        if reorder:
            lines.append(f"\nItems needing reorder: {len(reorder)}")
            for item in reorder:
                lines.append(f"  - {item.name} (qty: {item.quantity}, reorder at: {item.reorder_level})")

        return "\n".join(lines)

    def export_to_csv(self, filepath):
        """Export inventory to a CSV file."""
        if not filepath:
            raise InventoryError("Filepath cannot be empty")

        try:
            with open(filepath, "w", newline="") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=["name", "quantity", "unit", "reorder_level", "price", "expiry_date"],
                )
                writer.writeheader()
                for item in sorted(self._items.values(), key=lambda x: x.name):
                    writer.writerow(item.to_dict())
        except OSError as e:
            raise InventoryError(f"Failed to export CSV: {e}")

    def import_from_csv(self, filepath):
        """Import inventory items from a CSV file.

        Overwrites existing items with the same name.
        """
        if not filepath:
            raise InventoryError("Filepath cannot be empty")
        if not os.path.exists(filepath):
            raise InventoryError(f"File not found: {filepath}")

        try:
            with open(filepath, "r", newline="") as f:
                reader = csv.DictReader(f)
                imported_count = 0
                for row in reader:
                    name = row.get("name", "").strip()
                    if not name:
                        continue

                    quantity = float(row.get("quantity", 0))
                    unit = row.get("unit", "units").strip()
                    reorder_level = float(row.get("reorder_level", 0))
                    price = float(row.get("price", 0))
                    expiry_str = row.get("expiry_date", "").strip()
                    expiry_date = None
                    if expiry_str:
                        try:
                            expiry_date = datetime.fromisoformat(expiry_str)
                        except ValueError:
                            raise InventoryError(f"Invalid expiry date format for '{name}': {expiry_str}")

                    if name in self._items:
                        self._items[name].quantity = quantity
                        self._items[name].unit = unit
                        self._items[name].reorder_level = reorder_level
                        self._items[name].price = price
                        self._items[name].expiry_date = expiry_date
                        self._items[name].last_updated = datetime.now()
                    else:
                        self._items[name] = InventoryItem(
                            name, quantity, unit, reorder_level, price, expiry_date
                        )
                    imported_count += 1

                return imported_count
        except InventoryError:
            raise
        except Exception as e:
            raise InventoryError(f"Failed to import CSV: {e}")

    def search_items(self, query):
        """Search for items by name using fuzzy matching.

        Returns items whose names contain the query (case-insensitive)
        or have a similarity ratio >= 0.6.
        """
        if not query or not isinstance(query, str):
            raise InventoryError("Search query must be a non-empty string")

        query_lower = query.lower()
        results = []

        for item in self._items.values():
            name_lower = item.name.lower()
            # Exact substring match
            if query_lower in name_lower:
                results.append((item, 1.0))
                continue
            # Fuzzy match
            ratio = SequenceMatcher(None, query_lower, name_lower).ratio()
            if ratio >= 0.6:
                results.append((item, ratio))

        # Sort by match score descending, then by name
        results.sort(key=lambda x: (-x[1], x[0].name))
        return [item for item, score in results]

    def get_expiring_soon(self, days=7):
        """Return items expiring within the given number of days.

        Args:
            days: number of days to look ahead (default: 7)

        Returns:
            list of InventoryItem sorted by expiry date (soonest first)
        """
        if not isinstance(days, int) or days < 0:
            raise InventoryError("Days must be a non-negative integer")

        cutoff = datetime.now() + timedelta(days=days)
        expiring = []

        for item in self._items.values():
            if item.expiry_date is not None:
                if item.expiry_date <= cutoff and not item.is_expired():
                    expiring.append(item)

        return sorted(expiring, key=lambda x: x.expiry_date)
