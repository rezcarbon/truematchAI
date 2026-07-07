import React, { ReactElement } from 'react'
import { render, RenderOptions } from '@testing-library/react'
import { SessionProvider } from 'next-auth/react'

// Mock session data
export const mockSession = {
  user: {
    id: 'test-user-123',
    email: 'test@example.com',
    name: 'Test User',
    role: 'candidate' as const,
    image: 'https://example.com/avatar.jpg',
  },
  expires: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
}

export const mockRecruiterSession = {
  user: {
    id: 'recruiter-123',
    email: 'recruiter@example.com',
    name: 'Recruiter User',
    role: 'recruiter' as const,
    image: 'https://example.com/recruiter-avatar.jpg',
  },
  expires: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
}

// Custom render function with providers
const AllTheProviders = ({ children }: { children: React.ReactNode }) => {
  return (
    <SessionProvider session={mockSession}>
      {children}
    </SessionProvider>
  )
}

export const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>,
) => render(ui, { wrapper: AllTheProviders, ...options })

// Re-export everything from react-testing-library
export * from '@testing-library/react'
export { customRender as render }

// Custom setup utilities
export const createMockFile = (
  name: string = 'test.pdf',
  size: number = 1024,
  type: string = 'application/pdf',
): File => {
  const blob = new Blob(['a'.repeat(size)], { type })
  return new File([blob], name, { type })
}

export const createMockResume = (overrides = {}) => ({
  id: 'resume-123',
  userId: 'user-123',
  filename: 'resume.pdf',
  originalText: 'John Doe\nSoftware Engineer...',
  parsedData: {
    name: 'John Doe',
    email: 'john@example.com',
    phone: '555-1234',
    skills: ['React', 'TypeScript', 'Node.js'],
    experience: [
      {
        company: 'Tech Corp',
        position: 'Senior Developer',
        duration: '2 years',
      },
    ],
  },
  createdAt: new Date('2024-01-01'),
  updatedAt: new Date('2024-01-01'),
  ...overrides,
})

export const createMockJobDescription = (overrides = {}) => ({
  id: 'jd-123',
  title: 'Senior Software Engineer',
  description: 'We are looking for a senior software engineer...',
  requiredSkills: ['React', 'TypeScript', 'Node.js'],
  experience: '5+ years',
  salary: '$150k-$200k',
  location: 'Remote',
  ...overrides,
})

export const createMockCandidate = (overrides = {}) => ({
  id: 'candidate-123',
  name: 'John Doe',
  email: 'john@example.com',
  phone: '555-1234',
  resumeId: 'resume-123',
  matchScore: 85,
  status: 'applied',
  appliedAt: new Date('2024-01-15'),
  ...overrides,
})

export const createMockJob = (overrides = {}) => ({
  id: 'job-123',
  title: 'Senior Frontend Developer',
  company: 'Tech Company',
  location: 'San Francisco, CA',
  description: 'We are looking for a senior frontend developer...',
  requirements: ['React', 'TypeScript', 'CSS'],
  salary: '$120k-$180k',
  posted: new Date('2024-01-01'),
  ...overrides,
})

export const createMockUser = (overrides = {}) => ({
  id: 'user-123',
  email: 'user@example.com',
  name: 'Test User',
  role: 'candidate',
  avatar: 'https://example.com/avatar.jpg',
  createdAt: new Date('2023-01-01'),
  ...overrides,
})

// Wait utilities
export const waitForLoadingToFinish = async () => {
  const { screen, waitFor } = await import('@testing-library/react')
  const loaders = screen.queryAllByRole('progressbar')
  if (loaders.length > 0) {
    await waitFor(() => {
      expect(screen.queryAllByRole('progressbar')).toHaveLength(0)
    })
  }
}

// Type utilities
export interface MockResponse<T = any> {
  data: T
  status: number
  headers?: Record<string, string>
}

export const createMockResponse = <T,>(
  data: T,
  status: number = 200,
): MockResponse<T> => ({
  data,
  status,
})
