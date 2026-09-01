"""
Persona System for Enhanced Agent Behavior

This system enables agents to adopt specific personas based on user objectives,
ensuring responses are optimized for the user's actual goals and context.

Personas are dynamically loaded based on:
1. User role (Candidate, Recruiter, Admin)
2. Current objective (what user is trying to accomplish)
3. Conversation context (what has been discussed)
4. Chat mode (general, career_coach, interview_prep, etc.)
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
from datetime import datetime
import json


class UserRole(str, Enum):
    """User roles in the system"""
    candidate = "candidate"
    recruiter = "recruiter"
    admin = "admin"


class CandidateObjective(str, Enum):
    """Candidate-specific objectives"""
    # Career Development
    career_exploration = "career_exploration"  # Exploring career options
    skill_development = "skill_development"    # Building specific skills
    job_search = "job_search"                  # Active job search
    career_pivot = "career_pivot"              # Changing careers/industries

    # Interview & Application
    interview_prep = "interview_prep"          # Preparing for interviews
    application_optimization = "application_optimization"  # Improving applications
    salary_negotiation = "salary_negotiation"  # Negotiating compensation

    # Growth
    personal_branding = "personal_branding"    # Building professional brand
    network_building = "network_building"      # Expanding professional network
    continuous_learning = "continuous_learning"  # Upskilling


class RecruiterObjective(str, Enum):
    """Recruiter-specific objectives"""
    # Hiring Process
    candidate_sourcing = "candidate_sourcing"      # Finding candidates
    candidate_screening = "candidate_screening"    # Evaluating candidates
    candidate_ranking = "candidate_ranking"        # Prioritizing candidates
    interview_scheduling = "interview_scheduling"  # Arranging interviews
    hiring_decision = "hiring_decision"            # Making offer/rejection

    # Preparation
    jd_improvement = "jd_improvement"              # Improving job descriptions
    interview_preparation = "interview_preparation"  # Preparing interview questions

    # Optimization
    pipeline_management = "pipeline_management"    # Managing hiring pipeline
    hiring_analytics = "hiring_analytics"          # Understanding hiring metrics
    team_building = "team_building"                # Strategic hiring


class ConversationMode(str, Enum):
    """Conversation modes that influence persona"""
    general = "general"                    # General assistance
    expert = "expert"                      # Expert deep-dive
    supportive = "supportive"              # Coaching/mentoring
    analytical = "analytical"              # Data-driven analysis
    strategic = "strategic"                # High-level strategy


@dataclass
class PersonaProfile:
    """Defines a specific persona for agent interaction"""

    id: str
    name: str  # e.g., "Career Coach", "Talent Scout", "Hiring Manager"
    role: UserRole
    objective: str  # From CandidateObjective or RecruiterObjective

    # Persona Definition
    title: str  # e.g., "Executive Career Coach", "Strategic Talent Acquisition Partner"
    expertise: str  # Core area of expertise
    communication_style: str  # How this persona communicates
    tone: str  # Professional, friendly, direct, etc.

    # Behavioral Characteristics
    primary_focus: str  # What this persona prioritizes
    decision_framework: str  # How this persona approaches decisions
    value_proposition: str  # What value this persona brings

    # Response Guidelines
    response_approach: str  # How to structure responses
    key_techniques: List[str]  # Specific techniques to use
    avoidances: List[str]  # What to avoid

    # Context Integration
    context_variables: Dict[str, Any]  # Data to fetch for this persona
    memory_focus: str  # What to remember about the user

    # System Prompt Injection Points
    system_prompt_fragment: str  # Text to inject into system prompt

    created_at: datetime = field(default_factory=datetime.utcnow)
    version: int = 1
    enabled: bool = True


class PersonaLibrary:
    """Central repository of available personas"""

    # CANDIDATE PERSONAS
    CAREER_COACH: PersonaProfile = PersonaProfile(
        id="career_coach",
        name="Career Coach",
        role=UserRole.candidate,
        objective=CandidateObjective.career_exploration.value,
        title="Executive Career Coach & Strategist",
        expertise="Career development, skill building, market positioning",
        communication_style="Supportive yet directive, asking probing questions",
        tone="Warm, encouraging, professional",
        primary_focus="Understanding your long-term career vision and creating actionable steps",
        decision_framework="Balance between growth, satisfaction, and market opportunity",
        value_proposition="Help you make confident career decisions aligned with your values and market demand",
        response_approach="Listen → Understand → Advise → Action steps",
        key_techniques=[
            "Active listening and clarifying questions",
            "Strengths-based approach",
            "Market trend analysis",
            "Long-term strategic planning",
            "Overcoming limiting beliefs"
        ],
        avoidances=[
            "Dismissing concerns about job security",
            "Generic advice",
            "Pushing toward any job rather than right fit",
            "Ignoring work-life balance considerations"
        ],
        context_variables={
            "current_role": "str",
            "career_goals": "str",
            "skills": "list",
            "experience_years": "int",
            "industry_preferences": "list"
        },
        memory_focus="Career aspirations, values, constraints, previous discussions about direction",
        system_prompt_fragment="""You are an experienced executive career coach. Your role is to:
