#!/bin/bash
# Run tests with coverage and check for 90%+ threshold

set -e

echo "Running tests with coverage..."
echo ""

# Run pytest with coverage, capture output
OUTPUT=$(python -m pytest test_inventory.py --cov=inventory --cov-report=term -q 2>&1) || true

echo "$OUTPUT"
echo ""

# Extract coverage percentage from the TOTAL line
COVERAGE=$(echo "$OUTPUT" | grep -oP 'TOTAL\s+\d+\s+\d+\s+(\d+)%' | grep -oP '\d+%' | tr -d '%')

if [ -z "$COVERAGE" ]; then
    echo "Could not determine coverage percentage."
    echo "Make sure test_inventory.py exists and tests run successfully."
    exit 1
fi

echo ""
echo "============================================"
if [ "$COVERAGE" -ge 90 ]; then
    echo "Coverage: ${COVERAGE}% (>= 90%)"
    echo ""
    echo "FLAG{test_factory_90_percent_c0v3rag3}"
else
    echo "Coverage: ${COVERAGE}% - Need 90%+ coverage"
    echo "Keep writing tests!"
fi
echo "============================================"
