# TrueMatch AI Disaster Recovery Plan
## Phase 3: Disaster Recovery & Business Continuity

**Version:** 1.0  
**Last Updated:** 2026-07-19  
**Owner:** Infrastructure Team  
**Last Tested:** [Date]  
**Next Test Date:** [Date + 90 days]

---

## Executive Summary

This document outlines the disaster recovery (DR) procedures for TrueMatch AI production infrastructure. Our goal is to minimize data loss and downtime in the event of a catastrophic failure.

### Key Metrics

| Metric | Target | Current |
|--------|--------|---------|
| RTO (Recovery Time Objective) | 1 hour | TBD |
| RPO (Recovery Point Objective) | 15 minutes | TBD |
| Backup Frequency | Every 4 hours | Implemented |
| Backup Retention | 30 days | Implemented |
| DR Test Frequency | Every 90 days | Planned |

### Architecture Overview

```
Primary Region (us-west-2)
├── Kubernetes Cluster
├── PostgreSQL Database
├── Redis Cache
└── Application Services
    ↓ (async replication)
Backup Region (us-east-1)
├── Standby Kubernetes Cluster
├── PostgreSQL Replica (read-only)
├── Redis Replica
└── Application Services (cold standby)
    ↓ (point-in-time backups)
S3 Backup Buckets (Multi-region)
├── Database snapshots
├── Application backups
├── Configuration backups
└── Logs archive
```

---

## Table of Contents

