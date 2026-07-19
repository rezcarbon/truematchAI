"""Resume versioning endpoints."""
from __future__ import annotations

import io
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy import and_, desc, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import utcnow
from app.core.exceptions import NotFoundError, AuthorizationError, ValidationError
from app.deps import CurrentUser, DBSession
from app.models.resume import Resume
from app.models.resume_version import ChangeType, ResumeVersion
from app.models.user import User
from app.schemas.resume_versioning import (
    CreateResumeVersionRequest,
    UpdateResumeVersionRequest,
    TailorResumeRequest,
    OptimizeForATSRequest,
    ResumeVersionResponse,
    ResumeVersionDetailResponse,
    ResumeVersionListResponse,
    CompareVersionsRequest,
    CompareVersionsResponse,
    DownloadResumeRequest,
    BulkVersionActionRequest,
    TailorResumeResponse,
    ResumeVersionStatus,
    ResumeVersionType,
    VersionHistoryItem,
    VersionDifference,
)
from app.services.resume_versioning import ResumeVersioningService

router = APIRouter(prefix="/candidates/resume-versions", tags=["resume-versioning"])
logger = logging.getLogger("truematch.resume_versioning")


# ─────────────────────────────────────────────────────────────────────────
# Create & Manage Resume Versions
# ─────────────────────────────────────────────────────────────────────────


@router.post(
    "",
    response_model=ResumeVersionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new resume version",
    description="Create a new version from an existing resume",
)
async def create_resume_version(
    payload: CreateResumeVersionRequest,
    user: CurrentUser,
    db: DBSession,
) -> ResumeVersionResponse:
    """Create a new resume version for versioning and comparison."""
    try:
        # Validate base resume exists and belongs to user
        stmt = select(Resume).where(
            and_(Resume.id == payload.base_resume_id, Resume.user_id == user.id)
        )
        base_resume = (await db.execute(stmt)).scalar_one_or_none()

        if not base_resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Base resume not found",
            )

        # Get current version of base resume
        stmt = (
            select(ResumeVersion)
            .where(
                and_(
                    ResumeVersion.resume_id == payload.base_resume_id,
                    ResumeVersion.is_current == True,
                )
            )
            .limit(1)
        )
        current_version = (await db.execute(stmt)).scalar_one_or_none()

        if not current_version:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Base resume has no current version",
            )

        # Create new version from current version
        service = ResumeVersioningService(db)
        new_version = await service.create_version(
            resume_id=payload.base_resume_id,
            user_id=user.id,
            parsed_data=current_version.parsed_data or {},
            raw_narrative=current_version.raw_narrative or "",
            change_type=ChangeType.edit,
            change_summary=f"Created version: {payload.version_name}",
            file_id=current_version.file_id,
            file_name=payload.version_name,
            file_size_bytes=current_version.file_size_bytes,
            file_type=current_version.file_type,
        )

        # Update version metadata
        new_version.description = payload.description

        # If set as default, mark others as not default
        if payload.is_default:
            stmt = select(ResumeVersion).where(
                and_(
                    ResumeVersion.resume_id == payload.base_resume_id,
                    ResumeVersion.id != new_version.id,
                )
            )
            other_versions = (await db.execute(stmt)).scalars().all()
            for v in other_versions:
                v.is_current = False

        await db.flush()
        await db.refresh(new_version)

        logger.info(
            f"Created resume version",
            extra={
                "version_id": str(new_version.id),
                "resume_id": str(payload.base_resume_id),
                "user_id": str(user.id),
                "version_name": payload.version_name,
            },
        )

        return _version_to_response(new_version)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating resume version: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create resume version",
        )


