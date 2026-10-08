export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
export const ENVIRONMENT = process.env.NODE_ENV || 'development';
export const IS_PRODUCTION = ENVIRONMENT === 'production';

export const API_ENDPOINTS = {
  // Phase 1
  FORECASTING: {
    FORECAST_POSITION: '/api/v1/forecasting/pipeline',
    GET_FORECAST: '/api/v1/forecasting/pipeline/:id',
    BULK_FORECAST: '/api/v1/forecasting/pipeline/bulk',
    TRAIN_MODEL: '/api/v1/forecasting/model/train',
  },
  SALARY_BENCHMARKING: {
    GET_BENCHMARK: '/api/v1/salary-benchmarking/benchmark',
    GET_BENCHMARK_FOR_CANDIDATE: '/api/v1/salary-benchmarking/benchmark/candidate/:candidateId/:positionId',
    BULK_BENCHMARK: '/api/v1/salary-benchmarking/benchmark/bulk',
    UPDATE_DATA: '/api/v1/salary-benchmarking/data/update',
  },
  // Phase 2
  INTERVIEW_INTELLIGENCE: {
    GENERATE_PREP: '/api/v1/interview-intelligence/prep',
    SUBMIT_FEEDBACK: '/api/v1/interview-intelligence/feedback',
    FETCH_TRANSCRIPTION: '/api/v1/interview-intelligence/transcription/fetch',
  },
  RETENTION_PREDICTION: {
    ASSESS_RETENTION: '/api/v1/retention-prediction/assess',
    ASSESS_BULK_RETENTION: '/api/v1/retention-prediction/assess/bulk',
    GET_TRENDS: '/api/v1/retention-prediction/trends/:positionId',
    RECORD_INTERVENTION: '/api/v1/retention-prediction/record-intervention',
  },
};

export const CHART_COLORS = {
  primary: '#3b82f6',
  success: '#10b981',
  warning: '#f59e0b',
  error: '#ef4444',
  info: '#06b6d4',
};

export const THRESHOLDS = {
  FORECAST_CONFIDENCE_MIN: 0.6,
  RETENTION_RISK_LOW: 0.2,
  RETENTION_RISK_MEDIUM: 0.5,
  RETENTION_RISK_HIGH: 0.8,
  OFFER_ACCEPTANCE_TARGET: 0.75,
};

export const UI_CONFIG = {
  DEFAULT_PAGE_SIZE: 10,
  MAX_PAGE_SIZE: 100,
  CHART_HEIGHT: 300,
  CARD_HOVER_ENABLED: true,
  ANIMATIONS_ENABLED: true,
};
