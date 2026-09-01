#!/bin/bash
#
# TrueMatch AI - Production Deployment Script
# Phase 3: Production Deployment Automation
#
# This script automates the deployment of TrueMatch AI to production Kubernetes cluster.
# It handles database migrations, secret management, health checks, and rollback capabilities.

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
NAMESPACE="truematch-prod"
CLUSTER_NAME="${CLUSTER_NAME:-truematch-prod}"
REGION="${REGION:-us-west-2}"
KUBECONFIG="${KUBECONFIG:-${HOME}/.kube/config}"
DOCKER_REGISTRY="${DOCKER_REGISTRY:-registry.truematch.ai}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
DEPLOYMENT_TIMEOUT="${DEPLOYMENT_TIMEOUT:-600}"
HEALTH_CHECK_RETRIES="${HEALTH_CHECK_RETRIES:-30}"
HEALTH_CHECK_INTERVAL="${HEALTH_CHECK_INTERVAL:-10}"
SLACK_WEBHOOK="${SLACK_WEBHOOK:-}"
DRY_RUN="${DRY_RUN:-false}"
ENABLE_CANARY="${ENABLE_CANARY:-false}"
CANARY_PERCENTAGE="${CANARY_PERCENTAGE:-10}"
ENABLE_BACKUP="${ENABLE_BACKUP:-true}"

# Logging
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

# Slack notification
notify_slack() {
    if [[ -z "$SLACK_WEBHOOK" ]]; then
        return 0
    fi

    local message="$1"
    local color="${2:-#0099ff}"

    curl -X POST "$SLACK_WEBHOOK" \
        -H 'Content-Type: application/json' \
        -d "{
            \"attachments\": [{
                \"color\": \"$color\",
                \"title\": \"TrueMatch AI Deployment\",
                \"text\": \"$message\",
                \"footer\": \"Deployment Automation\",
                \"ts\": $(date +%s)
            }]
        }" 2>/dev/null || true
}

# Pre-deployment checks
pre_deployment_checks() {
    log "Running pre-deployment checks..."

    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed"
        return 1
    fi

    # Check cluster connectivity
    if ! kubectl cluster-info &>/dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        return 1
    fi

    # Check namespace exists
    if ! kubectl get namespace "$NAMESPACE" &>/dev/null; then
        log_warning "Namespace $NAMESPACE does not exist, creating..."
        kubectl create namespace "$NAMESPACE"
    fi

    # Check secrets exist
    if ! kubectl get secret truematch-prod-secrets -n "$NAMESPACE" &>/dev/null; then
        log_error "Secret 'truematch-prod-secrets' not found in namespace $NAMESPACE"
        return 1
    fi

    # Check required environment variables
    if [[ -z "${DATABASE_URL:-}" ]]; then
        log_error "DATABASE_URL environment variable not set"
        return 1
    fi

    # Check disk space
    local available_space
    available_space=$(df /var | awk 'NR==2 {print $4}')
    if [[ $available_space -lt 1000000 ]]; then
        log_error "Insufficient disk space available"
        return 1
    fi

    log_success "Pre-deployment checks passed"
    return 0
}

# Build Docker image
build_image() {
    log "Building Docker image..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log_warning "DRY RUN: Skipping image build"
        return 0
    fi

    cd "$PROJECT_ROOT"

    # Check if Dockerfile exists
    if [[ ! -f "Dockerfile" ]]; then
        log_error "Dockerfile not found in project root"
        return 1
    fi

    # Build image
    docker build \
        -t "${DOCKER_REGISTRY}/truematch-api:${IMAGE_TAG}" \
        -t "${DOCKER_REGISTRY}/truematch-api:latest" \
        -f Dockerfile \
        .

    if [[ $? -ne 0 ]]; then
        log_error "Docker image build failed"
        return 1
    fi

    log_success "Docker image built successfully"
}

# Push image to registry
push_image() {
    log "Pushing Docker image to registry..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log_warning "DRY RUN: Skipping image push"
        return 0
    fi

    docker push "${DOCKER_REGISTRY}/truematch-api:${IMAGE_TAG}"
    docker push "${DOCKER_REGISTRY}/truematch-api:latest"

    if [[ $? -ne 0 ]]; then
        log_error "Failed to push Docker image"
        return 1
    fi

    log_success "Docker image pushed successfully"
}

