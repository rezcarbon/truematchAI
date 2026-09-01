# Frontend Testing Guide

## Overview

This document describes the comprehensive Jest testing infrastructure for the TrueMatch Next.js/React frontend. The setup provides 50+ critical path component tests with full coverage of authentication flows, operator dashboard, assessment pipeline, and API client functionality.

## Quick Start

### Running Tests

```bash
# Run all tests
npm test

# Run tests in watch mode (for development)
npm run test:watch

# Generate coverage report
npm run test:coverage

# Run tests in CI mode (for CI/CD pipelines)
npm run test:ci
```

## Test Structure

### Configuration Files

- **jest.config.ts** - Main Jest configuration with coverage thresholds
- **jest.setup.ts** - Test environment setup with mocks for Next.js, next-auth, and WebSocket
- **src/lib/__tests__/test-utils.tsx** - Shared testing utilities and mock data generators

### Test Files

#### Authentication Tests
- **src/app/(auth)/__tests__/auth.test.tsx** (18 tests)
  - Login page rendering and validation
  - Signup form with password confirmation
  - Error handling and loading states
  - Credential submission and session management

#### Operator Dashboard Tests
- **src/components/admin/operators/__tests__/QueueTable.test.tsx** (13 tests)
  - Queue item rendering and filtering
  - Sorting and selection
  - Status badges and type displays
  - Empty states and error handling

- **src/components/admin/operators/__tests__/ActionPanel.test.tsx** (15 tests)
  - Approve/Reject/Hold action modals
  - Form validation and submission
  - Loading and error states
  - Toast notifications
  - Callback handling

#### Hook Tests
- **src/hooks/__tests__/useAgentOperator.test.ts** (14 tests)
  - WebSocket connection management
  - Real-time event handling (queue_item_action, agent_status_change, processing_alert)
  - Event history management
  - Callback registration and unsubscription
  - Connection lifecycle and error handling

#### API Tests
- **src/lib/__tests__/api.test.ts** (20 tests)
  - GET requests with fallback data
  - POST/PATCH mutations
  - Error handling and extraction
  - Authentication headers
  - Request configuration
  - Queue and assessment operations
  - Resume upload
  - Pagination and filtering

#### Utility Tests
- **src/lib/__tests__/utils.test.ts** (25+ tests)
  - Date formatting
  - String manipulation and validation
  - Object and array utilities
  - Email and URL validation
  - Number formatting and calculations
  - Promise utilities (retry, timeout)
  - Status mapping and icons
  - Debounce and throttle utilities

#### Integration Tests
- **__tests__/integration/operator-dashboard.test.tsx** (15 tests)
  - Full operator dashboard workflow
  - Queue item selection and detail display
  - Sequential actions (approve/reject)
  - State consistency across operations
  - Loading and error states
  - Success/failure feedback

## Coverage Targets

The project maintains the following coverage thresholds:

```typescript
coverageThreshold: {
  global: {
    branches: 50,     // Critical paths
    functions: 50,    // Exported functions
    lines: 50,        // Code lines
    statements: 50,   // Statements
  },
}
```

## Test Utilities

### Mock Session
```typescript
import { mockSession } from '@/lib/__tests__/test-utils'

const customSession = {
  ...mockSession,
  user: { ...mockSession.user, role: 'admin' },
}
```

### Mock Data Generators
```typescript
import {
  createMockQueueItem,
  createMockAssessment,
  createMockUser,
} from '@/lib/__tests__/test-utils'

const queueItem = createMockQueueItem({ name: 'Custom Name' })
const assessment = createMockAssessment({ status: 'completed' })
const user = createMockUser({ role: 'admin' })
```

### Custom Render with Providers
```typescript
import { renderWithProviders } from '@/lib/__tests__/test-utils'

test('renders with providers', () => {
  const { getByText } = renderWithProviders(<MyComponent />)
  expect(getByText('Content')).toBeInTheDocument()
})
```

## Mocked External Dependencies

### Next.js Router (next/router)
```typescript
jest.mock('next/router', () => ({
  useRouter() {
    return {
      route: '/',
      pathname: '/',
      push: jest.fn(),
      replace: jest.fn(),
      // ... other methods
    }
  },
}))
```

### Next.js Navigation (next/navigation)
```typescript
jest.mock('next/navigation', () => ({
  useRouter() {
    return {
      push: jest.fn(),
      back: jest.fn(),
    }
  },
  usePathname() {
    return '/'
  },
  useSearchParams() {
    return new URLSearchParams()
  },
}))
```

### NextAuth (next-auth/react)
```typescript
jest.mock('next-auth/react', () => ({
  useSession() {
    return {
      data: mockSession,
      status: 'authenticated',
    }
  },
  signIn: jest.fn(),
  signOut: jest.fn(),
  getSession: jest.fn(),
}))
```

### WebSocket
```typescript
class MockWebSocket {
  readyState = WebSocket.CONNECTING
  send = jest.fn()
  close = jest.fn()
  onopen: (() => void) | null = null
  onmessage: ((event: MessageEvent) => void) | null = null
  onerror: ((event: Event) => void) | null = null
  onclose: (() => void) | null = null
}
```

