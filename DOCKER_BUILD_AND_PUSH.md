# Docker Build and Push Guide
## TrueMatch AI - Container Image Management

**Version:** 1.0  
**Last Updated:** July 21, 2026  

---

## 1. Dockerfile Review & Optimization

### 1.1 Current Dockerfile Analysis

**Location:** `backend/Dockerfile`

```dockerfile
# PRODUCTION-OPTIMIZED DOCKERFILE
FROM python:3.12-slim AS base

# Environment variables for Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Install build dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies (cached layer)
COPY pyproject.toml ./
COPY app ./app
RUN pip install --upgrade pip && pip install .

# Copy application code
COPY alembic.ini ./
COPY alembic ./alembic
COPY governance ./governance

# Create non-root user
RUN useradd --create-home --uid 10001 appuser
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://localhost:8000/livez || exit 1

# Default command (can be overridden)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 1.2 Optimization Recommendations

**Current:** ✓ GOOD
- Uses python:3.12-slim (minimal base image)
- Non-root user (security best practice)
- Multi-stage build (implied by FROM)
- Dependency caching (pyproject.toml copied first)
- Health checks included

**Recommended Enhancements:**

```dockerfile
# Multi-stage build (explicit) for smaller final image
FROM python:3.12-slim AS builder

# Build dependencies only
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential libpq-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY pyproject.toml ./
RUN pip install --user --no-cache-dir -e .

# Final stage
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH=/root/.local/bin:$PATH

# Only runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy pip cache from builder
COPY --from=builder /root/.local /root/.local

# Copy application
COPY alembic.ini ./
COPY alembic ./alembic
COPY app ./app
COPY governance ./governance

# Create non-root user
RUN useradd --create-home --uid 10001 appuser
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://localhost:8000/livez || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 1.3 Build Arguments

```dockerfile
# Add build args for flexibility
ARG PYTHON_VERSION=3.12
ARG BASE_IMAGE=python:${PYTHON_VERSION}-slim

FROM ${BASE_IMAGE}

# Build-time info
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION

LABEL org.label-schema.build-date=$BUILD_DATE \
      org.label-schema.name="truematch-api" \
      org.label-schema.vcs-ref=$VCS_REF \
      org.label-schema.version=$VERSION
```

---

## 2. Docker Image Build Procedures

### 2.1 Local Development Build

```bash
# Build with default settings
docker build -t truematch-api:latest -f backend/Dockerfile .

# Build with custom tag
docker build -t truematch-api:v1.2.3 -f backend/Dockerfile .

# Build with build args
docker build \
  --build-arg PYTHON_VERSION=3.12 \
  --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
  --build-arg VCS_REF=$(git rev-parse --short HEAD) \
  --build-arg VERSION=v1.2.3 \
  -t truematch-api:v1.2.3 \
  -f backend/Dockerfile .

# Build with progress output
docker build --progress=plain -t truematch-api:v1.2.3 -f backend/Dockerfile .

# Verify image
docker images | grep truematch-api
docker inspect truematch-api:v1.2.3
```

### 2.2 Build Optimization Techniques

```bash
# 1. Use BuildKit for faster builds
export DOCKER_BUILDKIT=1
docker build -t truematch-api:v1.2.3 -f backend/Dockerfile .

# 2. Build with cache persistence
docker build \
  --cache-from truematch-api:latest \
  -t truematch-api:v1.2.3 \
  -f backend/Dockerfile .

# 3. Build specific stage only
docker build \
  --target builder \
  -t truematch-api-build:latest \
  -f backend/Dockerfile .

# 4. Build without cache (for clean build)
docker build --no-cache -t truematch-api:v1.2.3 -f backend/Dockerfile .
```

### 2.3 Docker Compose Build

```bash
# Build all services
cd backend
docker compose build

# Build specific service
docker compose build api

# Build with no cache
docker compose build --no-cache

# Build and up
docker compose up --build
```

### 2.4 Build Testing

```bash
# Test image locally
docker run -it \
  -e ENVIRONMENT=development \
  -e DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/test \
  -e REDIS_URL=redis://localhost:6379/0 \
  -p 8000:8000 \
  truematch-api:v1.2.3

# Run health check
curl http://localhost:8000/livez

# Run tests in container
docker run --rm \
  -v $(pwd)/backend:/app \
  truematch-api:v1.2.3 \
  pytest

# Run migrations
docker run --rm \
  -e DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/test \
  truematch-api:v1.2.3 \
  alembic upgrade head
```

