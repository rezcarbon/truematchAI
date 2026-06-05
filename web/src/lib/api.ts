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
  getAssessment: (id: string) =>
    get<Assessment>(`/assessments/${id}`, { ...mockAssessment, id }),
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
  getAudit: () => get<AuditEntry[]>(`/audit`, mockAudit),
  getUsers: () => get<UserRecord[]>(`/users`, mockUsers),

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
  getScrapers: () => get<any>(`/scrapers`, { scrapers: [] }),
  createScraper: (payload: any) => send<any>(`/scrapers`, "POST", payload),
  updateScraper: (id: string, payload: any) => send<any>(`/scrapers/${id}`, "PATCH", payload),
  testScraper: (id: string) => send<any>(`/scrapers/${id}/test`, "POST", {}),
  deleteScraper: (id: string) => send<void>(`/scrapers/${id}`, "DELETE"),
  getScraperRuns: (id: string) => get<any>(`/scrapers/${id}/runs`, { config_id: id, runs: [] }),

  // --- upload API ---
  getFieldMappings: () => get<any>(`/upload/field-mappings`, { mappings: [] }),
  getUploadBatches: () => get<any>(`/upload/batches`, { batches: [] }),
  getUploadBatch: (id: string) => get<any>(`/upload/batch/${id}`, {}),
  uploadCSV: (formData: FormData) => {
    const res = fetch(`${BASE}/upload/csv`, {
      method: "POST",
      body: formData,
    });
    return res.then(async (r) => {
      if (!r.ok) throw new Error(`Upload failed (${r.status})`);
      return (await r.json()) as any;
    });
  },
  uploadJSON: (payload: any) => send<any>(`/upload/json`, "POST", payload),
  downloadErrors: (id: string) => get<any>(`/upload/batch/${id}/errors`, {}),

  // --- CV Analysis API (candidate feature) ---
  createCVAnalysis: (formData: FormData) => {
    const res = fetch(`${BASE}/cv-analysis`, {
      method: "POST",
      body: formData,
    });
    return res.then(async (r) => {
      if (!r.ok) throw new Error(`CV analysis failed (${r.status})`);
      return (await r.json()) as { id: string };
    });
  },
  getCVAnalysis: (id: string) =>
    get<any>(`/cv-analysis/${id}`, {
      id,
      status: "pending",
      targetRole: "Target Role",
      missingCapabilities: [],
      weaknessAreas: [],
      strengthSummary: "",
      topMatchingPositions: [],
      improvementSuggestions: [],
      trajectoryAnalysis: "",
      marketPositioning: "",
      growthOpportunities: [],
    }),
  listCVAnalyses: () =>
    get<any>(`/cv-analysis`, {
      analyses: [],
    }),

  // --- JD Simulation API (recruiter feature) ---
  createJDSimulation: async (
    jdText: string,
    positionTitle?: string
  ): Promise<{ id: string }> => {
    return send<{ id: string }>(`/jd-simulation`, "POST", {
      jd_text: jdText,
      position_title: positionTitle ?? null,
    });
  },
  getJDSimulation: (id: string) =>
    get<any>(`/jd-simulation/${id}`, {
      id,
      status: "pending",
      jdText: "",
      positionTitle: "Untitled Position",
      jdQuality: {
        score: 0,
        flags: [],
      },
    }),
  listJDSimulations: () =>
    get<any>(`/jd-simulation`, {
      simulations: [],
    }),
};