@router.get(
    "",
    response_model=ResumeVersionListResponse,
    summary="List resume versions",
    description="List all resume versions for the user with pagination",
)
async def list_resume_versions(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    resume_id: Optional[uuid.UUID] = Query(None, description="Filter by resume ID"),
    status_filter: Optional[str] = Query(None, description="Filter by version status"),
    user: CurrentUser = None,
    db: DBSession = None,
) -> ResumeVersionListResponse:
    """List all resume versions owned by the current user."""
    try:
        # Build query
        stmt = select(ResumeVersion).where(ResumeVersion.user_id == user.id)

        # Apply filters
        if resume_id:
            stmt = stmt.where(ResumeVersion.resume_id == resume_id)

        # Count total
        count_stmt = select(func.count(ResumeVersion.id)).select_from(ResumeVersion).where(
            ResumeVersion.user_id == user.id
        )
        if resume_id:
            count_stmt = count_stmt.where(ResumeVersion.resume_id == resume_id)

        total = (await db.execute(count_stmt)).scalar() or 0

        # Apply pagination and ordering
        offset = (page - 1) * page_size
        stmt = stmt.order_by(desc(ResumeVersion.created_at)).offset(offset).limit(page_size)

        versions = (await db.execute(stmt)).scalars().all()

        pages = (total + page_size - 1) // page_size

        return ResumeVersionListResponse(
            items=[_version_to_response(v) for v in versions],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    except Exception as e:
        logger.error(f"Error listing resume versions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list resume versions",
        )


@router.get(
    "/{version_id}",
    response_model=ResumeVersionDetailResponse,
    summary="Get resume version details",
    description="Retrieve full details of a specific resume version",
)
async def get_resume_version(
    version_id: uuid.UUID,
    user: CurrentUser,
    db: DBSession,
) -> ResumeVersionDetailResponse:
    """Get detailed information about a specific resume version."""
    try:
        stmt = select(ResumeVersion).where(ResumeVersion.id == version_id)
        version = (await db.execute(stmt)).scalar_one_or_none()

        if not version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume version not found",
            )

        # Verify ownership
        if version.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this version",
            )

        return ResumeVersionDetailResponse(
            version_id=version.id,
            base_resume_id=version.resume_id,
            version_name=version.file_name or f"Version {version.version_number}",
            version_type=ResumeVersionType.GENERAL,
            status=ResumeVersionStatus.ACTIVE if version.is_current else ResumeVersionStatus.ARCHIVED,
            description=None,
            is_default=version.is_current,
            created_at=version.created_at,
            updated_at=version.updated_at,
            version_number=version.version_number,
            content=version.raw_narrative or "",
            file_url=None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting resume version: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve resume version",
        )


@router.put(
    "/{version_id}",
    response_model=ResumeVersionResponse,
    summary="Update resume version",
    description="Update metadata for a resume version",
)
async def update_resume_version(
    version_id: uuid.UUID,
    payload: UpdateResumeVersionRequest,
    user: CurrentUser,
    db: DBSession,
) -> ResumeVersionResponse:
    """Update a resume version's metadata."""
    try:
        stmt = select(ResumeVersion).where(ResumeVersion.id == version_id)
        version = (await db.execute(stmt)).scalar_one_or_none()

        if not version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume version not found",
            )

        # Verify ownership
        if version.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to modify this version",
            )

        # Update fields
        if payload.version_name is not None:
            version.file_name = payload.version_name
        if payload.description is not None:
            # Store description in change_summary for now
            version.change_summary = payload.description
        if payload.status is not None:
            if payload.status == ResumeVersionStatus.ARCHIVED:
                version.archived_at = utcnow()
        if payload.is_default is not None:
            if payload.is_default:
                # Mark others as not current
                stmt = select(ResumeVersion).where(
                    and_(
                        ResumeVersion.resume_id == version.resume_id,
                        ResumeVersion.id != version.id,
                    )
                )
                other_versions = (await db.execute(stmt)).scalars().all()
                for v in other_versions:
                    v.is_current = False
                version.is_current = True
            else:
                version.is_current = False

        await db.flush()
        await db.refresh(version)

        logger.info(
            f"Updated resume version",
            extra={"version_id": str(version.id), "user_id": str(user.id)},
        )

        return _version_to_response(version)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating resume version: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update resume version",
        )


@router.delete(
    "/{version_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete resume version",
    description="Delete a resume version (archive or soft delete)",
)
async def delete_resume_version(
    version_id: uuid.UUID,
    user: CurrentUser,
    db: DBSession,
) -> None:
    """Delete a resume version."""
    try:
        stmt = select(ResumeVersion).where(ResumeVersion.id == version_id)
        version = (await db.execute(stmt)).scalar_one_or_none()

        if not version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume version not found",
            )

        # Verify ownership
        if version.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this version",
            )

        # Soft delete - archive the version
        version.archived_at = utcnow()
        version.is_current = False

        await db.flush()

        logger.info(
            f"Deleted resume version",
            extra={"version_id": str(version.id), "user_id": str(user.id)},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting resume version: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete resume version",
        )


