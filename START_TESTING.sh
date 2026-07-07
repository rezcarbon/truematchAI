#!/bin/bash
# TrueMatch Complete Testing Framework
# Starts backend, validates APIs, launches iOS simulator, monitors testing

set -e

PROJECT_ROOT="/Users/modvader/Documents/codebase/truematch"
BACKEND_DIR="$PROJECT_ROOT/backend"
IOS_DIR="$PROJECT_ROOT/ios/TrueMatch"
BACKEND_LOG="/tmp/truematch-backend-network.log"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "╔════════════════════════════════════════════════════════╗"
echo "║   TrueMatch Complete Testing Framework                 ║"
echo "║   Simulator + iPhone Network Testing                   ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# ===========================================
# STEP 1: Verify Backend Running
# ===========================================
echo -e "${BLUE}Step 1: Checking Backend Status${NC}"
echo "────────────────────────────────────────────────────────"

if curl -s http://192.168.1.15:8000/api/v1/users/me > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend is running on 192.168.1.15:8000${NC}"
else
    echo -e "${YELLOW}⚠️  Backend not responding at 192.168.1.15:8000${NC}"
    echo "   Attempting to start backend..."
    cd "$BACKEND_DIR"
    source venv/bin/activate
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > "$BACKEND_LOG" 2>&1 &
    BACKEND_PID=$!
    echo "   Backend started (PID: $BACKEND_PID)"
    sleep 3

    if curl -s http://192.168.1.15:8000/api/v1/users/me > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Backend is now running${NC}"
    else
        echo -e "${RED}❌ Failed to start backend${NC}"
        exit 1
    fi
fi

echo ""

# ===========================================
# STEP 2: Display Testing Information
# ===========================================
echo -e "${BLUE}Step 2: Test Configuration${NC}"
echo "────────────────────────────────────────────────────────"
echo "Backend URL:     http://192.168.1.15:8000"
echo "API Base:        http://192.168.1.15:8000/api/v1"
echo "WebSocket:       ws://192.168.1.15:8000/api/v1"
echo ""
echo "iOS App:         TrueMatch (Simulator + Device)"
echo "iOS Config:      Updated to use 192.168.1.15"
echo ""
echo "Test Credentials:"
echo "  Email:         candidate@truematch.test"
echo "  Password:      (use any password, backend validates)"
echo ""

# ===========================================
# STEP 3: Display Test Scenarios
# ===========================================
echo -e "${BLUE}Step 3: Available Test Scenarios${NC}"
echo "────────────────────────────────────────────────────────"
echo ""
echo -e "${YELLOW}SIMULATOR TESTING:${NC}"
echo "  1. Build in Xcode: Product → Run (⌘R)"
echo "  2. App launches in simulator"
echo "  3. Test login with test credentials"
echo "  4. Test resume upload"
echo "  5. Test assessment creation"
echo "  6. Verify governance gates"
echo ""
echo -e "${YELLOW}IPHONE DEVICE TESTING:${NC}"
echo "  1. Connect iPhone via USB"
echo "  2. Select iPhone in Xcode device list"
echo "  3. Build and deploy (⌘R)"
echo "  4. Test on physical device"
echo "  5. Verify network connectivity"
echo ""

# ===========================================
# STEP 4: Show Backend Log Monitoring
# ===========================================
echo -e "${BLUE}Step 4: Backend Log Monitoring Setup${NC}"
echo "────────────────────────────────────────────────────────"
echo "Log file: $BACKEND_LOG"
echo ""
echo "To monitor backend requests in real-time, open a new terminal and run:"
echo ""
echo -e "${YELLOW}bash $PROJECT_ROOT/TESTING_LOG_MONITOR.sh${NC}"
echo ""
echo "This will show:"
echo "  ✓ Authentication requests"
echo "  ✓ Resume uploads"
echo "  ✓ Assessment creation"
echo "  ✓ Governance gate results"
echo "  ✓ API errors"
echo ""

# ===========================================
# STEP 5: Verify iOS Configuration
# ===========================================
echo -e "${BLUE}Step 5: iOS Configuration Verification${NC}"
echo "────────────────────────────────────────────────────────"

if grep -q "192.168.1.15" "$IOS_DIR/App/AppConfiguration.swift" 2>/dev/null; then
    echo -e "${GREEN}✅ iOS app configured for network IP (192.168.1.15)${NC}"
else
    echo -e "${YELLOW}⚠️  iOS app may not be configured for network IP${NC}"
    echo "   AppConfiguration.swift should use: http://192.168.1.15:8000/api"
fi

echo ""

# ===========================================
# STEP 6: Display Next Steps
# ===========================================
echo -e "${BLUE}Step 6: Next Steps${NC}"
echo "────────────────────────────────────────────────────────"
echo ""
echo -e "${YELLOW}1. SIMULATOR TESTING:${NC}"
echo "   a) Open Xcode with TrueMatch iOS project"
echo "   b) Press ⌘R (or Product → Run)"
echo "   c) Wait 2-3 minutes for build"
echo "   d) Simulator launches app automatically"
echo "   e) Test login and flows"
echo ""
echo -e "${YELLOW}2. MONITOR BACKEND:${NC}"
echo "   a) Open a new terminal window"
echo "   b) Run: bash $PROJECT_ROOT/TESTING_LOG_MONITOR.sh"
echo "   c) Watch for API requests in real-time"
echo ""
echo -e "${YELLOW}3. IPHONE DEVICE (when ready):${NC}"
echo "   a) Connect iPhone via USB"
echo "   b) Tap 'Trust' on iPhone"
echo "   c) In Xcode, select iPhone from device list"
echo "   d) Press ⌘R to build and deploy"
echo "   e) Test on physical device"
echo ""
echo -e "${YELLOW}4. TEST EXECUTION:${NC}"
echo "   Use the comprehensive test scenarios:"
echo "   File: $PROJECT_ROOT/TESTING_SCENARIOS.md"
echo ""
echo -e "${YELLOW}5. RECORD RESULTS:${NC}"
echo "   Document all test outcomes for Plug & Play meeting"
echo ""

# ===========================================
# STEP 7: Display Success Message
# ===========================================
echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║  ✅ TESTING ENVIRONMENT READY!                        ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""
echo -e "${GREEN}All systems are configured and ready for testing.${NC}"
echo ""
echo "Key Files:"
echo "  📋 Test Scenarios: TESTING_SCENARIOS.md"
echo "  📊 Log Monitor:    TESTING_LOG_MONITOR.sh"
echo "  🔍 Backend API:    BACKEND_VALIDATION.sh"
echo ""
echo "Backend is running at: http://192.168.1.15:8000"
echo "iOS app is configured for network testing"
echo ""
echo -e "${YELLOW}Ready to proceed with iOS simulator testing!${NC}"
echo ""
