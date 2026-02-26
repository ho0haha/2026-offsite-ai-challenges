"""
Output formatting for the restaurant management system.
Handles display formatting for orders, receipts, reports, etc.
"""

from .models import Order, Customer, MenuItem, OrderStatus
from .utils import format_currency, format_datetime


class OutputFormatter:
    """Formats data for display output."""

    @staticmethod
    def format_receipt(order: Order) -> str:
        """Format an order as a receipt string."""
        lines = []
        lines.append("=" * 40)
        lines.append("        RESTAURANT RECEIPT")
        lines.append("=" * 40)
        lines.append(f"Order #: {order.id}")
        lines.append(f"Date: {format_datetime(order.created_at)}")
        lines.append("-" * 40)

        for item in order.items:
            name = item.menu_item_name
            qty = item.quantity
            subtotal = item.subtotal
            lines.append(f"  {name} x{qty}  {format_currency(subtotal)}")
            if item.special_instructions:
                lines.append(f"    Note: {item.special_instructions}")

        lines.append("-" * 40)
        lines.append(f"  Subtotal:  {format_currency(order.subtotal)}")
        lines.append(f"  Tax:       {format_currency(order.tax)}")
        if order.discount > 0:
            lines.append(f"  Discount: -{format_currency(order.discount)}")
        if order.tip > 0:
            lines.append(f"  Tip:       {format_currency(order.tip)}")
        lines.append("-" * 40)
        lines.append(f"  TOTAL:     {format_currency(order.grand_total)}")
        lines.append("=" * 40)

        if order.is_paid:
            lines.append(f"  Paid via: {order.payment_method.value}")
        else:
            lines.append("  *** UNPAID ***")

        lines.append("")
        lines.append("  Thank you for dining with us!")
        lines.append("=" * 40)

        return "\n".join(lines)

    @staticmethod
    def format_menu_item(item: MenuItem) -> str:
        """Format a menu item for display."""
        status = "Available" if item.is_available else "Unavailable"
        return (
            f"{item.name} - {format_currency(item.price)}\n"
            f"  {item.description}\n"
            f"  Category: {item.category.value} | "
            f"Prep: {item.prep_time_minutes}min | "
            f"Cal: {item.calories} | {status}"
        )

    @staticmethod
    def format_customer_profile(customer: Customer) -> str:
        """Format a customer profile for display."""
        return (
            f"Customer: {customer.name}\n"
            f"  ID: {customer.id}\n"
            f"  Email: {customer.email or 'N/A'}\n"
            f"  Phone: {customer.phone or 'N/A'}\n"
            f"  Total Spent: {format_currency(customer.total_spent)}\n"
            f"  Orders: {customer.order_count}"
        )

    @staticmethod
    def format_order_status(order: Order) -> str:
        """Format an order's status for display."""
        status_emoji = {
            OrderStatus.PENDING: "[PENDING]",
            OrderStatus.CONFIRMED: "[CONFIRMED]",
            OrderStatus.PREPARING: "[PREPARING]",
            OrderStatus.READY: "[READY]",
            OrderStatus.DELIVERED: "[DELIVERED]",
            OrderStatus.CANCELLED: "[CANCELLED]",
        }
        marker = status_emoji.get(order.status, "[UNKNOWN]")
        return f"Order {order.id}: {marker} - {format_currency(order.grand_total)}"

    @staticmethod
    def format_sales_summary(summary: dict) -> str:
        """Format a sales summary report."""
        return (
            f"Sales Summary\n"
            f"{'=' * 30}\n"
            f"Total Revenue: {format_currency(summary['total_revenue'])}\n"
            f"Total Orders: {summary['total_orders']}\n"
            f"Avg Order Value: {format_currency(summary['average_order_value'])}\n"
            f"Cancelled: {summary['cancelled_orders']}"
        )

    # --- Loyalty Summary ---
    # TODO: Implement format_loyalty_summary(customer) method
    #
    # format_loyalty_summary(customer: Customer) -> str
    #   Returns a formatted string:
    #     Loyalty Summary for {name}
    #     Current Balance: {points} points
    #     Total Earned: {earned} points
    #     Total Redeemed: {redeemed} points
