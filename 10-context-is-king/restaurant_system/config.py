"""
Configuration constants for the restaurant management system.
"""

# --- Tax and Payment ---
TAX_RATE = 0.08  # 8% sales tax
DEFAULT_TIP_PERCENTAGE = 0.18  # 18% default tip
MIN_ORDER_AMOUNT = 5.00  # Minimum order total
MAX_ORDER_ITEMS = 50  # Maximum items per order

# --- Business Hours ---
OPENING_HOUR = 8  # 8 AM
CLOSING_HOUR = 22  # 10 PM

# --- Reservations ---
MAX_PARTY_SIZE = 20
RESERVATION_DURATION_MINUTES = 90
MAX_RESERVATIONS_PER_SLOT = 10

# --- Menu ---
MAX_MENU_ITEM_PRICE = 500.00
MIN_MENU_ITEM_PRICE = 0.50

# --- Reporting ---
TOP_ITEMS_COUNT = 10
REPORT_DATE_FORMAT = "%Y-%m-%d"

# --- Loyalty Program ---
# TODO: Add loyalty program constants
# LOYALTY_POINTS_PER_DOLLAR — points earned per dollar spent
# LOYALTY_REDEMPTION_RATE — dollar value of each point
