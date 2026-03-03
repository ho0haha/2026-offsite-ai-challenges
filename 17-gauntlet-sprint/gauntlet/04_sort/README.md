# Challenge 04: Custom Menu Sort

## Problem

`data.json` contains 100 menu items, each with `id`, `name`, `category`, and `price`. Some names contain Unicode characters.

## Task

Edit `solution.py` to implement `custom_sort(items)` that sorts menu items by these criteria (in order of priority):

1. **Category priority** (ascending): appetizer=1, entree=2, dessert=3, drink=4
2. **Price** (descending): higher prices first within same category
3. **Name** (alphabetical, case-insensitive): A-Z within same category+price
4. **ID** (ascending): lowest ID first as final tiebreak

## Files

- `data.json` — 100 menu items. Do NOT modify.
- `solution.py` — Your solution. Edit this file.
- `test_sort.py` — Tests. Do NOT modify.

## Run

```bash
python -m pytest test_sort.py -v
```
