"""Comprehensive tests for Resume Versioning Service."""
from __future__ import annotations

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.resume_version import ChangeType, ResumeVersion
from app.services.resume_versioning import ResumeDiff, ResumeVersioningService


@pytest.fixture
def resume_versioning_service():
    """Create a resume versioning service with mock DB."""
    mock_db = AsyncMock(spec=AsyncSession)
    return ResumeVersioningService(mock_db)


@pytest.fixture
def sample_parsed_data():
    """Create sample parsed resume data."""
    return {
        "personal_info": {
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "555-1234",
        },
        "work_experience": [
            {
                "position": "Senior Engineer",
                "company": "Tech Corp",
                "start_date": "2020-01-01",
                "end_date": "2023-01-01",
                "description": "Led team of 5 engineers on microservices",
            }
        ],
        "education": [
            {
                "degree": "BS Computer Science",
                "institution": "State University",
                "graduation_year": 2015,
            }
        ],
        "skills": ["python", "java", "sql", "docker", "kubernetes"],
        "certifications": ["AWS Solutions Architect"],
    }


@pytest.fixture
def sample_version(sample_parsed_data):
    """Create a sample resume version."""
    version = MagicMock(spec=ResumeVersion)
    version.id = uuid.uuid4()
    version.resume_id = uuid.uuid4()
    version.user_id = uuid.uuid4()
    version.version_number = 1
    version.is_current = True
    version.parsed_data = sample_parsed_data
    version.raw_narrative = "John Doe\nExperienced software engineer..."
    version.quality_score = 85.0
    version.completeness_percentage = 90
    version.sections_detected = {"personal_info": {"present": True}, "work_experience": {"present": True}}
    version.change_type = ChangeType.upload
    version.created_at = datetime(2026, 1, 1)
    return version


class TestResumeDiff:
    """Test ResumeDiff class."""

    def test_resume_diff_initialization(self):
        """Test ResumeDiff initialization."""
        diff = ResumeDiff()

        assert diff.added_sections == {}
        assert diff.removed_sections == {}
        assert diff.modified_sections == {}
        assert diff.unchanged_sections == {}
        assert diff.metrics == {}

    def test_resume_diff_to_dict(self):
        """Test converting ResumeDiff to dictionary."""
        diff = ResumeDiff()
        diff.added_sections = {"skills": ["python"]}
        diff.metrics = {"sections_added": 1}

        result = diff.to_dict()

        assert "added_sections" in result
        assert "removed_sections" in result
        assert "modified_sections" in result
        assert "metrics" in result
        assert result["added_sections"]["skills"] == ["python"]


class TestResumeVersioningServiceCreateVersion:
    """Test version creation functionality."""

    @pytest.mark.asyncio
    async def test_create_version_success(self, resume_versioning_service, sample_parsed_data):
        """Test successful version creation."""
        resume_id = uuid.uuid4()
        user_id = uuid.uuid4()

        resume_versioning_service._get_next_version_number = AsyncMock(return_value=1)
        resume_versioning_service._mark_previous_as_archived = AsyncMock()

        version = await resume_versioning_service.create_version(
            resume_id=resume_id,
            user_id=user_id,
            parsed_data=sample_parsed_data,
            raw_narrative="Test narrative",
            change_type=ChangeType.upload,
            change_summary="Initial upload",
        )

        assert version.resume_id == resume_id
        assert version.user_id == user_id
        assert version.version_number == 1
        assert version.is_current is True
        assert version.quality_score is not None
        assert version.completeness_percentage is not None

    @pytest.mark.asyncio
    async def test_create_version_marks_previous_as_archived(
        self, resume_versioning_service, sample_parsed_data
    ):
        """Test that previous version is marked as archived."""
        resume_versioning_service._get_next_version_number = AsyncMock(return_value=2)
        resume_versioning_service._mark_previous_as_archived = AsyncMock()

        await resume_versioning_service.create_version(
            resume_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            parsed_data=sample_parsed_data,
            raw_narrative="Test",
            change_type=ChangeType.edit,
        )

        resume_versioning_service._mark_previous_as_archived.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_version_increments_version_number(
        self, resume_versioning_service, sample_parsed_data
    ):
        """Test version number incrementation."""
        resume_versioning_service._get_next_version_number = AsyncMock(return_value=3)
        resume_versioning_service._mark_previous_as_archived = AsyncMock()

        version = await resume_versioning_service.create_version(
            resume_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            parsed_data=sample_parsed_data,
            raw_narrative="Test",
            change_type=ChangeType.edit,
        )

        assert version.version_number == 3


