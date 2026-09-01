# Applications Tracking System - Implementation Guide

## Overview

This document provides a complete guide to the Applications Tracking System, a comprehensive job application tracking solution with horizontal pipeline visualization, detailed application cards, timeline events, feedback management, AI-powered interview prep, offer details, and real-time notifications.

## What's Included

### Components

1. **HorizontalPipeline.tsx**
   - Visual pipeline showing application progression (Applied → Screened → Interviewed → Offer → Closed)
   - Progress percentage indicator
   - Interactive stage navigation
   - Status indicators (completed, current, pending)

2. **ApplicationCard.tsx**
   - Clean card-based application layout
   - Evaluation scores (Keyword, Semantic, Capability)
   - Quick action buttons
   - Status badges and metadata
   - Featured/urgent application highlighting

3. **ApplicationDetailModal.tsx**
   - Comprehensive application information display
   - Four-tab interface:
     - Overview: Scores, links, interview prep, offer details
     - Timeline: Chronological event log
     - Interviews: Interview details and feedback
     - Feedback: Team feedback and ratings
   - Quick info grid with contact and dates
   - Horizontal pipeline visualization

4. **TimelineView.tsx**
   - Chronological event visualization
   - Event categorization (status changes, interviews, feedback, offers, notes, calls)
   - Rich metadata display
   - Visual event hierarchy

5. **FeedbackSection.tsx**
   - Display feedback items with ratings (1-5 stars)
   - Calculate average rating
   - Feedback categorization (technical, cultural, communication, experience)
   - Add new feedback with structured form
   - Author and date tracking

6. **InterviewPrepWidget.tsx**
   - AI-powered preparation guide generation with Claude
   - Focus areas for the role
   - Key interview questions
   - Common challenges and solutions
   - Prep tips and recommendations
   - Copy-to-clipboard functionality

7. **OfferDetailsCard.tsx**
   - Display salary (exact or range)
   - Benefits package listing
   - Start date information
   - Expiration tracking with warning
   - Accept/Decline actions
   - Status indicators

### Types

All TypeScript types are defined in `types.ts` under the `HorizontalPipeline` namespace:

```typescript
export namespace HorizontalPipeline {
  export type ApplicationStatus = 'applied' | 'screened' | 'interviewed' | 'offer' | 'closed' | 'rejected';
  
  export interface Application {
    id: string;
    positionId: string;
    candidateName: string;
    candidateEmail: string;
    positionTitle: string;
    location?: string;
    status: ApplicationStatus;
    appliedAt: Date;
    source?: string;
    scores: ScoreBreakdown;
    tags?: string[];
    isUrgent: boolean;
    lastInterviewDate?: Date;
    nextSteps?: string;
    resumeUrl?: string;
    linkedinUrl?: string;
    interviews: InterviewInfo[];
    offer?: OfferDetails;
    timeline: TimelineEvent[];
    feedback: Feedback[];
    internalNotes?: string;
  }
  
  // Full type definitions in src/components/applications-tracker/types.ts
}
```

### Page Example

`src/app/recruiter/applications/page.tsx` demonstrates a full applications tracking page with:
- Statistics dashboard
- Search and filtering
- Multiple view modes (Gallery, Pipeline, Analytics)
- Application detail modal
- Integration with all components

### Tests

Comprehensive E2E tests in `src/components/applications-tracker/__tests__/ApplicationsTracker.test.tsx`:
- Component rendering tests
- User interaction tests
- Data flow tests
- End-to-end application journey tests

## Installation & Setup

### 1. Install Dependencies

The following packages have been added to `package.json`:

```bash
npm install
```

New dependencies:
- `@radix-ui/react-dialog@^1.1.1`
- `@radix-ui/react-icons@^1.3.0`

### 2. File Structure

