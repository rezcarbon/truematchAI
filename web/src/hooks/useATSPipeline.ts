import { useState, useCallback, useEffect } from 'react';
import { useToast } from '@/components/providers/ToastProvider';

export interface CandidateInPipeline {
  id: string;
  resume_id: string;
  position_id: string;
  user_id: string;
  stage: string;
  stage_entered_at: string;
  source?: string;
  tags?: Record<string, any>;
  applied_at: string;
  created_at: string;
  updated_at: string;
}

export interface AssessmentScores {
  keywordScore?: number;
  semanticScore?: number;
  capabilityScore?: number;
}

interface UsePipelineResult {
  candidates: (CandidateInPipeline & AssessmentScores)[];
  loading: boolean;
  error: string | null;
  updateStage: (applicationId: string, newStage: string) => Promise<void>;
  refetch: () => Promise<void>;
}

/**
 * Hook to fetch and manage candidates in pipeline for a position
 * Combines application data with assessment scores
 */
export function useATSPipeline(positionId: string): UsePipelineResult {
  const { addToast } = useToast();
  const [candidates, setCandidates] = useState<(CandidateInPipeline & AssessmentScores)[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch assessment scores for a candidate
  const fetchAssessmentScores = async (resumeId: string, positionId: string): Promise<AssessmentScores> => {
    try {
      const response = await fetch(`/api/proxy/assessments?resume_id=${resumeId}&position_id=${positionId}`);
      if (!response.ok) return {};

      const data = await response.json();
      if (Array.isArray(data) && data[0]) {
        return {
          keywordScore: data[0].traditional_score,
          semanticScore: data[0].semantic_score,
          capabilityScore: data[0].capability_score,
        };
      }
      return {};
    } catch (err) {
      console.error('Failed to fetch assessment scores:', err);
      return {};
    }
  };

  // Fetch candidates for position
  const fetchCandidates = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`/api/proxy/ats/positions/${positionId}/pipeline`);
      if (!response.ok) {
        throw new Error('Failed to fetch pipeline');
      }

      const data: CandidateInPipeline[] = await response.json();

      // Fetch assessment scores for each candidate
      const enriched = await Promise.all(
        data.map(async (candidate) => {
          const scores = await fetchAssessmentScores(candidate.resume_id, positionId);
          return { ...candidate, ...scores };
        })
      );

      setCandidates(enriched);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load pipeline';
      setError(message);
      addToast(message, 'error');
    } finally {
      setLoading(false);
    }
  }, [positionId, addToast]);

  // Update candidate stage
  const updateStage = useCallback(
    async (applicationId: string, newStage: string) => {
      try {
        const response = await fetch(`/api/proxy/ats/applications/${applicationId}`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ stage: newStage }),
        });

        if (!response.ok) {
          throw new Error('Failed to update stage');
        }

        // Update local state optimistically
        setCandidates((prev) =>
          prev.map((c) =>
            c.id === applicationId
              ? {
                  ...c,
                  stage: newStage,
                  stage_entered_at: new Date().toISOString(),
                }
              : c
          )
        );

        addToast('Stage updated successfully', 'success');
        await fetchCandidates(); // Refetch to ensure consistency
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to update stage';
        addToast(message, 'error');
        throw err;
      }
    },
    [addToast, fetchCandidates]
  );

  useEffect(() => {
    if (positionId) {
      fetchCandidates();
    }
  }, [positionId, fetchCandidates]);

  return {
    candidates,
    loading,
    error,
    updateStage,
    refetch: fetchCandidates,
  };
}
