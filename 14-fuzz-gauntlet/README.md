# Challenge 14: The Fuzz Gauntlet

**Tier 5 | 600 Points**

## Objective

Implement 4 functions that must survive **property-based testing** with [Hypothesis](https://hypothesis.readthedocs.io/) generating **10,000+ random inputs** per function.

Unlike example-based tests that check specific inputs, property-based tests verify **invariants** that must hold for ALL inputs. Your code will be hammered with edge cases you never imagined: NaN, empty strings, unicode, timezone gaps, negative numbers, and more.

## Setup

```bash
pip install -r requirements.txt
```

## The Challenge

Open `functions.py` and implement all 4 functions. Each function has a detailed docstring explaining the expected behavior, input/output formats, and invariants.

### Function 1: `calculate_bill`
Calculate a restaurant bill with coupons and tax. Key invariants:
- Total is always >= 0
- Tax is applied AFTER discounts
- Multiple coupons never drive total below $0
- NaN/Inf inputs raise ValueError

### Function 2: `schedule_reservation`
Schedule timezone-aware reservations with conflict detection. Key invariants:
- All overlaps are detected via UTC comparison
- DST spring-forward gaps raise ValueError
- Party size must be >= 1
- Result always has len(existing) + 1 reservations

### Function 3: `parse_order`
Parse free-form text into structured order data. Key invariants:
- **Never** raises an exception (returns ParseError instead)
- len(items) == len(quantities)
- Unicode and injection attempts don't crash it
- Empty input returns ParseError

### Function 4: `reconcile_inventory`
Merge inventory from 3 sources using majority/median resolution. Key invariants:
- Every item from all sources appears in the result
- Deterministic (same input = same output)
- All quantities >= 0
- Complete audit trail

## Running the Tests

```bash
pytest test_fuzz.py -v
```

Each test class runs 10,000+ random inputs. Be patient -- this takes a minute or two.

## Validation

When all property tests pass, the flag is printed. Submit it on the challenge card to record your score.

## Tips

- Read the docstrings in `functions.py` carefully -- they spell out every invariant.
- Check `models.py` for the data classes you need to return.
- Think defensively: what happens with 0 items? NaN prices? Empty strings?
- The Hypothesis tests are designed to be passable. If a test seems impossible, re-read the docstring.
- Use `pytest test_fuzz.py -x -v` to stop at the first failure and see the counterexample.
