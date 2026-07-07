"""Career Coaching Service - AI-powered career guidance and mentorship.

Provides comprehensive career coaching including:
- Personalized career context injection into prompts
- Learning path generation between roles
- Salary market benchmarking
- Conversation tracking and summarization
- Resource recommendations (Coursera, GitHub, communities)
"""
from __future__ import annotations

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Optional, Any

from anthropic import AsyncAnthropic
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.user import User
from app.models.resume_version import ResumeVersion

logger = logging.getLogger(__name__)


@dataclass
class CareerContext:
    """User's career context for coaching."""

    user_id: uuid.UUID
    current_role: str
    target_role: str
    years_experience: int
    skills: list[str] = field(default_factory=list)
    certifications: list[str] = field(default_factory=list)
    education: list[str] = field(default_factory=list)
    strengths: list[str] = field(default_factory=list)
    challenges: list[str] = field(default_factory=list)
    career_goals: str = ""
    recent_achievements: list[str] = field(default_factory=list)

    def to_prompt_text(self) -> str:
        """Format context as prompt text."""
        lines = [
            "=== CAREER CONTEXT ===",
            f"Current Role: {self.current_role}",
            f"Target Role: {self.target_role}",
            f"Years of Experience: {self.years_experience}",
            f"Skills: {', '.join(self.skills[:10])}",
            f"Certifications: {', '.join(self.certifications) if self.certifications else 'None'}",
            f"Education: {', '.join(self.education) if self.education else 'None'}",
            f"Strengths: {', '.join(self.strengths)}",
            f"Challenges: {', '.join(self.challenges)}",
            f"Goals: {self.career_goals}",
        ]
        return "\n".join(lines)


@dataclass
class LearningResource:
    """A learning resource recommendation."""

    title: str
    platform: str
    url: str
    estimated_hours: int
    difficulty_level: str  # beginner, intermediate, advanced
    skills_covered: list[str] = field(default_factory=list)
    cost: str = "free"  # free, paid, variable
    description: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class LearningPath:
    """A learning path to reach a target role."""

    from_role: str
    to_role: str
    duration_weeks: int
    phases: list[dict] = field(default_factory=list)
    required_skills: list[str] = field(default_factory=list)
    recommended_resources: list[LearningResource] = field(default_factory=list)
    milestones: list[dict] = field(default_factory=list)
    estimated_cost_usd: float = 0.0

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "from_role": self.from_role,
            "to_role": self.to_role,
            "duration_weeks": self.duration_weeks,
            "phases": self.phases,
            "required_skills": self.required_skills,
            "recommended_resources": [r.to_dict() for r in self.recommended_resources],
            "milestones": self.milestones,
            "estimated_cost_usd": self.estimated_cost_usd,
        }


@dataclass
class SalaryData:
    """Salary market data for a role."""

    role: str
    location: str
    experience_level: str
    min_salary: int
    median_salary: int
    max_salary: int
    currency: str = "USD"
    percentile_25: int = 0
    percentile_75: int = 0
    company_data: list[dict] = field(default_factory=list)
    data_source: str = "market_aggregation"
    confidence_score: float = 0.75

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class CoachingMessage:
    """A message in the coaching conversation."""

    role: str  # assistant or user
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    feedback: Optional[str] = None
    resources_suggested: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "feedback": self.feedback,
            "resources_suggested": self.resources_suggested,
        }


@dataclass
class ConversationSummary:
    """Summary of a coaching conversation."""

    conversation_id: str
    user_id: uuid.UUID
    topic: str
    key_points: list[str] = field(default_factory=list)
    action_items: list[str] = field(default_factory=list)
    resources_recommended: list[str] = field(default_factory=list)
    sentiment: str = "neutral"  # positive, neutral, negative
    next_steps: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    message_count: int = 0

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)


