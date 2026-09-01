# TrueMatch AI Incident Response Guide
## Phase 3: Incident Management & Response Procedures

**Version:** 1.0  
**Last Updated:** 2026-07-19  
**Owner:** On-Call Engineer  
**Severity Levels:** Critical, High, Medium, Low

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Incident Severity Levels](#incident-severity-levels)
3. [Incident Response Process](#incident-response-process)
4. [Escalation Procedures](#escalation-procedures)
5. [Communication Protocol](#communication-protocol)
6. [Investigation & Troubleshooting](#investigation--troubleshooting)
7. [Recovery Procedures](#recovery-procedures)
8. [Post-Incident Review](#post-incident-review)

---

## Quick Start

### When Something Breaks

**Step 1: Declare an Incident (< 1 minute)**
```bash
# Create incident ticket
# Post to #incidents Slack channel
# Start war room call
# Page on-call team
```

**Step 2: Stabilize (1-5 minutes)**
```bash
# Get situational awareness
kubectl get all -n truematch-prod

# Check logs for errors
kubectl logs deployment/api -n truematch-prod --tail=100 | grep ERROR

# Check metrics
# Visit https://grafana.truematch.ai
```

**Step 3: Communicate (ongoing)**
```
- Post updates every 5 minutes
- Set expectation for resolution time
- Escalate if needed
```

**Step 4: Resolve (varies)**
```
- Apply fix
- Verify resolution
- Document what happened
```

**Step 5: Review**
```
- Post-incident meeting (24-48 hours)
- Root cause analysis
- Action items
```

---

## Incident Severity Levels

### Severity 1 - CRITICAL
**Customer Impact:** Service completely unavailable  
**Response Time SLA:** 15 minutes  
**Escalation:** Immediate (CEO, VP Eng)

**Examples:**
- Production database down
- All API instances down
- Data loss or corruption
- Security breach

**Actions:**
- Page entire on-call team
- Open war room immediately
- All hands on deck
- CEO notified

```bash
# Declare incident
pagerduty trigger --service-id S1234 \
  --title "CRITICAL: Production API Down" \
  --urgency high

# Slack notification
# @channel CRITICAL INCIDENT: Production API unavailable
```

### Severity 2 - HIGH
**Customer Impact:** Partial service degradation  
**Response Time SLA:** 30 minutes  
**Escalation:** After 15 minutes if unresolved

**Examples:**
- High error rate (>5%)
- High latency (p99 > 2s)
- 1-2 deployments down
- Worker queue backed up

**Actions:**
- Page on-call engineer + backup
- Open war room
- VP Eng notified
- Begin investigation

```bash
# Declare incident
pagerduty trigger --service-id S1234 \
  --title "HIGH: API Error Rate 8%" \
  --urgency high
```

### Severity 3 - MEDIUM
**Customer Impact:** Minor degradation  
**Response Time SLA:** 1 hour  
**Escalation:** After 30 minutes if unresolved

**Examples:**
- Error rate 1-5%
- Latency elevated but acceptable
- Non-critical feature broken
- Performance degradation

**Actions:**
- Alert on-call engineer
- Investigate
- Create ticket
- Monitor closely

### Severity 4 - LOW
**Customer Impact:** No customer impact  
**Response Time SLA:** 8 hours  
**Escalation:** None required

**Examples:**
- Test environment issues
- Non-production alerts
- Documentation issues
- Minor bugs

---

## Incident Response Process

### Phase 1: Detection & Alert (0-5 min)

#### Monitoring Triggers Incident
1. Alert fires from Prometheus/PagerDuty
2. On-call engineer receives notification
3. Engineer logs into systems

#### Manual Detection
1. Customer reports issue
2. Team member notices in chat/monitor
3. Escalate via on-call rotation

#### Detection Confirmation
```bash
# Confirm the issue
curl https://api.truematch.ai/healthz  # Check health

# Check metrics
# Verify issue in Grafana dashboard

# Assign severity level
# Based on impact and scope
```

### Phase 2: Initial Response (5-15 min)

#### 2.1 Declare Incident
```bash
# Create incident ticket
jira create --project INC --summary "Production API Down"

# Post to Slack
# Notify stakeholders
```

#### 2.2 Activate War Room
```bash
# Start video call
# Add links to dashboard, logs, etc.
# Designate roles:
#   - Incident Commander
#   - Technical Lead
#   - Communicator
```

#### 2.3 Initial Investigation
```bash
# Check service status
kubectl get pods -n truematch-prod
kubectl get svc -n truematch-prod

# Check recent events
kubectl get events -n truematch-prod | head -20

# Check recent deployments
kubectl rollout history deployment/api -n truematch-prod
```

#### 2.4 Notification
- Post to Slack `#incidents` channel
- Send email to stakeholders
- Update status page
- Notify customers (if applicable)

### Phase 3: Investigation (15-60 min)

#### 3.1 Gather Information
```bash
# Application logs
kubectl logs deployment/api -n truematch-prod --tail=200

# Database status
kubectl exec -it postgres-prod-0 -- psql -c "SELECT version();"

# Metrics
# Check Prometheus for recent changes

# External services
# Verify dependencies are up
```

#### 3.2 Identify Root Cause
Use the decision tree in [Investigation & Troubleshooting](#investigation--troubleshooting)

#### 3.3 Document Timeline
```
HH:MM - Alert fired, on-call paged
HH:MM - Initial investigation started
HH:MM - Root cause identified
HH:MM - Fix applied
HH:MM - Service recovered
```

### Phase 4: Recovery (varies)

#### 4.1 Implement Fix
Depending on root cause:
- Restart pods
- Rollback deployment
- Fix database issue
- Increase resources
- etc.

#### 4.2 Verify Fix
```bash
# Service health
curl https://api.truematch.ai/healthz

# Metrics
# Error rate back to normal
# Latency acceptable
# Resource usage stable

# Logs
# No new errors
# Normal operation
```

#### 4.3 Communication Update
- Post recovery update to Slack
- Update status page
- Email stakeholders
- Set expectation for post-incident review

### Phase 5: Post-Incident (24-48 hours)

#### 5.1 Collect Information
- Review incident timeline
- Gather logs and metrics
- Identify root cause
- List contributing factors

#### 5.2 Schedule Review Meeting
- Participants: tech lead, on-call, deployer (if applicable), ops
- Time: 1-2 hours
- No blame, focus on process improvement

#### 5.3 Create Action Items
- Fix root cause (if coding change needed)
- Improve monitoring
- Update runbooks
- Improve processes

#### 5.4 Document & Communicate
- Share RCA to team
- Add findings to knowledge base
- Close related tickets

---

## Escalation Procedures

### When to Escalate

**Escalate to Next Level If:**
- Issue not resolved within SLA
- Issue severity increases
- Need additional expertise
- Customer/executive pressure

### Escalation Chain

```
Level 1: On-Call Engineer
  ↓ (unresolved after SLA)
Level 2: Tech Lead + Database Admin
  ↓ (unresolved after SLA)
Level 3: VP Engineering + Head of Operations
  ↓ (unresolved after SLA)
Level 4: CTO + VP Product
```

### Escalation Communication

```bash
# When escalating
# 1. Summarize what you've tried
# 2. Explain why you need escalation
# 3. Provide all context (logs, metrics)
# 4. Set expectation for resolution time

# Example
"@on-call-manager: Escalating Severity 2 incident - API latency
 high. Tried: restarting pods, checking DB. Need DBA to investigate
 slow queries. Metrics attached."
```

---

## Communication Protocol

### Internal Communication

#### Slack Channels
- `#incidents` - All incident discussion
- `#status-page` - Public status updates
- `#operations` - Ops-specific discussion
- Direct message - Individual questions

#### Message Template
```
[HH:MM] SEVERITY [STATUS] 

Issue: [Brief description]
Impact: [What's affected]
Status: [What we're doing about it]
ETA: [Estimated resolution time]

Dashboard: [Link]
Logs: [Link]
```

#### Update Frequency
- Critical: Every 5 minutes
- High: Every 10 minutes
- Medium: Every 30 minutes
- Low: As needed

### External Communication

#### Status Page Update
- Always update for Critical/High
- Use pre-written templates
- Set realistic ETAs
- Don't promise specific times if unsure

#### Email to Customers
- Professional, clear language
- Acknowledge impact
- Explain what we're doing
- Provide realistic timeline
- Offer workarounds if any

#### Example Email
```
Subject: Service Incident - TrueMatch API

Dear Customers,

We are currently experiencing elevated error rates on the TrueMatch
API. Our team is investigating the root cause.

Impact:
- Some API requests may fail
- Matching operations may be delayed
- Access to dashboard may be intermittent

Action:
- Our engineering team is actively investigating
- We expect to have more information within 30 minutes

Workaround:
- If possible, retry failed requests
- Contact support@truematch.ai for urgent assistance

We apologize for the inconvenience. We'll send another update
shortly.

Best regards,
TrueMatch Operations Team
```

---

## Investigation & Troubleshooting

### Decision Tree

```
Is the service responding at all?
├─ NO: Pods running?
│  ├─ NO: Rollout status / Events / Recent deployment?
│  │  └─ Fix: Rollback or fix and redeploy
│  └─ YES: Logs show startup errors?
│     ├─ YES: Database connection error?
│     │  └─ Fix: Check database
│     └─ NO: Other startup error
│        └─ Fix: Check logs for specifics
│
└─ YES: High error rate?
   ├─ YES: Type of error?
   │  ├─ 5xx: Application error
   │  │  └─ Check: Logs, database, dependent services
   │  └─ 4xx: Client error (usually OK)
   │     └─ Check: Client-side issue
   └─ NO: High latency?
      ├─ YES: Database slow?
      │  ├─ YES: Slow queries, missing index?
      │  │  └─ Fix: Optimize query or add index
      │  └─ NO: Resource contention?
      │     └─ Fix: Scale up or optimize
      └─ NO: User reports issues?
         └─ Might be intermittent, monitor closely
```

### Common Issues & Quick Fixes

#### Issue: All Pods Crashing

**Diagnosis:**
```bash
kubectl describe pod <pod-name> -n truematch-prod
kubectl logs <pod-name> -n truematch-prod
```

**Common Causes & Fixes:**
1. **Database connection failed**
   - Check connection string
   - Restart database pod
   - Check network connectivity

2. **Out of memory**
   - Increase memory limits
   - Restart pods
   - Look for memory leak

3. **Missing environment variable**
   - Check ConfigMap
   - Check Secret
   - Update and redeploy

**Quick Fix:**
```bash
# Rollback to previous version
kubectl rollout undo deployment/api -n truematch-prod

# Or restart if transient
kubectl rollout restart deployment/api -n truematch-prod
```

#### Issue: High Error Rate

**Diagnosis:**
```bash
# What's the error?
kubectl logs deployment/api -n truematch-prod | grep ERROR | head -20

# Is it all endpoints or specific ones?
curl https://prometheus.truematch.ai/graph \
  -d 'query=rate(http_requests_total{status=~"5.."}[1m]) by (path)'

# Check database
kubectl exec -it postgres-prod-0 -- psql -c "SELECT 1;"
```

**Common Causes & Fixes:**
1. **Database overloaded**
   - Check connection count
   - Check slow queries
   - Optimize or add caching

2. **Dependency down**
   - Check Redis
   - Check external APIs
   - Enable fallback logic

3. **Bug in code**
   - Rollback deployment
   - Fix bug and redeploy

#### Issue: High Latency

**Diagnosis:**
```bash
# Check latency by endpoint
curl https://prometheus.truematch.ai/graph \
  -d 'query=histogram_quantile(0.95,rate(http_request_duration_seconds_bucket[5m])) by (path)'

# Check database
PGPASSWORD=$DB_PASSWORD psql -h postgres-prod -U $DB_USER -d truematch_prod \
  -c "SELECT query, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 5;"

# Check resources
kubectl top pods -n truematch-prod
```

**Common Causes & Fixes:**
1. **Slow database query**
   - Run EXPLAIN ANALYZE
   - Add index if beneficial
   - Optimize query

2. **Resource contention**
   - Scale up replicas
   - Add more resources
   - Optimize code

3. **Network latency**
   - Check network between app and database
   - Look for packet loss

---

## Recovery Procedures

### Rollback Deployment

```bash
# Check rollout history
kubectl rollout history deployment/api -n truematch-prod

# Rollback to previous revision
kubectl rollout undo deployment/api -n truematch-prod

# Verify rollback
kubectl rollout status deployment/api -n truematch-prod --timeout=10m

# Check if recovered
curl https://api.truematch.ai/healthz
```

### Restart Services

```bash
# Restart specific deployment
kubectl rollout restart deployment/api -n truematch-prod

# Restart all deployments
kubectl rollout restart deployments -n truematch-prod

# Verify restart
kubectl get pods -n truematch-prod
```

### Scale Up Resources

```bash
# Increase replicas
kubectl scale deployment/api --replicas=5 -n truematch-prod

# Check if helping
kubectl top pods -n truematch-prod
kubectl logs deployment/api -n truematch-prod | grep ERROR | wc -l
```

### Failover to Standby

```bash
# If primary database down, failover to replica
# Contact database team for procedure

# If primary region down, failover to backup region
# Contact infrastructure team
```

### Restore from Backup

**WARNING: Use only for data corruption/loss**

```bash
# Get list of backups
aws s3 ls s3://truematch-backups/

# Restore specific backup
# See DISASTER_RECOVERY.md for full procedure
```

---

## Post-Incident Review

### Review Template

```markdown
# Incident Review: [Issue Title]

## Incident Details
- **Date:** YYYY-MM-DD
- **Duration:** HH:MM
- **Severity:** 1/2/3/4
- **Impact:** [What was affected]

## Timeline
[List of events with timestamps]

## Root Cause Analysis
[Why did this happen?]

## Contributing Factors
[What made it worse?]

## Resolution
[How was it fixed?]

## Action Items
1. [Fix in code/infrastructure]
2. [Improve monitoring]
3. [Update documentation]
4. [Team training]

## Lessons Learned
[What can we do better?]

## Follow-up
[Who will do what by when?]
```

### Required Attendees
- Incident Commander
- Technical Lead
- On-Call Engineer
- Affected Service Owner
- Operations Lead

### Success Criteria
- Root cause identified
- Fix implemented
- Action items assigned
- Documented in knowledge base

---

## Incident Metrics

Track these metrics to improve response time:

| Metric | Target | Current |
|--------|--------|---------|
| MTTD (Mean Time to Detect) | < 5 min | ____ |
| MTTR (Mean Time to Resolve) | < 30 min | ____ |
| Escalation Rate | < 20% | ____ |
| Repeat Incidents | 0% | ____ |

---

## Useful Commands

```bash
# Service status
kubectl get all -n truematch-prod

# Pod logs
kubectl logs deployment/api -n truematch-prod -f

# Pod events
kubectl describe pod <pod-name> -n truematch-prod

# Metrics query
curl 'http://prometheus:9090/api/v1/query?query=up'

# Database connection test
PGPASSWORD=xxx psql -h postgres-prod -U user -d db -c "SELECT 1;"

# Network connectivity
kubectl run debug --image=curlimages/curl -it --rm -- curl <target-url>
```

---

## Related Documents

- [Operations Runbook](./OPERATIONS_RUNBOOK.md)
- [Production Checklist](./PRODUCTION_CHECKLIST.md)
- [Disaster Recovery](./DISASTER_RECOVERY.md)

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-07-19 | DevOps Team | Initial creation |

---

**Last Review:** 2026-07-19  
**Next Review:** 2026-10-19  
**Owner:** On-Call Rotation Lead