class TestResumeVersioningServiceGetVersion:
    """Test version retrieval functionality."""

    @pytest.mark.asyncio
    async def test_get_version_success(self, resume_versioning_service, sample_version):
        """Test retrieving a version."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = sample_version
        resume_versioning_service.db.execute = AsyncMock(return_value=mock_result)

        result = await resume_versioning_service.get_version(sample_version.id)

        assert result == sample_version

    @pytest.mark.asyncio
    async def test_get_current_version(self, resume_versioning_service, sample_version):
        """Test getting the current version."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = sample_version
        resume_versioning_service.db.execute = AsyncMock(return_value=mock_result)

        result = await resume_versioning_service.get_current_version(sample_version.resume_id)

        assert result == sample_version


class TestResumeVersioningServiceComputeDiff:
    """Test diff computation."""

    @pytest.mark.asyncio
    async def test_compute_diff_success(self, resume_versioning_service):
        """Test computing diff between two versions."""
        v1_data = {
            "personal_info": {"name": "John Doe"},
            "skills": ["python", "java"],
        }

        v2_data = {
            "personal_info": {"name": "John Doe"},
            "skills": ["python", "java", "sql"],
            "certifications": ["AWS"],
        }

        v1 = MagicMock()
        v1.id = uuid.uuid4()
        v1.resume_id = uuid.uuid4()
        v1.parsed_data = v1_data

        v2 = MagicMock()
        v2.id = uuid.uuid4()
        v2.resume_id = v1.resume_id
        v2.parsed_data = v2_data
        v2.quality_score = 85.0
        v2.completeness_percentage = 90

        resume_versioning_service.get_version = AsyncMock(
            side_effect=lambda vid: v1 if vid == v1.id else v2
        )

        diff = await resume_versioning_service.compute_diff(v1.id, v2.id)

        assert isinstance(diff, ResumeDiff)
        assert "certifications" in diff.added_sections
        assert "skills" in diff.modified_sections
        assert "personal_info" in diff.unchanged_sections
        assert diff.metrics["sections_added"] == 1
        assert diff.metrics["sections_modified"] == 1

    @pytest.mark.asyncio
    async def test_compute_diff_version_not_found(self, resume_versioning_service):
        """Test diff computation with missing version."""
        resume_versioning_service.get_version = AsyncMock(return_value=None)

        with pytest.raises(ValueError, match="One or both versions not found"):
            await resume_versioning_service.compute_diff(uuid.uuid4(), uuid.uuid4())

    @pytest.mark.asyncio
    async def test_compute_diff_different_resumes(self, resume_versioning_service):
        """Test diff computation with versions from different resumes."""
        v1 = MagicMock()
        v1.id = uuid.uuid4()
        v1.resume_id = uuid.uuid4()

        v2 = MagicMock()
        v2.id = uuid.uuid4()
        v2.resume_id = uuid.uuid4()

        resume_versioning_service.get_version = AsyncMock(
            side_effect=lambda vid: v1 if vid == v1.id else v2
        )

        with pytest.raises(ValueError, match="Versions belong to different resumes"):
            await resume_versioning_service.compute_diff(v1.id, v2.id)


class TestResumeVersioningServiceRollback:
    """Test version rollback functionality."""

    @pytest.mark.asyncio
    async def test_rollback_to_version_success(
        self, resume_versioning_service, sample_version
    ):
        """Test rolling back to a previous version."""
        new_version = MagicMock()
        new_version.id = uuid.uuid4()
        new_version.version_number = 2

        resume_versioning_service.get_version = AsyncMock(return_value=sample_version)
        resume_versioning_service.create_version = AsyncMock(return_value=new_version)

        result = await resume_versioning_service.rollback_to_version(
            sample_version.resume_id, sample_version.id, sample_version.user_id
        )

        assert result == new_version
        resume_versioning_service.create_version.assert_called_once()

    @pytest.mark.asyncio
    async def test_rollback_version_not_found(self, resume_versioning_service):
        """Test rollback with nonexistent version."""
        resume_versioning_service.get_version = AsyncMock(return_value=None)

        with pytest.raises(ValueError):
            await resume_versioning_service.rollback_to_version(
                uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
            )


