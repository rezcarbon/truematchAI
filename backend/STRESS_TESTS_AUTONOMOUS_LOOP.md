# TrueMatch Autonomous Loop - Comprehensive Stress Tests

## Overview
This document defines 6 production-grade stress tests for the TrueMatch autonomous loop, covering load, resilience, governance, and budget constraints. Each test includes setup instructions, success metrics, and expected behavior.

**Test Framework:** pytest + asyncio  
**Duration:** ~30-45 minutes total runtime  
**Cost Impact:** Simulated (no real API calls with proper mocking)

---

## Test 1: Load Test - High Candidate Volume

### Objective
Verify the autonomous loop can process large batches of candidates without data loss or accuracy degradation.

### Scenario
- **10,000 candidates** uploaded in a single batch
- Each candidate represents a `ChatSession` with pending actions
- Actions are evenly distributed: 40% analyze, 30% rank, 20% schedule, 10% approve
- System has 2-minute timeout limit

### Setup Instructions

```bash
# 1. Create test database (in-memory SQLite for speed, PostgreSQL for production)
# 2. Create 10,000 user records with autonomous settings enabled
# 3. For each user:
#    - Create 1 ChatSession
#    - Create 1 ChatMessage with actions_taken payload
#    - Actions marked as "pending" status
# 4. Configure loop:
#    - POLLING_INTERVAL_SECONDS = 1 (aggressive for testing)
#    - MAX_BATCH_SIZE = 500 (handle large batches)
#    - Enable debug logging
```

### Test Code Structure

```python
@pytest.mark.asyncio
async def test_high_candidate_volume_processing():
    """Test 10k candidates processing in <5 minutes with 100% accuracy."""
    # Setup
    db = await create_test_db()
    manager = AutonomousLoopManager()
    
    # Create 10k users with pending actions
    users = await bulk_create_users(db, count=10000)
    actions_by_type = await bulk_create_actions(
        db, 
        users, 
        total_actions=10000,
        distribution={"analyze": 0.4, "rank": 0.3, "schedule": 0.2, "approve": 0.1}
    )
    
    # Record initial state
    initial_pending = await count_pending_actions(db)
    assert initial_pending == 10000
    
    # Start loop with timeout
    start_time = datetime.utcnow()
    async with asyncio.timeout(300):  # 5 minute timeout
        await manager._process_cycle()
    
    elapsed = (datetime.utcnow() - start_time).total_seconds()
    
    # Verify results
    final_pending = await count_pending_actions(db)
    completed = await count_completed_actions(db)
    
    # Assertions
    assert final_pending == 0, "All candidates processed"
    assert completed == 10000, "No data loss"
    assert elapsed < 300, f"Completed in {elapsed}s, target <300s"
    
    # Verify accuracy: all actions processed correctly
    for action_type, expected_count in actions_by_type.items():
        actual = await count_actions_by_type(db, action_type, status="completed")
        assert actual == expected_count, f"Action type {action_type} count mismatch"
    
    # Check metrics
    stats = manager.metrics.get_stats()
    assert stats["success_rate_percent"] == 100.0
    assert stats["actions_executed"] == 10000
    assert stats["actions_failed"] == 0
```

### Success Metrics
| Metric | Target | Pass Criteria |
|--------|--------|--------------|
| Processing Time | <5 min | All 10k actions processed |
| Accuracy | 100% | All action types counted correctly |
| Data Loss | 0% | Zero dropped actions |
| Throughput | >200 actions/sec | Sustained during batch |
| Memory Usage | <2GB | No OOM kills |
| DB Connection Pool | Stable | Max 30 active connections |

### Expected Behavior
1. Loop processes actions in parallel within batch size limits
2. Jitter prevents thundering herd on database
3. Batch size capping (MAX_BATCH_SIZE=500) prevents resource exhaustion
4. Metrics accurately track all completions
5. No deadlocks in concurrent access

### Failure Modes to Catch
- OOM from unbounded action lists
- Connection pool exhaustion
- Duplicate processing (idempotency failure)
- Race conditions in action status updates
- Metrics counting errors

