"""
Tests for the memory leak fix.
Do NOT modify this file.
"""

import sys
import tracemalloc
import pytest
from leaky_server import LeakyServer


def test_memory_under_50mb():
    """Server must stay under 50MB after 100K iterations."""
    tracemalloc.start()

    server = LeakyServer()
    for i in range(100_000):
        payload = f"request_payload_{i}_{'x' * 100}"
        result = server.process_request(i, payload)
        assert isinstance(result, str) and len(result) > 0

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    peak_mb = peak / (1024 * 1024)
    assert peak_mb < 50, f"Peak memory: {peak_mb:.1f}MB (limit: 50MB)"


def test_cache_still_works():
    """Cache should still return correct results for recent items."""
    server = LeakyServer()

    # Process some requests
    results = {}
    for i in range(100):
        payload = f"test_payload_{i}"
        result = server.process_request(i, payload)
        results[payload] = result

    # Recent items should still be retrievable (cache hit)
    for i in range(90, 100):
        payload = f"test_payload_{i}"
        result = server.process_request(i + 1000, payload)
        assert result == results[payload], f"Cache miss for recent item {i}"


def test_correct_results():
    """Results must still be correct after the fix."""
    import hashlib
    server = LeakyServer()

    for i in range(50):
        payload = f"verify_payload_{i}"
        result = server.process_request(i, payload)
        expected = hashlib.sha256(payload.encode()).hexdigest()
        assert result == expected, f"Wrong result for request {i}"


def test_no_unbounded_growth():
    """Internal data structures must not grow without bound."""
    server = LeakyServer()

    for i in range(10_000):
        payload = f"growth_test_{i}_{'y' * 50}"
        server.process_request(i, payload)

    # Cache and log should be bounded
    cache_size = server.get_cache_size()
    log_size = server.get_log_size()

    assert cache_size < 5000, f"Cache has {cache_size} entries (should be bounded)"
    assert log_size < 5000, f"Log has {log_size} entries (should be bounded)"
