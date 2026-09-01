/**
 * Comprehensive TypeScript type definitions for TrueMatch frontend
 * These types define all domain objects, API contracts, and UI component shapes
 */

import type { PipelineCandidate } from "@/lib/types";

// ============================================================================
// Session & Authentication Types
// ============================================================================

export interface Session {
  user?: {
    id: string;
    name?: string | null;
    email?: string | null;
    image?: string | null;
  };
  expires?: string;
  accessToken?: string;
}

// ============================================================================
// WebSocket & Real-time Types
// ============================================================================

export interface WebSocketMessage<T = Record<string, unknown>> {
  type: string;
  timestamp?: string;
  data?: T;
  [key: string]: unknown;
}

export type WebSocketMessageHandler = (message: WebSocketMessage) => void;

export interface PipelineUpdateEvent extends WebSocketMessage {
  type: 'pipeline_update';
  data: {
    candidateId: string;
    newStage: string;
    timestamp: string;
  };
}

export interface InterviewNotificationEvent extends WebSocketMessage {
  type: 'interview_notification';
  data: {
    interviewId: string;
    candidateId: string;
    positionId: string;
    scheduledAt: string;
  };
}

export interface PresenceEvent extends WebSocketMessage {
  type: 'presence';
  data: {
    userId: string;
    positionId: string;
    action: 'joined' | 'left';
  };
}

// ============================================================================
// Scraper & Data Ingestion Types
// ============================================================================

export interface ScraperConfig {
  id?: string;
  name: string;
  url: string;
  selector?: string;
  [key: string]: unknown;
}

export interface ScraperRun {
  id: string;
  config_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  created_at: string;
  updated_at?: string;
}

export interface FieldMapping {
  source: string;
  target: string;
  type: string;
}

export interface UploadBatch {
  id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  created_at: string;
  updated_at?: string;
  error_count?: number;
  success_count?: number;
}

export interface UploadError {
  row: number;
  field: string;
  error: string;
}

// ============================================================================
// CV Analysis Types
// ============================================================================

export interface CVAnalysisResponse {
  id: string;
  fileName: string;
  extractedText: string;
  skills: string[];
  experience_years: number;
  summary: string;
}

// ============================================================================
// JD Simulation Types
// ============================================================================

export interface JDSimulationResponse {
  id: string;
  jd_text: string;
  extracted_requirements: string[];
  quality_score: number;
  suggestions: string[];
}

// ============================================================================
// Bulk Action Types
// ============================================================================

export interface BulkActionPayload {
  action: string;
  items: string[];
  metadata?: Record<string, unknown>;
}

export interface BulkActionResponse {
  success: number;
  failed: number;
  results: Array<{
    itemId: string;
    success: boolean;
    error?: string;
  }>;
}

// ============================================================================
// Training Session Types
// ============================================================================

export interface TrainingSession {
  id: string;
  userId: string;
  topic: string;
  status: 'active' | 'completed' | 'paused';
  progress: number;
  messages: TrainingMessage[];
  createdAt: string;
  updatedAt: string;
}

export interface TrainingMessage {
  id: string;
  sessionId: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  learning_impact?: number;
}

export interface UploadResult {
  id: string;
  fileName: string;
  uploaded_mappings: Array<{
    field: string;
    value: string;
  }>;
  updated_mappings: Array<{
    field: string;
    oldValue: string;
    newValue: string;
  }>;
  createdAt: string;
}

// ============================================================================
// Analytics & Metrics Types
// ============================================================================

export interface DEIMetrics {
  totalCandidates: number;
  hiresByDemographic: Record<string, number>;
  assessmentRateByDemographic: Record<string, number>;
  advancementRateByDemographic: Record<string, number>;
  equity_gaps: Array<{
    demographic: string;
    gap_percentage: number;
    affected_count: number;
  }>;
}

export interface RecruiterMetrics {
  id: string;
  name: string;
  assessments_completed: number;
  decisions_made: number;
  override_rate: number;
  bias_signals: number;
  avg_assessment_time: number;
}

export interface ChartDataPoint {
  label: string;
  value: number;
  percentage?: number;
}

// ============================================================================
// Comparison Types
// ============================================================================

export interface ComparisonCandidate {
  id: string;
  name: string;
  assessment: {
    traditionalScore: number;
    semanticScore?: number;
    capabilityScore: number;
    delta: number;
    matchType?: 'hidden_gem' | 'surfaced_strong_match' | 'keyword_aligned';
  };
}

// ============================================================================
// API Client Types
// ============================================================================

export interface ApiClientOptions {
  baseUrl?: string;
  timeout?: number;
  retryAttempts?: number;
}

export interface ApiResponse<T> {
  data: T;
  error: null;
  status: 'success';
}

export interface ApiErrorResponse {
  type: string;
  title: string;
  detail: string;
  status: number;
  requestId?: string;
  errors?: Array<{
    field: string;
    message: string;
    type: string;
  }>;
}

// ============================================================================
// Form & UI Types
// ============================================================================

export interface FormState {
  isSubmitting: boolean;
  error: string | null;
  success: boolean;
}

export interface SortState {
  column: string;
  direction: 'asc' | 'desc';
}

export interface FilterState {
  [key: string]: unknown;
}

export interface PaginationState {
  page: number;
  pageSize: number;
  total: number;
  hasMore: boolean;
}

export interface ModalState {
  open: boolean;
  title?: string;
  description?: string;
}

// ============================================================================
// Hook Return Types
// ============================================================================

export interface UsePipelineWebSocketReturn {
  send: (message: WebSocketMessage) => void;
  isConnected: boolean;
}

export interface UseNotificationWebSocketReturn {
  isConnected: boolean;
}

export interface UseAgentOperatorReturn {
  connected: boolean;
  reconnecting: boolean;
  lastEvent: WebSocketMessage | null;
  subscribe: (eventType: string, callback: WebSocketMessageHandler) => void;
  unsubscribe: (eventType: string, callback: WebSocketMessageHandler) => void;
  disconnect: () => void;
}

export interface UseATSPipelineReturn {
  pipeline: PipelineCandidate[];
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

export interface UseProfileCompletionReturn {
  isComplete: boolean;
  missingFields: string[];
  percentComplete: number;
}

// ============================================================================
// Re-export domain types from ../lib/types.ts
// (These are the core Assessment, Position, etc. types)
// ============================================================================

export type {
  Assessment,
  PipelineCandidate,
  Position,
  DecisionRecord,
  AuditEntry,
  UserRecord,
  JDQuality,
  JDQualityFlag,
  CapabilityScore,
  GovernanceSignal,
  BiasFlag,
  Governance,
  TrajectoryPoint,
  GapItem,
  CounterRecommendation,
  Substitution,
  CapabilityComponent,
  GovernanceStatus,
} from '../lib/types';
