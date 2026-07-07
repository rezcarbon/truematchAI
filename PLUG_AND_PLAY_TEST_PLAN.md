# TrueMatch - Plug & Play Testing Plan
**Date**: July 5, 2026  
**Status**: ✅ ALL SYSTEMS READY FOR TESTING  
**Meeting**: Later Today

---

## 🎯 Testing Objectives

### 1. CV Assessment Testing
**Capability**: Full candidate evaluation with gap analysis and improvement recommendations

**Test Flow**:
1. **Upload Resume** → `/api/v1/candidates/cv-analysis` (POST)
2. **Parse & Analyze** → Extract skills, experience, trajectory
3. **Gap Analysis** → Missing capabilities vs target role
4. **Improvement Suggestions** → Specific, actionable recommendations

**Endpoints to Test**:
```
POST   /api/v1/candidates/cv-analysis
GET    /api/v1/candidates/cv-analysis/{analysis_id}
GET    /api/v1/candidates/cv-analysis (list all)
```

**Expected Output**:
```json
{
  "id": "uuid",
  "status": "completed",
  "missing_capabilities": ["Kubernetes", "Docker"],
  "weakness_areas": ["Limited cloud infrastructure experience"],
  "strength_summary": "Strong backend engineering background",
  "improvement_suggestions": [
    {
      "area": "Kubernetes",
      "current_level": "none",
      "target_level": "intermediate",
      "how": "Take Linux Foundation K8s fundamentals course"
    }
  ],
  "growth_opportunities": [
    "Site Reliability Engineer (adjacent role)"
  ]
}
```

---

### 2. JD Analysis Testing
**Capability**: Decompose job description, detect requirements drift, identify gaps

**Test Flow**:
1. **Upload/Provide JD** → `/api/v1/positions` (POST) or `/api/v1/agents/jd/draft`
2. **Analyze Requirements** → Parse essential vs preferred
3. **Quality Check** → Detect vague specs, impossible constraints
4. **Drift Detection** → Compare to previous versions (if available)

**Endpoints to Test**:
```
POST   /api/v1/positions (create job)
GET    /api/v1/positions/{position_id} (get details)
POST   /api/v1/agents/jd/draft (AI-assisted JD creation)
GET    /api/v1/agents/jd/{position_id}/suggestions
```

**Expected Output**:
```json
{
  "id": "uuid",
  "jd_quality_score": 78,
  "required_capabilities": [
    { "name": "Kubernetes", "role": "ESSENTIAL" },
    { "name": "Docker", "role": "ESSENTIAL" },
    { "name": "AWS", "role": "PREFERRED" }
  ],
  "proxies": [
    {
      "requirement": "5+ years Kubernetes",
      "underlying_capability": "container orchestration"
    }
  ],
  "issues": [
    {
      "type": "impossible_constraint",
      "detail": "Requests 10+ years Kubernetes (tool launched 2014)",
      "recommendation": "Reduce to 3-5 years for realistic candidate pool"
    }
  ]
}
```

---

### 3. CV-to-JD Alignment & Fit Testing
**Capability**: Multi-pillar matching with explainability

**Test Flow**:
1. **Create Assessment** → `/api/v1/assessments` (POST)
   - Provide resume_id + position_id
2. **Run Pipeline** → System executes:
   - **Pillar 1**: Traditional ATS (keyword matching)
   - **Pillar 2**: Semantic matching (embeddings)
   - **Pillar 3**: Capability reasoning (Claude)
3. **Governance Gates** → Verify fraud detection
4. **Get Results** → Scores + explanations

**Endpoints to Test**:
```
POST   /api/v1/assessments (create assessment)
GET    /api/v1/assessments/{assessment_id} (full result)
GET    /api/v1/assessments/{assessment_id}/traditional (pillar 1)
GET    /api/v1/assessments/{assessment_id}/explanation (why this score)
GET    /api/v1/assessments/{assessment_id}/trajectory (career fit)
GET    /api/v1/assessments/{assessment_id}/governance (compliance check)
```

**Expected Output**:
```json
{
  "id": "uuid",
  "resume_id": "uuid",
  "position_id": "uuid",
  
  // Three Pillar Scores
  "traditional_score": 65,  // Keyword baseline
  "semantic_score": 72,     // Embedding similarity
  "capability_score": 82,   // AI reasoning
  
  // Components with Evidence
  "capability_components": {
    "domain_depth": { "score": 85, "evidence": "Led 3 Docker migrations" },
    "problem_solving": { "score": 78, "evidence": "Architected load balancer" },
    "collaboration": { "score": 82, "evidence": "Mentored 5 junior engineers" }
  },
  
  // Narrative Explanation
  "capability_narrative": "Strong backend engineer with proven Kubernetes experience and team leadership. Domain depth in distributed systems is excellent. Gap: limited AWS platform experience—manageable with 2-week ramp-up.",
  
  // Governance Results
  "governance_fidelity": {
    "passed": true,
    "unsupported_claims": [],
    "observations": "All claims grounded in resume"
  },
  "governance_coherence": {
    "passed": true,
    "observations": "Score aligns with components and narrative"
  },
  "governance_consistency": {
    "passed": true,
    "deviation": 0.05,
    "observations": "Scoring is fair relative to evidence"
  },
  
  // Decision
  "decision_type": "approval",
  "human_review_required": false,
  "score_delta": 17  // capability - traditional
}
```

