"""
Reporting and analytics service.
Provides business intelligence and summary reports.
"""

from collections import Counter
from typing import Dict, List
from .models import OrderStatus, MenuCategory
from .database import Database
from . import config


class ReportingService:
    """Service for generating restaurant reports and analytics."""

    def __init__(self, db: Database):
        self.db = db

    def daily_sales_summary(self) -> Dict:
        """Generate a summary of all sales."""
        orders = self.db.get_all_orders()
        confirmed_orders = [
            o for o in orders if o.status != OrderStatus.CANCELLED
        ]

        total_revenue = sum(o.grand_total for o in confirmed_orders)
        total_orders = len(confirmed_orders)
        average_order_value = total_revenue / total_orders if total_orders > 0 else 0

        return {
            "total_revenue": round(total_revenue, 2),
            "total_orders": total_orders,
            "average_order_value": round(average_order_value, 2),
            "cancelled_orders": len(orders) - len(confirmed_orders),
        }

    def popular_items_report(self, limit: int = None) -> List[Dict]:
        """Get the most popular menu items by order count."""
        if limit is None:
            limit = config.TOP_ITEMS_COUNT

        item_counts = Counter()
        item_revenue = Counter()

        for order in self.db.get_all_orders():
            if order.status == OrderStatus.CANCELLED:
                continue
            for item in order.items:
                item_counts[item.menu_item_name] += item.quantity
                item_revenue[item.menu_item_name] += item.subtotal

        popular = []
        for item_name, count in item_counts.most_common(limit):
            popular.append({
                "name": item_name,
                "quantity_sold": count,
                "revenue": round(item_revenue[item_name], 2),
            })

        return popular

    def customer_spending_report(self) -> List[Dict]:
        """Report on customer spending habits."""
        customers = self.db.get_all_customers()
        report = []

        for customer in customers:
            orders = self.db.get_orders_by_customer(customer.id)
            active_orders = [
                o for o in orders if o.status != OrderStatus.CANCELLED
            ]

            report.append({
                "customer_id": customer.id,
                "name": customer.name,
                "total_spent": round(customer.total_spent, 2),
                "order_count": customer.order_count,
                "average_order": (
                    round(customer.total_spent / customer.order_count, 2)
                    if customer.order_count > 0
                    else 0
                ),
            })

        return sorted(report, key=lambda x: x["total_spent"], reverse=True)

    def category_breakdown(self) -> Dict[str, Dict]:
        """Break down sales by menu category."""
        category_data = {}

        for category in MenuCategory:
            category_data[category.value] = {
                "items_sold": 0,
                "revenue": 0.0,
            }

        for order in self.db.get_all_orders():
            if order.status == OrderStatus.CANCELLED:
                continue
            for item in order.items:
                menu_item = self.db.get_menu_item(item.menu_item_id)
                if menu_item:
                    cat = menu_item.category.value
                    category_data[cat]["items_sold"] += item.quantity
                    category_data[cat]["revenue"] += item.subtotal

        for cat in category_data:
            category_data[cat]["revenue"] = round(category_data[cat]["revenue"], 2)

        return category_data

    # --- Loyalty Report ---
    # TODO: Implement loyalty_report() method
    #
    # loyalty_report() -> Dict
    #   Returns a dict with:
    #     - total_points_in_circulation: sum of all customers' current balances
    #     - total_points_ever_earned: sum of all customers' lifetime earned
    #     - total_points_ever_redeemed: sum of all customers' lifetime redeemed
    #     - top_earners: list of top 5 customers by lifetime points earned,
    #       each as dict with customer_id, name, points_earned
