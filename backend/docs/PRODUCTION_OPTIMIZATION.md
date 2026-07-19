# PRODUCTION OPTIMIZATION GUIDE

**TrueMatch AI Performance Optimization Procedures**  
**Version:** 1.0  
**Date:** 2024

---

## TABLE OF CONTENTS

1. [Database Query Optimization](#database-query-optimization)
2. [Cache Optimization](#cache-optimization)
3. [API Optimization](#api-optimization)
4. [Resource Utilization](#resource-utilization)
5. [Load Distribution](#load-distribution)
6. [Cost Optimization](#cost-optimization)

---

## DATABASE QUERY OPTIMIZATION

### Identifying Slow Queries

```sql
-- List top 20 slowest queries
SELECT 
  query,
  calls,
  total_time,
  mean_time,
  max_time,
  min_time
FROM pg_stat_statements
WHERE query NOT LIKE '%pg_%'
ORDER BY mean_time DESC
LIMIT 20;
```

### Query Optimization Techniques

#### 1. Add Missing Indexes
```sql
-- Find missing indexes
CREATE INDEX idx_accounts_status ON accounts(status);
CREATE INDEX idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX idx_logs_created_at ON logs(created_at DESC);

-- Verify index usage
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
ORDER BY idx_scan ASC;

-- Drop unused indexes
DROP INDEX idx_unused_index;
```

#### 2. Query Rewriting
```sql
-- BAD: SELECT N+1 problem
SELECT * FROM accounts;
-- Then loop: SELECT * FROM api_keys WHERE account_id = ?

-- GOOD: JOIN
SELECT a.*, ak.*
FROM accounts a
LEFT JOIN api_keys ak ON a.id = ak.account_id;
```

#### 3. Pagination Implementation
```sql
-- BAD: SELECT all then limit
SELECT * FROM accounts ORDER BY created_at DESC LIMIT 1000000 OFFSET 500000;

-- GOOD: Keyset pagination
SELECT * FROM accounts
WHERE created_at < ?
ORDER BY created_at DESC
LIMIT 100;
```

#### 4. Use EXPLAIN ANALYZE
```bash
# Test query performance
psql -h $DB_HOST -U $DB_USER -d $DB_NAME << EOF
EXPLAIN ANALYZE
SELECT a.*, ak.*
FROM accounts a
LEFT JOIN api_keys ak ON a.id = ak.account_id
WHERE a.status = 'active'
ORDER BY a.created_at DESC
LIMIT 100;
EOF
```

### Connection Pool Tuning

```bash
# Check current configuration
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "SHOW max_connections"
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "SHOW shared_buffers"
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "SHOW work_mem"

# Optimal settings for production
# max_connections = 100 (default for most)
# shared_buffers = 25% of RAM (max 40% for dedicated)
# work_mem = total_RAM / (max_connections * 2)

# Check current connections
psql -h $DB_HOST -U $DB_USER -d $DB_NAME << EOF
SELECT 
  datname,
  count(*) as connections,
  max(extract(epoch from (now() - query_start))) as max_query_time_seconds
FROM pg_stat_activity
GROUP BY datname;
EOF

# Kill idle connections if needed
psql -h $DB_HOST -U $DB_USER -d $DB_NAME << EOF
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'idle'
AND query_start < now() - interval '30 minutes';
EOF
```

---

## CACHE OPTIMIZATION

### Cache Hit Rate Analysis

```bash
# Check Redis hit rate
redis-cli INFO stats | grep -E "keyspace_hits|keyspace_misses"

# Calculate hit rate
redis-cli EVAL "
local hits = redis.call('INFO', 'stats')
local misses = redis.call('INFO', 'stats')
return {hits, misses}
" 0

# Formula: hits / (hits + misses)
```

### Cache Strategy Implementation

#### 1. Application-Level Caching
```javascript
// Cache expensive computations
const cache = new Map();

async function getAccountMetrics(accountId) {
  const cacheKey = `metrics:${accountId}`;
  
  // Check cache
  if (cache.has(cacheKey)) {
    return cache.get(cacheKey);
  }
  
  // Compute if not cached
  const metrics = await computeExpensiveMetrics(accountId);
  
  // Store in cache with TTL
  cache.set(cacheKey, metrics);
  setTimeout(() => cache.delete(cacheKey), 3600000); // 1 hour TTL
  
  return metrics;
}
```

#### 2. Redis Caching
```bash
# Set cache entry
redis-cli SET account:123:profile '{"name":"John","status":"active"}' EX 3600

# Get cache entry
redis-cli GET account:123:profile

# Increment counter with cache
redis-cli INCR page_views:daily EX 86400

# Cache invalidation
redis-cli DEL account:123:profile
```

#### 3. Cache Warming
```bash
# Pre-load frequently accessed data on startup
async function warmCache() {
  const hotAccounts = await getTopAccounts(100);
  
  for (const account of hotAccounts) {
    const profile = await fetchProfile(account.id);
    await redis.set(
      `profile:${account.id}`,
      JSON.stringify(profile),
      { EX: 3600 }
    );
  }
}
```

### TTL Optimization

```
Data Type                  Current TTL    Recommended TTL
========================================================
User Profile               1 hour         4 hours
Account Settings           1 hour         8 hours
API Response Cache         5 minutes      15 minutes
Session Data               30 minutes     2 hours
Database Query Results     10 minutes     30 minutes
Third-party API Response   1 hour         24 hours

Decision Factors:
- Data change frequency
- Business impact of stale data
- Cost of recomputation
- Cache memory constraints
```

---

## API OPTIMIZATION

### Reduce Payload Size

```javascript
// BAD: Return all fields
GET /api/accounts/123
Response: {
  id: 123,
  name: "Acme Corp",
  email: "contact@acme.com",
  phone: "555-1234",
  address: "123 Main St",
  city: "Springfield",
  state: "IL",
  zip: "62701",
  country: "USA",
  created_at: "2023-01-01T00:00:00Z",
  updated_at: "2024-01-15T14:30:00Z",
  // ... 50 more fields
}

// GOOD: Return only needed fields
GET /api/accounts/123?fields=id,name,email
Response: {
  id: 123,
  name: "Acme Corp",
  email: "contact@acme.com"
}
```

### Implement Pagination

```javascript
// BAD: Return 10,000 results
GET /api/logs?limit=10000
Response: [
  { ... }, // 10,000 objects
  { ... },
  // ...
]

// GOOD: Paginate results
GET /api/logs?page=1&page_size=100
Response: {
  data: [
    { ... }, // 100 objects
  ],
  pagination: {
    page: 1,
    page_size: 100,
    total: 10000,
    has_next: true
  }
}
```

### Add Request Compression

```javascript
// Enable gzip compression
app.use(compression({
  filter: (req, res) => {
    if (req.headers['x-no-compression']) return false;
    return compression.filter(req, res);
  },
  level: 6  // Balance speed vs compression ratio
}));

// Result: ~70-80% reduction in response size
```

### Implement Streaming

```javascript
// BAD: Buffer entire response in memory
app.get('/api/exports/large', async (req, res) => {
  const data = await fetchLargeDataset();
  res.json(data);  // Memory issues with large datasets
});

// GOOD: Stream response
app.get('/api/exports/large', async (req, res) => {
  res.setHeader('Content-Type', 'application/ndjson');
  const stream = await fetchLargeDatasetAsStream();
  stream.pipe(res);
});
```

---

## RESOURCE UTILIZATION

### CPU Optimization

```bash
# Current CPU usage
kubectl top pods -n production -l app=truematch-api

# Identify CPU hot spots
node --prof app.js
node --prof-process isolate-*.log > cpu-profile.txt

# Optimize Node.js runtime
# Set heap size appropriately
export NODE_OPTIONS="--max-old-space-size=1024 --max-semi-space-size=512"

# Use clustering for CPU-bound work
const cluster = require('cluster');
const os = require('os');

if (cluster.isMaster) {
  const numCPUs = os.cpus().length;
  for (let i = 0; i < numCPUs; i++) {
    cluster.fork();
  }
} else {
  app.listen(3000);
}
```

### Memory Optimization

```bash
# Monitor memory usage
kubectl top pods -n production -l app=truematch-api

# Detect memory leaks
# 1. Baseline memory at startup
# 2. Monitor over time
# 3. Alert if > 10% increase per day

# Optimize memory
# 1. Use object pooling for frequently created objects
// Object pool
const objPool = [];
function createObject() {
  if (objPool.length > 0) {
    return objPool.pop();
  }
  return {};
}
function releaseObject(obj) {
  Object.keys(obj).forEach(key => delete obj[key]);
  objPool.push(obj);
}

# 2. Reduce object allocations
# 3. Use streaming for large data
# 4. Implement aggressive garbage collection tuning
```

### Disk I/O Optimization

```bash
# Monitor disk usage
kubectl top pods -n production -l app=truematch-api | grep "disk"

# Check slow disk operations
sudo iostat -x 1 10

# Optimize:
# 1. Use SSD for databases
# 2. Enable write caching (if safe)
# 3. Batch write operations
# 4. Archive old logs

# Verify disk performance
fio --name=randread --ioengine=libaio --iodepth=16 --rw=randread --bs=4k --direct=1 --size=1G
```

---

## LOAD DISTRIBUTION

### Horizontal Scaling

```bash
# Scale replicas based on load
kubectl scale deployment truematch-api -n production --replicas=6

# Autoscaling configuration
cat > autoscale.yaml <<EOF
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: truematch-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: truematch-api
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
EOF

kubectl apply -f autoscale.yaml
```

### Load Balancer Configuration

```bash
# Verify load balancer configuration
kubectl get service truematch-api -n production -o yaml

# Session affinity (sticky sessions)
kubectl patch service truematch-api -n production \
  -p '{"spec":{"sessionAffinity":"ClientIP","sessionAffinityConfig":{"clientIP":{"timeoutSeconds":10800}}}}'

# Load balancing algorithm
# Round Robin (default) - best for stateless services
# Least Connection - best for long-lived connections
# IP Hash - good for session affinity
```

### Request Distribution

```
Endpoint Load Distribution Analysis
====================================

Endpoint                     % of Traffic   Current Avg Time   Status
------------------------------------------------------------------
GET  /v1/health/ping         20%            5ms               ✓
GET  /v1/accounts/profile    28%            45ms              ✓
POST /v1/ai/inference        11%            280ms             ⚠ Slow
GET  /v1/search/query        13%            95ms              ✓
POST /v1/batch/process       8%             320ms             ⚠ Slow

Action Items:
1. Optimize AI inference endpoint (scale separately)
2. Batch process endpoint (use queue system)
```

---

## COST OPTIMIZATION

### Resource Right-Sizing

```bash
# Analyze current resource allocation
kubectl get pods -n production -o json | \
  jq '.items[] | {
    name: .metadata.name,
    cpu_request: .spec.containers[0].resources.requests.cpu,
    cpu_limit: .spec.containers[0].resources.limits.cpu,
    memory_request: .spec.containers[0].resources.requests.memory,
    memory_limit: .spec.containers[0].resources.limits.memory
  }'

# Benchmark to find optimal values
# Run load tests with different resource allocations
# Select minimum resources that meet performance targets

# Current allocation: 500m CPU / 512Mi memory
# Actual usage: 400m CPU / 400Mi memory
# Optimized allocation: 400m CPU / 400Mi memory (20% cost reduction)
```

### Compute Optimization

```
Cost Optimization Opportunities
================================

Current Setup:
- 3 nodes (8 CPU, 16GB RAM each)
- Monthly cost: $2,400

Optimization 1: Use preemptible instances
- Cost reduction: 60-70%
- Trade-off: Pod interruptions (mitigate with multiple replicas)
- New cost: $720-960/month
- Savings: $1,440-1,680/month

Optimization 2: Node consolidation
- Reduce to 2 large nodes instead of 3 medium
- More efficient resource utilization
- Cost reduction: 15-20%
- New cost: $1,920-2,040/month
- Savings: $360-480/month

Optimization 3: Reserved instances
- Commit to 1-year usage
- Cost reduction: 30-40%
- New cost: $1,440-1,680/month
- Savings: $720-960/month

Recommended: Combination approach
- Use preemptible instances for non-critical workloads
- Reserved instances for core services
- Target savings: 45-50% ($1,080-1,200/month)
```

### Database Optimization

```bash
# Identify expensive queries
psql -h $DB_HOST -U $DB_USER -d $DB_NAME << EOF
SELECT query, calls, total_time
FROM pg_stat_statements
ORDER BY total_time DESC
LIMIT 10;
EOF

# Optimize expensive queries
# 1. Add indexes
# 2. Reduce row scans
# 3. Use materialized views for aggregations
# 4. Archive old data

# Database storage optimization
# - Enable compression on large tables
# - Remove duplicate data
# - Archive historical data
# - Estimated savings: 30-40%
```

### Monitoring Cost

```bash
# Track compute costs
kubectl get nodes -o json | \
  jq '.items[] | {
    name: .metadata.name,
    instance_type: .spec.providerID,
    cpu: .status.allocatable.cpu,
    memory: .status.allocatable.memory
  }'

# Calculate monthly costs based on:
# - Compute (per node)
# - Storage (per GB)
# - Network (per GB transferred)
# - Services (load balancer, etc.)

# Set budget alerts
# Alert if: projected_monthly_cost > budget
```

---

## OPTIMIZATION CHECKLIST

- [ ] Database queries optimized (mean time < 10ms)
- [ ] Slow queries identified and fixed (< 5 per day)
- [ ] Indexes optimized (no unused indexes)
- [ ] Cache hit rate > 90%
- [ ] API response time p99 < 300ms
- [ ] CPU utilization < 70%
- [ ] Memory utilization < 75%
- [ ] Database connections < 80%
- [ ] Cost optimized (30%+ reduction achieved)
- [ ] Resource allocation right-sized
- [ ] Load distribution optimized
- [ ] Monitoring alerts tuned
- [ ] Documentation updated

---

**For optimization support:** engineering@truematch.com
