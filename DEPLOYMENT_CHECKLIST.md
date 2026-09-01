# Deployment Checklist
## TrueMatch AI - Production Deployment Verification

**Version:** 1.0  
**Date:** July 21, 2026  
**Deployment Lead:** ___________________  
**Approval:** ___________________  

---

## Phase 1: Pre-Deployment (1-2 weeks before)

### Infrastructure Planning
- [ ] AWS account created and configured
- [ ] Budget approved (~$1,200-2,000/month)
- [ ] Team members assigned
- [ ] Communication plan established (Slack channel, war room)
- [ ] Rollback plan documented
- [ ] Change window scheduled (off-peak hours)

### AWS Account Setup
- [ ] AWS CLI installed and configured
- [ ] MFA enabled for privileged users
- [ ] IAM roles and policies created
- [ ] VPC and networking designed
- [ ] KMS keys created for encryption
- [ ] S3 buckets created and configured
- [ ] ECR repositories created

### Database & Cache Preparation
- [ ] RDS PostgreSQL sizing determined
- [ ] ElastiCache Redis sizing determined
- [ ] Backup strategy documented
- [ ] Disaster recovery plan reviewed
- [ ] Database parameter groups configured
- [ ] Security groups defined

### Application Preparation
- [ ] All production secrets generated and secured
- [ ] Docker images built and tested
- [ ] Images pushed to ECR with proper tagging
- [ ] Kubernetes manifests reviewed and updated
- [ ] Configuration values validated
- [ ] Monitoring dashboards created

---

## Phase 2: Infrastructure Setup (5-7 days)

### AWS Infrastructure Provisioning
- [ ] EKS cluster created (1.29+)
- [ ] Node groups healthy (3+ nodes)
- [ ] VPC configured with proper subnets
- [ ] Security groups created and rules applied
- [ ] NAT gateways deployed (HA)
- [ ] RDS PostgreSQL instance created
  - [ ] Multi-AZ enabled
  - [ ] Automated backups configured
  - [ ] KMS encryption enabled
  - [ ] Enhanced monitoring enabled
- [ ] ElastiCache Redis cluster created
  - [ ] Cluster mode enabled
  - [ ] Multi-AZ failover enabled
  - [ ] Encryption enabled
  - [ ] Auth token configured
- [ ] S3 buckets configured
  - [ ] Versioning enabled
  - [ ] Encryption enabled
  - [ ] Lifecycle policies configured
  - [ ] Access logging enabled
- [ ] ALB created and configured
- [ ] ACM certificate requested/issued
- [ ] Route53 DNS zone configured

### Kubernetes Add-ons
- [ ] NGINX ingress controller installed
- [ ] cert-manager installed and configured
- [ ] External Secrets Operator installed
- [ ] Metrics Server deployed
- [ ] Prometheus/Grafana installed
- [ ] Fluent-bit DaemonSet deployed
- [ ] Loki log aggregation deployed

### Secrets Management
- [ ] All secrets created in AWS Secrets Manager
- [ ] Kubernetes secrets created/configured
- [ ] RBAC policies applied
- [ ] Secret rotation policies configured
- [ ] Access audit logging enabled

### Database & Cache Verification
- [ ] RDS connectivity verified from EKS
- [ ] Redis connectivity verified from EKS
- [ ] Database parameters optimal for workload
- [ ] Redis memory management configured
- [ ] Backup/restore procedures tested

---

## Phase 3: Application Deployment (2-3 days)

### Pre-Deployment Validation
- [ ] All code merged to main branch
- [ ] CI/CD pipeline passing all checks
- [ ] Docker images built successfully
- [ ] Image security scan passed (no critical CVEs)
- [ ] All tests passing
  - [ ] Unit tests: PASS
  - [ ] Integration tests: PASS
  - [ ] E2E tests: PASS
- [ ] Performance baseline established
- [ ] Load test completed (expected traffic)

### Database Migration
- [ ] Alembic migrations created and tested
- [ ] Migration rollback procedure documented
- [ ] Production database backup created
- [ ] Migration run in staging environment
- [ ] Data integrity validated post-migration
- [ ] Production migration scheduled