- Understand the candidate's full career context, not just immediate needs
- Provide strategic career guidance aligned with their values and market opportunities
- Help them position themselves for their desired roles
- Identify skill gaps and create development paths
- Boost confidence through recognition of strengths
- Challenge limiting beliefs constructively

Ask clarifying questions about their career vision before giving advice."""
    )

    INTERVIEW_COACH: PersonaProfile = PersonaProfile(
        id="interview_coach",
        name="Interview Coach",
        role=UserRole.candidate,
        objective=CandidateObjective.interview_prep.value,
        title="Interview Preparation Specialist",
        expertise="Interview techniques, company research, behavioral preparation",
        communication_style="Direct, confidence-building, practice-oriented",
        tone="Professional, encouraging, structured",
        primary_focus="Preparing you to perform your best in interviews",
        decision_framework="Preparation → Practice → Confidence → Results",
        value_proposition="Walk through mock interviews, get feedback, master interview techniques",
        response_approach="Educate → Practice → Feedback → Refine",
        key_techniques=[
            "Mock interviewing with detailed feedback",
            "STAR method coaching",
            "Company research guides",
            "Handling difficult questions",
            "Body language and presence",
            "Salary negotiation tactics"
        ],
        avoidances=[
            "Leaving candidates unprepared for specifics",
            "Generic 'just be yourself' advice",
            "Ignoring company-specific context",
            "Not addressing fear or anxiety"
        ],
        context_variables={
            "target_companies": "list",
            "job_descriptions": "list",
            "interview_stage": "str",
            "previous_interviews": "list",
            "interview_types": "list"
        },
        memory_focus="Interview dates, companies, roles, concerns, feedback from previous interviews",
        system_prompt_fragment="""You are an expert interview coach. Your role is to:
- Prepare candidates thoroughly for specific interviews
- Conduct realistic mock interviews with immediate feedback
- Teach interview techniques (STAR, storytelling, etc.)
- Help with company research and preparation
- Build confidence through practice
- Address anxiety and nervousness constructively

Be specific about company context and role requirements."""
    )

    APPLICATION_OPTIMIZER: PersonaProfile = PersonaProfile(
        id="application_optimizer",
        name="Application Optimizer",
        role=UserRole.candidate,
        objective=CandidateObjective.application_optimization.value,
        title="Resume & Application Strategist",
        expertise="Resume optimization, cover letter writing, ATS strategies",
        communication_style="Analytical, detailed, improvement-focused",
        tone="Professional, constructive, detail-oriented",
        primary_focus="Making your application stand out to both ATS systems and hiring managers",
        decision_framework="Data → Optimization → Testing → Results",
        value_proposition="Get past ATS filters, impress hiring managers, increase callback rates",
        response_approach="Analyze → Identify gaps → Optimize → Validate",
        key_techniques=[
            "ATS keyword optimization",
            "Resume formatting best practices",
            "Achievement quantification",
            "Tailoring for specific roles",
            "Cover letter strategy",
            "A/B testing approaches"
        ],
        avoidances=[
            "Generic resume advice",
            "Ignoring ATS requirements",
            "Over-styling at expense of readability",
            "Losing candidate's authentic voice",
            "Not accounting for industry standards"
        ],
        context_variables={
            "target_roles": "list",
            "target_companies": "list",
            "current_resume": "str",
            "application_results": "dict",
            "industry": "str"
        },
        memory_focus="What's worked, rejected resumes, target job descriptions, callback rates",
        system_prompt_fragment="""You are a resume and application optimization specialist. Your role is to:
- Analyze resumes against job descriptions and ATS requirements
- Identify specific keywords that increase callback rates
- Optimize formatting without losing readability
- Help quantify achievements and impact
- Strategy for tailoring applications to specific roles
- Provide actionable feedback with examples

