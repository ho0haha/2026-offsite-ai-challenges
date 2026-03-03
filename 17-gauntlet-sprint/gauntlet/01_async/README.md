# Challenge 01: Fix the Race Condition

## Problem

`broken_async.py` contains two async coroutines that append results to a shared list concurrently. There is a race condition: without proper synchronization, items can be lost, duplicated, or interleaved incorrectly.

## Task

Fix `broken_async.py` so that:
- All items are correctly appended to the shared list.
- No items are lost or duplicated.
- The coroutines still run concurrently (do NOT make them sequential).

## Files

- `broken_async.py` — The buggy code. Edit this file.
- `test_async.py` — Tests. Do NOT modify.

## Run

```bash
python -m pytest test_async.py -v
```