# ─────────────────────────────────────────────────────────────────────────
# Tailor Resumes
# ─────────────────────────────────────────────────────────────────────────


@router.post(
    "/{version_id}/tailor",
    response_model=TailorResumeResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Tailor resume for a job",
    description="Tailor a resume for a specific job description",
)
async def tailor_resume_for_job(
    version_id: uuid.UUID,
    payload: TailorResumeRequest,
    user: CurrentUser,
    db: DBSession,
) -> TailorResumeResponse:
    """Tailor a resume for a specific job posting."""
    try:
        stmt = select(ResumeVersion).where(ResumeVersion.id == version_id)
        version = (await db.execute(stmt)).scalar_one_or_none()

        if not version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume version not found",
            )

        # Verify ownership
        if version.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this version",
            )

        # Extract keywords from job description
        keywords = _extract_keywords(payload.job_description)

        # Generate tailored content (simplified AI logic)
        tailored_content = version.raw_narrative or ""
        changes_made = _generate_tailoring_changes(version, keywords, payload.target_role)
        alignment_score = _calculate_alignment_score(version.parsed_data or {}, keywords)

        # Optionally save as new version
        tailored_version_id = None
        if payload.save_as_version:
            service = ResumeVersioningService(db)
            new_version = await service.create_version(
                resume_id=version.resume_id,
                user_id=user.id,
                parsed_data=version.parsed_data or {},
                raw_narrative=tailored_content,
                change_type=ChangeType.ai_enhancement,
                change_summary=f"Tailored for {payload.target_role} at {payload.company_name or 'target company'}",
                file_id=version.file_id,
                file_name=f"Tailored - {payload.target_role}",
                file_size_bytes=len(tailored_content.encode()),
                file_type=version.file_type,
            )
            tailored_version_id = new_version.id

        logger.info(
            f"Tailored resume for job",
            extra={
                "version_id": str(version.id),
                "user_id": str(user.id),
                "target_role": payload.target_role,
                "alignment_score": alignment_score,
            },
        )

        return TailorResumeResponse(
            tailored_version_id=tailored_version_id,
            preview_content=tailored_content[:500] + "..." if len(tailored_content) > 500 else tailored_content,
            changes_made=changes_made,
            alignment_score=alignment_score,
            estimated_improvement=f"Potential {alignment_score - 50}% improvement in match score"
            if alignment_score > 50
            else "Review recommended sections for better alignment",
            save_version_prompt=True,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error tailoring resume: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to tailor resume",
        )


# ─────────────────────────────────────────────────────────────────────────
# Optimize for ATS
# ─────────────────────────────────────────────────────────────────────────


@router.post(
    "/{version_id}/optimize-ats",
    response_model=ResumeVersionResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Optimize resume for ATS",
    description="Optimize a resume for ATS parsing and applicant tracking systems",
)
async def optimize_resume_for_ats(
    version_id: uuid.UUID,
    payload: OptimizeForATSRequest,
    user: CurrentUser,
    db: DBSession,
) -> ResumeVersionResponse:
    """Optimize a resume for ATS parsing."""
    try:
        stmt = select(ResumeVersion).where(ResumeVersion.id == version_id)
        version = (await db.execute(stmt)).scalar_one_or_none()

        if not version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume version not found",
            )

        # Verify ownership
        if version.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this version",
            )

        # Apply ATS optimizations
        optimized_content = _apply_ats_optimizations(
            version.raw_narrative or "",
            payload.target_ats_systems or ["generic"],
        )

        # Optionally save as new version
        if payload.save_as_version:
            service = ResumeVersioningService(db)
            new_version = await service.create_version(
                resume_id=version.resume_id,
                user_id=user.id,
                parsed_data=version.parsed_data or {},
                raw_narrative=optimized_content,
                change_type=ChangeType.ai_enhancement,
                change_summary="ATS optimization applied",
                file_id=version.file_id,
                file_name="ATS Optimized",
                file_size_bytes=len(optimized_content.encode()),
                file_type=version.file_type,
            )
            version = new_version

        await db.flush()
        await db.refresh(version)

        logger.info(
            f"Optimized resume for ATS",
            extra={
                "version_id": str(version.id),
                "user_id": str(user.id),
                "ats_systems": payload.target_ats_systems,
            },
        )

        return _version_to_response(version)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error optimizing resume for ATS: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to optimize resume",
        )


