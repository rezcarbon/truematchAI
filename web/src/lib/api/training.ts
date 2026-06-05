/**
 * Training Simulation System API Client
 * Interfaces with the backend training endpoints
 */

export interface TrainingFeedback {
  id: string;
  user_id: string;
  feedback_type: 'hire' | 'reject' | 'maybe' | 'interested' | 'not_interested' | 'applied';
  rating?: number;
  comments?: string;
  time_to_action_seconds?: number;
  outcome?: string;
  created_at: string;
  updated_at: string;
}

export interface CapabilityMapping {
  id: string;
  cv_keyword: string;
  capability: string;
  confidence_score: number;
  frequency: number;
  positive_feedback: number;
  negative_feedback: number;
  job_category?: string;
  industry?: string;
  is_user_added: boolean;
  learned_from_feedback: boolean;
  created_at: string;
  updated_at: string;
}

export interface SuccessPattern {
  id: string;
  job_id?: string;
  job_category?: string;
  successful_candidate_profile: Record<string, unknown>;
  key_capabilities: string[];
  key_credentials: string[];
  success_rate: number;
  average_tenure_months?: number;
  sample_size: number;
  industry?: string;
  region?: string;
  confidence_level: number;
  is_valid: boolean;
  created_at: string;
  updated_at: string;
}

export interface TrainingProgress {
  id: string;
  metric_name: string;
  current_value: number;
  baseline_value: number;
  improvement_percent: number;
  sample_count: number;
  period: string;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface TrainingInsight {
  id: string;
  insight_type: string;
  insight_category?: string;
  title: string;
  description: string;
  metric_value?: number;
  sample_size: number;
  confidence: number;
  supporting_data: Record<string, unknown>;
  industry?: string;
  region?: string;
  is_public: boolean;
  is_trending: boolean;
  created_at: string;
  updated_at: string;
}

export interface TrainingStats {
  total_feedback: number;
  feedback_by_type: Record<string, number>;
  capability_mappings_learned: number;
  credential_mappings_learned: number;
  success_patterns_discovered: number;
  current_model: {
    version: number;
    match_accuracy: number;
    hire_success_accuracy: number;
    total_patterns: number;
  };
}

export interface VirtualBrainState {
  version: number;
  is_active: boolean;
  total_feedback_samples: number;
  total_patterns_learned: number;
  match_accuracy: number;
  hire_success_prediction_accuracy: number;
  performance_metrics: Record<string, unknown>;
  training_started_at?: string;
  training_completed_at?: string;
  created_at: string;
  updated_at: string;
}

export async function getTrainingStats(token: string): Promise<TrainingStats> {
  const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/training/stats`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) throw new Error('Failed to fetch training stats');
  return response.json();
}

export async function getTrainingFeedback(
  token: string,
  feedbackType?: string,
  limit = 50
): Promise<{ items: TrainingFeedback[]; total: number }> {
  const params = new URLSearchParams();
  if (feedbackType) params.append('feedback_type', feedbackType);
  params.append('limit', limit.toString());

  const response = await fetch(
    `${process.env.NEXT_PUBLIC_API_URL}/api/v1/training/feedback?${params}`,
    {
      headers: { Authorization: `Bearer ${token}` },
    }
  );
  if (!response.ok) throw new Error('Failed to fetch training feedback');
  return response.json();
}

export async function submitTrainingFeedback(
  token: string,
  feedback: Partial<TrainingFeedback>
): Promise<TrainingFeedback> {
  const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/training/feedback`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(feedback),
  });
  if (!response.ok) throw new Error('Failed to submit training feedback');
  return response.json();
}

export async function getCapabilityMappings(
  token: string,
  limit = 50
): Promise<CapabilityMapping[]> {
  const response = await fetch(
    `${process.env.NEXT_PUBLIC_API_URL}/api/v1/training/capabilities?limit=${limit}`,
    {
      headers: { Authorization: `Bearer ${token}` },
    }
  );
  if (!response.ok) throw new Error('Failed to fetch capability mappings');
  return response.json();
}

export async function getSuccessPatterns(token: string): Promise<SuccessPattern[]> {
  const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/training/success-patterns`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) throw new Error('Failed to fetch success patterns');
  return response.json();
}

export async function getTrainingProgress(token: string): Promise<TrainingProgress[]> {
  const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/training/progress`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) throw new Error('Failed to fetch training progress');
  return response.json();
}

export async function getTrainingInsights(token: string): Promise<TrainingInsight[]> {
  const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/training/insights`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) throw new Error('Failed to fetch training insights');
  return response.json();
}

export async function getVirtualBrainState(token: string): Promise<VirtualBrainState> {
  const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/training/brain/state`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) throw new Error('Failed to fetch virtual brain state');
  return response.json();
}
