# Agent Configuration Operations Guide

## Deployment & Setup

### Prerequisites

- PostgreSQL 12+ with async support
- Python 3.12+
- Redis (for Celery, if using background tasks)
- FastAPI application running

### Database Setup

The agent configuration system requires 3 tables. Apply migrations:

```bash
cd backend
alembic upgrade head
# This runs migration 0043_agent_config_customization.py
```

**Tables created:**
- `agent_configs` — Current configuration per agent
- `agent_config_versions` — Immutable version snapshots
- `agent_config_audits` — Complete audit trail

**Indexes:** 7 performance indexes on agent_configs, 4 on agent_config_versions, 4 on agent_config_audits

### Rollback

If you need to rollback:

```bash
alembic downgrade -1
# This removes the 3 tables and enums
```

## Configuration Management

### Loading Configurations

Agents automatically load custom configurations at runtime:

```python
from app.agents.agent_factory import AgentFactory

factory = AgentFactory(db_session)
agent = await factory.get_agent_for_user(
    user_id=user.id,
    user_role=user.role,
    company_id=user.company_id
)
# If custom config exists, it's injected
# Otherwise, agent uses hardcoded defaults
```

### Fallback Behavior

If a configuration lookup fails (database down, config missing):

```
Try to load custom config from DB
  ↓ (succeeds) → Inject into agent
  ↓ (fails) → Log warning, use hardcoded defaults
```

This ensures chat endpoints remain available even if config management is down.

### Configuration Parameters

**Agent parameters** supported:
- `temperature` (0.0-2.0): Controls creativity/randomness
- `max_tokens` (100-4096): Response length limit
- `model` (string): Which Claude model to use
- `timeout` (int): API timeout in seconds

**Tool parameters** per-tool:
```json
{
  "tool_name": {
    "max_length": 5000,
    "timeout": 30,
    "enabled": true
  }
}
```

## Monitoring & Alerting

### Key Metrics

Monitor these to ensure healthy operation:

1. **Configuration Load Time**
   - Query: `SELECT count(*), avg(load_time_ms) FROM agent_config_metrics`
   - Alert if > 100ms (indicates DB slowness)

2. **Approval Queue Depth**
   - Query: `SELECT count(*) FROM agent_configs WHERE status = 'pending_approval'`
   - Alert if > 10 (indicates admin backlog)

3. **Active Configuration Age**
   - Query: `SELECT max(activated_at) FROM agent_configs WHERE status = 'active'`
   - Alert if > 30 days without updates

4. **Audit Trail Growth**
   - Query: `SELECT count(*) FROM agent_config_audits`
   - Expected: ~10 logs per configuration lifecycle
   - Alert if growth rate exceeds 1000/day

### Error Tracking

Watch logs for:
- "Failed to load agent config from database" → Config DB issue
- "Config failed governance validation" → Admin rejected config
- "Can only update configs in DRAFT status" → Incorrect workflow

## Maintenance Tasks

### Weekly

- **Review pending approvals**
  ```sql
  SELECT id, name, created_by_id, created_at
  FROM agent_configs
  WHERE status = 'pending_approval'
  ORDER BY created_at DESC;
  ```
  Action: Approve/reject within 2 business days

- **Monitor fairness scores**
  ```sql
  SELECT version_number, fairness_score
  FROM agent_config_versions
  WHERE status = 'active'
  ORDER BY created_at DESC LIMIT 10;
  ```
  Alert if any active config has score < 70

### Monthly

- **Audit trail cleanup**
  ```sql
  -- Archive old audit logs (older than 90 days)
  COPY agent_config_audits TO 'audit_backup_2026_07.csv'
  WHERE created_at < NOW() - INTERVAL '90 days';
  
  DELETE FROM agent_config_audits
  WHERE created_at < NOW() - INTERVAL '365 days';
  ```

- **Deprecated configuration cleanup**
  ```sql
  -- Identify long-unused configs (deprecated > 6 months)
  SELECT id, status, deprecation_date FROM agent_configs
  WHERE status = 'deprecated'
  AND created_at < NOW() - INTERVAL '180 days';
  ```

- **Version growth analysis**
  ```sql
  SELECT config_id, count(*) as version_count
  FROM agent_config_versions
  GROUP BY config_id
  HAVING count(*) > 20
  ORDER BY version_count DESC;
  ```

### Quarterly

- **Security audit**
  - Review all active configurations for safety patterns
  - Check fairness scores of production agents
  - Verify admin approval patterns

- **Performance tuning**
  - Analyze slow config lookups
  - Review index usage on agent_configs table
  - Consider partitioning if dataset > 100k rows

## Troubleshooting

### Issue: Agents not loading custom configs

**Symptoms:** Chat endpoint returns responses but doesn't use custom instructions

**Diagnosis:**
```sql
-- Check if active config exists
SELECT * FROM agent_configs
WHERE status = 'active'
AND company_id = $company_id;

-- Check factory logs for errors
grep "Failed to load agent config" application.log
```

**Solutions:**
1. Verify database is accessible
2. Check that config is in ACTIVE status
3. Restart FastAPI workers to clear cache

### Issue: Approval checklist shows "review_required"