---

## 3. ECR Repository Setup

### 3.1 Create ECR Repositories

```bash
# Create repository for API
aws ecr create-repository \
  --repository-name truematch-api \
  --region us-east-1 \
  --encryption-configuration encryptionType=KMS \
  --image-scan-config scanOnPush=true \
  --image-tag-mutability IMMUTABLE

# Output:
# {
#     "repository": {
#         "repositoryUri": "123456789012.dkr.ecr.us-east-1.amazonaws.com/truematch-api",
#         ...
#     }
# }

# Create repository for web
aws ecr create-repository \
  --repository-name truematch-web \
  --region us-east-1 \
  --encryption-configuration encryptionType=KMS \
  --image-scan-config scanOnPush=true \
  --image-tag-mutability IMMUTABLE

# List repositories
aws ecr describe-repositories --region us-east-1
```

### 3.2 Configure ECR Lifecycle Policies

```bash
# Save lifecycle policy to file
cat > ecr-lifecycle.json << 'EOF'
{
  "rules": [
    {
      "rulePriority": 1,
      "description": "Keep last 10 images with 'latest' tag",
      "selection": {
        "tagStatus": "tagged",
        "tagPrefixList": ["latest"],
        "countType": "imageCountMoreThan",
        "countNumber": 10
      },
      "action": {
        "type": "expire"
      }
    },
    {
      "rulePriority": 2,
      "description": "Keep last 5 images with 'v' tag (releases)",
      "selection": {
        "tagStatus": "tagged",
        "tagPrefixList": ["v"],
        "countType": "imageCountMoreThan",
        "countNumber": 5
      },
      "action": {
        "type": "expire"
      }
    },
    {
      "rulePriority": 3,
      "description": "Delete untagged images after 7 days",
      "selection": {
        "tagStatus": "untagged",
        "countType": "sinceImagePushed",
        "countUnit": "days",
        "countNumber": 7
      },
      "action": {
        "type": "expire"
      }
    }
  ]
}
EOF

# Apply lifecycle policy
aws ecr put-lifecycle-policy \
  --repository-name truematch-api \
  --lifecycle-policy-text file://ecr-lifecycle.json \
  --region us-east-1
```

### 3.3 Enable Image Scanning

```bash
# Enable scanning on push
aws ecr put-image-scanning-configuration \
  --repository-name truematch-api \
  --image-scan-config scanOnPush=true \
  --region us-east-1

# Check scan results
aws ecr describe-image-scan-findings \
  --repository-name truematch-api \
  --image-id imageTag=v1.2.3 \
  --region us-east-1
```

---

## 4. Image Tagging Strategy

### 4.1 Tagging Conventions

```bash
# Base image URI
REGISTRY=123456789012.dkr.ecr.us-east-1.amazonaws.com
REPO=truematch-api

# Tag formats
# 1. Latest development
docker tag truematch-api:latest \
  $REGISTRY/$REPO:latest

# 2. Release version (semantic versioning)
docker tag truematch-api:latest \
  $REGISTRY/$REPO:v1.2.3

# 3. Major version
docker tag truematch-api:latest \
  $REGISTRY/$REPO:v1.2

# 4. Git commit SHA
docker tag truematch-api:latest \
  $REGISTRY/$REPO:sha-a1b2c3d

# 5. Build date
docker tag truematch-api:latest \
  $REGISTRY/$REPO:2026-07-21

# 6. Environment-specific
docker tag truematch-api:latest \
  $REGISTRY/$REPO:prod

docker tag truematch-api:latest \
  $REGISTRY/$REPO:staging
```

### 4.2 Automated Tagging Script

```bash
#!/bin/bash
# tag-image.sh

set -e

# Configuration
REGISTRY="123456789012.dkr.ecr.us-east-1.amazonaws.com"
REPO="truematch-api"
LOCAL_IMAGE="truematch-api:latest"
VERSION="v$(git describe --tags --abbrev=0 2>/dev/null || echo '1.0.0')"
GIT_SHA="sha-$(git rev-parse --short HEAD)"
BUILD_DATE=$(date -u +'%Y-%m-%d')

# Authenticate with ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin $REGISTRY

# Tag image
docker tag $LOCAL_IMAGE $REGISTRY/$REPO:latest
docker tag $LOCAL_IMAGE $REGISTRY/$REPO:$VERSION
docker tag $LOCAL_IMAGE $REGISTRY/$REPO:$GIT_SHA
docker tag $LOCAL_IMAGE $REGISTRY/$REPO:$BUILD_DATE

# Verify tags
echo "✓ Image tagged:"
docker images | grep $REGISTRY/$REPO

# List all tags
aws ecr list-images --repository-name $REPO --region us-east-1
```

