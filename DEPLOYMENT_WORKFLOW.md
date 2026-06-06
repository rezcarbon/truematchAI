# TrueMatch Kubernetes Deployment Workflow

Complete step-by-step guide for deploying TrueMatch to Kubernetes.

## Phase 1: Preparation (1-2 hours)

### 1.1 Prerequisites Validation

```bash
# Check kubectl version (1.24+)
kubectl version --client

# Check helm version (3.0+)
helm version

# Verify cluster connection
kubectl cluster-info
kubectl get nodes

# Check available resources
kubectl top nodes
kubectl describe node | grep -A 5 "Allocatable"
```

**Expected Output**:
- kubectl v1.24 or higher
- helm v3.0 or higher
- At least 2-3 nodes with 2+ CPU and 4GB RAM each
- Network plugin installed
- StorageClass available

### 1.2 Install Cluster Add-ons

```bash
# Add Helm repositories
helm repo add jetstack https://charts.jetstack.io
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo add sealed-secrets https://bitnami-labs.github.io/sealed-secrets
helm repo update

# Install cert-manager (for HTTPS/TLS)
helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --create-namespace \
  --set installCRDs=true \
  --wait

# Verify cert-manager
kubectl get pods -n cert-manager

# Install nginx-ingress controller
helm install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --create-namespace \
  --wait

# Verify ingress controller
kubectl get svc -n ingress-nginx
kubectl get pods -n ingress-nginx

# (Optional) Install sealed-secrets for secret encryption
helm install sealed-secrets sealed-secrets/sealed-secrets \
  --namespace kube-system \
  --wait

# Verify sealed-secrets
kubeseal --version
```

### 1.3 Prepare Container Images

```bash
# Clone or navigate to TrueMatch backend
cd TrueMatch/backend

# Build Docker image
docker build -t truematch-api:1.0.0 .

# (For private registry)
docker tag truematch-api:1.0.0 your-registry.com/truematch-api:1.0.0
docker push your-registry.com/truematch-api:1.0.0

# Update image references in k8s/ or helm/truematch/values*.yaml
# Replace: truematch-api:latest → your-registry.com/truematch-api:1.0.0
```

### 1.4 Configure DNS (if applicable)

```bash
# Get ingress controller external IP
kubectl get svc -n ingress-nginx nginx-ingress-ingress-nginx-controller

# Example output: EXTERNAL-IP: 34.567.89.012

# Add DNS record:
# api.truematch.ai A 34.567.89.012
```

## Phase 2: Deployment (30 minutes)

### 2.1 Deploy with Automated Script (Recommended)

```bash
cd /Users/darthmod/Desktop/TrueMatch

# Make scripts executable
chmod +x scripts/*.sh

# Choose environment
ENVIRONMENT=prod  # or: dev, staging

# Deploy
./scripts/deploy.sh $ENVIRONMENT install

# Expected output:
# [INFO] Starting TrueMatch deployment for environment: prod
# [SUCCESS] Namespace created
# [SUCCESS] Manifest deployment complete
# [SUCCESS] Deployment verification complete
# [SUCCESS] Deployment completed successfully!
```

### 2.2 Manual Deployment with Manifests (Alternative)

```bash
cd /Users/darthmod/Desktop/TrueMatch

# Step 1: Create namespace and RBAC
kubectl apply -f k8s/01-namespace.yaml

# Step 2: Create configuration
kubectl apply -f k8s/02-config.yaml

# Step 3: Deploy PostgreSQL
kubectl apply -f k8s/03-postgres.yaml

# Wait for PostgreSQL
kubectl wait --for=condition=ready pod -l app=postgres -n truematch --timeout=300s

# Verify database
kubectl exec postgres-0 -n truematch -- pg_isready -U truematch

# Step 4: Deploy Redis
kubectl apply -f k8s/04-redis.yaml

# Wait for Redis
kubectl wait --for=condition=ready pod -l app=redis -n truematch --timeout=300s

# Verify Redis
kubectl exec redis-0 -n truematch -- redis-cli ping

# Step 5: Run database migrations
kubectl apply -f k8s/05-migration.yaml

# Wait for migration
kubectl wait --for=condition=complete job/db-migrate -n truematch --timeout=300s

# Check migration status
kubectl logs job/db-migrate -n truematch

# Step 6: Deploy API
kubectl apply -f k8s/06-api.yaml

# Wait for API
kubectl wait --for=condition=available deployment/api -n truematch --timeout=300s

# Step 7: Deploy Workers
kubectl apply -f k8s/07-workers.yaml

# Step 8: Setup Ingress and Network Policies
kubectl apply -f k8s/08-ingress.yaml

# Step 9: Setup Monitoring
kubectl apply -f k8s/09-monitoring.yaml
```

