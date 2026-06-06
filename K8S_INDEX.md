# TrueMatch Kubernetes Deployment - File Index

## Quick Start
- **Start here**: [`K8S_QUICK_REFERENCE.md`](K8S_QUICK_REFERENCE.md) - One-page quick reference with essential commands
- **Automated deploy**: [`scripts/deploy.sh`](scripts/deploy.sh) - One-command deployment (dev/staging/prod)

## Complete Guides
1. [`DEPLOYMENT_WORKFLOW.md`](DEPLOYMENT_WORKFLOW.md) - Step-by-step deployment from prep to production
2. [`KUBERNETES_SETUP.md`](KUBERNETES_SETUP.md) - Comprehensive setup and operational guide (troubleshooting, scaling, maintenance)
3. [`KUBERNETES_DEPLOYMENT_SUMMARY.md`](KUBERNETES_DEPLOYMENT_SUMMARY.md) - Architecture overview and feature documentation

## Kubernetes Manifests (in `k8s/`)
Deploy in order:
```
01-namespace.yaml      → Namespace, ServiceAccount, RBAC
02-config.yaml         → ConfigMaps (50+ vars), Secrets, Prometheus config
03-postgres.yaml       → PostgreSQL StatefulSet (100Gi PVC)
04-redis.yaml          → Redis StatefulSet (50Gi PVC)
05-migration.yaml      → Database migration Job (alembic)
06-api.yaml            → API Deployment (3 replicas, Pod Disruption Budget)
07-workers.yaml        → Celery Workers (3-20 HPA)
08-ingress.yaml        → HTTPS Ingress, TLS, Network Policies
09-monitoring.yaml     → Prometheus, Loki, Fluent-bit
```

## Helm Chart (in `helm/truematch/`)
```
Chart.yaml            → Chart metadata
values.yaml           → Production values (default)
values-dev.yaml       → Development overrides
values-staging.yaml   → Staging overrides
templates/
  _helpers.tpl        → Template utilities
  NOTES.txt           → Post-install instructions
```

## Scripts (in `scripts/`)
```
deploy.sh             → Automated deployment (one-command)
  Usage: ./deploy.sh [dev|staging|prod] [install|upgrade]
  
verify-deployment.sh  → Health check validation (12 checks)
  Usage: ./verify-deployment.sh
  
setup-secrets.sh      → Interactive secret configuration
  Usage: ./setup-secrets.sh
```

## Documentation

### For First-Time Users
Start with **`K8S_QUICK_REFERENCE.md`** (5 min read)
Then follow **`DEPLOYMENT_WORKFLOW.md`** step-by-step

### For Complete Understanding
Read **`KUBERNETES_SETUP.md`** for:
- Prerequisites and installation
- Configuration management
- Deployment verification
- Scaling and updates
- Monitoring and observability
- Networking and security
- Troubleshooting

### For Architecture Overview
Read **`KUBERNETES_DEPLOYMENT_SUMMARY.md`** for:
- Directory structure
- Feature highlights per component
- Deployment options
- Security best practices
- Production checklist

## Component Summary

| Component | Type | Replicas | Storage | Image |
|-----------|------|----------|---------|-------|
| API | Deployment | 3 | - | truematch-api:latest |
| Workers | Deployment (HPA) | 3-20 | - | truematch-api:latest |
| PostgreSQL | StatefulSet | 1 | 100Gi | postgres:15-alpine |
| Redis | StatefulSet | 1 | 50Gi | redis:7-alpine |
| Prometheus | Deployment | 2 | emptyDir | prom/prometheus:latest |
| Loki | Deployment | 1 | emptyDir | grafana/loki:latest |
| Fluent-bit | DaemonSet | N/A | - | fluent/fluent-bit:latest |

## Key Configuration Files

- **Environment Variables**: `k8s/02-config.yaml` (ConfigMap section)
- **Secrets**: `k8s/02-config.yaml` (Secret section)
- **Database Config**: `k8s/02-config.yaml` (postgres-init ConfigMap)
- **Prometheus Config**: `k8s/02-config.yaml` (prometheus-config ConfigMap)
- **Redis Config**: `k8s/04-redis.yaml` (redis-config ConfigMap)
- **Fluent-bit Config**: `k8s/02-config.yaml` (fluent-bit-config ConfigMap)

## Deployment Methods

### Method 1: Automated Script (Recommended for most users)
```bash
./scripts/deploy.sh prod install
./scripts/verify-deployment.sh
```