class TestResumeVersioningServiceHistory:
    """Test version history retrieval."""

    @pytest.mark.asyncio
    async def test_get_version_history_success(
        self, resume_versioning_service, sample_version
    ):
        """Test getting version history."""
        resume_versioning_service.get_all_versions = AsyncMock(
            return_value=[sample_version]
        )

        result = await resume_versioning_service.get_version_history(
            sample_version.resume_id
        )

        assert result["resume_id"] == str(sample_version.resume_id)
        assert result["total_versions"] == 1
        assert len(result["versions"]) == 1
        assert len(result["timeline"]) == 1

    @pytest.mark.asyncio
    async def test_get_version_history_empty(self, resume_versioning_service):
        """Test getting history with no versions."""
        resume_versioning_service.get_all_versions = AsyncMock(return_value=[])

        result = await resume_versioning_service.get_version_history(uuid.uuid4())

        assert result["total_versions"] == 0
        assert len(result["versions"]) == 0

    @pytest.mark.asyncio
    async def test_compare_consecutive_versions(self, resume_versioning_service):
        """Test comparing consecutive versions."""
        v1 = MagicMock()
        v1.id = uuid.uuid4()
        v1.version_number = 1
        v1.resume_id = uuid.uuid4()
        v1.created_at = datetime(2026, 1, 1)
        v1.change_type = ChangeType.upload

        v2 = MagicMock()
        v2.id = uuid.uuid4()
        v2.version_number = 2
        v2.resume_id = v1.resume_id
        v2.created_at = datetime(2026, 6, 1)
        v2.change_type = ChangeType.edit

        resume_versioning_service.get_all_versions = AsyncMock(return_value=[v2, v1])
        resume_versioning_service.compute_diff = AsyncMock(
            return_value=ResumeDiff()
        )

        result = await resume_versioning_service.compare_consecutive_versions(
            v1.resume_id
        )

        assert len(result) == 1
        assert result[0]["from_version"] == 1
        assert result[0]["to_version"] == 2


class TestResumeVersioningServiceQualityTrends:
    """Test quality trend analysis."""

    @pytest.mark.asyncio
    async def test_get_quality_trends_improving(self, resume_versioning_service):
        """Test quality trends detection - improving."""
        v1 = MagicMock()
        v1.version_number = 1
        v1.quality_score = 70.0
        v1.completeness_percentage = 75
        v1.created_at = datetime(2026, 1, 1)

        v2 = MagicMock()
        v2.version_number = 2
        v2.quality_score = 85.0
        v2.completeness_percentage = 90
        v2.created_at = datetime(2026, 6, 1)

        resume_id = uuid.uuid4()
        resume_versioning_service.get_all_versions = AsyncMock(
            return_value=[v2, v1]
        )

        result = await resume_versioning_service.get_quality_trends(resume_id)

        assert result["total_versions"] == 2
        assert len(result["quality_scores"]) == 2
        assert result["overall_trend"]["direction"] == "improving"

    @pytest.mark.asyncio
    async def test_get_quality_trends_declining(self, resume_versioning_service):
        """Test quality trends detection - declining."""
        v1 = MagicMock()
        v1.version_number = 1
        v1.quality_score = 85.0
        v1.completeness_percentage = 90
        v1.created_at = datetime(2026, 1, 1)

        v2 = MagicMock()
        v2.version_number = 2
        v2.quality_score = 70.0
        v2.completeness_percentage = 75
        v2.created_at = datetime(2026, 6, 1)

        resume_versioning_service.get_all_versions = AsyncMock(
            return_value=[v2, v1]
        )

        result = await resume_versioning_service.get_quality_trends(uuid.uuid4())

        assert result["overall_trend"]["direction"] == "declining"
        assert result["overall_trend"]["improvement"] < 0


