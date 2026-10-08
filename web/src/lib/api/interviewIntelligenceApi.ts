import { API_BASE_URL } from '@/config';

export interface TalkingPoint {
  topic: string;
  key_message: string;
  supporting_details: string;
  estimated_duration_minutes: number;
}

export interface InterviewQuestion {
  question: string;
  category: string;
  required_skill: string;
  difficulty: string;
  suggested_follow_ups: string[];
}

export interface InterviewPrepResponse {
  talking_points: TalkingPoint[];
  questions: InterviewQuestion[];
  estimated_duration_minutes: number;
}

export interface InterviewFeedback {
  candidate_id: string;
  interview_date: string;
  communication_score: number;
  technical_score: number;
  cultural_fit_score: number;
  overall_score: number;
  recommendation: string;
  strengths: string[];
  concerns: string[];
  notes: string;
  interview_duration_minutes: number;
}

export interface InterviewAnalysisResponse {
  interview_id: string;
  candidate_id: string;
  position_id: string;
  preparation_quality: number;
  communication_effectiveness: number;
  skills_alignment: number;
  cultural_fit_score: number;
  recommended_next_step: string;
  confidence: number;
  created_at: string;
}

export interface InterviewPrepRequest {
  candidate_id: string;
  position_id: string;
  candidate_name: string;
  candidate_background: string;
  position_title: string;
  key_requirements: string[];
}

export interface TranscriptionFetchRequest {
  recording_id: string;
  service: 'otter' | 'fireflies';
}

export class InterviewIntelligenceApiClient {
  private baseUrl = `${API_BASE_URL}/api/v1/interview-intelligence`;

  async generatePrepMaterials(request: InterviewPrepRequest): Promise<InterviewPrepResponse> {
    const response = await fetch(`${this.baseUrl}/prep`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });

    if (!response.ok) throw new Error(`Prep generation failed: ${response.statusText}`);
    return response.json();
  }

  async submitFeedback(feedback: InterviewFeedback): Promise<InterviewAnalysisResponse> {
    const response = await fetch(`${this.baseUrl}/feedback`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(feedback),
    });

    if (!response.ok) throw new Error(`Feedback submission failed: ${response.statusText}`);
    return response.json();
  }

  async fetchTranscription(request: TranscriptionFetchRequest): Promise<{ transcript: string; word_count: number }> {
    const response = await fetch(`${this.baseUrl}/transcription/fetch`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });

    if (!response.ok) throw new Error(`Transcription fetch failed: ${response.statusText}`);
    return response.json();
  }
}

export const interviewIntelligenceApi = new InterviewIntelligenceApiClient();
