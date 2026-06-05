# TrueMatch Training Simulation System
## The Virtual Brain/Digital Assistant

**Status**: Design Document  
**Version**: 1.0  
**Date**: June 5, 2026  

---

## Executive Overview

The Training Simulation System is a **machine learning-driven digital assistant** that continuously learns from recruiter and candidate feedback to enhance CV-to-JD matching accuracy. It serves as:

- **For Recruiters**: Intelligent candidate sourcing & matching assistant
- **For Candidates**: Smart job discovery & career guidance tool
- **For Platform**: Self-improving matching engine that builds institutional knowledge

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    TRAINING SIMULATION SYSTEM                │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────┐    ┌──────────────────┐              │
│  │  Recruiter Flow  │    │  Candidate Flow  │              │
│  │                  │    │                  │              │
│  │ 1. Match JD to   │    │ 1. Submit CV     │              │
│  │    Candidates    │    │ 2. View Matched  │              │
│  │ 2. Review Matches│    │    Jobs          │              │
│  │ 3. Accept/Reject │    │ 3. Apply/Skip    │              │
│  │ 4. Provide       │    │ 4. Feedback on   │              │
│  │    Feedback      │    │    Matches       │              │
│  └──────────┬───────┘    └──────────┬───────┘              │
│             │                       │                      │
│             └───────────┬───────────┘                      │
│                         │                                  │
│             ┌───────────▼────────────┐                     │
│             │  FEEDBACK COLLECTION   │                     │
│             │  - Rating (1-5 stars)  │                     │
│             │  - Hire/No-Hire        │                     │
│             │  - Reasons (feedback)  │                     │
│             │  - Time to hire        │                     │
│             └───────────┬────────────┘                     │
│                         │                                  │
│             ┌───────────▼────────────┐                     │
│             │ TRAINING DATA PIPELINE │                     │
│             │ - Feature extraction   │                     │
│             │ - Pattern recognition  │                     │
│             │ - Credibility scoring  │                     │
│             │ - Capability mapping   │                     │
│             └───────────┬────────────┘                     │
│                         │                                  │
│             ┌───────────▼────────────┐                     │
│             │  VIRTUAL BRAIN ENGINE  │                     │
│             │ - Match optimization   │                     │
│             │ - Candidate profiling  │                     │
│             │ - Job clustering       │                     │
│             │ - Success prediction   │                     │
│             └───────────┬────────────┘                     │
│                         │                                  │
│             ┌───────────▼────────────┐                     │
│             │  INTELLIGENT MATCHING  │                     │
│             │ - Semantic matching    │                     │
│             │ - Capability mapping   │                     │
│             │ - Credential matching  │                     │
│             │ - Success prediction   │                     │
│             └───────────┬────────────┘                     │
│                         │                                  │
│        ┌────────────────┴────────────────┐                 │
│        │                                 │                 │
│   ┌────▼────┐                    ┌──────▼──────┐          │
│   │ Recruiter│                    │  Candidate   │          │
│   │ Dashboard│                    │  Dashboard   │          │
│   │ & Mobile │                    │  & Mobile    │          │
│   └──────────┘                    └──────────────┘          │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. Training Data Models

```python
# Training/Feedback Data
class TrainingFeedback(Base):
    """Captures recruiter/candidate feedback on matches"""
    id: UUID
    match_id: UUID  # Link to original match
    user_id: UUID  # Recruiter or candidate who provided feedback
    feedback_type: Enum  # "hire", "reject", "maybe", "interested", "not_interested"
    rating: int  # 1-5 stars
    comments: str  # Why did they accept/reject?
    time_to_action: int  # Seconds to decision
    outcome: str  # "hired", "rejected", "pending"
    created_at: datetime

# Learning Database
class CapabilityMapping(Base):
    """Maps CV keywords/phrases to specific capabilities"""
    id: UUID
    cv_keyword: str  # "Led cross-functional team"
    capability: str  # "Leadership"
    confidence: float  # 0-1 score
    frequency: int  # How many times seen in data
    feedback_count: int  # How many confirmations
    learned_at: datetime

class CredentialMapping(Base):
    """Maps credentials to job requirements"""
    id: UUID
    credential: str  # "BS Computer Science"
    requirement: str  # "Bachelor's degree in CS or related field"
    match_score: float  # 0-1
    alternative_matches: list  # Alternative credentials that also match
    industry: str  # Domain context
    learned_at: datetime

# Success Patterns
class SuccessPattern(Base):
    """Learned patterns for successful hires"""
    id: UUID
    job_id: UUID
    candidate_profile: dict  # Characteristics of successful hires
    capability_set: list  # Key capabilities needed
    credential_set: list  # Key credentials needed
    success_rate: float  # % of hires that succeeded (6mo+)
    sample_size: int  # Number of hires
    region: str  # Geographic context
    industry: str  # Industry context

# Training Progress
class TrainingProgress(Base):
    """Tracks model improvement over time"""
    id: UUID
    metric: str  # "match_accuracy", "hire_success", "user_satisfaction"
    value: float  # Current score
    baseline: float  # Starting score
    improvement: float  # % improvement
    samples: int  # Data points used
    period: str  # Weekly, monthly, etc
    created_at: datetime
```

