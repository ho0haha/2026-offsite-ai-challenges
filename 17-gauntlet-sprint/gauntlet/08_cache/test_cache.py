"""
Tests for the LRU cache with TTL.
Do NOT modify this file.
"""

import pytest
import threading
from solution import LRUCache


def test_basic_get_put():
    """Basic get/put operations."""
    cache = LRUCache(capacity=3, max_age=60.0)
    t = 1000.0

    cache.put("a", 1, t)
    cache.put("b", 2, t + 1)
    cache.put("c", 3, t + 2)

    assert cache.get("a", t + 3) == 1
    assert cache.get("b", t + 3) == 2
    assert cache.get("c", t + 3) == 3
    assert cache.get("d", t + 3) is None


def test_lru_eviction():
    """LRU item should be evicted when at capacity."""
    cache = LRUCache(capacity=3, max_age=60.0)
    t = 1000.0

    cache.put("a", 1, t)
    cache.put("b", 2, t + 1)
    cache.put("c", 3, t + 2)

    # Access "a" to make it recently used
    cache.get("a", t + 3)

    # Adding "d" should evict "b" (least recently used)
    cache.put("d", 4, t + 4)

    assert cache.get("a", t + 5) == 1  # accessed recently
    assert cache.get("b", t + 5) is None  # evicted
    assert cache.get("c", t + 5) == 3
    assert cache.get("d", t + 5) == 4


def test_ttl_expiry():
    """Entries should expire after max_age."""
    cache = LRUCache(capacity=10, max_age=5.0)
    t = 1000.0

    cache.put("x", 100, t)
    assert cache.get("x", t + 4) == 100   # still valid
    assert cache.get("x", t + 6) is None  # expired


def test_ttl_reset_on_put():
    """Updating a key should reset its TTL."""
    cache = LRUCache(capacity=10, max_age=5.0)
    t = 1000.0

    cache.put("x", 100, t)
    cache.put("x", 200, t + 4)  # reset TTL
    assert cache.get("x", t + 8) == 200   # still valid (TTL reset at t+4)
    assert cache.get("x", t + 10) is None  # expired (t+4 + 5 = t+9)


def test_get_does_not_reset_ttl():
    """Getting a key should NOT reset its TTL."""
    cache = LRUCache(capacity=10, max_age=5.0)
    t = 1000.0

    cache.put("x", 100, t)
    cache.get("x", t + 3)  # access but don't reset TTL
    assert cache.get("x", t + 6) is None  # expired (t + 5)


def test_delete():
    """Delete should remove a key."""
    cache = LRUCache(capacity=10, max_age=60.0)
    t = 1000.0

    cache.put("a", 1, t)
    assert cache.delete("a") is True
    assert cache.get("a", t + 1) is None
    assert cache.delete("a") is False  # already deleted
    assert cache.delete("nonexistent") is False


def test_update_value():
    """Putting the same key should update the value."""
    cache = LRUCache(capacity=10, max_age=60.0)
    t = 1000.0

    cache.put("a", 1, t)
    cache.put("a", 2, t + 1)
    assert cache.get("a", t + 2) == 2


def test_evict_expired_before_lru():
    """When evicting, prefer expired entries over LRU entries."""
    cache = LRUCache(capacity=2, max_age=5.0)
    t = 1000.0

    cache.put("old", 1, t)
    cache.put("new", 2, t + 4)

    # At t+6, "old" is expired. Adding "third" should evict "old" (expired), not "new"
    cache.put("third", 3, t + 6)

    assert cache.get("old", t + 6) is None    # expired and/or evicted
    assert cache.get("new", t + 6) == 2       # should still be here
    assert cache.get("third", t + 6) == 3


def test_capacity_one():
    """Cache with capacity 1."""
    cache = LRUCache(capacity=1, max_age=60.0)
    t = 1000.0

    cache.put("a", 1, t)
    assert cache.get("a", t + 1) == 1

    cache.put("b", 2, t + 2)
    assert cache.get("a", t + 3) is None
    assert cache.get("b", t + 3) == 2


def test_concurrent_access():
    """Cache should handle concurrent reads/writes correctly."""
    cache = LRUCache(capacity=100, max_age=60.0)
    t = 1000.0
    errors = []

    def writer(start_key):
        try:
            for i in range(100):
                key = f"{start_key}_{i}"
                cache.put(key, i, t + i * 0.001)
        except Exception as e:
            errors.append(e)

    def reader(start_key):
        try:
            for i in range(100):
                key = f"{start_key}_{i}"
                cache.get(key, t + 10)
        except Exception as e:
            errors.append(e)

    threads = []
    for j in range(5):
        threads.append(threading.Thread(target=writer, args=(f"w{j}",)))
        threads.append(threading.Thread(target=reader, args=(f"w{j}",)))

    for thr in threads:
        thr.start()
    for thr in threads:
        thr.join()

    assert len(errors) == 0, f"Errors during concurrent access: {errors}"


def test_no_functools_lru_cache():
    """Must not use functools.lru_cache."""
    import inspect
    source = inspect.getsource(LRUCache)
    assert "functools" not in source, "Cannot use functools.lru_cache"
    assert "cachetools" not in source, "Cannot use cachetools"
