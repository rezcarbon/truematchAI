"""
Training Chat Engine - Process conversational training feedback.

Handles:
- Claude-powered intelligent responses
- Training signal extraction from messages
- Multi-turn conversation context
- Feedback type detection
- Access to candidate resumes and job descriptions
"""
import json
import logging
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.engines.client import ClaudeClient, is_live
from app.models.resume import Resume
from app.models.position import Position

logger = logging.getLogger(__name__)


class TrainingChatEngine:
    """Process training chat interactions with access to resumes and job descriptions."""

    FEEDBACK_TYPES = {
        "capability_suggestion": "Suggest new capability or improve existing one",
        "mapping_correction": "Correct or improve capability/keyword mapping",
        "credential_equivalency": "Learn credential equivalencies",
        "pattern_discovery": "Discover success pattern or correlation",
        "scoring_adjustment": "Suggest reweighting of matching factors",
        "domain_insight": "Industry or role-specific learning",
    }

    def __init__(self, claude_client: Optional[ClaudeClient] = None, db: Optional[AsyncSession] = None):
        self.claude = claude_client or ClaudeClient()
        self.db = db

    async def _load_available_documents(self, user_id: UUID) -> tuple[list[dict], list[dict]]:
        """Load recent resumes and positions for context."""
        resumes = []
        positions = []

        if not self.db:
            return resumes, positions

        try:
            # Load recent resumes
            resume_query = select(Resume).where(
                Resume.user_id == user_id
            ).order_by(Resume.created_at.desc()).limit(3)
            resume_result = await self.db.execute(resume_query)
            for resume in resume_result.scalars().all():
                resumes.append({
                    "id": str(resume.id),
                    "narrative": (resume.raw_narrative or "")[:500],  # First 500 chars
                    "parsed": resume.parsed_data or {},
                })

            # Load recent positions
            position_query = select(Position).where(
                Position.created_by == user_id
            ).order_by(Position.created_at.desc()).limit(5)
            position_result = await self.db.execute(position_query)
            for position in position_result.scalars().all():
                positions.append({
                    "id": str(position.id),
                    "title": position.title or "",
                    "description": (position.description or "")[:500],  # First 500 chars
                    "requirements": position.parsed_requirements or {},
                })
        except Exception as e:
            logger.warning(f"Failed to load documents: {e}")

        return resumes, positions

    async def process_message(
        self,
        user_message: str,
        conversation_history: list[dict],
        user_id: Optional[UUID] = None,
    ) -> dict:
        """
        Process a training message and extract learning signals.

        Args:
            user_message: User's training feedback message
            conversation_history: Previous messages in session
            user_id: User ID to load documents for context

        Returns:
            Dict with ai_response, extracted_signal, feedback_type
        """
        try:
            # Load available resumes and positions
            resumes, positions = [], []
            if user_id:
                resumes, positions = await self._load_available_documents(user_id)

            # Build conversation context with documents
            context_text = self._build_conversation_context(conversation_history, resumes, positions)

            # Generate AI response and extract training signal
            response, signal = await self._generate_response_and_signal(
                user_message, context_text
            )

            # Detect feedback type
            feedback_type = await self._detect_feedback_type(user_message, signal)

            logger.info(
                "Processed training message",
                extra={
                    "message_length": len(user_message),
                    "feedback_type": feedback_type,
                    "signal_keys": list(signal.keys()) if signal else [],
                },
            )

            return {
                "ai_response": response,
                "extracted_training_signal": signal,
                "feedback_type": feedback_type,
            }

        except Exception as e:
            logger.error(f"Error processing training message: {e}")
            return {
                "ai_response": "I encountered an error processing your message. Please try again.",
                "extracted_training_signal": None,
                "feedback_type": None,
                "error": str(e),
            }

    async def _generate_response_and_signal(
        self,
        user_message: str,
        context_text: str,
    ) -> tuple[str, Optional[dict]]:
        """
        Generate intelligent response and extract training signal.

        Uses Claude to:
        1. Generate conversational response
        2. Extract structured training signal

        Falls back to mock responses when Claude API is not available.
        """
        # Check if Claude API is available
        if not is_live():
            logger.info("Claude API not configured, using mock training responses")
            return await self._generate_mock_response_async(user_message)

        prompt = f"""You are an AI training system for recruitment matching. Your role is to:
1. Understand recruiter/trainer feedback about hiring decisions and candidate assessments
2. Learn from their insights to improve matching algorithms
3. Ask clarifying questions to extract actionable learning signals
4. Provide intelligent, context-aware responses

{context_text}

User says: "{user_message}"

Respond with a JSON object containing:
{{
  "response": "Your conversational response to the user",
  "signal": {{
    "type": "one of: new_capability, credential_map, success_pattern, scoring_rule",
    "description": "What the user is trying to teach",
    "affected_area": "What part of matching this affects (e.g., 'backend_skills', 'team_leadership')",
    "confidence": 0.0-1.0,
    "action": "Specific action the system should take"
  }}
}}

Be conversational and helpful. Extract signals even from informal feedback."""

        try:
            response = self.claude.analyze(prompt, max_tokens=1000)

            # Parse response
            try:
                json_start = response.find("{")
                json_end = response.rfind("}") + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = response[json_start:json_end]
                    parsed = json.loads(json_str)
                    return (
                        parsed.get("response", response),
                        parsed.get("signal"),
                    )
            except (json.JSONDecodeError, ValueError):
                logger.warning("Failed to parse Claude response as JSON")
                return response, None

        except Exception as e:
            logger.error(f"Error calling Claude: {e}")
            return f"I'm having trouble processing your request: {str(e)}", None

    async def _generate_mock_response_async(self, user_message: str) -> tuple[str, Optional[dict]]:
        """
        Generate mock training response when Claude API is not available.

        Provides realistic mock responses for development/testing.
        """
        # Simple heuristics to detect message type and respond appropriately
        message_lower = user_message.lower()

        # Detect various feedback types
        if any(word in message_lower for word in ["should match", "should hire", "good fit"]):
            signal_type = "pattern_discovery"
            description = f"Positive match signal from user feedback: {user_message[:100]}"
            affected_area = "matching_confidence"
        elif any(word in message_lower for word in ["why", "explain", "how", "clarify"]):
            signal_type = "scoring_adjustment"
            description = f"User requested clarification on scoring: {user_message[:100]}"
            affected_area = "transparency"
        elif any(word in message_lower for word in ["skill", "experience", "credential", "expertise"]):
            signal_type = "credential_map"
            description = f"User providing skill/credential mapping feedback: {user_message[:100]}"
            affected_area = "skill_mapping"
        else:
            signal_type = "capability_suggestion"
            description = f"User providing training feedback: {user_message[:100]}"
            affected_area = "general_capabilities"

        mock_signal = {
            "type": signal_type,
            "description": description,
            "affected_area": affected_area,
            "confidence": 0.7,  # Moderate confidence for mock responses
            "action": "Learn from training feedback and update matching weights"
        }

        # Generate conversational response
        response = "Thank you for that feedback. I've captured your insight about candidate matching and capability assessment. "
        response += f"Signal Type: {signal_type}. Affected Area: {affected_area}. "
        response += "This feedback will help improve future assessments. Do you have additional training examples?"

        return response, mock_signal

    async def _detect_feedback_type(
        self,
        user_message: str,
        signal: Optional[dict],
    ) -> Optional[str]:
        """
        Detect the type of training feedback.

        Analyzes message to categorize as:
        - capability_suggestion
        - mapping_correction
        - credential_equivalency
        - pattern_discovery
        - scoring_adjustment
        - domain_insight

        Falls back to mock detection when Claude API is not available.
        """
        if not signal:
            return None

        # Use mock detection if API is not available
        if not is_live():
            logger.info("Claude API not configured, using mock feedback type detection")
            return self._detect_feedback_type_mock(user_message, signal)

        prompt = f"""Categorize this training feedback into one category:

Message: "{user_message}"

Signal: {json.dumps(signal)}

Categories:
- capability_suggestion: Teaching a new capability or improvement
- mapping_correction: Fixing keyword/credential to capability mapping
- credential_equivalency: Learning that credentials are equivalent
- pattern_discovery: Finding correlation or success pattern
- scoring_adjustment: Suggesting reweighting of factors
- domain_insight: Industry/role-specific learning

Respond with ONLY the category name, nothing else."""

        try:
            response = self.claude.analyze(prompt, max_tokens=50)
            response = response.strip().lower()

            # Find best match
            for category in self.FEEDBACK_TYPES.keys():
                if category in response:
                    return category

            return None

        except Exception as e:
            logger.error(f"Error detecting feedback type: {e}")
            return None

    def _detect_feedback_type_mock(self, user_message: str, signal: Optional[dict]) -> Optional[str]:
        """
        Mock feedback type detection for when Claude API is not available.

        Uses simple heuristics to categorize feedback.
        """
        if not signal:
            return None

        signal_type = signal.get("type", "").lower()
        message_lower = user_message.lower()

        # Map signal types to feedback categories
        if "credential" in signal_type or "equivalency" in message_lower:
            return "credential_equivalency"
        elif "skill" in signal_type or "mapping" in message_lower or "map" in message_lower:
            return "mapping_correction"
        elif "pattern" in signal_type or "correlation" in message_lower:
            return "pattern_discovery"
        elif "scoring" in signal_type or "weight" in message_lower or "score" in message_lower:
            return "scoring_adjustment"
        elif "domain" in message_lower or "industry" in message_lower or "role" in message_lower:
            return "domain_insight"
        else:
            return "capability_suggestion"

    def _build_conversation_context(self, history: list[dict], resumes: list[dict] = None, positions: list[dict] = None) -> str:
        """
        Build context from conversation history and available documents.

        Args:
            history: Previous messages in conversation
            resumes: List of candidate resumes with id, narrative, parsed data
            positions: List of job descriptions with id, title, description, requirements
        """
        context_lines = []

        # Add available documents if provided
        if resumes:
            context_lines.append("Available Candidate Resumes:")
            for resume in resumes:
                context_lines.append(f"  - Resume {resume['id'][:8]}...: {resume['narrative'][:100]}...")
            context_lines.append("")

        if positions:
            context_lines.append("Available Job Descriptions:")
            for position in positions:
                context_lines.append(f"  - Position {position['id'][:8]}...: {position['title']}")
                context_lines.append(f"    {position['description'][:100]}...")
            context_lines.append("")

        # Add conversation history
        if history:
            context_lines.append("Recent conversation:")
            for msg in history[-4:]:  # Last 4 messages
                role = "User" if msg.get("role") == "user" else "Assistant"
                context_lines.append(f"{role}: {msg.get('content', '')[:200]}")
        else:
            if not context_lines:
                context_lines.append("This is the start of the conversation.")

        return "\n".join(context_lines)

    async def analyze_learning_impact(
        self,
        feedback_history: list[dict],
    ) -> dict:
        """
        Analyze the cumulative impact of training feedback.

        Returns insights about what the system has learned.
        Falls back to mock analysis when Claude API is not available.
        """
        if not feedback_history:
            return {"impact": "No feedback yet"}

        # Use mock analysis if API is not available
        if not is_live():
            logger.info("Claude API not configured, using mock learning impact analysis")
            return self._analyze_learning_impact_mock(feedback_history)

        feedback_text = "\n".join(
            [f"- {f.get('feedback_type', 'unknown')}: {f.get('description', '')}"
             for f in feedback_history[-10:]]
        )

        prompt = f"""Analyze this training feedback and estimate its impact on the recruitment matching system:

{feedback_text}

Provide a JSON response with:
{{
  "total_feedback_items": number,
  "dominant_themes": ["theme1", "theme2"],
  "estimated_model_improvement": "X% accuracy improvement",
  "coverage_areas": ["area1", "area2"],
  "next_learning_priorities": ["priority1", "priority2"]
}}"""

        try:
            response = self.claude.analyze(prompt, max_tokens=500)

            try:
                json_start = response.find("{")
                json_end = response.rfind("}") + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = response[json_start:json_end]
                    return json.loads(json_str)
            except (json.JSONDecodeError, ValueError):
                pass

            return {"analysis": response}

        except Exception as e:
            logger.error(f"Error analyzing learning impact: {e}")
            return {"error": str(e)}

    def _analyze_learning_impact_mock(self, feedback_history: list[dict]) -> dict:
        """
        Mock learning impact analysis for when Claude API is not available.

        Provides realistic mock metrics for development/testing.
        """
        if not feedback_history:
            return {"impact": "No feedback yet"}

        # Analyze feedback types
        feedback_types = {}
        for feedback in feedback_history:
            ftype = feedback.get("feedback_type", "unknown")
            feedback_types[ftype] = feedback_types.get(ftype, 0) + 1

        # Identify dominant themes
        dominant_themes = []
        if feedback_types:
            sorted_types = sorted(feedback_types.items(), key=lambda x: x[1], reverse=True)
            dominant_themes = [ftype for ftype, _ in sorted_types[:2]]

        # Estimate coverage areas
        coverage_areas = set()
        for feedback in feedback_history:
            desc = feedback.get("description", "").lower()
            if "skill" in desc or "backend" in desc or "frontend" in desc:
                coverage_areas.add("technical_skills")
            if "experience" in desc or "years" in desc:
                coverage_areas.add("experience_levels")
            if "leadership" in desc or "management" in desc:
                coverage_areas.add("leadership_traits")
            if "credential" in desc or "certification" in desc:
                coverage_areas.add("credentials")

        return {
            "total_feedback_items": len(feedback_history),
            "dominant_themes": dominant_themes or ["general_matching"],
            "estimated_model_improvement": f"{min(5 + len(feedback_history) * 0.5, 15):.1f}% accuracy improvement",
            "coverage_areas": list(coverage_areas) or ["general_capabilities"],
            "next_learning_priorities": [
                "Collect more feedback on senior-level positions",
                "Establish credential equivalency mappings",
                "Refine domain-specific matching rules"
            ]
        }
