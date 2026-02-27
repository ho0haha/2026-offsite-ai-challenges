#!/bin/bash
#
# Recovery validation script for Challenge 4: Production Incident
# DO NOT MODIFY THIS FILE
#
# This script verifies that the root cause has been fixed and runs
# the health check to confirm the system is operational.

set -e

echo "=============================================="
echo "  RECOVERY VALIDATION SCRIPT"
echo "=============================================="
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVER_FILE="$SCRIPT_DIR/app/server.py"
HEALTHCHECK="$SCRIPT_DIR/healthcheck.py"

# Detect Python command (test that it actually runs, not just exists)
if python3 --version &>/dev/null 2>&1; then
    PYTHON=python3
elif python --version &>/dev/null 2>&1; then
    PYTHON=python
elif py --version &>/dev/null 2>&1; then
    PYTHON=py
else
    echo "[FAIL] Python not found. Please install Python 3."
    exit 1
fi

# Step 1: Verify the fix pattern exists in server.py
echo "[1/4] Checking server.py for proper connection cleanup..."
echo ""

HAS_FINALLY=false
HAS_RELEASE=false

if grep -q "finally" "$SERVER_FILE"; then
    HAS_FINALLY=true
    echo "  [PASS] Found 'finally' block in server.py"
else
    echo "  [FAIL] No 'finally' block found in server.py"
    echo "         Connections must be released in a finally block"
    echo "         to ensure cleanup on both success and error paths."
fi

if grep -q "release_connection" "$SERVER_FILE"; then
    HAS_RELEASE=true
    echo "  [PASS] Found 'release_connection' call in server.py"
else
    echo "  [FAIL] No 'release_connection' call found in server.py"
    echo "         Connections must be released back to the pool."
fi

echo ""

if [ "$HAS_FINALLY" = false ] || [ "$HAS_RELEASE" = false ]; then
    echo "[FAIL] Fix validation failed."
    echo "       The connection leak must be fixed by releasing"
    echo "       connections in a finally block."
    echo ""
    echo "=============================================="
    exit 1
fi

# Step 2: Verify all get_connection calls are protected by finally blocks
echo "[2/4] Checking that all connections are protected by finally blocks..."
echo ""

FINALLY_COUNT=$(grep -c "finally" "$SERVER_FILE")
GET_CONN_COUNT=$(grep -c "get_connection" "$SERVER_FILE")

if [ "$FINALLY_COUNT" -lt "$GET_CONN_COUNT" ]; then
    echo "  [FAIL] Not all get_connection() calls are protected by finally blocks"
    echo "         Found $GET_CONN_COUNT get_connection() calls but only $FINALLY_COUNT finally blocks"
    echo "         Every connection acquisition must have a corresponding finally block."
    echo ""
    echo "=============================================="
    exit 1
else
    echo "  [PASS] All get_connection() calls appear to be protected ($FINALLY_COUNT finally, $GET_CONN_COUNT get_connection)"
fi

echo ""
echo "[3/4] Fix pattern verified. Running health check..."
echo ""

# Step 3: Run the health check
cd "$SCRIPT_DIR"
if $PYTHON healthcheck.py; then
    echo ""
    echo "[4/4] Health check passed!"
    echo ""
    echo "=============================================="
    echo ""
    echo "  RECOVERY SUCCESSFUL!"
    echo ""
    echo "  Root cause: Connection leak in _validate_order()"
    echo "  Fix: Added try/finally to ensure release_connection()"
    echo "       is called on all code paths."
    echo ""
    echo "=============================================="
    $PYTHON "$SCRIPT_DIR/../ctf_helper.py" 4 app/server.py
    exit 0
else
    echo ""
    echo "[FAIL] Health check still failing."
    echo "       Your fix may be incomplete. Make sure connections"
    echo "       are released in ALL code paths (success and error)."
    echo ""
    echo "=============================================="
    exit 1
fi
