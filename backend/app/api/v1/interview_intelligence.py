"""Interview Intelligence API - Real-time interview analysis and automation.

Endpoints for generating interview prep, analyzing transcripts, and standardizing feedback.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.ml.interview_intelligence import InterviewIntelligenceService

router = APIRouter(prefix="/api/v1/interview-intelligence", tags=["interview"])


class InterviewPrepRequest(BaseModel):
    """Request interview preparation materials."""

    candidate_id: UUID = Field(..., description="Candidate UUID")
    position_id: UUID = Field(..., description="Position UUID")
    candidate_name: str = Field(..., description="Candidate name")
    candidate_background: str = Field(..., description="Background summary")
    position_title: str = Field(..., description="Position title")
    key_requirements: list[str] = Field(..., description="Key job requirements")


class InterviewPrepResponse(BaseModel):
    """Interview preparation materials."""

    talking_points: list[dict]
    questions: list[dict]
    estimated_duration_minutes: int


@router.post("/prep", response_model=InterviewPrepResponse)
async def generate_interview_prep(
    request: InterviewPrepRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate personalized interview preparation materials.

    Returns:
    - Talking points for recruiter
    - Interview questions mapped to job requirements
    - Estimated interview duration
    - Suggested follow-up questions
    """
    try:
        service = InterviewIntelligenceService(db)

        prep = await service.generate_interview_prep(
            candidate_id=request.candidate_id,
            position_id=request.position_id,
            candidate_name=request.candidate_name,
            candidate_background=request.candidate_background,
            position_title=request.position_title,
            key_requirements=request.key_requirements,
        )

        if "error" in prep:
            raise HTTPException(status_code=500, detail=prep["error"])

        return InterviewPrepResponse(**prep)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Interview prep error: {str(e)}")


class InterviewFeedbackRequest(BaseModel):
    """Submit interview feedback."""

    candidate_id: UUID
    interview_date: datetime
    communication_score: int = Field(..., ge=1, le=5)
    technical_score: int = Field(..., ge=1, le=5)
    cultural_fit_score: int = Field(..., ge=1, le=5)
    overall_score: int = Field(..., ge=1, le=5)
    recommendation: str = Field(..., description="strong_yes, yes, maybe, no, strong_no")
    strengths: list[str] = []
    concerns: list[str] = []
    notes: str = ""
    interview_duration_minutes: int = 60


class InterviewAnalysisResponse(BaseModel):
    """Interview analysis results."""

    interview_id: str
    candidate_id: str
    position_id: str
    preparation_quality: float
    communication_effectiveness: float
    skills_alignment: float
    cultural_fit_score: float
    recommended_next_step: str
    confidence: float
    created_at: str


@router.post("/feedback", response_model=InterviewAnalysisResponse)
async def submit_interview_feedback(
    request: InterviewFeedbackRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit and analyze interview feedback.

    Standardizes feedback to consistent rubric and provides:
    - Structured analysis of interview performance
    - Recommended next steps (advance, discuss, reject)
    - Confidence score on recommendation
    """
    try:
        from app.ml.interview_intelligence import InterviewFeedback

        service = InterviewIntelligenceService(db)

        # Create feedback object
        feedback = InterviewFeedback(
            interviewer_id=str(user.id),
            candidate_id=str(request.candidate_id),
            interview_date=request.interview_date,
            communication_score=request.communication_score,
            technical_score=request.technical_score,
            cultural_fit_score=request.cultural_fit_score,
            overall_score=request.overall_score,
            recommendation=request.recommendation,
            strengths=request.strengths,
            concerns=request.concerns,
            notes=request.notes,
            interview_duration_minutes=request.interview_duration_minutes,
        )

        # Analyze interview
        analysis = await service.analyze_interview(
            candidate_id=request.candidate_id,
            position_id=UUID("00000000-0000-0000-0000-000000000000"),  # Would get from request
            feedback=feedback,
        )

        if not analysis:
            raise HTTPException(status_code=500, detail="Failed to analyze interview")

        return InterviewAnalysisResponse(**analysis.to_dict())

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Feedback analysis error: {str(e)}")


class TranscriptionFetchRequest(BaseModel):
    """Request to fetch interview transcription."""

    recording_id: str = Field(..., description="Recording ID from transcription service")
    service: str = Field(default="otter", description="Transcription service (otter or fireflies)")


@router.post("/transcription/fetch")
async def fetch_interview_transcription(
    request: TranscriptionFetchRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Fetch interview transcription from external service.

    Supports:
    - Otter.ai
    - Fireflies.io

    Returns:
    - Transcript text
    - Word count
    - Sentiment analysis
    - Key phrases and themes
    """
    try:
        service = InterviewIntelligenceService(db)

        transcript = await service.get_interview_recording(
            recording_id=request.recording_id,
            service=request.service,
        )

        if not transcript:
            raise HTTPException(
                status_code=404,
                detail=f"Could not fetch transcription from {request.service}",
            )

        return {
            "recording_id": request.recording_id,
            "service": request.service,
            "transcript": transcript,
            "word_count": len(transcript.split()),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription error: {str(e)}")


__all__ = ["router"]
