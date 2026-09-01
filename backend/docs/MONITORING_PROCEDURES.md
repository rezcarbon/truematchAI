# MONITORING PROCEDURES

**TrueMatch AI Daily, Weekly, and Monthly Monitoring**  
**Version:** 1.0

---

## DAILY MONITORING CHECKLIST (06:00 UTC)

```bash
#!/bin/bash

echo "=== DAILY PRODUCTION MONITORING ==="
echo "Date: $(date -u)"

# 1. Error Rate Check
ERROR_RATE=$(curl -s https://prometheus.truematch.com/api/v1/query \
  --data-urlencode 'query=rate(truematch_errors_total[1h])' | jq -r '.data.result[0].value[1] // "N/A"')
echo "[1] Error Rate (past 1h): ${ERROR_RATE}%"
[ "$ERROR_RATE" != "N/A" ] && echo "  Expected: < 0.1%, Actual: ${ERROR_RATE}%" || echo "  ⚠ Unable to fetch metric"

# 2. Response Time Check
P99_LATENCY=$(curl -s https://prometheus.truematch.com/api/v1/query \
  --data-urlencode 'query=histogram_quantile(0.99,rate(truematch_request_duration_seconds_bucket[1h]))' | \
  jq -r '.data.result[0].value[1] // "N/A"')
P99_MS=$(echo "scale=0; $P99_LATENCY * 1000" | bc)
echo "[2] Response Time p99 (past 1h): ${P99_MS}ms"

# 3. Pod Status
POD_READY=$(kubectl get pods -n production -l app=truematch-api --field-selector=status.phase=Running -o json | jq '.items | length')
POD_TOTAL=$(kubectl get pods -n production -l app=truematch-api -o json | jq '.items | length')
echo "[3] Pod Status: $POD_READY/$POD_TOTAL running"
[ "$POD_READY" -ne "$POD_TOTAL" ] && echo "  ⚠ Some pods not running"

# 4. Database Check
DB_CONNECTIONS=$(psql -h $DB_HOST -U $DB_USER -d $DB_NAME -t -c "SELECT count(*) FROM pg_stat_activity WHERE datname = '$DB_NAME' AND state = 'active'")
echo "[4] Active DB Connections: $DB_CONNECTIONS"

# 5. Alert Status
ACTIVE_ALERTS=$(curl -s https://alertmanager.truematch.com/api/v1/alerts?silenced=false | jq '.data | length')
echo "[5] Active Alerts: $ACTIVE_ALERTS"
[ "$ACTIVE_ALERTS" -gt 0 ] && echo "  ⚠ Active alerts detected"

# 6. Log Errors
ERROR_COUNT=$(kubectl logs -n production -l app=truematch-api --since=1h 2>/dev/null | grep -c "ERROR")
echo "[6] Errors in Logs (past 1h): $ERROR_COUNT"

# 7. Resource Utilization
AVG_CPU=$(kubectl top pods -n production -l app=truematch-api 2>/dev/null | awk 'NR>1 {sum+=$2; count++} END {if(count>0) printf "%.0f", sum/count; else print "N/A"}')
AVG_MEM=$(kubectl top pods -n production -l app=truematch-api 2>/dev/null | awk 'NR>1 {sum+=$3; count++} END {if(count>0) printf "%.0f", sum/count; else print "N/A"}')
echo "[7] Average Pod Resources - CPU: ${AVG_CPU}m, Memory: ${AVG_MEM}Mi"

# 8. Database Performance
SLOW_QUERIES=$(psql -h $DB_HOST -U $DB_USER -d $DB_NAME -t -c \
  "SELECT COUNT(*) FROM pg_stat_statements WHERE mean_time > 10")
echo "[8] Slow Queries (>10ms): $SLOW_QUERIES"

# 9. Cache Hit Rate
CACHE_HITS=$(redis-cli INFO stats | grep keyspace_hits | awk -F: '{print $2}')
CACHE_MISSES=$(redis-cli INFO stats | grep keyspace_misses | awk -F: '{print $2}')
CACHE_HIT_RATE=$(echo "scale=2; $CACHE_HITS / ($CACHE_HITS + $CACHE_MISSES) * 100" | bc)
echo "[9] Cache Hit Rate: ${CACHE_HIT_RATE}%"

# 10. Final Status
if [ "$ERROR_RATE" != "N/A" ] && [ "$POD_READY" -eq "$POD_TOTAL" ] && [ "$ACTIVE_ALERTS" -eq 0 ]; then
  echo ""
  echo "✓ PRODUCTION HEALTHY"
else
  echo ""
  echo "✗ INVESTIGATE ISSUES"
fi
```

