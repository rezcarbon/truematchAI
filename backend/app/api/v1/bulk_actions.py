"""
Bulk operations API endpoints for candidates
Handles: stage updates, tag assignment, interview scheduling, rejections
"""

from typing import List
from uuid import UUID
from app.core.clock import utcnow
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db, get_current_recruiter
from app.models import Application

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/bulk-actions", tags=["bulk-actions"])


class BulkActionResponse:
    """Response for bulk actions"""
    def __init__(self, successful: int, failed: int, errors: List[str] = None):
        self.successful = successful
        self.failed = failed
        self.errors = errors or []

    def dict(self):
        return {
            "successful": self.successful,
            "failed": self.failed,
            "errors": self.errors
        }


@router.post("/stage")
async def bulk_update_stage(
    request: dict,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_recruiter),
):
    """
    Bulk update candidate stage

    Request body:
    {
        "candidate_ids": ["id1", "id2", ...],
        "new_stage": "technical"
    }
    """
    try:
        candidate_ids = request.get("candidate_ids", [])
        new_stage = request.get("new_stage")

        if not candidate_ids:
            raise HTTPException(status_code=400, detail="No candidates selected")

        if not new_stage:
            raise HTTPException(status_code=400, detail="New stage is required")

        # Validate stage
        valid_stages = [
            "applied", "phone_screen", "technical", "onsite", "offer", "hired", "rejected"
        ]
        if new_stage not in valid_stages:
            raise HTTPException(status_code=400, detail=f"Invalid stage: {new_stage}")

        # Convert string IDs to UUID
        try:
            app_ids = [UUID(id) for id in candidate_ids]
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid candidate ID format")

        # Update applications
        stmt = (
            update(Application)
            .where(Application.id.in_(app_ids))
            .values(
                stage=new_stage,
                stage_entered_at=utcnow()
            )
        )

        result = await db.execute(stmt)
        await db.commit()

        successful = result.rowcount
        failed = len(candidate_ids) - successful

        logger.info(
            f"Bulk stage update: {successful} successful, {failed} failed",
            extra={"user_id": str(current_user.id), "new_stage": new_stage}
        )

        # Create notifications for each updated candidate
        from app.services.notification_service import NotificationService
        try:
            for app_id in app_ids[:successful]:  # Only for successfully updated
                await NotificationService.create_notification(
                    db=db,
                    user_id=current_user.id,
                    notification_type="candidate_advanced",
                    title=f"Candidates advanced to {new_stage}",
                    message=f"Bulk update: {successful} candidates moved to {new_stage} stage",
                    action_url=f"/applications/{app_id}",
                    broadcast_websocket=True,
                )
                # Only create one notification per bulk action, not per candidate
                break
        except Exception as e:
            logger.error(f"Failed to create bulk update notifications: {str(e)}")
            # Don't fail the update if notifications fail

        return BulkActionResponse(successful=successful, failed=failed).dict()

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Bulk stage update error: {str(e)}")
        raise HTTPException(status_code=500, detail="Bulk update failed")


@router.post("/tags")
async def bulk_update_tags(
    request: dict,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_recruiter),
):
    """
    Bulk add/remove tags from candidates

    Request body:
    {
        "candidate_ids": ["id1", "id2", ...],
        "tags_to_add": ["tag1", "tag2"],
        "tags_to_remove": ["old_tag"]
    }
    """
    try:
        candidate_ids = request.get("candidate_ids", [])
        tags_to_add = request.get("tags_to_add", [])
        tags_to_remove = request.get("tags_to_remove", [])

        if not candidate_ids:
            raise HTTPException(status_code=400, detail="No candidates selected")

        if not tags_to_add and not tags_to_remove:
            raise HTTPException(status_code=400, detail="No tags to add or remove")

        # Convert string IDs to UUID
        try:
            app_ids = [UUID(id) for id in candidate_ids]
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid candidate ID format")

        successful = 0
        failed = 0

        # Process each application
        for app_id in app_ids:
            try:
                from sqlalchemy import select

                # Get application
                stmt = select(Application).where(Application.id == app_id)
                result = await db.execute(stmt)
                app = result.scalar_one_or_none()

                if not app:
                    failed += 1
                    continue

                # Update tags
                if app.tags is None:
                    app.tags = {}

                # Add tags
                for tag in tags_to_add:
                    app.tags[tag] = utcnow().isoformat()

                # Remove tags
                for tag in tags_to_remove:
                    if tag in app.tags:
                        del app.tags[tag]

                db.add(app)
                successful += 1

            except Exception as e:
                logger.error(f"Error updating tags for {app_id}: {str(e)}")
                failed += 1

        await db.commit()

        logger.info(
            f"Bulk tag update: {successful} successful, {failed} failed",
            extra={"user_id": str(current_user.id)}
        )

        return BulkActionResponse(successful=successful, failed=failed).dict()

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Bulk tag update error: {str(e)}")
        raise HTTPException(status_code=500, detail="Bulk tag update failed")


