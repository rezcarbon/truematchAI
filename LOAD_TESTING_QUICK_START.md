# TrueMatch Load Testing Quick Start Guide

**Last Updated:** June 7, 2026

Quick reference for running load tests against TrueMatch API.

---

## Installation (5 minutes)

```bash
# Install all load testing tools
make install-tools

# Or install individually:
pip install locust==2.15.1
brew install k6
brew install jmeter
```

## Setup (2 minutes)

```bash
# Prepare test environment
make setup-test-env

# Start test infrastructure (Prometheus, Grafana)
make docker-compose-up
```

---

## Running Tests

### Option 1: Locust (Web UI - Recommended for Learning)

```bash
# Start Locust interactive
make load-test-locust

# Then open: http://localhost:8089
# - Click "Start Swarming"
# - Set Users: 100
# - Set Spawn Rate: 10 users/sec
# - Watch metrics in real-time
```

**Web UI Features:**
- Start/stop tests mid-run
- Adjust users and spawn rate live
- View response time distribution
- Download CSV results

### Option 2: k6 (Scripted - Recommended for CI/CD)

```bash
# Run automated k6 test
make load-test-k6

# Custom parameters
k6 run \
  -e API_URL=http://localhost:8000 \
  --vus 100 \
  --duration 5m \
  load-tests/k6-script.js
```

**k6 Advantages:**
- Scripted and reproducible
- Easy CI/CD integration
- JSON output for analysis
- Cloud integration available

### Option 3: Apache JMeter (GUI - Advanced)

```bash
# Run JMeter test plan
make load-test-jmeter

# Or open GUI
jmeter -t load-tests/jmeter-plan.jmx
```

---

## Pre-built Test Profiles

### 🔍 Quick Smoke Test (2 minutes)
```bash
make smoke-test
```
- 5 concurrent users
- 2 minute duration
- Validates setup and baseline metrics
- **Use Before:** Production deployments

### 📊 Establish Baseline (5 minutes)
```bash
make baseline-test
```
- 1 concurrent user
- 5 minute duration
- Creates reference for future tests
- **Use When:** Setting up new environment

### 🔥 Stress Test (30+ minutes)
```bash
make stress-test
```
- Ramps up to 1000 users
- Tests system limits
- Find breaking point
- **Use When:** Planning capacity upgrades

### ⚡ Spike Test (10 minutes)
```bash
make spike-test
```
- Sudden 5x load increase
- Tests resilience
- Autoscaling response time
- **Use When:** Testing auto-recovery

### 😴 Soak Test (24 hours)
```bash
nohup make soak-test &
```
- 50 concurrent users (sustained)
- 24 hour duration
- Detects memory leaks
- **Use When:** Before major release

### 📈 Capacity Planning (20 minutes)
```bash
make capacity-planning
```
- Tests at 100, 250, 500, 1000 users
- Identifies scaling needs
- **Use When:** Quarterly review

---

## Understanding Results

### Key Metrics

| Metric | Good | OK | Bad |
|--------|------|-----|-----|
| **Response Time (Avg)** | <100ms | 100-300ms | >500ms |
| **P95 Latency** | <300ms | 300-1000ms | >1000ms |
| **P99 Latency** | <1000ms | 1-2000ms | >2000ms |
| **Error Rate** | <0.1% | 0.1-1% | >1% |
| **Throughput** | >1000 RPS | 500-1000 RPS | <500 RPS |
| **CPU** | <50% | 50-80% | >80% |
| **Memory** | <50% | 50-80% | >80% |

### Analyzing Output

**Locust CSV Results:**
```
Name                    Method  Count  Mean    Min   Max   Median  Requests/sec
/api/v1/assessments     GET     1200   95      12    450   85      15.2
/api/v1/assessments     POST    400    180     50    2100  150     5.1
/api/v1/positions       GET     1500   75      8     350   70      19.0
[Total]                         3100   110     8     2100  95       39.3
```

**k6 Summary:**
```
http_req_duration..........: avg=110ms, p(95)=350ms, p(99)=950ms
http_req_failed............: 0.4%
http_reqs..................: 3100 total
```

---

## Monitoring During Tests

### Real-time Metrics

```bash
# Watch system performance
make monitor

# In another terminal, watch API logs
kubectl logs -f -n truematch deployment/truematch-api

# Watch database performance
kubectl exec -n truematch postgres-0 -- \
  psql -U postgres -c "SELECT datname, numbackends FROM pg_stat_database;"
```

### Grafana Dashboards

1. Open http://localhost:3000
2. Username: admin / Password: admin
3. Select "Load Test" dashboard
4. Watch in real-time

---

## Common Issues & Solutions

### API Not Responding

```bash
# Check if API is running
curl http://localhost:8000/health

# Check pod status
kubectl get pods -n truematch

# View API logs
kubectl logs -n truematch deployment/truematch-api --tail=50
```

### High Error Rate During Test

```bash
# Check for errors
kubectl logs -n truematch deployment/truematch-api | grep -i error | tail -20

# Check database
kubectl exec -n truematch postgres-0 -- \
  psql -U postgres -c "SELECT COUNT(*) FROM pg_stat_activity;"

# Check Redis
kubectl exec -n truematch redis-0 -- redis-cli INFO memory
```

### Test Hangs or Stalls

```bash
# Stop all tests
make stop-tests

# Kill any stuck processes
pkill -9 locust
pkill -9 k6
pkill -9 jmeter
```

### "Connection Refused" Errors

```bash
# Verify API is reachable
curl -v http://localhost:8000/health

# Check if API service exists
kubectl get svc -n truematch

# Port forward if remote
kubectl port-forward -n truematch svc/truematch-api 8000:8000
```

