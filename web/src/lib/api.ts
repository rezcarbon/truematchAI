// Thin client-side API helper. The browser ONLY ever calls the BFF proxy
// (/api/proxy/...), never the backend directly. The proxy injects the logged-in
// user's token server-side.
//
// Reads fall back to clearly-typed mock data when the backend is unreachable so
// pages render standalone during development. Writes never fall back — a failed
// mutation throws so the UI can surface it.

import type {
  Assessment,
  PipelineCandidate,
  Position,
  DecisionRecord,
  AuditEntry,
  UserRecord,
  JDQuality,
  JDQualityFlag,
} from "./types";
import type {
  ScraperConfig,
  ScraperRun,
  FieldMapping,
  UploadBatch,
  CVAnalysisResponse,
  JDSimulationResponse,
} from "@/types";
import {
  mockAssessment,
  mockPipeline,
  mockPositions,
  mockDecisions,
  mockAudit,
  mockUsers,
} from "./mock";

const BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "/api/proxy";

async function get<T>(path: string, fallback: T): Promise<T> {
  try {
    const res = await fetch(`${BASE}${path}`, {
      headers: { Accept: "application/json" },
      cache: "no-store",
    });
    if (!res.ok) return fallback;
    return (await res.json()) as T;
  } catch {
    return fallback;
  }
}

