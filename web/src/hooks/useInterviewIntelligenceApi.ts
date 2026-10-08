import { useState, useCallback } from 'react';
import { interviewIntelligenceApi, InterviewPrepRequest, InterviewPrepResponse, InterviewFeedback, InterviewAnalysisResponse, TranscriptionFetchRequest } from '@/lib/api/interviewIntelligenceApi';

export function useInterviewIntelligenceApi() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const generatePrepMaterials = useCallback(
    async (request: InterviewPrepRequest): Promise<InterviewPrepResponse | null> => {
      setLoading(true);
      setError(null);
      try {
        const result = await interviewIntelligenceApi.generatePrepMaterials(request);
        return result;
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Unknown error';
        setError(message);
        return null;
      } finally {
        setLoading(false);
      }
    },
    []
  );

  const submitFeedback = useCallback(
    async (feedback: InterviewFeedback): Promise<InterviewAnalysisResponse | null> => {
      setLoading(true);
      setError(null);
      try {
        const result = await interviewIntelligenceApi.submitFeedback(feedback);
        return result;
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Unknown error';
        setError(message);
        return null;
      } finally {
        setLoading(false);
      }
    },
    []
  );

  const fetchTranscription = useCallback(
    async (request: TranscriptionFetchRequest): Promise<{ transcript: string; word_count: number } | null> => {
      setLoading(true);
      setError(null);
      try {
        const result = await interviewIntelligenceApi.fetchTranscription(request);
        return result;
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Unknown error';
        setError(message);
        return null;
      } finally {
        setLoading(false);
      }
    },
    []
  );

  return {
    generatePrepMaterials,
    submitFeedback,
    fetchTranscription,
    loading,
    error,
  };
}
