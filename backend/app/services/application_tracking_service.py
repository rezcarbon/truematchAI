"""Application tracking service for managing job applications and timeline events.

Handles application lifecycle, status transitions, timeline recording, and feedback.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import utcnow
from app.models.application import Application, PipelineStage
from app.models.application_tracking import (
    ApplicationEvent,
    ApplicationEventType,
    ActorType,
    ApplicationFeedback,
    FeedbackRecommendation,
)
from app.models.application_timeline import ApplicationTimeline, EventType
from app.models.position import Position
from app.models.resume import Resume
from app.models.saved_job import SavedJob, SavedJobStatus
from app.models.user import User

logger = logging.getLogger(__name__)


class TimelineEventData:
    """Represents a timeline event."""

    def __init__(
        self,
        event_id: uuid.UUID,
        event_type: EventType,
        created_at: datetime,
        data: Optional[dict] = None,
        description: Optional[str] = None,
    ):
        self.event_id = event_id
        self.event_type = event_type
        self.created_at = created_at
        self.data = data or {}
        self.description = description

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "event_id": str(self.event_id),
            "event_type": self.event_type.value,
            "created_at": self.created_at.isoformat(),
            "description": self.description,
            "data": self.data,
        }


class ApplicationWithTimeline:
    """Application with full timeline and feedback."""

    def __init__(
        self,
        application: Application,
        timeline_events: list[TimelineEventData],
        feedback: Optional[list[ApplicationFeedback]] = None,
        offer: Optional[dict] = None,
    ):
        self.application = application
        self.timeline_events = timeline_events
        self.feedback = feedback or []
        self.offer = offer

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "application_id": str(self.application.id),
            "position_id": str(self.application.position_id),
            "resume_id": str(self.application.resume_id),
            "user_id": str(self.application.user_id),
            "stage": self.application.stage.value,
            "stage_entered_at": self.application.stage_entered_at.isoformat(),
            "source": self.application.source,
            "applied_at": self.application.applied_at.isoformat(),
            "created_at": self.application.created_at.isoformat(),
            "updated_at": self.application.updated_at.isoformat(),
            "timeline": [e.to_dict() for e in self.timeline_events],
            "feedback": [
                {
                    "id": str(f.id),
                    "stage": f.feedback_stage,
                    "rating": f.overall_rating,
                    "recommendation": f.recommendation.value if f.recommendation else None,
                    "provided_by": f.provided_by_name,
                    "created_at": f.created_at.isoformat(),
                }
                for f in self.feedback
            ],
            "offer": self.offer,
        }


class ApplicationTrackingService:
    """Service for tracking job applications and timeline events."""

    # Valid status transitions
    VALID_TRANSITIONS = {
        PipelineStage.applied: [
            PipelineStage.phone_screen,
            PipelineStage.rejected,
        ],
        PipelineStage.phone_screen: [
            PipelineStage.technical,
            PipelineStage.onsite,
            PipelineStage.rejected,
        ],
        PipelineStage.technical: [
            PipelineStage.onsite,
            PipelineStage.rejected,
        ],
        PipelineStage.onsite: [
            PipelineStage.offer,
            PipelineStage.rejected,
        ],
        PipelineStage.offer: [
            PipelineStage.hired,
            PipelineStage.rejected,
        ],
        PipelineStage.hired: [],  # Terminal state
        PipelineStage.rejected: [],  # Terminal state
    }

    def __init__(self, db: AsyncSession):
        """Initialize application tracking service.

        Args:
            db: AsyncSession for database operations
        """
        self.db = db
        logger.debug("ApplicationTrackingService initialized")

    def _map_event_type(self, app_event_type: str) -> EventType:
        """Map ApplicationEventType to EventType.

        Args:
            app_event_type: ApplicationEventType value string

        Returns:
            Corresponding EventType
        """
        mapping = {
            "status_changed": EventType.status_change,
            "interview_scheduled": EventType.interview_scheduled,
            "interview_completed": EventType.interview_completed,
            "offer_extended": EventType.offer_extended,
            "offer_accepted": EventType.offer_accepted,
            "offer_rejected": EventType.status_change,
            "rejected": EventType.application_rejected,
            "feedback_provided": EventType.feedback_shared,
        }
        return mapping.get(app_event_type, EventType.status_change)

    async def apply_to_job(
        self,
        user_id: uuid.UUID,
        position_id: uuid.UUID,
        resume_id: uuid.UUID,
        cover_note: Optional[str] = None,
        source: Optional[str] = None,
    ) -> Application:
        """
        Record a job application.

        Args:
            user_id: User ID
            position_id: Position ID
            resume_id: Resume ID to apply with
            cover_note: Optional cover letter/note
            source: Application source (linkedin, referral, indeed, etc.)

        Returns:
            Created Application record
        """
        try:
            # Verify position exists
            position_query = select(Position).where(Position.id == position_id)
            position_result = await self.db.execute(position_query)
            position = position_result.scalar_one_or_none()

            if not position:
                raise ValueError(f"Position {position_id} not found")

            # Verify resume exists and belongs to user
            resume_query = select(Resume).where(
                and_(
                    Resume.id == resume_id,
                    Resume.user_id == user_id,
                )
            )
            resume_result = await self.db.execute(resume_query)
            resume = resume_result.scalar_one_or_none()

            if not resume:
                raise ValueError(f"Resume {resume_id} not found for user {user_id}")

            # Check for existing application
            existing_query = select(Application).where(
                and_(
                    Application.user_id == user_id,
                    Application.position_id == position_id,
                )
            )
            existing_result = await self.db.execute(existing_query)
            existing = existing_result.scalar_one_or_none()

            if existing:
                logger.warning(
                    f"User {user_id} already applied to position {position_id}"
                )
                return existing

            # Create application
            application = Application(
                user_id=user_id,
                position_id=position_id,
                resume_id=resume_id,
                stage=PipelineStage.applied,
                cover_note=cover_note,
                source=source or "direct",
                applied_at=utcnow(),
            )

            self.db.add(application)
            await self.db.flush()

            # Record timeline event
            await self.record_timeline_event(
                application.id,
                EventType.status_change,
                {
                    "from_stage": None,
                    "to_stage": PipelineStage.applied.value,
                    "source": source or "direct",
                },
                description=f"Application submitted from {source or 'direct'}",
            )

            # Record application event
            event = ApplicationEvent(
                application_id=application.id,
                user_id=user_id,
                event_type=ApplicationEventType.status_changed,
                event_data={
                    "from_stage": None,
                    "to_stage": PipelineStage.applied.value,
                    "source": source or "direct",
                },
                actor_type=ActorType.user,
                triggered_by_id=user_id,
            )
            self.db.add(event)

            await self.db.commit()

            logger.info(
                f"User {user_id} applied to position {position_id}",
                extra={
                    "application_id": str(application.id),
                    "resume_id": str(resume_id),
                    "source": source,
                },
            )

            return application

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error applying to job: {e}", exc_info=True)
            raise

    async def update_application_status(
        self,
        application_id: uuid.UUID,
        new_stage: PipelineStage,
        event_data: Optional[dict] = None,
        triggered_by_id: Optional[uuid.UUID] = None,
        actor_type: ActorType = ActorType.system,
    ) -> Application:
        """
        Update application stage with validation.

        Args:
            application_id: Application ID
            new_stage: New pipeline stage
            event_data: Additional event data
            triggered_by_id: User ID who triggered the change
            actor_type: Type of actor making the change

        Returns:
            Updated Application record

        Raises:
            ValueError: If transition is invalid
        """
        try:
            # Get application
            app_query = select(Application).where(Application.id == application_id)
            app_result = await self.db.execute(app_query)
            application = app_result.scalar_one_or_none()

            if not application:
                raise ValueError(f"Application {application_id} not found")

            old_stage = application.stage

            # Validate transition
            if new_stage not in self.VALID_TRANSITIONS.get(old_stage, []):
                raise ValueError(
                    f"Invalid transition from {old_stage.value} to {new_stage.value}"
                )

            # Update application
            application.stage = new_stage
            application.stage_entered_at = utcnow()
            application.updated_at = utcnow()

            # Record event
            transition_data = event_data or {}
            transition_data.update({
                "from_stage": old_stage.value,
                "to_stage": new_stage.value,
            })

            await self.record_timeline_event(
                application_id,
                EventType.status_change,
                transition_data,
                description=f"Status changed to {new_stage.value}",
            )

            # Record application event
            event = ApplicationEvent(
                application_id=application_id,
                user_id=application.user_id,
                event_type=ApplicationEventType.status_changed,
                event_data=transition_data,
                actor_type=actor_type,
                triggered_by_id=triggered_by_id,
            )
            self.db.add(event)

            await self.db.commit()

            logger.info(
                f"Updated application {application_id} status",
                extra={
                    "from_stage": old_stage.value,
                    "to_stage": new_stage.value,
                    "triggered_by": str(triggered_by_id) if triggered_by_id else None,
                },
            )

            return application

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating application status: {e}", exc_info=True)
            raise

    async def record_timeline_event(
        self,
        application_id: uuid.UUID,
        event_type: EventType,
        event_data: Optional[dict] = None,
        description: Optional[str] = None,
    ) -> ApplicationEvent:
        """
        Record immutable timeline event for application.

        Args:
            application_id: Application ID
            event_type: Type of event
            event_data: Event metadata
            description: Human-readable description

        Returns:
            Created ApplicationEvent record
        """
        try:
            # Get application to verify it exists and get user_id
            app_query = select(Application).where(Application.id == application_id)
            app_result = await self.db.execute(app_query)
            application = app_result.scalar_one_or_none()

            if not application:
                raise ValueError(f"Application {application_id} not found")

            # Create immutable event record
            event = ApplicationEvent(
                application_id=application_id,
                user_id=application.user_id,
                event_type=event_type.value,
                event_data=event_data or {},
                description=description,
                actor_type=ActorType.system,
            )

            self.db.add(event)
            await self.db.commit()

            logger.debug(
                f"Recorded timeline event for application {application_id}",
                extra={
                    "event_type": event_type.value,
                    "description": description,
                },
            )

            return event

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error recording timeline event: {e}", exc_info=True)
            raise

    async def get_application_with_timeline(
        self,
        application_id: uuid.UUID,
    ) -> Optional[ApplicationWithTimeline]:
        """
        Get application with full timeline and feedback.

        Args:
            application_id: Application ID

        Returns:
            ApplicationWithTimeline or None if not found
        """
        try:
            # Get application
            app_query = select(Application).where(Application.id == application_id)
            app_result = await self.db.execute(app_query)
            application = app_result.scalar_one_or_none()

            if not application:
                logger.warning(f"Application {application_id} not found")
                return None

            # Get timeline events
            events_query = select(ApplicationEvent).where(
                ApplicationEvent.application_id == application_id
            ).order_by(ApplicationEvent.created_at)

            events_result = await self.db.execute(events_query)
            events = events_result.scalars().all()

            timeline_events = [
                TimelineEventData(
                    event_id=e.id,
                    event_type=self._map_event_type(e.event_type),
                    created_at=e.created_at,
                    data=e.event_data,
                    description=e.description,
                )
                for e in events
            ]

            # Get feedback
            feedback_query = select(ApplicationFeedback).where(
                ApplicationFeedback.application_id == application_id
            ).order_by(ApplicationFeedback.created_at)

            feedback_result = await self.db.execute(feedback_query)
            feedback = feedback_result.scalars().all()

            # Get offer if exists
            offer = None
            for event in events:
                if event.event_type == ApplicationEventType.offer_extended:
                    offer = event.event_data
                    break

            result = ApplicationWithTimeline(
                application=application,
                timeline_events=timeline_events,
                feedback=feedback,
                offer=offer,
            )

            logger.debug(
                f"Retrieved application {application_id} with timeline",
                extra={
                    "timeline_events": len(timeline_events),
                    "feedback_count": len(feedback),
                },
            )

            return result

        except Exception as e:
            logger.error(
                f"Error getting application with timeline: {e}",
                exc_info=True,
            )
            return None

    async def save_job(
        self,
        user_id: uuid.UUID,
        position_id: uuid.UUID,
        notes: Optional[str] = None,
        list_name: str = "Default",
    ) -> SavedJob:
        """
        Save a job for later.

        Args:
            user_id: User ID
            position_id: Position ID
            notes: Optional notes
            list_name: Name of save list

        Returns:
            SavedJob record
        """
        try:
            # Verify position exists
            position_query = select(Position).where(Position.id == position_id)
            position_result = await self.db.execute(position_query)
            position = position_result.scalar_one_or_none()

            if not position:
                raise ValueError(f"Position {position_id} not found")

            # Check for existing save
            existing_query = select(SavedJob).where(
                and_(
                    SavedJob.user_id == user_id,
                    SavedJob.position_id == position_id,
                )
            )
            existing_result = await self.db.execute(existing_query)
            existing = existing_result.scalar_one_or_none()

            if existing:
                logger.info(f"Job already saved by user {user_id}")
                return existing

            # Create saved job
            saved_job = SavedJob(
                user_id=user_id,
                position_id=position_id,
                list_name=list_name,
                notes=notes,
                job_title=position.title,
                company_name=None,  # Would need to fetch from company model
                status=SavedJobStatus.saved,
            )

            self.db.add(saved_job)
            await self.db.commit()

            logger.info(
                f"Job {position_id} saved by user {user_id}",
                extra={"list_name": list_name},
            )

            return saved_job

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error saving job: {e}", exc_info=True)
            raise

    async def get_saved_jobs(
        self,
        user_id: uuid.UUID,
        status: Optional[SavedJobStatus] = None,
        list_name: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[SavedJob], int]:
        """
        Get saved jobs for user with pagination.

        Args:
            user_id: User ID
            status: Filter by status (saved, viewed, applied, archived, rejected)
            list_name: Filter by save list name
            limit: Maximum results
            offset: Pagination offset

        Returns:
            Tuple of (list of SavedJob, total count)
        """
        try:
            # Build base query
            query = select(SavedJob).where(SavedJob.user_id == user_id)

            if status:
                query = query.where(SavedJob.status == status)

            if list_name:
                query = query.where(SavedJob.list_name == list_name)

            # Get count
            count_query = select(func.count()).select_from(SavedJob).where(
                SavedJob.user_id == user_id
            )
            if status:
                count_query = count_query.where(SavedJob.status == status)
            if list_name:
                count_query = count_query.where(SavedJob.list_name == list_name)

            count_result = await self.db.execute(count_query)
            total_count = count_result.scalar() or 0

            # Apply ordering and pagination
            query = query.order_by(desc(SavedJob.created_at)).limit(limit).offset(offset)

            result = await self.db.execute(query)
            saved_jobs = result.scalars().all()

            logger.debug(
                f"Retrieved {len(saved_jobs)} saved jobs for user {user_id}",
                extra={
                    "status": status.value if status else None,
                    "list_name": list_name,
                    "total_count": total_count,
                },
            )

            return saved_jobs, total_count

        except Exception as e:
            logger.error(f"Error getting saved jobs: {e}", exc_info=True)
            return [], 0

    async def update_saved_job_status(
        self,
        saved_job_id: uuid.UUID,
        new_status: SavedJobStatus,
    ) -> Optional[SavedJob]:
        """
        Update saved job status.

        Args:
            saved_job_id: SavedJob ID
            new_status: New status

        Returns:
            Updated SavedJob or None
        """
        try:
            query = select(SavedJob).where(SavedJob.id == saved_job_id)
            result = await self.db.execute(query)
            saved_job = result.scalar_one_or_none()

            if not saved_job:
                logger.warning(f"SavedJob {saved_job_id} not found")
                return None

            saved_job.status = new_status

            if new_status == SavedJobStatus.viewed:
                saved_job.viewed_at = utcnow()
            elif new_status == SavedJobStatus.applied:
                saved_job.applied_at = utcnow()
            elif new_status == SavedJobStatus.archived:
                saved_job.archived_at = utcnow()

            await self.db.commit()

            logger.info(
                f"Updated saved job {saved_job_id} status to {new_status.value}"
            )

            return saved_job

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating saved job status: {e}", exc_info=True)
            return None
