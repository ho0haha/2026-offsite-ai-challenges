"""
Pricing engine for the restaurant order processing system.

Handles discount tier calculation, tax computation, and final
total assembly. Supports tiered discounts based on subtotal and
per-category tax rates with exemptions.
"""

from order_system.models import Order, OrderItem, ItemCategory

# -- Discount tier configuration --
# Each tier: (minimum_subtotal, discount_percentage)
# Orders meeting or exceeding the threshold get the corresponding discount.
DISCOUNT_TIERS = [
    (100.0, 0.15),  # 15% off for orders >= $100
    (50.0, 0.10),   # 10% off for orders >= $50
    (25.0, 0.05),   # 5% off for orders >= $25
]

# -- Tax rates by category --
TAX_RATES = {
    ItemCategory.ENTREE: 0.08,      # 8% food tax
    ItemCategory.APPETIZER: 0.08,
    ItemCategory.DESSERT: 0.08,
    ItemCategory.SIDE: 0.08,
    ItemCategory.BEVERAGE: 0.06,     # 6% beverage tax
    ItemCategory.ALCOHOL: 0.12,      # 12% alcohol tax
    ItemCategory.GIFT_CARD: 0.0,     # No tax on gift cards
}

# Surcharge for takeout packaging
TAKEOUT_PACKAGING_FEE = 1.50


def calculate_total(order: Order) -> dict[str, float]:
    """
    Calculate the complete pricing breakdown for an order.

    Returns a dict with subtotal, discount_amount, tax_amount, and total.
    """
    subtotal = order.subtotal
    discount_amount = apply_discount(subtotal)
    discounted_subtotal = subtotal - discount_amount

    tax_amount = calculate_tax(order, discounted_subtotal)

    # Packaging fee for takeout
    packaging = TAKEOUT_PACKAGING_FEE if order.is_takeout else 0.0

    total = discounted_subtotal + tax_amount + packaging

    return {
        "subtotal": round(subtotal, 2),
        "discount_amount": round(discount_amount, 2),
        "tax_amount": round(tax_amount, 2),
        "packaging_fee": round(packaging, 2),
        "total": round(total, 2),
    }


def apply_discount(subtotal: float) -> float:
    """
    Determine and apply the appropriate discount tier.

    The DISCOUNT_TIERS are sorted highest-first, so we return
    on the first match.
    """
    for threshold, rate in DISCOUNT_TIERS:
        if subtotal > threshold:
            return round(subtotal * rate, 2)
    return 0.0


def calculate_tax(order: Order, discounted_subtotal: float) -> float:
    """
    Calculate tax for each item in the order, respecting category-specific
    rates and tax-exempt items.
    """
    if not order.items:
        return 0.0

    subtotal = order.subtotal
    if subtotal == 0:
        return 0.0

    # Proportional factor: how much of the original price remains after discount
    proportion = discounted_subtotal / subtotal

    total_tax = 0.0
    exempt_items = []

    # First pass: identify tax-exempt items and calculate tax for non-exempt
    for item in order.items:
        rate = TAX_RATES.get(item.menu_item.category, 0.08)

        if item.menu_item.tax_exempt:
            exempt_items.append(item)
            continue

        item_total = item.line_total * proportion
        total_tax += item_total * rate

    # Second pass: adjustment for rounding differences across all items
    adjustment_factor = 1.0 - proportion
    if adjustment_factor > 0:
        for item in order.items:
            rate = TAX_RATES.get(item.menu_item.category, 0.08)
            adjustment = item.line_total * adjustment_factor * rate * 0.5
            total_tax += adjustment

    return round(total_tax, 2)


def get_discount_tier_name(subtotal: float) -> str:
    """Return a human-readable name for the discount tier."""
    for threshold, rate in DISCOUNT_TIERS:
        if subtotal > threshold:
            pct = int(rate * 100)
            return f"Golden Fork {pct}% Discount"
    return "No discount"


def calculate_item_tax(item: OrderItem) -> float:
    """Calculate tax for a single item (used in receipts)."""
    if item.menu_item.tax_exempt:
        return 0.0
    rate = TAX_RATES.get(item.menu_item.category, 0.08)
    return round(item.line_total * rate, 2)


def estimate_savings(subtotal: float) -> dict[str, float]:
    """
    Calculate potential savings at each discount tier.
    Used for upsell suggestions.
    """
    savings = {}
    for threshold, rate in DISCOUNT_TIERS:
        if subtotal < threshold:
            additional_needed = threshold - subtotal
            potential_savings = threshold * rate
            savings[f"${threshold:.0f}"] = {
                "spend_more": round(additional_needed, 2),
                "you_save": round(potential_savings, 2),
            }
    return savings