@router.post("/interviews")
async def bulk_schedule_interviews(
    request: dict,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_recruiter),
):
    """
    Bulk schedule interviews for candidates

    Request body:
    {
        "candidate_ids": ["id1", "id2", ...],
        "interview_data": {
            "meeting_platform": "zoom",
            "scheduled_at": "2026-06-15T14:00:00Z",
            "interviewer_ids": ["int1", "int2"]
        }
    }
    """
    try:
        candidate_ids = request.get("candidate_ids", [])
        interview_data = request.get("interview_data")

        if not candidate_ids:
            raise HTTPException(status_code=400, detail="No candidates selected")

        if not interview_data:
            raise HTTPException(status_code=400, detail="Interview data is required")

        # Validate interview data
        required_fields = ["meeting_platform", "scheduled_at", "interviewer_ids"]
        for field in required_fields:
            if field not in interview_data:
                raise HTTPException(status_code=400, detail=f"Missing {field}")

        # Convert string IDs to UUID
        try:
            app_ids = [UUID(id) for id in candidate_ids]
            interviewer_ids = [UUID(id) for id in interview_data.get("interviewer_ids", [])]
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid ID format")

        from app.models import Interview

        successful = 0
        failed = 0

        # Create interviews for each candidate
        for app_id in app_ids:
            try:
                # Verify application exists
                from sqlalchemy import select
                stmt = select(Application).where(Application.id == app_id)
                result = await db.execute(stmt)
                app = result.scalar_one_or_none()

                if not app:
                    failed += 1
                    continue

                # Create interview
                interview = Interview(
                    application_id=app_id,
                    position_id=app.position_id,
                    interviewer_ids=interviewer_ids,
                    meeting_platform=interview_data.get("meeting_platform"),
                    scheduled_at=interview_data.get("scheduled_at"),
                    status="scheduled"
                )

                db.add(interview)
                successful += 1

            except Exception as e:
                logger.error(f"Error scheduling interview for {app_id}: {str(e)}")
                failed += 1

        await db.commit()

        logger.info(
            f"Bulk interview scheduling: {successful} successful, {failed} failed",
            extra={"user_id": str(current_user.id)}
        )

        return BulkActionResponse(successful=successful, failed=failed).dict()

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Bulk interview scheduling error: {str(e)}")
        raise HTTPException(status_code=500, detail="Bulk interview scheduling failed")


@router.post("/reject")
async def bulk_reject_candidates(
    request: dict,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_recruiter),
):
    """
    Bulk reject candidates

    Request body:
    {
        "candidate_ids": ["id1", "id2", ...]
    }
    """
    try:
        candidate_ids = request.get("candidate_ids", [])

        if not candidate_ids:
            raise HTTPException(status_code=400, detail="No candidates selected")

        # Convert string IDs to UUID
        try:
            app_ids = [UUID(id) for id in candidate_ids]
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid candidate ID format")

        # Update applications to rejected
        stmt = (
            update(Application)
            .where(Application.id.in_(app_ids))
            .values(
                stage="rejected",
                stage_entered_at=utcnow()
            )
        )

        result = await db.execute(stmt)
        await db.commit()

        successful = result.rowcount
        failed = len(candidate_ids) - successful

        logger.info(
            f"Bulk rejection: {successful} successful, {failed} failed",
            extra={"user_id": str(current_user.id)}
        )

        return BulkActionResponse(successful=successful, failed=failed).dict()

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Bulk rejection error: {str(e)}")
        raise HTTPException(status_code=500, detail="Bulk rejection failed")
