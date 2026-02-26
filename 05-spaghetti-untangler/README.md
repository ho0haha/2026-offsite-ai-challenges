# Challenge 5: Spaghetti Untangler (250 pts)

**Tool:** Cursor

## Objective

You've inherited `order_processor.py` from a developer who believed in "one function to rule them all." The entire restaurant order processing pipeline lives inside a single ~400-line function full of magic numbers, deep nesting, duplicated logic, and single-letter variable names.

Your job: **refactor it into clean, modular code** without breaking any behavior.

## Rules

1. All existing **behavior tests** must continue to pass (these test correct calculations)
2. All **structural tests** must also pass after your refactoring:
   - No single function exceeds 30 lines
   - The module contains at least 6 functions
   - Magic numbers are replaced with named module-level constants
3. Do NOT change `test_processor.py`
4. The function signature `process_order(order_data: dict) -> dict` must still exist and work

## Getting Started

```bash
pip install -r requirements.txt

# Run tests (behavior tests pass, structural tests fail)
python -m pytest test_processor.py -v

# Your goal: make ALL tests pass
```

## Tips

- Start by understanding what the function does end-to-end
- Identify the distinct responsibilities (validation, pricing, tax, discounts, etc.)
- Extract helper functions one at a time, running tests after each change
- Replace magic numbers with well-named constants
- The behavior tests are your safety net - if they pass, you haven't broken anything

## Flag

When all tests pass: `FLAG{spaghetti_untangled_cl34n_c0de}`
