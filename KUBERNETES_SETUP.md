# TrueMatch Kubernetes Deployment Guide

This guide covers the complete Kubernetes setup for TrueMatch, including manifests and Helm charts for production-ready deployments.

## Directory Structure

```
TrueMatch/
├── k8s/                          # Raw Kubernetes manifests
│   ├── 01-namespace.yaml         # Namespace and RBAC
│   ├── 02-config.yaml            # ConfigMaps and Secrets
│   ├── 03-postgres.yaml          # PostgreSQL StatefulSet
│   ├── 04-redis.yaml             # Redis StatefulSet
│   ├── 05-migration.yaml         # Database migration Job
│   ├── 06-api.yaml               # API Deployment
│   ├── 07-workers.yaml           # Celery Workers with HPA
│   ├── 08-ingress.yaml           # Ingress, TLS, Network Policies
│   └── 09-monitoring.yaml        # Prometheus, Loki, Fluent-bit
│
└── helm/
    └── truematch/
        ├── Chart.yaml            # Helm chart metadata
        ├── values.yaml           # Default production values
        ├── values-dev.yaml       # Development overrides
        ├── values-staging.yaml   # Staging overrides
        └── templates/            # Helm templates
```

## Prerequisites

- Kubernetes 1.24+
- kubectl configured with cluster access
- Helm 3.0+
- cert-manager installed for TLS
- nginx-ingress controller installed
- (Optional) sealed-secrets for secret management

### Install cert-manager

```bash
helm repo add jetstack https://charts.jetstack.io
helm repo update
helm install cert-manager jetstack/cert-manager --namespace cert-manager --create-namespace --set installCRDs=true
```

### Install nginx-ingress

```bash
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update
helm install ingress-nginx ingress-nginx/ingress-nginx --namespace ingress-nginx --create-namespace
```

### Install sealed-secrets (recommended for production)

```bash
helm repo add sealed-secrets https://bitnami-labs.github.io/sealed-secrets
helm repo update
helm install sealed-secrets sealed-secrets/sealed-secrets --namespace kube-system
```

## Deployment Options

### Option 1: Raw Kubernetes Manifests

Deploy manifests in order:

```bash
# 1. Create namespace and RBAC
kubectl apply -f k8s/01-namespace.yaml

# 2. Create ConfigMaps and Secrets
kubectl apply -f k8s/02-config.yaml

# 3. Deploy PostgreSQL
kubectl apply -f k8s/03-postgres.yaml
kubectl wait --for=condition=ready pod -l app=postgres -n truematch --timeout=300s

# 4. Deploy Redis
kubectl apply -f k8s/04-redis.yaml
kubectl wait --for=condition=ready pod -l app=redis -n truematch --timeout=300s

# 5. Run database migrations
kubectl apply -f k8s/05-migration.yaml
kubectl wait --for=condition=complete job/db-migrate -n truematch --timeout=300s

# 6. Deploy API
kubectl apply -f k8s/06-api.yaml
kubectl wait --for=condition=available deployment/api -n truematch --timeout=300s

# 7. Deploy Workers
kubectl apply -f k8s/07-workers.yaml

# 8. Setup Ingress and Network Policies
kubectl apply -f k8s/08-ingress.yaml

# 9. Setup Monitoring
kubectl apply -f k8s/09-monitoring.yaml
```

### Option 2: Helm Charts (Recommended)

```bash
# Create values file for your environment
cp helm/truematch/values-prod.yaml helm/truematch/values-prod.yaml.custom
# Edit helm/truematch/values-prod.yaml.custom with your settings

# Install the chart
helm install truematch ./helm/truematch \
  -f helm/truematch/values-prod.yaml.custom \
  --namespace truematch \
  --create-namespace

# Verify installation
helm status truematch -n truematch
helm test truematch -n truematch
```

## Configuration

### Secrets Management

**Development**: Inline secrets in ConfigMaps (NOT RECOMMENDED for production)

**Production**: Use sealed-secrets or External Secrets Operator:

