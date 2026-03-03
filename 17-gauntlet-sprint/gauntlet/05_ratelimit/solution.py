"""
Sliding Window Rate Limiter - Solution Stub

Implement SlidingWindowRateLimiter with:
- allow(client_id, timestamp) -> bool
- get_remaining(client_id, timestamp) -> int
"""


class SlidingWindowRateLimiter:
    def __init__(self, max_requests: int, window_seconds: float):
        """
        Initialize the rate limiter.

        Args:
            max_requests: Maximum number of requests allowed per window.
            window_seconds: Size of the sliding window in seconds.
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        # TODO: Initialize your data structures

    def allow(self, client_id: str, timestamp: float) -> bool:
        """
        Check if a request from client_id at the given timestamp is allowed.
        If allowed, record the request and return True.
        If rate-limited, return False (do NOT record the request).

        The window covers (timestamp - window_seconds, timestamp].
        """
        # TODO: Implement
        return True

    def get_remaining(self, client_id: str, timestamp: float) -> int:
        """
        Return the number of requests the client can still make
        in the window ending at `timestamp`.
        """
        # TODO: Implement
        return self.max_requests
