"""
Tests for the SQL optimization challenge.
Do NOT modify this file.
"""

import sqlite3
import os
import time
import pytest
from solution import create_indexes, optimized_query
from setup_db import create_db, DB_PATH

SLOW_QUERY_PATH = os.path.join(os.path.dirname(__file__), "slow_query.sql")


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    """Ensure the database exists."""
    if not os.path.exists(DB_PATH):
        create_db()


def get_slow_results():
    """Run the reference slow query and return results."""
    with open(SLOW_QUERY_PATH) as f:
        slow_sql = f.read()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute(slow_sql)
    results = cursor.fetchall()
    conn.close()
    return results


def test_optimized_query_returns_same_results():
    """Optimized query must return identical results to the slow query."""
    expected = get_slow_results()
    assert len(expected) > 0, "Slow query returned no results - DB may be empty"

    conn = sqlite3.connect(DB_PATH)
    create_indexes(conn)
    conn.commit()

    query = optimized_query()
    assert query and len(query.strip()) > 0, "optimized_query() returned empty string"

    cursor = conn.execute(query)
    actual = cursor.fetchall()
    conn.close()

    assert len(actual) == len(expected), (
        f"Row count mismatch: expected {len(expected)}, got {len(actual)}"
    )

    for i, (exp_row, act_row) in enumerate(zip(expected, actual)):
        assert len(act_row) == len(exp_row), f"Column count mismatch in row {i}"
        # Compare product_name, category
        assert act_row[0] == exp_row[0], f"Row {i} product_name mismatch"
        assert act_row[1] == exp_row[1], f"Row {i} category mismatch"
        # Compare numeric values with tolerance
        assert abs(act_row[2] - exp_row[2]) < 0.01, f"Row {i} revenue mismatch"
        assert act_row[3] == exp_row[3], f"Row {i} unique_customers mismatch"
        assert act_row[4] == exp_row[4], f"Row {i} total_quantity mismatch"


def test_optimized_query_is_fast():
    """Optimized query must complete in under 100ms."""
    conn = sqlite3.connect(DB_PATH)
    create_indexes(conn)
    conn.commit()

    query = optimized_query()
    assert query and len(query.strip()) > 0

    # Warm up
    conn.execute(query).fetchall()

    # Timed run
    start = time.perf_counter()
    conn.execute(query).fetchall()
    elapsed_ms = (time.perf_counter() - start) * 1000
    conn.close()

    assert elapsed_ms < 100, f"Query took {elapsed_ms:.1f}ms, must be under 100ms"


def test_indexes_created():
    """At least one index must be created."""
    conn = sqlite3.connect(DB_PATH)

    # Get index count before
    before = conn.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='index'"
    ).fetchone()[0]

    create_indexes(conn)
    conn.commit()

    after = conn.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='index'"
    ).fetchone()[0]
    conn.close()

    assert after > before, "create_indexes() must create at least one index"
