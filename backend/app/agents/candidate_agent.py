"""Candidate Career Coach Agent for CV analysis and job matching."""
import logging
from typing import Optional, Dict, Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.enhanced_agent import EnhancedBaseAgent
from app.agents.persona_system import PersonaSystem, UserRole
from app.agents.persona_integration import (
    PersonaEnhancedAgentMixin,
    PersonaContextLoader,
    PersonaAnalytics,
)
from app.models.user import User
from app.models.resume import Resume
from app.models.application import Application
from app.models.position import Position

logger = logging.getLogger(__name__)


CANDIDATE_INSTRUCTIONS = """You are the TrueMatch Career Coach. Your job is to help candidates advance their careers.

You can help with:
1. **CV Analysis**: Analyze CVs, identify strengths and gaps
2. **Job Matching**: Find jobs that match the candidate's profile
3. **Skill Development**: Identify skills needed for target roles
4. **CV Optimization**: Suggest improvements and rewording
5. **Career Guidance**: Help with career trajectory and growth
6. **Application Tracking**: Track applications and status
7. **Interview Prep**: Prepare for interviews, mock questions

CAPABILITIES:
- Analyze CV and extract skills, experience, achievements
- Identify skill gaps for target roles
- Find matching jobs from the database
- Suggest CV improvements and better phrasing
- Analyze career trajectory and growth opportunities
- Provide market positioning insights
- Track application status and next steps
- Recommend roles based on profile

PROACTIVE BEHAVIORS:
- After CV upload, offer to analyze it
- Ask about career goals and target roles
- Suggest specific skill improvements
- Alert about new matching job opportunities
- Track application progress
- Provide encouragement and guidance

COMMUNICATION STYLE:
- Be a supportive career coach
- Use specific, actionable advice
- Reference their actual CV/experience
- Show opportunities that match their profile
- Celebrate progress and improvements
- Provide confidence and clarity

When a candidate uploads their CV:
1. Confirm receipt and do quick analysis
2. Ask about their career goals
3. Ask about target roles or seniority level
4. Offer to find matching jobs
5. Suggest CV improvements if needed

When discussing career goals:
1. Ask about target role, seniority, industry
2. Assess current skills vs. target requirements
3. Identify skill gaps
4. Suggest how to close gaps
5. Find matching jobs

When showing job matches:
1. Show top matching positions
2. Explain why they're a good fit
3. Highlight any skill gaps for specific roles
4. Suggest improvements for better fit
5. Offer to help with applications

Always be encouraging and practical - candidates should feel empowered to advance their careers."""