class CareerCoachService:
    """Service for AI-powered career coaching."""

    # Role transition paths
    ROLE_TRANSITIONS = {
        "junior_engineer": {
            "mid_engineer": {
                "weeks": 24,
                "skills": ["system_design", "leadership", "mentoring"],
            },
            "data_scientist": {
                "weeks": 52,
                "skills": ["machine_learning", "statistics", "python"],
            },
        },
        "mid_engineer": {
            "senior_engineer": {
                "weeks": 24,
                "skills": ["architecture", "technical_leadership", "cross_team_collaboration"],
            },
            "devops_engineer": {
                "weeks": 26,
                "skills": ["cloud_platforms", "cicd", "containers"],
            },
        },
        "senior_engineer": {
            "engineering_manager": {
                "weeks": 12,
                "skills": ["people_management", "communication", "strategy"],
            },
            "staff_engineer": {
                "weeks": 26,
                "skills": ["technical_strategy", "mentorship", "system_architecture"],
            },
        },
    }

    # Salary data by role/location/experience (would come from API in production)
    SALARY_BENCHMARKS = {
        "junior_engineer_us": {
            "min": 80000,
            "median": 110000,
            "max": 140000,
            "25th": 95000,
            "75th": 125000,
        },
        "mid_engineer_us": {
            "min": 120000,
            "median": 160000,
            "max": 200000,
            "25th": 140000,
            "75th": 180000,
        },
        "senior_engineer_us": {
            "min": 160000,
            "median": 220000,
            "max": 280000,
            "25th": 190000,
            "75th": 250000,
        },
        "data_scientist_us": {
            "min": 110000,
            "median": 150000,
            "max": 200000,
            "25th": 130000,
            "75th": 175000,
        },
    }

    # Learning resources by skill
    LEARNING_RESOURCES_DB = {
        "system_design": [
            LearningResource(
                title="System Design Interview",
                platform="Educative",
                url="https://educative.io/courses/grokking-the-system-design-interview",
                estimated_hours=20,
                difficulty_level="advanced",
                skills_covered=["system_design", "scalability"],
                cost="paid",
            ),
            LearningResource(
                title="Designing Data-Intensive Applications",
                platform="Book",
                url="https://dataintensive.net",
                estimated_hours=40,
                difficulty_level="advanced",
                skills_covered=["distributed_systems", "data_architecture"],
                cost="paid",
            ),
        ],
        "machine_learning": [
            LearningResource(
                title="Machine Learning Specialization",
                platform="Coursera",
                url="https://coursera.org/specializations/machine-learning",
                estimated_hours=100,
                difficulty_level="intermediate",
                skills_covered=["machine_learning", "python", "statistics"],
                cost="paid",
            ),
            LearningResource(
                title="Fast.ai",
                platform="Fast.ai",
                url="https://fast.ai",
                estimated_hours=80,
                difficulty_level="intermediate",
                skills_covered=["deep_learning", "pytorch"],
                cost="free",
            ),
        ],
        "leadership": [
            LearningResource(
                title="The Effective Manager",
                platform="Book",
                url="https://www.theeffectivemanager.com",
                estimated_hours=8,
                difficulty_level="intermediate",
                skills_covered=["people_management", "communication"],
                cost="paid",
            ),
            LearningResource(
                title="Radical Candor",
                platform="Book",
                url="https://www.radicalcandor.com",
                estimated_hours=6,
                difficulty_level="intermediate",
                skills_covered=["leadership", "feedback"],
                cost="paid",
            ),
        ],
    }

    def __init__(self, db: AsyncSession):
        """Initialize the service.

        Args:
            db: AsyncSession for database operations
        """
        self.db = db
        self.anthropic_client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    async def get_career_context(
        self, user_id: uuid.UUID
    ) -> Optional[CareerContext]:
        """Get career context for a user.

        Args:
            user_id: The user ID

        Returns:
            CareerContext or None
        """
        try:
            # Fetch user
            user_stmt = select(User).where(User.id == user_id)
            user_result = await self.db.execute(user_stmt)
            user = user_result.scalars().first()

            if not user:
                return None

            # Fetch latest resume version for context
            resume_stmt = (
                select(ResumeVersion)
                .where(ResumeVersion.user_id == user_id)
                .order_by(desc(ResumeVersion.created_at))
                .limit(1)
            )
            resume_result = await self.db.execute(resume_stmt)
            resume_version = resume_result.scalars().first()

            parsed_data = resume_version.parsed_data if resume_version else {}

            # Build context
            context = CareerContext(
                user_id=user_id,
                current_role=parsed_data.get("current_role", "Not specified"),
                target_role=getattr(user, "target_role", "Not specified"),
                years_experience=self._calculate_years_experience(parsed_data),
                skills=parsed_data.get("skills", [])[:20],
                certifications=parsed_data.get("certifications", []),
                education=[
                    e.get("degree", "")
                    for e in parsed_data.get("education", [])
                    if isinstance(e, dict)
                ],
                strengths=self._identify_strengths(parsed_data),
                challenges=self._identify_challenges(parsed_data),
                career_goals=getattr(user, "career_goals", ""),
                recent_achievements=self._extract_achievements(parsed_data),
            )

            logger.info(f"Retrieved career context for user {user_id}")
            return context

        except Exception as e:
            logger.error(f"Error getting career context: {str(e)}", exc_info=True)
            return None

    async def build_coaching_prompt(
        self, user_id: uuid.UUID, question: str
    ) -> str:
        """Build a coaching prompt with user context.

        Args:
            user_id: The user ID
            question: The user's question

        Returns:
            System prompt with injected context
        """
        try:
            context = await self.get_career_context(user_id)

            base_prompt = """You are an experienced career coach with expertise in:
- Career transition planning
- Skill development and learning paths
- Salary negotiation and market positioning
- Technical and leadership growth
- Interview preparation

Your guidance should be:
1. Specific and actionable with concrete next steps
2. Time-bound with realistic timeframes
3. Evidence-based using market data
4. Personalized to the person's situation
5. Encouraging but realistic

Always provide numbered steps, timeframes, and specific resources."""

            if context:
                base_prompt += "\n\n" + context.to_prompt_text()

            base_prompt += f"\n\n=== USER QUESTION ===\n{question}"

            return base_prompt

        except Exception as e:
            logger.error(f"Error building coaching prompt: {str(e)}", exc_info=True)
            return f"You are a career coach. Answer this question: {question}"

    async def generate_learning_path(
        self,
        current_role: str,
        target_role: str,
        current_skills: list[str] = None,
    ) -> LearningPath:
        """Generate a learning path between roles.

        Args:
            current_role: Current role
            target_role: Target role
            current_skills: Current skills

        Returns:
            LearningPath
        """
        try:
            if current_skills is None:
                current_skills = []

            # Look up transition path
            transition_key = current_role.lower().replace(" ", "_")
            target_key = target_role.lower().replace(" ", "_")

            transition_info = self.ROLE_TRANSITIONS.get(transition_key, {}).get(
                target_key, {"weeks": 26, "skills": []}
            )

            # Build phases
            phases = [
                {
                    "phase": 1,
                    "name": "Foundation Building",
                    "weeks": 8,
                    "focus": f"Master prerequisite skills for {target_role}",
                },
                {
                    "phase": 2,
                    "name": "Core Skills Development",
                    "weeks": 12,
                    "focus": f"Deep dive into key skills needed for {target_role}",
                },
                {
                    "phase": 3,
                    "name": "Practical Application",
                    "weeks": 4,
                    "focus": "Build projects and gain hands-on experience",
                },
                {
                    "phase": 4,
                    "name": "Interview Preparation",
                    "weeks": 2,
                    "focus": "Prepare for technical and behavioral interviews",
                },
            ]

            # Build milestones
            milestones = [
                {"week": 4, "milestone": "Complete foundational courses"},
                {"week": 12, "milestone": "Complete 2-3 projects"},
                {"week": 20, "milestone": "Contribute to open source"},
                {"week": 24, "milestone": "Apply to target roles"},
                {"week": 26, "milestone": "Secure new role"},
            ]

            # Get resources for required skills
            required_skills = transition_info.get("skills", [])
            recommended_resources = await self._get_resources_for_skills(
                required_skills
            )

            learning_path = LearningPath(
                from_role=current_role,
                to_role=target_role,
                duration_weeks=transition_info.get("weeks", 26),
                phases=phases,
                required_skills=required_skills,
                recommended_resources=recommended_resources,
                milestones=milestones,
                estimated_cost_usd=self._estimate_learning_cost(recommended_resources),
            )

            logger.info(
                f"Generated learning path from {current_role} to {target_role}"
            )
            return learning_path

        except Exception as e:
            logger.error(f"Error generating learning path: {str(e)}", exc_info=True)
            # Return default path
            return LearningPath(
                from_role=current_role,
                to_role=target_role,
                duration_weeks=26,
                phases=[
                    {
                        "phase": 1,
                        "name": "Foundation",
                        "weeks": 8,
                        "focus": "Build core skills",
                    }
                ],
                required_skills=[],
            )

    async def get_salary_benchmarks(
        self,
        role: str,
        location: str = "US",
        experience_level: str = "mid",
    ) -> SalaryData:
        """Get salary benchmarks for a role.

        Args:
            role: The job role
            location: Geographic location
            experience_level: junior/mid/senior

        Returns:
            SalaryData
        """
        try:
            # Look up salary data
            benchmark_key = f"{role.lower().replace(' ', '_')}_{location}".lower()

            salary_info = self.SALARY_BENCHMARKS.get(benchmark_key)

            if salary_info:
                salary_data = SalaryData(
                    role=role,
                    location=location,
                    experience_level=experience_level,
                    min_salary=salary_info["min"],
                    median_salary=salary_info["median"],
                    max_salary=salary_info["max"],
                    percentile_25=salary_info.get("25th", salary_info["min"]),
                    percentile_75=salary_info.get("75th", salary_info["max"]),
                    company_data=await self._get_company_salary_data(role, location),
                )
            else:
                # Default values if not found
                salary_data = SalaryData(
                    role=role,
                    location=location,
                    experience_level=experience_level,
                    min_salary=100000,
                    median_salary=140000,
                    max_salary=180000,
                    confidence_score=0.5,
                )

            logger.info(f"Retrieved salary benchmarks for {role} in {location}")
            return salary_data

        except Exception as e:
            logger.error(f"Error getting salary benchmarks: {str(e)}", exc_info=True)
            return SalaryData(
                role=role,
                location=location,
                experience_level=experience_level,
                min_salary=0,
                median_salary=0,
                max_salary=0,
                confidence_score=0.0,
            )

    async def track_coaching_conversation(
        self,
        user_id: uuid.UUID,
        messages: list[dict],
    ) -> ConversationSummary:
        """Track and summarize a coaching conversation.

        Args:
            user_id: The user ID
            messages: List of messages (format: {"role": "user"|"assistant", "content": "..."})

        Returns:
            ConversationSummary
        """
        try:
            conversation_id = str(uuid.uuid4())

            # Build conversation text
            conversation_text = "\n".join(
                [
                    f"{msg.get('role', 'unknown').upper()}: {msg.get('content', '')}"
                    for msg in messages
                ]
            )

            # Use Claude to summarize
            summary_prompt = f"""Analyze this career coaching conversation and provide a structured summary.

Conversation:
{conversation_text}

Provide JSON response with:
- topic: main topic discussed
- key_points: list of key discussion points
- action_items: list of specific actions the person should take
- resources_recommended: list of resources mentioned
- sentiment: overall sentiment (positive/neutral/negative)
- next_steps: what they should do next"""

            try:
                summary_response = await asyncio.wait_for(
                    self._call_claude_api(summary_prompt),
                    timeout=settings.llm_timeout_seconds,
                )

                summary_data = self._parse_summary_response(summary_response)
            except asyncio.TimeoutError:
                logger.warning("Claude API timeout for conversation summary")
                summary_data = {
                    "topic": "Career Coaching",
                    "key_points": [],
                    "action_items": [],
                    "resources_recommended": [],
                    "sentiment": "neutral",
                    "next_steps": "Continue working on defined goals",
                }

            summary = ConversationSummary(
                conversation_id=conversation_id,
                user_id=user_id,
                topic=summary_data.get("topic", "Career Discussion"),
                key_points=summary_data.get("key_points", []),
                action_items=summary_data.get("action_items", []),
                resources_recommended=summary_data.get("resources_recommended", []),
                sentiment=summary_data.get("sentiment", "neutral"),
                next_steps=summary_data.get("next_steps", ""),
                message_count=len(messages),
            )

            logger.info(
                f"Tracked coaching conversation for user {user_id}",
                extra={"conversation_id": conversation_id},
            )
            return summary

        except Exception as e:
            logger.error(f"Error tracking coaching conversation: {str(e)}", exc_info=True)
            return ConversationSummary(
                conversation_id=str(uuid.uuid4()),
                user_id=user_id,
                topic="Career Discussion",
                message_count=len(messages),
            )

    # Helper methods

    def _calculate_years_experience(self, parsed_data: dict) -> int:
        """Calculate years of experience from resume data.

        Args:
            parsed_data: Parsed resume data

        Returns:
            Estimated years of experience
        """
        work_exp = parsed_data.get("work_experience", [])
        if not work_exp:
            return 0

        # Rough estimate: assume each role is ~2 years
        return len(work_exp) * 2

    def _identify_strengths(self, parsed_data: dict) -> list[str]:
        """Identify candidate strengths from resume.

        Args:
            parsed_data: Parsed resume data

        Returns:
            List of strengths
        """
        strengths = []

        skills = parsed_data.get("skills", [])
        if len(skills) >= 10:
            strengths.append("Diverse technical skills")

        certifications = parsed_data.get("certifications", [])
        if certifications:
            strengths.append("Professional certifications")

        work_exp = parsed_data.get("work_experience", [])
        if len(work_exp) >= 5:
            strengths.append("Extensive work experience")

        education = parsed_data.get("education", [])
        if education:
            strengths.append("Strong educational background")

        return strengths

    def _identify_challenges(self, parsed_data: dict) -> list[str]:
        """Identify candidate challenges from resume.

        Args:
            parsed_data: Parsed resume data

        Returns:
            List of challenges
        """
        challenges = []

        skills = parsed_data.get("skills", [])
        if len(skills) < 5:
            challenges.append("Limited technical skills documented")

        work_exp = parsed_data.get("work_experience", [])
        if not work_exp:
            challenges.append("No work experience")
        elif len(work_exp) == 1:
            challenges.append("Limited work experience")

        certifications = parsed_data.get("certifications", [])
        if not certifications:
            challenges.append("No professional certifications")

        return challenges

    def _extract_achievements(self, parsed_data: dict) -> list[str]:
        """Extract achievements from resume.

        Args:
            parsed_data: Parsed resume data

        Returns:
            List of achievements
        """
        achievements = []

        work_exp = parsed_data.get("work_experience", [])
        for exp in work_exp[:3]:  # Get first 3 roles
            if isinstance(exp, dict) and exp.get("description"):
                achievements.append(
                    f"Achievement at {exp.get('position', 'role')}: {exp.get('description')[:100]}"
                )

        return achievements

    async def _get_resources_for_skills(
        self, skills: list[str]
    ) -> list[LearningResource]:
        """Get learning resources for skills.

        Args:
            skills: List of skills

        Returns:
            List of LearningResource
        """
        resources = []

        for skill in skills[:5]:  # Get top 5 skills
            skill_lower = skill.lower()
            if skill_lower in self.LEARNING_RESOURCES_DB:
                resources.extend(self.LEARNING_RESOURCES_DB[skill_lower][:2])

        return resources[:10]

    async def _get_company_salary_data(
        self, role: str, location: str
    ) -> list[dict]:
        """Get salary data by company (mock implementation).

        Args:
            role: The role
            location: The location

        Returns:
            List of company salary data
        """
        # In production, would query actual company salary data
        return [
            {"company": "Tech Corp", "salary": 150000},
            {"company": "StartUp Inc", "salary": 120000},
            {"company": "Big Tech", "salary": 180000},
        ]

    def _estimate_learning_cost(self, resources: list[LearningResource]) -> float:
        """Estimate total learning cost.

        Args:
            resources: List of resources

        Returns:
            Estimated cost in USD
        """
        total_cost = 0.0

        for resource in resources:
            if resource.cost == "paid":
                # Estimate typical paid course cost
                total_cost += 49.99
            elif resource.cost == "variable":
                total_cost += 25.0

        return round(total_cost, 2)

    async def _call_claude_api(self, prompt: str) -> str:
        """Call Claude API.

        Args:
            prompt: The prompt

        Returns:
            Claude's response
        """
        try:
            message = await self.anthropic_client.messages.create(
                model=settings.anthropic_model,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}],
            )
            return message.content[0].text if message.content else ""
        except Exception as e:
            logger.error(f"Error calling Claude API: {str(e)}", exc_info=True)
            return ""

    def _parse_summary_response(self, response: str) -> dict:
        """Parse Claude's summary response.

        Args:
            response: Claude's response

        Returns:
            Parsed summary dictionary
        """
        try:
            import re

            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            logger.debug(f"Could not parse summary: {str(e)}")

        return {
            "topic": "Career Discussion",
            "key_points": [],
            "action_items": [],
            "resources_recommended": [],
            "sentiment": "neutral",
            "next_steps": "",
        }
