import { useState, useCallback } from 'react';
import { useToast } from '@/components/providers/ToastProvider';

export interface InterviewData {
  id: string;
  application_id: string;
  position_id: string;
  scheduled_at?: string;
  interviewer_ids: string[];
  candidate_email?: string;
  meeting_link?: string;
  meeting_platform?: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface ScorecardData {
  id: string;
  interview_id: string;
  interviewer_id: string;
  position_id: string;
  competency_scores: Record<string, number>;
  feedback?: string;
  overall_recommendation?: string;
  submitted_at?: string;
  created_at: string;
  updated_at: string;
}

/**
 * Hook for scheduling interviews
 */
export function useScheduleInterview() {
  const { addToast } = useToast();
  const [loading, setLoading] = useState(false);

  const scheduleInterview = useCallback(
    async (
      applicationId: string,
      positionId: string,
      interviewerIds: string[],
      meetingPlatform: string,
      scheduledAt?: Date
    ): Promise<InterviewData> => {
      try {
        setLoading(true);

        const response = await fetch('/api/proxy/ats/interviews', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            application_id: applicationId,
            position_id: positionId,
            interviewer_ids: interviewerIds,
            meeting_platform: meetingPlatform,
            scheduled_at: scheduledAt?.toISOString(),
          }),
        });

        if (!response.ok) {
          throw new Error('Failed to schedule interview');
        }

        const data = await response.json();
        addToast('Interview scheduled successfully! 🎉', 'success');
        return data;
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to schedule interview';
        addToast(message, 'error');
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [addToast]
  );

  return { scheduleInterview, loading };
}

/**
 * Hook for fetching interviews for an application
 */
export function useApplicationInterviews(applicationId?: string) {
  const { addToast } = useToast();
  const [interviews, setInterviews] = useState<InterviewData[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchInterviews = useCallback(async () => {
    if (!applicationId) return;

    try {
      setLoading(true);

      const response = await fetch(`/api/proxy/ats/applications/${applicationId}/interviews`);
      if (!response.ok) {
        throw new Error('Failed to fetch interviews');
      }

      const data = await response.json();
      setInterviews(data.items || []);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load interviews';
      addToast(message, 'error');
    } finally {
      setLoading(false);
    }
  }, [applicationId, addToast]);

  return { interviews, loading, fetchInterviews };
}

/**
 * Hook for submitting scorecards
 */
export function useSubmitScorecard() {
  const { addToast } = useToast();
  const [loading, setLoading] = useState(false);

  const submitScorecard = useCallback(
    async (
      interviewId: string,
      competencyScores: Record<string, number>,
      feedback?: string,
      overallRecommendation?: string
    ): Promise<ScorecardData> => {
      try {
        setLoading(true);

        const response = await fetch('/api/proxy/ats/scorecards', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            interview_id: interviewId,
            competency_scores: competencyScores,
            feedback,
            overall_recommendation: overallRecommendation,
          }),
        });

        if (!response.ok) {
          throw new Error('Failed to submit scorecard');
        }

        const data = await response.json();
        addToast('Scorecard submitted successfully! ✅', 'success');
        return data;
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to submit scorecard';
        addToast(message, 'error');
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [addToast]
  );

  return { submitScorecard, loading };
}
