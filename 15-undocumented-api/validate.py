#!/usr/bin/env python3
"""
Validator for Challenge 15: The Undocumented API

Checks that the participant's explorer.py script produces the correct flag.
"""

import subprocess
import sys
import os

EXPECTED_FLAG = "CTF{api_explorer_master_chef}"


def validate():
    challenge_dir = os.path.dirname(os.path.abspath(__file__))
    explorer_path = os.path.join(challenge_dir, "explorer.py")

    if not os.path.exists(explorer_path):
        print("FAIL: explorer.py not found")
        return False

    # Read the file and check it has more than the starter content
    with open(explorer_path, "r") as f:
        content = f.read()

    if content.count("\n") < 15:
        print("FAIL: explorer.py appears to still be the starter template")
        return False

    # Run the explorer script and capture output
    try:
        result = subprocess.run(
            [sys.executable, explorer_path],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=challenge_dir,
        )
    except subprocess.TimeoutExpired:
        print("FAIL: explorer.py timed out after 60 seconds")
        return False

    output = result.stdout + result.stderr

    if EXPECTED_FLAG in output:
        print(f"PASS: Flag found -> {EXPECTED_FLAG}")
        return True
    else:
        print("FAIL: Flag not found in output")
        if result.returncode != 0:
            print(f"  Script exited with code {result.returncode}")
        if result.stderr:
            print(f"  Stderr: {result.stderr[:500]}")
        return False


if __name__ == "__main__":
    success = validate()
    sys.exit(0 if success else 1)
