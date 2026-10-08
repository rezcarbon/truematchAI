#!/bin/bash

# TrueMatch Staging Deployment Script
# Automated deployment to staging environment
# Usage: ./deploy-staging.sh

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REPO_PATH=$(pwd)
ENVIRONMENT="staging"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     TrueMatch Staging Deployment Automation Script     ║${NC}"
echo -e "${BLUE}║                                                        ║${NC}"
echo -e "${BLUE}║              Environment: STAGING                      ║${NC}"
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

# Phase 1: Pre-deployment Checks
print_phase "PHASE 1: Pre-deployment Checks"

# Check Docker
if ! command -v docker &> /dev/null; then
    print_error "Docker not found. Install Docker first: https://get.docker.com"
fi
print_status "Docker is installed"

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose not found"
fi
print_status "Docker Compose is installed"

# Check Git
if ! command -v git &> /dev/null; then
    print_error "Git not found"
fi
print_status "Git is installed"

# Verify repository
if [ ! -f "docker-compose.yml" ]; then
    print_error "docker-compose.yml not found. Are you in the truematch directory?"
fi
print_status "Repository structure verified"

# Phase 2: Git Verification
print_phase "PHASE 2: Git Verification"

# Check git status
if ! git diff-index --quiet HEAD --; then
    print_error "Uncommitted changes detected. Commit or stash changes first."
fi
print_status "No uncommitted changes"

# Get latest commit
LATEST_COMMIT=$(git rev-parse --short HEAD)
print_status "Latest commit: $LATEST_COMMIT"

# Phase 3: Environment Setup
print_phase "PHASE 3: Environment Configuration"

# Check environment file
if [ ! -f "backend/.env.staging" ]; then
    print_info "Creating .env.staging from template..."
    cp backend/.env.example backend/.env.staging
    print_error "Please configure backend/.env.staging with your staging credentials, then run this script again."
fi
print_status "Environment file exists: backend/.env.staging"

# Phase 4: Stop existing containers
print_phase "PHASE 4: Cleaning up Previous Deployment"

print_info "Stopping existing containers..."
docker-compose down --remove-orphans 2>/dev/null || true
print_status "Previous containers stopped"

# Phase 5: Start Infrastructure
print_phase "PHASE 5: Starting Infrastructure"

# Start PostgreSQL
print_info "Starting PostgreSQL..."
docker-compose up -d postgres
sleep 10

# Verify PostgreSQL
if docker-compose exec -T postgres pg_isready -U truematch > /dev/null 2>&1; then
    print_status "PostgreSQL started and healthy"
else
    print_error "PostgreSQL failed to start"
fi

# Start Redis
print_info "Starting Redis..."
docker-compose up -d redis
sleep 5

# Verify Redis
if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    print_status "Redis started and healthy"
else
    print_error "Redis failed to start"
fi

# Phase 6: Database Migrations
print_phase "PHASE 6: Database Migrations"

print_info "Running database migrations..."
if docker-compose run --rm api alembic upgrade head; then
    print_status "Database migrations completed successfully"
else
    print_error "Database migrations failed"
fi

# Phase 7: Start Backend Services
print_phase "PHASE 7: Starting Backend Services"

# Start API server
print_info "Starting API server..."
docker-compose up -d api
sleep 10

# Verify API is responding
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    print_status "API server is responding"
else
    print_error "API server failed to start"
fi

# Start Celery Worker
print_info "Starting Celery worker..."
docker-compose up -d worker
sleep 5
print_status "Celery worker started"

# Start Celery Beat
print_info "Starting Celery Beat..."
docker-compose up -d beat
sleep 5
print_status "Celery Beat started"

# Phase 8: Frontend Setup
print_phase "PHASE 8: Frontend Preparation"

# Create frontend env file if missing
if [ ! -f "web/.env.staging" ]; then
    print_info "Creating web/.env.staging..."
    cat > web/.env.staging << 'EOF'
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_ENVIRONMENT=staging
NEXT_PUBLIC_APP_URL=http://localhost:3000
EOF
    print_status "Frontend environment file created"
fi

