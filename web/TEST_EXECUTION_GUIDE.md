# Test Execution Guide

## Quick Start

### Install Dependencies
```bash
cd web
npm install
```

### Run All Tests
```bash
npm run test:all
```

## Test Commands

### Unit Tests (Jest)

```bash
# Run all unit tests once
npm run test

# Run unit tests in watch mode (re-runs on file changes)
npm run test:watch

# Run unit tests with coverage report
npm run test:coverage

# Run unit tests for CI (optimized for CI environments)
npm run test:ci

# Run tests for specific file
npm run test -- src/components/candidate/JobCard.test.tsx

# Run tests matching a pattern
npm run test -- --testNamePattern="JobCard"
```

### Integration Tests

```bash
# Run all integration tests
npm run test:integration

# Run specific integration test
npm run test:integration -- applications.test.tsx

# Run integration tests with coverage
npm run test:integration -- --coverage
```

### E2E Tests (Playwright)

```bash
# Run all E2E tests
npm run test:e2e

# Run E2E tests in debug mode (interactive)
npm run test:e2e:debug

# Run E2E tests in UI mode (visual interface)
npm run test:e2e:ui

# Run specific E2E test file
npm run test:e2e -- candidates.spec.ts

# Run E2E tests in a specific browser
npm run test:e2e -- --project=chromium
npm run test:e2e -- --project=firefox
npm run test:e2e -- --project=webkit

# Run E2E tests with headed browser (see browser window)
npm run test:e2e -- --headed

# Run E2E tests with specific number of workers
npm run test:e2e -- --workers=4
```

### Coverage Reports

```bash
# Generate coverage report
npm run test:coverage

# Generate coverage report for CI
npm run test:ci

# Display coverage report summary
npm run test:coverage:report

# Coverage report with all details
npm run test:coverage -- --verbose
```

### Combined Test Suites

```bash
# Run all tests (unit + integration + E2E)
npm run test:all

# Run unit and integration tests
npm run test && npm run test:integration

# Run unit tests with full coverage report
npm run test:coverage -- --coverage-reporters=text-summary
```

## Test Organization

### By Component/Feature

```bash
# Test JDOptimizer components
npm run test -- JDOptimizer
npm run test -- JDSimulationForm
npm run test -- QualityScoreGauge
npm run test -- JDSimulationResults

# Test Candidate components
npm run test -- JobCard
npm run test -- CVAnalysisWidget
npm run test -- ApplicationCard

# Test Shared components
npm run test -- ScoreGauge
npm run test -- NotificationBell
npm run test -- UploadZone
```

### By Test Type

```bash
# All unit tests for candidate workflow
npm run test -- src/components/candidate

# All integration tests for specific workflow
npm run test:integration -- jd-simulation.test.tsx

# All E2E tests for candidates
npm run test:e2e -- candidates.spec.ts
```

## Debugging Tests

### Debug Mode

```bash
# Debug with Node inspector
node --inspect-brk node_modules/.bin/jest --runInBand

# Debug specific test
node --inspect-brk node_modules/.bin/jest --runInBand --testNamePattern="JobCard"
```

### Verbose Output

```bash
# Show detailed test output
npm run test -- --verbose

# Show test names as they run
npm run test -- --verbose --testNamePattern=".*"

# Show console logs from tests
npm run test -- --verbose --no-coverage
```

### E2E Debug

```bash
# Interactive debug mode (best for E2E)
npm run test:e2e:debug

# Debug with headed browser
npm run test:e2e -- --headed --debug

# Debug specific test
npx playwright test e2e/candidates.spec.ts --headed --debug
```

### View Test Coverage in Browser

```bash
# After running coverage
open coverage/lcov-report/index.html

# On Windows
start coverage/lcov-report/index.html

# On Linux
xdg-open coverage/lcov-report/index.html
```

## Test Configuration

### Jest Configuration (jest.config.js)

- **Test Environment**: jsdom (browser-like environment)
- **Setup File**: jest.setup.ts
- **Module Mapper**: Maps `@/` to `src/`
- **Test Match Pattern**: `**/?(*.)+(spec|test).ts?(x)`
- **Coverage Thresholds**: 
  - Global: 30 branches, 15 functions, 5 lines, 5 statements
  - Components: 50 branches, 50 functions, 50 lines, 50 statements

### Playwright Configuration (playwright.config.ts)

- **Test Directory**: ./e2e
- **Parallel**: Enabled
- **Retries**: 2 on CI, 0 locally
- **Timeout**: 30 seconds per test
- **Base URL**: http://localhost:3000
- **Browsers**: Chrome, Firefox, Safari, Mobile Chrome, Mobile Safari
- **Screenshots**: Saved on failure
- **Videos**: Retained on failure
- **Traces**: Saved on first retry

## Best Practices

### 1. Before Running Tests

```bash
# Ensure code is built
npm run build

# Check for TypeScript errors
npm run typecheck

# Lint code
npm run lint
```

### 2. Running Tests Locally

```bash
# Start development server (in separate terminal)
npm run dev

# Then run E2E tests
npm run test:e2e
```

### 3. Running Tests in CI

```bash
# Recommended CI command
npm run test:ci

# Includes
# - Unit tests with coverage
# - CI-optimized settings
# - No watch mode
# - Limited parallel workers
```

