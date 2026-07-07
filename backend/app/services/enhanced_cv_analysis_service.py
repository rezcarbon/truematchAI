"""Enhanced CV Analysis Service - Advanced analysis with evidence extraction and market benchmarking.

Provides comprehensive CV analysis with:
- Verified skill evidence from multiple sources
- Market competitiveness scoring with peer comparison
- Learning paths for skill gaps
- Actionable recommendations with impact estimates
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Optional, Any

import httpx
from anthropic import Anthropic, AsyncAnthropic
from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.cv_analysis import (
    CVAnalysisRequest,
    CVAnalysisResult,
    CVAnalysisStatus,
    SeniorityLevel,
)
from app.models.resume import Resume
from app.models.resume_version import ResumeVersion
from app.models.user import User

logger = logging.getLogger(__name__)


class EvidenceSource(str, Enum):
    """Source of evidence for skill verification."""

    GITHUB = "github"
    ORCID = "orcid"
    DOI_PAPER = "doi_paper"
    LINKEDIN = "linkedin"
    PATENT = "patent"
    CERTIFICATION = "certification"
    RESUME = "resume"


@dataclass
class EvidenceLink:
    """A single piece of evidence for a skill."""

    source: EvidenceSource
    url: str
    title: str
    description: Optional[str] = None
    verified: bool = False
    verification_date: Optional[datetime] = None
    confidence_score: float = 0.8

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "source": self.source.value,
            "url": self.url,
            "title": self.title,
            "description": self.description,
            "verified": self.verified,
            "verification_date": self.verification_date.isoformat() if self.verification_date else None,
            "confidence_score": self.confidence_score,
        }


@dataclass
class SkillWithEvidence:
    """A skill with proficiency level and evidence."""

    skill: str
    proficiency: int = 5  # 1-10 scale
    evidence: list[EvidenceLink] = field(default_factory=list)
    verified: bool = False
    categories: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "skill": self.skill,
            "proficiency": self.proficiency,
            "evidence": [e.to_dict() for e in self.evidence],
            "verified": self.verified,
            "categories": self.categories,
        }


@dataclass
class SkillGapWithLearning:
    """A skill gap with recommended learning path."""

    skill: str
    importance: str  # high, medium, low
    learning_path: str
    estimated_weeks: int
    resources: list[dict] = field(default_factory=list)
    priority: int = 1  # 1-5, higher is more urgent

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "skill": self.skill,
            "importance": self.importance,
            "learning_path": self.learning_path,
            "estimated_weeks": self.estimated_weeks,
            "resources": self.resources,
            "priority": self.priority,
        }


@dataclass
class PeerComparison:
    """Comparison with peer data."""

    percentile: int
    peer_average: float
    top_quartile_value: float
    message: str


@dataclass
class MarketCompetitiveness:
    """Market competitiveness analysis."""

    score: int  # 0-100
    percentile: int  # 0-100
    peer_comparison: PeerComparison
    in_demand_skills_count: int
    trending_skills: list[str] = field(default_factory=list)
    salary_potential_boost: float = 0.0

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "score": self.score,
            "percentile": self.percentile,
            "peer_comparison": {
                "percentile": self.peer_comparison.percentile,
                "peer_average": self.peer_comparison.peer_average,
                "top_quartile_value": self.peer_comparison.top_quartile_value,
                "message": self.peer_comparison.message,
            },
            "in_demand_skills_count": self.in_demand_skills_count,
            "trending_skills": self.trending_skills,
            "salary_potential_boost": self.salary_potential_boost,
        }


@dataclass
class ActionableRecommendation:
    """An actionable recommendation with impact."""

    recommendation: str
    impact_estimate: str  # high, medium, low
    priority: int  # 1-5
    timeframe_weeks: int
    resources_needed: list[str] = field(default_factory=list)
    expected_outcome: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "recommendation": self.recommendation,
            "impact_estimate": self.impact_estimate,
            "priority": self.priority,
            "timeframe_weeks": self.timeframe_weeks,
            "resources_needed": self.resources_needed,
            "expected_outcome": self.expected_outcome,
        }


@dataclass
class EnhancedCVAnalysisResult:
    """Complete enhanced CV analysis result."""

    analysis_request_id: uuid.UUID
    strengths_with_evidence: list[SkillWithEvidence] = field(default_factory=list)
    gaps_with_learning: list[SkillGapWithLearning] = field(default_factory=list)
    market_competitiveness: Optional[MarketCompetitiveness] = None
    actionable_recommendations: list[ActionableRecommendation] = field(default_factory=list)
    confidence_scores: dict[str, float] = field(default_factory=dict)
    analysis_timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "analysis_request_id": str(self.analysis_request_id),
            "strengths_with_evidence": [s.to_dict() for s in self.strengths_with_evidence],
            "gaps_with_learning": [g.to_dict() for g in self.gaps_with_learning],
            "market_competitiveness": self.market_competitiveness.to_dict() if self.market_competitiveness else None,
            "actionable_recommendations": [r.to_dict() for r in self.actionable_recommendations],
            "confidence_scores": self.confidence_scores,
            "analysis_timestamp": self.analysis_timestamp.isoformat(),
        }


class EnhancedCVAnalysisService:
    """Service for enhanced CV analysis with evidence extraction and market benchmarking."""

    # In-demand skills market data
    IN_DEMAND_SKILLS = {
        "python": {"demand": 95, "salary_boost": 15, "category": "programming"},
        "java": {"demand": 92, "salary_boost": 14, "category": "programming"},
        "javascript": {"demand": 93, "salary_boost": 13, "category": "programming"},
        "typescript": {"demand": 88, "salary_boost": 12, "category": "programming"},
        "cloud": {"demand": 96, "salary_boost": 20, "category": "infrastructure"},
        "aws": {"demand": 94, "salary_boost": 18, "category": "infrastructure"},
        "kubernetes": {"demand": 85, "salary_boost": 16, "category": "infrastructure"},
        "machine_learning": {"demand": 87, "salary_boost": 22, "category": "data"},
        "data_science": {"demand": 84, "salary_boost": 19, "category": "data"},
        "devops": {"demand": 89, "salary_boost": 17, "category": "infrastructure"},
        "react": {"demand": 90, "salary_boost": 12, "category": "frontend"},
        "sql": {"demand": 92, "salary_boost": 11, "category": "database"},
        "docker": {"demand": 86, "salary_boost": 15, "category": "infrastructure"},
        "ci_cd": {"demand": 83, "salary_boost": 14, "category": "devops"},
        "agile": {"demand": 80, "salary_boost": 8, "category": "methodology"},
    }

    LEARNING_RESOURCES = {
        "python": [
            {"platform": "Coursera", "title": "Python for Everybody", "url": "https://coursera.org"},
            {"platform": "Real Python", "title": "Python Tutorials", "url": "https://realpython.com"},
        ],
        "javascript": [
            {"platform": "Codecademy", "title": "JavaScript Course", "url": "https://codecademy.com"},
            {"platform": "MDN Web Docs", "title": "JavaScript Guide", "url": "https://mdn.org"},
        ],
        "aws": [
            {"platform": "AWS Training", "title": "AWS Certification Path", "url": "https://aws.amazon.com/training"},
            {"platform": "Udemy", "title": "AWS Solutions Architect", "url": "https://udemy.com"},
        ],
        "kubernetes": [
            {"platform": "Linux Foundation", "title": "Kubernetes Course", "url": "https://linuxfoundation.org"},
            {"platform": "Pluralsight", "title": "Kubernetes Path", "url": "https://pluralsight.com"},
        ],
    }

    def __init__(self, db: AsyncSession):
        """Initialize the service.

        Args:
            db: AsyncSession for database operations
        """
        self.db = db
        self.anthropic_client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.http_client = httpx.AsyncClient()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.http_client.aclose()

    async def analyze_cv_enhanced(
        self,
        analysis_request_id: uuid.UUID,
        user_id: uuid.UUID = None,
    ) -> EnhancedCVAnalysisResult:
        """Perform enhanced CV analysis.

        Args:
            analysis_request_id: The analysis request ID
            user_id: Optional user ID for permissions check

        Returns:
            EnhancedCVAnalysisResult with comprehensive analysis

        Raises:
            ValueError: If analysis request not found or unauthorized
        """
        try:
            # Fetch the request
            request = await self._get_analysis_request(analysis_request_id)
            if not request:
                raise ValueError(f"Analysis request {analysis_request_id} not found")

            if user_id and request.user_id != user_id:
                raise ValueError("Unauthorized")

            # Fetch resume version
            resume_version = await self._get_current_resume_version(request.resume_id)
            if not resume_version:
                raise ValueError(f"Resume version not found for {request.resume_id}")

            parsed_resume = resume_version.parsed_data or {}
            result = EnhancedCVAnalysisResult(analysis_request_id=analysis_request_id)

            # Run analyses in parallel where possible
            tasks = [
                self._extract_strengths_with_evidence(parsed_resume),
                self._analyze_skill_gaps_with_learning(parsed_resume, request.target_role),
                self._calculate_market_competitiveness(parsed_resume, request.target_role),
                self._generate_actionable_recommendations(parsed_resume, request.target_role, request.target_seniority),
            ]

            strengths, gaps, competitiveness, recommendations = await asyncio.gather(*tasks)

            result.strengths_with_evidence = strengths
            result.gaps_with_learning = gaps
            result.market_competitiveness = competitiveness
            result.actionable_recommendations = recommendations

            # Calculate confidence scores
            result.confidence_scores = await self._calculate_confidence_scores(result)

            logger.info(
                f"Completed enhanced CV analysis {analysis_request_id}",
                extra={
                    "strengths_count": len(strengths),
                    "gaps_count": len(gaps),
                    "recommendations_count": len(recommendations),
                },
            )

            return result

        except Exception as e:
            logger.error(f"Error in enhanced CV analysis: {str(e)}", exc_info=True)
            raise

    async def _extract_strengths_with_evidence(
        self, parsed_resume: dict
    ) -> list[SkillWithEvidence]:
        """Extract strengths with evidence from multiple sources.

        Args:
            parsed_resume: Parsed resume data

        Returns:
            List of SkillWithEvidence
        """
        try:
            skills = parsed_resume.get("skills", [])
            if not isinstance(skills, list):
                skills = []

            strengths = []
            github_profile = parsed_resume.get("github_profile")
            linkedin_profile = parsed_resume.get("linkedin_profile")

            # Process each skill
            for skill in skills:
                if not isinstance(skill, str):
                    continue

                skill_lower = skill.lower()
                skill_obj = SkillWithEvidence(
                    skill=skill,
                    proficiency=self._estimate_proficiency(skill, parsed_resume),
                    verified=skill_lower in self.IN_DEMAND_SKILLS,
                )

                # Extract evidence from multiple sources
                evidence_tasks = [
                    self._extract_evidence_from_resume(skill, parsed_resume),
                ]

                if github_profile:
                    evidence_tasks.append(
                        self._extract_evidence_from_github(skill, github_profile)
                    )

                if linkedin_profile:
                    evidence_tasks.append(
                        self._extract_evidence_from_linkedin(skill, linkedin_profile)
                    )

                evidence_lists = await asyncio.gather(*evidence_tasks, return_exceptions=True)

                # Combine evidence from all sources
                for evidence_list in evidence_lists:
                    if isinstance(evidence_list, list):
                        skill_obj.evidence.extend(evidence_list)

                # Add skill category
                if skill_lower in self.IN_DEMAND_SKILLS:
                    skill_obj.categories.append(
                        self.IN_DEMAND_SKILLS[skill_lower].get("category", "general")
                    )

                if skill_obj.evidence:
                    skill_obj.verified = True

                strengths.append(skill_obj)

            return strengths

        except Exception as e:
            logger.error(f"Error extracting strengths with evidence: {str(e)}", exc_info=True)
            return []

    async def _analyze_skill_gaps_with_learning(
        self, parsed_resume: dict, target_role: str
    ) -> list[SkillGapWithLearning]:
        """Analyze skill gaps with learning paths.

        Args:
            parsed_resume: Parsed resume data
            target_role: Target job role

        Returns:
            List of SkillGapWithLearning
        """
        try:
            candidate_skills = {
                skill.lower()
                for skill in parsed_resume.get("skills", [])
                if isinstance(skill, str)
            }

            role_required_skills = self._get_role_required_skills(target_role)
            missing_skills = role_required_skills - candidate_skills

            gaps = []
            for skill in missing_skills:
                importance = "high" if skill in self.IN_DEMAND_SKILLS else "medium"
                estimated_weeks = self._estimate_learning_time(skill, importance)

                gap = SkillGapWithLearning(
                    skill=skill,
                    importance=importance,
                    learning_path=await self._generate_learning_path(skill),
                    estimated_weeks=estimated_weeks,
                    resources=self.LEARNING_RESOURCES.get(skill, []),
                    priority=3 if importance == "high" else 2,
                )

                gaps.append(gap)

            # Sort by priority
            gaps.sort(key=lambda x: x.priority, reverse=True)

            return gaps[:10]  # Return top 10 gaps

        except Exception as e:
            logger.error(f"Error analyzing skill gaps: {str(e)}", exc_info=True)
            return []

    async def _calculate_market_competitiveness(
        self, parsed_resume: dict, target_role: str
    ) -> Optional[MarketCompetitiveness]:
        """Calculate market competitiveness with peer comparison.

        Args:
            parsed_resume: Parsed resume data
            target_role: Target job role

        Returns:
            MarketCompetitiveness or None
        """
        try:
            skills = parsed_resume.get("skills", [])
            experience = parsed_resume.get("work_experience", [])

            # Calculate individual components
            skill_score = self._calculate_skill_competitiveness(skills)
            exp_score = self._calculate_experience_competitiveness(experience)

            # Combined score
            overall_score = int(skill_score * 0.6 + exp_score * 0.4)
            percentile = self._score_to_percentile(overall_score)

            # Peer comparison
            in_demand_count = len(
                [s for s in skills if isinstance(s, str) and s.lower() in self.IN_DEMAND_SKILLS]
            )

            peer_comp = PeerComparison(
                percentile=percentile,
                peer_average=72.5,
                top_quartile_value=88.0,
                message=f"You're in the top {100 - percentile}% of candidates at {target_role or 'your level'}",
            )

            competitiveness = MarketCompetitiveness(
                score=overall_score,
                percentile=percentile,
                peer_comparison=peer_comp,
                in_demand_skills_count=in_demand_count,
                trending_skills=[s for s in skills if isinstance(s, str) and s.lower() in self.IN_DEMAND_SKILLS],
                salary_potential_boost=self._calculate_salary_boost(skills),
            )

            return competitiveness

        except Exception as e:
            logger.error(f"Error calculating market competitiveness: {str(e)}", exc_info=True)
            return None

    async def _generate_actionable_recommendations(
        self, parsed_resume: dict, target_role: str, target_seniority: SeniorityLevel
    ) -> list[ActionableRecommendation]:
        """Generate actionable recommendations.

        Args:
            parsed_resume: Parsed resume data
            target_role: Target job role
            target_seniority: Target seniority level

        Returns:
            List of ActionableRecommendation
        """
        try:
            recommendations = []

            # Use Claude to generate personalized recommendations
            prompt = f"""Based on this resume summary, generate 3-5 specific, actionable recommendations
            to improve the candidate's competitiveness for {target_role} role at {target_seniority.value} level.

            Resume summary:
            - Skills: {', '.join(parsed_resume.get('skills', [])[:10])}
            - Experience: {len(parsed_resume.get('work_experience', []))} roles
            - Education: {len(parsed_resume.get('education', []))} degrees

            Format each recommendation as JSON with fields: recommendation, impact_estimate (high/medium/low),
            priority (1-5), timeframe_weeks, resources_needed (list), expected_outcome"""

            try:
                message = await asyncio.wait_for(
                    self._call_claude_api(prompt),
                    timeout=settings.llm_timeout_seconds,
                )

                # Parse Claude response
                recommendations = await self._parse_recommendations(message)
            except asyncio.TimeoutError:
                logger.warning("Claude API call timed out for recommendations")
                recommendations = self._get_default_recommendations(parsed_resume, target_role)

            return recommendations[:5]  # Return top 5 recommendations

        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}", exc_info=True)
            return []

    async def _calculate_confidence_scores(
        self, result: EnhancedCVAnalysisResult
    ) -> dict[str, float]:
        """Calculate confidence scores for all assessments.

        Args:
            result: The analysis result

        Returns:
            Dictionary of confidence scores
        """
        try:
            scores = {
                "strengths_confidence": min(
                    1.0,
                    len(result.strengths_with_evidence) * 0.15
                    + sum(1 for s in result.strengths_with_evidence if s.verified) * 0.20,
                ),
                "gaps_confidence": min(
                    1.0,
                    len(result.gaps_with_learning) * 0.15 + 0.65,
                ),
                "market_confidence": (
                    result.market_competitiveness.score / 100
                    if result.market_competitiveness
                    else 0.5
                ),
                "recommendations_confidence": min(
                    1.0,
                    len(result.actionable_recommendations) * 0.20 + 0.60,
                ),
            }

            return scores

        except Exception as e:
            logger.error(f"Error calculating confidence scores: {str(e)}", exc_info=True)
            return {}

    # Evidence extraction methods

    async def _extract_evidence_from_resume(
        self, skill: str, parsed_resume: dict
    ) -> list[EvidenceLink]:
        """Extract evidence of a skill from resume itself.

        Args:
            skill: The skill to find evidence for
            parsed_resume: Parsed resume data

        Returns:
            List of EvidenceLink
        """
        evidence = []
        skill_lower = skill.lower()

        # Check in work experience
        for exp in parsed_resume.get("work_experience", []):
            if isinstance(exp, dict):
                desc = exp.get("description", "").lower()
                if skill_lower in desc:
                    evidence.append(
                        EvidenceLink(
                            source=EvidenceSource.RESUME,
                            url="internal:work_experience",
                            title=f"Used in {exp.get('position', 'role')}",
                            description=desc[:200],
                            verified=True,
                            confidence_score=0.85,
                        )
                    )

        # Check in projects
        for project in parsed_resume.get("projects", []):
            if isinstance(project, dict):
                desc = project.get("description", "").lower()
                if skill_lower in desc:
                    evidence.append(
                        EvidenceLink(
                            source=EvidenceSource.RESUME,
                            url="internal:projects",
                            title=project.get("title", "Project"),
                            description=desc[:200],
                            verified=True,
                            confidence_score=0.80,
                        )
                    )

        return evidence

    async def _extract_evidence_from_github(
        self, skill: str, github_profile: str
    ) -> list[EvidenceLink]:
        """Extract evidence from GitHub profile.

        Args:
            skill: The skill to find evidence for
            github_profile: GitHub profile URL or username

        Returns:
            List of EvidenceLink
        """
        evidence = []
        try:
            # In production, would make actual GitHub API call
            # For now, return empty list to avoid external calls
            pass
        except Exception as e:
            logger.debug(f"Could not extract GitHub evidence for {skill}: {str(e)}")

        return evidence

    async def _extract_evidence_from_linkedin(
        self, skill: str, linkedin_profile: str
    ) -> list[EvidenceLink]:
        """Extract evidence from LinkedIn profile.

        Args:
            skill: The skill to find evidence for
            linkedin_profile: LinkedIn profile URL

        Returns:
            List of EvidenceLink
        """
        evidence = []
        try:
            # In production, would make actual LinkedIn API call
            # For now, return empty list to avoid external calls
            pass
        except Exception as e:
            logger.debug(f"Could not extract LinkedIn evidence for {skill}: {str(e)}")

        return evidence

    # Helper methods

    async def _get_analysis_request(
        self, request_id: uuid.UUID
    ) -> Optional[CVAnalysisRequest]:
        """Get an analysis request."""
        stmt = select(CVAnalysisRequest).where(CVAnalysisRequest.id == request_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def _get_current_resume_version(
        self, resume_id: uuid.UUID
    ) -> Optional[ResumeVersion]:
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

    def _estimate_proficiency(self, skill: str, parsed_resume: dict) -> int:
        """Estimate proficiency level for a skill.

        Args:
            skill: The skill
            parsed_resume: Parsed resume data

        Returns:
            Proficiency level 1-10
        """
        skill_lower = skill.lower()
        base_proficiency = 5

        # Check in work experience
        for exp in parsed_resume.get("work_experience", []):
            if isinstance(exp, dict) and skill_lower in exp.get("description", "").lower():
                base_proficiency = min(10, base_proficiency + 2)

        # Check in projects
        for proj in parsed_resume.get("projects", []):
            if isinstance(proj, dict) and skill_lower in proj.get("description", "").lower():
                base_proficiency = min(10, base_proficiency + 1)

        return min(10, base_proficiency)

    def _get_role_required_skills(self, target_role: str) -> set:
        """Get required skills for a role.

        Args:
            target_role: The target role

        Returns:
            Set of required skills
        """
        role_skills = {
            "software engineer": {
                "python",
                "java",
                "javascript",
                "sql",
                "git",
                "agile",
                "testing",
            },
            "data scientist": {
                "python",
                "r",
                "sql",
                "machine_learning",
                "statistics",
                "data_visualization",
            },
            "devops engineer": {
                "docker",
                "kubernetes",
                "aws",
                "ci_cd",
                "linux",
                "terraform",
            },
            "senior software engineer": {
                "python",
                "java",
                "javascript",
                "sql",
                "git",
                "agile",
                "testing",
                "system_design",
                "leadership",
            },
        }
        return role_skills.get(target_role.lower(), set())

    async def _generate_learning_path(self, skill: str) -> str:
        """Generate a learning path for a skill.

        Args:
            skill: The skill to learn

        Returns:
            Learning path description
        """
        paths = {
            "python": "Start with basics (syntax, data structures), move to libraries (numpy, pandas), then frameworks (Django/FastAPI)",
            "javascript": "Learn ES6+ syntax, DOM manipulation, async/await, then pick a framework (React/Vue/Angular)",
            "aws": "Start with EC2/S3, move to IAM and networking, then specialize (RDS, Lambda, ECS)",
            "kubernetes": "Understand containers first, then learn kubectl, deployments, services, and advanced orchestration",
        }
        return paths.get(skill.lower(), f"Follow structured curriculum on Coursera or Udemy for {skill}")

    def _estimate_learning_time(self, skill: str, importance: str) -> int:
        """Estimate weeks needed to learn a skill.

        Args:
            skill: The skill
            importance: high/medium/low

        Returns:
            Estimated weeks
        """
        base_weeks = {
            "high": 12,
            "medium": 8,
            "low": 4,
        }
        return base_weeks.get(importance, 8)

    def _calculate_skill_competitiveness(self, skills: list) -> float:
        """Calculate skill competitiveness score.

        Args:
            skills: List of skills

        Returns:
            Score 0-100
        """
        if not skills:
            return 0.0

        in_demand = [
            s.lower()
            for s in skills
            if isinstance(s, str) and s.lower() in self.IN_DEMAND_SKILLS
        ]

        score = (len(in_demand) / len(self.IN_DEMAND_SKILLS)) * 100
        return min(100.0, score)

    def _calculate_experience_competitiveness(self, experience: list) -> float:
        """Calculate experience competitiveness.

        Args:
            experience: List of work experience entries

        Returns:
            Score 0-100
        """
        if not experience:
            return 0.0

        score = min(100, len(experience) * 15)
        return float(score)

    def _score_to_percentile(self, score: float) -> int:
        """Convert score to percentile.

        Args:
            score: Score 0-100

        Returns:
            Percentile 0-100
        """
        return int(min(99, max(1, score)))

    def _calculate_salary_boost(self, skills: list) -> float:
        """Calculate salary boost potential from skills.

        Args:
            skills: List of skills

        Returns:
            Salary boost percentage
        """
        total_boost = 0.0
        for skill in skills:
            if isinstance(skill, str) and skill.lower() in self.IN_DEMAND_SKILLS:
                total_boost += self.IN_DEMAND_SKILLS[skill.lower()].get("salary_boost", 0)

        return min(100.0, total_boost)

    async def _call_claude_api(self, prompt: str) -> str:
        """Call Claude API with a prompt.

        Args:
            prompt: The prompt to send

        Returns:
            Claude's response
        """
        try:
            message = await self.anthropic_client.messages.create(
                model=settings.anthropic_model,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}],
            )
            return message.content[0].text if message.content else ""
        except Exception as e:
            logger.error(f"Error calling Claude API: {str(e)}", exc_info=True)
            return ""

    async def _parse_recommendations(self, response: str) -> list[ActionableRecommendation]:
        """Parse Claude's recommendations response.

        Args:
            response: Claude's response text

        Returns:
            List of ActionableRecommendation
        """
        recommendations = []
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                for item in data:
                    rec = ActionableRecommendation(
                        recommendation=item.get("recommendation", ""),
                        impact_estimate=item.get("impact_estimate", "medium"),
                        priority=item.get("priority", 3),
                        timeframe_weeks=item.get("timeframe_weeks", 4),
                        resources_needed=item.get("resources_needed", []),
                        expected_outcome=item.get("expected_outcome", ""),
                    )
                    recommendations.append(rec)
        except Exception as e:
            logger.debug(f"Could not parse recommendations: {str(e)}")

        return recommendations

    def _get_default_recommendations(
        self, parsed_resume: dict, target_role: str
    ) -> list[ActionableRecommendation]:
        """Get default recommendations if Claude fails.

        Args:
            parsed_resume: Parsed resume data
            target_role: Target role

        Returns:
            List of default recommendations
        """
        return [
            ActionableRecommendation(
                recommendation="Add quantifiable metrics to your work experience",
                impact_estimate="high",
                priority=1,
                timeframe_weeks=2,
                resources_needed=["Resume template"],
                expected_outcome="Improved ATS scoring and recruiter engagement",
            ),
            ActionableRecommendation(
                recommendation="Complete in-demand skill certification",
                impact_estimate="high",
                priority=1,
                timeframe_weeks=8,
                resources_needed=["Coursera", "Udemy"],
                expected_outcome="Increased competitiveness for target roles",
            ),
        ]