---

## WEEKLY REVIEW CHECKLIST (Every Monday 10:00 UTC)

### Metrics Analysis

```bash
#!/bin/bash

WEEK=$(date -u +%Y-W%V)
echo "=== WEEKLY PRODUCTION REVIEW: $WEEK ==="

# Get 7-day metrics
START_TIME=$(date -u -d '7 days ago' +%s)
END_TIME=$(date -u +%s)

# Error Rate Trend
curl -s https://prometheus.truematch.com/api/v1/query_range \
  --data-urlencode "query=rate(truematch_errors_total[1d])" \
  --data-urlencode "start=$START_TIME" \
  --data-urlencode "end=$END_TIME" \
  --data-urlencode "step=86400" | jq '.data.result' > error_rate_weekly.json

# Response Time Trend
curl -s https://prometheus.truematch.com/api/v1/query_range \
  --data-urlencode "query=histogram_quantile(0.99,rate(truematch_request_duration_seconds_bucket[1d]))" \
  --data-urlencode "start=$START_TIME" \
  --data-urlencode "end=$END_TIME" \
  --data-urlencode "step=86400" | jq '.data.result' > latency_weekly.json

# CPU Trend
kubectl top pods -n production -l app=truematch-api --containers --sort-by=cpu | \
  tee cpu_weekly.txt

# Generate weekly report
cat > weekly_report_$WEEK.md <<'EOF'
# Weekly Production Report

## Key Metrics
- Error Rate: [FETCH_FROM_JSON]
- Response Time p99: [FETCH_FROM_JSON]
- CPU Utilization: [FETCH_FROM_DATA]
- Memory Utilization: [FETCH_FROM_DATA]
- Cache Hit Rate: [FETCH_FROM_REDIS]
- Database Connections: [FETCH_FROM_DB]

## Incidents This Week
- [List any incidents]

## Improvements Made
- [List optimizations]

## Next Week's Focus
- [List priorities]
EOF

echo "Report generated: weekly_report_$WEEK.md"
```

### Team Review Meeting
- Review weekly report
- Discuss any incidents
- Plan optimizations
- Adjust priorities
- Document decisions

---

## MONTHLY REVIEW CHECKLIST (First Monday 10:00 UTC)

### Comprehensive Analysis

```
MONTHLY PRODUCTION ANALYSIS
============================

Period: [MONTH] [YEAR]

1. PERFORMANCE METRICS
   - Uptime: [%] (Target: 99.9%)
   - Error Rate: [%] (Target: < 0.1%)
   - Response Time p99: [ms] (Target: < 300ms)
   - Cache Hit Rate: [%] (Target: > 85%)
   - Throughput: [RPS] (Baseline: 1,100 RPS)

2. INCIDENTS
   - Critical: [N] (0 target)
   - High: [N] (0 target)
   - Medium: [N]
   - Low: [N]
   - MTTR (Mean Time To Resolve): [minutes]

3. DEPLOYMENTS
   - Deployments: [N]
   - Successful: [N]
   - Rollbacks: [N]
   - Issues: [List]

4. CAPACITY ANALYSIS
   - CPU Usage: [%] trend
   - Memory Usage: [%] trend
   - Storage Usage: [%] trend
   - Database Connections: [%] trend
   - Projected Capacity Hit: [N] weeks

5. COST ANALYSIS
   - Compute Cost: $[X]
   - Storage Cost: $[X]
   - Network Cost: $[X]
   - Total: $[X]
   - vs. Budget: [+/- %]
   - vs. Previous Month: [+/- %]

6. SECURITY
   - Vulnerabilities Fixed: [N]
   - Security Incidents: [N]
   - Compliance Status: [Pass/Fail]
   - Penetration Test Results: [TBD/Pass/Fail]

7. OPTIMIZATION COMPLETED
   - Database: [List optimizations]
   - Cache: [List optimizations]
   - API: [List optimizations]
   - Infrastructure: [List optimizations]

8. PLANNED IMPROVEMENTS
   - [Priority 1]: [Action] - ETA: [Date]
   - [Priority 2]: [Action] - ETA: [Date]
   - [Priority 3]: [Action] - ETA: [Date]

9. TEAM FEEDBACK
   - Pain Points: [List]
   - Suggestions: [List]
   - Training Needs: [List]

10. EXECUTIVE SUMMARY
    - Status: [Green/Yellow/Red]
    - Key Achievements: [List 3-5]
    - Key Challenges: [List 3-5]
    - Forecast for Next Month: [Text]
```

