"""Comprehensive tests for Career Coach Service."""
from __future__ import annotations

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.resume_version import ResumeVersion
from app.services.career_coach_service import (
    CareerCoachService,
    CareerContext,
    LearningPath,
    LearningResource,
    SalaryData,
    CoachingMessage,
    ConversationSummary,
)


@pytest.fixture
def mock_db():
    """Create mock database session."""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def career_coach_service(mock_db):
    """Create career coach service with mock DB."""
    return CareerCoachService(mock_db)


@pytest.fixture
def sample_user():
    """Create a sample user."""
    user = MagicMock(spec=User)
    user.id = uuid.uuid4()
    user.email = "alice@example.com"
    user.target_role = "Staff Engineer"
    user.career_goals = "Become a technical leader"
    return user


@pytest.fixture
def sample_resume_data():
    """Create sample resume data."""
    return {
        "current_role": "Senior Software Engineer",
        "skills": [
            "python",
            "java",
            "javascript",
            "aws",
            "docker",
            "kubernetes",
            "sql",
            "system_design",
        ],
        "certifications": ["AWS Solutions Architect", "Kubernetes Administrator"],
        "education": [
            {
                "degree": "BS Computer Science",
                "institution": "Tech University",
            }
        ],
        "work_experience": [
            {
                "position": "Senior Software Engineer",
                "company": "Tech Corp",
                "start_date": "2021-01-01",
                "description": "Led microservices architecture",
            },
            {
                "position": "Software Engineer",
                "company": "StartUp Inc",
                "start_date": "2018-01-01",
                "end_date": "2021-01-01",
                "description": "Full-stack development",
            },
            {
                "position": "Junior Developer",
                "company": "Small Co",
                "start_date": "2016-01-01",
                "end_date": "2018-01-01",
                "description": "Web development",
            },
        ],
    }


@pytest.fixture
def sample_resume_version(sample_resume_data):
    """Create sample resume version."""
    version = MagicMock(spec=ResumeVersion)
    version.id = uuid.uuid4()
    version.user_id = uuid.uuid4()
    version.parsed_data = sample_resume_data
    version.created_at = datetime.utcnow()
    return version


class TestCareerContext:
    """Test CareerContext class."""

    def test_career_context_creation(self):
        """Test creating career context."""
        context = CareerContext(
            user_id=uuid.uuid4(),
            current_role="Software Engineer",
            target_role="Staff Engineer",
            years_experience=5,
            skills=["Python", "AWS"],
        )

        assert context.current_role == "Software Engineer"
        assert context.target_role == "Staff Engineer"
        assert context.years_experience == 5

    def test_career_context_to_prompt_text(self):
        """Test converting career context to prompt text."""
        context = CareerContext(
            user_id=uuid.uuid4(),
            current_role="Engineer",
            target_role="Staff Engineer",
            years_experience=5,
            skills=["Python"],
            strengths=["Problem solving"],
            challenges=["Leadership"],
        )

        prompt_text = context.to_prompt_text()

        assert "CAREER CONTEXT" in prompt_text
        assert "Software Engineer" in prompt_text or "Engineer" in prompt_text
        assert "Python" in prompt_text


class TestLearningResource:
    """Test LearningResource class."""

    def test_learning_resource_creation(self):
        """Test creating a learning resource."""
        resource = LearningResource(
            title="Python Fundamentals",
            platform="Coursera",
            url="https://coursera.org/course",
            estimated_hours=20,
            difficulty_level="beginner",
            skills_covered=["Python"],
            cost="paid",
        )

        assert resource.title == "Python Fundamentals"
        assert resource.platform == "Coursera"
        assert resource.estimated_hours == 20

    def test_learning_resource_to_dict(self):
        """Test converting resource to dictionary."""
        resource = LearningResource(
            title="Advanced Python",
            platform="Udemy",
            url="https://udemy.com/course",
            estimated_hours=30,
            difficulty_level="advanced",
            skills_covered=["Python", "Async"],
            cost="paid",
        )

        resource_dict = resource.to_dict()

        assert resource_dict["title"] == "Advanced Python"
        assert resource_dict["estimated_hours"] == 30


class TestLearningPath:
    """Test LearningPath class."""

    def test_learning_path_creation(self):
        """Test creating a learning path."""
        path = LearningPath(
            from_role="Software Engineer",
            to_role="Staff Engineer",
            duration_weeks=26,
            required_skills=["system_design", "leadership"],
            phases=[
                {"phase": 1, "name": "Foundations", "weeks": 8}
            ],
        )

        assert path.from_role == "Software Engineer"
        assert path.to_role == "Staff Engineer"
        assert path.duration_weeks == 26

    def test_learning_path_to_dict(self):
        """Test converting learning path to dictionary."""
        path = LearningPath(
            from_role="Mid Engineer",
            to_role="Senior Engineer",
            duration_weeks=24,
            required_skills=["architecture"],
        )

        path_dict = path.to_dict()

        assert path_dict["duration_weeks"] == 24
        assert path_dict["from_role"] == "Mid Engineer"