# ─────────────────────────────────────────────────────────────────────────
# Compare & Download
# ─────────────────────────────────────────────────────────────────────────


@router.post(
    "/compare",
    response_model=CompareVersionsResponse,
    summary="Compare two resume versions",
    description="Compare two resume versions and show differences",
)
async def compare_resume_versions(
    payload: CompareVersionsRequest,
    user: CurrentUser,
    db: DBSession,
) -> CompareVersionsResponse:
    """Compare two resume versions and highlight differences."""
    try:
        # Get both versions
        stmt1 = select(ResumeVersion).where(ResumeVersion.id == payload.version_id_1)
        version1 = (await db.execute(stmt1)).scalar_one_or_none()

        stmt2 = select(ResumeVersion).where(ResumeVersion.id == payload.version_id_2)
        version2 = (await db.execute(stmt2)).scalar_one_or_none()

        if not version1 or not version2:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or both versions not found",
            )

        # Verify ownership
        if version1.user_id != user.id or version2.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access these versions",
            )

        # Ensure they're from the same resume
        if version1.resume_id != version2.resume_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Versions must be from the same resume",
            )

        # Compute differences
        service = ResumeVersioningService(db)
        diff = await service.compute_diff(payload.version_id_1, payload.version_id_2)

        # Calculate similarity score
        similarity_score = _calculate_similarity_score(
            version1.raw_narrative or "",
            version2.raw_narrative or "",
        )

        # Build differences list
        differences = _build_differences_list(diff, version1, version2)

        logger.info(
            f"Compared resume versions",
            extra={
                "version1": str(payload.version_id_1),
                "version2": str(payload.version_id_2),
                "user_id": str(user.id),
                "similarity_score": similarity_score,
            },
        )

        return CompareVersionsResponse(
            version_1=_version_to_response(version1),
            version_2=_version_to_response(version2),
            differences=differences,
            similarity_score=similarity_score,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing resume versions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compare versions",
        )


@router.post(
    "/{version_id}/download",
    summary="Download resume version",
    description="Download resume in specified format (PDF, DOCX, TXT)",
)
async def download_resume_version(
    version_id: uuid.UUID,
    payload: DownloadResumeRequest,
    user: CurrentUser,
    db: DBSession,
):
    """Download a resume version in the specified format."""
    try:
        stmt = select(ResumeVersion).where(ResumeVersion.id == version_id)
        version = (await db.execute(stmt)).scalar_one_or_none()

        if not version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume version not found",
            )

        # Verify ownership
        if version.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to download this version",
            )

        # Get content
        content = version.raw_narrative or ""

        # Convert based on format
        if payload.format.lower() == "txt":
            file_content = content.encode()
            media_type = "text/plain"
            filename = f"resume_v{version.version_number}.txt"
        elif payload.format.lower() == "pdf":
            # Simplified PDF generation - in production use a proper PDF library
            file_content = _generate_pdf_content(content)
            media_type = "application/pdf"
            filename = f"resume_v{version.version_number}.pdf"
        elif payload.format.lower() == "docx":
            # Simplified DOCX generation - in production use python-docx
            file_content = _generate_docx_content(content)
            media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            filename = f"resume_v{version.version_number}.docx"
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported format. Use pdf, docx, or txt",
            )

        logger.info(
            f"Downloaded resume version",
            extra={
                "version_id": str(version.id),
                "user_id": str(user.id),
                "format": payload.format,
            },
        )

        return StreamingResponse(
            io.BytesIO(file_content),
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading resume: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download resume",
        )


# ─────────────────────────────────────────────────────────────────────────
# Bulk Operations
# ─────────────────────────────────────────────────────────────────────────