class TestResumeVersioningServiceQualityCalculation:
    """Test quality score calculations."""

    def test_calculate_quality_score_complete(
        self, resume_versioning_service, sample_parsed_data
    ):
        """Test quality score for complete resume."""
        score = resume_versioning_service._calculate_quality_score(sample_parsed_data)

        assert 0 <= score <= 100
        assert score > 80  # Should be high for complete resume

    def test_calculate_quality_score_incomplete(self, resume_versioning_service):
        """Test quality score for incomplete resume."""
        incomplete_data = {
            "personal_info": {"name": "John"},
        }

        score = resume_versioning_service._calculate_quality_score(incomplete_data)

        assert 0 <= score <= 100
        assert score < 50

    def test_calculate_quality_score_empty(self, resume_versioning_service):
        """Test quality score for empty resume."""
        score = resume_versioning_service._calculate_quality_score({})

        assert score == 0.0

    def test_calculate_completeness(self, resume_versioning_service, sample_parsed_data):
        """Test completeness calculation."""
        completeness = resume_versioning_service._calculate_completeness(
            sample_parsed_data
        )

        assert 0 <= completeness <= 100
        assert completeness > 50

    def test_detect_sections(self, resume_versioning_service, sample_parsed_data):
        """Test section detection."""
        sections = resume_versioning_service._detect_sections(sample_parsed_data)

        assert "personal_info" in sections
        assert "work_experience" in sections
        assert "education" in sections
        assert sections["personal_info"]["present"] is True


class TestResumeVersioningServiceDiffComputation:
    """Test detailed diff computation."""

    def test_compute_section_diff_string(self, resume_versioning_service):
        """Test diff computation for string content."""
        content1 = "Python experience\nJava development"
        content2 = "Python expertise\nJava development\nKotlin skills"

        diff = resume_versioning_service._compute_section_diff(content1, content2)

        assert isinstance(diff, list)
        assert len(diff) > 0

    def test_compute_section_diff_list(self, resume_versioning_service):
        """Test diff computation for list content."""
        content1 = ["python", "java"]
        content2 = ["python", "java", "sql"]

        diff = resume_versioning_service._compute_section_diff(content1, content2)

        assert isinstance(diff, dict)
        assert "added" in diff
        assert "sql" in diff["added"]

    def test_compute_section_diff_dict(self, resume_versioning_service):
        """Test diff computation for dict content."""
        content1 = {"name": "John", "title": "Engineer"}
        content2 = {"name": "John", "title": "Senior Engineer"}

        diff = resume_versioning_service._compute_section_diff(content1, content2)

        assert isinstance(diff, dict)
        assert "modified_keys" in diff
        assert "title" in diff["modified_keys"]

    def test_calculate_change_percentage(self, resume_versioning_service):
        """Test change percentage calculation."""
        diff = ResumeDiff()
        diff.added_sections = {"skills": ["python"]}
        diff.removed_sections = {"projects": []}
        diff.modified_sections = {"experience": {}}
        diff.unchanged_sections = {"education": {}}

        percentage = resume_versioning_service._calculate_change_percentage(diff)

        assert 0 <= percentage <= 100
        assert percentage == 75.0  # 3 out of 4 sections changed

    def test_analyze_trend_improving(self, resume_versioning_service):
        """Test trend analysis - improving."""
        scores = [50, 60, 70, 80]

        trend = resume_versioning_service._analyze_trend(scores)

        assert trend == "improving"

    def test_analyze_trend_declining(self, resume_versioning_service):
        """Test trend analysis - declining."""
        scores = [80, 70, 60, 50]

        trend = resume_versioning_service._analyze_trend(scores)

        assert trend == "declining"

    def test_analyze_trend_stable(self, resume_versioning_service):
        """Test trend analysis - stable."""
        scores = [70, 70, 70]

        trend = resume_versioning_service._analyze_trend(scores)

        assert trend == "stable"


class TestResumeVersioningServiceEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_create_version_with_minimal_data(self, resume_versioning_service):
        """Test creating version with minimal data."""
        resume_versioning_service._get_next_version_number = AsyncMock(return_value=1)
        resume_versioning_service._mark_previous_as_archived = AsyncMock()

        version = await resume_versioning_service.create_version(
            resume_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            parsed_data={},
            raw_narrative="",
            change_type=ChangeType.upload,
        )

        assert version.quality_score == 0.0
        assert version.completeness_percentage == 0

    def test_calculate_completeness_null_sections(self, resume_versioning_service):
        """Test completeness calculation with null sections."""
        data = {
            "personal_info": None,
            "work_experience": None,
            "education": None,
        }

        completeness = resume_versioning_service._calculate_completeness(data)

        assert completeness == 0
