import { forecastingApi, ForecastRequest, ForecastResponse } from '@/lib/api/forecastingApi';

describe('ForecastingApiClient', () => {
  beforeEach(() => {
    global.fetch = jest.fn();
  });

  afterEach(() => {
    jest.resetAllMocks();
  });

  describe('forecast', () => {
    it('makes POST request to forecast endpoint', async () => {
      const mockResponse: ForecastResponse = {
        position_id: 'pos-1',
        position_title: 'Senior Engineer',
        forecasted_fill_date: '2026-11-15',
        estimated_days_to_fill: 30,
        confidence: 0.85,
        bottleneck_stage: 'interview',
        recommendations: ['Increase slots'],
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const request: ForecastRequest = { position_id: 'pos-1' };
      const result = await forecastingApi.forecast(request);

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/pipeline'),
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
        })
      );
      expect(result).toEqual(mockResponse);
    });

    it('handles API errors', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        statusText: 'Internal Server Error',
      });

      const request: ForecastRequest = { position_id: 'pos-1' };
      await expect(forecastingApi.forecast(request)).rejects.toThrow();
    });
  });

  describe('bulkForecast', () => {
    it('makes POST request for multiple positions', async () => {
      const mockResponse = {
        forecasts: [],
        average_days_to_fill: 30,
        critical_bottlenecks: [],
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await forecastingApi.bulkForecast({
        position_ids: ['pos-1', 'pos-2'],
      });

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/bulk'),
        expect.objectContaining({ method: 'POST' })
      );
      expect(result).toEqual(mockResponse);
    });
  });

  describe('trainModel', () => {
    it('initiates model training', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ status: 'success', accuracy: 0.92 }),
      });

      const result = await forecastingApi.trainModel();

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/model/train'),
        expect.objectContaining({ method: 'POST' })
      );
      expect(result.accuracy).toBeGreaterThan(0.8);
    });
  });
});