### 2.3 Deployment with Helm (Alternative)

```bash
cd /Users/darthmod/Desktop/TrueMatch

# Create namespace
kubectl create namespace truematch

# Install Helm chart
helm install truematch ./helm/truematch \
  -f helm/truematch/values-prod.yaml \
  --namespace truematch \
  --wait \
  --timeout 10m

# Verify installation
helm status truematch -n truematch
helm test truematch -n truematch
```

### 2.4 Configure Secrets

Before deploying, set up sensitive data:

```bash
# Interactive secret setup (recommended)
./scripts/setup-secrets.sh

# The script will prompt for:
# - JWT Secret
# - Database Password
# - Encryption Keys
# - AWS Credentials
# - Email Service Keys
# - OAuth Credentials

# For manual setup:
kubectl create secret generic truematch-secrets \
  --from-literal=JWT_SECRET="$(openssl rand -base64 32)" \
  --from-literal=DATABASE_PASSWORD="your-secure-password" \
  --from-literal=ENCRYPTION_KEY="$(openssl rand -base64 32)" \
  --from-literal=AWS_ACCESS_KEY_ID="your-aws-key" \
  --from-literal=AWS_SECRET_ACCESS_KEY="your-aws-secret" \
  --from-literal=SENDGRID_API_KEY="your-sendgrid-key" \
  -n truematch

# Verify secrets
kubectl get secret truematch-secrets -n truematch
kubectl get secret truematch-secrets -n truematch -o jsonpath='{.data}' | jq 'keys'
```

## Phase 3: Verification (15 minutes)

### 3.1 Automated Health Check

```bash
# Run comprehensive verification script
./scripts/verify-deployment.sh

# Expected output:
# ✓ Namespace truematch exists
# ✓ API deployment ready (3/3 replicas)
# ✓ PostgreSQL StatefulSet ready
# ✓ Redis StatefulSet ready
# ✓ All pods are running or succeeded
# ✓ API liveness probe successful
# ✓ API readiness probe successful
# ✓ PostgreSQL is accepting connections
# ✓ Redis is accepting connections
# ✓ ConfigMap truematch-config exists
# ✓ Secret truematch-secrets exists
# ✓ All PVCs are bound
# 
# Verification Summary
# Passed:   12
# Failed:   0
# Warnings: 0
```

### 3.2 Manual Verification

```bash
# Check overall status
kubectl get all -n truematch
kubectl get pvc -n truematch
kubectl get ingress -n truematch

# Check pod status in detail
kubectl get pods -n truematch -o wide
kubectl describe pod api-0 -n truematch

# View recent events
kubectl get events -n truematch --sort-by='.lastTimestamp'

# Check resource usage
kubectl top nodes
kubectl top pods -n truematch

# Test API endpoint
kubectl port-forward -n truematch svc/api 8000:80 &
curl -v http://localhost:8000/livez
curl -v http://localhost:8000/readyz
kill %1

# Test database connection
kubectl exec -it postgres-0 -n truematch -- psql -U truematch -d truematch -c "SELECT version();"

# Test Redis connection
kubectl exec -it redis-0 -n truematch -- redis-cli INFO server

# Check logs
kubectl logs -n truematch -l app=api --tail=50
kubectl logs -n truematch -l app=worker --tail=50
kubectl logs -n truematch -l app=postgres --tail=50
```

### 3.3 Security Verification

