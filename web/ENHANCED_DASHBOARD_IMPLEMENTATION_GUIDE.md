# Enhanced Candidate Portal Dashboard - Implementation & Integration Guide

## Quick Start

### 1. Component Location
```
src/components/candidate/EnhancedDashboard.tsx
src/app/candidate/dashboard/page.tsx (updated to use new component)
```

### 2. Install Dependencies (if not already present)
```bash
npm install recharts lucide-react
```

### 3. Component Import
```typescript
import { EnhancedDashboard } from "@/components/candidate/EnhancedDashboard";
```

### 4. Basic Usage
```tsx
<EnhancedDashboard
  assessment={assessmentData}
  assessmentCount={3}
  averageScore={84}
  activeApplications={2}
  recentActivity={activityData}
/>
```

---

## Detailed Integration Steps

### Step 1: File Setup ✅ DONE

**Created Files**:
1. `src/components/candidate/EnhancedDashboard.tsx` - Main component
2. Documentation files (see below)

**Updated Files**:
1. `src/app/candidate/dashboard/page.tsx` - Integrated new component

### Step 2: Component Props

Define the data structure you'll pass to the component:

```typescript
interface EnhancedDashboardProps {
  // Assessment data (required)
  assessment: Assessment;
  
  // Metrics (required)
  assessmentCount: number;
  averageScore: number;
  activeApplications: number;
  
  // Optional activity feed
  recentActivity?: Array<{
    id: string;
    type: 'assessment' | 'application' | 'message' | 'update';
    title: string;
    description: string;
    timestamp: string;
    icon?: React.ReactNode;
  }>;
}
```

### Step 3: Data Integration

#### Option A: Use Mock Data (Development)
```typescript
import { mockAssessment } from "@/lib/mock";

export default function CandidateDashboard() {
  return (
    <EnhancedDashboard
      assessment={mockAssessment}
      assessmentCount={3}
      averageScore={84}
      activeApplications={2}
    />
  );
}
```

#### Option B: Fetch from API (Production)
```typescript
'use client';

import { useEffect, useState } from 'react';
import { EnhancedDashboard } from "@/components/candidate/EnhancedDashboard";

export default function CandidateDashboard() {
  const [assessmentData, setAssessmentData] = useState(null);
  const [stats, setStats] = useState({
    count: 0,
    average: 0,
    active: 0,
  });
  const [activity, setActivity] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Fetch latest assessment
        const assessRes = await fetch('/api/proxy/assessments/latest');
        const assessment = await assessRes.json();
        setAssessmentData(assessment);

        // Fetch stats
        const countRes = await fetch('/api/proxy/assessments/count');
        const countData = await countRes.json();

        const avgRes = await fetch('/api/proxy/assessments/average');
        const avgData = await avgRes.json();

        const activeRes = await fetch('/api/proxy/applications/active');
        const activeData = await activeRes.json();

        setStats({
          count: countData.count || 0,
          average: avgData.average || 0,
          active: activeData.count || 0,
        });

        // Fetch activity feed
        const actRes = await fetch('/api/proxy/activity?limit=10');
        const actData = await actRes.json();
        setActivity(actData);

        setLoading(false);
      } catch (err) {
        console.error('Failed to load dashboard data:', err);
        setError(err.message);
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) return <div>Loading dashboard...</div>;
  if (error) return <div>Error: {error}</div>;
  if (!assessmentData) return <div>No assessment data available</div>;

  return (
    <EnhancedDashboard
      assessment={assessmentData}
      assessmentCount={stats.count}
      averageScore={stats.average}
      activeApplications={stats.active}
      recentActivity={activity}
    />
  );
}
```

### Step 4: API Endpoints Required

For production, implement these API endpoints:

```typescript
// 1. Get latest assessment
GET /api/proxy/assessments/latest
Response: Assessment

// 2. Get assessment count
GET /api/proxy/assessments/count
Response: { count: number }

// 3. Get average capability score
GET /api/proxy/assessments/average
Response: { average: number }

// 4. Get active applications count
GET /api/proxy/applications/active
Response: { count: number }

// 5. Get activity feed
GET /api/proxy/activity?limit=10&offset=0
Response: Activity[]

// 6. Get single assessment (for details page)
GET /api/proxy/assessments/{id}
Response: Assessment
```

### Step 5: Styling

The component uses Tailwind CSS classes. Ensure your `tailwind.config.js` includes:

```javascript
module.exports = {
  content: [
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: 'hsl(221, 83%, 53%)',
        success: 'rgb(16, 185, 129)',
        destructive: 'rgb(239, 68, 68)',
      },
    },
  },
};
```

### Step 6: Testing

