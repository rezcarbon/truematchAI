"""Interview Intelligence Service - High-level orchestration."""

import logging
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from .interview_model import (
    InterviewIntelligence,
    InterviewAnalysis,
    InterviewFeedback,
)

logger = logging.getLogger(__name__)


class InterviewIntelligenceService:
    """Orchestrates interview intelligence for recruiters."""

    def __init__(
        self,
        db: AsyncSession,
        model: Optional[InterviewIntelligence] = None,
        otter_api_key: Optional[str] = None,
        fireflies_api_key: Optional[str] = None,
    ):
        self.db = db
        self.model = model or InterviewIntelligence(
            otter_api_key=otter_api_key,
            fireflies_api_key=fireflies_api_key,
        )

    async def generate_interview_prep(
        self,
        candidate_id: UUID,
        position_id: UUID,
        candidate_name: str,
        candidate_background: str,
        position_title: str,
        key_requirements: list[str],
    ) -> dict:
        """
        Generate personalized interview preparation materials.

        Args:
            candidate_id: Candidate UUID
            position_id: Position UUID
            candidate_name: Candidate name
            candidate_background: Background summary
            position_title: Position title
            key_requirements: Key job requirements

        Returns:
            Interview prep materials (talking points, questions, timeline)
        """
        try:
            prep = await self.model.generate_interview_prep(
                candidate_name, candidate_background, position_title, key_requirements
            )

            if "error" not in prep:
                # Store prep record in database (optional)
                logger.info(f"Generated prep for {candidate_name} for {position_title}")

            return prep

        except Exception as e:
            logger.error(f"Error generating interview prep: {e}")
            return {"error": str(e)}

    async def analyze_interview(
        self,
        candidate_id: UUID,
        position_id: UUID,
        transcript: Optional[str] = None,
        feedback: Optional[InterviewFeedback] = None,
    ) -> Optional[InterviewAnalysis]:
        """
        Analyze completed interview.

        Args:
            candidate_id: Candidate UUID
            position_id: Position UUID
            transcript: Interview transcript (optional)
            feedback: Interview feedback (optional)

        Returns:
            InterviewAnalysis with recommendations
        """
        try:
            # Start with transcript analysis if available
            transcript_analysis = None
            if transcript:
                transcript_analysis = await self.model.analyze_transcript(transcript)

            # Score interview based on feedback
            interview_analysis = None
            if feedback:
                interview_analysis = self.model.score_interview_feedback(feedback)
                interview_analysis.interview_id = f"interview_{candidate_id}"
                interview_analysis.position_id = str(position_id)
                interview_analysis.transcript_analysis = transcript_analysis

            return interview_analysis

        except Exception as e:
            logger.error(f"Error analyzing interview: {e}")
            return None

    async def get_interview_recording(
        self,
        recording_id: str,
        service: str = "otter",
    ) -> Optional[str]:
        """Get transcription from external service."""
        return await self.model.fetch_transcription(recording_id, service)

    async def standardize_feedback(
        self, interviewer_id: str, candidate_id: str, raw_feedback: dict
    ) -> InterviewFeedback:
        """
        Standardize interview feedback to consistent rubric.

        Args:
            interviewer_id: Interviewer ID
            candidate_id: Candidate ID
            raw_feedback: Raw feedback from interviewer

        Returns:
            Standardized InterviewFeedback
        """
        # Map raw feedback to structured format
        return InterviewFeedback(
            interviewer_id=interviewer_id,
            candidate_id=candidate_id,
            interview_date=raw_feedback.get("interview_date"),
            communication_score=raw_feedback.get("communication_score", 3),
            technical_score=raw_feedback.get("technical_score", 3),
            cultural_fit_score=raw_feedback.get("cultural_fit_score", 3),
            overall_score=raw_feedback.get("overall_score", 3),
            recommendation=raw_feedback.get("recommendation", "maybe"),
            strengths=raw_feedback.get("strengths", []),
            concerns=raw_feedback.get("concerns", []),
            notes=raw_feedback.get("notes", ""),
            interview_duration_minutes=raw_feedback.get("duration_minutes", 60),
        )


__all__ = ["InterviewIntelligenceService"]
