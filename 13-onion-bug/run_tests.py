#!/usr/bin/env python3
"""
Onion Bug Challenge - Sequential Test Runner
=============================================

Runs 7 test groups in sequence. Each group only runs if the previous
group passed. When all 7 pass, the flag is revealed.

Usage:
    python run_tests.py
"""

import sys
import unittest
import io

from test_onion import TEST_GROUPS


FLAG = "CTF{onion_layers_peeled_7_deep}"

BANNER = r"""
   ___       _               ____
  / _ \ _ _ (_) ___  _ __   | __ ) _   _  __ _
 | | | | '_ \| / _ \| '_ \  |  _ \| | | |/ _` |
 | |_| | | | | | (_) | | | | | |_) | |_| | (_| |
  \___/|_| |_|_|\___/|_| |_| |____/ \__,_|\__, |
                                           |___/
  The Golden Fork Restaurant - Order System Debugger
  ==================================================
  Peel back 7 layers of bugs. Each fix reveals the next.
"""


def run_group(name: str, test_class: type) -> bool:
    """Run a test group and return True if all tests passed."""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(test_class)

    # Capture output
    stream = io.StringIO()
    runner = unittest.TextTestRunner(stream=stream, verbosity=2)
    result = runner.run(suite)

    passed = result.wasSuccessful()

    return passed, stream.getvalue(), result


def main():
    print(BANNER)

    total_groups = len(TEST_GROUPS)
    passed_groups = 0

    for i, (name, test_class) in enumerate(TEST_GROUPS, 1):
        print(f"\n{'='*60}")
        print(f"  LAYER {i}/{total_groups}: {name}")
        print(f"{'='*60}")

        passed, output, result = run_group(name, test_class)

        # Print test output
        for line in output.strip().split("\n"):
            print(f"  {line}")

        tests_run = result.testsRun
        failures = len(result.failures)
        errors = len(result.errors)

        if passed:
            passed_groups += 1
            print(f"\n  [PASS] Layer {i} - All {tests_run} tests passed!")
            print(f"  Progress: [{passed_groups}/{total_groups}] layers peeled")
        else:
            print(f"\n  [FAIL] Layer {i} - {failures} failure(s), {errors} error(s)")
            print(f"  Progress: [{passed_groups}/{total_groups}] layers peeled")

            # Show failure details
            if result.failures:
                print(f"\n  --- Failure Details ---")
                for test, traceback in result.failures:
                    print(f"\n  Test: {test}")
                    for tb_line in traceback.strip().split("\n"):
                        print(f"    {tb_line}")

            if result.errors:
                print(f"\n  --- Error Details ---")
                for test, traceback in result.errors:
                    print(f"\n  Test: {test}")
                    for tb_line in traceback.strip().split("\n"):
                        print(f"    {tb_line}")

            print(f"\n  Fix the bugs in Layer {i} before proceeding to Layer {i+1}.")
            print(f"  Hint: Read the test names and error messages carefully.")
            print(f"\n{'='*60}")
            print(f"  STOPPED at Layer {i}. Fix this layer and re-run.")
            print(f"{'='*60}")
            sys.exit(1)

    # All layers passed!
    print(f"\n{'='*60}")
    print(f"  ALL {total_groups} LAYERS PEELED!")
    print(f"{'='*60}")
    print(f"""
  Congratulations! You've debugged all 7 layers of the
  Golden Fork Restaurant order processing system.

  Each bug was hidden beneath the previous one:
    Layer 1: Return type mismatch (string vs OrderResult)
    Layer 2: Off-by-one in discount tier boundaries
    Layer 3: Missing null check on optional field
    Layer 4: Tax-exempt items double-taxed after discount fix
    Layer 5: Unbounded recursion in modifier flattening
    Layer 6: TOCTOU race condition in inventory
    Layer 7: String format conflict with curly braces

  FLAG: {FLAG}
""")
    print(f"{'='*60}")
    sys.exit(0)


if __name__ == "__main__":
    main()
