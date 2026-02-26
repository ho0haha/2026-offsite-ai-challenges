"""
Challenge 1: Hello AI — Implement these 3 functions using your AI coding tool.
Each function has a detailed docstring specifying the expected behavior.
"""


def parse_order(order_string: str) -> dict:
    """Parse a restaurant order string into a structured dictionary.

    The order string format is: "QTYxITEM@PRICE"
    Multiple items are separated by commas.

    Args:
        order_string: A string like "2xBurger@5.99,1xFries@2.49,3xSoda@1.99"

    Returns:
        A dictionary with the following keys:
        - "items": list of dicts, each with "name" (str), "quantity" (int), "price" (float)
        - "total": float, the sum of (quantity * price) for all items, rounded to 2 decimal places

    Examples:
        >>> parse_order("2xBurger@5.99,1xFries@2.49")
        {'items': [{'name': 'Burger', 'quantity': 2, 'price': 5.99}, {'name': 'Fries', 'quantity': 1, 'price': 2.49}], 'total': 14.47}

        >>> parse_order("1xSoda@1.99")
        {'items': [{'name': 'Soda', 'quantity': 1, 'price': 1.99}], 'total': 1.99}

    Edge cases:
        - Empty string returns {"items": [], "total": 0.0}
        - Prices and totals should always be rounded to 2 decimal places
    """
    pass


def format_receipt(order: dict, tax_rate: float = 0.08) -> str:
    """Format a parsed order (from parse_order) into a human-readable receipt string.

    Args:
        order: A dictionary as returned by parse_order, with "items" and "total" keys.
        tax_rate: Tax rate as a decimal (default 0.08 = 8%).

    Returns:
        A multi-line string formatted as a receipt. The format is:
        ---
        RECEIPT
        ---
        Burger     x2    $11.98
        Fries      x1     $2.49
        ---
        Subtotal:        $14.47
        Tax (8.0%):       $1.16
        Total:           $15.63
        ---

        Formatting rules:
        - Item name left-aligned, padded to 10 chars
        - Quantity right after name as "x{qty}", padded to 6 chars
        - Price right-aligned to fill remaining space up to a total width of 30 chars per line
        - Subtotal, Tax, and Total labels are left-aligned, amounts right-aligned to column 30
        - Tax percentage should show one decimal place (e.g., "8.0%")
        - All dollar amounts use 2 decimal places
        - Lines of "---" are exactly 30 dashes

    Edge cases:
        - If items list is empty, still produce the receipt structure with $0.00 amounts
    """
    pass


def analyze_sales(orders: list[dict]) -> dict:
    """Analyze a list of parsed orders and return sales statistics.

    Args:
        orders: A list of dictionaries, each in the format returned by parse_order.

    Returns:
        A dictionary with the following keys:
        - "total_revenue": float, sum of all order totals, rounded to 2 decimal places
        - "average_order": float, mean order total, rounded to 2 decimal places
        - "most_popular_item": str, the item name with the highest total quantity across all orders
        - "item_breakdown": dict mapping item name (str) to total quantity (int) ordered across all orders

    Examples:
        >>> orders = [
        ...     parse_order("2xBurger@5.99,1xFries@2.49"),
        ...     parse_order("1xBurger@5.99,2xSoda@1.99")
        ... ]
        >>> result = analyze_sales(orders)
        >>> result["total_revenue"]
        24.44
        >>> result["most_popular_item"]
        'Burger'

    Edge cases:
        - Empty list returns {"total_revenue": 0.0, "average_order": 0.0, "most_popular_item": "", "item_breakdown": {}}
        - If there's a tie for most popular item, return the one that appears first alphabetically
    """
    pass
