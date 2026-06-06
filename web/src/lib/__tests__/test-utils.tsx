import React, { ReactElement, ReactNode } from 'react'
import { render, RenderOptions } from '@testing-library/react'

// Mock session for testing
export const mockSession = {
  user: {
    id: '123',
    email: 'test@example.com',
    name: 'Test User',
    role: 'recruiter',
  },
  expires: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
}

interface ExtendedRenderOptions extends Omit<RenderOptions, 'queries'> {
  session?: typeof mockSession
}

export function renderWithProviders(
  ui: ReactElement,
  { session = mockSession, ...renderOptions }: ExtendedRenderOptions = {}
) {
  function Wrapper({ children }: { children: ReactNode }) {
    return <>{children}</>
  }

  return { ...render(ui, { wrapper: Wrapper, ...renderOptions }) }
}

export * from '@testing-library/react'
export { default as userEvent } from '@testing-library/user-event'

/**
 * Mock data generators for testing
 */
export function createMockQueueItem(overrides = {}) {
  return {
    id: '1',
    name: 'Resume 1',
    type: 'cv' as const,
    source: 'email',
    created_at: new Date().toISOString(),
    awaiting_review: true,
    status: 'awaiting_review',
    ...overrides,
  }
}

export function createMockAssessment(overrides = {}) {
  return {
    id: 'assess-1',
    candidate_id: 'cand-1',
    position_id: 'pos-1',
    status: 'pending' as const,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    score: 0,
    feedback: null,
    ...overrides,
  }
}

export function createMockUser(overrides = {}) {
  return {
    id: 'user-1',
    email: 'test@example.com',
    name: 'Test User',
    role: 'recruiter' as const,
    created_at: new Date().toISOString(),
    ...overrides,
  }
}

/**
 * Wait for async operations with custom timeout
 */
export async function waitForAsync(ms = 50) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}
