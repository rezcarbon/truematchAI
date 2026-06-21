"""Data Subject Access Request (DSAR) endpoints for GDPR Article 15/17 compliance.

Endpoints for managing data access and deletion requests:
- POST /access-request: Initiate GDPR Article 15 (Right of Access)
- POST /deletion-request: Initiate GDPR Article 17 (Right to be Forgotten)
- GET /requests: List user's DSAR history (paginated, most recent first)
"""
from __future__ import annotations

import logging
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select

from app.deps import CurrentUser, DBSession
from app.models.dsar import DSARRequest, DSARStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/dsar", tags=["dsar"])


class DSARResponse:
    """Response schema for DSAR requests."""

    def __init__(
        self,
        dsar_id: uuid.UUID,
        user_id: uuid.UUID,
        request_type: str,
        status: DSARStatus,
        created_at: Any,
        message: str,
    ):
        self.dsar_id = dsar_id
        self.user_id = user_id
        self.request_type = request_type
        self.status = status
        self.created_at = created_at
        self.message = message

    def dict(self) -> dict:
        """Convert response to dict."""
        return {
            "dsar_id": str(self.dsar_id),
            "user_id": str(self.user_id),
            "request_type": self.request_type,
            "status": self.status.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "message": self.message,
        }


class DSARRequestDetail:
    """Detailed DSAR request schema for list responses."""

    def __init__(
        self,
        id: uuid.UUID,
        user_id: uuid.UUID,
        request_type: str,
        status: DSARStatus,
        created_at: Any,
        completed_at: Any = None,
        data_export_url: str | None = None,
    ):
        self.id = id
        self.user_id = user_id
        self.request_type = request_type
        self.status = status
        self.created_at = created_at
        self.completed_at = completed_at
        self.data_export_url = data_export_url

    def dict(self) -> dict:
        """Convert to dict."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "request_type": self.request_type,
            "status": self.status.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat()
            if self.completed_at
            else None,
            "data_export_url": self.data_export_url,
        }


@router.post("/access-request", status_code=status.HTTP_202_ACCEPTED)
async def create_access_request(
    user: CurrentUser,
    db: DBSession,
) -> dict:
    """
    Request a copy of personal data (GDPR Article 15 - Right of Access).

    The request is queued for processing. The user will be notified when
    the data export is ready for download.

    Returns:
        202 Accepted with dsar_id and processing status
    """
    try:
        dsar = DSARRequest(
            user_id=user.id,
            request_type="access",
            status=DSARStatus.received,
        )
        db.add(dsar)
        await db.flush()
        await db.commit()

        logger.info(
            "DSAR access request created",
            extra={
                "dsar_id": str(dsar.id),
                "user_id": str(user.id),
                "request_type": "access",
            },
        )

        from app.workers.tasks import export_dsar_data

        export_dsar_data.delay(str(dsar.id))

        response = DSARResponse(
            dsar_id=dsar.id,
            user_id=user.id,
            request_type="access",
            status=DSARStatus.received,
            created_at=dsar.created_at,
            message="Data access request received. You will be notified when your data export is ready.",
        )
        return response.dict()

    except Exception as e:
        logger.error(
            "Failed to create DSAR access request",
            extra={"user_id": str(user.id), "error": str(e)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process data access request",
        )


@router.post("/deletion-request", status_code=status.HTTP_202_ACCEPTED)
async def create_deletion_request(
    user: CurrentUser,
    db: DBSession,
) -> dict:
    """
    Request permanent deletion of personal data (GDPR Article 17 - Right to be Forgotten).

    WARNING: This action is irreversible. The user account and all associated data
    will be permanently deleted after a 30-day grace period (configurable).

    Returns:
        202 Accepted with dsar_id and processing status
    """
    try:
        dsar = DSARRequest(
            user_id=user.id,
            request_type="deletion",
            status=DSARStatus.received,
        )
        db.add(dsar)
        await db.flush()
        await db.commit()

        logger.warning(
            "DSAR deletion request created",
            extra={
                "dsar_id": str(dsar.id),
                "user_id": str(user.id),
                "request_type": "deletion",
            },
        )

        from app.workers.tasks import delete_user_data

        delete_user_data.delay(str(user.id), str(dsar.id))

        response = DSARResponse(
            dsar_id=dsar.id,
            user_id=user.id,
            request_type="deletion",
            status=DSARStatus.received,
            created_at=dsar.created_at,
            message="Deletion request received. Your account will be permanently deleted after the grace period.",
        )
        return response.dict()

    except Exception as e:
        logger.error(
            "Failed to create DSAR deletion request",
            extra={"user_id": str(user.id), "error": str(e)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process deletion request",
        )


@router.get("/requests")
async def list_dsar_requests(
    user: CurrentUser,
    db: DBSession,
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(
        20, ge=1, le=100, description="Items per page (max 100)"
    ),
) -> dict:
    """
    List all DSAR requests for the current user (paginated, most recent first).

    Returns paginated list of the user's data access and deletion requests
    with their current status and timestamps.

    Query Parameters:
        page: Page number (default: 1)
        page_size: Items per page (default: 20, max: 100)

    Returns:
        Paginated list of DSAR requests with metadata
    """
    try:
        stmt = select(DSARRequest).where(DSARRequest.user_id == user.id)
        count_stmt = select(func.count()).select_from(DSARRequest).where(
            DSARRequest.user_id == user.id
        )

        total = await db.scalar(count_stmt) or 0

        stmt = (
            stmt.order_by(DSARRequest.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        requests = list((await db.scalars(stmt)).all())

        items = [
            DSARRequestDetail(
                id=req.id,
                user_id=req.user_id,
                request_type=req.request_type,
                status=req.status,
                created_at=req.created_at,
                completed_at=req.completed_at,
                data_export_url=req.data_export_url,
            ).dict()
            for req in requests
        ]

        logger.info(
            "DSAR requests listed",
            extra={
                "user_id": str(user.id),
                "page": page,
                "page_size": page_size,
                "total": total,
            },
        )

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": (total + page_size - 1) // page_size,
        }

    except Exception as e:
        logger.error(
            "Failed to list DSAR requests",
            extra={"user_id": str(user.id), "error": str(e)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve DSAR requests",
        )


@router.get("/requests/{dsar_id}")
async def get_dsar_request(
    dsar_id: uuid.UUID,
    user: CurrentUser,
    db: DBSession,
) -> dict:
    """
    Retrieve a specific DSAR request by ID (access control enforced).

    Users can only access their own DSAR requests.

    Path Parameters:
        dsar_id: The ID of the DSAR request

    Returns:
        Detailed DSAR request information

    Raises:
        404: Request not found or access denied
    """
    try:
        dsar = await db.get(DSARRequest, dsar_id)

        if dsar is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="DSAR request not found",
            )

        if dsar.user_id != user.id:
            logger.warning(
                "Unauthorized DSAR access attempt",
                extra={
                    "requesting_user_id": str(user.id),
                    "target_dsar_id": str(dsar_id),
                    "target_user_id": str(dsar.user_id),
                },
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this request",
            )

        detail = DSARRequestDetail(
            id=dsar.id,
            user_id=dsar.user_id,
            request_type=dsar.request_type,
            status=dsar.status,
            created_at=dsar.created_at,
            completed_at=dsar.completed_at,
            data_export_url=dsar.data_export_url,
        )

        logger.info(
            "DSAR request retrieved",
            extra={
                "user_id": str(user.id),
                "dsar_id": str(dsar_id),
            },
        )

        return detail.dict()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to retrieve DSAR request",
            extra={
                "user_id": str(user.id),
                "dsar_id": str(dsar_id),
                "error": str(e),
            },
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve DSAR request",
        )