### 2. Training Simulation Engine

```python
# Core Training Engine
class TrainingSimulationEngine:
    """
    Machine learning engine that learns from feedback
    to improve CV-to-JD matching
    """
    
    async def process_feedback(self, feedback: TrainingFeedback):
        """Process recruiter/candidate feedback"""
        # 1. Extract features from feedback
        # 2. Update capability mappings
        # 3. Update credential mappings
        # 4. Retrain matching model
        # 5. Calculate improvement metrics
        pass
    
    async def extract_capabilities(self, cv_text: str) -> dict:
        """Extract capabilities from CV using ML"""
        # 1. NLP parsing
        # 2. Keyword extraction
        # 3. Capability mapping
        # 4. Confidence scoring
        pass
    
    async def extract_requirements(self, jd_text: str) -> dict:
        """Extract requirements from job description"""
        # 1. Parse JD structure
        # 2. Identify requirements
        # 3. Categorize (must-have, nice-to-have)
        # 4. Map to capabilities
        pass
    
    async def calculate_match_score(
        self,
        cv_profile: dict,
        jd_profile: dict
    ) -> MatchResult:
        """
        Calculate intelligent match score considering:
        - Credential matching (20%)
        - Capability matching (60%)
        - Career trajectory (10%)
        - Success probability (10%)
        """
        credential_score = await self.match_credentials(...)
        capability_score = await self.match_capabilities(...)
        trajectory_score = await self.analyze_trajectory(...)
        success_prob = await self.predict_success(...)
        
        return MatchResult(
            overall_score=0.2*credential_score + 0.6*capability_score + 
                         0.1*trajectory_score + 0.1*success_prob,
            credential_match=credential_score,
            capability_match=capability_score,
            trajectory_match=trajectory_score,
            success_probability=success_prob,
            confidence=confidence_level
        )
    
    async def predict_success(
        self,
        candidate_profile: dict,
        job_profile: dict
    ) -> float:
        """Predict probability of successful hire (stays >6mo)"""
        # Uses learned success patterns
        pass
    
    async def recommend_candidates(
        self,
        jd_id: UUID,
        top_n: int = 10
    ) -> List[CandidateRecommendation]:
        """
        Recommend top candidates for a job using trained model
        """
        # 1. Load learned success patterns for this job type
        # 2. Score all candidates against learned patterns
        # 3. Rank by match + success probability
        # 4. Return top N with explanations
        pass
    
    async def recommend_jobs(
        self,
        candidate_id: UUID,
        top_n: int = 5
    ) -> List[JobRecommendation]:
        """
        Recommend top jobs for a candidate using trained model
        """
        # 1. Extract candidate capabilities/credentials
        # 2. Find jobs matching those capabilities
        # 3. Predict success probability for each
        # 4. Rank by match + success probability
        # 5. Provide career guidance
        pass
    
    async def get_training_insights(self) -> TrainingInsights:
        """
        Return insights on what the platform has learned
        """
        return TrainingInsights(
            top_capabilities_by_role={...},
            credential_effectiveness={...},
            success_factors={...},
            common_patterns={...},
            recommendations={...}
        )
```

### 3. Mobile APIs for Digital Assistant

