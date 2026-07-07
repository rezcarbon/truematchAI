#!/bin/bash

set -e

REPO_ROOT="/Users/modvader/Documents/codebase/truematch"
cd "$REPO_ROOT"

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║           TrueMatch - Full Stack Development Setup             ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Ensure services are running
echo "${BLUE}[1/4]${NC} Checking database services..."
brew services start postgresql@15 2>/dev/null || true
brew services start redis 2>/dev/null || true

# Wait for services
sleep 2
pg_isready -h localhost >/dev/null 2>&1 && echo "  ${GREEN}✓${NC} PostgreSQL running" || echo "  ${RED}✗${NC} PostgreSQL not ready"
redis-cli ping >/dev/null 2>&1 && echo "  ${GREEN}✓${NC} Redis running" || echo "  ${RED}✗${NC} Redis not ready"

echo ""
echo "${BLUE}[2/4]${NC} Setting up backend..."

cd backend
source venv/bin/activate

# Run migrations
echo "  - Running database migrations..."
python -m alembic upgrade head 2>&1 | grep -E "^[A-Za-z]|done|error" | head -3 || echo "    Migrations processed"

# Create test data (optional)
if [ -f "create_test_admin.py" ]; then
  echo "  - Setting up test admin user..."
  python create_test_admin.py 2>/dev/null || true
fi

echo "  ${GREEN}✓${NC} Backend ready"

echo ""
echo "${BLUE}[3/4]${NC} Starting services..."

# Start backend in background
echo "  - Starting FastAPI backend (http://localhost:8000)..."
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
sleep 2

# Start frontend in background
echo "  - Starting Next.js frontend (http://localhost:3000)..."
cd ../web
npm run dev &
FRONTEND_PID=$!
sleep 2

echo ""
echo "${BLUE}[4/4]${NC} Service status..."

# Check if services started
if ps -p $BACKEND_PID > /dev/null; then
  echo "  ${GREEN}✓${NC} Backend running (PID: $BACKEND_PID)"
else
  echo "  ${RED}✗${NC} Backend failed to start"
  exit 1
fi

if ps -p $FRONTEND_PID > /dev/null; then
  echo "  ${GREEN}✓${NC} Frontend running (PID: $FRONTEND_PID)"
else
  echo "  ${RED}✗${NC} Frontend failed to start"
  exit 1
fi

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                   🎉 SERVICES READY TO ROLL 🎉                 ║"
echo "╠════════════════════════════════════════════════════════════════╣"
echo "║                                                                ║"
echo "║  Backend API:       http://localhost:8000                      ║"
echo "║  API Docs:          http://localhost:8000/docs                 ║"
echo "║  Frontend:          http://localhost:3000                      ║"
echo "║  Database:          postgresql://localhost:5432/truematch_dev  ║"
echo "║  Cache:             redis://localhost:6379/0                   ║"
echo "║                                                                ║"
echo "║  Backend PID:       $BACKEND_PID"
echo "║  Frontend PID:      $FRONTEND_PID"
echo "║                                                                ║"
echo "║  Press Ctrl+C to stop all services                             ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Function to cleanup on exit
cleanup() {
  echo ""
  echo "${YELLOW}Shutting down services...${NC}"
  kill $BACKEND_PID 2>/dev/null || true
  kill $FRONTEND_PID 2>/dev/null || true
  wait $BACKEND_PID 2>/dev/null || true
  wait $FRONTEND_PID 2>/dev/null || true
  echo "${GREEN}Services stopped${NC}"
}

trap cleanup EXIT

# Keep script running
wait $BACKEND_PID $FRONTEND_PID