```bash
# Encode a secret
echo -n 'your-secret-value' | base64

# Create sealed secret
kubectl create secret generic truematch-secrets \
  --from-literal=JWT_SECRET='your-jwt-secret' \
  --from-literal=DATABASE_PASSWORD='your-db-password' \
  --from-literal=ENCRYPTION_KEY='your-encryption-key' \
  --from-literal=AWS_ACCESS_KEY_ID='your-aws-key' \
  --from-literal=AWS_SECRET_ACCESS_KEY='your-aws-secret' \
  --from-literal=SENDGRID_API_KEY='your-sendgrid-key' \
  -n truematch --dry-run=client -o yaml | kubeseal -f - > k8s/sealed-secrets.yaml

# Apply sealed secrets
kubectl apply -f k8s/sealed-secrets.yaml
```

### Environment Variables

Core configuration is managed via ConfigMap at `k8s/02-config.yaml`. Key variables:

- `DATABASE_HOST`, `DATABASE_PORT`, `DATABASE_NAME`: PostgreSQL connection
- `REDIS_HOST`, `REDIS_PORT`: Redis connection
- `AWS_REGION`, `S3_BUCKET`: S3 configuration
- `EMAIL_PROVIDER`, `SENDGRID_API_KEY`: Email settings
- `SINGPASS_ENABLED`: Feature toggle for Singpass authentication
- `LOG_LEVEL`, `DEBUG`: Logging configuration

### Image Build and Push

Build and push container images before deployment:

```bash
# Build API image
cd backend
docker build -t truematch-api:1.0.0 .
docker tag truematch-api:1.0.0 your-registry.com/truematch-api:1.0.0
docker push your-registry.com/truematch-api:1.0.0

# Update image references in k8s/ or values.yaml
```

## Deployment Verification

### Health Checks

```bash
# Check deployment status
kubectl get deployments -n truematch
kubectl get statefulsets -n truematch
kubectl get pods -n truematch

# View logs
kubectl logs -n truematch -l app=api --tail=50
kubectl logs -n truematch -l app=worker --tail=50
kubectl logs -n truematch -l app=postgres --tail=50

# Port-forward to test API
kubectl port-forward -n truematch svc/api 8000:80
curl http://localhost:8000/livez
curl http://localhost:8000/readyz
```

### Database Health

```bash
# Connect to PostgreSQL
kubectl exec -it postgres-0 -n truematch -- psql -U truematch -d truematch

# View migrations status
\dt

# Exit
\q
```

### Redis Health

```bash
# Connect to Redis
kubectl exec -it redis-0 -n truematch -- redis-cli

# Check memory usage
INFO memory

# Exit
EXIT
```

## Scaling

### Horizontal Pod Autoscaling

Workers automatically scale based on CPU and memory. Check status:

```bash
kubectl get hpa -n truematch
kubectl describe hpa worker-hpa -n truematch
```

### Manual Scaling

```bash
# Scale API
kubectl scale deployment api --replicas=5 -n truematch

# Scale Workers
kubectl scale deployment worker --replicas=10 -n truematch
```

## Updates and Rollouts

### Rolling Update

```bash
# Update image
kubectl set image deployment/api api=truematch-api:1.0.1 -n truematch

# Watch rollout
kubectl rollout status deployment/api -n truematch

# Rollback if needed
kubectl rollout undo deployment/api -n truematch
```

### Helm Updates

```bash
# Fetch updated values
helm get values truematch -n truematch > values-backup.yaml

# Upgrade release
helm upgrade truematch ./helm/truematch \
  -f helm/truematch/values-prod.yaml \
  -n truematch

# Verify
helm status truematch -n truematch

# Rollback if needed
helm rollback truematch -n truematch
```

## Monitoring and Observability

### Prometheus

Access metrics dashboard:

```bash
kubectl port-forward -n truematch svc/prometheus 9090:9090
# Open http://localhost:9090
```

Key metrics:
- `http_requests_total`: API request count
- `http_request_duration_seconds`: Request latency
- `celery_tasks_total`: Task execution count
- `database_connections`: Active DB connections
- `redis_connected_clients`: Active Redis clients

### Logging with Loki

Access logs:

```bash
kubectl port-forward -n truematch svc/loki 3100:3100
# Configure Grafana datasource: http://localhost:3100
```

### Database Metrics

PostgreSQL metrics available at `postgres-exporter:9187`. Add to Prometheus scrape config for detailed metrics.

## Networking

### Internal Service Discovery

