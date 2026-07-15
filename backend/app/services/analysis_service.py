"""Analysis Service - Phase 3 orchestration."""
from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.analysis_agent import AnalysisAgent
from app.models.analysis_result import AnalysisResult, AnalysisStatus
from app.models.assessment import Assessment
from app.models.assessment_design import AssessmentDesign

logger = logging.getLogger("truematch.analysis_service")


class AnalysisService:
    """Service for managing analysis pipeline.

    Responsibilities:
    - Initiate analysis for completed assessments
    - Query pending analysis
    - Approve/review analysis results
    - Generate reports
    """

    def __init__(self, db: AsyncSession):
        """Initialize analysis service.

        Args:
            db: Async database session
        """
        self.db = db
        self.agent = AnalysisAgent(db)

    async def initiate_analysis(self, assessment_id: UUID) -> AnalysisResult:
        """Initiate analysis for a completed assessment.

        Args:
            assessment_id: Assessment ID to analyze

        Returns:
            AnalysisResult record (status: pending_analysis)

        Raises:
            ValueError: If assessment not found
        """
        # Load assessment
        assessment = await self.db.execute(
            select(Assessment).where(Assessment.id == assessment_id)
        )
        assessment = assessment.scalar_one_or_none()

        if not assessment:
            raise ValueError(f"Assessment {assessment_id} not found")

        # Load assessment design
        design = await self.db.execute(
            select(AssessmentDesign).where(AssessmentDesign.id == assessment.id)
        )
        design = design.scalar_one_or_none()

        if not design:
            raise ValueError(f"Assessment design not found")

        # Create analysis result record
        analysis = AnalysisResult(
            assessment_id=assessment.id,
            assessment_design_id=design.id,
            candidate_id=assessment.user_id,
            position_id=assessment.position_id,
            status=AnalysisStatus.pending_analysis,
        )

        self.db.add(analysis)
        await self.db.flush()

        logger.info(f"Initiated analysis {analysis.id} for assessment {assessment_id}")

        return analysis

    async def get_pending_analysis(
        self, page: int = 1, limit: int = 10
    ) -> tuple[list[AnalysisResult], dict]:
        """Get pending analysis results (recruiter queue).

        Args:
            page: Page number (1-indexed)
            limit: Results per page (max 100)

        Returns:
            (list of analysis results, pagination info)
        """
        # Query pending analysis
        query = select(AnalysisResult).where(
            AnalysisResult.status == AnalysisStatus.pending_analysis
        )

        # Pagination
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)

        results = await self.db.execute(query)
        analyses = results.scalars().all()

        # Count total
        count_query = select(AnalysisResult).where(
            AnalysisResult.status == AnalysisStatus.pending_analysis
        )
        count = await self.db.execute(count_query)
        total = len(count.scalars().all())

        pagination = {
            "page": page,
            "limit": limit,
            "total": total,
            "pages": (total + limit - 1) // limit,
        }

        return analyses, pagination

    async def get_analysis_result(self, analysis_id: UUID) -> AnalysisResult:
        """Get full analysis result details.

        Args:
            analysis_id: Analysis result ID

        Returns:
            AnalysisResult record

        Raises:
            ValueError: If not found
        """
        result = await self.db.execute(
            select(AnalysisResult).where(AnalysisResult.id == analysis_id)
        )
        result = result.scalar_one_or_none()

        if not result:
            raise ValueError(f"Analysis result {analysis_id} not found")

        return result

    async def approve_analysis(
        self, analysis_id: UUID, recruiter_id: UUID, notes: str | None = None
    ) -> AnalysisResult:
        """Recruiter approves analysis result.

        Args:
            analysis_id: Analysis result ID
            recruiter_id: Recruiter user ID
            notes: Optional recruiter notes

        Returns:
            Updated AnalysisResult

        Raises:
            ValueError: If not found or already reviewed
        """
        result = await self.get_analysis_result(analysis_id)

        if result.recruiter_reviewed:
            raise ValueError(f"Analysis {analysis_id} already reviewed")

        result.recruiter_reviewed = True
        result.recruiter_review_at = __import__("datetime").datetime.utcnow()
        result.recruiter_notes = notes

        await self.db.commit()

        logger.info(f"Recruiter {recruiter_id} approved analysis {analysis_id}")

        return result

    async def get_fairness_report(self, analysis_id: UUID) -> dict:
        """Get fairness analysis report.

        Args:
            analysis_id: Analysis result ID

        Returns:
            Fairness report dict

        Raises:
            ValueError: If not found
        """
        result = await self.get_analysis_result(analysis_id)

        fairness = result.analysis_fairness_check or {}

        return {
            "analysis_id": str(analysis_id),
            "fairness_score": fairness.get("fairness_score", 0),
            "passed": fairness.get("passed", False),
            "bias_indicators": fairness.get("bias_indicators", []),
            "issues": fairness.get("issues", []),
        }


__all__ = ["AnalysisService"]
