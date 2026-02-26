# Feature Specification: Loyalty Points Program

## Overview

Add a loyalty points system to the restaurant management platform. Customers earn points on every purchase and can redeem them for discounts on future orders.

## Points Earning

- Customers earn **1 point per dollar spent** (rounded down to nearest integer)
- Points are earned on the **actual amount paid** (after any discounts)
- A $0.00 order earns 0 points
- Points are awarded automatically after a successful order

## Points Redemption

- **100 points = $5.00 discount**
- Redemption rate: each point is worth $0.05
- Customers can do **partial redemptions** (e.g., redeem 50 points for $2.50)
- Customers **cannot redeem more points than their current balance**
- After redemption with points, the customer still earns loyalty points on the remaining amount paid (not the discount portion)

## Data Model

The `Customer` model already has fields that can be extended. Track:
- `loyalty_points` — current balance (integer, starts at 0)
- `loyalty_points_earned` — lifetime total earned (integer, starts at 0)
- `loyalty_points_redeemed` — lifetime total redeemed (integer, starts at 0)

## Required Changes

### config.py
Add two constants:
- `LOYALTY_POINTS_PER_DOLLAR = 1` — points earned per dollar spent
- `LOYALTY_REDEMPTION_RATE = 0.05` — dollar value per point ($0.05/point, so 100 pts = $5)

### customer_service.py
Add three methods to `CustomerService`:
- `get_loyalty_balance(customer_id: str) -> int` — returns current points balance
- `add_loyalty_points(customer_id: str, points: int) -> int` — adds points, updates earned history, returns new balance
- `redeem_loyalty_points(customer_id: str, points: int) -> float` — redeems points for discount amount, updates redeemed history, returns dollar discount. Raises ValueError if insufficient balance.

### order_service.py
Modify the `place_order` method:
- After a successful order, calculate loyalty points earned (1 per dollar of amount paid)
- Call `customer_service.add_loyalty_points()` to award the points
- Store the points earned on the order object (add `loyalty_points_earned` field to orders)

### payment_service.py
Add support for loyalty point payments:
- Add method `apply_loyalty_discount(customer_id: str, order_total: float, points_to_redeem: int) -> dict`
- Returns dict with keys: `discount_amount`, `final_total`, `points_redeemed`
- The discount cannot exceed the order total
- Must validate customer has enough points

### reporting.py
Add a `loyalty_report()` method to `ReportingService`:
- Returns a dict with:
  - `total_points_in_circulation` — sum of all customers' current balances
  - `total_points_ever_earned` — sum of all customers' lifetime earned
  - `total_points_ever_redeemed` — sum of all customers' lifetime redeemed
  - `top_earners` — list of top 5 customers by lifetime points earned, each as dict with `customer_id`, `name`, `points_earned`

### formatters.py
Add a `format_loyalty_summary(customer)` method to `OutputFormatter`:
- Returns a formatted string with customer name, current balance, lifetime earned, and lifetime redeemed
- Format:
  ```
  Loyalty Summary for {name}
  Current Balance: {points} points
  Total Earned: {earned} points
  Total Redeemed: {redeemed} points
  ```

## Testing

Run: `python -m pytest tests/test_loyalty.py -v`

All 15 tests must pass for the challenge to be complete.
