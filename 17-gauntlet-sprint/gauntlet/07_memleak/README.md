# Challenge 07: Fix the Memory Leak

## Problem

`leaky_server.py` simulates a long-running server process that handles requests. It has two memory leaks:

1. A cache dict that grows unboundedly (items are never evicted).
2. Circular references between request and response objects that prevent garbage collection.

## Task

Fix `leaky_server.py` so that:
- Memory usage stays under **50MB** after 100,000 iterations.
- The server still functions correctly (processes requests and returns correct responses).
- The cache still works (recent items can be retrieved) but has bounded size.

## Files

- `leaky_server.py` — The buggy server code. Edit this file.
- `test_memleak.py` — Tests. Do NOT modify.

## Run

```bash
python -m pytest test_memleak.py -v
```
