# Comprehensive Testing Guide - TrueMatch Platform

## Overview

This guide provides a complete testing strategy for the TrueMatch platform, targeting **80%+ code coverage** across all components, with a focus on critical user flows and integration points.

## Testing Stack

- **Unit & Component Tests**: Jest + React Testing Library
- **API Integration Tests**: Mock Service Worker (MSW) + Jest
- **E2E Tests**: Playwright (critical user flows)
- **Complex Interactions**: Cypress (real browser state, animations)

## Project Structure

```
truematch/web/
├── src/
│   ├── __tests__/
│   │   ├── mocks/
│   │   │   ├── handlers.ts          # MSW API handlers
│   │   │   └── server.ts            # MSW server setup
│   │   ├── utils/
│   │   │   └── test-utils.tsx       # Custom render, factories, helpers
│   │   ├── templates/
│   │   │   ├── ComponentTestTemplate.test.tsx
│   │   │   └── APIIntegrationTemplate.test.ts
│   │   ├── hooks/
│   │   │   └── useResumeVersioning.test.ts (example)
│   │   └── ...
│   ├── components/
│   │   └── __tests__/
│   │       └── *.test.tsx
│   ├── hooks/
│   │   └── __tests__/
│   │       └── *.test.ts
│   └── lib/
│       └── __tests__/
│           └── *.test.ts
├── e2e/
│   ├── resume-upload-analyze-apply.spec.ts
│   ├── jd-optimizer-simulate.spec.ts
│   └── fixtures/
│       └── sample-resume.pdf
├── cypress/
│   ├── e2e/
│   │   └── complex-interactions.cy.ts
│   ├── support/
│   │   ├── commands.ts
│   │   ├── e2e.ts
│   │   └── component.ts
│   └── fixtures/
│       └── sample-resume.pdf
├── jest.config.js
├── playwright.config.ts
├── cypress.config.ts
└── jest.setup.ts
```

## Test Types & Responsibilities

### 1. Unit Tests (Jest)
**Target Coverage**: 80%+

Test individual functions, utilities, and small components in isolation.

```bash
npm run test
```

**Files to test:**
- `src/lib/utils.ts` - Utility functions
- `src/lib/api.ts` - API client
- `src/lib/capability-matching.ts` - Business logic
- `src/hooks/*.ts` - Custom hooks
- `src/components/ui/*.tsx` - Basic UI components

**Template**: See `src/__tests__/templates/ComponentTestTemplate.test.tsx`

### 2. Component Tests (React Testing Library)
**Target Coverage**: 80%+ for all components

Test components with props, state, and user interactions.

**Key Testing Areas:**
```typescript
// 1. Rendering
it('renders without crashing', () => {
  render(<Component />);
  expect(screen.getByRole('button')).toBeInTheDocument();
});

// 2. Props
it('applies props correctly', () => {
  render(<Button label="Click me" />);
  expect(screen.getByRole('button')).toHaveTextContent('Click me');
});

// 3. User Interactions
it('handles clicks', async () => {
  const onClick = jest.fn();
  render(<Button onClick={onClick} />);
  await userEvent.click(screen.getByRole('button'));
  expect(onClick).toHaveBeenCalled();
});

// 4. State Changes
it('updates on state change', async () => {
  render(<Counter />);
  await userEvent.click(screen.getByRole('button', { name: /increment/i }));
  expect(screen.getByText('1')).toBeInTheDocument();
});

// 5. Async Operations
it('loads data', async () => {
  render(<DataComponent />);
  await userEvent.click(screen.getByRole('button', { name: /load/i }));
  expect(await screen.findByText('Data loaded')).toBeInTheDocument();
});

// 6. Accessibility
it('is accessible', () => {
  render(<Component />);
  const button = screen.getByRole('button');
  expect(button).toHaveAccessibleName();
});
```

