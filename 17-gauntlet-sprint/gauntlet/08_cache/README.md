# Challenge 08: LRU Cache with TTL

## Problem

Implement an LRU (Least Recently Used) cache with time-based expiration (TTL).

## Task

Edit `solution.py` to implement the `LRUCache` class with:

- `__init__(self, capacity: int, max_age: float)` — `capacity` is max items, `max_age` is TTL in seconds.
- `get(self, key: str, timestamp: float) -> Optional[Any]` — Return value if key exists and not expired, else None. Accessing a key refreshes its LRU position (but NOT its TTL).
- `put(self, key: str, value: Any, timestamp: float)` — Insert or update a key. If at capacity, evict the least recently used non-expired item. Resets the TTL on update.
- `delete(self, key: str) -> bool` — Remove a key. Returns True if the key existed.

**Requirements:**
- All operations must be O(1) average time.
- You may NOT use `functools.lru_cache` or `cachetools`.
- Expired entries should be lazily cleaned up (on access) or proactively evicted.

## Files

- `solution.py` — Your solution. Edit this file.
- `test_cache.py` — Tests. Do NOT modify.

## Run

```bash
python -m pytest test_cache.py -v
```
