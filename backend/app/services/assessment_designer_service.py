"""Assessment Designer Service - Phase 2 orchestration layer."""
from __future__ import annotations

import logging
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assessment_design import AssessmentDesign, AssessmentDesignReviewStatus
from app.models.screening import ScreeningResult
from app.models.position import Position
from app.models.resume import Resume
from app.models.user import User
from app.agents.assessment_designer_agent import AssessmentDesignerAgent

logger = logging.getLogger("truematch.assessment_designer_service")


class AssessmentDesignerService:
    """
    High-level service for assessment design orchestration.

    Manages:
    - Design initiation
    - Agent coordination
    - Recruiter review workflow
    - Fairness reporting
    """

    def __init__(self, db: AsyncSession):
        """Initialize service with database session."""
        self.db = db
        self.agent = AssessmentDesignerAgent(db)

    async def initiate_design(
        self,
        screening_result_id: UUID,
        position_id: UUID,
    ) -> AssessmentDesign:
        """
        Initiate assessment design process.

        Args:
            screening_result_id: From Phase 1 screening
            position_id: Position to design assessment for

        Returns:
            AssessmentDesign record with pending_review status

        Raises:
            ValueError: If screening result or position not found
        """
        try:
            logger.info(f"Initiating design for screening {screening_result_id}")

            # Load screening result
            screening_result = await self.db.execute(
                select(ScreeningResult).where(
                    ScreeningResult.id == screening_result_id
                )
            )
            screening_result = screening_result.scalar_one_or_none()

            if not screening_result:
                raise ValueError(f"Screening result {screening_result_id} not found")

            # Load position
            position = await self.db.execute(
                select(Position).where(Position.id == position_id)
            )
            position = position.scalar_one_or_none()

            if not position:
                raise ValueError(f"Position {position_id} not found")

            # Load resume
            resume = await self.db.execute(
                select(Resume).where(Resume.id == screening_result.resume_id)
            )
            resume = resume.scalar_one_or_none()

            if not resume:
                raise ValueError(f"Resume not found")

            # Run agent design
            design_result = await self.agent.design_assessment(
                resume, position, str(screening_result_id)
            )

            # Create AssessmentDesign record
            assessment_design = AssessmentDesign(
                id=UUID(int=0),  # Will be generated
                position_id=position_id,
                candidate_id=screening_result.user_id,
                screening_result_id=screening_result_id,
                agent_design=design_result["agent_design"],
                design_fairness_check=design_result["design_fairness_check"],
                review_status=AssessmentDesignReviewStatus.pending_review,
            )

            self.db.add(assessment_design)
            await self.db.commit()

            logger.info(f"Design initiated: {assessment_design.id}")

            return assessment_design

        except Exception as e:
            logger.error(f"Error initiating design: {e}", exc_info=True)
            await self.db.rollback()
            raise

    async def get_pending_designs(
        self,
        page: int = 1,
        limit: int = 10,
        position_id: Optional[UUID] = None,
    ) -> tuple[list[AssessmentDesign], dict]:
        """
        Get pending designs for recruiter review.

        Args:
            page: Page number (1-indexed)
            limit: Results per page
            position_id: Optional filter by position

        Returns:
            (designs, pagination_info)
        """
        try:
            # Build query
            query = select(AssessmentDesign).where(
                AssessmentDesign.review_status == AssessmentDesignReviewStatus.pending_review
            )

            if position_id:
                query = query.where(
                    AssessmentDesign.position_id == position_id
                )

            # Order by created_at DESC (newest first)
            query = query.order_by(AssessmentDesign.created_at.desc())

            # Count total
            count_query = select(func.count(AssessmentDesign.id)).where(
                AssessmentDesign.review_status == AssessmentDesignReviewStatus.pending_review
            )
            if position_id:
                count_query = count_query.where(
                    AssessmentDesign.position_id == position_id
                )

            total = await self.db.execute(count_query)
            total = total.scalar() or 0

            # Paginate
            offset = (page - 1) * limit
            query = query.offset(offset).limit(limit)

            designs = await self.db.execute(query)
            designs = designs.scalars().all()

            pagination = {
                "total": total,
                "page": page,
                "limit": limit,
                "pages": (total + limit - 1) // limit,
            }

            return designs, pagination

        except Exception as e:
            logger.error(f"Error getting pending designs: {e}")
            return [], {"total": 0, "page": 1, "limit": limit, "pages": 0}

    async def approve_design(
        self,
        design_id: UUID,
        recruiter_id: UUID,
        recruiter_notes: Optional[str] = None,
        recruiter_confidence: Optional[int] = None,
    ) -> AssessmentDesign:
        """
        Recruiter approves assessment design.

        Creates Assessment record and links design.

        Args:
            design_id: AssessmentDesign ID
            recruiter_id: Recruiter approving
            recruiter_notes: Optional notes
            recruiter_confidence: Confidence (0-100)

        Returns:
            Updated AssessmentDesign record
        """
        try:
            logger.info(f"Approving design {design_id}")

            # Load design
            design = await self.db.execute(
                select(AssessmentDesign).where(
                    AssessmentDesign.id == design_id
                )
            )
            design = design.scalar_one_or_none()

            if not design:
                raise ValueError(f"Design {design_id} not found")

            # Update design
            design.review_status = AssessmentDesignReviewStatus.approved
            design.recruiter_id = recruiter_id
            design.recruiter_feedback = recruiter_notes
            design.recruiter_confidence = recruiter_confidence

            # TODO: Create Assessment record linked to design

            await self.db.commit()

            logger.info(f"Design approved: {design_id}")

            return design

        except Exception as e:
            logger.error(f"Error approving design: {e}")
            await self.db.rollback()
            raise

    async def request_changes(
        self,
        design_id: UUID,
        recruiter_id: UUID,
        feedback: str,
        specific_issues: list[str],
    ) -> AssessmentDesign:
        """
        Recruiter requests changes to assessment design.

        Agent will redesign based on feedback.

        Args:
            design_id: AssessmentDesign ID
            recruiter_id: Recruiter requesting changes
            feedback: General feedback
            specific_issues: Specific issues to address

        Returns:
            Updated AssessmentDesign record
        """
        try:
            logger.info(f"Requesting changes for design {design_id}")

            # Load design
            design = await self.db.execute(
                select(AssessmentDesign).where(
                    AssessmentDesign.id == design_id
                )
            )
            design = design.scalar_one_or_none()

            if not design:
                raise ValueError(f"Design {design_id} not found")

            # Update status
            design.review_status = AssessmentDesignReviewStatus.changes_requested
            design.recruiter_id = recruiter_id
            design.recruiter_feedback = f"{feedback}\n\nIssues:\n" + "\n".join(f"- {issue}" for issue in specific_issues)

            await self.db.commit()

            logger.info(f"Changes requested for design {design_id}")

            return design

        except Exception as e:
            logger.error(f"Error requesting changes: {e}")
            await self.db.rollback()
            raise

    async def reject_design(
        self,
        design_id: UUID,
        recruiter_id: UUID,
        reason: str,
    ) -> AssessmentDesign:
        """
        Recruiter rejects design (will create manual design).

        Args:
            design_id: AssessmentDesign ID
            recruiter_id: Recruiter rejecting
            reason: Reason for rejection

        Returns:
            Updated AssessmentDesign record
        """
        try:
            logger.info(f"Rejecting design {design_id}")

            design = await self.db.execute(
                select(AssessmentDesign).where(
                    AssessmentDesign.id == design_id
                )
            )
            design = design.scalar_one_or_none()

            if not design:
                raise ValueError(f"Design {design_id} not found")

            design.review_status = AssessmentDesignReviewStatus.rejected
            design.recruiter_id = recruiter_id
            design.recruiter_feedback = f"Design rejected: {reason}"

            await self.db.commit()

            logger.info(f"Design rejected: {design_id}")

            return design

        except Exception as e:
            logger.error(f"Error rejecting design: {e}")
            await self.db.rollback()
            raise

    async def get_fairness_report(self, design_id: UUID) -> dict:
        """
        Get fairness analysis report for design.

        Args:
            design_id: AssessmentDesign ID

        Returns:
            Fairness report with recommendations
        """
        try:
            design = await self.db.execute(
                select(AssessmentDesign).where(
                    AssessmentDesign.id == design_id
                )
            )
            design = design.scalar_one_or_none()

            if not design:
                raise ValueError(f"Design {design_id} not found")

            fairness = design.design_fairness_check or {}

            return {
                "design_id": design_id,
                "fairness_score": fairness.get("fairness_score", 0),
                "passed": fairness.get("passed", False),
                "bias_indicators": fairness.get("bias_indicators", []),
                "recommendations": fairness.get("recommendations", []),
                "gates_evaluated": fairness.get("gates_evaluated", []),
                "assessment_suitability": (
                    "good" if fairness.get("fairness_score", 0) >= 80
                    else "fair" if fairness.get("fairness_score", 0) >= 60
                    else "needs_review"
                ),
            }

        except Exception as e:
            logger.error(f"Error getting fairness report: {e}")
            return {
                "design_id": design_id,
                "fairness_score": 0,
                "passed": False,
                "bias_indicators": ["Error generating report"],
                "recommendations": ["Manual review required"],
                "gates_evaluated": [],
                "assessment_suitability": "needs_review",
            }


# Import func for count query
from sqlalchemy import func

__all__ = ["AssessmentDesignerService"]
