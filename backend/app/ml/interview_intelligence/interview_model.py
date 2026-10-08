"""Interview Intelligence Model - Real-time interview analysis and automation.

Provides:
- Interview preparation (talking points, questions)
- Real-time transcription integration (Otter.ai, Fireflies.io)
- Interview analysis (sentiment, structure, key signals)
- Feedback standardization (consistent rubrics)
- Panel performance analytics
"""

import logging
from dataclasses import dataclass, field
from typing import Optional, Dict, List
from datetime import datetime
from enum import Enum
import asyncio

logger = logging.getLogger(__name__)


class InterviewPhase(str, Enum):
    """Interview lifecycle phases."""

    preparation = "preparation"
    in_progress = "in_progress"
    completed = "completed"
    analysis = "analysis"


class InterviewQuality(str, Enum):
    """Interview quality assessment."""

    excellent = "excellent"
    good = "good"
    fair = "fair"
    poor = "poor"


@dataclass
class InterviewTalkingPoint:
    """Talking point for interview preparation."""

    topic: str
    key_message: str
    supporting_details: List[str]
    estimated_duration_minutes: int = 5


@dataclass
class InterviewQuestion:
    """Interview question mapped to job requirements."""

    question: str
    category: str  # behavioral, technical, cultural, competency
    required_skill: str
    difficulty: str  # junior, mid, senior
    suggested_follow_ups: List[str] = field(default_factory=list)


@dataclass
class InterviewFeedback:
    """Standardized interview feedback."""

    interviewer_id: str
    candidate_id: str
    interview_date: datetime

    # Structured feedback on key dimensions
    communication_score: int  # 1-5
    technical_score: int  # 1-5
    cultural_fit_score: int  # 1-5
    overall_score: int  # 1-5

    # Recommendation
    recommendation: str  # strong_yes, yes, maybe, no, strong_no

    # Free-form notes
    strengths: List[str]
    concerns: List[str]
    notes: str

    # Metadata
    interview_duration_minutes: int
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class TranscriptAnalysis:
    """Analysis of interview transcript."""

    transcript_text: str
    word_count: int

    # Sentiment analysis
    overall_sentiment: str  # positive, neutral, negative
    sentiment_progression: List[Dict]  # sentiment over time

    # Speech analysis
    speaking_pace: str  # slow, normal, fast
    clarity_score: float  # 0-1
    confidence_indicators: int  # count of confidence signals

    # Content analysis
    relevant_examples: int  # STAR method examples
    technical_accuracy: float  # 0-1
    communication_structure: str  # well_structured, adequate, disorganized

    # Key signals
    key_achievements: List[str]
    skills_demonstrated: List[str]
    red_flags: List[str]


@dataclass
class InterviewAnalysis:
    """Complete interview analysis."""

    interview_id: str
    candidate_id: str
    position_id: str

    # Transcription
    has_transcript: bool
    transcript_analysis: Optional[TranscriptAnalysis] = None

    # Feedback
    interviewer_feedback: Optional[InterviewFeedback] = None

    # AI analysis
    preparation_quality: float  # 0-1
    communication_effectiveness: float  # 0-1
    skills_alignment: float  # 0-1
    cultural_fit_score: float  # 0-1

    # Recommendation
    recommended_next_step: str  # advance, further_discussion, reject
    confidence: float  # 0-1

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self):
        """Serialize to dictionary."""
        return {
            "interview_id": self.interview_id,
            "candidate_id": self.candidate_id,
            "position_id": self.position_id,
            "has_transcript": self.has_transcript,
            "preparation_quality": round(self.preparation_quality, 2),
            "communication_effectiveness": round(self.communication_effectiveness, 2),
            "skills_alignment": round(self.skills_alignment, 2),
            "cultural_fit_score": round(self.cultural_fit_score, 2),
            "recommended_next_step": self.recommended_next_step,
            "confidence": round(self.confidence, 2),
            "created_at": self.created_at.isoformat(),
        }


