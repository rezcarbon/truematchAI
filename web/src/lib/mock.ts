// Mock data for standalone rendering while the backend is not live.
// All values here are illustrative fixtures. Governance scores/statuses are
// treated strictly as opaque, backend-owned display values — no thresholds,
// no client-side computation of governance semantics.

import type {
  Assessment,
  PipelineCandidate,
  Position,
  DecisionRecord,
  AuditEntry,
  UserRecord,
} from "./types";

export const mockAssessment: Assessment = {
  id: "asm_demo_001",
  candidateName: "Priya Nair",
  positionTitle: "Senior Backend Engineer",
  createdAt: "2026-05-20T09:12:00Z",
  substitutions: [
    {
      requirement: "MSc in Computer Science",
      underlyingCapability: "deep technical / systems design ability",
      strength: "HIGH",
      rationale:
        "No MSc, but shipped a production system at scale and contributes to a widely-used open-source library — verified.",
      alternateEvidence: ["Production system, 3,421 verified operations", "OSS library, 8k stars (verified)"],
    },
    {
      requirement: "8+ years at a large tech firm",
      underlyingCapability: "operating at scale",
      strength: "MEDIUM",
      rationale: "Scale evidenced via venture/ecosystem builds; large-firm tenure not present.",
    },
  ],
  traditionalScore: 19,
  semanticScore: 72,
  matchType: "surfaced_strong_match",
  capabilityScore: {
    overall: 87,
    components: [
      { key: "systems", label: "Systems Design", score: 91, weight: 0.3 },
      { key: "delivery", label: "Delivery & Ownership", score: 88, weight: 0.25 },
      { key: "collab", label: "Cross-functional Collaboration", score: 84, weight: 0.2 },
      { key: "learning", label: "Learning Velocity", score: 89, weight: 0.15 },
      { key: "domain", label: "Domain Adjacency", score: 78, weight: 0.1 },
    ],
  },
  delta: 68,
  narrative:
    "The candidate's resume under-indexes on the exact keywords in the job description, which depresses the traditional match. Read for demonstrated capability, the picture is markedly stronger: a consistent record of owning ambiguous backend problems end to end, leading migrations, and ramping quickly into unfamiliar stacks. The gap between the two scores is driven almost entirely by surface terminology rather than substance.",
  gaps: [
    { area: "Kubernetes (named in JD)", status: "partial", detail: "Operated comparable container orchestration; no exact keyword match." },
    { area: "Go (named in JD)", status: "gap", detail: "Primary languages are Java/Kotlin; strong adjacent transfer signal." },
    { area: "Distributed systems", status: "met", detail: "Led a multi-region data pipeline rebuild." },
    { area: "On-call ownership", status: "met", detail: "Owned production reliability for a tier-1 service." },
  ],
  counterRecommendation: {
    triggered: true,
    headline: "This candidate does not match the JD as written. However…",
    rationale:
      "The low traditional score reflects keyword mismatch (Go, Kubernetes) rather than a capability deficit. Demonstrated systems-design and delivery ability sit well above the bar for this role. The JD's language stack requirement appears to be a proxy for distributed-systems competence the candidate clearly holds.",
    suggestedRoles: [
      "Senior Backend Engineer (this role)",
      "Platform Engineer",
      "Staff Engineer — Infrastructure (stretch)",
    ],
  },
  jdQuality: {
    score: 61,
    flags: [
      { id: "f1", type: "proxy", field: "Required: Go", message: "Specific language likely a proxy for distributed-systems skill.", recommendation: "Ask for distributed-systems experience in any language; treat Go as preferred, not required." },
      { id: "f2", type: "impossible", field: "Required: 8+ yrs Kubernetes", message: "Requested tenure exceeds the technology's practical availability window.", recommendation: "Lower to 4+ years, or reframe as 'production Kubernetes operations at scale'." },
      { id: "f3", type: "ambiguous", field: "Responsibilities", message: "\"Wear many hats\" is unscoped and may deter strong applicants.", recommendation: "List the 3-4 concrete responsibilities that matter most for the first 6 months." },
    ],
  },
  trajectory: [
    { period: "2017", role: "Software Engineer", capability: 52, scope: 30 },
    { period: "2019", role: "Software Engineer II", capability: 64, scope: 45 },
    { period: "2021", role: "Senior Engineer", capability: 76, scope: 62 },
    { period: "2023", role: "Senior Engineer (Lead)", capability: 83, scope: 78 },
    { period: "2025", role: "Tech Lead", capability: 87, scope: 88 },
  ],
  governance: {
    coherence: { score: 94, status: "pass", label: "Coherence" },
    consistency: { score: 91, status: "pass", label: "Consistency" },
    fidelity: { score: 88, status: "pass", label: "Fidelity" },
    biasFlags: [],
  },
};

