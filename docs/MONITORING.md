# TrueMatch Monitoring & Observability Guide

**Document Version:** 1.0  
**Last Updated:** 2026-06-07  
**Status:** Production Ready

---

## Table of Contents

1. [Overview](#overview)
2. [Monitoring Stack](#monitoring-stack)
3. [Prometheus Setup](#prometheus-setup)
4. [Grafana Dashboards](#grafana-dashboards)
5. [Loki Log Aggregation](#loki-log-aggregation)
6. [Alerting Rules](#alerting-rules)
7. [Key Metrics](#key-metrics)
8. [Troubleshooting](#troubleshooting)

---

## Overview

TrueMatch uses a comprehensive monitoring stack:

- **Prometheus**: Metrics collection and time-series database
- **Grafana**: Metrics visualization and dashboarding
- **Loki**: Log aggregation and querying
- **AlertManager**: Alert routing and deduplication

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Application Layer                        │
│ ┌────────────────┐ ┌────────────────┐ ┌────────────────┐   │
│ │  Backend API   │ │  Frontend      │ │  Celery Worker │   │
│ │ (metrics       │ │ (RUM metrics)  │ │ (task metrics) │   │
│ │  & logs)       │ │                │ │                │   │
│ └────────────────┘ └────────────────┘ └────────────────┘   │
└──────────────────────────────────────────────────────────────┘
        ↓ HTTP Scrape        ↓ JSON Logs         ↓ Events
┌──────────────────────────────────────────────────────────────┐
│                   Monitoring Stack                            │
│ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐          │
│ │ Prometheus   │ │ Loki         │ │ AlertManager │          │
│ │ (scrapes     │ │ (aggregates  │ │ (routes      │          │
│ │  metrics)    │ │  logs)       │ │  alerts)     │          │
│ └──────────────┘ └──────────────┘ └──────────────┘          │
└──────────────────────────────────────────────────────────────┘
        ↓ Query                ↓ Query             ↓ Rule Eval
┌──────────────────────────────────────────────────────────────┐
│                   Visualization                               │
│ ┌──────────────────────────────────────────────────────────┐ │
│ │ Grafana Dashboard                                        │ │
│ │ • API Performance                                        │ │
│ │ • Database Health                                        │ │
│ │ • Error Rates & Logs                                    │ │
│ │ • Resource Usage                                         │ │
│ └──────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

---

## Monitoring Stack

### Quick Start

```bash
# Start monitoring services
docker-compose -f docker-compose.monitoring.yml up -d

# Verify all services are running
docker-compose -f docker-compose.monitoring.yml ps

# Access web interfaces
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3001 (admin/admin)
# AlertManager: http://localhost:9093
# Loki: http://localhost:3100
```

### Service Ports

| Service | Port | Purpose |
|---------|------|---------|
| Prometheus | 9090 | Metrics scraping, TSDB |
| Grafana | 3001 | Visualization |
| Loki | 3100 | Log aggregation |
| Promtail | 9080 | Log forwarding |
| AlertManager | 9093 | Alert routing |

### Configuration Files

| File | Purpose |
|------|---------|
| `monitoring/prometheus.yml` | Scrape configs, alerting rules |
| `monitoring/alerts.yml` | Alert rules and expressions |
| `monitoring/loki.yml` | Log storage & retention |
| `monitoring/promtail.yml` | Log collection sources |
| `monitoring/alertmanager.yml` | Alert routing rules |
| `monitoring/grafana/provisioning/datasources/` | Data source config |
| `monitoring/grafana/provisioning/dashboards/` | Dashboard definitions |

---

## Prometheus Setup

### What is Prometheus?

Prometheus is a metrics collection and time-series database. It:
- **Scrapes** metrics from applications at regular intervals
- **Stores** metrics with timestamps
- **Evaluates** alert rules
- **Provides** a query language (PromQL)

### Configuring Scrape Targets

Edit `monitoring/prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'truematch-backend'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s
```

### Common PromQL Queries

```promql
# Request rate (requests per second)
rate(http_requests_total[1m])

# Error rate (5xx errors as percentage)
rate(http_requests_total{status=~"5.."}[5m]) / 
rate(http_requests_total[5m])

# P95 latency
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Active database connections
postgresql_connection_in_use

# Memory usage percentage
(container_memory_usage_bytes / container_spec_memory_limit_bytes) * 100

# Celery task success rate
rate(celery_task_succeeded_total[1m]) / 
(rate(celery_task_succeeded_total[1m]) + rate(celery_task_failed_total[1m]))
```

### Accessing Prometheus UI

1. Open http://localhost:9090
2. **Graph** tab: Enter PromQL query
3. **Alerts** tab: View current alerts and evaluation status
4. **Status** → **Targets**: View scrape status

---

## Grafana Dashboards

### Logging In

```
URL: http://localhost:3001
Username: admin
Password: admin
```

**Change password immediately in production!**

### Available Dashboards

#### 1. TrueMatch API Dashboard
- **Location:** Home → Dashboards → TrueMatch API
- **Metrics:**
  - Request rate (requests/sec)
  - Request latency (P95, P99)
  - Error rate (4xx, 5xx)
  - Application logs (errors)

#### 2. Database Performance
- **Metrics:**
  - Query execution time
  - Active connections
  - Disk usage
  - Backup status

#### 3. System Resources
- **Metrics:**
  - CPU usage
  - Memory usage
  - Disk I/O
  - Network traffic

#### 4. Celery Workers
- **Metrics:**
  - Task processing rate
  - Task failure rate
  - Queue depth
  - Worker status

### Creating Custom Dashboards

1. Click **+** → **Dashboard** → **New Dashboard**
2. Click **Add a new panel**
3. Select data source (Prometheus or Loki)
4. Enter query:
   ```promql
   rate(http_requests_total[1m])
   ```
5. Customize title, colors, axes
6. Click **Save dashboard**

### Dashboard Best Practices

- **Title:** Describe what's being measured
- **Y-axis:** Include units (req/s, ms, %)
- **Legend:** Show metric labels
- **Threshold:** Add warning/critical thresholds
- **Annotations:** Add deployment markers

---

## Loki Log Aggregation

### What is Loki?

Loki is a log aggregation system that:
- **Collects** logs from all sources
- **Indexes** logs with labels for fast querying
- **Stores** logs efficiently
- **Integrates** with Grafana for visualization

### Log Sources

| Source | Path | Format |
|--------|------|--------|
| Application | `/var/log/truematch/app.log` | JSON |
| Database | `/var/log/postgresql/*.log` | Text |
| Redis | `/var/log/redis/*.log` | Text |
| Celery | `/var/log/celery/*.log` | Text |
| Nginx | `/var/log/nginx/access.log` | Combined |
| Docker | Docker daemon | JSON |

### Querying Logs in Grafana

1. Select **Loki** data source
2. Enter LogQL query:

```logql
# All errors
{job="truematch-app"} | json | level="ERROR"

# Specific service
{service="backend"} | json

# Errors in last hour
{job="truematch-app"} | json | level="ERROR" | __error__=""

# Slow queries
{job="postgres"} | json duration > 1000

# Request latency
{job="truematch-app"} | json endpoint="/api/v1/cv-analysis" response_time > 5000
```

### Log Levels

- **DEBUG**: Detailed debugging information
- **INFO**: Informational messages
- **WARNING**: Warning messages (non-critical issues)
- **ERROR**: Error messages (service impacted)
- **CRITICAL**: Critical errors (service down)

### Structured Logging

All application logs should be JSON with standard fields:

```json
{
  "timestamp": "2024-06-07T16:02:30.123Z",
  "level": "ERROR",
  "logger": "app.api.assessments",
  "message": "Assessment creation failed",
  "request_id": "req-abc123def",
  "user_id": "usr-12345",
  "error": "Database connection timeout",
  "stack_trace": "..."
}
```

---

## Alerting Rules

### Alert Severity Levels

| Severity | Response Time | Action |
|----------|---------------|--------|
| **Critical** | Immediate (< 5 min) | Page on-call engineer |
| **Warning** | 1-4 hours | Create ticket, send Slack |
| **Info** | Daily review | Log and monitor |

### Configured Alerts

#### High Error Rate
```
Condition: Error rate > 5% for 5 minutes
Severity: Critical
Action: PagerDuty notification
```

#### High Latency
```
Condition: P95 latency > 1 second for 5 minutes
Severity: Warning
Action: Slack notification
```

#### Database Unavailable
```
Condition: Database down for 1 minute
Severity: Critical
Action: PagerDuty notification
```

#### Redis Unavailable
```
Condition: Redis down for 1 minute
Severity: Critical
Action: PagerDuty notification
```

#### Celery Task Failures
```
Condition: > 5 tasks failed in 5 minutes
Severity: Warning
Action: Slack notification
```

### Adding Custom Alerts

1. Edit `monitoring/alerts.yml`
2. Add rule under appropriate group:

```yaml
- alert: MyAlert
  expr: <PromQL expression>
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "Alert summary"
    description: "Alert description"
```

3. Reload Prometheus:
```bash
curl -X POST http://localhost:9090/-/reload
```

---

## Key Metrics

### API Metrics

```promql
# Success rate (%)
(sum(rate(http_requests_total{status=~"2.."}[5m])) / 
 sum(rate(http_requests_total[5m]))) * 100

# Request rate by endpoint
sum(rate(http_requests_total[1m])) by (endpoint)

# Latency by percentile
histogram_quantile(0.50, rate(http_request_duration_seconds_bucket[5m]))  # p50
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))  # p95
histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))  # p99
```

### Database Metrics

```promql
# Connection count
postgresql_stat_activity_count

# Active queries
postgresql_stat_activity_count{state="active"}

# Query duration
rate(postgresql_slow_query_count[5m])

# Cache hit ratio
postgresql_stat_database_blks_hit / 
(postgresql_stat_database_blks_hit + postgresql_stat_database_blks_read)
```

### Application Metrics

```promql
# Task processing rate
rate(celery_task_received_total[1m])

# Task failure rate
rate(celery_task_failed_total[1m])

# Queue depth
celery_queue_length{queue="celery"}

# Worker count
count(celery_worker_tasks_active)
```

---

## Troubleshooting

### Issue: Prometheus Not Scraping

**Symptoms:**
```
Targets: x down, 0 up
```

**Solution:**
```bash
# Check if targets are reachable
curl http://localhost:8000/metrics

# Verify configuration
cat monitoring/prometheus.yml | grep -A5 "scrape_configs:"

# Check Prometheus logs
docker-compose logs prometheus | tail -20

# Restart Prometheus
docker-compose -f docker-compose.monitoring.yml restart prometheus
```

### Issue: Grafana Can't Connect to Prometheus

**Symptoms:**
```
Error: Bad Gateway
Unable to read datasources via API
```

**Solution:**
```bash
# Check Prometheus is running
curl http://prometheus:9090/api/v1/query?query=up

# Verify network connectivity
docker network ls
docker network inspect truematch-monitoring

# Recreate containers
docker-compose -f docker-compose.monitoring.yml down
docker-compose -f docker-compose.monitoring.yml up -d
```

### Issue: High Memory Usage in Prometheus

**Symptoms:**
```
OOMKilled
Memory: 4.2GB / 4GB
```

**Solution:**
```bash
# Check retention period
cat monitoring/prometheus.yml | grep retention

# Reduce retention (default 30 days)
# Edit prometheus.yml:
# command:
#   - '--storage.tsdb.retention.time=7d'

# Delete old data
docker exec truematch-prometheus \
  find /prometheus -name "*.db" -mtime +7 -delete

# Restart with new config
docker-compose -f docker-compose.monitoring.yml restart prometheus
```

### Issue: Loki Disk Space Full

**Symptoms:**
```
ENOSPC: no space left on device
```

**Solution:**
```bash
# Check disk usage
du -sh /loki/*

# Reduce retention
# Edit loki.yml and set retention_deletes_enabled: true

# Delete old logs
docker exec truematch-loki \
  find /loki/chunks -type d -mtime +30 -exec rm -rf {} \;

# Compact index
docker exec truematch-loki \
  /usr/bin/loki -print-config-stderr -config.file=/etc/loki/local-config.yml
```

### Issue: Alerts Not Firing

**Symptoms:**
```
Alert rule exists but never fires
```

**Solution:**
```bash
# Check alert rule evaluation
curl http://localhost:9090/api/v1/rules | jq '.data.groups[0].rules'

# Check for evaluation errors
curl http://localhost:9090/api/v1/query?query=ALERTS

# Verify metric exists
curl 'http://localhost:9090/api/v1/query?query=<metric_name>'

# Check AlertManager configuration
curl http://localhost:9093/api/v1/status
```

---

## Operations Checklist

### Daily
- [ ] Review alerts in AlertManager
- [ ] Check error rates in Grafana
- [ ] Verify backup completion
- [ ] Monitor disk space

### Weekly
- [ ] Review slow query logs
- [ ] Check resource trends
- [ ] Update runbooks if needed
- [ ] Test alert notifications

### Monthly
- [ ] Review retention policies
- [ ] Optimize database indexes
- [ ] Archive old logs
- [ ] Update dashboards

### Quarterly
- [ ] Capacity planning review
- [ ] Scaling assessment
- [ ] Performance testing
- [ ] Disaster recovery drill