```
src/
├── components/
│   ├── applications-tracker/
│   │   ├── HorizontalPipeline.tsx
│   │   ├── ApplicationCard.tsx
│   │   ├── ApplicationDetailModal.tsx
│   │   ├── TimelineView.tsx
│   │   ├── FeedbackSection.tsx
│   │   ├── InterviewPrepWidget.tsx
│   │   ├── OfferDetailsCard.tsx
│   │   ├── types.ts
│   │   ├── index.tsx
│   │   ├── __tests__/
│   │   │   └── ApplicationsTracker.test.tsx
│   │   └── README.md
│   └── ui/
│       └── dialog.tsx
├── app/
│   └── recruiter/
│       └── applications/
│           └── page.tsx
└── types/
    └── (existing types)
```

### 3. Usage Examples

#### Basic Application Card

```tsx
import { ApplicationCard } from '@/components/applications-tracker';
import type { HorizontalPipeline } from '@/components/applications-tracker';

const application: HorizontalPipeline.Application = {
  id: 'app-1',
  positionId: 'pos-1',
  candidateName: 'John Smith',
  candidateEmail: 'john@example.com',
  positionTitle: 'Senior Backend Engineer',
  status: 'interviewed',
  appliedAt: new Date(),
  scores: { keyword: 85, semantic: 78, capability: 92 },
  tags: ['Backend', 'Python'],
  isUrgent: false,
  interviews: [],
  timeline: [],
  feedback: [],
};

<ApplicationCard
  application={application}
  onViewDetails={(id) => console.log('View details:', id)}
  onScheduleInterview={(id) => console.log('Schedule interview:', id)}
/>
```

#### Horizontal Pipeline

```tsx
import { HorizontalPipeline } from '@/components/applications-tracker';

<HorizontalPipeline
  applicationStatus={{
    applicationId: 'app-1',
    currentStage: 'interviewed',
    completedStages: ['applied', 'screened'],
    timestamp: new Date(),
  }}
  onStageClick={(stageId) => console.log('Stage clicked:', stageId)}
/>
```

#### Full Application Detail Modal

```tsx
import { ApplicationDetailModal } from '@/components/applications-tracker';

<ApplicationDetailModal
  application={application}
  isOpen={isOpen}
  onClose={() => setIsOpen(false)}
  onScheduleInterview={() => handleScheduleInterview()}
  onAddFeedback={(feedback) => handleAddFeedback(feedback)}
  onGeneratePrepGuide={async (position, candidate) => {
    const response = await fetch('/api/interview-prep', {
      method: 'POST',
      body: JSON.stringify({ position, candidate }),
    });
    return response.json();
  }}
/>
```

## API Integration

The system requires the following API endpoints:

### GET `/api/v1/applications/{id}`
Fetch application details
```json
Response: HorizontalPipeline.Application
```

### GET `/api/v1/applications/{id}/timeline`
Fetch timeline events
```json
Response: HorizontalPipeline.TimelineEvent[]
```

### POST `/api/v1/applications/{id}/feedback`
Add feedback
```json
Request: {
  author: string;
  text: string;
  rating?: number;
  category?: 'technical' | 'cultural' | 'communication' | 'experience';
}
Response: HorizontalPipeline.Feedback
```

### POST `/api/interview-prep`
Generate interview prep guide with Claude
```json
Request: {
  positionTitle: string;
  candidateName: string;
}
Response: HorizontalPipeline.InterviewPrepGuide
```

### PATCH `/api/v1/applications/{id}/status`
Update application status
```json
Request: {
  status: HorizontalPipeline.ApplicationStatus;
}
Response: HorizontalPipeline.Application
```

### POST `/api/v1/applications/{id}/offer/accept`
Accept offer
```json
Response: HorizontalPipeline.Application
```

### WebSocket `/ws/applications/{id}`
Real-time updates
```json
Message: {
  type: 'status_change' | 'interview_scheduled' | 'feedback_added' | 'offer_updated';
  data: any;
}
```

## Testing

### Run All Tests

```bash
npm test
```

### Run Specific Test File

```bash
npm test ApplicationsTracker.test.tsx
```

### Run with Coverage

```bash
npm test -- --coverage
```

### Watch Mode

```bash
npm test -- --watch
```

### Test Coverage

The test suite includes:
- HorizontalPipeline component tests
- ApplicationCard component tests
- TimelineView component tests
- FeedbackSection component tests
- OfferDetailsCard component tests
- InterviewPrepWidget component tests
- ApplicationDetailModal component tests
- End-to-end application tracking flow tests

