# Applications Tracking System

A comprehensive job application tracking system with a horizontal pipeline visualization, detailed application cards, timeline of events, feedback management, interview preparation with Claude, offer details, and real-time status notifications.

## Features

### 1. Horizontal Pipeline Visualization
- **Applied → Screened → Interviewed → Offer → Closed** flow
- Visual progress indicator showing completion percentage
- Stage highlighting based on application status
- Interactive stage navigation
- Real-time progress tracking

**Component**: `HorizontalPipeline.tsx`

### 2. Application Cards
- Clean card-based layout showing application essentials
- Evaluation scores display (Keyword, Semantic, Capability)
- Quick access buttons (Details, Schedule Interview)
- Status badges and time-in-stage indicators
- Tag display and source information
- Featured/urgent application highlighting

**Component**: `ApplicationCard.tsx`

### 3. Detailed View Modal
- Comprehensive application information display
- Multi-tab interface (Overview, Timeline, Interviews, Feedback)
- Quick info grid with contact, dates, and status
- Full pipeline visualization within modal
- Application linking (Resume, LinkedIn)

**Component**: `ApplicationDetailModal.tsx`

### 4. Timeline of Events
- Chronological event visualization
- Event categorization:
  - Status changes
  - Interviews scheduled/completed
  - Feedback submissions
  - Offer events
  - Call logs
  - Internal notes
- Rich metadata display for each event
- Interactive timeline navigation

**Component**: `TimelineView.tsx`

### 5. Feedback Section
- Feedback display with ratings (1-5 stars)
- Average rating calculation
- Feedback categorization:
  - Technical
  - Cultural
  - Communication
  - Experience
- Add new feedback with form
- Feedback author and date tracking

**Component**: `FeedbackSection.tsx`

### 6. Interview Prep with Claude
- AI-powered interview preparation guide generation
- Focus areas identification
- Key questions for the position
- Common challenges and how to address them
- Prep tips and recommendations
- Copy-to-clipboard functionality for questions
- Different interview type support (phone, technical, onsite, final)

**Component**: `InterviewPrepWidget.tsx`

### 7. Offer Details Card
- Salary display with range support
- Benefits package listing
- Start date information
- Offer expiration tracking
- Accept/Decline actions
- Offer status indicators
- Additional notes and terms

**Component**: `OfferDetailsCard.tsx`

### 8. Status Notifications
- Real-time updates on application changes
- Event-based notifications
- Toast-style alerts for:
  - Stage changes
  - Interview scheduling
  - Feedback submissions
  - Offer actions
- WebSocket integration for live updates

## Type Definitions

All TypeScript types are defined in `types.ts`:

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
  
  // ... additional types
}
```

## Usage Examples

### Basic Application Card

```tsx
import { ApplicationCard } from '@/components/ApplicationCard';

<ApplicationCard
  application={applicationData}
  onViewDetails={(id) => console.log(id)}
  onScheduleInterview={(id) => console.log(id)}
/>
```

### Horizontal Pipeline

```tsx
import { HorizontalPipeline } from '@/components/HorizontalPipeline';

<HorizontalPipeline
  applicationStatus={{
    applicationId: 'app-1',
    currentStage: 'interviewed',
    completedStages: ['applied', 'screened'],
    timestamp: new Date(),
  }}
  onStageClick={(stageId) => console.log(stageId)}
/>
```

### Full Application Detail Modal

```tsx
import { ApplicationDetailModal } from '@/components/ApplicationDetailModal';

<ApplicationDetailModal
  application={applicationData}
  isOpen={isOpen}
  onClose={() => setIsOpen(false)}
  onScheduleInterview={handleScheduleInterview}
  onAddFeedback={handleAddFeedback}
  onGeneratePrepGuide={generateInterviewPrep}
/>
```

### Interview Prep with Claude

```tsx
import { InterviewPrepWidget } from '@/components/InterviewPrepWidget';

const handleGeneratePrepGuide = async (position, candidate) => {
  const response = await fetch('/api/interview-prep', {
    method: 'POST',
    body: JSON.stringify({ position, candidate }),
  });
  return response.json();
};

<InterviewPrepWidget
  positionTitle="Senior Backend Engineer"
  candidateName="John Smith"
  onGeneratePrepGuide={handleGeneratePrepGuide}
