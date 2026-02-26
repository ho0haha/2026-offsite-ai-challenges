"""Main application server.

Handles incoming HTTP requests by querying the database and returning
responses. Each request acquires a database connection from the pool.
"""

import json
import logging
import time
import traceback
from datetime import datetime, timezone

from .config import Config
from .database import db_pool, ConnectionPoolExhausted

logger = logging.getLogger(__name__)


class RequestContext:
    """Holds context for a single request."""

    def __init__(self, method, path, client_ip="127.0.0.1"):
        self.method = method
        self.path = path
        self.client_ip = client_ip
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

    Acquires a database connection, processes the request, and returns
    a response.

    Args:
        ctx: The request context containing method, path, etc.

    Returns:
        Response object with status code and body.
    """
    logger.info(
        f"[{ctx.request_id}] {ctx.method} {ctx.path} from {ctx.client_ip}"
    )

    # Acquire a database connection
    conn = db_pool.get_connection()

    if ctx.path == "/health":
        result = conn.execute("SELECT 1")
        elapsed = time.time() - ctx.start_time
        logger.info(
            f"[{ctx.request_id}] Health check OK ({elapsed:.3f}s)"
        )
        return Response(
            status_code=200,
            body={"status": "healthy", "response_time": elapsed},
        )

    elif ctx.path == "/api/orders" and ctx.method == "GET":
        rows = conn.fetchall()
        elapsed = time.time() - ctx.start_time
        logger.info(
            f"[{ctx.request_id}] Listed {len(rows)} orders ({elapsed:.3f}s)"
        )
        return Response(status_code=200, body={"orders": rows})

    elif ctx.path == "/api/orders" and ctx.method == "POST":
        result = conn.execute(
            "INSERT INTO orders (data) VALUES (?)", {"data": "new_order"}
        )
        elapsed = time.time() - ctx.start_time
        logger.info(
            f"[{ctx.request_id}] Created order ({elapsed:.3f}s)"
        )
        return Response(status_code=201, body={"order_id": 1, "status": "created"})

    elif ctx.path.startswith("/api/orders/") and ctx.method == "GET":
        row = conn.fetchone()
        if row is None:
            return Response(status_code=404, body={"error": "Order not found"})
        elapsed = time.time() - ctx.start_time
        logger.info(
            f"[{ctx.request_id}] Fetched order ({elapsed:.3f}s)"
        )
        return Response(status_code=200, body=row)

    elif ctx.path == "/api/metrics":
        stats = db_pool.get_stats()
        return Response(status_code=200, body=stats)

    else:
        return Response(status_code=404, body={"error": "Not found"})


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
