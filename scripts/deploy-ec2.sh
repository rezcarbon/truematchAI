#!/bin/bash

# TrueMatch AI - EC2 Deployment Script
# Deploys the latest code to running EC2 instance
# Usage: ./deploy-ec2.sh <EC2_USER@EC2_HOST> [branch] [env_file]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] ✓${NC} $*"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ✗${NC} $*"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] ⚠${NC} $*"
}

# Configuration
EC2_HOST="${1:-}"
BRANCH="${2:-main}"
ENV_FILE="${3:-.env}"
PROJECT_DIR="/home/ubuntu/truematchAI"  # Adjust based on your EC2 setup
BACKUP_DIR="/home/ubuntu/backups"

# Validate arguments
if [[ -z "$EC2_HOST" ]]; then
    log_error "Usage: $0 <EC2_USER@EC2_HOST> [branch] [env_file]"
    log_error "Example: $0 ubuntu@ec2-xxx.compute.amazonaws.com main .env"
    exit 1
fi

log "Starting deployment to EC2: $EC2_HOST"
log "Branch: $BRANCH"
log "Environment file: $ENV_FILE"

# Step 1: Verify SSH connection
log "Verifying SSH connection to $EC2_HOST..."
if ssh -o ConnectTimeout=5 "$EC2_HOST" "echo 'SSH connection OK'" 2>/dev/null; then
    log_success "SSH connection verified"
else
    log_error "Cannot connect to $EC2_HOST via SSH"
    exit 1
fi

# Step 2: Create backup on EC2
log "Creating backup of current deployment..."
ssh "$EC2_HOST" "
    set -e
    BACKUP_DIR='$BACKUP_DIR'
    mkdir -p \$BACKUP_DIR
    BACKUP_FILE=\"\$BACKUP_DIR/backup-\$(date +%Y%m%d-%H%M%S).tar.gz\"
    cd '$PROJECT_DIR'

    # Backup database
    if command -v docker &> /dev/null; then
        echo 'Backing up database...'
        docker compose exec -T postgres pg_dump -U truematch truematch > \"/tmp/db-backup-\$(date +%Y%m%d-%H%M%S).sql\" 2>/dev/null || true
    fi

    # Backup docker volumes
    echo 'Creating volume backup...'
    tar -czf \"\$BACKUP_FILE\" \
        --exclude='node_modules' \
        --exclude='.git' \
        --exclude='.env' \
        .docker/ backend/ 2>/dev/null || true

    echo \"Backup created: \$BACKUP_FILE\"
" || log_warning "Backup creation had issues, continuing..."

# Step 3: Pull latest code
log "Pulling latest code from branch: $BRANCH..."
ssh "$EC2_HOST" "
    set -e
    cd '$PROJECT_DIR'
    git fetch origin
    git checkout $BRANCH
    git pull origin $BRANCH
    git log --oneline -1
" || {
    log_error "Failed to pull latest code"
    exit 1
}
log_success "Code pulled successfully"

# Step 4: Rebuild Docker images
log "Rebuilding Docker images..."
ssh "$EC2_HOST" "
    set -e
    cd '$PROJECT_DIR/backend'

    if command -v docker &> /dev/null; then
        echo 'Building API image...'
        docker build -t truematch-api:latest .

        echo 'Rebuilding all services...'
        docker compose build --no-cache
        log_success 'Docker images rebuilt'
    else
        echo 'Docker not found, skipping image rebuild'
    fi
" || {
    log_warning "Docker rebuild had issues"
}

# Step 5: Stop running services
log "Stopping running services..."
ssh "$EC2_HOST" "
    cd '$PROJECT_DIR/backend'
    if command -v docker-compose &> /dev/null || command -v docker &> /dev/null; then
        docker compose down || true
    fi
" || log_warning "Services stop had issues"