- API: `api.truematch.svc.cluster.local:80`
- Workers: Use Redis for message passing
- Database: `postgres.truematch.svc.cluster.local:5432`
- Redis: `redis.truematch.svc.cluster.local:6379`

### Network Policies

Network policies enforce pod-to-pod communication rules:

- API ↔ Database: Allowed
- Workers ↔ Database: Allowed
- API ↔ Redis: Allowed
- Workers ↔ Redis: Allowed
- Ingress → API: Allowed
- External egress: Allowed (with restrictions on metadata service)

View policies:

```bash
kubectl get networkpolicy -n truematch
kubectl describe networkpolicy api-network-policy -n truematch
```

## Security

### RBAC

Service accounts and roles restrict permissions:

```bash
kubectl get serviceaccount -n truematch
kubectl get rolebindings -n truematch
kubectl get clusterrolebindings | grep truematch
```

### Pod Security

- Non-root user (10001) for all pods
- Read-only root filesystem where possible
- Dropped Linux capabilities
- Resource limits enforced

### TLS/HTTPS

- Automatic certificate generation via cert-manager
- Let's Encrypt for public-facing ingress
- Renewal 15 days before expiration

Check certificates:

```bash
kubectl get certificate -n truematch
kubectl describe certificate truematch-cert -n truematch
```

## Persistence

### PostgreSQL Persistence

- PVC: `postgres-pvc` (100Gi by default)
- Data location: `/var/lib/postgresql/data`
- Backup strategy: Configure external backups

### Redis Persistence

- PVC: `redis-pvc` (50Gi by default)
- Persistence: AOF (Append-Only File) enabled
- Data location: `/data`

### Storage Classes

Modify storage class in manifests to match your cluster:

- AWS: `ebs-sc` or `gp3`
- GCP: `standard-rwo` or `pd-ssd`
- Azure: `default` or `managed-premium`
- Local: `local-path`

```bash
kubectl get storageclass
```

## Maintenance

### Database Backups

```bash
# Export database
kubectl exec postgres-0 -n truematch -- pg_dump -U truematch truematch > backup.sql

# Restore database
kubectl exec -i postgres-0 -n truematch -- psql -U truematch truematch < backup.sql
```

### Clean Up

```bash
# Delete all resources
helm uninstall truematch -n truematch

# Or with raw manifests:
kubectl delete -f k8s/ -n truematch
kubectl delete ns truematch
```

### Debug Commands

```bash
# Describe problematic pods
kubectl describe pod <pod-name> -n truematch

# Get events
kubectl get events -n truematch --sort-by='.lastTimestamp'

# Access pod shell
kubectl exec -it <pod-name> -n truematch -- /bin/sh

# Check resource usage
kubectl top nodes
kubectl top pods -n truematch
```

## Troubleshooting

### Pod not starting

```bash
kubectl describe pod <pod-name> -n truematch
kubectl logs <pod-name> -n truematch --previous
```

### Database migration failures

```bash
kubectl logs -n truematch -l app=truematch,component=migration
kubectl get job -n truematch
```

### Worker not processing tasks

```bash
kubectl exec worker-0 -n truematch -- celery -A app.workers.celery_app inspect active
```

### DNS issues

```bash
kubectl run -it --rm debug --image=busybox --restart=Never -- nslookup postgres.truematch.svc.cluster.local
```

## Production Checklist

- [ ] Use sealed-secrets or External Secrets Operator for sensitive data
- [ ] Configure persistent volume backups
- [ ] Set resource requests and limits appropriately
- [ ] Enable network policies
- [ ] Configure pod disruption budgets
- [ ] Set up monitoring and alerting
- [ ] Configure centralized logging
- [ ] Enable RBAC and audit logging
- [ ] Use private container registries
- [ ] Configure image pull secrets
- [ ] Set resource quotas per namespace
- [ ] Enable pod security standards
- [ ] Configure external DNS
- [ ] Set up automated backups
- [ ] Configure cluster autoscaling
- [ ] Enable metrics-server for HPA

## References

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Helm Documentation](https://helm.sh/docs/)
- [cert-manager Documentation](https://cert-manager.io/docs/)
- [PostgreSQL Operator](https://github.com/zalando/postgres-operator)
- [Redis Operator](https://github.com/aiven/redis-operator)