```python
# Recruiter Mobile APIs
@router.post("/mobile/recruiter/match-candidates")
async def match_candidates_mobile(
    recruiter_id: UUID,
    jd_id: UUID,
    filters: dict = None,
    limit: int = 10
) -> List[CandidateMatch]:
    """
    Digital Assistant: Find candidates for a job
    Returns: Top matches with explanations
    """
    pass

@router.get("/mobile/recruiter/candidate/{candidate_id}/analysis")
async def get_candidate_analysis_mobile(
    candidate_id: UUID,
    jd_id: UUID = None
) -> CandidateAnalysis:
    """
    Digital Assistant: Deep dive on candidate
    Shows: Capabilities, credentials, fit explanation
    """
    pass

@router.post("/mobile/recruiter/feedback")
async def submit_match_feedback_mobile(
    match_id: UUID,
    decision: str,  # "hire", "reject", "maybe"
    rating: int,
    comments: str = None
) -> FeedbackResponse:
    """
    Digital Assistant learns: Record hiring decision
    """
    pass

# Candidate Mobile APIs
@router.post("/mobile/candidate/match-jobs")
async def match_jobs_mobile(
    candidate_id: UUID,
    filters: dict = None,
    limit: int = 5
) -> List<JobMatch>:
    """
    Digital Assistant: Find jobs for candidate
    Returns: Top matches with explanations
    """
    pass

@router.get("/mobile/candidate/job/{job_id}/suitability")
async def get_job_suitability_mobile(
    candidate_id: UUID,
    job_id: UUID
) -> JobSuitabilityAnalysis:
    """
    Digital Assistant: How suitable is this job?
    Shows: Gap analysis, skill mapping, growth opportunity
    """
    pass

@router.post("/mobile/candidate/feedback")
async def submit_job_feedback_mobile(
    job_id: UUID,
    decision: str,  # "applied", "interested", "not_interested"
    rating: int,
    comments: str = None
) -> FeedbackResponse:
    """
    Digital Assistant learns: Record candidate interest
    """
    pass

# Shared Analytics APIs
@router.get("/mobile/assistant/training-progress")
async def get_training_progress_mobile() -> TrainingProgress:
    """
    Show: How smart is the digital assistant?
    Metrics: Match accuracy, success rate, user satisfaction
    """
    pass

@router.get("/mobile/assistant/insights")
async def get_assistant_insights_mobile() -> AssistantInsights:
    """
    Show: What has the assistant learned?
    Topics: Top skills, salary ranges, success factors
    """
    pass
```

---

## Key Features

### 1. For Recruiters (Digital Sourcing Assistant)
- **Intelligent Candidate Sourcing**: "Find candidates like [successful hire]"
- **Match Explanations**: "This candidate is a good fit because..."
- **Success Prediction**: "92% chance this hire will last 18+ months"
- **Feedback Loop**: Rate decisions to improve future matches
- **Trend Analysis**: "These skills are getting harder to find"

### 2. For Candidates (Digital Job Advisor)
- **Smart Job Discovery**: "Top 5 jobs for your profile"
- **Gap Analysis**: "You're 85% qualified; missing X skill"
- **Career Guidance**: "This role will build your X capability"
- **Success Insights**: "This company has 90% retention for your role"
- **Learning Path**: "To land [target role], develop [skills]"

### 3. For Platform (Virtual Brain)
- **Self-Improvement**: Accuracy improves with each feedback
- **Pattern Recognition**: Learns what makes successful hires
- **Market Intelligence**: Understands evolving market demands
- **Predictive Models**: Anticipates market trends
- **Institutional Knowledge**: Builds over time across all users

---

## Implementation Phases

### Phase 1: Foundation (Weeks 1-2)
```
✓ Database models for training data
✓ Training simulation engine core
✓ Feedback collection endpoints
✓ Basic mobile APIs
```

### Phase 2: Intelligence (Weeks 3-4)
```
✓ Capability extraction (NLP)
✓ Credential mapping engine
✓ Success pattern learning
✓ Match score optimization
```

### Phase 3: Assistant Features (Weeks 5-6)
```
✓ Candidate recommendation engine
✓ Job recommendation engine
✓ Explanation generation
✓ Gap analysis tool
```

### Phase 4: Analytics & Optimization (Weeks 7-8)
```
✓ Training progress dashboard
✓ Insight generation
✓ Performance metrics
✓ Model optimization
```

---

## Data Flow Example