## Performance Tips

### Faster Test Execution

```bash
# Run only changed files
npm run test -- --onlyChanged

# Run tests matching pattern (faster than running all)
npm run test -- --testNamePattern="specific-test"

# Run tests in single worker for debugging
npm run test -- --runInBand

# Run tests in 4 workers (parallel)
npm run test -- --maxWorkers=4
```

### Faster E2E Tests

```bash
# Run only chromium (fastest)
npm run test:e2e -- --project=chromium

# Run tests in parallel (limit to hardware cores)
npm run test:e2e -- --workers=4

# Skip headed browser (faster)
npm run test:e2e -- --project=chromium
```

## Troubleshooting

### Tests Not Running

```bash
# Clear Jest cache
npm run test -- --clearCache

# Reinstall dependencies
rm -rf node_modules
npm install

# Check Node version (should be 16+)
node --version
```

### Failing Tests

```bash
# Run with verbose output
npm run test -- --verbose

# Run in watch mode to iterate
npm run test:watch

# Run test file in isolation
npm run test -- src/components/candidate/JobCard.test.tsx
```

### E2E Tests Flaky

```bash
# Increase timeout
export PLAYWRIGHT_TEST_TIMEOUT_MS=60000
npm run test:e2e

# Run with headed browser to see what's happening
npm run test:e2e -- --headed

# Debug mode (interactive)
npm run test:e2e:debug
```

### Coverage Not Meeting Threshold

```bash
# View coverage report
npm run test:coverage

# See detailed coverage
npm run test:coverage -- --coverage-reporters=text-summary

# Open HTML report
open coverage/lcov-report/index.html
```

## Continuous Integration

### GitHub Actions

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Run unit tests
        run: npm run test:ci
      
      - name: Run integration tests
        run: npm run test:integration
      
      - name: Run E2E tests
        run: npm run test:e2e
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Coverage Reports

### View Coverage

```bash
# Text summary
npm run test:coverage

# HTML report
npm run test:coverage -- --coverage-reporters=html
open coverage/index.html

# LCOV report
npm run test:coverage -- --coverage-reporters=lcov
open coverage/lcov-report/index.html

# JSON report
npm run test:coverage -- --coverage-reporters=json
```

### Coverage Thresholds by Directory

- **Global**: Lines 5%, Statements 5%, Branches 30%, Functions 15%
- **Components**: Lines 50%, Statements 50%, Branches 50%, Functions 50%
- **Hooks**: Lines 60%, Statements 60%, Branches 60%, Functions 60%
- **Lib**: Lines 70%, Statements 70%, Branches 70%, Functions 70%

## Environment Variables

### Jest Environment

```bash
# Suppress console output during tests
NODE_ENV=test npm run test

# Show debug output
DEBUG=* npm run test

# Use specific test timeout
JEST_TIMEOUT=10000 npm run test
```

### Playwright Environment

```bash
# Set base URL
PLAYWRIGHT_TEST_BASE_URL=http://localhost:3000 npm run test:e2e

# Set number of workers
PLAYWRIGHT_WORKERS=4 npm run test:e2e

# Enable debug mode
PWDEBUG=1 npm run test:e2e
```

## Useful VSCode Extensions

For better test development experience:

1. **Jest Runner** - Run tests directly from VSCode
2. **Test Explorer** - Visual test explorer
3. **Playwright Test for VSCode** - Run E2E tests from editor
4. **Coverage Gutters** - Show coverage in editor

## Common Test Patterns

### Testing Component Props

```typescript
it('renders with correct props', () => {
  render(<Component prop="value" />);
  expect(screen.getByText('value')).toBeInTheDocument();
});
```

### Testing User Interactions

```typescript
it('handles click event', async () => {
  const user = userEvent.setup();
  render(<Component />);
  
  const button = screen.getByRole('button');
  await user.click(button);
  
  expect(screen.getByText('Clicked')).toBeInTheDocument();
});
```

### Testing Async Operations

```typescript
it('loads data asynchronously', async () => {
  render(<Component />);
  
  const result = await screen.findByText('Loaded');
  expect(result).toBeInTheDocument();
});
```

### Testing Error States

```typescript
it('displays error message', async () => {
  const mockFn = jest.fn().mockRejectedValue(new Error('API Error'));
  render(<Component onSubmit={mockFn} />);
  
  await userEvent.click(screen.getByRole('button'));
  
  expect(screen.getByText('API Error')).toBeInTheDocument();
});
```

## Resources

- [Jest Documentation](https://jestjs.io/docs/getting-started)
- [React Testing Library](https://testing-library.com/docs/react-testing-library/intro/)
- [Playwright Documentation](https://playwright.dev/docs/intro)
- [Testing Best Practices](https://kentcdodds.com/blog/common-mistakes-with-react-testing-library)

## Getting Help

1. Check TEST_IMPLEMENTATION_SUMMARY.md for overview
2. Review similar test files for patterns
3. Check jest.setup.ts for global mocks
4. Check test-utils.tsx for available utilities
5. Run test in debug mode to inspect
6. Check Playwright traces for E2E failures

---

**Last Updated**: 2024-07-08
**Version**: 1.0
**Status**: Ready for Use
