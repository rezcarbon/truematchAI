# Test Infrastructure Setup - TrueMatch Platform

## Summary

This document provides a step-by-step implementation guide for the comprehensive test infrastructure targeting 80%+ code coverage.

## What Has Been Set Up

### 1. ✅ Test Configuration Files

#### Jest Configuration (`jest.config.js`)
- Updated with progressive coverage thresholds
- Component-specific targets (50%+)
- Hook-specific targets (60%+)
- Lib-specific targets (70%+)
- MSW integration support

#### Playwright Configuration (`playwright.config.ts`)
- Desktop browsers (Chrome, Firefox, Safari)
- Mobile browsers (iPhone 12, Pixel 5)
- Screenshot/video on failure
- HTML report generation
- Dev server integration

#### Cypress Configuration (`cypress.config.ts`)
- E2E and component test support
- Video recording
- Screenshot on failure
- Custom command support

#### Jest Setup (`jest.setup.ts`)
- Mock Service Worker server initialization
- Next.js router/navigation mocks
- NextAuth mocks
- WebSocket mocks
- IntersectionObserver/ResizeObserver mocks

### 2. ✅ Test Utilities & Helpers

#### Test Utils (`src/__tests__/utils/test-utils.tsx`)
- Custom render function with providers
- Mock data factories:
  - `createMockResume()`
  - `createMockJob()`
  - `createMockCandidate()`
  - `createMockUser()`
  - `createMockJobDescription()`
- Mock file creation
- Session mocks (candidate & recruiter)

#### MSW Setup
- **Handlers** (`src/__tests__/mocks/handlers.ts`): API endpoint mocks
  - Resume upload/management
  - JD optimizer
  - Job search
  - Applications
  - Authentication
- **Server** (`src/__tests__/mocks/server.ts`): MSW server instance

### 3. ✅ Test Templates

#### Component Test Template (`src/__tests__/templates/ComponentTestTemplate.test.tsx`)
- Basic rendering tests
- Props testing
- User interaction tests
- State management tests
- Async operation tests
- Accessibility tests
- Comprehensive patterns and best practices

#### API Integration Template (`src/__tests__/templates/APIIntegrationTemplate.test.ts`)
- Success case testing
- Error handling
- Request validation
- Response validation
- Edge cases
- Performance considerations

### 4. ✅ E2E Test Templates

#### Resume Upload Flow (`e2e/resume-upload-analyze-apply.spec.ts`)
- Upload resume file
- View CV analysis
- Show job matches
- Apply to job
- Handle errors
- Mobile responsiveness

#### JD Optimizer Flow (`e2e/jd-optimizer-simulate.spec.ts`)
- Create JD
- Optimize JD
- Run simulations
- View matched candidates
- Batch actions
- Accessibility

### 5. ✅ Cypress Test Suite

#### Complex Interactions (`cypress/e2e/complex-interactions.cy.ts`)
- **Table Interactions**: Sort, filter, paginate, select, expand
- **Form Interactions**: Validation, conditional fields, autosave, loading states
- **Modal Interactions**: Open/close, stacked modals, state preservation
- **WebSocket Updates**: Real-time data synchronization
- **Chart Interactions**: Hover, tooltips, filters
- **Tab Navigation**: State preservation, indicator updates
- **Responsive Design**: Mobile, tablet, desktop layouts

#### Cypress Support Files
- **Commands** (`cypress/support/commands.ts`): 15+ custom commands
  - `login()`
  - `uploadFile()`
  - `waitForAPI()`
  - `mockAPI()`
  - `checkA11y()`
  - And more...
- **E2E Support** (`cypress/support/e2e.ts`): Global setup/teardown
- **Component Support** (`cypress/support/component.ts`): React component mounting

### 6. ✅ Hook Test Example

#### Resume Versioning Hook Test (`src/__tests__/hooks/useResumeVersioning.test.ts`)
- Initialization testing
- Fetch operations
- Create new version
- Compare versions
- Revert operations
- Error handling
- Loading states