```bash
# Verify RBAC
kubectl get serviceaccount -n truematch
kubectl get rolebindings -n truematch
kubectl get clusterrolebindings | grep truematch

# Verify Network Policies
kubectl get networkpolicy -n truematch
kubectl describe networkpolicy api-network-policy -n truematch

# Verify TLS certificates
kubectl get certificate -n truematch
kubectl describe certificate truematch-cert -n truematch

# Check pod security context
kubectl get pod api-0 -n truematch -o jsonpath='{.spec.securityContext}'

# Verify HTTPS
kubectl get ingress -n truematch -o jsonpath='{.items[0].spec.tls}'
```

## Phase 4: Access & Testing (15 minutes)

### 4.1 Access Application

```bash
# Get API endpoint
kubectl get ingress -n truematch -o jsonpath='{.items[0].spec.rules[0].host}'
# Example output: api.truematch.ai

# Test HTTPS (if ingress is ready)
curl -v https://api.truematch.ai/livez

# Test via port-forward (if DNS not configured)
kubectl port-forward -n truematch svc/api 8000:80
curl http://localhost:8000/livez

# Check API response
curl http://localhost:8000/readyz | jq .

# View API logs in real-time
kubectl logs -n truematch -l app=api -f
```

### 4.2 Access Monitoring

```bash
# Prometheus metrics
kubectl port-forward -n truematch svc/prometheus 9090:9090 &
# Visit http://localhost:9090
# Query examples:
# - http_requests_total
# - http_request_duration_seconds
# - celery_tasks_total
# - container_memory_usage_bytes

# Loki logs
kubectl port-forward -n truematch svc/loki 3100:3100 &
# Configure Grafana datasource: http://localhost:3100

# View Fluent-bit logs
kubectl logs -n truematch -l app=fluent-bit -f
```

### 4.3 Test Database

```bash
# Port-forward to PostgreSQL
kubectl port-forward -n truematch svc/postgres 5432:5432 &

# Connect with psql
psql -h localhost -U truematch -d truematch

# Inside psql:
# \dt                    # List tables
# \l                     # List databases
# SELECT COUNT(*) FROM users;  # Query data
# \q                     # Exit
```

### 4.4 Test Redis

```bash
# Port-forward to Redis
kubectl port-forward -n truematch svc/redis 6379:6379 &

# Connect with redis-cli
redis-cli -p 6379

# Inside redis-cli:
# PING                   # Health check
# INFO                   # Server info
# DBSIZE                 # Number of keys
# KEYS *                 # List all keys
# EXIT                   # Exit
```

### 4.5 Run Sample Tasks

```bash
# Port-forward to API
kubectl port-forward -n truematch svc/api 8000:80 &

# Create a test task (example)
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Task",
    "description": "Testing Kubernetes deployment"
  }'

# Check worker processing logs
kubectl logs -n truematch -l app=worker -f
```

## Phase 5: Monitoring & Maintenance (Ongoing)

### 5.1 Daily Health Checks

```bash
# Run verification script daily
./scripts/verify-deployment.sh

# Monitor resource usage
kubectl top nodes
kubectl top pods -n truematch

# Check for pod restarts
kubectl get pods -n truematch -o json | \
  jq '.items[] | select(.status.containerStatuses[0].restartCount > 5)'

# Review recent events
kubectl get events -n truematch --sort-by='.lastTimestamp' | tail -20
```

### 5.2 Scaling Operations

```bash
# Check current HPA status
kubectl get hpa -n truematch
kubectl describe hpa worker-hpa -n truematch

# Manual scaling if needed
kubectl scale deployment api --replicas=5 -n truematch
kubectl scale deployment worker --replicas=10 -n truematch

# Monitor scaling activities
kubectl get hpa -n truematch -w
```

### 5.3 Updates & Rollbacks

```bash
# Rolling update to new API version
kubectl set image deployment/api api=truematch-api:1.0.1 -n truematch

# Watch the rollout
kubectl rollout status deployment/api -n truematch -w

# Rollback if needed
kubectl rollout undo deployment/api -n truematch

# With Helm
helm upgrade truematch ./helm/truematch -f helm/truematch/values-prod.yaml -n truematch
helm rollback truematch -n truematch
```

### 5.4 Backup & Disaster Recovery

