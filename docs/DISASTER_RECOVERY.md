# TrueMatch Disaster Recovery Plan

**Document Version:** 1.0  
**Last Updated:** 2026-06-07  
**Status:** Production Ready

---

## Table of Contents

1. [Overview](#overview)
2. [Recovery Objectives](#recovery-objectives)
3. [Failure Scenarios](#failure-scenarios)
4. [Recovery Procedures](#recovery-procedures)
5. [Testing & Drills](#testing--drills)
6. [Communication Plan](#communication-plan)

---

## Overview

This document outlines procedures to recover from various failure scenarios affecting TrueMatch services.

### Scope

- Database failures and corruption
- Application crashes
- Service degradation
- Data loss scenarios
- Infrastructure failures
- Security incidents

### Recovery Principles

1. **RPO (Recovery Point Objective):** 1 hour
   - Acceptable data loss: Up to 1 hour of recent transactions

2. **RTO (Recovery Time Objective):** 15 minutes
   - Target time to restore service: 15 minutes

3. **Backup Frequency:** Every hour
   - Database backups every hour
   - Log backups every 10 minutes
   - Code backups (git) continuous

---

## Recovery Objectives

| Component | RPO | RTO | Priority |
|-----------|-----|-----|----------|
| Database (PostgreSQL) | 1h | 15m | P1 |
| Application (Backend) | N/A | 5m | P1 |
| Frontend | N/A | 5m | P1 |
| Celery Workers | 1h | 10m | P2 |
| Redis Cache | N/A | 2m | P2 |
| Monitoring Stack | N/A | 30m | P3 |

### Priority Levels
- **P1 (Critical):** Service down, users affected, revenue impact
- **P2 (High):** Service degraded, functionality limited
- **P3 (Medium):** Non-critical service down, no user impact

---

## Failure Scenarios

### Scenario 1: Database Unavailable

**Symptoms:**
```
ERROR: could not translate host name "db.example.com" to address: Temporary failure in name resolution
ERROR: (psycopg2.OperationalError) server closed the connection unexpectedly
```

**Root Causes:**
- Network connectivity lost
- PostgreSQL service crashed
- Disk full (ENOSPC)
- Memory exhausted (OOMKilled)
- Connection pool exhausted

**Recovery Steps:**

```bash
# Step 1: Diagnose
ping db.example.com                    # Check network
systemctl status postgresql            # Check service status
df -h | grep /var                      # Check disk space
free -h                                # Check memory

# Step 2: Restart PostgreSQL (if applicable)
systemctl restart postgresql

# Step 3: Verify connectivity
psql -h db.example.com -U truematch -d truematch -c "SELECT 1"

# Step 4: If restart fails, restore from backup
./scripts/restore_database.sh ./backups/truematch_backup_<timestamp>.sql.gz

# Step 5: Restart application
docker-compose restart backend

# Step 6: Verify
curl http://localhost:8000/readyz
```

**Estimated Recovery Time:** 5-15 minutes

---

### Scenario 2: Application Crash

**Symptoms:**
```
HTTP 502: Bad Gateway
Connection refused on port 8000
```

**Root Causes:**
- Out of memory (OOM)
- Unhandled exception
- Database connection pool exhausted
- Infinite loop / deadlock

**Recovery Steps:**

```bash
# Step 1: Check logs
docker-compose logs backend | tail -50

# Step 2: Restart application
docker-compose restart backend

# Step 3: Monitor logs during startup
docker-compose logs -f backend

# Step 4: If still failing, check resources
docker stats

# Step 5: If memory issue, increase limit
# Edit docker-compose.yml and add:
# services:
#   backend:
#     mem_limit: 4g

# Step 6: Deploy previous stable version
git checkout HEAD~1
docker-compose build
docker-compose up -d

# Step 7: Verify
curl http://localhost:8000/health
```

**Estimated Recovery Time:** 2-5 minutes

---

### Scenario 3: Data Corruption

**Symptoms:**
```
Database constraint violations
Corrupted index
Data inconsistency detected
```

**Root Causes:**
- Incomplete transaction
- Hardware failure
- Buggy migration
- Concurrent write conflict

**Recovery Steps:**

```bash
# Step 1: Backup corrupted database (for forensics)
./scripts/backup_database.sh  # Creates timestamped backup

# Step 2: Identify last good backup
ls -lt ./backups/ | head -5

# Step 3: Restore from last good backup
./scripts/restore_database.sh ./backups/truematch_backup_<good_timestamp>.sql.gz

# Step 4: Verify data integrity
psql -U truematch -d truematch << EOF
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM assessments;
SELECT COUNT(*) FROM decisions;
SELECT COUNT(*) FROM audit_trail;
EOF

# Step 5: Run database integrity check
VACUUM ANALYZE;

# Step 6: Review application logs for errors
grep "ERROR\|constraint\|violation" /var/log/truematch/app.log | tail -50

# Step 7: Restart application
docker-compose restart backend

# Step 8: Monitor for issues
docker-compose logs -f backend
```

**Estimated Recovery Time:** 10-30 minutes (depending on backup size)

---

### Scenario 4: Celery Worker Failure

**Symptoms:**
```
CV Analysis tasks stuck in "pending"
Tasks not processing
Queue keeps growing
```

**Root Causes:**
- Worker process crashed
- Redis connection lost
- Task timeout
- Memory exhausted

**Recovery Steps:**

```bash
# Step 1: Check worker status
celery -A app.workers.celery_app inspect active

# Step 2: Check Redis connectivity
redis-cli ping

# Step 3: Restart Celery worker
systemctl restart celery-worker

# Step 4: If Redis is down, restart it
systemctl restart redis-server

# Step 5: Check task queue
redis-cli LLEN celery

# Step 6: If queue is large, process in background
celery -A app.workers.celery_app worker --loglevel=info --concurrency=8

# Step 7: Monitor task completion
watch -n 5 'redis-cli LLEN celery'

# Step 8: If tasks are stuck, purge and restart
celery -A app.workers.celery_app purge  # WARNING: Deletes pending tasks
celery -A app.workers.celery_app worker --loglevel=info
```

**Estimated Recovery Time:** 5-10 minutes

---

### Scenario 5: Complete Data Center Failure

**Symptoms:**
```
All services down
No connectivity
No backups accessible
```

**Root Causes:**
- Data center outage
- Natural disaster
- Major security incident
- Infrastructure meltdown

**Recovery Steps:**

```bash
# Step 1: Activate disaster recovery plan
# - Notify management
# - Activate backup data center
# - Pull latest backups

# Step 2: Verify backup integrity
./scripts/verify_backup.sh ./backups/truematch_backup_<timestamp>.sql.gz

# Step 3: Deploy to alternate infrastructure
# - Provision new servers (AWS, another DC)
# - Install dependencies
# - Configure environment

# Step 4: Restore database
./scripts/restore_database.sh ./backups/truematch_backup_<timestamp>.sql.gz \
  --host=backup-db.example.com

# Step 5: Deploy application
docker-compose -f docker-compose.yml up -d

# Step 6: Verify services
curl http://backup-api.example.com/health

# Step 7: Update DNS to point to backup
# - Update CNAME records
# - Update load balancer
# - Notify users

# Step 8: Monitor closely
docker-compose logs -f

# Step 9: Once primary DC recovered, fail back
# - Repeat steps 4-7 for primary
# - Sync data between backups
# - Switch DNS back
```

**Estimated Recovery Time:** 30-60 minutes (depending on backup size and infrastructure availability)

---

## Recovery Procedures

### Database Recovery Checklist

```bash
# Before recovery
[ ] Stop application
[ ] Stop background workers
[ ] Verify backup exists and is readable
[ ] Notify team

# During recovery
[ ] Run restore script
[ ] Verify restore completed successfully
[ ] Run integrity checks
[ ] Check row counts match expectations

# After recovery
[ ] Start application
[ ] Monitor logs for errors
[ ] Run smoke tests
[ ] Verify user-facing features
[ ] Monitor performance
[ ] Notify stakeholders
```

### Application Recovery Checklist

```bash
# Immediate actions
[ ] Check logs for error cause
[ ] Verify infrastructure (CPU, memory, disk)
[ ] Check external dependencies (DB, Redis, API keys)

# Recovery
[ ] Restart service
[ ] Monitor startup logs
[ ] Verify health checks passing
[ ] Run smoke tests
[ ] Check error rates normalizing

# Post-recovery
[ ] Review error logs
[ ] Document root cause
[ ] Create ticket for permanent fix
[ ] Update runbooks if needed
```

---

## Testing & Drills

### Monthly DR Drills

**Objective:** Verify recovery procedures work

**Schedule:** First Monday of each month, 2 AM UTC

```bash
# Step 1: Create test environment
docker-compose -f docker-compose.test.yml up -d

# Step 2: Simulate database failure
docker-compose stop database

# Step 3: Execute recovery procedure
./scripts/restore_database.sh ./backups/truematch_backup_<timestamp>.sql.gz \
  --target=test_db

# Step 4: Verify recovery
# - Check database is accessible
# - Run integrity checks
# - Verify application works

# Step 5: Document results
# - Time to recovery
# - Issues encountered
# - Improvements needed

# Step 6: Cleanup
docker-compose -f docker-compose.test.yml down
```

### Quarterly RTO Testing

**Objective:** Verify recovery meets 15-minute RTO

**Procedure:**
1. Create isolated test environment
2. Simulate complete failure
3. Execute full recovery (steps 1-8 from Scenario 5)
4. Measure actual time
5. Document results
6. Adjust procedures if RTO exceeded

### Annual Full DR Test

**Objective:** Full end-to-end disaster recovery testing

**Scope:**
- Simulate complete data center failure
- Recover to alternate location
- Verify all services functional
- Run full test suite
- Measure RTO and RPO

---

## Communication Plan

### Incident Severity Levels

| Level | Impact | Communication |
|-------|--------|-----------------|
| **SEV-1** | Service completely down | Immediate notification to all stakeholders |
| **SEV-2** | Major functionality impaired | Notification to team + customers |
| **SEV-3** | Minor issues, users still working | Slack notification to team |

### Notification Checklist

```
[ ] Page on-call engineer
[ ] Update status page
[ ] Notify team lead
[ ] Notify product team
[ ] Notify customers (if applicable)
[ ] Create incident ticket
[ ] Start recording logs for RCA
```

### Status Page Updates

**Template for Investigating:**
```
We are investigating an issue affecting [SERVICE]. 
Current status: [DESCRIPTION]
ETA for update: [TIME]
```

**Template for Recovery:**
```
We are recovering [SERVICE].
Progress: [STEP COMPLETED]
ETA for resolution: [TIME]
```

**Template for Resolved:**
```
[SERVICE] has been recovered.
Total downtime: [DURATION]
Root cause: [BRIEF DESCRIPTION]
Action items: [TICKETS CREATED]
```

---

## Post-Incident Review

### RCA (Root Cause Analysis) Template

```
Date: ____________________
Duration: ____________________
Severity: ____________________

Timeline:
- [Time] Event detected
- [Time] Incident acknowledged
- [Time] Investigation started
- [Time] Fix implemented
- [Time] Service recovered

Root Cause:
[Detailed explanation]

Contributing Factors:
1. [Factor]
2. [Factor]

Impact:
- Users affected: ____
- Data lost: ____
- Revenue impact: ____

Resolution:
[What was done to fix]

Action Items:
- [ ] Fix code issue (ticket #____)
- [ ] Update runbooks
- [ ] Add monitoring/alerting
- [ ] Update procedures
- [ ] Schedule training

Prevention:
[How to prevent in future]
```

---

## Contacts & Escalation

### Emergency Contacts

| Role | Name | Phone | Slack |
|------|------|-------|-------|
| On-Call Engineer | [Name] | [Phone] | @[slack] |
| Engineering Manager | [Name] | [Phone] | @[slack] |
| VP Engineering | [Name] | [Phone] | @[slack] |
| CEO | [Name] | [Phone] | @[slack] |

### External Contacts

| Vendor | Service | Contact | SLA |
|--------|---------|---------|-----|
| AWS | Infrastructure | [Support ticket] | 1 hour |
| Datadog | Monitoring | [Support ticket] | 4 hours |
| PagerDuty | Alerting | [Support ticket] | 1 hour |

### Communication Channels

- **Slack:** #truematch-incidents
- **Email:** incidents@truematch.ai
- **Status Page:** status.truematch.ai
- **War Room:** [Zoom URL]
- **Phone:** [Incident hotline]

---

## Appendix: Quick Reference

### Backup

```bash
# Create backup
./scripts/backup_database.sh

# List recent backups
ls -lt ./backups/ | head -10

# Verify backup
gunzip -t ./backups/truematch_backup_*.sql.gz
```

### Restore

```bash
# Restore to same database
./scripts/restore_database.sh ./backups/truematch_backup_<timestamp>.sql.gz

# Restore to different database
./scripts/restore_database.sh ./backups/truematch_backup_<timestamp>.sql.gz truematch_restored
```

### Health Checks

```bash
# API health
curl http://localhost:8000/health
curl http://localhost:8000/livez
curl http://localhost:8000/readyz

# Database
psql -U truematch -d truematch -c "SELECT 1"

# Redis
redis-cli ping

# Worker
celery -A app.workers.celery_app inspect active
```

### Restart Services

```bash
# All services
docker-compose down && docker-compose up -d

# Just backend
docker-compose restart backend

# Just database
docker-compose restart database

# Just cache
docker-compose restart redis
```

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-06-07 | DevOps Team | Initial version |

---

**Last Tested:** [Date]  
**Next Test Scheduled:** [Date]  
**Document Owner:** [Name]  
**Approval:** [Signature]

