"""
Database Migration Challenge - Solution Stub

Implement migrate(db_path) that transforms the database from old_schema to new_schema.
"""

import sqlite3


def migrate(db_path: str):
    """
    Migrate the database at db_path from the old schema to the new schema.

    Steps:
    1. Read all data from menu_items (old schema).
    2. Create the categories and items tables (new schema).
    3. Extract unique category_name values into the categories table.
    4. Migrate each menu_item into the items table with transformations:
       - item_name -> name
       - item_description -> description
       - price_str ("$12.99") -> price_cents (1299)
       - category_name -> category_id (FK to categories)
       - is_available ("yes"/"no") -> is_available (1/0)
       - created -> created_at
       - Compute price_display from price_cents (e.g., 1299 -> "$12.99")
    5. Drop the old menu_items table.

    Args:
        db_path: Path to the SQLite database file.

    TODO: Implement this function.
    """
    pass
