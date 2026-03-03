-- New schema: normalized with proper types

CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    price_cents INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    is_available INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    price_display TEXT NOT NULL,
    FOREIGN KEY (category_id) REFERENCES categories(id)
);
