# Monthly Alert Game Day Protocol

**Frequency:** First Saturday of every month, 02:00-05:00 UTC  
**Purpose:** Verify all production alerting works end-to-end before a real incident  
**Duration:** 3 hours  
**Participants:** On-call engineer, alert verification team  
**Post-Incident:** Review findings, update thresholds, document improvements

---

## Overview

A "game day" simulates production incidents in a controlled environment to verify that:

1. ✅ Alert rules are configured correctly
2. ✅ Alerts fire within expected timeframes (< 2 minutes)
3. ✅ Notifications reach the right teams (Slack, email, PagerDuty)
4. ✅ Escalation chains work as designed
5. ✅ Recovery procedures complete without data loss
6. ✅ On-call procedures are executable and understood

Game days prevent "alert fatigue" from broken alerts and ensure the team's confidence in the monitoring system.

---

## Pre-Game Day Preparation (Friday Before)

### 1. Schedule & Notify (2 weeks before)
- [ ] Announce game day on team Slack: `@channel Game day scheduled Saturday 02:00-05:00 UTC`
- [ ] Assign roles:
  - **Incident Commander (IC):** Leads the game day, manages timing
  - **Alert Tester:** Triggers each alert scenario
  - **Verifier:** Confirms alerts fired in monitoring system
  - **Responder:** Simulates operational response (e.g., restart service)

### 2. Pre-Checks (Friday Evening)
- [ ] Run alert connectivity test:
  ```bash
  cd backend && python scripts/test_alerts.py
  ```
  Expected output: ✅ All alert systems operational

- [ ] Verify staging/test environment is stable:
  ```bash
  # Check readiness probe
  curl -s http://localhost:8000/readyz | jq .
  # Should return: "status": "ready"
  ```

- [ ] Confirm Slack channel is ready:
  - [ ] Test Slack webhook: `curl -X POST {SLACK_WEBHOOK_URL} -d '{"text":"Test"}'`
  - [ ] Mute/archive #incidents channel to prevent noise
  - [ ] Create temporary channel #gameday-alerts for test alerts

### 3. Notify Stakeholders (Friday)
- [ ] Email: alert-team@truematch.com with schedule and expectations
- [ ] Slack: Post agenda and estimated duration

---

## During Game Day (02:00-05:00 UTC)

### Phase 1: System Connectivity Check (15 min, 02:00-02:15)

**Goal:** Baseline all alert systems are reachable before testing.

```bash
python scripts/test_alerts.py
```

**Checklist:**
- [ ] Slack webhook connected
- [ ] Email SMTP reachable
- [ ] Celery broker online
- [ ] PostgreSQL accessible

**Action on Failure:**
- **If Slack fails:** Update webhook URL; restart any Slack integrations
- **If Database fails:** Page on-call DBA; do not proceed with game day (reschedule)
- **If Celery fails:** Restart Redis; verify broker is healthy

**Expected:** All 4 systems green, ~30 seconds per check

---

### Phase 2: Alert Trigger Scenarios (45 min, 02:15-03:00)

Trigger each alert type in sequence. Each alert should fire within 2 minutes.

#### Scenario 1: High Error Rate (> 5%)

**Trigger Method:**  
Make API endpoint return 500 errors:
```bash
# On production/staging server
curl -X POST http://localhost:8000/api/v1/admin/trigger-error-alert \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"error_rate": 0.06}'
```

**Expected Alert:**
- Slack: ❌ "High Error Rate Alert"
- Metrics: `rate(http_requests_total{status="500"}[5m]) > 0.05`
- **Timing:** Should fire within 2 minutes
- **Verify:**
  - [ ] Alert appears in Slack #incidents
  - [ ] Alert title includes error rate percentage
  - [ ] Timestamp is recent (< 2 min ago)

**Recovery:**
```bash
curl -X POST http://localhost:8000/api/v1/admin/clear-error-alert \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

**Expected:** Slack alert transitions to "Resolved" within 1 minute

---

#### Scenario 2: Database Connection Pool Exhausted

**Trigger Method:**  
Create multiple long-running connections:
```bash
# From database test tool
for i in {1..30}; do
  psql $DATABASE_URL -c "SELECT pg_sleep(300);" &
done
```

**Expected Alert:**
- Slack: 🔴 "Database Connection Pool Exhausted"
- Metrics: `truematch_db_connections_available < 2`
- Readiness probe should fail (503)

**Verify:**
- [ ] Alert in Slack within 2 minutes
- [ ] `curl -s http://localhost:8000/readyz` returns 503
- [ ] `/health` endpoint still returns 200 (basic liveness)

**Recovery:**
```bash
# Kill the test connections
pkill -f "pg_sleep(300)"
```

**Expected:** Pool recovers and alert clears within 1 minute

---

#### Scenario 3: Celery Worker Down

**Trigger Method:**
Stop Celery worker container:
```bash
docker stop truematch-celery-worker
```

