-- Old schema: single denormalized table
CREATE TABLE IF NOT EXISTS menu_items (
    id INTEGER PRIMARY KEY,
    item_name TEXT,
    item_description TEXT,
    price_str TEXT,
    category_name TEXT,
    is_available TEXT,
    created TEXT
);
