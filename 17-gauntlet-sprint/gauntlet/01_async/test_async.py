"""
Tests for the async race condition fix.
Do NOT modify this file.
"""

import asyncio
import pytest
from broken_async import collect


@pytest.mark.asyncio
async def test_no_items_lost_small():
    """All items from both producers appear in results."""
    items_a = list(range(0, 10))
    items_b = list(range(10, 20))
    result = await collect(items_a, items_b)
    assert sorted(result) == list(range(20)), f"Expected 0-19, got {sorted(result)}"


@pytest.mark.asyncio
async def test_no_items_lost_large():
    """Larger dataset - all items preserved."""
    items_a = list(range(0, 500))
    items_b = list(range(500, 1000))
    result = await collect(items_a, items_b)
    assert len(result) == 1000, f"Expected 1000 items, got {len(result)}"
    assert sorted(result) == list(range(1000))


@pytest.mark.asyncio
async def test_no_duplicates():
    """No duplicate items in results."""
    items_a = ["a", "b", "c", "d", "e"]
    items_b = ["f", "g", "h", "i", "j"]
    result = await collect(items_a, items_b)
    assert len(result) == len(set(result)), "Duplicate items found"
    assert len(result) == 10


@pytest.mark.asyncio
async def test_concurrent_execution():
    """Both producers must run concurrently, not sequentially."""
    import time

    items_a = list(range(50))
    items_b = list(range(50, 100))

    start = time.monotonic()
    result = await collect(items_a, items_b)
    elapsed = time.monotonic() - start

    assert sorted(result) == list(range(100))
    # If run sequentially with sleep(0), should still be fast
    # but items from both producers should be interleaved
    assert elapsed < 5.0, "Took too long - are producers running concurrently?"


@pytest.mark.asyncio
async def test_repeated_runs_consistent():
    """Multiple runs produce consistent results."""
    for _ in range(10):
        items_a = list(range(0, 50))
        items_b = list(range(50, 100))
        result = await collect(items_a, items_b)
        assert len(result) == 100, f"Run produced {len(result)} items instead of 100"
        assert sorted(result) == list(range(100))
