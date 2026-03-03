# Challenge 13: The Onion Bug

**Tier 4 | 600 Points**

## Background

"The Golden Fork" restaurant recently upgraded their order processing system, but customers are reporting issues left and right. The development team left in a hurry, and now it's your job to fix the system.

The catch? This codebase has **7 layered bugs**. Each fix changes the execution flow and reveals the next bug hiding underneath. Like peeling an onion, you must work through them one layer at a time.

## Getting Started

```bash
# Run the test suite
python run_tests.py
```

The test runner will execute 7 groups of tests sequentially. Each group only runs if the previous group passes. Your goal is to make all 7 groups pass.

## Project Structure

```
order_system/
  __init__.py          # Package exports
  models.py            # Data classes (MenuItem, Order, OrderResult, etc.)
  processor.py         # Main order processing pipeline
  pricing.py           # Discount tiers and tax calculation
  validators.py        # Order validation
  inventory.py         # Stock management
test_onion.py          # 7 groups of tests (one per layer)
run_tests.py           # Sequential test runner
```

## Rules

1. Fix bugs in the `order_system/` source files only
2. Do **not** modify `test_onion.py` or `run_tests.py`
3. Each layer reveals the next -- you must fix them in order
4. The flag is printed when all 7 test groups pass

## Hints

- Read the test names and error messages carefully
- Each bug is in a specific file -- the test group name hints at where
- Some bugs only appear because fixing an earlier bug changes which code paths execute
- The comments in the source code may contain useful context

## Requirements

- Python 3.10+
- No external dependencies (standard library only)

Good luck peeling the onion!
