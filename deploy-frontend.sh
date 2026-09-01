#!/bin/bash

# TrueMatch Frontend Deployment Script
# Deploys Next.js frontend to AWS S3 + CloudFront CDN
# Usage: ./deploy-frontend.sh [staging|production]

set -e

ENVIRONMENT=${1:-production}
REGION=${AWS_REGION:-us-east-1}
PROJECT_NAME=truematch

echo "════════════════════════════════════════════════════════════════"
echo "🚀 TRUEMATCH FRONTEND DEPLOYMENT"
echo "════════════════════════════════════════════════════════════════"
echo "Environment: $ENVIRONMENT"
echo "Region: $REGION"
echo "Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"

# Verify AWS credentials
echo ""
echo "🔐 Verifying AWS credentials..."
aws sts get-caller-identity 2>&1 | head -3

# Determine bucket and distribution names
if [ "$ENVIRONMENT" = "production" ]; then
  S3_BUCKET="${PROJECT_NAME}-frontend-prod"
  CLOUDFRONT_DISTRIBUTION="E3VH8Z9M2K4L5J"  # Replace with your distribution ID
  CDN_URL="https://truematch.ai"
else
  S3_BUCKET="${PROJECT_NAME}-frontend-staging"
  CLOUDFRONT_DISTRIBUTION="E1A2B3C4D5E6F7G"  # Replace with your distribution ID
  CDN_URL="https://staging.truematch.ai"
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "📦 PREPARING BUILD ARTIFACTS"
echo "════════════════════════════════════════════════════════════════"

cd "$(dirname "$0")"
cd web

# Rebuild frontend
echo "Building frontend..."
npm run build

# Create deployment package
echo "Creating deployment package..."
tar -czf /tmp/frontend-build.tar.gz .next/

echo "✅ Build artifacts ready ($(du -h /tmp/frontend-build.tar.gz | cut -f1))"

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "☁️  UPLOADING TO S3"
echo "════════════════════════════════════════════════════════════════"

# Sync .next/static files to S3 with aggressive caching
aws s3 sync .next/static "s3://${S3_BUCKET}/static/" \
  --region "$REGION" \
  --cache-control "public, max-age=31536000, immutable" \
  --delete \
  --exclude "*.map" \
  --quiet

echo "✅ Static files uploaded (1-year cache)"

# Upload server-side files with short caching
aws s3 sync .next/server "s3://${S3_BUCKET}/server/" \
  --region "$REGION" \
  --cache-control "public, max-age=3600" \
  --delete \
  --quiet

echo "✅ Server files uploaded (1-hour cache)"

# Upload root files
aws s3 cp .next/package.json "s3://${S3_BUCKET}/" \
  --region "$REGION" \
  --cache-control "public, max-age=3600" \
  --quiet

echo "✅ Root files uploaded"

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "🔄 INVALIDATING CLOUDFRONT CACHE"
echo "════════════════════════════════════════════════════════════════"

# Invalidate CloudFront distribution
aws cloudfront create-invalidation \
  --distribution-id "$CLOUDFRONT_DISTRIBUTION" \
  --paths "/*" \
  --query 'Invalidation.Id' \
  --output text

echo "✅ Cache invalidation triggered"

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "✨ DEPLOYMENT COMPLETE"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "Frontend URL: $CDN_URL"
echo "S3 Bucket: $S3_BUCKET"
echo "CloudFront Distribution: $CLOUDFRONT_DISTRIBUTION"
echo ""
echo "📊 Deployment Summary:"
echo "  - Static files: 1-year cache (immutable)"
echo "  - Server files: 1-hour cache"
echo "  - CloudFront CDN: ✅ Cache invalidated"
echo ""
echo "🔍 Verification:"
echo "  1. Check CloudFront distribution: $CDN_URL"
echo "  2. Verify assets load correctly"
echo "  3. Monitor CloudWatch metrics for latency"
