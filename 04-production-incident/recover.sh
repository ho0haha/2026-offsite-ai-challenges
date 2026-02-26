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

# Step 1: Verify the fix pattern exists in server.py
echo "[1/3] Checking server.py for proper connection cleanup..."
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
    echo "       The connection leak in handle_request() must be fixed"
    echo "       by releasing connections in a finally block."
    echo ""
    echo "=============================================="
    exit 1
fi

echo "[2/3] Fix pattern verified. Running health check..."
echo ""

# Step 2: Run the health check
cd "$SCRIPT_DIR"
if python healthcheck.py; then
    echo ""
    echo "[3/3] Health check passed!"
    echo ""
    echo "=============================================="
    echo ""
    echo "  RECOVERY SUCCESSFUL!"
    echo ""
    echo "  Root cause: Connection leak in handle_request()"
    echo "  Fix: Added try/finally with release_connection()"
    echo ""
    echo "  FLAG{production_incident_r00t_caus3}"
    echo ""
    echo "=============================================="
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
