"""
Custom Menu Sort Challenge - Solution Stub

Implement custom_sort(items) that sorts menu items by:
1. Category priority (appetizer=1, entree=2, dessert=3, drink=4) ascending
2. Price descending
3. Name alphabetical (case-insensitive)
4. ID ascending
"""

from typing import List, Dict


def custom_sort(items: List[Dict]) -> List[Dict]:
    """
    Sort menu items by the multi-criteria sort order.

    Each item is a dict with keys: id, name, category, price
    Categories: "appetizer", "entree", "dessert", "drink"

    Returns:
        List[Dict]: Sorted list of items.

    TODO: Implement the sorting logic.
    """
    return items
