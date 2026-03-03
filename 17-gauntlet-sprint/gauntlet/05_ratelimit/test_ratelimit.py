"""
Tests for the sliding window rate limiter.
Do NOT modify this file.
"""

import pytest
from solution import SlidingWindowRateLimiter


def test_basic_allow():
    """Basic: allow up to max_requests, then deny."""
    limiter = SlidingWindowRateLimiter(max_requests=5, window_seconds=60.0)
    t = 1000.0

    for i in range(5):
        assert limiter.allow("client_a", t + i) is True, f"Request {i+1} should be allowed"

    assert limiter.allow("client_a", t + 5) is False, "6th request should be denied"


def test_window_expiry():
    """Requests outside the window should not count."""
    limiter = SlidingWindowRateLimiter(max_requests=3, window_seconds=10.0)

    assert limiter.allow("c1", 100.0) is True
    assert limiter.allow("c1", 105.0) is True
    assert limiter.allow("c1", 109.0) is True
    assert limiter.allow("c1", 109.5) is False  # 3 requests in window

    # At t=111, the request at t=100 is outside the window (100 <= 111-10=101)
    assert limiter.allow("c1", 111.0) is True


def test_multiple_clients():
    """Each client has independent limits."""
    limiter = SlidingWindowRateLimiter(max_requests=2, window_seconds=60.0)
    t = 1000.0

    assert limiter.allow("alice", t) is True
    assert limiter.allow("alice", t + 1) is True
    assert limiter.allow("alice", t + 2) is False

    # Bob should be independent
    assert limiter.allow("bob", t) is True
    assert limiter.allow("bob", t + 1) is True
    assert limiter.allow("bob", t + 2) is False


def test_burst_traffic():
    """Many requests at the exact same timestamp."""
    limiter = SlidingWindowRateLimiter(max_requests=10, window_seconds=1.0)
    t = 500.0

    allowed = sum(1 for _ in range(20) if limiter.allow("burst_client", t))
    assert allowed == 10, f"Expected 10 allowed, got {allowed}"


def test_get_remaining():
    """get_remaining should reflect current state."""
    limiter = SlidingWindowRateLimiter(max_requests=5, window_seconds=60.0)
    t = 1000.0

    assert limiter.get_remaining("x", t) == 5
    limiter.allow("x", t)
    assert limiter.get_remaining("x", t + 1) == 4
    limiter.allow("x", t + 1)
    limiter.allow("x", t + 2)
    assert limiter.get_remaining("x", t + 3) == 2


def test_get_remaining_after_expiry():
    """get_remaining should account for expired requests."""
    limiter = SlidingWindowRateLimiter(max_requests=3, window_seconds=10.0)

    limiter.allow("y", 100.0)
    limiter.allow("y", 105.0)
    limiter.allow("y", 109.0)

    assert limiter.get_remaining("y", 109.0) == 0
    # At t=111, request at t=100 has expired
    assert limiter.get_remaining("y", 111.0) == 1


def test_denied_requests_not_recorded():
    """Denied requests should not be recorded in the window."""
    limiter = SlidingWindowRateLimiter(max_requests=2, window_seconds=60.0)
    t = 1000.0

    limiter.allow("z", t)
    limiter.allow("z", t + 1)

    # These should all be denied and NOT recorded
    for i in range(10):
        assert limiter.allow("z", t + 2 + i) is False

    # After window expires, should allow again
    assert limiter.allow("z", t + 61) is True
    assert limiter.allow("z", t + 62) is True
    assert limiter.allow("z", t + 63) is False  # only 2 allowed


def test_clock_tolerance():
    """Slightly out-of-order timestamps should still work."""
    limiter = SlidingWindowRateLimiter(max_requests=3, window_seconds=10.0)

    limiter.allow("w", 100.0)
    limiter.allow("w", 102.0)
    # Slightly earlier timestamp (clock skew)
    limiter.allow("w", 101.5)

    assert limiter.get_remaining("w", 103.0) == 0


def test_large_number_of_clients():
    """Handle many concurrent clients."""
    limiter = SlidingWindowRateLimiter(max_requests=5, window_seconds=60.0)
    t = 1000.0

    for i in range(1000):
        client = f"client_{i}"
        for j in range(5):
            assert limiter.allow(client, t + j) is True
        assert limiter.allow(client, t + 5) is False
