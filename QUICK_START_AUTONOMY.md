# Quick Start: Operator Dashboard & Autonomous Features

## 5-Minute Setup

### Frontend

1. **Import the hook and components:**
```typescript
import { useAgentOperator } from '@/hooks/useAgentOperator';
import { QueueTable } from '@/components/admin/operators/QueueTable';
import { QueueItemDetail } from '@/components/admin/operators/QueueItemDetail';
import { ActionPanel } from '@/components/admin/operators/ActionPanel';
```

2. **Use in your dashboard:**
```typescript
export function OperatorDashboard() {
  const [selectedItem, setSelectedItem] = useState<QueueItem>();
  const { queueItems, isConnected, error } = useAgentOperator();

  return (
    <div className="grid grid-cols-3 gap-4">
      <div className="col-span-2">
        <QueueTable
          items={queueItems}
          onSelectRow={setSelectedItem}
          selectedId={selectedItem?.id}
        />
      </div>
      {selectedItem && (
        <div className="col-span-1">
          <QueueItemDetail
            item={selectedItem}
            onApprove={handleApprove}
            onReject={handleReject}
            onHold={handleHold}
          />
        </div>
      )}
    </div>
  );
}
```

### Backend

1. **Copy worker files:**
```bash
cp /workspace/auto_approve.py backend/app/workers/
cp /workspace/auto_reject.py backend/app/workers/
cp /workspace/candidate_notification.py backend/app/workers/
```

2. **Copy API file:**
```bash
cp /workspace/autonomous_decisions.py backend/app/api/v1/
```

3. **Update main.py to register router:**
```python
from app.api.v1 import autonomous_decisions

app.include_router(
    autonomous_decisions.router,
    prefix="/api/v1",
    tags=["autonomous-decisions"],
)
```

4. **Test the APIs:**
```bash
# Get thresholds
curl http://localhost:8000/api/v1/config/thresholds

# Evaluate assessment
curl -X POST http://localhost:8000/api/v1/assessments/{id}/auto-decisions
```

---

## File Locations

### Frontend Files
```
web/src/hooks/useAgentOperator.ts
web/src/components/admin/operators/QueueTable.tsx
web/src/components/admin/operators/QueueItemDetail.tsx
web/src/components/admin/operators/ActionPanel.tsx
```

### Backend Files
```
backend/app/workers/auto_approve.py
backend/app/workers/auto_reject.py
backend/app/workers/candidate_notification.py
backend/app/api/v1/autonomous_decisions.py
```

### Configuration
```
backend/app/config.py  # Updated with AUTO_APPROVE_THRESHOLD, etc.
```

---

## Key Endpoints

### Configuration
```
GET  /api/v1/config/thresholds
POST /api/v1/config/thresholds (admin only)
```

### Auto-Decisions
```
POST /api/v1/assessments/{id}/auto-decisions
POST /api/v1/assessments/batch/auto-decisions
```

### WebSocket
```
WS /ws/operator?token={access_token}

Events:
- queue_item_action: {item_id, action, status, notes}
- agent_status_change: {agent_type, running, queue_size}
- processing_alert: {agent_type, level, message}
```

---

## Configuration

### Thresholds (in config.py)
```python
AUTO_APPROVE_THRESHOLD = 0.90  # Auto-approve if score >= this and governance passes
AUTO_REJECT_THRESHOLD = 0.40   # Auto-reject if score < this
DECISION_REVIEW_THRESHOLD = 0.65  # Manual review if between reject and approve
```

### Environment Variables
```bash
# For candidate emails
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@truematch.ai
```

---

## Hook API

### useAgentOperator()
```typescript
const {
  queueItems,              // Current queue items
  agentStatuses,           // Map of agent status by type
  events,                  // Recent events (last 100)
  isConnected,             // WebSocket connection status
  error,                   // Connection error if any
  onQueueItemAction,       // Stub handler (for reference)
  onAgentStatusChange,     // Register listener callback
  onProcessingAlert,       // Register alert callback
  clearEvents,             // Clear event history
} = useAgentOperator();
```

---

## Component APIs

### QueueTable
```typescript
<QueueTable
  items={queueItems}
  onSelectRow={(item) => {...}}
  selectedId={selectedId}
  isLoading={loading}
  error={error}
  filterAwaitingReview={true}
  onFilterChange={(filtered) => {...}}
/>
```

### QueueItemDetail
```typescript
<QueueItemDetail
  item={selectedItem}
  onApprove={async (notes) => {...}}
  onReject={async (reason, notes) => {...}}
  onHold={async (holdUntil, notes) => {...}}
  isActionLoading={loading}
  actionError={error}
/>
```

### ActionPanel
```typescript
<ActionPanel
  onAction={async (payload) => {...}}
  isLoading={loading}
  error={error}
  itemId={item.id}
  itemStatus={item.status}
  onSuccess={(action) => {...}}
  onError={(error) => {...}}
/>
```

---

## Testing

### Auto-Approve a Test Assessment
```bash
# 1. Create assessment with score 0.95
POST /api/v1/assessments \
  -H "Content-Type: application/json" \
  -d '{
    "resume_id": "...",
    "position_id": "...",
    "metadata": {
      "capability_score": 0.95,
      "governance_gates_passed": true
    }
  }'

# 2. Check if auto-approved
GET /api/v1/assessments/{id}/auto-decisions
# Should return: {"decision": "auto_approve", ...}
```

### Check WebSocket Events
```typescript
import { useAgentOperator } from '@/hooks/useAgentOperator';

function TestComponent() {
  const { events, isConnected } = useAgentOperator();

  useEffect(() => {
    console.log('Connected:', isConnected);
    console.log('Recent events:', events);
  }, [events, isConnected]);

  return <div>{isConnected ? 'Connected' : 'Disconnected'}</div>;
}
```

---

## Debugging

### Common Issues

**WebSocket not connecting:**
- Check token in URL: `/ws/operator?token={access_token}`
- Verify CORS configuration allows WS upgrade
- Check browser console for WebSocket errors

**Auto-decisions not firing:**
- Verify assessment has `governance_gates_passed` in metadata
- Check threshold values in config
- Review backend logs for `[AutoApprove]` or `[AutoReject]` entries

**Components not updating:**
- Confirm hook is connected to real WebSocket (check `isConnected`)
- Verify parent is passing props correctly
- Check React DevTools for hook state

### Logs to Check
```bash
# Frontend (browser console)
[Operator] WebSocket connected
[Operator] Queue item action: item_id -> approved

# Backend (server logs)
[AutoApprove] Processing assessment {id}: score=0.95
[AutoReject] Auto-rejected queue item {id}
[CandidateNotification] Sent assessment_started via email
```

---

## Performance Tips

1. **Table with many items:** Add virtual scrolling
   ```bash
   npm install react-window
   # Then wrap table in FixedSizeList
   ```

2. **WebSocket updates:** Use memoization
   ```typescript
   const memoizedItems = useMemo(() => queueItems, [queueItems]);
   ```

3. **Batch operations:** Use `/api/v1/assessments/batch/auto-decisions`

---

## Next: Full Integration

See **PRODUCTION_CODE_DELIVERY.md** for:
- Complete API documentation
- All configuration options
- Audit trail details
- Testing strategies
- Next phase roadmap

---

**Ready to integrate?**

1. Copy the 4 frontend files to `web/src/`
2. Copy the 4 backend files to `backend/app/`
3. Update `config.py` with new thresholds
4. Register API router in `main.py`
5. Test WebSocket and auto-decisions
6. Deploy! 🚀
