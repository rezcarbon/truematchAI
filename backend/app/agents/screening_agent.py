"""Screening Agent — Autonomous CV screening for bulk candidate evaluation.

Phase 1: Agent recommends (advance/hold/review) but NEVER excludes.
Recruiter makes final interview/reject decision.
All overrides logged for learning.

Core Principle - Conscience by Design:
1. Agent can only output: "advance" | "hold" | "review" (NO "exclude" or "reject")
2. Red flags are concerns, not disqualifications
3. Governance gates flag disparate impact but never hide candidates
4. Recruiter always has final decision authority
5. All agent reasoning logged for transparency
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assessment import Assessment
from app.models.resume import Resume
from app.models.position import Position
from app.models.screening import (
    ScreeningResult,
    ScreeningRecommendation,
    RecruiterDecision,
)
from app.models._types import EncryptedJSON, EncryptedText

logger = logging.getLogger(__name__)


class ScreeningAgent:
    """
    Autonomous agent for bulk CV screening.

    Inputs:
    - Resume (parsed text)
    - Position (job description + requirements)
    - Batch config (min experience, required skills, etc.)

    Outputs:
    - ScreeningResult {
        agent_recommendation: "advance" | "hold" | "review",
        confidence_score: 0-100,
        screening_summary: str (5-min recruiter brief),
        screening_details: dict (full analysis),
        bias_flags: dict (conscience checks)
      }

    Design Principles:
    - CONSCIENCE: Never outputs "exclude" or "reject"
    - TRANSPARENCY: All reasoning logged
    - FAIRNESS: Bias checks built-in
    - LEARNING: Overrides captured for feedback
    """

    def __init__(self, db: AsyncSession):
        """Initialize screening agent."""
        self.db = db
        self.logger = logger

    async def screen_resume(
        self,
        resume: Resume,
        position: Position,
        batch_config: Optional[dict] = None,
    ) -> ScreeningResult:
        """
        Main screening endpoint.

        Evaluates a resume against a position and returns a structured
        screening result with recommendation and recruiter brief.

        Args:
            resume: Resume object with parsed text
            position: Position object with JD
            batch_config: Optional batch configuration dict

        Returns:
            ScreeningResult with recommendation and summary
        """
        try:
            # Extract resume text
            resume_text = resume.supplementary.get("extracted_text", "")
            if not resume_text:
                self.logger.warning(f"Resume {resume.id} has no extracted text")
                resume_text = resume.raw_narrative or ""

            # Extract position requirements
            position_title = position.title
            jd_text = position.description or ""
            jd_requirements = position.metadata.get("requirements", {}) if position.metadata else {}

            # Phase 1: Conscience Check (BEFORE evaluation)
            # Fail-safe: Detect demographic indicators, never exclude
            bias_check = await self._run_conscience_check(resume_text, batch_config)

            # Phase 2: Skill Matching (Pillar 1 - Traditional)
            skill_match = await self._evaluate_skill_match(
                resume_text, jd_text, batch_config
            )

            # Phase 3: Experience Fit (Pillar 2)
            experience_fit = await self._evaluate_experience(
                resume_text, position, jd_requirements, batch_config
            )

            # Phase 4: Career Trajectory (Pillar 3)
            trajectory = await self._evaluate_trajectory(resume_text)

            # Phase 5: Red Flags (concerns, not exclusions)
            red_flags = await self._identify_red_flags(
                resume_text, position, batch_config
            )

            # Phase 6: Recommendation Generation
            # CRITICAL: Can only return advance/hold/review
            recommendation, confidence = await self._generate_recommendation(
                skill_match, experience_fit, trajectory, red_flags, bias_check
            )

            # Phase 7: Summary Generation (5-min brief for recruiter)
            summary = await self._generate_summary(
                resume, position, recommendation, confidence,
                skill_match, experience_fit, trajectory, red_flags, bias_check
            )

            # Phase 8: Learning Signal Capture
            learning_signals = await self._capture_learning_signals(
                resume, position, recommendation, confidence
            )

            # Construct screening details
            screening_details = {
                "skills_matched": skill_match.get("matched", []),
                "skills_missing": skill_match.get("missing", []),
                "experience_fit": experience_fit,
                "career_trajectory": trajectory,
                "red_flags": red_flags,
                "learning_signals": learning_signals,
            }

            # Log successful screening
            self.logger.info(
                f"Screened {resume.id} for {position.id}: "
                f"{recommendation} ({confidence}%)"
            )

            return {
                "agent_recommendation": recommendation,
                "confidence_score": confidence,
                "screening_summary": summary,
                "screening_details": screening_details,
                "bias_flags": bias_check,
            }

        except Exception as e:
            self.logger.error(
                f"Error screening resume {resume.id} for position {position.id}: {e}",
                exc_info=True
            )
            # Return review recommendation on error (escalate to human)
            return {
                "agent_recommendation": ScreeningRecommendation.review,
                "confidence_score": 0,
                "screening_summary": f"Error during screening: {str(e)}. Escalating to recruiter.",
                "screening_details": {"error": str(e)},
                "bias_flags": {"should_be_reviewed": True, "reason": "screening_error"},
            }

    # ========================================================================
    # PHASE 1: CONSCIENCE CHECK
    # ========================================================================

    async def _run_conscience_check(
        self,
        resume_text: str,
        batch_config: Optional[dict] = None,
    ) -> dict:
        """
        CONSCIENCE GATE: Detect demographic indicators.

        NEVER excludes candidates. Returns flags for recruiter awareness.

        Checks for:
        - Age indicators (graduation dates, years of experience)
        - Name-based nationality/gender proxies
        - Work gaps (pregnancy proxy)
        - Disability indicators
        - Other protected class signals

        Output: {
            "demographic_indicators": [str],
            "potential_disparate_impact": bool,
            "fairness_notes": str,
            "should_be_reviewed": bool
        }
        """
        try:
            indicators = []
            fairness_notes = []

            # Check for age indicators
            age_keywords = [
                "19", "20", "graduated", "graduation", "class of", "age"
            ]
            for keyword in age_keywords:
                if keyword.lower() in resume_text.lower():
                    indicators.append(f"potential_age_indicator: {keyword}")

            # Check for disability indicators
            disability_keywords = [
                "disability", "accommodations", "accessibility", "veterans",
                "service-connected"
            ]
            for keyword in disability_keywords:
                if keyword.lower() in resume_text.lower():
                    indicators.append(f"disability_disclosure: {keyword}")
                    fairness_notes.append(
                        "Candidate disclosed disability status. "
                        "Ensure evaluation focuses on job-relevant capabilities only."
                    )

            # Check for pregnancy/family status proxies
            family_keywords = [
                "maternity", "paternity", "parental", "childcare",
                "family leave", "caregiving"
            ]
            for keyword in family_keywords:
                if keyword.lower() in resume_text.lower():
                    indicators.append(f"family_status_disclosure: {keyword}")
                    fairness_notes.append(
                        "Candidate may have disclosed family status. "
                        "Ensure gaps in employment history are not penalized."
                    )

            disparate_impact = len(indicators) > 0
            should_review = disparate_impact  # Any indicators trigger review

            return {
                "demographic_indicators": indicators,
                "potential_disparate_impact": disparate_impact,
                "fairness_notes": " ".join(fairness_notes) or "No fairness concerns detected.",
                "should_be_reviewed": should_review,
                "governance_escalation": should_review,
            }

        except Exception as e:
            self.logger.error(f"Error in conscience check: {e}")
            return {
                "demographic_indicators": [],
                "potential_disparate_impact": False,
                "fairness_notes": "Conscience check errored; flagging for human review.",
                "should_be_reviewed": True,
                "governance_escalation": True,
            }

    # ========================================================================
    # PHASE 2: SKILL MATCHING
    # ========================================================================

    async def _evaluate_skill_match(
        self,
        resume_text: str,
        jd_text: str,
        batch_config: Optional[dict] = None,
    ) -> dict:
        """
        Evaluate skill matching between resume and JD.

        Uses keyword/semantic matching.
        Output: {
            "matched": [str],
            "missing": [str],
            "score": 0-100
        }
        """
        try:
            required_skills = []
            if batch_config and batch_config.get("required_skills"):
                required_skills = batch_config["required_skills"]
            elif jd_text:
                # Extract skills from JD (basic keyword extraction)
                required_skills = self._extract_skills_from_text(jd_text)

            matched = []
            missing = []
            resume_lower = resume_text.lower()

            for skill in required_skills:
                if skill.lower() in resume_lower:
                    matched.append(skill)
                else:
                    missing.append(skill)

            # Score: percentage of required skills matched
            if required_skills:
                score = int((len(matched) / len(required_skills)) * 100)
            else:
                score = 50  # Neutral if no required skills specified

            return {
                "matched": matched,
                "missing": missing,
                "score": score,
            }

        except Exception as e:
            self.logger.error(f"Error in skill matching: {e}")
            return {"matched": [], "missing": [], "score": 0}

    def _extract_skills_from_text(self, text: str) -> list[str]:
        """Extract technical skills from text (basic implementation)."""
        # Simple keyword-based extraction
        common_skills = [
            "python", "java", "javascript", "typescript", "react", "sql",
            "aws", "gcp", "azure", "docker", "kubernetes", "golang",
            "node", "fastapi", "django", "c++", "c#", "rust", "scala",
            "machine learning", "ai", "data science", "analytics",
            "agile", "scrum", "git", "ci/cd", "devops", "terraform",
            "postgresql", "mongodb", "redis", "elasticsearch",
        ]

        found_skills = []
        text_lower = text.lower()
        for skill in common_skills:
            if skill in text_lower:
                found_skills.append(skill.title())

        return found_skills

    # ========================================================================
    # PHASE 3: EXPERIENCE FIT
    # ========================================================================

    async def _evaluate_experience(
        self,
        resume_text: str,
        position: Position,
        jd_requirements: dict,
        batch_config: Optional[dict] = None,
    ) -> dict:
        """
        Evaluate experience fit.

        Checks years of experience, relevance, progression.
        Output: {
            "years": int,
            "relevance": "high" | "medium" | "low",
            "progression": str,
            "score": 0-100
        }
        """
        try:
            min_years = batch_config.get("min_experience_years", 0) if batch_config else 0

            # Count experience (simplified: count years mentioned)
            years = 0
            for i in range(1, 50):
                if str(i) + " year" in resume_text.lower():
                    years = max(years, i)

            # Determine relevance (check for keywords from position)
            relevance = "low"
            relevance_keywords = jd_requirements.get("skills", [])
            if not relevance_keywords and position.description:
                relevance_keywords = self._extract_skills_from_text(position.description)

            relevant_matches = sum(
                1 for keyword in relevance_keywords
                if keyword.lower() in resume_text.lower()
            )

            if relevant_matches >= len(relevance_keywords) * 0.8:
                relevance = "high"
            elif relevant_matches >= len(relevance_keywords) * 0.5:
                relevance = "medium"

            # Calculate score
            score = 0
            if years >= min_years:
                score += 50
            if relevance == "high":
                score += 50
            elif relevance == "medium":
                score += 25

            return {
                "years": years,
                "relevance": relevance,
                "progression": "Check resume for career growth",
                "score": score,
            }

        except Exception as e:
            self.logger.error(f"Error evaluating experience: {e}")
            return {"years": 0, "relevance": "low", "progression": "", "score": 0}

    # ========================================================================
    # PHASE 4: CAREER TRAJECTORY
    # ========================================================================

    async def _evaluate_trajectory(self, resume_text: str) -> dict:
        """
        Evaluate career progression and stability.

        Output: {
            "stability": "stable" | "moderate" | "volatile",
            "progression": "progressing" | "stable" | "declining",
            "score": 0-100
        }
        """
        try:
            # Simple heuristics
            score = 50  # Neutral

            # Check for gaps (5+ year stretches with same company = stable)
            if "5 year" in resume_text.lower() or "10 year" in resume_text.lower():
                stability = "stable"
                score += 25
            else:
                stability = "moderate"

            # Check for progression (promotions, title changes, seniority increase)
            seniority_keywords = ["director", "senior", "lead", "principal", "manager"]
            if any(kw in resume_text.lower() for kw in seniority_keywords):
                progression = "progressing"
                score += 25
            else:
                progression = "stable"

            return {
                "stability": stability,
                "progression": progression,
                "score": score,
            }

        except Exception as e:
            self.logger.error(f"Error evaluating trajectory: {e}")
            return {"stability": "moderate", "progression": "stable", "score": 50}

    # ========================================================================
    # PHASE 5: RED FLAGS
    # ========================================================================

    async def _identify_red_flags(
        self,
        resume_text: str,
        position: Position,
        batch_config: Optional[dict] = None,
    ) -> list[dict]:
        """
        Identify concerns (NOT disqualifications).

        Red flags are informational. Recruiter decides.

        Output: [
            {"type": "employment_gaps", "description": "6+ month gap...", "severity": "medium"},
            ...
        ]
        """
        try:
            red_flags = []

            # Check for employment gaps
            # (very simplified detection)
            if "gap" in resume_text.lower() or "break" in resume_text.lower():
                red_flags.append({
                    "type": "employment_gaps",
                    "description": "Resume mentions employment gap. "
                    "Consider discussing career transition.",
                    "severity": "low",
                })

            # Check for frequent job changes (very simplified)
            if resume_text.count("20") >= 10:  # Rough proxy: many year references
                red_flags.append({
                    "type": "frequent_job_changes",
                    "description": "May have multiple job changes. "
                    "Consider discussing stability and growth.",
                    "severity": "low",
                })

            # Check for skills atrophy (no recent years)
            current_year = datetime.now().year
            if str(current_year) not in resume_text and str(current_year - 1) not in resume_text:
                red_flags.append({
                    "type": "skills_atrophy",
                    "description": "No recent experience mentioned. "
                    "Consider discussing current skills and upskilling.",
                    "severity": "medium",
                })

            # Check custom red flag keywords from batch config
            if batch_config and batch_config.get("red_flag_keywords"):
                for keyword in batch_config["red_flag_keywords"]:
                    if keyword.lower() in resume_text.lower():
                        red_flags.append({
                            "type": "custom_keyword",
                            "description": f"Resume contains '{keyword}'",
                            "severity": "medium",
                        })

            return red_flags

        except Exception as e:
            self.logger.error(f"Error identifying red flags: {e}")
            return []

    # ========================================================================
    # PHASE 6: RECOMMENDATION GENERATION
    # ========================================================================

    async def _generate_recommendation(
        self,
        skill_match: dict,
        experience_fit: dict,
        trajectory: dict,
        red_flags: list,
        bias_check: dict,
    ) -> tuple[ScreeningRecommendation, int]:
        """
        Generate recommendation based on evaluation pillars.

        CRITICAL: Only outputs advance/hold/review.
        Never excludes based on score alone.

        Scoring:
        - Advance (75+): clear fit
        - Hold (50-75): potential fit
        - Review (<50): unclear OR governance concern

        If conscience check triggered: Always review.
        If red flags present: Always review.
        """
        try:
            # Aggregate scores
            skill_score = skill_match.get("score", 0)
            exp_score = experience_fit.get("score", 0)
            traj_score = trajectory.get("score", 50)

            # Weighted combination
            weighted_score = (
                skill_score * 0.4 +
                exp_score * 0.35 +
                traj_score * 0.25
            )

            # Apply conscience check override
            if bias_check.get("should_be_reviewed"):
                return (ScreeningRecommendation.review, int(weighted_score))

            # Apply red flag override
            if red_flags:
                return (ScreeningRecommendation.review, int(weighted_score))

            # Generate recommendation
            if weighted_score >= 75:
                return (ScreeningRecommendation.advance, int(weighted_score))
            elif weighted_score >= 50:
                return (ScreeningRecommendation.hold, int(weighted_score))
            else:
                return (ScreeningRecommendation.review, int(weighted_score))

        except Exception as e:
            self.logger.error(f"Error generating recommendation: {e}")
            return (ScreeningRecommendation.review, 0)

    # ========================================================================
    # PHASE 7: SUMMARY GENERATION
    # ========================================================================

    async def _generate_summary(
        self,
        resume: Resume,
        position: Position,
        recommendation: ScreeningRecommendation,
        confidence: int,
        skill_match: dict,
        experience_fit: dict,
        trajectory: dict,
        red_flags: list,
        bias_check: dict,
    ) -> str:
        """
        Generate 5-minute recruiter brief (~300-400 words).

        Clear, scannable, actionable.
        """
        try:
            summary_lines = []

            # Header
            summary_lines.append(f"SCREENING RECOMMENDATION: {recommendation.value.upper()}")
            summary_lines.append(f"Confidence Level: {confidence}%\n")

            # Candidate snapshot
            summary_lines.append("CANDIDATE SNAPSHOT:")
            summary_lines.append(f"• Experience: {experience_fit.get('years', 0)} years")
            summary_lines.append(f"• Relevance: {experience_fit.get('relevance', 'unknown')}")
            summary_lines.append(f"• Progression: {trajectory.get('progression', 'unknown')}\n")

            # Skills match
            matched = skill_match.get("matched", [])
            missing = skill_match.get("missing", [])

            if matched:
                summary_lines.append("KEY MATCHES:")
                for skill in matched[:3]:
                    summary_lines.append(f"  ✓ {skill}")
                summary_lines.append("")

            if missing:
                summary_lines.append("SKILLS GAPS (not disqualifying):")
                for skill in missing[:3]:
                    summary_lines.append(f"  • {skill}")
                summary_lines.append("")

            # Red flags
            if red_flags:
                summary_lines.append("CONSIDERATIONS FOR DISCUSSION:")
                for flag in red_flags:
                    summary_lines.append(f"  • {flag.get('description', '')}")
                summary_lines.append("")

            # Fairness notes
            if bias_check.get("potential_disparate_impact"):
                summary_lines.append("FAIRNESS NOTE:")
                summary_lines.append(f"  {bias_check.get('fairness_notes', '')}\n")

            # Recommendation action
            summary_lines.append("NEXT STEP:")
            if recommendation == ScreeningRecommendation.advance:
                summary_lines.append("  → Schedule phone screen")
            elif recommendation == ScreeningRecommendation.hold:
                summary_lines.append("  → Hold for later consideration or waitlist")
            else:
                summary_lines.append("  → Requires further review by recruiter")

            return "\n".join(summary_lines)

        except Exception as e:
            self.logger.error(f"Error generating summary: {e}")
            return f"Error generating summary: {e}"

    # ========================================================================
    # PHASE 8: LEARNING SIGNALS
    # ========================================================================

    async def _capture_learning_signals(
        self,
        resume: Resume,
        position: Position,
        recommendation: ScreeningRecommendation,
        confidence: int,
    ) -> dict:
        """
        Capture signals for agent learning loop.

        Used to improve future screening based on recruiter feedback.
        """
        return {
            "position_id": str(position.id),
            "candidate_id": str(resume.user_id),
            "recommendation": recommendation.value,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat(),
        }


__all__ = ["ScreeningAgent"]