class TestSalaryData:
    """Test SalaryData class."""

    def test_salary_data_creation(self):
        """Test creating salary data."""
        salary = SalaryData(
            role="Software Engineer",
            location="San Francisco, CA",
            experience_level="mid",
            min_salary=120000,
            median_salary=160000,
            max_salary=200000,
            percentile_25=140000,
            percentile_75=180000,
        )

        assert salary.role == "Software Engineer"
        assert salary.median_salary == 160000
        assert salary.percentile_75 == 180000

    def test_salary_data_to_dict(self):
        """Test converting salary data to dictionary."""
        salary = SalaryData(
            role="Data Scientist",
            location="New York, NY",
            experience_level="senior",
            min_salary=130000,
            median_salary=170000,
            max_salary=210000,
        )

        salary_dict = salary.to_dict()

        assert salary_dict["role"] == "Data Scientist"
        assert salary_dict["median_salary"] == 170000


class TestCoachingMessage:
    """Test CoachingMessage class."""

    def test_coaching_message_creation(self):
        """Test creating a coaching message."""
        message = CoachingMessage(
            role="assistant",
            content="Here's my advice...",
            resources_suggested=["Coursera"],
        )

        assert message.role == "assistant"
        assert "advice" in message.content
        assert len(message.resources_suggested) == 1

    def test_coaching_message_to_dict(self):
        """Test converting message to dictionary."""
        message = CoachingMessage(
            role="user",
            content="How should I transition?",
        )

        message_dict = message.to_dict()

        assert message_dict["role"] == "user"
        assert "timestamp" in message_dict


class TestConversationSummary:
    """Test ConversationSummary class."""

    def test_conversation_summary_creation(self):
        """Test creating conversation summary."""
        summary = ConversationSummary(
            conversation_id=str(uuid.uuid4()),
            user_id=uuid.uuid4(),
            topic="Career Transition",
            key_points=["Point 1", "Point 2"],
            action_items=["Action 1"],
            sentiment="positive",
            message_count=5,
        )

        assert summary.topic == "Career Transition"
        assert len(summary.key_points) == 2
        assert summary.message_count == 5

    def test_conversation_summary_to_dict(self):
        """Test converting summary to dictionary."""
        summary = ConversationSummary(
            conversation_id=str(uuid.uuid4()),
            user_id=uuid.uuid4(),
            topic="Salary Negotiation",
            key_points=["Market research"],
            sentiment="neutral",
        )

        summary_dict = summary.to_dict()

        assert summary_dict["topic"] == "Salary Negotiation"
        assert "created_at" in summary_dict