@router.post(
    "/bulk/actions",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Bulk actions on resume versions",
    description="Perform bulk operations (archive, delete, set default) on multiple versions",
)
async def bulk_version_actions(
    payload: BulkVersionActionRequest,
    user: CurrentUser,
    db: DBSession,
) -> None:
    """Perform bulk actions on multiple resume versions."""
    try:
        if not payload.version_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No version IDs provided",
            )

        # Verify ownership of all versions
        stmt = select(ResumeVersion).where(
            and_(
                ResumeVersion.id.in_(payload.version_ids),
                ResumeVersion.user_id == user.id,
            )
        )
        versions = (await db.execute(stmt)).scalars().all()

        if len(versions) != len(payload.version_ids):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access one or more versions",
            )

        # Apply action
        if payload.action == "archive":
            for v in versions:
                v.archived_at = utcnow()
                v.is_current = False
        elif payload.action == "delete":
            for v in versions:
                v.archived_at = utcnow()
                v.is_current = False
        elif payload.action == "set_default":
            if len(versions) > 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Can only set one version as default at a time",
                )
            # Mark as current
            version = versions[0]
            version.is_current = True
            # Mark others from same resume as not current
            stmt = select(ResumeVersion).where(
                and_(
                    ResumeVersion.resume_id == version.resume_id,
                    ResumeVersion.id != version.id,
                )
            )
            others = (await db.execute(stmt)).scalars().all()
            for v in others:
                v.is_current = False
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid action. Use archive, delete, or set_default",
            )

        await db.flush()

        logger.info(
            f"Bulk action performed",
            extra={
                "action": payload.action,
                "version_count": len(versions),
                "user_id": str(user.id),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error performing bulk actions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform bulk actions",
        )


# ─────────────────────────────────────────────────────────────────────────
# Version History & Insights
# ─────────────────────────────────────────────────────────────────────────


@router.get(
    "/{version_id}/history",
    summary="Get version history",
    description="Get change history and modifications for a resume version",
)
async def get_version_history(
    version_id: uuid.UUID,
    user: CurrentUser,
    db: DBSession,
):
    """Get change history for a resume version."""
    try:
        stmt = select(ResumeVersion).where(ResumeVersion.id == version_id)
        version = (await db.execute(stmt)).scalar_one_or_none()

        if not version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume version not found",
            )

        # Verify ownership
        if version.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this version",
            )

        # Get all versions for this resume
        service = ResumeVersioningService(db)
        history = await service.get_version_history(version.resume_id)

        logger.info(
            f"Retrieved version history",
            extra={
                "version_id": str(version.id),
                "user_id": str(user.id),
                "version_count": history.get("total_versions", 0),
            },
        )

        return history

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving version history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve version history",
        )


@router.get(
    "/{version_id}/match-score",
    summary="Get job match score",
    description="Get resume's match score against a job description",
)
async def get_resume_match_score(
    version_id: uuid.UUID,
    job_id: Optional[str] = Query(None, description="Job ID to match against"),
    job_description: Optional[str] = Query(None, description="Raw job description to match"),
    user: CurrentUser = None,
    db: DBSession = None,
):
    """Get resume's match score against a job."""
    try:
        stmt = select(ResumeVersion).where(ResumeVersion.id == version_id)
        version = (await db.execute(stmt)).scalar_one_or_none()

        if not version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume version not found",
            )

        # Verify ownership
        if version.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this version",
            )

        if not job_description:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="job_description is required",
            )

        # Calculate match score
        score = _calculate_alignment_score(
            version.parsed_data or {},
            _extract_keywords(job_description),
        )

        # Extract key matching and missing skills
        matching_skills = _extract_matching_skills(version.parsed_data or {}, job_description)
        missing_skills = _extract_missing_skills(version.parsed_data or {}, job_description)

        logger.info(
            f"Calculated match score",
            extra={
                "version_id": str(version.id),
                "user_id": str(user.id),
                "match_score": score,
            },
        )

        return {
            "version_id": str(version.id),
            "match_score": score,
            "matching_skills": matching_skills,
            "missing_skills": missing_skills,
            "score_breakdown": {
                "skills_match": int(score * 0.4),
                "experience_match": int(score * 0.3),
                "education_match": int(score * 0.2),
                "other_match": int(score * 0.1),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating match score: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate match score",
        )


@router.get(
    "/{version_id}/recommendations",
    summary="Get resume improvement recommendations",
    description="Get AI-powered recommendations to improve the resume",
)
async def get_resume_recommendations(
    version_id: uuid.UUID,
    target_role: Optional[str] = Query(None),
    user: CurrentUser = None,
    db: DBSession = None,
):
    """Get recommendations to improve a resume."""
    try:
        stmt = select(ResumeVersion).where(ResumeVersion.id == version_id)
        version = (await db.execute(stmt)).scalar_one_or_none()

        if not version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume version not found",
            )

        # Verify ownership
        if version.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this version",
            )

        # Generate recommendations
        recommendations = _generate_recommendations(version, target_role)

        logger.info(
            f"Generated resume recommendations",
            extra={
                "version_id": str(version.id),
                "user_id": str(user.id),
                "target_role": target_role,
                "recommendation_count": len(recommendations),
            },
        )

        return {
            "version_id": str(version.id),
            "recommendations": recommendations,
            "priority_areas": _identify_priority_areas(version, target_role),
            "estimated_impact": "High" if len(recommendations) > 3 else "Medium" if len(recommendations) > 0 else "Low",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating recommendations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate recommendations",
        )


