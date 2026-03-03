# Challenge 05: Sliding Window Rate Limiter

## Problem

Implement a sliding-window rate limiter that tracks requests per client over a configurable time window.

## Task

Edit `solution.py` to implement the `SlidingWindowRateLimiter` class with:

- `__init__(self, max_requests: int, window_seconds: float)` — Configure the limiter.
- `allow(self, client_id: str, timestamp: float) -> bool` — Returns True if the request is allowed, False if rate-limited. `timestamp` is a Unix timestamp (seconds).
- `get_remaining(self, client_id: str, timestamp: float) -> int` — Returns how many requests the client can still make in the current window.

The sliding window should count requests in the interval `(timestamp - window_seconds, timestamp]`.

## Files

- `solution.py` — Your solution. Edit this file.
- `test_ratelimit.py` — Tests. Do NOT modify.

## Run

```bash
python -m pytest test_ratelimit.py -v
```