#### Unit Tests
```typescript
import { render, screen } from '@testing-library/react';
import { EnhancedDashboard } from '@/components/candidate/EnhancedDashboard';
import { mockAssessment } from '@/lib/mock';

describe('EnhancedDashboard', () => {
  it('renders assessment summary', () => {
    render(
      <EnhancedDashboard
        assessment={mockAssessment}
        assessmentCount={3}
        averageScore={84}
        activeApplications={2}
      />
    );
    expect(screen.getByText(mockAssessment.positionTitle)).toBeInTheDocument();
  });

  it('displays three-signal gauges', () => {
    render(
      <EnhancedDashboard
        assessment={mockAssessment}
        assessmentCount={3}
        averageScore={84}
        activeApplications={2}
      />
    );
    expect(screen.getByText('Traditional ATS Score')).toBeInTheDocument();
    expect(screen.getByText('Capability Score')).toBeInTheDocument();
  });

  it('shows stats cards', () => {
    render(
      <EnhancedDashboard
        assessment={mockAssessment}
        assessmentCount={3}
        averageScore={84}
        activeApplications={2}
      />
    );
    expect(screen.getByText('Assessments')).toBeInTheDocument();
    expect(screen.getByText('84')).toBeInTheDocument(); // average score
    expect(screen.getByText('Active')).toBeInTheDocument();
  });

  it('renders strengths section', () => {
    render(
      <EnhancedDashboard
        assessment={mockAssessment}
        assessmentCount={3}
        averageScore={84}
        activeApplications={2}
      />
    );
    expect(screen.getByText('Top Strengths')).toBeInTheDocument();
  });

  it('renders next steps guidance', () => {
    render(
      <EnhancedDashboard
        assessment={mockAssessment}
        assessmentCount={3}
        averageScore={84}
        activeApplications={2}
      />
    );
    expect(screen.getByText('Recommended Next Steps')).toBeInTheDocument();
  });
});
```

#### Integration Tests
```typescript
// Test navigation
it('navigates to browse roles on click', async () => {
  const { user } = render(
    <EnhancedDashboard
      assessment={mockAssessment}
      assessmentCount={3}
      averageScore={84}
      activeApplications={2}
    />
  );
  
  const browseButton = screen.getByText('Browse roles');
  await user.click(browseButton);
  expect(router.pathname).toBe('/candidate/jobs');
});
```

### Step 7: Error Handling

Add error boundaries:

```typescript
import { ErrorBoundary } from 'react-error-boundary';

function ErrorFallback({ error, resetErrorBoundary }: any) {
  return (
    <div role="alert" className="p-4 bg-red-50 border border-red-200 rounded">
      <h2 className="font-bold text-red-900">Something went wrong loading your dashboard</h2>
      <p className="text-red-700 mt-2">{error.message}</p>
      <button
        onClick={resetErrorBoundary}
        className="mt-4 px-4 py-2 bg-red-600 text-white rounded"
      >
        Try again
      </button>
    </div>
  );
}

export default function CandidateDashboard() {
  return (
    <ErrorBoundary FallbackComponent={ErrorFallback}>
      <EnhancedDashboard
        assessment={assessment}
        assessmentCount={count}
        averageScore={average}
        activeApplications={active}
      />
    </ErrorBoundary>
  );
}
```

### Step 8: Loading States

Add loading skeleton:

```typescript
function DashboardSkeleton() {
  return (
    <div className="space-y-6">
      <div className="h-64 bg-gray-200 rounded animate-pulse" />
      <div className="grid grid-cols-3 gap-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-32 bg-gray-200 rounded animate-pulse" />
        ))}
      </div>
    </div>
  );
}

export default function CandidateDashboard() {
  const [loading, setLoading] = useState(true);

  if (loading) return <DashboardSkeleton />;

  return <EnhancedDashboard {...props} />;
}
```

---

## Customization & Extension

### Adding Custom Activity Types

```typescript
const customActivity = {
  id: '123',
  type: 'custom_event',
  title: 'Custom event title',
  description: 'Custom event description',
  timestamp: new Date().toISOString(),
  icon: <CustomIcon />,
};
```

### Modifying Next Steps

Edit the `nextSteps` array in the component:

```typescript
const nextSteps = [
  {
    title: 'Custom Step Title',
    description: 'Your custom description',
    icon: CustomIcon,
    actionText: 'Action',
    actionHref: '/your/path',
  },
  // ... more steps
];
```

### Customizing Colors

Update color classes in the component:

```typescript
// For badges
const getMatchTypeBadgeClass = (matchType?: string) => {
  const classes: Record<string, string> = {
    hidden_gem: 'bg-purple-50 text-purple-700 border-purple-200',
    // ... other types
  };
  return classes[matchType || ''] || 'bg-slate-50';
};
```

