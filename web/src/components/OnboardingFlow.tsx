'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

interface OnboardingStep {
  role: 'admin' | 'recruiter' | 'candidate';
  steps: {
    title: string;
    description: string;
    action?: string;
    tips?: string[];
  }[];
}

const ONBOARDING_FLOWS: Record<string, OnboardingStep['steps']> = {
  admin: [
    {
      title: 'Welcome to TrueMatch Admin',
      description:
        "You're now the platform steward. Your role is to ensure everything runs smoothly.",
      tips: [
        'Monitor system health and metrics in real-time',
        'Review and approve governance decisions',
        'Manage user access and roles',
      ],
    },
    {
      title: 'System Health Monitoring',
      description: 'Start by checking the current system status and metrics.',
      action: 'View System Health',
      tips: [
        'Look for pending reviews that need attention',
        'Check error rates and response times',
        'Review active user counts by role',
      ],
    },
    {
      title: 'Governance Management',
      description: 'Review and manage governance decisions made by the AI system.',
      action: 'View Governance Reviews',
      tips: [
        'Approve successful evaluations',
        'Escalate edge cases requiring human judgment',
        'Track approval trends over time',
      ],
    },
    {
      title: 'Ready to Lead',
      description: 'You now have full visibility into the TrueMatch platform.',
      tips: [
        'Check in regularly for metrics updates',
        'Act on governance reviews promptly',
        'Use analytics to drive improvements',
      ],
    },
  ],
  recruiter: [
    {
      title: 'Welcome to TrueMatch Recruiter Tools',
      description: 'Your AI-powered hiring partner is ready to help you find great talent.',
      tips: [
        'Upload candidate resumes and job descriptions',
        'Get instant insights on candidate fit',
        'Let the AI rank candidates for you',
      ],
    },
    {
      title: 'Upload Your First Candidates',
      description: 'Start by uploading resumes. The system will analyze them instantly.',
      action: 'Upload Resumes',
      tips: [
        'You can upload individual files or bulk lists',
        'The AI will extract skills and experience',
        'You can then rank candidates against your jobs',
      ],
    },
    {
      title: 'Test Job Description Quality',
      description:
        'Upload a job description to get insights on clarity, requirements, and talent fit.',
      action: 'Analyze Job Description',
      tips: [
        'Check if your requirements are realistic',
        'See estimated talent pool size',
        'Get wording suggestions for your posting',
      ],
    },
    {
      title: 'Rank Candidates',
      description: 'Have the AI rank your candidates against your open positions.',
      action: 'Start Ranking',
      tips: [
        'Understand why candidates are ranked that way',
        'Identify top candidates quickly',
        'Schedule interviews with top matches',
      ],
    },
    {
      title: 'Ready to Hire',
      description: 'You have all the tools needed to accelerate your hiring process.',
      tips: [
        'Keep uploading new candidates as they arrive',
        'Test new job descriptions before posting',
        'Use rankings to prioritize your pipeline',
      ],
    },
  ],
  candidate: [
    {
      title: 'Welcome to Your Career Coach',
      description: 'Your personal AI assistant is here to help advance your career.',
      tips: [
        'Upload your resume for analysis',
        'Find jobs that match your profile',
        'Get personalized improvement suggestions',
      ],
    },
    {
      title: 'Upload Your Resume',
      description: 'Start by uploading your resume. The system will analyze your profile.',
      action: 'Upload Resume',
      tips: [
        'Share your CV, LinkedIn PDF, or text',
        'The AI will extract your skills and experience',
        'You can then explore better career paths',
      ],
    },
    {
      title: 'Tell Us Your Career Goals',
      description: 'Share your target role or what you want to achieve next.',
      action: 'Set Career Goal',
      tips: [
        'Example: "Senior Backend Engineer at a fintech"',
        'Example: "Transition to product management"',
        'The AI will guide you toward your goal',
      ],
    },
    {
      title: 'Find Matching Jobs',
      description: 'Discover jobs that align with your profile and goals.',
      action: 'Find Matching Jobs',
      tips: [
        'See why each job is a good fit',
        'Identify any skill gaps for specific roles',
        'Get tips on how to close gaps',
      ],
    },
    {
      title: 'Improve Your CV',
      description: 'Get specific recommendations to strengthen your resume.',
      action: 'View CV Suggestions',
      tips: [
        'Learn how to better highlight your achievements',
        'Get examples of stronger phrasing',
        'See what successful candidates include',
      ],
    },
    {
      title: 'Ready to Advance',
      description: 'You have everything you need to accelerate your career journey.',
      tips: [
        'Update your profile as you gain new skills',
        'Check back for new matching opportunities',
        'Track your application progress',
      ],
    },
  ],
};

interface OnboardingFlowProps {
  userRole: 'admin' | 'recruiter' | 'candidate';
  onComplete: () => void;
}

/**
 * Onboarding Flow Component
 *
 * Guides new users through their first interaction with the system.
 * Shows role-specific workflows and quick tips.
 */
export function OnboardingFlow({ userRole, onComplete }: OnboardingFlowProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const steps = ONBOARDING_FLOWS[userRole];

  if (!steps) {
    return null;
  }

  const step = steps[currentStep];
  const isFirstStep = currentStep === 0;
  const isLastStep = currentStep === steps.length - 1;

  const handleNext = () => {
    if (isLastStep) {
      onComplete();
    } else {
      setCurrentStep(currentStep + 1);
    }
  };

  const handleSkip = () => {
    onComplete();
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <Card className="max-w-xl w-full mx-4">
        <CardHeader>
          <CardTitle>{step.title}</CardTitle>
          <CardDescription>
            Step {currentStep + 1} of {steps.length}
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-6">
          <p className="text-base">{step.description}</p>

          {step.tips && step.tips.length > 0 && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h4 className="font-semibold text-sm mb-2 text-blue-900">Quick Tips:</h4>
              <ul className="space-y-1">
                {step.tips.map((tip, i) => (
                  <li key={i} className="text-sm text-blue-800">
                    • {tip}
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="flex gap-3 justify-between pt-4">
            <Button variant="outline" onClick={handleSkip}>
              Skip Tutorial
            </Button>

            <div className="flex gap-2">
              {!isFirstStep && (
                <Button
                  variant="outline"
                  onClick={() => setCurrentStep(currentStep - 1)}
                >
                  Back
                </Button>
              )}

              {step.action && (
                <Button onClick={handleNext} className="gap-2">
                  {step.action} →
                </Button>
              )}

              {!step.action && (
                <Button onClick={handleNext}>
                  {isLastStep ? 'Get Started' : 'Continue'} →
                </Button>
              )}
            </div>
          </div>

          <div className="flex gap-1 justify-center pt-2">
            {steps.map((_, i) => (
              <div
                key={i}
                className={`h-2 w-2 rounded-full ${
                  i <= currentStep ? 'bg-blue-500' : 'bg-gray-300'
                }`}
              />
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
