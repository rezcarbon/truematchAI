"""JD Optimization Service - Enhanced JD analysis with 10-dimension scoring."""
from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.jd_version import JDVersion
from app.models.position import Position
from app.models.user import User

logger = logging.getLogger(__name__)


class JDDimension:
    """Represents a scoring dimension for JD analysis."""

    def __init__(
        self,
        name: str,
        weight: float,
        description: str,
        min_score: float = 0.0,
        max_score: float = 100.0,
    ):
        self.name = name
        self.weight = weight
        self.description = description
        self.min_score = min_score
        self.max_score = max_score


class JDOptimizationService:
    """Service for optimizing and analyzing job descriptions."""

    # 10-dimension scoring framework
    DIMENSIONS = {
        "clarity": JDDimension(
            name="Clarity",
            weight=0.10,
            description="How clearly the JD communicates role expectations",
        ),
        "completeness": JDDimension(
            name="Completeness",
            weight=0.12,
            description="Coverage of all key role components",
        ),
        "specificity": JDDimension(
            name="Specificity",
            weight=0.12,
            description="Precision of requirements and qualifications",
        ),
        "fairness": JDDimension(
            name="Fairness",
            weight=0.10,
            description="Absence of bias and discriminatory language",
        ),
        "accessibility": JDDimension(
            name="Accessibility",
            weight=0.08,
            description="Accessibility requirements clarity",
        ),
        "market_competitiveness": JDDimension(
            name="Market Competitiveness",
            weight=0.12,
            description="Alignment with market standards and expectations",
        ),
        "skill_alignment": JDDimension(
            name="Skill Alignment",
            weight=0.10,
            description="Logical grouping and relevance of required skills",
        ),
        "growth_opportunity": JDDimension(
            name="Growth Opportunity",
            weight=0.08,
            description="Learning and development potential",
        ),
        "compliance": JDDimension(
            name="Compliance",
            weight=0.10,
            description="Adherence to legal and regulatory requirements",
        ),
        "engagement_appeal": JDDimension(
            name="Engagement Appeal",
            weight=0.08,
            description="How compelling the role is to candidates",
        ),
    }

    def __init__(self, db: AsyncSession):
        self.db = db

    async def analyze_jd(
        self, position_id: uuid.UUID, user_id: uuid.UUID
    ) -> dict:
        """
        Analyze a job description across all 10 dimensions.

        Args:
            position_id: The position to analyze
            user_id: User performing the analysis

        Returns:
            Dictionary containing scores for all dimensions and overall score
        """
        # Fetch the position and latest JD version
        position = await self._get_position(position_id)
        if not position:
            raise ValueError(f"Position {position_id} not found")

        jd_version = await self._get_latest_jd_version(position_id)
        if not jd_version:
            raise ValueError(f"No JD version found for position {position_id}")

        # Calculate scores for each dimension
        dimension_scores = {}
        for dim_key, dimension in self.DIMENSIONS.items():
            score = await self._score_dimension(
                dim_key, jd_version, position
            )
            dimension_scores[dim_key] = {
                "name": dimension.name,
                "score": score,
                "weight": dimension.weight,
                "max_score": dimension.max_score,
            }

        # Calculate weighted overall score
        overall_score = self._calculate_weighted_score(dimension_scores)

        # Identify improvement areas
        improvement_areas = self._identify_improvements(dimension_scores)

        return {
            "position_id": str(position_id),
            "jd_version_id": str(jd_version.id),
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "dimension_scores": dimension_scores,
            "overall_score": overall_score,
            "improvement_areas": improvement_areas,
            "recommendations": self._generate_recommendations(
                dimension_scores, jd_version
            ),
        }

    async def compare_jd_versions(
        self, position_id: uuid.UUID, version1_id: uuid.UUID, version2_id: uuid.UUID
    ) -> dict:
        """
        Compare two versions of a job description.

        Args:
            position_id: The position to analyze
            version1_id: First JD version ID
            version2_id: Second JD version ID

        Returns:
            Dictionary containing comparison metrics and changes
        """
        v1 = await self._get_jd_version(version1_id)
        v2 = await self._get_jd_version(version2_id)

        if not v1 or not v2:
            raise ValueError("One or both JD versions not found")

        if v1.position_id != position_id or v2.position_id != position_id:
            raise ValueError("Version positions do not match")

        return {
            "position_id": str(position_id),
            "version1": {
                "id": str(v1.id),
                "version": v1.version,
                "created_at": v1.created_at.isoformat() if v1.created_at else None,
            },
            "version2": {
                "id": str(v2.id),
                "version": v2.version,
                "created_at": v2.created_at.isoformat() if v2.created_at else None,
            },
            "requirement_changes": self._extract_requirement_changes(v1, v2),
            "requirement_additions": self._extract_additions(v1, v2),
            "requirement_removals": self._extract_removals(v1, v2),
            "scope_change": self._analyze_scope_change(v1, v2),
        }

    async def detect_requirement_drift(
        self, position_id: uuid.UUID
    ) -> dict:
        """
        Detect how requirements have changed over time (requirement drift).

        Args:
            position_id: The position to analyze

        Returns:
            Dictionary containing drift analysis and trend data
        """
        versions = await self._get_all_jd_versions(position_id)
        if len(versions) < 2:
            return {
                "position_id": str(position_id),
                "drift_detected": False,
                "message": "Insufficient versions for drift analysis",
            }

        # Analyze progression
        drift_analysis = {
            "position_id": str(position_id),
            "total_versions": len(versions),
            "drift_detected": False,
            "analysis": {},
        }

        # Check for scope/complexity creep
        complexity_trend = []
        seniority_trend = []
        skill_count_trend = []

        for version in versions:
            parsed = version.parsed_requirements or {}
            complexity_trend.append(
                {
                    "version": version.version,
                    "complexity_score": parsed.get("complexity_score", 0),
                    "created_at": version.created_at.isoformat()
                    if version.created_at
                    else None,
                }
            )
            seniority_trend.append(
                {
                    "version": version.version,
                    "seniority_level": parsed.get("seniority_level", "unknown"),
                    "created_at": version.created_at.isoformat()
                    if version.created_at
                    else None,
                }
            )
            skill_count_trend.append(
                {
                    "version": version.version,
                    "skill_count": len(parsed.get("required_skills", [])),
                    "created_at": version.created_at.isoformat()
                    if version.created_at
                    else None,
                }
            )

        drift_analysis["complexity_trend"] = complexity_trend
        drift_analysis["seniority_trend"] = seniority_trend
        drift_analysis["skill_count_trend"] = skill_count_trend

        # Detect drift (e.g., continuous increase in complexity)
        if len(complexity_trend) >= 2:
            complexity_scores = [
                t["complexity_score"] for t in complexity_trend
            ]
            if all(
                complexity_scores[i] <= complexity_scores[i + 1]
                for i in range(len(complexity_scores) - 1)
            ):
                drift_analysis["drift_detected"] = True
                drift_analysis["analysis"]["complexity_creep"] = True

        if len(skill_count_trend) >= 2:
            skill_counts = [t["skill_count"] for t in skill_count_trend]
            if all(
                skill_counts[i] <= skill_counts[i + 1]
                for i in range(len(skill_counts) - 1)
            ):
                drift_analysis["drift_detected"] = True
                drift_analysis["analysis"]["skill_requirement_growth"] = True

        return drift_analysis

    async def optimize_jd_recommendations(
        self, position_id: uuid.UUID
    ) -> dict:
        """
        Generate specific recommendations to optimize a JD.

        Args:
            position_id: The position to optimize

        Returns:
            Dictionary containing specific actionable recommendations
        """
        position = await self._get_position(position_id)
        if not position:
            raise ValueError(f"Position {position_id} not found")

        jd_version = await self._get_latest_jd_version(position_id)
        if not jd_version:
            raise ValueError(f"No JD version found for position {position_id}")

        # Perform full analysis
        analysis = await self.analyze_jd(position_id, position.user_id)

        # Generate detailed recommendations
        recommendations = {
            "position_id": str(position_id),
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "immediate_actions": [],
            "high_priority": [],
            "medium_priority": [],
            "low_priority": [],
        }

        # Analyze each dimension for specific recommendations
        for dim_key, scores in analysis["dimension_scores"].items():
            score = scores["score"]

            if score < 50:
                recommendations["immediate_actions"].append({
                    "dimension": scores["name"],
                    "current_score": score,
                    "issue": f"{scores['name']} scoring below 50",
                    "action": self._get_dimension_action(dim_key, score),
                })
            elif score < 70:
                recommendations["high_priority"].append({
                    "dimension": scores["name"],
                    "current_score": score,
                    "issue": f"{scores['name']} scoring below 70",
                    "action": self._get_dimension_action(dim_key, score),
                })
            elif score < 85:
                recommendations["medium_priority"].append({
                    "dimension": scores["name"],
                    "current_score": score,
                    "action": self._get_dimension_action(dim_key, score),
                })
            else:
                recommendations["low_priority"].append({
                    "dimension": scores["name"],
                    "current_score": score,
                    "action": "Minor refinements could improve appeal",
                })

        return recommendations

    # Private helper methods

    async def _get_position(self, position_id: uuid.UUID) -> Optional[Position]:
        """Fetch a position by ID."""
        stmt = select(Position).where(Position.id == position_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def _get_latest_jd_version(
        self, position_id: uuid.UUID
    ) -> Optional[JDVersion]:
        """Get the latest JD version for a position."""
        stmt = (
            select(JDVersion)
            .where(JDVersion.position_id == position_id)
            .order_by(desc(JDVersion.version))
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def _get_jd_version(self, version_id: uuid.UUID) -> Optional[JDVersion]:
        """Get a specific JD version by ID."""
        stmt = select(JDVersion).where(JDVersion.id == version_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def _get_all_jd_versions(
        self, position_id: uuid.UUID
    ) -> list[JDVersion]:
        """Get all JD versions for a position, ordered by version."""
        stmt = (
            select(JDVersion)
            .where(JDVersion.position_id == position_id)
            .order_by(JDVersion.version)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def _score_dimension(
        self, dimension_key: str, jd_version: JDVersion, position: Position
    ) -> float:
        """Score a specific dimension of the JD."""
        # Base score from parsed JD issues
        parsed = jd_version.parsed_requirements or {}
        base_score = parsed.get(f"{dimension_key}_score", 50.0)

        # Apply adjustments based on JD issues
        issues = jd_version.jd_issues or {}
        dimension_issues = issues.get(dimension_key, [])

        # Deduct points for each issue
        penalty = len(dimension_issues) * 5
        final_score = max(0, min(100, base_score - penalty))

        return float(final_score)

    def _calculate_weighted_score(self, dimension_scores: dict) -> float:
        """Calculate weighted overall score from dimension scores."""
        total_weighted = 0.0
        total_weight = 0.0

        for dim_key, dimension in self.DIMENSIONS.items():
            if dim_key in dimension_scores:
                score = dimension_scores[dim_key]["score"]
                weight = dimension_scores[dim_key]["weight"]
                total_weighted += score * weight
                total_weight += weight

        return float(total_weighted / total_weight) if total_weight > 0 else 0.0

    def _identify_improvements(self, dimension_scores: dict) -> list[dict]:
        """Identify areas with the most improvement potential."""
        improvements = []

        for dim_key, scores in dimension_scores.items():
            score = scores["score"]
            max_score = scores["max_score"]

            # Calculate improvement potential
            potential = max_score - score

            if potential > 10:  # Meaningful improvement possible
                improvements.append({
                    "dimension": scores["name"],
                    "current_score": score,
                    "potential_gain": potential,
                    "priority": (
                        "high"
                        if potential > 30
                        else ("medium" if potential > 15 else "low")
                    ),
                })

        # Sort by priority and potential
        return sorted(
            improvements,
            key=lambda x: (x["priority"] == "high", x["potential_gain"]),
            reverse=True,
        )

    def _generate_recommendations(
        self, dimension_scores: dict, jd_version: JDVersion
    ) -> list[str]:
        """Generate human-readable recommendations."""
        recommendations = []

        for dim_key, scores in dimension_scores.items():
            score = scores["score"]

            if dim_key == "clarity" and score < 70:
                recommendations.append(
                    "Simplify language and remove jargon where possible"
                )
            elif dim_key == "completeness" and score < 70:
                recommendations.append(
                    "Add missing sections: reporting structure, key responsibilities"
                )
            elif dim_key == "specificity" and score < 70:
                recommendations.append(
                    "Replace vague terms with specific metrics and examples"
                )
            elif dim_key == "fairness" and score < 80:
                recommendations.append(
                    "Review for potential bias in language and requirements"
                )
            elif dim_key == "accessibility" and score < 70:
                recommendations.append(
                    "Explicitly state accessibility accommodations available"
                )
            elif dim_key == "market_competitiveness" and score < 70:
                recommendations.append(
                    "Benchmark salary and benefits against market standards"
                )
            elif dim_key == "skill_alignment" and score < 70:
                recommendations.append(
                    "Group related skills and clarify nice-to-have vs required"
                )
            elif dim_key == "growth_opportunity" and score < 70:
                recommendations.append(
                    "Highlight career development paths and learning opportunities"
                )
            elif dim_key == "compliance" and score < 80:
                recommendations.append(
                    "Review compliance with local employment laws"
                )
            elif dim_key == "engagement_appeal" and score < 70:
                recommendations.append(
                    "Add company culture details and mission alignment"
                )

        return recommendations

    def _get_dimension_action(self, dimension_key: str, score: float) -> str:
        """Get specific action to improve a dimension."""
        actions = {
            "clarity": "Rewrite unclear sections using simpler language",
            "completeness": "Add missing sections like reporting structure",
            "specificity": "Replace vague requirements with specific metrics",
            "fairness": "Remove potentially biased or discriminatory language",
            "accessibility": "Clearly list accessibility accommodations",
            "market_competitiveness": "Adjust compensation to market rates",
            "skill_alignment": "Reorganize skills by criticality",
            "growth_opportunity": "Highlight training and career advancement",
            "compliance": "Ensure compliance with employment law",
            "engagement_appeal": "Emphasize culture and mission",
        }
        return actions.get(dimension_key, "Review and improve this dimension")

    def _extract_requirement_changes(
        self, v1: JDVersion, v2: JDVersion
    ) -> list[dict]:
        """Extract requirements that changed between versions."""
        changes = []

        p1 = v1.parsed_requirements or {}
        p2 = v2.parsed_requirements or {}

        # Compare required skills
        skills1 = set(p1.get("required_skills", []))
        skills2 = set(p2.get("required_skills", []))

        for skill in skills1 & skills2:
            # Check if experience requirement changed
            exp1 = p1.get("skill_experience", {}).get(skill, 0)
            exp2 = p2.get("skill_experience", {}).get(skill, 0)

            if exp1 != exp2:
                changes.append({
                    "skill": skill,
                    "type": "experience_change",
                    "from": exp1,
                    "to": exp2,
                })

        return changes

    def _extract_additions(self, v1: JDVersion, v2: JDVersion) -> list[dict]:
        """Extract new requirements added in version 2."""
        additions = []

        p1 = v1.parsed_requirements or {}
        p2 = v2.parsed_requirements or {}

        skills1 = set(p1.get("required_skills", []))
        skills2 = set(p2.get("required_skills", []))

        for skill in skills2 - skills1:
            additions.append({
                "skill": skill,
                "type": "new_requirement",
                "experience": p2.get("skill_experience", {}).get(skill, 0),
            })

        return additions

    def _extract_removals(self, v1: JDVersion, v2: JDVersion) -> list[dict]:
        """Extract requirements removed in version 2."""
        removals = []

        p1 = v1.parsed_requirements or {}
        p2 = v2.parsed_requirements or {}

        skills1 = set(p1.get("required_skills", []))
        skills2 = set(p2.get("required_skills", []))

        for skill in skills1 - skills2:
            removals.append({
                "skill": skill,
                "type": "removed_requirement",
                "was_required_years": p1.get("skill_experience", {}).get(skill, 0),
            })

        return removals

    def _analyze_scope_change(self, v1: JDVersion, v2: JDVersion) -> dict:
        """Analyze overall scope change between versions."""
        p1 = v1.parsed_requirements or {}
        p2 = v2.parsed_requirements or {}

        return {
            "complexity_change": p2.get("complexity_score", 50)
            - p1.get("complexity_score", 50),
            "seniority_change": (
                p2.get("seniority_level", "mid") != p1.get("seniority_level", "mid")
            ),
            "min_years_experience_change": p2.get("min_years_experience", 0)
            - p1.get("min_years_experience", 0),
        }
