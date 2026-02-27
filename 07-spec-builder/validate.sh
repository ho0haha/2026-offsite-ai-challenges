#!/bin/bash
# Validation script for Challenge 7: Spec Builder + Build
# Runs PRD validator and implementation tests, prints flag if both pass.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "============================================================"
echo "  Challenge 7: Spec Builder + Build — Validation"
echo "============================================================"
echo ""

# Phase 1: Validate the PRD
echo "--- Phase 1: PRD Validation ---"
echo ""

if [ ! -f "prd.md" ]; then
    echo "FAIL: prd.md not found. Create your PRD first."
    echo ""
    echo "Phase 1 FAILED"
    exit 1
fi

if python prd_validator.py prd.md; then
    echo ""
    echo "Phase 1 PASSED"
else
    echo ""
    echo "Phase 1 FAILED — fix your PRD and try again."
    exit 1
fi

echo ""
echo "--- Phase 2: Implementation Tests ---"
echo ""

if python -m pytest test_implementation.py -v; then
    echo ""
    echo "Phase 2 PASSED"
else
    echo ""
    echo "Phase 2 FAILED — fix your implementation and try again."
    exit 1
fi

echo ""
echo "============================================================"
echo "  BOTH PHASES PASSED!"
echo "============================================================"

python "$SCRIPT_DIR/../ctf_helper.py" 7 prd.md
