"""
Creates the old-schema SQLite database for the migration challenge.
Run this before running tests: python setup_db.py
Do NOT modify this file.
"""

import sqlite3
import random
import os

random.seed(123)

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gauntlet_09.db")

CATEGORIES = ["Appetizers", "Entrees", "Desserts", "Drinks", "Sides", "Specials"]

ITEM_TEMPLATES = [
    "Classic {}", "Grilled {}", "Crispy {}", "Smoked {}", "Fresh {}",
    "Spicy {}", "Honey {}", "Garlic {}", "BBQ {}", "Lemon {}",
]

FOOD_WORDS = [
    "Chicken", "Salmon", "Steak", "Pasta", "Salad", "Soup", "Burger",
    "Tacos", "Wings", "Ribs", "Shrimp", "Lobster", "Pizza", "Wrap",
    "Sandwich", "Nachos", "Fries", "Cake", "Pie", "Brownie",
    "Lemonade", "Coffee", "Tea", "Smoothie", "Milkshake",
]

DESCRIPTIONS = [
    "Served with house-made sauce",
    "A local favorite, made fresh daily",
    "Topped with seasonal vegetables",
    "Slow-cooked for maximum flavor",
    "Paired with a side of your choice",
    "Our chef's signature creation",
    "Made with organic ingredients",
    "A hearty portion for any appetite",
    "Light and refreshing",
    "Rich and indulgent",
]


def create_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "old_schema.sql")
    with open(schema_path) as f:
        c.executescript(f.read())

    rows = []
    for i in range(1, 5001):
        template = random.choice(ITEM_TEMPLATES)
        food = random.choice(FOOD_WORDS)
        name = template.format(food)
        desc = random.choice(DESCRIPTIONS)
        price = round(random.uniform(2.99, 49.99), 2)
        price_str = f"${price:.2f}"
        category = random.choice(CATEGORIES)
        available = random.choice(["yes", "yes", "yes", "no"])
        month = random.randint(1, 12)
        day = random.randint(1, 28)
        hour = random.randint(8, 22)
        minute = random.randint(0, 59)
        created = f"2025-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:00"

        rows.append((i, name, desc, price_str, category, available, created))

    c.executemany(
        "INSERT INTO menu_items VALUES (?, ?, ?, ?, ?, ?, ?)",
        rows,
    )

    conn.commit()
    conn.close()
    print(f"Database created at {DB_PATH}")
    print(f"  menu_items: {len(rows)} rows")


if __name__ == "__main__":
    create_db()
