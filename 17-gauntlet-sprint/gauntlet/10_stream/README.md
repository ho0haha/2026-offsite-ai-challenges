# Challenge 10: Streaming JSON Aggregator

## Problem

Build a stream processor that reads JSON lines from stdin, applies 5-minute tumbling window aggregation, and writes summary records to stdout.

## Input Format

Each line is a JSON object:
```json
{"timestamp": 1700000100, "sensor_id": "temp_01", "value": 23.5}
```

- `timestamp`: Unix epoch seconds (integer), monotonically increasing
- `sensor_id`: String identifier
- `value`: Floating point measurement

## Output Format

When a 5-minute window closes (a new record's timestamp is >= window_end), emit one JSON line per sensor for that window:

```json
{"window_start": 1700000100, "window_end": 1700000400, "sensor_id": "temp_01", "count": 42, "sum": 987.6, "avg": 23.51, "min": 20.1, "max": 27.3}
```

- `window_start`: First timestamp in the window (aligned to 300-second boundaries: `ts - (ts % 300)`)
- `window_end`: `window_start + 300`
- Output lines sorted by sensor_id within each window
- `avg` rounded to 2 decimal places, `sum` rounded to 2 decimal places
- `min` and `max` are exact values from the input

## Task

Edit `solution.py` to implement the stream processor. It should:
1. Read JSON lines from stdin
2. Aggregate by 5-minute tumbling windows per sensor
3. Write summary JSON lines to stdout when windows close
4. Flush any remaining open windows when stdin ends
5. Use bounded memory (do NOT load all input into memory)

## Files

- `generate_data.py` — Generates test data. Run for manual testing.
- `solution.py` — Your solution. Edit this file.
- `test_stream.py` — Tests. Do NOT modify.

## Run

```bash
python generate_data.py | python solution.py          # Manual test
python -m pytest test_stream.py -v                     # Automated tests
```
