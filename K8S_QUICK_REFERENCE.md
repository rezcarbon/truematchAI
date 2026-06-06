# TrueMatch Kubernetes Quick Reference

## One-Line Deployment

```bash
# Development
./scripts/deploy.sh dev install

# Staging
./scripts/deploy.sh staging install

# Production
./scripts/deploy.sh prod install
```

## File Organization

| File | Purpose |
|------|---------|
| `k8s/01-namespace.yaml` | Namespace, ServiceAccount, RBAC |
| `k8s/02-config.yaml` | ConfigMaps, Secrets, Prometheus/Loki config |
| `k8s/03-postgres.yaml` | PostgreSQL StatefulSet (100Gi) |
| `k8s/04-redis.yaml` | Redis StatefulSet (50Gi) |
| `k8s/05-migration.yaml` | Database migration Job |
| `k8s/06-api.yaml` | API Deployment (3 replicas) |
| `k8s/07-workers.yaml` | Celery Workers + HPA (3-20 replicas) |
| `k8s/08-ingress.yaml` | HTTPS Ingress, TLS, Network Policies |
| `k8s/09-monitoring.yaml` | Prometheus, Loki, Fluent-bit |

## Essential Commands

### Deployment
```bash
# Install prerequisites
helm repo add jetstack https://charts.jetstack.io
helm install cert-manager jetstack/cert-manager --set installCRDs=true
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm install ingress-nginx ingress-nginx/ingress-nginx

# Deploy with Helm
helm install truematch ./helm/truematch -f helm/truematch/values-prod.yaml -n truematch --create-namespace

# Deploy with manifests
kubectl apply -f k8s/

# Verify
./scripts/verify-deployment.sh
```

### Secrets
```bash
# Interactive setup
./scripts/setup-secrets.sh

# Create manually
kubectl create secret generic truematch-secrets \
  --from-literal=JWT_SECRET='...' \
  --from-literal=DATABASE_PASSWORD='...' \
  -n truematch
```

### Monitoring
```bash
# Prometheus
kubectl port-forward -n truematch svc/prometheus 9090:9090
# Visit http://localhost:9090

# API Logs
kubectl logs -n truematch -l app=api -f

# Worker Logs
kubectl logs -n truematch -l app=worker -f

# Database Logs
kubectl logs -n truematch -l app=postgres -f
```

### Access Services
```bash
# API
kubectl port-forward -n truematch svc/api 8000:80
# curl http://localhost:8000

# Database
kubectl port-forward -n truematch svc/postgres 5432:5432
# psql -h localhost -U truematch -d truematch

# Redis
kubectl port-forward -n truematch svc/redis 6379:6379
# redis-cli -p 6379
```

### Scaling
```bash
# View HPA status
kubectl get hpa -n truematch

# Manual scale API
kubectl scale deployment api --replicas=5 -n truematch

# Manual scale Workers
kubectl scale deployment worker --replicas=10 -n truematch
```

### Updates
```bash
# Update API image
kubectl set image deployment/api api=truematch-api:1.0.1 -n truematch

# Watch rollout
kubectl rollout status deployment/api -n truematch

# Rollback
kubectl rollout undo deployment/api -n truematch

# Helm upgrade
helm upgrade truematch ./helm/truematch -f helm/truematch/values-prod.yaml -n truematch

# Helm rollback
helm rollback truematch -n truematch
```

### Health Checks
```bash
# Pod status
kubectl get pods -n truematch

# Deployment status
kubectl get deployments -n truematch

# Service endpoints
kubectl get svc -n truematch

# PVC status
kubectl get pvc -n truematch

# Resource usage
kubectl top pods -n truematch
kubectl top nodes
```

### Troubleshooting
```bash
# Describe pod
kubectl describe pod <pod-name> -n truematch

# View logs
kubectl logs <pod-name> -n truematch
kubectl logs <pod-name> -n truematch --previous

# Shell into pod
kubectl exec -it <pod-name> -n truematch -- /bin/sh

# Events
kubectl get events -n truematch --sort-by='.lastTimestamp'

# Database health
kubectl exec postgres-0 -n truematch -- pg_isready -U truematch

# Redis health
kubectl exec redis-0 -n truematch -- redis-cli ping

# Worker health
kubectl exec worker-0 -n truematch -- celery -A app.workers.celery_app inspect active
```

## Defaults

| Component | Replicas | CPU Req | Memory Req | CPU Lim | Memory Lim | Storage |
|-----------|----------|---------|-----------|---------|-----------|---------|
| API | 3 | 500m | 512Mi | 1000m | 1Gi | - |
| Worker | 3 (3-20 HPA) | 500m | 512Mi | 1000m | 1Gi | - |
| PostgreSQL | 1 | 500m | 512Mi | 2000m | 2Gi | 100Gi |
| Redis | 1 | 250m | 256Mi | 500m | 1Gi | 50Gi |
| Prometheus | 2 | 500m | 512Mi | 1000m | 1Gi | emptyDir |
| Loki | 1 | 250m | 256Mi | 500m | 512Mi | emptyDir |

## Configuration Files

**Development** (`values-dev.yaml`)
- 1 replica each
- Minimal resources (100m CPU, 128-256Mi RAM)
- No autoscaling
- No ingress (use port-forward)
- Monitoring disabled

**Staging** (`values-staging.yaml`)
- 2 replicas each
- Balanced resources (300m CPU, 384Mi RAM)
- Autoscaling enabled (2-5 API, 2-10 worker)
- Ingress enabled (`api-staging.truematch.ai`)
- Full monitoring (14d prometheus, 3d loki)