---

## Test 2: Load Test - High Loop Frequency

### Objective
Verify the loop maintains sub-100ms latency under high action frequency (5-second intervals × 100 concurrent users).

### Scenario
- **100 users** with autonomous mode enabled
- Each user triggers 1 action every **5 seconds**
- Target: **<100ms latency** per action, **zero dropped** actions
- Duration: 5 minutes (300 total actions expected)

### Setup Instructions

```bash
# 1. Create 100 users with autonomous settings
# 2. Instrument the loop to measure latency per action
# 3. Use a background task to generate new pending actions every 5s
# 4. Configure:
#    - POLLING_INTERVAL_SECONDS = 1
#    - rate limiting: 10 actions/hour per user (well above 12/hour)
#    - daily budget: $100 per user
```

### Test Code Structure

```python
@pytest.mark.asyncio
async def test_high_loop_frequency():
    """Test <100ms latency under 100 users × 12 actions/min each."""
    db = await create_test_db()
    manager = AutonomousLoopManager()
    
    # Setup 100 users
    users = await bulk_create_users(db, count=100)
    for user in users:
        await create_autonomous_settings(
            db, 
            user.id, 
            enabled=True, 
            actions_per_hour=120,  # Allow 12 actions/5min
            daily_budget=1000.0
        )
    
    # Track latencies
    latencies = []
    generated_count = 0
    
    async def action_generator():
        """Generate new pending actions every 5 seconds."""
        nonlocal generated_count
        for _ in range(60):  # 5 minutes / 5 seconds per action
            for user in users:
                await create_pending_action(
                    db, 
                    user_id=user.id,
                    action_type="send",
                    cost=0.02
                )
                generated_count += 1
            await asyncio.sleep(5)
    
    # Track execution latency per action
    original_execute = manager._process_user_tasks
    
    async def tracked_execute(user_id, db):
        start = datetime.utcnow()
        await original_execute(user_id, db)
        latency_ms = (datetime.utcnow() - start).total_seconds() * 1000
        latencies.append(latency_ms)
    
    manager._process_user_tasks = tracked_execute
    
    # Run both generators in parallel
    start_time = datetime.utcnow()
    try:
        async with asyncio.timeout(330):  # 5.5 min
            await asyncio.gather(
                manager._process_cycle_repeat(times=330),  # 1 cycle/sec
                action_generator()
            )
    except asyncio.TimeoutError:
        pass
    
    # Verify results
    elapsed = (datetime.utcnow() - start_time).total_seconds()
    expected_actions = 100 * 60  # 100 users × 60 actions in 5 min
    
    assert generated_count == expected_actions
    assert len(latencies) >= expected_actions * 0.95, "Captured 95%+ of actions"
    
    # Latency analysis
    p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]
    p99_latency = sorted(latencies)[int(len(latencies) * 0.99)]
    max_latency = max(latencies)
    mean_latency = sum(latencies) / len(latencies)
    
    assert p95_latency < 100, f"P95 latency {p95_latency}ms < 100ms"
    assert max_latency < 500, f"Max latency {max_latency}ms < 500ms"
    
    # Check metrics
    stats = manager.metrics.get_stats()
    assert stats["actions_executed"] == expected_actions
    assert stats["actions_failed"] == 0
```

### Success Metrics
| Metric | Target | Pass Criteria |
|--------|--------|--------------|
| P95 Latency | <100ms | 95th percentile |
| P99 Latency | <200ms | 99th percentile |
| Max Latency | <500ms | No outliers >500ms |
| Mean Latency | <50ms | Average response time |
| Dropped Actions | 0 | 100% delivery rate |
| Action Accuracy | 100% | Correct action types |

### Expected Behavior
1. Loop cycles every 1-3 seconds (with jitter)
2. Each user's actions processed within 100ms
3. Rate limiting prevents exceeding 120 actions/hour per user
4. Polling jitter spreads load across time
5. Connection pool handles concurrent access

