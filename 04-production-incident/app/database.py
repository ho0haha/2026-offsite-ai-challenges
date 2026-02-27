"""Database connection pool implementation.

This module manages a pool of database connections for the application.
Connections should be acquired with get_connection() and MUST be released
back to the pool with release_connection() when done.
"""

import threading
import time
import logging
from queue import Queue, Empty

from .config import Config

logger = logging.getLogger(__name__)


class ConnectionPoolExhausted(Exception):
    """Raised when the connection pool has no available connections."""
    pass


class MockConnection:
    """Simulates a database connection for demonstration purposes."""

    _id_counter = 0
    _lock = threading.Lock()

    def __init__(self):
        with MockConnection._lock:
            MockConnection._id_counter += 1
            self.id = MockConnection._id_counter
        self.in_use = False
        self.created_at = time.time()
        self.last_used = time.time()

    def execute(self, query, params=None):
        """Simulate executing a database query."""
        self.last_used = time.time()
        # Simulate query execution time
        time.sleep(0.01)
        return {"status": "ok", "rows_affected": 1}

    def fetchone(self):
        """Simulate fetching one row."""
        self.last_used = time.time()
        return {"id": 1, "data": "sample"}

    def fetchall(self):
        """Simulate fetching all rows."""
        self.last_used = time.time()
        return [{"id": i, "data": f"row_{i}"} for i in range(5)]

    def close(self):
        """Close the connection."""
        logger.debug(f"Connection {self.id} closed")

    def is_alive(self):
        """Check if the connection is still valid."""
        return True

    def __repr__(self):
        return f"<Connection id={self.id} in_use={self.in_use}>"


class ConnectionPool:
    """A thread-safe database connection pool.

    Manages a fixed-size pool of database connections. Connections are
    acquired with get_connection() and MUST be returned with
    release_connection() to prevent pool exhaustion.
    """

    def __init__(self, min_size=None, max_size=None, timeout=None):
        self.min_size = min_size or Config.POOL_MIN_SIZE
        self.max_size = max_size or Config.POOL_MAX_SIZE
        self.timeout = timeout or Config.POOL_TIMEOUT
        self._pool = Queue(maxsize=self.max_size)
        self._all_connections = []
        self._lock = threading.Lock()
        self._total_created = 0
        self._active_count = 0
        self._total_acquired = 0
        self._total_released = 0

        # Pre-populate pool with minimum connections
        for _ in range(self.min_size):
            conn = self._create_connection()
            self._pool.put(conn)

        logger.info(
            f"Connection pool initialized: min={self.min_size}, "
            f"max={self.max_size}, timeout={self.timeout}s"
        )

    def _create_connection(self, _locked=False):
        """Create a new database connection.

        Args:
            _locked: If True, caller already holds self._lock.
        """
        conn = MockConnection()
        if _locked:
            self._all_connections.append(conn)
            self._total_created += 1
        else:
            with self._lock:
                self._all_connections.append(conn)
                self._total_created += 1
        logger.debug(f"Created new connection {conn.id} (total: {self._total_created})")
        return conn

    def get_connection(self):
        """Acquire a connection from the pool.

        Returns a connection from the pool, creating a new one if the pool
        is empty but the maximum hasn't been reached. Blocks up to
        self.timeout seconds if the pool is exhausted.

        Returns:
            MockConnection: A database connection.

        Raises:
            ConnectionPoolExhausted: If no connection is available within
                the timeout period.
        """
        start = time.time()

        # Try to get an existing connection from the pool
        try:
            conn = self._pool.get(timeout=0.1)
            conn.in_use = True
            with self._lock:
                self._active_count += 1
                self._total_acquired += 1
            logger.info(
                f"Acquired connection {conn.id} from pool "
                f"(active: {self._active_count}/{self.max_size})"
            )
            return conn
        except Empty:
            pass

        # Pool is empty - try to create a new connection if under max
        with self._lock:
            if self._total_created < self.max_size:
                conn = self._create_connection(_locked=True)
                conn.in_use = True
                self._active_count += 1
                self._total_acquired += 1
                logger.info(
                    f"Created and acquired connection {conn.id} "
                    f"(active: {self._active_count}/{self.max_size})"
                )
                return conn

        # At max capacity - wait for a connection to be released
        elapsed = time.time() - start
        remaining_timeout = max(0, self.timeout - elapsed)

        if remaining_timeout > 0:
            wait_start = time.time()
            logger.warning(
                f"Connection pool at capacity ({self._active_count}/{self.max_size}). "
                f"Waiting up to {remaining_timeout:.1f}s for available connection..."
            )
            try:
                conn = self._pool.get(timeout=remaining_timeout)
                wait_time = time.time() - wait_start
                conn.in_use = True
                with self._lock:
                    self._active_count += 1
                    self._total_acquired += 1
                logger.warning(
                    f"Acquired connection {conn.id} after {wait_time:.2f}s wait "
                    f"(active: {self._active_count}/{self.max_size})"
                )
                return conn
            except Empty:
                pass

        # Timeout - no connections available
        with self._lock:
            active = self._active_count
        elapsed = time.time() - start
        logger.error(
            f"Connection pool exhausted! "
            f"active={active}/{self.max_size}, "
            f"waited={elapsed:.2f}s, timeout={self.timeout}s"
        )
        raise ConnectionPoolExhausted(
            f"Could not acquire connection within {self.timeout}s. "
            f"Pool: {active}/{self.max_size} connections in use."
        )

    def release_connection(self, conn):
        """Release a connection back to the pool.

        IMPORTANT: Always call this method when you are done with a
        connection. Failing to do so will leak connections and eventually
        exhaust the pool.

        Args:
            conn: The connection to release back to the pool.
        """
        if conn is None:
            return

        conn.in_use = False
        with self._lock:
            self._active_count = max(0, self._active_count - 1)
            self._total_released += 1

        try:
            self._pool.put_nowait(conn)
            logger.info(
                f"Released connection {conn.id} back to pool "
                f"(active: {self._active_count}/{self.max_size})"
            )
        except Exception:
            # Pool is full (shouldn't happen normally), close the connection
            conn.close()
            logger.warning(f"Pool full, closed excess connection {conn.id}")

    def get_stats(self):
        """Get current pool statistics."""
        with self._lock:
            return {
                "total_created": self._total_created,
                "active_connections": self._active_count,
                "pool_size": self._pool.qsize(),
                "max_size": self.max_size,
                "available": self._pool.qsize(),
                "total_acquired": self._total_acquired,
                "total_released": self._total_released,
            }

    def shutdown(self):
        """Close all connections and shut down the pool."""
        logger.info("Shutting down connection pool...")
        while not self._pool.empty():
            try:
                conn = self._pool.get_nowait()
                conn.close()
            except Empty:
                break
        logger.info("Connection pool shut down complete.")


# Global connection pool instance
db_pool = ConnectionPool()
