# Challenge 10: Context is King (350 pts)

## Objective

Add a **loyalty points** feature to an existing restaurant management system. The feature must be implemented across 6 files while keeping all existing functionality working.

## Background

You have a working in-memory restaurant management system with customers, menu items, orders, payment processing, and basic reporting. Your job is to add a loyalty points program.

## What You Need To Do

1. Read `FEATURE_SPEC.md` carefully — it describes exactly what to implement
2. Modify **6 files** in the `restaurant_system/` package:
   - `config.py` — Add loyalty configuration constants
   - `customer_service.py` — Add loyalty point management methods
   - `order_service.py` — Award points after successful orders
   - `payment_service.py` — Support paying with loyalty points
   - `reporting.py` — Add loyalty analytics report
   - `formatters.py` — Add loyalty summary formatting

## Submission

When you're ready, submit your modified files for server-side validation:

```bash
python ctf_helper.py 10 restaurant_system/config.py restaurant_system/customer_service.py restaurant_system/order_service.py restaurant_system/payment_service.py restaurant_system/reporting.py restaurant_system/formatters.py
```

The server runs a test suite (15 tests) against your implementation. All tests must pass.

## Tips

- Read the full feature spec before writing any code
- The existing system is fully functional — don't break it
- Look at existing patterns in the code to stay consistent
- The feature spec tells you exactly what the system should do