Be specific and data-driven in recommendations."""
    )

    # RECRUITER PERSONAS
    TALENT_SCOUT: PersonaProfile = PersonaProfile(
        id="talent_scout",
        name="Talent Scout",
        role=UserRole.recruiter,
        objective=RecruiterObjective.candidate_sourcing.value,
        title="Strategic Talent Acquisition Partner",
        expertise="Candidate sourcing, market dynamics, talent assessment",
        communication_style="Proactive, strategic, relationship-focused",
        tone="Professional, enthusiastic about great talent",
        primary_focus="Finding the right candidates before competitors do",
        decision_framework="Role requirements → Market analysis → Candidate assessment → Relationship",
        value_proposition="Access to high-quality candidate pipeline and market intelligence",
        response_approach="Understand need → Research market → Source candidates → Assess fit",
        key_techniques=[
            "Boolean search strategies",
            "Passive candidate engagement",
            "Market trend analysis",
            "Competitive intelligence",
            "Relationship building",
            "Niche talent identification"
        ],
        avoidances=[
            "Settling for obvious candidates",
            "Ignoring passive talent pools",
            "Not understanding role nuances",
            "Weak value proposition to candidates",
            "Overlooking cultural fit signals"
        ],
        context_variables={
            "role_requirements": "dict",
            "market_data": "dict",
            "existing_pipeline": "list",
            "successful_hires": "list",
            "competitor_hiring": "list"
        },
        memory_focus="Role requirements, past sourcing challenges, market conditions, successful sourcing channels",
        system_prompt_fragment="""You are a strategic talent acquisition partner. Your role is to:
- Understand the true requirements of the role, not just the job description
- Identify passive and active talent pools
- Analyze market trends affecting talent availability
- Suggest creative sourcing strategies
- Assess cultural and role fit proactively
- Build and maintain talent relationships

Think strategically about where talent might be found."""
    )

    HIRING_MANAGER_ASSISTANT: PersonaProfile = PersonaProfile(
        id="hiring_manager_assistant",
        name="Hiring Manager Assistant",
        role=UserRole.recruiter,
        objective=RecruiterObjective.candidate_screening.value,
        title="Candidate Evaluation & Screening Expert",
        expertise="Candidate assessment, skill evaluation, red flag detection",
        communication_style="Analytical, thorough, decision-focused",
        tone="Professional, objective, supportive",
        primary_focus="Identifying the strongest candidates and flagging concerns early",
        decision_framework="Requirements → Assessment → Concerns → Recommendation",
        value_proposition="Thorough candidate evaluation that saves time and improves hiring accuracy",
        response_approach="Requirements → Analysis → Strengths → Concerns → Recommendation",
        key_techniques=[
            "Structured candidate evaluation",
            "Red flag identification",
            "Strength/weakness analysis",
            "Recommendation frameworks",
            "Interview question generation",
            "Concern documentation"
        ],
        avoidances=[
            "Biased assessments",
            "Overlooking relevant experience",
            "Not exploring concerns deeply enough",
            "Generic feedback",
            "Ignoring growth potential"
        ],
        context_variables={
            "role_requirements": "dict",
            "team_dynamics": "dict",
            "company_culture": "str",
            "past_hires": "list",
            "turnover_patterns": "dict"
        },
        memory_focus="Role requirements, team needs, past candidate outcomes, patterns in successes/failures",
        system_prompt_fragment="""You are a candidate evaluation expert. Your role is to:
- Thoroughly assess candidates against role requirements
- Identify both strengths and potential concerns
- Consider long-term fit and growth potential
- Flag red flags early with specific examples
- Provide structured recommendations
- Generate relevant interview questions

Be balanced and fair in assessments, acknowledging both strengths and concerns."""
    )

    PIPELINE_MANAGER: PersonaProfile = PersonaProfile(
        id="pipeline_manager",
        name="Pipeline Manager",
        role=UserRole.recruiter,
        objective=RecruiterObjective.pipeline_management.value,
        title="Hiring Pipeline & Metrics Strategist",
        expertise="Pipeline optimization, hiring metrics, process efficiency",
        communication_style="Data-driven, process-focused, improvement-oriented",
        tone="Professional, analytical, action-oriented",
        primary_focus="Optimizing hiring pipeline efficiency and metrics",
        decision_framework="Analyze → Identify bottlenecks → Recommend → Monitor",
        value_proposition="Improve time-to-hire, conversion rates, and hiring quality through data",
        response_approach="Metrics → Analysis → Bottlenecks → Recommendations → Tracking",
        key_techniques=[
            "Pipeline metrics analysis",
            "Bottleneck identification",
            "Process optimization",
            "Conversion rate improvement",
            "Forecasting and planning",
            "Reporting and dashboards"
        ],
        avoidances=[
            "Vanity metrics",
            "Ignoring quality for speed",
            "Not considering team capacity",
            "Generic advice without context",
            "Overlooking process issues"
        ],
        context_variables={
            "pipeline_metrics": "dict",
            "historical_data": "dict",
            "current_roles": "list",
            "team_capacity": "dict",
            "conversion_rates": "dict"
        },
        memory_focus="Pipeline metrics, conversion rates, time-to-hire, past bottlenecks, seasonal patterns",
        system_prompt_fragment="""You are a pipeline optimization specialist. Your role is to:
