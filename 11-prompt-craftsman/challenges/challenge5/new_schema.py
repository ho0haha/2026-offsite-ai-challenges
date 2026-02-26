"""
NEW database schema — the target schema after migration.

Changes from old schema:
- Users: added 'phone' and 'role' columns, renamed 'full_name' to 'display_name'
- Orders: split 'shipping_address' into structured address fields, added 'tracking_number'
- OrderItem: 'product_name' replaced with 'product_id' foreign key
- New table: Products
- New table: Addresses
"""


class User:
    """Users table — updated."""
    __tablename__ = "users"

    id: int              # Primary key, auto-increment
    username: str        # Unique, max 50 chars
    email: str           # Unique, max 100 chars
    password_hash: str   # max 255 chars
    display_name: str    # max 100 chars (renamed from full_name)
    phone: str           # max 20 chars (NEW)
    role: str            # varchar(20): 'customer', 'admin', 'manager' (NEW, default 'customer')
    created_at: str      # datetime
    is_active: bool      # default True


class Product:
    """Products table — NEW."""
    __tablename__ = "products"

    id: int              # Primary key, auto-increment
    name: str            # varchar(200)
    sku: str             # Unique, varchar(50)
    price: float         # decimal(10, 2)
    stock_quantity: int  # default 0
    category: str        # varchar(50)
    created_at: str      # datetime


class Address:
    """Addresses table — NEW."""
    __tablename__ = "addresses"

    id: int              # Primary key, auto-increment
    user_id: int         # Foreign key -> users.id
    street: str          # varchar(200)
    city: str            # varchar(100)
    state: str           # varchar(50)
    zip_code: str        # varchar(20)
    country: str         # varchar(50), default 'US'
    is_default: bool     # default False


class Order:
    """Orders table — updated."""
    __tablename__ = "orders"

    id: int              # Primary key, auto-increment
    user_id: int         # Foreign key -> users.id
    shipping_address_id: int  # Foreign key -> addresses.id (replaces shipping_address text)
    total_amount: float  # decimal(10, 2)
    status: str          # varchar(20): 'pending', 'processing', 'shipped', 'delivered', 'cancelled'
    tracking_number: str  # varchar(100), nullable (NEW)
    created_at: str      # datetime
    updated_at: str      # datetime


class OrderItem:
    """Order items table — updated."""
    __tablename__ = "order_items"

    id: int              # Primary key, auto-increment
    order_id: int        # Foreign key -> orders.id
    product_id: int      # Foreign key -> products.id (replaces product_name)
    quantity: int
    unit_price: float    # decimal(10, 2)
