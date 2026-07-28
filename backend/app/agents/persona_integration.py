"""
Persona Integration Layer

Integrates the PersonaSystem with existing agents (EnhancedBaseAgent subclasses)
to inject persona-driven behavior into agent responses.

This layer:
1. Detects user objective from conversation
2. Selects appropriate persona
3. Injects persona into system prompt
4. Loads persona-specific context
5. Adapts response tone and structure based on persona
"""

from typing import Optional, Dict, List, Any, Tuple
from datetime import datetime
import logging

from .persona_system import (
    PersonaSystem,
    PersonaProfile,
    ConversationContext,
    ConversationMode,
    UserRole
)

logger = logging.getLogger(__name__)


class PersonaContextLoader:
    """Loads context data needed by specific personas"""

    def __init__(self, db_session):
        self.db = db_session

    def load_candidate_context(
        self,
        user_id: str,
        objective: Optional[str] = None
    ) -> Dict[str, Any]:
        """Load candidate-specific context for persona"""

        context = {
            "user_id": user_id,
            "current_role": None,
            "career_goals": None,
            "skills": [],
            "experience_years": 0,
            "industry_preferences": [],
            "target_companies": [],
            "job_descriptions": [],
            "interview_stage": None,
            "previous_interviews": [],
            "interview_types": [],
        }

        # TODO: Query actual data from database
        # This is a placeholder for the actual implementation

        return context

    def load_recruiter_context(
        self,
        company_id: str,
        objective: Optional[str] = None
    ) -> Dict[str, Any]:
        """Load recruiter-specific context for persona"""

        context = {
            "company_id": company_id,
            "role_requirements": {},
            "market_data": {},
            "existing_pipeline": [],
            "successful_hires": [],
            "competitor_hiring": [],
            "pipeline_metrics": {},
            "historical_data": {},
            "current_roles": [],
            "team_capacity": {},
            "conversion_rates": {},
        }

        # TODO: Query actual data from database

        return context


class PersonaResponseAdapter:
    """Adapts agent responses based on active persona"""

    @staticmethod
    def adapt_response_format(
        response: str,
        persona: PersonaProfile,
        conversation_mode: ConversationMode
    ) -> str:
        """Adapt response format based on persona and conversation mode"""

        if conversation_mode == ConversationMode.expert:
            return PersonaResponseAdapter._format_expert_response(response, persona)
        elif conversation_mode == ConversationMode.supportive:
            return PersonaResponseAdapter._format_supportive_response(response, persona)
        elif conversation_mode == ConversationMode.analytical:
            return PersonaResponseAdapter._format_analytical_response(response, persona)
        elif conversation_mode == ConversationMode.strategic:
            return PersonaResponseAdapter._format_strategic_response(response, persona)
        else:
            return response

    @staticmethod
    def _format_expert_response(response: str, persona: PersonaProfile) -> str:
        """Format response for expert mode - deep, detailed, technical"""
        # Add depth markers and structured sections
        adapted = f"""### Expert Deep Dive: {persona.name}

{response}

---
**Key Techniques Applied:**
- Detailed analysis and recommendations
- Industry best practices and benchmarks
- Edge cases and nuanced considerations
- Advanced strategies for optimization
"""
        return adapted

    @staticmethod
    def _format_supportive_response(response: str, persona: PersonaProfile) -> str:
        """Format response for supportive mode - encouraging, coaching"""
        adapted = f"""### {persona.name} - Your Success Partner

{response}

---
**Remember:**
- You have the capabilities to succeed
- Small improvements compound over time
- I'm here to help you every step of the way
- Your effort and growth matter

What specific area would you like to focus on next?
"""
        return adapted

    @staticmethod
    def _format_analytical_response(response: str, persona: PersonaProfile) -> str:
        """Format response for analytical mode - data-driven, metrics-focused"""
        adapted = f"""### {persona.name} - Data-Driven Analysis

{response}

---
**Key Metrics:**
- What to measure and track
- How to know if you're improving
- Benchmarks for comparison
- Data points to watch

**Next Steps:**
- Which metrics to focus on
- How to optimize based on data
"""
        return adapted

    @staticmethod
    def _format_strategic_response(response: str, persona: PersonaProfile) -> str:
        """Format response for strategic mode - high-level planning"""
        adapted = f"""### {persona.name} - Strategic Roadmap

{response}

---
**Strategic Timeline:**
- Immediate actions (next 2 weeks)
- Short-term goals (1-3 months)
- Medium-term milestones (3-6 months)
- Long-term vision (6+ months)

**Success Factors:**
- Critical success factors
- Potential obstacles and mitigation
- Key performance indicators
"""
        return adapted


class PersonaEnhancedAgentMixin:
    """Mixin to add persona functionality to existing agents"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.persona_system = PersonaSystem()
        self.context_loader: Optional[PersonaContextLoader] = None
        self.response_adapter = PersonaResponseAdapter()
        self.conversation_history: List[str] = []

    def set_context_loader(self, loader: PersonaContextLoader):
        """Set the context loader for persona data"""
        self.context_loader = loader

    def _build_persona_aware_system_prompt(
        self,
        base_system_prompt: str,
        user_id: str,
        user_role: UserRole,
        last_message: str
    ) -> Tuple[str, PersonaProfile]:
        """
        Build system prompt with persona injection

        Returns:
            Tuple of (enhanced_system_prompt, active_persona)
        """

        # Get appropriate persona
        persona = self.persona_system.get_appropriate_persona(
            user_id=user_id,
            user_role=user_role,
            message=last_message,
            conversation_history=self.conversation_history
        )

        # Load persona-specific context
        if user_role == UserRole.candidate and self.context_loader:
            user_context = self.context_loader.load_candidate_context(user_id)
        elif user_role == UserRole.recruiter and self.context_loader:
            user_context = self.context_loader.load_recruiter_context(
                company_id=getattr(self, 'company_id', 'unknown')
            )
        else:
            user_context = {}

        # Generate conversation summary
        conversation_summary = self._generate_conversation_summary()

        # Generate persona-enhanced system prompt
        persona_system_prompt = self.persona_system.get_persona_system_prompt(
            persona=persona,
            user_context=user_context,
            conversation_summary=conversation_summary
        )

        # Combine base prompt with persona prompt
        combined_prompt = f"""{base_system_prompt}