### 7. ✅ NPM Scripts

Updated `package.json` with comprehensive test scripts:

```json
{
  "test": "jest",
  "test:watch": "jest --watch",
  "test:coverage": "jest --coverage",
  "test:ci": "jest --coverage --watchAll=false --maxWorkers=2",
  "test:integration": "jest --testPathPattern='__tests__/integration'",
  "test:e2e": "playwright test",
  "test:e2e:debug": "playwright test --debug",
  "test:e2e:ui": "playwright test --ui",
  "test:cypress": "cypress run",
  "test:cypress:open": "cypress open",
  "test:all": "npm run test:ci && npm run test:integration && npm run test:e2e",
  "test:coverage:report": "jest --coverage --coverage-reporters=text-summary"
}
```

### 8. ✅ Dev Dependencies Added

```json
{
  "@playwright/test": "^1.45.1",
  "cypress": "^13.15.1",
  "jest-coverage-report": "^1.4.0",
  "jest-mock-extended": "^3.0.5",
  "msw": "^2.3.0"
}
```

## Next Steps: Implementation Roadmap

### Phase 1: Component Tests (Week 1-2)
**Goal**: 40%+ coverage

#### Week 1: UI Components
1. Test all `src/components/ui/*.tsx` components
   - Button, Card, Dialog, Badge, Progress, Tabs, Gauge, etc.
   - Each should have 80%+ coverage
   - Use template: `src/__tests__/templates/ComponentTestTemplate.test.tsx`

2. Create test files:
   ```
   src/components/ui/__tests__/
   ├── button.test.tsx
   ├── card.test.tsx
   ├── dialog.test.tsx
   ├── badge.test.tsx
   ├── progress.test.tsx
   └── ... (other ui components)
   ```

#### Week 2: Feature Components
1. Test feature components
   - `src/components/candidate/*`
   - `src/components/recruiter/*`
   - `src/components/admin/*`

2. Create test files:
   ```
   src/components/candidate/__tests__/
   ├── CVAnalysisWidget.test.tsx
   ├── EnhancedDashboard.test.tsx
   └── ...
   
   src/components/recruiter/__tests__/
   └── ...
   
   src/components/admin/__tests__/
   └── ...
   ```

3. Run coverage report:
   ```bash
   npm run test:coverage
   ```

### Phase 2: Hook & Utility Tests (Week 3-4)
**Goal**: 60%+ coverage

#### Week 3: Hooks
1. Create hook tests using template pattern
2. Test all custom hooks in `src/hooks/`
   - useResumeVersioning
   - useJobFavorites
   - useFilteredPipeline
   - useATSPipeline
   - useBulkActions
   - useProfileCompletion
   - useATSInterviews
   - useWebSocket
   - useAgentOperator

3. Create test files:
   ```
   src/hooks/__tests__/
   ├── useResumeVersioning.test.ts
   ├── useJobFavorites.test.ts
   ├── useFilteredPipeline.test.ts
   └── ... (other hooks)
   ```

#### Week 4: Utilities & Libraries
1. Test utility functions
   ```
   src/lib/__tests__/
   ├── utils.test.ts
   ├── api.test.ts
   ├── capability-matching.test.ts
   ├── job-data.test.ts
   └── auth.test.ts
   ```

2. Test middleware and API routes
   ```
   src/app/api/__tests__/
   ├── resume-upload.test.ts
   ├── jd-optimizer.test.ts
   └── ... (other endpoints)
   ```

### Phase 3: Integration Tests (Week 5-6)
**Goal**: 70%+ coverage, 100% API endpoint coverage

#### Week 5: API Integration Tests
1. Create integration test suite
   ```
   src/__tests__/integration/
   ├── resume-api.test.ts
   ├── jd-optimizer-api.test.ts
   ├── applications-api.test.ts
   ├── jobs-api.test.ts
   └── auth-api.test.ts
   ```