### Failure Modes to Catch
- Lock contention causing >100ms stalls
- Database connection exhaustion
- Memory pressure slowing loop
- Lost actions due to transaction rollback
- Incorrect rate limit calculation

---

## Test 3: Stress Test - Budget Exhaustion

### Objective
Verify fair cost allocation when users approach or exceed daily budget limits.

### Scenario
- **User A**: $10.00 daily budget with $9.50 already spent
- **Queue**: 1000 pending `send` actions ($0.01 each = $10.00 total)
- Expected: First 50 actions execute ($0.50), then budget exceeded
- Remaining 950 actions should be deferred (not dropped)

### Setup Instructions

```bash
# 1. Create 1 user with:
#    - autonomous_settings.daily_budget = 10.00
#    - autonomous_settings.spending_today = 9.50
# 2. Create 1 ChatSession with 1 message containing 1000 pending actions
# 3. All actions are type "send" ($0.01 cost each)
# 4. Verify budget enforcement logic
```

### Test Code Structure

```python
@pytest.mark.asyncio
async def test_budget_exhaustion_fairness():
    """Test that budget exhaustion is handled fairly without dropping actions."""
    db = await create_test_db()
    manager = AutonomousLoopManager()
    
    # Create user with near-exhausted budget
    user = await create_user(db)
    settings = await create_autonomous_settings(
        db,
        user_id=user.id,
        enabled=True,
        daily_budget=10.00,
        spending_today=9.50,  # $0.50 remaining
        actions_per_hour=1000  # No rate limit
    )
    
    # Create 1000 pending send actions ($0.01 each)
    session = await create_chat_session(db, user.id)
    actions = []
    for i in range(1000):
        actions.append({
            "id": f"action_{i}",
            "type": "send",
            "status": "pending",
            "cost": 0.01,
            "description": f"Send action {i}"
        })
    
    message = await create_chat_message(
        db,
        session_id=session.id,
        role="assistant",
        content="",
        actions_taken=actions
    )
    
    # Record initial state
    initial_pending = await count_pending_actions(db, user_id=user.id)
    assert initial_pending == 1000
    
    # Execute one loop cycle
    await manager._process_user_tasks(user.id, db)
    
    # Verify budget enforcement
    updated_settings = await get_autonomous_settings(db, user.id)
    
    # After execution:
    # - 50 actions should complete ($0.50)
    # - 950 actions should remain pending
    # - Budget should be at exactly $10.00
    completed = await count_completed_actions(db, user_id=user.id)
    remaining_pending = await count_pending_actions(db, user_id=user.id)
    
    assert completed == 50, f"Expected 50 completed, got {completed}"
    assert remaining_pending == 950, f"Expected 950 pending, got {remaining_pending}"
    assert abs(updated_settings.spending_today - 10.00) < 0.001, "Budget exactly at limit"
    assert updated_settings.actions_count_today == 50
    
    # Verify no actions lost or dropped
    total_actions = completed + remaining_pending
    assert total_actions == 1000, "No actions lost"
    
    # Verify second cycle defers all actions
    await manager._process_user_tasks(user.id, db)
    
    completed_2 = await count_completed_actions(db, user_id=user.id)
    assert completed_2 == 50, "No additional actions executed after budget"
```

### Success Metrics
| Metric | Target | Pass Criteria |
|--------|--------|--------------|
| Budget Limit Respected | Exact | No overage beyond budget |
| Fairness (FIFO) | 100% | First-in-first-out execution |
| No Data Loss | 0% | All deferred actions preserved |
| Cost Accuracy | ±0.01 | Correct cost calculation |
| Deferred Actions | 950 | Correct count of remaining |

### Expected Behavior
1. Cost calculator correctly determines action cost ($0.01)
2. Budget check prevents execution after $10.00 spent
3. Deferred actions remain in "pending" status
4. No partial charges or rounding errors
5. Metrics correctly track allowed vs. deferred