---

## Comparing Results

### Find Regressions

```bash
# Compare with baseline
ls -la load-test-results/
# Look for changes in:
# - Average response time (should stay same)
# - P95/P99 latency (should stay same)
# - Error rate (should stay low)
# - Throughput (should stay high)
```

### Generate Trend Report

```bash
# Create comparison spreadsheet
# Columns: Date, Users, Avg Latency, P95, P99, Errors, RPS
# Add results over time
# Create chart to see trends
```

---

## Test Scenarios Explained

### Recruiter Workflow (50% of traffic)
```
1. Login as recruiter
2. List positions (browse)
3. View position details
4. List assessments for position
5. View assessment scores/details
6. Check approval queue
7. Approve or reject candidate
```

**Why:** Most common recruiter behavior

### Candidate Workflow (40% of traffic)
```
1. Login as candidate
2. Browse available positions
3. View job posting details
4. Submit assessment/resume
5. Check application status
6. Receive notification
```

**Why:** High volume, primary business flow

### Operator Workflow (10% of traffic)
```
1. Login as operator
2. Check pending approvals
3. Review candidate profile
4. Approve candidate
5. Reject candidate
6. Send notification
```

**Why:** Lower volume, critical workflow

---

## Production Deployment Readiness

### Pre-Deployment Load Test Checklist

- [ ] Run baseline test on staging
- [ ] Compare with current production baseline
- [ ] Run spike test (5x load)
- [ ] Monitor error rate (<0.5% threshold)
- [ ] Check response time degradation (<50% increase)
- [ ] Verify database can handle peak load
- [ ] Verify cache efficiency (>90% hit rate)
- [ ] Review scaling policies
- [ ] Test rollback procedure
- [ ] Brief on-call team on expected load patterns

### Baseline Metrics to Capture

Create a baseline before every major deployment:

```bash
# Smoke test establishes baseline
make baseline-test

# Save results with version tag
cp load-test-results/results_* \
   load-test-results/baseline_v1.2.0_$(date +%s).csv
```

---

## Automation & CI/CD

### GitHub Actions Example

```yaml
name: Load Test
on: [pull_request]
jobs:
  load-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Install tools
        run: make install-tools
      - name: Run smoke test
        run: make smoke-test
      - name: Upload results
        uses: actions/upload-artifact@v2
        with:
          name: load-test-results
          path: load-test-results/
```

### Scheduled Nightly Tests

```bash
# Add to crontab
0 2 * * * cd /home/user/truematch && \
  make baseline-test >> /var/log/load-tests.log 2>&1

# Run weekly stress test
0 3 * * 0 cd /home/user/truematch && \
  make capacity-planning >> /var/log/load-tests.log 2>&1
```

---

## Advanced: Custom Scenarios

### Create Custom User Behavior

Edit `load-tests/locustfile.py`:

```python
class MyCustomUser(AuthenticatedUser):
    wait_time = between(1, 3)
    
    @task(3)
    def custom_workflow(self):
        # Your custom workflow here
        self.client.get("/api/v1/assessments")
        time.sleep(1)
        self.client.post("/api/v1/assessments/123/approve", json={...})
```

Run with:
```bash
locust -f load-tests/locustfile.py \
  --host=http://localhost:8000 \
  --tags my_custom
```

### Create Custom k6 Test

Edit `load-tests/k6-script.js` or create new:

```javascript
import http from 'k6/http'
import { check } from 'k6'

export const options = {
  vus: 10,
  duration: '5m',
  thresholds: {
    http_req_duration: ['p(95)<500'],
    http_req_failed: ['rate<0.01'],
  },
}

export default function() {
  // Your custom test
  const res = http.get('http://localhost:8000/api/v1/assessments')
  check(res, {
    'status is 200': (r) => r.status === 200,
  })
}
```

---

## Resources

### Documentation
- **Locust Docs:** https://docs.locust.io/
- **k6 Docs:** https://k6.io/docs/
- **JMeter Docs:** https://jmeter.apache.org/usermanual/

### Performance Testing Best Practices
- Load test regularly (weekly/monthly)
- Test before major releases
- Establish baselines for comparison
- Document results and trends
- Automate tests in CI/CD

### Tools
- **Grafana:** Real-time dashboards (http://localhost:3000)
- **Prometheus:** Metrics collection (http://localhost:9090)
- **Docker:** Container management for test infrastructure

---

## Troubleshooting

### "Permission denied" when running Makefile

```bash
chmod +x Makefile
# Or use 'bash make target'
```

### Locust web UI not opening

```bash
# Check if Locust is running
lsof -i :8089

# Manually open in browser
http://127.0.0.1:8089
```

### k6 threshold failures

If test fails with "thresholds violated":
- Response time too high → optimize slow endpoints
- Error rate too high → debug API errors
- Increase thresholds if acceptable

```bash
# Run with higher thresholds (temporary)
k6 run --threshold 'http_req_duration p(95)<1000' load-tests/k6-script.js
```

### Results file not created

```bash
# Check directory exists
mkdir -p load-test-results

# Check permissions
ls -la load-test-results/

# Run test again
make load-test-locust-headless
```

---

## Next Steps

1. **Run baseline test first:** `make baseline-test`
2. **Run smoke test weekly:** `make smoke-test`
3. **Run capacity test quarterly:** `make capacity-planning`
4. **Monitor trends:** Maintain spreadsheet of results
5. **Scale infrastructure based on findings**

---

**Questions?** Check the detailed runbook: `PRODUCTION_RUNBOOK.md`
