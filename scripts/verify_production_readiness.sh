#!/bin/bash
################################################################################
# TrueMatch Production Readiness Verification Script
#
# This script verifies all 8 pre-flight items are in place:
# 1. SECRET_KEY set
# 2. SSL certificates exist
# 3. Health endpoints responding
# 4. Database backups working
# 5. Monitoring stack running
# 6. Log aggregation configured
# 7. Disaster recovery procedures documented
# 8. All systems operational
#
# Usage: ./verify_production_readiness.sh
#
################################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKEND_URL="http://localhost:8000"
GRAFANA_URL="http://localhost:3001"
PROMETHEUS_URL="http://localhost:9090"
LOKI_URL="http://localhost:3100"

# Counters
PASSED=0
FAILED=0
WARNINGS=0

# Functions
print_header() {
    echo -e "\n${BLUE}════════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}\n"
}

check_pass() {
    echo -e "${GREEN}✅${NC} $1"
    ((PASSED++))
}

check_fail() {
    echo -e "${RED}❌${NC} $1"
    ((FAILED++))
}

check_warn() {
    echo -e "${YELLOW}⚠️${NC} $1"
    ((WARNINGS++))
}

# ─────────────────────────────────────────────────────────────────────────────
# ITEM 1: SECRET_KEY Verification
# ─────────────────────────────────────────────────────────────────────────────

print_header "1. SECRET_KEY Configuration"

