# Persona Enhancement System - Implementation Guide

## Overview

This guide explains how to integrate the new Persona System into the existing TrueMatch platform, enabling agents to adopt specific personas based on user objectives and optimize user interactions.

---

## What's New

### Two New Modules Added

1. **`persona_system.py`** - Core persona definitions and detection system
   - Defines personas for each role/objective combination
   - Detects user objectives from conversation
   - Manages persona selection logic

2. **`persona_integration.py`** - Integration layer for existing agents
   - Connects personas to agents
   - Adapts responses based on persona
   - Loads persona-specific context

### Key Features

✅ **Objective Detection** - Automatically detects what users are trying to accomplish  
✅ **Dynamic Persona Selection** - Chooses best persona for the task  
✅ **System Prompt Injection** - Embeds persona into agent instructions  
✅ **Context Loading** - Fetches persona-relevant data  
✅ **Response Adaptation** - Formats responses based on conversation mode  
✅ **Analytics** - Tracks persona effectiveness  

---

## Available Personas

### Candidate Personas

#### 1. **Career Coach** 
- **Objective**: Career exploration, long-term planning
- **Approach**: Supportive, strategic, probing questions
- **Best for**: Users exploring career options, career transitions, long-term goals
- **Key Techniques**: Active listening, strengths-based approach, market analysis, strategic planning

#### 2. **Interview Coach**
- **Objective**: Interview preparation, practice
- **Approach**: Direct, confidence-building, practice-oriented
- **Best for**: Users preparing for specific interviews, mock interview practice
- **Key Techniques**: Mock interviewing, STAR method, company research, handling difficult questions

#### 3. **Application Optimizer**
- **Objective**: Resume/CV optimization, improving applications
- **Approach**: Analytical, detailed, improvement-focused
- **Best for**: Users optimizing resumes, tailoring applications, improving callback rates
- **Key Techniques**: ATS keyword optimization, achievement quantification, tailoring strategy

### Recruiter Personas

#### 1. **Talent Scout**
- **Objective**: Candidate sourcing, finding talent
- **Approach**: Proactive, strategic, relationship-focused
- **Best for**: Building candidate pipelines, finding passive talent, market intelligence
- **Key Techniques**: Boolean search, passive candidate engagement, niche talent identification

#### 2. **Hiring Manager Assistant**
- **Objective**: Candidate evaluation and screening
- **Approach**: Analytical, thorough, decision-focused
- **Best for**: Evaluating candidates, identifying red flags, structuring assessments
- **Key Techniques**: Structured evaluation, red flag detection, interview question generation

#### 3. **Pipeline Manager**
- **Objective**: Pipeline optimization, hiring metrics
- **Approach**: Data-driven, process-focused, improvement-oriented
- **Best for**: Optimizing hiring efficiency, analyzing metrics, bottleneck removal
- **Key Techniques**: Metrics analysis, bottleneck identification, process optimization

---

## Implementation Steps

### Step 1: Update Imports in Agent Classes

In `candidate_agent.py`:
```python
from app.agents.persona_system import PersonaSystem, UserRole
from app.agents.persona_integration import (
    CandidateAgentWithPersona,
    PersonaContextLoader,
    PersonaAnalytics
)
```

In `recruiter_agent.py`:
```python
from app.agents.persona_system import PersonaSystem, UserRole
from app.agents.persona_integration import (
    RecruiterAgentWithPersona,
    PersonaContextLoader,
    PersonaAnalytics
)
```

### Step 2: Add Persona Mixin to Agent Classes

**Before:**
```python
class CandidateAgent(EnhancedBaseAgent):
    def __init__(self, ...):
        super().__init__(...)
        # ... existing code ...
```

**After:**
```python
class CandidateAgent(PersonaEnhancedAgentMixin, EnhancedBaseAgent):
    def __init__(self, db_session, ...):
        super().__init__(...)
        # Initialize persona system
        context_loader = PersonaContextLoader(db_session)
        self.set_context_loader(context_loader)
        self.analytics = PersonaAnalytics(db_session)
        # ... existing code ...
```

### Step 3: Update respond() Method

**Before:**
```python
async def respond(self, message: str, session_id: str, user_id: str, **kwargs):
    # ... existing response logic ...
    return response
```

