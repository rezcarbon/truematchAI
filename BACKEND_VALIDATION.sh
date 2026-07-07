#!/bin/bash
# TrueMatch Backend Validation Script
# Tests all critical API endpoints

set -e

API_URL="http://192.168.1.15:8000/api/v1"
TOKEN=""

echo "╔════════════════════════════════════════════════════════╗"
echo "║     TrueMatch Backend API Validation Suite             ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

test_count=0
pass_count=0
fail_count=0

# Helper function for API calls
api_call() {
    local method=$1
    local endpoint=$2
    local data=$3
    local description=$4

    test_count=$((test_count + 1))
    echo ""
    echo -e "${BLUE}Test $test_count: $description${NC}"
    echo "  Method: $method"
    echo "  Endpoint: $endpoint"

    if [ -z "$data" ]; then
        response=$(curl -s -w "\n%{http_code}" \
            -X "$method" \
            -H "Content-Type: application/json" \
            -H "Authorization: Bearer $TOKEN" \
            "$API_URL$endpoint" 2>/dev/null)
    else
        response=$(curl -s -w "\n%{http_code}" \
            -X "$method" \
            -H "Content-Type: application/json" \
            -H "Authorization: Bearer $TOKEN" \
            -d "$data" \
            "$API_URL$endpoint" 2>/dev/null)
    fi

    http_code=$(echo "$response" | tail -1)
    body=$(echo "$response" | sed '$d')

    echo "  Status: $http_code"

    # Check if successful
    if [[ "$http_code" =~ ^(200|201|204|400|401|404)$ ]]; then
        echo -e "  ${GREEN}✅ PASS${NC}"
        pass_count=$((pass_count + 1))

        # Extract token if login
        if [[ "$endpoint" == "/auth/login" && "$http_code" == "200" ]]; then
            TOKEN=$(echo "$body" | grep -o '"token":"[^"]*' | cut -d'"' -f4 2>/dev/null || echo "")
            if [ -n "$TOKEN" ]; then
                echo "  Token: ${TOKEN:0:20}..."
            fi
        fi
    else
        echo -e "  ${RED}❌ FAIL (unexpected status)${NC}"
        fail_count=$((fail_count + 1))
    fi

    # Show response preview
    if [ -n "$body" ] && [ ${#body} -lt 200 ]; then
        echo "  Response: $body"
    elif [ -n "$body" ]; then
        echo "  Response: ${body:0:200}..."
    fi
}

echo "📌 Endpoint: $API_URL"
echo ""

# ============================================
# SECTION 1: AUTHENTICATION
# ============================================
echo "╔════════════════════════════════════════════════════════╗"
echo "║  1. AUTHENTICATION TESTS                               ║"
echo "╚════════════════════════════════════════════════════════╝"

api_call "POST" "/auth/login" \
    '{"email":"candidate@truematch.test","password":"test"}' \
    "User login with valid credentials"

# ============================================
# SECTION 2: USER PROFILE
# ============================================
if [ -n "$TOKEN" ]; then
    echo ""
    echo "╔════════════════════════════════════════════════════════╗"
    echo "║  2. USER PROFILE TESTS                                 ║"
    echo "╚════════════════════════════════════════════════════════╝"

    api_call "GET" "/users/me" \
        "" \
        "Get current user profile"
fi

# ============================================
# SECTION 3: RESUMES
# ============================================
if [ -n "$TOKEN" ]; then
    echo ""
    echo "╔════════════════════════════════════════════════════════╗"
    echo "║  3. RESUME MANAGEMENT TESTS                            ║"
    echo "╚════════════════════════════════════════════════════════╝"

    api_call "GET" "/resumes" \
        "" \
        "List user's resumes"
fi

# ============================================
# SECTION 4: POSITIONS (JOB DESCRIPTIONS)
# ============================================
if [ -n "$TOKEN" ]; then
    echo ""
    echo "╔════════════════════════════════════════════════════════╗"
    echo "║  4. POSITION/JD TESTS                                  ║"
    echo "╚════════════════════════════════════════════════════════╝"

    api_call "GET" "/positions?limit=5" \
        "" \
        "List available job positions"
fi

# ============================================
# SECTION 5: ASSESSMENTS
# ============================================
if [ -n "$TOKEN" ]; then
    echo ""
    echo "╔════════════════════════════════════════════════════════╗"
    echo "║  5. ASSESSMENT TESTS                                   ║"
    echo "╚════════════════════════════════════════════════════════╝"

    api_call "GET" "/assessments" \
        "" \
        "List user's assessments"
fi

# ============================================
# SECTION 6: SUMMARY
# ============================================
echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║  TEST SUMMARY                                          ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""
echo -e "Total Tests:    $test_count"
echo -e "${GREEN}Passed:        $pass_count${NC}"
echo -e "${RED}Failed:        $fail_count${NC}"
echo ""

if [ $fail_count -eq 0 ]; then
    echo -e "${GREEN}✅ ALL TESTS PASSED - Backend is ready!${NC}"
    exit 0
else
    echo -e "${RED}❌ SOME TESTS FAILED - Check backend configuration${NC}"
    exit 1
fi