**Expected Alert:**
- Slack: 🔴 "Celery Worker Down"
- Metrics: `celery_worker_count == 0`
- Assessment queue should pile up

**Verify:**
- [ ] Alert in Slack within 3 minutes
- [ ] Queue length visible in Celery Flower: `http://localhost:5555`
- [ ] New assessments enqueued but not processed

**Recovery:**
```bash
docker start truematch-celery-worker
```

**Expected:**
- [ ] Worker comes online within 30 seconds
- [ ] Alert clears
- [ ] Queued assessments process within 5 minutes

---

#### Scenario 4: Claude API Quota Exceeded

**Trigger Method:**  
Simulate API key exhaustion:
```bash
curl -X POST http://localhost:8000/api/v1/admin/simulate-claude-quota-error \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

**Expected Alert:**
- Slack: 🔴 "Claude API Quota Exceeded"
- Circuit breaker should OPEN
- Fallback mode activated (return mock data)

**Verify:**
- [ ] Alert in Slack within 2 minutes
- [ ] System returns mock assessments gracefully
- [ ] Logs show circuit breaker state = OPEN

**Recovery:**
Reset simulated error:
```bash
curl -X POST http://localhost:8000/api/v1/admin/clear-claude-error \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

**Expected:** Circuit breaker transitions to HALF_OPEN → CLOSED within 1-2 minutes

---

#### Scenario 5: Redis Connection Lost

**Trigger Method:**  
Temporarily block Redis network:
```bash
# On network interface
sudo pfctl -f /etc/pf.conf  # On macOS, blocks Redis port
# Or on Linux:
sudo iptables -A OUTPUT -p tcp --dport 6379 -j DROP
```

**Expected Alert:**
- Slack: 🔴 "Redis Connection Lost"
- Metrics: `redis_connection_failures_total` increments
- Rate limiting fails open (allows requests)

**Verify:**
- [ ] Alert in Slack within 2 minutes
- [ ] API still responds (degraded gracefully)
- [ ] Logs show connection pool exhaustion

**Recovery:**
```bash
# Restore network
sudo iptables -D OUTPUT -p tcp --dport 6379 -j DROP
```

**Expected:** Redis reconnects automatically; alert clears

---

### Phase 3: Recovery & Escalation (30 min, 03:00-03:30)

**Goal:** Verify incident response procedures work end-to-end.

1. **Simulate PagerDuty Escalation:**
   - [ ] Manually trigger PagerDuty incident (high-severity alert)
   - [ ] Verify on-call engineer is paged
   - [ ] Confirm they receive notification within 1 minute
   - [ ] Team acknowledges incident
   - [ ] Resolve incident in PagerDuty

2. **Verify Human Escalation:**
   - [ ] If 3 alerts fire simultaneously, verify dedicated channel is created
   - [ ] Verify IC is notified (@incident-commander)
   - [ ] Verify status page is updated (if applicable)

3. **Test Communication:**
   - [ ] Post status update to #incidents: "Game day in progress, testing alert response"
   - [ ] Verify team can read updates
   - [ ] Confirm no customer-facing systems were affected

---

### Phase 4: RCA & Documentation (30 min, 03:30-04:00)

**During:**
- Record findings in `/tmp/gameday-notes-YYYY-MM-DD.txt`
- For each alert:
  - Did it fire? (Yes/No)
  - How long did it take? (timing)
  - Was the threshold appropriate?
  - Any false positives?
  - Any missed scenarios?

**After Game Day (within 24 hours):**

1. **Publish Game Day Report:**
   - File: `docs/GAME_DAY_REPORTS.md`
   - Template:
     ```markdown
     ## Game Day Report - {DATE}
     
     **Status:** ✅ All systems functional | ⚠️ {N} issues found | ❌ Critical failure
     
     ### Summary
     Tested 5 alert scenarios; all fired correctly within target timeframes.
     
     ### Results
     
     | Alert | Fired? | Latency | Status |
     |-------|--------|---------|--------|
     | High Error Rate | ✅ | 1m 23s | OK |
     | DB Pool Exhausted | ✅ | 2m 10s | SLOW (threshold?) |
     | Celery Down | ✅ | 2m 45s | OK |
     | Claude Quota | ✅ | 1m 50s | OK |
     | Redis Lost | ❌ | N/A | FAILED |
     
     ### Findings
     - Redis alert does not fire (check Prometheus config)
     - High error rate latency is acceptable but close to SLA (2 min target)
     - Celery worker takes 2m 45s to be detected; consider faster heartbeat
     
     ### Actions
     - [ ] Fix Redis alert rule in monitoring/alerts.yml
     - [ ] Consider lowering Celery worker heartbeat from 60s to 30s
     - [ ] Update error rate threshold docs (currently 2 min, very consistent)
     
     ### Next Game Day
     Scheduled for {NEXT_MONTH} at same time. Include these fixes.
     ```