### Method 2: Helm (Best for release management)
```bash
helm install truematch ./helm/truematch \
  -f helm/truematch/values-prod.yaml \
  -n truematch --create-namespace
```

### Method 3: Raw Manifests (Most control)
```bash
kubectl apply -f k8s/
```

## Essential Commands

```bash
# Deploy
./scripts/deploy.sh prod install

# Verify
./scripts/verify-deployment.sh

# Setup secrets
./scripts/setup-secrets.sh

# View status
kubectl get all -n truematch

# View logs
kubectl logs -n truematch -l app=api -f

# Port-forward to API
kubectl port-forward -n truematch svc/api 8000:80

# Scale workers
kubectl scale deployment worker --replicas=10 -n truematch

# Monitor metrics
kubectl port-forward -n truematch svc/prometheus 9090:9090
# Open http://localhost:9090

# Check health
./scripts/verify-deployment.sh
```

## File Statistics

| Category | Count | Lines |
|----------|-------|-------|
| Kubernetes Manifests | 9 | ~1,500 |
| Helm Chart | 5 | ~400 |
| Scripts | 3 | ~600 |
| Documentation | 4 | ~2,000 |
| **Total** | **21** | **~4,500** |

## Feature Checklist

### Deployment ✓
- [x] Namespace isolation
- [x] Service accounts & RBAC
- [x] StatefulSets for databases
- [x] Deployments for stateless apps
- [x] Jobs for migrations

### Reliability ✓
- [x] Liveness probes
- [x] Readiness probes
- [x] Startup probes
- [x] Pod disruption budgets
- [x] Rolling updates
- [x] Horizontal pod autoscaling

### Security ✓
- [x] Non-root user (uid 10001)
- [x] RBAC roles
- [x] Network policies
- [x] HTTPS/TLS with cert-manager
- [x] Rate limiting & ModSecurity
- [x] Security headers
- [x] Secret management

### Observability ✓
- [x] Prometheus metrics
- [x] Loki logs
- [x] Fluent-bit collection
- [x] Health checks
- [x] Resource monitoring

### Scalability ✓
- [x] HPA for workers
- [x] Resource limits
- [x] Pod anti-affinity
- [x] Configurable storage
- [x] Environment overrides

## Troubleshooting Resources

For specific issues, see `KUBERNETES_SETUP.md` section: "Troubleshooting"

Quick issues:
- Pod not starting → `kubectl describe pod` + `kubectl logs`
- Database issues → `KUBERNETES_SETUP.md` → "Database Health"
- Worker issues → `KUBERNETES_SETUP.md` → "Debug Commands"
- Network issues → `KUBERNETES_SETUP.md` → "Networking"

## Next Steps

1. **First Time?**
   - Read `K8S_QUICK_REFERENCE.md`
   - Run `./scripts/deploy.sh dev install`

2. **Going to Production?**
   - Read `DEPLOYMENT_WORKFLOW.md`
   - Run `./scripts/setup-secrets.sh`
   - Run `./scripts/deploy.sh prod install`
   - Run `./scripts/verify-deployment.sh`

3. **Need Help?**
   - Check `KUBERNETES_SETUP.md` troubleshooting section
   - Review pod logs: `kubectl logs -n truematch -l app=api -f`
   - Check events: `kubectl get events -n truematch`

## Production Pre-Flight Checklist

- [ ] Secrets configured (run `./scripts/setup-secrets.sh`)
- [ ] Container images built and pushed
- [ ] Cluster prerequisites installed (cert-manager, nginx-ingress)
- [ ] DNS configured
- [ ] Storage class selected
- [ ] Run `./scripts/deploy.sh prod install`
- [ ] Run `./scripts/verify-deployment.sh`
- [ ] All checks passing
- [ ] Test API: `curl https://api.truematch.ai/livez`
- [ ] Monitor logs for 10 minutes
- [ ] No pod restarts or errors

## Version

- **TrueMatch Kubernetes**: v1.0.0
- **Kubernetes Minimum**: v1.24
- **Helm**: v3.0+
- **Last Updated**: 2024-06-07
- **Status**: Production Ready

## License

TrueMatch Kubernetes Infrastructure - Production Ready

---

**Ready to deploy?** Start with [`K8S_QUICK_REFERENCE.md`](K8S_QUICK_REFERENCE.md)

**Questions?** See [`KUBERNETES_SETUP.md`](KUBERNETES_SETUP.md)

**Step-by-step?** Follow [`DEPLOYMENT_WORKFLOW.md`](DEPLOYMENT_WORKFLOW.md)
