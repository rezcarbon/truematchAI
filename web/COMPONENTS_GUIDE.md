# TrueMatch UI Components Guide

Comprehensive documentation for the Career Coach, Applications, and Portal Dashboard UI components.

## Table of Contents

1. [Career Coach Components](#career-coach-components)
2. [Applications Components](#applications-components)
3. [Portal Dashboard Components](#portal-dashboard-components)
4. [Shared Components](#shared-components)

---

## Career Coach Components

### GuidanceCard

A structured response display for career guidance with numbered steps, time estimates, and resource links.

**Location**: `src/components/chat/GuidanceCard.tsx`

**Props**:
- `title` (string): Main title of the guidance
- `description` (string): Brief description
- `steps` (GuidanceStep[]): Array of learning steps
- `difficulty` ('Beginner' | 'Intermediate' | 'Advanced'): Difficulty level
- `totalTime?` (number): Optional override for total time calculation
- `onStepClick?` (callback): Called when a step is clicked
- `className?` (string): Additional CSS classes

**Usage Example**:
```tsx
import { GuidanceCard } from '@/components/chat';

<GuidanceCard
  title="Web Development Fundamentals"
  description="Master the basics of modern web development"
  difficulty="Beginner"
  steps={[
    {
      number: 1,
      title: "Learn HTML",
      description: "Understand semantic HTML and structure",
      estimatedTime: 30,
      resources: [
        { title: "MDN HTML Guide", url: "https://...", type: "docs" }
      ]
    },
    // ... more steps
  ]}
  onStepClick={(stepNum) => console.log(`Step ${stepNum} clicked`)}
/>
```

**Features**:
- Difficulty badges with color coding
- Numbered steps with time estimates
- Resource links with icons (Coursera, GitHub, communities)
- Total time calculation
- Keyboard accessible
- Performance optimized with useMemo

---

### LearningPath

Visual learning path component showing step-by-step progression with completion tracking.

**Location**: `src/components/chat/LearningPath.tsx`

**Props**:
- `title` (string): Path title
- `description?` (string): Optional description
- `steps` (LearningPathStep[]): Array of path steps
- `currentStepIndex?` (number): Index of current step (default: 0)
- `onStepClick?` (callback): Called when step is clicked
- `onCompleteStep?` (callback): Called when step is marked complete
- `className?` (string): Additional CSS classes

**Step Status**: 'completed' | 'current' | 'locked' | 'upcoming'

**Usage Example**:
```tsx
import { LearningPath } from '@/components/chat';

<LearningPath
  title="Advanced TypeScript Path"
  description="Master TypeScript for enterprise development"
  currentStepIndex={1}
  steps={[
    {
      id: 'ts-basics',
      title: 'TypeScript Basics',
      description: 'Learn type system fundamentals',
      status: 'completed',
      estimatedTime: 45,
      completedAt: '2026-07-05T10:00:00Z'
    },
    {
      id: 'ts-advanced',
      title: 'Advanced Types',
      description: 'Generics, unions, and discriminated unions',
      status: 'current',
      estimatedTime: 60,
      resources: [
        { title: "TypeScript Handbook", url: "https://..." }
      ]
    },
    // ... more steps
  ]}
  onStepClick={(stepId, index) => console.log(`Clicked step: ${stepId}`)}
  onCompleteStep={(stepId, index) => console.log(`Completed step: ${stepId}`)}
/>
```

**Features**:
- Progress bar with percentage
- Step completion tracking
- Animated pulse on current step
- Locked step handling
- Timeline connector lines
- Statistics (total time, completion %)
- Responsive design

---

## Applications Components

### ApplicationPipeline

Horizontal stage visualization showing application progress through pipeline stages.

**Location**: `src/components/candidate/ApplicationPipeline.tsx`

**Stages**: 'applied' | 'screened' | 'interviewed' | 'offer' | 'closed'

**Props**:
- `applicationId` (string): Unique application ID
- `currentStage` (ApplicationStage): Current pipeline stage
- `stageTimestamps?` (Record): Timestamps for each stage
- `isActive?` (boolean): Whether application is active (default: true)
- `onStageClick?` (callback): Called when stage indicator is clicked
- `className?` (string): Additional CSS classes

**Usage Example**:
```tsx
import { ApplicationPipeline } from '@/components/candidate';

<ApplicationPipeline
  applicationId="app_123"
  currentStage="interviewed"
  stageTimestamps={{
    applied: '2026-06-15T10:00:00Z',
    screened: '2026-06-20T14:30:00Z',
    interviewed: '2026-07-01T09:00:00Z'
  }}
  isActive={true}
  onStageClick={(stage) => console.log(`Stage: ${stage}`)}
/>
```

**Features**:
- Visual stage indicators with icons
- Progress tracking
- Stage date display
- Connected stage flow
- Completed/current/upcoming status
- Next step indication
- Closed application alert
- Color-coded stages

---

### ApplicationCard

Card component for displaying job application information with quick actions.

**Location**: `src/components/candidate/ApplicationCard.tsx`

**Props**:
- `id` (string): Application ID
- `jobTitle` (string): Job title
- `company` (string): Company name
- `stage` (ApplicationStage): Current stage
- `appliedDate` (string): When applied (ISO string)
- `stageDate?` (string): When stage changed (ISO string)
- `logo?` (string): Company logo URL
- `matchScore?` (number): Match percentage
- `location?` (string): Job location
- `onViewDetails` (callback): Handle view details click
- `onTrackStatus?` (callback): Handle track status click
- `className?` (string): Additional CSS classes

**Usage Example**:
```tsx
import { ApplicationCard } from '@/components/candidate';

<ApplicationCard
  id="app_456"
  jobTitle="Senior Software Engineer"
  company="TechCorp Inc"
  stage="interviewed"
  appliedDate="2026-06-15T10:00:00Z"
  stageDate="2026-07-01T09:00:00Z"
  logo="https://..."
  matchScore={85}
  location="San Francisco, CA"
  onViewDetails={(id) => router.push(`/applications/${id}`)}
  onTrackStatus={(id) => console.log(`Track: ${id}`)}
/>
```

**Features**:
- Company logo display
- Stage badge with color coding
- Date tracking (applied and stage changed)
- Days since applied calculation
- Match score progress bar
- Quick action buttons
- Hover effects and transitions

---

### TimelineView

Timeline display for application events with actor information and details.

**Location**: `src/components/candidate/TimelineView.tsx`

**Event Types**: 'applied' | 'screened' | 'interviewed' | 'offer' | 'feedback' | 'update' | 'rejection' | 'other'

**Props**:
- `events` (TimelineEvent[]): Array of timeline events
- `title?` (string): Timeline title (default: "Application Timeline")
- `className?` (string): Additional CSS classes

**Event Structure**:
```tsx
interface TimelineEvent {
  id: string;
  type: TimelineEventType;
  title: string;
  description?: string;
  timestamp: string; // ISO string
  actor?: {
    name: string;
    role?: string;
    avatar?: string;
  };
  details?: Record<string, unknown>;
}
```

**Usage Example**:
```tsx
import { TimelineView } from '@/components/candidate';

<TimelineView
  title="Application Timeline"
  events={[
    {
      id: '1',
      type: 'applied',
      title: 'Application Submitted',
      description: 'Your application has been received',
      timestamp: '2026-06-15T10:00:00Z',
      actor: { name: 'System' }
    },
    {
      id: '2',
      type: 'screened',
      title: 'Screening Complete',
      description: 'Your profile meets our requirements',
      timestamp: '2026-06-20T14:30:00Z',
      actor: {
        name: 'Sarah Chen',
        role: 'Recruiting Manager',
        avatar: 'https://...'
      }
    },
    // ... more events
  ]}
/>
```

**Features**:
- Chronological event display
- Event type badges
- Actor avatars and roles
- Relative time formatting
- Event details display
- Empty state handling
- Color-coded event types

---

### ApplicationDetail

Modal component for detailed application information with multiple tabs.

**Location**: `src/components/candidate/ApplicationDetail.tsx`

**Props**:
- `open` (boolean): Modal open state
- `onOpenChange` (callback): Called when modal state changes
- `applicationId` (string): Application ID
- `jobTitle` (string): Job title
- `company` (string): Company name
- `stage` (ApplicationStage): Current stage
- `appliedDate` (string): Application date (ISO string)
- `jobDescription?` (string): Full job description
- `salary?` (object): Salary range
- `location?` (string): Job location
- `companyWebsite?` (string): Company website URL
- `applicationUrl?` (string): Application portal URL
- `feedback?` (object): Recruiter feedback
- `offer?` (object): Offer details
- `timelineEvents` (TimelineEvent[]): Application timeline
- `onInterviewPrepClick?` (callback): Interview prep clicked
- `className?` (string): Additional CSS classes

**Tabs**:
- Overview: Job details and description
- Timeline: Event history
- Feedback: Recruiter feedback (if available)
- Offer: Offer details (if available)

**Usage Example**:
```tsx
import { ApplicationDetail } from '@/components/candidate';

const [detailOpen, setDetailOpen] = useState(false);

<ApplicationDetail
  open={detailOpen}
  onOpenChange={setDetailOpen}
  applicationId="app_789"
  jobTitle="Staff Engineer"
  company="InnovateCorp"
  stage="offer"
  appliedDate="2026-05-01T10:00:00Z"
  jobDescription="Lead technical strategy..."
  salary={{ min: 150000, max: 200000, currency: 'USD' }}
  location="Remote"
  offer={{
    details: "We're pleased to offer you...",
    salary: "USD 175,000 - 190,000",
    benefits: ["Health Insurance", "401k", "Remote Work", "PTO"],
    deadline: "2026-07-15T23:59:59Z"
  }}
  timelineEvents={events}
  onInterviewPrepClick={(appId) => router.push(`/interview-prep/${appId}`)}
/>
```

**Features**:
- Multi-tab interface
- Full job description display
- Salary range display
- Offer details with benefits
- Company information
- Timeline integration
- Interview prep button
- Responsive modal

---

## Portal Dashboard Components

### AssessmentSummary

Latest assessment summary card with scores and next steps.

**Location**: `src/components/candidate/AssessmentSummary.tsx`

**Props**:
- `assessment` (Assessment): Assessment data object
- `className?` (string): Additional CSS classes
- `onViewAnalysis?` (callback): Called when view analysis clicked

**Usage Example**:
```tsx
import { AssessmentSummary } from '@/components/candidate';

<AssessmentSummary
  assessment={mockAssessment}
  onViewAnalysis={() => router.push(`/assessment/${assessment.id}`)}
/>
```

**Features**:
- Three-score display (Traditional, Semantic, Capability)
- Color-coded scores
- Top strengths display
- Learning opportunities section
- Assessment date display
- View full analysis button
- Performance optimized with useMemo

---

### ThreeSignalScores

Three gauge visualization for assessment scores with interpretation guide.

**Location**: `src/components/shared/ThreeSignalScores.tsx`

**Props**:
- `traditional` (ScoreGaugeProps): Traditional score info
- `semantic` (ScoreGaugeProps): Semantic score info
- `capability` (ScoreGaugeProps): Capability score info
- `className?` (string): Additional CSS classes

**ScoreGaugeProps**:
```tsx
interface ScoreGaugeProps {
  label: string;
  score: number; // 0-100
  delta?: number; // Change from previous
  description?: string;
  icon?: React.ReactNode;
}
```

**Usage Example**:
```tsx
import { ThreeSignalScores } from '@/components/shared';

<ThreeSignalScores
  traditional={{
    label: 'Traditional',
    score: 75,
    delta: 5,
    description: 'Keyword match score'
  }}
  semantic={{
    label: 'Semantic',
    score: 82,
    delta: 3,
    description: 'Concept-level match'
  }}
  capability={{
    label: 'Capability',
    score: 88,
    delta: -2,
    description: 'TrueMatch capability'
  }}
/>
```

**Features**:
- Animated circular gauges
- Color-coded scores (green/amber/red)
- Delta indicators (up/down/stable)
- Average score calculation
- Signal interpretation guide
- Responsive grid layout

---

### StatCards

Statistics grid showing key metrics.

**Location**: `src/components/candidate/StatCards.tsx`

**Props**:
- `stats` (StatCardData[]): Array of stat card data
- `className?` (string): Additional CSS classes

**StatCardData**:
```tsx
interface StatCardData {
  label: string;
  value: number | string;
  icon: React.ReactNode;
  trend?: { value: number; direction: 'up' | 'down' | 'stable' };
  description?: string;
  suffix?: string;
  color?: 'blue' | 'green' | 'purple' | 'amber';
}
```

**Usage Example**:
```tsx
import { StatCards } from '@/components/candidate';

<StatCards
  stats={[
    {
      label: 'Assessments Completed',
      value: 5,
      icon: <CheckCircle2 className="w-6 h-6" />,
      trend: { value: 20, direction: 'up' },
      description: 'In the last 30 days',
      color: 'blue'
    },
    {
      label: 'Average Score',
      value: 76,
      icon: <TrendingUp className="w-6 h-6" />,
      trend: { value: 5, direction: 'up' },
      suffix: '%',
      color: 'green'
    },
    // ... more stats
  ]}
/>
```

**Features**:
- Color-coded cards
- Trend indicators
- Icon support
- Responsive grid (1-4 columns)
- Default stats when empty
- Hover effects

---

### ActivityFeed

Recent activity feed with event types and actions.

**Location**: `src/components/candidate/ActivityFeed.tsx`

**Activity Types**: 'assessment' | 'application' | 'message' | 'interview' | 'offer' | 'update' | 'notification' | 'other'

**Props**:
- `items` (ActivityFeedItem[]): Array of activity items
- `title?` (string): Feed title (default: "Recent Activity")
- `className?` (string): Additional CSS classes
- `maxItems?` (number): Max items to show (default: 5)
- `onViewAll?` (callback): Called when view all clicked

**ActivityFeedItem**:
```tsx
interface ActivityFeedItem {
  id: string;
  type: ActivityType;
  title: string;
  description?: string;
  timestamp: string; // ISO string
  actor?: {
    name: string;
    avatar?: string;
  };
  actionLabel?: string;
  onAction?: () => void;
}
```

**Usage Example**:
```tsx
import { ActivityFeed } from '@/components/candidate';

<ActivityFeed
  title="Your Recent Activity"
  items={[
    {
      id: '1',
      type: 'assessment',
      title: 'Assessment Completed',
      description: 'You completed the Senior Engineer assessment',
      timestamp: new Date().toISOString(),
      actor: { name: 'System' }
    },
    {
      id: '2',
      type: 'interview',
      title: 'Interview Scheduled',
      description: 'Your interview is scheduled for tomorrow',
      timestamp: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
      actor: { name: 'Sarah Chen', avatar: 'https://...' },
      actionLabel: 'Prepare',
      onAction: () => router.push('/interview-prep')
    },
    // ... more items
  ]}
  maxItems={5}
  onViewAll={() => router.push('/activity')}
/>
```

**Features**:
- Activity type badges
- Actor avatars
- Relative time display
- Action buttons
- Empty state
- Item limiting with view all
- Color-coded types
- Empty state display

---

## Component Architecture

### Performance Optimizations

All components use performance optimizations:
- `React.memo` for component memoization
- `useMemo` for expensive calculations
- `useCallback` for stable callback references
- Proper dependency arrays to prevent unnecessary re-renders

### Accessibility

Components follow accessibility best practices:
- ARIA labels and roles
- Keyboard navigation support
- Semantic HTML
- Color contrast compliance
- Focus management

### Styling

All components use:
- Tailwind CSS for styling
- Custom theme variables
- Dark mode support via `dark:` classes
- Responsive design (mobile-first)
- Consistent spacing and typography

### TypeScript

- Strict TypeScript types for all props
- Exported interfaces for component props
- Union types for enums
- Proper generics where applicable

---

## Testing

All components have comprehensive test coverage (80%+):
- Unit tests for rendering
- Integration tests for user interactions
- Accessibility tests
- Edge case handling
- Mock data patterns

**Test location**: `src/__tests__/components/`

### Running Tests

```bash
npm test
npm test -- --coverage  # With coverage report
```

---

## Integration Guide

### In Pages

```tsx
import { ApplicationCard, TimelineView } from '@/components/candidate';
import { StatCards, ActivityFeed } from '@/components/candidate';
import { ThreeSignalScores } from '@/components/shared';

export default function DashboardPage() {
  return (
    <div className="space-y-8">
      <StatCards stats={stats} />
      <ThreeSignalScores {...scoreProps} />
      <ActivityFeed items={activities} />
    </div>
  );
}
```

### With Data Fetching

```tsx
'use client';
import { useState, useEffect } from 'react';
import { ApplicationCard } from '@/components/candidate';

export default function ApplicationsPage() {
  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchApplications() {
      const response = await fetch('/api/applications');
      const data = await response.json();
      setApplications(data);
      setLoading(false);
    }

    fetchApplications();
  }, []);

  if (loading) return <div>Loading...</div>;

  return (
    <div className="grid gap-4">
      {applications.map((app) => (
        <ApplicationCard
          key={app.id}
          {...app}
          onViewDetails={handleViewDetails}
        />
      ))}
    </div>
  );
}
```

---

## Component Dependencies

All components have minimal dependencies:
- React (core)
- Next.js (framework)
- shadcn/ui (UI primitives)
- Tailwind CSS (styling)
- lucide-react (icons)

No external state management required - components use React hooks and props.

---

## Best Practices

1. **Use TypeScript interfaces**: Always type your props
2. **Memoize components**: Use `React.memo` for optimization
3. **Stable callbacks**: Use `useCallback` for event handlers
4. **Test coverage**: Aim for 80%+ coverage
5. **Accessibility**: Follow WCAG guidelines
6. **Performance**: Monitor component render counts
7. **Documentation**: Keep JSDoc comments updated

---

## Support

For issues or feature requests, refer to the component source files or test files for usage examples and edge cases.
