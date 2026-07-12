"""Comprehensive integration tests for Resume Versioning Service."""
from __future__ import annotations

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.resume import Resume
from app.models.resume_version import ChangeType, ResumeVersion
from app.services.resume_versioning_service import ContentDiff, ResumVersioningService


@pytest.fixture
def resume_versioning_service():
    """Create resume versioning service with mock DB."""
    mock_db = AsyncMock(spec=AsyncSession)
    return ResumVersioningService(mock_db)


@pytest.fixture
def sample_user_id():
    """Sample user ID."""
    return uuid.uuid4()


@pytest.fixture
def sample_resume_id():
    """Sample resume ID."""
    return uuid.uuid4()


@pytest.fixture
def sample_parsed_data():
    """Sample parsed resume data."""
    return {
        "personal_info": {
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "+1-555-0123",
        },
        "work_experience": [
            {
                "position": "Senior Software Engineer",
                "company": "Tech Corp",
                "start_date": "2020-01-15",
                "end_date": "2024-01-15",
                "description": "Led microservices team",
            }
        ],
        "education": [
            {
                "degree": "BS Computer Science",
                "institution": "State University",
                "graduation_year": 2015,
            }
        ],
        "skills": ["python", "java", "sql", "aws", "kubernetes"],
        "certifications": ["AWS Solutions Architect"],
    }


@pytest.fixture
def sample_raw_text():
    """Sample raw resume text."""
    return """JOHN DOE
    john@example.com | 555-0123

    EXPERIENCE
    Senior Software Engineer - Tech Corp (2020-2024)
    Led microservices team, designed scalable systems

    EDUCATION
    BS Computer Science - State University (2015)

    SKILLS
    Python, Java, SQL, AWS, Kubernetes
    """


@pytest.fixture
def sample_resume_version(sample_parsed_data, sample_raw_text, sample_user_id, sample_resume_id):
    """Create a sample resume version."""
    version = MagicMock(spec=ResumeVersion)
    version.id = uuid.uuid4()
    version.resume_id = sample_resume_id
    version.user_id = sample_user_id
    version.version_number = 1
    version.is_current = True
    version.parsed_data = sample_parsed_data
    version.raw_narrative = sample_raw_text
    version.file_id = "file-123"
    version.file_name = "resume.pdf"
    version.file_size_bytes = 102400
    version.file_type = "application/pdf"
    version.quality_score = 85.0
    version.completeness_percentage = 90
    version.sections_detected = {
        "personal_info": {"present": True, "item_count": 1},
        "work_experience": {"present": True, "item_count": 1},
    }
    version.change_type = ChangeType.upload
    version.created_at = datetime.utcnow()
    version.archived_at = None
    return version


class TestContentDiff:
    """Test ContentDiff class."""

    def test_content_diff_initialization(self):
        """Test ContentDiff initialization."""
        diff = ContentDiff()

        assert diff.added_lines == []
        assert diff.removed_lines == []
        assert diff.modified_lines == []
        assert diff.unified_diff == ""
        assert diff.metrics["total_additions"] == 0
        assert diff.metrics["total_deletions"] == 0

    def test_content_diff_to_dict(self):
        """Test converting ContentDiff to dictionary."""
        diff = ContentDiff()
        diff.added_lines = ["Python developer"]
        diff.metrics["total_additions"] = 1

        result = diff.to_dict()

        assert "added_lines" in result
        assert "removed_lines" in result
        assert "unified_diff" in result
        assert "metrics" in result
        assert result["metrics"]["total_additions"] == 1