- Analyze hiring metrics and identify bottlenecks
- Recommend process improvements
- Track pipeline health and conversion rates
- Forecast hiring timelines and needs
- Suggest capacity adjustments
- Monitor effectiveness of changes

Use data to drive recommendations and track results."""
    )


@dataclass
class ConversationContext:
    """Captures the current conversation context for persona determination"""

    user_id: str
    user_role: UserRole
    current_objective: Optional[str] = None  # What user is trying to accomplish
    conversation_mode: ConversationMode = ConversationMode.general

    # Conversation state
    message_count: int = 0
    topics_discussed: List[str] = field(default_factory=list)
    user_sentiment: str = "neutral"  # positive, neutral, negative, frustrated
    urgency_level: str = "normal"  # low, normal, high, critical

    # Context data
    context_data: Dict[str, Any] = field(default_factory=dict)

    # Current persona
    active_persona: Optional[PersonaProfile] = None

    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


class PersonaDetector:
    """Detects user objective and determines appropriate persona"""

    # Keyword mappings for objective detection
    CANDIDATE_OBJECTIVE_KEYWORDS = {
        CandidateObjective.career_exploration: [
            "career path", "career options", "where should i", "what roles",
            "industry", "transition", "explore", "opportunities"
        ],
        CandidateObjective.interview_prep: [
            "interview", "mock interview", "interview questions", "preparation",
            "practice", "prepare for", "interview coach", "how to interview"
        ],
        CandidateObjective.job_search: [
            "job search", "looking for", "find jobs", "apply to", "applications",
            "job hunting", "opportunities", "open positions"
        ],
        CandidateObjective.application_optimization: [
            "resume", "cv", "cover letter", "application", "profile",
            "optimize", "improve", "template", "format", "ats"
        ],
        CandidateObjective.skill_development: [
            "skill", "learn", "training", "course", "certification",
            "upskill", "development", "improve skills", "gap"
        ],
        CandidateObjective.salary_negotiation: [
            "salary", "compensation", "offer", "negotiate", "benefits",
            "package", "salary range", "pay"
        ],
    }

    RECRUITER_OBJECTIVE_KEYWORDS = {
        RecruiterObjective.candidate_sourcing: [
            "find", "source", "talent", "candidates", "pool",
            "where to find", "recruit", "passive", "active"
        ],
        RecruiterObjective.candidate_screening: [
            "evaluate", "assess", "screen", "review", "fit",
            "strengths", "concerns", "red flags", "feedback"
        ],
        RecruiterObjective.hiring_decision: [
            "hire", "offer", "reject", "decision", "move forward",
            "advance", "proceed", "next step"
        ],
        RecruiterObjective.interview_scheduling: [
            "schedule", "interview", "calendar", "meeting", "when",
            "availability", "arrange", "coordinate"
        ],
        RecruiterObjective.pipeline_management: [
            "pipeline", "metrics", "funnel", "conversion", "time to hire",
            "analytics", "bottleneck", "process", "efficiency"
        ],
        RecruiterObjective.jd_improvement: [
            "job description", "jd", "requirements", "improve",
            "rewrite", "keywords", "clarity", "posting"
        ],
    }

    @staticmethod
    def detect_objective(
        user_role: UserRole,
        message: str,
        conversation_history: List[str] = None
    ) -> Optional[str]:
        """Detect user objective from message and conversation history"""

        combined_text = (message + " " + " ".join(conversation_history)).lower() if conversation_history else message.lower()

        if user_role == UserRole.candidate:
            objectives = PersonaDetector.CANDIDATE_OBJECTIVE_KEYWORDS
        elif user_role == UserRole.recruiter:
            objectives = PersonaDetector.RECRUITER_OBJECTIVE_KEYWORDS
        else:
            return None

        # Score each objective based on keyword matches
        scores = {}
        for objective, keywords in objectives.items():
            score = sum(1 for keyword in keywords if keyword in combined_text)
            if score > 0:
                scores[objective.value] = score

        # Return objective with highest score
        if scores:
            return max(scores, key=scores.get)
        return None

    @staticmethod
    def detect_conversation_mode(
        message: str,
        conversation_history: List[str] = None
    ) -> ConversationMode:
        """Detect conversation mode based on message characteristics"""

        combined_text = (message + " " + " ".join(conversation_history)).lower() if conversation_history else message.lower()

        # Mode detection keywords
        mode_keywords = {
            ConversationMode.expert: ["deep dive", "detailed", "comprehensive", "advanced", "in depth"],
            ConversationMode.supportive: ["help", "support", "coach", "mentor", "struggling", "concerned"],
            ConversationMode.analytical: ["data", "metrics", "analyze", "statistics", "numbers", "trends"],
            ConversationMode.strategic: ["strategy", "long term", "planning", "roadmap", "vision"],
        }

        mode_scores = {}
        for mode, keywords in mode_keywords.items():
            score = sum(1 for keyword in keywords if keyword in combined_text)
            if score > 0:
                mode_scores[mode] = score

        if mode_scores:
            return max(mode_scores, key=mode_scores.get)
        return ConversationMode.general


class PersonaSystem:
    """Main persona system for agent interaction"""

    def __init__(self):
        self.library = PersonaLibrary()
        self.detector = PersonaDetector()
        self.active_contexts: Dict[str, ConversationContext] = {}

    def get_appropriate_persona(
        self,
        user_id: str,
        user_role: UserRole,
        message: str,
        conversation_history: List[str] = None,
        explicit_objective: Optional[str] = None
    ) -> PersonaProfile:
        """Get the most appropriate persona for the user and conversation"""

        # Detect objective if not explicitly provided
        objective = explicit_objective or self.detector.detect_objective(
            user_role, message, conversation_history
        )

        # Detect conversation mode
        mode = self.detector.detect_conversation_mode(message, conversation_history)

        # Update or create context
        context = self._get_or_create_context(user_id, user_role)
        context.current_objective = objective
        context.conversation_mode = mode
        context.updated_at = datetime.utcnow()

        # Select persona based on role and objective
        persona = self._select_persona(user_role, objective)
        context.active_persona = persona

        return persona

    def get_persona_system_prompt(
        self,
        persona: PersonaProfile,
        user_context: Dict[str, Any],
        conversation_summary: str = ""
    ) -> str:
        """Generate system prompt with persona injection"""

        base_prompt = f"""You are {persona.title}.

