# DEPLOYMENT PROCEDURES

**TrueMatch AI Production Deployment Manual**  
**Version:** 1.0  
**Last Updated:** 2024

---

## TABLE OF CONTENTS

1. [Quick Start](#quick-start)
2. [Standard Deployment](#standard-deployment)
3. [Canary Deployment](#canary-deployment)
4. [Blue-Green Deployment](#blue-green-deployment)
5. [Database Migration Procedures](#database-migration-procedures)
6. [Secret Rotation](#secret-rotation)
7. [Emergency Procedures](#emergency-procedures)
8. [Troubleshooting](#troubleshooting)

---

## QUICK START

### Prerequisites
```bash
# Verify you have required tools
which kubectl jq curl aws

# Set environment variables
export KUBECONFIG=/path/to/kubeconfig
export NAMESPACE=production
export IMAGE_VERSION=v2.0.0
```

### One-Liner Deployment
```bash
# Standard deployment (30 minutes, medium risk)
bash backend/scripts/deploy-production-standard.sh v2.0.0

# Canary deployment (24 hours, low risk)
bash backend/scripts/deploy-production-canary.sh v2.0.0

# Blue-green deployment (2-4 hours, very low risk)
bash backend/scripts/deploy-production-bluegreen.sh v2.0.0
```

---

## STANDARD DEPLOYMENT

**Use Case:** Non-critical updates, bug fixes  
**Duration:** 30 minutes  
**Risk Level:** Medium  
**Rollback Time:** 5-10 minutes

### Step 1: Pre-Deployment Checks

```bash
# Verify current deployment status
kubectl get deployment truematch-api -n production
kubectl get pods -n production -l app=truematch-api

# Check resource availability
kubectl describe nodes | grep -A 5 "Allocated resources"

# Verify database connectivity
kubectl exec -it $(kubectl get pod -n production -l app=truematch-api -o jsonpath='{.items[0].metadata.name}') \
  -n production -- node -e "require('./db').connect().then(() => console.log('Connected'))"

# Verify monitoring systems
curl -s https://prometheus.truematch.com/api/v1/query?query=up | jq .

# Verify backup system
ls -lh /backups/truematch-*.sql
```

### Step 2: Create Database Backup

```bash
# Create backup
pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME > /backups/truematch-backup-$(date +%Y%m%d-%H%M%S).sql

# Verify backup
ls -lh /backups/truematch-backup-*.sql
file /backups/truematch-backup-*.sql

# Test restore (optional, in staging)
createdb -h localhost truematch_test
psql -h localhost -d truematch_test < /backups/truematch-backup-latest.sql
dropdb -h localhost truematch_test
```

### Step 3: Apply Database Migrations

```bash
# Run migrations
kubectl run migration-job \
  --image=truematch:v2.0.0 \
  --env="DB_HOST=$DB_HOST" \
  --env="DB_USER=$DB_USER" \
  --env="DB_PASSWORD=$DB_PASSWORD" \
  --env="MIGRATION_MODE=up" \
  -it \
  -n production \
  -- npm run migrate:up

# Verify migrations completed
kubectl logs migration-job -n production | grep -E "Migration|completed|error"

# If migration failed, rollback:
kubectl run migration-rollback \
  --image=truematch:v1.9.9 \
  --env="DB_HOST=$DB_HOST" \
  --env="MIGRATION_MODE=down" \
  -it \
  -n production \
  -- npm run migrate:down

# Restore from backup if needed
psql -h $DB_HOST -U $DB_USER -d $DB_NAME < /backups/truematch-backup-latest.sql
```

### Step 4: Update Deployment Image

```bash
# Set new image
kubectl set image deployment/truematch-api \
  truematch-api=truematch:v2.0.0 \
  -n production

# Watch rollout progress
kubectl rollout status deployment/truematch-api -n production --timeout=10m

# Verify deployment
kubectl get deployment truematch-api -n production
kubectl get pods -n production -l app=truematch-api
kubectl get pods -n production -l app=truematch-api -o wide
```

### Step 5: Post-Deployment Verification

```bash
# Verify all pods are running
kubectl get pods -n production -l app=truematch-api -o json | \
  jq '.items[] | {name: .metadata.name, status: .status.phase, ready: .status.conditions[?(@.type=="Ready")].status}'

# Check for errors in logs
kubectl logs -n production -l app=truematch-api --tail=50 | grep -i error

# Test health endpoints
curl -H "Authorization: Bearer $TEST_TOKEN" https://api.truematch.com/v1/health/ping
curl -H "Authorization: Bearer $TEST_TOKEN" https://api.truematch.com/v1/health/readiness
curl -H "Authorization: Bearer $TEST_TOKEN" https://api.truematch.com/v1/accounts/profile

# Verify database is accessible
kubectl exec -it truematch-api-pod -n production -- \
  node -e "require('./db').query('SELECT COUNT(*) FROM accounts').then(r => console.log(r))"

# Check metrics
curl https://prometheus.truematch.com/api/v1/query?query='rate(truematch_requests_total[1m])'
```

### Step 6: Monitor (Minimum 30 minutes)

```bash
# Watch metrics in real-time
watch -n 1 'kubectl top pods -n production -l app=truematch-api'

# Stream logs
kubectl logs -f -n production -l app=truematch-api --all-containers=true

# Monitor error rate
watch -n 10 'curl -s https://prometheus.truematch.com/api/v1/query?query=rate(truematch_errors_total[5m]) | jq .'

# Monitor response latency
watch -n 10 'curl -s https://prometheus.truematch.com/api/v1/query?query=histogram_quantile(0.99,rate(truematch_request_duration_seconds_bucket[5m])) | jq .'
```

### Rollback (If Needed)

```bash
# Quick rollback
kubectl rollout undo deployment/truematch-api -n production

# Verify rollback
kubectl rollout status deployment/truematch-api -n production

# If database migration rollback needed:
kubectl run migration-rollback \
  --image=truematch:v1.9.9 \
  --env="MIGRATION_MODE=down" \
  -it -n production -- npm run migrate:down

# Restore database from backup if needed:
psql -h $DB_HOST -U $DB_USER -d $DB_NAME < /backups/truematch-backup-pre-deploy.sql
```

---

## CANARY DEPLOYMENT

**Use Case:** Major features, API changes  
**Duration:** 24 hours (phased)  
**Risk Level:** Low  
**Rollback Time:** 2-5 minutes

### Automated Canary Deployment

```bash
# Execute automated canary deployment
bash backend/scripts/deploy-production-canary.sh v2.0.0 --auto-promote

# Monitor progress
tail -f /var/log/truematch/canary-deployment.log

# Watch traffic split
watch kubectl get virtualservice truematch-vs -n production -o yaml
```

### Manual Canary Deployment

```bash
# Phase 1: Deploy canary with 10% traffic (0-2 hours)
kubectl apply -f backend/k8s/truematch-canary.yaml
kubectl apply -f backend/k8s/istio-virtualservice-canary-10.yaml

# Monitor for 2 hours
for i in {1..120}; do
  echo "[$(date +'%H:%M:%S')] Error Rate: $(curl -s https://prometheus.truematch.com/api/v1/query?query=rate(truematch_errors_total[5m]) | jq -r '.data.result[0].value[1]')%"
  sleep 60
done

# Phase 2: Increase to 25% traffic (2-6 hours)
kubectl apply -f backend/k8s/istio-virtualservice-canary-25.yaml

# Monitor for 4 hours
for i in {1..240}; do
  echo "[$(date +'%H:%M:%S')] Error Rate: $(curl -s https://prometheus.truematch.com/api/v1/query?query=rate(truematch_errors_total[5m]) | jq -r '.data.result[0].value[1]')%"
  sleep 60
done

# Phase 3: Increase to 50% traffic (6-14 hours)
kubectl apply -f backend/k8s/istio-virtualservice-canary-50.yaml

# Monitor for 8 hours
for i in {1..480}; do
  echo "[$(date +'%H:%M:%S')] Error Rate: $(curl -s https://prometheus.truematch.com/api/v1/query?query=rate(truematch_errors_total[5m]) | jq -r '.data.result[0].value[1]')%"
  sleep 60
done

# Phase 4: Promote to 100% traffic (14-24 hours)
kubectl apply -f backend/k8s/istio-virtualservice-canary-100.yaml

# Monitor for 10 hours
for i in {1..600}; do
  echo "[$(date +'%H:%M:%S')] Error Rate: $(curl -s https://prometheus.truematch.com/api/v1/query?query=rate(truematch_errors_total[5m]) | jq -r '.data.result[0].value[1]')%"
  sleep 60
done

# If all phases passed, promote canary to stable
kubectl delete deployment truematch-api-stable -n production
kubectl patch deployment truematch-api-canary -n production \
  -p '{"spec":{"selector":{"matchLabels":{"version":"stable"}}}}'
```

### Canary Rollback

```bash
# If issues detected at any phase:
kubectl apply -f backend/k8s/istio-virtualservice-stable-100.yaml
kubectl delete deployment truematch-api-canary -n production

# Verify stable version is handling traffic
kubectl logs -f -n production -l app=truematch-api,version=stable | head -20
```

---

## BLUE-GREEN DEPLOYMENT

**Use Case:** Critical updates, zero-tolerance downtime  
**Duration:** 2-4 hours (setup), instant switchover  
**Risk Level:** Very Low  
**Rollback Time:** <5 seconds

### Automated Blue-Green Deployment

```bash
# Execute automated blue-green deployment
bash backend/scripts/deploy-production-bluegreen.sh v2.0.0

# Monitor progress
tail -f /var/log/truematch/bluegreen-deployment.log

# Watch Green environment deployment
kubectl get pods -n production-green -l app=truematch-api -o wide
```

### Manual Blue-Green Deployment

```bash
# Step 1: Deploy Green environment
kubectl apply -f backend/k8s/truematch-green.yaml

# Wait for Green pods to be ready
kubectl wait --for=condition=ready pod \
  -l app=truematch-api,environment=green \
  -n production-green \
  --timeout=10m

# Step 2: Run comprehensive tests on Green
kubectl run integration-tests \
  --image=truematch-test:latest \
  --restart=Never \
  -n production-green \
  --env="TARGET_ENV=truematch-api.production-green.svc.cluster.local" \
  -- npm run test:integration

# Monitor test completion
kubectl logs integration-tests -n production-green -f

# Step 3: Run load tests
kubectl run load-tests \
  --image=truematch-loadtest:latest \
  --restart=Never \
  -n production-green \
  --env="TARGET_ENV=truematch-api.production-green.svc.cluster.local" \
  --env="RPS=10000" \
  --env="DURATION=300" \
  -- npm run test:load

# Monitor load test completion
kubectl logs load-tests -n production-green -f

# Step 4: Run security scans
kubectl run security-scans \
  --image=truematch-security:latest \
  --restart=Never \
  -n production-green \
  --env="TARGET_ENV=truematch-api.production-green.svc.cluster.local" \
  -- npm run test:security

# Step 5: Instant switchover to Green
kubectl apply -f backend/k8s/istio-virtualservice-green-100.yaml

# Verify traffic is routing to Green
kubectl logs -f -n production-green -l app=truematch-api | grep "GET\|POST"

# Step 6: Monitor for 30+ minutes
kubectl top pods -n production-green
kubectl logs -f -n production-green -l app=truematch-api

# Step 7: Maintain Blue as rollback point (24 hours)
# Blue still running with 0% traffic, ready for instant rollback
```

### Blue-Green Rollback

```bash
# If critical issues detected:
kubectl apply -f backend/k8s/istio-virtualservice-blue-100.yaml

# Verify traffic switched back to Blue
kubectl logs -f -n production-blue -l app=truematch-api | grep "GET\|POST"

# Decommission Green after stability verification
kubectl delete deployment truematch-api-green -n production-green
```

---

## DATABASE MIGRATION PROCEDURES

### Pre-Migration Tasks

```bash
# Backup current database
pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME \
  --format=custom \
  --file=/backups/truematch-pre-migration-$(date +%Y%m%d-%H%M%S).dump

# Disable application access (optional, for critical migrations)
kubectl scale deployment truematch-api -n production --replicas=0

# Notify database team
echo "Prepare for database migration: $(date)" | mail -s "DB Migration Alert" dba@truematch.com
```

### Execute Migrations

```bash
# Run migrations forward
kubectl run db-migration \
  --image=truematch:v2.0.0 \
  --restart=Never \
  -n production \
  --env="MIGRATION_MODE=up" \
  -- npm run migrate:up

# Verify migration success
kubectl logs db-migration -n production | tail -20

# Check database state
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "\dt"
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "\di"
```

### Migration Rollback

```bash
# If migration failed, rollback immediately
kubectl run db-migration-rollback \
  --image=truematch:v1.9.9 \
  --restart=Never \
  -n production \
  --env="MIGRATION_MODE=down" \
  -- npm run migrate:down

# Verify rollback
kubectl logs db-migration-rollback -n production | tail -20

# If Kubernetes rollback insufficient, restore from backup:
pg_restore -h $DB_HOST -U $DB_USER -d $DB_NAME \
  /backups/truematch-pre-migration-*.dump

# Re-enable application access
kubectl scale deployment truematch-api -n production --replicas=3
```

### Post-Migration Verification

```bash
# Verify all tables exist
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "\dt+"

# Check for constraint issues
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "SELECT COUNT(*) FROM accounts"

# Verify indexes
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "\di"

# Test application connectivity
curl -H "Authorization: Bearer $TEST_TOKEN" https://api.truematch.com/v1/health/ping
```

---

## SECRET ROTATION

### Rotate API Keys

```bash
# Generate new API key
NEW_API_KEY=$(openssl rand -hex 32)

# Update secret in Kubernetes
kubectl patch secret truematch-secrets -n production \
  -p "{\"data\":{\"api-key\":\"$(echo -n $NEW_API_KEY | base64 -w0 | tr -d '\n')\"}}"

# Restart pods to pick up new secret
kubectl rollout restart deployment/truematch-api -n production

# Verify pods are running
kubectl wait --for=condition=ready pod -l app=truematch-api \
  -n production --timeout=5m

# Test API with new key
curl -H "Authorization: Bearer $NEW_API_KEY" https://api.truematch.com/v1/health/ping
```

### Rotate Database Credentials

```bash
# Generate new database password
NEW_DB_PASSWORD=$(openssl rand -base64 32)

# Update PostgreSQL user password
psql -h $DB_HOST -U $DB_USER -d postgres \
  -c "ALTER USER $DB_USER WITH PASSWORD '$NEW_DB_PASSWORD';"

# Update Kubernetes secret
kubectl patch secret truematch-secrets -n production \
  -p "{\"data\":{\"db-password\":\"$(echo -n $NEW_DB_PASSWORD | base64 -w0 | tr -d '\n')\"}}"

# Restart pods
kubectl rollout restart deployment/truematch-api -n production

# Verify connectivity
kubectl exec -it $(kubectl get pod -n production -l app=truematch-api -o jsonpath='{.items[0].metadata.name}') \
  -n production -- node -e "require('./db').connect().then(() => console.log('Connected'))"
```

### Rotate TLS Certificates

```bash
# Request new certificate from Let's Encrypt or CA
certbot certonly --dns-cloudflare \
  -d api.truematch.com \
  -d '*.truematch.com'

# Create Kubernetes secret
kubectl create secret tls truematch-tls \
  --cert=/etc/letsencrypt/live/api.truematch.com/fullchain.pem \
  --key=/etc/letsencrypt/live/api.truematch.com/privkey.pem \
  -n production \
  --dry-run=client -o yaml | kubectl apply -f -

# Restart ingress controller to pick up new cert
kubectl rollout restart deployment/nginx-ingress-controller -n ingress-nginx

# Verify certificate is valid
openssl s_client -connect api.truematch.com:443 -showcerts | grep -A 5 "Subject:"
```

---

## EMERGENCY PROCEDURES

### Emergency Rollback (All Data Intact)

```bash
# Quick rollback to previous version
kubectl rollout undo deployment/truematch-api -n production

# Verify rollback
kubectl rollout status deployment/truematch-api -n production

# Test connectivity
curl -H "Authorization: Bearer $TEST_TOKEN" https://api.truematch.com/v1/health/ping
```

### Emergency Shutdown (Complete Data Loss Scenario)

```bash
# Scale deployment to 0
kubectl scale deployment truematch-api -n production --replicas=0

# Verify pods are terminated
kubectl get pods -n production -l app=truematch-api

# Wait for graceful shutdown (30 seconds)
sleep 30

# Restore from backup
psql -h $DB_HOST -U $DB_USER -d $DB_NAME < /backups/truematch-backup-latest.sql

# Restart application
kubectl scale deployment truematch-api -n production --replicas=3

# Verify recovery
kubectl wait --for=condition=ready pod -l app=truematch-api \
  -n production --timeout=5m
```

### Data Corruption Recovery

```bash
# Stop all write operations
kubectl scale deployment truematch-api -n production --replicas=0

# Identify latest clean backup
ls -lht /backups/truematch-backup-*.sql | head -3

# Restore from backup
psql -h $DB_HOST -U $DB_USER -d $DB_NAME < /backups/truematch-backup-2024-01-15-14-30-00.sql

# Verify data integrity
psql -h $DB_HOST -U $DB_USER -d $DB_NAME \
  -c "SELECT COUNT(*) FROM accounts; SELECT COUNT(*) FROM api_keys;"

# Restart application with previous version
kubectl set image deployment/truematch-api \
  truematch-api=truematch:v1.9.9 \
  -n production

kubectl scale deployment truematch-api -n production --replicas=3

# Notify stakeholders of data point-in-time
echo "Data recovered to 2024-01-15 14:30:00 UTC" | mail -s "Data Recovery Complete" team@truematch.com
```

---

## TROUBLESHOOTING

### Pod Crash Loop

```bash
# Check pod status
kubectl get pods -n production -l app=truematch-api -o wide

# View pod events
kubectl describe pod <pod-name> -n production

# Check logs for errors
kubectl logs <pod-name> -n production --previous

# Common fixes:
# 1. Verify environment variables
kubectl get deployment truematch-api -n production -o yaml | grep -A 10 "env:"

# 2. Check resource limits
kubectl top pod <pod-name> -n production

# 3. Check liveness probe
kubectl get deployment truematch-api -n production -o yaml | grep -A 10 "livenessProbe:"

# 4. Verify image exists and is pullable
kubectl describe pod <pod-name> -n production | grep "Image:"
```

### Database Connection Errors

```bash
# Test database connectivity
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "SELECT 1"

# Check database credentials in secrets
kubectl get secret truematch-secrets -n production -o yaml | grep db-

# Verify database host is reachable
kubectl exec -it <pod-name> -n production -- ping $DB_HOST

# Check connection pool exhaustion
psql -h $DB_HOST -U $DB_USER -d $DB_NAME \
  -c "SELECT count(*) FROM pg_stat_activity WHERE datname = '$DB_NAME'"

# If pool exhausted, kill idle connections:
psql -h $DB_HOST -U $DB_USER -d $DB_NAME \
  -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle' AND query_start < now() - interval '1 hour'"
```

### High Memory Usage

```bash
# Check memory usage
kubectl top pods -n production -l app=truematch-api --sort-by=memory

# View memory limit
kubectl get pods -n production -l app=truematch-api -o jsonpath='{.items[*].spec.containers[0].resources.limits.memory}'

# Check for memory leaks in logs
kubectl logs -n production -l app=truematch-api | grep -i "memory\|heap"

# Increase memory limit
kubectl set resources deployment truematch-api \
  -n production \
  --limits=memory=2Gi \
  --requests=memory=1Gi

# Trigger pod restart
kubectl rollout restart deployment/truematch-api -n production
```

### High CPU Usage

```bash
# Check CPU usage
kubectl top pods -n production -l app=truematch-api --sort-by=cpu

# View CPU limit
kubectl get pods -n production -l app=truematch-api -o jsonpath='{.items[*].spec.containers[0].resources.limits.cpu}'

# Identify hot endpoints
kubectl logs -n production -l app=truematch-api | grep "duration" | sort -t: -k2 -rn | head -10

# Check database query performance
psql -h $DB_HOST -U $DB_USER -d $DB_NAME \
  -c "SELECT query, calls, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10"

# Scale up replicas if sustainable
kubectl scale deployment truematch-api -n production --replicas=6
```

### Network Connectivity Issues

```bash
# Verify service is available
kubectl get service truematch-api -n production

# Check endpoints
kubectl get endpoints truematch-api -n production

# Test DNS resolution
kubectl run dns-test --image=busybox --rm -it -- nslookup truematch-api.production.svc.cluster.local

# Check network policies
kubectl get networkpolicies -n production

# Test pod-to-pod connectivity
kubectl run test-pod --image=busybox --rm -it -- \
  wget -O- http://truematch-api.production.svc.cluster.local:3000/health/ping
```

---

**For additional support, contact: engineering@truematch.com**
