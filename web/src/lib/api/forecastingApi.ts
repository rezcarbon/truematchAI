import { API_BASE_URL } from '@/config';

export interface ForecastRequest {
  position_id: string;
}

export interface BulkForecastRequest {
  position_ids: string[];
}

export interface ForecastResponse {
  position_id: string;
  position_title: string;
  forecasted_fill_date: string;
  estimated_days_to_fill: number;
  confidence: number;
  bottleneck_stage: string;
  recommendations: string[];
}

export interface BulkForecastResponse {
  forecasts: ForecastResponse[];
  average_days_to_fill: number;
  critical_bottlenecks: string[];
}

export class ForecastingApiClient {
  private baseUrl = `${API_BASE_URL}/api/v1/forecasting`;

  async forecast(request: ForecastRequest): Promise<ForecastResponse> {
    const response = await fetch(`${this.baseUrl}/pipeline`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });

    if (!response.ok) throw new Error(`Forecast failed: ${response.statusText}`);
    return response.json();
  }

  async getForecast(positionId: string): Promise<ForecastResponse> {
    const response = await fetch(`${this.baseUrl}/pipeline/${positionId}`);
    if (!response.ok) throw new Error(`Get forecast failed: ${response.statusText}`);
    return response.json();
  }

  async bulkForecast(request: BulkForecastRequest): Promise<BulkForecastResponse> {
    const response = await fetch(`${this.baseUrl}/pipeline/bulk`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });

    if (!response.ok) throw new Error(`Bulk forecast failed: ${response.statusText}`);
    return response.json();
  }

  async trainModel(data?: { min_samples?: number }): Promise<{ status: string; accuracy: number }> {
    const response = await fetch(`${this.baseUrl}/model/train`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data || {}),
    });

    if (!response.ok) throw new Error(`Model training failed: ${response.statusText}`);
    return response.json();
  }
}

export const forecastingApi = new ForecastingApiClient();