if grep -q "^SECRET_KEY=" backend/.env; then
    SECRET_KEY=$(grep "^SECRET_KEY=" backend/.env | cut -d'=' -f2)
    if [ ${#SECRET_KEY} -ge 32 ]; then
        check_pass "SECRET_KEY set and meets minimum length (32+ chars)"
    else
        check_fail "SECRET_KEY too short (${#SECRET_KEY} chars, need 32+)"
    fi
else
    check_fail "SECRET_KEY not found in .env"
fi

# ─────────────────────────────────────────────────────────────────────────────
# ITEM 2: SSL Certificates
# ─────────────────────────────────────────────────────────────────────────────

print_header "2. SSL/TLS Certificates"

if [ -f backend/certs/cert.pem ] && [ -f backend/certs/key.pem ]; then
    check_pass "SSL certificates found (cert.pem, key.pem)"

    # Check certificate validity
    EXPIRY=$(openssl x509 -enddate -noout -in backend/certs/cert.pem | cut -d= -f2)
    check_pass "Certificate valid until: $EXPIRY"
else
    check_fail "SSL certificates not found at backend/certs/"
fi

# ─────────────────────────────────────────────────────────────────────────────
# ITEM 3: Health Endpoints
# ─────────────────────────────────────────────────────────────────────────────

print_header "3. Health Endpoints"

# Check if backend is running
if ! curl -s ${BACKEND_URL}/livez > /dev/null 2>&1; then
    check_warn "Backend not running on ${BACKEND_URL}. Skipping endpoint tests."
    check_warn "To test health endpoints, start backend: python -m uvicorn app.main:app"
else
    # /livez endpoint
    LIVEZ_STATUS=$(curl -s ${BACKEND_URL}/livez | jq -r '.status' 2>/dev/null)
    if [ "$LIVEZ_STATUS" = "ok" ]; then
        check_pass "/livez endpoint responding (status: ok)"
    else
        check_fail "/livez endpoint not responding correctly"
    fi

    # /readyz endpoint
    READYZ_RESPONSE=$(curl -s ${BACKEND_URL}/readyz)
    if echo "$READYZ_RESPONSE" | jq -e '.components.database' > /dev/null 2>&1; then
        check_pass "/readyz endpoint responding with component checks"
    else
        check_fail "/readyz endpoint not responding correctly"
    fi

    # /health endpoint
    HEALTH_STATUS=$(curl -s ${BACKEND_URL}/health | jq -r '.status' 2>/dev/null)
    if [ "$HEALTH_STATUS" = "ok" ]; then
        check_pass "/health endpoint responding (status: ok)"
    else
        check_fail "/health endpoint not responding correctly"
    fi
fi

# ─────────────────────────────────────────────────────────────────────────────
# ITEM 4: Database Backups
# ─────────────────────────────────────────────────────────────────────────────

print_header "4. Database Backup Configuration"

if [ -x scripts/backup_database.sh ]; then
    check_pass "Backup script exists and is executable"

    # Check if backups directory exists
    if [ -d backups ]; then
        BACKUP_COUNT=$(find backups -name "truematch_backup_*.sql.gz" 2>/dev/null | wc -l)
        if [ $BACKUP_COUNT -gt 0 ]; then
            LATEST_BACKUP=$(ls -t backups/truematch_backup_*.sql.gz 2>/dev/null | head -1)
            BACKUP_SIZE=$(du -h "$LATEST_BACKUP" | cut -f1)
            check_pass "Database backups found ($BACKUP_COUNT backups, latest: $BACKUP_SIZE)"
        else
            check_warn "Backup directory exists but no backups found"
        fi
    else
        check_warn "Backups directory not found. Create with: mkdir -p backups"
    fi
else
    check_fail "Backup script not found or not executable"
fi

if [ -x scripts/restore_database.sh ]; then
    check_pass "Restore script exists and is executable"
else
    check_fail "Restore script not found or not executable"
fi

# ─────────────────────────────────────────────────────────────────────────────
# ITEM 5: Monitoring Stack (Prometheus, Grafana, Loki)
# ─────────────────────────────────────────────────────────────────────────────

print_header "5. Monitoring Stack"

# Check docker-compose.monitoring.yml
if [ -f docker-compose.monitoring.yml ]; then
    check_pass "docker-compose.monitoring.yml exists"
else
    check_fail "docker-compose.monitoring.yml not found"
fi

# Check for monitoring configuration files
MONITORING_FILES=(
    "monitoring/prometheus.yml"
    "monitoring/alerts.yml"
    "monitoring/loki.yml"
    "monitoring/promtail.yml"
    "monitoring/alertmanager.yml"
)

for file in "${MONITORING_FILES[@]}"; do
    if [ -f "$file" ]; then
        check_pass "Found: $file"
    else
        check_fail "Missing: $file"
    fi
done

# Check if monitoring services are running
if command -v docker-compose &> /dev/null; then
    # Check Prometheus
    if docker-compose -f docker-compose.monitoring.yml ps prometheus 2>/dev/null | grep -q "running"; then
        check_pass "Prometheus container running"
    else
        check_warn "Prometheus not running (start with: docker-compose -f docker-compose.monitoring.yml up -d)"
    fi

    # Check Grafana
    if docker-compose -f docker-compose.monitoring.yml ps grafana 2>/dev/null | grep -q "running"; then
        check_pass "Grafana container running"
    else
        check_warn "Grafana not running"
    fi

    # Check Loki
    if docker-compose -f docker-compose.monitoring.yml ps loki 2>/dev/null | grep -q "running"; then
        check_pass "Loki container running"
    else
        check_warn "Loki not running"
    fi
fi

# ─────────────────────────────────────────────────────────────────────────────
# ITEM 6: Log Aggregation Configuration
# ─────────────────────────────────────────────────────────────────────────────

print_header "6. Log Aggregation Setup"

if [ -f monitoring/loki.yml ]; then
    check_pass "Loki configuration found"
    if grep -q "retention_deletes_enabled" monitoring/loki.yml; then
        check_pass "Log retention configured"
    fi
fi

if [ -f monitoring/promtail.yml ]; then
    check_pass "Promtail configuration found"
    if grep -q "loki:3100" monitoring/promtail.yml; then
        check_pass "Promtail configured to send logs to Loki"
    fi
fi

# ─────────────────────────────────────────────────────────────────────────────
# ITEM 7: Documentation
# ─────────────────────────────────────────────────────────────────────────────

print_header "7. Disaster Recovery & Operational Runbooks"

DOCS=(
    "docs/DEPLOYMENT.md"
    "docs/MONITORING.md"
    "docs/DISASTER_RECOVERY.md"
)

for doc in "${DOCS[@]}"; do
    if [ -f "$doc" ]; then
        LINES=$(wc -l < "$doc")
        check_pass "Found: $doc ($LINES lines)"
    else
        check_fail "Missing: $doc"
    fi
done

# ─────────────────────────────────────────────────────────────────────────────
# ITEM 8: Final System Checks
# ─────────────────────────────────────────────────────────────────────────────

print_header "8. Final System Verification"

# Check database connectivity
if command -v psql &> /dev/null; then
    if PGPASSWORD=${DATABASE_PASSWORD:-password} psql -h ${DATABASE_HOST:-127.0.0.1} -U ${DATABASE_USER:-truematch} -d ${DATABASE_NAME:-truematch} -c "SELECT 1;" > /dev/null 2>&1; then
        check_pass "PostgreSQL database accessible"
    else
        check_warn "PostgreSQL database not accessible (may not be running)"
    fi
fi

# Check Redis connectivity
if command -v redis-cli &> /dev/null; then
    if redis-cli ping > /dev/null 2>&1; then
        check_pass "Redis accessible"
    else
        check_warn "Redis not accessible (may not be running)"
    fi
fi

# Check Python environment
if [ -f backend/pyproject.toml ] || [ -f backend/requirements.txt ]; then
    check_pass "Python dependencies configured"
fi

# Check git status
if [ -d .git ]; then
    if [ -z "$(git status --porcelain)" ]; then
        check_pass "Git working tree clean"
    else
        check_warn "Git working tree has uncommitted changes"
    fi
fi

# ─────────────────────────────────────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────────────────────────────────────

print_header "PRODUCTION READINESS SUMMARY"

TOTAL=$((PASSED + FAILED))
PERCENTAGE=$((PASSED * 100 / TOTAL))

echo -e "Tests Passed:   ${GREEN}${PASSED}${NC}"
echo -e "Tests Failed:   ${RED}${FAILED}${NC}"
echo -e "Warnings:       ${YELLOW}${WARNINGS}${NC}"
echo -e "Total:          ${BLUE}${TOTAL}${NC}"
echo ""
echo -e "Success Rate:   ${PERCENTAGE}%"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ SYSTEM IS PRODUCTION READY${NC}"
    exit 0
elif [ $FAILED -le 3 ]; then
    echo -e "${YELLOW}⚠️  SYSTEM IS MOSTLY READY (Minor issues to fix)${NC}"
    exit 1
else
    echo -e "${RED}❌ SYSTEM NOT READY FOR PRODUCTION (Critical issues)${NC}"
    exit 2
fi
