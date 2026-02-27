"""Health check script for the production server.

This script simulates a series of requests to the application server
and verifies that it remains healthy. It tests that the server can
handle multiple consecutive requests — including POST requests that
trigger order validation — without connection pool exhaustion.

Expected behavior when bug is PRESENT:
    - GET requests work fine initially
    - POST /api/orders requests trigger validation that leaks connections
    - After ~10 POST requests, the connection pool is exhausted
    - Subsequent requests fail with 503 errors
    - The health check reports FAILURE

Expected behavior when bug is FIXED:
    - All requests succeed (GET and POST)
    - The connection pool stays healthy
    - total_acquired == total_released
    - The health check reports PASS
"""

import sys
import os
import logging

# Suppress debug logging during health check
logging.basicConfig(level=logging.WARNING)

# Add parent directory to path so we can import app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import ConnectionPool, ConnectionPoolExhausted
from app.server import handle_request, RequestContext


def run_health_check():
    """Run the health check.

    Simulates a realistic mix of requests including GET and POST operations.
    POST /api/orders triggers order validation which, if buggy, will leak
    connections on the duplicate-check path. With a pool size of 10, the
    pool will exhaust after ~10 leaked POST requests.
    """
    print("=" * 60)
    print("  PRODUCTION HEALTH CHECK")
    print("=" * 60)
    print()

    # Create a fresh pool for testing
    from app import database
    database.db_pool = ConnectionPool(min_size=2, max_size=10, timeout=0.5)

    # Realistic mix of requests across all endpoint types
    request_sequence = [
        ("GET", "/health"),
        ("GET", "/api/orders"),
        ("POST", "/api/orders"),
        ("GET", "/api/orders/1"),
        ("GET", "/health"),
        ("POST", "/api/orders"),
        ("GET", "/api/orders"),
        ("GET", "/api/orders/42"),
        ("POST", "/api/orders"),
        ("GET", "/health"),
        ("POST", "/api/orders"),
        ("GET", "/api/orders/7"),
        ("POST", "/api/orders"),
        ("GET", "/api/orders"),
        ("POST", "/api/orders"),
        ("GET", "/health"),
        ("POST", "/api/orders"),
        ("GET", "/api/orders/3"),
        ("POST", "/api/orders"),
        ("GET", "/api/orders"),
        ("POST", "/api/orders"),
        ("GET", "/health"),
        ("POST", "/api/orders"),
        ("GET", "/api/orders/15"),
        ("POST", "/api/orders"),
        ("GET", "/api/orders"),
        ("GET", "/health"),
        ("POST", "/api/orders"),
        ("GET", "/api/orders/99"),
        ("POST", "/api/orders"),
    ]

    total_requests = len(request_sequence)
    successes = 0
    failures = 0
    pool_errors = 0

    print(f"Sending {total_requests} test requests...")
    print()

    for i, (method, path) in enumerate(request_sequence):
        ctx = RequestContext(
            method=method,
            path=path,
            client_ip=f"10.0.0.{i % 256}",
        )
        try:
            response = handle_request(ctx)
            if response.status_code < 500:
                successes += 1
            else:
                failures += 1
                print(f"  Request {i+1}: {method} {path} -> HTTP {response.status_code}")
        except ConnectionPoolExhausted as e:
            pool_errors += 1
            if pool_errors == 1:
                print(f"  Request {i+1}: {method} {path} -> CONNECTION POOL EXHAUSTED")
                print(f"    {e}")
            elif pool_errors == 2:
                print(f"  ... (suppressing further pool errors)")
        except Exception as e:
            failures += 1
            print(f"  Request {i+1}: {method} {path} -> ERROR - {e}")

    print()
    print("-" * 60)
    print(f"  Results:")
    print(f"    Successful:    {successes}/{total_requests}")
    print(f"    Failed:        {failures}/{total_requests}")
    print(f"    Pool Errors:   {pool_errors}/{total_requests}")
    print()

    # Check pool stats
    stats = database.db_pool.get_stats()
    print(f"  Connection Pool Status:")
    print(f"    Active:         {stats['active_connections']}/{stats['max_size']}")
    print(f"    Available:      {stats['available']}")
    print(f"    Created:        {stats['total_created']}")
    print(f"    Total Acquired: {stats['total_acquired']}")
    print(f"    Total Released: {stats['total_released']}")
    print()

    if pool_errors > 0:
        print("  STATUS: FAIL - Connection pool exhausted!")
        print()
        print("  DIAGNOSIS: Connections are being acquired but not released")
        print("  back to the pool. Check the logs to identify which endpoint")
        print("  and code path is leaking connections.")
        print("=" * 60)
        return False
    elif failures > 0:
        print("  STATUS: FAIL - Some requests returned errors")
        print("=" * 60)
        return False
    else:
        print("  STATUS: PASS - All requests successful")
        print(f"  Pool is healthy: {stats['available']} connections available")
        print("=" * 60)
        return True


if __name__ == "__main__":
    passed = run_health_check()
    sys.exit(0 if passed else 1)
