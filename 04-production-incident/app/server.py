"""Main application server.

Handles incoming HTTP requests by dispatching to the appropriate handler.
Each handler acquires a database connection from the pool and releases it
when done to prevent connection leaks.
"""

import json
import logging
import time
import traceback
from datetime import datetime, timezone

from .config import Config
from . import database
from .database import ConnectionPoolExhausted

logger = logging.getLogger(__name__)


class RequestContext:
    """Holds context for a single request."""

    def __init__(self, method, path, client_ip="127.0.0.1", body=None):
        self.method = method
        self.path = path
        self.client_ip = client_ip
        self.body = body or {}
        self.request_id = f"req-{int(time.time()*1000)}"
        self.start_time = time.time()


class Response:
    """Simple HTTP response object."""

    def __init__(self, status_code=200, body=None, headers=None):
        self.status_code = status_code
        self.body = body or {}
        self.headers = headers or {"Content-Type": "application/json"}

    def to_dict(self):
        return {
            "status_code": self.status_code,
            "body": self.body,
            "headers": self.headers,
        }


def handle_request(ctx: RequestContext) -> Response:
    """Handle an incoming HTTP request.

    Routes the request to the appropriate handler based on method and path.

    Args:
        ctx: The request context containing method, path, etc.

    Returns:
        Response object with status code and body.
    """
    logger.info(
        f"[{ctx.request_id}] {ctx.method} {ctx.path} from {ctx.client_ip}"
    )

    if ctx.path == "/health":
        return _handle_health(ctx)

    elif ctx.path == "/api/orders" and ctx.method == "GET":
        return _handle_list_orders(ctx)

    elif ctx.path == "/api/orders" and ctx.method == "POST":
        return _handle_create_order(ctx)

    elif ctx.path.startswith("/api/orders/") and ctx.method == "GET":
        return _handle_get_order(ctx)

    elif ctx.path.startswith("/api/orders/") and ctx.method == "PUT":
        return _handle_update_order(ctx)

    elif ctx.path.startswith("/api/orders/") and ctx.method == "DELETE":
        return _handle_delete_order(ctx)

    elif ctx.path == "/api/metrics":
        stats = database.db_pool.get_stats()
        return Response(status_code=200, body=stats)

    else:
        return Response(status_code=404, body={"error": "Not found"})


def _handle_health(ctx):
    """Handle GET /health requests."""
    conn = database.db_pool.get_connection()
    try:
        result = conn.execute("SELECT 1")
        elapsed = time.time() - ctx.start_time
        logger.info(
            f"[{ctx.request_id}] Health check OK ({elapsed:.3f}s)"
        )
        return Response(
            status_code=200,
            body={"status": "healthy", "response_time": elapsed},
        )
    finally:
        database.db_pool.release_connection(conn)


def _handle_list_orders(ctx):
    """Handle GET /api/orders requests."""
    conn = database.db_pool.get_connection()
    try:
        rows = conn.fetchall()
        elapsed = time.time() - ctx.start_time
        logger.info(
            f"[{ctx.request_id}] Listed {len(rows)} orders ({elapsed:.3f}s)"
        )
        return Response(status_code=200, body={"orders": rows})
    finally:
        database.db_pool.release_connection(conn)


def _handle_create_order(ctx):
    """Handle POST /api/orders requests."""
    # Validate order data before creating
    if not _validate_order(ctx):
        return Response(
            status_code=409,
            body={"error": "Duplicate order detected"},
        )

    conn = database.db_pool.get_connection()
    try:
        result = conn.execute(
            "INSERT INTO orders (data) VALUES (?)", {"data": "new_order"}
        )
        elapsed = time.time() - ctx.start_time
        logger.info(
            f"[{ctx.request_id}] Created order ({elapsed:.3f}s)"
        )
        return Response(
            status_code=201,
            body={"order_id": 1, "status": "created"},
        )
    finally:
        database.db_pool.release_connection(conn)


def _validate_order(ctx):
    """Validate order data against business rules.

    Checks for duplicate orders from the same client to prevent
    double-submissions. Returns True if the order is valid.
    """
    conn = database.db_pool.get_connection()

    # Check for recent duplicate orders from this client
    existing = conn.fetchone()

    if existing:
        logger.warning(
            f"[{ctx.request_id}] Duplicate order from {ctx.client_ip}"
        )
        return False

    database.db_pool.release_connection(conn)
    return True


