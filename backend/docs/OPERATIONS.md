# TrueMatch Backend Operations Runbook

**Last Updated:** 2026-06-03

This document provides runbooks for deploying, operating, and troubleshooting the TrueMatch backend in production.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Deployment](#deployment)
3. [Rollback](#rollback)
4. [Common Issues](#common-issues)
5. [Monitoring & Alerts](#monitoring--alerts)
6. [Performance Tuning](#performance-tuning)
7. [Data Backup & Recovery](#data-backup--recovery)
8. [Security Checklist](#security-checklist)

---

## Prerequisites

**System Requirements:**
- PostgreSQL 13+ with async driver support
- Redis 6.0+ (for rate limiting and Celery queue)
- Python 3.11+
- Docker + docker-compose (for containerized deployments)
- Kubernetes 1.20+ (for orchestrated deployments)

**Environment Variables:**
```bash
# Database
DATABASE_URL=postgresql+asyncpg://truematch:password@db.example.com:5432/truematch

# Redis (Celery + Rate Limiting)
REDIS_URL=redis://redis.example.com:6379

# Secrets (NEVER commit to git)
JWT_SECRET=<random-32-char-string>
ENCRYPTION_KEY=<base64-encoded-32-byte-key>
ENCRYPTION_INDEX_KEY=<base64-encoded-32-byte-key>
ANTHROPIC_API_KEY=<your-api-key>

# AWS S3 (file storage)
S3_BUCKET=truematch-uploads
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=<your-key>
AWS_SECRET_ACCESS_KEY=<your-secret>

# Observability
SENTRY_DSN=<your-sentry-dsn>
LOG_JSON=true
LOG_LEVEL=INFO

# CORS (set to your frontend domain)
CORS_ORIGINS=https://app.truematch.ai

# Environment
ENVIRONMENT=production
```

---

## Deployment

### Pre-Deployment Checklist

- [ ] All tests pass: `pytest --cov`
- [ ] No uncommitted changes in code
- [ ] Database migration tested on staging: `alembic upgrade head`
- [ ] Sentry project is set up and healthy
- [ ] Monitoring dashboards are set up
- [ ] Incident response team is on-call
- [ ] Feature flags are configured
- [ ] Load testing passed with 100+ concurrent users

### Step 1: Build & Push Docker Image

```bash
# Build image
docker build -t truematch-backend:v1.2.3 .

# Tag and push
docker tag truematch-backend:v1.2.3 gcr.io/truematch/backend:v1.2.3
docker push gcr.io/truematch/backend:v1.2.3

# Verify image
docker pull gcr.io/truematch/backend:v1.2.3
```

### Step 2: Deploy to Staging

```bash
# Update staging deployment
kubectl set image deployment/truematch-backend-staging \
  app=gcr.io/truematch/backend:v1.2.3 \
  --record

# Wait for rollout to complete
kubectl rollout status deployment/truematch-backend-staging

# Run smoke tests
pytest tests/integration/smoke_tests.py --endpoint staging
```

### Step 3: Run Database Migrations

**Important:** Always run migrations **before** the code deployment.

```bash
# Connect to production database
psql postgresql://truematch:password@db.prod.example.com:5432/truematch

# Backup database FIRST
pg_dump postgresql://truematch:password@db.prod.example.com:5432/truematch \
  > truematch-backup-$(date +%Y%m%d-%H%M%S).sql

# Run migrations in a transaction (rollback on failure)
alembic upgrade head --sql  # Dry run to see SQL
alembic upgrade head        # Actually apply
```

### Step 4: Deploy to Production (Blue-Green Strategy)

```bash
# Create new "green" deployment
kubectl set image deployment/truematch-backend-green \
  app=gcr.io/truematch/backend:v1.2.3 \
  --record

# Wait for green to be ready
kubectl rollout status deployment/truematch-backend-green

# Route traffic to green (using load balancer or service selector)
kubectl patch service truematch-backend-api \
  -p '{"spec":{"selector":{"version":"v1.2.3"}}}'

# Monitor error rates and latency for 10 minutes
# If healthy, delete old blue deployment
kubectl delete deployment truematch-backend-blue
```

### Step 5: Verify Deployment

```bash
# Check health endpoints
curl https://api.truematch.ai/livez
curl https://api.truematch.ai/readyz

# Check logs
kubectl logs -f deployment/truematch-backend-green

# Run smoke tests against production
pytest tests/integration/smoke_tests.py --endpoint production
```

---

## Rollback

### Immediate Rollback (Error Rate > 5%)

```bash
# 1. Switch traffic back to previous version
kubectl patch service truematch-backend-api \
  -p '{"spec":{"selector":{"version":"v1.2.2"}}}'

# 2. Verify traffic is routed correctly
curl https://api.truematch.ai/health

# 3. Scale down the bad deployment
kubectl scale deployment truematch-backend-green --replicas=0

# 4. Notify on-call team
# Slack: @oncall "Rolled back backend to v1.2.2 due to high error rate"
```

### Database Rollback (if migration failed)

```bash
# Restore from backup
psql postgresql://truematch:password@db.prod.example.com:5432/truematch \
  < truematch-backup-20260603-143025.sql

# Verify database integrity
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM assessments;
```

---

## Common Issues

### Issue: High Error Rate (> 5%)

**Symptoms:** Error rate spike after deployment

**Diagnosis:**
1. Check error logs: `kubectl logs -f deployment/truematch-backend`
2. Look for pattern: Are all errors from one endpoint? New error type?
3. Check request_id in logs for correlation
4. Check Sentry for error grouping

**Resolution:**
```bash
# If new code caused errors, rollback immediately
# See "Immediate Rollback" above

# If database migration caused errors:
# 1. Check migration alembic/versions/XXXX_*.py
# 2. Rollback migration: alembic downgrade -1
# 3. Fix migration and redeploy
```

**Example Log Analysis:**
```bash
kubectl logs deployment/truematch-backend | grep "error_type" | jq '.' | sort | uniq -c | sort -rn
# Identify error types and fix root cause
```

---

### Issue: Slow API (p99 latency > 2s)

**Symptoms:** Requests are slow but not failing

**Diagnosis:**
1. Check database slow-query log:
```sql
SELECT * FROM pg_stat_statements 
WHERE query LIKE '%assessments%' 
ORDER BY mean_exec_time DESC LIMIT 10;
```

2. Check connection pool exhaustion:
```bash
# If pool_size is 20, check if we have 20+ active connections
SELECT count(*) FROM pg_stat_activity WHERE state = 'active';
```

3. Check CPU/Memory on API pods:
```bash
kubectl top pods -l app=truematch-backend
```

**Resolution:**
- **N+1 queries:** Add `selectinload()` to the endpoint
- **Slow query:** Add index on frequently-filtered columns
- **Connection pool exhausted:** Increase pool_size in database.py

---

### Issue: Failed Assessments (Worker Errors)

**Symptoms:** Assessments stuck in "processing" status or marked "failed"

**Diagnosis:**
1. Check worker logs:
```bash
kubectl logs -f deployment/truematch-worker --tail=100
```

2. Check Celery queue:
```bash
redis-cli -h redis.prod.example.com
> LLEN celery
> LRANGE celery 0 -1  # Peek at queue
```

3. Check S3 and LLM availability:
```bash
curl https://api.truematch.ai/readyz
# Check if s3 and llm components are true
```

**Resolution:**
- **LLM unavailable:** Check Anthropic API status and rate limits
- **S3 unavailable:** Verify AWS credentials and bucket permissions
- **Worker crashed:** Check `docker logs <worker-container>`

---

### Issue: Database Connection Errors

**Symptoms:** `sqlalchemy.exc.ResourceClosedError` or `connection timeout`

**Diagnosis:**
1. Check database availability:
```bash
psql postgresql://truematch:password@db.prod.example.com:5432/truematch \
  -c "SELECT 1;"
```

2. Check for connection leaks:
```sql
-- Count connections by state
SELECT state, COUNT(*) FROM pg_stat_activity GROUP BY state;

-- Kill idle connections older than 30 minutes
SELECT pg_terminate_backend(pid) 
FROM pg_stat_activity 
WHERE state = 'idle' 
AND query_start < now() - interval '30 minutes';
```

**Resolution:**
- **Connection pool exhausted:** Check if pool_size is sufficient
- **Database down:** Failover to replica or restore from backup
- **Long-running queries:** Kill with `pg_terminate_backend(pid)`

---

### Issue: Rate Limit False Positives

**Symptoms:** Legitimate users getting HTTP 429

**Diagnosis:**
1. Check rate limit config:
```bash
# Get limit from settings
curl https://api.truematch.ai/docs  # View CORS_ORIGINS
```

2. Check if traffic is coming from shared IP (office, VPN):
```bash
# Rate limiting is per-IP, so if users share IP, they share limit
grep "429" /var/log/app.log | jq '.client_ip' | sort | uniq -c
```

**Resolution:**
- **Shared IP:** Increase rate limit in settings or use API keys instead of IP
- **Misconfigured:** Update `settings.rate_limit_per_minute` and redeploy

---

## Monitoring & Alerts

### Key Metrics to Track

| Metric | Alert Threshold | Action |
|--------|-----------------|--------|
| Error Rate | > 5% | Page on-call immediately |
| p99 Latency | > 2s | Investigate slow queries |
| DB Connection Pool | > 80% utilization | Scale up pool_size |
| Redis Memory | > 80% of max | Flush expired keys |
| S3 Request Failures | > 1% | Check AWS status |
| LLM Token Usage | > 80% of quota | Contact Anthropic |
| Disk Space | < 10% free | Trigger cleanup |

### Setting Up Prometheus Metrics

```yaml
# prometheus-config.yml
scrape_configs:
  - job_name: 'truematch-backend'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

### Alert Rules (Alertmanager)

```yaml
groups:
  - name: truematch
    rules:
      # Error rate alert
      - alert: HighErrorRate
        expr: rate(truematch_http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        annotations:
          summary: "High error rate detected"
          description: "Error rate {{ $value }} > 5%"

      # Latency alert
      - alert: HighLatency
        expr: histogram_quantile(0.99, truematch_http_request_duration_seconds) > 2
        for: 5m
        annotations:
          summary: "High p99 latency detected"

      # Connection pool alert
      - alert: ConnectionPoolExhausted
        expr: pg_connections_used / pg_connections_max > 0.8
        annotations:
          summary: "Database connection pool 80% full"
```

---

## Performance Tuning

### Database Tuning

```sql
-- Check index usage
SELECT schemaname, tablename, indexname, idx_scan 
FROM pg_stat_user_indexes 
WHERE idx_scan = 0 
ORDER BY pg_relation_size(indexrelid) DESC;

-- Analyze slow queries
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

-- Update statistics
VACUUM ANALYZE;
REINDEX;
```

### API Tuning

**If p99 latency is high:**
1. Add `selectinload()` to list endpoints
2. Add indexes on frequently-filtered columns
3. Increase `pool_size` in database.py

**If error rate is high:**
1. Check Sentry for error patterns
2. Add retry logic for transient failures
3. Check external service health

---

## Data Backup & Recovery

### Daily Backups

```bash
#!/bin/bash
# Run daily at 2 AM UTC
pg_dump postgresql://truematch:password@db.prod.example.com:5432/truematch \
  | gzip > /backups/truematch-$(date +%Y%m%d).sql.gz

# Upload to S3
aws s3 cp /backups/truematch-$(date +%Y%m%d).sql.gz \
  s3://truematch-backups/daily/
```

### Point-in-Time Recovery

```bash
# Find backup from desired date
aws s3 ls s3://truematch-backups/daily/ | grep 20260601

# Restore
aws s3 cp s3://truematch-backups/daily/truematch-20260601.sql.gz - | gunzip | psql postgresql://truematch:password@db.recovery.example.com:5432/truematch
```

---

## Security Checklist

**Before Production Deployment:**

- [ ] All secrets are in environment variables (never in code)
- [ ] CORS_ORIGINS is set to production domain only
- [ ] JWT_SECRET is a random 32-character string
- [ ] ENCRYPTION_KEY and ENCRYPTION_INDEX_KEY are strong
- [ ] SSL/TLS is enabled on all endpoints
- [ ] Rate limiting is enabled
- [ ] Audit logging is enabled
- [ ] Sentry is configured for error tracking
- [ ] Database backups are automated
- [ ] Only authorized IPs can access admin endpoints
- [ ] Singpass credentials are not logged
- [ ] S3 bucket has encryption enabled
- [ ] API documentation is updated

**Regular Security Reviews:**

- [ ] Review access logs for suspicious activity
- [ ] Check for failed authentication attempts
- [ ] Audit database for unauthorized access
- [ ] Verify encryption keys are rotated annually
- [ ] Test disaster recovery procedures
- [ ] Review recent CVEs for dependencies

---

## Support

For production issues, contact:
- **On-Call Pager:** Opsgenie page
- **Slack:** #truematch-incidents
- **Email:** ops@truematch.ai

