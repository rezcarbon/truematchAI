"""
Training Chat Engine - Process conversational training feedback.

Handles:
- Claude-powered intelligent responses
- Training signal extraction from messages
- Multi-turn conversation context
- Feedback type detection
"""
import json
import logging
from typing import Optional

from app.clients.claude_client import ClaudeClient

logger = logging.getLogger(__name__)


class TrainingChatEngine:
    """Process training chat interactions."""

    FEEDBACK_TYPES = {
        "capability_suggestion": "Suggest new capability or improve existing one",
        "mapping_correction": "Correct or improve capability/keyword mapping",
        "credential_equivalency": "Learn credential equivalencies",
        "pattern_discovery": "Discover success pattern or correlation",
        "scoring_adjustment": "Suggest reweighting of matching factors",
        "domain_insight": "Industry or role-specific learning",
    }

    def __init__(self, claude_client: Optional[ClaudeClient] = None):
        self.claude = claude_client or ClaudeClient()

    async def process_message(
        self,
        user_message: str,
        conversation_history: list[dict],
    ) -> dict:
        """
        Process a training message and extract learning signals.

        Args:
            user_message: User's training feedback message
            conversation_history: Previous messages in session

        Returns:
            Dict with ai_response, extracted_signal, feedback_type
        """
        try:
            # Build conversation context
            context_text = self._build_conversation_context(conversation_history)

            # Generate AI response and extract training signal
            response, signal = await self._generate_response_and_signal(
                user_message, context_text
            )

            # Detect feedback type
            feedback_type = await self._detect_feedback_type(user_message, signal)

            logger.info(
                f"Processed training message",
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
                "ai_response": f"I encountered an error processing your message. Please try again.",
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
        """
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
            response = await self.claude.send_message(prompt, max_tokens=1000)

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
                logger.warning(f"Failed to parse Claude response as JSON")
                return response, None

        except Exception as e:
            logger.error(f"Error calling Claude: {e}")
            return f"I'm having trouble processing your request: {str(e)}", None

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
        """
        if not signal:
            return None

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
            response = await self.claude.send_message(prompt, max_tokens=50)
            response = response.strip().lower()

            # Find best match
            for category in self.FEEDBACK_TYPES.keys():
                if category in response:
                    return category

            return None

        except Exception as e:
            logger.error(f"Error detecting feedback type: {e}")
            return None

    def _build_conversation_context(self, history: list[dict]) -> str:
        """Build context from conversation history."""
        if not history:
            return "This is the start of the conversation."

        context_lines = ["Recent conversation:"]
        for msg in history[-4:]:  # Last 4 messages
            role = "User" if msg.get("role") == "user" else "Assistant"
            context_lines.append(f"{role}: {msg.get('content', '')[:200]}")

        return "\n".join(context_lines)

    async def analyze_learning_impact(
        self,
        feedback_history: list[dict],
    ) -> dict:
        """
        Analyze the cumulative impact of training feedback.

        Returns insights about what the system has learned.
        """
        if not feedback_history:
            return {"impact": "No feedback yet"}

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
            response = await self.claude.send_message(prompt, max_tokens=500)

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
