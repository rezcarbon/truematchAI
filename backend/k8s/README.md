# TrueMatch AI - Kubernetes Deployment Configuration
## Phase 3: Production Infrastructure as Code

**Version:** 1.0  
**Last Updated:** 2026-07-19  
**Status:** Production Ready

---

## Overview

This directory contains all Kubernetes manifests and deployment configuration for TrueMatch AI production infrastructure. It covers compute (API, workers), data persistence (PostgreSQL, Redis), monitoring, and alerting.

### Architecture

```
Kubernetes Cluster (truematch-prod)
├── Namespace: truematch-prod
│   ├── API Deployment (3 replicas)
│   ├── Worker Deployment (3 replicas)
│   ├── Scheduler Deployment (1 replica)
│   ├── PostgreSQL StatefulSet
│   ├── Redis StatefulSet
│   └── Monitoring Stack
│       ├── Prometheus
│       ├── Grafana
│       └── Loki
├── Ingress Controller
├── Network Policies
└── Storage Classes
```

---

## Files Overview

### Core Deployment Manifests

- **prod-deployment.yaml** - Complete production deployment configuration
  - API service with 3 replicas
  - Worker service with 3 replicas
  - Scheduler service (1 replica)
  - ConfigMaps and Secrets
  - RBAC and ServiceAccounts
  - NetworkPolicies
  - HorizontalPodAutoscalers
  - PodDisruptionBudgets

### Configuration Files

Located in `/backend/config/`:

- **monitoring/prometheus.yml** - Prometheus scrape targets and global config
- **monitoring/grafana-dashboards.json** - Grafana dashboard definitions
- **alerting/rules.yml** - Prometheus alert rules
- **sentry.yml** - Sentry error tracking configuration

### Scripts

Located in `/backend/scripts/`:

- **deploy-to-production.sh** - Automated deployment script with health checks

---

## Quick Start

### Prerequisites

1. **Kubernetes Cluster**
   ```bash
   kubectl version --client
   kubectl cluster-info
   ```

2. **Environment Variables**
   ```bash
   export CLUSTER_NAME="truematch-prod"
   export NAMESPACE="truematch-prod"
   export DOCKER_REGISTRY="registry.truematch.ai"
   export IMAGE_TAG="v1.2.3"
   ```

3. **Required Secrets**
   ```bash
   # Create namespace first
   kubectl create namespace truematch-prod

   # Create secrets (from external secret manager)
   kubectl create secret generic truematch-prod-secrets \
     --from-literal=DATABASE_USER=truematch_prod \
     --from-literal=DATABASE_PASSWORD=$DB_PASSWORD \
     --from-literal=REDIS_PASSWORD=$REDIS_PASSWORD \
     -n truematch-prod
   ```

### Deployment

#### Option 1: Using Deployment Script (Recommended)

```bash
cd backend/scripts

# Dry run first
./deploy-to-production.sh \
  --dry-run \
  --tag v1.2.3

# Execute deployment
./deploy-to-production.sh \
  --tag v1.2.3 \
  --slack-webhook https://hooks.slack.com/...
```

#### Option 2: Manual kubectl Apply

```bash
# Apply all manifests in order
kubectl apply -f backend/k8s/prod-deployment.yaml -n truematch-prod

# Verify deployment
kubectl get all -n truematch-prod

# Wait for rollout
kubectl rollout status deployment/api -n truematch-prod --timeout=10m
```

### Verification

```bash
# Check all pods running
kubectl get pods -n truematch-prod

# Verify services
kubectl get svc -n truematch-prod

# Check ingress
kubectl get ingress -n truematch-prod

# View recent events
kubectl get events -n truematch-prod --sort-by='.lastTimestamp'

# Test API endpoint
curl https://api.truematch.ai/healthz
```

---

## Configuration Management

### Environment Variables

Edit `prod-deployment.yaml` ConfigMap section:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: truematch-prod-config
  namespace: truematch-prod
data:
  ENVIRONMENT: "production"
  LOG_LEVEL: "INFO"
  DATABASE_POOL_SIZE: "20"
  # ... more variables
```

### Secrets

Secrets should be managed via external secret manager (AWS Secrets Manager, HashiCorp Vault, etc.):

```bash
# Example: AWS Secrets Manager
aws secretsmanager create-secret \
  --name truematch/prod/database-password \
  --secret-string "$(openssl rand -base64 32)"

# Use external-secrets operator to sync to Kubernetes
# https://external-secrets.io/
```

### Resource Limits

Adjust resource requests/limits in deployment spec:

```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "500m"
  limits:
    memory: "1Gi"
    cpu: "1000m"
```

### Scaling

**Automatic Scaling (HPA):**

```bash
kubectl get hpa -n truematch-prod

