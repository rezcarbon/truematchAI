import { http, HttpResponse } from 'msw';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000/api';

export const handlers = [
  // Resume endpoints
  http.post(`${API_BASE}/resume/upload`, async ({ request }) => {
    const formData = await request.formData();
    const file = formData.get('file') as File;

    if (!file) {
      return HttpResponse.json(
        { error: 'No file provided' },
        { status: 400 }
      );
    }

    return HttpResponse.json(
      {
        id: 'resume-' + Math.random().toString(36).substr(2, 9),
        filename: file.name,
        size: file.size,
        uploadedAt: new Date().toISOString(),
      },
      { status: 201 }
    );
  }),

  http.get(`${API_BASE}/resume/:resumeId/versions`, ({ params }) => {
    return HttpResponse.json(
      {
        versions: [
          {
            id: 'v1',
            resumeId: params.resumeId,
            versionNumber: 1,
            createdAt: new Date().toISOString(),
            title: 'Original',
          },
          {
            id: 'v2',
            resumeId: params.resumeId,
            versionNumber: 2,
            createdAt: new Date(Date.now() - 86400000).toISOString(),
            title: 'Optimized for Tech Role',
          },
        ],
      },
      { status: 200 }
    );
  }),

  http.get(
    `${API_BASE}/resume/:resumeId/versions/:versionId`,
    ({ params }) => {
      return HttpResponse.json(
        {
          id: params.versionId,
          resumeId: params.resumeId,
          versionNumber: 1,
          content: 'Resume content here...',
          createdAt: new Date().toISOString(),
        },
        { status: 200 }
      );
    }
  ),

  http.post(
    `${API_BASE}/resume/:resumeId/versions/:versionId/annotate`,
    ({ params }) => {
      return HttpResponse.json(
        {
          id: params.versionId,
          annotations: [
            {
              id: 'ann-1',
              type: 'highlight',
              text: 'Senior Developer',
              suggestion: 'Could be more prominent',
            },
          ],
        },
        { status: 200 }
      );
    }
  ),

  http.post(`${API_BASE}/resume/:resumeId/compare`, ({ params }) => {
    return HttpResponse.json(
      {
        resumeId: params.resumeId,
        comparison: {
          added: ['New skill added'],
          removed: ['Old skill removed'],
          modified: ['Title changed from Developer to Senior Developer'],
        },
      },
      { status: 200 }
    );
  }),

  http.post(`${API_BASE}/resume/:resumeId/revert`, ({ params }) => {
    return HttpResponse.json(
      {
        message: 'Resume reverted successfully',
        resumeId: params.resumeId,
      },
      { status: 200 }
    );
  }),

  // JD Optimizer endpoints
  http.post(`${API_BASE}/jd-optimizer`, async ({ request }) => {
    const body = await request.json() as any;

    return HttpResponse.json(
      {
        id: 'optimizer-' + Math.random().toString(36).substr(2, 9),
        optimizedJD: body.jobDescription
          ? body.jobDescription.toUpperCase() + ' [OPTIMIZED]'
          : 'Optimized JD',
        improvements: [
          'Added clarity to requirements',
          'Improved formatting',
          'Enhanced keyword optimization',
        ],
        matchScore: 0.85,
      },
      { status: 201 }
    );
  }),

  // Job Search endpoints
  http.get(`${API_BASE}/jobs`, () => {
    return HttpResponse.json(
      {
        jobs: [
          {
            id: 'job-1',
            title: 'Senior Frontend Developer',
            company: 'Tech Corp',
            location: 'San Francisco',
            salary: '$120k-$180k',
            matchScore: 0.88,
          },
          {
            id: 'job-2',
            title: 'Full Stack Engineer',
            company: 'StartUp Inc',
            location: 'Remote',
            salary: '$100k-$150k',
            matchScore: 0.75,
          },
        ],
        total: 2,
      },
      { status: 200 }
    );
  }),

  // Application endpoints
  http.post(`${API_BASE}/applications`, async ({ request }) => {
    const body = await request.json() as any;

    return HttpResponse.json(
      {
        id: 'app-' + Math.random().toString(36).substr(2, 9),
        jobId: body.jobId,
        candidateId: body.candidateId,
        status: 'applied',
        appliedAt: new Date().toISOString(),
      },
      { status: 201 }
    );
  }),

  http.get(`${API_BASE}/applications`, () => {
    return HttpResponse.json(
      {
        applications: [
          {
            id: 'app-1',
            jobId: 'job-1',
            title: 'Senior Frontend Developer',
            company: 'Tech Corp',
            status: 'applied',
            appliedAt: new Date().toISOString(),
          },
        ],
        total: 1,
      },
      { status: 200 }
    );
  }),

  // Auth endpoints (if not using NextAuth)
  http.post(`${API_BASE}/auth/login`, async ({ request }) => {
    const body = await request.json() as any;

    if (!body.email || !body.password) {
      return HttpResponse.json(
        { error: 'Invalid credentials' },
        { status: 401 }
      );
    }

    return HttpResponse.json(
      {
        token: 'mock-jwt-token',
        user: {
          id: 'user-123',
          email: body.email,
          name: 'Test User',
        },
      },
      { status: 200 }
    );
  }),

  // Catch-all for unhandled requests
  http.all('*', () => {
    console.warn('Unhandled request to:', new URL(arguments[0] as any).href);
    return HttpResponse.json(
      { error: 'Not found' },
      { status: 404 }
    );
  }),
];