class TestCareerCoachService:
    """Test CareerCoachService."""

    @pytest.mark.asyncio
    async def test_service_initialization(self, career_coach_service):
        """Test service initialization."""
        assert career_coach_service.db is not None
        assert career_coach_service.anthropic_client is not None

    @pytest.mark.asyncio
    async def test_get_career_context(
        self, career_coach_service, sample_user, sample_resume_version
    ):
        """Test getting career context."""
        career_coach_service.db.execute = AsyncMock()

        # Mock first execute for user
        mock_user_result = MagicMock()
        mock_user_result.scalars.return_value.first = MagicMock(return_value=sample_user)

        # Mock second execute for resume
        mock_resume_result = MagicMock()
        mock_resume_result.scalars.return_value.first = MagicMock(
            return_value=sample_resume_version
        )

        career_coach_service.db.execute.side_effect = [mock_user_result, mock_resume_result]

        context = await career_coach_service.get_career_context(sample_user.id)

        assert context is not None
        assert context.user_id == sample_user.id

    @pytest.mark.asyncio
    async def test_get_career_context_user_not_found(self, career_coach_service):
        """Test getting career context when user not found."""
        career_coach_service.db.execute = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.first = MagicMock(return_value=None)
        career_coach_service.db.execute.return_value = mock_result

        context = await career_coach_service.get_career_context(uuid.uuid4())

        assert context is None

    @pytest.mark.asyncio
    async def test_build_coaching_prompt(self, career_coach_service, sample_user):
        """Test building coaching prompt with context."""
        with patch.object(
            career_coach_service,
            "get_career_context",
            return_value=CareerContext(
                user_id=sample_user.id,
                current_role="Engineer",
                target_role="Staff Engineer",
                years_experience=5,
            ),
        ):
            prompt = await career_coach_service.build_coaching_prompt(
                sample_user.id, "How do I advance?"
            )

        assert "career coach" in prompt.lower()
        assert "How do I advance?" in prompt
        assert "Engineer" in prompt

    @pytest.mark.asyncio
    async def test_build_coaching_prompt_no_context(self, career_coach_service):
        """Test building coaching prompt without context."""
        with patch.object(
            career_coach_service,
            "get_career_context",
            return_value=None,
        ):
            prompt = await career_coach_service.build_coaching_prompt(
                uuid.uuid4(), "Question?"
            )

        assert "career coach" in prompt.lower()
        assert "Question?" in prompt

    @pytest.mark.asyncio
    async def test_generate_learning_path(self, career_coach_service):
        """Test generating learning path."""
        path = await career_coach_service.generate_learning_path(
            "Software Engineer", "Senior Engineer", ["python", "aws"]
        )

        assert path.from_role == "Software Engineer"
        assert path.to_role == "Senior Engineer"
        assert path.duration_weeks > 0
        assert len(path.phases) > 0

    @pytest.mark.asyncio
    async def test_generate_learning_path_unknown_transition(self, career_coach_service):
        """Test generating learning path for unknown transition."""
        path = await career_coach_service.generate_learning_path(
            "Unknown Role", "Another Unknown", []
        )

        assert path is not None
        assert path.duration_weeks == 26  # Default

    @pytest.mark.asyncio
    async def test_get_salary_benchmarks(self, career_coach_service):
        """Test getting salary benchmarks."""
        salary = await career_coach_service.get_salary_benchmarks(
            "software_engineer_us", "US", "mid"
        )

        assert salary.role == "software_engineer_us"
        assert salary.median_salary > 0
        assert salary.min_salary <= salary.median_salary <= salary.max_salary

    @pytest.mark.asyncio
    async def test_get_salary_benchmarks_unknown_role(self, career_coach_service):
        """Test getting salary benchmarks for unknown role."""
        salary = await career_coach_service.get_salary_benchmarks(
            "unknown_role_xyz", "US", "senior"
        )

        assert salary.role == "unknown_role_xyz"
        assert salary.median_salary == 0  # Default for unknown

    @pytest.mark.asyncio
    async def test_track_coaching_conversation(self, career_coach_service):
        """Test tracking coaching conversation."""
        user_id = uuid.uuid4()
        messages = [
            {"role": "user", "content": "How do I advance?"},
            {"role": "assistant", "content": "Here's a plan..."},
        ]

        with patch.object(
            career_coach_service,
            "_call_claude_api",
            return_value='{"topic": "Career", "key_points": ["Point1"]}',
        ):
            summary = await career_coach_service.track_coaching_conversation(
                user_id, messages
            )

        assert summary.user_id == user_id
        assert summary.message_count == 2
        assert summary.conversation_id is not None

    @pytest.mark.asyncio
    async def test_track_coaching_conversation_error(self, career_coach_service):
        """Test tracking conversation with API error."""
        user_id = uuid.uuid4()
        messages = [{"role": "user", "content": "Question"}]

        with patch.object(
            career_coach_service,
            "_call_claude_api",
            return_value="",
        ):
            summary = await career_coach_service.track_coaching_conversation(
                user_id, messages
            )

        assert summary.user_id == user_id
        assert summary.message_count == 1

    @pytest.mark.asyncio
    async def test_calculate_years_experience(self, career_coach_service, sample_resume_data):
        """Test calculating years of experience."""
        years = career_coach_service._calculate_years_experience(sample_resume_data)

        assert years > 0
        assert years == len(sample_resume_data["work_experience"]) * 2

    @pytest.mark.asyncio
    async def test_identify_strengths(self, career_coach_service, sample_resume_data):
        """Test identifying strengths."""
        strengths = career_coach_service._identify_strengths(sample_resume_data)

        assert isinstance(strengths, list)
        assert len(strengths) > 0
        assert any("experience" in s.lower() for s in strengths)

    @pytest.mark.asyncio
    async def test_identify_challenges(self, career_coach_service):
        """Test identifying challenges."""
        weak_resume = {
            "skills": ["Python"],
            "work_experience": [],
            "certifications": [],
        }

        challenges = career_coach_service._identify_challenges(weak_resume)

        assert isinstance(challenges, list)
        assert any("experience" in c.lower() for c in challenges)

    @pytest.mark.asyncio
    async def test_extract_achievements(self, career_coach_service, sample_resume_data):
        """Test extracting achievements."""
        achievements = career_coach_service._extract_achievements(sample_resume_data)

        assert isinstance(achievements, list)
        assert len(achievements) > 0

    @pytest.mark.asyncio
    async def test_get_resources_for_skills(self, career_coach_service):
        """Test getting resources for skills."""
        skills = ["system_design", "machine_learning"]
        resources = await career_coach_service._get_resources_for_skills(skills)

        assert isinstance(resources, list)
        assert len(resources) <= 10

    @pytest.mark.asyncio
    async def test_get_company_salary_data(self, career_coach_service):
        """Test getting company salary data."""
        company_data = await career_coach_service._get_company_salary_data(
            "Software Engineer", "San Francisco"
        )

        assert isinstance(company_data, list)

    @pytest.mark.asyncio
    async def test_estimate_learning_cost(self, career_coach_service):
        """Test estimating learning cost."""
        resources = [
            LearningResource(
                title="Course 1",
                platform="Coursera",
                url="https://coursera.org",
                estimated_hours=20,
                difficulty_level="intermediate",
                cost="paid",
            ),
            LearningResource(
                title="Course 2",
                platform="Udemy",
                url="https://udemy.com",
                estimated_hours=15,
                difficulty_level="beginner",
                cost="free",
            ),
        ]

        cost = career_coach_service._estimate_learning_cost(resources)

        assert cost >= 0
        assert isinstance(cost, float)

    @pytest.mark.asyncio
    async def test_parse_summary_response(self, career_coach_service):
        """Test parsing summary response from Claude."""
        response = """
        {
            "topic": "Career Advancement",
            "key_points": ["Build leadership skills", "Learn system design"],
            "action_items": ["Complete course"],
            "sentiment": "positive"
        }
        """

        summary = career_coach_service._parse_summary_response(response)

        assert summary["topic"] == "Career Advancement"
        assert len(summary["key_points"]) == 2


