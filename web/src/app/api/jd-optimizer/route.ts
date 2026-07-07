import { NextRequest, NextResponse } from 'next/server';
import {
  JDOptimizationRequest,
  JDOptimizationResult,
  JDOptimizationError,
  OptimizationIssue,
} from '@/types/jd-optimizer';

/**
 * Mock JD optimization logic
 * Replace this with actual AI/ML backend integration
 */
function analyzeJobDescription(jd: string): {
  score: number;
  issues: OptimizationIssue[];
  optimized: string;
} {
  const issues: OptimizationIssue[] = [];
  let optimized = jd;
  let score = 60;

  // Check for common issues
  if (jd.includes('we need')) {
    issues.push({
      id: 'issue-1',
      title: 'Weak Language',
      description: 'Replace "we need" with more specific, active language',
      category: 'clarity',
      severity: 'medium',
      problematicText: 'we need',
      suggestion: 'seeks, requires, or must have',
      explanation:
        'Active voice and specific requirements are more engaging and clear to candidates',
      impact:
        'Improved candidate clarity and alignment with job requirements',
      isFixed: false,
    });
    score -= 10;
  }

  if (!jd.includes('salary') && !jd.includes('compensation')) {
    issues.push({
      id: 'issue-2',
      title: 'Missing Compensation Information',
      description: 'Include salary range or compensation details',
      category: 'completeness',
      severity: 'high',
      suggestion: 'Add salary range (e.g., $80,000 - $120,000)',
      explanation:
        'Candidates want to know compensation before applying; this reduces unqualified applications',
      impact: 'Higher quality applications and better candidate satisfaction',
      isFixed: false,
    });
    score -= 15;
  }

  if (jd.length < 300) {
    issues.push({
      id: 'issue-3',
      title: 'Insufficient Detail',
      description: 'Job description is too brief',
      category: 'completeness',
      severity: 'medium',
      suggestion: 'Expand with more responsibilities, requirements, and benefits',
      explanation:
        'Detailed descriptions attract better-qualified candidates and reduce turnover',
      impact: 'Better candidate matching and reduced hiring cycle time',
      isFixed: false,
    });
    score -= 10;
  }

  if (jd.toLowerCase().includes('asap') || jd.toLowerCase().includes('urgently')) {
    issues.push({
      id: 'issue-4',
      title: 'Urgent Tone Issues',
      description: 'Excessive urgency language may deter candidates',
      category: 'tone',
      severity: 'low',
      problematicText: 'ASAP/Urgently',
      suggestion: 'Replace with specific start date or timeline',
      explanation:
        'Urgency can signal poor planning and discourage quality candidates from applying',
      impact: 'Improved perception of company professionalism',
      isFixed: false,
    });
    score -= 5;
  }

  if (!jd.match(/experience|years|background/i)) {
    issues.push({
      id: 'issue-5',
      title: 'Vague Experience Requirements',
      description: 'Experience requirements lack specificity',
      category: 'clarity',
      severity: 'medium',
      suggestion:
        'Specify years of experience and specific skill requirements',
      explanation:
        'Clear experience requirements help candidates self-assess fit before applying',
      impact: 'Better qualified candidate pool',
      isFixed: false,
    });
    score -= 8;
  }

  // Apply grammar/clarity improvements
  optimized = optimized
    .replace(/we need/gi, 'We are seeking')
    .replace(/you should/gi, 'You will')
    .replace(/etc\./gi, 'and more');

  // Ensure score is between 0-100
  score = Math.max(0, Math.min(100, score));

  return { score, issues, optimized };
}

export async function POST(request: NextRequest): Promise<NextResponse> {
  try {
    const body: JDOptimizationRequest = await request.json();

    // Validate input
    if (!body.jobDescription || body.jobDescription.trim().length === 0) {
      return NextResponse.json(
        { error: 'Job description is required' } as JDOptimizationError,
        { status: 400 }
      );
    }

    if (body.jobDescription.length > 50000) {
      return NextResponse.json(
        { error: 'Job description exceeds maximum length (50,000 characters)' } as JDOptimizationError,
        { status: 400 }
      );
    }

    // Analyze job description
    const { score, issues, optimized } = analyzeJobDescription(
      body.jobDescription
    );

    // Build response
    const result: JDOptimizationResult = {
      qualityScore: score,
      optimizedJD: optimized,
      issues,
      summary: `Found ${issues.length} improvement opportunities. Quality score: ${score}/100`,
      improvements: issues.map((i) => i.title),
    };

    return NextResponse.json(result, { status: 200 });
  } catch (error) {
    console.error('JD Optimization Error:', error);

    const errorResponse: JDOptimizationError = {
      error: 'Internal server error',
      message:
        error instanceof Error
          ? error.message
          : 'An unexpected error occurred',
    };

    return NextResponse.json(errorResponse, { status: 500 });
  }
}

export async function OPTIONS(): Promise<NextResponse> {
  return NextResponse.json({ ok: true }, { status: 200 });
}
