# Challenge 10: Context is King (350 pts)

## Tool: Cursor

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
3. Run the test suite to verify your implementation

## Running Tests

```bash
pip install -r requirements.txt
python -m pytest tests/test_loyalty.py -v
```

## Success Criteria

All 15 tests in `tests/test_loyalty.py` must pass.

## Flag

When all tests pass, the flag will be printed:
```
FLAG{context_is_king_l0yalty_p0ints}
```

## Tips

- Read the full feature spec before writing any code
- The existing system is fully functional — don't break it
- Look at existing patterns in the code to stay consistent
- The tests tell you exactly what the system should do
