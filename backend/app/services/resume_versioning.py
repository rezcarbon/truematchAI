"""Resume Versioning Service - Resume version management with diff computation."""
from __future__ import annotations

import difflib
import json
import logging
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.resume import Resume
from app.models.resume_version import ChangeType, ResumeVersion
from app.models.user import User

logger = logging.getLogger(__name__)


class ResumeDiff:
    """Represents differences between two resume versions."""

    def __init__(self):
        self.added_sections: dict = {}
        self.removed_sections: dict = {}
        self.modified_sections: dict = {}
        self.unchanged_sections: dict = {}
        self.metrics: dict = {}

    def to_dict(self) -> dict:
        """Convert diff to dictionary representation."""
        return {
            "added_sections": self.added_sections,
            "removed_sections": self.removed_sections,
            "modified_sections": self.modified_sections,
            "unchanged_sections": self.unchanged_sections,
            "metrics": self.metrics,
        }


class ResumeVersioningService:
    """Service for managing resume versions and computing diffs."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_version(
        self,
        resume_id: uuid.UUID,
        user_id: uuid.UUID,
        parsed_data: dict,
        raw_narrative: str,
        change_type: ChangeType,
        change_summary: str = None,
        file_id: str = None,
        file_name: str = None,
        file_size_bytes: int = None,
        file_type: str = None,
    ) -> ResumeVersion:
        """
        Create a new resume version.

        Args:
            resume_id: The resume ID
            user_id: The user ID
            parsed_data: Structured resume data
            raw_narrative: Raw resume text
            change_type: Type of change made
            change_summary: Human-readable summary of changes
            file_id: File storage ID
            file_name: Original file name
            file_size_bytes: File size
            file_type: File MIME type

        Returns:
            The created ResumeVersion
        """
        # Get the next version number
        version_number = await self._get_next_version_number(resume_id)

        # Mark previous version as not current
        await self._mark_previous_as_archived(resume_id)

        # Create new version
        version = ResumeVersion(
            resume_id=resume_id,
            user_id=user_id,
            version_number=version_number,
            is_current=True,
            parsed_data=parsed_data,
            raw_narrative=raw_narrative,
            change_type=change_type,
            change_summary=change_summary,
            file_id=file_id,
            file_name=file_name,
            file_size_bytes=file_size_bytes,
            file_type=file_type,
            quality_score=self._calculate_quality_score(parsed_data),
            completeness_percentage=self._calculate_completeness(parsed_data),
            sections_detected=self._detect_sections(parsed_data),
            created_by_id=user_id,
        )

        self.db.add(version)
        await self.db.flush()

        logger.info(
            f"Created resume version {version.id} for resume {resume_id}",
            extra={"version_number": version_number, "user_id": user_id},
        )

        return version

    async def get_version(self, version_id: uuid.UUID) -> Optional[ResumeVersion]:
        """Get a specific resume version."""
        stmt = select(ResumeVersion).where(ResumeVersion.id == version_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_current_version(self, resume_id: uuid.UUID) -> Optional[ResumeVersion]:
        """Get the current version of a resume."""
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
        return result.scalars().first()

    async def get_all_versions(
        self, resume_id: uuid.UUID, include_archived: bool = False
    ) -> list[ResumeVersion]:
        """
        Get all versions of a resume.

        Args:
            resume_id: The resume ID
            include_archived: Whether to include archived versions

        Returns:
            List of resume versions ordered by version_number descending
        """
        if include_archived:
            stmt = (
                select(ResumeVersion)
                .where(ResumeVersion.resume_id == resume_id)
                .order_by(desc(ResumeVersion.version_number))
            )
        else:
            stmt = (
                select(ResumeVersion)
                .where(
                    and_(
                        ResumeVersion.resume_id == resume_id,
                        ResumeVersion.archived_at == None,
                    )
                )
                .order_by(desc(ResumeVersion.version_number))
            )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def compute_diff(
        self, version1_id: uuid.UUID, version2_id: uuid.UUID
    ) -> ResumeDiff:
        """
        Compute the differences between two resume versions.

        Args:
            version1_id: First version ID (older)
            version2_id: Second version ID (newer)

        Returns:
            ResumeDiff object containing all differences
        """
        v1 = await self.get_version(version1_id)
        v2 = await self.get_version(version2_id)

        if not v1 or not v2:
            raise ValueError("One or both versions not found")

        if v1.resume_id != v2.resume_id:
            raise ValueError("Versions belong to different resumes")

        diff = ResumeDiff()

        # Compare parsed data
        data1 = v1.parsed_data or {}
        data2 = v2.parsed_data or {}

        # Get all possible sections
        all_sections = set(data1.keys()) | set(data2.keys())

        for section in all_sections:
            content1 = data1.get(section)
            content2 = data2.get(section)

            if content1 is None:
                # Section was added
                diff.added_sections[section] = content2
            elif content2 is None:
                # Section was removed
                diff.removed_sections[section] = content1
            elif content1 != content2:
                # Section was modified
                diff.modified_sections[section] = {
                    "before": content1,
                    "after": content2,
                    "changes": self._compute_section_diff(content1, content2),
                }
            else:
                # Section unchanged
                diff.unchanged_sections[section] = content1

        # Calculate metrics
        diff.metrics = {
            "sections_added": len(diff.added_sections),
            "sections_removed": len(diff.removed_sections),
            "sections_modified": len(diff.modified_sections),
            "sections_unchanged": len(diff.unchanged_sections),
            "total_sections": len(all_sections),
            "change_percentage": self._calculate_change_percentage(diff),
            "quality_score_change": (
                (v2.quality_score or 0) - (v1.quality_score or 0)
            ),
            "completeness_change": (
                (v2.completeness_percentage or 0)
                - (v1.completeness_percentage or 0)
            ),
        }

        return diff

    async def rollback_to_version(
        self, resume_id: uuid.UUID, version_id: uuid.UUID, user_id: uuid.UUID
    ) -> ResumeVersion:
        """
        Rollback a resume to a previous version.

        Args:
            resume_id: The resume ID
            version_id: The version to rollback to
            user_id: User performing the rollback

        Returns:
            The new version created as a result of rollback
        """
        source_version = await self.get_version(version_id)
        if not source_version or source_version.resume_id != resume_id:
            raise ValueError("Version not found or does not match resume")

        # Create a new version based on the source version
        rollback_version = await self.create_version(
            resume_id=resume_id,
            user_id=user_id,
            parsed_data=source_version.parsed_data,
            raw_narrative=source_version.raw_narrative,
            change_type=ChangeType.edit,
            change_summary=f"Rolled back to version {source_version.version_number}",
            file_id=source_version.file_id,
            file_name=source_version.file_name,
            file_size_bytes=source_version.file_size_bytes,
            file_type=source_version.file_type,
        )

        logger.info(
            f"Resume {resume_id} rolled back to version {version_id}",
            extra={"rolled_back_version": version_id, "user_id": user_id},
        )

        return rollback_version

    async def get_version_history(
        self, resume_id: uuid.UUID
    ) -> dict:
        """
        Get the complete version history for a resume.

        Args:
            resume_id: The resume ID

        Returns:
            Dictionary containing complete version history and timeline
        """
        versions = await self.get_all_versions(resume_id, include_archived=True)

        if not versions:
            return {
                "resume_id": str(resume_id),
                "total_versions": 0,
                "versions": [],
            }

        history = {
            "resume_id": str(resume_id),
            "total_versions": len(versions),
            "versions": [],
            "timeline": [],
        }

        for version in versions:
            version_info = {
                "id": str(version.id),
                "version_number": version.version_number,
                "is_current": version.is_current,
                "change_type": version.change_type.value if version.change_type else None,
                "change_summary": version.change_summary,
                "quality_score": version.quality_score,
                "completeness_percentage": version.completeness_percentage,
                "created_at": version.created_at.isoformat()
                if version.created_at
                else None,
                "archived_at": version.archived_at.isoformat()
                if version.archived_at
                else None,
                "file_name": version.file_name,
                "file_size_bytes": version.file_size_bytes,
            }
            history["versions"].append(version_info)
            history["timeline"].append({
                "version": version.version_number,
                "timestamp": version.created_at.isoformat()
                if version.created_at
                else None,
                "change_type": version.change_type.value if version.change_type else None,
            })

        return history

    async def compare_consecutive_versions(
        self, resume_id: uuid.UUID
    ) -> list[dict]:
        """
        Compare all consecutive versions in a resume's history.

        Args:
            resume_id: The resume ID

        Returns:
            List of diffs between consecutive versions
        """
        versions = await self.get_all_versions(resume_id, include_archived=True)

        if len(versions) < 2:
            return []

        # Versions are ordered newest first, so reverse for chronological order
        versions = list(reversed(versions))

        comparisons = []
        for i in range(len(versions) - 1):
            v1 = versions[i]
            v2 = versions[i + 1]

            diff = await self.compute_diff(v1.id, v2.id)
            comparisons.append({
                "from_version": v1.version_number,
                "to_version": v2.version_number,
                "timestamp": v2.created_at.isoformat() if v2.created_at else None,
                "change_type": v2.change_type.value if v2.change_type else None,
                "diff": diff.to_dict(),
            })

        return comparisons

    async def get_quality_trends(self, resume_id: uuid.UUID) -> dict:
        """
        Analyze quality score trends over time.

        Args:
            resume_id: The resume ID

        Returns:
            Dictionary containing quality score trends and analysis
        """
        versions = await self.get_all_versions(resume_id, include_archived=True)

        if not versions:
            return {
                "resume_id": str(resume_id),
                "trends": [],
                "summary": "No version history available",
            }

        # Reverse for chronological order
        versions = list(reversed(versions))

        trends = {
            "resume_id": str(resume_id),
            "total_versions": len(versions),
            "quality_scores": [],
            "completeness_scores": [],
            "overall_trend": None,
        }

        quality_scores = []
        completeness_scores = []

        for version in versions:
            if version.quality_score is not None:
                trends["quality_scores"].append({
                    "version": version.version_number,
                    "score": version.quality_score,
                    "timestamp": version.created_at.isoformat()
                    if version.created_at
                    else None,
                })
                quality_scores.append(version.quality_score)

            if version.completeness_percentage is not None:
                trends["completeness_scores"].append({
                    "version": version.version_number,
                    "score": version.completeness_percentage,
                    "timestamp": version.created_at.isoformat()
                    if version.created_at
                    else None,
                })
                completeness_scores.append(version.completeness_percentage)

        # Analyze trend
        if quality_scores:
            trend_direction = self._analyze_trend(quality_scores)
            trends["overall_trend"] = {
                "direction": trend_direction,
                "initial_score": quality_scores[0],
                "final_score": quality_scores[-1],
                "improvement": quality_scores[-1] - quality_scores[0],
            }

        return trends

    # Private helper methods

    async def _get_next_version_number(self, resume_id: uuid.UUID) -> int:
        """Get the next version number for a resume."""
        stmt = (
            select(ResumeVersion.version_number)
            .where(ResumeVersion.resume_id == resume_id)
            .order_by(desc(ResumeVersion.version_number))
            .limit(1)
        )
        result = await self.db.execute(stmt)
        last_version = result.scalars().first()
        return (last_version or 0) + 1

    async def _mark_previous_as_archived(self, resume_id: uuid.UUID) -> None:
        """Mark the previous current version as archived."""
        current = await self.get_current_version(resume_id)
        if current:
            current.is_current = False
            current.archived_at = datetime.utcnow()

    def _calculate_quality_score(self, parsed_data: dict) -> float:
        """Calculate quality score for resume data."""
        if not parsed_data:
            return 0.0

        score = 0.0
        max_score = 0.0

        # Check for required sections
        required_sections = {
            "personal_info": 15,
            "work_experience": 25,
            "education": 15,
            "skills": 20,
        }

        for section, points in required_sections.items():
            max_score += points
            if section in parsed_data and parsed_data[section]:
                score += points

        # Bonus points for additional sections
        additional_sections = {"projects", "certifications", "publications"}
        for section in additional_sections:
            if section in parsed_data and parsed_data[section]:
                score += 5
                max_score += 5

        return (score / max_score * 100) if max_score > 0 else 0.0

    def _calculate_completeness(self, parsed_data: dict) -> int:
        """Calculate completeness percentage for resume data."""
        if not parsed_data:
            return 0

        total_fields = 0
        filled_fields = 0

        # Define expected fields per section
        section_fields = {
            "personal_info": ["name", "email", "phone"],
            "work_experience": ["position", "company", "start_date"],
            "education": ["degree", "institution"],
            "skills": ["skill_name", "proficiency"],
        }

        for section, fields in section_fields.items():
            if section in parsed_data:
                section_data = parsed_data[section]
                if isinstance(section_data, list):
                    for item in section_data:
                        for field in fields:
                            total_fields += 1
                            if item.get(field):
                                filled_fields += 1
                elif isinstance(section_data, dict):
                    for field in fields:
                        total_fields += 1
                        if section_data.get(field):
                            filled_fields += 1

        return (
            int(filled_fields / total_fields * 100)
            if total_fields > 0
            else 0
        )

    def _detect_sections(self, parsed_data: dict) -> dict:
        """Detect which sections are present in the resume."""
        sections = {}
        for section in parsed_data.keys():
            sections[section] = {
                "present": True,
                "item_count": (
                    len(parsed_data[section])
                    if isinstance(parsed_data[section], list)
                    else 1
                ),
            }
        return sections

    def _compute_section_diff(self, content1, content2) -> list:
        """Compute detailed diff for a section."""
        if isinstance(content1, str) and isinstance(content2, str):
            # String diff
            differ = difflib.Differ()
            return list(
                differ.compare(content1.splitlines(), content2.splitlines())
            )
        elif isinstance(content1, list) and isinstance(content2, list):
            # List diff
            return {
                "added": [item for item in content2 if item not in content1],
                "removed": [item for item in content1 if item not in content2],
            }
        elif isinstance(content1, dict) and isinstance(content2, dict):
            # Dict diff
            changes = {
                "added_keys": list(set(content2.keys()) - set(content1.keys())),
                "removed_keys": list(set(content1.keys()) - set(content2.keys())),
                "modified_keys": {},
            }
            for key in set(content1.keys()) & set(content2.keys()):
                if content1[key] != content2[key]:
                    changes["modified_keys"][key] = {
                        "from": content1[key],
                        "to": content2[key],
                    }
            return changes
        else:
            # Different types
            return {"from_type": type(content1).__name__, "to_type": type(content2).__name__}

    def _calculate_change_percentage(self, diff: ResumeDiff) -> float:
        """Calculate the percentage of content that changed."""
        total_sections = (
            len(diff.added_sections)
            + len(diff.removed_sections)
            + len(diff.modified_sections)
            + len(diff.unchanged_sections)
        )

        if total_sections == 0:
            return 0.0

        changed_sections = (
            len(diff.added_sections)
            + len(diff.removed_sections)
            + len(diff.modified_sections)
        )

        return (changed_sections / total_sections * 100)

    def _analyze_trend(self, scores: list) -> str:
        """Analyze trend direction from a list of scores."""
        if len(scores) < 2:
            return "insufficient_data"

        improvements = sum(1 for i in range(len(scores) - 1) if scores[i] < scores[i + 1])
        decreases = sum(1 for i in range(len(scores) - 1) if scores[i] > scores[i + 1])

        if improvements > decreases:
            return "improving"
        elif decreases > improvements:
            return "declining"
        else:
            return "stable"