### Failure Modes to Catch
- Overspending (executing beyond budget)
- Dropping deferred actions
- Rounding errors (e.g., 50.001 actions)
- Race condition on `spending_today` field
- Missing cost calculation

---

## Test 4: Stress Test - Governance Conflicts

### Objective
Verify graceful escalation when governance gates have contradictory settings or multiple gates fail.

### Scenario
- **User B** has autonomous mode with contradictory governance rules:
  - `min_confidence_threshold: 95%` (very strict)
  - `requires_governance_approval: True`
  - `auto_escalate_on_governance_fail: True`
- **Assessment**: Coherence gate fails (internal resume inconsistency)
- Expected: Escalate to human review, create `GovernanceReview` record, mark actions as "blocked"

### Setup Instructions

```bash
# 1. Create user with conflicting governance settings
# 2. Create autonomous settings with:
#    - min_confidence_threshold: 95
#    - requires_governance_approval: True
#    - auto_escalate_on_governance_fail: True
# 3. Create a ChatMessage with assessment data that fails coherence check
# 4. Mock governance checks to return multiple failures
```

### Test Code Structure

```python
@pytest.mark.asyncio
async def test_governance_conflict_escalation():
    """Test graceful escalation when governance gates fail or conflict."""
    db = await create_test_db()
    manager = AutonomousLoopManager()
    
    # Create user with strict governance
    user = await create_user(db)
    settings = await create_autonomous_settings(
        db,
        user_id=user.id,
        enabled=True,
        min_confidence_threshold=95,
        requires_governance_approval=True,
        auto_escalate_on_governance_fail=True,
        daily_budget=500.0
    )
    
    # Create assessment that fails multiple gates
    session = await create_chat_session(db, user.id)
    
    # Mock governance check results
    failed_assessment = {
        "candidate_id": "test_cand_001",
        "capability_score": 0.82,  # Below 95% threshold
        "analysis": {
            "coherence": "Resume has date overlap in employment history",
            "consistency": "Skill progression inconsistent with timeline"
        }
    }
    
    message = await create_chat_message(
        db,
        session_id=session.id,
        role="assistant",
        content="",
        actions_taken=[
            {
                "id": "assess_001",
                "type": "analyze",
                "status": "pending",
                "assessment": failed_assessment,
                "governance_status": "pending_review"
            }
        ]
    )
    
    # Mock governance engine to fail multiple gates
    async def mock_governance_check(assessment, config):
        return {
            "passed": False,
            "gates": {
                "coherence": {
                    "passed": False,
                    "reason": "Date overlap detected"
                },
                "consistency": {
                    "passed": False,
                    "reason": "Score inconsistent with role baseline"
                },
                "fidelity": {
                    "passed": True,
                    "reason": "Insufficient post-hire data"
                },
                "bias": {
                    "passed": True,
                    "reason": "No demographic data"
                }
            },
            "failed_gates": ["coherence", "consistency"]
        }
    
    # Process with governance check
    with patch("app.engines.governance_engine.run_governance_gates", 
               side_effect=mock_governance_check):
        await manager._process_user_tasks(user.id, db)
        
        # Should not have executed the action
        completed = await count_completed_actions(db, user_id=user.id)
        assert completed == 0, "No actions completed when governance fails"
        
        # Should have created governance review
        reviews = await get_governance_reviews(db, user_id=user.id)
        assert len(reviews) == 1, "One governance review created"
        
        review = reviews[0]
        assert review.status == ReviewStatus.pending, "Review marked pending"
        assert "coherence" in review.failed_gates, "Coherence failure recorded"
        assert "consistency" in review.failed_gates, "Consistency failure recorded"
        assert len(review.failed_gates) == 2, "Both failures recorded"
        
        # Check metrics
        stats = manager.metrics.get_stats()
        assert stats["governance_reviews_created"] == 1
```

### Success Metrics
| Metric | Target | Pass Criteria |
|--------|--------|--------------|
| Escalation Trigger | Always | When any gate fails |
| Review Created | 100% | GovernanceReview record exists |
| Failed Gates Recorded | 100% | All failures logged |
| Review Status | "pending" | Awaiting human review |
| Action Blocked | 100% | No autonomous execution |
| Notification Sent | Configured | User notified if enabled |

