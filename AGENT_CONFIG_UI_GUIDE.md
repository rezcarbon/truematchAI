# Agent Configuration Approval UI Guide

## Overview

The Agent Configuration Approval UI is a complete admin dashboard for reviewing, validating, and approving agent configurations before they go live. Built with React + TypeScript, it provides a structured workflow for governance and compliance.

## Components

### 1. ApprovalDashboard

Main entry point for admins. Displays list of pending agent configuration approvals.

**Features:**
- List of pending approvals with quick stats
- Search by name or agent type
- Filter by status (all, needs review, ready)
- Quick fairness score visualization
- Click to open detail view

**Usage:**
```tsx
import { ApprovalDashboard } from '@/components/AgentConfigApproval'

export default function AdminPage() {
  return <ApprovalDashboard />
}
```

**Props:** None (uses mock data in development)

### 2. ApprovalDetailPage

Detailed review and approval interface. Shows validation results, side-by-side config comparison, and audit history.

**Features:**
- Tabbed interface (Validation, Comparison, History)
- Validation checklist with color-coded status
- Config comparison (proposed vs active)
- Audit timeline showing all changes
- Feedback form
- Approve/reject buttons with confirmation

**Usage:**
```tsx
import { ApprovalDetailPage } from '@/components/AgentConfigApproval'

export default function ReviewPage() {
  return (
    <ApprovalDetailPage
      configId="550e8400-e29b-41d4-a716-446655440000"
      onApprovalComplete={() => alert('Approved!')}
    />
  )
}
```

**Props:**
- `configId` (string): Configuration ID to review
- `onApprovalComplete` (optional function): Callback when approval/rejection completes

### 3. ValidationChecklist

Displays governance validation results with color-coded status indicators.

**Shows:**
- Safety validation (passed/failed)
- Fairness score (0-100) with progress bar
- Detailed approval items checklist
- Errors and warnings
- Configuration completeness checks

**Usage:**
```tsx
import { ValidationChecklist } from '@/components/AgentConfigApproval'

export default function ValidateComponent() {
  const validation = {
    config_id: '...',
    version_number: 1,
    validation: {
      safety_passed: true,
      fairness_score: 85,
      warnings: [],
      errors: []
    },
    // ... other fields
  }

  return <ValidationChecklist validation={validation} />
}
```

### 4. ConfigComparison

Side-by-side comparison of proposed configuration vs current active configuration.

**Shows:**
- Instructions diff (highlighted if changed)
- Tools comparison (new, removed, unchanged)
- Agent parameters (highlighted if changed)
- Change reason

**Usage:**
```tsx
import { ConfigComparison } from '@/components/AgentConfigApproval'

export default function CompareComponent() {
  return (
    <ConfigComparison
      proposedVersion={proposedConfig}
      activeVersion={activeConfig}
    />
  )
}
```

### 5. AuditTimeline

Immutable audit log showing all changes to a configuration.

**Shows:**
- Timeline of all actions (created, modified, submitted, approved, etc.)
- Who made each change and when
- Reason for each change
- Detailed before/after for modifications

**Usage:**
```tsx
import { AuditTimeline } from '@/components/AgentConfigApproval'

export default function HistoryComponent() {
  return <AuditTimeline configId="550e8400-e29b-41d4-a716-446655440000" />
}
```

## API Integration

### Hooks

The UI uses custom React hooks to fetch and mutate data:

```tsx
import {
  useGetConfig,
  useGetApprovalChecklist,
  useValidateConfig,
  useGetAuditLogs,
  useApproveConfig,
  useRejectConfig,
  useActivateConfig,
} from '@/hooks/useAgentConfigApi'

// Fetch config
const { data: config, loading, error, fetch } = useGetConfig(configId)

// Fetch approval checklist
const { data: checklist, loading, error, fetch } = useGetApprovalChecklist(configId)

// Validate config
const { data: validation, loading, error, fetch } = useValidateConfig(configId)

// Get audit logs
const { data: logs, loading, error, fetch } = useGetAuditLogs(configId)

// Approve config
const { approve, loading, error } = useApproveConfig()
await approve(configId, 'feedback')

// Reject config
const { reject, loading, error } = useRejectConfig()
await reject(configId, 'feedback')

// Activate config
const { activate, loading, error } = useActivateConfig()
await activate(configId)
```

### API Endpoints

The UI calls these backend endpoints:

```
GET    /api/v1/agent-configs/{config_id}
GET    /api/v1/agent-configs/{config_id}/approval-checklist
GET    /api/v1/agent-configs/{config_id}/validate
GET    /api/v1/agent-configs/{config_id}/audit
POST   /api/v1/agent-configs/{config_id}/approve
POST   /api/v1/agent-configs/{config_id}/reject
POST   /api/v1/agent-configs/{config_id}/activate
```

## Styling

The UI uses **Tailwind CSS** for styling. Ensure Tailwind is configured in your Next.js project:

```js
// tailwind.config.js
module.exports = {
  content: [
    './src/**/*.{js,jsx,ts,tsx}',
  ],
  theme: {
    extend: {},
  },
}
```

## Integration Steps

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Copy Components

Components are in `/frontend/src/components/AgentConfigApproval/`:
- `ApprovalDashboard.tsx`
- `ApprovalDetailPage.tsx`
- `ValidationChecklist.tsx`
- `ConfigComparison.tsx`
- `AuditTimeline.tsx`
- `types.ts`
- `index.ts`

Hooks are in `/frontend/src/hooks/`:
- `useAgentConfigApi.ts`

### 3. Add Route

```tsx
// app/admin/approvals/page.tsx
import { ApprovalDashboard } from '@/components/AgentConfigApproval'

export default function ApprovalsPage() {
  return (
    <div className="max-w-7xl mx-auto py-8 px-4">
      <ApprovalDashboard />
    </div>
  )
}
```

