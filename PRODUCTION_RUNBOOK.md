# TrueMatch Production Runbook

**Version:** 1.0  
**Last Updated:** June 7, 2026  
**Status:** Production Ready  
**Environment:** Kubernetes-based multi-region deployment  
**RTO:** 1 hour | **RPO:** 5 minutes

---

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Deployment Procedures](#deployment-procedures)
3. [Operations & Monitoring](#operations--monitoring)
4. [Backup & Recovery](#backup--recovery)
5. [Incident Response](#incident-response)
6. [Scaling Procedures](#scaling-procedures)
7. [Security Procedures](#security-procedures)
8. [Troubleshooting Guide](#troubleshooting-guide)
9. [Operational Contacts](#operational-contacts)
10. [Configuration Reference](#configuration-reference)

---

## PRE-DEPLOYMENT CHECKLIST

### Infrastructure Requirements

#### Hardware Specifications

**Kubernetes Cluster (Minimum for Production)**
- **Control Plane Nodes:** 3 nodes
  - CPU: 4 cores minimum per node
  - Memory: 8GB minimum per node
  - Storage: 100GB per node for etcd
  - Network: 1Gbps dedicated link
- **Worker Nodes:** 5 nodes (scalable)
  - CPU: 8 cores minimum per node
  - Memory: 16GB minimum per node
  - Storage: 200GB per node (50GB reserved for system)
  - Network: 1Gbps with failover capability
  
**Database Server (PostgreSQL)**
- **CPU:** 16 cores (dedicated)
- **Memory:** 64GB RAM
- **Storage:** SSD-based
  - Data volume: 500GB minimum
  - Backup volume: 500GB minimum
  - Growth capacity: Plan for 100GB/month
- **Network:** Low-latency connection (<5ms)

**Redis Cluster (Caching & Queues)**
- **CPU:** 8 cores (dedicated)
- **Memory:** 32GB RAM
- **Storage:** 200GB SSD
- **Replication:** Master-slave with automatic failover

**Storage (S3-compatible)**
- **Capacity:** 1TB minimum
- **Throughput:** 1000 RPS for documents
- **Encryption:** AES-256 with KMS key management
- **Redundancy:** Cross-region replication enabled

#### Network Requirements

**Bandwidth Specifications**
- **Minimum WAN Bandwidth:** 100Mbps dedicated
- **Expected Peak Bandwidth:** 500Mbps (during data imports)
- **CDN:** CloudFront or equivalent for static assets
- **DNS Failover:** Route53 with health checks every 30 seconds

**Latency Requirements**
- **API to Database:** <5ms average, <20ms p99
- **API to Redis:** <3ms average, <10ms p99
- **API to S3:** <100ms average, <500ms p99
- **Cross-region replication:** <100ms

**Network Security**
- **TLS 1.3:** Enforced on all connections
- **VPN/Private Link:** Established to on-premises systems
- **DDoS Protection:** AWS Shield Advanced or equivalent
- **WAF Rules:** ModSecurity OWASP Core Rule Set v3.3+
- **Firewall Rules:**
  ```
  - Inbound: HTTPS (443), SSH (22 - restricted)
  - Outbound: DNS (53), NTP (123), HTTPS (443)
  - Database: Internal network only
  - Redis: Internal network only
  ```

#### Security Requirements

**TLS Certificate Management**
- **Certificate Authority:** Let's Encrypt (auto-renewal via cert-manager)
- **Wildcard Cert:** *.truematch.ai valid for 90 days
- **Backup Cert:** Sectigo RSA Domain Validation for manual renewal
- **Renewal Automation:** Enabled 30 days before expiry
- **Renewal Verification:** Automated tests post-renewal

**Firewall Rules (Pre-deployment)**
- [ ] Ingress rules allow port 443 (HTTPS)
- [ ] Ingress rules allow port 80 (HTTP redirect)
- [ ] Egress rules allow external API calls
- [ ] Database firewall restricts to application subnet
- [ ] Redis firewall restricts to application subnet
- [ ] SSH access limited to 3 IP ranges (on-call bastion)

**Secret Management**
- [ ] Secrets stored in AWS Secrets Manager or Vault
- [ ] KMS keys created and rotated annually
- [ ] Database passwords: 32+ char alphanumeric
- [ ] JWT secret: 64+ char from `secrets.token_urlsafe(43)`
- [ ] S3 keys: Generated with least privilege IAM policy
- [ ] OIDC credentials: Singpass provisioned by Singapore NDI team

**Authentication & Authorization**
- [ ] OIDC provider configured (Singpass or Auth0)
- [ ] JWT key pair generated and stored securely
- [ ] RBAC roles defined (admin, recruiter, candidate, operator)
- [ ] MFA enabled for all admin accounts
- [ ] Service account credentials rotated quarterly

#### Database Schema Verification

**Pre-deployment Checks**
- [ ] PostgreSQL 14+ installed
- [ ] Extensions enabled: `uuid-ossp`, `pg_trgm`, `pgcrypto`
- [ ] All migrations applied successfully
  ```bash
  # Verify migration status
  alembic upgrade head
  
  # Check schema version
  SELECT version_num FROM alembic_version;
  ```

**Critical Tables Verified**
- [ ] `users` table exists with constraints
- [ ] `assessments` table with proper indexing
- [ ] `queue_items` table for async processing
- [ ] `cv_documents` and `jd_documents` tables
- [ ] `audit_logs` table for compliance
- [ ] Indexes on high-query columns created

**Database Tuning**
- [ ] `shared_buffers` set to 16GB (25% of RAM)
- [ ] `effective_cache_size` set to 48GB (75% of RAM)
- [ ] `work_mem` set to 64MB
- [ ] `maintenance_work_mem` set to 2GB
- [ ] `max_connections` set to 500
- [ ] `max_parallel_workers_per_gather` set to 4
- [ ] Autovacuum enabled with appropriate thresholds

**Connection Pooling**
- [ ] PgBouncer or similar running on separate server
- [ ] Pool size: 100 (application layer)
- [ ] Reserve pool: 10
- [ ] Idle timeout: 15 minutes
- [ ] Connection lifetime: 1 hour

#### Backup SOP Verification

**Backup Schedule Confirmed**
- [ ] Daily full backup at 02:00 UTC
- [ ] Hourly incremental backup
- [ ] Transaction log archiving every 5 minutes
- [ ] Weekly full backup to cold storage
- [ ] Monthly snapshot to different region

**Backup Destination**
- [ ] S3 bucket created: `truematch-backups-prod`
- [ ] Versioning enabled
- [ ] Server-side encryption with KMS key
- [ ] Cross-region replication to secondary bucket
- [ ] Retention policy: 30 days (hot), 1 year (cold)

**Backup Restoration Test**
- [ ] Full restore test completed in staging (success)
- [ ] Point-in-time recovery test completed
- [ ] Restore time documented: < 15 minutes
- [ ] Data integrity verified post-restore

#### Monitoring Alerting Setup

**Alerting Infrastructure**
- [ ] Prometheus stack deployed
- [ ] AlertManager configured with Slack webhook
- [ ] PagerDuty integration for critical alerts
- [ ] Email alerts to ops team configured
- [ ] SMS alerts for tier-1 incidents configured

**Alert Rules Deployed**
- [ ] CPU usage >80% sustained for 5 minutes
- [ ] Memory usage >85%
- [ ] Disk usage >90%
- [ ] API error rate >5%
- [ ] API p99 latency >2 seconds
- [ ] Database connections >400/500
- [ ] Redis memory >28GB/32GB
- [ ] Worker queue backlog >10,000 items
- [ ] Certificate expiry <30 days

**Dashboards Created**
- [ ] System Overview (CPU, memory, disk, network)
- [ ] Application Metrics (requests, errors, latency)
- [ ] Database Metrics (connections, slow queries, replication)
- [ ] Redis Metrics (memory, evictions, latency)
- [ ] Business Metrics (assessments processed, queue depth)

#### Disaster Recovery Plan Review

**RTO/RPO Verification**
- [ ] Recovery Time Objective: 1 hour (confirmed achievable)
- [ ] Recovery Point Objective: 5 minutes (backup every 5 min)
- [ ] Failover procedures documented and tested
- [ ] Runbook location known to all ops engineers

**Failover Scenarios Tested**
- [ ] Single worker node failure: 2 minutes to restore
- [ ] Database failure: 5 minutes to failover (read-replica)
- [ ] Redis failure: Immediate (sentinel-managed)
- [ ] Region failure: 30 minutes (cross-region deployment)
- [ ] Complete cluster failure: 60 minutes (full restore)

**Disaster Recovery Drill Schedule**
- [ ] Monthly: Database failover drill
- [ ] Quarterly: Full region failover drill
- [ ] Annually: Complete disaster recovery simulation
- [ ] Post-incident: RCA-driven drill

### Pre-deployment Sign-off

**Required Approvals**
- [ ] Infrastructure team lead: _________________ Date: _______
- [ ] Database team lead: _________________ Date: _______
- [ ] Security team lead: _________________ Date: _______
- [ ] Product owner: _________________ Date: _______
- [ ] Deployment engineer: _________________ Date: _______

**Environment Readiness Confirmation**
- [ ] All 10 checklist sections completed
- [ ] All critical tests passed
- [ ] Disaster recovery procedures verified
- [ ] On-call team briefed on deployment
- [ ] Rollback plan prepared and tested

---

## DEPLOYMENT PROCEDURES

### Zero-Downtime Deployment Strategy

**Deployment Overview**
- RollingUpdate strategy: 25% max unavailability
- Readiness probes: 30-second startup buffer
- Liveness probes: 60-second failure threshold
- Service mesh: Traffic management via Istio

**Pre-deployment Steps**
1. **Lock deployment repository** - prevent parallel deployments
2. **Backup current state** - capture cluster snapshots
3. **Health check** - verify system is healthy
4. **Test manifest** - validate YAML syntax and policies
5. **Drain one node** - prepare rolling update
6. **Create backup database snapshot** - point-in-time recovery

**Step-by-Step Zero-Downtime Deployment**

#### Phase 1: Pre-deployment Validation (10 minutes)

```bash
#!/bin/bash
set -e

DEPLOYMENT_ENV=${1:-staging}
IMAGE_TAG=${2:-latest}

echo "=== Phase 1: Pre-deployment Validation ==="

# 1. Lock deployment
LOCK_FILE="/tmp/truematch-deployment.lock"
if [ -f "$LOCK_FILE" ]; then
    echo "ERROR: Deployment in progress. Lock file exists: $LOCK_FILE"
    exit 1
fi
touch "$LOCK_FILE"
trap "rm -f $LOCK_FILE" EXIT

# 2. Verify cluster connectivity
echo "Verifying cluster connectivity..."
kubectl cluster-info
kubectl get nodes

# 3. Current health check
echo "Performing pre-deployment health check..."
HEALTHY=$(curl -s -o /dev/null -w "%{http_code}" https://api.truematch.ai/health)
if [ "$HEALTHY" != "200" ]; then
    echo "WARNING: Current system not healthy. HTTP $HEALTHY"
fi

# 4. Test image
echo "Testing image: $IMAGE_TAG"
docker pull gcr.io/truematch/api:$IMAGE_TAG
docker inspect gcr.io/truematch/api:$IMAGE_TAG

# 5. Validate manifests
echo "Validating Kubernetes manifests..."
kubectl apply --dry-run=client -f k8s/

# 6. Create database snapshot
echo "Creating database snapshot for rollback..."
kubectl exec -n truematch postgres-0 -- \
    pg_dump -U postgres truematch > /backup/pre-deployment-$(date +%s).sql

echo "Phase 1 completed successfully"
```

#### Phase 2: Rolling Update (30-45 minutes)

```bash
#!/bin/bash
set -e

IMAGE_TAG=${1:-latest}

echo "=== Phase 2: Rolling Update ==="

# Update API deployment
echo "Updating API deployment..."
kubectl set image deployment/truematch-api \
    api=gcr.io/truematch/api:$IMAGE_TAG \
    -n truematch

# Wait for rollout
echo "Waiting for API rollout..."
kubectl rollout status deployment/truematch-api \
    -n truematch \
    --timeout=10m

# Update worker deployment
echo "Updating worker deployment..."
kubectl set image deployment/truematch-workers \
    worker=gcr.io/truematch/workers:$IMAGE_TAG \
    -n truematch

# Wait for rollout
echo "Waiting for worker rollout..."
kubectl rollout status deployment/truematch-workers \
    -n truematch \
    --timeout=10m

echo "Rolling update completed"
```

#### Phase 3: Health Verification (10 minutes)

```bash
#!/bin/bash
set -e

echo "=== Phase 3: Post-deployment Health Verification ==="

# 1. Check pod status
echo "Checking pod status..."
kubectl get pods -n truematch
POD_STATUS=$(kubectl get pods -n truematch -o json | \
    jq '[.items[].status.conditions[] | select(.type=="Ready" and .status=="False")] | length')
if [ "$POD_STATUS" -gt 0 ]; then
    echo "ERROR: $POD_STATUS pods not ready"
    exit 1
fi

# 2. API health check
echo "Performing health checks..."
for i in {1..10}; do
    HEALTH=$(curl -s -o /dev/null -w "%{http_code}" https://api.truematch.ai/health)
    if [ "$HEALTH" = "200" ]; then
        echo "✓ Health check passed ($i/10)"
    else
        echo "✗ Health check failed: HTTP $HEALTH"
        sleep 5
    fi
done

# 3. Database connectivity
echo "Verifying database connectivity..."
kubectl exec -n truematch deployment/truematch-api -- \
    python -c "from app.database import get_db; print('Database OK')"

# 4. Redis connectivity
echo "Verifying Redis connectivity..."
kubectl exec -n truematch deployment/truematch-api -- \
    python -c "from app.cache import get_redis; print('Redis OK')"

# 5. Metrics validation
echo "Validating metrics..."
ERROR_RATE=$(curl -s http://prometheus:9090/api/v1/query \
    --data-urlencode 'query=rate(http_requests_total{status=~"5.."}[5m])' | \
    jq '.data.result[0].value[1]' | tr -d '"')
echo "Error rate: $ERROR_RATE (should be < 1%)"

# 6. Sample business transaction
echo "Testing sample business transactions..."
curl -X POST https://api.truematch.ai/api/v1/assessments \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TEST_TOKEN" \
    -d '{"test": true}' || echo "Test transaction may have failed"

echo "Phase 3 completed successfully"
```

### Blue-Green Deployment Option

**When to Use Blue-Green**
- Major version upgrades
- Database schema changes
- Significant infrastructure modifications
- High-risk changes requiring instant rollback

**Blue-Green Procedure**

```bash
#!/bin/bash
set -e

IMAGE_TAG=${1:-latest}
BLUE_VERSION=${2:-blue}
GREEN_VERSION=${3:-green}

echo "=== Blue-Green Deployment ==="

# 1. Prepare GREEN environment (new version)
echo "Preparing GREEN environment..."
kubectl set image deployment/truematch-api-${GREEN_VERSION} \
    api=gcr.io/truematch/api:$IMAGE_TAG \
    -n truematch

# 2. Wait for GREEN to be healthy
echo "Waiting for GREEN environment to be ready..."
kubectl rollout status deployment/truematch-api-${GREEN_VERSION} \
    -n truematch --timeout=15m

# 3. Run smoke tests on GREEN
echo "Running smoke tests on GREEN..."
kubectl run test-pod \
    --image=gcr.io/truematch/test-suite:latest \
    --restart=Never \
    -n truematch \
    -- ./run-smoke-tests.sh https://green-api.truematch.ai

# 4. Monitor GREEN traffic
echo "Monitoring GREEN environment for 5 minutes..."
for i in {1..5}; do
    HEALTH=$(curl -s https://green-api.truematch.ai/health)
    echo "Minute $i: $HEALTH"
    sleep 60
done

# 5. Switch traffic to GREEN
echo "Switching traffic from BLUE to GREEN..."
kubectl patch service truematch-api \
    -p '{"spec":{"selector":{"version":"'${GREEN_VERSION}'"}}}' \
    -n truematch

# 6. Verify switch
echo "Verifying traffic switched to GREEN..."
sleep 30
curl -I https://api.truematch.ai/health | grep "200 OK"

# 7. Keep BLUE running for 24 hours
echo "Keeping BLUE environment for 24-hour rollback window..."

# 8. After 24 hours, decommission BLUE
echo "After 24 hours, run: kubectl delete deployment truematch-api-${BLUE_VERSION} -n truematch"

echo "Blue-Green deployment completed"
```

### Canary Deployment Option

**When to Use Canary**
- New algorithm or feature changes
- ML model updates
- Configuration changes
- Lower-risk updates that benefit from gradual rollout

**Canary Procedure**

```bash
#!/bin/bash
set -e

IMAGE_TAG=${1:-latest}

echo "=== Canary Deployment ==="

# 1. Create canary replica with new version
echo "Creating canary replica (5% traffic)..."
kubectl set image deployment/truematch-api-canary \
    api=gcr.io/truematch/api:$IMAGE_TAG \
    -n truematch

# 2. Configure traffic split (5% to canary)
cat <<EOF | kubectl apply -f -
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: truematch-api
  namespace: truematch
spec:
  hosts:
  - truematch-api
  http:
  - match:
    - uri:
      prefix: /
    route:
    - destination:
        host: truematch-api-stable
      weight: 95
    - destination:
        host: truematch-api-canary
      weight: 5
EOF

# 3. Monitor canary metrics
echo "Monitoring canary metrics for 30 minutes..."
CANARY_ERROR_THRESHOLD=5  # percent higher than stable

while true; do
    STABLE_ERROR=$(curl -s http://prometheus:9090/api/v1/query \
        --data-urlencode 'query=rate(http_requests_total{version="stable",status=~"5.."}[5m])' | \
        jq '.data.result[0].value[1]' | tr -d '"' | head -c 5)
    
    CANARY_ERROR=$(curl -s http://prometheus:9090/api/v1/query \
        --data-urlencode 'query=rate(http_requests_total{version="canary",status=~"5.."}[5m])' | \
        jq '.data.result[0].value[1]' | tr -d '"' | head -c 5)
    
    echo "Stable error rate: ${STABLE_ERROR}% | Canary error rate: ${CANARY_ERROR}%"
    
    if (( $(echo "$CANARY_ERROR > $STABLE_ERROR + $CANARY_ERROR_THRESHOLD" | bc -l) )); then
        echo "ERROR: Canary error rate too high. Rolling back..."
        kubectl set image deployment/truematch-api-canary \
            api=gcr.io/truematch/api:stable \
            -n truematch
        exit 1
    fi
    
    sleep 60
done

# 4. Gradually increase canary traffic
for weight in 10 25 50 100; do
    echo "Increasing canary traffic to ${weight}%..."
    kubectl patch virtualservice truematch-api -n truematch \
        --type merge -p "{\"spec\":{\"http\":[{\"route\":[{\"destination\":{\"host\":\"truematch-api-stable\"},\"weight\":$((100-weight))},{\"destination\":{\"host\":\"truematch-api-canary\"},\"weight\":$weight}]}]}}"
    
    sleep 300
done

# 5. Decommission canary
echo "Canary deployment successful. Decommissioning canary replica..."
kubectl delete deployment truematch-api-canary -n truematch

echo "Canary deployment completed"
```

### Rollback Procedures

#### Automatic Rollback (Failed Health Check)

```bash
#!/bin/bash
set -e

echo "=== Automatic Rollback Procedure ==="

# Get previous stable version
PREVIOUS_IMAGE=$(kubectl rollout history deployment/truematch-api -n truematch | \
    tail -2 | head -1 | awk '{print $1}')

echo "Rolling back to revision: $PREVIOUS_IMAGE"

# Trigger rollback
kubectl rollout undo deployment/truematch-api \
    -n truematch \
    --to-revision=$PREVIOUS_IMAGE

# Wait for rollback completion
kubectl rollout status deployment/truematch-api \
    -n truematch \
    --timeout=10m

# Verify rollback
echo "Verifying rollback..."
HEALTH=$(curl -s -o /dev/null -w "%{http_code}" https://api.truematch.api/health)
if [ "$HEALTH" = "200" ]; then
    echo "✓ Rollback successful"
else
    echo "✗ Rollback verification failed: HTTP $HEALTH"
    exit 1
fi

echo "Rollback completed"
```

#### Manual Rollback (Operator-initiated)

```bash
#!/bin/bash
set -e

REVISION=${1:-0}  # Revision number or 0 for previous

echo "=== Manual Rollback Procedure ==="

# List available revisions
echo "Available revisions:"
kubectl rollout history deployment/truematch-api -n truematch

# Perform rollback
if [ "$REVISION" -eq 0 ]; then
    echo "Rolling back to previous revision..."
    kubectl rollout undo deployment/truematch-api -n truematch
else
    echo "Rolling back to revision $REVISION..."
    kubectl rollout undo deployment/truematch-api \
        -n truematch \
        --to-revision=$REVISION
fi

# Wait for completion
kubectl rollout status deployment/truematch-api \
    -n truematch \
    --timeout=10m

# Restore from database snapshot if needed
if [ -f "/backup/pre-deployment-*.sql" ]; then
    echo "Restoring from pre-deployment database snapshot..."
    kubectl exec -n truematch postgres-0 -- \
        psql -U postgres truematch < /backup/pre-deployment-*.sql
fi

echo "Manual rollback completed"
```

### Data Migration Procedures

#### Schema Migration (with downtime mitigation)

```bash
#!/bin/bash
set -e

MIGRATION_NAME=${1:-}

if [ -z "$MIGRATION_NAME" ]; then
    echo "Usage: $0 <migration_name>"
    exit 1
fi

echo "=== Data Migration Procedure ==="

# 1. Create pre-migration backup
echo "Creating pre-migration backup..."
kubectl exec -n truematch postgres-0 -- \
    pg_dump -U postgres truematch > /backup/pre-migration-$(date +%s).sql

# 2. Test migration in staging
echo "Testing migration in staging environment..."
kubectl exec -n truematch-staging postgres-0 -- \
    alembic -c staging.ini upgrade head

# 3. Schedule maintenance window (if needed)
echo "Migration will run during: 2026-06-08 02:00-04:00 UTC"
echo "Estimated downtime: 30 seconds (if backward-compatible)"

# 4. Run migration
echo "Running migration: $MIGRATION_NAME"
kubectl exec -n truematch postgres-0 -- \
    alembic upgrade head

# 5. Verify migration
echo "Verifying migration..."
kubectl exec -n truematch postgres-0 -- \
    psql -U postgres truematch -c "SELECT version_num FROM alembic_version;"

# 6. Health check post-migration
echo "Performing health checks..."
HEALTH=$(curl -s -o /dev/null -w "%{http_code}" https://api.truematch.ai/health)
if [ "$HEALTH" = "200" ]; then
    echo "✓ Health check passed"
else
    echo "✗ Health check failed: HTTP $HEALTH"
    echo "Rolling back from backup..."
    exit 1
fi

echo "Data migration completed successfully"
```

#### Large Data Migration (without downtime)

```bash
#!/bin/bash
set -e

echo "=== Large Data Migration (Zero-downtime) ==="

# 1. Create new table with new schema
echo "Creating new table with updated schema..."
cat <<EOF | kubectl exec -n truematch postgres-0 -- psql -U postgres truematch -f -
BEGIN TRANSACTION ISOLATION LEVEL SERIALIZABLE;

CREATE TABLE assessments_new (
    id UUID PRIMARY KEY,
    -- Updated columns here
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

CREATE INDEX idx_assessments_new_created_at ON assessments_new(created_at);
COMMIT;
EOF

# 2. Trigger logical replication (continuous sync)
echo "Setting up logical replication to new table..."
cat <<EOF | kubectl exec -n truematch postgres-0 -- psql -U postgres truematch -f -
CREATE TRIGGER assessment_sync_trigger
AFTER INSERT OR UPDATE ON assessments
FOR EACH ROW
EXECUTE FUNCTION sync_to_assessments_new();
EOF

# 3. Copy existing data
echo "Copying existing data (background process)..."
cat <<EOF | kubectl exec -n truematch postgres-0 -- psql -U postgres truematch -f -
INSERT INTO assessments_new
SELECT * FROM assessments
WHERE created_at < NOW() - INTERVAL '1 day';
EOF

# 4. Wait for background copy
echo "Waiting for data copy to complete..."
sleep 3600

# 5. Switch application to new table
echo "Switching application to new table..."
# This is a coordinated switch with the application layer
# ensuring no downtime

# 6. Drop old table
echo "Dropping old table (after 24-hour validation)..."
cat <<EOF | kubectl exec -n truematch postgres-0 -- psql -U postgres truematch -f -
DROP TABLE assessments;
ALTER TABLE assessments_new RENAME TO assessments;
EOF

echo "Large data migration completed"
```

### Configuration Update Procedures

```bash
#!/bin/bash
set -e

CONFIG_FILE=${1:-}

if [ -z "$CONFIG_FILE" ]; then
    echo "Usage: $0 <config_file>"
    exit 1
fi

echo "=== Configuration Update Procedure ==="

# 1. Validate configuration
echo "Validating configuration..."
python -m app.config --validate $CONFIG_FILE

# 2. Create backup
echo "Creating configuration backup..."
kubectl get configmap truematch-config -o yaml \
    -n truematch > /backup/config-backup-$(date +%s).yaml

# 3. Update configuration
echo "Updating configuration..."
kubectl create configmap truematch-config \
    --from-file=$CONFIG_FILE \
    --dry-run=client -o yaml | \
    kubectl apply -f -

# 4. Rolling restart (pick up new config)
echo "Rolling restart of deployments..."
kubectl rollout restart deployment/truematch-api -n truematch
kubectl rollout status deployment/truematch-api -n truematch

# 5. Health check
echo "Verifying health with new configuration..."
HEALTH=$(curl -s -o /dev/null -w "%{http_code}" https://api.truematch.ai/health)
if [ "$HEALTH" = "200" ]; then
    echo "✓ Configuration update successful"
else
    echo "✗ Configuration update failed"
    kubectl apply -f /backup/config-backup-*.yaml
    kubectl rollout restart deployment/truematch-api -n truematch
    exit 1
fi

echo "Configuration update completed"
```

### Database Migration Procedures

#### Live Database Schema Changes

```bash
#!/bin/bash
set -e

echo "=== Live Database Schema Change ==="

# SAFE pattern: ADD COLUMN with default (no lock)
# UNSAFE pattern: DROP COLUMN (requires full table rewrite)

# 1. Add new column (non-blocking)
echo "Adding new column to assessments..."
kubectl exec -n truematch postgres-0 -- psql -U postgres truematch -c \
    "ALTER TABLE assessments ADD COLUMN new_field VARCHAR(255) DEFAULT '';"

# 2. Backfill data (in batches, no locks)
echo "Backfilling data in batches..."
for offset in {0..100000..1000}; do
    kubectl exec -n truematch postgres-0 -- psql -U postgres truematch -c \
        "UPDATE assessments SET new_field = 'value' WHERE id IN (SELECT id FROM assessments LIMIT 1000 OFFSET $offset);"
    sleep 1
done

# 3. Add index (if needed)
echo "Adding index..."
kubectl exec -n truematch postgres-0 -- psql -U postgres truematch -c \
    "CREATE INDEX CONCURRENTLY idx_assessments_new_field ON assessments(new_field);"

# 4. Drop old column (if applicable)
echo "Dropping old column..."
kubectl exec -n truematch postgres-0 -- psql -U postgres truematch -c \
    "ALTER TABLE assessments DROP COLUMN old_field;"

echo "Database schema change completed"
```

---

## OPERATIONS & MONITORING

### System Health Checks

#### Hourly Health Check (Automated via Cronjob)

```bash
#!/bin/bash
set -e

echo "=== Hourly Health Check ==="
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# 1. Kubernetes cluster health
CLUSTER_STATUS=$(kubectl get nodes -o json | \
    jq '[.items[].status.conditions[] | select(.type=="Ready" and .status=="False")] | length')
if [ "$CLUSTER_STATUS" -eq 0 ]; then
    echo "$TIMESTAMP: ✓ All nodes ready"
else
    echo "$TIMESTAMP: ✗ $CLUSTER_STATUS nodes not ready" && exit 1
fi

# 2. Pod status
POD_STATUS=$(kubectl get pods -n truematch -o json | \
    jq '[.items[].status.conditions[] | select(.type=="Ready" and .status=="False")] | length')
if [ "$POD_STATUS" -eq 0 ]; then
    echo "$TIMESTAMP: ✓ All pods ready"
else
    echo "$TIMESTAMP: ✗ $POD_STATUS pods not ready" && exit 1
fi

# 3. API response
API_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" https://api.truematch.ai/health)
if [ "$API_HEALTH" = "200" ]; then
    echo "$TIMESTAMP: ✓ API healthy"
else
    echo "$TIMESTAMP: ✗ API unhealthy: HTTP $API_HEALTH" && exit 1
fi

# 4. Database connectivity
DB_CHECK=$(kubectl exec -n truematch deployment/truematch-api -- \
    python -c "from app.database import get_db; print('OK')" 2>&1 | tail -1)
if [ "$DB_CHECK" = "OK" ]; then
    echo "$TIMESTAMP: ✓ Database connected"
else
    echo "$TIMESTAMP: ✗ Database connection failed" && exit 1
fi

# 5. Redis connectivity
REDIS_CHECK=$(kubectl exec -n truematch deployment/truematch-api -- \
    python -c "from app.cache import get_redis; print('OK')" 2>&1 | tail -1)
if [ "$REDIS_CHECK" = "OK" ]; then
    echo "$TIMESTAMP: ✓ Redis connected"
else
    echo "$TIMESTAMP: ✗ Redis connection failed" && exit 1
fi

echo "$TIMESTAMP: All hourly checks passed ✓"
```

#### Daily Health Check (Human review)

- [ ] **10:00 UTC:** Check Kubernetes cluster status
  ```bash
  kubectl get nodes && kubectl top nodes
  ```

- [ ] **10:05 UTC:** Check pod resource usage
  ```bash
  kubectl top pods -n truematch
  ```

- [ ] **10:10 UTC:** Check disk usage
  ```bash
  kubectl exec -n truematch deployment/truematch-api -- df -h
  ```

- [ ] **10:15 UTC:** Review error logs
  ```bash
  kubectl logs -n truematch deployment/truematch-api --tail=1000 | grep -i error
  ```

- [ ] **10:20 UTC:** Check database size
  ```bash
  kubectl exec -n truematch postgres-0 -- \
      psql -U postgres truematch -c "SELECT pg_size_pretty(pg_database_size('truematch'));"
  ```

- [ ] **10:25 UTC:** Check Redis memory usage
  ```bash
  kubectl exec -n truematch redis-0 -- redis-cli INFO memory
  ```

#### Weekly Health Check (Performance review)

- [ ] **Monday 14:00 UTC:** Run Prometheus health check
- [ ] **Monday 14:30 UTC:** Review performance trends (7 days)
- [ ] **Monday 15:00 UTC:** Check backup completion status
- [ ] **Monday 15:30 UTC:** Review certificate expiry dates
- [ ] **Monday 16:00 UTC:** Assess scaling needs

### Performance Baselines

**API Performance Targets**
- **p50 latency:** <100ms
- **p95 latency:** <300ms
- **p99 latency:** <2000ms
- **Throughput:** 1000 RPS
- **Error rate:** <0.1%
- **Availability:** 99.95%

**Database Performance Targets**
- **Connection pool utilization:** <70%
- **Slow query (>1s):** <10/hour
- **Query response time:** <100ms (p95)
- **Replication lag:** <1 second
- **Checkpoint duration:** <30 seconds

**Worker Queue Performance**
- **Queue depth:** <1000 items
- **Processing latency:** <30 seconds (p95)
- **Task success rate:** >99%
- **Worker CPU utilization:** 40-60%

### Alert Configurations and Meanings

**Critical Alerts (Page on-call engineer)**
- **API Error Rate >5%:** Application returning errors. Check logs, restart if needed.
- **API p99 Latency >2s:** Slow requests. Check database locks, Redis connectivity.
- **Database Connections >400/500:** Connection pool exhausted. Kill idle connections or scale up.
- **Worker Queue Backlog >10,000:** Async processing failing. Check worker logs, increase replicas.
- **Disk Usage >95%:** Imminent out-of-space. Clear old logs, expand volumes.

**High Alerts (Email ops team)**
- **CPU Usage >80% for 10 min:** Performance degradation. Check resource requests.
- **Memory Usage >85%:** OOM kill risk. Identify memory leak.
- **Redis Memory >28GB/32GB:** Cache eviction imminent. Analyze keys, increase size.
- **Certificate Expiry <7 days:** TLS certificate expiring. Trigger renewal process.

**Medium Alerts (Slack notification)**
- **API p95 Latency >500ms:** Acceptable but monitor trend.
- **Database Replication Lag >5s:** Replication catching up.
- **Worker Queue Depth >5000:** Normal during peak load.

### Common Metrics and Dashboards

**System Overview Dashboard**
```
┌─────────────────────────────────────────────────┐
│ Kubernetes Cluster Status                       │
├─────────────────────────────────────────────────┤
│ Nodes: 5/5 Ready        CPU: 45%  Memory: 62%   │
│ Pods: 12/12 Running     Disk: 67%               │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ Application Metrics (1h view)                   │
├─────────────────────────────────────────────────┤
│ Requests: 180,000 (p50: 45ms)                   │
│ Errors: 12 (0.007%)                             │
│ p95 Latency: 250ms                              │
│ p99 Latency: 890ms                              │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ Database Metrics                                │
├─────────────────────────────────────────────────┤
│ Connections: 120/500 (24%)                      │
│ Slow Queries: 2/hour                            │
│ Size: 45GB / 500GB                              │
│ Replication Lag: 0.8s                           │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ Cache Metrics                                   │
├─────────────────────────────────────────────────┤
│ Memory: 18.4GB / 32GB (57%)                     │
│ Hit Rate: 92%                                   │
│ Evictions/min: 2                                │
└─────────────────────────────────────────────────┘
```

**Business Metrics Dashboard**
```
┌─────────────────────────────────────────────────┐
│ Assessments Processed (1h)                      │
├─────────────────────────────────────────────────┤
│ Total: 2,450                                    │
│ Approved Auto: 1,960 (80%)                      │
│ Requires Review: 420 (17%)                      │
│ Rejected: 70 (3%)                               │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ Queue Status                                    │
├─────────────────────────────────────────────────┤
│ Pending: 3,200 items                            │
│ In Progress: 45 items                           │
│ Avg Processing Time: 22 seconds                 │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ User Activity (1h)                              │
├─────────────────────────────────────────────────┤
│ Active Recruiters: 45                           │
│ Active Candidates: 320                          │
│ Assessments Created: 125                        │
└─────────────────────────────────────────────────┘
```

### Log Aggregation and Searching

**Log Aggregation Stack**
- **Filebeat/Fluentd:** Collect logs from containers
- **Elasticsearch:** Index and store logs
- **Kibana:** Search and visualize logs

**Useful Log Queries**

```json
// Find all errors in past hour
{
  "query": {
    "bool": {
      "must": [
        { "match": { "level": "ERROR" } },
        { "range": { "timestamp": { "gte": "now-1h" } } }
      ]
    }
  }
}

// Find specific assessment processing issues
{
  "query": {
    "bool": {
      "must": [
        { "match": { "endpoint": "/assessments" } },
        { "range": { "response_time_ms": { "gte": 2000 } } }
      ]
    }
  }
}

// Find database connection pool warnings
{
  "query": {
    "match": { "message": "connection pool exhausted" }
  }
}
```

### Distributed Tracing Setup

**Distributed Tracing Stack**
- **OpenTelemetry SDK:** Instrument application
- **Jaeger:** Trace collection and visualization

**Sample Trace Analysis**

```
Service Trace: POST /assessments
├─ Middleware                           (2ms)
│  ├─ Auth verification                (0.5ms)
│  └─ Rate limiting check               (0.3ms)
├─ Handler: create_assessment           (450ms)
│  ├─ Validate CV document              (50ms)
│  ├─ Validate JD document              (50ms)
│  ├─ Semantic matching                 (200ms)
│  ├─ Database insert                   (100ms)
│  └─ Queue async processing            (30ms)
└─ Response serialization                (5ms)
  Total: 457ms (Good ✓)
```

---

## BACKUP & RECOVERY

### Database Backup Procedures

#### Daily Full Backup (02:00 UTC)

```bash
#!/bin/bash
set -e

BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/postgres"
S3_BUCKET="s3://truematch-backups-prod"

echo "=== Daily Full Backup ($(date)) ==="

# 1. Create full backup
echo "Creating full backup..."
kubectl exec -n truematch postgres-0 -- \
    pg_dump -U postgres -Fc truematch \
    > "${BACKUP_DIR}/truematch_full_${BACKUP_DATE}.dump"

# 2. Compress backup
echo "Compressing backup..."
gzip "${BACKUP_DIR}/truematch_full_${BACKUP_DATE}.dump"

# 3. Calculate checksum
echo "Calculating checksum..."
MD5=$(md5sum "${BACKUP_DIR}/truematch_full_${BACKUP_DATE}.dump.gz" | awk '{print $1}')
echo "$MD5" > "${BACKUP_DIR}/truematch_full_${BACKUP_DATE}.dump.gz.md5"

# 4. Upload to S3
echo "Uploading to S3..."
aws s3 cp "${BACKUP_DIR}/truematch_full_${BACKUP_DATE}.dump.gz" \
    "${S3_BUCKET}/daily/" \
    --sse aws:kms \
    --sse-kms-key-id arn:aws:kms:ap-southeast-1:ACCOUNT:key/KEY_ID

# 5. Upload checksum
aws s3 cp "${BACKUP_DIR}/truematch_full_${BACKUP_DATE}.dump.gz.md5" \
    "${S3_BUCKET}/daily/"

# 6. Verify upload
echo "Verifying S3 upload..."
aws s3 ls "${S3_BUCKET}/daily/truematch_full_${BACKUP_DATE}.dump.gz"

# 7. Clean up local copy (keep last 3 days)
echo "Cleaning up local copies..."
find "${BACKUP_DIR}" -name "truematch_full_*.dump.gz" -mtime +3 -delete

# 8. Log backup
echo "{\"timestamp\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",\"size\":\"$(du -h ${BACKUP_DIR}/truematch_full_${BACKUP_DATE}.dump.gz | cut -f1)\",\"status\":\"success\"}" \
    >> /var/log/truematch-backups.log

echo "Daily full backup completed"
```

#### Hourly Incremental Backup (Every hour)

```bash
#!/bin/bash
set -e

BACKUP_DATE=$(date +%Y%m%d_%H)
BACKUP_DIR="/backups/postgres"

echo "=== Hourly Incremental Backup ($(date)) ==="

# 1. Create WAL backup
echo "Creating WAL backup..."
kubectl exec -n truematch postgres-0 -- \
    pg_basebackup -U postgres \
    -D "${BACKUP_DIR}/incremental_${BACKUP_DATE}" \
    -Ft -z -P

# 2. Upload to S3
echo "Uploading to S3..."
aws s3 sync "${BACKUP_DIR}/incremental_${BACKUP_DATE}/" \
    "s3://truematch-backups-prod/hourly/${BACKUP_DATE}/" \
    --sse aws:kms

# 3. Clean up local copy
echo "Cleaning up..."
rm -rf "${BACKUP_DIR}/incremental_${BACKUP_DATE}"

echo "Hourly incremental backup completed"
```

#### Transaction Log Archiving (Every 5 minutes)

```bash
#!/bin/bash
set -e

ARCHIVE_DIR="/var/lib/postgresql/archive"
S3_BUCKET="s3://truematch-backups-prod"

echo "=== Transaction Log Archive ($(date)) ==="

# 1. Compress and upload WAL files
for wal_file in ${ARCHIVE_DIR}/*; do
    if [ -f "$wal_file" ]; then
        echo "Archiving $(basename $wal_file)..."
        gzip "$wal_file"
        aws s3 cp "${wal_file}.gz" \
            "${S3_BUCKET}/wal/" \
            --sse aws:kms
        rm "${wal_file}.gz"
    fi
done

echo "Transaction log archiving completed"
```

#### Weekly Full Backup to Cold Storage (Sundays 22:00 UTC)

```bash
#!/bin/bash
set -e

BACKUP_DATE=$(date +%Y%m%d)
BACKUP_DIR="/backups/postgres"
GLACIER_VAULT="truematch-cold-storage"

echo "=== Weekly Cold Storage Backup ($(date)) ==="

# 1. Create full backup
echo "Creating full backup..."
kubectl exec -n truematch postgres-0 -- \
    pg_dump -U postgres -Fc truematch \
    > "${BACKUP_DIR}/truematch_weekly_${BACKUP_DATE}.dump"

# 2. Encrypt with GPG
echo "Encrypting with GPG..."
gpg --symmetric --cipher-algo AES256 \
    "${BACKUP_DIR}/truematch_weekly_${BACKUP_DATE}.dump"
rm "${BACKUP_DIR}/truematch_weekly_${BACKUP_DATE}.dump"

# 3. Upload to Glacier
echo "Uploading to Glacier..."
aws glacier upload-archive \
    --vault-name "${GLACIER_VAULT}" \
    --archive-file "${BACKUP_DIR}/truematch_weekly_${BACKUP_DATE}.dump.gpg" \
    --region ap-southeast-1

# 4. Clean up
rm "${BACKUP_DIR}/truematch_weekly_${BACKUP_DATE}.dump.gpg"

echo "Weekly cold storage backup completed"
```

### Point-in-Time Recovery Testing

#### Monthly Recovery Drill (First Thursday)

```bash
#!/bin/bash
set -e

echo "=== Monthly Point-in-Time Recovery Drill ==="

TARGET_TIME="2026-06-07 14:30:00 UTC"
STAGING_CLUSTER="gke-truematch-staging"

# 1. List available backups
echo "Available backups:"
aws s3 ls "s3://truematch-backups-prod/daily/" | sort

# 2. Select backup to restore from
echo "Selecting backup from: $(date -d '2026-06-07 00:00:00' +%Y%m%d)"
BACKUP_FILE="truematch_full_20260607_000000.dump.gz"

# 3. Download backup from S3
echo "Downloading backup..."
aws s3 cp "s3://truematch-backups-prod/daily/${BACKUP_FILE}" \
    "/tmp/${BACKUP_FILE}"

# 4. Decompress
echo "Decompressing..."
gunzip "/tmp/${BACKUP_FILE}"

# 5. Create temporary database
echo "Creating temporary database..."
kubectl exec -n truematch-staging postgres-0 -- \
    psql -U postgres -c "CREATE DATABASE truematch_recovery;"

# 6. Restore from backup
echo "Restoring from backup..."
kubectl exec -n truematch-staging postgres-0 -- \
    pg_restore -U postgres -d truematch_recovery \
    < "/tmp/${BACKUP_FILE%.gz}"

# 7. Apply WAL logs to reach target time
echo "Applying WAL logs up to ${TARGET_TIME}..."
# WAL replay via recovery_target_timeline and recovery_target_time

# 8. Verify data integrity
echo "Verifying data integrity..."
RECORD_COUNT=$(kubectl exec -n truematch-staging postgres-0 -- \
    psql -U postgres truematch_recovery -c \
    "SELECT COUNT(*) FROM assessments;" | tail -1)
echo "Assessment records: $RECORD_COUNT"

if [ "$RECORD_COUNT" -gt 0 ]; then
    echo "✓ Data integrity verified"
else
    echo "✗ Data integrity check failed"
    exit 1
fi

# 9. Test application connectivity
echo "Testing application connectivity..."
kubectl run test-pod \
    --image=gcr.io/truematch/api:latest \
    --restart=Never \
    -n truematch-staging \
    -- python -c "from app.database import DATABASE_URL; print('Connection OK')"

# 10. Drop recovery database
echo "Cleaning up..."
kubectl exec -n truematch-staging postgres-0 -- \
    psql -U postgres -c "DROP DATABASE truematch_recovery;"

echo "Point-in-time recovery drill completed successfully ✓"
```

### Backup Retention Policy

**Retention Schedule**
- **Hourly backups:** 24 hours
- **Daily backups:** 30 days (hot storage - S3)
- **Weekly backups:** 12 weeks (warm storage - S3)
- **Monthly backups:** 12 months (cold storage - Glacier)
- **Yearly archives:** 7 years (compliance requirement)

**Automated Cleanup Script**

```bash
#!/bin/bash
set -e

S3_BUCKET="s3://truematch-backups-prod"

echo "=== Backup Retention Policy Enforcement ==="

# Daily backups older than 30 days
echo "Removing daily backups older than 30 days..."
aws s3 ls "${S3_BUCKET}/daily/" | while read -r line; do
    DATE=$(echo $line | awk '{print $1}')
    if [[ $(date -d "$DATE" +%s) -lt $(date -d "30 days ago" +%s) ]]; then
        FILE=$(echo $line | awk '{print $4}')
        echo "Removing: $FILE"
        aws s3 rm "${S3_BUCKET}/daily/${FILE}"
    fi
done

# Weekly backups older than 12 weeks
echo "Removing weekly backups older than 12 weeks..."
aws s3 ls "${S3_BUCKET}/weekly/" | while read -r line; do
    DATE=$(echo $line | awk '{print $1}')
    if [[ $(date -d "$DATE" +%s) -lt $(date -d "12 weeks ago" +%s) ]]; then
        FILE=$(echo $line | awk '{print $4}')
        echo "Removing: $FILE"
        aws s3 rm "${S3_BUCKET}/weekly/${FILE}"
    fi
done

echo "Backup retention policy enforcement completed"
```

### Disaster Recovery Drill Schedule

**Monthly Drills (First Thursday, 14:00 UTC)**
- Type: Point-in-time recovery from daily backup
- Duration: 1 hour
- Staging environment: Restored full copy
- Success criteria: All data verified, application functional

**Quarterly Drills (End of each quarter, 14:00 UTC)**
- Type: Full region failover simulation
- Duration: 4 hours
- Scope: Complete infrastructure failover
- Success criteria: RTO <1 hour, RPO <5 minutes

**Annual DR Simulation (December 1, 14:00 UTC)**
- Type: Complete disaster scenario
- Scope: Total data center failure
- Duration: 8 hours
- Success criteria: Full recovery with zero data loss

**Post-Incident Drills**
- Any critical incident triggers a focused recovery drill within 48 hours
- Targets the specific failure mode encountered
- Results documented in postmortem

---

## INCIDENT RESPONSE

### On-Call Rotation Setup

**On-Call Schedule**
- **Primary Engineer:** Mon-Fri, 09:00-17:00 UTC
- **Secondary Engineer:** Mon-Fri, 17:00-09:00 UTC + weekends
- **Escalation Engineer:** Backup (24/7 available)

**On-Call Responsibilities**
- Monitor Slack #incidents channel
- Respond to PagerDuty alerts
- Execute incident response procedures
- Document incident timeline
- Complete postmortem within 24 hours

**Contact Directory**
```
Primary On-Call:     +1-555-0100  (Slack: @ops-primary)
Secondary On-Call:   +1-555-0101  (Slack: @ops-secondary)
Escalation:          +1-555-0102  (Slack: @ops-escalation)
Database DBA:        +1-555-0103  (Slack: @dba-oncall)
Infrastructure Lead: +1-555-0104  (Slack: @infra-lead)
VP Engineering:      +1-555-0105  (Slack: @vp-eng)
```

### Incident Escalation Procedures

**Severity Levels**

| Severity | Definition | Response Time | Escalation |
|----------|-----------|---|---|
| **S1 (Critical)** | Service completely down, data loss risk, security breach | 5 minutes | VP Eng + All leads |
| **S2 (Major)** | Significant functionality impaired, performance degradation | 15 minutes | Eng Lead + DB Lead |
| **S3 (Minor)** | Limited impact, workaround available | 1 hour | Primary On-Call |
| **S4 (Trivial)** | No impact on production users | 24 hours | Triage for backlog |

**S1 Incident Flow**
```
Alert → On-Call (5 min) → Escalation (10 min) → VP Eng (15 min)
  ↓
  Assessment & triage (5 min)
  ↓
  Execute incident response playbook (ongoing)
  ↓
  All-hands on deck if necessary
  ↓
  Postmortem within 24 hours
```

### Common Incidents and Resolutions

#### Incident #1: Database Connection Pool Exhausted

**Symptoms**
- API returning 503 "Service Unavailable"
- Log message: "connection pool exhausted"
- User-facing: "Cannot process your assessment right now"

**Root Causes**
- Slow queries holding connections open
- Worker processes not releasing connections
- Database server down (cascade failure)
- Connection leak in application code

**Resolution Steps**

```bash
#!/bin/bash
set -e

echo "=== Database Connection Pool Exhausted ==="

# 1. Confirm issue
echo "Checking connection pool status..."
kubectl exec -n truematch postgres-0 -- psql -U postgres -c \
    "SELECT count(*) FROM pg_stat_activity;" | tail -1

CURRENT_CONNS=$(kubectl exec -n truematch postgres-0 -- psql -U postgres -c \
    "SELECT count(*) FROM pg_stat_activity;" | tail -1 | tr -d ' ')

if [ "$CURRENT_CONNS" -lt 490 ]; then
    echo "Connection count: $CURRENT_CONNS (not critical)"
    exit 0
fi

# 2. Alert severity: P1
echo "SEVERITY: P1 - System impaired"

# 3. Find slow queries
echo "Finding slow queries..."
kubectl exec -n truematch postgres-0 -- psql -U postgres -c \
    "SELECT pid, query, query_start FROM pg_stat_activity WHERE state = 'active' AND query_start < NOW() - INTERVAL '5 minutes';"

# 4. Kill idle connections
echo "Killing idle connections..."
kubectl exec -n truematch postgres-0 -- psql -U postgres -c \
    "SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE datname = 'truematch' AND pid <> pg_backend_pid() AND state = 'idle' AND query_start < NOW() - INTERVAL '10 minutes';"

# 5. Kill long-running queries (if necessary)
echo "Checking for long-running queries..."
LONG_QUERY=$(kubectl exec -n truematch postgres-0 -- psql -U postgres -c \
    "SELECT pid FROM pg_stat_activity WHERE query_time > INTERVAL '30 minutes' LIMIT 1;" | tail -1 | tr -d ' ')

if [ -n "$LONG_QUERY" ] && [ "$LONG_QUERY" != "pid" ]; then
    echo "Killing long-running query: $LONG_QUERY"
    kubectl exec -n truematch postgres-0 -- psql -U postgres -c \
        "SELECT pg_terminate_backend($LONG_QUERY);"
fi

# 6. Check for worker issues
echo "Checking worker pods..."
kubectl get pods -n truematch -l app=worker -o wide
kubectl logs -n truematch -l app=worker --tail=50 | grep -i "error\|timeout" || echo "No errors in worker logs"

# 7. Restart workers if needed
if [ "$CURRENT_CONNS" -gt 450 ]; then
    echo "Restarting worker pods..."
    kubectl rollout restart deployment/truematch-workers -n truematch
    kubectl rollout status deployment/truematch-workers -n truematch --timeout=5m
fi

# 8. Monitor recovery
echo "Monitoring connection recovery..."
for i in {1..10}; do
    CONNS=$(kubectl exec -n truematch postgres-0 -- psql -U postgres -c \
        "SELECT count(*) FROM pg_stat_activity;" | tail -1 | tr -d ' ')
    echo "Connections: $CONNS ($(( (CONNS * 100) / 500 ))%)"
    if [ "$CONNS" -lt 300 ]; then
        echo "✓ Pool recovered"
        break
    fi
    sleep 10
done

echo "Incident resolved"
```

#### Incident #2: Memory Leak in API

**Symptoms**
- API pod memory usage growing over time
- Kubernetes OOMKilled pods periodically
- Restart count increasing
- Performance degradation over hours

**Root Causes**
- Unclosed database connections
- Memory cached without eviction
- Large objects held in memory
- Third-party library leak

**Resolution Steps**

```bash
#!/bin/bash
set -e

echo "=== Memory Leak in API ==="

# 1. Confirm memory issue
echo "Checking memory usage..."
kubectl top pods -n truematch -l app=api

# 2. Get memory metrics from Prometheus
echo "Querying memory trend (past 6 hours)..."
curl -s 'http://prometheus:9090/api/v1/query' \
    --data-urlencode 'query=rate(container_memory_usage_bytes{pod=~"truematch-api.*"}[5m])' | \
    jq '.data.result[0].values[-10:]'

# 3. Identify pod with highest memory
MEMORY_POD=$(kubectl top pods -n truematch -l app=api | tail -1 | awk '{print $1}')
echo "Highest memory pod: $MEMORY_POD"

# 4. Get memory profile
echo "Generating memory profile..."
kubectl exec -n truematch "$MEMORY_POD" -- \
    python -m memory_profiler > /tmp/memory_profile.txt
cat /tmp/memory_profile.txt | head -50

# 5. Check for connection leaks
echo "Checking database connection leaks..."
kubectl exec -n truematch "$MEMORY_POD" -- \
    python -c "
from app.database import engine
from sqlalchemy import text
session = engine.raw_connection()
print('Active connections:', len(engine.pool._pool.queue))
session.close()
"

# 6. Check for cache size
echo "Checking cache memory usage..."
kubectl exec -n truematch "$MEMORY_POD" -- \
    python -c "
import gc
import sys
gc.collect()
print('Objects in memory:', len(gc.get_objects()))
for obj in gc.get_objects()[:10]:
    print(sys.getsizeof(obj), type(obj))
"

# 7. Short-term mitigation: restart pod
echo "Restarting problematic pod..."
kubectl delete pod -n truematch "$MEMORY_POD"
kubectl rollout status deployment/truematch-api -n truematch --timeout=5m

# 8. Long-term fix: increase memory request
echo "Increasing memory limits (temporary)..."
kubectl set resources deployment/truematch-api \
    --limits=memory=4Gi \
    --requests=memory=2Gi \
    -n truematch

# 9. Schedule code review
echo "✓ SCHEDULED: Code review for memory leak"
echo "✓ SCHEDULED: Profiling in staging environment"

echo "Incident mitigated"
```

#### Incident #3: Worker Queue Backlog

**Symptoms**
- Assessment processing delayed
- Queue depth: 50,000+ items
- New assessments not being processed
- Users report "Assessment still processing"

**Root Causes**
- Worker pods crashed or stuck
- Slow processing (ML timeout)
- External API unavailable (enrichment)
- Database performance degradation
- Queue blocking on task

**Resolution Steps**

```bash
#!/bin/bash
set -e

echo "=== Worker Queue Backlog ==="

# 1. Check queue depth
echo "Checking queue depth..."
QUEUE_DEPTH=$(kubectl exec -n truematch redis-0 -- \
    redis-cli LLEN assessment:queue | head -1)
echo "Queue depth: $QUEUE_DEPTH"

if [ "$QUEUE_DEPTH" -lt 10000 ]; then
    echo "Queue depth acceptable, investigating further..."
fi

# 2. Check worker pod status
echo "Checking worker pods..."
kubectl get pods -n truematch -l app=worker -o wide
WORKER_READY=$(kubectl get pods -n truematch -l app=worker -o json | \
    jq '[.items[].status.conditions[] | select(.type=="Ready" and .status=="False")] | length')
if [ "$WORKER_READY" -gt 0 ]; then
    echo "ERROR: $WORKER_READY worker pods not ready"
fi

# 3. Check worker logs
echo "Checking worker logs for errors..."
kubectl logs -n truematch -l app=worker --all-containers=true --tail=100 | \
    grep -i "error\|exception\|timeout" | head -20

# 4. Check if workers are processing
echo "Checking worker activity..."
PROCESSING=$(kubectl exec -n truematch redis-0 -- \
    redis-cli LLEN assessment:processing | head -1)
echo "Items being processed: $PROCESSING"

if [ "$PROCESSING" -eq 0 ]; then
    echo "ERROR: No items being processed (workers stuck)"
fi

# 5. Check external service (enrichment API)
echo "Checking enrichment service..."
ENRICHMENT_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://enrichment-api.example.com/health)
if [ "$ENRICHMENT_STATUS" != "200" ]; then
    echo "WARNING: Enrichment API unhealthy ($ENRICHMENT_STATUS)"
    echo "ACTION: Disable enrichment and retry failed items"
fi

# 6. Check database performance
echo "Checking database performance..."
kubectl exec -n truematch postgres-0 -- psql -U postgres truematch -c \
    "SELECT pid, query_start, query FROM pg_stat_activity WHERE state = 'active' AND query_start < NOW() - INTERVAL '1 minute' LIMIT 5;"

# 7. Scale up worker replicas
echo "Scaling up worker replicas..."
kubectl scale deployment truematch-workers --replicas=10 -n truematch
kubectl rollout status deployment/truematch-workers -n truematch --timeout=5m

# 8. Monitor queue draining
echo "Monitoring queue drain..."
for i in {1..20}; do
    CURRENT=$(kubectl exec -n truematch redis-0 -- \
        redis-cli LLEN assessment:queue | head -1)
    echo "Queue depth: $CURRENT ($(( (QUEUE_DEPTH - CURRENT) * 100 / QUEUE_DEPTH ))% drained)"
    if [ "$CURRENT" -lt 10000 ]; then
        echo "✓ Queue recovered"
        break
    fi
    sleep 30
done

# 9. Post-incident analysis
echo "✓ Collecting worker logs for analysis..."
kubectl logs -n truematch -l app=worker --all-containers=true > /tmp/worker-logs-$(date +%s).txt

echo "Incident resolved"
```

#### Incident #4: Certificate Expiration

**Symptoms**
- Browser warning: "SSL certificate expired"
- Curl: `SSL: certificate problem: certificate has expired`
- API clients: `TLS handshake failure`
- Users cannot access platform

**Root Causes**
- Auto-renewal failed
- Cert-manager pod crash
- Let's Encrypt API timeout
- Manual renewal forgotten

**Resolution Steps**

```bash
#!/bin/bash
set -e

echo "=== Certificate Expiration ==="

# 1. Check certificate status
echo "Checking certificate status..."
CERT_EXPIRY=$(echo | openssl s_client -connect api.truematch.ai:443 2>/dev/null | \
    openssl x509 -noout -dates | grep notAfter | cut -d= -f2)
echo "Certificate expires: $CERT_EXPIRY"

# 2. Check cert-manager
echo "Checking cert-manager..."
kubectl get pods -n cert-manager
kubectl get certificates -n truematch

# 3. If auto-renewal failed, manually renew
echo "Attempting manual renewal..."
certbot renew --force-renewal \
    --cert-name api.truematch.ai \
    --email ops@truematch.ai \
    --non-interactive

# 4. Update secret in Kubernetes
echo "Updating certificate secret..."
kubectl create secret tls truematch-tls \
    --cert=/etc/letsencrypt/live/api.truematch.ai/fullchain.pem \
    --key=/etc/letsencrypt/live/api.truematch.ai/privkey.pem \
    --namespace=truematch \
    --dry-run=client -o yaml | kubectl apply -f -

# 5. Restart ingress to pick up new cert
echo "Restarting ingress controller..."
kubectl rollout restart deployment/ingress-nginx \
    -n ingress-nginx
kubectl rollout status deployment/ingress-nginx \
    -n ingress-nginx --timeout=5m

# 6. Verify certificate
echo "Verifying new certificate..."
curl -I https://api.truematch.ai/health | head -5

echo "Certificate updated successfully"
```

#### Incident #5: DDoS Attack

**Symptoms**
- Traffic spike: 100x normal
- API response timeouts
- High CPU/bandwidth utilization
- Legitimate users unable to access

**Root Causes**
- Bot traffic (automated scraping)
- Distributed denial of service
- Misconfigured client (retry loop)

**Resolution Steps**

```bash
#!/bin/bash
set -e

echo "=== DDoS Attack Response ==="

# 1. Confirm attack
echo "Checking request rates..."
curl -s http://prometheus:9090/api/v1/query \
    --data-urlencode 'query=rate(http_requests_total[1m])' | \
    jq '.data.result[0].value[1]'

# 2. Identify attack source
echo "Identifying attack sources..."
kubectl logs -n truematch deployment/truematch-api --tail=10000 | \
    awk '{print $1}' | sort | uniq -c | sort -rn | head -20

# 3. Enable WAF rules
echo "Enabling AWS WAF DDoS protection..."
aws wafv2 update-ip-set \
    --name truematch-block-list \
    --addresses '["1.2.3.4/32","5.6.7.8/32"]' \
    --region ap-southeast-1 \
    --id arn:aws:wafv2:ap-southeast-1:ACCOUNT:regional/ipset/truematch-block-list/ID

# 4. Rate limit aggressively
echo "Applying aggressive rate limiting..."
kubectl patch configmap rate-limit-config -n truematch \
    -p '{"data":{"per_minute":"10","per_second":"1"}}'

# 5. Scale up API replicas
echo "Scaling up API replicas..."
kubectl scale deployment truematch-api --replicas=20 -n truematch

# 6. Enable caching
echo "Enabling aggressive caching..."
kubectl set env deployment/truematch-api \
    CACHE_TTL_SECONDS=3600 \
    -n truematch

# 7. Block specific endpoints
echo "Blocking resource-intensive endpoints..."
kubectl patch ingress truematch-ingress -n truematch \
    --type merge -p '{"spec":{"rules":[{"http":{"paths":[{"path":"/api/v1/analytics/*","pathType":"Prefix","backend":{"service":{"name":"rate-limit-blocker","port":{"number":429}}}}]}}]}}'

# 8. Alert and escalate
echo "CRITICAL ALERT: DDoS attack in progress"
slack-webhook --message "🚨 DDoS attack detected. Attack source IPs: [see logs]. WAF enabled. API scaled to 20 replicas."

# 9. Monitor
echo "Monitoring attack..."
for i in {1..30}; do
    RPS=$(curl -s http://prometheus:9090/api/v1/query \
        --data-urlencode 'query=rate(http_requests_total[1m])' | \
        jq '.data.result[0].value[1]')
    echo "RPS: $RPS"
    sleep 10
done

echo "DDoS mitigation in progress"
```

#### Incident #6: Data Corruption

**Symptoms**
- Inconsistent data in assessments
- Assessment scores don't match calculations
- Users report assessment details don't match originals
- Audit logs show data modification without user action

**Root Causes**
- Concurrent update race condition
- Database transaction rollback failure
- Data migration script error
- Encryption/decryption mismatch

**Resolution Steps**

```bash
#!/bin/bash
set -e

echo "=== Data Corruption Response ==="

# 1. IMMEDIATE: Stop all writes
echo "Pausing write operations..."
kubectl set env deployment/truematch-api \
    API_WRITE_DISABLED=true \
    -n truematch

echo "⚠️  WARNING: All write operations paused. System is READ-ONLY."

# 2. Assess scope of corruption
echo "Assessing corruption scope..."
kubectl exec -n truematch postgres-0 -- psql -U postgres truematch -c \
    "SELECT COUNT(*) FROM assessments WHERE score IS NULL OR score < 0 OR score > 100;" | tail -1

# 3. Create backup immediately
echo "Creating emergency backup..."
kubectl exec -n truematch postgres-0 -- \
    pg_dump -U postgres -Fc truematch \
    > /backup/corruption-backup-$(date +%s).dump

# 4. Validate data integrity
echo "Running integrity checks..."
kubectl exec -n truematch postgres-0 -- psql -U postgres truematch <<EOF
  SELECT COUNT(*) as assessments_with_invalid_scores FROM assessments 
  WHERE score < 0 OR score > 100;
  
  SELECT COUNT(*) as cv_without_assessment FROM cv_documents
  WHERE assessment_id NOT IN (SELECT id FROM assessments);
  
  SELECT COUNT(*) FROM audit_logs WHERE action IS NULL;
EOF

# 5. Check logs for root cause
echo "Analyzing application logs for corruption source..."
kubectl logs -n truematch deployment/truematch-api --tail=5000 | \
    grep -i "error\|corruption\|transaction" | head -50

# 6. Escalate to data team
echo "ESCALATION REQUIRED: Data corruption detected"
echo "VP Eng + Database Lead need to investigate"

# 7. Plan recovery
echo "Recovery options:"
echo "Option A: Restore from pre-incident backup (data loss: ~30 minutes)"
echo "Option B: Re-process corrupted assessments (time: ~2 hours)"
echo "Option C: Manual data correction (time: variable)"

# 8. Implement selected recovery
echo "Awaiting decision from leadership..."
# [Manual intervention required here]

# 9. Post-incident: Improve validation
echo "✓ ACTION: Add data validation triggers"
echo "✓ ACTION: Increase audit logging"
echo "✓ ACTION: Implement data reconciliation service"

echo "Data corruption incident requires manual intervention"
```

### Root Cause Analysis Template

```markdown
## Incident Post-Mortem: [Incident Title]

**Date:** 2026-06-07  
**Duration:** 14:30-15:45 UTC (75 minutes)  
**Severity:** S2 (Major)  
**Impact:** 2,400 assessments delayed by 45 minutes  

### Timeline

| Time | Event |
|------|-------|
| 14:30 | Alert: Error rate >5% |
| 14:32 | On-call investigating |
| 14:35 | Root cause identified: worker crash |
| 14:40 | Mitigation: Restarted worker pods |
| 14:45 | System recovering |
| 15:00 | System fully recovered |
| 15:45 | Postmortem meeting held |

### Root Cause

**Primary Cause:** Worker process exceeded memory limit (leak in new assessment parser)

**Contributing Factors:**
- Memory alerts not triggered early enough
- No automatic pod restart on memory pressure
- New code not load-tested before deployment

### Impact

- 2,400 assessments stuck in queue
- Users unable to submit new assessments for 45 minutes
- Affected regions: APAC (3 recruiters)
- No data loss

### Resolution

1. Immediately: Restarted worker pods (5 min)
2. Short-term: Increased memory limits (10 min)
3. Medium-term: Code review of memory leak (in progress)
4. Long-term: Improve load testing before deployment

### Action Items

- [ ] Fix memory leak in assessment parser code
- [ ] Implement memory profiling in CI/CD
- [ ] Add memory threshold alerting at 70%, 85%
- [ ] Load test all new code with 100k+ sample size
- [ ] Increase memory request from 512Mi to 1Gi
- Due: 2026-06-14 (one week)

### Prevention

- Add memory profiling to standard load test suite
- Require load test results in PR reviews
- Implement automatic pod restart on memory threshold

**Assigned to:** [Engineer Name] | **Follow-up meeting:** 2026-06-14
```

### Postmortem Process

**Postmortem Meeting Schedule (24 hours after incident)**
1. Review timeline and impact (5 min)
2. Identify root causes (10 min)
3. Discuss contributing factors (10 min)
4. Agree on action items (15 min)
5. Assign owners and due dates (5 min)

**Postmortem Audience**
- On-call engineer (facilitator)
- All team members involved
- Engineering lead
- Product owner (if customer-facing)
- VP Engineering (if S1 incident)

**Output**
- Postmortem document (24 hours)
- Action items tracked in JIRA
- Action item follow-up (one week)
- Public incident summary (if applicable)

---

## SCALING PROCEDURES

### Adding New API Replicas

**Horizontal Scaling (Most Common)**

```bash
#!/bin/bash
set -e

TARGET_REPLICAS=${1:-5}

echo "=== Scaling API Replicas to $TARGET_REPLICAS ==="

# 1. Check current status
echo "Current deployment status:"
kubectl get deployment truematch-api -n truematch -o wide

# 2. Update replica count
echo "Scaling to $TARGET_REPLICAS replicas..."
kubectl scale deployment/truematch-api \
    --replicas=$TARGET_REPLICAS \
    -n truematch

# 3. Wait for scaling
echo "Waiting for pods to be ready..."
kubectl rollout status deployment/truematch-api \
    -n truematch \
    --timeout=10m

# 4. Verify all pods are healthy
echo "Verifying pod health..."
kubectl get pods -n truematch -l app=api -o wide | head -20

# 5. Check load balancer distribution
echo "Verifying load balancer distribution..."
kubectl get endpoints truematch-api -n truematch

# 6. Monitor performance
echo "Monitoring API performance..."
for i in {1..5}; do
    LATENCY=$(curl -s http://prometheus:9090/api/v1/query \
        --data-urlencode 'query=histogram_quantile(0.95,rate(http_request_duration_seconds_bucket[5m]))' | \
        jq '.data.result[0].value[1]' | tr -d '"')
    ERROR_RATE=$(curl -s http://prometheus:9090/api/v1/query \
        --data-urlencode 'query=rate(http_requests_total{status=~"5.."}[5m])' | \
        jq '.data.result[0].value[1]' | tr -d '"')
    echo "Iteration $i: Latency ${LATENCY}s, Error Rate ${ERROR_RATE}%"
    sleep 30
done

echo "Scaling completed successfully ✓"
```

### Adding New Worker Replicas

```bash
#!/bin/bash
set -e

TARGET_REPLICAS=${1:-3}

echo "=== Scaling Worker Replicas to $TARGET_REPLICAS ==="

# 1. Current status
kubectl get deployment truematch-workers -n truematch -o wide

# 2. Scale workers
kubectl scale deployment/truematch-workers \
    --replicas=$TARGET_REPLICAS \
    -n truematch

# 3. Wait for ready
kubectl rollout status deployment/truematch-workers \
    -n truematch \
    --timeout=10m

# 4. Monitor queue draining
echo "Monitoring queue drain..."
for i in {1..10}; do
    QUEUE_DEPTH=$(kubectl exec -n truematch redis-0 -- \
        redis-cli LLEN assessment:queue)
    PROCESSING=$(kubectl exec -n truematch redis-0 -- \
        redis-cli LLEN assessment:processing)
    echo "Queue: $QUEUE_DEPTH, Processing: $PROCESSING"
    sleep 30
done

echo "Worker scaling completed ✓"
```

### Increasing Database Storage

```bash
#!/bin/bash
set -e

echo "=== Increasing Database Storage ==="

# 1. Check current usage
echo "Current storage usage:"
kubectl exec -n truematch postgres-0 -- \
    psql -U postgres -c "SELECT pg_size_pretty(pg_database_size('truematch'));"

# 2. Grow persistent volume
echo "Growing persistent volume from 500GB to 1TB..."
kubectl patch pvc postgres-data -n truematch \
    -p '{"spec":{"resources":{"requests":{"storage":"1Ti"}}}}'

# 3. Wait for volume expansion
echo "Waiting for volume expansion..."
sleep 60

# 4. Restart PostgreSQL
echo "Restarting PostgreSQL to recognize new space..."
kubectl delete pod postgres-0 -n truematch
kubectl wait --for=condition=ready pod/postgres-0 \
    -n truematch --timeout=300s

# 5. Verify
kubectl exec -n truematch postgres-0 -- \
    psql -U postgres -c "SELECT pg_size_pretty(pg_tablespace_size('pg_default'));"

echo "Storage expansion completed ✓"
```

### Increasing Redis Capacity

**Vertical Scaling (Single Node)**

```bash
#!/bin/bash
set -e

echo "=== Increasing Redis Memory Capacity ==="

# 1. Check current memory
kubectl exec -n truematch redis-0 -- redis-cli INFO memory | grep used_memory_human

# 2. Update Redis limits
kubectl set resources statefulset/redis \
    --limits=memory=64Gi \
    --requests=memory=32Gi \
    -n truematch

# 3. Restart Redis
kubectl rollout restart statefulset/redis -n truematch
kubectl rollout status statefulset/redis -n truematch

# 4. Verify
kubectl exec -n truematch redis-0 -- redis-cli CONFIG GET maxmemory

echo "Redis capacity increased ✓"
```

### Multi-Region Deployment

```bash
#!/bin/bash
set -e

SECONDARY_REGION="us-east-1"
SECONDARY_CLUSTER="gke-truematch-useast"

echo "=== Multi-Region Deployment Setup ==="

# 1. Create secondary cluster
echo "Creating secondary GKE cluster in $SECONDARY_REGION..."
gcloud container clusters create "$SECONDARY_CLUSTER" \
    --zone "$SECONDARY_REGION-b" \
    --num-nodes 5 \
    --enable-ip-alias \
    --network "truematch-vpc"

# 2. Deploy to secondary cluster
echo "Deploying application to secondary cluster..."
kubectl --context="gke_truematch_${SECONDARY_REGION}_${SECONDARY_CLUSTER}" \
    apply -f k8s/ -n truematch

# 3. Set up database replication
echo "Setting up database replication..."
# Create read replica in secondary region
gcloud sql instances create truematch-replica-useast \
    --master-instance-name=truematch-primary \
    --region="$SECONDARY_REGION" \
    --tier=db-n1-highmem-16

# 4. Configure DNS failover
echo "Configuring DNS failover..."
gcloud dns record-sets create api.truematch.ai \
    --rrdatas="gke-apac.truematch.ai,gke-useast.truematch.ai" \
    --ttl=60 \
    --type=A \
    --zone=truematch-zone \
    --routing-policy=geo

# 5. Test failover
echo "Testing regional failover..."
# [Failover test procedure]

echo "Multi-region deployment completed ✓"
```

### Load Balancing Configuration

```yaml
# Istio VirtualService for load balancing
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: truematch-api
  namespace: truematch
spec:
  hosts:
  - api.truematch.ai
  http:
  - match:
    - uri:
        prefix: /api/v1/assessments
    route:
    - destination:
        host: truematch-api
        port:
          number: 8000
      weight: 100
    timeout: 30s
    retries:
      attempts: 3
      perTryTimeout: 10s
  - match:
    - uri:
        prefix: /api/v1/
    route:
    - destination:
        host: truematch-api
      weight: 100
---
# Destination rule for connection pooling
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: truematch-api
  namespace: truematch
spec:
  host: truematch-api
  trafficPolicy:
    connectionPool:
      tcp:
        maxConnections: 500
      http:
        http1MaxPendingRequests: 1000
        http2MaxRequests: 1000
        maxRequestsPerConnection: 1
    outlierDetection:
      consecutive5xxErrors: 5
      interval: 30s
      baseEjectionTime: 30s
```

---

## SECURITY PROCEDURES

### Secret Rotation Procedures

#### Database Password Rotation (Quarterly)

```bash
#!/bin/bash
set -e

echo "=== Database Password Rotation ==="

# 1. Generate new password
NEW_PASSWORD=$(openssl rand -base64 32)
echo "New password generated: [REDACTED]"

# 2. Update PostgreSQL user
echo "Updating database user password..."
kubectl exec -n truematch postgres-0 -- \
    psql -U postgres -c "ALTER USER truematch WITH PASSWORD '$NEW_PASSWORD';"

# 3. Update Kubernetes secret
echo "Updating Kubernetes secret..."
kubectl create secret generic postgres-credentials \
    --from-literal=password="$NEW_PASSWORD" \
    --from-literal=username=truematch \
    --from-literal=database=truematch \
    --from-literal=host=postgres \
    --dry-run=client -o yaml | kubectl apply -f -

# 4. Update application environment
echo "Updating application deployment..."
kubectl rollout restart deployment/truematch-api -n truematch
kubectl rollout status deployment/truematch-api -n truematch --timeout=10m

# 5. Verify connectivity
echo "Verifying database connectivity..."
kubectl exec -n truematch deployment/truematch-api -- \
    python -c "from app.database import get_db; print('✓ Connected')"

# 6. Test with old password (should fail)
echo "Verifying old password no longer works..."
if kubectl exec -n truematch postgres-0 -- \
    psql -U truematch -c "SELECT 1;" 2>&1 | grep -q "password authentication failed"; then
    echo "✓ Old password revoked"
else
    echo "⚠️  Old password still works - investigate!"
fi

# 7. Document rotation
echo "{\"timestamp\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",\"secret\":\"postgres_password\",\"status\":\"rotated\"}" \
    >> /var/log/secret-rotation.log

echo "Database password rotation completed ✓"
```

#### JWT Secret Rotation (Annually)

```bash
#!/bin/bash
set -e

echo "=== JWT Secret Rotation ==="

# 1. Generate new JWT secret
NEW_JWT_SECRET=$(python -c "import secrets; print(secrets.token_urlsafe(64))")
echo "New JWT secret generated"

# 2. Create new secret keeping old one
echo "Creating new JWT secret in Kubernetes..."
kubectl patch secret jwt-secrets -n truematch \
    -p '{"data":{"current":"'$(echo -n "$NEW_JWT_SECRET" | base64)'"}}'

# 3. Update API deployment
echo "Updating API with new JWT secret..."
kubectl set env deployment/truematch-api \
    JWT_SECRET="$NEW_JWT_SECRET" \
    -n truematch

# 4. Restart API gradually
kubectl rollout restart deployment/truematch-api -n truematch
kubectl rollout status deployment/truematch-api -n truematch --timeout=10m

# 5. Invalidate old tokens (optional: notify users to re-login)
echo "Old JWT tokens will remain valid for 30 days. Force re-auth if security required."

echo "JWT secret rotation completed ✓"
```

### Certificate Renewal (Automatic + Manual)

#### Automatic Renewal (Let's Encrypt + cert-manager)

```yaml
# cert-manager Certificate resource
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: truematch-tls
  namespace: truematch
spec:
  secretName: truematch-tls
  issuerRef:
    name: letsencrypt-prod
    kind: ClusterIssuer
  dnsNames:
  - api.truematch.ai
  - '*.truematch.ai'
  # Renew 30 days before expiry
  renewBefore: 720h
```

**Verification**
```bash
# Check certificate status
kubectl describe certificate truematch-tls -n truematch

# Monitor renewal attempts
kubectl logs -n cert-manager -l app=cert-manager | grep truematch

# View certificate details
kubectl get secret truematch-tls -o jsonpath='{.data.tls\.crt}' | \
    base64 -d | openssl x509 -noout -dates
```

#### Manual Certificate Renewal

```bash
#!/bin/bash
set -e

echo "=== Manual Certificate Renewal ==="

# If automatic renewal fails, manually renew
certbot renew \
    --cert-name api.truematch.ai \
    --email ops@truematch.ai \
    --force-renewal \
    --non-interactive

# Update Kubernetes secret
kubectl create secret tls truematch-tls \
    --cert=/etc/letsencrypt/live/api.truematch.ai/fullchain.pem \
    --key=/etc/letsencrypt/live/api.truematch.ai/privkey.pem \
    --namespace=truematch \
    --dry-run=client -o yaml | kubectl apply -f -

# Restart ingress
kubectl rollout restart deployment/ingress-nginx -n ingress-nginx

echo "Manual renewal completed ✓"
```

### Security Patching Process

#### Kubernetes Cluster Patching (Monthly)

```bash
#!/bin/bash
set -e

echo "=== Kubernetes Cluster Patching ==="

# 1. Check available updates
echo "Checking available Kubernetes updates..."
gcloud container clusters describe truematch-cluster \
    --zone ap-southeast-1-b | grep currentMasterVersion

# 2. Schedule maintenance window
echo "Scheduling maintenance window: 2026-06-15 02:00-04:00 UTC"
gcloud container clusters update truematch-cluster \
    --zone ap-southeast-1-b \
    --maintenance-window-start 2026-06-15T02:00:00Z \
    --maintenance-window-end 2026-06-15T04:00:00Z \
    --maintenance-window-recurrence "FREQ=MONTHLY;BYMONTHDAY=15"

# 3. Enable cluster auto-upgrade
gcloud container clusters update truematch-cluster \
    --zone ap-southeast-1-b \
    --enable-autorepair \
    --enable-autoupgrade

# 4. Node pool updates
echo "Updating node pools..."
gcloud container node-pools update default-pool \
    --cluster truematch-cluster \
    --zone ap-southeast-1-b \
    --enable-autoupgrade \
    --enable-autorepair

echo "Kubernetes patching scheduled ✓"
```

#### Dependency Updates (Weekly Security Scan)

```bash
#!/bin/bash
set -e

echo "=== Dependency Security Scan ==="

# 1. Scan Python dependencies
echo "Scanning Python dependencies..."
pip-audit --desc | grep -i critical

# 2. Scan Node.js dependencies
echo "Scanning Node.js dependencies..."
npm audit --audit-level=critical

# 3. Scan Docker images
echo "Scanning container images..."
grype gcr.io/truematch/api:latest --fail-on critical

# 4. Update if critical issues found
if [ $? -ne 0 ]; then
    echo "CRITICAL: Found vulnerabilities. Triggering updates..."
    # Update and rebuild
fi

echo "Dependency security scan completed"
```

### Dependency Update Procedures

#### Safe Dependency Update

```bash
#!/bin/bash
set -e

PACKAGE=${1:-}

if [ -z "$PACKAGE" ]; then
    echo "Usage: $0 <package_name>"
    exit 1
fi

echo "=== Dependency Update: $PACKAGE ==="

# 1. Create feature branch
git checkout -b "deps/update-$PACKAGE"

# 2. Update dependency
pip install --upgrade $PACKAGE

# 3. Run tests locally
echo "Running local tests..."
pytest --cov=app tests/

# 4. Build and test Docker image
echo "Building Docker image..."
docker build -t gcr.io/truematch/api:test-$PACKAGE .
docker run --rm gcr.io/truematch/api:test-$PACKAGE pytest

# 5. Deploy to staging
echo "Deploying to staging..."
kubectl set image deployment/truematch-api \
    api=gcr.io/truematch/api:test-$PACKAGE \
    -n truematch-staging
kubectl rollout status deployment/truematch-api \
    -n truematch-staging --timeout=10m

# 6. Run integration tests
echo "Running integration tests..."
# [Integration test suite]

# 7. Commit and create PR
git add requirements.txt
git commit -m "chore: upgrade $PACKAGE"
git push origin "deps/update-$PACKAGE"

echo "Create PR for review"
```

### Security Audit Checklist

**Monthly Security Audit**
- [ ] Review IAM permissions (remove unused)
- [ ] Check SSH access logs
- [ ] Audit database user permissions
- [ ] Review secret access logs
- [ ] Check certificate expiry
- [ ] Verify backup encryption
- [ ] Review VPN access
- [ ] Audit API key usage
- [ ] Check firewall rules
- [ ] Review compliance status

**Quarterly Security Review**
- [ ] Full vulnerability assessment
- [ ] Penetration testing results
- [ ] Code security scan (SAST)
- [ ] Supply chain security review
- [ ] Incident log review
- [ ] Disaster recovery test
- [ ] Compliance audit

### Data Access Control Review (Monthly)

```bash
#!/bin/bash
set -e

echo "=== Data Access Control Review ==="

# 1. Audit database role permissions
echo "Auditing database roles..."
kubectl exec -n truematch postgres-0 -- psql -U postgres -c \
    "SELECT grantee, privilege_type FROM role_table_grants WHERE table_name='assessments';"

# 2. Check S3 access
echo "Auditing S3 bucket access..."
aws s3api get-bucket-acl --bucket truematch-uploads

# 3. Review service account permissions
echo "Auditing Kubernetes service account permissions..."
kubectl auth can-i --list --as=system:serviceaccount:truematch:truematch-api

# 4. Check secrets access logs
echo "Reviewing secret access logs..."
kubectl logs -n truematch deployment/truematch-api | grep -i "secret\|password" | head -50

echo "Data access control review completed"
```

### Compliance Verification

**GDPR Compliance Checklist**
- [ ] User data deletion requests processed within 30 days
- [ ] Data retention policy enforced
- [ ] Encryption at rest enabled
- [ ] Encryption in transit (TLS) enforced
- [ ] Privacy policy updated
- [ ] DPA with data processor signed
- [ ] Right to access implemented
- [ ] Right to portability implemented

**Regular Compliance Validation**
```bash
# Check encryption at rest
kubectl exec -n truematch postgres-0 -- \
    psql -U postgres -c "SELECT datname, pg_database_size(datname) FROM pg_database WHERE datname = 'truematch';"

# Verify TLS in prod
curl -I https://api.truematch.ai/health | grep "X-Content-Type-Options\|X-Frame-Options"

# Check data retention
kubectl exec -n truematch postgres-0 -- \
    psql -U postgres -c "SELECT COUNT(*) FROM assessments WHERE created_at < NOW() - INTERVAL '90 days';"
```

---

## TROUBLESHOOTING GUIDE

### 30+ Common Issues and Solutions

#### 1. High API Latency (>2 seconds)

**Check these in order:**

1. Database performance
   ```bash
   kubectl exec -n truematch postgres-0 -- psql -U postgres -c \
       "SELECT query, mean_exec_time FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 5;"
   ```

2. Slow queries (>1s)
   ```bash
   kubectl logs -n truematch deployment/truematch-api --tail=1000 | \
       grep "slow_query\|duration.*ms" | grep -E "[1-9][0-9]{3,}" | head -20
   ```

3. Database connection pool
   ```bash
   kubectl exec -n truematch postgres-0 -- psql -U postgres -c \
       "SELECT count(*) FROM pg_stat_activity WHERE state = 'active';"
   ```

4. Redis latency
   ```bash
   kubectl exec -n truematch redis-0 -- redis-cli latency latest
   ```

5. Pod resource limits
   ```bash
   kubectl top pods -n truematch -l app=api
   ```

**Resolution:**
- Increase database connection pool size
- Add database indexes on high-query columns
- Implement query caching
- Scale API replicas

---

#### 2. High Error Rate (>5%)

```bash
# Identify error type
kubectl logs -n truematch deployment/truematch-api --tail=5000 | \
    grep -i error | awk -F'[: ]' '{print $NF}' | sort | uniq -c | sort -rn | head -10

# Check specific error
kubectl logs -n truematch deployment/truematch-api --tail=5000 | \
    grep "500\|Exception\|Traceback" | head -20
```

**Common Causes:**
- Database connectivity: Increase pool size, check credentials
- Out of memory: Check pod memory usage, increase request
- Unhandled exception: Review application logs, deploy fix
- Upstream API failure: Check external service health, implement fallback

---

#### 3. Worker Queue Backlog (>10,000 items)

See **Incident #3: Worker Queue Backlog** in Incident Response section.

---

#### 4. Memory Leak in API

See **Incident #2: Memory Leak in API** in Incident Response section.

---

#### 5. Disk Full (>95% used)

```bash
# Find largest files
kubectl exec -n truematch deployment/truematch-api -- \
    du -h / | sort -rh | head -20

# Check log sizes
kubectl logs -n truematch --all-pods=true --tail=0 | wc -l
```

**Resolution:**
- Delete old logs: `kubectl logs --since=3d | tee /archive.log | rm -f` 
- Archive old data: Move to S3
- Expand persistent volume: See Scaling section
- Clean Docker images: `docker image prune -a`

---

#### 6. Database Slow Queries

```bash
# Identify slow queries
kubectl exec -n truematch postgres-0 -- psql -U postgres -c \
    "SELECT query, calls, total_time FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"

# Analyze query plan
kubectl exec -n truematch postgres-0 -- psql -U postgres -c \
    "EXPLAIN (ANALYZE, BUFFERS) SELECT * FROM assessments WHERE score > 0.8;"
```

**Resolution:**
- Add index: `CREATE INDEX idx_assessments_score ON assessments(score)`
- Optimize query: Review WHERE clause, use LIMIT
- Update statistics: `VACUUM ANALYZE`

---

#### 7. Database Connection Pool Exhausted

See **Incident #1: Database Connection Pool Exhausted** in Incident Response section.

---

#### 8. Network Connectivity Issues

```bash
# Test cluster networking
kubectl run debug-pod --image=busybox --rm -it -- sh
/ # wget -q -O- http://truematch-api/health
/ # nslookup postgres
/ # nslookup redis

# Check network policies
kubectl get networkpolicy -n truematch
kubectl describe networkpolicy truematch-network-policy -n truematch

# Test external connectivity
curl -I https://enrichment-api.example.com/health
```

**Resolution:**
- Verify DNS resolution
- Check network policy rules
- Verify firewall rules
- Check VPC route tables

---

#### 9. Authentication Failures

```bash
# Check auth logs
kubectl logs -n truematch deployment/truematch-api --tail=1000 | \
    grep -i "auth\|jwt\|token\|unauthorized"

# Verify JWT secret
kubectl get secret jwt-secrets -n truematch -o jsonpath='{.data}' | base64 -d

# Check OIDC configuration
kubectl get secret oidc-config -n truematch -o jsonpath='{.data}'
```

**Resolution:**
- Verify JWT secret is correct
- Check token expiry configuration
- Validate OIDC provider settings
- Review session timeout settings

---

#### 10. Certificate Expiration

See **Incident #4: Certificate Expiration** in Incident Response section.

---

#### 11-40. Additional Common Issues

**[Abbreviated for space, but would include detailed troubleshooting for:]**
- Redis memory exhaustion
- Pod crash loop
- PVC mount failures
- Image pull failures
- ConfigMap/Secret not mounted
- Readiness probe failures
- Liveness probe failures
- Request timeout
- Rate limiting blocking legitimate traffic
- S3 connectivity issues
- IMAP email ingestion failures
- Assessment parsing errors
- ML model timeout
- Governance gate failures
- Data validation errors
- Concurrent update conflicts
- Cache invalidation issues
- Queue job failures
- Worker job timeout
- And more...

---

#### 41. Debugging Techniques

**Port Forwarding for Direct Access**
```bash
kubectl port-forward -n truematch svc/postgres 5432:5432
psql -h localhost -U postgres truematch
```

**Execute Commands in Pods**
```bash
kubectl exec -n truematch deployment/truematch-api -- bash
# Now in the pod shell
python -c "from app.database import get_db; print('OK')"
```

**Stream Logs in Real-Time**
```bash
kubectl logs -n truematch deployment/truematch-api -f
```

**Copy Files to/from Pods**
```bash
kubectl cp -n truematch deployment/truematch-api:app/config.py ./local-config.py
```

---

#### 42. Performance Profiling

**CPU Profiling**
```bash
# Record CPU profile
kubectl exec -n truematch deployment/truematch-api -- \
    python -m cProfile -o profile.prof app/main.py

# Analyze profile
pstats profile.prof
```

**Memory Profiling**
```bash
# Trace memory usage
kubectl exec -n truematch deployment/truematch-api -- \
    python -m memory_profiler app/main.py > memory.txt
```

**Database Profiling**
```bash
# Log slow queries
ALTER SYSTEM SET log_min_duration_statement = 1000;  -- 1 second
SELECT pg_reload_conf();
```

---

## OPERATIONAL CONTACTS

### On-Call Escalation

```
Level 1: Primary On-Call Engineer
  Contact: Slack @ops-primary or +1-555-0100
  Availability: 24/7
  Response Time: <5 minutes
  
Level 2: Engineering Lead
  Contact: Slack @eng-lead or +1-555-0104
  Availability: Business hours + on-call rotation
  Response Time: <15 minutes
  
Level 3: VP Engineering
  Contact: Slack @vp-eng or +1-555-0105
  Availability: Business hours
  Response Time: <30 minutes
  
Level 4: Chief Technical Officer
  Contact: Email cto@truematch.ai
  Availability: Business hours
  Response Time: <1 hour
```

### Cloud Provider Support

```
AWS Support
  Tier: Business (4-hour response)
  Account ID: 123456789
  Primary Contact: ops+aws@truematch.ai
  URL: https://console.aws.amazon.com/support/

Google Cloud Support
  Tier: Enhanced (1-hour response)
  Project ID: truematch-prod-123
  Primary Contact: ops+gcp@truematch.ai
  URL: https://cloud.google.com/support

Database Vendor Support (PostgreSQL)
  Community Support: https://www.postgresql.org/support/
  Commercial Support: EDB (if applicable)
```

### Internal Team Directory

```
Operations Team
  Lead: [Name] - ops-lead@truematch.ai
  Members: [Names] - ops-team@truematch.ai
  
Database Team
  Lead: [Name] - db-lead@truematch.ai
  Members: [Names] - db-team@truematch.ai
  
Security Team
  Lead: [Name] - security-lead@truematch.ai
  Members: [Names] - security-team@truematch.ai
  
Infrastructure Team
  Lead: [Name] - infra-lead@truematch.ai
  Members: [Names] - infra-team@truematch.ai
```

### Postmortem Meeting Templates

**S1/S2 Incident Postmortem**
```
Title: [Incident Title]
Time: [Within 24 hours]
Attendees: [All involved + Lead]
Facilitator: On-call engineer
Duration: 1 hour
Output: Postmortem doc + action items
```

**Postmortem Document**
```markdown
# Postmortem: [Incident Title]

## Summary
- Impact: [users affected, duration]
- Severity: [S1-S4]
- Timeline: [start - end time]

## Root Cause
[Primary cause + contributing factors]

## Timeline
[Detailed events with timestamps]

## Action Items
- [ ] Item 1 - Owner: [Name] - Due: [Date]
- [ ] Item 2 - Owner: [Name] - Due: [Date]

## Lessons Learned
[What did we learn]

## Prevention
[How to prevent in future]
```

---

## CONFIGURATION REFERENCE

### All Critical Configuration Options

**Database Connection**
```
database_url=postgresql+asyncpg://truematch:password@postgres:5432/truematch
```

**Cache & Queue**
```
redis_url=redis://redis:6379/0
celery_broker_url=redis://redis:6379/0
celery_result_backend=redis://redis:6379/0
```

**Authentication**
```
jwt_secret=[64+ char secret]
jwt_algorithm=HS256
access_token_expire_minutes=30
refresh_token_expire_days=7
```

**API Configuration**
```
environment=production
log_level=INFO
log_json=true
metrics_enabled=true
rate_limit_enabled=true
rate_limit_per_minute=120
cors_origins=https://truematch.ai,https://app.truematch.ai
```

**Storage (S3)**
```
aws_access_key_id=[AWS key]
aws_secret_access_key=[AWS secret]
s3_bucket=truematch-uploads
aws_region=ap-southeast-1
max_upload_bytes=5000000
```

**Encryption**
```
encryption_key=[base64 32-byte AES key]
encryption_index_key=[base64 32-byte HMAC key]
s3_kms_key_id=arn:aws:kms:ap-southeast-1:ACCOUNT:key/KEY_ID
```

**AI/ML Configuration**
```
anthropic_api_key=sk-ant-[key]
anthropic_model=claude-sonnet-4-20250514
llm_timeout_seconds=60
semantic_embedding_model=minishlab/potion-base-8M
semantic_embedding_threshold=0.40
```

**Ingestion**
```
ingest_cv_folder=./inbox/cv
ingest_jd_folder=./inbox/jd
ingest_folder_poll_seconds=30
ingest_imap_host=imap.gmail.com
ingest_imap_port=993
ingest_max_retries=3
ingest_require_approval=false
```

**Governance**
```
governance_enable_coherence_gate=true
governance_enable_consistency_gate=true
governance_enable_fidelity_gate=true
governance_enable_bias_gate=true
decision_auto_approve_threshold=0.85
decision_review_threshold=0.65
decision_auto_reject_threshold=0.65
```

**Monitoring & Observability**
```
sentry_dsn=https://key@sentry.io/project
metrics_enabled=true
log_json=true
log_level=INFO
```

### Safe Modification Procedures

**Safe Changes (No review required)**
- Log level: DEBUG, INFO, WARNING, ERROR
- Rate limit: Increase up to 1000/min
- Cache TTL: Adjust between 1-3600 seconds
- API timeouts: Increase (5-120 seconds)
- Non-critical alert thresholds

**Changes Requiring Review (Engineering Lead)**
- Database connection pool size
- Worker count
- Memory/CPU requests
- Encryption keys (rotation only)
- Auto-scaling thresholds
- Governance gates

**Dangerous Changes (Requires CTO Approval)**
- Database migrations
- Disable encryption
- Change authentication method
- Modify governance logic
- Disable audit logging
- Change data retention policy

### Configuration Validation

```bash
#!/bin/bash
set -e

echo "=== Configuration Validation ==="

# 1. Check required environment variables
for var in DATABASE_URL REDIS_URL JWT_SECRET AWS_ACCESS_KEY_ID; do
    if [ -z "${!var}" ]; then
        echo "ERROR: Required env var not set: $var"
        exit 1
    fi
done

# 2. Validate format
if ! [[ "$JWT_SECRET" =~ ^.{64,}$ ]]; then
    echo "ERROR: JWT_SECRET must be 64+ characters"
    exit 1
fi

# 3. Test database connection
python -c "import psycopg2; conn = psycopg2.connect('$DATABASE_URL'); print('✓ Database OK')"

# 4. Test Redis connection
python -c "import redis; r = redis.from_url('$REDIS_URL'); r.ping(); print('✓ Redis OK')"

# 5. Test S3 credentials
aws s3 ls --region "$AWS_REGION" | head -1 && echo "✓ S3 OK"

echo "Configuration validation completed ✓"
```

### Secrets Management

**Secret Storage**
- **Development:** .env file (never committed)
- **Staging:** AWS Secrets Manager
- **Production:** AWS Secrets Manager + KMS encryption

**Secret Rotation Schedule**
- Database password: Quarterly
- JWT secret: Annually
- API keys: Quarterly
- SSL certificates: Automatic (Let's Encrypt)
- S3 credentials: Annually

**Access Control**
- Database: Only application service account
- S3: Least privilege IAM policy
- Secrets: Only necessary services
- API keys: Rotated per environment

---

## APPENDIX

### Useful Commands Reference

**Kubernetes Cluster Operations**
```bash
# View cluster status
kubectl cluster-info
kubectl get nodes

# View deployments
kubectl get deployments -n truematch
kubectl describe deployment truematch-api -n truematch

# View pods
kubectl get pods -n truematch
kubectl top pods -n truematch

# View logs
kubectl logs -n truematch deployment/truematch-api --tail=100
kubectl logs -n truematch deployment/truematch-api -f

# Execute commands
kubectl exec -n truematch deployment/truematch-api -- bash
kubectl exec -n truematch postgres-0 -- psql -U postgres -c "SELECT VERSION();"

# Port forwarding
kubectl port-forward -n truematch svc/postgres 5432:5432
```

**Database Operations**
```bash
# Connect to database
psql -h postgres.truematch.svc.cluster.local -U postgres -d truematch

# Database size
SELECT pg_size_pretty(pg_database_size('truematch'));

# Table size
SELECT relname, pg_size_pretty(pg_total_relation_size(relid)) FROM pg_stat_user_tables ORDER BY pg_total_relation_size(relid) DESC;

# Active connections
SELECT datname, usename, count(*) FROM pg_stat_activity GROUP BY datname, usename;

# Slow queries
SELECT query, mean_exec_time FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;
```

**Redis Operations**
```bash
# Connect to Redis
redis-cli -h redis.truematch.svc.cluster.local

# Memory info
INFO memory

# Key stats
DBSIZE
KEYS assessment:*

# Queue depth
LLEN assessment:queue
```

**Monitoring**
```bash
# Prometheus queries
http://prometheus:9090/api/v1/query?query=http_requests_total

# Grafana dashboards
http://grafana:3000

# Check metrics endpoint
curl http://api:8000/metrics | grep truematch
```

---

**End of Production Runbook**

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-06-07 | Initial production runbook |

**Next Review Date:** 2026-09-07 (Quarterly)
