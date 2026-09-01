#!/bin/bash

# TrueMatch Kubernetes Deployment Script
# Usage: ./deploy.sh [dev|staging|prod] [install|upgrade]

set -e

ENVIRONMENT=${1:-prod}
ACTION=${2:-install}
NAMESPACE="truematch"
RELEASE_NAME="truematch"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(dev|staging|prod)$ ]]; then
    log_error "Invalid environment: $ENVIRONMENT"
    echo "Usage: ./deploy.sh [dev|staging|prod] [install|upgrade]"
    exit 1
fi

# Validate action
if [[ ! "$ACTION" =~ ^(install|upgrade)$ ]]; then
    log_error "Invalid action: $ACTION"
    echo "Usage: ./deploy.sh [dev|staging|prod] [install|upgrade]"
    exit 1
fi

# Check dependencies
check_dependencies() {
    log_info "Checking dependencies..."

    local deps=("kubectl" "helm")
    for cmd in "${deps[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            log_error "$cmd is not installed"
            exit 1
        fi
    done

    log_success "All dependencies are installed"
}

# Check cluster connection
check_cluster() {
    log_info "Checking cluster connection..."

    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi

    local context=$(kubectl config current-context)
    log_success "Connected to cluster: $context"
}

# Create namespace
create_namespace() {
    log_info "Creating namespace: $NAMESPACE"

    if kubectl get ns "$NAMESPACE" &> /dev/null; then
        log_warning "Namespace $NAMESPACE already exists"
    else
        kubectl create namespace "$NAMESPACE"
        kubectl label namespace "$NAMESPACE" app=truematch
        log_success "Namespace created"
    fi
}

# Deploy using raw manifests
deploy_manifests() {
    log_info "Deploying using Kubernetes manifests..."

    # Apply in order
    kubectl apply -f "$SCRIPT_DIR/k8s/01-namespace.yaml"
    kubectl apply -f "$SCRIPT_DIR/k8s/02-config.yaml"

    log_info "Waiting for PostgreSQL to be ready..."
    kubectl apply -f "$SCRIPT_DIR/k8s/03-postgres.yaml"
    kubectl wait --for=condition=ready pod -l app=postgres -n "$NAMESPACE" --timeout=300s

    log_info "Waiting for Redis to be ready..."
    kubectl apply -f "$SCRIPT_DIR/k8s/04-redis.yaml"
    kubectl wait --for=condition=ready pod -l app=redis -n "$NAMESPACE" --timeout=300s

    log_info "Running database migrations..."
    kubectl apply -f "$SCRIPT_DIR/k8s/05-migration.yaml"
    kubectl wait --for=condition=complete job/db-migrate -n "$NAMESPACE" --timeout=300s

    log_info "Deploying API..."
    kubectl apply -f "$SCRIPT_DIR/k8s/06-api.yaml"
    kubectl wait --for=condition=available deployment/api -n "$NAMESPACE" --timeout=300s

    log_info "Deploying Workers..."
    kubectl apply -f "$SCRIPT_DIR/k8s/07-workers.yaml"

    log_info "Setting up Ingress..."
    kubectl apply -f "$SCRIPT_DIR/k8s/08-ingress.yaml"

    log_info "Setting up Monitoring..."
    kubectl apply -f "$SCRIPT_DIR/k8s/09-monitoring.yaml"

    log_success "Manifest deployment complete"
}

# Deploy using Helm
deploy_helm() {
    log_info "Deploying using Helm..."

    local values_file="$SCRIPT_DIR/helm/truematch/values-$ENVIRONMENT.yaml"

    if [[ ! -f "$values_file" ]]; then
        log_error "Values file not found: $values_file"
        exit 1
    fi

    if [[ "$ACTION" == "install" ]]; then
        helm install "$RELEASE_NAME" "$SCRIPT_DIR/helm/truematch" \
            -f "$values_file" \
            --namespace "$NAMESPACE" \
            --create-namespace \
            --wait \
            --timeout 10m
    else
        helm upgrade "$RELEASE_NAME" "$SCRIPT_DIR/helm/truematch" \
            -f "$values_file" \
            --namespace "$NAMESPACE" \
            --wait \
            --timeout 10m
    fi

    log_success "Helm deployment complete"
}

# Verify deployment
verify_deployment() {
    log_info "Verifying deployment..."

    log_info "Checking pod status..."
    kubectl get pods -n "$NAMESPACE"

    log_info "Checking deployment status..."
    kubectl get deployments -n "$NAMESPACE"

    log_info "Checking services..."
    kubectl get services -n "$NAMESPACE"

    log_info "Checking ingress..."
    kubectl get ingress -n "$NAMESPACE"

    log_success "Deployment verification complete"
}

# Get access information
show_access_info() {
    log_info "Access Information:"

    if kubectl get ingress -n "$NAMESPACE" &> /dev/null; then
        local ingress=$(kubectl get ingress -n "$NAMESPACE" -o jsonpath='{.items[0].spec.rules[0].host}')
        log_info "API URL: https://$ingress"
    else
        log_info "No ingress found. Using port-forward:"
        echo "  kubectl port-forward -n $NAMESPACE svc/api 8000:80"
        echo "  http://localhost:8000"
    fi

    log_info "Prometheus:"
    echo "  kubectl port-forward -n $NAMESPACE svc/prometheus 9090:9090"
    echo "  http://localhost:9090"

    log_info "Database access:"
    echo "  kubectl port-forward -n $NAMESPACE svc/postgres 5432:5432"
    echo "  psql -h localhost -U truematch -d truematch"

    log_info "View logs:"
    echo "  kubectl logs -n $NAMESPACE -l app=api -f"
}

# Main execution
main() {
    log_info "Starting TrueMatch deployment for environment: $ENVIRONMENT"

    check_dependencies
    check_cluster
    create_namespace

    if command -v helm &> /dev/null; then
        deploy_helm
    else
        log_warning "Helm not found, using raw Kubernetes manifests"
        deploy_manifests
    fi

    verify_deployment
    show_access_info

    log_success "Deployment completed successfully!"
}

main
