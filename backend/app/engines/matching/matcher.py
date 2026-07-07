"""Enhanced matching engine for job-candidate pairing with component-based scoring.

Combines keyword matching, semantic matching, and capability matching to provide
comprehensive scoring with multiple match type classifications.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Any

from app.engines import semantic_match, text_utils

logger = logging.getLogger(__name__)


class MatchType(str, Enum):
    """Classification of job-candidate match quality."""
    hidden_gem = "hidden_gem"  # Semantic/capability strong, keyword weak
    perfect_match = "perfect_match"  # All signals >= 80
    overqualified = "overqualified"  # Capability >> role_level
    growth_opportunity = "growth_opportunity"  # Semantic matches, capability needs development
    partial_match = "partial_match"  # Mixed signals


@dataclass
class Skill:
    """Represents a skill with assessment data."""
    name: str
    proficiency: Optional[str] = None
    years_of_experience: Optional[float] = None
    confidence: float = 0.5
    source: str = "unknown"  # resume, jd, inferred, etc.

    def to_dict(self) -> dict:
        """Convert skill to dictionary."""
        return {
            "name": self.name,
            "proficiency": self.proficiency,
            "years_of_experience": self.years_of_experience,
            "confidence": self.confidence,
            "source": self.source,
        }


@dataclass
class MatchResult:
    """Complete match analysis between candidate and job."""
    keyword_score: float
    semantic_score: float
    capability_score: float
    overall_score: float
    match_type: MatchType
    explanation: str
    skills_aligned: list[Skill] = field(default_factory=list)
    skills_missing: list[Skill] = field(default_factory=list)
    matched_concepts: list[str] = field(default_factory=list)
    missing_concepts: list[str] = field(default_factory=list)
    component_details: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert result to dictionary for serialization."""
        return {
            "keyword_score": self.keyword_score,
            "semantic_score": self.semantic_score,
            "capability_score": self.capability_score,
            "overall_score": self.overall_score,
            "match_type": self.match_type.value,
            "explanation": self.explanation,
            "skills_aligned": [s.to_dict() for s in self.skills_aligned],
            "skills_missing": [s.to_dict() for s in self.skills_missing],
            "matched_concepts": self.matched_concepts,
            "missing_concepts": self.missing_concepts,
            "component_details": self.component_details,
        }


