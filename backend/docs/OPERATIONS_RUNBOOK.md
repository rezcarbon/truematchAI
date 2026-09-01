# TrueMatch AI Operations Runbook
## Phase 3: Production Operations & Incident Response

**Version:** 1.0  
**Last Updated:** 2026-07-19  
**Audience:** Operations, DevOps, Backend Team  
**Severity Levels:** Critical, High, Medium, Low

---

## Table of Contents

1. [Quick Reference](#quick-reference)
2. [Deployment Procedures](#deployment-procedures)
3. [Common Troubleshooting](#common-troubleshooting)
4. [Performance Tuning](#performance-tuning)
5. [Database Operations](#database-operations)
6. [Security Operations](#security-operations)
7. [Emergency Procedures](#emergency-procedures)

---

## Quick Reference

### Key Contacts
- **On-Call Engineer:** Check PagerDuty schedule
- **Database Admin:** [database-team@truematch.ai]
- **Security Team:** [security@truematch.ai]
- **Platform Team:** [platform@truematch.ai]

### Important URLs
- **Grafana Dashboard:** https://grafana.truematch.ai
- **Prometheus:** https://prometheus.truematch.ai
- **Sentry:** https://sentry.truematch.ai
- **Kubernetes Dashboard:** https://k8s.truematch.ai
- **Documentation:** https://wiki.truematch.ai/operations

### Critical Thresholds
| Metric | Warning | Critical |
|--------|---------|----------|
| API Error Rate | 1% | 5% |
| API Latency (p99) | 1s | 2s |
| Memory Usage | 80% | 90% |
| CPU Usage | 75% | 85% |
| Database Connections | 80% | 95% |
| Queue Depth | 500 | 1000 |

---

## Deployment Procedures

### Standard Deployment

#### Prerequisites
1. All tests passing in CI/CD pipeline
2. Code reviewed and approved
3. Database migrations tested
4. Release notes prepared

#### Deployment Steps

```bash
# 1. Prepare deployment
export IMAGE_TAG="v1.2.3"
export SLACK_WEBHOOK="https://hooks.slack.com/..."

# 2. Dry run (recommended for first-time deployments)
./scripts/deploy-to-production.sh \
  --dry-run \
  --tag $IMAGE_TAG \
  --slack-webhook $SLACK_WEBHOOK

# 3. Execute deployment
./scripts/deploy-to-production.sh \
  --tag $IMAGE_TAG \
  --slack-webhook $SLACK_WEBHOOK

# 4. Monitor deployment
kubectl rollout status deployment/api -n truematch-prod
kubectl rollout status deployment/worker -n truematch-prod
kubectl rollout status deployment/scheduler -n truematch-prod

# 5. Verify deployment
curl https://api.truematch.ai/healthz
```

#### Expected Timeline
- Pre-deployment checks: 2-3 minutes
- Image build & push: 5-10 minutes
- Database migrations: 1-5 minutes (depends on schema changes)
- Kubernetes rollout: 5-10 minutes
- Health checks: 2-3 minutes
- **Total: 15-30 minutes**

### Canary Deployment

For high-risk changes, use canary deployment to gradually roll out changes:

```bash
# 1. Deploy new version to 10% of traffic
./scripts/deploy-to-production.sh \
  --tag $IMAGE_TAG \
  --enable-canary \
  --canary-percentage 10

# 2. Monitor metrics for 15-30 minutes
# Watch error rate, latency, and resource usage

# 3. If metrics look good, increase to 50%
kubectl patch deployment api \
  -p '{"spec":{"replicas":6}}' \
  -n truematch-prod

# 4. Monitor for another 15-30 minutes

# 5. If still good, complete rollout
kubectl patch deployment api \
  -p '{"spec":{"replicas":3}}' \
  -n truematch-prod
```

### Blue-Green Deployment

For maximum safety, use blue-green deployment:

```bash
# 1. Deploy new version alongside current version
kubectl set image deployment/api-green \
  api=truematch-api:new-version \
  -n truematch-prod

# 2. Wait for new version to be ready
kubectl rollout status deployment/api-green \
  -n truematch-prod --timeout=10m

# 3. Run smoke tests against new version
curl http://api-green.truematch-prod.svc.cluster.local/healthz

# 4. Switch traffic to new version
kubectl patch service api \
  -p '{"spec":{"selector":{"deployment":"api-green"}}}' \
  -n truematch-prod

# 5. Monitor new version
kubectl logs deployment/api-green \
  -n truematch-prod -f

# 6. If rollback needed, switch back to old version
kubectl patch service api \
  -p '{"spec":{"selector":{"deployment":"api-blue"}}}' \
  -n truematch-prod
```

### Rollback Procedures

#### Automatic Rollback (triggered by health checks)
The deployment script automatically rolls back on:
- Health check failures
- Deployment timeout
- High error rates during rollout

#### Manual Rollback

```bash
# 1. Identify current revision
kubectl rollout history deployment/api -n truematch-prod

# 2. Rollback to previous revision
kubectl rollout undo deployment/api -n truematch-prod

# 3. Verify rollback
kubectl rollout status deployment/api \
  -n truematch-prod --timeout=10m

# 4. Check logs for issues
kubectl logs deployment/api \
  -n truematch-prod --tail=100 -f

# 5. Post-incident review
# - Identify root cause
# - Update runbook if needed
# - Communicate with team
```

---

## Common Troubleshooting

### Issue: API Pods Crashing

**Symptoms:**
- Pods in `CrashLoopBackOff` state
- High restart count
- Logs show errors

**Diagnosis:**
```bash
# Check pod status
kubectl get pods -n truematch-prod -l app=api

# Check pod logs
kubectl logs deployment/api -n truematch-prod --tail=100
kubectl logs deployment/api -n truematch-prod --previous  # Previous crash

# Describe pod for events
kubectl describe pod <pod-name> -n truematch-prod

# Check resource usage
kubectl top pods -n truematch-prod -l app=api
```

**Common Causes & Solutions:**

1. **Database Connection Failed**
   - Check DATABASE_URL environment variable
   - Verify database is running: `kubectl get pods -n truematch-prod -l app=postgres-prod`
   - Check database credentials in secrets: `kubectl get secret truematch-prod-secrets -n truematch-prod -o yaml`
   - Test connection: `kubectl run -it --rm psql-test --image=postgres:latest -- psql $DATABASE_URL`

2. **Out of Memory**
   - Check memory usage: `kubectl top pods -n truematch-prod`
   - Increase memory limits in deployment
   - Check for memory leaks in application logs
   - Restart pods if temporary spike: `kubectl rollout restart deployment/api -n truematch-prod`

3. **Missing Environment Variables**
   - Verify ConfigMap: `kubectl get cm truematch-prod-config -n truematch-prod -o yaml`
   - Verify Secrets: `kubectl get secret truematch-prod-secrets -n truematch-prod -o yaml`
   - Check pod's environment: `kubectl exec <pod-name> -n truematch-prod -- env`

4. **Port Already in Use**
   - Check port conflicts: `kubectl get svc -n truematch-prod`
   - Check node port usage: `netstat -tulpn | grep 8000`

### Issue: High Error Rate

**Symptoms:**
- Error rate > 5%
- Alert firing in monitoring
- Users reporting issues

**Diagnosis:**
```bash
# Check error rate by endpoint
curl https://prometheus.truematch.ai/graph \
  -d 'query=rate(http_requests_total{status=~"5.."}[5m])'

# Check error logs
kubectl logs deployment/api -n truematch-prod \
  --tail=200 | grep ERROR

# Check specific error type in Sentry
curl https://sentry.truematch.ai/api/0/projects/truematch/truematch-backend/issues/
```

**Common Causes & Solutions:**

1. **Database Overload**
   - Check database connection count: `SELECT count(*) FROM pg_stat_activity;`
   - Check slow queries: Enable slow query log
   - Scale up workers or add connection pooling

2. **Dependent Service Down**
   - Check Redis: `kubectl get pods -n truematch-prod -l app=redis-prod`
   - Check database: `kubectl get pods -n truematch-prod -l app=postgres-prod`
   - Check external APIs (if applicable)

3. **Bug in Recent Deployment**
   - Rollback to previous version
   - Fix bug and re-deploy
   - Post-incident review

4. **Traffic Spike**
   - Check current request rate
   - Scale up replicas: `kubectl scale deployment/api --replicas=5 -n truematch-prod`
   - Check if legitimate traffic or attack

### Issue: Slow API Response

**Symptoms:**
- API latency > 1s
- Users report slow performance
- Latency alert firing

**Diagnosis:**
```bash
# Check latency by endpoint
curl https://prometheus.truematch.ai/graph \
  -d 'query=histogram_quantile(0.99,rate(http_request_duration_seconds_bucket[5m]))'

# Check slowest endpoints
kubectl logs deployment/api -n truematch-prod \
  --tail=200 | grep "duration"

# Check database query performance
PGPASSWORD=$DB_PASSWORD psql -h postgres-prod -U $DB_USER -d truematch_prod \
  -c "SELECT query, calls, total_time, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"

# Check system resources
kubectl top nodes
kubectl top pods -n truematch-prod
```

**Common Causes & Solutions:**

1. **Slow Database Queries**
   - Enable slow query log
   - Check query execution plans: `EXPLAIN ANALYZE <query>`
   - Add missing indexes
   - Optimize query

2. **Connection Pool Exhaustion**
   - Check connection count: `SELECT count(*) FROM pg_stat_activity;`
   - Increase pool size
   - Identify long-running connections

3. **Resource Contention**
   - Check CPU: `kubectl top pods -n truematch-prod`
   - Check memory: `kubectl top pods -n truematch-prod`
   - Scale up or optimize code

4. **Network Issues**
   - Check network latency to database
   - Check network bandwidth usage
   - Check packet loss

### Issue: Worker Queue Backing Up

**Symptoms:**
- Queue depth > 1000 tasks
- Alert firing
- Tasks not being processed

**Diagnosis:**
```bash
# Check queue depth
kubectl exec -it deployment/worker -n truematch-prod -- \
  python -c "from app.worker import get_queue_length; print(get_queue_length())"

# Check worker status
kubectl get pods -n truematch-prod -l app=worker

# Check worker logs
kubectl logs deployment/worker -n truematch-prod --tail=100

# Check task processing rate
curl https://prometheus.truematch.ai/graph \
  -d 'query=rate(celery_task_total[1m])'
```

**Common Causes & Solutions:**

1. **Worker Pods Down**
   - Restart workers: `kubectl rollout restart deployment/worker -n truematch-prod`
   - Check pod events: `kubectl describe pod <pod-name> -n truematch-prod`

2. **Long-Running Tasks**
   - Check task duration: `kubectl logs deployment/worker -n truematch-prod | grep "Task.*started"`
   - Identify slow tasks in code
   - Optimize or increase task timeout

3. **Database Overload**
   - Scale up database connections
   - Optimize database queries
   - Add caching

4. **Not Enough Worker Replicas**
   - Scale up workers: `kubectl scale deployment/worker --replicas=5 -n truematch-prod`
   - Check if HPA is working: `kubectl get hpa -n truematch-prod`

---

## Performance Tuning

### Database Performance

#### Check Slow Queries
```bash
# Connect to database
PGPASSWORD=$DB_PASSWORD psql -h postgres-prod -U $DB_USER -d truematch_prod

# Enable slow query logging
ALTER SYSTEM SET log_min_duration_statement = 1000;  -- 1 second
SELECT pg_reload_conf();

# View slow queries
SELECT query, calls, total_time, mean_time 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;
```

#### Add Indexes
```bash
-- Identify missing indexes for frequent queries
SELECT schemaname, tablename, attname, n_distinct, correlation 
FROM pg_stats 
WHERE tablename IN ('matches', 'candidates', 'jobs')
ORDER BY n_distinct DESC;

-- Create index (if beneficial)
CREATE INDEX CONCURRENTLY idx_table_column ON table(column);
```

#### Analyze and Vacuum
```bash
-- Analyze table statistics
ANALYZE matches;
ANALYZE candidates;

-- Vacuum (cleanup dead rows)
VACUUM ANALYZE matches;
```

### Application Performance

#### Enable Profiling
```bash
# Add to deployment
export ENABLE_PROFILING="true"
kubectl set env deployment/api ENABLE_PROFILING=true -n truematch-prod

# Generate flamegraph
# (Requires py-spy or similar)
```

#### Memory Optimization
```bash
# Check memory usage by object type
kubectl exec deployment/api -n truematch-prod -- \
  python -c "import tracemalloc; tracemalloc.start(); ..."

# Identify large objects in memory
# Review logs for memory usage patterns
```

#### Connection Pool Tuning
```bash
# Check current pool settings
echo "select setting from pg_settings where name = 'max_connections';" | \
  PGPASSWORD=$DB_PASSWORD psql -h postgres-prod -U $DB_USER

# Increase if needed (requires restart)
ALTER SYSTEM SET max_connections = 200;
SELECT pg_reload_conf();
```

### Network Performance

#### Latency Optimization
```bash
# Check network latency to database
kubectl exec deployment/api -n truematch-prod -- \
  ping -c 5 postgres-prod

# Check if in same availability zone
kubectl describe nodes | grep topology.kubernetes.io/zone

# Consider moving to same AZ if not
```

#### Bandwidth Optimization
```bash
# Check network usage
kubectl top pods -n truematch-prod

# Implement caching to reduce network calls
# Use compression for large responses
# Batch API requests when possible
```

---

## Database Operations

### Backup and Restore

#### Create Manual Backup
```bash
# Create backup pod
kubectl run backup-$(date +%s) \
  --image=postgres:latest \
  --namespace=truematch-prod \
  -i --tty --rm \
  -- pg_dump -h postgres-prod -U $DB_USER \
     -d truematch_prod > backup-$(date +%Y%m%d-%H%M%S).sql

# Backup file size
du -h backup-*.sql
```

#### Restore from Backup
```bash
# WARNING: This will overwrite current database!
# 1. Create snapshot first
kubectl exec -it postgres-prod-0 -- \
  pg_dump truematch_prod > pre-restore-backup.sql

# 2. Drop current database
kubectl exec -it postgres-prod-0 -- \
  psql -c "DROP DATABASE truematch_prod;"

# 3. Create new database
kubectl exec -it postgres-prod-0 -- \
  psql -c "CREATE DATABASE truematch_prod;"

# 4. Restore from backup
kubectl exec -it postgres-prod-0 -- \
  psql truematch_prod < backup-20260719-120000.sql

# 5. Verify
kubectl exec -it postgres-prod-0 -- \
  psql truematch_prod -c "SELECT COUNT(*) FROM matches;"
```

### Database Maintenance

#### Regular Tasks
```bash
# Weekly vacuum (cleanup dead rows)
kubectl exec -it postgres-prod-0 -- \
  psql truematch_prod -c "VACUUM ANALYZE;"

# Monthly reindex
kubectl exec -it postgres-prod-0 -- \
  psql truematch_prod -c "REINDEX DATABASE truematch_prod;"

# Check bloat
kubectl exec -it postgres-prod-0 -- \
  psql truematch_prod -c "
    SELECT schemaname, tablename, 
           ROUND(100.0 * (pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) / pg_total_relation_size(schemaname||'.'||tablename)) AS bloat_ratio
    FROM pg_tables
    WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
    ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"
```

### Connection Management

#### Monitor Connections
```bash
# Check active connections
kubectl exec -it postgres-prod-0 -- \
  psql truematch_prod -c "SELECT pid, usename, state, query FROM pg_stat_activity WHERE state != 'idle';"

# Check connection count by user/database
kubectl exec -it postgres-prod-0 -- \
  psql -c "SELECT datname, count(*) FROM pg_stat_activity GROUP BY datname;"
```

#### Kill Long-Running Queries
```bash
# Find long-running queries
kubectl exec -it postgres-prod-0 -- \
  psql truematch_prod -c "
    SELECT pid, usename, duration, query 
    FROM pg_stat_activity 
    WHERE state != 'idle' 
    AND duration > interval '10 minutes';"

# Kill specific query
kubectl exec -it postgres-prod-0 -- \
  psql truematch_prod -c "SELECT pg_terminate_backend(PID);"
```

---

## Security Operations

### Secrets Management

#### Rotate Secrets
```bash
# 1. Generate new secret
NEW_SECRET=$(openssl rand -base64 32)

# 2. Update in secrets management (e.g., AWS Secrets Manager)
aws secretsmanager update-secret \
  --secret-id truematch/prod/database-password \
  --secret-string "$NEW_SECRET"

# 3. Update Kubernetes secret
kubectl patch secret truematch-prod-secrets -n truematch-prod \
  -p "{\"data\":{\"DATABASE_PASSWORD\":\"$(echo -n $NEW_SECRET | base64)\"}}\"

# 4. Restart pods to pick up new secret
kubectl rollout restart deployment/api -n truematch-prod

# 5. Verify pods restarted
kubectl get pods -n truematch-prod -o wide
```

#### Audit Secret Access
```bash
# Check who accessed secrets
kubectl get events -n truematch-prod | grep "secret"

# Check RBAC permissions
kubectl get rolebindings,clusterrolebindings -o json | grep "secret"
```

### Network Security

#### Check Network Policies
```bash
# List network policies
kubectl get networkpolicies -n truematch-prod

# Test connectivity
kubectl run -it --rm test-pod --image=curlimages/curl:latest -- \
  curl http://api.truematch-prod.svc.cluster.local/healthz
```

#### Update Ingress Rules
```bash
# Edit ingress
kubectl edit ingress api-ingress -n truematch-prod

# Add IP whitelist (example)
annotations:
  nginx.ingress.kubernetes.io/whitelist-source-range: "10.0.0.0/8,203.0.113.0/24"
```

### Access Control

#### Audit RBAC
```bash
# List all role bindings in namespace
kubectl get rolebindings -n truematch-prod

# Check service account permissions
kubectl describe sa truematch-prod -n truematch-prod

# Audit recent API access
kubectl logs -n kube-apiserver | grep "truematch"
```

#### Revoke Access
```bash
# Remove role binding
kubectl delete rolebinding <binding-name> -n truematch-prod

# Remove user from group
# (Method depends on your user management system)
```

---

## Emergency Procedures

### Total Service Outage

**Goal:** Restore service to working state as quickly as possible

```bash
# 1. Declare incident
# - Notify team via Slack
# - Create incident ticket
# - Start war room call

# 2. Assess situation
kubectl get deployments -n truematch-prod
kubectl get pods -n truematch-prod
kubectl get events -n truematch-prod | tail -20

# 3. Attempt quick fixes
# Check if pods are crashing
kubectl logs deployment/api -n truematch-prod --tail=50 | grep ERROR

# 4. If pod issues, try restart
kubectl rollout restart deployment/api -n truematch-prod

# 5. If restart fails, check database
kubectl exec -it postgres-prod-0 -- psql -c "SELECT 1;"

# 6. If database down, check backups
aws s3 ls s3://truematch-backups/

# 7. If all else fails, execute DR plan
# See Disaster Recovery guide

# 8. Monitor recovery
kubectl logs deployment/api -n truematch-prod -f

# 9. Post-incident review
# - Identify root cause
# - Document what happened
# - Plan prevention measures
```

### Database Corruption

**Symptoms:**
- Database won't start
- Query errors about corrupted data
- Replication lag growing indefinitely

**Recovery Steps:**
```bash
# 1. Stop writes to database
# Disable deployment
kubectl scale deployment/api --replicas=0 -n truematch-prod

# 2. Restore from latest backup
# See "Restore from Backup" section above

# 3. Verify data integrity
# Run validation checks

# 4. Resume operations
kubectl scale deployment/api --replicas=3 -n truematch-prod

# 5. Post-incident review
# - Determine cause of corruption
# - Improve monitoring
# - Document lessons learned
```

### Memory Leak / Resource Exhaustion

**Symptoms:**
- Pod memory growing continuously
- OOMKilled pods
- Nodes becoming unschedulable

**Recovery Steps:**
```bash
# 1. Immediate: Scale up or add nodes
kubectl node-drain node-name  # If draining, migrate pods
kubectl scale deployment/api --replicas=5 -n truematch-prod

# 2. Diagnose leak
kubectl top pods -n truematch-prod -l app=api

# 3. Gather memory profile
kubectl exec deployment/api -n truematch-prod -- \
  python -m memory_profiler app/main.py

# 4. Find and fix leak in code

# 5. Deploy fix
./scripts/deploy-to-production.sh --tag v1.2.4

# 6. Monitor
kubectl logs deployment/api -n truematch-prod -f
```

### Suspicious Activity / Security Incident

**Steps:**
```bash
# 1. Isolate affected resources
kubectl patch networkpolicy truematch-prod-network-policy -n truematch-prod \
  --type merge -p '{"spec":{"ingress":[]}}'

# 2. Preserve logs for investigation
kubectl logs deployment/api -n truematch-prod > incident-logs.txt

# 3. Check for unauthorized access
kubectl get rolebindings,clusterrolebindings -o json > rbac-backup.json

# 4. Review recent changes
kubectl rollout history deployment/api -n truematch-prod

# 5. Notify security team
# - Provide logs
# - Timeline of events

# 6. Restore network policies
kubectl apply -f backend/k8s/prod-deployment.yaml -n truematch-prod

# 7. Deploy security patch if needed
```

---

## Monitoring & Alerting

### Key Metrics to Monitor

**Availability Metrics:**
- Pod uptime
- Deployment replica readiness
- Service availability

**Performance Metrics:**
- Request latency (p50, p95, p99)
- Request rate
- Error rate

**Resource Metrics:**
- CPU usage
- Memory usage
- Disk usage
- Network I/O

**Business Metrics:**
- Matches created
- Success rate
- Processing latency

### Alert Response Guide

| Alert | Typical Cause | Solution |
|-------|---------------|----------|
| APIHighErrorRate | Bug, dependency down | Check logs, rollback if needed |
| APILatencyHigh | Resource contention, slow query | Check DB, scale up if needed |
| APIDownPods | Crash, node issue | Check pod logs, restart if needed |
| WorkerHighQueueDepth | Workers down, slow tasks | Scale workers or optimize tasks |
| DatabaseDown | Connection lost, crash | Check DB pod, restart if needed |
| NodeDiskSpaceLow | Logs/data accumulation | Clean up, increase storage |

---

## Related Documents

- [Production Checklist](./PRODUCTION_CHECKLIST.md)
- [Incident Response](./INCIDENT_RESPONSE.md)
- [Disaster Recovery](./DISASTER_RECOVERY.md)
- [Kubernetes Deployment](../backend/k8s/prod-deployment.yaml)

---

## Document History

| Date | Author | Changes |
|------|--------|---------|
| 2026-07-19 | DevOps Team | Initial creation |

---

**Last Review:** 2026-07-19  
**Next Review Date:** 2026-10-19  
**Reviewed By:** DevOps Team
