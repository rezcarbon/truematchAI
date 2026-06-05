// Shared types mirroring the backend Assessment API response.
// These are DISPLAY contracts only — the web client never computes any of
// these values. Scores, statuses, and flags all originate from the backend.

export type GovernanceStatus = "pass" | "review" | "fail";

/** Governance signals are display-only. The numeric `score` and the `status`
 *  are produced entirely by the backend; the client only renders them. */
export interface GovernanceSignal {
  /** Backend-supplied 0..100 score. The client must not threshold this. */
  score: number;
  /** Backend-supplied status. The client must not derive this. */
  status: GovernanceStatus;
  label: string;
}

export interface BiasFlag {
  id: string;
  category: string;
  description: string;
  severity: "low" | "medium" | "high";
}

export interface Governance {
  coherence: GovernanceSignal;
  consistency: GovernanceSignal;
  fidelity: GovernanceSignal;
  biasFlags: BiasFlag[];
}

export interface CapabilityComponent {
  key: string;
  label: string;
  score: number; // 0..100, backend-supplied
  weight: number; // 0..1, backend-supplied
}

export interface CapabilityScore {
  overall: number; // 0..100
  components: CapabilityComponent[];
}

export interface TrajectoryPoint {
  period: string; // e.g. "2019", "2021 Q3"
  role: string;
  capability: number; // backend-supplied capability estimate at this point
  scope: number; // breadth/responsibility index
}

export interface JDQualityFlag {
  id: string;
  type: "proxy" | "impossible" | "ambiguous" | "exclusionary";
  field: string;
  message: string;
  /** Actionable fix the JD-interrogation engine proposed for this issue. */
  recommendation?: string;
  severity?: string;
}

export interface JDQuality {
  score: number; // 0..100 JD quality score, backend-supplied
  flags: JDQualityFlag[];
}

export interface GapItem {
  area: string;
  status: "met" | "partial" | "gap";
  detail: string;
}

export interface CounterRecommendation {
  triggered: boolean;
  headline: string;
  rationale: string;
  suggestedRoles: string[];
}

/** Pillar 6: how a candidate's alternate evidence substitutes for a proxy/credential. */
export interface Substitution {
  requirement: string;
  underlyingCapability: string;
  strength: "HIGH" | "MEDIUM" | "WEAK";
  rationale: string;
  alternateEvidence?: string[];
}

export interface Assessment {
  id: string;
  candidateName: string;
  positionTitle: string;
  /** Position this assessment belongs to (needed to record a decision). */
  positionId?: string;
  /** Pillar 6 substitutions (backend-supplied; empty when no proxies). */
  substitutions?: Substitution[];
  createdAt: string;
  /** Traditional keyword/ATS match score (0..100). */
  traditionalScore: number;
  /** Pillar 1 concept-level semantic match (0..100) — the middle signal. */
  semanticScore?: number;
  /** TrueMatch capability score (0..100). */
  capabilityScore: CapabilityScore;
  /** Signed difference highlighted as the signature insight. */
  delta: number;
  /** hidden_gem | surfaced_strong_match | keyword_aligned */
  matchType?: "hidden_gem" | "surfaced_strong_match" | "keyword_aligned";
  narrative: string;
  gaps: GapItem[];
  counterRecommendation: CounterRecommendation;
  jdQuality: JDQuality;
  trajectory: TrajectoryPoint[];
  governance: Governance;
}

export interface PipelineCandidate {
  id: string;
  name: string;
  appliedFor: string;
  traditionalScore: number;
  capabilityScore: number;
  delta: number;
  stage: "new" | "screening" | "interview" | "offer" | "rejected";
  governanceStatus: GovernanceStatus;
  matchType?: "hidden_gem" | "surfaced_strong_match" | "keyword_aligned";
  counterRecommendation?: {
    triggered: boolean;
    headline: string;
    rationale: string;
    suggestedRoles?: string[];
  };
}

export interface Position {
  id: string;
  title: string;
  department: string;
  location: string;
  candidateCount: number;
  jdQualityScore: number;
  status: "open" | "paused" | "closed";
  /** Optional: days the position has been open */
  daysOpen?: number;
  /** Optional: total applications received */
  totalApplied?: number;
  /** Optional: candidates in active screening/interview */
  inProgress?: number;
}

export interface DecisionRecord {
  id: string;
  candidateName: string;
  positionTitle: string;
  recruiter: string;
  decision: "advance" | "reject" | "hold";
  traditionalScore: number;
  capabilityScore: number;
  overrodeRecommendation: boolean;
  timestamp: string;
}

export interface AuditEntry {
  id: string;
  actor: string;
  action: string;
  target: string;
  timestamp: string;
  ip: string;
}

export interface UserRecord {
  id: string;
  name: string;
  email: string;
  role: "candidate" | "recruiter" | "admin";
  status: "active" | "invited" | "suspended";
  lastActive: string;
}