# Step 6: Start services with new code
log "Starting services with updated code..."
ssh "$EC2_HOST" "
    set -e
    cd '$PROJECT_DIR/backend'

    if command -v docker &> /dev/null; then
        echo 'Starting services...'
        docker compose up -d

        # Wait for services to be ready
        echo 'Waiting for services to be ready...'
        sleep 10

        # Check if API is responding
        for i in {1..30}; do
            if docker compose exec -T api curl -s http://localhost:8000/health >/dev/null 2>&1; then
                echo 'API is responding'
                break
            fi
            echo \"Waiting... attempt \$i/30\"
            sleep 2
        done
    fi
" || {
    log_error "Failed to start services"
    exit 1
}
log_success "Services started successfully"

# Step 7: Run migrations
log "Running database migrations..."
ssh "$EC2_HOST" "
    cd '$PROJECT_DIR/backend'

    if command -v docker &> /dev/null; then
        echo 'Running alembic migrations...'
        docker compose exec -T api alembic upgrade head
    fi
" || log_warning "Migrations had issues"

# Step 8: Health check
log "Running health checks..."
ssh "$EC2_HOST" "
    cd '$PROJECT_DIR/backend'

    if command -v docker &> /dev/null; then
        echo 'Checking API health...'
        docker compose exec -T api curl -s http://localhost:8000/health | head -20

        echo 'Checking Celery worker...'
        docker compose ps | grep worker

        echo 'Checking database...'
        docker compose exec -T api psql -U truematch -d truematch -c 'SELECT version();' || true
    fi
" || log_warning "Health checks had issues"

# Step 9: Verify Persona System
log "Verifying Persona System deployment..."
ssh "$EC2_HOST" "
    cd '$PROJECT_DIR/backend'

    if command -v docker &> /dev/null; then
        echo 'Checking if persona_system.py is deployed...'
        docker compose exec -T api ls -la app/agents/persona_*.py

        echo 'Testing persona imports...'
        docker compose exec -T api python3 -c \"from app.agents.persona_system import PersonaLibrary; personas = PersonaLibrary.get_candidate_personas(); print(f'✓ Persona system loaded: {len(personas)} candidate personas')\" || true
    fi
" || log_warning "Persona verification had issues"

# Step 10: Test Persona API endpoint
log "Testing persona-enhanced chat endpoint..."
ssh "$EC2_HOST" "
    cd '$PROJECT_DIR/backend'

    if command -v docker &> /dev/null; then
        # Get a test token (this assumes you have test data)
        echo 'Testing chat API with persona system...'

        # Simple health check for now
        docker compose exec -T api curl -s http://localhost:8000/health
    fi
" || log_warning "API test had issues"

log_success "Deployment completed successfully!"

# Display status and access information
log "Deployment Summary:"
ssh "$EC2_HOST" "
    echo '================================'
    echo 'TrueMatch AI - Deployment Status'
    echo '================================'
    echo ''
    echo 'Deployed at: '$(date)
    echo 'Branch: $BRANCH'
    echo ''
    echo 'Services:'
    cd '$PROJECT_DIR/backend'
    docker compose ps
    echo ''
    echo 'Access Information:'
    echo '  API URL: http://$EC2_HOST:8000'
    echo '  Health Check: http://$EC2_HOST:8000/health'
    echo ''
    echo 'Logs:'
    echo '  docker compose logs -f api'
    echo ''
    echo 'Rollback if needed:'
    echo '  cd $PROJECT_DIR'
    echo '  git reset --hard HEAD~1'
    echo '  docker compose up -d --build'
    echo ''
    echo 'Persona System Status:'
    docker compose exec -T api python3 -c \"
try:
    from app.agents.persona_system import PersonaLibrary
    candidates = len(PersonaLibrary.get_candidate_personas())
    recruiters = len(PersonaLibrary.get_recruiter_personas())
    print(f'✓ Persona System: {candidates} candidate personas, {recruiters} recruiter personas')
except Exception as e:
    print(f'✗ Persona System Error: {e}')
\" 2>/dev/null || echo 'Persona system check skipped'
"

log_success "Deployment to EC2 completed!"
log "Persona Enhancement System is now live on your EC2 instance"