**After:**
```python
async def respond(self, message: str, session_id: str, user_id: str, **kwargs):
    # Use persona-enhanced response
    result = await self.respond_with_persona(
        message=message,
        user_id=user_id,
        session_id=session_id,
        chat_mode=kwargs.get('chat_mode', 'general')
    )
    
    # Track persona usage for analytics
    context = self.persona_system.active_contexts.get(user_id)
    if context and context.active_persona:
        await self.analytics.track_persona_usage(
            user_id=user_id,
            persona_id=context.active_persona.id,
            objective=context.current_objective or "unknown",
            mode=context.conversation_mode.value,
            effectiveness_score=0.85  # Calculate based on user engagement
        )
    
    return result
```

### Step 4: Update Chat API Endpoint

In `api/v1/chat.py`:

**Before:**
```python
@router.post("/")
async def send_message(session_id: str, message: str, ...):
    agent = get_agent_for_user(user_role)
    response = await agent.respond(message, session_id, user_id)
    return response
```

**After:**
```python
@router.post("/")
async def send_message(session_id: str, message: str, explicit_objective: Optional[str] = None, ...):
    agent = get_agent_for_user(user_role)
    
    # Pass explicit objective if user specifies it
    if explicit_objective:
        # Store in session context for persona detection
        session_context.explicit_objective = explicit_objective
    
    response = await agent.respond(message, session_id, user_id)
    
    # Return persona information with response
    return {
        "message": response.get("response"),
        "actions": response.get("actions"),
        "persona": response.get("persona"),  # New: persona information
        "mode": response.get("mode"),         # New: conversation mode
        "objective": response.get("objective") # New: detected objective
    }
```

---

## Usage Examples

### Example 1: Candidate Job Search

**User Message**: "I'm looking for a new job in tech startups, but I'm not sure how to position my resume"

**System Detection**:
- Objective: `application_optimization` + `job_search`
- Persona Selected: `Application Optimizer`
- Mode: `analytical`

**Response**:
```
### Application Optimizer - Resume Strategist

Based on your goal of landing roles in tech startups, here's how to position your resume:

1. **ATS Optimization** (Most important for startup roles):
   - Keywords to include: "agile", "rapid prototyping", "startup mentality", "lean methodology"
   - Structure: Put most recent and relevant startup experience at top
   
2. **Achievements to Highlight** (What startups care about):
   - Growth metrics: "Grew user base from X to Y"
   - Efficiency gains: "Reduced onboarding time by 40%"
   - Innovation: "Led implementation of new feature that increased engagement"

3. **Tailoring by Startup Type**:
   - Early-stage: Emphasize scrappiness, versatility, learning ability
   - Growth-stage: Focus on scaling experience and metrics

[Action: Analyze your current resume against startup job descriptions]
```

### Example 2: Recruiter Candidate Screening

**User Message**: "I need help evaluating this candidate - great experience but seems overqualified"

**System Detection**:
- Objective: `candidate_screening`
- Persona Selected: `Hiring Manager Assistant`
- Mode: `analytical`

**Response**:
```
### Hiring Manager Assistant - Candidate Evaluation Expert

Overqualification is a common concern. Let me help you evaluate this systematically:

1. **Assess True Risk Level**:
   - Question: Is this person overqualified or just well-experienced?
   - Risk indicators: Previous job-hopping, expressions of boredom, salary expectations misalignment
   - Growth potential: Could they grow into more senior roles with you?

2. **Strengths of Having an Overqualified Candidate**:
   - Brings expertise that could elevate team
   - Less training required
   - Strong foundation for leadership development

3. **Red Flags to Investigate**:
   - Why are they interested in "stepping back" in responsibilities?
   - What's their long-term career goal with this role?
   - Will they get bored and leave quickly?

[Recommended Interview Questions to Ask]
- "What attracted you to this role specifically?"
- "How do you see this role fitting into your 3-year career plan?"
- "What would make you want to stay in this role long-term?"
```

### Example 3: Recruiter Pipeline Analysis

**User Message**: "Why is our hiring taking so long? We've been open for 45 days"

**System Detection**:
- Objective: `pipeline_management`
- Persona Selected: `Pipeline Manager`
- Mode: `analytical`

