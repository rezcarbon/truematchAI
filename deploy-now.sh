#!/bin/bash

# TrueMatch Complete Deployment Script
# Deploys Admin Dashboard + Recruiter Dashboard + Billing System to EC2

set -e

EC2_HOST="${1:-}"
EC2_USER="${2:-ubuntu}"
SSH_KEY="${3:-$HOME/.ssh/truematch-staging-key.pem}"

if [[ -z "$EC2_HOST" ]]; then
    echo "Usage: $0 <EC2_HOST> [EC2_USER] [SSH_KEY]"
    echo "Example: $0 ec2-54-123-45-67.compute.amazonaws.com ubuntu ~/.ssh/truematch-staging-key.pem"
    exit 1
fi

echo "=========================================="
echo "TrueMatch Complete Deployment"
echo "=========================================="
echo "EC2 Host: $EC2_HOST"
echo "EC2 User: $EC2_USER"
echo "SSH Key: $SSH_KEY"
echo ""

# Verify SSH key exists
if [[ ! -f "$SSH_KEY" ]]; then
    echo "❌ SSH key not found: $SSH_KEY"
    exit 1
fi

echo "✓ SSH key found"
echo "✓ Starting deployment..."
echo ""

# Run the main deployment script
./scripts/deploy-ec2.sh "$EC2_USER@$EC2_HOST" main web/.env.production
