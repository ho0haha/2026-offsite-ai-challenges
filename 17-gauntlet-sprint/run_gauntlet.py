#!/usr/bin/env python3
"""
Gauntlet Sprint Master Runner
Executes all 10 mini-challenge test suites and reports results.
Prints the flag when 9 or more challenges pass.
"""

import subprocess
import sys
import os

CHALLENGES = [
    ("01_async", "test_async.py"),
    ("02_sql", "test_sql.py"),
    ("03_regex", "test_regex.py"),
    ("04_sort", "test_sort.py"),
    ("05_ratelimit", "test_ratelimit.py"),
    ("06_logparse", "test_logparse.py"),
    ("07_memleak", "test_memleak.py"),
    ("08_cache", "test_cache.py"),
    ("09_migration", "test_migration.py"),
    ("10_stream", "test_stream.py"),
]

REQUIRED_PASS = 9
FLAG = "CTF{gauntlet_sprint_9_of_10_complete}"


def run_challenge(base_dir, challenge_dir, test_file):
    """Run a single challenge's test suite. Returns True if all tests pass."""
    challenge_path = os.path.join(base_dir, "gauntlet", challenge_dir)
    test_path = os.path.join(challenge_path, test_file)

    if not os.path.exists(test_path):
        return False, "Test file not found"

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", test_file, "-v", "--tb=short", "-q"],
            cwd=challenge_path,
            capture_output=True,
            text=True,
            timeout=120,
        )
        passed = result.returncode == 0
        output = result.stdout + result.stderr
        return passed, output
    except subprocess.TimeoutExpired:
        return False, "TIMEOUT (120s)"
    except Exception as e:
        return False, str(e)


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    results = []
    passed_count = 0

    print("=" * 60)
    print("       THE GAUNTLET SPRINT — 10 Challenges")
    print("=" * 60)
    print()

    for i, (challenge_dir, test_file) in enumerate(CHALLENGES, 1):
        label = challenge_dir.replace("_", " ").upper()
        print(f"[{i:2d}/10] {label} ", end="", flush=True)

        passed, output = run_challenge(base_dir, challenge_dir, test_file)
        results.append((challenge_dir, passed, output))

        if passed:
            passed_count += 1
            print("PASS")
        else:
            print("FAIL")

    print()
    print("=" * 60)
    print(f"  RESULTS: {passed_count}/{len(CHALLENGES)} challenges passed")
    print("=" * 60)
    print()

    for challenge_dir, passed, _ in results:
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {challenge_dir}")

    print()

    if passed_count >= REQUIRED_PASS:
        print(f"  FLAG: {FLAG}")
        print()
        print("  Congratulations! You've conquered the Gauntlet!")
    else:
        remaining = REQUIRED_PASS - passed_count
        print(f"  You need {remaining} more passing challenge(s).")
        print(f"  Minimum required: {REQUIRED_PASS}/{len(CHALLENGES)}")

    print()
    return 0 if passed_count >= REQUIRED_PASS else 1


if __name__ == "__main__":
    sys.exit(main())