export const mockPipeline: PipelineCandidate[] = [
  { id: "c1", name: "Priya Nair", appliedFor: "Senior Backend Engineer", traditionalScore: 43, capabilityScore: 87, delta: 44, stage: "screening", governanceStatus: "pass" },
  { id: "c2", name: "Marcus Lee", appliedFor: "Senior Backend Engineer", traditionalScore: 88, capabilityScore: 71, delta: -17, stage: "interview", governanceStatus: "pass" },
  { id: "c3", name: "Aisha Rahman", appliedFor: "Senior Backend Engineer", traditionalScore: 65, capabilityScore: 82, delta: 17, stage: "screening", governanceStatus: "review" },
  { id: "c4", name: "Daniel Osei", appliedFor: "Senior Backend Engineer", traditionalScore: 72, capabilityScore: 69, delta: -3, stage: "new", governanceStatus: "pass" },
  { id: "c5", name: "Sofia Alvarez", appliedFor: "Senior Backend Engineer", traditionalScore: 39, capabilityScore: 79, delta: 40, stage: "new", governanceStatus: "pass" },
  { id: "c6", name: "Tom Becker", appliedFor: "Senior Backend Engineer", traditionalScore: 91, capabilityScore: 58, delta: -33, stage: "rejected", governanceStatus: "pass" },
];

export const mockPositions: Position[] = [
  { id: "p1", title: "Senior Backend Engineer", department: "Engineering", location: "Singapore", candidateCount: 42, jdQualityScore: 61, status: "open" },
  { id: "p2", title: "Product Designer", department: "Design", location: "Remote", candidateCount: 28, jdQualityScore: 84, status: "open" },
  { id: "p3", title: "Data Scientist", department: "Data", location: "Singapore", candidateCount: 19, jdQualityScore: 73, status: "paused" },
  { id: "p4", title: "Engineering Manager", department: "Engineering", location: "London", candidateCount: 11, jdQualityScore: 58, status: "open" },
];

export const mockDecisions: DecisionRecord[] = [
  { id: "d1", candidateName: "Priya Nair", positionTitle: "Senior Backend Engineer", recruiter: "J. Tan", decision: "advance", traditionalScore: 43, capabilityScore: 87, overrodeRecommendation: false, timestamp: "2026-05-28T14:00:00Z" },
  { id: "d2", candidateName: "Tom Becker", positionTitle: "Senior Backend Engineer", recruiter: "J. Tan", decision: "reject", traditionalScore: 91, capabilityScore: 58, overrodeRecommendation: true, timestamp: "2026-05-27T10:30:00Z" },
  { id: "d3", candidateName: "Aisha Rahman", positionTitle: "Senior Backend Engineer", recruiter: "M. Owusu", decision: "hold", traditionalScore: 65, capabilityScore: 82, overrodeRecommendation: false, timestamp: "2026-05-26T16:45:00Z" },
];

export const mockAudit: AuditEntry[] = [
  { id: "a1", actor: "j.tan@acme.com", action: "DECISION_ADVANCE", target: "candidate:c1", timestamp: "2026-05-28T14:00:11Z", ip: "10.2.4.18" },
  { id: "a2", actor: "j.tan@acme.com", action: "DECISION_OVERRIDE_REJECT", target: "candidate:c6", timestamp: "2026-05-27T10:30:02Z", ip: "10.2.4.18" },
  { id: "a3", actor: "admin@acme.com", action: "CONFIG_UPDATE", target: "governance:profile", timestamp: "2026-05-25T08:15:00Z", ip: "10.2.4.9" },
  { id: "a4", actor: "m.owusu@acme.com", action: "ASSESSMENT_VIEW", target: "assessment:asm_demo_001", timestamp: "2026-05-26T16:40:00Z", ip: "10.2.4.21" },
];

export const mockUsers: UserRecord[] = [
  { id: "u1", name: "Jocelyn Tan", email: "j.tan@acme.com", role: "recruiter", status: "active", lastActive: "2026-05-30T09:00:00Z" },
  { id: "u2", name: "Michael Owusu", email: "m.owusu@acme.com", role: "recruiter", status: "active", lastActive: "2026-05-29T17:20:00Z" },
  { id: "u3", name: "Sara Admin", email: "admin@acme.com", role: "admin", status: "active", lastActive: "2026-05-31T07:45:00Z" },
  { id: "u4", name: "Priya Nair", email: "priya.n@example.com", role: "candidate", status: "active", lastActive: "2026-05-20T09:12:00Z" },
  { id: "u5", name: "New Recruiter", email: "pending@acme.com", role: "recruiter", status: "invited", lastActive: "—" },
];