### Recruiter Training Flow
```
1. Recruiter posts Job Description
   → System extracts requirements & maps to capabilities
   → Learning engine identifies success patterns

2. System recommends candidates
   → Shows top matches with confidence scores
   → Explains why each candidate is suitable

3. Recruiter reviews, accepts/rejects candidates
   → Provides feedback: "Hired", "Not interested", rating
   → Comments: "Great technical skills but weak leadership"

4. System learns from feedback
   → Updates capability mappings
   → Adjusts success patterns
   → Improves future recommendations

5. After 6+ months, tracks hiring outcome
   → "Employee stayed 18+ months" = Successful pattern
   → Updates success probability model
   → Becomes more accurate over time
```

### Candidate Training Flow
```
1. Candidate uploads CV
   → System extracts capabilities & credentials
   → Maps to job requirements

2. System recommends jobs
   → Shows top 5 matches based on capabilities
   → Predicts success for each
   → Explains gaps (if any)

3. Candidate applies/skips, provides feedback
   → "Applied" or "Not interested"
   → Rating: "This was a great fit"
   → Comments: "Perfect for my career stage"

4. System learns from feedback
   → Understands candidate preferences
   → Learns what motivates decisions
   → Improves personalization

5. Tracks outcomes
   → If hired: "Happy?" after 3/6/12 months
   → Learns what makes good career moves
   → Becomes better career advisor
```

---

## Success Metrics

### Accuracy Metrics
- **Match Accuracy**: % of matches that lead to hire
- **Candidate Satisfaction**: Avg rating of matches (1-5)
- **Time-to-Hire**: Average days from match to offer
- **False Positive Rate**: Rejections we predicted as good fits

### Learning Metrics
- **Training Data Points**: # of feedback samples
- **Model Improvement**: % increase in accuracy over time
- **Confidence Level**: Average prediction confidence
- **Pattern Discovery**: # of learned success patterns

### Business Metrics
- **Hire Success Rate**: % of hires retained 6+ months
- **Career Move Success**: % of candidates satisfied at 6mo
- **Time-Saved**: Hours saved by recruiter on sourcing
- **User Retention**: % of users who return monthly

---

## Technical Stack

### ML/AI Components
- **NLP**: spacy, transformers for text analysis
- **Feature Extraction**: Custom algorithms for capabilities/credentials
- **ML Models**: scikit-learn for prediction
- **Vector DB**: Pinecone/Weaviate for semantic search
- **LLM**: Claude API for explanation generation

### Backend Integration
- **Async Processing**: Celery for training tasks
- **Real-time Updates**: WebSocket for match updates
- **Caching**: Redis for model caching
- **Analytics**: TimescaleDB for metrics

### Frontend
- **Web Dashboard**: React components for analytics
- **Mobile APIs**: REST endpoints for iOS/Android
- **Real-time**: WebSocket for live recommendations

---

## Security & Privacy

- **Data Anonymization**: Remove PII from training data
- **Consent Management**: Users opt-in to training
- **Model Explainability**: Transparent decision explanations
- **Fairness Checks**: Monitor for bias in recommendations
- **Audit Trail**: Track all feedback and model changes

---

## Competitive Advantage

This system creates a **self-improving AI** that:

1. **Gets Smarter Over Time**: Improves accuracy with each hire
2. **Understands Context**: Learns local market realities
3. **Predicts Success**: Not just matches, but success probabilities
4. **Explains Decisions**: "Why" behind every recommendation
5. **Helps Both Sides**: Recruiter sourcing + Candidate job finding
6. **Builds Loyalty**: Becomes trusted advisor over time

---

## Next Steps

1. Review & approve this design
2. Begin Phase 1 implementation (database + engine)
3. Integrate with existing CV/JD analysis
4. Build mobile endpoints
5. Deploy learning infrastructure
6. Start collecting training data

**Timeline**: 8 weeks to full implementation
**ROI**: Measurable improvement in hire success rate within 4 weeks

---

## Conclusion

The Training Simulation System transforms TrueMatch from a **matching platform** into a **self-improving digital assistant** that serves as:
- **Recruiter's intelligent sourcing partner**
- **Candidate's career advisor**
- **Market intelligence engine**

This is the "virtual brain" that continuously learns and improves, becoming more valuable with each user interaction.

