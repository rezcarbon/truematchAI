"""Recruiter Assistant Agent for hiring and candidate management."""
import logging
from typing import Optional, Dict, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.enhanced_agent import EnhancedBaseAgent
from app.agents.persona_system import PersonaSystem, UserRole
from app.agents.persona_integration import (
    PersonaEnhancedAgentMixin,
    PersonaContextLoader,
    PersonaAnalytics,
)
from app.models.user import User
from app.models.position import Position, PositionStatus
from app.models.application import Application, PipelineStage

logger = logging.getLogger(__name__)


RECRUITER_INSTRUCTIONS = """You are the TrueMatch Recruiter Assistant. Your job is to help recruiters hire the best talent.

You can help with:
1. **Job Management**: Create, analyze, and improve job descriptions
2. **Candidate Sourcing**: Upload, search, and rank candidates
3. **Candidate Evaluation**: Assess fit, identify gaps, provide recommendations
4. **Pipeline Management**: Track stages, identify bottlenecks, suggest next steps
5. **Interview Scheduling**: Schedule interviews, send assessments
6. **Hiring Analytics**: Show metrics, pipeline status, hiring progress
7. **Job Description Analysis**: Test JD quality, find requirement creep, suggest improvements

CAPABILITIES:
- Analyze job descriptions for clarity, competitiveness, and requirements
- Rank candidates by fit to specific roles
- Identify skill gaps and training opportunities
- Suggest next steps in hiring pipeline
- Schedule interviews and send assessments
- Provide hiring metrics and pipeline visualizations
- Test JD against candidate archetypes
- Recommend candidates for open roles

PROACTIVE BEHAVIORS:
- After receiving candidates, offer to analyze and rank them
- Alert when interviews haven't been scheduled
- Suggest candidates for roles
- Flag long-pending candidates
- Recommend optimization opportunities

COMMUNICATION STYLE:
- Be an enthusiastic hiring partner
- Use data to back up recommendations
- Always explain why you recommend something
- Ask clarifying questions about roles, team, timeline
- Show candidate fit scores and reasoning
- Provide actionable next steps

When the recruiter mentions a job role or describes what they need to hire for, you should:
1. Ask clarifying questions about the role (seniority, team size, timeline)
2. Offer to help with job description
3. Ask about candidate sources (upload, search, referrals)
4. Offer to analyze and rank candidates
5. Suggest interview process

When the recruiter uploads candidates:
1. Confirm receipt and quantity
2. Offer to analyze them
3. Ask about the target role
4. Ask if you should start ranking candidates
5. Provide recommendations on next steps

Always be proactive - suggest what to do next rather than waiting to be asked."""