class TestResumVersioningServiceCreateVersion:
    """Test version creation functionality."""

    @pytest.mark.asyncio
    async def test_create_version_success(
        self,
        resume_versioning_service,
        sample_user_id,
        sample_resume_id,
        sample_parsed_data,
        sample_raw_text,
    ):
        """Test successful version creation."""
        # Mock database operations
        resume_versioning_service._get_next_version_number = AsyncMock(return_value=1)
        resume_versioning_service._mark_previous_as_current = AsyncMock()

        version = await resume_versioning_service.create_version(
            user_id=sample_user_id,
            resume_id=sample_resume_id,
            file_id="file-123",
            extracted_text=sample_raw_text,
            parsed_data=sample_parsed_data,
            change_type=ChangeType.upload,
            change_summary="Initial upload",
            file_name="resume.pdf",
            file_size_bytes=102400,
            file_type="application/pdf",
        )

        assert version.resume_id == sample_resume_id
        assert version.user_id == sample_user_id
        assert version.version_number == 1
        assert version.is_current is True
        assert version.quality_score is not None
        assert version.completeness_percentage is not None

    @pytest.mark.asyncio
    async def test_create_version_increments_number(
        self,
        resume_versioning_service,
        sample_user_id,
        sample_resume_id,
        sample_raw_text,
    ):
        """Test that version numbers increment properly."""
        resume_versioning_service._get_next_version_number = AsyncMock(return_value=3)
        resume_versioning_service._mark_previous_as_current = AsyncMock()

        version = await resume_versioning_service.create_version(
            user_id=sample_user_id,
            resume_id=sample_resume_id,
            file_id="file-123",
            extracted_text=sample_raw_text,
            change_type=ChangeType.edit,
        )

        assert version.version_number == 3

    @pytest.mark.asyncio
    async def test_create_version_marks_previous_archived(
        self,
        resume_versioning_service,
        sample_user_id,
        sample_resume_id,
        sample_raw_text,
    ):
        """Test that previous version is marked as archived."""
        resume_versioning_service._get_next_version_number = AsyncMock(return_value=2)
        resume_versioning_service._mark_previous_as_current = AsyncMock()

        await resume_versioning_service.create_version(
            user_id=sample_user_id,
            resume_id=sample_resume_id,
            file_id="file-123",
            extracted_text=sample_raw_text,
        )

        resume_versioning_service._mark_previous_as_current.assert_called_once_with(
            sample_resume_id
        )

    @pytest.mark.asyncio
    async def test_create_version_with_minimal_data(
        self, resume_versioning_service, sample_user_id, sample_resume_id
    ):
        """Test creating version with minimal required data."""
        resume_versioning_service._get_next_version_number = AsyncMock(return_value=1)
        resume_versioning_service._mark_previous_as_current = AsyncMock()

        version = await resume_versioning_service.create_version(
            user_id=sample_user_id,
            resume_id=sample_resume_id,
            file_id="file-123",
            extracted_text="",
        )

        assert version is not None
        assert version.version_number == 1