### Expected Behavior
1. Multiple failing gates all recorded
2. Action status remains "pending" (never executes)
3. `GovernanceReview` created with review status "pending"
4. Metrics track governance escalations
5. No retry attempts (human must review)
6. Audit log captures gate failures

### Failure Modes to Catch
- Partial execution despite gate failure
- Lost governance reviews
- Incorrect failed gates list
- Double escalations
- Missing audit log entries

---

## Test 5: Resilience Test - Database Latency

### Objective
Verify the loop handles variable database latency (1-10 second responses) without exceeding 30-second timeout and with correct retry logic.

### Scenario
- **Inject latency**: Database operations take 1-10 seconds randomly
- **1000 pending actions** to process
- Expected: Process completes within 30 seconds max, all actions eventually processed
- Verify **retry logic** executes correctly for failed queries

### Setup Instructions

```bash
# 1. Create test database with latency injection
# 2. Use pytest-benchmark or unittest.mock to add delays:
#    - execute() → sleep(random 1-10s)
#    - commit() → sleep(random 1-5s)
# 3. Create 1000 pending actions
# 4. Set RETRY_DELAY_SECONDS = 10 (for testing)
# 5. Monitor query timing and retry counts
```

### Test Code Structure

```python
@pytest.mark.asyncio
async def test_database_latency_resilience():
    """Test resilience to variable database latency up to 10 seconds."""
    db = await create_test_db()
    manager = AutonomousLoopManager()
    
    # Create user with pending actions
    user = await create_user(db)
    settings = await create_autonomous_settings(db, user.id, enabled=True)
    session = await create_chat_session(db, user.id)
    
    # Create 1000 pending actions
    actions = [
        {
            "id": f"action_{i}",
            "type": "send",
            "status": "pending",
            "cost": 0.01
        }
        for i in range(1000)
    ]
    
    message = await create_chat_message(
        db,
        session_id=session.id,
        role="assistant",
        content="",
        actions_taken=actions
    )
    
    # Inject latency into database operations
    original_execute = AsyncSession.execute
    original_commit = AsyncSession.commit
    
    query_times = []
    commit_times = []
    
    async def latency_execute(self, *args, **kwargs):
        latency = random.uniform(0.1, 2.0)  # 100-2000ms
        query_times.append(latency)
        await asyncio.sleep(latency)
        return await original_execute(self, *args, **kwargs)
    
    async def latency_commit(self, *args, **kwargs):
        latency = random.uniform(0.05, 0.5)  # 50-500ms
        commit_times.append(latency)
        await asyncio.sleep(latency)
        return await original_commit(self, *args, **kwargs)
    
    AsyncSession.execute = latency_execute
    AsyncSession.commit = latency_commit
    
    try:
        # Run processing with timeout
        start_time = datetime.utcnow()
        
        async with asyncio.timeout(35):  # 35 second timeout (5s buffer)
            await manager._process_user_tasks(user.id, db)
        
        elapsed = (datetime.utcnow() - start_time).total_seconds()
        
        # Verify results
        completed = await count_completed_actions(db, user_id=user.id)
        
        assert completed >= 950, f"At least 95% completed ({completed}/1000)"
        assert elapsed < 30, f"Completed within 30s (actual: {elapsed:.1f}s)"
        
        # Analyze latency distribution
        avg_query_latency = sum(query_times) / len(query_times)
        max_query_latency = max(query_times)
        
        assert avg_query_latency < 1.0, f"Average query latency < 1s"
        assert max_query_latency < 3.0, f"Max query latency < 3s"
        
        # Check retry logic
        stats = manager.metrics.get_stats()
        assert stats["actions_failed"] < 50, "Less than 5% failures"
        
    finally:
        # Restore original methods
        AsyncSession.execute = original_execute
        AsyncSession.commit = original_commit
```

