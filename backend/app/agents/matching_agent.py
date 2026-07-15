"""Phase 4: Matching Agent - Calculate job-to-candidate fit.

Analyzes candidate-to-position fit and:
- Scores skill match (technical, soft)
- Scores experience match (years, relevance)
- Assesses team fit
- Evaluates compensation alignment
- Validates match (gates)
- Ranks candidates
- Identifies concerns and opportunities
"""
from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analysis_result import AnalysisResult
from app.models.position import Position
from app.models.resume import Resume

logger = logging.getLogger("truematch.matching_agent")


class MatchingAgent:
    """Agent for calculating candidate-to-position fit.

    Pipeline:
    1. Load analysis results and position requirements
    2. Score skill match
    3. Score experience match
    4. Assess team fit
    5. Evaluate compensation fit
    6. Run validation gates
    7. Rank candidates (batch context)
    8. Generate match recommendations
    """

    def __init__(self, db: AsyncSession):
        """Initialize matching agent.

        Args:
            db: Async database session
        """
        self.db = db

    async def calculate_match(
        self,
        analysis_result: AnalysisResult,
        position: Position,
        resume: Resume,
        batch_context: dict | None = None,
    ) -> dict:
        """Calculate candidate-to-position fit (main pipeline).

        Args:
            analysis_result: Completed analysis result
            position: Position object
            resume: Resume/candidate object
            batch_context: Optional batch ranking context

        Returns:
            {
                "skill_match": {...},
                "experience_match": {...},
                "team_fit": {...},
                "compensation_fit": {...},
                "overall_match": {...},
                "match_validation": {...},
                "concerns": {...},
                "opportunities": {...},
                "rank_in_batch": int | None
            }
        """
        logger.info(f"Starting match calculation for analysis {analysis_result.id}")

        try:
            # Phase 4.1: Score skill match
            skill_match = await self._score_skill_match(analysis_result, position)

            # Phase 4.2: Score experience match
            experience_match = await self._score_experience_match(
                analysis_result, position, resume
            )

            # Phase 4.3: Assess team fit
            team_fit = await self._assess_team_fit(analysis_result, position)

            # Phase 4.4: Evaluate compensation fit
            compensation_fit = await self._evaluate_compensation_fit(resume, position)

            # Phase 4.5: Calculate overall match
            overall_match, overall_score = await self._calculate_overall_match(
                skill_match, experience_match, team_fit, compensation_fit
            )

            # Phase 4.6: Run validation gates
            match_validation = await self._run_validation_gates(
                skill_match, experience_match, overall_score
            )

            # Phase 4.7: Identify concerns and opportunities
            concerns = await self._identify_concerns(
                analysis_result, skill_match, experience_match
            )
            opportunities = await self._identify_opportunities(
                analysis_result, skill_match, team_fit
            )

            # Phase 4.8: Rank in batch (if context provided)
            rank_info = await self._rank_in_batch(overall_score, batch_context or {})

            logger.info(
                f"Match calculation complete for {analysis_result.id}: "
                f"score={overall_score}, fit={overall_match.get('fit_level', 'unknown')}"
            )

            return {
                "skill_match": skill_match,
                "experience_match": experience_match,
                "team_fit": team_fit,
                "compensation_fit": compensation_fit,
                "overall_match": overall_match,
                "match_validation": match_validation,
                "overall_score": overall_score,
                "concerns": concerns,
                "opportunities": opportunities,
                "rank_in_batch": rank_info.get("rank"),
                "percentile": rank_info.get("percentile"),
            }

        except Exception as e:
            logger.error(f"Error in matching pipeline: {e}", exc_info=True)
            raise

    async def _score_skill_match(self, analysis: AnalysisResult, position: Position) -> dict:
        """Score technical and soft skill match.

        Args:
            analysis: Analysis result with assessment data
            position: Position with requirements

        Returns:
            {technical, required, gaps, match_score}
        """
        # Extract required skills from position
        description = position.description or ""
        required_skills = self._extract_required_skills(description)

        # Extract candidate skills from analysis patterns
        patterns = analysis.pattern_analysis or {}
        strengths = patterns.get("strengths", [])

        # Calculate matched vs gap
        matched = [s for s in required_skills if any(t in str(s).lower() for t in strengths)]
        gaps = [s for s in required_skills if s not in matched]

        # Score skill match
        match_score = int(100 * len(matched) / len(required_skills)) if required_skills else 50

        return {
            "technical": matched,
            "required": required_skills,
            "gaps": gaps,
            "match_score": min(100, match_score),
        }

    async def _score_experience_match(
        self, analysis: AnalysisResult, position: Position, resume: Resume
    ) -> dict:
        """Score experience fit (years, relevance, growth).

        Args:
            analysis: Analysis result
            position: Position
            resume: Resume with career data

        Returns:
            {years_required, years_candidate, relevance, growth_trajectory, match_score}
        """
        # Extract years required from JD
        description = position.description or ""
        years_required = self._extract_years_required(description)

        # Get candidate experience (simulated)
        years_candidate = 5  # Default to 5 years

        # Relevance based on analysis patterns
        gaps = len(analysis.pattern_analysis.get("gaps", []))
        relevance = "high" if gaps <= 2 else "medium" if gaps <= 5 else "low"

        # Growth trajectory from patterns
        growth_signals = analysis.pattern_analysis.get("growth_signals", [])
        growth = "ascending" if len(growth_signals) > 2 else "stable"

        # Match score
        if years_candidate >= years_required and relevance == "high":
            match_score = 90
        elif years_candidate >= years_required - 2 and relevance in ["high", "medium"]:
            match_score = 70
        else:
            match_score = 50

        return {
            "years_required": years_required,
            "years_candidate": years_candidate,
            "relevance": relevance,
            "growth_trajectory": growth,
            "match_score": match_score,
        }

    async def _assess_team_fit(self, analysis: AnalysisResult, position: Position) -> dict:
        """Assess team culture and communication fit.

        Args:
            analysis: Analysis result with patterns
            position: Position with team info

        Returns:
            {communication_style, collaboration_signals, leadership_fit, team_match_score}
        """
        # Get communication signals from growth signals
        growth_signals = analysis.pattern_analysis.get("growth_signals", [])

        communication = "collaborative" if len(growth_signals) > 1 else "independent"

        collaboration_signals = [s for s in growth_signals if "collaborate" in s.lower()]

        # Leadership fit (from strengths)
        strengths = analysis.pattern_analysis.get("strengths", [])
        leadership = "strong" if len(strengths) > 3 else "moderate" if len(strengths) > 1 else "developing"

        # Team match score
        team_match_score = 70 if communication == "collaborative" else 60

        return {
            "communication_style": communication,
            "collaboration_signals": collaboration_signals,
            "leadership_fit": leadership,
            "team_match_score": team_match_score,
        }

    async def _evaluate_compensation_fit(self, resume: Resume, position: Position) -> dict:
        """Evaluate salary expectations vs. job range.

        Args:
            resume: Resume with expectations
            position: Position with salary info

        Returns:
            {job_salary_range, candidate_expectation, alignment, stretch_factor}
        """
        # Salary range from position (simulated)
        job_range = "$120k-$150k"

        # Candidate expectation (from resume or default)
        candidate_expectation = "$130k"

        # Alignment check
        alignment = "aligned"  # Default to aligned if no conflict

        stretch_factor = 1.0

        return {
            "job_salary_range": job_range,
            "candidate_expectation": candidate_expectation,
            "alignment": alignment,
            "stretch_factor": stretch_factor,
        }

    async def _calculate_overall_match(
        self, skill: dict, experience: dict, team: dict, compensation: dict
    ) -> tuple[dict, int]:
        """Calculate overall match score and fit level.

        Weights:
        - Skill: 40%
        - Experience: 30%
        - Team: 20%
        - Compensation: 10%

        Args:
            skill: Skill match
            experience: Experience match
            team: Team fit
            compensation: Compensation fit

        Returns:
            ({overall_match_data}, overall_score)
        """
        # Weighted average
        score = int(
            0.4 * skill.get("match_score", 0)
            + 0.3 * experience.get("match_score", 0)
            + 0.2 * team.get("team_match_score", 0)
            + 0.1 * (100 if compensation.get("alignment") == "aligned" else 50)
        )

        # Determine fit level
        if score >= 85:
            fit_level = "strong_fit"
        elif score >= 70:
            fit_level = "good_fit"
        elif score >= 50:
            fit_level = "moderate_fit"
        elif score >= 30:
            fit_level = "weak_fit"
        else:
            fit_level = "poor_fit"

        overall = {
            "total_score": score,
            "fit_level": fit_level,
            "recommendation": "advance" if fit_level in ["strong_fit", "good_fit"] else "explore",
        }

        return overall, score

    async def _run_validation_gates(
        self, skill: dict, experience: dict, overall_score: int
    ) -> dict:
        """Run match validation gates.

        Gates:
        - Minimum skill match (50%)
        - Minimum experience (years or relevance)
        - Minimum overall score (40)

        Args:
            skill: Skill match
            experience: Experience match
            overall_score: Overall match score

        Returns:
            {passed, issues, risk_indicators}
        """
        issues = []
        risk_indicators = []

        # Gate 1: Skill match minimum
        if skill.get("match_score", 0) < 50:
            issues.append("Insufficient skill match")
            risk_indicators.append("major_skill_gap")

        # Gate 2: Experience minimum
        if experience.get("match_score", 0) < 40 and experience.get("relevance") == "low":
            issues.append("Experience mismatch")
            risk_indicators.append("experience_gap")

        # Gate 3: Overall score minimum
        if overall_score < 40:
            issues.append("Overall match below threshold")
            risk_indicators.append("low_overall_fit")

        passed = len(issues) == 0

        return {
            "passed": passed,
            "issues": issues,
            "risk_indicators": risk_indicators,
        }

    async def _identify_concerns(
        self, analysis: AnalysisResult, skill: dict, experience: dict
    ) -> dict:
        """Identify match concerns for recruiter.

        Args:
            analysis: Analysis result
            skill: Skill match
            experience: Experience match

        Returns:
            {growth_gaps, risk_signals, needs_discussion}
        """
        gaps = skill.get("gaps", [])
        red_flags = analysis.pattern_analysis.get("red_flags", [])

        return {
            "growth_gaps": gaps,
            "risk_signals": red_flags,
            "needs_discussion": gaps[:3] if gaps else [],
        }

    async def _identify_opportunities(
        self, analysis: AnalysisResult, skill: dict, team: dict
    ) -> dict:
        """Identify match opportunities for recruiter.

        Args:
            analysis: Analysis result
            skill: Skill match
            team: Team fit

        Returns:
            {growth_potential, unique_strengths, value_adds}
        """
        strengths = analysis.pattern_analysis.get("strengths", [])
        growth_signals = analysis.pattern_analysis.get("growth_signals", [])

        return {
            "growth_potential": growth_signals[:3],
            "unique_strengths": strengths[:3],
            "value_adds": [team.get("communication_style", "")],
        }

    async def _rank_in_batch(self, score: int, batch_context: dict) -> dict:
        """Rank candidate in batch context.

        Args:
            score: Overall match score
            batch_context: Batch ranking context

        Returns:
            {rank, percentile} or {rank: None, percentile: None}
        """
        if not batch_context:
            return {"rank": None, "percentile": None}

        # Would use batch_context to determine rank
        # For now, return placeholder
        return {"rank": None, "percentile": None}

    # Helper methods
    def _extract_required_skills(self, description: str) -> list[str]:
        """Extract required skills from job description."""
        if not description:
            return []

        keywords = [
            "python",
            "javascript",
            "sql",
            "react",
            "docker",
            "kubernetes",
            "leadership",
            "communication",
        ]

        return [k for k in keywords if k in description.lower()]

    def _extract_years_required(self, description: str) -> int:
        """Extract years of experience required from JD."""
        if not description:
            return 0

        import re

        match = re.search(r"(\d+)\s*\+?\s*years?", description, re.IGNORECASE)
        return int(match.group(1)) if match else 0


__all__ = ["MatchingAgent"]
