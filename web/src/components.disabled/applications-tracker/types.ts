export namespace HorizontalPipeline {
  export type ApplicationStatus = 'applied' | 'screened' | 'interviewed' | 'offer' | 'closed' | 'rejected';

  export interface ScoreBreakdown {
    keyword?: number;
    semantic?: number;
    capability?: number;
  }

  export interface InterviewInfo {
    id: string;
    date: Date;
    type: 'phone' | 'technical' | 'onsite' | 'final';
    interviewer?: string;
    notes?: string;
    feedback?: string;
    score?: number;
  }

  export interface OfferDetails {
    id: string;
    salary?: number;
    salaryRange?: { min: number; max: number };
    benefits?: string[];
    startDate?: Date;
    notes?: string;
    expiresAt?: Date;
    accepted?: boolean;
  }

  export interface TimelineEvent {
    id: string;
    type: 'status_change' | 'interview' | 'feedback' | 'offer' | 'note' | 'call';
    timestamp: Date;
    title: string;
    description?: string;
    metadata?: Record<string, unknown>;
  }

  export interface Feedback {
    id: string;
    author: string;
    date: Date;
    text: string;
    rating?: number;
    category?: 'technical' | 'cultural' | 'communication' | 'experience';
  }

  export interface Application {
    id: string;
    positionId: string;
    candidateName: string;
    candidateEmail: string;
    positionTitle: string;
    location?: string;
    status: ApplicationStatus;
    appliedAt: Date;
    source?: string;
    scores: ScoreBreakdown;
    tags?: string[];
    isUrgent: boolean;
    lastInterviewDate?: Date;
    nextSteps?: string;
    resumeUrl?: string;
    linkedinUrl?: string;
    interviews: InterviewInfo[];
    offer?: OfferDetails;
    timeline: TimelineEvent[];
    feedback: Feedback[];
    internalNotes?: string;
  }

  export interface PipelineStats {
    total: number;
    applied: number;
    screened: number;
    interviewed: number;
    offer: number;
    closed: number;
    rejected: number;
    avgDaysInPipeline: number;
  }

  export interface InterviewPrepGuide {
    focusAreas: string[];
    keyQuestions: string[];
    commonChallenges: string[];
    prepTips: string[];
  }
}
