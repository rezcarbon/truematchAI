import { API_BASE_URL } from '@/config';

export interface AttritionRiskResponse {
  hire_id: string;
  candidate_id: string;
  risk_score: number;
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  detected_signals: string[];
  primary_risk_factor: string;
  days_to_potential_attrition: number;
  confidence: number;
}

export interface InterventionResponse {
  intervention_type: string;
  priority: string;
  description: string;
  action_steps: string[];
  expected_impact: string;
  success_indicators: string[];
}

export interface RetentionPredictionResponse {
  hire_id: string;
  candidate_id: string;
  attrition_risk: AttritionRiskResponse;
  recommended_interventions: InterventionResponse[];
  strengths: string[];
  challenges: string[];
  assessment_period: string;
}

export interface RetentionAssessmentRequest {
  hire_id: string;
  candidate_id: string;
  hire_date: string;
  position_id: string;
  performance_rating: number;
  previous_performance_rating?: number;
  engagement_score: number;
  role_satisfaction_score: number;
  compensation_satisfaction: number;
  team_dynamics_score: number;
  team_size?: number;
  manager_tenure_months?: number;
  is_first_month?: boolean;
}

export interface BulkRetentionAssessmentRequest {
  assessments: RetentionAssessmentRequest[];
}

export interface BulkRetentionAssessmentResponse {
  predictions: RetentionPredictionResponse[];
  high_risk_count: number;
  critical_count: number;
  average_risk_score: number;
}

export interface RetentionTrendsResponse {
  position_id: string;
  average_tenure_months: number;
  attrition_rate: number;
  most_common_signals: string[];
  intervention_effectiveness: Record<string, number>;
}

export interface InterventionRecordRequest {
  hire_id: string;
  intervention_type: string;
  completed_by: string;
  outcome: string;
  notes?: string;
}

export class RetentionPredictionApiClient {
  private baseUrl = `${API_BASE_URL}/api/v1/retention-prediction`;

  async assessRetention(request: RetentionAssessmentRequest): Promise<RetentionPredictionResponse> {
    const response = await fetch(`${this.baseUrl}/assess`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });

    if (!response.ok) throw new Error(`Assessment failed: ${response.statusText}`);
    return response.json();
  }

  async assessBulkRetention(request: BulkRetentionAssessmentRequest): Promise<BulkRetentionAssessmentResponse> {
    const response = await fetch(`${this.baseUrl}/assess/bulk`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });

    if (!response.ok) throw new Error(`Bulk assessment failed: ${response.statusText}`);
    return response.json();
  }

  async getRetentionTrends(positionId: string): Promise<RetentionTrendsResponse> {
    const response = await fetch(`${this.baseUrl}/trends/${positionId}`);
    if (!response.ok) throw new Error(`Trends fetch failed: ${response.statusText}`);
    return response.json();
  }

  async recordIntervention(request: InterventionRecordRequest): Promise<{ id: string; status: string }> {
    const response = await fetch(`${this.baseUrl}/record-intervention`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });

    if (!response.ok) throw new Error(`Intervention recording failed: ${response.statusText}`);
    return response.json();
  }
}

export const retentionPredictionApi = new RetentionPredictionApiClient();
