"""JD Optimization Service - Analysis with Claude Opus using 10-dimension scoring."""
from __future__ import annotations

import json
import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.engines.client import LLMError, _create_with_retry

logger = logging.getLogger(__name__)


class JDDimension:
    """Represents a scoring dimension for JD analysis."""

    def __init__(self, name: str, weight: float, description: str):
        self.name = name
        self.weight = weight
        self.description = description


class JDOptimizationService:
    """Service for optimizing and analyzing job descriptions using Claude Opus."""

    # 10-dimension scoring framework as specified
    DIMENSIONS = {
        "clarity": JDDimension(
            name="Clarity",
            weight=0.10,
            description="How clearly the JD communicates role expectations",
        ),
        "realism": JDDimension(
            name="Realism",
            weight=0.10,
            description="Whether requirements are realistic and achievable",
        ),
        "inclusivity": JDDimension(
            name="Inclusivity",
            weight=0.10,
            description="How welcoming and inclusive the language is",
        ),
        "competitiveness": JDDimension(
            name="Competitiveness",
            weight=0.12,
            description="Alignment with market standards and compensation",
        ),
        "specificity": JDDimension(
            name="Specificity",
            weight=0.12,
            description="Precision of requirements and qualifications",
        ),
        "skill_accuracy": JDDimension(
            name="Skill Accuracy",
            weight=0.10,
            description="Logical grouping and relevance of required skills",
        ),
        "bias_indicators": JDDimension(
            name="Bias Indicators",
            weight=0.12,
            description="Absence of discriminatory or biased language",
        ),
        "growth_potential": JDDimension(
            name="Growth Potential",
            weight=0.08,
            description="Learning and development opportunities in the role",
        ),
        "remote_friendliness": JDDimension(
            name="Remote Friendliness",
            weight=0.08,
            description="Clarity on remote work arrangements",
        ),
        "diversity_focus": JDDimension(
            name="Diversity Focus",
            weight=0.08,
            description="Commitment to diversity and inclusion",
        ),
    }

    def __init__(self, db: Optional[AsyncSession] = None):
        self.db = db

    async def analyze_jd_detailed(
        self, jd_text: str, position_title: str
    ) -> dict:
        """
        Analyze a job description across all 10 dimensions using Claude Opus.

        Args:
            jd_text: The full job description text
            position_title: The title of the position

        Returns:
            Dictionary containing:
                - score: Overall score 0-100
                - dimensions: List of dimension scores
                - issues: List of identified issues
                - suggestions: List of improvement suggestions
        """
        try:
            # Prepare analysis prompt for Claude Opus
            prompt = self._build_analysis_prompt(jd_text, position_title)

            # Call Claude Opus for analysis
            response = _create_with_retry(
                model="claude-opus-4-1-20250805",
                max_tokens=2048,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}],
            )

            # Extract response text
            response_text = "".join(
                block.text for block in response.content
                if getattr(block, "type", None) == "text"
            ).strip()

            # Parse JSON response
            analysis_result = self._parse_analysis_response(response_text)

            # Calculate overall score and organize results
            dimensions = analysis_result.get("dimensions", {})
            overall_score = self.compute_quality_score(dimensions)

            return {
                "score": overall_score,
                "dimensions": [
                    {
                        "name": dim_key,
                        "score": dimensions.get(dim_key, {}).get("score", 0),
                        "weight": self.DIMENSIONS[dim_key].weight,
                        "feedback": dimensions.get(dim_key, {}).get("feedback", ""),
                    }
                    for dim_key in self.DIMENSIONS.keys()
                    if dim_key in dimensions
                ],
                "issues": analysis_result.get("issues", []),
                "suggestions": analysis_result.get("suggestions", []),
            }

        except LLMError as e:
            logger.error(f"Claude Opus analysis failed: {str(e)}", extra={"position_title": position_title})
            raise
        except Exception as e:
            logger.error(f"JD analysis failed: {str(e)}", extra={"position_title": position_title})
            raise

    def compute_quality_score(self, dimensions: dict) -> int:
        """
        Compute overall quality score from dimension scores.

        Args:
            dimensions: Dictionary of dimension scores

        Returns:
            Weighted overall score 0-100
        """
        if not dimensions:
            return 0

        total_weighted = 0.0
        total_weight = 0.0

        for dim_key, dimension in self.DIMENSIONS.items():
            if dim_key in dimensions:
                score = dimensions[dim_key].get("score", 0)
                weight = dimension.weight
                total_weighted += score * weight
                total_weight += weight

        return int(total_weighted / total_weight) if total_weight > 0 else 0

    def generate_fixes_for_issue(self, issue: dict) -> list[dict]:
        """
        Generate specific fixes for an identified issue.

        Args:
            issue: Issue dictionary containing type and details

        Returns:
            List of Fix objects with actionable recommendations
        """
        issue_type = issue.get("type", "general")
        issue_text = issue.get("text", "")
        dimension = issue.get("dimension", "general")

        fixes = []

        # Map issues to specific fixes
        if issue_type == "bias":
            fixes.append({
                "priority": "high",
                "action": "Remove potentially biased language",
                "example": f'Replace "{issue_text}" with neutral, inclusive language',
                "impact": "bias_indicators",
            })
        elif issue_type == "vagueness":
            fixes.append({
                "priority": "high",
                "action": "Replace vague requirements with specific metrics",
                "example": f'Instead of "{issue_text}", specify exact years/skills required',
                "impact": "specificity",
            })
        elif issue_type == "unrealistic":
            fixes.append({
                "priority": "high",
                "action": "Make requirements more realistic",
                "example": f'Reduce years required or mark as nice-to-have',
                "impact": "realism",
            })
        elif issue_type == "unclear":
            fixes.append({
                "priority": "medium",
                "action": "Clarify requirements or expectations",
                "example": f'Provide more context or examples for "{issue_text}"',
                "impact": "clarity",
            })
        elif issue_type == "missing_context":
            fixes.append({
                "priority": "medium",
                "action": "Add missing information",
                "example": f'Add details about {issue_text}',
                "impact": "completeness",
            })
        else:
            fixes.append({
                "priority": "low",
                "action": f"Address {issue_type} issue",
                "example": issue_text,
                "impact": dimension,
            })

        return fixes

    def compute_market_competitiveness(self, jd: str, market_data: Optional[dict] = None) -> float:
        """
        Compute market competitiveness score for a JD.

        Args:
            jd: Job description text
            market_data: Optional market benchmark data

        Returns:
            Competitiveness score 0-100
        """
        if not market_data:
            market_data = self._get_default_market_data()

        score = 50.0

        # Check salary/compensation
        if "salary" in jd.lower() or "compensation" in jd.lower():
            score += 10
        else:
            score -= 5

        # Check benefits
        if any(
            keyword in jd.lower()
            for keyword in ["health", "pto", "retirement", "benefits", "401k"]
        ):
            score += 10
        else:
            score -= 5

        # Check career development
        if any(
            keyword in jd.lower()
            for keyword in ["growth", "development", "training", "mentorship", "learning"]
        ):
            score += 10

        # Check remote/flexibility
        if any(
            keyword in jd.lower()
            for keyword in ["remote", "flexible", "hybrid", "work from home"]
        ):
            score += 10

        # Check diversity/inclusion
        if any(
            keyword in jd.lower()
            for keyword in ["diverse", "diversity", "inclusion", "equal opportunity"]
        ):
            score += 10

        # Ensure score is in valid range
        return max(0.0, min(100.0, score))

    # Private helper methods

    def _build_analysis_prompt(self, jd_text: str, position_title: str) -> str:
        """Build the analysis prompt for Claude Opus."""
        dimension_descriptions = "\n".join(
            f"- {dim.name}: {dim.description}" for dim in self.DIMENSIONS.values()
        )

        return f"""Analyze the following job description across these 10 dimensions and provide a JSON response.

Position Title: {position_title}

Job Description:
{jd_text}

Dimensions to score (0-100 scale):
{dimension_descriptions}

Provide your analysis as JSON with this exact structure:
{{
  "dimensions": {{
    "clarity": {{"score": <0-100>, "feedback": "..."}},
    "realism": {{"score": <0-100>, "feedback": "..."}},
    "inclusivity": {{"score": <0-100>, "feedback": "..."}},
    "competitiveness": {{"score": <0-100>, "feedback": "..."}},
    "specificity": {{"score": <0-100>, "feedback": "..."}},
    "skill_accuracy": {{"score": <0-100>, "feedback": "..."}},
    "bias_indicators": {{"score": <0-100>, "feedback": "..."}},
    "growth_potential": {{"score": <0-100>, "feedback": "..."}},
    "remote_friendliness": {{"score": <0-100>, "feedback": "..."}},
    "diversity_focus": {{"score": <0-100>, "feedback": "..."}}
  }},
  "issues": [
    {{"type": "bias|vagueness|unrealistic|unclear|missing_context", "dimension": "...", "text": "...", "severity": "high|medium|low"}},
    ...
  ],
  "suggestions": [
    {{"dimension": "...", "action": "...", "rationale": "..."}},
    ...
  ]
}}

Score fairly and objectively. Be specific about issues found and constructive in suggestions."""

    def _parse_analysis_response(self, response_text: str) -> dict:
        """Parse Claude's JSON response."""
        try:
            # Extract JSON from response
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON found in response")

            json_str = response_text[json_start:json_end]
            return json.loads(json_str)
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse Claude response: {str(e)}")
            # Return default structure on parse error
            return {
                "dimensions": {
                    key: {"score": 50, "feedback": "Unable to analyze"}
                    for key in self.DIMENSIONS.keys()
                },
                "issues": [],
                "suggestions": [],
            }

    def _get_default_market_data(self) -> dict:
        """Get default market benchmark data."""
        return {
            "avg_salary_min": 80000,
            "avg_salary_max": 150000,
            "standard_benefits": [
                "health_insurance",
                "pto",
                "401k",
                "remote_option",
            ],
            "expected_experience": "3-5 years",
        }