async function send<T>(path: string, method: string, body?: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers: body === undefined ? undefined : { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try {
      const j = await res.json();
      if (j?.detail) detail = typeof j.detail === "string" ? j.detail : detail;
    } catch {
      /* non-JSON error body */
    }
    throw new Error(detail);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export interface UploadedResume {
  resume_id: string;
  file_id: string;
  file_type: string;
}

export interface TranslationBullet {
  text: string;
  grounding: string;
  evidenceStrength: string; // HIGH | MEDIUM | WEAK
}

export interface CourseRecommendation {
  capability: string;
  title: string;
  provider: string;
  url?: string | null;
  format?: string | null;
  durationWeeks?: number | null;
  level?: string | null;
  relevance?: string;
}

export interface UpskillingItem {
  capability: string;
  why?: string;
  how?: string;
  recommendedTraining?: CourseRecommendation[];
}

export interface TransitionTimeline {
  monthsMin: number;
  monthsMax: number;
  confidence: string; // low | medium | high
  basis?: string;
}

export interface TransitionOption {
  role: string;
  direction: string; // lateral | upward | adjacent
  feasibility: string; // READY | STRETCH | ASPIRATIONAL
  rationale: string;
  transferableStrengths?: string[];
  upskillingGap?: UpskillingItem[];
  timeline?: TransitionTimeline | null;
  evidenceStrength: string; // HIGH | MEDIUM | WEAK
}

export interface TrajectoryPoint {
  analysisId: string;
  date?: string | null;
  capabilityScore?: number | null;
  options: number;
  ready: number;
  stretch: number;
  aspirational: number;
  topRole?: string | null;
}

export interface TransitionMetrics {
  analysesTotal: number;
  analysesCompleted: number;
  tracked: number;
  candidates: number;
  readiness: Record<string, number>;
  outcomes: Record<string, number>;
  resolvedOutcomes: number;
  achievementRate?: number | null;
}

export interface TransitionResult {
  analysisId: string;
  status: "pending" | "analyzing" | "completed" | "failed";
  currentRole?: string | null;
  sourceLanguage?: string | null;
  capabilityScore?: number | null;
  readinessSummary?: string | null;
  transitionOptions: TransitionOption[];
  honestyNotes?: string | null;
  droppedUngrounded: number;
  error?: string | null;
}

export interface CapabilityTranslationResult {
  translationId: string;
  status: "pending" | "translating" | "completed" | "failed";
  targetRole?: string | null;
  /** ISO code of the CV's original language when non-English (an English pivot
   * was rewritten); null/"en" for English. originalText keeps the original CV. */
  sourceLanguage?: string | null;
  originalText?: string | null;
  summary?: string | null;
  bullets: TranslationBullet[];
  skills: string[];
  translationNotes?: string | null;
  droppedUngrounded: number;
  beforeKeywordScore?: number | null;
  afterKeywordScore?: number | null;
  beforeSemanticScore?: number | null;
  afterSemanticScore?: number | null;
  keywordLift?: number | null;
  semanticLift?: number | null;
  capabilityScore?: number | null;
  capabilityDelta?: number | null;
  matchedKeywordsAfter: string[];
  stillMissingKeywords: string[];
  error?: string | null;
}

// Ingest queue item returned by the agent control API.
export interface IngestQueueItem {
  id: string;
  source: string;
  ingest_type: string;
  status: string;
  resume_id: string | null;
  assessment_id: string | null;
  position_id: string | null;
  retry_count: number;
  created_at: string;
  last_error?: string | null;
  jd_agent_output?: Record<string, unknown> | null;
  review_notes?: string | null;
}

export interface DecisionPayload {
  assessment_id: string;
  position_id: string;
  decision: "advance" | "reject" | "hold" | "interview" | "hire";
  ai_recommendation_followed?: boolean;
  override_reasoning?: string | null;
  cultural_fit_notes?: string | null;
  interview_notes?: string | null;
}

// Maps the backend JD-interrogation shape ({issues:[{type,severity,detail,
// recommendation}]}) into the UI's JDQuality shape, preserving the per-issue
// recommendation (the actionable fix) and severity.
interface BackendJDIssue {
  type: string;
  severity?: string;
  detail?: string;
  recommendation?: string;
}

const JD_TYPE_MAP: Record<string, JDQualityFlag["type"]> = {
  proxy: "proxy",
  proxy_requirement: "proxy",
  impossible: "impossible",
  impossible_requirement: "impossible",
  contradiction: "impossible",
  purple_squirrel: "impossible",
  exclusionary: "exclusionary",
  biased: "exclusionary",
  vague_requirement: "ambiguous",
  inflated_seniority: "ambiguous",
  ambiguous: "ambiguous",
};

function mapJDQuality(score: number | null, issues: BackendJDIssue[]): JDQuality {
  return {
    score: score ?? 0,
    flags: issues.map((it, i) => ({
      id: `jd-${i}`,
      type: JD_TYPE_MAP[it.type] ?? "ambiguous",
      field: (it.type ?? "issue").replace(/_/g, " "),
      message: it.detail ?? "",
      recommendation: it.recommendation,
      severity: it.severity,
    })),
  };
}

export const api = {
  // --- reads (mock fallback) ---
  getAssessment: async (id: string): Promise<Assessment> => {
    const a = await get<Assessment>(`/assessments/${id}`, { ...mockAssessment, id });
    // The backend sends source languages snake_cased; surface them as camelCase
    // for the translation badge regardless of the rest of the mapping state.
    const raw = a as unknown as Record<string, unknown>;
    return {
      ...a,
      sourceLanguage: a.sourceLanguage ?? (raw.source_language as string | undefined),
      jdSourceLanguage: a.jdSourceLanguage ?? (raw.jd_source_language as string | undefined),
    };
  },
  // Live JD quality for a position (score + interrogation issues + fixes).
  getPositionJD: async (id: string): Promise<JDQuality> => {
    try {
      const res = await fetch(`${BASE}/positions/${id}`, {
        headers: { Accept: "application/json" },
        cache: "no-store",
      });
      if (!res.ok) return mockAssessment.jdQuality;
      const p = (await res.json()) as {
        jd_quality_score?: number | null;
        jd_issues?: { issues?: BackendJDIssue[] } | null;
      };
      return mapJDQuality(p.jd_quality_score ?? null, p.jd_issues?.issues ?? []);
    } catch {
      return mockAssessment.jdQuality;
    }
  },
  getPipeline: (positionId?: string) =>
    get<PipelineCandidate[]>(`/positions/${positionId ?? "all"}/pipeline`, mockPipeline),
  getPositions: () => get<Position[]>(`/positions`, mockPositions),
  getDecisions: () => get<DecisionRecord[]>(`/decisions`, mockDecisions),
  getAudit: async (): Promise<AuditEntry[]> => {
    // Real audit trail (admin). Maps the backend AuditTrail rows to the UI shape.
    const resp = await get<{ items: Array<Record<string, unknown>> }>(`/admin/audit`, { items: [] });
    if (!resp.items?.length) return mockAudit;
    return resp.items.map((r) => ({
      id: String(r.id),
      actor: String(r.actor_type ?? "system"),
      action: String(r.event_type ?? ""),
      target: String(r.assessment_id ?? ""),
      timestamp: String(r.created_at ?? ""),
      ip: "—",
    })) as AuditEntry[];
  },
  getUsers: async (): Promise<UserRecord[]> => {
    // Real users list (admin) — previously called a non-existent /users path
    // and always rendered mock data.
    const resp = await get<{ items: Array<Record<string, unknown>> }>(`/admin/users`, { items: [] });
    if (!resp.items?.length) return mockUsers;
    return resp.items.map((u) => ({
      id: String(u.id),
      name: String(u.display_name ?? u.email ?? ""),
      email: String(u.email ?? ""),
      role: (u.role as UserRecord["role"]) ?? "candidate",
      status: "active",
      lastActive: String(u.created_at ?? ""),
    })) as UserRecord[];
  },

  // --- writes (no fallback; throw on failure) ---
  uploadResume: async (file: File): Promise<UploadedResume> => {
    const form = new FormData();
    form.append("file", file);
    const res = await fetch(`${BASE}/files/resume`, { method: "POST", body: form });
    if (!res.ok) {
      let detail = `Upload failed (${res.status})`;
      try {
        const errBody = await res.json();
        if (errBody?.detail) {
          detail = typeof errBody.detail === "string" ? errBody.detail : detail;
        }
      } catch {
        /* non-JSON error body */
      }
      throw new Error(detail);
    }
    return (await res.json()) as UploadedResume;
  },
  createPosition: (title: string, description: string) =>
    send<{ id: string }>(`/positions`, "POST", { title, description }),
  createAssessment: (resumeId: string, positionId: string) =>
    send<Assessment>(`/assessments`, "POST", {
      resume_id: resumeId,
      position_id: positionId,
    }),
  // Candidate self-serve: own resume + a pasted job description.
  createSelfAssessment: (resumeId: string, jdText: string, positionTitle?: string) =>
    send<{ id: string }>(`/assessments/self`, "POST", {
      resume_id: resumeId,
      jd_text: jdText,
      position_title: positionTitle ?? null,
    }),
  // Capability Translation: re-express evidenced capability in ATS-legible,
  // JD-targeted language; backend returns measured before→after lift.
  createCapabilityTranslation: (resumeId: string, jdText: string, targetRole?: string) =>
    send<{ translationId: string; status: string }>(`/candidates/capability-translation`, "POST", {
      resume_id: resumeId,
      jd_text: jdText,
      target_role: targetRole ?? null,
    }),
  getCapabilityTranslation: (id: string) =>
    get<CapabilityTranslationResult>(`/candidates/capability-translation/${id}`, {
      translationId: id,
      status: "pending",
      bullets: [],
      skills: [],
      matchedKeywordsAfter: [],
      stillMissingKeywords: [],
      droppedUngrounded: 0,
    }),

  // --- Transition Intelligence (predict adjacent/higher roles + upskilling) ---
  createTransition: (resumeId: string, currentRole?: string, target?: string) =>
    send<{ analysisId: string; status: string }>(`/candidates/transition-intelligence`, "POST", {
      resume_id: resumeId,
      current_role: currentRole ?? null,
      target: target ?? null,
    }),
  getTransition: (id: string) =>
    get<TransitionResult>(`/candidates/transition-intelligence/${id}`, {
      analysisId: id,
      status: "pending",
      transitionOptions: [],
      droppedUngrounded: 0,
    }),
  // Phase 3: longitudinal tracking
  setTransitionTracking: (id: string, enabled: boolean) =>
    send<{ tracking: boolean; nextReviewAt: string | null }>(
      `/candidates/transition-intelligence/${id}/track`, "POST", { enabled }),
  getTransitionTrajectory: (resumeId: string) =>
    get<TrajectoryPoint[]>(`/candidates/transition-intelligence/trajectory/by-resume/${resumeId}`, []),
  recordTransitionOutcome: (payload: {
    analysisId: string; predictedRole: string; status: string; actualRole?: string; note?: string;
  }) =>
    send<unknown>(`/candidates/transition-intelligence/outcome`, "POST", {
      analysis_id: payload.analysisId,
      predicted_role: payload.predictedRole,
      status: payload.status,
      actual_role: payload.actualRole ?? null,
      note: payload.note ?? null,
    }),
  getTransitionMetrics: () =>
    get<TransitionMetrics>(`/candidates/transition-intelligence/cohort/metrics`, {
      analysesTotal: 0, analysesCompleted: 0, tracked: 0, candidates: 0,
      readiness: {}, outcomes: {}, resolvedOutcomes: 0, achievementRate: null,
    }),
  recordDecision: (payload: DecisionPayload) =>
    send<DecisionRecord>(`/decisions`, "POST", payload),
  setProfileVisibility: (visibility: "private" | "link" | "public") =>
    send<unknown>(`/profile/me`, "PATCH", { visibility }),
  exportMyData: () => send<unknown>(`/profile/export`, "POST"),
  deleteMyAccount: () => send<void>(`/profile`, "DELETE"),

  // --- agent control API ---
  getAgentQueue: (status?: string): Promise<IngestQueueItem[]> => {
    const url = status ? `/agents/queue?status=${status}` : `/agents/queue`;
    return get<IngestQueueItem[]>(url, []);
  },
  approveQueueItem: (id: string, notes?: string) =>
    send<{ status: string }>(`/agents/queue/${id}/approve`, "POST", { notes: notes ?? null }),
  rejectQueueItem: (id: string, notes?: string) =>
    send<{ status: string }>(`/agents/queue/${id}/reject`, "POST", { notes: notes ?? null }),

  // --- scraper API ---
  getScrapers: () => get<{ scrapers: ScraperConfig[] }>(`/scrapers`, { scrapers: [] }),
  createScraper: (payload: ScraperConfig) => send<ScraperConfig>(`/scrapers`, "POST", payload),
  updateScraper: (id: string, payload: Partial<ScraperConfig>) => send<ScraperConfig>(`/scrapers/${id}`, "PATCH", payload),
  testScraper: (id: string) => send<{ status: string }>(`/scrapers/${id}/test`, "POST", {}),
  deleteScraper: (id: string) => send<void>(`/scrapers/${id}`, "DELETE"),
  getScraperRuns: (id: string) => get<{ config_id: string; runs: ScraperRun[] }>(`/scrapers/${id}/runs`, { config_id: id, runs: [] }),

  // --- upload API ---
  getFieldMappings: () => get<{ mappings: FieldMapping[] }>(`/upload/field-mappings`, { mappings: [] }),
  getUploadBatches: () => get<{ batches: UploadBatch[] }>(`/upload/batches`, { batches: [] }),
  getUploadBatch: (id: string) => get<UploadBatch>(`/upload/batch/${id}`, {} as UploadBatch),
  uploadCSV: async (formData: FormData): Promise<UploadBatch> => {
    const res = await fetch(`${BASE}/upload/csv`, {
      method: "POST",
      body: formData,
    });
    if (!res.ok) throw new Error(`Upload failed (${res.status})`);
    return (await res.json()) as UploadBatch;
  },
  uploadJSON: (payload: Record<string, unknown>) => send<UploadBatch>(`/upload/json`, "POST", payload),
  downloadErrors: (id: string) => get<{ errors: Array<{ row: number; field: string; error: string }> }>(`/upload/batch/${id}/errors`, { errors: [] }),

  // --- CV Analysis API (candidate feature) ---
  // Backend: /candidates/cv-analysis (JSON body; returns { analysis_id }).
  createCVAnalysis: (payload: {
    resumeId: string;
    targetRole: string;
    targetSeniority: "junior" | "mid" | "senior" | "lead";
    careerFocusAreas?: string[];
  }): Promise<{ analysis_id: string; status: string }> =>
    send<{ analysis_id: string; status: string }>(`/candidates/cv-analysis`, "POST", {
      resume_id: payload.resumeId,
      target_role: payload.targetRole,
      target_seniority: payload.targetSeniority,
      career_focus_areas: payload.careerFocusAreas ?? null,
    }),
  getCVAnalysis: (id: string) =>
    get<CVAnalysisResponse>(`/candidates/cv-analysis/${id}`, {
      id,
      fileName: "",
      extractedText: "",
      skills: [],
      experience_years: 0,
      summary: "",
    } as unknown as CVAnalysisResponse),
  listCVAnalyses: () =>
    get<{ items: unknown[]; total: number }>(`/candidates/cv-analysis`, {
      items: [],
      total: 0,
    }),

  // --- JD Simulation API (recruiter feature) ---
  // Backend: /recruiters/jd-simulation (JSON body; returns { simulation_id }).
  createJDSimulation: (payload: {
    jdText?: string;
    positionId?: string;
    simulationType?: "requirement_fit" | "market_comparison" | "candidate_archetype";
  }): Promise<{ simulation_id: string; status: string }> =>
    send<{ simulation_id: string; status: string }>(`/recruiters/jd-simulation`, "POST", {
      jd_text: payload.jdText ?? null,
      position_id: payload.positionId ?? null,
      simulation_type: payload.simulationType ?? "requirement_fit",
    }),
  getJDSimulation: (id: string) =>
    get<JDSimulationResponse>(`/recruiters/jd-simulation/${id}`, {
      id,
      jd_text: "",
      extracted_requirements: [],
      quality_score: 0,
      suggestions: [],
    } as unknown as JDSimulationResponse),
  listJDSimulations: () =>
    get<{ items: unknown[]; total: number }>(`/recruiters/jd-simulation`, {
      items: [],
      total: 0,
    }),

  // --- billing & payments ---
  getCatalog: () =>
    get<{ items: CatalogItem[]; configured: boolean }>(`/billing/catalog`, {
      items: [],
      configured: false,
    }),
  getBilling: () =>
    get<BillingSummary>(`/billing/me`, {
      has_access: false,
      credit_balance: 0,
      unlimited: false,
      entitlement: null,
      orders: [],
    }),
  // Returns a Stripe Checkout URL the caller should redirect to.
  startCheckout: (sku: string, quantity = 1) =>
    send<{ order_id: string; checkout_url: string }>(`/billing/checkout`, "POST", {
      sku,
      quantity,
    }),
  redeemCode: (code: string) =>
    send<{ granted_credits: number; balance: number }>(`/billing/redeem`, "POST", { code }),
  // Live Founding-100 inventory (public).
  getFounding: () =>
    get<{ tiers: FoundingTier[] }>(`/billing/founding`, { tiers: [] }),

  // --- admin: orders / fulfillment queue ---
  getBillingSummary: () =>
    get<BillingAdminSummary>(`/billing/admin/summary`, {
      paid_orders: 0,
      gross_revenue: 0,
      awaiting_fulfillment: 0,
      refunded_orders: 0,
      founding: [],
    }),
  getAdminOrders: (statusFilter?: string, fulfillment?: string) => {
    const qs = new URLSearchParams();
    if (statusFilter) qs.set("status_filter", statusFilter);
    if (fulfillment) qs.set("fulfillment", fulfillment);
    const q = qs.toString();
    return get<{ items: AdminOrder[]; total: number }>(
      `/billing/admin/orders${q ? `?${q}` : ""}`,
      { items: [], total: 0 },
    );
  },
  setFulfillment: (orderId: string, fulfillment_status: string, note?: string) =>
    send<{ id: string; fulfillment_status: string }>(
      `/billing/admin/orders/${orderId}/fulfillment`,
      "PATCH",
      { fulfillment_status, note },
    ),
  refundOrderById: (order_id: string) =>
    send<{ order_id: string; status: string }>(`/billing/refund`, "POST", { order_id }),

  // --- referrals & shareable results ---
  getReferral: () =>
    get<ReferralInfo>(`/billing/referral`, {
      code: "", share_base: "", referrals: 0, credits_earned: 0, reward_credits: 1,
    }),
  redeemReferral: (code: string) =>
    send<{ granted_credits: number; balance: number }>(`/billing/referral/redeem`, "POST", { code }),
  shareAssessment: (assessmentId: string) =>
    send<{ token: string; share_url: string; referral_code: string }>(
      `/assessments/${assessmentId}/share`, "POST",
    ),
  getSharedResult: (token: string) =>
    get<SharedResultView | null>(`/billing/share/${token}`, null),
};

export interface ReferralInfo {
  code: string;
  share_base: string;
  referrals: number;
  credits_earned: number;
  reward_credits: number;
}

export interface SharedResultView {
  traditional_score: number | null;
  semantic_score: number | null;
  capability_score: number | null;
  score_delta: number | null;
  counter_rec: boolean;
  referral_code: string | null;
  created_at: string | null;
}

export interface FoundingTier {
  sku: string;
  name: string;
  amount: number;
  currency: string;
  limit: number;
  sold: number;
  remaining: number;
}

export interface AdminOrder {
  id: string;
  user_email: string;
  sku: string;
  amount: number;
  currency: string;
  status: string;
  fulfillment_status: string;
  stripe_payment_intent: string | null;
  created_at: string | null;
}

export interface BillingAdminSummary {
  paid_orders: number;
  gross_revenue: number;
  awaiting_fulfillment: number;
  refunded_orders: number;
  founding: FoundingTier[];
}

export interface CatalogItem {
  id: string;
  name: string;
  description: string;
  amount: number; // cents
  currency: string;
  mode: "payment" | "subscription";
  credits: number;
  entitlement_kind: string | null;
  entitlement_plan: string | null;
}

export interface BillingSummary {
  has_access: boolean;
  credit_balance: number;
  unlimited: boolean;
  entitlement: {
    kind: string;
    plan: string;
    status: string;
    expires_at: string | null;
    monthly_credits: number | null;
  } | null;
  orders: {
    id: string;
    sku: string;
    amount: number;
    currency: string;
    status: string;
    fulfillment_status: string;
    created_at: string | null;
  }[];
}