---

## 5. Push to ECR

### 5.1 Simple Push

```bash
# 1. Authenticate
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  123456789012.dkr.ecr.us-east-1.amazonaws.com

# 2. Tag image
docker tag truematch-api:latest \
  123456789012.dkr.ecr.us-east-1.amazonaws.com/truematch-api:v1.2.3

# 3. Push to ECR
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/truematch-api:v1.2.3

# Output:
# The push refers to repository [123456789012.dkr.ecr.us-east-1.amazonaws.com/truematch-api]
# a1b2c3d: Pushed
# e4f5g6h: Pushed
# ...
# v1.2.3: digest: sha256:... size: 1234
```

### 5.2 Comprehensive Push Script

```bash
#!/bin/bash
# push-to-ecr.sh

set -euo pipefail

REGISTRY="${REGISTRY:-123456789012.dkr.ecr.us-east-1.amazonaws.com}"
REPO="${REPO:-truematch-api}"
REGION="${REGION:-us-east-1}"
LOCAL_IMAGE="${LOCAL_IMAGE:-truematch-api:latest}"
VERSION="${VERSION:-v1.2.3}"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $1"; }
log_success() { echo -e "${GREEN}[$(date +'%H:%M:%S')] ✓${NC} $1"; }

log "Starting ECR push..."
log "Registry: $REGISTRY"
log "Repository: $REPO"
log "Version: $VERSION"

# 1. Authenticate
log "Authenticating with ECR..."
aws ecr get-login-password --region $REGION | \
  docker login --username AWS --password-stdin $REGISTRY
log_success "Authenticated"

# 2. Tag image
log "Tagging image..."
docker tag $LOCAL_IMAGE $REGISTRY/$REPO:$VERSION
docker tag $LOCAL_IMAGE $REGISTRY/$REPO:latest
log_success "Tagged: $REGISTRY/$REPO:$VERSION"

# 3. Push image
log "Pushing to ECR..."
docker push $REGISTRY/$REPO:$VERSION
docker push $REGISTRY/$REPO:latest
log_success "Pushed"

# 4. Verify
log "Verifying push..."
aws ecr describe-images \
  --repository-name $REPO \
  --image-ids imageTag=$VERSION \
  --region $REGION

log_success "Image push complete!"
log "Image URI: $REGISTRY/$REPO:$VERSION"
```

### 5.3 Verify Push

```bash
# List images in repository
aws ecr list-images \
  --repository-name truematch-api \
  --region us-east-1

# Describe specific image
aws ecr describe-images \
  --repository-name truematch-api \
  --image-ids imageTag=v1.2.3 \
  --region us-east-1

# Check image size
aws ecr describe-images \
  --repository-name truematch-api \
  --query 'imageDetails[0].imageSizeBytes' \
  --region us-east-1

# Check scan findings
aws ecr describe-image-scan-findings \
  --repository-name truematch-api \
  --image-id imageTag=v1.2.3 \
  --region us-east-1
```

---

## 6. CI/CD Integration

### 6.1 GitHub Actions Workflow

```yaml
# .github/workflows/build-push.yml
name: Build & Push to ECR

on:
  push:
    branches: [main]
    tags: [v*]

env:
  AWS_REGION: us-east-1
  REGISTRY: ${{ secrets.AWS_ACCOUNT_ID }}.dkr.ecr.us-east-1.amazonaws.com
  REPO_API: truematch-api
  REPO_WEB: truematch-web

jobs:
  build-api:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      id-token: write
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_TO_ASSUME }}
          aws-region: ${{ env.AWS_REGION }}
      
      - name: Login to ECR
        run: |
          aws ecr get-login-password --region ${{ env.AWS_REGION }} | \
            docker login --username AWS --password-stdin ${{ env.REGISTRY }}
      
      - name: Build image
        run: |
          docker build \
            --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
            --build-arg VCS_REF=${{ github.sha }} \
            --build-arg VERSION=${{ github.ref_name }} \
            -t ${{ env.REGISTRY }}/${{ env.REPO_API }}:latest \
            -f backend/Dockerfile .
      
      - name: Tag image
        run: |
          docker tag \
            ${{ env.REGISTRY }}/${{ env.REPO_API }}:latest \
            ${{ env.REGISTRY }}/${{ env.REPO_API }}:${{ github.sha }}
          
          if [[ ${{ github.ref }} == refs/tags/v* ]]; then
            docker tag \
              ${{ env.REGISTRY }}/${{ env.REPO_API }}:latest \
              ${{ env.REGISTRY }}/${{ env.REPO_API }}:${{ github.ref_name }}
          fi
      
      - name: Push to ECR
        run: |
          docker push ${{ env.REGISTRY }}/${{ env.REPO_API }}:latest
          docker push ${{ env.REGISTRY }}/${{ env.REPO_API }}:${{ github.sha }}
          if [[ ${{ github.ref }} == refs/tags/v* ]]; then
            docker push ${{ env.REGISTRY }}/${{ env.REPO_API }}:${{ github.ref_name }}
          fi
      
      - name: Verify image
        run: |
          aws ecr describe-images \
            --repository-name ${{ env.REPO_API }} \
            --image-ids imageTag=${{ github.sha }}
```

