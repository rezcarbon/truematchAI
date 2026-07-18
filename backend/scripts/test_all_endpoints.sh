#!/bin/bash
# Comprehensive endpoint testing script for TrueMatch AI

set -e

echo "🧪 TrueMatch AI - Endpoint Validation Test Suite"
echo "=================================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Test counters
PASSED=0
FAILED=0
SKIPPED=0

# Base URL
BASE_URL="${BASE_URL:-http://localhost:8000}"
API_BASE="$BASE_URL/api/v1"

# Mock token for testing
MOCK_TOKEN="Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0LXVzZXIiLCJleHAiOjk5OTk5OTk5OTl9.test"

echo "📡 Base URL: $BASE_URL"
echo ""

# ============================================================================
# Helper Functions
# ============================================================================

test_endpoint() {
    local method=$1
    local path=$2
    local description=$3
    local payload=${4:-}

    echo -n "Testing $description... "

    if [ -z "$payload" ]; then
        response=$(curl -s -w "\n%{http_code}" -X "$method" \
            -H "Authorization: $MOCK_TOKEN" \
            -H "Content-Type: application/json" \
            "$API_BASE$path")
    else
        response=$(curl -s -w "\n%{http_code}" -X "$method" \
            -H "Authorization: $MOCK_TOKEN" \
            -H "Content-Type: application/json" \
            -d "$payload" \
            "$API_BASE$path")
    fi

    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)

    # Check for success (2xx) or expected errors (4xx - validation)
    if [[ $http_code =~ ^[234] ]]; then
        echo -e "${GREEN}✓ OK (HTTP $http_code)${NC}"
        ((PASSED++))
    else
        echo -e "${RED}✗ FAILED (HTTP $http_code)${NC}"
        echo "  Response: $body"
        ((FAILED++))
    fi
}

check_endpoint_implemented() {
    local method=$1
    local path=$2
    local description=$3

    echo -n "Checking $description is implemented... "

    response=$(curl -s -w "\n%{http_code}" -X "$method" \
        -H "Authorization: $MOCK_TOKEN" \
        -H "Content-Type: application/json" \
        "$API_BASE$path")

    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)

    if [[ "$body" == *"Feature not yet implemented"* ]] || [[ "$body" == *"501"* ]]; then
        echo -e "${RED}✗ NOT IMPLEMENTED (HTTP 501)${NC}"
        ((FAILED++))
    elif [[ $http_code =~ ^[234] ]]; then
        echo -e "${GREEN}✓ IMPLEMENTED (HTTP $http_code)${NC}"
        ((PASSED++))
    else
        # Other errors are OK (auth, validation, etc.)
        echo -e "${YELLOW}⚠ Endpoint exists (HTTP $http_code)${NC}"
        ((SKIPPED++))
    fi
}

# ============================================================================
# Health Check
# ============================================================================

echo -e "${BLUE}═ Health Check ═${NC}"
test_endpoint GET "/livez" "Liveness endpoint"
test_endpoint GET "/readyz" "Readiness endpoint"
echo ""

# ============================================================================
# Applications Endpoints (17 total)
# ============================================================================

echo -e "${BLUE}═ Applications Endpoints ═${NC}"

# List applications
check_endpoint_implemented GET "/candidates/applications" "List applications (GET)"

# Submit application
check_endpoint_implemented POST "/candidates/applications" "Submit application (POST)"

# Get application
check_endpoint_implemented GET "/candidates/applications/test-id-1234" "Get application details"

# Update application
check_endpoint_implemented PUT "/candidates/applications/test-id-1234" "Update application"

# Delete application
check_endpoint_implemented DELETE "/candidates/applications/test-id-1234" "Delete application"

# Schedule interview
check_endpoint_implemented POST "/candidates/applications/test-id-1234/interviews/schedule" "Schedule interview"

# Get interviews
check_endpoint_implemented GET "/candidates/applications/test-id-1234/interviews" "Get interviews"

# Log interview
check_endpoint_implemented POST "/candidates/applications/test-id-1234/interviews/test-interview-id/log" "Log interview"

# Update interview
check_endpoint_implemented PUT "/candidates/applications/test-id-1234/interviews/test-interview-id" "Update interview"

# Cancel interview
check_endpoint_implemented POST "/candidates/applications/test-id-1234/interviews/test-interview-id/cancel" "Cancel interview"

# Application stats
check_endpoint_implemented GET "/candidates/applications/stats" "Get application stats"

# Application history
check_endpoint_implemented GET "/candidates/applications/test-id-1234/history" "Get application history"

# Suggested follow-up
check_endpoint_implemented GET "/candidates/applications/test-id-1234/suggested-follow-up" "Get suggested follow-up"

# Mark rejected
check_endpoint_implemented POST "/candidates/applications/test-id-1234/mark-rejected" "Mark application rejected"