**Production** (`values.yaml`)
- 3 replicas minimum
- Full resources (500m CPU, 512Mi RAM)
- Aggressive autoscaling (3-20 worker)
- HTTPS ingress with cert-manager
- 30d prometheus retention
- All security features enabled

## Key Features Checklist

### Deployment
- [x] Namespace isolation
- [x] Service accounts & RBAC
- [x] StatefulSet for databases (persistence)
- [x] Deployment for stateless apps
- [x] Job for database migrations

### Reliability
- [x] Liveness probes (restarts failed pods)
- [x] Readiness probes (only healthy pods receive traffic)
- [x] Startup probes (handles slow startups)
- [x] Pod disruption budgets (high availability)
- [x] Rolling updates (zero-downtime deployments)
- [x] Horizontal pod autoscaling (workers)

### Security
- [x] Non-root user (uid 10001)
- [x] RBAC roles and bindings
- [x] Network policies (ingress/egress rules)
- [x] TLS/HTTPS with cert-manager
- [x] Rate limiting and ModSecurity
- [x] Security headers (HSTS, X-Frame-Options, etc.)
- [x] Secret separation from config
- [x] Support for sealed-secrets

### Observability
- [x] Prometheus metrics
- [x] Centralized logging (Loki)
- [x] Log collection (Fluent-bit)
- [x] Pod resource metrics
- [x] Service health checks
- [x] Event logging

### Scalability
- [x] HPA for workers (3-20 replicas)
- [x] Resource limits and requests
- [x] Pod anti-affinity (spread across nodes)
- [x] Configurable persistence sizes
- [x] Environment-specific overrides

## Helm Commands

```bash
# Install
helm install truematch ./helm/truematch -n truematch --create-namespace

# Upgrade
helm upgrade truematch ./helm/truematch -n truematch

# Rollback
helm rollback truematch -n truematch

# List
helm list -n truematch

# Status
helm status truematch -n truematch

# Values
helm get values truematch -n truematch

# Test
helm test truematch -n truematch

# Delete
helm uninstall truematch -n truematch
```

## Environment Variables

See `k8s/02-config.yaml` for all 50+ configuration variables:
- `ENVIRONMENT`: production, staging, dev
- `LOG_LEVEL`: info, debug, warning, error
- `DATABASE_*`: PostgreSQL connection
- `REDIS_*`: Redis connection
- `AWS_*`, `S3_*`: S3 configuration
- `EMAIL_*`: Email service configuration
- `SINGPASS_*`: Singpass authentication
- `CELERY_*`: Async task queue settings
- `CORS_*`: Cross-origin resource sharing
- `RATE_LIMIT_*`: API rate limiting
- And more...

## Common Issues

| Issue | Solution |
|-------|----------|
| Pods not starting | `kubectl describe pod <pod> -n truematch` |
| Database not ready | `kubectl exec postgres-0 -n truematch -- pg_isready -U truematch` |
| Migration failures | `kubectl logs job/db-migrate -n truematch` |
| Worker not processing | `kubectl exec worker-0 -n truematch -- celery inspect active` |
| High CPU usage | `kubectl top pods -n truematch` then scale up |
| Storage full | Check PVC usage: `kubectl exec postgres-0 -n truematch -- df -h` |
| DNS issues | `kubectl run -it debug --image=busybox --rm -- nslookup postgres.truematch.svc.cluster.local` |

## Performance Tuning

**API**
- Increase replicas: `kubectl scale deployment api --replicas=10`
- Adjust workers: Update `API_WORKERS` in ConfigMap

**Workers**
- HPA automatically scales (3-20 replicas)
- Increase concurrency: Update `CELERY_WORKER_CONCURRENCY`

**Database**
- Increase max connections: Update `max_connections` in postgres
- Adjust shared_buffers: Update PostgreSQL config

**Redis**
- Increase maxmemory: Update redis.conf ConfigMap
- Check eviction policy: LRU is default

## Disaster Recovery

```bash
# Backup database
kubectl exec postgres-0 -n truematch -- pg_dump -U truematch truematch > backup.sql

# Restore database
kubectl exec -i postgres-0 -n truematch -- psql -U truematch truematch < backup.sql

# Full namespace backup
kubectl get all -n truematch -o yaml > truematch-backup.yaml

# Restore from backup
kubectl apply -f truematch-backup.yaml
```

## Production Pre-Flight

```bash
# 1. Setup secrets
./scripts/setup-secrets.sh

# 2. Install prerequisites
helm install cert-manager jetstack/cert-manager --set installCRDs=true
helm install ingress-nginx ingress-nginx/ingress-nginx

# 3. Deploy
./scripts/deploy.sh prod install

# 4. Verify
./scripts/verify-deployment.sh

# 5. Check health
kubectl get all -n truematch
kubectl top pods -n truematch
kubectl logs -n truematch -l app=api --tail=20

# 6. Access API
kubectl port-forward -n truematch svc/api 8000:80
curl http://localhost:8000/livez
```

## Further Reading

- **Complete Setup Guide**: `KUBERNETES_SETUP.md`
- **Deployment Summary**: `KUBERNETES_DEPLOYMENT_SUMMARY.md`
- **Helm Chart**: `helm/truematch/`
- **Raw Manifests**: `k8s/`
- **Scripts**: `scripts/deploy.sh`, `scripts/verify-deployment.sh`, `scripts/setup-secrets.sh`

---

**Version**: 1.0.0  
**Last Updated**: 2024-06-07  
**Status**: Production Ready
