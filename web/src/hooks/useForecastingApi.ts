import { useState, useCallback } from 'react';
import { forecastingApi, ForecastResponse, BulkForecastResponse, ForecastRequest } from '@/lib/api/forecastingApi';

export function useForecastingApi() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const forecast = useCallback(async (request: ForecastRequest): Promise<ForecastResponse | null> => {
    setLoading(true);
    setError(null);
    try {
      const result = await forecastingApi.forecast(request);
      return result;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      setError(message);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const getForecast = useCallback(async (positionId: string): Promise<ForecastResponse | null> => {
    setLoading(true);
    setError(null);
    try {
      const result = await forecastingApi.getForecast(positionId);
      return result;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      setError(message);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const bulkForecast = useCallback(async (positionIds: string[]): Promise<BulkForecastResponse | null> => {
    setLoading(true);
    setError(null);
    try {
      const result = await forecastingApi.bulkForecast({ position_ids: positionIds });
      return result;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      setError(message);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const trainModel = useCallback(async (): Promise<{ status: string; accuracy: number } | null> => {
    setLoading(true);
    setError(null);
    try {
      const result = await forecastingApi.trainModel();
      return result;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      setError(message);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    forecast,
    getForecast,
    bulkForecast,
    trainModel,
    loading,
    error,
  };
}