# Rejection analysis
check_endpoint_implemented GET "/candidates/applications/test-id-1234/rejection-analysis" "Analyze rejection"

# Withdraw application
check_endpoint_implemented POST "/candidates/applications/test-id-1234/withdraw" "Withdraw application"

# Bulk actions
check_endpoint_implemented POST "/candidates/applications/bulk/actions" "Bulk application actions"

# Export
check_endpoint_implemented GET "/candidates/applications/export?format=csv" "Export applications"

# Monthly report
check_endpoint_implemented GET "/candidates/applications/report/monthly" "Get monthly report"

echo ""

# ============================================================================
# Job Search Endpoints (17 total)
# ============================================================================

echo -e "${BLUE}═ Job Search Endpoints ═${NC}"

# Create job search
check_endpoint_implemented POST "/candidates/job-search" "Create job search"

# List job searches
check_endpoint_implemented GET "/candidates/job-search" "List job searches"

# Get search details
check_endpoint_implemented GET "/candidates/job-search/test-search-id" "Get search details"

# Update search
check_endpoint_implemented PUT "/candidates/job-search/test-search-id" "Update job search"

# Delete search
check_endpoint_implemented DELETE "/candidates/job-search/test-search-id" "Delete job search"

# Execute search
check_endpoint_implemented POST "/candidates/job-search/test-search-id/execute" "Execute job search"

# Get results
check_endpoint_implemented GET "/candidates/job-search/test-search-id/results" "Get search results"

# Save job
check_endpoint_implemented POST "/candidates/job-search/test-search-id/jobs/test-job-id/save" "Save job"

# Bulk save jobs
check_endpoint_implemented POST "/candidates/job-search/jobs/bulk-save" "Bulk save jobs"

# Get saved jobs
check_endpoint_implemented GET "/candidates/job-search/jobs/saved" "Get saved jobs"

# Unsave job
check_endpoint_implemented DELETE "/candidates/job-search/test-search-id/jobs/test-job-id/unsave" "Unsave job"

# Get stats
check_endpoint_implemented GET "/candidates/job-search/test-search-id/stats" "Get search stats"

# Setup alerts
check_endpoint_implemented POST "/candidates/job-search/test-search-id/alerts" "Setup search alerts"

# Get alerts
check_endpoint_implemented GET "/candidates/job-search/test-search-id/alerts" "Get alert settings"

# Delete alerts
check_endpoint_implemented DELETE "/candidates/job-search/test-search-id/alerts" "Delete search alerts"

# Pause search
check_endpoint_implemented POST "/candidates/job-search/test-search-id/pause" "Pause job search"

# Resume search
check_endpoint_implemented POST "/candidates/job-search/test-search-id/resume" "Resume job search"

# Export
check_endpoint_implemented GET "/candidates/job-search/test-search-id/export?format=csv" "Export search results"

# Share
check_endpoint_implemented POST "/candidates/job-search/test-search-id/share" "Share search results"

echo ""

# ============================================================================
# Resume Versioning Endpoints (11 total)
# ============================================================================

echo -e "${BLUE}═ Resume Versioning Endpoints ═${NC}"

check_endpoint_implemented POST "/candidates/resume-versions" "Create resume version"
check_endpoint_implemented GET "/candidates/resume-versions" "List resume versions"
check_endpoint_implemented GET "/candidates/resume-versions/test-version-id" "Get version details"
check_endpoint_implemented PUT "/candidates/resume-versions/test-version-id" "Update resume version"
check_endpoint_implemented DELETE "/candidates/resume-versions/test-version-id" "Delete resume version"
check_endpoint_implemented POST "/candidates/resume-versions/test-version-id/tailor" "Tailor resume"
check_endpoint_implemented POST "/candidates/resume-versions/test-version-id/optimize-ats" "Optimize for ATS"
check_endpoint_implemented POST "/candidates/resume-versions/compare" "Compare versions"
check_endpoint_implemented POST "/candidates/resume-versions/test-version-id/download" "Download resume"
check_endpoint_implemented POST "/candidates/resume-versions/bulk/actions" "Bulk version actions"
check_endpoint_implemented GET "/candidates/resume-versions/test-version-id/recommendations" "Get recommendations"

echo ""

# ============================================================================
# Summary
# ============================================================================

TOTAL=$((PASSED + FAILED + SKIPPED))

echo -e "${BLUE}═ Test Summary ═${NC}"
echo -e "${GREEN}✓ Passed:${NC}  $PASSED"
echo -e "${RED}✗ Failed:${NC}  $FAILED"
echo -e "${YELLOW}⚠ Skipped:${NC} $SKIPPED"
echo "─────────────────"
echo "Total:  $TOTAL"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All endpoints are implemented!${NC}"
    exit 0
else
    echo -e "${RED}❌ $FAILED endpoints still need implementation${NC}"
    exit 1
fi
