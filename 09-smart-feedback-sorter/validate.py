#!/usr/bin/env python3
"""
Validator for Challenge 9: Smart Feedback Sorter

Reads output.csv (participant-generated) and compares against ground_truth.json.
Both category AND sentiment must match for an entry to count as correct.
Requires >= 85% accuracy to earn the flag.
"""

import csv
import json
import os
import sys

GROUND_TRUTH_FILE = "ground_truth.json"
OUTPUT_FILE = "output.csv"
REQUIRED_ACCURACY = 0.85
FLAG = "FLAG{smart_sorter_85_percent_acc}"

VALID_CATEGORIES = {"service", "food_quality", "wait_time", "cleanliness", "other"}
VALID_SENTIMENTS = {"positive", "negative"}


def load_ground_truth(path: str) -> dict:
    """Load the ground truth JSON file."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"ERROR: Ground truth file not found: {path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in ground truth file: {e}")
        sys.exit(1)


def load_output(path: str) -> dict:
    """Load the participant's output CSV file."""
    if not os.path.exists(path):
        print(f"ERROR: Output file not found: {path}")
        print(f"Run your sorter script first to generate {path}")
        sys.exit(1)

    results = {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            # Verify required columns exist
            if reader.fieldnames is None:
                print("ERROR: output.csv appears to be empty or missing a header row.")
                sys.exit(1)

            fieldnames_lower = [fn.lower().strip() for fn in reader.fieldnames]
            required = {"id", "category", "sentiment"}
            if not required.issubset(set(fieldnames_lower)):
                missing = required - set(fieldnames_lower)
                print(f"ERROR: output.csv is missing columns: {missing}")
                print(f"Found columns: {reader.fieldnames}")
                sys.exit(1)

            # Build a normalized fieldname mapping
            field_map = {}
            for fn in reader.fieldnames:
                field_map[fn.lower().strip()] = fn

            for row in reader:
                entry_id = row[field_map["id"]].strip()
                category = row[field_map["category"]].strip().lower()
                sentiment = row[field_map["sentiment"]].strip().lower()
                results[entry_id] = {"category": category, "sentiment": sentiment}

    except Exception as e:
        print(f"ERROR: Could not read output.csv: {e}")
        sys.exit(1)

    return results


def validate():
    """Compare output against ground truth and report results."""
    # Resolve paths relative to the script's directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    gt_path = os.path.join(script_dir, GROUND_TRUTH_FILE)
    out_path = os.path.join(script_dir, OUTPUT_FILE)

    ground_truth = load_ground_truth(gt_path)
    output = load_output(out_path)

    print("=" * 65)
    print("  Smart Feedback Sorter — Validation")
    print("=" * 65)
    print()

    total = len(ground_truth)
    correct = 0
    mismatches = []
    missing_ids = []
    invalid_entries = []

    for entry_id, expected in sorted(ground_truth.items(), key=lambda x: int(x[0])):
        if entry_id not in output:
            missing_ids.append(entry_id)
            continue

        actual = output[entry_id]

        # Validate category and sentiment values
        if actual["category"] not in VALID_CATEGORIES:
            invalid_entries.append(
                f"  ID {entry_id}: invalid category '{actual['category']}' "
                f"(must be one of: {', '.join(sorted(VALID_CATEGORIES))})"
            )
            continue

        if actual["sentiment"] not in VALID_SENTIMENTS:
            invalid_entries.append(
                f"  ID {entry_id}: invalid sentiment '{actual['sentiment']}' "
                f"(must be one of: {', '.join(sorted(VALID_SENTIMENTS))})"
            )
            continue

        # Check match
        cat_match = actual["category"] == expected["category"]
        sent_match = actual["sentiment"] == expected["sentiment"]

        if cat_match and sent_match:
            correct += 1
        else:
            mismatch_detail = f"  ID {entry_id:>2}: "
            if not cat_match:
                mismatch_detail += f"category: got '{actual['category']}', expected '{expected['category']}'"
            if not cat_match and not sent_match:
                mismatch_detail += " | "
            if not sent_match:
                mismatch_detail += f"sentiment: got '{actual['sentiment']}', expected '{expected['sentiment']}'"
            mismatches.append(mismatch_detail)

    # Report missing IDs
    if missing_ids:
        print(f"  WARNING: {len(missing_ids)} entries missing from output.csv:")
        for mid in missing_ids:
            print(f"    - ID {mid}")
        print()

    # Report invalid entries
    if invalid_entries:
        print(f"  WARNING: {len(invalid_entries)} entries have invalid values:")
        for inv in invalid_entries:
            print(inv)
        print()

    # Calculate accuracy
    accuracy = correct / total if total > 0 else 0.0
    pct = accuracy * 100

    print(f"  Correct: {correct}/{total} ({pct:.1f}%)")
    print(f"  Required: {REQUIRED_ACCURACY * 100:.0f}%")
    print()

    if mismatches:
        print(f"  Mismatches ({len(mismatches)}):")
        for m in mismatches:
            print(m)
        print()

    print("=" * 65)

    if accuracy >= REQUIRED_ACCURACY:
        print()
        print(f"  {FLAG}")
        print()
    else:
        print()
        print(f"  Accuracy {pct:.1f}% is below the {REQUIRED_ACCURACY * 100:.0f}% threshold.")
        print("  Review the mismatches above and refine your classification prompts.")
        print()


if __name__ == "__main__":
    validate()
