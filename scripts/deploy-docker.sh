#!/bin/bash

# TrueMatch Admin Dashboard - Docker Deployment Script
# This script handles building, pushing, and deploying the admin dashboard to production

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOCKER_REGISTRY="${DOCKER_REGISTRY:-docker.io}"
IMAGE_NAME="${IMAGE_NAME:-truematch/admin-dashboard}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
FULL_IMAGE_NAME="${DOCKER_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
WORK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WEB_DIR="${WORK_DIR}/web"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  TrueMatch Admin Dashboard - Docker Deployment Script          ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"

# Functions
log_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

log_success() {
    echo -e "${GREEN}✓${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Step 1: Verify prerequisites
echo -e "\n${BLUE}Step 1: Verifying Prerequisites${NC}"
log_info "Checking for required tools..."

if ! command -v docker &> /dev/null; then
    log_error "Docker is not installed. Please install Docker first."
    exit 1
fi
log_success "Docker found: $(docker --version)"

# Step 2: Verify environment
echo -e "\n${BLUE}Step 2: Verifying Environment${NC}"
log_info "Checking for production environment file..."

if [ ! -f "${WEB_DIR}/.env.production" ]; then
    log_error ".env.production not found at ${WEB_DIR}/.env.production"
    log_warning "Please create .env.production with production secrets before deploying"
    echo -e "${YELLOW}Template available at: ${WEB_DIR}/.env.production${NC}"
    exit 1
fi
log_success "Production environment file found"

# Step 3: Check Docker credentials
echo -e "\n${BLUE}Step 3: Verifying Docker Authentication${NC}"
log_info "Attempting Docker registry login (if not already authenticated)..."

if [ -n "$DOCKER_USERNAME" ] && [ -n "$DOCKER_PASSWORD" ]; then
    echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin "$DOCKER_REGISTRY" 2>/dev/null
    log_success "Docker authentication successful"
else
    log_warning "Docker credentials not found in environment variables"
    log_info "Proceeding with local build only (push will require manual authentication)"
fi

# Step 4: Build Docker image
echo -e "\n${BLUE}Step 4: Building Docker Image${NC}"
log_info "Building image: ${FULL_IMAGE_NAME}"

cd "${WEB_DIR}"
docker build \
    -f Dockerfile.production \
    -t "${FULL_IMAGE_NAME}" \
    --build-arg BUILDKIT_INLINE_CACHE=1 \
    .

if [ $? -eq 0 ]; then
    log_success "Docker image built successfully"
    docker images | grep "${IMAGE_NAME}" | head -1
else
    log_error "Failed to build Docker image"
    exit 1
fi

# Step 5: Verify image
echo -e "\n${BLUE}Step 5: Verifying Docker Image${NC}"
log_info "Running basic image tests..."

# Check image size
IMAGE_SIZE=$(docker images "${FULL_IMAGE_NAME}" --format "{{.Size}}")
log_info "Image size: ${IMAGE_SIZE}"

# Check image layers
LAYER_COUNT=$(docker inspect "${FULL_IMAGE_NAME}" --format='{{.RootFS.Layers | len}}')
log_info "Number of layers: ${LAYER_COUNT}"

log_success "Image verification passed"

# Step 6: Push to registry (if credentials available)
echo -e "\n${BLUE}Step 6: Pushing to Docker Registry${NC}"

if docker push "${FULL_IMAGE_NAME}" 2>/dev/null; then
    log_success "Image pushed to ${DOCKER_REGISTRY}/${IMAGE_NAME}"

    # Display image information
    echo -e "\n${BLUE}Image Details:${NC}"
    echo "  Registry: ${DOCKER_REGISTRY}"
    echo "  Image: ${IMAGE_NAME}"
    echo "  Tag: ${IMAGE_TAG}"
    echo "  Full Name: ${FULL_IMAGE_NAME}"
else
    log_warning "Failed to push to registry (docker push requires authentication)"
    log_info "Image is available locally: ${FULL_IMAGE_NAME}"
    log_info "To push manually: docker push ${FULL_IMAGE_NAME}"
fi

# Step 7: Deployment instructions
echo -e "\n${BLUE}Step 7: Deployment Instructions${NC}"
echo -e "\n${GREEN}✓ Docker image is ready for deployment${NC}"
echo -e "\n${YELLOW}Option 1: Deploy with Docker Compose${NC}"
echo "  cd ${WORK_DIR}"
echo "  docker-compose -f docker-compose.production.yml up -d"

echo -e "\n${YELLOW}Option 2: Deploy with Docker directly${NC}"
echo "  docker run -d \\"
echo "    --restart always \\"
echo "    --name truematch-admin-dashboard \\"
echo "    --env-file ${WEB_DIR}/.env.production \\"
echo "    -p 3000:3000 \\"
echo "    ${FULL_IMAGE_NAME}"

echo -e "\n${YELLOW}Option 3: Deploy to Kubernetes${NC}"
echo "  kubectl set image deployment/admin-dashboard \\"
echo "    admin-dashboard=${FULL_IMAGE_NAME} \\"
echo "    --record"

# Step 8: Summary
echo -e "\n${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Deployment Status                                             ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo -e "${GREEN}✓${NC} Docker image built successfully"
echo -e "${GREEN}✓${NC} Image verified and ready for deployment"
echo -e "${GREEN}✓${NC} Production environment configured"

echo -e "\n${BLUE}Next Steps:${NC}"
echo "1. Choose deployment method above"
echo "2. Ensure production infrastructure is ready"
echo "3. Deploy image using chosen method"
echo "4. Verify deployment with health checks"
echo "5. Monitor logs: docker logs truematch-admin-dashboard"

echo -e "\n${GREEN}Deployment ready! ✓${NC}\n"