class EnhancedMatcher:
    """Enhanced matching engine combining multiple matching signals."""

    # Scoring thresholds and weights
    KEYWORD_WEIGHT = 0.30
    SEMANTIC_WEIGHT = 0.35
    CAPABILITY_WEIGHT = 0.35

    # Match type detection thresholds
    PERFECT_MATCH_THRESHOLD = 80.0
    HIDDEN_GEM_KEYWORD_MAX = 60.0
    OVERQUALIFIED_DIFF = 20.0
    GROWTH_OPPORTUNITY_CAPABILITY_MAX = 70.0

    def __init__(self):
        """Initialize the enhanced matcher."""
        self.semantic_matcher = semantic_match
        logger.debug("EnhancedMatcher initialized")

    def match_with_components(
        self,
        candidate_profile: dict,
        job_description: str,
        role_level: Optional[str] = None,
    ) -> MatchResult:
        """
        Analyze match between candidate and job with component breakdown.

        Args:
            candidate_profile: Candidate data including resume text, skills, experience
            job_description: Full job description text
            role_level: Expected seniority level (junior, mid, senior, lead)

        Returns:
            MatchResult with detailed scoring and analysis
        """
        # Extract data from profile
        resume_text = candidate_profile.get("resume_text", "")
        candidate_skills = candidate_profile.get("skills", [])
        experience_years = candidate_profile.get("experience_years", 0)
        candidate_title = candidate_profile.get("current_title", "")

        if not resume_text or not job_description:
            logger.warning("Missing resume_text or job_description for matching")
            return self._create_empty_result()

        try:
            # Calculate component scores
            keyword_score = self._calculate_keyword_score(
                resume_text, job_description, candidate_skills
            )
            semantic_result = self.semantic_matcher.semantic_score(
                resume_text, job_description
            )
            semantic_score = semantic_result.get("score", 0)
            matched_concepts = semantic_result.get("matched_concepts", [])
            missing_concepts = semantic_result.get("missing_concepts", [])

            capability_score = self._calculate_capability_score(
                candidate_profile, job_description, role_level
            )

            # Calculate overall weighted score
            overall_score = (
                keyword_score * self.KEYWORD_WEIGHT
                + semantic_score * self.SEMANTIC_WEIGHT
                + capability_score * self.CAPABILITY_WEIGHT
            )

            # Extract aligned and missing skills
            skills_aligned, skills_missing = self._extract_skills(
                job_description, candidate_skills
            )

            # Determine match type
            match_type = self._classify_match_type(
                keyword_score, semantic_score, capability_score, role_level, experience_years
            )

            # Generate explanation
            explanation = self._generate_explanation(
                match_type, keyword_score, semantic_score, capability_score
            )

            component_details = {
                "semantic_method": semantic_result.get("method"),
                "semantic_deterministic": semantic_result.get("deterministic", False),
                "keyword_analysis": {
                    "score": keyword_score,
                    "resume_length": len(resume_text),
                    "jd_length": len(job_description),
                },
                "capability_analysis": {
                    "score": capability_score,
                    "role_level": role_level,
                    "experience_years": experience_years,
                },
            }

            result = MatchResult(
                keyword_score=keyword_score,
                semantic_score=semantic_score,
                capability_score=capability_score,
                overall_score=round(overall_score, 2),
                match_type=match_type,
                explanation=explanation,
                skills_aligned=skills_aligned,
                skills_missing=skills_missing,
                matched_concepts=matched_concepts,
                missing_concepts=missing_concepts,
                component_details=component_details,
            )

            logger.info(
                "Match completed",
                extra={
                    "overall_score": result.overall_score,
                    "match_type": result.match_type.value,
                    "keyword_score": keyword_score,
                    "semantic_score": semantic_score,
                    "capability_score": capability_score,
                },
            )

            return result

        except Exception as e:
            logger.error(f"Error during matching: {e}", exc_info=True)
            return self._create_error_result(str(e))

    def _calculate_keyword_score(
        self,
        resume_text: str,
        job_description: str,
        candidate_skills: list[dict] | None = None,
    ) -> float:
        """
        Calculate keyword matching score (0-100).

        Uses exact skill matching and weighted keyword overlap.
        """
        if not resume_text or not job_description:
            return 0.0

        # Extract keywords/skills from JD
        jd_keywords = set(text_utils.tokenize(job_description))
        resume_keywords = set(text_utils.tokenize(resume_text))

        if not jd_keywords:
            return 0.0

        # Calculate base overlap
        overlap = len(jd_keywords & resume_keywords) / len(jd_keywords)
        base_score = overlap * 100

        # Boost score for exact skill matches
        bonus = 0.0
        if candidate_skills:
            skill_names = {s.get("name", "").lower() for s in candidate_skills}
            jd_skill_requirements = self._extract_skill_requirements(job_description)
            matched_skills = len(skill_names & jd_skill_requirements)
            if jd_skill_requirements:
                bonus = (matched_skills / len(jd_skill_requirements)) * 20

        keyword_score = min(100.0, base_score + bonus)
        logger.debug(f"Keyword score: {keyword_score} (overlap: {overlap:.2%}, bonus: {bonus:.1f})")
        return round(keyword_score, 2)

    def _calculate_capability_score(
        self,
        candidate_profile: dict,
        job_description: str,
        role_level: Optional[str] = None,
    ) -> float:
        """
        Calculate capability/experience matching score (0-100).

        Considers experience level, years of experience, and skill depth.
        """
        experience_years = candidate_profile.get("experience_years", 0)
        candidate_seniority = candidate_profile.get("seniority_level", "mid")
        candidate_skills = candidate_profile.get("skills", [])

        if not candidate_skills and experience_years == 0:
            return 0.0

        # Score based on experience years alignment
        level_score = self._score_level_alignment(
            candidate_seniority, role_level, experience_years
        )

        # Score based on skill depth and specialization
        skill_depth_score = self._score_skill_depth(candidate_skills)

        # Score based on relevant domain experience
        domain_score = self._score_domain_alignment(
            candidate_profile, job_description
        )

        capability_score = (
            level_score * 0.4 + skill_depth_score * 0.35 + domain_score * 0.25
        )

        logger.debug(
            f"Capability score: {capability_score} "
            f"(level: {level_score}, depth: {skill_depth_score}, domain: {domain_score})"
        )
        return round(capability_score, 2)

    def _score_level_alignment(
        self,
        candidate_seniority: str,
        role_level: Optional[str],
        experience_years: float,
    ) -> float:
        """Score alignment between candidate and role seniority level."""
        level_hierarchy = {
            "junior": 0,
            "mid": 1,
            "senior": 2,
            "lead": 3,
            "principal": 4,
        }

        candidate_level = level_hierarchy.get(
            candidate_seniority.lower(), 1
        )
        role_level_val = level_hierarchy.get(
            role_level.lower() if role_level else "mid", 1
        )

        # Perfect alignment
        if candidate_level == role_level_val:
            return 100.0

        # One level difference is acceptable
        if abs(candidate_level - role_level_val) == 1:
            return 80.0

        # Two or more levels difference
        level_diff = abs(candidate_level - role_level_val)
        return max(40.0, 100.0 - (level_diff * 15))

    def _score_skill_depth(self, candidate_skills: list[dict] | None) -> float:
        """Score the depth and breadth of candidate's skills."""
        if not candidate_skills:
            return 0.0

        total_skills = len(candidate_skills)
        deep_skills = sum(
            1 for s in candidate_skills
            if s.get("years_of_experience", 0) >= 3
        )
        expert_skills = sum(
            1 for s in candidate_skills
            if s.get("years_of_experience", 0) >= 7
        )

        # Breadth score (number of skills)
        breadth = min(100.0, total_skills * 10)

        # Depth score (deep experience)
        depth = (deep_skills / max(1, total_skills)) * 100 if total_skills else 0
        expert_bonus = (expert_skills / max(1, total_skills)) * 20 if total_skills else 0

        skill_depth = (breadth * 0.3 + depth * 0.7) + expert_bonus
        return min(100.0, skill_depth)

    def _score_domain_alignment(
        self,
        candidate_profile: dict,
        job_description: str,
    ) -> float:
        """Score alignment between candidate's domain experience and job domain."""
        candidate_background = candidate_profile.get("background", "")
        candidate_industries = candidate_profile.get("industries", [])

        if not candidate_background and not candidate_industries:
            return 50.0  # Neutral score if no domain info

        # Extract industry keywords from JD
        jd_industries = self._extract_industries(job_description)

        if not jd_industries:
            return 60.0  # No clear domain requirement

        # Score industry overlap
        industry_match = set(candidate_industries) & set(jd_industries)
        industry_score = (len(industry_match) / len(jd_industries)) * 100 if jd_industries else 0

        return min(100.0, industry_score)

    def _classify_match_type(
        self,
        keyword_score: float,
        semantic_score: float,
        capability_score: float,
        role_level: Optional[str],
        experience_years: float,
    ) -> MatchType:
        """Classify the type of match based on score components."""
        # Perfect match: all signals strong
        if (
            keyword_score >= self.PERFECT_MATCH_THRESHOLD
            and semantic_score >= self.PERFECT_MATCH_THRESHOLD
            and capability_score >= self.PERFECT_MATCH_THRESHOLD
        ):
            return MatchType.perfect_match

        # Hidden gem: weak keyword, strong semantic/capability
        if (
            keyword_score < self.HIDDEN_GEM_KEYWORD_MAX
            and semantic_score >= 70
            and capability_score >= 70
        ):
            return MatchType.hidden_gem

        # Overqualified: capability significantly higher than needed
        expected_capability = (keyword_score + semantic_score) / 2
        if (
            capability_score - expected_capability
            >= self.OVERQUALIFIED_DIFF
        ):
            return MatchType.overqualified

        # Growth opportunity: semantic strong, capability weak
        if (
            semantic_score >= 75
            and capability_score < self.GROWTH_OPPORTUNITY_CAPABILITY_MAX
        ):
            return MatchType.growth_opportunity

        # Default: partial match
        return MatchType.partial_match

    def _generate_explanation(
        self,
        match_type: MatchType,
        keyword_score: float,
        semantic_score: float,
        capability_score: float,
    ) -> str:
        """Generate a human-readable explanation of the match."""
        explanations = {
            MatchType.perfect_match: (
                f"Excellent match across all dimensions. "
                f"Strong keyword alignment ({keyword_score:.0f}), "
                f"semantic understanding ({semantic_score:.0f}), "
                f"and capability match ({capability_score:.0f})."
            ),
            MatchType.hidden_gem: (
                f"High potential match despite lower keyword overlap ({keyword_score:.0f}). "
                f"Candidate demonstrates strong semantic understanding ({semantic_score:.0f}) "
                f"and relevant capabilities ({capability_score:.0f}) for the role."
            ),
            MatchType.overqualified: (
                f"Candidate appears overqualified for this role. "
                f"Strong capabilities ({capability_score:.0f}) exceed typical requirements. "
                f"May seek higher-level opportunities."
            ),
            MatchType.growth_opportunity: (
                f"Good semantic fit ({semantic_score:.0f}) with room for capability development. "
                f"Candidate has foundation but needs to strengthen specific skills "
                f"(current capability: {capability_score:.0f})."
            ),
            MatchType.partial_match: (
                f"Mixed match signals. Keyword overlap: {keyword_score:.0f}, "
                f"Semantic match: {semantic_score:.0f}, Capability: {capability_score:.0f}. "
                f"Review skills and experience alignment."
            ),
        }
        return explanations.get(match_type, "Unable to classify match.")

    def _extract_skills(
        self,
        job_description: str,
        candidate_skills: list[dict] | None = None,
    ) -> tuple[list[Skill], list[Skill]]:
        """Extract and classify aligned vs missing skills."""
        candidate_skills = candidate_skills or []
        candidate_skill_names = {s.get("name", "").lower() for s in candidate_skills}

        # Extract required skills from JD
        jd_skills = self._extract_skill_requirements(job_description)

        aligned_skills = []
        missing_skills = []

        for jd_skill in jd_skills[:10]:  # Limit to top 10 skills
            if jd_skill.lower() in candidate_skill_names:
                # Find matching candidate skill
                for c_skill in candidate_skills:
                    if c_skill.get("name", "").lower() == jd_skill.lower():
                        aligned_skills.append(
                            Skill(
                                name=jd_skill,
                                proficiency=c_skill.get("proficiency"),
                                years_of_experience=c_skill.get("years_of_experience"),
                                confidence=0.9,
                                source="resume",
                            )
                        )
                        break
            else:
                missing_skills.append(
                    Skill(
                        name=jd_skill,
                        proficiency=None,
                        confidence=0.7,
                        source="jd",
                    )
                )

        return aligned_skills, missing_skills

    def _extract_skill_requirements(self, job_description: str) -> set[str]:
        """Extract likely skill requirements from job description."""
        # Common tech and professional skills
        common_skills = {
            "python", "java", "javascript", "typescript", "go", "rust", "c++",
            "sql", "mongodb", "postgresql", "react", "angular", "vue", "node",
            "aws", "gcp", "azure", "kubernetes", "docker", "git", "ci/cd",
            "devops", "machine learning", "data science", "analytics",
            "agile", "scrum", "project management", "communication",
            "leadership", "teamwork", "problem solving", "critical thinking",
            "html", "css", "rest api", "graphql", "microservices",
            "testing", "tdd", "debugging", "performance optimization",
        }

        jd_lower = job_description.lower()
        extracted_skills = set()

        for skill in common_skills:
            if skill in jd_lower:
                extracted_skills.add(skill)

        return extracted_skills

    def _extract_industries(self, job_description: str) -> list[str]:
        """Extract likely industry tags from job description."""
        industries = [
            "fintech", "finance", "healthcare", "medical", "biotech",
            "technology", "software", "saas", "ecommerce", "retail",
            "manufacturing", "logistics", "education", "media", "entertainment",
            "telecommunications", "energy", "government", "nonprofit",
        ]

        jd_lower = job_description.lower()
        found_industries = []

        for industry in industries:
            if industry in jd_lower:
                found_industries.append(industry)

        return found_industries

    def _create_empty_result(self) -> MatchResult:
        """Create empty result when matching cannot proceed."""
        return MatchResult(
            keyword_score=0.0,
            semantic_score=0.0,
            capability_score=0.0,
            overall_score=0.0,
            match_type=MatchType.partial_match,
            explanation="Unable to perform match due to missing data.",
        )

    def _create_error_result(self, error_message: str) -> MatchResult:
        """Create error result."""
        return MatchResult(
            keyword_score=0.0,
            semantic_score=0.0,
            capability_score=0.0,
            overall_score=0.0,
            match_type=MatchType.partial_match,
            explanation=f"Error during matching: {error_message}",
        )