**Diagnosis:**
```python
from app.services.agent_config_governance import AgentConfigGovernance

governance = AgentConfigGovernance(db)
config = await service.get_config_by_id(config_id)
version = await service.get_version_by_number(config_id, config.version_number)
checklist = await governance.get_approval_checklist(config, version)
print(checklist["approval_items"])
```

**Common issues:**
- Fairness score < 70 → Add fairness language to instructions
- Dangerous patterns detected → Remove blocked keywords
- Missing tool definitions → Specify tools_enabled

### Issue: "Config failed governance validation" on approve

**Root causes:**
1. Dangerous instruction patterns (bypass, disable, ignore, override)
2. Invalid parameter ranges (temperature, max_tokens)
3. Fairness score calculation changed

**Fix:**
```bash
# View validation details
curl http://localhost:8000/api/v1/agent-configs/{config_id}/validate
```

Then reject and have recruiter update config.

### Issue: Slow config lookup

**Diagnosis:**
```sql
-- Check index usage
EXPLAIN ANALYZE
SELECT * FROM agent_configs
WHERE company_id = $company_id
AND agent_type = $agent_type
AND status = 'active';
```

**Solutions:**
- Verify `ix_agent_configs_company_agent` index exists
- Check PostgreSQL query plan
- Consider adding composite index if needed

## Disaster Recovery

### Backup Strategy

```bash
# Nightly backup (recommended)
pg_dump -h localhost -U postgres truematch_db \
  --table=agent_configs \
  --table=agent_config_versions \
  --table=agent_config_audits \
  > backups/agent_config_$(date +%Y%m%d).sql

# Retention: Keep 30 days
find backups -name "agent_config_*.sql" -mtime +30 -delete
```

### Recovery Procedure

If configurations are lost:

```bash
# 1. Restore from backup
psql -h localhost -U postgres truematch_db < backups/agent_config_20260715.sql

# 2. Verify restoration
SELECT count(*) FROM agent_configs;
SELECT count(*) FROM agent_config_versions;

# 3. Check agent behavior
# Agents fall back to hardcoded defaults automatically
# Chat endpoints will continue working
```

### Fallback Mode

If entire config system fails:

1. Database down → Agents use hardcoded instructions
2. Config table corrupted → Agents use hardcoded instructions
3. Migration failed → Rollback migration, agents use hardcoded instructions

**No user-facing impact** — system is designed to degrade gracefully.

## Production Checklist

Before deploying to production:

- [ ] Database migration tested in staging
- [ ] Backup strategy implemented
- [ ] Monitoring/alerting configured
- [ ] Admin training completed
- [ ] Fallback behavior verified
- [ ] Audit logging enabled
- [ ] Permission checks validated
- [ ] Load testing at expected scale
- [ ] Recovery procedure documented
- [ ] On-call runbook prepared

## Configuration Distribution

### Multi-Region Deployment

If using multiple database replicas:

```python
# Primary (write) region
AsyncSession(engine_write)  # agent_configs write endpoint

# Replica (read) regions
AsyncSession(engine_replica)  # get_active_config uses replica
```

Replication lag: Typically <1 second. Safe for read-heavy lookup.

### Cache Strategy

For high-traffic deployments, consider caching active configs:

```python
cache = TTLCache(maxsize=1000, ttl=300)  # 5-min TTL

async def get_active_config(company_id, agent_type):
    cache_key = f"{company_id}:{agent_type}"
    
    if cache_key in cache:
        return cache[cache_key]
    
    config = await db.query(AgentConfig).where(...)
    cache[cache_key] = config
    return config
```

Cache invalidation on config activation (explicit, not TTL-based).

## Performance Benchmarks

Expected performance (PostgreSQL 12+ on standard hardware):

| Operation | Time | Notes |
|-----------|------|-------|
| Create config | 50ms | Includes audit logging |
| Update config | 75ms | Creates new version |
| Submit for approval | 25ms | Status update only |
| Approve config | 100ms | Runs governance validation |
| Activate config | 150ms | Deactivates others |
| Get active config | 5ms | Indexed lookup |
| List versions | 20ms | Per 100 versions |
| Validation check | 50ms | CPU-bound |

Load testing target: 1000 concurrent chat sessions.

## Compliance & Audit

### Audit Trail Retention

- **Required:** 1 year (legal compliance)
- **Recommended:** 3 years (operational history)

Configuration:
```sql
-- Archive logs older than 1 year
DELETE FROM agent_config_audits
WHERE created_at < NOW() - INTERVAL '1 year';
```

### Compliance Queries

```sql
-- Who changed configs and when?
SELECT actor_id, action, count(*), created_at
FROM agent_config_audits
GROUP BY actor_id, action, DATE(created_at)
ORDER BY created_at DESC;

-- Which configs changed most frequently?
SELECT config_id, count(*) as changes
FROM agent_config_audits
GROUP BY config_id
ORDER BY changes DESC;

-- Approval lag time?
SELECT 
  a.config_id,
  (SELECT created_at FROM agent_config_audits 
   WHERE config_id = a.config_id AND action = 'submitted') as submitted,
  (SELECT created_at FROM agent_config_audits 
   WHERE config_id = a.config_id AND action = 'approved') as approved
FROM agent_configs a
WHERE status IN ('approved', 'active');
```