# ─────────────────────────────────────────────────────────────────────────
# Helper Functions
# ─────────────────────────────────────────────────────────────────────────


def _version_to_response(version: ResumeVersion) -> ResumeVersionResponse:
    """Convert ResumeVersion model to response schema."""
    return ResumeVersionResponse(
        version_id=version.id,
        base_resume_id=version.resume_id,
        version_name=version.file_name or f"Version {version.version_number}",
        version_type=ResumeVersionType.GENERAL,
        status=ResumeVersionStatus.ACTIVE if version.is_current else ResumeVersionStatus.ARCHIVED,
        description=version.change_summary,
        is_default=version.is_current,
        created_at=version.created_at,
        updated_at=version.updated_at,
        version_number=version.version_number,
    )


def _extract_keywords(text: str) -> list[str]:
    """Extract keywords from text (simplified)."""
    import re
    # Simple keyword extraction - remove common words
    common_words = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "up", "about", "into", "through", "during"
    }

    words = re.findall(r'\b\w+\b', text.lower())
    keywords = [w for w in words if len(w) > 3 and w not in common_words]
    return list(set(keywords))[:20]  # Return unique keywords, limit to 20


def _generate_tailoring_changes(
    version: ResumeVersion,
    keywords: list[str],
    target_role: str,
) -> list[str]:
    """Generate list of suggested tailoring changes."""
    changes = []

    # Check if target role is mentioned
    if target_role.lower() not in (version.raw_narrative or "").lower():
        changes.append(f"Add '{target_role}' to highlight your focus on this role")

    # Check for skill keywords
    for keyword in keywords[:5]:
        if keyword not in (version.raw_narrative or "").lower():
            changes.append(f"Emphasize '{keyword}' skill/experience")

    # Generic suggestions
    changes.extend([
        "Highlight achievements with quantifiable results",
        "Use industry-specific terminology from the job posting",
        "Reorder experience to show most relevant roles first",
    ])

    return changes[:5]  # Return top 5 changes


