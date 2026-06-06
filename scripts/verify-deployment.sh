#!/bin/bash

# TrueMatch Kubernetes Deployment Verification Script
# Checks health of all deployed components

set -e

NAMESPACE="truematch"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PASSED=0
FAILED=0
WARNINGS=0

log_pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((PASSED++))
}

log_fail() {
    echo -e "${RED}✗${NC} $1"
    ((FAILED++))
}

log_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
    ((WARNINGS++))
}

log_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

echo "TrueMatch Kubernetes Deployment Verification"
echo "=============================================="
echo ""

# Check namespace
log_info "Checking namespace..."
if kubectl get ns "$NAMESPACE" &> /dev/null; then
    log_pass "Namespace $NAMESPACE exists"
else
    log_fail "Namespace $NAMESPACE does not exist"
    exit 1
fi

# Check deployments
log_info "Checking deployments..."
if kubectl get deployment -n "$NAMESPACE" &> /dev/null; then
    local api_ready=$(kubectl get deployment api -n "$NAMESPACE" -o jsonpath='{.status.readyReplicas}')
    local api_desired=$(kubectl get deployment api -n "$NAMESPACE" -o jsonpath='{.spec.replicas}')

    if [[ "$api_ready" == "$api_desired" && "$api_ready" -gt 0 ]]; then
        log_pass "API deployment ready ($api_ready/$api_desired replicas)"
    else
        log_fail "API deployment not ready ($api_ready/$api_desired replicas)"
    fi
else
    log_fail "Cannot get deployments"
fi

# Check StatefulSets
log_info "Checking StatefulSets..."
if kubectl get statefulset postgres -n "$NAMESPACE" &> /dev/null; then
    local pg_ready=$(kubectl get statefulset postgres -n "$NAMESPACE" -o jsonpath='{.status.readyReplicas}')
    if [[ "$pg_ready" -gt 0 ]]; then
        log_pass "PostgreSQL StatefulSet ready"
    else
        log_fail "PostgreSQL StatefulSet not ready"
    fi
else
    log_fail "PostgreSQL StatefulSet not found"
fi

if kubectl get statefulset redis -n "$NAMESPACE" &> /dev/null; then
    local redis_ready=$(kubectl get statefulset redis -n "$NAMESPACE" -o jsonpath='{.status.readyReplicas}')
    if [[ "$redis_ready" -gt 0 ]]; then
        log_pass "Redis StatefulSet ready"
    else
        log_fail "Redis StatefulSet not ready"
    fi
else
    log_fail "Redis StatefulSet not found"
fi

# Check Services
log_info "Checking services..."
if kubectl get svc api -n "$NAMESPACE" &> /dev/null; then
    log_pass "API service exists"
else
    log_fail "API service not found"
fi

if kubectl get svc postgres -n "$NAMESPACE" &> /dev/null; then
    log_pass "PostgreSQL service exists"
else
    log_fail "PostgreSQL service not found"
fi

if kubectl get svc redis -n "$NAMESPACE" &> /dev/null; then
    log_pass "Redis service exists"
else
    log_fail "Redis service not found"
fi

# Check Pods
log_info "Checking pod health..."
local unhealthy_pods=$(kubectl get pods -n "$NAMESPACE" --field-selector=status.phase!=Running,status.phase!=Succeeded -o name)
if [[ -z "$unhealthy_pods" ]]; then
    log_pass "All pods are running or succeeded"
else
    log_warn "Some pods are not running: $unhealthy_pods"
fi

# Check API health endpoints
log_info "Checking API health..."
local api_pod=$(kubectl get pod -n "$NAMESPACE" -l app=api -o jsonpath='{.items[0].metadata.name}')
if [[ -n "$api_pod" ]]; then
    if kubectl exec "$api_pod" -n "$NAMESPACE" -- curl -fsS http://localhost:8000/livez &> /dev/null; then
        log_pass "API liveness probe successful"
    else
        log_warn "API liveness probe failed"
    fi

    if kubectl exec "$api_pod" -n "$NAMESPACE" -- curl -fsS http://localhost:8000/readyz &> /dev/null; then
        log_pass "API readiness probe successful"
    else
        log_warn "API readiness probe failed"
    fi
else
    log_warn "No API pods found"