# Edit thresholds
kubectl edit hpa api-hpa -n truematch-prod
```

**Manual Scaling:**

```bash
kubectl scale deployment/api --replicas=5 -n truematch-prod
```

---

## Monitoring & Observability

### Prometheus

```bash
# Port forward to access locally
kubectl port-forward svc/prometheus 9090:9090 -n truematch-prod

# Visit: http://localhost:9090
```

**Key Queries:**

```
# API request rate
rate(http_requests_total[1m])

# Error rate
rate(http_requests_total{status=~"5.."}[1m])

# Latency p99
histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))
```

### Grafana

```bash
# Port forward to access locally
kubectl port-forward svc/grafana 3000:3000 -n truematch-prod

# Visit: http://localhost:3000
# Login with configured credentials
```

**Dashboards:**
- System Overview
- API Performance
- Worker Status
- Resource Usage
- Database Health
- Business Metrics

### Sentry

Configuration: `/backend/config/sentry.yml`

```bash
# View in web browser
open https://sentry.truematch.ai/projects/truematch/truematch-backend-prod/

# Alert routing configured in Sentry UI
```

### Logging

```bash
# View logs from pod
kubectl logs deployment/api -n truematch-prod -f

# View logs from specific pod
kubectl logs pod/api-abc123 -n truematch-prod

# View with timestamps
kubectl logs deployment/api -n truematch-prod --timestamps=true

# View previous logs (after crash)
kubectl logs deployment/api -n truematch-prod --previous
```

---

## Troubleshooting

### Pods Not Starting

```bash
# Check pod status
kubectl describe pod <pod-name> -n truematch-prod

# Check logs
kubectl logs <pod-name> -n truematch-prod

# Check events
kubectl get events -n truematch-prod --sort-by='.lastTimestamp' | tail -20
```

**Common Issues:**

1. **ImagePullBackOff** - Docker image not found
   - Verify image tag in deployment
   - Check registry credentials
   - Verify image exists in registry

2. **CrashLoopBackOff** - Container exits immediately
   - Check application logs
   - Verify environment variables
   - Check database connectivity

3. **Pending** - Pod can't be scheduled
   - Check node resources: `kubectl top nodes`
   - Check resource requests are reasonable
   - Check node selectors/affinity rules

### High CPU/Memory Usage

```bash
# Check resource usage
kubectl top pods -n truematch-prod
kubectl top nodes

# Check metrics history
kubectl get --raw /apis/metrics.k8s.io/v1beta1/namespaces/truematch-prod/pods
```

### Database Connection Issues

```bash
# Test database connectivity from pod
kubectl run -it --rm debug --image=postgres:latest -- \
  psql -h postgres-prod -U $DB_USER -d truematch_prod -c "SELECT 1;"

# Check database pod status
kubectl get pods -n truematch-prod -l app=postgres-prod

# View database logs
kubectl logs -n truematch-prod -l app=postgres-prod
```

---

## Updating & Upgrading

### Rolling Update

```bash
# Update image tag
kubectl set image deployment/api \
  api=truematch-api:v1.2.4 \
  -n truematch-prod

# Monitor rollout
kubectl rollout status deployment/api -n truematch-prod
```

### Rollback

```bash
# View rollout history
kubectl rollout history deployment/api -n truematch-prod

# Rollback to previous revision
kubectl rollout undo deployment/api -n truematch-prod

# Rollback to specific revision
kubectl rollout undo deployment/api --to-revision=3 -n truematch-prod
```

### Update Configuration

```bash
# Update ConfigMap
kubectl edit cm truematch-prod-config -n truematch-prod

# Restart pods to pick up changes
kubectl rollout restart deployment/api -n truematch-prod
```

### Rotate Secrets

```bash
# Update secret in external manager, then update Kubernetes
kubectl delete secret truematch-prod-secrets -n truematch-prod

# Create new secret
kubectl create secret generic truematch-prod-secrets \
  --from-literal=DATABASE_PASSWORD=$NEW_PASSWORD \
  -n truematch-prod

# Restart pods
kubectl rollout restart deployment/api -n truematch-prod
```

---

## Security

### RBAC

Default RBAC configured in `prod-deployment.yaml`:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: truematch-prod-role
rules:
- apiGroups: [""]
  resources: ["configmaps"]
  verbs: ["get", "list", "watch"]
```

### Network Policies

Restrict traffic between services:

```bash
kubectl get networkpolicies -n truematch-prod

kubectl edit networkpolicies/truematch-prod-network-policy -n truematch-prod
```

### Secrets Management

**Best Practices:**

1. Use external secret manager (AWS Secrets Manager, Vault)
2. Rotate secrets regularly
3. Don't commit secrets to Git
4. Use RBAC to limit access
5. Enable audit logging