### Success Metrics
| Metric | Target | Pass Criteria |
|--------|--------|--------------|
| Max Response Time | <30s | All queries complete |
| Retry Success Rate | >95% | Failed queries eventually succeed |
| Average Latency | <1s | Acceptable performance |
| P95 Latency | <3s | No major outliers |
| Data Consistency | 100% | No partial commits |

### Expected Behavior
1. Query timeouts trigger retry logic (MAX_RETRY_ATTEMPTS=3)
2. Exponential backoff prevents thundering herd
3. Circuit breaker opens after 3 failures
4. Connection pool recovers after latency clears
5. Overall processing completes within 30 seconds

### Failure Modes to Catch
- Queries hanging indefinitely
- Retries exceeding maximum attempts
- Connection pool stalling
- Partial commits (dirty reads)
- Lost data due to transaction rollback

---

## Test 6: Resilience Test - API Failures

### Objective
Verify the loop handles 30% API failure rate gracefully, ensuring all actions eventually succeed with proper error handling and Dead Letter Queue management.

### Scenario
- **1000 actions** pending execution
- **30% random failure rate** on API calls (e.g., external service timeouts)
- Expected: All 1000 actions eventually succeed after retries
- DLQ captures: Actions exceeding MAX_RETRY_ATTEMPTS
- No data loss

### Setup Instructions

```bash
# 1. Create 1000 pending actions
# 2. Mock external API calls to fail 30% of the time
# 3. Set MAX_RETRY_ATTEMPTS = 3
# 4. RETRY_DELAY_SECONDS = 1 (for testing, normally 60)
# 5. Simulate multiple retries in a loop
# 6. Track DLQ additions
```

### Test Code Structure

```python
@pytest.mark.asyncio
async def test_api_failures_resilience():
    """Test resilience to 30% API failure rate with proper retry logic."""
    db = await create_test_db()
    manager = AutonomousLoopManager()
    
    # Setup
    user = await create_user(db)
    settings = await create_autonomous_settings(db, user.id, enabled=True)
    session = await create_chat_session(db, user.id)
    
    # Create 1000 pending actions
    actions = [
        {
            "id": f"action_{i}",
            "type": "send",
            "status": "pending",
            "cost": 0.01,
            "retry_count": 0,
            "last_error": None
        }
        for i in range(1000)
    ]
    
    message = await create_chat_message(
        db,
        session_id=session.id,
        role="assistant",
        content="",
        actions_taken=actions
    )
    
    # Mock action executor to fail 30% of the time
    from app.agents.action_executor import ActionExecutor
    original_execute = ActionExecutor.execute_action
    
    call_count = 0
    failure_count = 0
    
    async def flaky_execute_action(action, user, db, **kwargs):
        nonlocal call_count, failure_count
        call_count += 1
        
        # 30% fail rate
        if random.random() < 0.30:
            failure_count += 1
            raise RuntimeError(f"Simulated API timeout for action {action['id']}")
        
        # Success
        return {
            **action,
            "status": "completed",
            "executed_at": datetime.utcnow().isoformat()
        }
    
    ActionExecutor.execute_action = flaky_execute_action
    
    try:
        # Execute with retries
        max_attempts = 5  # Allow multiple cycles
        
        for attempt in range(max_attempts):
            pending = await count_pending_actions(db, user_id=user.id)
            
            if pending == 0:
                break
            
            # Run one processing cycle
            await manager._process_user_tasks(user.id, db)
            
            # Brief delay before retry
            await asyncio.sleep(0.1)
        
        # Final verification
        completed = await count_completed_actions(db, user_id=user.id)
        remaining_pending = await count_pending_actions(db, user_id=user.id)
        dlq_items = await manager.dlq.get_pending_reviews()
        
        # With retry logic, >95% should succeed
        success_rate = completed / 1000
        
        assert completed >= 950, f"95%+ actions succeeded ({completed}/1000, {success_rate*100:.1f}%)"
        assert call_count >= 1000, "All actions attempted at least once"
        
        # DLQ should contain permanent failures
        # (actions exceeding MAX_RETRY_ATTEMPTS=3)
        assert len(dlq_items) <= 50, "At most 5% in DLQ"
        
        # Track failure characteristics
        estimated_failures = call_count - completed
        estimated_failure_rate = estimated_failures / call_count
        
        # Expected failures: 30% chance per attempt
        # After ~3 retries, should converge to ~98-99% success
        assert success_rate >= 0.95, f"Success rate {success_rate*100:.1f}% >= 95%"
        
        # Verify no data loss
        total_tracked = completed + remaining_pending + len(dlq_items)
        assert total_tracked == 1000, "No actions lost"
        
        # Check metrics
        stats = manager.metrics.get_stats()
        logger.info(f"Final stats: {stats}")
        
    finally:
        ActionExecutor.execute_action = original_execute
```

