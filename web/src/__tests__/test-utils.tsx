import React, { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';

/**
 * Custom render function that includes all providers
 * Usage: const { getByText } = renderWithProviders(<Component />);
 */
export function renderWithProviders(
  ui: ReactElement,
  {
    route = '/',
    ...renderOptions
  }: Omit<RenderOptions, 'wrapper'> & { route?: string } = {}
) {
  // Mock next/router
  const mockUseRouter = jest.fn();
  jest.mock('next/router', () => ({
    useRouter: mockUseRouter,
  }));

  return render(ui, { ...renderOptions });
}

/**
 * Mock data generators for consistent test data
 */
export const mockDataGenerators = {
  /**
   * Generate a mock job object
   */
  generateJob: (overrides = {}) => ({
    id: 'job-1',
    title: 'Senior React Developer',
    company: 'Tech Corp',
    location: 'San Francisco, CA',
    remote: 'hybrid' as const,
    salaryMin: 120000,
    salaryMax: 160000,
    salary_currency: 'USD',
    yearsOfExperienceRequired: 5,
    description: 'We are hiring a senior React developer',
    requirements: ['React', 'TypeScript', 'Node.js'],
    responsibilities: [],
    benefits: [],
    postedDate: new Date(),
    jobType: 'full-time',
    industry: 'Technology',
    companySize: 'large',
    level: 'senior',
    tags: [],
    ...overrides,
  }),

  /**
   * Generate a mock capability match
   */
  generateCapabilityMatch: (overrides = {}) => ({
    score: 85,
    matchType: 'strong' as const,
    breakdown: {
      skillsMatch: 80,
      experienceMatch: 90,
      roleTransitionScore: 75,
      culturalFitEstimate: 85,
    },
    reasoning: ['Strong technical background', 'Relevant experience'],
    ...overrides,
  }),

  /**
   * Generate a mock JD optimization result
   */
  generateJDOptimizationResult: (overrides = {}) => ({
    qualityScore: 75,
    summary: 'Job description is well-structured with minor improvements needed',
    issues: [
      {
        id: '1',
        title: 'Vague job requirements',
        description: 'Requirements are not specific enough',
        category: 'clarity',
        severity: 'high' as const,
        suggestion: 'Add specific metrics and KPIs',
      },
    ],
    improvements: [
      'Add specific experience years required',
      'Clarify reporting structure',
    ],
    ...overrides,
  }),

  /**
   * Generate a mock user profile
   */
  generateUserProfile: (overrides = {}) => ({
    id: 'user-1',
    name: 'John Doe',
    email: 'john@example.com',
    role: 'candidate' as const,
    profilePicture: null,
    bio: 'Experienced software engineer',
    location: 'San Francisco, CA',
    skills: ['React', 'TypeScript', 'Node.js'],
    yearsOfExperience: 5,
    createdAt: new Date(),
    updatedAt: new Date(),
    ...overrides,
  }),

  /**
   * Generate a mock application
   */
  generateApplication: (overrides = {}) => ({
    id: 'app-1',
    jobId: 'job-1',
    userId: 'user-1',
    status: 'applied' as const,
    appliedDate: new Date(),
    coverLetter: 'I am interested in this position',
    resumeVersion: 1,
    matchScore: 85,
    ...overrides,
  }),

  /**
   * Generate mock CV analysis
   */
  generateCVAnalysis: (overrides = {}) => ({
    id: 'analysis-1',
    userId: 'user-1',
    jobId: 'job-1',
    matchScore: 78,
    strengths: ['Strong React skills', 'Good communication'],
    gaps: ['Limited system design experience'],
    recommendations: ['Take system design course'],
    createdAt: new Date(),
    ...overrides,
  }),
};

/**
 * Common test data constants
 */
export const testConstants = {
  VALID_JD_TEXT: 'Senior Software Engineer - We are looking for a senior developer with 5+ years of experience in React, TypeScript, and Node.js. The ideal candidate should have strong problem-solving skills and be able to lead a team of developers.',

  SHORT_JD_TEXT: 'Developer needed',

  LONG_JD_TEXT: 'a'.repeat(11000),

  DEFAULT_MIN_JD_LENGTH: 50,
  DEFAULT_MAX_JD_LENGTH: 10000,

  TIMEOUTS: {
    SHORT: 1000,
    MEDIUM: 3000,
    LONG: 10000,
  },
};

/**
 * Custom matchers for common assertions
 */
export const customMatchers = {
  /**
   * Check if element has loading state
   */
  toHaveLoadingState: (element: HTMLElement) => {
    const hasDisabledAttribute = element.hasAttribute('disabled');
    const hasLoadingClass = element.className.includes('opacity-50') || element.className.includes('cursor-not-allowed');
    const hasLoadingText = element.textContent?.includes('Loading') || element.textContent?.includes('...');

    return {
      pass: hasDisabledAttribute || hasLoadingClass || hasLoadingText || false,
      message: () => 'Element does not have loading state',
    };
  },

  /**
   * Check if element has error state
   */
  toHaveErrorState: (element: HTMLElement) => {
    const hasErrorClass = element.className.includes('error') || element.className.includes('red');
    const hasErrorText = element.textContent?.toLowerCase().includes('error');
    const hasAriaInvalid = element.getAttribute('aria-invalid') === 'true';

    return {
      pass: hasErrorClass || hasErrorText || hasAriaInvalid || false,
      message: () => 'Element does not have error state',
    };
  },
};

/**
 * Utility function to wait for async operations
 */
export const waitForAsync = (ms: number = testConstants.TIMEOUTS.SHORT) =>
  new Promise(resolve => setTimeout(resolve, ms));

/**
 * Mock API responses
 */
export const mockApiResponses = {
  successResponse: (data: any) => Promise.resolve(data),
  errorResponse: (error: string) => Promise.reject(new Error(error)),
  delayedResponse: (data: any, delay: number = 1000) =>
    new Promise(resolve => setTimeout(() => resolve(data), delay)),
};

/**
 * Setup and teardown utilities
 */
export const testSetup = {
  /**
   * Setup common mocks
   */
  setupCommonMocks: () => {
    // Mock fetch
    global.fetch = jest.fn();

    // Mock localStorage
    const localStorageMock = {
      getItem: jest.fn(),
      setItem: jest.fn(),
      removeItem: jest.fn(),
      clear: jest.fn(),
    };
    Object.defineProperty(window, 'localStorage', {
      value: localStorageMock,
    });
  },

  /**
   * Cleanup mocks
   */
  cleanupMocks: () => {
    jest.clearAllMocks();
    jest.resetAllMocks();
  },
};
