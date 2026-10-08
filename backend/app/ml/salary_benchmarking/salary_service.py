"""Salary Benchmarking Service - Orchestrates salary intelligence for recruiters."""

import logging
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.position import Position
from app.models.resume import Resume
from app.models.candidate_match import CandidateMatch
from .salary_model import SalaryBenchmarkingModel, SalaryBenchmark

logger = logging.getLogger(__name__)


class SalaryBenchmarkingService:
    """High-level service for salary benchmarking and offer optimization."""

    def __init__(
        self,
        db: AsyncSession,
        model: Optional[SalaryBenchmarkingModel] = None,
        levels_api_key: Optional[str] = None,
        glassdoor_api_key: Optional[str] = None,
    ):
        self.db = db
        self.model = model or SalaryBenchmarkingModel(
            levels_api_key=levels_api_key,
            glassdoor_api_key=glassdoor_api_key,
        )

    async def get_benchmark(
        self,
        role_title: str,
        level: str,
        location: str,
    ) -> Optional[SalaryBenchmark]:
        """
        Get market salary benchmark and offer recommendations.

        Args:
            role_title: Job title (e.g., "Software Engineer")
            level: Career level (junior, mid, senior, lead)
            location: Location (e.g., "San Francisco, CA")

        Returns:
            SalaryBenchmark with market data and recommendations
        """
        try:
            # Fetch market data
            market_data = await self.model.get_market_data(
                role_title=role_title,
                level=level,
                location=location,
            )

            if not market_data:
                logger.warning(f"No market data found for {role_title} in {location}")
                return None

            # Generate default offer recommendation
            recommendation = self.model.recommend_offer(
                market_data=market_data,
                candidate_level=level,
                candidate_skills_match=0.8,  # Default assumption
                role_criticality=1.0,
            )

            benchmark = SalaryBenchmark(
                role=role_title,
                location=location,
                market_data=market_data,
                recommendation=recommendation,
            )

            return benchmark

        except Exception as e:
            logger.error(f"Error getting salary benchmark: {e}")
            return None

    async def get_benchmark_for_candidate(
        self,
        candidate_id: UUID,
        position_id: UUID,
    ) -> Optional[SalaryBenchmark]:
        """
        Get salary benchmark for a specific candidate/position pair.

        Args:
            candidate_id: Candidate UUID
            position_id: Position UUID

        Returns:
            SalaryBenchmark with personalized offer recommendation
        """
        try:
            # Get position
            position = await self._get_position(position_id)
            if not position:
                return None

            # Get candidate resume
            resume = await self._get_candidate_resume(candidate_id)
            if not resume:
                return None

            # Get or create candidate match
            candidate_match = await self._get_candidate_match(candidate_id, position_id)

            # Extract role title and level from position
            role_title = position.title
            level = self._infer_level_from_position(position)
            location = self._infer_location_from_position(position)

            # Extract candidate salary expectations from resume
            candidate_expectation = self._extract_salary_from_resume(resume)

            # Get market data
            market_data = await self.model.get_market_data(
                role_title=role_title,
                level=level,
                location=location,
            )

            if not market_data:
                return None

            # Calculate skills match
            skills_match = await self._calculate_skills_match(
                resume, position, candidate_match
            )

            # Generate personalized recommendation
            recommendation = self.model.recommend_offer(
                market_data=market_data,
                candidate_level=level,
                candidate_skills_match=skills_match,
                role_criticality=1.0,
            )

            benchmark = SalaryBenchmark(
                role=role_title,
                location=location,
                market_data=market_data,
                recommendation=recommendation,
            )

            return benchmark

        except Exception as e:
            logger.error(f"Error getting candidate benchmark: {e}")
            return None

    async def _get_position(self, position_id: UUID) -> Optional[Position]:
        """Fetch position from database."""
        stmt = select(Position).where(Position.id == position_id)
        result = await self.db.execute(stmt)
        return result.scalar()

    async def _get_candidate_resume(self, candidate_id: UUID) -> Optional[Resume]:
        """Fetch candidate's latest resume."""
        stmt = (
            select(Resume)
            .where(Resume.user_id == candidate_id)
            .order_by(Resume.created_at.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar()

    async def _get_candidate_match(
        self, candidate_id: UUID, position_id: UUID
    ) -> Optional[CandidateMatch]:
        """Fetch candidate match record."""
        stmt = select(CandidateMatch).where(
            (CandidateMatch.candidate_id == candidate_id)
            & (CandidateMatch.position_id == position_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar()

    def _infer_level_from_position(self, position: Position) -> str:
        """Infer seniority level from position title."""
        title = position.title.lower()
        if "principal" in title or "director" in title:
            return "principal"
        elif "senior" in title or "lead" in title or "staff" in title:
            return "senior"
        elif "mid" in title or "intermediate" in title:
            return "mid"
        else:
            return "junior"

    def _infer_location_from_position(self, position: Position) -> str:
        """Infer location from position."""
        # Placeholder - would need location field in Position model
        return "Remote"

    def _extract_salary_from_resume(self, resume: Resume) -> Optional[float]:
        """Extract salary expectations from resume."""
        if not resume.parsed_data:
            return None

        # Look for salary in parsed data
        parsed = resume.parsed_data
        if isinstance(parsed, dict):
            salary_expectation = parsed.get("salary_expectation")
            if salary_expectation:
                # Try to parse as number
                try:
                    if isinstance(salary_expectation, (int, float)):
                        return float(salary_expectation)
                    elif isinstance(salary_expectation, str):
                        # Extract number from string (e.g., "$120000" → 120000)
                        import re
                        match = re.search(r"\d+", salary_expectation)
                        if match:
                            return float(match.group())
                except Exception:
                    pass

        return None

    async def _calculate_skills_match(
        self,
        resume: Resume,
        position: Position,
        candidate_match: Optional[CandidateMatch],
    ) -> float:
        """Calculate how well candidate's skills match the role (0-1)."""
        if candidate_match:
            # Use existing match score if available
            if candidate_match.skill_match:
                skill_score = candidate_match.skill_match.get("match_score", 0.5)
                return min(1.0, max(0.0, skill_score / 100))

        # Fallback: return 0.7 (neutral assumption)
        return 0.7


__all__ = ["SalaryBenchmarkingService"]