def _calculate_alignment_score(parsed_data: dict, keywords: list[str]) -> int:
    """Calculate how well resume aligns with keywords (0-100)."""
    if not keywords:
        return 50

    score = 0
    content_str = json.dumps(parsed_data).lower()

    for keyword in keywords:
        if keyword.lower() in content_str:
            score += 5

    return min(100, 50 + (score // len(keywords)) if keywords else 50)


def _apply_ats_optimizations(content: str, systems: list[str]) -> str:
    """Apply ATS optimization to content."""
    optimized = content

    # Remove special characters that ATS might not parse
    optimized = optimized.replace("•", "-")
    optimized = optimized.replace("→", "->")
    optimized = optimized.replace("–", "-")

    # Ensure consistent spacing
    optimized = '\n'.join(line.strip() for line in optimized.split('\n'))

    # Remove unnecessary formatting for ATS
    optimized = optimized.replace("**", "").replace("__", "")

    return optimized


def _calculate_similarity_score(text1: str, text2: str) -> int:
    """Calculate similarity between two texts (0-100)."""
    import difflib

    if not text1 or not text2:
        return 0

    matcher = difflib.SequenceMatcher(None, text1, text2)
    ratio = matcher.ratio()
    return int(ratio * 100)


def _build_differences_list(
    diff,
    version1: ResumeVersion,
    version2: ResumeVersion,
) -> list[VersionDifference]:
    """Build list of differences between versions."""
    differences = []

    # Parse the diff metrics
    metrics = diff.metrics if hasattr(diff, 'metrics') else {}

    if metrics.get('sections_added'):
        differences.append(VersionDifference(
            section="structure",
            field="sections_added",
            value_in_v1=None,
            value_in_v2=str(metrics.get('sections_added')),
            change_type="added",
        ))

    if metrics.get('sections_modified'):
        differences.append(VersionDifference(
            section="content",
            field="modified_sections",
            value_in_v1=None,
            value_in_v2=str(metrics.get('sections_modified')),
            change_type="modified",
        ))

    if metrics.get('sections_removed'):
        differences.append(VersionDifference(
            section="structure",
            field="sections_removed",
            value_in_v1=str(metrics.get('sections_removed')),
            value_in_v2=None,
            change_type="removed",
        ))

    return differences


def _generate_pdf_content(content: str) -> bytes:
    """Generate PDF content (simplified)."""
    # In production, use reportlab or similar
    pdf_header = b"%PDF-1.4\n"
    pdf_body = content.encode('utf-8')[:1000]  # Limit size for demo
    return pdf_header + pdf_body


def _generate_docx_content(content: str) -> bytes:
    """Generate DOCX content (simplified)."""
    # In production, use python-docx
    docx_placeholder = b"PK\x03\x04" + content.encode('utf-8')[:1000]
    return docx_placeholder


def _extract_matching_skills(parsed_data: dict, job_description: str) -> list[str]:
    """Extract skills that match job description."""
    resume_skills = parsed_data.get("skills", [])
    job_keywords = _extract_keywords(job_description)

    if isinstance(resume_skills, list):
        matching = []
        for skill in resume_skills:
            if isinstance(skill, dict):
                skill_name = skill.get("skill_name", "").lower()
            else:
                skill_name = str(skill).lower()

            for keyword in job_keywords:
                if keyword in skill_name or skill_name in keyword:
                    matching.append(skill_name)
                    break
        return list(set(matching))[:10]

    return []


def _extract_missing_skills(parsed_data: dict, job_description: str) -> list[str]:
    """Extract skills from job description that are missing from resume."""
    resume_skills_str = json.dumps(parsed_data).lower()
    job_keywords = _extract_keywords(job_description)

    missing = []
    for keyword in job_keywords:
        if keyword not in resume_skills_str:
            missing.append(keyword)

    return missing[:10]


def _generate_recommendations(
    version: ResumeVersion,
    target_role: Optional[str],
) -> list[dict]:
    """Generate improvement recommendations."""
    recommendations = []

    # Check completeness
    completeness = version.completeness_percentage or 0
    if completeness < 70:
        recommendations.append({
            "priority": "high",
            "area": "completeness",
            "suggestion": "Fill in missing sections to improve resume completeness",
            "impact": "High",
        })

    # Check quality
    quality = version.quality_score or 0
    if quality < 70:
        recommendations.append({
            "priority": "high",
            "area": "quality",
            "suggestion": "Add more details to work experience and achievements",
            "impact": "High",
        })

    # Generic recommendations
    recommendations.extend([
        {
            "priority": "medium",
            "area": "formatting",
            "suggestion": "Use consistent formatting and clear section headers",
            "impact": "Medium",
        },
        {
            "priority": "medium",
            "area": "keywords",
            "suggestion": "Include industry keywords relevant to your target role",
            "impact": "High",
        },
    ])

    return recommendations[:5]


def _identify_priority_areas(
    version: ResumeVersion,
    target_role: Optional[str],
) -> list[str]:
    """Identify priority areas for improvement."""
    areas = []

    if (version.completeness_percentage or 0) < 70:
        areas.append("Resume Completeness")

    if (version.quality_score or 0) < 70:
        areas.append("Content Quality")

    if target_role and target_role.lower() not in (version.raw_narrative or "").lower():
        areas.append("Role-Specific Content")

    return areas
