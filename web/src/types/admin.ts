/**
 * TrueMatch Admin Dashboard Type Definitions
 * Comprehensive types for all admin operations and data
 */

// ==================== User Management ====================
export type UserRole = 'admin' | 'recruiter' | 'candidate';
export type UserStatus = 'active' | 'inactive' | 'invited' | 'suspended';

export interface User {
  id: string;
  email: string;
  displayName: string;
  role: UserRole;
  status: UserStatus;
  lastLogin?: string;
  createdAt: string;
  updatedAt: string;
  organization?: string;
}

export interface CreateUserRequest {
  email: string;
  displayName: string;
  role: UserRole;
  sendInvite: boolean;
}

export interface UpdateUserRequest {
  displayName?: string;
  role?: UserRole;
  status?: UserStatus;
}

export interface InviteUserRequest {
  emails: string[];
  role: UserRole;
  sendEmail: boolean;
}

// ==================== Audit & Logging ====================
export type AuditEventType =
  | 'assessment_created'
  | 'assessment_completed'
  | 'assessment_overridden'
  | 'governance_gate_triggered'
  | 'compliance_check_failed'
  | 'user_invited'
  | 'user_role_changed'
  | 'configuration_changed'
  | 'report_generated'
  | 'admin_action';

export interface AuditEvent {
  id: string;
  eventType: AuditEventType;
  actor: {
    id: string;
    email: string;
    role: UserRole;
  };
  resource?: {
    type: string;
    id: string;
  };
  details: Record<string, unknown>;
  timestamp: string;
  ipAddress?: string;
}

export interface AuditFilter {
  startDate?: string;
  endDate?: string;
  eventType?: AuditEventType;
  actorId?: string;
  resourceType?: string;
  search?: string;
  limit?: number;
  offset?: number;
}

export interface AuditQueryResponse {
  events: AuditEvent[];
  total: number;
  hasMore: boolean;
}

// ==================== Compliance ====================
export type ComplianceStatus = 'pass' | 'fail' | 'review' | 'pending';

export interface ComplianceItem {
  area: string;
  status: ComplianceStatus;
  detail: string;
  lastChecked?: string;
  action?: string;
}

export interface BiasMetric {
  group: string;
  selectionRate: number;
  sampleSize: number;
  fourFifthsRule?: boolean; // True if passes 80% rule
}

export interface ComplianceReportResponse {
  generatedAt: string;
  totalAssessments: number;
  governedAssessments: number;
  counterRecommendations: number;
  overrideCount: number;
  biasFlagsRaised: number;
  items: ComplianceItem[];
  biasMetrics: BiasMetric[];
  status: 'compliant' | 'at-risk' | 'non-compliant';
}

// ==================== Governance ====================
export interface GovernanceGate {
  name: string;
  status: 'enabled' | 'disabled';
  triggered: number;
  passed: number;
  failed: number;
}

export interface GovernanceConfigStatus {
  configuredGates: GovernanceGate[];
  isPlaceholder: boolean;
  source: string;
  lastUpdated?: string;
}

export interface GovernanceConfigPatch {
  namedKeyOverrides?: Record<string, unknown>;
}

// ==================== Analytics ====================
export interface PipelineMetric {
  month: string;
  assessmentsCreated: number;
  assessmentsCompleted: number;
  assessmentsPassed: number;
  conversionRate: number;
}

export interface SourceMetric {
  source: string;
  jobsIngested: number;
  assessmentsGenerated: number;
  applicationsReceived: number;
  hireRate: number;
}

export interface ThreeSignalMetric {
  delta: number;
  counterRecRate: number;
  overrideRate: number;
  accuracy: number;
}

export interface RecruiterPerformance {
  recruiterId: string;
  recruiterName: string;
  assessmentsReviewed: number;
  decisionsOverridden: number;
  averageDelta: number;
  hiringRate: number;
}

export interface AnalyticsResponse {
  generatedAt: string;
  period: string;
  pipeline: PipelineMetric[];
  sources: SourceMetric[];
  threeSignal: ThreeSignalMetric;
  topRecruiters: RecruiterPerformance[];
}

// ==================== System Health ====================
export type ServiceStatus = 'operational' | 'degraded' | 'down';

export interface ServiceHealth {
  name: string;
  status: ServiceStatus;
  lastCheck: string;
  responseTime?: number; // ms
  message?: string;
}

export interface SystemMetrics {
  timestamp: string;
  cpuUsage: number;
  memoryUsage: number;
  diskUsage: number;
  databaseConnections: number;
  queuedJobs: number;
  errorRate: number;
  requestsPerSecond: number;
}

export interface SystemHealthResponse {
  status: ServiceStatus;
  services: ServiceHealth[];
  metrics: SystemMetrics;
  uptime: number; // seconds
}

// ==================== Billing ====================
export type SubscriptionStatus = 'active' | 'canceled' | 'past_due' | 'expired';

export interface UsageMetric {
  date: string;
  assessmentsCreated: number;
  activeRecruiters: number;
  costEstimate: number;
}

export interface Subscription {
  id: string;
  organizationId: string;
  organizationName: string;
  status: SubscriptionStatus;
  plan: string;
  monthlyRate: number;
  usageThisMonth: UsageMetric[];
  totalThisMonth: number;
  estimatedNextMonth: number;
  billingCycleStart: string;
  billingCycleEnd: string;
  autoRenew: boolean;
}

export interface Invoice {
  id: string;
  organizationId: string;
  amount: number;
  period: string;
  status: 'paid' | 'unpaid' | 'overdue';
  issuedDate: string;
  dueDate: string;
  pdfUrl?: string;
}

// ==================== Email Templates ====================
export interface EmailTemplate {
  id: string;
  name: string;
  subject: string;
  body: string;
  variables: string[]; // e.g., ['name', 'email', 'assessment_link']
  category: 'invitation' | 'reminder' | 'result' | 'notification' | 'other';
  active: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface CreateEmailTemplateRequest {
  name: string;
  subject: string;
  body: string;
  category: string;
}

export interface UpdateEmailTemplateRequest {
  name?: string;
  subject?: string;
  body?: string;
  active?: boolean;
}

// ==================== Pagination ====================
export interface PaginationParams {
  page?: number;
  limit?: number;
  sort?: string;
  order?: 'asc' | 'desc';
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  limit: number;
  hasMore: boolean;
  pages: number;
}

// ==================== API Responses ====================
export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, unknown>;
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: ApiError;
  timestamp: string;
}
