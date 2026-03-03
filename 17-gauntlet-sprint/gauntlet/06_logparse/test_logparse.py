"""
Tests for the POS log parser challenge.
Do NOT modify this file.
"""

import os
import pytest
from solution import parse_logs
from generate_logs import generate, LOG_PATH, EXPECTED_PATH


@pytest.fixture(scope="module", autouse=True)
def setup_logs():
    """Ensure log files exist."""
    if not os.path.exists(LOG_PATH) or not os.path.exists(EXPECTED_PATH):
        generate()


def test_output_matches_expected():
    """Parsed output must exactly match expected_output.txt."""
    with open(EXPECTED_PATH) as f:
        expected = f.read().strip()

    result = parse_logs(LOG_PATH).strip()
    assert result == expected, (
        f"Output does not match expected.\n"
        f"First difference at character {next((i for i, (a, b) in enumerate(zip(result, expected)) if a != b), min(len(result), len(expected)))}\n"
        f"Expected length: {len(expected)}, Got length: {len(result)}"
    )


def test_hourly_revenue_section():
    """Report must contain hourly revenue section."""
    result = parse_logs(LOG_PATH)
    assert "=== HOURLY REVENUE ===" in result


def test_top_items_section():
    """Report must contain top 10 items section."""
    result = parse_logs(LOG_PATH)
    assert "=== TOP 10 ITEMS ===" in result


def test_average_ticket_time_section():
    """Report must contain average ticket time section."""
    result = parse_logs(LOG_PATH)
    assert "=== AVERAGE TICKET TIME ===" in result


def test_report_has_all_sections():
    """Report must have all three sections in order."""
    result = parse_logs(LOG_PATH)
    idx_hourly = result.index("=== HOURLY REVENUE ===")
    idx_items = result.index("=== TOP 10 ITEMS ===")
    idx_time = result.index("=== AVERAGE TICKET TIME ===")
    assert idx_hourly < idx_items < idx_time, "Sections must be in order"
