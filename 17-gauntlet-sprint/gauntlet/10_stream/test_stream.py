"""
Tests for the streaming JSON aggregator.
Do NOT modify this file.
"""

import json
import subprocess
import sys
import os
import tracemalloc
import pytest

SOLUTION_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "solution.py")
GENERATE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "generate_data.py")
WINDOW_SIZE = 300


def run_processor(input_lines):
    """Run solution.py with given input lines and return output lines."""
    input_text = "\n".join(input_lines) + "\n"
    result = subprocess.run(
        [sys.executable, SOLUTION_PATH],
        input=input_text,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, f"Process failed: {result.stderr}"
    return [line for line in result.stdout.strip().split("\n") if line.strip()]


def reference_aggregate(records):
    """Compute the expected aggregation for comparison."""
    windows = {}
    for rec in records:
        ts = rec["timestamp"]
        window_start = ts - (ts % WINDOW_SIZE)
        window_end = window_start + WINDOW_SIZE
        key = (window_start, rec["sensor_id"])

        if key not in windows:
            windows[key] = {
                "window_start": window_start,
                "window_end": window_end,
                "sensor_id": rec["sensor_id"],
                "count": 0,
                "sum": 0.0,
                "min": float("inf"),
                "max": float("-inf"),
                "values": [],
            }

        w = windows[key]
        w["count"] += 1
        w["sum"] += rec["value"]
        w["min"] = min(w["min"], rec["value"])
        w["max"] = max(w["max"], rec["value"])

    results = []
    for key in sorted(windows.keys()):
        w = windows[key]
        results.append({
            "window_start": w["window_start"],
            "window_end": w["window_end"],
            "sensor_id": w["sensor_id"],
            "count": w["count"],
            "sum": round(w["sum"], 2),
            "avg": round(w["sum"] / w["count"], 2),
            "min": w["min"],
            "max": w["max"],
        })

    return results


def test_simple_single_window():
    """Single window with a few records."""
    records = [
        {"timestamp": 1699999800, "sensor_id": "s1", "value": 10.0},
        {"timestamp": 1699999900, "sensor_id": "s1", "value": 20.0},
        {"timestamp": 1699999999, "sensor_id": "s1", "value": 30.0},
    ]
    input_lines = [json.dumps(r) for r in records]
    output_lines = run_processor(input_lines)

    assert len(output_lines) == 1
    result = json.loads(output_lines[0])
    assert result["sensor_id"] == "s1"
    assert result["count"] == 3
    assert abs(result["avg"] - 20.0) < 0.01
    assert result["min"] == 10.0
    assert result["max"] == 30.0


def test_multiple_sensors():
    """Multiple sensors in same window."""
    records = [
        {"timestamp": 1699999800, "sensor_id": "a", "value": 5.0},
        {"timestamp": 1699999801, "sensor_id": "b", "value": 15.0},
        {"timestamp": 1699999802, "sensor_id": "a", "value": 10.0},
        {"timestamp": 1699999803, "sensor_id": "b", "value": 25.0},
    ]
    input_lines = [json.dumps(r) for r in records]
    output_lines = run_processor(input_lines)

    assert len(output_lines) == 2
    results = [json.loads(line) for line in output_lines]
    results.sort(key=lambda x: x["sensor_id"])

    assert results[0]["sensor_id"] == "a"
    assert results[0]["count"] == 2
    assert results[1]["sensor_id"] == "b"
    assert results[1]["count"] == 2


def test_window_boundaries():
    """Records spanning multiple windows."""
    records = [
        {"timestamp": 1699999800, "sensor_id": "s1", "value": 10.0},
        {"timestamp": 1700000099, "sensor_id": "s1", "value": 20.0},
        # New window
        {"timestamp": 1700000100, "sensor_id": "s1", "value": 30.0},
        {"timestamp": 1700000399, "sensor_id": "s1", "value": 40.0},
    ]
    input_lines = [json.dumps(r) for r in records]
    output_lines = run_processor(input_lines)

    assert len(output_lines) == 2
    results = [json.loads(line) for line in output_lines]
    results.sort(key=lambda x: x["window_start"])

    assert results[0]["window_start"] == 1699999800
    assert results[0]["count"] == 2
    assert results[0]["avg"] == 15.0

    assert results[1]["window_start"] == 1700000100
    assert results[1]["count"] == 2
    assert results[1]["avg"] == 35.0


def test_correctness_medium():
    """Medium dataset correctness check."""
    import random
    random.seed(42)

    records = []
    ts = 1699999800
    sensors = ["alpha", "beta", "gamma"]
    for _ in range(1000):
        ts += random.randint(1, 5)
        records.append({
            "timestamp": ts,
            "sensor_id": random.choice(sensors),
            "value": round(random.uniform(0, 100), 2),
        })

    expected = reference_aggregate(records)
    input_lines = [json.dumps(r) for r in records]
    output_lines = run_processor(input_lines)

    actual = [json.loads(line) for line in output_lines]
    actual.sort(key=lambda x: (x["window_start"], x["sensor_id"]))

    assert len(actual) == len(expected), (
        f"Expected {len(expected)} output records, got {len(actual)}"
    )

    for i, (a, e) in enumerate(zip(actual, expected)):
        assert a["window_start"] == e["window_start"], f"Record {i}: window_start mismatch"
        assert a["sensor_id"] == e["sensor_id"], f"Record {i}: sensor_id mismatch"
        assert a["count"] == e["count"], f"Record {i}: count mismatch"
        assert abs(a["sum"] - e["sum"]) < 0.02, f"Record {i}: sum mismatch"
        assert abs(a["avg"] - e["avg"]) < 0.02, f"Record {i}: avg mismatch"
        assert a["min"] == e["min"], f"Record {i}: min mismatch"
        assert a["max"] == e["max"], f"Record {i}: max mismatch"


def test_large_dataset_memory():
    """Process 1M records without excessive memory usage."""
    # Generate 1M lines via generate_data.py
    gen_result = subprocess.run(
        [sys.executable, GENERATE_PATH, "1000000"],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert gen_result.returncode == 0, f"Data generation failed: {gen_result.stderr}"

    # Run solution with 1M lines
    proc_result = subprocess.run(
        [sys.executable, SOLUTION_PATH],
        input=gen_result.stdout,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert proc_result.returncode == 0, f"Processing failed: {proc_result.stderr}"

    # Verify output is valid JSON lines
    output_lines = [l for l in proc_result.stdout.strip().split("\n") if l.strip()]
    assert len(output_lines) > 0, "No output produced"

    for i, line in enumerate(output_lines[:10]):
        record = json.loads(line)
        assert "window_start" in record
        assert "sensor_id" in record
        assert "count" in record
        assert "avg" in record


def test_sorted_output_within_window():
    """Output within each window must be sorted by sensor_id."""
    records = [
        {"timestamp": 1699999800, "sensor_id": "z_sensor", "value": 1.0},
        {"timestamp": 1699999801, "sensor_id": "a_sensor", "value": 2.0},
        {"timestamp": 1699999802, "sensor_id": "m_sensor", "value": 3.0},
        # Force window close
        {"timestamp": 1700000100, "sensor_id": "a_sensor", "value": 4.0},
    ]
    input_lines = [json.dumps(r) for r in records]
    output_lines = run_processor(input_lines)

    results = [json.loads(line) for line in output_lines]
    first_window = [r for r in results if r["window_start"] == 1699999800]
    sensor_ids = [r["sensor_id"] for r in first_window]
    assert sensor_ids == sorted(sensor_ids), f"Not sorted: {sensor_ids}"