---

## 7. Image Security Scanning

### 7.1 Enable Trivy Scanning

```bash
# Install Trivy
brew install aquasecurity/trivy/trivy

# Scan local image
trivy image truematch-api:v1.2.3

# Scan with JSON output
trivy image --format json --output report.json truematch-api:v1.2.3

# Scan remote image from ECR
trivy image \
  123456789012.dkr.ecr.us-east-1.amazonaws.com/truematch-api:v1.2.3
```

### 7.2 ECR Scanning Results

```bash
# Get scan findings
aws ecr describe-image-scan-findings \
  --repository-name truematch-api \
  --image-id imageTag=v1.2.3 \
  --region us-east-1 \
  --query 'imageScanFindings.findings'

# Check severity
aws ecr describe-image-scan-findings \
  --repository-name truematch-api \
  --image-id imageTag=v1.2.3 \
  --region us-east-1 \
  --query 'imageScanFindings.[findingDetails[].{Severity:severity}]'
```

---

## 8. Troubleshooting

### 8.1 Build Issues

```bash
# Error: "denied: User is not authorized"
# Solution: Re-login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin $REGISTRY

# Error: "repository not found"
# Solution: Create ECR repository first
aws ecr create-repository --repository-name truematch-api

# Error: "requested image not found"
# Solution: Check image name/tag
docker images | grep truematch-api

# Error: Out of memory during build
# Solution: Increase Docker memory or use BuildKit cache
export DOCKER_BUILDKIT=1
docker build --cache-from truematch-api:latest ...
```

### 8.2 Push Issues

```bash
# Error: "net/http: request canceled"
# Solution: Check network connectivity and increase timeout
docker push --timeout 600 $REGISTRY/$REPO:$TAG

# Error: "manifest too large"
# Solution: Image too large, optimize Dockerfile
docker images | grep truematch-api  # Check size

# Error: "permission denied"
# Solution: Check IAM permissions
aws sts get-caller-identity
```

---

## 9. Image Maintenance

### 9.1 Clean Up Old Images

```bash
# Remove local images
docker rmi truematch-api:v1.0.0
docker rmi $(docker images | grep truematch | awk '{print $3}')

# Remove untagged images
docker rmi $(docker images | grep '<none>' | awk '{print $3}')

# ECR cleanup (via lifecycle policy)
# Images are auto-deleted based on lifecycle policy

# Manual deletion
aws ecr batch-delete-image \
  --repository-name truematch-api \
  --image-ids imageTag=old-version \
  --region us-east-1
```

### 9.2 Image Vulnerability Management

```bash
# Regular scanning (automated via ECR scan-on-push)
# Check scan results:
aws ecr describe-image-scan-findings \
  --repository-name truematch-api \
  --image-id imageTag=v1.2.3 \
  --region us-east-1

# Update base image
# 1. Update Dockerfile base image version
# 2. Rebuild and test
# 3. Push new version

# Monitor for CVEs
aws inspector start-assessment-run \
  --assessment-template-arn arn:aws:inspector:...
```

---

## 10. Quick Reference

```bash
# BUILD
docker build -t truematch-api:v1.2.3 -f backend/Dockerfile .

# LOGIN
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com

# TAG
docker tag truematch-api:v1.2.3 \
  123456789012.dkr.ecr.us-east-1.amazonaws.com/truematch-api:v1.2.3

# PUSH
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/truematch-api:v1.2.3

# VERIFY
aws ecr list-images --repository-name truematch-api
```

---

*Docker Build & Push Guide - Complete. Proceed to environment secrets setup.*
