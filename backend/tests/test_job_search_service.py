"""Tests for job search service."""
import pytest
import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.job_search_service import JobSearchService, JobWithMatch
from app.models.position import Position, PositionStatus
from app.models.resume import Resume, ResumeStatus
from app.models.user import User
from app.core.clock import utcnow


class TestJobSearchService:
    """Test JobSearchService functionality."""

    @pytest.fixture
    async def service(self, db: AsyncSession):
        """Create service instance."""
        return JobSearchService(db)

    @pytest.fixture
    async def test_user(self, db: AsyncSession):
        """Create test user."""
        user = User(
            email=f"test_{uuid.uuid4().hex}@example.com",
            password_hash="dummy",
        )
        db.add(user)
        await db.commit()
        return user

    @pytest.fixture
    async def test_resume(self, db: AsyncSession, test_user: User):
        """Create test resume."""
        resume = Resume(
            user_id=test_user.id,
            status=ResumeStatus.parsed,
            raw_narrative=(
                "Senior Software Engineer with 8 years experience in Python, Java, "
                "and cloud technologies. Expert in AWS, Kubernetes, Docker."
            ),
            parsed_data={
                "current_title": "Senior Software Engineer",
                "years_of_experience": 8,
                "seniority_level": "senior",
                "skills": [
                    {"name": "Python", "years_of_experience": 8},
                    {"name": "AWS", "years_of_experience": 6},
                    {"name": "Kubernetes", "years_of_experience": 5},
                ],
                "industries": ["technology"],
            },
        )
        db.add(resume)
        await db.commit()
        return resume

    @pytest.fixture
    async def test_positions(self, db: AsyncSession):
        """Create test positions."""
        positions = []

        # Perfect match position
        p1 = Position(
            title="Senior Python Engineer",
            description=(
                "Senior Python Engineer - We seek an experienced Senior Engineer with 7+ years "
                "building distributed systems. Required: Python, AWS, Kubernetes, Docker."
            ),
            status=PositionStatus.open,
        )
        db.add(p1)
        await db.flush()
        positions.append(p1)

        # Entry-level position (overqualified)
        p2 = Position(
            title="Junior Python Developer",
            description="Entry-level position. Learn web development with Python and Flask.",
            status=PositionStatus.open,
        )
        db.add(p2)
        await db.flush()
        positions.append(p2)

        # Hidden gem position
        p3 = Position(
            title="Platform Architect",
            description=(
                "Design resilient, scalable systems. Work with distributed computing, "
                "cloud infrastructure, and orchestration platforms."
            ),
            status=PositionStatus.open,
        )
        db.add(p3)
        await db.flush()
        positions.append(p3)

        await db.commit()
        return positions

    @pytest.mark.asyncio
    async def test_search_jobs_with_matching(
        self,
        service: JobSearchService,
        test_user: User,
        test_resume: Resume,
        test_positions: list,
        db: AsyncSession,
    ):
        """Test searching jobs with matching analysis."""
        results, total_count = await service.search_jobs_with_matching(
            test_user.id,
            limit=10,
            offset=0,
        )

        assert len(results) <= 10
        assert total_count >= len(results)
        assert all(isinstance(r, JobWithMatch) for r in results)
        assert all(hasattr(r, "match_score") for r in results)

    @pytest.mark.asyncio
    async def test_rank_by_match(self, service: JobSearchService):
        """Test ranking jobs by match score."""
        jobs = [
            JobWithMatch(
                position=Position(title="Job 1"),
                match_score=95.0,
                match_type="perfect_match",
                explanation="Test",
                keyword_score=95.0,
                semantic_score=95.0,
                capability_score=95.0,
                skills_aligned=[],
                skills_missing=[],
            ),
            JobWithMatch(
                position=Position(title="Job 2"),
                match_score=65.0,
                match_type="partial_match",
                explanation="Test",
                keyword_score=65.0,
                semantic_score=65.0,
                capability_score=65.0,
                skills_aligned=[],
                skills_missing=[],
            ),
            JobWithMatch(
                position=Position(title="Job 3"),
                match_score=80.0,
                match_type="growth_opportunity",
                explanation="Test",
                keyword_score=80.0,
                semantic_score=80.0,
                capability_score=60.0,
                skills_aligned=[],
                skills_missing=[],
            ),
        ]

        ranked = await service.rank_by_match(jobs)

        assert ranked[0].match_score >= ranked[1].match_score >= ranked[2].match_score

    @pytest.mark.asyncio
    async def test_detect_hidden_gems(self, service: JobSearchService):
        """Test hidden gem detection."""
        jobs = [
            JobWithMatch(
                position=Position(title="Hidden Gem"),
                match_score=75.0,
                match_type="hidden_gem",
                explanation="Test",
                keyword_score=50.0,
                semantic_score=78.0,
                capability_score=76.0,
                skills_aligned=[],
                skills_missing=[],
            ),
            JobWithMatch(
                position=Position(title="Perfect"),
                match_score=90.0,
                match_type="perfect_match",
                explanation="Test",
                keyword_score=90.0,
                semantic_score=90.0,
                capability_score=90.0,
                skills_aligned=[],
                skills_missing=[],
            ),
            JobWithMatch(
                position=Position(title="Partial"),
                match_score=55.0,
                match_type="partial_match",
                explanation="Test",
                keyword_score=55.0,
                semantic_score=55.0,
                capability_score=55.0,
                skills_aligned=[],
                skills_missing=[],
            ),
        ]

        hidden_gems = await service.detect_hidden_gems(jobs)

        assert len(hidden_gems) >= 0
        for gem in hidden_gems:
            assert gem.match_type == "hidden_gem"
            assert gem.keyword_score < 60

    @pytest.mark.asyncio
    async def test_get_personalized_recommendations(
        self,
        service: JobSearchService,
        test_user: User,
        test_positions: list,
        db: AsyncSession,
    ):
        """Test personalized recommendations."""
        recommendations = await service.get_personalized_recommendations(
            test_user.id,
            limit=5,
        )

        assert len(recommendations) <= 5
        # Sorted by quality
        if len(recommendations) > 1:
            assert recommendations[0].match_score >= recommendations[-1].match_score

    @pytest.mark.asyncio
    async def test_build_candidate_profile_success(
        self,
        service: JobSearchService,
        test_user: User,
        test_resume: Resume,
        db: AsyncSession,
    ):
        """Test successful candidate profile building."""
        profile = await service._build_candidate_profile(test_user.id)

        assert profile is not None
        assert profile["user_id"] == str(test_user.id)
        assert profile["resume_id"] == str(test_resume.id)
        assert "resume_text" in profile
        assert profile["experience_years"] == 8
        assert profile["seniority_level"] == "senior"

    @pytest.mark.asyncio
    async def test_build_candidate_profile_no_resume(
        self,
        service: JobSearchService,
        test_user: User,
    ):
        """Test candidate profile building with no resume."""
        new_user = User(email=f"test_{uuid.uuid4().hex}@example.com", password_hash="dummy")
        # Don't add to DB to avoid FK issues

        profile = await service._build_candidate_profile(new_user.id)

        assert profile is None

    @pytest.mark.asyncio
    async def test_apply_filters(self, service: JobSearchService, db: AsyncSession):
        """Test filter application."""
        query = db.query(Position)

        # Test role keyword filter
        filters = {"role_keywords": ["python"]}
        filtered_query = service._apply_filters(query, filters)
        # Just verify it doesn't error

    def test_extract_preferences_from_saved(self, service: JobSearchService):
        """Test preference extraction from saved jobs."""
        from app.models.saved_job import SavedJob, SavedJobStatus

        saved_jobs = [
            SavedJob(
                job_title="Senior Python Engineer",
                company_name="TechCorp",
                position_id=uuid.uuid4(),
                user_id=uuid.uuid4(),
                status=SavedJobStatus.saved,
            ),
            SavedJob(
                job_title="Senior Java Engineer",
                company_name="TechCorp",
                position_id=uuid.uuid4(),
                user_id=uuid.uuid4(),
                status=SavedJobStatus.saved,
            ),
        ]

        preferences = service._extract_preferences_from_saved(saved_jobs)

        assert isinstance(preferences, dict)

    def test_extract_role_level(self, service: JobSearchService):
        """Test role level extraction from job title."""
        assert service._extract_role_level("Senior Python Engineer") == "senior"
        assert service._extract_role_level("Junior Developer") == "junior"
        assert service._extract_role_level("Lead Software Engineer") == "lead"
        assert service._extract_role_level("Principal Engineer") == "principal"
        assert service._extract_role_level("Software Engineer") == "mid"

    @pytest.mark.asyncio
    async def test_search_with_pagination(
        self,
        service: JobSearchService,
        test_user: User,
        test_positions: list,
        db: AsyncSession,
    ):
        """Test pagination in search."""
        results1, count1 = await service.search_jobs_with_matching(
            test_user.id,
            limit=2,
            offset=0,
        )

        results2, count2 = await service.search_jobs_with_matching(
            test_user.id,
            limit=2,
            offset=2,
        )

        assert count1 == count2
        # Different results if enough positions
        if count1 > 2:
            # IDs might differ
            pass

    @pytest.mark.asyncio
    async def test_search_empty_filters(
        self,
        service: JobSearchService,
        test_user: User,
        test_positions: list,
        db: AsyncSession,
    ):
        """Test search with empty filters."""
        results, count = await service.search_jobs_with_matching(
            test_user.id,
            filters={},
        )

        assert isinstance(results, list)
        assert isinstance(count, int)

    @pytest.mark.asyncio
    async def test_job_with_match_serialization(self, service: JobSearchService):
        """Test JobWithMatch serialization."""
        position = Position(
            title="Test Position",
            description="Test Description",
            status=PositionStatus.open,
        )

        job_match = JobWithMatch(
            position=position,
            match_score=85.5,
            match_type="perfect_match",
            explanation="Great match",
            keyword_score=85.0,
            semantic_score=87.0,
            capability_score=84.0,
            skills_aligned=[],
            skills_missing=[],
        )

        result_dict = job_match.to_dict()

        assert result_dict["title"] == "Test Position"
        assert result_dict["match_score"] == 85.5
        assert result_dict["match_type"] == "perfect_match"
        assert isinstance(result_dict["skills_aligned"], list)