### Kubernetes Deployment
- [ ] Kubernetes manifests updated with production values
  - [ ] Correct image URIs
  - [ ] Correct database/Redis hosts
  - [ ] Correct replicas for HA
  - [ ] Correct resource requests/limits
  - [ ] Correct health check probes
- [ ] Namespace created
- [ ] RBAC roles and bindings applied
- [ ] ConfigMaps deployed
- [ ] Secrets deployed
- [ ] Database migration job runs successfully
- [ ] API deployment rolls out (3 replicas healthy)
- [ ] Worker deployment rolls out (3+ replicas)
- [ ] Beat scheduler deployed (1 replica)
- [ ] Network policies applied

### Ingress & SSL/TLS
- [ ] Certificate issued and stored
- [ ] Ingress resource deployed
- [ ] TLS configuration validated
- [ ] CORS headers configured
- [ ] Rate limiting configured
- [ ] WAF rules enabled (if using)

### Monitoring Setup
- [ ] Prometheus scrape targets configured
- [ ] Loki log aggregation working
- [ ] Grafana dashboards deployed
- [ ] Key metrics collection verified
- [ ] CloudWatch alarms created
- [ ] PagerDuty integration configured (if applicable)
- [ ] Sentry error tracking configured

---

## Phase 4: Validation & Testing (2-3 days)

### Functionality Testing
- [ ] API health checks responding
  - [ ] `/livez` → 200 OK
  - [ ] `/readyz` → 200 OK
  - [ ] `/metrics` → Prometheus metrics
  - [ ] `/docs` → API documentation
- [ ] Database connectivity verified
- [ ] Redis connectivity verified
- [ ] File uploads to S3 working
- [ ] Email notifications sending
- [ ] Authentication (JWT, Singpass) working
- [ ] Background tasks (Celery) processing
- [ ] Scheduled jobs (Beat) running
- [ ] Webhook integrations functional

### Performance Testing
- [ ] API latency p95 < 500ms
- [ ] Database query performance acceptable
- [ ] Redis latency < 10ms
- [ ] Memory usage stable over 24 hours
- [ ] CPU usage within expected ranges
- [ ] No memory leaks detected
- [ ] Connection pools not exhausted
- [ ] Task queue processing efficiently

### Security Validation
- [ ] TLS certificate valid and trusted
- [ ] HTTPS enforced (HTTP redirects)
- [ ] Security headers present
  - [ ] HSTS
  - [ ] X-Frame-Options
  - [ ] X-Content-Type-Options
  - [ ] CSP
- [ ] No sensitive data in logs
- [ ] Secrets not exposed in responses
- [ ] CORS origin validation working
- [ ] Rate limiting enforced
- [ ] Authentication required for protected endpoints
- [ ] Network policies enforced

### Monitoring Validation
- [ ] Metrics flowing into Prometheus
- [ ] Logs flowing into Loki
- [ ] Dashboards displaying data correctly
- [ ] Alarms created and tested (no false positives)
- [ ] Error tracking (Sentry) receiving errors
- [ ] Alert notifications working
- [ ] Log retention policies active

### Backup & Disaster Recovery
- [ ] Database backup created and stored
  - [ ] Backup size: _____ GB
  - [ ] Backup location: truematch-backups S3
  - [ ] Retention policy: 30 days
- [ ] Backup restore test completed
  - [ ] Restore completed in: _____ minutes
  - [ ] Data integrity verified: ✓
- [ ] Redis snapshot created
- [ ] S3 backup encryption verified
- [ ] Disaster recovery playbook reviewed

### Data Quality
- [ ] No data corruption
- [ ] No missing records
- [ ] Encryption keys accessible
- [ ] Field-level encryption working
- [ ] Index searches functional
- [ ] Data validation rules enforced

---

## Phase 5: Staging Full Run (3-5 days)

### End-to-End Testing
- [ ] Complete user workflow tested
- [ ] Resume upload and processing working
- [ ] Job description ingestion working
- [ ] CV/JD matching running correctly
- [ ] Assessment scoring accurate
- [ ] Reports generating correctly
- [ ] Admin panel functional
- [ ] User notifications delivering

