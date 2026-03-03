"""
Creates the SQLite database for the SQL optimization challenge.
Run this before running tests: python setup_db.py
Do NOT modify this file.
"""

import sqlite3
import random
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gauntlet_02.db")

CATEGORIES = ["appetizer", "entree", "dessert", "drink", "side"]
PRODUCT_NAMES = [
    "Bruschetta", "Caesar Salad", "Onion Rings", "Spring Rolls", "Soup",
    "Grilled Salmon", "Ribeye Steak", "Chicken Parmesan", "Pasta Primavera",
    "Fish Tacos", "Veggie Burger", "Lamb Chops", "Lobster Tail", "Pad Thai",
    "Pizza Margherita", "Chocolate Cake", "Tiramisu", "Cheesecake",
    "Ice Cream Sundae", "Creme Brulee", "Lemonade", "Iced Tea", "Coffee",
    "Espresso", "Milkshake", "Fries", "Coleslaw", "Mac and Cheese",
    "Garlic Bread", "Rice Pilaf",
]


def create_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            active INTEGER NOT NULL DEFAULT 1
        )
    """)

    c.execute("""
        CREATE TABLE orders (
            id INTEGER PRIMARY KEY,
            customer_name TEXT NOT NULL,
            order_date TEXT NOT NULL,
            status TEXT NOT NULL,
            total REAL NOT NULL DEFAULT 0
        )
    """)

    c.execute("""
        CREATE TABLE order_items (
            id INTEGER PRIMARY KEY,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """)

    # Insert 30 products
    products = []
    for i, name in enumerate(PRODUCT_NAMES, 1):
        cat = CATEGORIES[i % len(CATEGORIES)]
        price = round(random.uniform(3.99, 49.99), 2)
        active = 1 if random.random() > 0.1 else 0
        products.append((i, name, cat, price, active))
    c.executemany("INSERT INTO products VALUES (?, ?, ?, ?, ?)", products)

    # Insert 10000 orders
    statuses = ["completed", "completed", "completed", "pending", "cancelled"]
    customers = [f"Customer_{i}" for i in range(500)]
    orders = []
    for oid in range(1, 10001):
        cust = random.choice(customers)
        month = random.randint(1, 12)
        day = random.randint(1, 28)
        date = f"2025-{month:02d}-{day:02d}"
        status = random.choice(statuses)
        orders.append((oid, cust, date, status, 0))
    c.executemany("INSERT INTO orders VALUES (?, ?, ?, ?, ?)", orders)

    # Insert ~50000 order items (avg 5 per order)
    items = []
    item_id = 1
    for oid in range(1, 10001):
        num_items = random.randint(1, 10)
        order_total = 0
        for _ in range(num_items):
            prod = random.choice(products)
            qty = random.randint(1, 5)
            price = prod[3]
            items.append((item_id, oid, prod[0], qty, price))
            order_total += qty * price
            item_id += 1
        c.execute("UPDATE orders SET total = ? WHERE id = ?",
                  (round(order_total, 2), oid))
    c.executemany("INSERT INTO order_items VALUES (?, ?, ?, ?, ?)", items)

    conn.commit()
    conn.close()
    print(f"Database created at {DB_PATH}")
    print(f"  products: {len(products)} rows")
    print(f"  orders: {len(orders)} rows")
    print(f"  order_items: {len(items)} rows")


if __name__ == "__main__":
    create_db()
