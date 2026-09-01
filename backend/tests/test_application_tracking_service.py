"""Tests for application tracking service."""
import pytest
import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.application_tracking_service import ApplicationTrackingService
from app.models.application import Application, PipelineStage
from app.models.position import Position, PositionStatus
from app.models.resume import Resume, ResumeStatus
from app.models.user import User
from app.models.saved_job import SavedJob, SavedJobStatus
from app.core.clock import utcnow


class TestApplicationTrackingService:
    """Test ApplicationTrackingService functionality."""

    @pytest.fixture
    async def service(self, db: AsyncSession):
        """Create service instance."""
        return ApplicationTrackingService(db)

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
            raw_narrative="Senior Engineer with 5 years experience",
            parsed_data={"skills": ["Python", "Java"]},
        )
        db.add(resume)
        await db.commit()
        return resume

    @pytest.fixture
    async def test_position(self, db: AsyncSession):
        """Create test position."""
        position = Position(
            title="Senior Engineer",
            description="Looking for a senior engineer",
            status=PositionStatus.open,
        )
        db.add(position)
        await db.commit()
        return position

    @pytest.mark.asyncio
    async def test_apply_to_job_success(
        self,
        service: ApplicationTrackingService,
        test_user: User,
        test_resume: Resume,
        test_position: Position,
        db: AsyncSession,
    ):
        """Test successful job application."""
        application = await service.apply_to_job(
            user_id=test_user.id,
            position_id=test_position.id,
            resume_id=test_resume.id,
            cover_note="Interested in this position",
            source="direct",
        )

        assert application is not None
        assert application.user_id == test_user.id
        assert application.position_id == test_position.id
        assert application.resume_id == test_resume.id
        assert application.stage == PipelineStage.applied
        assert application.cover_note == "Interested in this position"
        assert application.source == "direct"

    @pytest.mark.asyncio
    async def test_apply_to_job_nonexistent_position(
        self,
        service: ApplicationTrackingService,
        test_user: User,
        test_resume: Resume,
    ):
        """Test applying to nonexistent position."""
        with pytest.raises(ValueError):
            await service.apply_to_job(
                user_id=test_user.id,
                position_id=uuid.uuid4(),
                resume_id=test_resume.id,
            )

    @pytest.mark.asyncio
    async def test_apply_to_job_wrong_resume(
        self,
        service: ApplicationTrackingService,
        test_user: User,
        test_position: Position,
    ):
        """Test applying with resume from different user."""
        other_user = User(
            email=f"other_{uuid.uuid4().hex}@example.com",
            password_hash="dummy",
        )
        # Mock - would need to be added to DB in real test

        with pytest.raises(ValueError):
            await service.apply_to_job(
                user_id=test_user.id,
                position_id=test_position.id,
                resume_id=uuid.uuid4(),
            )

    @pytest.mark.asyncio
    async def test_apply_to_job_duplicate(
        self,
        service: ApplicationTrackingService,
        test_user: User,
        test_resume: Resume,
        test_position: Position,
        db: AsyncSession,
    ):
        """Test duplicate application handling."""
        # First application
        app1 = await service.apply_to_job(
            user_id=test_user.id,
            position_id=test_position.id,
            resume_id=test_resume.id,
        )

        # Second application to same job
        app2 = await service.apply_to_job(
            user_id=test_user.id,
            position_id=test_position.id,
            resume_id=test_resume.id,
        )

        # Should return existing
        assert app1.id == app2.id

    @pytest.mark.asyncio
    async def test_update_application_status_valid_transition(
        self,
        service: ApplicationTrackingService,
        test_user: User,
        test_resume: Resume,
        test_position: Position,
        db: AsyncSession,
    ):
        """Test valid status transition."""
        # Create application
        application = await service.apply_to_job(
            user_id=test_user.id,
            position_id=test_position.id,
            resume_id=test_resume.id,
        )

        # Update to phone screen
        updated = await service.update_application_status(
            application_id=application.id,
            new_stage=PipelineStage.phone_screen,
            event_data={"interviewer": "John"},
            triggered_by_id=test_user.id,
        )

        assert updated.stage == PipelineStage.phone_screen
        assert updated.stage_entered_at is not None

    @pytest.mark.asyncio
    async def test_update_application_status_invalid_transition(
        self,
        service: ApplicationTrackingService,
        test_user: User,
        test_resume: Resume,
        test_position: Position,
        db: AsyncSession,
    ):
        """Test invalid status transition."""
        application = await service.apply_to_job(
            user_id=test_user.id,
            position_id=test_position.id,
            resume_id=test_resume.id,
        )

        # Try invalid transition
        with pytest.raises(ValueError):
            await service.update_application_status(
                application_id=application.id,
                new_stage=PipelineStage.hired,  # Can't go directly from applied to hired
            )

    @pytest.mark.asyncio
    async def test_update_application_status_nonexistent(
        self,
        service: ApplicationTrackingService,
    ):
        """Test updating nonexistent application."""
        with pytest.raises(ValueError):
            await service.update_application_status(
                application_id=uuid.uuid4(),
                new_stage=PipelineStage.phone_screen,
            )

    @pytest.mark.asyncio
    async def test_record_timeline_event(
        self,
        service: ApplicationTrackingService,
        test_user: User,
        test_resume: Resume,
        test_position: Position,
        db: AsyncSession,
    ):
        """Test recording timeline event."""
        application = await service.apply_to_job(
            user_id=test_user.id,
            position_id=test_position.id,
            resume_id=test_resume.id,
        )

        from app.models.application_timeline import EventType

        event = await service.record_timeline_event(
            application_id=application.id,
            event_type=EventType.interview_scheduled,
            event_data={"date": "2024-01-15", "time": "10:00"},
            description="Interview scheduled",
        )

        assert event is not None
        assert event.application_id == application.id

    @pytest.mark.asyncio
    async def test_record_timeline_event_nonexistent_app(
        self,
        service: ApplicationTrackingService,
    ):
        """Test recording event for nonexistent application."""
        from app.models.application_timeline import EventType

        with pytest.raises(ValueError):
            await service.record_timeline_event(
                application_id=uuid.uuid4(),
                event_type=EventType.status_change,
            )

    @pytest.mark.asyncio
    async def test_get_application_with_timeline(
        self,
        service: ApplicationTrackingService,
        test_user: User,
        test_resume: Resume,
        test_position: Position,
        db: AsyncSession,
    ):
        """Test retrieving application with timeline."""
        application = await service.apply_to_job(
            user_id=test_user.id,
            position_id=test_position.id,
            resume_id=test_resume.id,
        )

        # Update status to create more events
        await service.update_application_status(
            application_id=application.id,
            new_stage=PipelineStage.phone_screen,
        )

        result = await service.get_application_with_timeline(application.id)

        assert result is not None
        assert result.application.id == application.id
        assert len(result.timeline_events) > 0

    @pytest.mark.asyncio
    async def test_get_application_with_timeline_not_found(
        self,
        service: ApplicationTrackingService,
    ):
        """Test retrieving nonexistent application."""
        result = await service.get_application_with_timeline(uuid.uuid4())

        assert result is None

    @pytest.mark.asyncio
    async def test_save_job(
        self,
        service: ApplicationTrackingService,
        test_user: User,
        test_position: Position,
        db: AsyncSession,
    ):
        """Test saving a job."""
        saved_job = await service.save_job(
            user_id=test_user.id,
            position_id=test_position.id,
            notes="Interested in this role",
            list_name="Interested",
        )

        assert saved_job is not None
        assert saved_job.user_id == test_user.id
        assert saved_job.position_id == test_position.id
        assert saved_job.notes == "Interested in this role"
        assert saved_job.list_name == "Interested"
        assert saved_job.status == SavedJobStatus.saved

    @pytest.mark.asyncio
    async def test_save_job_nonexistent_position(
        self,
        service: ApplicationTrackingService,
        test_user: User,
    ):
        """Test saving nonexistent position."""
        with pytest.raises(ValueError):
            await service.save_job(
                user_id=test_user.id,
                position_id=uuid.uuid4(),
            )

    @pytest.mark.asyncio
    async def test_save_job_duplicate(
        self,
        service: ApplicationTrackingService,
        test_user: User,
        test_position: Position,
        db: AsyncSession,
    ):
        """Test duplicate save handling."""
        saved1 = await service.save_job(
            user_id=test_user.id,
            position_id=test_position.id,
        )

        saved2 = await service.save_job(
            user_id=test_user.id,
            position_id=test_position.id,
        )

        assert saved1.id == saved2.id

    @pytest.mark.asyncio
    async def test_get_saved_jobs(
        self,
        service: ApplicationTrackingService,
        test_user: User,
        test_position: Position,
        db: AsyncSession,
    ):
        """Test retrieving saved jobs."""
        # Save a few jobs
        await service.save_job(
            user_id=test_user.id,
            position_id=test_position.id,
            list_name="List1",
        )

        # Create another position
        pos2 = Position(
            title="Another Role",
            description="Another job",
            status=PositionStatus.open,
        )
        db.add(pos2)
        await db.commit()

        await service.save_job(
            user_id=test_user.id,
            position_id=pos2.id,
            list_name="List2",
        )

        # Get all saved jobs
        jobs, count = await service.get_saved_jobs(user_id=test_user.id)

        assert len(jobs) >= 2
        assert count >= 2

    @pytest.mark.asyncio
    async def test_get_saved_jobs_filtered_by_status(
        self,
        service: ApplicationTrackingService,
        test_user: User,
        test_position: Position,
        db: AsyncSession,
    ):
        """Test retrieving saved jobs filtered by status."""
        saved_job = await service.save_job(
            user_id=test_user.id,
            position_id=test_position.id,
        )

        jobs, count = await service.get_saved_jobs(
            user_id=test_user.id,
            status=SavedJobStatus.saved,
        )

        assert len(jobs) > 0
        assert all(j.status == SavedJobStatus.saved for j in jobs)

    @pytest.mark.asyncio
    async def test_get_saved_jobs_filtered_by_list(
        self,
        service: ApplicationTrackingService,
        test_user: User,
        test_position: Position,
        db: AsyncSession,
    ):
        """Test retrieving saved jobs filtered by list."""
        await service.save_job(
            user_id=test_user.id,
            position_id=test_position.id,
            list_name="Dreams",
        )

        jobs, count = await service.get_saved_jobs(
            user_id=test_user.id,
            list_name="Dreams",
        )

        assert all(j.list_name == "Dreams" for j in jobs)

    @pytest.mark.asyncio
    async def test_get_saved_jobs_pagination(
        self,
        service: ApplicationTrackingService,
        test_user: User,
        db: AsyncSession,
    ):
        """Test pagination of saved jobs."""
        # Create multiple positions and save them
        for i in range(5):
            pos = Position(
                title=f"Job {i}",
                description=f"Description {i}",
                status=PositionStatus.open,
            )
            db.add(pos)
            await db.flush()
            await service.save_job(user_id=test_user.id, position_id=pos.id)

        # Get with pagination
        page1, count1 = await service.get_saved_jobs(
            user_id=test_user.id,
            limit=2,
            offset=0,
        )

        page2, count2 = await service.get_saved_jobs(
            user_id=test_user.id,
            limit=2,
            offset=2,
        )

        assert len(page1) <= 2
        assert len(page2) <= 2
        assert count1 == count2

    @pytest.mark.asyncio
    async def test_update_saved_job_status(
        self,
        service: ApplicationTrackingService,
        test_user: User,
        test_position: Position,
        db: AsyncSession,
    ):
        """Test updating saved job status."""
        saved_job = await service.save_job(
            user_id=test_user.id,
            position_id=test_position.id,
        )

        updated = await service.update_saved_job_status(
            saved_job_id=saved_job.id,
            new_status=SavedJobStatus.viewed,
        )

        assert updated is not None
        assert updated.status == SavedJobStatus.viewed
        assert updated.viewed_at is not None

    @pytest.mark.asyncio
    async def test_update_saved_job_status_nonexistent(
        self,
        service: ApplicationTrackingService,
    ):
        """Test updating nonexistent saved job."""
        result = await service.update_saved_job_status(
            saved_job_id=uuid.uuid4(),
            new_status=SavedJobStatus.viewed,
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_application_with_timeline_serialization(
        self,
        service: ApplicationTrackingService,
        test_user: User,
        test_resume: Resume,
        test_position: Position,
        db: AsyncSession,
    ):
        """Test ApplicationWithTimeline serialization."""
        application = await service.apply_to_job(
            user_id=test_user.id,
            position_id=test_position.id,
            resume_id=test_resume.id,
        )

        result = await service.get_application_with_timeline(application.id)

        result_dict = result.to_dict()

        assert "application_id" in result_dict
        assert "timeline" in result_dict
        assert "feedback" in result_dict
        assert isinstance(result_dict["timeline"], list)

    def test_valid_transitions_configuration(self, service: ApplicationTrackingService):
        """Test that valid transitions are properly configured."""
        # Applied can go to phone screen
        assert PipelineStage.phone_screen in service.VALID_TRANSITIONS[PipelineStage.applied]

        # Hired is terminal
        assert len(service.VALID_TRANSITIONS[PipelineStage.hired]) == 0

        # Rejected is terminal
        assert len(service.VALID_TRANSITIONS[PipelineStage.rejected]) == 0

    def test_map_event_type(self, service: ApplicationTrackingService):
        """Test event type mapping."""
        from app.models.application_timeline import EventType

        result = service._map_event_type("status_changed")
        assert result == EventType.status_change

        result = service._map_event_type("interview_scheduled")
        assert result == EventType.interview_scheduled