**Tools:**

- [External Secrets Operator](https://external-secrets.io/) - Sync external secrets to Kubernetes
- [Sealed Secrets](https://github.com/bitnami-labs/sealed-secrets) - Encrypt secrets in Git

---

## Performance Tuning

### CPU & Memory

Adjust in `prod-deployment.yaml`:

```yaml
resources:
  requests:
    memory: "512Mi"    # Minimum guaranteed
    cpu: "500m"        # 0.5 CPU core
  limits:
    memory: "1Gi"      # Maximum allowed
    cpu: "1000m"       # 1 CPU core
```

### Database Connections

```yaml
env:
  - name: DATABASE_POOL_SIZE
    value: "20"
  - name: DATABASE_MAX_OVERFLOW
    value: "40"
```

### Timeouts

```yaml
livenessProbe:
  initialDelaySeconds: 30
  periodSeconds: 10
  timeoutSeconds: 5

readinessProbe:
  initialDelaySeconds: 10
  periodSeconds: 5
  timeoutSeconds: 3
```

### Affinity Rules

Prefer pods on different nodes:

```yaml
affinity:
  podAntiAffinity:
    preferredDuringSchedulingIgnoredDuringExecution:
    - weight: 100
      podAffinityTerm:
        labelSelector:
          matchExpressions:
          - key: app
            operator: In
            values:
            - api
        topologyKey: kubernetes.io/hostname
```

---

## Backup & Recovery

### Backup Configuration

PostgreSQL backups automated:

```bash
# Manual backup
kubectl exec -it postgres-prod-0 -- \
  pg_dump -U $DB_USER -d truematch_prod | gzip > backup.sql.gz

# Upload to S3
aws s3 cp backup.sql.gz s3://truematch-backups/
```

### Restore from Backup

See [Disaster Recovery Guide](../docs/DISASTER_RECOVERY.md) for detailed procedures.

---

## Maintenance & Operations

### Health Checks

```bash
# API health check
curl https://api.truematch.ai/healthz

# Metrics endpoint
curl https://api.truematch.ai/metrics

# Readiness check (for load balancer)
curl https://api.truematch.ai/readyz
```

### Logs

```bash
# Stream logs from all API pods
kubectl logs -f deployment/api -n truematch-prod

# View logs with grep
kubectl logs deployment/api -n truematch-prod | grep ERROR

# View logs from specific time
kubectl logs deployment/api -n truematch-prod --since=1h
```

### Resource Cleanup

```bash
# Delete old pods (should be automatic)
kubectl delete pods -n truematch-prod --field-selector=status.phase=Failed

# View disk usage
kubectl exec -it api-pod-123 -n truematch-prod -- du -sh /

# Clean up logs
kubectl exec -it api-pod-123 -n truematch-prod -- find /var/log -name "*.log" -delete
```

---

## CI/CD Integration

### GitOps Approach

For automatic deployments when code changes:

```bash
# Install ArgoCD
helm repo add argo https://argoproj.github.io/argo-helm
helm install argocd argo/argo-cd -n argocd --create-namespace

# Create ArgoCD application
kubectl apply -f - <<EOF
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: truematch
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/truematch/truematch-ai
    path: backend/k8s
    targetRevision: main
  destination:
    server: https://kubernetes.default.svc
    namespace: truematch-prod
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
EOF
```

---

## Documentation & References

- **Operations Runbook:** [OPERATIONS_RUNBOOK.md](../docs/OPERATIONS_RUNBOOK.md)
- **Production Checklist:** [PRODUCTION_CHECKLIST.md](../docs/PRODUCTION_CHECKLIST.md)
- **Incident Response:** [INCIDENT_RESPONSE.md](../docs/INCIDENT_RESPONSE.md)
- **Disaster Recovery:** [DISASTER_RECOVERY.md](../docs/DISASTER_RECOVERY.md)

---

## Support & Help

### Common Questions

**Q: How do I deploy a new version?**
A: See "Quick Start - Deployment" section above or run:
```bash
./scripts/deploy-to-production.sh --tag v1.2.3
```

**Q: How do I rollback to previous version?**
A: Run:
```bash
kubectl rollout undo deployment/api -n truematch-prod
```

**Q: How do I check deployment status?**
A: Run:
```bash
kubectl get all -n truematch-prod
kubectl get events -n truematch-prod --sort-by='.lastTimestamp'
```

### Getting Help

- Check Operations Runbook for troubleshooting guide
- Review logs and metrics in Grafana
- Check Sentry for application errors
- Contact Platform Team: [platform@truematch.ai]

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-07-19 | Initial production deployment configuration |

---

**Last Updated:** 2026-07-19  
**Maintained By:** Infrastructure Team  
**Next Review:** 2026-10-19
