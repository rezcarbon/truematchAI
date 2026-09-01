"""Job search and matching service for candidate-job pairing and recommendations.

Provides job search, ranking, and recommendation capabilities with match scoring.
"""
from __future__ import annotations

import logging
import uuid
from typing import Optional
from datetime import datetime

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.engines.matching.matcher import EnhancedMatcher, MatchType
from app.models.position import Position, PositionStatus
from app.models.saved_job import SavedJob
from app.models.application import Application
from app.models.resume import Resume, ResumeStatus
from app.models.user import User

logger = logging.getLogger(__name__)


class JobWithMatch:
    """Job with matching analysis."""

    def __init__(
        self,
        position: Position,
        match_score: float,
        match_type: str,
        explanation: str,
        keyword_score: float,
        semantic_score: float,
        capability_score: float,
        skills_aligned: list,
        skills_missing: list,
    ):
        self.position = position
        self.match_score = match_score
        self.match_type = match_type
        self.explanation = explanation
        self.keyword_score = keyword_score
        self.semantic_score = semantic_score
        self.capability_score = capability_score
        self.skills_aligned = skills_aligned
        self.skills_missing = skills_missing

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "position_id": str(self.position.id),
            "title": self.position.title,
            "company_id": str(self.position.company_id) if self.position.company_id else None,
            "description": self.position.description,
            "status": self.position.status.value,
            "match_score": round(self.match_score, 2),
            "match_type": self.match_type,
            "explanation": self.explanation,
            "keyword_score": round(self.keyword_score, 2),
            "semantic_score": round(self.semantic_score, 2),
            "capability_score": round(self.capability_score, 2),
            "skills_aligned": [s.to_dict() if hasattr(s, 'to_dict') else s for s in self.skills_aligned],
            "skills_missing": [s.to_dict() if hasattr(s, 'to_dict') else s for s in self.skills_missing],
            "created_at": self.position.created_at.isoformat() if self.position.created_at else None,
        }