**Response**:
```
### Pipeline Manager - Hiring Pipeline Strategist

45 days is above the typical tech industry average of 35-40 days. Let's identify your bottlenecks:

**Pipeline Analysis Needed**:
1. How many candidates in each stage?
2. Average time per stage (source → screen → interview → offer)
3. Conversion rates between stages

**Common Bottlenecks at 45 days**:
- Sourcing (0-14 days): Can't find qualified candidates
- Screening (14-21 days): Large candidate pool requires long review
- Interview (21-35 days): Multiple interview rounds, coordination delays
- Decision (35-45 days): Slow hiring team response

**Optimization Recommendations**:
- Add pre-screen phone calls (15 min) to reduce in-person interviews
- Implement "interview committee" to parallel interview tracks
- Set clear decision deadlines (24-48 hours after last interview)
- Create candidate drop-off report to find leakage points

[Data dashboard showing: Current pipeline by stage, velocity, bottleneck analysis]
```

---

## Objective Detection Keywords

The system automatically detects user objectives from keywords in their messages.

### Candidate Objectives

| Objective | Keywords |
|-----------|----------|
| Career Exploration | career path, where should i, what roles, industry, transition, explore |
| Interview Prep | interview, mock interview, preparation, practice, prepare for |
| Job Search | job search, looking for, find jobs, apply to, job hunting |
| Application Optimization | resume, cv, cover letter, application, optimize, improve, ats |
| Skill Development | skill, learn, training, course, certification, upskill |
| Salary Negotiation | salary, compensation, offer, negotiate, benefits, package |

### Recruiter Objectives

| Objective | Keywords |
|-----------|----------|
| Candidate Sourcing | find, source, talent, candidates, pool, recruit, passive, active |
| Candidate Screening | evaluate, assess, screen, review, fit, strengths, concerns, red flags |
| Hiring Decision | hire, offer, reject, decision, move forward, advance, next step |
| Interview Scheduling | schedule, interview, calendar, meeting, when, availability |
| Pipeline Management | pipeline, metrics, funnel, conversion, time to hire, analytics |
| JD Improvement | job description, jd, requirements, improve, rewrite, keywords |

---

## Conversation Modes

The system also detects conversation mode based on user message characteristics:

| Mode | Use Case | Triggers |
|------|----------|----------|
| **General** | Default mode | No specific indicators |
| **Expert** | Deep technical discussion | deep dive, detailed, comprehensive, advanced |
| **Supportive** | Coaching/mentoring | help, support, coach, mentor, struggling |
| **Analytical** | Data-driven analysis | data, metrics, analyze, statistics, numbers |
| **Strategic** | High-level planning | strategy, long term, planning, roadmap, vision |

---

## Configuration & Customization

### Customizing System Prompts

Each persona has a `system_prompt_fragment` that can be customized in the database:

```python
# In database or config
AgentConfig(
    agent_type="candidate",
    role="application_optimizer",
    instructions="""You are a resume optimization expert...
    [custom instructions]
    """
)
```

### Adding New Personas

To add a new persona:

1. **Define in PersonaLibrary**:
```python
class PersonaLibrary:
    NEW_PERSONA: PersonaProfile = PersonaProfile(
        id="new_persona_id",
        name="New Persona Name",
        role=UserRole.candidate,
        # ... other fields
    )
```

2. **Update objective detection**:
```python
CANDIDATE_OBJECTIVE_KEYWORDS = {
    CandidateObjective.new_objective: [
        "keyword1", "keyword2", ...
    ],
}
```

3. **Update _select_persona()**:
```python
def _select_persona(self, user_role: UserRole, objective: Optional[str]):
    if objective == CandidateObjective.new_objective.value:
        return PersonaLibrary.NEW_PERSONA
```

---

## Database Schema Changes

Add these tables to track persona usage:

```sql
CREATE TABLE persona_usage_log (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    persona_id VARCHAR NOT NULL,
    objective VARCHAR,
    conversation_mode VARCHAR,
    effectiveness_score FLOAT,
    created_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES "user"(id)
);

CREATE TABLE persona_effectiveness (
    id UUID PRIMARY KEY,
    persona_id VARCHAR NOT NULL,
    user_id UUID,
    metric_type VARCHAR,  -- "callback_rate", "job_landing", "interview_success", etc.
    value FLOAT,
    period_start DATE,
    period_end DATE,
    created_at TIMESTAMP
);
```

---

## Testing Persona System

### Unit Tests

