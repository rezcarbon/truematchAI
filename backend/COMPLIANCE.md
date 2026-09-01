# TrueMatch — Regulatory Compliance & Auditability

TrueMatch is an automated employment-decision support tool and is treated as a
**high-risk AI system**. This document maps each regulatory obligation to the
concrete control implemented in the codebase, so any assessment can be fully
documented, reproduced, and audited.

> Scope note: TrueMatch is decision **support** — it surfaces capability and a
> counter-recommendation, but a **human always decides** (recorded in `decisions`
> with override reasoning). It never auto-rejects or auto-hires.

---

## 1. End-to-end auditability of every assessment

Every assessment writes an **immutable, timestamped audit trail** (`audit_trail`,
append-only; `models/audit.py`). For one assessment the chain is:

| Event | Records |
|---|---|
| `pipeline.provenance` | **Reproducibility manifest** — input SHA-256 hashes (resume + JD), model name, `prompt_registry_version`, deterministic engine method versions, reasoning mode (live/mock), enrichment flag (`core/provenance.py`) |
| `intake.completed` | traditional (keyword) score + **semantic score + method** |
| `enrichment.completed` | external-evidence counts (total / verified) + substitution count |
| `reasoning.completed` | capability score, score delta |
| `governance.completed` | governed flag + coherence/consistency/fidelity pass-booleans + bias-flag count + review-required |
| `pipeline.completed` | final status (`completed` / `flagged_for_review`) |
| `pipeline.failed` | error (on failure) |

Because the manifest stores **input hashes + exact versions**, an auditor can prove
which inputs and which prompt/engine versions produced a given decision. The
**deterministic engines** (semantic match `lexical-concept-v1`, JD-evolution drift
`jd-evolution-v1`) are byte-for-byte reproducible from the same inputs.

---

## 2. EU AI Act (high-risk AI obligations)

| Article / obligation | Control in TrueMatch |
|---|---|
| **Art. 9 Risk management** | Governance engine runs coherence/consistency/fidelity/bias checks on every assessment; gate failure routes to `flagged_for_review` (cannot be bypassed) — `engines/governance_engine.py`, `workers/tasks.py` |
| **Art. 10 Data governance** | Resume parsing preserves provenance; external links verified, not assumed (`engines/enrichment.py`); inputs hashed |
| **Art. 12 Record-keeping / logging** | Immutable `audit_trail` per stage with provenance manifest (§1) |
| **Art. 13 Transparency** | Dual/triple score (keyword → semantic → capability) + narrative + per-issue JD recommendations are surfaced to users; nothing is a black-box number |
| **Art. 14 Human oversight** | Human decision layer (`decisions`) with accept/override + mandatory override reasoning; counter-recommendation is advisory only |
| **Art. 15 Accuracy/robustness/reproducibility** | Deterministic, versioned scoring engines; `prompt_registry_version`; retry + strict-JSON parsing in the LLM client |
| **Trade-secret protection (Art. 78 confidentiality)** | Governance threshold values never in source/logs/responses — named constants only (`core/governance.py`); IP-safe by design |

---

## 3. NYC Local Law 144 (automated employment decision tools)

| Requirement | Control |
|---|---|
| **Annual independent bias audit** | `governance_engine.check_bias()` runs on **every** assessment (not sampled), scanning for protected/proxy-attribute influence; results stored per assessment and aggregated in `GET /admin/compliance/report` and `/admin/analytics` |
| **Bias-audit data availability** | Bias flags + governed-assessment counts are queryable/exportable for an independent auditor via the admin compliance endpoints |
| **Candidate notice & data** | PDPA/GDPR export (`POST /profile/export`) gives the candidate their full record, including the assessment that was run |
| **Capability over proxies** | Proxy detection (`JD_ANALYZE`) + explicit substitution scoring (`engines/substitution.py`) reduce credential-proxy adverse impact by crediting alternate evidence |

---

## 4. PDPA (Singapore) / GDPR (data protection)

| Requirement | Control |
|---|---|
| **Encryption at rest** | AES-256-GCM field encryption on all PII columns (resume text/parsed data, narratives, decision notes, audit event data, evidence, substitutions, `singpass_id`) — `core/crypto.py`, `models/_types.py` |
| **Encryption in transit** | TLS terminated at the gateway (deployment); S3 objects server-side encrypted (KMS/AES256) |
| **Right to data portability** | `POST /profile/export` returns the user's complete record (`api/v1/profile.py`) |
| **Right to erasure** | `DELETE /profile` deletes the user + cascades all associated data, leaving an unlinked compliance tombstone proving erasure occurred |
| **Data minimisation** | Singpass stores only the opaque NDI UUID, never the NRIC (`core/singpass.py`) |
| **Searchable-without-exposure** | Keyed blind index for `singpass_id` lookups (`core/crypto.blind_index`) |
| **No silent secret exposure** | `.gitignore` excludes `.env`, governance config, `*.jwk`/`*.pem`; secrets injected at runtime |

---

## 5. Fairness-by-design controls (beyond the letter of the law)

- **JD interrogation** flags exclusionary phrasing, inflated seniority, and
  impossible/"purple-squirrel" requirements that suppress qualified applicants,
  with a concrete fix per issue (`reasoning.interrogate_jd`).
- **JD evolution** (`engines/jd_evolution.py`) detects longitudinal *requirement
  creep* (e.g. years-of-experience climbing posting over posting) — a structural
  source of adverse impact — and recommends how the role should evolve.
- **Counter-recommendation** is gated on a *delta* between keyword and capability
  signals, surfacing qualified candidates a keyword screen would silently reject.
- **JD version history** (`jd_versions`) is an immutable record of how a posting's
  requirements changed over time.

---

## 6. What an operator must still provide

These are deployment/governance responsibilities, not code:

1. Real governance threshold values via secrets manager (`GOVERNANCE_*`) — without
   them, runs are honestly recorded as **ungoverned**, not falsely passed.
2. A real `ANTHROPIC_API_KEY` (reasoning runs in reproducible **mock** mode otherwise).
3. KMS-wrapped `ENCRYPTION_KEY` + a documented key-rotation procedure (`enc:v1:`
   token versioning supports rotation).
4. Candidate-facing notice/consent flow per local law (the data rights endpoints
   exist to back it).
5. A scheduled export of the audit trail + bias metrics to the independent auditor.
