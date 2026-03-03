#!/usr/bin/env python3
"""
Fuzz Gauntlet — Test Runner
============================
Runs the Hypothesis property-based test suite against your functions.py
implementation. Prints the flag when all tests pass.

Usage:
    python run_fuzz.py
"""

import subprocess
import sys
import os

FLAG = "CTF{fuzz_tested_and_bulletproof}"


def main():
    print("=" * 60)
    print("       THE FUZZ GAUNTLET")
    print("  Property-Based Testing with Hypothesis")
    print("=" * 60)
    print()
    print("Running 10,000+ random inputs per function...")
    print("This may take several minutes.")
    print()

    test_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_fuzz.py")

    result = subprocess.run(
        [sys.executable, "-m", "pytest", test_file, "-v", "--tb=short"],
        cwd=os.path.dirname(os.path.abspath(__file__)),
    )

    print()
    print("=" * 60)

    if result.returncode == 0:
        print("  ALL PROPERTY TESTS PASSED!")
        print()
        print("  Your implementations survived 10,000+ random inputs each.")
        print("  Edge cases, adversarial inputs, boundary conditions — all handled.")
        print()
        print(f"  FLAG: {FLAG}")
    else:
        print("  SOME TESTS FAILED")
        print()
        print("  Review the failures above. Hypothesis will show you the")
        print("  minimal failing example for each broken property.")
        print()
        print("  Tips:")
        print("  - Read the property name to understand what invariant broke")
        print("  - The 'Falsifying example' shows the exact input that failed")
        print("  - Think about edge cases: NaN, Inf, empty, negative, unicode")

    print("=" * 60)
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
