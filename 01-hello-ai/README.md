# Challenge 1: Hello AI

**Points:** 50 | **Difficulty:** Easy

## Objective

Use your AI coding tool to generate Python function implementations from docstrings.

## Instructions

1. Open `starter.py` — you'll find 3 functions with detailed docstrings but empty bodies (`pass`)
2. Use your AI coding assistant to implement each function based on the docstring
3. Run the test suite:
   ```bash
   pip install -r requirements.txt
   python -m pytest test_solution.py -v
   ```
4. When all 9 tests pass, the test harness auto-submits your solution to the CTF server
5. Check the leaderboard to confirm your points!

## Tips

- Read each docstring carefully — they specify exact behavior including edge cases
- The tests are strict: match the documented return types and formats
- If a test fails, read the error message and adjust your implementation

## Files

- `starter.py` — Implement the 3 functions here
- `test_solution.py` — Test suite (do not modify)
- `requirements.txt` — Dependencies