## Writing New Tests

### Component Tests
```typescript
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MyComponent } from './MyComponent'

describe('MyComponent', () => {
  it('renders with expected content', () => {
    render(<MyComponent />)
    expect(screen.getByText('Expected')).toBeInTheDocument()
  })

  it('handles user interactions', async () => {
    const user = userEvent.setup()
    render(<MyComponent />)

    await user.click(screen.getByRole('button', { name: /submit/i }))

    await waitFor(() => {
      expect(screen.getByText(/success/i)).toBeInTheDocument()
    })
  })
})
```

### Hook Tests
```typescript
import { renderHook, waitFor } from '@testing-library/react'
import { useMyHook } from './useMyHook'

describe('useMyHook', () => {
  it('returns expected value', async () => {
    const { result } = renderHook(() => useMyHook())

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })
  })
})
```

### API Tests
```typescript
describe('API client', () => {
  it('fetches data with correct parameters', async () => {
    global.fetch = jest.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => ({ id: '1', name: 'Test' }),
    })

    const data = await fetch('/api/endpoint')
    const json = await data.json()

    expect(global.fetch).toHaveBeenCalledWith(
      '/api/endpoint',
      expect.objectContaining({ method: 'GET' })
    )
    expect(json).toEqual({ id: '1', name: 'Test' })
  })
})
```

## Best Practices

### 1. Use Semantic Queries
```typescript
// Good
screen.getByRole('button', { name: /submit/i })
screen.getByLabelText(/email/i)
screen.getByText(/success message/i)

// Avoid
screen.getByTestId('submit-btn')
screen.getByClassName('email-input')
```

### 2. Wait for Async Updates
```typescript
// Good
await waitFor(() => {
  expect(screen.getByText(/loaded/i)).toBeInTheDocument()
})

// Avoid
expect(screen.getByText(/loaded/i)).toBeInTheDocument() // might fail before async completes
```

### 3. Use User Event Over Fire Event
```typescript
// Good
const user = userEvent.setup()
await user.click(button)
await user.type(input, 'text')

// Avoid
fireEvent.click(button)
fireEvent.change(input, { target: { value: 'text' } })
```

### 4. Mock External Dependencies
```typescript
// Good
jest.mock('@/lib/api', () => ({
  fetchData: jest.fn(),
}))

// Avoid - Don't test implementation details
```

### 5. Test User Behavior, Not Implementation
```typescript
// Good
await user.click(screen.getByRole('button', { name: /approve/i }))
expect(screen.getByText(/success/i)).toBeInTheDocument()

// Avoid
expect(component.state.isApproved).toBe(true)
```

## CI/CD Integration

The test suite integrates with GitHub Actions via `.github/workflows/test.yml`:

### On Push/PR
- Runs tests on Node.js 18.x and 20.x
- Generates coverage reports
- Uploads to Codecov
- Comments on PRs with coverage changes

### Coverage Reports
Coverage reports are generated in `coverage/` directory:
- `coverage/lcov.info` - For Codecov
- `coverage/coverage-final.json` - Detailed JSON
- `coverage/index.html` - HTML coverage report

## Debugging Tests

### Run Specific Test File
```bash
npm test -- auth.test.tsx
```

### Run Specific Test Case
```bash
npm test -- auth.test.tsx -t "renders login form"
```

### Debug Mode
```bash
node --inspect-brk node_modules/.bin/jest --runInBand
```

### Watch Specific Files
```bash
npm test -- --watch --testPathPattern=auth
```

## Common Issues and Solutions

### Issue: Tests timeout
**Solution:** Increase timeout in jest.config.ts
```typescript
testTimeout: 10000, // 10 seconds
```

### Issue: Mock not working
**Solution:** Clear mocks between tests
```typescript
beforeEach(() => {
  jest.clearAllMocks()
})
```

### Issue: Async state not updating
**Solution:** Use proper async/await with waitFor
```typescript
await waitFor(() => {
  expect(something).toBeInTheDocument()
})
```

### Issue: WebSocket mock not connected
**Solution:** Ensure mock WebSocket implementation in jest.setup.ts

## Future Improvements

- [ ] E2E tests with Playwright or Cypress
- [ ] Performance testing with lighthouse
- [ ] Visual regression testing
- [ ] Accessibility (a11y) testing with jest-axe
- [ ] Component snapshot testing
- [ ] Load testing for WebSocket connections

## Resources

- [Jest Documentation](https://jestjs.io/)
- [React Testing Library](https://testing-library.com/react)
- [Testing Best Practices](https://kentcdodds.com/blog/common-mistakes-with-react-testing-library)
- [Next.js Testing Guide](https://nextjs.org/docs/testing)

## Support

For questions about the testing setup, refer to:
1. Test files in `src/**/__tests__/`
2. Jest configuration in `jest.config.ts`
3. Test utilities in `src/lib/__tests__/test-utils.tsx`
