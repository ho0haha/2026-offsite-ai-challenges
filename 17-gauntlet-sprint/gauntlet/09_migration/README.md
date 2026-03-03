# Challenge 09: Database Schema Migration

## Problem

An application's SQLite database needs to be migrated from an old schema to a new one. The migration involves column renames, type changes, splitting a table, and backfilling computed columns.

## Old Schema (see `old_schema.sql`)

```sql
-- Single table with all data
CREATE TABLE menu_items (
    id INTEGER PRIMARY KEY,
    item_name TEXT,
    item_description TEXT,
    price_str TEXT,          -- e.g., "$12.99"
    category_name TEXT,      -- e.g., "Appetizers"
    is_available TEXT,       -- "yes" or "no"
    created TEXT             -- e.g., "2025-01-15 10:30:00"
);
```

## New Schema (see `new_schema.sql`)

```sql
CREATE TABLE categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE items (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,              -- renamed from item_name
    description TEXT,                -- renamed from item_description
    price_cents INTEGER NOT NULL,    -- type change: "$12.99" -> 1299
    category_id INTEGER NOT NULL,    -- FK to categories
    is_available INTEGER NOT NULL,   -- type change: "yes"/"no" -> 1/0
    created_at TEXT NOT NULL,        -- renamed from created
    price_display TEXT NOT NULL,     -- computed: "$12.99" format
    FOREIGN KEY (category_id) REFERENCES categories(id)
);
```

## Task

Edit `solution.py` to implement `migrate(db_path)` that:
1. Reads all data from the old schema.
2. Creates the new schema tables.
3. Extracts unique categories into the `categories` table.
4. Migrates all items with proper transformations.
5. Drops the old `menu_items` table.

## Setup

```bash
python setup_db.py   # Creates gauntlet_09.db with old schema + 5000 rows
python -m pytest test_migration.py -v
```

## Files

- `old_schema.sql` — Old schema definition. Do NOT modify.
- `new_schema.sql` — New schema definition. Do NOT modify.
- `setup_db.py` — Creates test database. Do NOT modify.
- `solution.py` — Your solution. Edit this file.
- `test_migration.py` — Tests. Do NOT modify.
