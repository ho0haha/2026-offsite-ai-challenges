# Challenge 02: Optimize the Slow Query

## Problem

A SQLite database has ~50K rows across 3 tables: `orders`, `order_items`, and `products`. The query in `slow_query.sql` is correct but painfully slow due to missing indexes, unnecessary subqueries, and inefficient joins.

## Task

Edit `solution.py` to:
1. Create any indexes needed to speed up the query.
2. Write an optimized query that returns the **exact same results** as the slow query.
3. The optimized query must complete in **under 100ms**.

## Files

- `setup_db.py` — Run this first to create the database. Do NOT modify.
- `slow_query.sql` — The slow reference query. Do NOT modify.
- `solution.py` — Your solution. Edit this file.
- `test_sql.py` — Tests. Do NOT modify.

## Setup

```bash
python setup_db.py   # Creates gauntlet_02.db
python -m pytest test_sql.py -v
```
