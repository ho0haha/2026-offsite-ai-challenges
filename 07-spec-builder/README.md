# Challenge 7: Spec Builder + Build (500 pts)

**Tool:** Claude Code

## Overview

This is a two-phase challenge. First, you write a Product Requirements Document (PRD) based on a vague business brief. Then, you build the feature described in your own PRD.

## Phase 1: Write the PRD

Read `brief.md` — it contains a 3-sentence business brief from a stakeholder. Your job is to turn this into a proper PRD.

Create a file called `prd.md` that includes:

1. **User Stories** — At least 3 user stories in the format: "As a [role], I want [feature], so that [benefit]."
2. **Acceptance Criteria** — At least 5 specific, testable acceptance criteria.
3. **Edge Cases / Error Handling** — A section describing edge cases and how the system should handle errors.
4. **Technical Approach** — A section describing the technical approach, architecture, or implementation strategy.

Validate your PRD:
```bash
python prd_validator.py prd.md
```

## Phase 2: Build the Feature

Based on your PRD, implement a `waste_tracker.py` module that passes all tests in `test_implementation.py`.

The module should provide a `WasteTracker` class that can:
- Log food waste entries (date, item, quantity, unit, reason, brand)
- Query entries by date range and brand
- Calculate waste statistics (totals by category, daily averages, top wasted items)
- Determine waste trends (increasing, decreasing, or stable)
- Export data to CSV

Run the tests:
```bash
python -m pytest test_implementation.py -v
```

## Validation

Once both phases pass, run:
```bash
bash validate.sh
```

This will verify your PRD structure and run all implementation tests. If everything passes, you'll receive the flag.

## Files

| File | Description |
|------|-------------|
| `brief.md` | The 3-sentence business brief |
| `prd_validator.py` | Validates your PRD structure |
| `test_implementation.py` | Tests for your implementation |
| `validate.sh` | Runs both validators, prints flag |
| `requirements.txt` | Python dependencies |

## Rules

- You must create `prd.md` (your PRD) and `waste_tracker.py` (your implementation)
- The PRD must pass `prd_validator.py`
- The implementation must pass all tests in `test_implementation.py`
- Do not modify test files or the validator