fi

# Check database connectivity
log_info "Checking database..."
local pg_pod=$(kubectl get pod -n "$NAMESPACE" -l app=postgres -o jsonpath='{.items[0].metadata.name}')
if [[ -n "$pg_pod" ]]; then
    if kubectl exec "$pg_pod" -n "$NAMESPACE" -- pg_isready -U truematch &> /dev/null; then
        log_pass "PostgreSQL is accepting connections"
    else
        log_fail "PostgreSQL is not accepting connections"
    fi
else
    log_warn "No PostgreSQL pods found"
fi

# Check Redis connectivity
log_info "Checking Redis..."
local redis_pod=$(kubectl get pod -n "$NAMESPACE" -l app=redis -o jsonpath='{.items[0].metadata.name}')
if [[ -n "$redis_pod" ]]; then
    if kubectl exec "$redis_pod" -n "$NAMESPACE" -- redis-cli ping &> /dev/null; then
        log_pass "Redis is accepting connections"
    else
        log_fail "Redis is not accepting connections"
    fi
else
    log_warn "No Redis pods found"
fi

# Check resource usage
log_info "Checking resource usage..."
local high_cpu=$(kubectl top pods -n "$NAMESPACE" --no-headers 2>/dev/null | awk '$2 > 80 {print $1}')
if [[ -z "$high_cpu" ]]; then
    log_pass "No pods with high CPU usage"
else
    log_warn "Pods with high CPU usage: $high_cpu"
fi

local high_mem=$(kubectl top pods -n "$NAMESPACE" --no-headers 2>/dev/null | awk '$3 > 80 {print $1}')
if [[ -z "$high_mem" ]]; then
    log_pass "No pods with high memory usage"
else
    log_warn "Pods with high memory usage: $high_mem"
fi

# Check ConfigMaps and Secrets
log_info "Checking configuration..."
if kubectl get cm truematch-config -n "$NAMESPACE" &> /dev/null; then
    log_pass "ConfigMap truematch-config exists"
else
    log_fail "ConfigMap truematch-config not found"
fi

if kubectl get secret truematch-secrets -n "$NAMESPACE" &> /dev/null; then
    log_pass "Secret truematch-secrets exists"
else
    log_fail "Secret truematch-secrets not found"
fi

# Check Ingress
log_info "Checking ingress..."
if kubectl get ingress -n "$NAMESPACE" &> /dev/null; then
    local ingress=$(kubectl get ingress -n "$NAMESPACE" -o jsonpath='{.items[0].metadata.name}')
    if [[ -n "$ingress" ]]; then
        log_pass "Ingress $ingress exists"
        local hosts=$(kubectl get ingress "$ingress" -n "$NAMESPACE" -o jsonpath='{.spec.rules[*].host}')
        log_info "Configured hosts: $hosts"
    fi
else
    log_warn "No ingress configured"
fi

# Check HPA
log_info "Checking autoscaling..."
if kubectl get hpa -n "$NAMESPACE" &> /dev/null; then
    local hpa=$(kubectl get hpa -n "$NAMESPACE" -o name)
    if [[ -n "$hpa" ]]; then
        log_pass "HPA configured: $hpa"
    fi
else
    log_warn "No HPA configured"
fi

# Check PVC status
log_info "Checking persistent volumes..."
if kubectl get pvc -n "$NAMESPACE" &> /dev/null; then
    local unbound=$(kubectl get pvc -n "$NAMESPACE" -o jsonpath='{.items[?(@.status.phase!="Bound")].metadata.name}')
    if [[ -z "$unbound" ]]; then
        log_pass "All PVCs are bound"
    else
        log_fail "Unbound PVCs: $unbound"
    fi
else
    log_warn "No PVCs found"
fi

# Print summary
echo ""
echo "=============================================="
echo "Verification Summary"
echo "=============================================="
echo -e "${GREEN}Passed:${NC}   $PASSED"
echo -e "${RED}Failed:${NC}   $FAILED"
echo -e "${YELLOW}Warnings:${NC} $WARNINGS"
echo ""

if [[ $FAILED -eq 0 ]]; then
    log_pass "All critical checks passed!"
    exit 0
else
    log_fail "$FAILED check(s) failed"
    exit 1
fi