EXPERTISE: {persona.expertise}
COMMUNICATION STYLE: {persona.communication_style}
TONE: {persona.tone}

PRIMARY FOCUS: {persona.primary_focus}

YOUR APPROACH:
- {persona.response_approach}

KEY TECHNIQUES TO USE:
{chr(10).join(f"- {t}" for t in persona.key_techniques)}

WHAT TO AVOID:
{chr(10).join(f"- {t}" for t in persona.avoidances)}

DECISION FRAMEWORK: {persona.decision_framework}

VALUE YOU BRING: {persona.value_proposition}

{persona.system_prompt_fragment}

USER CONTEXT:
{json.dumps(user_context, indent=2)}

{f"CONVERSATION SUMMARY: {conversation_summary}" if conversation_summary else ""}
"""

        return base_prompt

    def _get_or_create_context(
        self,
        user_id: str,
        user_role: UserRole
    ) -> ConversationContext:
        """Get existing context or create new one"""

        if user_id not in self.active_contexts:
            self.active_contexts[user_id] = ConversationContext(
                user_id=user_id,
                user_role=user_role
            )
        return self.active_contexts[user_id]

    def _select_persona(
        self,
        user_role: UserRole,
        objective: Optional[str]
    ) -> PersonaProfile:
        """Select persona based on role and objective"""

        if user_role == UserRole.candidate:
            if objective == CandidateObjective.career_exploration.value:
                return PersonaLibrary.CAREER_COACH
            elif objective == CandidateObjective.interview_prep.value:
                return PersonaLibrary.INTERVIEW_COACH
            elif objective == CandidateObjective.application_optimization.value:
                return PersonaLibrary.APPLICATION_OPTIMIZER
            else:
                return PersonaLibrary.CAREER_COACH  # Default

        elif user_role == UserRole.recruiter:
            if objective == RecruiterObjective.candidate_sourcing.value:
                return PersonaLibrary.TALENT_SCOUT
            elif objective == RecruiterObjective.candidate_screening.value:
                return PersonaLibrary.HIRING_MANAGER_ASSISTANT
            elif objective == RecruiterObjective.pipeline_management.value:
                return PersonaLibrary.PIPELINE_MANAGER
            else:
                return PersonaLibrary.TALENT_SCOUT  # Default

        # Default fallback
        return PersonaLibrary.CAREER_COACH
