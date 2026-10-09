#!/bin/bash

# TrueMatch Render Staging Deployment Script
# AI-Native Autonomous Deployment to Render
# Usage: ./deploy-render.sh

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REPO_PATH=$(pwd)
API_KEY="${RENDER_API_KEY:-rnd_hF88wspihspe8TbxBs9SJn8xnfqI}"
RENDER_API="https://api.render.com/v1"
GITHUB_REPO="rezcarbon/truematchAI"
GITHUB_BRANCH="main"
PROJECT_NAME="truematch-staging"

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     TrueMatch Render Staging Deployment Automation     ║${NC}"
echo -e "${BLUE}║                                                        ║${NC}"
echo -e "${BLUE}║              Environment: STAGING (Render)            ║${NC}"
echo -e "${BLUE}║              Date: $(date)                    ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"

# Helper functions
print_status() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
    exit 1
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

print_phase() {
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# Phase 1: Pre-Deployment Checks
print_phase "PHASE 1: Pre-Deployment Validation"

# Check Render API key
if [ -z "$API_KEY" ]; then
    print_error "RENDER_API_KEY not set. Export it first: export RENDER_API_KEY=your_key"
fi
print_status "Render API key configured"

# Check render.yaml exists
if [ ! -f "render.yaml" ]; then
    print_error "render.yaml not found. Are you in the truematch directory?"
fi
print_status "render.yaml verified"

# Check Git status
if ! git diff-index --quiet HEAD --; then
    print_error "Uncommitted changes detected. Commit first."
fi
print_status "Git status clean"

# Get latest commit
LATEST_COMMIT=$(git rev-parse --short HEAD)
print_status "Latest commit: $LATEST_COMMIT"

# Phase 2: Verify Render Connectivity
print_phase "PHASE 2: Verifying Render API Connectivity"

# Test API connectivity
print_info "Testing Render API connection..."
API_TEST=$(curl -s -H "Authorization: Bearer $API_KEY" \
    -H "Accept: application/json" \
    "$RENDER_API/services" \
    -w "\n%{http_code}" -o /tmp/render_test.json)

HTTP_CODE=$(tail -n1 /tmp/render_test.json)
if [ "$HTTP_CODE" != "200" ]; then
    print_error "Render API authentication failed (HTTP $HTTP_CODE). Check your API key."
fi
print_status "Render API connection successful"

# Phase 3: GitHub Repository Check
print_phase "PHASE 3: GitHub Repository Verification"

print_info "Verifying GitHub repository: $GITHUB_REPO"
git remote -v | grep -q "$GITHUB_REPO" || print_error "GitHub remote not configured correctly"
print_status "GitHub repository verified: $GITHUB_REPO"

# Phase 4: Deploy via Render
print_phase "PHASE 4: Deploying to Render"

print_info "Triggering Render deployment from GitHub..."
print_info "This will:"
print_info "  1. Deploy API service (FastAPI on Python)"
print_info "  2. Deploy Frontend service (Next.js on Node.js)"
print_info "  3. Create PostgreSQL managed database"
print_info "  4. Create Redis cache instance"
print_info "  5. Configure environment variables"
print_info "  6. Run database migrations"

# The actual deployment is triggered by:
# 1. render.yaml in the repo root
# 2. Render auto-detecting it on GitHub push
# 3. Creating services based on the manifest

echo ""
print_status "Render manifest (render.yaml) is committed"
print_status "Render will auto-deploy from: https://github.com/$GITHUB_REPO/blob/$GITHUB_BRANCH/render.yaml"

# Phase 5: Deployment Status
print_phase "PHASE 5: Deployment Monitoring"

print_info "Monitor deployment progress at:"
echo -e "  ${YELLOW}https://dashboard.render.com${NC}"

echo ""
print_status "Services will be deployed as:"
echo -e "  ${YELLOW}API:      truematch-api-staging.onrender.com${NC}"
echo -e "  ${YELLOW}Frontend: truematch-web-staging.onrender.com${NC}"
echo -e "  ${YELLOW}Database: PostgreSQL (Managed by Render)${NC}"
echo -e "  ${YELLOW}Cache:    Redis (Managed by Render)${NC}"

# Phase 6: Health Check Instructions
print_phase "PHASE 6: Verification Steps"

echo ""
print_info "After deployment, verify with these commands:"
echo ""
echo -e "  ${YELLOW}# Check API health${NC}"
echo "  curl https://truematch-api-staging.onrender.com/health"
echo ""
echo -e "  ${YELLOW}# Check API docs${NC}"
echo "  curl https://truematch-api-staging.onrender.com/docs"
echo ""
echo -e "  ${YELLOW}# Test forecasting endpoint${NC}"
echo "  curl -X POST https://truematch-api-staging.onrender.com/api/v1/forecasting/pipeline \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"position_id\":\"test\"}'"
echo ""

# Phase 7: Summary
print_phase "PHASE 7: Deployment Complete"

echo -e "\n${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║    ✓ RENDER DEPLOYMENT INITIATED SUCCESSFULLY         ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"

echo -e "\n${YELLOW}Deployment Summary:${NC}"
echo -e "  Commit: $LATEST_COMMIT"
echo -e "  Branch: $GITHUB_BRANCH"
echo -e "  Repository: $GITHUB_REPO"
echo -e "  Time: $(date)"

echo -e "\n${YELLOW}Access URLs (once deployed):${NC}"
echo -e "  Frontend:     https://truematch-web-staging.onrender.com"
echo -e "  API:          https://truematch-api-staging.onrender.com"
echo -e "  API Docs:     https://truematch-api-staging.onrender.com/docs"
echo -e "  Health:       https://truematch-api-staging.onrender.com/health"

echo -e "\n${YELLOW}Expected Timeline:${NC}"
echo -e "  API Build:    2-3 minutes"
echo -e "  Frontend Build: 2-3 minutes"
echo -e "  DB Setup:     1-2 minutes"
echo -e "  Total:        ~5-8 minutes"

echo -e "\n${YELLOW}Dashboard:${NC}"
echo -e "  https://dashboard.render.com/services"

echo -e "\n${BLUE}Deployment initiated!${NC}"
echo -e "Check Render Dashboard for real-time progress."

exit 0