### 4. Add Navigation Link

```tsx
// components/Sidebar.tsx
<Link href="/admin/approvals">
  ✓ Approvals
</Link>
```

## Data Flow

```
ApprovalDashboard (list view)
    ↓
  [click item]
    ↓
ApprovalDetailPage (detail view)
    ├─→ ValidationChecklist (tab)
    │   └─→ useGetApprovalChecklist()
    ├─→ ConfigComparison (tab)
    │   ├─→ useGetConfig()
    │   └─→ [compare with active config]
    └─→ AuditTimeline (tab)
        └─→ useGetAuditLogs()
    ↓
  [approve/reject button]
    ↓
  [confirmation modal]
    ↓
  useApproveConfig() or useRejectConfig()
    ↓
  API call
    ↓
  onApprovalComplete()
    ↓
  [back to dashboard]
```

## Production Checklist

- [ ] Tailwind CSS configured in project
- [ ] Backend API endpoints implemented
- [ ] Authentication guards added (only admins access)
- [ ] Error handling tested
- [ ] Loading states verified
- [ ] Confirmation modals tested
- [ ] Responsive design on mobile/tablet
- [ ] Accessibility tested (keyboard nav, screen readers)
- [ ] Performance optimized (lazy load tabs)
- [ ] Audit logging working
- [ ] Rate limiting on approve/reject endpoints

## Customization

### Change Colors

Edit color classes in components (e.g., `bg-green-600` → `bg-blue-600`):

```tsx
// ValidationChecklist.tsx
<span className="text-green-600 text-xl">✓</span>
// Change to:
<span className="text-blue-600 text-xl">✓</span>
```

### Change Icons

Replace emoji icons with SVG icons:

```tsx
// Before:
<span className="text-green-600 text-xl">✓</span>

// After:
import { CheckIcon } from '@heroicons/react/24/outline'
<CheckIcon className="w-5 h-5 text-green-600" />
```

### Add More Tabs

In `ApprovalDetailPage.tsx`:

```tsx
const [activeTab, setActiveTab] = useState<TabType>("checklist")

// Add "metrics" to TabType
type TabType = "checklist" | "comparison" | "audit" | "metrics"

// Add tab button
<button onClick={() => setActiveTab("metrics")} ...>Metrics</button>

// Add tab content
{activeTab === "metrics" && <MetricsPanel />}
```

## Testing

### Unit Tests

```tsx
// __tests__/ApprovalDashboard.test.tsx
import { render, screen } from '@testing-library/react'
import { ApprovalDashboard } from '@/components/AgentConfigApproval'

describe('ApprovalDashboard', () => {
  it('renders pending approvals', () => {
    render(<ApprovalDashboard />)
    expect(screen.getByText(/pending/i)).toBeInTheDocument()
  })
})
```

### E2E Tests (Cypress)

```js
// cypress/e2e/approvals.cy.js
describe('Approval Workflow', () => {
  it('approves a configuration', () => {
    cy.visit('/admin/approvals')
    cy.contains('Cultural Fit Screener').click()
    cy.contains('Approve').click()
    cy.contains('Approve Configuration').should('be.visible')
    cy.contains('Confirm Approve').click()
    cy.contains('Approval completed')
  })
})
```

## Performance Optimization

### Lazy Load Tabs

```tsx
const ValidationChecklist = lazy(() => import('./ValidationChecklist'))
const ConfigComparison = lazy(() => import('./ConfigComparison'))
const AuditTimeline = lazy(() => import('./AuditTimeline'))

export const ApprovalDetailPage = () => {
  return (
    <Suspense fallback={<Loading />}>
      {activeTab === "checklist" && <ValidationChecklist />}
    </Suspense>
  )
}
```

### Memoize Heavy Components

```tsx
import { memo } from 'react'

export const ValidationChecklist = memo(
  function ValidationChecklist({ validation }) {
    // component code
  }
)
```

### Virtualize Long Lists

For dashboards with 100+ pending approvals:

```tsx
import { FixedSizeList } from 'react-window'

<FixedSizeList
  height={600}
  itemCount={approvals.length}
  itemSize={120}
>
  {({ index, style }) => (
    <div style={style}>
      {/* approval item */}
    </div>
  )}
</FixedSizeList>
```

## Accessibility

All components follow WCAG 2.1 AA standards:

- ✓ Semantic HTML (button, form, dialog)
- ✓ ARIA labels for icons
- ✓ Keyboard navigation (Tab, Enter, Escape)
- ✓ Color contrast ratios > 4.5:1
- ✓ Focus indicators on all interactive elements
- ✓ Loading states announced to screen readers

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Deployment

### Build

```bash
npm run build
# Produces optimized bundle in .next/
```

### Deploy to Vercel

```bash
vercel deploy
```

### Deploy to Self-Hosted

```bash
npm run build
npm start
# Server runs on port 3000
```

## Troubleshooting

### Problem: Approval checklist not loading

**Solution:** Check backend endpoint is running and accessible:
```bash
curl http://localhost:8000/api/v1/agent-configs/test-id/approval-checklist
```

### Problem: Styles not applied (Tailwind)

**Solution:** Rebuild Tailwind:
```bash
npm run build
# Or in dev mode, Tailwind rebuilds automatically
```

### Problem: Infinite loading state

**Solution:** Check API response format matches expected type:
```tsx
// Expected format
{
  config_id: string,
  version_number: number,
  validation: { ... },
  version_checks: { ... },
  approval_items: [ ... ],
  recommendation: string
}
```

## Support

For issues or questions:
1. Check this guide
2. Review component source code comments
3. Check backend API documentation
4. Open an issue in the repo

