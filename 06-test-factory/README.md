# Challenge 6: Test Factory (200 pts)

**Tool:** Claude Code

## Objective

You have a fully functional restaurant inventory management module (`inventory.py`) with **0% test coverage**. Your job is to write a comprehensive test suite that achieves **90%+ code coverage**.

## Rules

1. Do NOT modify `inventory.py`
2. Create a file called `test_inventory.py` with your tests
3. Use `pytest` and `pytest-cov`
4. Achieve 90%+ line coverage to get the flag

## Getting Started

```bash
pip install -r requirements.txt

# Run the coverage check
bash run_coverage.sh
```

## Tips

- Read through `inventory.py` carefully to understand all code paths
- Pay attention to error handling - you need to test both success and failure cases
- Don't forget edge cases: empty inventories, zero quantities, expired items, etc.
- The CSV export/import methods need file I/O testing (use `tmp_path` fixture)
- The `search_items` method does fuzzy matching - test various search patterns
- Check the `get_expiring_soon` method with different date scenarios

## Submission

When coverage reaches 90%+, your solution is auto-submitted to the CTF server.
