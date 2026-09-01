# TrueMatch Admin Dashboard - Docker Deployment Guide

**Status**: ✅ Production Ready  
**Date**: September 2, 2026  
**Version**: 1.0.0  
**Environment**: Production

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Prerequisites](#prerequisites)
3. [Configuration](#configuration)
4. [Deployment Methods](#deployment-methods)
5. [Post-Deployment](#post-deployment)
6. [Troubleshooting](#troubleshooting)
7. [Monitoring](#monitoring)

---

## Quick Start

```bash
# 1. Configure production environment
cd web
cp .env.production.template .env.production
# Edit .env.production with production secrets

# 2. Make deployment script executable
chmod +x scripts/deploy-docker.sh

# 3. Build and deploy
./scripts/deploy-docker.sh

# 4. Verify deployment
docker ps | grep admin-dashboard
curl http://localhost:3000
```

---

## Prerequisites

### Required Tools
- Docker 20.10+
- Docker Compose 2.0+
- Git
- Bash

### Required Credentials
- Docker Registry credentials (if pushing to registry)
- Production NextAuth secret
- Production API token
- Production backend URL

### Infrastructure Requirements
- Linux server or Docker host with 2+ CPU cores
- 2GB+ RAM
- 10GB+ disk space
- Network access to backend API
- SSL/TLS reverse proxy (Nginx, HAProxy, AWS ALB)

---

## Configuration

### Step 1: Create Production Environment File

```bash
cp web/.env.production.template web/.env.production
```

### Step 2: Edit Production Secrets

Edit `web/.env.production` with actual production values:

```env
# Generate a secure random string for NEXTAUTH_SECRET
NEXTAUTH_SECRET=<generate-with: openssl rand -base64 32>

# Production URLs
NEXTAUTH_URL=https://admin.truematch.ai
BACKEND_API_URL=https://api.truematch.ai/v1
NEXT_PUBLIC_API_BASE_URL=/api

# API Authentication
BACKEND_API_TOKEN=<get-from-backend-team>
```

### Step 3: Verify Configuration

```bash
# Check all required variables are set
grep -E "your-|<|>" web/.env.production && echo "ERROR: Placeholder values found!" || echo "✓ All secrets configured"
```

---

## Deployment Methods

### Method 1: Docker Compose (Recommended for Single Host)

**Advantages:**
- Simple single-host deployment
- Easy to manage
- Built-in container orchestration

**Steps:**

```bash
# 1. Navigate to repository root
cd /path/to/truematchAI

# 2. Build and start containers
docker-compose -f docker-compose.production.yml up -d

# 3. Check status
docker-compose -f docker-compose.production.yml ps

# 4. View logs
docker-compose -f docker-compose.production.yml logs -f admin-dashboard

# 5. Stop deployment
docker-compose -f docker-compose.production.yml down
```

**Health Check:**
```bash
curl http://localhost:3000
```

---

### Method 2: Docker Registry + Docker Run (Multi-Host)

**Advantages:**
- Deploy across multiple servers
- Version control via tags
- Easy rollbacks

**Steps:**

```bash
# 1. Build image
docker build -f web/Dockerfile.production -t truematch/admin-dashboard:1.0.0 ./web

# 2. Tag for registry
docker tag truematch/admin-dashboard:1.0.0 docker.io/truematch/admin-dashboard:1.0.0
docker tag truematch/admin-dashboard:1.0.0 docker.io/truematch/admin-dashboard:latest

# 3. Push to registry
docker login docker.io
docker push docker.io/truematch/admin-dashboard:1.0.0
docker push docker.io/truematch/admin-dashboard:latest

# 4. On production server, pull and run
docker pull docker.io/truematch/admin-dashboard:latest

docker run -d \
  --name truematch-admin-dashboard \
  --restart always \
  --env-file web/.env.production \
  -p 3000:3000 \
  --health-cmd="curl -f http://localhost:3000 || exit 1" \
  --health-interval=30s \
  --health-timeout=3s \
  --health-retries=3 \
  docker.io/truematch/admin-dashboard:latest
```

---

### Method 3: Kubernetes (Enterprise)

**Advantages:**
- High availability
- Auto-scaling
- Self-healing
- Rolling updates

**Steps:**

```bash
# 1. Create namespace
kubectl apply -f k8s/admin-dashboard-deployment.yaml

# 2. Verify deployment
kubectl get deployments -n truematch
kubectl get pods -n truematch
kubectl get svc -n truematch

# 3. Check pod status
kubectl describe pod -n truematch -l app=admin-dashboard

# 4. View logs
kubectl logs -n truematch -l app=admin-dashboard -f

# 5. Port forward for testing
kubectl port-forward -n truematch svc/admin-dashboard 3000:80
```

**Ingress Configuration (Nginx):**

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: admin-dashboard-ingress
  namespace: truematch
spec:
  ingressClassName: nginx
  rules:
  - host: admin.truematch.ai
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: admin-dashboard
            port:
              number: 80
  tls:
  - hosts:
    - admin.truematch.ai
    secretName: admin-dashboard-tls
```

---

## Post-Deployment

### Verification Checklist

```bash
# 1. Container is running
docker ps | grep admin-dashboard || echo "FAILED"

# 2. Health check passes
curl -I http://localhost:3000 | grep "200\|301" || echo "FAILED"

# 3. Environment variables loaded
docker exec truematch-admin-dashboard env | grep NEXTAUTH_URL || echo "FAILED"

# 4. API connectivity
curl -I http://localhost:3000/api/health || echo "Check API connectivity"

# 5. Check logs for errors
docker logs truematch-admin-dashboard 2>&1 | grep -i "error\|critical" || echo "No errors found"
```

### Create Reverse Proxy Configuration

**Nginx Example:**

```nginx
upstream admin_dashboard {
    server localhost:3000;
}

server {
    listen 80;
    server_name admin.truematch.ai;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name admin.truematch.ai;

    ssl_certificate /etc/ssl/certs/admin.truematch.ai.crt;
    ssl_certificate_key /etc/ssl/private/admin.truematch.ai.key;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;

    location / {
        proxy_pass http://admin_dashboard;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $server_name;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

---

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker logs truematch-admin-dashboard

# Common issues:
# 1. Missing environment variables
docker inspect truematch-admin-dashboard | grep Env

# 2. Port already in use
lsof -i :3000

# 3. Insufficient memory
docker stats
```

### API Connectivity Issues

```bash
# Check backend connectivity
curl -v https://api.truematch.ai/v1/health

# Verify environment variables
docker exec truematch-admin-dashboard env | grep BACKEND_API

# Check network connectivity
docker exec truematch-admin-dashboard ping api.truematch.ai
```

### Performance Issues

```bash
# Check resource usage
docker stats truematch-admin-dashboard

# Increase memory/CPU limits
docker update --memory 2g --memory-swap 2g --cpus 2 truematch-admin-dashboard

# Check for errors
docker logs truematch-admin-dashboard | tail -100
```

### Authentication Issues

```bash
# Verify NEXTAUTH_SECRET is set
docker exec truematch-admin-dashboard env | grep NEXTAUTH_SECRET

# Check NextAuth logs
docker logs truematch-admin-dashboard | grep -i auth
```

---

## Monitoring

### Container Health

```bash
# Real-time monitoring
docker stats truematch-admin-dashboard

# Health status
docker inspect --format='{{.State.Health.Status}}' truematch-admin-dashboard

# Restart count
docker inspect --format='{{.RestartCount}}' truematch-admin-dashboard
```

### Application Logs

```bash
# Stream logs
docker logs -f truematch-admin-dashboard

# Last 100 lines
docker logs --tail 100 truematch-admin-dashboard

# Timestamp and tail
docker logs -f --timestamps truematch-admin-dashboard
```

### Performance Metrics

```bash
# CPU and Memory
docker stats --no-stream truematch-admin-dashboard

# Network
docker exec truematch-admin-dashboard cat /proc/net/dev

# Disk usage
docker exec truematch-admin-dashboard du -sh /app
```

### Recommended Monitoring Stack

1. **Prometheus** - Metrics collection
2. **Grafana** - Visualization
3. **Loki** - Log aggregation
4. **AlertManager** - Alerting

### Logging Setup

```bash
# Docker logging driver
docker run -d \
  --log-driver=splunk \
  --log-opt splunk-token=<token> \
  --log-opt splunk-url=<url> \
  truematch/admin-dashboard:latest

# Or use syslog
docker run -d \
  --log-driver=syslog \
  --log-opt syslog-address=udp://127.0.0.1:514 \
  truematch/admin-dashboard:latest
```

---

## Backup & Recovery

### Create Image Backup

```bash
# Save image
docker save truematch/admin-dashboard:latest | gzip > admin-dashboard-backup.tar.gz

# Load from backup
docker load < admin-dashboard-backup.tar.gz
```

### Database Backup (if applicable)

```bash
# Backup Docker volumes
docker run --rm -v admin-dashboard-data:/data \
  -v $(pwd):/backup alpine \
  tar czf /backup/admin-dashboard-data.tar.gz /data
```

---

## Security Considerations

### Network Security
- ✅ Use HTTPS only
- ✅ Implement WAF rules
- ✅ Rate limiting
- ✅ DDoS protection

### Container Security
- ✅ Non-root user (UID 1000)
- ✅ Read-only filesystem (where possible)
- ✅ Security context restrictions
- ✅ Regular vulnerability scans

### Secrets Management
- ✅ Use Docker secrets (Swarm) or K8s secrets
- ✅ Never commit secrets to git
- ✅ Rotate API tokens regularly
- ✅ Audit access logs

---

## Rollback Procedure

```bash
# If deployment fails:

# 1. Stop current deployment
docker-compose -f docker-compose.production.yml down

# 2. Remove current image
docker rmi docker.io/truematch/admin-dashboard:latest

# 3. Pull previous version
docker pull docker.io/truematch/admin-dashboard:v1.0.0-prev

# 4. Tag as latest
docker tag docker.io/truematch/admin-dashboard:v1.0.0-prev \
  docker.io/truematch/admin-dashboard:latest

# 5. Restart deployment
docker-compose -f docker-compose.production.yml up -d
```

---

## Support & Documentation

- **Repository**: https://github.com/rezcarbon/truematchAI
- **Issues**: Report issues on GitHub
- **Documentation**: See `/docs` directory
- **Status Page**: https://status.truematch.ai

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-09-02 | Initial production release |
| 0.9.0 | 2026-09-01 | Beta version |

---

**Deployment Status**: ✅ READY FOR PRODUCTION  
**Last Updated**: September 2, 2026  
**Next Review**: September 9, 2026