**Example Component Tests:**
- `CVAnalysisWidget.test.tsx` - Resume analysis display
- `EnhancedDashboard.test.tsx` - Complex dashboard
- `ApplicationsTracker.test.tsx` - Applications tracking
- `ActionPanel.test.tsx` - Action controls
- `QueueTable.test.tsx` - Data table

### 3. Hook Tests
**Target Coverage**: 80%+

Test custom React hooks for state management and side effects.

```bash
npm run test -- --testPathPattern='hooks'
```

**Key hooks to test:**
- `useResumeVersioning` - Resume version management
- `useJobFavorites` - Favorite jobs list
- `useFilteredPipeline` - Pipeline filtering
- `useATSPipeline` - ATS integration
- `useBulkActions` - Batch operations
- `useProfileCompletion` - Profile tracking
- `useATSInterviews` - Interview management
- `useWebSocket` - Real-time updates
- `useAgentOperator` - Agent operations

**Template**: See `src/__tests__/hooks/useResumeVersioning.test.ts`

### 4. API Integration Tests
**Target Coverage**: 100% of endpoints

Test API endpoints with request/response validation and error handling.

```bash
npm run test:integration
```

**Endpoints to test:**

#### Resume Operations
- `POST /api/resume/upload` - File upload and parsing
- `GET /api/resume/:resumeId/versions` - Version history
- `GET /api/resume/:resumeId/versions/:versionId` - Specific version
- `POST /api/resume/:resumeId/versions/:versionId/annotate` - Annotations
- `POST /api/resume/:resumeId/compare` - Version comparison
- `POST /api/resume/:resumeId/revert` - Revert to version

#### JD Operations
- `POST /api/jd-optimizer` - JD optimization

#### Applications
- `POST /api/applications` - Create application
- `GET /api/applications` - List applications
- `PUT /api/applications/:applicationId` - Update application
- `DELETE /api/applications/:applicationId` - Delete application

#### Jobs
- `GET /api/jobs` - List jobs
- `POST /api/jobs/:jobId/favorite` - Favorite job
- `GET /api/jobs/:jobId/matches` - Get matches

**Template**: See `src/__tests__/templates/APIIntegrationTemplate.test.ts`

**Test Patterns:**
```typescript
it('endpoint returns correct status code', async () => {
  const response = await fetch('/api/endpoint');
  expect(response.status).toBe(200);
});

it('response has correct structure', async () => {
  const response = await fetch('/api/endpoint');
  const data = await response.json();
  expect(data).toHaveProperty('expectedField');
});

it('handles errors correctly', async () => {
  const response = await fetch('/api/invalid');
  expect(response.status).toBe(404);
});

it('validates request data', async () => {
  const response = await fetch('/api/endpoint', {
    method: 'POST',
    body: JSON.stringify({ invalid: 'data' })
  });
  expect(response.status).toBe(400);
});
```

### 5. E2E Tests (Playwright)
**Target**: Critical user flows

Test complete user journeys from start to finish in a real browser.

```bash
npm run test:e2e
```

**Critical Flows:**

#### Candidate Flow 1: Resume Upload → Analysis → Application
1. Navigate to dashboard
2. Upload resume file
3. View CV analysis
4. See job matches
5. Apply to job
6. Confirm application

**File**: `e2e/resume-upload-analyze-apply.spec.ts`

#### Candidate Flow 2: Resume Versioning → Optimization
1. Select resume
2. Create new version
3. Optimize for JD
4. Compare versions
5. Revert if needed

#### Recruiter Flow 1: Create JD → Simulate → Track
1. Navigate to JD Optimizer
2. Input job description
3. Run optimization
4. View improvements
5. Run simulation
6. View matched candidates
7. Track applications

**File**: `e2e/jd-optimizer-simulate.spec.ts`

#### Recruiter Flow 2: Bulk Actions
1. Select multiple candidates
2. Perform batch operation
3. Confirm results
4. Track progress

**E2E Test Structure:**
```typescript
test.describe('Feature Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/path');
    await page.waitForLoadState('networkidle');
  });

  test('user can complete flow', async ({ page }) => {
    // Act
    await page.click('[data-testid="button"]');
    
    // Assert
    await expect(page.locator('[data-testid="result"]')).toBeVisible();
  });
});
```