## Features in Detail

### 1. Horizontal Pipeline Visualization

The pipeline shows the progression from Applied through Closed:
- Visual indicators for completed, current, and pending stages
- Progress percentage calculation
- Interactive stage navigation
- Smooth transitions and animations

**Use Case**: Quickly see where each application stands in the hiring process

### 2. Application Cards

Cards display key information at a glance:
- Candidate name and position
- Status and time in stage
- Evaluation scores with color coding
- Quick action buttons (Details, Schedule Interview)
- Tags and source information
- Featured/urgent highlighting

**Use Case**: Browse through applications efficiently

### 3. Detailed View Modal

Comprehensive view with four tabs:

**Overview Tab**:
- Evaluation scores breakdown
- Links to resume and LinkedIn
- Interview prep widget
- Offer details (if in offer stage)

**Timeline Tab**:
- Chronological event log
- Event categorization
- Rich metadata display
- Event descriptions

**Interviews Tab**:
- All scheduled/completed interviews
- Interview type and date
- Interviewer information
- Feedback and scores

**Feedback Tab**:
- All feedback items with ratings
- Category breakdown
- Add new feedback form
- Average rating display

**Use Case**: Deep dive into a specific application

### 4. Interview Prep with Claude

AI-powered preparation guide:
- Generates focus areas for the role
- Provides key interview questions
- Highlights common challenges
- Offers prep tips
- Copy-to-clipboard for questions

**Use Case**: Prepare interview questions and anticipate candidate responses

### 5. Timeline Events

Tracks all important events:
- Application submissions
- Interview scheduling and completion
- Feedback submissions
- Offer extensions
- Call logs
- Internal notes

**Use Case**: Understand the full history of an application

### 6. Feedback Management

Structured feedback collection:
- Multiple feedback sources
- Rating system (1-5 stars)
- Category classification
- Author tracking
- Average rating calculation

**Use Case**: Make informed decisions based on team input

### 7. Offer Details

Comprehensive offer display:
- Salary display (exact or range)
- Benefits package
- Start date
- Expiration tracking
- Accept/Decline actions
- Expired offer warnings

**Use Case**: Track offer status and deadlines

### 8. Status Notifications

Real-time updates via:
- Toast notifications
- WebSocket events
- Status change indicators

**Use Case**: Stay updated on application changes

## Performance Optimization

- Component memoization prevents unnecessary re-renders
- Efficient event handling with useCallback
- Lazy loading of timeline events
- WebSocket connection pooling
- Optimized data transformations

## Accessibility

- Semantic HTML structure
- ARIA labels on interactive elements
- Keyboard navigation support
- Color contrast compliance (WCAG AA)
- Screen reader friendly
- Focus management in modals

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Mobile browsers (iOS Safari 14+, Chrome Android)

## Future Enhancements

1. **Bulk Operations**: Process multiple applications at once
2. **Custom Stages**: Allow teams to define their own pipeline stages
3. **Advanced Filtering**: Multiple criteria filtering and saved views
4. **Analytics Dashboard**: Pipeline metrics and trends
5. **Email Integration**: Sync with candidate communications
6. **Calendar Integration**: View interviews in calendar
7. **Interview Recording**: Store and review video interviews
8. **Automated Workflows**: Trigger actions based on conditions
9. **Export/Reporting**: Generate hiring reports
10. **Mobile App**: Native mobile experience

## Troubleshooting

### Dialog component not found

Ensure `@radix-ui/react-dialog` is installed:
```bash
npm install @radix-ui/react-dialog @radix-ui/react-icons
```

### Type errors in components

Ensure `types.ts` is properly exported from the index:
```tsx
export type { HorizontalPipeline } from './types';
```

### WebSocket connection issues

Check WebSocket endpoint configuration and ensure backend supports `/ws/applications/{id}` path.

### Interview prep not generating

Verify `/api/interview-prep` endpoint exists and Claude API is properly configured.

## Support & Contributions

For issues or contributions, please refer to the main project documentation or contact the development team.

## License

Same as the main TrueMatch project.