class RecruiterAgent(PersonaEnhancedAgentMixin, EnhancedBaseAgent):
    """Agent that helps recruiters with hiring and candidate management.

    Enhanced with persona system for objective-based personalization.
    Automatically detects recruiter objective (sourcing, screening, pipeline mgmt, etc.)
    and adopts the appropriate persona for strategic guidance.
    """

    def __init__(self, db: AsyncSession, company_id: str):
        super().__init__(
            role="recruiter",
            instructions=RECRUITER_INSTRUCTIONS,
        )

        # ✨ Initialize persona system
        self.db = db
        self.company_id = company_id
        self.context_loader = PersonaContextLoader(db)
        self.set_context_loader(self.context_loader)
        self.analytics = PersonaAnalytics(db)

    async def _load_role_context(self, user: User, db: AsyncSession) -> dict:
        """Load recruiter-specific context: open jobs, pending candidates, metrics.

        Args:
            user: User object
            db: Database session

        Returns:
            Dict with recruiter context
        """
        from sqlalchemy import and_, func

        context = {
            "capabilities": [
                "job_analysis",
                "candidate_ranking",
                "pipeline_tracking",
                "interview_scheduling",
                "hiring_analytics",
            ],
        }

        try:
            # Load open positions for recruiter's company
            positions_stmt = select(Position).where(
                and_(
                    Position.status == PositionStatus.open,
                    Position.created_by == user.id,
                )
            ).limit(5)
            result = await db.execute(positions_stmt)
            positions = result.scalars().all()

            open_positions = [
                {
                    "id": str(p.id),
                    "title": p.title,
                    "status": p.status.value,
                    "created_at": p.created_at.isoformat() if p.created_at else None,
                }
                for p in positions
            ]

            # Load pending candidates (applications in early pipeline stages)
            pending_stmt = select(Application).where(
                and_(
                    Application.stage.in_([PipelineStage.applied, PipelineStage.phone_screen]),
                    select(Position).where(Position.id == Application.position_id).where(
                        Position.created_by == user.id
                    ).exists(),
                )
            ).limit(10)
            result = await db.execute(pending_stmt)
            pending = result.scalars().all()

            pending_candidates = [
                {
                    "stage": p.stage.value,
                    "applied_at": p.applied_at.isoformat() if p.applied_at else None,
                }
                for p in pending
            ]

            # Load pipeline metrics
            metrics_stmt = select(
                Application.stage,
                func.count(Application.id),
            ).where(
                select(Position).where(Position.id == Application.position_id).where(
                    Position.created_by == user.id
                ).exists(),
            ).group_by(Application.stage)

            result = await db.execute(metrics_stmt)
            metrics = {stage.value: count for stage, count in result.all()}

            context.update({
                "open_positions_count": len(open_positions),
                "open_positions": open_positions,
                "pending_candidates_count": len(pending_candidates),
                "pending_candidates": pending_candidates,
                "pipeline_status": metrics,
            })

            logger.info(
                "Loaded recruiter context",
                extra={
                    "user_id": str(user.id),
                    "open_positions": len(open_positions),
                    "pending_candidates": len(pending_candidates),
                },
            )

        except Exception as e:
            logger.error(f"Failed to load recruiter context: {e}")
            context.update({
                "open_positions": [],
                "pending_candidates": [],
                "pipeline_status": {},
            })

        return context

    def _format_context(self, user_context: dict) -> str:
        """Format recruiter context for system prompt."""
        capabilities = user_context.get("capabilities", [])
        return f"""
- Capabilities Available: {', '.join(capabilities)}
- Open Positions: {user_context.get('open_positions', 'N/A')}
- Pending Candidates: {user_context.get('pending_candidates', 'N/A')}
- Pipeline Status: {user_context.get('pipeline_status', 'N/A')}

Focus on helping with the above capabilities and referring to the loaded context."""

    async def respond_with_persona(
        self,
        message: str,
        user_id: str,
        session_id: str,
        explicit_objective: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Respond with persona enhancement.

        Automatically detects recruiter objective and adopts the appropriate persona
        (Talent Scout, Hiring Manager Assistant, or Pipeline Manager) for strategic guidance.

        Args:
            message: User message
            user_id: User ID
            session_id: Chat session ID
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
            user_role=UserRole.recruiter,
            last_message=message,
        )

        # Get response with enhanced prompt
        response_text = await self._respond_with_prompt(
            message=message,
            system_prompt=enhanced_prompt,
            session_id=session_id,
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
            "actions": [],  # Actions would be extracted from response
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
    ) -> str:
        """
        Internal method for generating response with given system prompt.

        This is called by respond_with_persona with the persona-enhanced prompt.
        """

        # Load company context for this session
        company_context = {
            "company_id": self.company_id,
            "session_id": session_id,
        }

        # Combine system prompt with context
        full_prompt = system_prompt + "\n\nCOMPANY_CONTEXT:\n" + str(company_context)

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

        Scores based on response length, data-driven insights, and persona-specific techniques.
        """

        effectiveness = 0.5  # baseline

        # Bonus for length (indicates thorough analysis)
        if len(response) > 500:
            effectiveness += 0.15
        if len(response) > 1000:
            effectiveness += 0.15

        # Bonus for data-driven content
        data_indicators = [
            "metrics", "data", "analysis", "statistics",
            "conversion", "pipeline", "percentage", "number",
            "recommendation", "insight"
        ]
        if any(indicator in response.lower() for indicator in data_indicators):
            effectiveness += 0.2

        return min(effectiveness, 1.0)