### 6. Cypress Tests
**Target**: Complex interactions and real-time updates

Test complex user interactions that benefit from Cypress's real browser state.

```bash
npm run test:cypress
```

**Test Scenarios:**

#### Table Interactions
- Sorting by column
- Filtering with multiple criteria
- Pagination
- Multi-select with checkboxes
- Row expansion
- Search within table

#### Form Interactions
- Field validation on blur
- Conditional field visibility
- Autosave
- Loading states
- Error handling

#### Modal Interactions
- Open/close modals
- Stacked modals
- State preservation
- Keyboard navigation (Escape)

#### Real-time Updates
- WebSocket message handling
- Live data updates
- Status changes

#### Chart Interactions
- Hover tooltips
- Filter updates
- Responsive sizing

#### Responsive Design
- Mobile layout
- Tablet layout
- Desktop layout
- Sidebar behavior

**File**: `cypress/e2e/complex-interactions.cy.ts`

## Running Tests

### Run All Tests
```bash
npm run test:all
```

### Unit & Component Tests Only
```bash
npm run test               # Single run
npm run test:watch        # Watch mode
npm run test:coverage     # With coverage report
npm run test:ci          # CI mode (single run, max workers=2)
npm run test:integration # Integration tests only
```

### E2E Tests
```bash
npm run test:e2e         # Run all tests
npm run test:e2e:debug   # Debug mode with inspector
npm run test:e2e:ui      # UI mode with interactive viewer
```

### Cypress Tests
```bash
npm run test:cypress      # Headless run
npm run test:cypress:open # Interactive mode
```

### Coverage Report
```bash
npm run test:coverage:report
```

## Coverage Thresholds

### Current Baseline
- Branches: 30%
- Functions: 15%
- Lines: 5%
- Statements: 5%

### Phase 1 Target (Month 1)
- Branches: 45%
- Functions: 35%
- Lines: 40%
- Statements: 40%

### Phase 2 Target (Month 2)
- Branches: 60%
- Functions: 55%
- Lines: 60%
- Statements: 60%

### Phase 3 Target (End State - 80%+)
- Branches: 75%+
- Functions: 80%+
- Lines: 80%+
- Statements: 80%+

**Location Specific Targets:**
- Components: 50%+ (Phase 1)
- Hooks: 60%+ (Phase 1)
- Lib: 70%+ (Phase 1)

## Test Data & Mocking

### Using Test Utilities
```typescript
import {
  createMockResume,
  createMockJob,
  createMockCandidate,
  createMockUser,
  createMockJobDescription,
  mockSession,
} from '@/__tests__/utils/test-utils';

// Usage
const mockResume = createMockResume({ userId: 'custom-id' });
const mockJob = createMockJob({ title: 'Custom Title' });
```

### Mock API Responses
```typescript
import { server } from '@/__tests__/mocks/server';
import { http, HttpResponse } from 'msw';

// Override handler for specific test
server.use(
  http.get('/api/endpoint', () => {
    return HttpResponse.json({ custom: 'data' });
  })
);
```

### Mock File Uploads
```typescript
import { createMockFile } from '@/__tests__/utils/test-utils';

const file = createMockFile('resume.pdf', 1024, 'application/pdf');
```

## Best Practices

### 1. Use Data Test IDs
```tsx
<button data-testid="upload-button">Upload</button>
```

Selector:
```typescript
screen.getByTestId('upload-button')
```

### 2. Query by Accessibility Role
```typescript
// Good - uses semantic meaning
screen.getByRole('button', { name: /upload/i })
screen.getByRole('textbox', { name: /email/i })

// Avoid - relies on implementation details
screen.getByClassName('my-button')
```

### 3. User Events Over Fire Event
```typescript
// Good - simulates actual user behavior
await userEvent.click(button);
await userEvent.type(input, 'text');

// Avoid - unrealistic interactions
fireEvent.click(button);
```