---

## ALERT MONITORING DASHBOARD

### Active Alerts View
```
Severity | Alert Name              | Duration | Status
---------|-------------------------|----------|--------
Critical | Error Rate High         | 2m       | Firing
Warning  | CPU Utilization High    | 15m      | Firing
Info     | Deployment In Progress  | 5m       | Firing
```

### Alert Response Procedure
1. **Critical Alert**
   - Immediate notification to on-call
   - Investigate within 2 minutes
   - Escalate if needed
   - Resolve or mitigate within 15 minutes

2. **High Alert**
   - Investigate within 10 minutes
   - Take action within 30 minutes
   - Document resolution

3. **Medium Alert**
   - Investigate within 1 hour
   - Plan resolution
   - Document for optimization

4. **Low Alert**
   - Review during daily check
   - Plan improvement
   - Document learnings

---

## DASHBOARD UPDATES

### Grafana Dashboard Maintenance

```bash
# Create/Update main dashboard
curl -X POST https://grafana.truematch.com/api/dashboards/db \
  -H "Authorization: Bearer $GRAFANA_API_KEY" \
  -H "Content-Type: application/json" \
  -d @production-dashboard.json

# Key panels to maintain:
# 1. Error Rate (current + 30-day trend)
# 2. Response Time (p50, p95, p99)
# 3. Resource Utilization (CPU, Memory, Disk)
# 4. Database Metrics (connections, query time)
# 5. Cache Metrics (hit rate, misses)
# 6. Active Alerts
# 7. Deployment History
# 8. Cost Trend
```

---

## SCHEDULED MAINTENANCE

### Weekly Maintenance (Every Sunday 02:00 UTC)
- [ ] Database VACUUM ANALYZE
- [ ] Log cleanup (archive old logs)
- [ ] Metrics cleanup (remove old metrics)
- [ ] Cache refresh (if needed)
- [ ] Backup verification

### Monthly Maintenance (First Sunday 02:00 UTC)
- [ ] Database statistics update
- [ ] Index optimization
- [ ] Old data archival
- [ ] Full backup verification
- [ ] Disaster recovery test

### Quarterly Maintenance (Jan, Apr, Jul, Oct - Sunday 02:00 UTC)
- [ ] Database optimization
- [ ] Full security audit
- [ ] Capacity planning update
- [ ] Cost review
- [ ] Team training

---

## ESCALATION PROCEDURES

### Escalation Matrix

```
Condition                  Response Time    Escalation Level
=========================================================
Service Unavailable        <5 min           VP Engineering
Error Rate > 5%            <10 min          Eng Manager
Response Time > 1s         <15 min          Eng Lead
CPU > 90%                  <20 min          Ops Lead
Memory > 90%               <20 min          Ops Lead
Database Down              <2 min           DBA + VP Eng

Contact Information:
- On-Call: [Phone/Slack]
- Escalation: [Phone/Slack]
- VP Engineering: [Phone/Email]
```

---

## DOCUMENTATION UPDATES

### Update Schedule
- **Daily:** Alert thresholds (if needed)
- **Weekly:** Procedures (if changed)
- **Monthly:** Baseline metrics (always)
- **Quarterly:** Runbooks (review/update)

### Documentation to Maintain
- [ ] DEPLOYMENT_PROCEDURES.md
- [ ] MONITORING_PROCEDURES.md
- [ ] TROUBLESHOOTING_GUIDE.md
- [ ] RUNBOOKS.md
- [ ] DASHBOARDS.md
- [ ] ALERT_RULES.md

---

**Monitoring Lead:** [Name]  
**On-Call Schedule:** [Link]  
**Escalation Contacts:** See Matrix Above