### Success Metrics
| Metric | Target | Pass Criteria |
|--------|--------|--------------|
| Final Success Rate | ≥95% | At least 950 actions completed |
| Retry Efficiency | <5 cycles | Converges quickly |
| DLQ Capture | 100% | All permanent failures in DLQ |
| Data Loss | 0% | Zero actions lost |
| Error Tracking | Complete | All errors logged |
| Max Retry Count | ≤3 | Respects MAX_RETRY_ATTEMPTS |

### Expected Behavior
1. API failure triggers retry with exponential backoff
2. MAX_RETRY_ATTEMPTS=3 honored
3. After 3 failures, action moved to DLQ
4. DLQ marked as "pending_review" for human action
5. Metrics track failures and retries
6. No cascading failures (one failure doesn't crash loop)

### Failure Modes to Catch
- Retries exceeding MAX_RETRY_ATTEMPTS
- Lost DLQ items
- Infinite retry loops
- Actions never moved to DLQ despite failures
- Missing error context

---

## Test Execution Guide

### Run All Tests
```bash
cd /Users/darthmod/Desktop/TrueMatch/backend

# Install test dependencies
pip install pytest pytest-asyncio pytest-benchmark pytest-mock

# Run stress tests with verbose output
pytest tests/test_autonomous_loop_stress.py -v --tb=short

# Run with performance profiling
pytest tests/test_autonomous_loop_stress.py -v --benchmark-only

# Run specific test
pytest tests/test_autonomous_loop_stress.py::test_high_candidate_volume_processing -v -s
```

### Test File Structure
```
tests/
├── test_autonomous_loop_stress.py          # Main stress test file
├── fixtures/
│   ├── actions.py                          # Bulk action creation
│   ├── users.py                            # User fixtures
│   └── db.py                               # Database setup
└── conftest.py                             # Shared configuration
```

### Monitoring During Tests
```bash
# Terminal 1: Run tests with logs
pytest tests/test_autonomous_loop_stress.py -v -s --log-level=DEBUG

# Terminal 2: Monitor system resources
watch -n 1 'ps aux | grep python'
watch -n 1 'lsof | grep db.sqlite'
```

### CI/CD Integration
```yaml
# .github/workflows/stress-tests.yml
name: Stress Tests
on: [push]
jobs:
  stress-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with: { python-version: '3.11' }
      - run: pip install -r requirements.txt
      - run: pytest tests/test_autonomous_loop_stress.py -v --tb=short
```

---

## Bottleneck Identification

### Key Metrics to Monitor

| Component | Metric | Threshold | Action |
|-----------|--------|-----------|--------|
| Database | Query latency | >1s avg | Scale connection pool |
| Memory | Heap usage | >2GB | Reduce batch size |
| Loop | Cycle time | >5s avg | Optimize polling |
| Actions | Processing time | >100ms per action | Add workers |
| Governance | Gate check latency | >500ms | Cache gate results |
| Budget | Calculation time | >10ms | Pre-compute budgets |

### Expected Bottlenecks

1. **Database Query Latency** (Most Common)
   - Symptom: P95 latency >500ms
   - Fix: Add indexes on (user_id, created_at)
   - Prevention: Connection pooling, read replicas

2. **Memory Pressure** (Large Batches)
   - Symptom: OOM killing process
   - Fix: Reduce MAX_BATCH_SIZE from 500 to 100
   - Prevention: Streaming, chunked processing

3. **Governance Gate Delays** (if enabled)
   - Symptom: Per-action latency >100ms
   - Fix: Cache gate results, async gate evaluation
   - Prevention: Governance gates run in parallel

4. **Lock Contention** (Concurrent Users)
   - Symptom: Deadlocks in logs
   - Fix: Use optimistic locking (versions) instead
   - Prevention: Distributed locking (Redis)

5. **Cost Calculation** (Budget Checks)
   - Symptom: Spending_today out of sync
   - Fix: Denormalize spending in cache
   - Prevention: Eventual consistency model

---

## Success Criteria Summary

All tests must pass the following:
- ✅ **Test 1**: 10k candidates in <5 min, 100% accuracy
- ✅ **Test 2**: <100ms latency, zero dropped actions (100 concurrent users)
- ✅ **Test 3**: Budget enforced exactly, no overspend, all deferred preserved
- ✅ **Test 4**: Governance failures escalated, no partial execution
- ✅ **Test 5**: DB latency tolerated, <30s max, retries work
- ✅ **Test 6**: 95%+ success after retries, DLQ captures failures, zero loss

**Overall**: Autonomous loop production-ready for 10k+ daily users, sub-100ms latency, zero data loss.

---

## Appendix: Test Utilities

### Bulk Data Creation

```python
# fixtures/actions.py
async def bulk_create_users(db: AsyncSession, count: int = 100) -> list[User]:
    """Create users in bulk for stress testing."""
    users = [
        User(
            email=f"user_{i}@test.com",
            hashed_password="hash",
            role="recruiter"
        )
        for i in range(count)
    ]
    db.add_all(users)
    await db.commit()
    return users

async def bulk_create_actions(
    db: AsyncSession,
    users: list[User],
    total_actions: int = 1000,
    distribution: dict = None
) -> dict:
    """Create pending actions with specified distribution."""
    if distribution is None:
        distribution = {"analyze": 0.4, "rank": 0.3, "schedule": 0.2, "approve": 0.1}
    
    type_counts = {}
    actions_per_user = total_actions // len(users)
    
    for user in users:
        session = ChatSession(user_id=user.id)
        db.add(session)
        await db.flush()
        
        for i in range(actions_per_user):
            action_type = random.choices(
                list(distribution.keys()),
                weights=list(distribution.values())
            )[0]
            
            type_counts[action_type] = type_counts.get(action_type, 0) + 1
        
        # Create message with actions
        actions = [
            {
                "id": f"{user.id}_{i}",
                "type": action_type,
                "status": "pending",
                "cost": 0.01
            }
            for i in range(actions_per_user)
        ]
        
        message = ChatMessage(
            session_id=session.id,
            role="assistant",
            content="",
            actions_taken=actions
        )
        db.add(message)
    
    await db.commit()
    return type_counts
```

### Assertion Helpers

```python
# fixtures/assertions.py
async def count_pending_actions(
    db: AsyncSession,
    user_id: uuid.UUID = None
) -> int:
    """Count pending actions."""
    stmt = select(func.count()).select_from(ChatMessage).where(
        ChatMessage.actions_taken.op('->')('status').astext == 'pending'
    )
    if user_id:
        stmt = stmt.join(ChatSession).where(ChatSession.user_id == user_id)
    
    result = await db.execute(stmt)
    return result.scalar() or 0

async def count_completed_actions(
    db: AsyncSession,
    user_id: uuid.UUID = None
) -> int:
    """Count completed actions."""
    stmt = select(func.count()).select_from(ChatMessage).where(
        ChatMessage.actions_taken.op('->')('status').astext == 'completed'
    )
    if user_id:
        stmt = stmt.join(ChatSession).where(ChatSession.user_id == user_id)
    
    result = await db.execute(stmt)
    return result.scalar() or 0
```