def _handle_get_order(ctx):
    """Handle GET /api/orders/:id requests."""
    conn = database.db_pool.get_connection()
    try:
        order_id = ctx.path.split("/")[-1]
        row = conn.fetchone()
        if row is None:
            return Response(
                status_code=404,
                body={"error": "Order not found"},
            )
        elapsed = time.time() - ctx.start_time
        logger.info(
            f"[{ctx.request_id}] Fetched order {order_id} ({elapsed:.3f}s)"
        )
        return Response(status_code=200, body=row)
    finally:
        database.db_pool.release_connection(conn)


def _handle_update_order(ctx):
    """Handle PUT /api/orders/:id requests."""
    conn = database.db_pool.get_connection()
    try:
        order_id = ctx.path.split("/")[-1]
        result = conn.execute(
            "UPDATE orders SET data = ? WHERE id = ?",
            {"data": "updated", "id": order_id},
        )
        elapsed = time.time() - ctx.start_time
        logger.info(
            f"[{ctx.request_id}] Updated order {order_id} ({elapsed:.3f}s)"
        )
        return Response(
            status_code=200,
            body={"order_id": order_id, "status": "updated"},
        )
    finally:
        database.db_pool.release_connection(conn)


def _handle_delete_order(ctx):
    """Handle DELETE /api/orders/:id requests."""
    conn = database.db_pool.get_connection()
    try:
        order_id = ctx.path.split("/")[-1]
        result = conn.execute(
            "DELETE FROM orders WHERE id = ?", {"id": order_id}
        )
        elapsed = time.time() - ctx.start_time
        logger.info(
            f"[{ctx.request_id}] Deleted order {order_id} ({elapsed:.3f}s)"
        )
        return Response(
            status_code=200,
            body={"order_id": order_id, "status": "deleted"},
        )
    finally:
        database.db_pool.release_connection(conn)


def process_batch(requests):
    """Process a batch of requests sequentially.

    Args:
        requests: List of RequestContext objects.

    Returns:
        List of Response objects.
    """
    responses = []
    for ctx in requests:
        try:
            resp = handle_request(ctx)
            responses.append(resp)
        except ConnectionPoolExhausted as e:
            logger.error(
                f"[{ctx.request_id}] Connection pool exhausted: {e}"
            )
            responses.append(
                Response(
                    status_code=503,
                    body={"error": "Service temporarily unavailable"},
                )
            )
        except Exception as e:
            logger.error(
                f"[{ctx.request_id}] Unhandled error: {e}\n"
                f"{traceback.format_exc()}"
            )
            responses.append(
                Response(
                    status_code=500,
                    body={"error": "Internal server error"},
                )
            )
    return responses


def run_server():
    """Start the application server (simulation).

    In a real application this would start an HTTP server. For this
    challenge it simulates processing requests to demonstrate the
    connection leak issue.
    """
    logging.basicConfig(
        level=getattr(logging, Config.LOG_LEVEL),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    logger.info(
        f"Server starting on {Config.SERVER_HOST}:{Config.SERVER_PORT} "
        f"with {Config.WORKER_COUNT} workers"
    )

    # Simulate incoming requests
    paths = ["/health", "/api/orders", "/api/orders/1", "/api/orders"]
    methods = ["GET", "GET", "GET", "POST"]

    request_num = 0
    while True:
        idx = request_num % len(paths)
        ctx = RequestContext(
            method=methods[idx],
            path=paths[idx],
            client_ip=f"10.0.{request_num % 256}.{(request_num * 7) % 256}",
        )
        try:
            resp = handle_request(ctx)
            logger.info(
                f"[{ctx.request_id}] Response: {resp.status_code}"
            )
        except ConnectionPoolExhausted:
            logger.critical(
                f"[{ctx.request_id}] FATAL: Connection pool exhausted! "
                f"Server cannot process requests."
            )
            break
        except Exception as e:
            logger.error(f"[{ctx.request_id}] Error: {e}")

        request_num += 1
        time.sleep(0.05)


if __name__ == "__main__":
    run_server()
