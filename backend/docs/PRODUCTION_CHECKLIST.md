# TrueMatch AI Production Deployment Checklist
## Phase 3: Pre & Post Deployment Verification

**Version:** 1.0  
**Last Updated:** 2026-07-19  
**Deployment Manager:** [Name]  
**Deployment Date:** [Date]

---

## Pre-Deployment Checklist (T-24 Hours)

### Code Quality
- [ ] All unit tests passing (>90% coverage)
- [ ] All integration tests passing
- [ ] Code review completed and approved
- [ ] No high/critical severity security vulnerabilities
- [ ] Static analysis (linting, type checking) passing
- [ ] Performance benchmarks met
- [ ] Database migration tested locally
- [ ] Database migration backwards compatible (if applicable)

### Planning & Documentation
- [ ] Release notes prepared and reviewed
- [ ] Deployment plan documented
- [ ] Rollback plan documented
- [ ] Team trained on deployment procedure
- [ ] Stakeholders notified of deployment window
- [ ] Maintenance window scheduled (if needed)
- [ ] On-call engineer assigned
- [ ] War room details prepared

### Infrastructure Readiness
- [ ] Kubernetes cluster healthy
- [ ] All nodes ready
- [ ] Storage sufficient (>10% free)
- [ ] Network connectivity verified
- [ ] Database backups current
- [ ] Backup tested and verified
- [ ] Database replicas in sync
- [ ] Monitoring systems operational
- [ ] Log aggregation working
- [ ] Alert channels tested (Slack, email, PagerDuty)

### Secrets & Configuration
- [ ] All required secrets present
- [ ] Secrets rotated if >90 days old
- [ ] Environment variables documented
- [ ] Configuration validated
- [ ] Database credentials correct
- [ ] API keys valid
- [ ] SSL certificates valid (>30 days)
- [ ] No hardcoded secrets in code

### External Dependencies
- [ ] Database service status: ✓ Operational
- [ ] Cache (Redis) status: ✓ Operational
- [ ] Message queue status: ✓ Operational
- [ ] Email service status: ✓ Operational
- [ ] External APIs status: ✓ Operational
- [ ] Third-party services health checked
- [ ] Rate limits understood
- [ ] API quotas sufficient

### Team & Communication
- [ ] Team members available (no vacations)
- [ ] On-call coverage 24/7 for 24 hours
- [ ] Communication channels open
- [ ] Escalation paths clear
- [ ] Customer support notified
- [ ] Status page ready
- [ ] Incident templates prepared

---

## Pre-Deployment Checklist (T-2 Hours)

### Final Code Verification
- [ ] Git commit verified
- [ ] Docker image built successfully
- [ ] Docker image pushed to registry
- [ ] Docker image pull tested
- [ ] Image scanned for vulnerabilities

### Database Verification
- [ ] Migration script dry-run successful
- [ ] Migration estimated time < acceptable window
- [ ] Rollback migration prepared
- [ ] Database backup created
- [ ] Backup size reasonable

### Monitoring Setup
- [ ] Grafana dashboards configured
- [ ] Prometheus targets configured
- [ ] Alert rules loaded
- [ ] Sentry project ready
- [ ] Log aggregation configured
- [ ] Custom metrics tested
- [ ] Dashboard filters configured

### Final Approval
- [ ] Product Manager approved
- [ ] Tech Lead approved
- [ ] Operations approved
- [ ] Security approved (if applicable)
- [ ] No critical bugs in release notes
- [ ] Go/No-Go decision made

### Communication
- [ ] Status page updated ("Deploying")
- [ ] Team notified of start time
- [ ] Stakeholders notified
- [ ] Customers notified (if applicable)
- [ ] Chat channel active and monitored

---

## Deployment Execution Checklist

### Start of Deployment
- [ ] Deployment start time logged
- [ ] Team assembled
- [ ] War room started
- [ ] Screen sharing active
- [ ] Logs being monitored
- [ ] Metrics being watched

### Pre-Deployment Checks
```bash
./scripts/deploy-to-production.sh --dry-run --tag v1.2.3
```
- [ ] All pre-checks pass
- [ ] Namespace accessible
- [ ] Secrets readable
- [ ] No conflicting resources
- [ ] Sufficient resources available

### Deployment
```bash
./scripts/deploy-to-production.sh --tag v1.2.3 --slack-webhook [URL]
```
- [ ] Deployment started successfully
- [ ] Image pull initiated
- [ ] Pods creating
- [ ] Migration started (if applicable)
- [ ] Migration progress monitored

### Rollout Monitoring
- [ ] Old pods terminating gracefully
- [ ] New pods starting
- [ ] New pods becoming ready
- [ ] Service endpoints updating
- [ ] No spike in error rate
- [ ] Latency acceptable
- [ ] Database connection pool stable
- [ ] Worker queue depth stable

```bash
# Commands to monitor
kubectl get pods -n truematch-prod -l app=api -o wide
kubectl rollout status deployment/api -n truematch-prod
kubectl logs deployment/api -n truematch-prod -f
curl https://prometheus.truematch.ai/graph
```

### Health Checks
- [ ] API /healthz endpoint responding
- [ ] API /readyz endpoint responding
- [ ] Database responding to queries
- [ ] Redis responding
- [ ] Workers processing tasks
- [ ] Scheduler creating jobs
- [ ] Ingress routing traffic

---

## Post-Deployment Checklist (T+15 Minutes)

