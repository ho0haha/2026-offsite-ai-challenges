#!/usr/bin/env python3
"""
Validator for Challenge 11: Prompt Craftsman.
Checks all 5 output files for required content elements.
All 5 must pass to print the flag.
"""

import os
import sys
import re

OUTPUTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "outputs")


def read_output(filename):
    """Read an output file and return its contents, or None if missing."""
    path = os.path.join(OUTPUTS_DIR, filename)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def count_code_blocks(text):
    """Count the number of code block markers (```) in the text."""
    return text.count("```")


def word_count(text):
    """Count words in text."""
    return len(text.split())


def validate_challenge1():
    """Validate output1.md — Docstring Generator."""
    content = read_output("output1.md")
    if content is None:
        return False, "output1.md not found"

    errors = []
    content_lower = content.lower()

    # Must have Args or Parameters section
    if "args" not in content_lower and "parameters" not in content_lower:
        errors.append("Missing 'Args' or 'Parameters' section")

    # Must have Returns section
    if "returns" not in content_lower and "return" not in content_lower:
        errors.append("Missing 'Returns' section")

    # Must have at least 2 code blocks (for examples)
    code_blocks = count_code_blocks(content)
    if code_blocks < 4:  # 2 code blocks = 4 ``` markers (open + close each)
        errors.append(f"Need at least 2 code blocks (found {code_blocks // 2})")

    # Must have Raises or Exceptions
    if "raises" not in content_lower and "exceptions" not in content_lower:
        errors.append("Missing 'Raises' or 'Exceptions' section")

    # Must mention all 6 parameters
    params = [
        "transactions",
        "currency_rates",
        "base_currency",
        "filters",
        "include_metadata",
        "max_retries",
    ]
    for param in params:
        if param not in content:
            errors.append(f"Missing parameter: {param}")

    # Must mention ValueError and KeyError
    if "ValueError" not in content:
        errors.append("Missing 'ValueError'")
    if "KeyError" not in content:
        errors.append("Missing 'KeyError'")

    if errors:
        return False, "; ".join(errors)
    return True, "PASS"


def validate_challenge2():
    """Validate output2.md — Bug Pattern Finder."""
    content = read_output("output2.md")
    if content is None:
        return False, "output2.md not found"

    errors = []
    content_lower = content.lower()

    # Must mention all 3 function names
    functions = [
        "calculate_average_score",
        "find_longest_streak",
        "merge_user_profiles",
    ]
    for func in functions:
        if func not in content:
            errors.append(f"Missing function name: {func}")

    # Must mention None or null (the bug pattern)
    if "none" not in content_lower and "null" not in content_lower:
        errors.append("Missing mention of 'None' or 'null' (the bug)")

    # Must have a fix/solution
    if (
        "fix" not in content_lower
        and "solution" not in content_lower
        and "corrected" not in content_lower
    ):
        errors.append("Missing 'fix', 'solution', or 'corrected'")

    if errors:
        return False, "; ".join(errors)
    return True, "PASS"


def validate_challenge3():
    """Validate output3.md — Optimization Advisor."""
    content = read_output("output3.md")
    if content is None:
        return False, "output3.md not found"

    errors = []
    content_lower = content.lower()

    # Must have at least 2 code blocks
    code_blocks = count_code_blocks(content)
    if code_blocks < 4:
        errors.append(f"Need at least 2 code blocks (found {code_blocks // 2})")

    # Must mention complexity
    if "O(n" not in content and "O(N" not in content:
        errors.append("Missing complexity notation (e.g., 'O(n')")

    # Must have before and after
    if "before" not in content_lower:
        errors.append("Missing 'before'")
    if "after" not in content_lower:
        errors.append("Missing 'after'")

    if errors:
        return False, "; ".join(errors)
    return True, "PASS"


def validate_challenge4():
    """Validate output4.md — Complexity Explainer."""
    content = read_output("output4.md")
    if content is None:
        return False, "output4.md not found"

    errors = []
    content_lower = content.lower()

    # Must have Big-O notation
    if "O(" not in content:
        errors.append("Missing Big-O notation")

    # Must have analogy or analogical explanation
    if "analog" not in content_lower and "like" not in content_lower and "imagine" not in content_lower:
        errors.append("Missing analogy (expected 'analogy', 'like', or 'imagine')")

    # Must mention log
    if "log" not in content_lower:
        errors.append("Missing 'log' (logarithmic)")

    # Must be at least 100 words
    wc = word_count(content)
    if wc < 100:
        errors.append(f"Too short ({wc} words, need at least 100)")

    if errors:
        return False, "; ".join(errors)
    return True, "PASS"


def validate_challenge5():
    """Validate output5.md — Migration Planner."""
    content = read_output("output5.md")
    if content is None:
        return False, "output5.md not found"

    errors = []
    content_lower = content.lower()

    # Must mention step
    if "step" not in content_lower:
        errors.append("Missing 'step' (step-by-step plan)")

    # Must mention rollback or revert
    if "rollback" not in content_lower and "revert" not in content_lower:
        errors.append("Missing 'rollback' or 'revert'")

    # Must mention backwards/backward compatible
    if (
        "backwards compatible" not in content_lower
        and "backward compatible" not in content_lower
        and "backward-compatible" not in content_lower
        and "backwards-compatible" not in content_lower
    ):
        errors.append("Missing 'backwards compatible' or 'backward compatible'")

    # Must discuss data migration
    if "data" not in content_lower:
        errors.append("Missing 'data' (data migration discussion)")
    if "migration" not in content_lower and "migrate" not in content_lower:
        errors.append("Missing 'migration' or 'migrate'")

    # Must be at least 200 words
    wc = word_count(content)
    if wc < 200:
        errors.append(f"Too short ({wc} words, need at least 200)")

    if errors:
        return False, "; ".join(errors)
    return True, "PASS"


def main():
    validators = [
        ("Challenge 1: Docstring Generator", validate_challenge1),
        ("Challenge 2: Bug Pattern Finder", validate_challenge2),
        ("Challenge 3: Optimization Advisor", validate_challenge3),
        ("Challenge 4: Complexity Explainer", validate_challenge4),
        ("Challenge 5: Migration Planner", validate_challenge5),
    ]

    print("=" * 60)
    print("  Prompt Craftsman - Validation Results")
    print("=" * 60)
    print()

    all_passed = True
    for name, validator in validators:
        passed, message = validator()
        status = "PASS" if passed else "FAIL"
        icon = "[+]" if passed else "[-]"
        print(f"  {icon} {name}: {status}")
        if not passed:
            all_passed = False
            print(f"      Reason: {message}")

    print()
    print("-" * 60)

    if all_passed:
        print()
        print("  All 5 challenges passed!")
        print()
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
        import ctf_helper
        ctf_helper.submit(11, [
            "outputs/output1.md",
            "outputs/output2.md",
            "outputs/output3.md",
            "outputs/output4.md",
            "outputs/output5.md",
        ])
    else:
        print()
        print("  Not all challenges passed. Keep working!")
        print()

    print("=" * 60)
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