### Load Testing
- [ ] Expected traffic load simulated
- [ ] System remains responsive under load
- [ ] No cascading failures
- [ ] Auto-scaling triggers appropriately
- [ ] Rate limiting doesn't affect users
- [ ] Database connections stable
- [ ] Redis eviction not excessive

### Integration Testing
- [ ] External API integrations working
- [ ] Webhook deliveries successful
- [ ] Third-party service connectivity stable
- [ ] SSO/OAuth integration functional
- [ ] Payment processing (if applicable) verified

### Compliance Validation
- [ ] PDPA compliance verified (data residency)
- [ ] GDPR compliance (if applicable)
- [ ] SOC 2 controls in place
- [ ] Audit logging enabled
- [ ] Data access controls enforced
- [ ] Encryption standards met

---

## Phase 6: Production Cutover (1 day)

### Final Pre-Cutover Checks (2 hours before)
- [ ] All validation tests passed
- [ ] No critical bugs identified
- [ ] Monitoring fully operational
- [ ] Alert channels tested and working
- [ ] Team on standby and ready
- [ ] Communication channels open
- [ ] Rollback plan reviewed with team
- [ ] Customer communication ready
- [ ] Maintenance window announced
- [ ] Database backup created (final)

### DNS Cutover
- [ ] Update Route53 records to point to production ALB
- [ ] Test DNS resolution
- [ ] Verify DNS propagation (may take 5-15 minutes)
- [ ] Monitor DNS queries for errors

### Traffic Migration
- [ ] Gradually shift traffic from old to new (if applicable)
  - [ ] 0% → 25% → 50% → 75% → 100%
  - [ ] Monitor errors at each step
  - [ ] Allow 5-10 minutes per step
- [ ] Or perform immediate cutover if not applicable
- [ ] Monitor error rates closely (target: <0.1%)
- [ ] Monitor latency (target: p95 < 500ms)

### Real-Time Monitoring
- [ ] Error rate normal
- [ ] Latency acceptable
- [ ] Database CPU < 70%
- [ ] Database connections stable
- [ ] Memory usage stable
- [ ] Disk space available
- [ ] No pod crashes
- [ ] Task queue processing normally
- [ ] Logs flowing correctly
- [ ] Alerts firing appropriately (no false positives)

### Immediate Post-Cutover (First 2 hours)
- [ ] Continue close monitoring
- [ ] Be prepared for quick rollback
- [ ] Check user support channels for issues
- [ ] Verify key workflows are functional
- [ ] Confirm data is being written correctly
- [ ] Validate file uploads are working
- [ ] Test user authentication
- [ ] Confirm scheduled jobs are running

---

## Phase 7: Post-Deployment (1-2 weeks)

### Immediate Follow-up (24 hours)
- [ ] No critical issues reported
- [ ] System performing within SLA
- [ ] All metrics normal
- [ ] User feedback positive
- [ ] No data integrity issues
- [ ] Backup/restore procedures validated

### Short-term Optimization (1 week)
- [ ] Performance baseline captured
- [ ] Resource utilization optimized
- [ ] Cost analysis completed
- [ ] Reserved instances purchased (if applicable)
- [ ] Auto-scaling policies tuned
- [ ] Alert thresholds adjusted based on baseline

### Documentation & Knowledge Transfer
- [ ] Runbooks created/updated
  - [ ] Deployment runbook
  - [ ] Rollback runbook
  - [ ] Incident response playbook
  - [ ] Scaling procedures
- [ ] Team trained on operations
- [ ] On-call documentation completed
- [ ] Monitoring dashboard training
- [ ] Alert response procedures documented

### Post-Deployment Verification
- [ ] Cost tracking in place
- [ ] Budget alerts configured
- [ ] Performance benchmarks established
- [ ] SLA targets confirmed achievable
- [ ] Incident response tested
- [ ] Communication procedures validated

### Long-term Planning
- [ ] Next update strategy planned
- [ ] Maintenance window schedule created
- [ ] Backup testing schedule established
- [ ] Capacity planning initiated
- [ ] Technical debt identified and prioritized

---