class InterviewIntelligence:
    """ML model for interview intelligence and analysis."""

    def __init__(
        self,
        otter_api_key: Optional[str] = None,
        fireflies_api_key: Optional[str] = None,
    ):
        self.otter_api_key = otter_api_key
        self.fireflies_api_key = fireflies_api_key

    async def generate_interview_prep(
        self,
        candidate_name: str,
        candidate_background: str,
        position_title: str,
        key_requirements: List[str],
    ) -> Dict:
        """
        Generate interview preparation materials for recruiter.

        Args:
            candidate_name: Candidate name
            candidate_background: Background summary
            position_title: Position title
            key_requirements: Key job requirements

        Returns:
            Dict with talking points and questions
        """
        try:
            # Generate talking points
            talking_points = await self._generate_talking_points(
                candidate_name, candidate_background, position_title
            )

            # Generate questions
            questions = await self._generate_interview_questions(
                position_title, key_requirements
            )

            return {
                "talking_points": talking_points,
                "questions": questions,
                "estimated_duration_minutes": sum(tp.estimated_duration_minutes for tp in talking_points) + (len(questions) * 5),
            }

        except Exception as e:
            logger.error(f"Error generating interview prep: {e}")
            return {"error": str(e)}

    async def _generate_talking_points(
        self, candidate_name: str, background: str, position: str
    ) -> List[InterviewTalkingPoint]:
        """Generate talking points for candidate interview."""
        # In production, this would use Claude API to generate contextual talking points
        return [
            InterviewTalkingPoint(
                topic="Role Overview",
                key_message=f"The {position} role is critical to our team's success",
                supporting_details=[
                    "Team structure and reporting lines",
                    "Key responsibilities",
                    "Success metrics",
                ],
                estimated_duration_minutes=5,
            ),
            InterviewTalkingPoint(
                topic="Candidate Background",
                key_message=f"Welcome {candidate_name}! Tell us about your journey",
                supporting_details=[
                    "Career progression",
                    "Relevant experience",
                    "Achievements",
                ],
                estimated_duration_minutes=10,
            ),
            InterviewTalkingPoint(
                topic="Skill Validation",
                key_message="Let's explore your technical and soft skills",
                supporting_details=[
                    "Technical depth",
                    "Problem-solving approach",
                    "Collaboration style",
                ],
                estimated_duration_minutes=15,
            ),
        ]

    async def _generate_interview_questions(
        self, position: str, requirements: List[str]
    ) -> List[InterviewQuestion]:
        """Generate interview questions mapped to job requirements."""
        return [
            InterviewQuestion(
                question="Tell me about a time you solved a complex problem in your previous role.",
                category="behavioral",
                required_skill="Problem-solving",
                difficulty="mid",
                suggested_follow_ups=[
                    "What was the outcome?",
                    "What would you do differently?",
                ],
            ),
            InterviewQuestion(
                question="How do you approach learning new technologies?",
                category="competency",
                required_skill="Learning Agility",
                difficulty="mid",
                suggested_follow_ups=[
                    "Give me an example",
                    "What resources do you use?",
                ],
            ),
            InterviewQuestion(
                question="Describe your ideal team environment.",
                category="cultural",
                required_skill="Team Collaboration",
                difficulty="junior",
                suggested_follow_ups=[
                    "Why is that important to you?",
                    "Tell me about a great team you've been part of",
                ],
            ),
        ]

    async def analyze_transcript(self, transcript_text: str) -> TranscriptAnalysis:
        """
        Analyze interview transcript for key signals.

        Args:
            transcript_text: Full interview transcript

        Returns:
            TranscriptAnalysis with insights
        """
        try:
            # In production, would use NLP/AI for actual analysis
            # For now, return structured analysis framework

            word_count = len(transcript_text.split())

            # Count STAR method examples (heuristic)
            star_keywords = ["situation", "task", "action", "result"]
            star_count = sum(
                transcript_text.lower().count(kw) for kw in star_keywords
            )

            return TranscriptAnalysis(
                transcript_text=transcript_text,
                word_count=word_count,
                overall_sentiment="neutral",  # Would use sentiment analysis
                sentiment_progression=[],
                speaking_pace="normal",
                clarity_score=0.75,
                confidence_indicators=star_count,
                relevant_examples=star_count // 4,
                technical_accuracy=0.8,
                communication_structure="adequate",
                key_achievements=[],
                skills_demonstrated=[],
                red_flags=[],
            )

        except Exception as e:
            logger.error(f"Error analyzing transcript: {e}")
            raise

    def score_interview_feedback(
        self, feedback: InterviewFeedback
    ) -> InterviewAnalysis:
        """
        Score and analyze interview feedback.

        Args:
            feedback: Interview feedback from recruiter

        Returns:
            InterviewAnalysis with recommendations
        """
        # Calculate dimensions from feedback
        avg_score = (
            feedback.communication_score +
            feedback.technical_score +
            feedback.cultural_fit_score
        ) / 3

        # Map recommendation to next steps
        recommendation_map = {
            "strong_yes": "advance",
            "yes": "advance",
            "maybe": "further_discussion",
            "no": "reject",
            "strong_no": "reject",
        }

        return InterviewAnalysis(
            interview_id=f"interview_{feedback.candidate_id}",
            candidate_id=feedback.candidate_id,
            position_id="",  # Would be provided
            has_transcript=False,
            interviewer_feedback=feedback,
            preparation_quality=0.8,
            communication_effectiveness=feedback.communication_score / 5,
            skills_alignment=feedback.technical_score / 5,
            cultural_fit_score=feedback.cultural_fit_score / 5,
            recommended_next_step=recommendation_map.get(feedback.recommendation, "further_discussion"),
            confidence=min(1.0, avg_score / 5),
        )

    async def fetch_transcription(
        self, interview_recording_id: str, service: str = "otter"
    ) -> Optional[str]:
        """
        Fetch transcription from external service.

        Args:
            interview_recording_id: Recording ID from external service
            service: Transcription service (otter or fireflies)

        Returns:
            Transcript text or None if unavailable
        """
        try:
            if service == "otter" and self.otter_api_key:
                return await self._fetch_from_otter(interview_recording_id)
            elif service == "fireflies" and self.fireflies_api_key:
                return await self._fetch_from_fireflies(interview_recording_id)
            else:
                logger.warning(f"Service {service} not configured")
                return None

        except Exception as e:
            logger.error(f"Error fetching transcription: {e}")
            return None

    async def _fetch_from_otter(self, recording_id: str) -> Optional[str]:
        """Fetch transcription from Otter.ai."""
        # Would implement Otter.ai API call
        logger.info(f"Fetching transcription from Otter: {recording_id}")
        return None

    async def _fetch_from_fireflies(self, recording_id: str) -> Optional[str]:
        """Fetch transcription from Fireflies.io."""
        # Would implement Fireflies.io API call
        logger.info(f"Fetching transcription from Fireflies: {recording_id}")
        return None


__all__ = ["InterviewIntelligence", "InterviewAnalysis", "InterviewFeedback"]