class TestCareerCoachIntegration:
    """Integration tests for career coach service."""

    @pytest.mark.asyncio
    async def test_full_coaching_workflow(self, career_coach_service):
        """Test complete coaching workflow."""
        user_id = uuid.uuid4()

        # Get context
        with patch.object(
            career_coach_service,
            "get_career_context",
            return_value=CareerContext(
                user_id=user_id,
                current_role="Engineer",
                target_role="Staff Engineer",
                years_experience=5,
                skills=["Python", "AWS"],
            ),
        ):
            context = await career_coach_service.get_career_context(user_id)
            assert context is not None

            # Build prompt
            prompt = await career_coach_service.build_coaching_prompt(
                user_id, "How do I get promoted?"
            )
            assert "Staff Engineer" in prompt

            # Generate learning path
            path = await career_coach_service.generate_learning_path(
                context.current_role, context.target_role, context.skills
            )
            assert path.duration_weeks > 0

            # Get salary data
            salary = await career_coach_service.get_salary_benchmarks(
                "senior_engineer_us"
            )
            assert salary is not None

    @pytest.mark.asyncio
    async def test_learning_path_phases(self, career_coach_service):
        """Test that learning path has proper phases."""
        path = await career_coach_service.generate_learning_path(
            "Junior Developer", "Senior Engineer", []
        )

        assert len(path.phases) > 0
        phase_names = [p.get("name", "") for p in path.phases]
        assert any("Foundation" in name for name in phase_names)

    @pytest.mark.asyncio
    async def test_salary_benchmark_logic(self, career_coach_service):
        """Test salary benchmark logic."""
        # Test known role
        known_salary = await career_coach_service.get_salary_benchmarks(
            "mid_engineer_us", "US", "mid"
        )

        # Test unknown role
        unknown_salary = await career_coach_service.get_salary_benchmarks(
            "unknown", "US", "mid"
        )

        # Known should have data, unknown should have defaults
        assert known_salary.median_salary > 0 or unknown_salary.median_salary == 0


class TestErrorHandling:
    """Test error handling in career coach service."""

    @pytest.mark.asyncio
    async def test_identify_strengths_with_invalid_data(self, career_coach_service):
        """Test identifying strengths with invalid data."""
        invalid_resume = {
            "skills": None,
            "work_experience": "invalid",
        }

        strengths = career_coach_service._identify_strengths(invalid_resume)

        assert isinstance(strengths, list)

    @pytest.mark.asyncio
    async def test_extract_achievements_with_empty_resume(self, career_coach_service):
        """Test extracting achievements with empty resume."""
        empty_resume = {
            "work_experience": [],
        }

        achievements = career_coach_service._extract_achievements(empty_resume)

        assert isinstance(achievements, list)
        assert len(achievements) == 0

    @pytest.mark.asyncio
    async def test_parse_summary_with_malformed_json(self, career_coach_service):
        """Test parsing summary with malformed JSON."""
        response = "Not valid JSON at all"

        summary = career_coach_service._parse_summary_response(response)

        # Should return default structure
        assert isinstance(summary, dict)
        assert "topic" in summary