# Install frontend dependencies
print_info "Installing frontend dependencies..."
cd web
npm install --legacy-peer-deps > /dev/null 2>&1
print_status "Frontend dependencies installed"
cd ..

# Build frontend
print_info "Building frontend..."
cd web
npm run build > /dev/null 2>&1 || print_error "Frontend build failed"
print_status "Frontend build successful"
cd ..

# Phase 9: Health Verification
print_phase "PHASE 9: Health Verification"

# Check all containers
print_info "Verifying all containers..."
docker-compose ps

# Test API endpoints
print_info "Testing API endpoints..."

# Test health
if curl -s http://localhost:8000/health > /dev/null; then
    print_status "API health check passed"
else
    print_error "API health check failed"
fi

# Test forecasting endpoint
if curl -s -X POST http://localhost:8000/api/v1/forecasting/pipeline \
    -H "Content-Type: application/json" \
    -d '{"position_id":"test"}' > /dev/null; then
    print_status "Forecasting endpoint responding"
else
    print_error "Forecasting endpoint failed"
fi

# Test salary benchmarking endpoint
if curl -s -X GET http://localhost:8000/api/v1/salary-benchmarking/benchmark > /dev/null 2>&1; then
    print_status "Salary benchmarking endpoint responding"
else
    print_error "Salary benchmarking endpoint failed"
fi

# Test interview intelligence endpoint
if curl -s -X POST http://localhost:8000/api/v1/interview-intelligence/prep \
    -H "Content-Type: application/json" \
    -d '{
      "candidate_id":"test",
      "position_id":"test",
      "candidate_name":"Test",
      "candidate_background":"Engineer",
      "position_title":"Senior Engineer",
      "key_requirements":["Python"]
    }' > /dev/null; then
    print_status "Interview intelligence endpoint responding"
else
    print_error "Interview intelligence endpoint failed"
fi

# Phase 10: Summary
print_phase "PHASE 10: Deployment Summary"

echo -e "\n${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║         ✓ STAGING DEPLOYMENT SUCCESSFUL              ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"

echo -e "\n${YELLOW}Service Status:${NC}"
echo -e "  ${GREEN}✓${NC} PostgreSQL (Port 5432)"
echo -e "  ${GREEN}✓${NC} Redis (Port 6379)"
echo -e "  ${GREEN}✓${NC} API Server (Port 8000)"
echo -e "  ${GREEN}✓${NC} Celery Worker"
echo -e "  ${GREEN}✓${NC} Celery Beat"
echo -e "  ${GREEN}✓${NC} Frontend (Ready)"

echo -e "\n${YELLOW}Access Points:${NC}"
echo -e "  API:         http://localhost:8000"
echo -e "  API Docs:    http://localhost:8000/docs"
echo -e "  API Health:  http://localhost:8000/health"
echo -e "  Frontend:    http://localhost:3000 (npm run dev)"
echo -e "  Database:    localhost:5432"
echo -e "  Cache:       localhost:6379"

echo -e "\n${YELLOW}Useful Commands:${NC}"
echo -e "  View API logs:     docker-compose logs -f api"
echo -e "  View worker logs:  docker-compose logs -f worker"
echo -e "  View all logs:     docker-compose logs -f"
echo -e "  Stop deployment:   docker-compose down"
echo -e "  Fresh start:       docker-compose down -v && ./deploy-staging.sh"
echo -e "  Start frontend:    cd web && npm run dev"

echo -e "\n${YELLOW}Next Steps:${NC}"
echo -e "  1. Start frontend: cd web && npm run dev"
echo -e "  2. Open browser:   http://localhost:3000"
echo -e "  3. Test features:  Pipeline Forecast, Salary Benchmark, etc."
echo -e "  4. Monitor logs:   docker-compose logs -f"
echo -e "  5. Check API docs: http://localhost:8000/docs"

echo -e "\n${BLUE}Deployment Complete!${NC}"
echo -e "Timestamp: $TIMESTAMP"
echo -e "Latest Commit: $LATEST_COMMIT"
echo -e "\nFor more information, see: STAGING_DEPLOYMENT_GUIDE.md"

exit 0