```python
def test_objective_detection():
    msg = "I have an interview next week and I'm nervous"
    objective = PersonaDetector.detect_objective(
        UserRole.candidate,
        msg
    )
    assert objective == CandidateObjective.interview_prep.value

def test_persona_selection():
    system = PersonaSystem()
    persona = system.get_appropriate_persona(
        user_id="user123",
        user_role=UserRole.candidate,
        message="Help me prepare for my interview"
    )
    assert persona.id == "interview_coach"

def test_response_adaptation():
    persona = PersonaLibrary.INTERVIEW_COACH
    original = "Here are some interview tips..."
    adapted = PersonaResponseAdapter.adapt_response_format(
        original,
        persona,
        ConversationMode.supportive
    )
    assert "Success Partner" in adapted
```

### Integration Tests

```python
async def test_candidate_agent_with_persona():
    agent = CandidateAgent(db_session)
    response = await agent.respond_with_persona(
        message="Help me get better at interviews",
        user_id="user123",
        session_id="session456"
    )
    
    assert response["persona"]["name"] == "Interview Coach"
    assert "Expert Deep Dive" in response["response"]
```

---

## Monitoring & Analytics

### Key Metrics to Track

1. **Persona Usage**: Which personas are most used?
2. **Effectiveness by Persona**: Which personas lead to better outcomes?
3. **Objective Distribution**: What are users trying to accomplish?
4. **Mode Distribution**: Which conversation modes are most common?
5. **Engagement**: Do persona-aware responses increase engagement?

### Dashboard Queries

```python
# Most used personas
SELECT persona_id, COUNT(*) as usage_count
FROM persona_usage_log
WHERE created_at > NOW() - INTERVAL 30 DAY
GROUP BY persona_id
ORDER BY usage_count DESC;

# Persona effectiveness
SELECT p.persona_id, AVG(p.effectiveness_score) as avg_effectiveness
FROM persona_usage_log p
GROUP BY p.persona_id;

# Objective distribution
SELECT objective, COUNT(*) as count
FROM persona_usage_log
GROUP BY objective
ORDER BY count DESC;
```

---

## Migration Path

### Phase 1: Add to CandidateAgent (Week 1)
- Implement persona system for candidate chat
- Test with 10% of candidate traffic
- Monitor objective detection accuracy

### Phase 2: Add to RecruiterAgent (Week 2)
- Implement persona system for recruiter chat
- Test with recruiter beta group
- Collect effectiveness metrics

### Phase 3: Optimize (Week 3+)
- Analyze persona effectiveness
- Refine objective detection
- Add new personas based on usage patterns
- A/B test response adaptations

---

## Expected Outcomes

### For Candidates
✅ More targeted career advice based on their actual goals  
✅ Better interview preparation with persona-specific coaching  
✅ Improved resume optimization with strategic guidance  
✅ Increased confidence through supportive personalized interaction  

### For Recruiters
✅ Better candidate evaluation frameworks  
✅ Data-driven pipeline optimization  
✅ Strategic sourcing guidance  
✅ Faster hiring cycles through objective-specific assistance  

### For Platform
✅ Higher user engagement and satisfaction  
✅ Better outcomes (job placements, hires)  
✅ Data on what works (persona effectiveness)  
✅ Foundation for future AI enhancements  

---

## Support & Troubleshooting

### Issue: Objective not detected correctly

**Solution**: Check keyword list for objective. Add missing keywords if needed.

```python
# Add keywords to CANDIDATE_OBJECTIVE_KEYWORDS
CandidateObjective.interview_prep: [
    "interview", "mock interview", "preparation",
    # Add new keywords:
    "behavioral questions", "technical assessment"
]
```

### Issue: Wrong persona selected

**Solution**: Check _select_persona() logic. May need to add objective-specific logic.

### Issue: Response format not matching persona

**Solution**: Update PersonaResponseAdapter._format_* methods to match expected format.

---

## Next Steps

1. ✅ Create persona definitions (Done)
2. ✅ Create integration layer (Done)
3. → Integrate into CandidateAgent (Implementation)
4. → Integrate into RecruiterAgent (Implementation)
5. → Add database tracking (Implementation)
6. → Deploy and monitor (Deployment)
7. → Optimize based on metrics (Optimization)

---

## Questions?

For questions about persona implementation or enhancements, refer to:
- `persona_system.py` - Persona definitions
- `persona_integration.py` - Integration patterns
- Individual agent files - Implementation examples
