"""Matching Service - Phase 4 orchestration."""
from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.matching_agent import MatchingAgent
from app.models.analysis_result import AnalysisResult
from app.models.candidate_match import CandidateMatch, MatchStatus
from app.models.position import Position
from app.models.resume import Resume

logger = logging.getLogger("truematch.matching_service")


class MatchingService:
    """Service for managing candidate matching pipeline.

    Responsibilities:
    - Calculate fit for analyzed candidates
    - Rank candidates within positions
    - Generate match reports
    - Validate matches
    """

    def __init__(self, db: AsyncSession):
        """Initialize matching service.

        Args:
            db: Async database session
        """
        self.db = db
        self.agent = MatchingAgent(db)

    async def initiate_match(self, analysis_result_id: UUID) -> CandidateMatch:
        """Initiate matching for completed analysis.

        Args:
            analysis_result_id: Analysis result ID to match

        Returns:
            CandidateMatch record (status: pending_match)

        Raises:
            ValueError: If analysis result not found
        """
        # Load analysis result
        analysis = await self.db.execute(
            select(AnalysisResult).where(AnalysisResult.id == analysis_result_id)
        )
        analysis = analysis.scalar_one_or_none()

        if not analysis:
            raise ValueError(f"Analysis result {analysis_result_id} not found")

        # Create match record
        match = CandidateMatch(
            analysis_result_id=analysis.id,
            position_id=analysis.position_id,
            candidate_id=analysis.candidate_id,
            status=MatchStatus.pending_match,
        )

        self.db.add(match)
        await self.db.flush()

        logger.info(f"Initiated match {match.id} for analysis {analysis_result_id}")

        return match

    async def get_pending_matches(
        self, page: int = 1, limit: int = 10, position_id: UUID | None = None
    ) -> tuple[list[CandidateMatch], dict]:
        """Get pending matches for review.

        Args:
            page: Page number (1-indexed)
            limit: Results per page (max 100)
            position_id: Optional filter by position

        Returns:
            (list of matches, pagination info)
        """
        # Build query
        query = select(CandidateMatch).where(
            CandidateMatch.status == MatchStatus.match_complete
        )

        if position_id:
            query = query.where(CandidateMatch.position_id == position_id)

        # Pagination
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)

        results = await self.db.execute(query)
        matches = results.scalars().all()

        # Count total
        count_query = select(CandidateMatch).where(
            CandidateMatch.status == MatchStatus.match_complete
        )
        if position_id:
            count_query = count_query.where(CandidateMatch.position_id == position_id)

        count = await self.db.execute(count_query)
        total = len(count.scalars().all())

        pagination = {
            "page": page,
            "limit": limit,
            "total": total,
            "pages": (total + limit - 1) // limit,
        }

        return matches, pagination

    async def get_match_details(self, match_id: UUID) -> CandidateMatch:
        """Get full match details.

        Args:
            match_id: Match ID

        Returns:
            CandidateMatch record

        Raises:
            ValueError: If not found
        """
        result = await self.db.execute(
            select(CandidateMatch).where(CandidateMatch.id == match_id)
        )
        result = result.scalar_one_or_none()

        if not result:
            raise ValueError(f"Match {match_id} not found")

        return result

    async def approve_match(
        self,
        match_id: UUID,
        recruiter_id: UUID,
        notes: str | None = None,
    ) -> CandidateMatch:
        """Recruiter approves match.

        Args:
            match_id: Match ID
            recruiter_id: Recruiter user ID
            notes: Optional recruiter notes

        Returns:
            Updated CandidateMatch

        Raises:
            ValueError: If not found or already reviewed
        """
        match = await self.get_match_details(match_id)

        if match.recruiter_reviewed:
            raise ValueError(f"Match {match_id} already reviewed")

        match.recruiter_reviewed = True
        match.recruiter_review_at = __import__("datetime").datetime.utcnow()
        match.recruiter_notes = notes
        match.status = MatchStatus.ranked

        await self.db.commit()

        logger.info(f"Recruiter {recruiter_id} approved match {match_id}")

        return match

    async def get_position_rankings(
        self, position_id: UUID
    ) -> list[CandidateMatch]:
        """Get ranked candidates for a position.

        Args:
            position_id: Position ID

        Returns:
            List of matches ranked by overall_score (descending)
        """
        query = select(CandidateMatch).where(
            CandidateMatch.position_id == position_id,
            CandidateMatch.status == MatchStatus.ranked,
        )
        query = query.order_by(CandidateMatch.overall_score.desc())

        results = await self.db.execute(query)
        matches = results.scalars().all()

        return matches

    async def get_candidate_alternatives(
        self, candidate_id: UUID
    ) -> list[CandidateMatch]:
        """Get alternative position matches for a candidate.

        Args:
            candidate_id: Candidate user ID

        Returns:
            List of matches ranked by overall_score
        """
        query = select(CandidateMatch).where(
            CandidateMatch.candidate_id == candidate_id,
            CandidateMatch.status == MatchStatus.ranked,
        )
        query = query.order_by(CandidateMatch.overall_score.desc())

        results = await self.db.execute(query)
        matches = results.scalars().all()

        return matches


__all__ = ["MatchingService"]
