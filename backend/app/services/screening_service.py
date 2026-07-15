"""Screening Service — High-level orchestration of screening workflow."""
from __future__ import annotations

import logging
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.screening_agent import ScreeningAgent
from app.models.screening import (
    ScreeningBatch,
    ScreeningResult,
    ScreeningBatchStatus,
    RecruiterDecision,
)
from app.models.resume import Resume
from app.models.position import Position
from app.models.decision import Decision

logger = logging.getLogger(__name__)


class ScreeningService:
    """
    High-level service for screening operations.

    Orchestrates:
    - Batch creation and management
    - Agent invocation
    - Result persistence
    - Recruiter decisions
    - Learning loop integration
    """

    def __init__(self, db: AsyncSession):
        """Initialize screening service."""
        self.db = db
        self.agent = ScreeningAgent(db)
        self.logger = logger

    async def create_screening_batch(
        self,
        position_id: UUID,
        resume_ids: list[UUID],
        batch_config: Optional[dict] = None,
        recruiter_id: Optional[UUID] = None,
    ) -> ScreeningBatch:
        """
        Create a new screening batch.

        Args:
            position_id: Position to screen candidates for
            resume_ids: Resume IDs to screen (1000+)
            batch_config: Optional configuration (min years, required skills, etc.)
            recruiter_id: Recruiter initiating the batch

        Returns:
            ScreeningBatch (status=queued, ready for processing)
        """
        try:
            batch = ScreeningBatch(
                position_id=position_id,
                created_by=recruiter_id,
                total_candidates=len(resume_ids),
                screened_count=0,
                pending_review_count=len(resume_ids),
                status=ScreeningBatchStatus.queued,
                batch_config=batch_config,
                metadata={
                    "resume_ids": [str(rid) for rid in resume_ids],
                    "initialized_at": None,  # Set when screening starts
                },
            )

            self.db.add(batch)
            await self.db.commit()
            await self.db.refresh(batch)

            self.logger.info(
                f"Created screening batch {batch.id} for position {position_id} "
                f"with {len(resume_ids)} candidates"
            )

            return batch

        except Exception as e:
            self.logger.error(f"Error creating screening batch: {e}")
            await self.db.rollback()
            raise

    async def screen_candidate(
        self,
        batch_id: UUID,
        resume_id: UUID,
        position_id: UUID,
    ) -> ScreeningResult:
        """
        Screen a single candidate (called by batch processor).

        Args:
            batch_id: Screening batch ID
            resume_id: Resume to screen
            position_id: Position to screen against

        Returns:
            ScreeningResult (persisted to DB)
        """
        try:
            # Load resume and position
            resume = await self.db.execute(
                select(Resume).where(Resume.id == resume_id)
            )
            resume = resume.scalar_one_or_none()

            position = await self.db.execute(
                select(Position).where(Position.id == position_id)
            )
            position = position.scalar_one_or_none()

            if not resume or not position:
                self.logger.error(
                    f"Resume {resume_id} or position {position_id} not found"
                )
                raise ValueError("Resume or position not found")

            # Load batch config
            batch = await self.db.execute(
                select(ScreeningBatch).where(ScreeningBatch.id == batch_id)
            )
            batch = batch.scalar_one_or_none()
            batch_config = batch.batch_config if batch else None

            # Run screening agent
            agent_result = await self.agent.screen_resume(
                resume, position, batch_config
            )

            # Create ScreeningResult record
            screening_result = ScreeningResult(
                screening_batch_id=batch_id,
                position_id=position_id,
                resume_id=resume_id,
                user_id=resume.user_id,
                assessment_id=None,  # Linked later if assessment is created
                agent_recommendation=agent_result["agent_recommendation"],
                confidence_score=agent_result["confidence_score"],
                screening_summary=agent_result["screening_summary"],
                screening_details=agent_result["screening_details"],
                bias_flags=agent_result["bias_flags"],
                recruiter_decision=None,  # Pending recruiter review
                recruiter_id=None,
                recruiter_notes=None,
                was_overridden=False,
            )

            self.db.add(screening_result)

            # Update batch progress
            batch.screened_count += 1
            if batch.screened_count >= batch.total_candidates:
                batch.status = ScreeningBatchStatus.pending_review

            await self.db.commit()
            await self.db.refresh(screening_result)

            self.logger.info(
                f"Screened {resume_id} → {screening_result.agent_recommendation} "
                f"({screening_result.confidence_score}%)"
            )

            return screening_result

        except Exception as e:
            self.logger.error(f"Error screening candidate: {e}")
            await self.db.rollback()
            raise

    async def get_pending_reviews(
        self,
        batch_id: UUID,
        page: int = 1,
        limit: int = 10,
        sort_by: str = "confidence_desc",
    ) -> tuple[list[ScreeningResult], dict]:
        """
        Get paginated screening results pending recruiter review.

        Args:
            batch_id: Screening batch ID
            page: Page number (1-indexed)
            limit: Results per page
            sort_by: Sort order (confidence_desc, created_asc, etc.)

        Returns:
            (results, pagination_info)
        """
        try:
            # Count total
            count_query = select(func.count(ScreeningResult.id)).where(
                ScreeningResult.screening_batch_id == batch_id,
                ScreeningResult.recruiter_decision == None,  # Not yet decided
            )
            total = await self.db.execute(count_query)
            total = total.scalar() or 0

            # Build query
            query = select(ScreeningResult).where(
                ScreeningResult.screening_batch_id == batch_id,
                ScreeningResult.recruiter_decision == None,
            )

            # Apply sorting
            if sort_by == "confidence_desc":
                query = query.order_by(ScreeningResult.confidence_score.desc())
            elif sort_by == "created_asc":
                query = query.order_by(ScreeningResult.created_at.asc())

            # Apply pagination
            offset = (page - 1) * limit
            query = query.offset(offset).limit(limit)

            results = await self.db.execute(query)
            results = results.scalars().all()

            pagination = {
                "total": total,
                "page": page,
                "limit": limit,
                "pages": (total + limit - 1) // limit,
            }

            return results, pagination

        except Exception as e:
            self.logger.error(f"Error getting pending reviews: {e}")
            raise

    async def process_recruiter_decision(
        self,
        screening_result_id: UUID,
        recruiter_decision: RecruiterDecision,
        recruiter_id: UUID,
        recruiter_notes: Optional[str] = None,
        recruiter_confidence: Optional[int] = None,
    ) -> Decision:
        """
        Record recruiter decision on screening result.

        Creates Decision record, captures override pattern, triggers learning.

        Args:
            screening_result_id: Screening result to decide on
            recruiter_decision: Interview | Hold | Further Review
            recruiter_id: Recruiter making decision
            recruiter_notes: Optional notes explaining decision
            recruiter_confidence: Optional confidence (0-100) for learning

        Returns:
            Decision record (persisted)
        """
        try:
            # Load screening result
            screening_result = await self.db.execute(
                select(ScreeningResult).where(
                    ScreeningResult.id == screening_result_id
                )
            )
            screening_result = screening_result.scalar_one_or_none()

            if not screening_result:
                raise ValueError(f"Screening result {screening_result_id} not found")

            # Check if override
            was_overridden = (
                recruiter_decision != screening_result.agent_recommendation
            )

            # Update screening result
            screening_result.recruiter_decision = recruiter_decision
            screening_result.recruiter_id = recruiter_id
            screening_result.recruiter_notes = recruiter_notes
            screening_result.recruiter_confidence = recruiter_confidence
            screening_result.was_overridden = was_overridden

            # Create Decision record (links to Decision model)
            # Note: This links to assessment_id if available, otherwise just records it
            decision = Decision(
                assessment_id=screening_result.assessment_id,
                position_id=screening_result.position_id,
                recruiter_id=recruiter_id,
                decision=recruiter_decision.value,  # "interview" → DecisionOutcome
                ai_recommendation_followed=not was_overridden,
                override_reasoning=recruiter_notes,
                screening_override_reason=recruiter_notes if was_overridden else None,
                is_screening_decision=True,  # Mark as screening phase decision
            )

            self.db.add(decision)

            await self.db.commit()
            await self.db.refresh(screening_result)
            await self.db.refresh(decision)

            self.logger.info(
                f"Recruiter {recruiter_id} decided: {recruiter_decision.value} "
                f"for screening result {screening_result_id} "
                f"(override={was_overridden})"
            )

            # TODO: Trigger learning loop integration
            # await self._trigger_learning_loop(decision, screening_result)

            return decision

        except Exception as e:
            self.logger.error(f"Error processing recruiter decision: {e}")
            await self.db.rollback()
            raise

    async def get_screening_metrics(self, batch_id: UUID) -> dict:
        """
        Get analytics for screening batch.

        Args:
            batch_id: Screening batch ID

        Returns:
            Metrics dict with recommendations, decisions, override rate, etc.
        """
        try:
            # Load batch
            batch = await self.db.execute(
                select(ScreeningBatch).where(ScreeningBatch.id == batch_id)
            )
            batch = batch.scalar_one_or_none()

            if not batch:
                raise ValueError(f"Batch {batch_id} not found")

            # Get all results for this batch
            results = await self.db.execute(
                select(ScreeningResult).where(
                    ScreeningResult.screening_batch_id == batch_id
                )
            )
            results = results.scalars().all()

            # Count recommendations
            recommendations = {
                "advance": sum(1 for r in results if r.agent_recommendation.value == "advance"),
                "hold": sum(1 for r in results if r.agent_recommendation.value == "hold"),
                "review": sum(1 for r in results if r.agent_recommendation.value == "review"),
            }

            # Count decisions
            recruiter_decisions = {
                "interview": sum(1 for r in results if r.recruiter_decision and r.recruiter_decision.value == "interview"),
                "hold": sum(1 for r in results if r.recruiter_decision and r.recruiter_decision.value == "hold"),
                "further_review": sum(1 for r in results if r.recruiter_decision and r.recruiter_decision.value == "further_review"),
                "pending": sum(1 for r in results if r.recruiter_decision is None),
            }

            # Calculate override rate
            decided_results = [r for r in results if r.recruiter_decision]
            overridden = sum(1 for r in decided_results if r.was_overridden)
            override_rate = (
                (overridden / len(decided_results)) if decided_results else 0.0
            )

            # Calculate average confidence
            avg_confidence = (
                sum(r.confidence_score for r in results) / len(results)
                if results else 0.0
            )

            # Count bias alerts
            bias_alerts = sum(
                1 for r in results
                if r.bias_flags.get("should_be_reviewed", False)
            )

            return {
                "batch_id": str(batch.id),
                "position_id": str(batch.position_id),
                "total_screened": len(results),
                "recommendations": recommendations,
                "recruiter_decisions": recruiter_decisions,
                "override_rate": override_rate,
                "avg_confidence_score": avg_confidence,
                "bias_alerts_count": bias_alerts,
                "time_to_complete_minutes": None,  # TODO: Calculate from timestamps
                "avg_recruiter_review_time_seconds": None,
            }

        except Exception as e:
            self.logger.error(f"Error getting screening metrics: {e}")
            raise

    async def get_batch_status(self, batch_id: UUID) -> dict:
        """
        Get batch processing status.

        Args:
            batch_id: Screening batch ID

        Returns:
            Status dict with progress, ETA, etc.
        """
        try:
            batch = await self.db.execute(
                select(ScreeningBatch).where(ScreeningBatch.id == batch_id)
            )
            batch = batch.scalar_one_or_none()

            if not batch:
                raise ValueError(f"Batch {batch_id} not found")

            progress_pct = (
                (batch.screened_count / batch.total_candidates * 100)
                if batch.total_candidates > 0 else 0
            )

            return {
                "batch_id": str(batch.id),
                "position_id": str(batch.position_id),
                "status": batch.status.value,
                "total_candidates": batch.total_candidates,
                "screened_count": batch.screened_count,
                "pending_review_count": batch.pending_review_count,
                "progress_percentage": progress_pct,
                "estimated_completion_seconds": None,  # TODO: Calculate ETA
                "started_at": batch.started_at.isoformat() if batch.started_at else None,
                "completed_at": batch.completed_at.isoformat() if batch.completed_at else None,
            }

        except Exception as e:
            self.logger.error(f"Error getting batch status: {e}")
            raise


__all__ = ["ScreeningService"]