# Run database migrations
run_migrations() {
    log "Running database migrations..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log_warning "DRY RUN: Skipping migrations"
        return 0
    fi

    # Create migration job
    kubectl create job --from=cronjob/db-migration \
        "db-migration-$(date +%s)" \
        -n "$NAMESPACE" || true

    # Wait for migration job to complete
    local max_attempts=60
    local attempt=0
    while [[ $attempt -lt $max_attempts ]]; do
        local status
        status=$(kubectl get job "db-migration-$(date +%s)" -n "$NAMESPACE" \
            -o jsonpath='{.status.conditions[?(@.type=="Complete")].status}' 2>/dev/null)

        if [[ "$status" == "True" ]]; then
            log_success "Database migrations completed"
            return 0
        fi

        attempt=$((attempt + 1))
        sleep 5
    done

    log_error "Database migration timeout"
    return 1
}

# Create backup before deployment
create_backup() {
    if [[ "$ENABLE_BACKUP" != "true" ]]; then
        return 0
    fi

    log "Creating database backup..."

    # Create backup pod
    kubectl run "backup-$(date +%s)" \
        --image=postgres:latest \
        --namespace="$NAMESPACE" \
        -- pg_dump -h postgres-prod -U "$DB_USER" "$DB_NAME" > "/tmp/backup-$(date +%Y%m%d-%H%M%S).sql" || true

    log_success "Backup created"
}

# Deploy to Kubernetes
deploy_kubernetes() {
    log "Deploying to Kubernetes..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log_warning "DRY RUN: Running deployment with --dry-run=client"
        kubectl apply -f "${PROJECT_ROOT}/backend/k8s/prod-deployment.yaml" \
            --dry-run=client -n "$NAMESPACE"
        return 0
    fi

    # Apply configuration
    kubectl apply -f "${PROJECT_ROOT}/backend/k8s/prod-deployment.yaml" \
        -n "$NAMESPACE"

    if [[ $? -ne 0 ]]; then
        log_error "Failed to apply Kubernetes manifests"
        return 1
    fi

    log_success "Kubernetes manifests applied"
}

# Wait for rollout
wait_for_rollout() {
    local deployment=$1
    local timeout=${2:-$DEPLOYMENT_TIMEOUT}

    log "Waiting for $deployment rollout to complete (timeout: ${timeout}s)..."

    kubectl rollout status deployment/"$deployment" \
        -n "$NAMESPACE" \
        --timeout="${timeout}s"

    if [[ $? -ne 0 ]]; then
        log_error "Rollout failed for $deployment"
        return 1
    fi

    log_success "$deployment rollout completed"
}

# Health check endpoints
health_check() {
    log "Running health checks..."

    local attempts=0
    while [[ $attempts -lt $HEALTH_CHECK_RETRIES ]]; do
        # Get API service IP
        local api_ip
        api_ip=$(kubectl get service api -n "$NAMESPACE" -o jsonpath='{.spec.clusterIP}' 2>/dev/null)

        if [[ -z "$api_ip" ]]; then
            log_warning "API service not found, attempt $((attempts + 1))/$HEALTH_CHECK_RETRIES"
            attempts=$((attempts + 1))
            sleep "$HEALTH_CHECK_INTERVAL"
            continue
        fi

        # Check health endpoint
        local response
        response=$(kubectl run health-check-"$attempts" \
            --image=curlimages/curl:latest \
            --restart=Never \
            -n "$NAMESPACE" \
            -- curl -s -o /dev/null -w "%{http_code}" "http://${api_ip}/healthz" 2>/dev/null || echo "000")

        if [[ "$response" == "200" ]]; then
            log_success "Health check passed"
            kubectl delete pod "health-check-$attempts" -n "$NAMESPACE" --ignore-not-found=true
            return 0
        fi

        log_warning "Health check failed with status $response, attempt $((attempts + 1))/$HEALTH_CHECK_RETRIES"
        attempts=$((attempts + 1))
        sleep "$HEALTH_CHECK_INTERVAL"
    done

    log_error "Health checks failed after $HEALTH_CHECK_RETRIES attempts"
    return 1
}

# Verify deployment
verify_deployment() {
    log "Verifying deployment..."

    # Check pod replicas
    local api_replicas
    api_replicas=$(kubectl get deployment api -n "$NAMESPACE" -o jsonpath='{.status.replicas}' 2>/dev/null)

    if [[ -z "$api_replicas" ]] || [[ "$api_replicas" -lt 1 ]]; then
        log_error "API deployment has no replicas"
        return 1
    fi

    # Check worker replicas
    local worker_replicas
    worker_replicas=$(kubectl get deployment worker -n "$NAMESPACE" -o jsonpath='{.status.replicas}' 2>/dev/null)

    if [[ -z "$worker_replicas" ]] || [[ "$worker_replicas" -lt 1 ]]; then
        log_error "Worker deployment has no replicas"
        return 1
    fi

    log_success "Deployment verified - API: $api_replicas replicas, Worker: $worker_replicas replicas"
    return 0
}