## Phase 8: Success Criteria

### Technical Metrics
- [ ] Uptime: ≥ 99.9% (43m/month downtime max)
- [ ] API Latency p95: < 500ms
- [ ] API Latency p99: < 1000ms
- [ ] Error Rate: < 0.1% (1 error per 1000 requests)
- [ ] Database Query Time p95: < 100ms
- [ ] Celery Task Processing: < 30 seconds 95% of time

### Operational Metrics
- [ ] No data loss or corruption
- [ ] All backups completing successfully
- [ ] Disaster recovery tested successfully
- [ ] Monitoring capturing all metrics
- [ ] Alerts responding correctly
- [ ] On-call team responding effectively

### Business Metrics
- [ ] User satisfaction maintained/improved
- [ ] No major user-reported issues
- [ ] Service adoption on track
- [ ] Revenue processing correctly (if applicable)
- [ ] Support ticket volume normal

---

## Rollback Decision Criteria

**Rollback if:**
- Critical data loss or corruption
- Error rate > 5%
- API latency p95 > 5 seconds
- Database unavailability
- Security breach detected
- Revenue processing failures
- User authentication failures
- >= 3 critical bugs requiring immediate fixes

**Rollback Procedure:**
1. Alert team and notify leadership
2. Announce maintenance window to users
3. Revert traffic/DNS to previous version
4. Verify old version stable (30 minutes)
5. Investigate root cause
6. Plan remediation
7. Communicate status to users

**Rollback RTO:** < 1 hour from decision

---

## Sign-Off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Project Lead | ________________ | ________ | ____________ |
| DevOps Lead | ________________ | ________ | ____________ |
| QA Lead | ________________ | ________ | ____________ |
| Security Lead | ________________ | ________ | ____________ |
| Product Owner | ________________ | ________ | ____________ |
| Executive Sponsor | ________________ | ________ | ____________ |

---

## Notes & Issues

### Blockers
- [ ] None identified
1. _________________________________
2. _________________________________

### Warnings
- [ ] None identified
1. _________________________________
2. _________________________________

### Follow-up Items
- [ ] None identified
1. _________________________________
2. _________________________________

---

## Post-Deployment Review Meeting

**Date:** _______________  
**Time:** _______________  
**Attendees:** _______________

### Successes
1. _________________________________
2. _________________________________
3. _________________________________

### Challenges
1. _________________________________
2. _________________________________
3. _________________________________

### Lessons Learned
1. _________________________________
2. _________________________________
3. _________________________________

### Improvements for Next Deployment
1. _________________________________
2. _________________________________
3. _________________________________

---

## Appendix A: Emergency Contact Information

**On-Call Engineer:** _________________ Phone: _________________  
**Escalation Lead:** _________________ Phone: _________________  
**Executive Sponsor:** _________________ Phone: _________________  
**AWS Support:** Premium Support Case URL: _________________

## Appendix B: Important URLs

- EKS Cluster: https://console.aws.amazon.com/eks/
- RDS Console: https://console.aws.amazon.com/rds/
- ECR Repositories: https://console.aws.amazon.com/ecr/
- CloudWatch Logs: https://console.aws.amazon.com/cloudwatch/
- Grafana Dashboard: https://grafana.truematch.digital
- Prometheus: https://prometheus.truematch.digital
- API Documentation: https://api.truematch.digital/docs

## Appendix C: Useful kubectl Commands

```bash
# Monitor deployment
kubectl rollout status deployment/api -n truematch -w

# View logs
kubectl logs -f deployment/api -n truematch

# Get pod details
kubectl describe pod POD_NAME -n truematch

# Execute command in pod
kubectl exec -it POD_NAME -n truematch -- bash

# Scale deployment
kubectl scale deployment api --replicas=5 -n truematch

# Restart deployment
kubectl rollout restart deployment/api -n truematch

# Rollback deployment
kubectl rollout undo deployment/api -n truematch

# Check events
kubectl get events -n truematch --sort-by=.metadata.creationTimestamp
```

---

*Deployment Checklist - Production Ready. Use this checklist to ensure safe, successful deployment of TrueMatch AI to AWS EKS.*
