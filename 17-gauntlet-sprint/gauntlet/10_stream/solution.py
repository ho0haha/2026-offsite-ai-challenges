#!/usr/bin/env python3
"""
Streaming JSON Aggregator - Solution Stub

Read JSON lines from stdin, apply 5-minute tumbling window aggregation,
write summary JSON lines to stdout.

Usage:
    python generate_data.py | python solution.py
"""

import sys
import json


WINDOW_SIZE = 300  # 5 minutes in seconds


def process_stream():
    """
    Read JSON lines from stdin and produce windowed aggregates on stdout.

    For each 5-minute tumbling window (aligned to 300-second boundaries):
    - Track count, sum, min, max per sensor_id
    - When a new record's timestamp >= current window_end, emit summaries
      for all sensors in the closing window (sorted by sensor_id)
    - Flush remaining windows when stdin ends

    Output format (one JSON line per sensor per window):
    {"window_start": N, "window_end": N, "sensor_id": "...", "count": N,
     "sum": N.NN, "avg": N.NN, "min": N.NN, "max": N.NN}

    TODO: Implement this function.
    """
    pass


if __name__ == "__main__":
    process_stream()