# Rollback deployment
rollback_deployment() {
    log_error "Initiating rollback..."

    kubectl rollout undo deployment/api -n "$NAMESPACE"
    kubectl rollout undo deployment/worker -n "$NAMESPACE"
    kubectl rollout undo deployment/scheduler -n "$NAMESPACE"

    sleep 10
    kubectl rollout status deployment/api -n "$NAMESPACE" --timeout=300s

    log_success "Rollback completed"
}

# Cleanup resources
cleanup() {
    log "Cleaning up..."

    # Remove health check pods
    kubectl delete pods -n "$NAMESPACE" -l run=health-check-* --ignore-not-found=true

    # Remove backup pods
    kubectl delete pods -n "$NAMESPACE" -l run=backup-* --ignore-not-found=true

    log_success "Cleanup completed"
}

# Main deployment flow
main() {
    log "Starting TrueMatch AI production deployment"
    log "Configuration:"
    log "  Namespace: $NAMESPACE"
    log "  Cluster: $CLUSTER_NAME"
    log "  Image Tag: $IMAGE_TAG"
    log "  Dry Run: $DRY_RUN"
    log "  Enable Backup: $ENABLE_BACKUP"

    notify_slack "Starting deployment: $IMAGE_TAG" "#0099ff"

    # Run pre-deployment checks
    if ! pre_deployment_checks; then
        notify_slack "Deployment failed: Pre-deployment checks failed" "#ff0000"
        return 1
    fi

    # Create backup
    if ! create_backup; then
        log_warning "Backup creation failed, continuing with deployment"
    fi

    # Build and push image
    if ! build_image; then
        notify_slack "Deployment failed: Docker build failed" "#ff0000"
        return 1
    fi

    if ! push_image; then
        notify_slack "Deployment failed: Docker push failed" "#ff0000"
        return 1
    fi

    # Run migrations
    if ! run_migrations; then
        notify_slack "Deployment failed: Database migrations failed" "#ff0000"
        return 1
    fi

    # Deploy to Kubernetes
    if ! deploy_kubernetes; then
        notify_slack "Deployment failed: Kubernetes deployment failed" "#ff0000"
        return 1
    fi

    # Wait for rollout
    if ! wait_for_rollout "api" || ! wait_for_rollout "worker" || ! wait_for_rollout "scheduler"; then
        notify_slack "Deployment failed: Rollout failed" "#ff0000"
        rollback_deployment
        return 1
    fi

    # Verify deployment
    if ! verify_deployment; then
        notify_slack "Deployment failed: Verification failed" "#ff0000"
        rollback_deployment
        return 1
    fi

    # Health checks
    if ! health_check; then
        notify_slack "Deployment failed: Health checks failed" "#ff0000"
        rollback_deployment
        return 1
    fi

    # Cleanup
    cleanup

    log_success "Deployment completed successfully"
    notify_slack "Deployment completed successfully: $IMAGE_TAG" "#00ff00"
    return 0
}

# Error handling
trap cleanup EXIT

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN="true"
            shift
            ;;
        --tag)
            IMAGE_TAG="$2"
            shift 2
            ;;
        --namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        --cluster)
            CLUSTER_NAME="$2"
            shift 2
            ;;
        --no-backup)
            ENABLE_BACKUP="false"
            shift
            ;;
        --slack-webhook)
            SLACK_WEBHOOK="$2"
            shift 2
            ;;
        --help)
            cat << EOF
Usage: $0 [OPTIONS]

Options:
  --dry-run              Run deployment in dry-run mode
  --tag TAG              Docker image tag (default: latest)
  --namespace NS         Kubernetes namespace (default: truematch-prod)
  --cluster CLUSTER      Cluster name (default: truematch-prod)
  --no-backup            Disable database backup
  --slack-webhook URL    Slack webhook URL for notifications
  --help                 Show this help message

Examples:
  $0 --tag v1.2.3
  $0 --dry-run --tag v1.2.3
  $0 --tag v1.2.3 --slack-webhook https://hooks.slack.com/...

EOF
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Execute main
main