```bash
# Backup database
kubectl exec postgres-0 -n truematch -- pg_dump -U truematch truematch > backup.sql
gzip backup.sql

# Backup Kubernetes manifests
kubectl get all -n truematch -o yaml > truematch-state.yaml

# Restore database (if needed)
gunzip backup.sql.gz
kubectl exec -i postgres-0 -n truematch -- psql -U truematch truematch < backup.sql

# Restore from manifest backup
kubectl apply -f truematch-state.yaml
```

## Troubleshooting Quick Guide

### Pod Fails to Start

```bash
# Get pod details
kubectl describe pod <pod-name> -n truematch

# Check logs
kubectl logs <pod-name> -n truematch
kubectl logs <pod-name> -n truematch --previous

# Check events
kubectl get events -n truematch --sort-by='.lastTimestamp'
```

### Database Not Accepting Connections

```bash
# Check PostgreSQL pod
kubectl exec postgres-0 -n truematch -- pg_isready -U truematch

# Check logs
kubectl logs postgres-0 -n truematch

# Check PVC
kubectl describe pvc postgres-pvc -n truematch

# Manually connect
kubectl exec -it postgres-0 -n truematch -- psql -U truematch
```

### Workers Not Processing Tasks

```bash
# Check worker pods
kubectl get pods -n truematch -l app=worker

# Check celery status
kubectl exec worker-0 -n truematch -- \
  celery -A app.workers.celery_app inspect active

# Check logs
kubectl logs -n truematch -l app=worker -f

# Check Redis connection
kubectl exec redis-0 -n truematch -- redis-cli PING
```

### High Memory/CPU Usage

```bash
# Check resource usage
kubectl top pods -n truematch

# Find problematic pods
kubectl top pods -n truematch --sort-by=memory
kubectl top pods -n truematch --sort-by=cpu

# Scale up if needed
kubectl scale deployment api --replicas=10 -n truematch

# Or adjust resource limits
kubectl patch deployment api -p '{"spec":{"template":{"spec":{"containers":[{"name":"api","resources":{"limits":{"memory":"2Gi"}}}]}}}' -n truematch
```

## Post-Deployment Checklist

- [ ] All pods running successfully
- [ ] Database migrations completed
- [ ] API responding to health checks
- [ ] Workers processing tasks
- [ ] Ingress configured with HTTPS
- [ ] Certificates automatically renewed
- [ ] Monitoring and logging operational
- [ ] Secrets encrypted (sealed-secrets)
- [ ] Network policies enforcing restrictions
- [ ] Resource requests and limits configured
- [ ] Pod disruption budgets in place
- [ ] Backups scheduled and tested
- [ ] Alerting configured
- [ ] Runbooks documented
- [ ] On-call rotation established

## Success Criteria

✓ All pods in `Running` state  
✓ Database accepting connections  
✓ API responding to `/livez` and `/readyz`  
✓ Workers processing tasks  
✓ Monitoring metrics visible  
✓ HTTPS/TLS working  
✓ Network policies applied  
✓ No pod restarts in 5 minutes  
✓ Resource usage < 80% of limits  

## Next Steps

1. **Monitor in Production**
   - Set up alerting rules
   - Configure log aggregation
   - Establish SLOs/SLIs

2. **Optimize Performance**
   - Run load tests
   - Tune resource requests
   - Optimize database queries

3. **Plan Maintenance**
   - Schedule regular backups
   - Plan upgrade strategy
   - Document runbooks

4. **Improve Reliability**
   - Configure failover
   - Test disaster recovery
   - Document recovery procedures

## Support & Reference

- **Quick Reference**: `K8S_QUICK_REFERENCE.md`
- **Complete Setup Guide**: `KUBERNETES_SETUP.md`
- **Deployment Summary**: `KUBERNETES_DEPLOYMENT_SUMMARY.md`
- **Kubernetes Docs**: https://kubernetes.io/docs/
- **Helm Docs**: https://helm.sh/docs/

---

**Estimated Total Time**: 2-3 hours  
**Skill Level**: Intermediate to Advanced  
**Requirements**: kubectl, helm, docker, basic Kubernetes knowledge
