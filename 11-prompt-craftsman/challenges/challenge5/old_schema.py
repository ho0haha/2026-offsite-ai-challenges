"""
OLD database schema — the current production schema.
"""


class User:
    """Users table."""
    __tablename__ = "users"

    id: int              # Primary key, auto-increment
    username: str        # Unique, max 50 chars
    email: str           # Unique, max 100 chars
    password_hash: str   # max 255 chars
    full_name: str       # max 100 chars
    created_at: str      # datetime
    is_active: bool      # default True


class Order:
    """Orders table."""
    __tablename__ = "orders"

    id: int              # Primary key, auto-increment
    user_id: int         # Foreign key -> users.id
    total_amount: float  # decimal(10, 2)
    status: str          # varchar(20): 'pending', 'shipped', 'delivered'
    shipping_address: str  # text — full address as a single string
    created_at: str      # datetime
    updated_at: str      # datetime


class OrderItem:
    """Order items table."""
    __tablename__ = "order_items"

    id: int              # Primary key, auto-increment
    order_id: int        # Foreign key -> orders.id
    product_name: str    # varchar(200) — stored as plain text
    quantity: int
    unit_price: float    # decimal(10, 2)