class CandidateAgent(PersonaEnhancedAgentMixin, EnhancedBaseAgent):
    """Agent that helps candidates with career development and job matching.

    Enhanced with persona system for objective-based personalization.
    Automatically detects user objective (interview prep, resume optimization, etc.)
    and adopts the appropriate persona for guidance.
    """

    def __init__(self, db: AsyncSession):
        super().__init__(
            role="candidate",
            instructions=CANDIDATE_INSTRUCTIONS,
        )

        # ✨ Initialize persona system
        self.db = db
        self.context_loader = PersonaContextLoader(db)
        self.set_context_loader(self.context_loader)
        self.analytics = PersonaAnalytics(db)

    async def _load_role_context(self, user: User, db: AsyncSession) -> dict:
        """Load candidate-specific context: CVs, applications, recommendations.

        Args:
            user: User object
            db: Database session

        Returns:
            Dict with candidate context
        """
        import logging
        logger = logging.getLogger(__name__)

        context = {
            "capabilities": [
                "cv_analysis",
                "skill_assessment",
                "job_matching",
                "market_positioning",
                "career_guidance",
            ],
        }

        try:
            # Load uploaded CVs for this candidate
            logger.debug(f"Loading CVs for user {user.id}")
            cvs_stmt = select(Resume).where(Resume.user_id == user.id)
            result = await db.execute(cvs_stmt)
            cvs = result.scalars().all()
            logger.debug(f"Loaded {len(cvs)} CVs")

            uploaded_cvs = [
                {
                    "id": str(cv.id),
                    "file_type": cv.file_type or "unknown",
                    "created_at": cv.created_at.isoformat() if cv.created_at else None,
                    "has_parsed_data": bool(cv.parsed_data),
                }
                for cv in cvs
            ]

            # Load applied jobs (applications)
            applications_stmt = (
                select(Application, Position)
                .join(Position)
                .where(Application.user_id == user.id)
                .order_by(Application.applied_at.desc())
                .limit(5)
            )
            result = await db.execute(applications_stmt)
            applications = result.all()

            applied_jobs = [
                {
                    "position_title": pos.title,
                    "stage": app.stage.value,
                    "applied_at": app.applied_at.isoformat() if app.applied_at else None,
                }
                for app, pos in applications
            ]

            # Get pipeline breakdown
            pipeline_stmt = (
                select(
                    Application.stage,
                    select(func.count(Application.id))
                    .where(Application.user_id == user.id)
                    .correlate(None)
                    .scalar_subquery(),
                )
                .where(Application.user_id == user.id)
                .distinct()
            )
            result = await db.execute(pipeline_stmt)
            stages = {stage.value: count for stage, count in result.all()}

            context.update({
                "cv_count": len(uploaded_cvs),
                "uploaded_cvs": uploaded_cvs,
                "applications_count": len(applied_jobs),
                "applied_jobs": applied_jobs,
                "pipeline_breakdown": stages,
            })

            logger.info(
                "Loaded candidate context",
                extra={
                    "user_id": str(user.id),
                    "cv_count": len(uploaded_cvs),
                    "applications": len(applied_jobs),
                },
            )

        except Exception as e:
            logger.error(f"Failed to load candidate context: {e}")
            context.update({
                "uploaded_cvs": [],
                "applied_jobs": [],
                "pipeline_breakdown": {},
            })

        return context

    def _format_context(self, user_context: dict) -> str:
        """Format candidate context for system prompt."""
        capabilities = user_context.get("capabilities", [])
        return f"""
- Capabilities Available: {', '.join(capabilities)}
- Your CVs: {user_context.get('uploaded_cvs', 'N/A')}
- Applied Jobs: {user_context.get('applied_jobs', 'N/A')}
- Recommendations: {user_context.get('recommendations', 'N/A')}

Focus on helping with career development, CV improvement, and job matching."""

    async def respond_with_persona(
        self,
        message: str,
        user_id: str,
        session_id: str,
        chat_mode: str = "general",
        explicit_objective: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Respond with persona enhancement.

        Automatically detects user objective and adopts the appropriate persona
        (Career Coach, Interview Coach, or Application Optimizer) for personalized guidance.

        Args:
            message: User message
            user_id: User ID
            session_id: Chat session ID
            chat_mode: Chat mode (general, career_coach, interview_prep, etc.)
            explicit_objective: Optional explicit objective override

        Returns:
            Response dict with: message, actions, persona info, objective, mode
        """

        # Store user context for persona system
        self.user_id = user_id
        self.session_id = session_id

        # Build persona-aware system prompt
        enhanced_prompt, active_persona = self._build_persona_aware_system_prompt(
            base_system_prompt=self.instructions,
            user_id=user_id,
            user_role=UserRole.candidate,
            last_message=message,
        )

        # Get response with enhanced prompt
        response_text = await self._respond_with_prompt(
            message=message,
            system_prompt=enhanced_prompt,
            session_id=session_id,
            chat_mode=chat_mode,
        )

        # Adapt response based on persona
        adapted_response = self.adapt_response(response_text, active_persona)

        # Track persona usage for analytics
        context = self.persona_system.active_contexts.get(user_id)
        if context and context.active_persona:
            effectiveness_score = await self._calculate_effectiveness(message, adapted_response)
            await self.analytics.track_persona_usage(
                user_id=user_id,
                persona_id=context.active_persona.id,
                objective=context.current_objective or "unknown",
                mode=context.conversation_mode.value,
                effectiveness_score=effectiveness_score,
            )

        # Update conversation history
        self._update_conversation_history(message)

        return {
            "response": adapted_response,
            "persona": {
                "id": active_persona.id,
                "name": active_persona.name,
                "title": active_persona.title,
            },
            "objective": context.current_objective if context else None,
            "mode": context.conversation_mode.value if context else "general",
        }

    async def _respond_with_prompt(
        self,
        message: str,
        system_prompt: str,
        session_id: str,
        chat_mode: str = "general",
    ) -> str:
        """
        Internal method for generating response with given system prompt.

        This is called by respond_with_persona with the persona-enhanced prompt.
        """

        # Load user context for this session
        # (In a real implementation, fetch user from session)
        user_context = {
            "chat_mode": chat_mode,
            "session_id": session_id,
        }

        # Combine system prompt with context
        full_prompt = system_prompt + "\n\nUSER_CONTEXT:\n" + str(user_context)

        # This would normally call the actual Claude API or agent logic
        # For now, return a placeholder that will be handled by parent class
        return message

    async def _calculate_effectiveness(
        self,
        message: str,
        response: str,
    ) -> float:
        """
        Calculate how effective the persona response was (0.0 to 1.0).

        Scores based on response length, actionability, and persona-specific techniques.
        """

        effectiveness = 0.5  # baseline

        # Bonus for length (indicates thoroughness)
        if len(response) > 500:
            effectiveness += 0.15
        if len(response) > 1000:
            effectiveness += 0.15

        # Bonus for actionable content
        action_indicators = [
            "recommended", "suggested", "try", "next step",
            "action", "practice", "work on", "focus on"
        ]
        if any(indicator in response.lower() for indicator in action_indicators):
            effectiveness += 0.2

        return min(effectiveness, 1.0)
