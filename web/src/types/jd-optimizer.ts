export interface OptimizationIssue {
  id: string;
  title: string;
  description: string;
  category: 'clarity' | 'tone' | 'completeness' | 'structure' | 'engagement' | string;
  severity: 'high' | 'medium' | 'low';
  problematicText?: string;
  suggestion?: string;
  explanation?: string;
  impact?: string;
  isFixed?: boolean;
}

export interface JDOptimizationResult {
  qualityScore: number;
  optimizedJD: string;
  issues?: OptimizationIssue[];
  summary?: string;
  improvements?: string[];
}

export interface JDOptimizationRequest {
  jobDescription: string;
}

export interface JDOptimizationError {
  error: string;
  message?: string;
}