---

### 4. JD Alignment to Similar Online JDs
**Capability**: Detect requirement drift, compare to market standards

**Testing**:
1. **Get JD Requirements** from assessment
2. **Analyze Against Industry** patterns
3. **Detect Drift** from typical specs
4. **Get Recommendations** for alignment

**Expected Insights**:
- "This JD asks for 10 years Kubernetes—most similar roles ask 3-5"
- "Required skills align with market 82% (good)"
- "Seniority requirement is 15% above average for this role level"

---

### 5. CV Positioning Against Similar JDs
**Capability**: Show how candidate's CV translates across roles

**Endpoints to Test**:
```
POST   /api/v1/candidates/capability-translation
GET    /api/v1/candidates/capability-translation/{translation_id}
```

**Test Flow**:
1. **Select CV** (parsed profile)
2. **Select Target JD** (different from assessment)
3. **Run Translation** → Re-express skills in target language
4. **Get Results** → How candidate looks for THIS role

**Expected Output**:
```json
{
  "source_jd": { "title": "DevOps Engineer", "company": "TechCorp" },
  "target_jd": { "title": "Site Reliability Engineer", "company": "CloudCo" },
  
  "summary": "Candidate's DevOps background translates well to SRE focus. Strong infrastructure and incident response signals. Would need ramp-up on SRE-specific observability stack.",
  
  "translated_bullets": [
    {
      "original": "Built CI/CD pipeline with Jenkins and Docker",
      "translated": "Architected and maintained deployment infrastructure using containerization and orchestration technologies (translatable to Kubernetes environments)",
      "evidence_strength": "HIGH",
      "grounding": "Resume shows 4 years Docker/Jenkins experience"
    },
    {
      "original": "Reduced deployment time from 2 hours to 15 minutes",
      "translated": "Demonstrated measurable infrastructure reliability improvements (relevant to SRE efficiency metrics)",
      "evidence_strength": "HIGH",
      "grounding": "Directly supports SRE velocity focus"
    }
  ],
  
  "fit_score": 78,
  "readiness": "STRETCH",  // Can do it but needs support
  "upskilling_gap": [
    {
      "capability": "Observability/Monitoring (Datadog/New Relic)",
      "why": "SRE role deeply focuses on metrics-driven incident response",
      "how": "2-3 week hands-on with SRE team; relevant courses available"
    }
  ]
}
```

---

### 6. CV Improvement Recommendations
**Capability**: Actionable, grounded guidance

**Test Flow**:
1. **Get CV Assessment** results
2. **Extract Improvement Suggestions**
3. **Get Detailed Recommendations** by area

**Expected Output**:
```json
{
  "improvement_suggestions": [
    {
      "category": "Skills Gap",
      "current": "No Kubernetes experience",
      "target": "Intermediate Kubernetes",
      "priority": "HIGH",
      "action": "Complete Linux Foundation Kubernetes Admin course (40 hours)",
      "timeline": "8 weeks self-paced",
      "evidence_benefit": "Would move capability_score from 82 → 91 (autonomy threshold)"
    },
    {
      "category": "Credential Substitution",
      "current": "No cloud certifications",
      "alternative": "Your shipped products + GitHub contributions show cloud design ability",
      "recommendation": "Add AWS certification OR create public portfolio of cloud projects",
      "impact": "Significant (addresses credential proxy requirement)"
    },
    {
      "category": "Resume Rewriting",
      "current": "Mentions 'built infrastructure tools'",
      "rewritten": "Architected multi-region Kubernetes infrastructure supporting 10M+ daily requests",
      "grounding": "Your resume says you worked on this; just be more specific",
      "impact": "Could move traditional_score from 65 → 75"
    }
  ],
  
  "reworded_cv_sections": {
    "DevOps Experience": "Your actual resume text → More compelling version grounded in your work"
  },
  
  "trajectory_analysis": {
    "direction": "ascending",
    "velocity": "moderate",
    "domain_crossings": [
      { "from": "Backend Engineering", "to": "Infrastructure", "impact": "Positive (broader perspective)" }
    ]
  }
}
```

---

## 🛡️ Governance & Compliance Testing

### Fraud Detection Test
**Endpoints**:
```
GET    /api/v1/assessments/{assessment_id}/governance
```

**Test Scenario**: Upload CV with embellished claims
- Expected: `governance_fidelity.passed = false`
- Expected: `governance_fidelity.unsupported_claims` populated
- Result: `status = "flagged_for_review"`

### Reproducibility Test
**Endpoints**:
```
GET    /api/v1/compliance/assessment/{assessment_id}/verify-reproducibility
```