class TestResumVersioningServiceGetVersionHistory:
    """Test version history retrieval."""

    @pytest.mark.asyncio
    async def test_get_version_history_success(
        self, resume_versioning_service, sample_resume_id, sample_resume_version
    ):
        """Test retrieving version history."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_resume_version]
        resume_versioning_service.db.execute = AsyncMock(return_value=mock_result)

        result = await resume_versioning_service.get_version_history(sample_resume_id)

        assert len(result) == 1
        assert result[0].version_number == 1

    @pytest.mark.asyncio
    async def test_get_version_history_empty(
        self, resume_versioning_service, sample_resume_id
    ):
        """Test retrieving history for resume with no versions."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        resume_versioning_service.db.execute = AsyncMock(return_value=mock_result)

        result = await resume_versioning_service.get_version_history(sample_resume_id)

        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_get_version_history_with_limit(
        self, resume_versioning_service, sample_resume_id, sample_resume_version
    ):
        """Test retrieving version history with limit."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_resume_version]
        resume_versioning_service.db.execute = AsyncMock(return_value=mock_result)

        result = await resume_versioning_service.get_version_history(
            sample_resume_id, limit=5
        )

        assert len(result) >= 0


class TestResumVersioningServiceRevertToVersion:
    """Test version revert functionality."""

    @pytest.mark.asyncio
    async def test_revert_to_version_success(
        self,
        resume_versioning_service,
        sample_user_id,
        sample_resume_id,
        sample_resume_version,
    ):
        """Test reverting to a previous version."""
        mock_resume = MagicMock(spec=Resume)
        mock_resume.id = sample_resume_id

        # Mock version retrieval
        resume_versioning_service._get_version = AsyncMock(
            return_value=sample_resume_version
        )

        # Mock version creation
        new_version = MagicMock(spec=ResumeVersion)
        new_version.id = uuid.uuid4()
        new_version.version_number = 2
        resume_versioning_service.create_version = AsyncMock(
            return_value=new_version
        )

        # Mock resume retrieval and update
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_resume
        resume_versioning_service.db.execute = AsyncMock(return_value=mock_result)

        result = await resume_versioning_service.revert_to_version(
            sample_resume_id, sample_resume_version.id
        )

        assert result is not None
        resume_versioning_service.create_version.assert_called_once()

    @pytest.mark.asyncio
    async def test_revert_version_not_found(
        self, resume_versioning_service, sample_resume_id
    ):
        """Test reverting to nonexistent version."""
        resume_versioning_service._get_version = AsyncMock(return_value=None)

        with pytest.raises(ValueError):
            await resume_versioning_service.revert_to_version(
                sample_resume_id, uuid.uuid4()
            )

    @pytest.mark.asyncio
    async def test_revert_mismatched_resume(
        self, resume_versioning_service, sample_resume_version
    ):
        """Test reverting with mismatched resume ID."""
        wrong_resume_id = uuid.uuid4()
        resume_versioning_service._get_version = AsyncMock(
            return_value=sample_resume_version
        )

        with pytest.raises(ValueError):
            await resume_versioning_service.revert_to_version(
                wrong_resume_id, sample_resume_version.id
            )


class TestResumVersioningServiceComputeDiff:
    """Test diff computation."""

    @pytest.mark.asyncio
    async def test_compute_diff_success(
        self,
        resume_versioning_service,
        sample_resume_id,
    ):
        """Test computing diff between two versions."""
        v1 = MagicMock()
        v1.id = uuid.uuid4()
        v1.resume_id = sample_resume_id
        v1.version_number = 1
        v1.raw_narrative = "John Doe\nSoftware Engineer"

        v2 = MagicMock()
        v2.id = uuid.uuid4()
        v2.resume_id = sample_resume_id
        v2.version_number = 2
        v2.raw_narrative = "John Doe\nSenior Software Engineer\nPython Expert"

        resume_versioning_service._get_version = AsyncMock(
            side_effect=lambda vid: v1 if vid == v1.id else v2
        )

        diff = await resume_versioning_service.compute_diff(v1.id, v2.id)

        assert isinstance(diff, ContentDiff)
        assert len(diff.added_lines) > 0 or len(diff.removed_lines) > 0
        assert diff.metrics["total_additions"] >= 0
        assert diff.metrics["total_deletions"] >= 0

    @pytest.mark.asyncio
    async def test_compute_diff_version_not_found(self, resume_versioning_service):
        """Test diff computation with missing version."""
        resume_versioning_service._get_version = AsyncMock(return_value=None)

        with pytest.raises(ValueError, match="One or both versions not found"):
            await resume_versioning_service.compute_diff(uuid.uuid4(), uuid.uuid4())

    @pytest.mark.asyncio
    async def test_compute_diff_different_resumes(
        self, resume_versioning_service
    ):
        """Test diff computation with versions from different resumes."""
        v1 = MagicMock()
        v1.id = uuid.uuid4()
        v1.resume_id = uuid.uuid4()
        v1.raw_narrative = "Test"

        v2 = MagicMock()
        v2.id = uuid.uuid4()
        v2.resume_id = uuid.uuid4()
        v2.raw_narrative = "Test"

        resume_versioning_service._get_version = AsyncMock(
            side_effect=lambda vid: v1 if vid == v1.id else v2
        )

        with pytest.raises(ValueError, match="Versions belong to different resumes"):
            await resume_versioning_service.compute_diff(v1.id, v2.id)

    @pytest.mark.asyncio
    async def test_compute_diff_identical_content(
        self, resume_versioning_service, sample_resume_id
    ):
        """Test diff computation with identical content."""
        v1 = MagicMock()
        v1.id = uuid.uuid4()
        v1.resume_id = sample_resume_id
        v1.version_number = 1
        v1.raw_narrative = "Same content"

        v2 = MagicMock()
        v2.id = uuid.uuid4()
        v2.resume_id = sample_resume_id
        v2.version_number = 2
        v2.raw_narrative = "Same content"

        resume_versioning_service._get_version = AsyncMock(
            side_effect=lambda vid: v1 if vid == v1.id else v2
        )

        diff = await resume_versioning_service.compute_diff(v1.id, v2.id)

        assert len(diff.added_lines) == 0
        assert len(diff.removed_lines) == 0
        assert diff.metrics["change_percentage"] == 0.0


class TestResumVersioningServiceCompareAssessments:
    """Test assessment comparison."""

    @pytest.mark.asyncio
    async def test_compare_assessments_quality_improvement(
        self, resume_versioning_service
    ):
        """Test comparing assessments with quality improvement."""
        v1 = MagicMock(spec=ResumeVersion)
        v1.id = uuid.uuid4()
        v1.quality_score = 70.0
        v1.completeness_percentage = 75
        v1.sections_detected = {"personal_info": {}}

        v2 = MagicMock(spec=ResumeVersion)
        v2.id = uuid.uuid4()
        v2.quality_score = 85.0
        v2.completeness_percentage = 90
        v2.sections_detected = {"personal_info": {}, "work_experience": {}}

        result = await resume_versioning_service.compare_assessments(v1, v2)

        assert result["score_delta"] == 15
        assert "improved" in result["summary"].lower()
        assert len(result["changes"]) > 0

    @pytest.mark.asyncio
    async def test_compare_assessments_quality_decline(
        self, resume_versioning_service
    ):
        """Test comparing assessments with quality decline."""
        v1 = MagicMock(spec=ResumeVersion)
        v1.id = uuid.uuid4()
        v1.quality_score = 85.0
        v1.completeness_percentage = 90
        v1.sections_detected = {}

        v2 = MagicMock(spec=ResumeVersion)
        v2.id = uuid.uuid4()
        v2.quality_score = 70.0
        v2.completeness_percentage = 75
        v2.sections_detected = {}

        result = await resume_versioning_service.compare_assessments(v1, v2)

        assert result["score_delta"] == -15
        assert "declined" in result["summary"].lower()

    @pytest.mark.asyncio
    async def test_compare_assessments_no_change(
        self, resume_versioning_service
    ):
        """Test comparing identical assessments."""
        v1 = MagicMock(spec=ResumeVersion)
        v1.id = uuid.uuid4()
        v1.quality_score = 80.0
        v1.completeness_percentage = 85
        v1.sections_detected = {"personal_info": {}}

        v2 = MagicMock(spec=ResumeVersion)
        v2.id = uuid.uuid4()
        v2.quality_score = 80.0
        v2.completeness_percentage = 85
        v2.sections_detected = {"personal_info": {}}

        result = await resume_versioning_service.compare_assessments(v1, v2)

        assert result["score_delta"] == 0
        assert "unchanged" in result["summary"].lower()

    @pytest.mark.asyncio
    async def test_compare_assessments_section_changes(
        self, resume_versioning_service
    ):
        """Test comparing assessments with section changes."""
        v1 = MagicMock(spec=ResumeVersion)
        v1.id = uuid.uuid4()
        v1.quality_score = 80.0
        v1.completeness_percentage = 80
        v1.sections_detected = {"personal_info": {}, "education": {}}

        v2 = MagicMock(spec=ResumeVersion)
        v2.id = uuid.uuid4()
        v2.quality_score = 85.0
        v2.completeness_percentage = 90
        v2.sections_detected = {
            "personal_info": {},
            "education": {},
            "work_experience": {},
            "skills": {},
        }

        result = await resume_versioning_service.compare_assessments(v1, v2)

        assert any(
            change["metric"] == "sections_added" for change in result["changes"]
        )


class TestResumVersioningServiceQualityCalculation:
    """Test quality score calculations."""

    def test_calculate_quality_score_complete(
        self, resume_versioning_service, sample_parsed_data, sample_raw_text
    ):
        """Test quality score for complete resume."""
        score = resume_versioning_service._calculate_quality_score(
            sample_parsed_data, sample_raw_text
        )

        assert 0 <= score <= 100
        assert score > 70  # Should be high for complete resume

    def test_calculate_quality_score_incomplete(self, resume_versioning_service):
        """Test quality score for incomplete resume."""
        incomplete_data = {
            "personal_info": {"name": "John"},
        }

        score = resume_versioning_service._calculate_quality_score(
            incomplete_data, "John Doe"
        )

        assert 0 <= score <= 100
        assert score < 50

    def test_calculate_quality_score_empty(self, resume_versioning_service):
        """Test quality score for empty resume."""
        score = resume_versioning_service._calculate_quality_score({}, "")

        assert score == 0.0

    def test_calculate_quality_score_long_text_bonus(self, resume_versioning_service):
        """Test quality score bonus for longer text."""
        long_text = "x" * 2000
        data = {"personal_info": {"name": "John"}}

        score = resume_versioning_service._calculate_quality_score(data, long_text)

        assert score > 20  # Should get bonus for length

    def test_calculate_completeness(
        self, resume_versioning_service, sample_parsed_data
    ):
        """Test completeness calculation."""
        completeness = resume_versioning_service._calculate_completeness(
            sample_parsed_data
        )

        assert 0 <= completeness <= 100
        assert completeness > 50

    def test_calculate_completeness_empty(self, resume_versioning_service):
        """Test completeness for empty data."""
        completeness = resume_versioning_service._calculate_completeness({})

        assert completeness == 0

    def test_detect_sections(
        self, resume_versioning_service, sample_parsed_data
    ):
        """Test section detection."""
        sections = resume_versioning_service._detect_sections(sample_parsed_data)

        assert "personal_info" in sections
        assert "work_experience" in sections
        assert sections["personal_info"]["present"] is True


class TestResumVersioningServicePrivateMethods:
    """Test private helper methods."""

    @pytest.mark.asyncio
    async def test_get_next_version_number_first(
        self, resume_versioning_service, sample_resume_id
    ):
        """Test getting first version number."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        resume_versioning_service.db.execute = AsyncMock(return_value=mock_result)

        version_num = await resume_versioning_service._get_next_version_number(
            sample_resume_id
        )

        assert version_num == 1

    @pytest.mark.asyncio
    async def test_get_next_version_number_increments(
        self, resume_versioning_service, sample_resume_id
    ):
        """Test version number incrementation."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = 5
        resume_versioning_service.db.execute = AsyncMock(return_value=mock_result)

        version_num = await resume_versioning_service._get_next_version_number(
            sample_resume_id
        )

        assert version_num == 6

    @pytest.mark.asyncio
    async def test_mark_previous_as_current_no_current(
        self, resume_versioning_service, sample_resume_id
    ):
        """Test marking previous as current when none exists."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        resume_versioning_service.db.execute = AsyncMock(return_value=mock_result)

        await resume_versioning_service._mark_previous_as_current(sample_resume_id)

        # Should handle gracefully
        resume_versioning_service.db.execute.assert_called()


class TestResumVersioningServiceIntegration:
    """Integration tests for the service."""

    @pytest.mark.asyncio
    async def test_full_versioning_workflow(
        self,
        resume_versioning_service,
        sample_user_id,
        sample_resume_id,
        sample_parsed_data,
        sample_raw_text,
    ):
        """Test complete versioning workflow."""
        resume_versioning_service._get_next_version_number = AsyncMock(
            side_effect=[1, 2]
        )
        resume_versioning_service._mark_previous_as_current = AsyncMock()

        # Create first version
        v1 = await resume_versioning_service.create_version(
            user_id=sample_user_id,
            resume_id=sample_resume_id,
            file_id="file-1",
            extracted_text=sample_raw_text,
            parsed_data=sample_parsed_data,
            change_type=ChangeType.upload,
        )

        assert v1.version_number == 1

        # Create second version
        v2 = await resume_versioning_service.create_version(
            user_id=sample_user_id,
            resume_id=sample_resume_id,
            file_id="file-2",
            extracted_text=sample_raw_text + "\nPython Expert",
            parsed_data=sample_parsed_data,
            change_type=ChangeType.edit,
        )

        assert v2.version_number == 2