2. **Update Alert Thresholds:**
   - If any alert took > 2 minutes: review Prometheus scrape intervals
   - If any alert was noisy: increase threshold by 10-20%
   - If any alert missed a real problem: lower threshold by 10-20%

3. **Update Runbooks:**
   - Add notes from actual recovery procedures used
   - Update estimated MTTR (Mean Time To Recovery)
   - Add any workarounds discovered

4. **Team Retrospective:**
   - 30-minute sync with team
   - Review game day findings
   - Discuss lessons learned
   - Plan next month's test (same time, or different scenario?)

---

## Post-Game Day (Next 24 hours)

### Verification Checklist

- [ ] All alerts that fired are documented with latencies
- [ ] All alerts that didn't fire have investigation tickets
- [ ] Findings reviewed with team
- [ ] Thresholds updated in monitoring/alerts.yml
- [ ] Runbooks updated with new MTTRs
- [ ] Game day report published to docs/
- [ ] Next month's game day scheduled on calendar

### Create Tickets for Improvements

If any alert failed or was slow:

```
Title: [GameDay] Fix {Alert Name} - {Finding}
Description:
Severity: {P0|P1|P2}
Timeline: Fix before next game day

In the {DATE} game day:
- Alert: {Alert Name}
- Issue: {What failed or was slow}
- Impact: {How long until we notice in production?}
- Fix: {Proposed solution}

Testing criteria:
- [ ] Alerting test passes (test_alerts.py)
- [ ] Alert fires within 2 minutes in game day scenario
```

---

## Alert Checklist Template

Print and fill this out during game day:

```
ALERT CHECKLIST - {DATE}
=====================================================

[ ] Phase 1: System Connectivity
  - Slack: ✅ ❌ ⚠️
  - Email: ✅ ❌ ⚠️
  - Celery: ✅ ❌ ⚠️
  - Database: ✅ ❌ ⚠️

[ ] Phase 2: Alert Scenarios
  1. High Error Rate
     - Fired: ✅ ❌ Latency: ___ min
  2. DB Pool Exhausted
     - Fired: ✅ ❌ Latency: ___ min
  3. Celery Worker Down
     - Fired: ✅ ❌ Latency: ___ min
  4. Claude Quota
     - Fired: ✅ ❌ Latency: ___ min
  5. Redis Lost
     - Fired: ✅ ❌ Latency: ___ min

[ ] Phase 3: Recovery
  - PagerDuty escalation: ✅ ❌
  - Status page updated: ✅ ❌
  - Team acknowledged: ✅ ❌

[ ] Phase 4: Documentation
  - Issues logged: ___ tickets
  - Thresholds updated: ✅ ❌
  - Report published: ✅ ❌

OVERALL: ✅ PASS | ⚠️ ISSUES | ❌ FAIL
```

---

## Troubleshooting During Game Day

### Alert Won't Fire

**Check:**
1. Is the test scenario actually happening?
   ```bash
   # Verify metric is being recorded
   curl -s http://localhost:9090/api/v1/query?query=http_requests_total | jq
   ```

2. Is the alert rule enabled in Prometheus?
   ```bash
   # Check rule file
   grep -A 5 "alert_name" monitoring/alerts.yml
   ```

3. Is Prometheus scraping the right targets?
   ```bash
   # Prometheus UI at http://localhost:9090
   # Status → Targets → Check last scrape time
   ```

### Alert Fires But Message is Malformed

- Check AlertManager config: `monitoring/alertmanager.yml`
- Verify Slack webhook URL in environment
- Test webhook directly:
  ```bash
  curl -X POST $SLACK_WEBHOOK_URL \
    -H 'Content-Type: application/json' \
    -d '{"text":"Test message"}'
  ```

### Timing is Very Slow (> 5 minutes)

- Increase Prometheus scrape frequency (default 15s)
- Check if alert has `for: 5m` clause (add `for: 1m` for game day)
- Reduce alertmanager `group_wait` (default 10s)

---

## FAQ

**Q: Can we do game days during business hours?**  
A: We use 02:00 UTC (off-hours in US) to simulate realistic on-call scenarios. Business-hours game days can be done monthly; off-hours is standard for critical systems.

**Q: What if an alert fails during game day?**  
A: Create a P1 ticket and disable that alert in production immediately. The system degrades gracefully; redundant alerts should catch the issue.

**Q: Can I skip a month's game day?**  
A: Not recommended. Monthly game days catch configuration drift and team turnover. Skip one, and your next incident response will be your first real test.

**Q: How do we prevent false alerts from reaching customers?**  
A: All game day alerts post to #gameday-alerts (internal) and use a test PagerDuty service (if applicable). Status pages are never updated during game days.

---

## Next Game Day

- **Date:** {NEXT_MONTH} 1st Saturday
- **Time:** 02:00-05:00 UTC
- **Incident Commander:** {NAME}
- **Alert Tester:** {NAME}
- **Verifier:** {NAME}

Calendar reminder: `https://calendar.google.com/...` (add link to team calendar)
