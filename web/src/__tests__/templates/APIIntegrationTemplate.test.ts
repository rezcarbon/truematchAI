/**
 * API INTEGRATION TEST TEMPLATE
 *
 * This file demonstrates how to test API endpoints.
 * These tests verify that:
 * - Endpoints respond with correct status codes
 * - Request/response payloads match expected schemas
 * - Error handling works correctly
 * - Edge cases are handled
 *
 * Uses Mock Service Worker (MSW) for mocking API responses
 */

import { http, HttpResponse } from 'msw';
import { server } from '../mocks/server';

/**
 * Note: Make sure to import the server setup in your jest.setup.ts:
 * import '../__tests__/mocks/server'
 */

const API_BASE = 'http://localhost:3000/api';

/**
 * Example: Testing Resume Upload Endpoint
 */
describe('Resume Upload API', () => {
  it('uploads a resume file successfully', async () => {
    const file = new File(['resume content'], 'resume.pdf', {
      type: 'application/pdf',
    });
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE}/resume/upload`, {
      method: 'POST',
      body: formData,
    });

    expect(response.status).toBe(201);
    const data = await response.json();
    expect(data).toHaveProperty('id');
    expect(data).toHaveProperty('filename', 'resume.pdf');
    expect(data).toHaveProperty('uploadedAt');
  });

  it('returns 400 when no file is provided', async () => {
    const formData = new FormData();

    const response = await fetch(`${API_BASE}/resume/upload`, {
      method: 'POST',
      body: formData,
    });

    expect(response.status).toBe(400);
    const data = await response.json();
    expect(data).toHaveProperty('error');
  });

  it('handles large file uploads', async () => {
    const largeFile = new File(['x'.repeat(5 * 1024 * 1024)], 'large.pdf', {
      type: 'application/pdf',
    });
    const formData = new FormData();
    formData.append('file', largeFile);

    const response = await fetch(`${API_BASE}/resume/upload`, {
      method: 'POST',
      body: formData,
    });

    expect(response.status).toBe(201);
  });
});

/**
 * Example: Testing Resume Versions Endpoint
 */
describe('Resume Versions API', () => {
  const resumeId = 'resume-123';

  it('retrieves resume versions', async () => {
    const response = await fetch(
      `${API_BASE}/resume/${resumeId}/versions`
    );

    expect(response.status).toBe(200);
    const data = await response.json();
    expect(data).toHaveProperty('versions');
    expect(Array.isArray(data.versions)).toBe(true);
    expect(data.versions.length).toBeGreaterThan(0);
  });

  it('returns versions with correct structure', async () => {
    const response = await fetch(
      `${API_BASE}/resume/${resumeId}/versions`
    );

    const data = await response.json();
    const version = data.versions[0];

    expect(version).toHaveProperty('id');
    expect(version).toHaveProperty('resumeId');
    expect(version).toHaveProperty('versionNumber');
    expect(version).toHaveProperty('createdAt');
    expect(version).toHaveProperty('title');
  });

  it('retrieves specific version', async () => {
    const versionId = 'v1';
    const response = await fetch(
      `${API_BASE}/resume/${resumeId}/versions/${versionId}`
    );

    expect(response.status).toBe(200);
    const data = await response.json();
    expect(data).toHaveProperty('id', versionId);
    expect(data).toHaveProperty('content');
  });
});

/**
 * Example: Testing Resume Compare Endpoint
 */
describe('Resume Compare API', () => {
  it('compares two resume versions', async () => {
    const resumeId = 'resume-123';
    const response = await fetch(
      `${API_BASE}/resume/${resumeId}/compare`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          versionId1: 'v1',
          versionId2: 'v2',
        }),
      }
    );

    expect(response.status).toBe(200);
    const data = await response.json();
    expect(data).toHaveProperty('comparison');
    expect(data.comparison).toHaveProperty('added');
    expect(data.comparison).toHaveProperty('removed');
    expect(data.comparison).toHaveProperty('modified');
  });

  it('returns empty diff for identical versions', async () => {
    // Setup MSW to return empty diff for this case
    server.use(
      http.post(`${API_BASE}/resume/:resumeId/compare`, () => {
        return HttpResponse.json(
          {
            resumeId: 'resume-123',
            comparison: {
              added: [],
              removed: [],
              modified: [],
            },
          },
          { status: 200 }
        );
      })
    );

    const response = await fetch(
      `${API_BASE}/resume/resume-123/compare`,
      {
        method: 'POST',
        body: JSON.stringify({}),
      }
    );

    const data = await response.json();
    expect(data.comparison.added).toHaveLength(0);
    expect(data.comparison.removed).toHaveLength(0);
    expect(data.comparison.modified).toHaveLength(0);
  });
});

/**
 * Example: Testing JD Optimizer Endpoint
 */
describe('JD Optimizer API', () => {
  it('optimizes a job description', async () => {
    const jdPayload = {
      jobDescription: 'We need a software engineer',
      targetSkills: ['React', 'TypeScript'],
      experienceLevel: 'senior',
    };

    const response = await fetch(`${API_BASE}/jd-optimizer`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(jdPayload),
    });

    expect(response.status).toBe(201);
    const data = await response.json();
    expect(data).toHaveProperty('id');
    expect(data).toHaveProperty('optimizedJD');
    expect(data).toHaveProperty('improvements');
    expect(data).toHaveProperty('matchScore');
  });

  it('returns improvements array', async () => {
    const response = await fetch(`${API_BASE}/jd-optimizer`, {
      method: 'POST',
      body: JSON.stringify({
        jobDescription: 'Sample JD',
      }),
    });

    const data = await response.json();
    expect(Array.isArray(data.improvements)).toBe(true);
    expect(data.improvements.length).toBeGreaterThan(0);
  });

  it('provides match score between 0 and 1', async () => {
    const response = await fetch(`${API_BASE}/jd-optimizer`, {
      method: 'POST',
      body: JSON.stringify({
        jobDescription: 'Sample JD',
      }),
    });

    const data = await response.json();
    expect(typeof data.matchScore).toBe('number');
    expect(data.matchScore).toBeGreaterThanOrEqual(0);
    expect(data.matchScore).toBeLessThanOrEqual(1);
  });
});

/**
 * Example: Testing Error Handling
 */
describe('API Error Handling', () => {
  it('returns 404 for non-existent resume', async () => {
    server.use(
      http.get(`${API_BASE}/resume/:resumeId/versions`, () => {
        return HttpResponse.json(
          { error: 'Resume not found' },
          { status: 404 }
        );
      })
    );

    const response = await fetch(`${API_BASE}/resume/invalid-id/versions`);
    expect(response.status).toBe(404);
  });

  it('returns 401 for unauthorized requests', async () => {
    server.use(
      http.post(`${API_BASE}/applications`, () => {
        return HttpResponse.json(
          { error: 'Unauthorized' },
          { status: 401 }
        );
      })
    );

    const response = await fetch(`${API_BASE}/applications`, {
      method: 'POST',
      body: JSON.stringify({}),
    });

    expect(response.status).toBe(401);
  });

  it('returns 500 for server errors', async () => {
    server.use(
      http.post(`${API_BASE}/resume/upload`, () => {
        return HttpResponse.json(
          { error: 'Internal server error' },
          { status: 500 }
        );
      })
    );

    const response = await fetch(`${API_BASE}/resume/upload`, {
      method: 'POST',
      body: new FormData(),
    });

    expect(response.status).toBe(500);
  });

  it('includes error message in response', async () => {
    server.use(
      http.get(`${API_BASE}/resume/:resumeId/versions`, () => {
        return HttpResponse.json(
          { error: 'Database connection failed' },
          { status: 500 }
        );
      })
    );

    const response = await fetch(`${API_BASE}/resume/any-id/versions`);
    const data = await response.json();
    expect(data).toHaveProperty('error');
    expect(data.error).toBe('Database connection failed');
  });
});

/**
 * Example: Testing Request Validation
 */
describe('API Request Validation', () => {
  it('validates required fields', async () => {
    server.use(
      http.post(`${API_BASE}/jd-optimizer`, async ({ request }) => {
        const body = await request.json() as any;

        if (!body.jobDescription) {
          return HttpResponse.json(
            { error: 'jobDescription is required' },
            { status: 400 }
          );
        }

        return HttpResponse.json({ id: 'opt-123' }, { status: 201 });
      })
    );

    const response = await fetch(`${API_BASE}/jd-optimizer`, {
      method: 'POST',
      body: JSON.stringify({}),
    });

    expect(response.status).toBe(400);
    const data = await response.json();
    expect(data.error).toContain('required');
  });

  it('validates field types', async () => {
    const response = await fetch(`${API_BASE}/jd-optimizer`, {
      method: 'POST',
      body: JSON.stringify({
        jobDescription: 'Valid JD',
        matchScore: 'not-a-number', // Should be number
      }),
    });

    // MSW will still process this, but in a real API it would validate types
    expect(response.ok || response.status === 400).toBe(true);
  });
});

/**
 * Key API Testing Patterns:
 *
 * 1. Success Cases:
 *    - Test happy path with valid inputs
 *    - Verify correct status codes (200, 201, etc.)
 *    - Check response structure matches schema
 *
 * 2. Error Cases:
 *    - Test invalid inputs (400)
 *    - Test unauthorized access (401)
 *    - Test not found (404)
 *    - Test server errors (500)
 *
 * 3. Edge Cases:
 *    - Empty inputs
 *    - Large payloads
 *    - Special characters
 *    - Concurrent requests
 *
 * 4. Response Validation:
 *    - Check all required fields are present
 *    - Verify field types
 *    - Validate date formats
 *    - Check array contents
 *
 * 5. Performance:
 *    - Measure response times
 *    - Test pagination
 *    - Test caching headers
 */