### 4. Wait for Async Operations
```typescript
// Good
await waitFor(() => {
  expect(screen.getByText('Loaded')).toBeInTheDocument();
});

// Also good - using findBy
const element = await screen.findByText('Loaded');
```

### 5. Test Behavior, Not Implementation
```typescript
// Good - tests what user sees
it('shows error message on invalid email', () => {
  render(<Form />);
  userEvent.type(screen.getByLabelText(/email/i), 'invalid');
  expect(screen.getByText(/invalid email/i)).toBeInTheDocument();
});

// Avoid - tests internal state
it('sets state.error to true', () => {
  const { rerender } = render(<Form />);
  // ... internal state checking
});
```

### 6. Organize with Describe Blocks
```typescript
describe('Resume Upload', () => {
  describe('when file is valid', () => {
    it('uploads successfully', () => { });
  });

  describe('when file is invalid', () => {
    it('shows error message', () => { });
  });
});
```

### 7. Use Before/After Hooks
```typescript
beforeEach(() => {
  // Setup before each test
  render(<Component />);
});

afterEach(() => {
  // Cleanup after each test
  cleanup();
});
```

## Debugging Tests

### View Test Output
```bash
npm run test -- --verbose
```

### Debug Mode
```bash
# Jest
npm run test -- --debug

# Playwright
npm run test:e2e:debug

# Cypress
npm run test:cypress:open
```

### Console Logs
```typescript
it('logs values', () => {
  render(<Component />);
  console.log(screen.debug()); // Print DOM
  screen.logTestingPlaygroundURL(); // Testingplayground link
});
```

### Visual Debugging
```typescript
// Playwright
await page.pause(); // Opens inspector

// Cypress
cy.pause(); // Pauses execution
cy.debug(); // Logs chainable value
```

## CI/CD Integration

### Run Tests in CI
```bash
npm run test:ci
```

### GitHub Actions Example
```yaml
- name: Run Tests
  run: npm run test:ci

- name: Run E2E Tests
  run: npm run test:e2e

- name: Upload Coverage
  uses: codecov/codecov-action@v3
  with:
    files: ./coverage/lcov.info
```

## Maintenance

### Updating Tests
When code changes:
1. Update affected tests
2. Maintain or improve coverage
3. Run full test suite before committing
4. Add new tests for new features

### Keeping Tests Fast
- Use mocks instead of real API calls
- Avoid unnecessary timeouts
- Run tests in parallel when possible
- Keep test data minimal

### Organizing Large Test Suites
- One describe block per component/function
- Group related tests together
- Use consistent naming: `it('should [action] when [condition]')`
- Keep individual tests focused on one behavior

## Resources

- [Jest Documentation](https://jestjs.io/)
- [React Testing Library Docs](https://testing-library.com/react)
- [Playwright Documentation](https://playwright.dev/)
- [Cypress Documentation](https://docs.cypress.io/)
- [Mock Service Worker Docs](https://mswjs.io/)

## Troubleshooting

### Tests Timing Out
- Increase timeout: `jest.setTimeout(10000)`
- Check for unresolved promises
- Verify API mocks are set up

### React State Updates After Test
- Use `act()` wrapper for state changes
- Ensure component unmounts properly
- Check for memory leaks

### Flaky Tests
- Avoid hardcoded delays - use `waitFor()`
- Check for race conditions
- Verify test data is consistent
- Use `screen.getByRole()` instead of element selectors

### E2E Test Failures
- Check that dev server is running
- Verify test data files exist
- Clear browser cache/cookies
- Use headed mode for debugging

## Next Steps

1. **Phase 1**: Implement component tests for critical paths (Week 1-2)
2. **Phase 2**: Add integration tests for all APIs (Week 3-4)
3. **Phase 3**: Implement E2E tests for user flows (Week 5-6)
4. **Phase 4**: Add Cypress tests for complex interactions (Week 7-8)
5. **Maintenance**: Continuous improvement and coverage growth