---

ACTIVE PERSONA SYSTEM:

{persona_system_prompt}
"""

        return combined_prompt, persona

    def adapt_response(
        self,
        response: str,
        persona: PersonaProfile
    ) -> str:
        """Adapt response based on active persona and conversation mode"""

        context = self.persona_system.active_contexts.get(getattr(self, 'user_id', None))
        if context:
            response = self.response_adapter.adapt_response_format(
                response,
                persona,
                context.conversation_mode
            )

        return response

    def _generate_conversation_summary(self) -> str:
        """Generate summary of conversation so far"""

        if len(self.conversation_history) < 2:
            return ""

        # Create concise summary of last few exchanges
        recent_messages = self.conversation_history[-4:]
        summary = "Recent conversation topics: " + ", ".join(recent_messages[:2])
        return summary

    def _update_conversation_history(self, message: str):
        """Update conversation history for context"""

        # Keep last N messages for context
        self.conversation_history.append(message)
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]


class CandidateAgentWithPersona(PersonaEnhancedAgentMixin):
    """
    CandidateAgent enhanced with persona system

    This mixin should be applied to the existing CandidateAgent class
    """

    async def respond_with_persona(
        self,
        message: str,
        user_id: str,
        session_id: str,
        chat_mode: str = "general"
    ) -> Dict[str, Any]:
        """
        Respond with persona enhancement

        Args:
            message: User message
            user_id: User ID
            session_id: Chat session ID
            chat_mode: Chat mode (general, career_coach, interview_prep, etc.)

        Returns:
            Response with persona-aware content
        """

        # Build persona-aware system prompt
        enhanced_prompt, active_persona = self._build_persona_aware_system_prompt(
            base_system_prompt=self.system_prompt,
            user_id=user_id,
            user_role=UserRole.candidate,
            last_message=message
        )

        # Call parent respond method with enhanced prompt
        # (This would be customized based on actual agent implementation)
        response = await self._respond_with_prompt(
            message=message,
            system_prompt=enhanced_prompt,
            session_id=session_id,
            chat_mode=chat_mode
        )

        # Adapt response based on persona
        adapted_response = self.adapt_response(response, active_persona)

        # Update conversation history
        self._update_conversation_history(message)

        return {
            "response": adapted_response,
            "persona": {
                "id": active_persona.id,
                "name": active_persona.name,
                "title": active_persona.title
            },
            "mode": self.persona_system.active_contexts[user_id].conversation_mode.value
        }


class RecruiterAgentWithPersona(PersonaEnhancedAgentMixin):
    """
    RecruiterAgent enhanced with persona system
    """

    async def respond_with_persona(
        self,
        message: str,
        user_id: str,
        company_id: str,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Respond with persona enhancement

        Args:
            message: User message
            user_id: User ID
            company_id: Company ID
            session_id: Chat session ID

        Returns:
            Response with persona-aware content
        """

        # Store company_id for context loading
        self.company_id = company_id

        # Build persona-aware system prompt
        enhanced_prompt, active_persona = self._build_persona_aware_system_prompt(
            base_system_prompt=self.system_prompt,
            user_id=user_id,
            user_role=UserRole.recruiter,
            last_message=message
        )

        # Call parent respond method with enhanced prompt
        response = await self._respond_with_prompt(
            message=message,
            system_prompt=enhanced_prompt,
            session_id=session_id
        )

        # Adapt response based on persona
        adapted_response = self.adapt_response(response, active_persona)

        # Update conversation history
        self._update_conversation_history(message)

        return {
            "response": adapted_response,
            "persona": {
                "id": active_persona.id,
                "name": active_persona.name,
                "title": active_persona.title
            },
            "objective": self.persona_system.active_contexts[user_id].current_objective,
            "mode": self.persona_system.active_contexts[user_id].conversation_mode.value
        }


class PersonaAnalytics:
    """Analytics for persona usage and effectiveness"""

    def __init__(self, db_session):
        self.db = db_session

    async def track_persona_usage(
        self,
        user_id: str,
        persona_id: str,
        objective: str,
        mode: str,
        effectiveness_score: float
    ):
        """Track persona usage and effectiveness"""
        # TODO: Implement tracking in database

        logger.info(
            f"Persona usage - User: {user_id}, Persona: {persona_id}, "
            f"Objective: {objective}, Mode: {mode}, Effectiveness: {effectiveness_score}"
        )

    async def get_persona_recommendations(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """Get persona recommendations based on user history"""
        # TODO: Analyze usage patterns and recommend optimal personas

        return {
            "primary_persona": "career_coach",
            "alternative_personas": ["interview_coach", "application_optimizer"],
            "confidence": 0.92,
            "reasoning": "Based on previous interactions and conversation patterns"
        }