### Service Verification
```bash
# Verify all services
kubectl get all -n truematch-prod
kubectl get svc,deploy,pods -n truematch-prod
```
- [ ] All deployments have desired replicas
- [ ] All pods running (no `CrashLoopBackOff`)
- [ ] Services have endpoints
- [ ] Ingress has backends
- [ ] No `NodeNotReady` events

### Health Endpoint Testing
```bash
curl -v https://api.truematch.ai/healthz
curl -v https://api.truematch.ai/readyz
curl -v https://api.truematch.ai/metrics
```
- [ ] /healthz returns 200
- [ ] /readyz returns 200
- [ ] /metrics endpoint accessible
- [ ] No 5xx errors
- [ ] Response time acceptable

### Metrics Verification
- [ ] Request rate stable
- [ ] Error rate < baseline
- [ ] Latency p99 < threshold
- [ ] Memory usage stable
- [ ] CPU usage stable
- [ ] Database connections stable
- [ ] Cache hit ratio normal

### Log Review
```bash
kubectl logs deployment/api -n truematch-prod --tail=100
kubectl logs deployment/worker -n truematch-prod --tail=100
```
- [ ] No ERROR level logs
- [ ] No WARNING level logs (unexpected)
- [ ] Startup messages normal
- [ ] No stuck jobs

### Database Status
```bash
# Connect to database and verify
PGPASSWORD=$DB_PASSWORD psql -h postgres-prod -U $DB_USER -d truematch_prod
```
- [ ] Database responding
- [ ] All tables accessible
- [ ] Recent migration applied
- [ ] Data integrity verified
- [ ] Replication in sync

### Functional Testing
- [ ] Basic API call successful
- [ ] Authentication working
- [ ] Sample match creation successful
- [ ] Data visible in system
- [ ] Email notifications working (if applicable)
- [ ] User workflows operational

---

## Post-Deployment Checklist (T+1 Hour)

### Continued Monitoring
- [ ] Error rate stable and low
- [ ] No new alerts firing
- [ ] Alert channels operational
- [ ] Automated alerts tested
- [ ] No manual intervention needed

### Performance Verification
- [ ] Latency metrics acceptable
- [ ] Memory usage stable and normal
- [ ] CPU usage stable and normal
- [ ] Database performance acceptable
- [ ] Network utilization normal
- [ ] No resource warnings

### Logging & Observability
- [ ] Application logs flowing normally
- [ ] No excessive log volume
- [ ] Structured logging working
- [ ] Tracing functional
- [ ] Metrics collection active
- [ ] Dashboards displaying data

### Incident Preparedness
- [ ] On-call engineer available
- [ ] Escalation paths confirmed
- [ ] Rollback procedure tested (dry-run)
- [ ] War room on standby
- [ ] 24-hour monitoring plan in place

---

## Post-Deployment Checklist (T+24 Hours)

### Extended Stability
- [ ] No errors accumulated in Sentry
- [ ] No repeated alerts
- [ ] Performance remained stable
- [ ] Database size normal
- [ ] Backup completed successfully
- [ ] Replication functioning properly
- [ ] No unexpected high load
- [ ] No security alerts

### User Impact
- [ ] No customer complaints received
- [ ] Support team reports normal activity
- [ ] Analytics show normal usage patterns
- [ ] No spike in error tracking
- [ ] User experience unaffected

### Post-Deployment Review
- [ ] Deployment metrics reviewed
  - Deployment duration: ____ minutes
  - Errors during deployment: ____
  - Alerts fired: ____
- [ ] Timeline of events documented
- [ ] Any issues encountered recorded
- [ ] Lessons learned captured
- [ ] Process improvements identified
- [ ] Documentation updated

### Cleanup & Finalization
- [ ] Status page updated ("Operational")
- [ ] Temporary test resources removed
- [ ] Backup verified and archived
- [ ] Deployment artifacts retained
- [ ] Team debriefing completed
- [ ] Post-incident review scheduled (if needed)

---

## Deployment Metrics

### Deployment Information
| Metric | Value |
|--------|-------|
| Deployment Date | ____________ |
| Deployment Time | ____________ |
| Image Tag | ____________ |
| Committed By | ____________ |
| Reviewed By | ____________ |

### Timeline
| Event | Time | Duration |
|-------|------|----------|
| Pre-checks started | | |
| Database migration started | | |
| Database migration completed | | |
| Deployment started | | |
| API rollout completed | | |
| Worker rollout completed | | |
| All health checks passed | | |
| Status: COMPLETE | | |

### Issues Encountered
```
None / Describe any issues and how they were resolved:
```

### Performance Impact
| Metric | Before | After |
|--------|--------|-------|
| Error Rate | ___% | ___% |
| Latency (p99) | ___ ms | ___ ms |
| CPU Usage | ___% | ___% |
| Memory Usage | ___% | ___% |
| Database Connections | ___ | ___ |

---

## Sign-Off

**Deployment Executed By:** _________________________

**Time Deployment Complete:** _________________________

**Deployment Status:** [ ] Success  [ ] Rollback  [ ] Partial

**Approved By:** _________________________

**Date:** _________________________

**Notes:**
```
[Add any final notes, lessons learned, or follow-up items]
```

---

## Related Documentation

- [Operations Runbook](./OPERATIONS_RUNBOOK.md)
- [Incident Response](./INCIDENT_RESPONSE.md)
- [Disaster Recovery](./DISASTER_RECOVERY.md)
- [Production Deployment](../backend/k8s/prod-deployment.yaml)

---

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-07-19 | DevOps Team | Initial creation |

---

**Questions?** Contact: [devops@truematch.ai](mailto:devops@truematch.ai)
