import { POST, OPTIONS } from '@/app/api/jd-optimizer/route';
import { NextRequest } from 'next/server';

describe('JD Optimizer API Route', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('returns 400 for missing job description', async () => {
    const req = new NextRequest('http://localhost:3000/api/jd-optimizer', {
      method: 'POST',
      body: JSON.stringify({ jobDescription: '' }),
    });

    const response = await POST(req);
    expect(response.status).toBe(400);

    const data = await response.json();
    expect(data.error).toBe('Job description is required');
  });

  it('returns 400 for null job description', async () => {
    const req = new NextRequest('http://localhost:3000/api/jd-optimizer', {
      method: 'POST',
      body: JSON.stringify({ jobDescription: null }),
    });

    const response = await POST(req);
    expect(response.status).toBe(400);
  });

  it('returns 400 for exceeding max length', async () => {
    const longText = 'a'.repeat(50001);
    const req = new NextRequest('http://localhost:3000/api/jd-optimizer', {
      method: 'POST',
      body: JSON.stringify({ jobDescription: longText }),
    });

    const response = await POST(req);
    expect(response.status).toBe(400);
    const data = await response.json();
    expect(data.error).toContain('exceeds maximum length');
  });

  it('returns 200 for valid job description', async () => {
    const req = new NextRequest('http://localhost:3000/api/jd-optimizer', {
      method: 'POST',
      body: JSON.stringify({
        jobDescription: 'Senior Developer position requiring 5+ years experience',
      }),
    });

    const response = await POST(req);
    expect(response.status).toBe(200);

    const data = await response.json();
    expect(data).toHaveProperty('qualityScore');
    expect(data).toHaveProperty('optimizedJD');
    expect(data).toHaveProperty('issues');
  });

  it('returns quality score between 0-100', async () => {
    const req = new NextRequest('http://localhost:3000/api/jd-optimizer', {
      method: 'POST',
      body: JSON.stringify({
        jobDescription: 'Test job description',
      }),
    });

    const response = await POST(req);
    const data = await response.json();

    expect(data.qualityScore).toBeGreaterThanOrEqual(0);
    expect(data.qualityScore).toBeLessThanOrEqual(100);
  });

  it('detects missing compensation information', async () => {
    const req = new NextRequest('http://localhost:3000/api/jd-optimizer', {
      method: 'POST',
      body: JSON.stringify({
        jobDescription: 'Senior Developer needed. Must have 5 years experience.',
      }),
    });

    const response = await POST(req);
    const data = await response.json();

    const compensationIssue = data.issues.find(
      (issue: any) => issue.category === 'completeness'
    );
    expect(compensationIssue).toBeDefined();
  });

  it('detects weak language', async () => {
    const req = new NextRequest('http://localhost:3000/api/jd-optimizer', {
      method: 'POST',
      body: JSON.stringify({
        jobDescription: 'We need a developer who can we need to help the team',
      }),
    });

    const response = await POST(req);
    const data = await response.json();

    const weakLanguageIssue = data.issues.find(
      (issue: any) => issue.category === 'clarity'
    );
    expect(weakLanguageIssue).toBeDefined();
  });

  it('detects insufficient detail', async () => {
    const req = new NextRequest('http://localhost:3000/api/jd-optimizer', {
      method: 'POST',
      body: JSON.stringify({
        jobDescription: 'Developer wanted',
      }),
    });

    const response = await POST(req);
    const data = await response.json();

    const insufficientDetailIssue = data.issues.find(
      (issue: any) => issue.title === 'Insufficient Detail'
    );
    expect(insufficientDetailIssue).toBeDefined();
  });

  it('returns optimized JD text', async () => {
    const jd = 'We need a developer we need for the team';
    const req = new NextRequest('http://localhost:3000/api/jd-optimizer', {
      method: 'POST',
      body: JSON.stringify({ jobDescription: jd }),
    });

    const response = await POST(req);
    const data = await response.json();

    expect(data.optimizedJD).toBeDefined();
    expect(typeof data.optimizedJD).toBe('string');
    // Optimized text should have improvements
    expect(data.optimizedJD).not.toContain('we need we need');
  });

  it('returns issues array', async () => {
    const req = new NextRequest('http://localhost:3000/api/jd-optimizer', {
      method: 'POST',
      body: JSON.stringify({
        jobDescription: 'Test job description',
      }),
    });

    const response = await POST(req);
    const data = await response.json();

    expect(Array.isArray(data.issues)).toBe(true);
    if (data.issues.length > 0) {
      const issue = data.issues[0];
      expect(issue).toHaveProperty('id');
      expect(issue).toHaveProperty('title');
      expect(issue).toHaveProperty('description');
      expect(issue).toHaveProperty('category');
      expect(issue).toHaveProperty('severity');
    }
  });

  it('returns improvement summary', async () => {
    const req = new NextRequest('http://localhost:3000/api/jd-optimizer', {
      method: 'POST',
      body: JSON.stringify({
        jobDescription: 'Test job description',
      }),
    });

    const response = await POST(req);
    const data = await response.json();

    expect(data.summary).toBeDefined();
    expect(typeof data.summary).toBe('string');
  });

  it('returns improvements list', async () => {
    const req = new NextRequest('http://localhost:3000/api/jd-optimizer', {
      method: 'POST',
      body: JSON.stringify({
        jobDescription: 'Test job description we need help',
      }),
    });

    const response = await POST(req);
    const data = await response.json();

    expect(Array.isArray(data.improvements)).toBe(true);
  });

  it('handles OPTIONS request', async () => {
    const response = await OPTIONS();
    expect(response.status).toBe(200);

    const data = await response.json();
    expect(data.ok).toBe(true);
  });

  it('returns correct issue properties', async () => {
    const req = new NextRequest('http://localhost:3000/api/jd-optimizer', {
      method: 'POST',
      body: JSON.stringify({
        jobDescription: 'Developer we need for our team',
      }),
    });

    const response = await POST(req);
    const data = await response.json();

    if (data.issues.length > 0) {
      const issue = data.issues[0];
      expect(issue.id).toBeDefined();
      expect(['high', 'medium', 'low']).toContain(issue.severity);
      expect(issue.title).toBeDefined();
      expect(issue.description).toBeDefined();
    }
  });

  it('handles whitespace-only input', async () => {
    const req = new NextRequest('http://localhost:3000/api/jd-optimizer', {
      method: 'POST',
      body: JSON.stringify({ jobDescription: '   \n\t  ' }),
    });

    const response = await POST(req);
    expect(response.status).toBe(400);
  });

  it('processes valid input without issues', async () => {
    const req = new NextRequest('http://localhost:3000/api/jd-optimizer', {
      method: 'POST',
      body: JSON.stringify({
        jobDescription:
          'Senior Software Engineer - Salary: $100,000-$150,000. We are seeking an experienced engineer with 5+ years in backend development. Key responsibilities include system design, code review, and team mentorship. Required skills: Python, Go, and SQL.',
      }),
    });

    const response = await POST(req);
    expect(response.status).toBe(200);

    const data = await response.json();
    expect(data.qualityScore).toBeGreaterThan(50);
  });

  it('handles malformed JSON', async () => {
    const req = new NextRequest('http://localhost:3000/api/jd-optimizer', {
      method: 'POST',
      body: '{invalid json}',
    });

    const response = await POST(req);
    expect(response.status).toBe(500);
  });

  it('includes issue fixing suggestions', async () => {
    const req = new NextRequest('http://localhost:3000/api/jd-optimizer', {
      method: 'POST',
      body: JSON.stringify({
        jobDescription: 'We need a developer',
      }),
    });

    const response = await POST(req);
    const data = await response.json();

    if (data.issues.length > 0) {
      const issue = data.issues[0];
      if (issue.suggestion) {
        expect(typeof issue.suggestion).toBe('string');
        expect(issue.suggestion.length).toBeGreaterThan(0);
      }
    }
  });

  it('returns explanation for each issue', async () => {
    const req = new NextRequest('http://localhost:3000/api/jd-optimizer', {
      method: 'POST',
      body: JSON.stringify({
        jobDescription: 'We need we need a developer urgently',
      }),
    });

    const response = await POST(req);
    const data = await response.json();

    data.issues.forEach((issue: any) => {
      if (issue.explanation) {
        expect(typeof issue.explanation).toBe('string');
      }
    });
  });
});
