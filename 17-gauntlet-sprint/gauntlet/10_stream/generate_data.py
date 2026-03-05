"""
Generates test JSON lines data for the stream processing challenge.
Outputs to stdout or a file.

Usage:
    python generate_data.py             # stdout
    python generate_data.py > data.jsonl  # file
"""

import json
import random
import sys

random.seed(99)

SENSORS = [f"sensor_{i:02d}" for i in range(10)]
BASE_TS = 1699999800  # Starting timestamp (aligned to 300s window)


def generate(num_records=100000):
    """Generate monotonically increasing timestamped sensor data."""
    ts = BASE_TS
    for _ in range(num_records):
        ts += random.randint(0, 3)  # 0-3 seconds increment
        sensor = random.choice(SENSORS)
        value = round(random.uniform(10.0, 50.0), 2)
        record = {
            "timestamp": ts,
            "sensor_id": sensor,
            "value": value,
        }
        print(json.dumps(record))


if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 100000
    generate(count)