### Adding New Sections

Add sections following the existing pattern:

```typescript
<Card>
  <CardHeader>
    <CardTitle>New Section</CardTitle>
    <CardDescription>Description</CardDescription>
  </CardHeader>
  <CardContent>
    {/* Your content here */}
  </CardContent>
</Card>
```

---

## Deployment

### Build
```bash
npm run build
```

### Environment Setup
```
No environment variables required for current implementation.
For API integration, add:
NEXT_PUBLIC_API_URL=your_api_url
```

### Deploy to Production
```bash
# Vercel
vercel deploy

# Docker
docker build . -t truematch:latest
docker run truematch:latest

# Traditional server
npm run start
```

---

## Performance Optimization

### 1. Lazy Load Activity Feed
```typescript
const [showAllActivity, setShowAllActivity] = useState(false);
const displayedActivity = showAllActivity ? activityFeed : activityFeed.slice(0, 3);
```

### 2. Memoize Component
```typescript
export const EnhancedDashboard = memo(function Dashboard(props) {
  // component code
});
```

### 3. Code Splitting
```typescript
const EnhancedDashboard = dynamic(
  () => import('@/components/candidate/EnhancedDashboard'),
  { loading: () => <DashboardSkeleton /> }
);
```

### 4. Image Optimization
If adding images:
```typescript
import Image from 'next/image';

<Image
  src="/assessment-badge.png"
  alt="Assessment badge"
  width={100}
  height={100}
/>
```

---

## Troubleshooting

### Issue: Component not rendering
**Solution**: Check that all imports are correct and dependencies are installed
```bash
npm install recharts lucide-react @/components/ui/card @/components/ui/button
```

### Issue: Gauge not displaying
**Solution**: Ensure `ScoreGauge` and `Gauge` components are available
```bash
ls src/components/shared/ScoreGauge.tsx
ls src/components/ui/gauge.tsx
```

### Issue: Styles not applied
**Solution**: Verify Tailwind CSS is configured
```bash
# Check tailwind config
cat tailwind.config.js

# Rebuild CSS
npm run build
```

### Issue: Activity feed shows mock data
**Solution**: Pass `recentActivity` prop with real data
```typescript
<EnhancedDashboard
  {...props}
  recentActivity={realActivityData}
/>
```

### Issue: Navigation links not working
**Solution**: Verify Next.js Link component is working
```typescript
// Ensure routes exist
ls -la src/app/candidate/jobs
ls -la src/app/candidate/profile
```

---

## Migration from Old Dashboard

If migrating from an existing dashboard:

### 1. Backup existing component
```bash
mv src/app/candidate/dashboard/page.tsx src/app/candidate/dashboard/page.tsx.backup
```

### 2. Check data structure
Ensure your `Assessment` type matches:
```typescript
interface Assessment {
  id: string;
  positionTitle: string;
  createdAt: string;
  matchType?: string;
  traditionalScore: number;
  semanticScore?: number;
  capabilityScore: {
    overall: number;
    components: Array<{
      key: string;
      label: string;
      score: number;
      weight: number;
    }>;
  };
  delta: number;
  narrative?: string;
}
```

### 3. Update imports
Replace old component imports with new:
```typescript
// Old
import { OldDashboard } from '@/components/old/OldDashboard';

// New
import { EnhancedDashboard } from '@/components/candidate/EnhancedDashboard';
```

### 4. Update props
Map old props to new structure:
```typescript
<EnhancedDashboard
  assessment={oldData.assessment}
  assessmentCount={oldData.totalAssessments}
  averageScore={oldData.avgScore}
  activeApplications={oldData.activeApps}
  recentActivity={transformActivity(oldData.activityLog)}
/>
```

### 5. Test thoroughly
- [ ] All sections render
- [ ] Navigation works
- [ ] Responsive on mobile
- [ ] No console errors

---

## Documentation Files

| File | Purpose |
|------|---------|
| `ENHANCED_DASHBOARD_DOCUMENTATION.md` | Complete feature documentation |
| `ENHANCED_DASHBOARD_MOCKUP.md` | Visual mockup and design reference |
| `ENHANCED_DASHBOARD_FEATURE_CHECKLIST.md` | Feature verification checklist |
| `ENHANCED_DASHBOARD_IMPLEMENTATION_GUIDE.md` | This file - implementation guide |

---

## Support

For issues or questions:
1. Check the documentation files
2. Review the component code
3. Check browser console for errors
4. Verify API endpoints are responding
5. Open an issue with error details

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-07-07 | Initial release |

---

**Ready to deploy!** 🚀
