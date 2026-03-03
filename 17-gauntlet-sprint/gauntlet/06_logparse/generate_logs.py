"""
Generates POS log data and expected output for the log parsing challenge.
Run this before running tests: python generate_logs.py
Do NOT modify this file.
"""

import random
import os
from collections import defaultdict
from datetime import datetime, timedelta

random.seed(42)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_PATH = os.path.join(BASE_DIR, "pos_logs.txt")
EXPECTED_PATH = os.path.join(BASE_DIR, "expected_output.txt")

MENU_ITEMS = [
    ("Burger", 12.99), ("Fries", 4.99), ("Salad", 9.99),
    ("Pizza", 14.99), ("Pasta", 13.49), ("Soup", 6.99),
    ("Steak", 24.99), ("Salmon", 19.99), ("Tacos", 10.99),
    ("Wings", 11.49), ("Sandwich", 8.99), ("Nachos", 7.99),
    ("Wrap", 9.49), ("Ribs", 18.99), ("Chicken", 15.49),
    ("Sushi", 16.99), ("Ramen", 12.49), ("Curry", 13.99),
    ("Burrito", 10.49), ("Quesadilla", 8.49),
]

PAYMENT_METHODS = ["CARD", "CARD", "CARD", "CASH", "MOBILE"]


def generate():
    lines = []
    hourly_revenue = defaultdict(float)
    item_quantities = defaultdict(int)
    ticket_times = []

    base_date = datetime(2025, 6, 15, 9, 0, 0)
    order_id = 1000
    order_start_times = {}

    # Generate ~2000 orders spread across 9am-11pm
    for _ in range(2000):
        hour = random.choices(
            range(9, 23),
            weights=[2, 3, 5, 8, 8, 5, 3, 4, 6, 8, 8, 5, 3, 2],
            k=1
        )[0]
        minute = random.randint(0, 59)
        second = random.randint(0, 59)
        order_time = base_date.replace(hour=hour, minute=minute, second=second)

        order_id += 1
        num_items = random.randint(1, 6)
        items_list = random.choices(MENU_ITEMS, k=num_items)
        total = sum(price * random.randint(1, 3) for _, price in items_list)
        total = round(total, 2)

        ts = order_time.strftime("%Y-%m-%d %H:%M:%S")
        lines.append(
            f"[{ts}] ORDER_PLACED | order_id={order_id} | items={num_items} | total={total:.2f}"
        )
        order_start_times[order_id] = order_time

        # Item sold events
        for item_name, price in items_list:
            qty = random.randint(1, 3)
            item_quantities[item_name] += qty
            item_ts = (order_time + timedelta(seconds=random.randint(1, 30))).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            lines.append(
                f"[{item_ts}] ITEM_SOLD | item_name={item_name} | quantity={qty} | "
                f"price={price:.2f} | order_id={order_id}"
            )

        # Order completed + payment
        duration = random.randint(120, 1800)  # 2-30 minutes
        complete_time = order_time + timedelta(seconds=duration)
        complete_ts = complete_time.strftime("%Y-%m-%d %H:%M:%S")

        lines.append(
            f"[{complete_ts}] ORDER_COMPLETED | order_id={order_id} | duration_secs={duration}"
        )

        payment_method = random.choice(PAYMENT_METHODS)
        lines.append(
            f"[{complete_ts}] PAYMENT | order_id={order_id} | method={payment_method} | "
            f"amount={total:.2f}"
        )

        hour_key = f"{hour:02d}:00"
        hourly_revenue[hour_key] += total
        ticket_times.append(duration)

    # Sort lines by timestamp
    lines.sort(key=lambda l: l[1:20])

    with open(LOG_PATH, "w") as f:
        f.write("\n".join(lines) + "\n")

    # Generate expected output
    report_lines = []
    report_lines.append("=== HOURLY REVENUE ===")
    for hour in sorted(hourly_revenue.keys()):
        rev = hourly_revenue[hour]
        report_lines.append(f"{hour}  ${rev:>12,.2f}")
    total_rev = sum(hourly_revenue.values())
    report_lines.append(f"TOTAL  ${total_rev:>12,.2f}")
    report_lines.append("")

    report_lines.append("=== TOP 10 ITEMS ===")
    top_items = sorted(item_quantities.items(), key=lambda x: (-x[1], x[0]))[:10]
    for rank, (name, qty) in enumerate(top_items, 1):
        report_lines.append(f"{rank:>2}. {name:<20s} {qty:>6d}")
    report_lines.append("")

    report_lines.append("=== AVERAGE TICKET TIME ===")
    avg_time = sum(ticket_times) / len(ticket_times)
    avg_minutes = int(avg_time // 60)
    avg_seconds = int(avg_time % 60)
    report_lines.append(f"{avg_minutes}m {avg_seconds}s")

    with open(EXPECTED_PATH, "w") as f:
        f.write("\n".join(report_lines) + "\n")

    print(f"Generated {len(lines)} log lines in {LOG_PATH}")
    print(f"Expected output in {EXPECTED_PATH}")


if __name__ == "__main__":
    generate()
