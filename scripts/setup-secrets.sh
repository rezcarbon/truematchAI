#!/bin/bash

# TrueMatch Kubernetes Secrets Setup Script
# Creates sealed secrets for production deployment

set -e

NAMESPACE="truematch"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Colors
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

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

prompt_secret() {
    local prompt="$1"
    local secret_var
    local confirmation

    while true; do
        read -sp "${BLUE}${prompt}:${NC} " secret_var
        echo ""
        read -sp "Confirm: " confirmation
        echo ""

        if [[ "$secret_var" == "$confirmation" ]]; then
            echo "$secret_var"
            break
        else
            log_error "Values do not match. Please try again."
        fi
    done
}

echo "TrueMatch Kubernetes Secrets Setup"
echo "==================================="
echo ""

# Check kubectl and kubeseal
if ! command -v kubectl &> /dev/null; then
    log_error "kubectl is not installed"
    exit 1
fi

log_info "Checking kubeseal installation..."
if ! command -v kubeseal &> /dev/null; then
    log_warning "kubeseal not found. Using base64 encoding instead (LESS SECURE)"
    USE_KUBESEAL=false
else
    log_success "kubeseal is installed"
    USE_KUBESEAL=true
fi

# Check namespace
if ! kubectl get ns "$NAMESPACE" &> /dev/null; then
    log_error "Namespace $NAMESPACE does not exist"
    exit 1
fi

log_info "Collecting secrets..."
echo ""

# Collect secrets interactively
JWT_SECRET=$(prompt_secret "JWT Secret (32+ chars)")
DATABASE_PASSWORD=$(prompt_secret "Database Password")
ENCRYPTION_KEY=$(prompt_secret "Encryption Key")
ENCRYPTION_INDEX_KEY=$(prompt_secret "Encryption Index Key")
AWS_ACCESS_KEY=$(prompt_secret "AWS Access Key ID")
AWS_SECRET_KEY=$(prompt_secret "AWS Secret Access Key")
SENDGRID_KEY=$(prompt_secret "SendGrid API Key")
GOOGLE_CLIENT_ID=$(prompt_secret "Google Client ID")
GOOGLE_CLIENT_SECRET=$(prompt_secret "Google Client Secret")

echo ""
log_info "Creating Kubernetes secret..."

# Create temporary secret manifest
TEMP_SECRET=$(mktemp)
cat > "$TEMP_SECRET" <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: truematch-secrets
  namespace: $NAMESPACE
type: Opaque
stringData:
  JWT_SECRET: "$JWT_SECRET"
  ENCRYPTION_KEY: "$ENCRYPTION_KEY"
  ENCRYPTION_INDEX_KEY: "$ENCRYPTION_INDEX_KEY"
  DATABASE_USER: "truematch"
  DATABASE_PASSWORD: "$DATABASE_PASSWORD"
  AWS_ACCESS_KEY_ID: "$AWS_ACCESS_KEY"
  AWS_SECRET_ACCESS_KEY: "$AWS_SECRET_KEY"
  S3_KMS_KEY_ID: ""
  SENDGRID_API_KEY: "$SENDGRID_KEY"
  GOOGLE_CLIENT_ID: "$GOOGLE_CLIENT_ID"
  GOOGLE_CLIENT_SECRET: "$GOOGLE_CLIENT_SECRET"
  SENTRY_DSN: ""
EOF

if [[ "$USE_KUBESEAL" == "true" ]]; then
    log_info "Sealing secret with kubeseal..."
    kubeseal -f "$TEMP_SECRET" -w "$SCRIPT_DIR/k8s/sealed-secrets.yaml" -n "$NAMESPACE"
    log_success "Sealed secret created at k8s/sealed-secrets.yaml"
    log_warning "Apply with: kubectl apply -f k8s/sealed-secrets.yaml"
else
    log_warning "Creating unencrypted secret (use sealed-secrets for production!)"
    kubectl apply -f "$TEMP_SECRET"
    log_success "Secret created in cluster"
fi

# Clean up
rm -f "$TEMP_SECRET"

echo ""
log_success "Secrets setup complete"
echo ""
log_info "Next steps:"
echo "  1. If using sealed-secrets, apply the sealed secret:"
echo "     kubectl apply -f $SCRIPT_DIR/k8s/sealed-secrets.yaml"
echo "  2. Verify the secret exists:"
echo "     kubectl get secret truematch-secrets -n $NAMESPACE"
echo "  3. List secret keys:"
echo "     kubectl get secret truematch-secrets -n $NAMESPACE -o jsonpath='{.data}' | jq 'keys'"