/>
```

## Testing

Comprehensive E2E tests are included in `ApplicationsTracker.test.tsx`:

### Test Coverage

1. **HorizontalPipeline Tests**
   - Renders all stages
   - Shows progress percentage
   - Handles stage click events

2. **ApplicationCard Tests**
   - Displays candidate information
   - Shows evaluation scores
   - Handles view details and interview scheduling

3. **TimelineView Tests**
   - Renders events in chronological order
   - Displays metadata and descriptions
   - Shows empty state

4. **FeedbackSection Tests**
   - Displays feedback items
   - Shows average ratings
   - Allows adding new feedback

5. **OfferDetailsCard Tests**
   - Displays offer information
   - Shows expiry tracking
   - Handles accept/reject actions

6. **InterviewPrepWidget Tests**
   - Generates prep guide with Claude
   - Shows key questions and focus areas
   - Supports copy-to-clipboard

7. **ApplicationDetailModal Tests**
   - Displays full application details
   - Switches between tabs
   - Handles all interactions

8. **End-to-End Tests**
   - Complete application journey
   - Multi-tab navigation
   - Feedback submission
   - Interview prep generation

### Running Tests

```bash
# Run all tests
npm test

# Run specific test file
npm test ApplicationsTracker.test.tsx

# Run with coverage
npm test -- --coverage

# Watch mode
npm test -- --watch
```

## Integration with Existing Pipeline

The new components integrate seamlessly with the existing ATS infrastructure:

1. **Extends PipelineBoard**: Uses similar stage management
2. **Compatible with useATSPipeline hook**: Reuses candidate data fetching
3. **Works with InterviewScheduler**: Existing interview scheduling
4. **Integrates WebSocket updates**: Real-time status changes
5. **Uses existing UI components**: Card, Badge, Button, Tabs, Dialog

### API Integration Points

- `GET /api/v1/applications/{id}` - Fetch application details
- `GET /api/v1/applications/{id}/timeline` - Fetch timeline events
- `POST /api/v1/applications/{id}/feedback` - Add feedback
- `POST /api/v1/interview-prep` - Generate interview prep with Claude
- `PATCH /api/v1/applications/{id}/status` - Update application status
- `POST /api/v1/applications/{id}/offer/accept` - Accept offer
- `WebSocket /ws/applications/{id}` - Real-time updates

## Installation

1. Copy all component files to `/src/components/applications-tracker/`:
   ```
   HorizontalPipeline.tsx
   ApplicationCard.tsx
   ApplicationDetailModal.tsx
   TimelineView.tsx
   FeedbackSection.tsx
   InterviewPrepWidget.tsx
   OfferDetailsCard.tsx
   types.ts
   ```

2. Copy test file to `/src/components/applications-tracker/__tests__/`:
   ```
   ApplicationsTracker.test.tsx
   ```

3. Add types to `/src/types/index.ts`

4. Ensure dependencies are installed (all components use existing packages)

## Dependencies

All components use existing project dependencies:
- React 18.3.1
- TypeScript 5.5.3
- TailwindCSS 3.4.6
- Radix UI components
- Lucide icons
- Jest & React Testing Library (for tests)

No new dependencies required!

## Accessibility

- Semantic HTML elements
- ARIA labels on interactive elements
- Keyboard navigation support
- Color contrast compliance
- Screen reader friendly
- Focus management in modals

## Performance Considerations

- Lazy loading of timeline events
- Memoized component calculations
- Efficient re-renders with proper dependency arrays
- Optimized event handlers
- WebSocket connection pooling
- Image lazy loading for resumes

## Future Enhancements

1. **Bulk operations**: Process multiple applications at once
2. **Custom stages**: Allow teams to define their own pipeline stages
3. **Advanced filtering**: Filter by multiple criteria
4. **Saved views**: Store favorite filter combinations
5. **Analytics dashboard**: Track pipeline metrics over time
6. **Email integration**: Sync with candidate emails
7. **Calendar sync**: Show interviews in calendar
8. **Mobile app**: Native mobile experience
9. **Interview recording**: Store and review interview videos
10. **Automated workflows**: Trigger actions based on conditions

## Support

For issues or questions, please refer to the main ATS documentation or contact the development team.
