"""
Tests for the database migration challenge.
Do NOT modify this file.
"""

import sqlite3
import os
import shutil
import pytest
from solution import migrate
from setup_db import create_db, DB_PATH

TEST_DB = DB_PATH + ".test"


@pytest.fixture(autouse=True)
def setup_test_db():
    """Create a fresh copy of the database for each test."""
    if not os.path.exists(DB_PATH):
        create_db()
    shutil.copy2(DB_PATH, TEST_DB)
    yield
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)


def get_old_data():
    """Read all data from the original DB before migration."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM menu_items ORDER BY id").fetchall()
    conn.close()
    return rows


def test_migration_creates_new_tables():
    """Migration must create categories and items tables."""
    migrate(TEST_DB)
    conn = sqlite3.connect(TEST_DB)
    tables = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()}
    conn.close()
    assert "categories" in tables, "categories table not found"
    assert "items" in tables, "items table not found"


def test_old_table_dropped():
    """menu_items table must be dropped after migration."""
    migrate(TEST_DB)
    conn = sqlite3.connect(TEST_DB)
    tables = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()}
    conn.close()
    assert "menu_items" not in tables, "menu_items table should be dropped"


def test_all_rows_migrated():
    """All 5000 rows must be migrated."""
    old_rows = get_old_data()
    migrate(TEST_DB)
    conn = sqlite3.connect(TEST_DB)
    count = conn.execute("SELECT COUNT(*) FROM items").fetchone()[0]
    conn.close()
    assert count == len(old_rows), f"Expected {len(old_rows)} items, got {count}"


def test_categories_extracted():
    """Unique categories must be in the categories table."""
    old_rows = get_old_data()
    expected_cats = sorted(set(r["category_name"] for r in old_rows))

    migrate(TEST_DB)
    conn = sqlite3.connect(TEST_DB)
    actual_cats = sorted(
        r[0] for r in conn.execute("SELECT name FROM categories ORDER BY name").fetchall()
    )
    conn.close()
    assert actual_cats == expected_cats


def test_price_conversion():
    """price_str must be converted to price_cents correctly."""
    old_rows = get_old_data()
    migrate(TEST_DB)

    conn = sqlite3.connect(TEST_DB)
    conn.row_factory = sqlite3.Row

    for old in old_rows[:100]:  # Check first 100
        new = conn.execute("SELECT * FROM items WHERE id = ?", (old["id"],)).fetchone()
        assert new is not None, f"Item {old['id']} not found after migration"

        price_str = old["price_str"]  # e.g., "$12.99"
        expected_cents = round(float(price_str.replace("$", "")) * 100)
        assert new["price_cents"] == expected_cents, (
            f"Item {old['id']}: expected {expected_cents} cents, got {new['price_cents']}"
        )

    conn.close()


def test_boolean_conversion():
    """is_available must be converted from yes/no to 1/0."""
    old_rows = get_old_data()
    migrate(TEST_DB)

    conn = sqlite3.connect(TEST_DB)
    conn.row_factory = sqlite3.Row

    for old in old_rows[:100]:
        new = conn.execute("SELECT * FROM items WHERE id = ?", (old["id"],)).fetchone()
        expected = 1 if old["is_available"] == "yes" else 0
        assert new["is_available"] == expected, (
            f"Item {old['id']}: expected is_available={expected}, got {new['is_available']}"
        )

    conn.close()


def test_column_renames():
    """Columns must be renamed correctly."""
    old_rows = get_old_data()
    migrate(TEST_DB)

    conn = sqlite3.connect(TEST_DB)
    conn.row_factory = sqlite3.Row

    for old in old_rows[:50]:
        new = conn.execute("SELECT * FROM items WHERE id = ?", (old["id"],)).fetchone()
        assert new["name"] == old["item_name"], f"Item {old['id']}: name mismatch"
        assert new["description"] == old["item_description"], f"Item {old['id']}: description mismatch"
        assert new["created_at"] == old["created"], f"Item {old['id']}: created_at mismatch"

    conn.close()


def test_category_foreign_key():
    """category_id must correctly reference the categories table."""
    old_rows = get_old_data()
    migrate(TEST_DB)

    conn = sqlite3.connect(TEST_DB)
    conn.row_factory = sqlite3.Row

    cat_map = {
        r["name"]: r["id"]
        for r in conn.execute("SELECT * FROM categories").fetchall()
    }

    for old in old_rows[:100]:
        new = conn.execute("SELECT * FROM items WHERE id = ?", (old["id"],)).fetchone()
        expected_cat_id = cat_map[old["category_name"]]
        assert new["category_id"] == expected_cat_id, (
            f"Item {old['id']}: expected category_id={expected_cat_id}, got {new['category_id']}"
        )

    conn.close()


def test_price_display_computed():
    """price_display must be computed from price_cents."""
    old_rows = get_old_data()
    migrate(TEST_DB)

    conn = sqlite3.connect(TEST_DB)
    conn.row_factory = sqlite3.Row

    for old in old_rows[:100]:
        new = conn.execute("SELECT * FROM items WHERE id = ?", (old["id"],)).fetchone()
        expected_display = old["price_str"]  # Should match original
        assert new["price_display"] == expected_display, (
            f"Item {old['id']}: expected price_display={expected_display}, got {new['price_display']}"
        )

    conn.close()
