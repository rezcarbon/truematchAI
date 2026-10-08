import { useState, useCallback } from 'react';
import { retentionPredictionApi, RetentionAssessmentRequest, RetentionPredictionResponse, BulkRetentionAssessmentRequest, BulkRetentionAssessmentResponse, InterventionRecordRequest, RetentionTrendsResponse } from '@/lib/api/retentionPredictionApi';

export function useRetentionPredictionApi() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const assessRetention = useCallback(
    async (request: RetentionAssessmentRequest): Promise<RetentionPredictionResponse | null> => {
      setLoading(true);
      setError(null);
      try {
        const result = await retentionPredictionApi.assessRetention(request);
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

  const assessBulkRetention = useCallback(
    async (request: BulkRetentionAssessmentRequest): Promise<BulkRetentionAssessmentResponse | null> => {
      setLoading(true);
      setError(null);
      try {
        const result = await retentionPredictionApi.assessBulkRetention(request);
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

  const getRetentionTrends = useCallback(
    async (positionId: string): Promise<RetentionTrendsResponse | null> => {
      setLoading(true);
      setError(null);
      try {
        const result = await retentionPredictionApi.getRetentionTrends(positionId);
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

  const recordIntervention = useCallback(
    async (request: InterventionRecordRequest): Promise<{ id: string; status: string } | null> => {
      setLoading(true);
      setError(null);
      try {
        const result = await retentionPredictionApi.recordIntervention(request);
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
    assessRetention,
    assessBulkRetention,
    getRetentionTrends,
    recordIntervention,
    loading,
    error,
  };
}
