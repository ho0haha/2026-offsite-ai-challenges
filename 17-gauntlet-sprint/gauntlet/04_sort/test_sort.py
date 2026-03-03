"""
Tests for the custom sort challenge.
Do NOT modify this file.
"""

import json
import os
import pytest
from solution import custom_sort

DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.json")
CATEGORY_PRIORITY = {"appetizer": 1, "entree": 2, "dessert": 3, "drink": 4}


@pytest.fixture
def items():
    with open(DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


def reference_sort(items):
    """Reference implementation of the correct sort order."""
    return sorted(
        items,
        key=lambda x: (
            CATEGORY_PRIORITY[x["category"]],
            -x["price"],
            x["name"].lower(),
            x["id"],
        ),
    )


def test_sort_returns_all_items(items):
    """Sort must return all 100 items."""
    result = custom_sort(items)
    assert len(result) == 100, f"Expected 100 items, got {len(result)}"


def test_sort_correct_order(items):
    """Sort order must match the 4-criteria specification."""
    result = custom_sort(items)
    expected = reference_sort(items)

    for i, (r, e) in enumerate(zip(result, expected)):
        assert r["id"] == e["id"], (
            f"Position {i}: expected id={e['id']} ({e['name']}, {e['category']}, "
            f"${e['price']}), got id={r['id']} ({r['name']}, {r['category']}, "
            f"${r['price']})"
        )


def test_category_grouping(items):
    """Items must be grouped by category in priority order."""
    result = custom_sort(items)
    categories = [r["category"] for r in result]

    seen = set()
    order = []
    for cat in categories:
        if cat not in seen:
            seen.add(cat)
            order.append(cat)

    assert order == ["appetizer", "entree", "dessert", "drink"], (
        f"Category order: {order}"
    )


def test_price_descending_within_category(items):
    """Within each category, prices should be descending."""
    result = custom_sort(items)

    by_category = {}
    for item in result:
        cat = item["category"]
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(item)

    for cat, cat_items in by_category.items():
        for i in range(len(cat_items) - 1):
            a, b = cat_items[i], cat_items[i + 1]
            assert a["price"] >= b["price"] or (
                a["price"] == b["price"]
            ), (
                f"In {cat}: {a['name']} (${a['price']}) should come before "
                f"{b['name']} (${b['price']})"
            )


def test_unicode_names_handled(items):
    """Unicode names must be handled correctly."""
    result = custom_sort(items)
    names = [r["name"] for r in result]

    unicode_names = ["Épinards Gratinés", "Crème Brûlée", "Tōfu Stir Fry",
                     "Crêpes Salées", "Günstiges Curry", "Gâteau Opéra",
                     "Éclair", "Glühwein", "Café au Lait", "Virgin Piña Colada"]

    for uname in unicode_names:
        assert uname in names, f"Unicode name {uname!r} missing from results"


def test_does_not_modify_original(items):
    """custom_sort must not modify the original list."""
    original_ids = [item["id"] for item in items]
    custom_sort(items)
    after_ids = [item["id"] for item in items]
    assert original_ids == after_ids, "custom_sort must not modify the original list"