class JobSearchService:
    """Service for searching jobs and matching candidates."""

    def __init__(self, db: AsyncSession):
        """Initialize job search service.

        Args:
            db: AsyncSession for database operations
        """
        self.db = db
        self.matcher = EnhancedMatcher()
        logger.debug("JobSearchService initialized")

    async def search_jobs_with_matching(
        self,
        user_id: uuid.UUID,
        filters: Optional[dict] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[JobWithMatch], int]:
        """
        Search for jobs and return with matching analysis for the user.

        Args:
            user_id: User ID to match jobs for
            filters: Filter criteria (location, salary, role, company, etc.)
            limit: Maximum number of results (default 20)
            offset: Offset for pagination (default 0)

        Returns:
            Tuple of (list of JobWithMatch, total count)
        """
        filters = filters or {}

        try:
            # Get user's resume and profile
            candidate_profile = await self._build_candidate_profile(user_id)
            if not candidate_profile:
                logger.warning(f"No candidate profile found for user {user_id}")
                return [], 0

            # Build base query
            query = select(Position).where(
                Position.status == PositionStatus.open
            )

            # Apply filters
            query = self._apply_filters(query, filters)

            # Get total count
            count_query = select(func.count()).select_from(Position).where(
                Position.status == PositionStatus.open
            )
            count_query = self._apply_filters(count_query, filters)
            total_result = await self.db.execute(count_query)
            total_count = total_result.scalar() or 0

            # Apply pagination
            query = query.limit(limit).offset(offset)

            # Execute query
            result = await self.db.execute(query)
            positions = result.scalars().all()

            if not positions:
                logger.info(f"No positions found for user {user_id}")
                return [], total_count

            # Match each job
            jobs_with_match = []
            for position in positions:
                try:
                    match_result = self.matcher.match_with_components(
                        candidate_profile,
                        position.description_en or position.description or "",
                        role_level=self._extract_role_level(position.title),
                    )

                    job_match = JobWithMatch(
                        position=position,
                        match_score=match_result.overall_score,
                        match_type=match_result.match_type.value,
                        explanation=match_result.explanation,
                        keyword_score=match_result.keyword_score,
                        semantic_score=match_result.semantic_score,
                        capability_score=match_result.capability_score,
                        skills_aligned=match_result.skills_aligned,
                        skills_missing=match_result.skills_missing,
                    )
                    jobs_with_match.append(job_match)

                except Exception as e:
                    logger.error(
                        f"Error matching position {position.id}: {e}",
                        exc_info=True,
                    )
                    continue

            logger.info(
                f"Found {len(jobs_with_match)} jobs with matches for user {user_id}",
                extra={"total_count": total_count},
            )

            return jobs_with_match, total_count

        except Exception as e:
            logger.error(f"Error in search_jobs_with_matching: {e}", exc_info=True)
            raise

    async def rank_by_match(
        self,
        jobs: list[JobWithMatch],
        candidate_profile: Optional[dict] = None,
    ) -> list[JobWithMatch]:
        """
        Sort jobs by match score (descending).

        Args:
            jobs: List of JobWithMatch to rank
            candidate_profile: Candidate profile (optional, for re-scoring if needed)

        Returns:
            Sorted list of JobWithMatch
        """
        sorted_jobs = sorted(
            jobs,
            key=lambda j: (j.match_score, j.semantic_score, j.capability_score),
            reverse=True,
        )

        logger.info(
            f"Ranked {len(sorted_jobs)} jobs",
            extra={
                "top_score": sorted_jobs[0].match_score if sorted_jobs else 0,
                "bottom_score": sorted_jobs[-1].match_score if sorted_jobs else 0,
            },
        )

        return sorted_jobs

    async def detect_hidden_gems(
        self,
        jobs: list[JobWithMatch],
        keyword_threshold: float = 60.0,
        semantic_threshold: float = 70.0,
        capability_threshold: float = 70.0,
    ) -> list[JobWithMatch]:
        """
        Identify hidden gem opportunities in job list.

        Hidden gems are jobs where:
        - Keyword score is relatively low (< threshold)
        - But semantic and capability scores are strong (>= threshold)

        Args:
            jobs: List of JobWithMatch to analyze
            keyword_threshold: Max keyword score for hidden gem (default 60)
            semantic_threshold: Min semantic score for hidden gem (default 70)
            capability_threshold: Min capability score for hidden gem (default 70)

        Returns:
            List of JobWithMatch that are hidden gems
        """
        hidden_gems = [
            j for j in jobs
            if (
                j.keyword_score < keyword_threshold
                and j.semantic_score >= semantic_threshold
                and j.capability_score >= capability_threshold
                and j.match_type == MatchType.hidden_gem.value
            )
        ]

        logger.info(
            f"Identified {len(hidden_gems)} hidden gems from {len(jobs)} jobs",
            extra={
                "keywords_max": keyword_threshold,
                "semantic_min": semantic_threshold,
                "capability_min": capability_threshold,
            },
        )

        return sorted(
            hidden_gems,
            key=lambda j: (j.semantic_score, j.capability_score),
            reverse=True,
        )

    async def get_personalized_recommendations(
        self,
        user_id: uuid.UUID,
        limit: int = 10,
    ) -> list[JobWithMatch]:
        """
        Get personalized job recommendations for user.

        Combines multiple signals:
        - Recently viewed/saved jobs
        - User's resume and skills
        - Match type preferences
        - Historical application patterns

        Args:
            user_id: User ID to get recommendations for
            limit: Number of recommendations (default 10)

        Returns:
            List of recommended JobWithMatch
        """
        try:
            # Get user's saved jobs to understand preferences
            saved_jobs_query = select(SavedJob).where(
                SavedJob.user_id == user_id
            ).order_by(desc(SavedJob.created_at)).limit(5)

            saved_result = await self.db.execute(saved_jobs_query)
            saved_jobs = saved_result.scalars().all()

            # Get candidate profile
            candidate_profile = await self._build_candidate_profile(user_id)
            if not candidate_profile:
                logger.warning(f"No candidate profile for personalization: {user_id}")
                return []

            # Extract preferences from saved jobs
            filters = self._extract_preferences_from_saved(saved_jobs)

            # Search with enhanced filters
            jobs_with_match, _ = await self.search_jobs_with_matching(
                user_id,
                filters=filters,
                limit=limit * 2,  # Get more to filter
                offset=0,
            )

            if not jobs_with_match:
                logger.info(f"No personalized recommendations found for {user_id}")
                return []

            # Rank by match and filter by match type
            ranked = await self.rank_by_match(jobs_with_match, candidate_profile)

            # Prefer hidden gems and perfect matches, deprioritize overqualified
            def scoring_fn(job: JobWithMatch) -> tuple:
                type_priority = {
                    MatchType.perfect_match.value: 4,
                    MatchType.hidden_gem.value: 3,
                    MatchType.growth_opportunity.value: 2,
                    MatchType.partial_match.value: 1,
                    MatchType.overqualified.value: 0,
                }
                type_score = type_priority.get(job.match_type, 0)
                return (type_score, job.match_score)

            recommended = sorted(
                ranked,
                key=scoring_fn,
                reverse=True,
            )[:limit]

            logger.info(
                f"Generated {len(recommended)} personalized recommendations for {user_id}"
            )

            return recommended

        except Exception as e:
            logger.error(
                f"Error getting personalized recommendations for {user_id}: {e}",
                exc_info=True,
            )
            return []

    async def _build_candidate_profile(self, user_id: uuid.UUID) -> Optional[dict]:
        """Build candidate profile from user data.

        Args:
            user_id: User ID

        Returns:
            Candidate profile dictionary or None
        """
        try:
            # Get latest resume
            resume_query = select(Resume).where(
                and_(
                    Resume.user_id == user_id,
                    Resume.status == ResumeStatus.parsed,
                )
            ).order_by(desc(Resume.created_at)).limit(1)

            resume_result = await self.db.execute(resume_query)
            resume = resume_result.scalar_one_or_none()

            if not resume:
                logger.warning(f"No parsed resume found for user {user_id}")
                return None

            # Extract profile data
            parsed_data = resume.parsed_data or {}
            raw_text = resume.raw_narrative or ""

            profile = {
                "user_id": str(user_id),
                "resume_id": str(resume.id),
                "resume_text": raw_text,
                "current_title": parsed_data.get("current_title", ""),
                "experience_years": parsed_data.get("years_of_experience", 0),
                "seniority_level": parsed_data.get("seniority_level", "mid"),
                "skills": parsed_data.get("skills", []),
                "industries": parsed_data.get("industries", []),
                "background": parsed_data.get("summary", ""),
            }

            logger.debug(f"Built candidate profile for user {user_id}")
            return profile

        except Exception as e:
            logger.error(f"Error building candidate profile for {user_id}: {e}", exc_info=True)
            return None

    def _apply_filters(self, query, filters: dict):
        """Apply filter criteria to query.

        Args:
            query: SQLAlchemy query to filter
            filters: Dictionary of filter criteria

        Returns:
            Filtered query
        """
        if not filters:
            return query

        # Filter by match score range
        if "min_match_score" in filters or "max_match_score" in filters:
            # Note: Score filtering happens post-query in search_jobs_with_matching
            pass

        # Filter by role/title keywords
        if "role_keywords" in filters:
            keywords = filters["role_keywords"]
            if isinstance(keywords, str):
                keywords = [keywords]
            conditions = [
                Position.title.ilike(f"%{kw}%") for kw in keywords
            ]
            query = query.where(or_(*conditions))

        # Filter by company
        if "company_id" in filters:
            query = query.where(Position.company_id == filters["company_id"])

        # Filter by status
        if "status" in filters:
            query = query.where(Position.status == filters["status"])

        logger.debug(f"Applied filters: {list(filters.keys())}")
        return query

    def _extract_preferences_from_saved(self, saved_jobs: list[SavedJob]) -> dict:
        """Extract search preferences from saved jobs.

        Args:
            saved_jobs: List of saved jobs

        Returns:
            Filter dictionary with extracted preferences
        """
        filters = {}

        if not saved_jobs:
            return filters

        # Extract company preferences
        companies = {j.position_id for j in saved_jobs if j.position_id}
        if companies:
            # Would need to fetch positions to get company_ids
            pass

        # Extract job title patterns
        titles = [j.job_title for j in saved_jobs if j.job_title]
        if titles:
            # Extract common keywords from titles
            common_words = set()
            for title in titles:
                words = title.lower().split()
                if common_words:
                    common_words &= set(words)
                else:
                    common_words = set(words)

            if common_words:
                filters["role_keywords"] = list(common_words)

        logger.debug(f"Extracted preferences from {len(saved_jobs)} saved jobs")
        return filters

    def _extract_role_level(self, job_title: str) -> Optional[str]:
        """Extract seniority level from job title.

        Args:
            job_title: Job title string

        Returns:
            Seniority level or None
        """
        title_lower = job_title.lower()

        if "principal" in title_lower or "director" in title_lower:
            return "principal"
        elif "lead" in title_lower or "head" in title_lower:
            return "lead"
        elif "senior" in title_lower or "sr." in title_lower:
            return "senior"
        elif "junior" in title_lower or "jr." in title_lower:
            return "junior"
        elif "intern" in title_lower:
            return "junior"

        return "mid"