2. Test all API endpoints using template
3. Run tests:
   ```bash
   npm run test:integration
   ```

#### Week 6: Enhance MSW Handlers
1. Expand `src/__tests__/mocks/handlers.ts` with:
   - More realistic response data
   - Error scenarios
   - Edge cases
   - Rate limiting simulation
   - Request validation

2. Add integration test examples
3. Document handler patterns

### Phase 4: E2E Tests (Week 7-8)
**Goal**: 80%+ coverage, critical flows tested

#### Week 7: Playwright E2E Tests
1. Expand E2E test suite:
   ```
   e2e/
   ├── resume-upload-analyze-apply.spec.ts (exists)
   ├── jd-optimizer-simulate.spec.ts (exists)
   ├── resume-versioning.spec.ts (new)
   ├── bulk-actions.spec.ts (new)
   ├── authentication.spec.ts (new)
   └── mobile-flows.spec.ts (new)
   ```

2. Create test fixtures (sample files):
   ```
   e2e/fixtures/
   ├── sample-resume.pdf
   ├── sample-resume-2.pdf
   ├── invalid-file.txt
   └── large-resume.pdf
   ```

3. Run E2E tests:
   ```bash
   npm run test:e2e
   ```

#### Week 8: Cypress Complex Interactions
1. Expand Cypress test suite with:
   - Additional complex workflows
   - Performance tests
   - Cross-browser compatibility
   - Accessibility audits

2. Create additional test files:
   ```
   cypress/e2e/
   ├── complex-interactions.cy.ts (exists)
   ├── performance.cy.ts (new)
   ├── accessibility.cy.ts (new)
   └── cross-browser.cy.ts (new)
   ```

3. Run Cypress tests:
   ```bash
   npm run test:cypress
   ```

## Installation & Setup

### 1. Install Dependencies

```bash
cd /Users/modvader/Documents/codebase/truematch/web

npm install
# This will install:
# - @playwright/test
# - cypress
# - jest-coverage-report
# - jest-mock-extended
# - msw
# - and all existing dependencies
```

### 2. Verify Setup

```bash
# Check Jest is working
npm run test -- --version

# Check Playwright is installed
npx playwright --version

# Check Cypress is installed
npx cypress --version
```

### 3. Create Test Fixtures Directory

```bash
mkdir -p e2e/fixtures
mkdir -p cypress/fixtures

# Add sample files (you need to provide actual PDF files)
# For now, create placeholder files
touch e2e/fixtures/sample-resume.pdf
touch cypress/fixtures/sample-resume.pdf
```

### 4. Run Initial Tests

```bash
# Run existing tests
npm run test

# Run new test templates
npm run test -- --testPathPattern='templates'

# Run with coverage
npm run test:coverage
```

## Configuration Files Locations

All files have been created at:

**Test Configuration:**
- `/Users/modvader/Documents/codebase/truematch/web/jest.config.js` (updated)
- `/Users/modvader/Documents/codebase/truematch/web/jest.setup.ts` (existing, good)
- `/Users/modvader/Documents/codebase/truematch/web/playwright.config.ts` (new)
- `/Users/modvader/Documents/codebase/truematch/web/cypress.config.ts` (new)

**Test Utilities:**
- `/Users/modvader/Documents/codebase/truematch/web/src/__tests__/utils/test-utils.tsx`
- `/Users/modvader/Documents/codebase/truematch/web/src/__tests__/mocks/handlers.ts`
- `/Users/modvader/Documents/codebase/truematch/web/src/__tests__/mocks/server.ts`

**Test Templates:**
- `/Users/modvader/Documents/codebase/truematch/web/src/__tests__/templates/ComponentTestTemplate.test.tsx`
- `/Users/modvader/Documents/codebase/truematch/web/src/__tests__/templates/APIIntegrationTemplate.test.ts`
- `/Users/modvader/Documents/codebase/truematch/web/src/__tests__/hooks/useResumeVersioning.test.ts`