**Expected**: Same resume + JD → Same score (deterministic)

### Audit Trail Test
**Endpoints**:
```
GET    /api/v1/compliance/assessment/{assessment_id}/audit-trail
```

**Expected**: Full history of assessment, all gate results, decision metadata

---

## 📊 Test Data You Can Use

### Sample CV (Test)
```
Name: Jane Engineer
Experience:
  - Senior Backend Engineer at TechCorp (2020-present, 3 years)
    • Led Kubernetes infrastructure (15 microservices)
    • Built CI/CD pipeline (Jenkins, Docker)
    • Mentored 3 junior engineers
    
  - Software Engineer at StartupXYZ (2018-2020, 2 years)
    • Full-stack web application development
    • Python, JavaScript, PostgreSQL
    
Skills:
  - Kubernetes, Docker, AWS, Python, Go, PostgreSQL
  - CI/CD, Monitoring, Incident Response
  
Education:
  - BS Computer Science, State University (2018)
```

### Sample JD (Test)
```
Title: Senior DevOps Engineer

Required:
  - 5+ years infrastructure/DevOps
  - Kubernetes (production experience)
  - AWS (EC2, RDS, ECS)
  
Preferred:
  - Team leadership
  - Incident response
  - Cost optimization
  
Nice to Have:
  - Terraform, Go programming
```

---

## 🧪 Quick Test Script

```bash
# 1. Health check
curl http://localhost:8000/docs

# 2. List assessments
curl http://localhost:8000/api/v1/assessments -H "Authorization: Bearer YOUR_TOKEN"

# 3. Create assessment
curl -X POST http://localhost:8000/api/v1/assessments \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "resume_id": "uuid",
    "position_id": "uuid"
  }'

# 4. Get results with governance
curl http://localhost:8000/api/v1/assessments/{assessment_id}/governance \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 📝 Expected Test Results

| Capability | Endpoint | Status | Evidence |
|------------|----------|--------|----------|
| CV Assessment | `/api/v1/candidates/cv-analysis` | ✅ Enabled | Gap analysis + suggestions |
| JD Analysis | `/api/v1/positions` + `/api/v1/agents/jd/*` | ✅ Enabled | Quality score + issues |
| CV-to-JD Fit | `/api/v1/assessments` | ✅ Enabled | 3-pillar scores + narrative |
| Governance | `/api/v1/assessments/{id}/governance` | ✅ Enabled | 4-gate results |
| Fraud Detection | `governance_fidelity` gate | ✅ Enabled | Unsupported claims list |
| Reproducibility | `/api/v1/compliance/.../verify-reproducibility` | ✅ Enabled | Deterministic hashing |
| Audit Trail | `/api/v1/compliance/.../audit-trail` | ✅ Enabled | Full decision history |
| CV Positioning | `/api/v1/candidates/capability-translation` | ✅ Enabled | Translation + fit score |
| Improvement Tips | `/api/v1/candidates/cv-analysis/{id}` | ✅ Enabled | Actionable suggestions |

---

## 🎤 What to Demo

### 5-Minute Quick Demo
1. **Upload Sample CV** → Show parsing
2. **Create Assessment** → Run against sample JD
3. **Show 3-Pillar Scores** → Traditional (65) vs Semantic (72) vs Capability (82)
4. **Show Governance** → "All gates passed, ready for autonomy"
5. **Show Improvement Suggestions** → "Here's how this candidate gets to 90+"

### 15-Minute Deep Demo
1. All above +
2. **Show Fraud Detection** → Upload embellished CV, show fidelity gate failure
3. **Show Audit Trail** → Every decision tracked for compliance
4. **Show CV Translation** → Same candidate, different JD, different narrative
5. **Show JD Analysis** → Quality issues + drift detection

### Full Demo (30+ Minutes)
1. All above +
2. **Live Governance Configuration** → Show thresholds
3. **Batch Processing** → Multiple CVs/JDs
4. **Compliance Package Export** → For auditors
5. **Analytics Dashboard** → Patterns across assessments

---

## ✅ Pre-Meeting Checklist

- [x] Backend running (http://localhost:8000)
- [x] Frontend running (http://localhost:3000)
- [x] PostgreSQL ready
- [x] Redis ready
- [x] All 15 prompt templates loaded
- [x] Governance gates configured
- [x] API documentation live at /docs
- [x] Test data ready
- [x] Audit trail tracking enabled
- [x] Encryption enabled (PII protected)

---

## 📞 Support During Demo

If you hit issues:

1. **API Health**: `curl http://localhost:8000/docs`
2. **Database**: `PGPASSWORD=truematch_dev psql -U truematch -h localhost -d truematch_dev -c "\dt"`
3. **Backend Logs**: `tail -f /tmp/truematch-backend.log`
4. **Frontend Logs**: `tail -f /tmp/truematch-frontend.log`

---

**Status**: 🟢 READY FOR PLUG & PLAY MEETING
