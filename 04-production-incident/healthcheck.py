"""Health check script for the production server.

This script simulates a series of requests to the application server
and verifies that it remains healthy. It tests that the server can
handle multiple consecutive requests without connection pool exhaustion.

Expected behavior when bug is PRESENT:
    - The server starts responding normally
    - After ~20 requests, the connection pool is exhausted
    - Subsequent requests fail with 503 errors
    - The health check reports FAILURE

Expected behavior when bug is FIXED:
    - All requests succeed
    - The connection pool stays healthy
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

    Simulates 50 sequential requests to the server. If the connection
    pool is leaking, it will be exhausted after ~20 requests (the default
    pool max size). If the bug is fixed, all 50 requests should succeed.
    """
    print("=" * 60)
    print("  PRODUCTION HEALTH CHECK")
    print("=" * 60)
    print()

    # Create a fresh pool for testing
    from app import database
    database.db_pool = ConnectionPool(min_size=2, max_size=10, timeout=2)

    total_requests = 50
    successes = 0
    failures = 0
    pool_errors = 0

    print(f"Sending {total_requests} test requests...")
    print()

    for i in range(total_requests):
        ctx = RequestContext(
            method="GET",
            path="/health",
            client_ip="10.0.0.1",
        )
        try:
            response = handle_request(ctx)
            if response.status_code == 200:
                successes += 1
            else:
                failures += 1
                print(f"  Request {i+1}: HTTP {response.status_code}")
        except ConnectionPoolExhausted as e:
            pool_errors += 1
            if pool_errors == 1:
                print(f"  Request {i+1}: CONNECTION POOL EXHAUSTED")
                print(f"    {e}")
            elif pool_errors == 2:
                print(f"  ... (suppressing further pool errors)")
        except Exception as e:
            failures += 1
            print(f"  Request {i+1}: ERROR - {e}")

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
    print(f"    Active:    {stats['active_connections']}/{stats['max_size']}")
    print(f"    Available: {stats['available']}")
    print(f"    Created:   {stats['total_created']}")
    print()

    if pool_errors > 0:
        print("  STATUS: FAIL - Connection pool exhausted!")
        print()
        print("  DIAGNOSIS: Connections are being acquired but not released")
        print("  back to the pool. Investigate request handlers in server.py")
        print("  for missing release_connection() calls.")
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