**E2E Tests:**
- `/Users/modvader/Documents/codebase/truematch/web/e2e/resume-upload-analyze-apply.spec.ts`
- `/Users/modvader/Documents/codebase/truematch/web/e2e/jd-optimizer-simulate.spec.ts`

**Cypress Tests:**
- `/Users/modvader/Documents/codebase/truematch/web/cypress/e2e/complex-interactions.cy.ts`
- `/Users/modvader/Documents/codebase/truematch/web/cypress/support/commands.ts`
- `/Users/modvader/Documents/codebase/truematch/web/cypress/support/e2e.ts`
- `/Users/modvader/Documents/codebase/truematch/web/cypress/support/component.ts`

**Documentation:**
- `/Users/modvader/Documents/codebase/truematch/web/COMPREHENSIVE_TESTING_GUIDE.md`
- `/Users/modvader/Documents/codebase/truematch/web/TEST_INFRASTRUCTURE_SETUP.md` (this file)

## Quick Reference Commands

```bash
# Install and setup
npm install

# Run tests locally
npm run test                  # Single run
npm run test:watch          # Watch mode
npm run test:coverage       # With coverage

# Run integration tests
npm run test:integration

# Run E2E tests
npm run test:e2e            # Headless
npm run test:e2e:debug      # With debugger
npm run test:e2e:ui         # Interactive UI

# Run Cypress tests
npm run test:cypress        # Headless
npm run test:cypress:open   # Interactive

# Run all tests
npm run test:all

# View coverage report
npm run test:coverage:report
```

## CI/CD Integration

### GitHub Actions Workflow Example

Create `.github/workflows/test.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node
        uses: actions/setup-node@v3
        with:
          node-version: 18
          cache: npm
      
      - name: Install dependencies
        run: npm ci
      
      - name: Lint
        run: npm run lint
      
      - name: Type check
        run: npm run typecheck
      
      - name: Unit tests
        run: npm run test:ci
      
      - name: Integration tests
        run: npm run test:integration
      
      - name: E2E tests
        run: npm run test:e2e
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage/lcov.info
      
      - name: Archive E2E results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: playwright-report/
```

## Monitoring & Maintenance

### Regular Tasks

1. **Daily**: Run tests locally before committing
   ```bash
   npm run test:ci
   ```

2. **Weekly**: Review coverage reports
   ```bash
   npm run test:coverage:report
   ```

3. **Monthly**: Update test dependencies
   ```bash
   npm update @playwright/test cypress
   ```

4. **Quarterly**: Refactor and optimize tests

### Coverage Targets

- Week 1: 40% (components)
- Week 3: 60% (components + hooks)
- Week 5: 70% (+ integration)
- Week 8: 80%+ (full coverage)

## Troubleshooting

### MSW Server Not Working
- Ensure `import '../__tests__/mocks/server'` is in jest.setup.ts
- Verify handlers are catching requests

### Playwright Timeouts
- Check dev server is running: `npm run dev`
- Increase timeout in playwright.config.ts
- Use `page.waitForLoadState('networkidle')`

### Cypress Flaky Tests
- Use `cy.waitForTable()` instead of fixed waits
- Implement custom commands for complex flows
- Use `{force: true}` carefully

## Support & Resources

- **Jest**: https://jestjs.io/
- **React Testing Library**: https://testing-library.com/
- **Playwright**: https://playwright.dev/
- **Cypress**: https://docs.cypress.io/
- **MSW**: https://mswjs.io/

## Next Actions

1. ✅ Setup infrastructure (COMPLETED)
2. 📋 Install dependencies
3. 📋 Run initial test suite
4. 📋 Create component tests (Phase 1)
5. 📋 Create hook tests (Phase 2)
6. 📋 Create integration tests (Phase 3)
7. 📋 Refine E2E tests (Phase 4)
8. 📋 Achieve 80%+ coverage

---

**Infrastructure Setup Date**: July 7, 2026
**Target Coverage**: 80%+
**Implementation Timeline**: 8 weeks
