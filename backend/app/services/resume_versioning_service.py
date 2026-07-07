"""Resume Versioning Service - Version management with comprehensive diff tracking."""
from __future__ import annotations

import difflib
import json
import logging
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import utcnow
from app.models.resume import Resume
from app.models.resume_version import ChangeType, ResumeVersion

logger = logging.getLogger(__name__)


class ContentDiff:
    """Represents unified diff format changes between resume versions."""

    def __init__(self):
        self.added_lines: list[str] = []
        self.removed_lines: list[str] = []
        self.modified_lines: list[dict] = []
        self.unified_diff: str = ""
        self.metrics: dict = {
            "total_additions": 0,
            "total_deletions": 0,
            "total_modifications": 0,
            "change_percentage": 0.0,
        }

    def to_dict(self) -> dict:
        """Convert ContentDiff to dictionary representation."""
        return {
            "added_lines": self.added_lines,
            "removed_lines": self.removed_lines,
            "modified_lines": self.modified_lines,
            "unified_diff": self.unified_diff,
            "metrics": self.metrics,
        }


class ResumVersioningService:
    """Service for managing resume versions with full versioning and diff capabilities."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_version(
        self,
        user_id: uuid.UUID,
        resume_id: uuid.UUID,
        file_id: str,
        extracted_text: str,
        parsed_data: Optional[dict] = None,
        change_type: ChangeType = ChangeType.upload,
        change_summary: Optional[str] = None,
        file_name: Optional[str] = None,
        file_size_bytes: Optional[int] = None,
        file_type: Optional[str] = None,
    ) -> ResumeVersion:
        """
        Create a new resume version.

        Args:
            user_id: User who owns the resume
            resume_id: Resume ID
            file_id: File storage ID
            extracted_text: Raw extracted text from resume
            parsed_data: Structured parsed resume data
            change_type: Type of change (upload, edit, etc.)
            change_summary: Human-readable summary of changes
            file_name: Original file name
            file_size_bytes: File size in bytes
            file_type: File MIME type

        Returns:
            Created ResumeVersion object
        """
        try:
            # Get next version number
            version_number = await self._get_next_version_number(resume_id)

            # Mark previous version as archived
            await self._mark_previous_as_current(resume_id)

            # Calculate quality metrics
            quality_score = self._calculate_quality_score(
                parsed_data or {}, extracted_text
            )
            completeness = self._calculate_completeness(parsed_data or {})
            sections_detected = self._detect_sections(parsed_data or {})

            # Create new version
            version = ResumeVersion(
                resume_id=resume_id,
                user_id=user_id,
                version_number=version_number,
                is_current=True,
                file_id=file_id,
                file_name=file_name,
                file_size_bytes=file_size_bytes,
                file_type=file_type,
                parsed_data=parsed_data or {},
                raw_narrative=extracted_text,
                change_type=change_type,
                change_summary=change_summary,
                quality_score=quality_score,
                completeness_percentage=completeness,
                sections_detected=sections_detected,
                created_by_id=user_id,
            )

            self.db.add(version)
            await self.db.flush()
            await self.db.refresh(version)

            logger.info(
                f"Resume version created",
                extra={
                    "version_id": str(version.id),
                    "resume_id": str(resume_id),
                    "user_id": str(user_id),
                    "version_number": version_number,
                    "change_type": change_type.value,
                },
            )

            return version

        except Exception as e:
            logger.error(
                f"Failed to create resume version: {str(e)}",
                extra={"resume_id": str(resume_id), "user_id": str(user_id)},
            )
            raise

    async def get_version_history(
        self, resume_id: uuid.UUID, limit: Optional[int] = None
    ) -> list[ResumeVersion]:
        """
        Get version history for a resume.

        Args:
            resume_id: Resume ID
            limit: Maximum number of versions to return

        Returns:
            List of ResumeVersion objects ordered by version number descending
        """
        try:
            stmt = (
                select(ResumeVersion)
                .where(ResumeVersion.resume_id == resume_id)
                .order_by(desc(ResumeVersion.version_number))
            )

            if limit:
                stmt = stmt.limit(limit)

            result = await self.db.execute(stmt)
            versions = result.scalars().all()

            logger.info(
                f"Retrieved resume version history",
                extra={"resume_id": str(resume_id), "version_count": len(versions)},
            )

            return list(versions)

        except Exception as e:
            logger.error(
                f"Failed to get version history: {str(e)}",
                extra={"resume_id": str(resume_id)},
            )
            raise

    async def revert_to_version(
        self, resume_id: uuid.UUID, version_id: uuid.UUID
    ) -> Resume:
        """
        Revert resume to a specific previous version.

        Args:
            resume_id: Resume ID
            version_id: Version to revert to

        Returns:
            Updated Resume object
        """
        try:
            # Get target version
            target_version = await self._get_version(version_id)
            if not target_version or target_version.resume_id != resume_id:
                raise ValueError(
                    f"Version {version_id} not found or does not match resume {resume_id}"
                )

            # Create a new version based on the target
            new_version = await self.create_version(
                user_id=target_version.user_id,
                resume_id=resume_id,
                file_id=target_version.file_id or "",
                extracted_text=target_version.raw_narrative or "",
                parsed_data=target_version.parsed_data,
                change_type=ChangeType.edit,
                change_summary=f"Reverted to version {target_version.version_number}",
                file_name=target_version.file_name,
                file_size_bytes=target_version.file_size_bytes,
                file_type=target_version.file_type,
            )

            # Fetch and update the actual Resume object
            stmt = select(Resume).where(Resume.id == resume_id)
            result = await self.db.execute(stmt)
            resume = result.scalar_one_or_none()

            if resume:
                resume.current_version_id = new_version.id
                await self.db.flush()
                await self.db.refresh(resume)

            logger.info(
                f"Resume reverted to version",
                extra={
                    "resume_id": str(resume_id),
                    "target_version": target_version.version_number,
                    "new_version": new_version.version_number,
                },
            )

            return resume

        except Exception as e:
            logger.error(
                f"Failed to revert resume: {str(e)}",
                extra={"resume_id": str(resume_id), "version_id": str(version_id)},
            )
            raise

    async def compute_diff(
        self, version1_id: uuid.UUID, version2_id: uuid.UUID
    ) -> ContentDiff:
        """
        Compute unified diff between two resume versions.

        Args:
            version1_id: First version ID (older)
            version2_id: Second version ID (newer)

        Returns:
            ContentDiff with unified diff format changes
        """
        try:
            v1 = await self._get_version(version1_id)
            v2 = await self._get_version(version2_id)

            if not v1 or not v2:
                raise ValueError("One or both versions not found")

            if v1.resume_id != v2.resume_id:
                raise ValueError("Versions belong to different resumes")

            diff = ContentDiff()

            # Get text content for diff
            text1 = (v1.raw_narrative or "").splitlines(keepends=True)
            text2 = (v2.raw_narrative or "").splitlines(keepends=True)

            # Generate unified diff
            unified_diff = list(
                difflib.unified_diff(
                    text1,
                    text2,
                    fromfile=f"Version {v1.version_number}",
                    tofile=f"Version {v2.version_number}",
                    lineterm="",
                )
            )
            diff.unified_diff = "\n".join(unified_diff)

            # Extract added/removed/modified lines
            for line in unified_diff:
                if line.startswith("+") and not line.startswith("+++"):
                    diff.added_lines.append(line[1:])
                elif line.startswith("-") and not line.startswith("---"):
                    diff.removed_lines.append(line[1:])

            # Calculate metrics
            diff.metrics["total_additions"] = len(diff.added_lines)
            diff.metrics["total_deletions"] = len(diff.removed_lines)
            diff.metrics["total_modifications"] = max(
                len(diff.added_lines), len(diff.removed_lines)
            )

            total_lines = len(text1) + len(text2)
            if total_lines > 0:
                diff.metrics["change_percentage"] = (
                    (len(diff.added_lines) + len(diff.removed_lines)) / total_lines * 100
                )

            logger.info(
                f"Computed diff between versions",
                extra={
                    "version1": version1_id,
                    "version2": version2_id,
                    "additions": diff.metrics["total_additions"],
                    "deletions": diff.metrics["total_deletions"],
                },
            )

            return diff

        except Exception as e:
            logger.error(
                f"Failed to compute diff: {str(e)}",
                extra={"version1_id": str(version1_id), "version2_id": str(version2_id)},
            )
            raise

    async def compare_assessments(
        self, resume_version_1: ResumeVersion, resume_version_2: ResumeVersion
    ) -> dict:
        """
        Compare assessment metrics between two resume versions.

        Args:
            resume_version_1: First resume version
            resume_version_2: Second resume version

        Returns:
            Dictionary with:
                - changes: List of metric changes
                - score_delta: Change in quality score
        """
        try:
            changes = []

            # Compare quality score
            score1 = resume_version_1.quality_score or 0
            score2 = resume_version_2.quality_score or 0
            score_delta = score2 - score1

            if score_delta != 0:
                changes.append({
                    "metric": "quality_score",
                    "from": score1,
                    "to": score2,
                    "change": score_delta,
                    "direction": "improved" if score_delta > 0 else "declined",
                })

            # Compare completeness
            comp1 = resume_version_1.completeness_percentage or 0
            comp2 = resume_version_2.completeness_percentage or 0
            comp_delta = comp2 - comp1

            if comp_delta != 0:
                changes.append({
                    "metric": "completeness_percentage",
                    "from": comp1,
                    "to": comp2,
                    "change": comp_delta,
                    "direction": "improved" if comp_delta > 0 else "declined",
                })

            # Compare detected sections
            sections1 = resume_version_1.sections_detected or {}
            sections2 = resume_version_2.sections_detected or {}

            if sections1 != sections2:
                added_sections = set(sections2.keys()) - set(sections1.keys())
                removed_sections = set(sections1.keys()) - set(sections2.keys())

                if added_sections:
                    changes.append({
                        "metric": "sections_added",
                        "value": list(added_sections),
                        "change": len(added_sections),
                    })

                if removed_sections:
                    changes.append({
                        "metric": "sections_removed",
                        "value": list(removed_sections),
                        "change": len(removed_sections),
                    })

            logger.info(
                f"Compared assessments between versions",
                extra={
                    "version1": str(resume_version_1.id),
                    "version2": str(resume_version_2.id),
                    "score_delta": score_delta,
                    "changes_count": len(changes),
                },
            )

            return {
                "changes": changes,
                "score_delta": int(score_delta),
                "completeness_delta": int(comp_delta),
                "summary": self._generate_assessment_summary(changes, score_delta),
            }

        except Exception as e:
            logger.error(
                f"Failed to compare assessments: {str(e)}",
                extra={
                    "version1": str(resume_version_1.id),
                    "version2": str(resume_version_2.id),
                },
            )
            raise

    # Private helper methods

    async def _get_next_version_number(self, resume_id: uuid.UUID) -> int:
        """Get next version number for a resume."""
        stmt = (
            select(ResumeVersion.version_number)
            .where(ResumeVersion.resume_id == resume_id)
            .order_by(desc(ResumeVersion.version_number))
            .limit(1)
        )
        result = await self.db.execute(stmt)
        last_version = result.scalar_one_or_none()
        return (last_version or 0) + 1

    async def _mark_previous_as_current(self, resume_id: uuid.UUID) -> None:
        """Mark previous current version as not current."""
        stmt = (
            select(ResumeVersion)
            .where(
                and_(
                    ResumeVersion.resume_id == resume_id,
                    ResumeVersion.is_current == True,
                )
            )
            .limit(1)
        )
        result = await self.db.execute(stmt)
        current = result.scalar_one_or_none()

        if current:
            current.is_current = False
            current.archived_at = utcnow()
            await self.db.flush()

    async def _get_version(self, version_id: uuid.UUID) -> Optional[ResumeVersion]:
        """Get a specific version by ID."""
        stmt = select(ResumeVersion).where(ResumeVersion.id == version_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    def _calculate_quality_score(self, parsed_data: dict, raw_text: str) -> float:
        """Calculate quality score for resume data."""
        score = 0.0

        # Check for key sections
        required_sections = {
            "personal_info": 20,
            "work_experience": 30,
            "education": 20,
            "skills": 15,
        }

        for section, weight in required_sections.items():
            if section in parsed_data and parsed_data[section]:
                score += weight

        # Bonus for additional sections
        optional_sections = {"projects", "certifications", "publications", "languages"}
        for section in optional_sections:
            if section in parsed_data and parsed_data[section]:
                score += 3.75

        # Text length consideration
        if len(raw_text) > 500:
            score += 5
        if len(raw_text) > 1000:
            score += 5

        return min(100.0, max(0.0, score))

    def _calculate_completeness(self, parsed_data: dict) -> int:
        """Calculate completeness percentage."""
        if not parsed_data:
            return 0

        total_fields = 0
        filled_fields = 0

        # Expected fields per section
        section_expectations = {
            "personal_info": ["name", "email"],
            "work_experience": ["position", "company"],
            "education": ["degree", "institution"],
            "skills": ["skill_name"],
        }

        for section, fields in section_expectations.items():
            if section in parsed_data:
                data = parsed_data[section]
                if isinstance(data, list):
                    for item in data:
                        for field in fields:
                            total_fields += 1
                            if item.get(field):
                                filled_fields += 1
                elif isinstance(data, dict):
                    for field in fields:
                        total_fields += 1
                        if data.get(field):
                            filled_fields += 1

        return (
            int(filled_fields / total_fields * 100) if total_fields > 0 else 0
        )

    def _detect_sections(self, parsed_data: dict) -> dict:
        """Detect which sections are present."""
        sections = {}
        for section, content in parsed_data.items():
            if content:
                sections[section] = {
                    "present": True,
                    "item_count": (
                        len(content)
                        if isinstance(content, (list, dict))
                        else 1
                    ),
                }
        return sections

    def _generate_assessment_summary(self, changes: list, score_delta: float) -> str:
        """Generate human-readable summary of assessment changes."""
        if score_delta > 10:
            summary = "Quality improved significantly"
        elif score_delta > 0:
            summary = "Quality improved"
        elif score_delta < -10:
            summary = "Quality declined significantly"
        elif score_delta < 0:
            summary = "Quality declined"
        else:
            summary = "Quality unchanged"

        if changes:
            summary += f" ({len(changes)} metric changes detected)"

        return summary