1. [Disaster Classification](#disaster-classification)
2. [Backup & Recovery](#backup--recovery)
3. [Regional Failover](#regional-failover)
4. [Service Recovery](#service-recovery)
5. [Data Recovery](#data-recovery)
6. [Testing & Validation](#testing--validation)
7. [Communication Plan](#communication-plan)

---

## Disaster Classification

### Level 1: Single Service Degradation
**Impact:** One component affected (e.g., API, worker)  
**RTO:** 30 minutes  
**RPO:** < 5 minutes

**Examples:**
- API deployment failed
- Worker nodes unhealthy
- Single pod crash

**Recovery:** See Operations Runbook

### Level 2: Regional Service Outage
**Impact:** Multiple services in primary region down  
**RTO:** 1 hour  
**RPO:** < 15 minutes

**Examples:**
- Kubernetes cluster failure
- Multiple node failures
- Network partition

**Recovery:** Regional failover (this document)

### Level 3: Data Loss / Corruption
**Impact:** Database damaged or inaccessible  
**RTO:** 2-4 hours  
**RPO:** < 4 hours

**Examples:**
- Database hardware failure
- Data corruption
- Accidental deletion

**Recovery:** Restore from backup

### Level 4: Complete Region Failure
**Impact:** Entire region (us-west-2) unavailable  
**RTO:** 4-8 hours  
**RPO:** < 1 hour

**Examples:**
- AWS region outage
- Major power loss
- Catastrophic infrastructure failure

**Recovery:** Multi-region failover

---

## Backup & Recovery

### Backup Strategy

#### Database Backups

**Method:** Automated snapshots + incremental backups

```bash
# Manual backup command
PGPASSWORD=$DB_PASSWORD pg_dump \
  -h postgres-prod.c.truematch-prod.internal \
  -U truematch_prod \
  -d truematch_prod \
  | gzip > backup-$(date +%Y%m%d-%H%M%S).sql.gz

# Upload to S3
aws s3 cp backup-*.sql.gz s3://truematch-backups/production/
```

**Schedule:**
- Full backup: Daily at 2 AM UTC
- Incremental backups: Every 4 hours
- WAL archival: Continuous

**Retention:**
- Daily backups: 30 days
- Weekly backups: 13 weeks
- Monthly backups: 1 year

#### Application Backups

**Method:** Container image snapshots, configuration backups

```bash
# Backup configuration
kubectl get all -n truematch-prod -o yaml > kube-backup.yaml
kubectl get secrets -n truematch-prod -o yaml > kube-secrets.yaml  # (encrypted)
```

**Schedule:**
- After each production deployment
- Daily configuration backup

**Retention:**
- Last 10 deployments
- 30 days retention

#### Verification

**Weekly Backup Validation:**
```bash
# Verify most recent backup
aws s3 ls s3://truematch-backups/production/ --recursive | tail -1

# Check backup size (should be > 100MB for database)
aws s3 ls s3://truematch-backups/production/ --human-readable | tail -1

# Monthly: Restore backup to test environment and verify data
# See "Restore from Backup" section below
```

### Restore from Backup

#### Restore Database (Minimal Downtime)

**Procedure:**

```bash
# 1. Create backup of current database first
PGPASSWORD=$DB_PASSWORD pg_dump -h postgres-prod -U truematch_prod -d truematch_prod > pre-restore-backup.sql

# 2. Download backup from S3
aws s3 cp s3://truematch-backups/production/backup-20260715-020000.sql.gz .
gunzip backup-20260715-020000.sql.gz

# 3. Prepare clean database
PGPASSWORD=$DB_PASSWORD psql -h postgres-prod -U postgres -c "DROP DATABASE truematch_prod;"
PGPASSWORD=$DB_PASSWORD psql -h postgres-prod -U postgres -c "CREATE DATABASE truematch_prod OWNER truematch_prod;"

# 4. Restore data
PGPASSWORD=$DB_PASSWORD psql -h postgres-prod -U truematch_prod -d truematch_prod < backup-20260715-020000.sql

# 5. Verify data integrity
PGPASSWORD=$DB_PASSWORD psql -h postgres-prod -U truematch_prod -d truematch_prod -c "
  SELECT COUNT(*) as total_records,
         COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '7 days') as recent_records
  FROM matches;"

# 6. Rebuild indexes if needed
PGPASSWORD=$DB_PASSWORD psql -h postgres-prod -U truematch_prod -d truematch_prod -c "REINDEX DATABASE truematch_prod;"
```

#### Restore Configuration

```bash
# 1. Update ConfigMap
kubectl apply -f backed-up-config.yaml -n truematch-prod

# 2. Restart affected deployments
kubectl rollout restart deployment/api -n truematch-prod
kubectl rollout restart deployment/worker -n truematch-prod

# 3. Verify
kubectl get pods -n truematch-prod
```

#### Restore from Point-in-Time (PITR)

If you need to restore to a specific point in time:

```bash
# 1. Stop all writes to database
kubectl scale deployment/api --replicas=0 -n truematch-prod

# 2. Restore to specific time (PostgreSQL requires recovery to run)
# This requires creating a new database cluster and using PITR
# Contact AWS/Infrastructure team for this

# 3. Verify recovered state
# Check data at the point in time

# 4. Resume operations
kubectl scale deployment/api --replicas=3 -n truematch-prod
```

---

## Regional Failover

### Pre-Failover Checks

**Verify before initiating failover:**

```bash
# 1. Confirm primary region is truly down
ping -c 5 api.truematch.ai
timeout 10 curl https://api.truematch.ai/healthz

# 2. Check status page / AWS console
# - Confirm AWS region is having issues (not just our infrastructure)

# 3. Verify backup region is healthy
kubectl --kubeconfig ~/.kube/backup-region.config get all -n truematch-prod

# 4. Check backup region database
PGPASSWORD=$DB_PASSWORD psql -h postgres-backup.region.internal -U truematch_prod -d truematch_prod -c "SELECT COUNT(*) FROM matches;"

# 5. Confirm DNS failover ready
dig api.truematch.ai @8.8.8.8  # Verify current DNS resolution
```

### Failover Procedure

**Step 1: Declare Failover (5 min)**

```bash
# 1. Create incident
# CRITICAL: Failing over to backup region (us-east-1)

# 2. Notify team
# Post to Slack: @channel - CRITICAL: Initiating regional failover

# 3. Page all on-call staff
# Use PagerDuty for critical incident escalation
```

**Step 2: Update DNS (5-10 min)**

```bash
# Update DNS to point to backup region
# THIS MUST BE DONE CAREFULLY - AFFECTS ALL USERS

# Option A: AWS Route 53 failover routing
aws route53 change-resource-record-sets \
  --hosted-zone-id Z1234567890ABC \
  --change-batch '{
    "Changes": [{
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "api.truematch.ai",
        "Type": "A",
        "SetIdentifier": "Primary",
        "Failover": "PRIMARY",
        "TTL": 60,
        "ResourceRecords": [{"Value": "10.1.0.10"}]  # backup region IP
      }
    }]
  }'

# Option B: Cloudflare failover (if using Cloudflare)
curl -X PATCH "https://api.cloudflare.com/client/v4/zones/abc123/dns_records/def456" \
  -H "X-Auth-Email: admin@truematch.ai" \
  -H "Authorization: Bearer $CLOUDFLARE_TOKEN" \
  -d '{"content":"backup-ip-address"}'

# Verify DNS resolution (wait for TTL)
# Allow 60-300 seconds for DNS propagation
```

**Step 3: Activate Backup Region Kubernetes (10-15 min)**

```bash
# 1. Scale up backup cluster
export KUBECONFIG=~/.kube/backup-region.config

# 2. Verify cluster is ready
kubectl get nodes

# 3. Check if backup services are already running
kubectl get all -n truematch-prod

# 4. If not running, deploy from backup
kubectl apply -f kube-backup.yaml -n truematch-prod

# 5. Wait for pods to start
kubectl rollout status deployment/api -n truematch-prod --timeout=10m
```

**Step 4: Promote Backup Database (10 min)**

```bash
# Connect to backup PostgreSQL replica
PGPASSWORD=$DB_PASSWORD psql -h postgres-backup-region.internal -U truematch_prod -d truematch_prod

# Promote replica to primary (one-way, cannot revert)
SELECT pg_promote();

# Verify promotion
SELECT pg_is_in_recovery();  # Should return false (no longer in recovery mode)

# Check replication status
SELECT * FROM pg_stat_replication;
```

**Step 5: Update Application Configuration (5 min)**

```bash
# Update connection strings to point to backup region database
kubectl set env deployment/api \
  DATABASE_URL="postgresql+asyncpg://user:pass@postgres-backup-region.internal:5432/truematch_prod" \
  -n truematch-prod

# Update Redis connection
kubectl set env deployment/api \
  REDIS_URL="redis://redis-backup-region.internal:6379/0" \
  -n truematch-prod

# Restart pods
kubectl rollout restart deployment/api -n truematch-prod
```

**Step 6: Verify Service (10 min)**

```bash
# Test API endpoint
curl https://api.truematch.ai/healthz
curl https://api.truematch.ai/readyz

# Check logs
kubectl logs deployment/api -n truematch-prod --tail=20

# Verify data
curl https://api.truematch.ai/api/v1/stats

# Monitor metrics
# Visit Grafana and verify all metrics flowing
```

**Step 7: Communication Update (ongoing)**

```
Post to Slack every 5-10 minutes:
- Current status
- What's been recovered
- What's still being worked on
- ETA for full recovery

Example:
"UPDATE (HH:MM UTC): Regional failover 60% complete
- DNS updated and propagating
- Backup Kubernetes cluster activated
- Database promoted
- Next: Verify all services healthy
- ETA: Full recovery in 30 minutes"
```

### Post-Failover

**After service is restored:**

1. Monitor closely for 24-48 hours
2. Identify any data loss
3. Plan for failback to primary (if applicable)
4. Run post-incident review

**Failback Procedure:**

```bash
# Only perform after primary region is fully recovered

# 1. Rebuild primary database from backup
# Same procedure as "Restore Database"

# 2. Re-enable replication from primary to backup
# Contact Infrastructure team

# 3. Update DNS to point back to primary
# Same as failover, but change IP back

# 4. Monitor and verify

# 5. Run comprehensive tests
```

---

## Service Recovery

### Critical Service Checklist

```markdown
## API Service
- [ ] Container image available
- [ ] Environment variables configured
- [ ] Database connection working
- [ ] Health endpoint responding
- [ ] Metrics endpoint working

## Worker Service
- [ ] Container image available
- [ ] Queue connection working
- [ ] Database connection working
- [ ] Tasks processing

## Database
- [ ] Backup available
- [ ] Replication working (if applicable)
- [ ] Connections accepted
- [ ] Data integrity verified

## Cache (Redis)
- [ ] Backup available
- [ ] Replication working (if applicable)
- [ ] Connections accepted

## Monitoring
- [ ] Prometheus targets configured
- [ ] Grafana dashboards loading
- [ ] Sentry accepting events
- [ ] Logs flowing to aggregator
```

### Rollback to Previous State

If recovery is unsuccessful:

```bash
# 1. Assess what went wrong
# Review logs and error messages

# 2. Restore from previous backup
# If data was corrupted during recovery

# 3. Investigate root cause
# What caused the corruption?

# 4. Prevent recurrence
# Update procedures or tooling
```

---

## Data Recovery

### Recovery Procedures by Data Type

#### Recent Data Loss (< 24 hours)

```bash
# Use point-in-time recovery (PITR)
# Restore to a time before data was lost

# 1. Stop all writes
kubectl scale deployment/api --replicas=0 -n truematch-prod

# 2. Perform PITR (with Infrastructure team help)

# 3. Verify recovered data

# 4. Resume operations
kubectl scale deployment/api --replicas=3 -n truematch-prod
```

#### Corrupted Data

```bash
# Identify corrupt records
SELECT * FROM matches WHERE updated_at > NOW() - INTERVAL '1 hour' AND status = 'invalid';

# Option 1: Restore from backup (safest)
# See "Restore from Backup" section

# Option 2: Delete corrupted records and regenerate
DELETE FROM matches WHERE id IN (...);
# Regenerate data if possible

# Option 3: Manual data fixing (if small amount)
# Update specific records to correct values
```

#### Accidental Deletion

```bash
# Immediately STOP all writes to prevent overwrite
kubectl scale deployment/api --replicas=0 -n truematch-prod

# Identify when deletion occurred
# Get backup from that time period

# Restore specific tables or records from backup
pg_restore -d truematch_prod -a -t deleted_table backup-20260715.sql

# Verify restoration

# Resume operations
kubectl scale deployment/api --replicas=3 -n truematch-prod
```

### Data Validation After Recovery

```bash
# Check data integrity
PGPASSWORD=$DB_PASSWORD psql -h postgres-prod -U truematch_prod -d truematch_prod << EOF

-- Check for orphaned records
SELECT COUNT(*) FROM matches WHERE user_id NOT IN (SELECT id FROM users);

-- Check for missing records
SELECT COUNT(*) FROM matches WHERE created_at IS NULL;

-- Verify recent data
SELECT COUNT(*) FROM matches WHERE created_at > NOW() - INTERVAL '24 hours';

-- Check for duplicates
SELECT id, COUNT(*) FROM matches GROUP BY id HAVING COUNT(*) > 1;

-- Verify relationships
SELECT COUNT(*) FROM matches m
WHERE NOT EXISTS (SELECT 1 FROM users u WHERE u.id = m.user_id);

EOF
```

---

## Testing & Validation

### Quarterly DR Test

**Frequency:** Every 90 days  
**Duration:** 2-4 hours  
**Team:** DevOps, Database, On-call staff

**Test Procedure:**

```bash
# 1. Prepare test environment (1 hour before)
# - Allocate test resources in backup region
# - Notify team of test start time
# - Create test incident ticket

# 2. Test database restore (30 min)
# - Download latest backup
# - Restore to test database
# - Verify data integrity
# - Document any issues

# 3. Test backup region failover (30 min)
# - Deploy services to backup region
# - Update test DNS
# - Verify services operational
# - Document any issues

# 4. Clean up (15 min)
# - Tear down test resources
# - Restore original DNS
# - Document lessons learned

# 5. Retrospective (30 min)
# - Review what worked
# - Identify improvements
# - Update procedures
```

### Monthly Backup Validation

```bash
# Every month, test that backups are actually restorable

# 1. List recent backups
aws s3 ls s3://truematch-backups/production/ --recursive | tail -5

# 2. Download most recent backup
aws s3 cp s3://truematch-backups/production/backup-latest.sql.gz .

# 3. Verify backup integrity
gunzip -t backup-latest.sql.gz  # Test compression

# 4. Spot-check restore (in test environment)
# - Restore to test database
# - Verify record counts
# - Check most recent records
```

### Post-Test Documentation

```markdown
# DR Test Report - [Date]

## Test Results
- Database Restore: ✓ PASS / ✗ FAIL (took X minutes)
- Backup Region Deploy: ✓ PASS / ✗ FAIL
- Service Verification: ✓ PASS / ✗ FAIL
- Data Integrity: ✓ PASS / ✗ FAIL

## Issues Encountered
1. [Issue] - [How resolved]
2. [Issue] - [How resolved]

## Improvements Needed
1. [Update procedure]
2. [Improve documentation]
3. [Add tooling]

## Next Test: [Date + 90 days]
```

---

## Communication Plan

### Notification Tree

```
CTO / VP Eng (automatic on critical alert)
    ↓
On-Call Manager
    ↓
Primary On-Call Team (all paged)
    ↓
Backup On-Call Team (called if needed)
    ↓
Infrastructure Team
    ↓
Executive Team (notified after 30 min if unresolved)
```

### Status Updates

| Time | Update Frequency | Channel |
|------|-----------------|---------|
| 0-15 min | Every 3-5 min | Slack, War Room |
| 15-60 min | Every 10 min | Slack, War Room, Status Page |
| 60+ min | Every 30 min | Slack, War Room, Email, Status Page |

### Sample Status Updates

```
T+0: "CRITICAL: Loss of connectivity to primary region. 
      Investigating and preparing for failover. More info in 5 min."

T+5: "CRITICAL: Confirmed primary region AWS outage affecting us.
      Initiating backup region failover. All hands on deck."

T+15: "CRITICAL: DNS failover in progress. Backup region services
       being activated. Database promotion underway."

T+30: "CRITICAL: 80% of traffic now on backup region. Database
       promotion complete. Verifying data integrity."

T+45: "HIGH: Service partially restored in backup region. Working
      on final health checks before full recovery."

T+60: "RESOLVED: Service fully recovered in backup region. Normal
      operations resumed. Post-incident review scheduled for tomorrow."
```

### Customer Communication

**Email Template:**

```
Subject: Service Incident Resolution - TrueMatch API

Dear Valued Customers,

At [HH:MM UTC] on [Date], our production infrastructure experienced
a regional failure affecting the TrueMatch API. 

What Happened:
- AWS us-west-2 region experienced an outage
- Our primary infrastructure became unavailable
- Service was unavailable for approximately [duration]

Actions Taken:
- We automatically failed over to our backup infrastructure
- Services were restored at [time]
- Data integrity was verified
- All systems are now operating normally

Impact:
- Some API requests may have failed
- Data within 15 minutes of the incident may not be replicated
- No permanent data loss occurred

Next Steps:
- We are monitoring closely for any issues
- A detailed post-incident review is underway
- We will share findings and improvements within 48 hours

We apologize for the inconvenience. Thank you for your patience.

Best regards,
TrueMatch Operations Team
```

---

## Contacts & Resources

### Key Contacts

| Role | Name | Phone | Email |
|------|------|-------|-------|
| Infrastructure Lead | [Name] | [Number] | [Email] |
| Database Admin | [Name] | [Number] | [Email] |
| On-Call Manager | [Name] | [Number] | [Email] |

### Important URLs

- Status Page: https://status.truematch.ai
- Monitoring: https://grafana.truematch.ai
- Logs: https://logs.truematch.ai
- AWS Console: https://console.aws.amazon.com
- PagerDuty: https://truematch.pagerduty.com

### Useful Scripts

- Backup automation: `backend/scripts/backup.sh`
- Restore automation: `backend/scripts/restore.sh`
- Failover automation: `backend/scripts/failover.sh`
- Health check: `backend/scripts/health-check.sh`

---

## Appendix: Quick Reference

### Failover Checklist (One Page)

```
☐ Confirm primary region truly down
☐ Verify backup region is healthy
☐ Page all on-call staff
☐ Create critical incident ticket
☐ Update DNS to backup region IP
☐ Wait for DNS propagation (60-300s)
☐ Promote backup database replica
☐ Update app configs to use backup resources
☐ Restart application services
☐ Verify service health
☐ Monitor closely
☐ Update status page
☐ Post regular Slack updates
```

### Restore Checklist (One Page)

```
☐ Download backup from S3
☐ Verify backup integrity (test decompress)
☐ Stop all writes to database
☐ Drop current database
☐ Create new database
☐ Restore from backup file
☐ Verify data integrity (count records)
☐ Rebuild indexes if needed
☐ Resume writes
☐ Monitor for issues
```

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-07-19 | Infrastructure Team | Initial creation |

---

**Last DR Test:** [Date]  
**Next DR Test:** [Date + 90 days]  
**Plan Review Date:** 2026-10-19  
**Owner:** Infrastructure Team Lead
