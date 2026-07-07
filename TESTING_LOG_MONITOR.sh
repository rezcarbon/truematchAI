#!/bin/bash
# TrueMatch Backend Real-Time Log Monitor
# Usage: chmod +x TESTING_LOG_MONITOR.sh && ./TESTING_LOG_MONITOR.sh

set -e

LOG_FILE="/tmp/truematch-backend-network.log"
COLORS=(
  "\033[0;32m"    # Green - success
  "\033[0;31m"    # Red - error
  "\033[0;33m"    # Yellow - warning
  "\033[0;34m"    # Blue - info
  "\033[0m"       # Reset
)

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "   TrueMatch Backend Log Monitor"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 Log File: $LOG_FILE"
echo "📍 Backend: http://192.168.1.15:8000"
echo ""
echo "🔍 Monitoring for:"
echo "   ✓ Authentication (login/logout)"
echo "   ✓ Resume uploads"
echo "   ✓ Assessment creation"
echo "   ✓ Governance gate results"
echo "   ✓ API errors and timeouts"
echo ""
echo "Press Ctrl+C to stop"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if log file exists
if [ ! -f "$LOG_FILE" ]; then
    echo "⚠️  Log file not found. Backend may not be running."
    echo "Start backend with:"
    echo "  cd ~/Documents/codebase/truematch"
    echo "  source venv/bin/activate"
    echo "  python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > $LOG_FILE 2>&1 &"
    exit 1
fi

# Color-coded real-time monitoring
tail -f "$LOG_FILE" | while IFS= read -r line; do
    # Check for authentication
    if echo "$line" | grep -qi "auth/login"; then
        if echo "$line" | grep -qi "200\|201"; then
            echo -e "${COLORS[0]}✅ LOGIN SUCCESS${COLORS[4]} $line"
        elif echo "$line" | grep -qi "401\|403"; then
            echo -e "${COLORS[1]}❌ LOGIN FAILED${COLORS[4]} $line"
        else
            echo -e "${COLORS[3]}🔐 LOGIN REQUEST${COLORS[4]} $line"
        fi

    # Check for assessment creation
    elif echo "$line" | grep -qi "assessments"; then
        if echo "$line" | grep -qi "200\|201"; then
            echo -e "${COLORS[0]}✅ ASSESSMENT SUCCESS${COLORS[4]} $line"
        elif echo "$line" | grep -qi "error\|failed"; then
            echo -e "${COLORS[1]}❌ ASSESSMENT FAILED${COLORS[4]} $line"
        else
            echo -e "${COLORS[3]}📊 ASSESSMENT REQUEST${COLORS[4]} $line"
        fi

    # Check for resume operations
    elif echo "$line" | grep -qi "resume"; then
        if echo "$line" | grep -qi "200\|201"; then
            echo -e "${COLORS[0]}✅ RESUME SUCCESS${COLORS[4]} $line"
        elif echo "$line" | grep -qi "error"; then
            echo -e "${COLORS[1]}❌ RESUME ERROR${COLORS[4]} $line"
        else
            echo -e "${COLORS[3]}📄 RESUME REQUEST${COLORS[4]} $line"
        fi

    # Check for errors
    elif echo "$line" | grep -qi "error\|exception\|failed\|500\|503"; then
        echo -e "${COLORS[1]}🚨 ERROR${COLORS[4]} $line"

    # Check for warnings
    elif echo "$line" | grep -qi "warning\|warn\|deprecated"; then
        echo -e "${COLORS[2]}⚠️  WARNING${COLORS[4]} $line"

    # Check for governance
    elif echo "$line" | grep -qi "governance\|fidelity\|coherence\|consistency"; then
        echo -e "${COLORS[0]}🛡️  GOVERNANCE${COLORS[4]} $line"

    # Default info
    else
        echo -e "${COLORS[3]}ℹ️  $line${COLORS[4]}"
    fi
done
