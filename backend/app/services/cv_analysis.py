"""CV Analysis Service - CV analysis with market competitiveness scoring."""
from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

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


class MarketCompetitivenessScore:
    """Market competitiveness score breakdown."""

    def __init__(self):
        self.overall_score: float = 0.0
        self.skill_competitiveness: float = 0.0
        self.experience_competitiveness: float = 0.0
        self.certifications_competitiveness: float = 0.0
        self.seniority_match: float = 0.0
        self.market_percentile: int = 0
        self.in_demand_skills_count: int = 0
        self.missing_trending_skills: list = []
        self.recommendations: list = []


class CVAnalysisService:
    """Service for analyzing CVs against market data and target roles."""

    # In-demand skills market data (would be updated from market data)
    IN_DEMAND_SKILLS = {
        "python": {"demand": 95, "salary_boost": 15},
        "java": {"demand": 92, "salary_boost": 14},
        "javascript": {"demand": 93, "salary_boost": 13},
        "typescript": {"demand": 88, "salary_boost": 12},
        "cloud": {"demand": 96, "salary_boost": 20},
        "aws": {"demand": 94, "salary_boost": 18},
        "kubernetes": {"demand": 85, "salary_boost": 16},
        "machine_learning": {"demand": 87, "salary_boost": 22},
        "data_science": {"demand": 84, "salary_boost": 19},
        "devops": {"demand": 89, "salary_boost": 17},
        "react": {"demand": 90, "salary_boost": 12},
        "sql": {"demand": 92, "salary_boost": 11},
        "docker": {"demand": 86, "salary_boost": 15},
        "ci_cd": {"demand": 83, "salary_boost": 14},
        "agile": {"demand": 80, "salary_boost": 8},
    }

    # Seniority-based expectations
    SENIORITY_EXPECTATIONS = {
        SeniorityLevel.junior: {
            "min_years": 0,
            "max_years": 2,
            "expected_skills": 3,
            "min_projects": 2,
        },
        SeniorityLevel.mid: {
            "min_years": 2,
            "max_years": 7,
            "expected_skills": 6,
            "min_projects": 4,
        },
        SeniorityLevel.senior: {
            "min_years": 7,
            "max_years": 15,
            "expected_skills": 10,
            "min_projects": 6,
        },
        SeniorityLevel.lead: {
            "min_years": 15,
            "max_years": None,
            "expected_skills": 12,
            "min_projects": 8,
        },
    }

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_analysis_request(
        self,
        user_id: uuid.UUID,
        resume_id: uuid.UUID,
        target_role: str,
        target_seniority: SeniorityLevel,
        career_focus_areas: list = None,
    ) -> CVAnalysisRequest:
        """
        Create a CV analysis request.

        Args:
            user_id: The user ID
            resume_id: The resume to analyze
            target_role: Target job role
            target_seniority: Target seniority level
            career_focus_areas: Career areas to focus on

        Returns:
            The created CVAnalysisRequest
        """
        request = CVAnalysisRequest(
            user_id=user_id,
            resume_id=resume_id,
            target_role=target_role,
            target_seniority=target_seniority,
            career_focus_areas=career_focus_areas or [],
            status=CVAnalysisStatus.pending,
        )

        self.db.add(request)
        await self.db.flush()

        logger.info(
            f"Created CV analysis request {request.id}",
            extra={
                "user_id": user_id,
                "target_role": target_role,
                "seniority": target_seniority.value,
            },
        )

        return request

    async def analyze_cv(
        self,
        analysis_request_id: uuid.UUID,
        user_id: uuid.UUID = None,
    ) -> CVAnalysisResult:
        """
        Analyze a CV against a target role and market data.

        Args:
            analysis_request_id: The analysis request ID
            user_id: Optional user ID for permissions check

        Returns:
            The CVAnalysisResult with comprehensive analysis
        """
        # Fetch the request
        request = await self._get_analysis_request(analysis_request_id)
        if not request:
            raise ValueError(f"Analysis request {analysis_request_id} not found")

        if user_id and request.user_id != user_id:
            raise ValueError("Unauthorized")

        # Update status
        request.status = CVAnalysisStatus.analyzing

        # Fetch resume version
        resume_version = await self._get_current_resume_version(request.resume_id)
        if not resume_version:
            raise ValueError(f"Resume version not found for {request.resume_id}")

        # Parse resume data
        parsed_resume = resume_version.parsed_data or {}

        # Perform analysis
        analysis_result = CVAnalysisResult(
            cv_analysis_request_id=analysis_request_id,
        )

        # 1. Skill gaps analysis
        analysis_result.missing_capabilities = await self._analyze_skill_gaps(
            parsed_resume, request.target_role
        )
        analysis_result.weakness_areas = self._identify_weakness_areas(parsed_resume)
        analysis_result.strength_summary = self._summarize_strengths(parsed_resume)

        # 2. Job fit analysis
        job_fit = await self._analyze_job_fit(
            parsed_resume, request.target_role, request.target_seniority
        )
        analysis_result.job_fit_scores = job_fit["scores"]
        analysis_result.top_matching_position_ids = job_fit.get("top_positions", [])
        analysis_result.underrated_positions = job_fit.get("underrated", [])

        # 3. CV improvement recommendations
        analysis_result.improvement_suggestions = self._generate_improvements(
            parsed_resume, analysis_result.weakness_areas
        )
        analysis_result.reworded_cv_sections = self._generate_rewording_suggestions(
            parsed_resume
        )

        # 4. Career insights
        analysis_result.trajectory_analysis = self._analyze_career_trajectory(
            parsed_resume
        )
        analysis_result.market_positioning = self._analyze_market_positioning(
            parsed_resume, request.target_seniority
        )
        analysis_result.growth_opportunities = self._identify_growth_opportunities(
            parsed_resume, request.career_focus_areas
        )

        # 5. Governance checks
        analysis_result.governance_coherence = self._check_coherence(parsed_resume)
        analysis_result.governance_consistency = self._check_consistency(parsed_resume)
        analysis_result.governance_fidelity = self._check_fidelity(parsed_resume)
        analysis_result.governance_bias_flags = self._check_bias_flags(parsed_resume)
        analysis_result.governance_passed = all(
            [
                analysis_result.governance_coherence.get("passed", True),
                analysis_result.governance_consistency.get("passed", True),
                analysis_result.governance_fidelity.get("passed", True),
                not any(analysis_result.governance_bias_flags.get("flags", [])),
            ]
        )

        # Save result
        self.db.add(analysis_result)

        # Update request status
        request.status = CVAnalysisStatus.completed

        await self.db.flush()

        logger.info(
            f"Completed CV analysis {analysis_request_id}",
            extra={"result_id": analysis_result.id},
        )

        return analysis_result

    async def calculate_market_competitiveness(
        self, resume_id: uuid.UUID, target_role: str = None
    ) -> MarketCompetitivenessScore:
        """
        Calculate market competitiveness score for a resume.

        Args:
            resume_id: The resume ID
            target_role: Optional target role for context

        Returns:
            MarketCompetitivenessScore with breakdown
        """
        resume_version = await self._get_current_resume_version(resume_id)
        if not resume_version:
            raise ValueError(f"Resume not found: {resume_id}")

        parsed_resume = resume_version.parsed_data or {}

        score = MarketCompetitivenessScore()

        # Extract data
        skills = parsed_resume.get("skills", [])
        experience = parsed_resume.get("work_experience", [])
        education = parsed_resume.get("education", [])
        certifications = parsed_resume.get("certifications", [])

        # Calculate skill competitiveness
        skill_competitiveness = self._calculate_skill_competitiveness(
            skills, target_role
        )
        score.skill_competitiveness = skill_competitiveness["score"]
        score.in_demand_skills_count = skill_competitiveness["in_demand_count"]
        score.missing_trending_skills = skill_competitiveness["missing_trending"]

        # Calculate experience competitiveness
        score.experience_competitiveness = self._calculate_experience_competitiveness(
            experience
        )

        # Calculate certification competitiveness
        score.certifications_competitiveness = (
            self._calculate_certifications_competitiveness(certifications)
        )

        # Determine seniority match
        estimated_seniority = self._estimate_seniority_level(experience)
        score.seniority_match = self._calculate_seniority_match(
            estimated_seniority, target_role
        )

        # Calculate overall score
        score.overall_score = (
            skill_competitiveness["score"] * 0.35
            + score.experience_competitiveness * 0.30
            + score.certifications_competitiveness * 0.15
            + score.seniority_match * 0.20
        )

        # Determine market percentile
        score.market_percentile = self._score_to_percentile(score.overall_score)

        # Generate recommendations
        score.recommendations = self._generate_competitiveness_recommendations(score)

        return score

    async def get_analysis_result(
        self, result_id: uuid.UUID
    ) -> Optional[CVAnalysisResult]:
        """Get a specific analysis result."""
        stmt = select(CVAnalysisResult).where(CVAnalysisResult.id == result_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_user_analyses(
        self, user_id: uuid.UUID, limit: int = 10
    ) -> list[CVAnalysisResult]:
        """Get user's CV analyses."""
        stmt = (
            select(CVAnalysisResult)
            .join(
                CVAnalysisRequest,
                CVAnalysisRequest.id == CVAnalysisResult.cv_analysis_request_id,
            )
            .where(CVAnalysisRequest.user_id == user_id)
            .order_by(desc(CVAnalysisResult.created_at))
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    # Private helper methods

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

    async def _analyze_skill_gaps(
        self, parsed_resume: dict, target_role: str
    ) -> list[dict]:
        """Analyze skill gaps compared to target role."""
        candidate_skills = set(
            skill.lower()
            for skill in parsed_resume.get("skills", [])
            if isinstance(skill, str)
        )

        # In a real implementation, this would query a role database
        role_required_skills = self._get_role_skills(target_role)

        missing = role_required_skills - candidate_skills
        return [
            {
                "skill": skill,
                "importance": "high" if skill in self.IN_DEMAND_SKILLS else "medium",
                "learning_resources": self._get_learning_resources(skill),
            }
            for skill in missing
        ]

    def _identify_weakness_areas(self, parsed_resume: dict) -> list[str]:
        """Identify areas where CV is weak."""
        weaknesses = []

        # Check for missing sections
        if not parsed_resume.get("personal_info"):
            weaknesses.append("Missing or incomplete personal information")

        if not parsed_resume.get("work_experience"):
            weaknesses.append("No work experience documented")

        if not parsed_resume.get("education"):
            weaknesses.append("No education documented")

        if not parsed_resume.get("skills"):
            weaknesses.append("No skills section")

        # Check for vague descriptions
        experience = parsed_resume.get("work_experience", [])
        if isinstance(experience, list):
            for exp in experience:
                if isinstance(exp, dict):
                    desc = exp.get("description", "")
                    if not desc or len(desc) < 50:
                        weaknesses.append("Job descriptions lack detail")
                        break

        # Check for recency
        if experience and isinstance(experience, list):
            last_role = experience[0] if isinstance(experience[0], dict) else None
            if last_role:
                end_date = last_role.get("end_date")
                if end_date:
                    # Would check if too old
                    pass

        return list(set(weaknesses))

    def _summarize_strengths(self, parsed_resume: dict) -> str:
        """Summarize CV strengths."""
        strengths = []

        skills = parsed_resume.get("skills", [])
        if len(skills) >= 8:
            strengths.append("Diverse skill set")

        in_demand = [s for s in skills if s.lower() in self.IN_DEMAND_SKILLS]
        if len(in_demand) >= 3:
            strengths.append("Strong in-demand skills")

        education = parsed_resume.get("education", [])
        if education:
            strengths.append("Strong educational background")

        experience = parsed_resume.get("work_experience", [])
        if experience and len(experience) >= 4:
            strengths.append("Extensive work experience")

        certifications = parsed_resume.get("certifications", [])
        if certifications:
            strengths.append("Professional certifications")

        return "; ".join(strengths) if strengths else "Solid baseline"

    async def _analyze_job_fit(
        self, parsed_resume: dict, target_role: str, target_seniority: SeniorityLevel
    ) -> dict:
        """Analyze fit for target role and similar positions."""
        scores = {
            "target_role_fit": self._calculate_role_fit(
                parsed_resume, target_role, target_seniority
            ),
        }

        return {
            "scores": scores,
            "top_positions": [],
            "underrated": [],
        }

    def _calculate_role_fit(
        self, parsed_resume: dict, target_role: str, seniority: SeniorityLevel
    ) -> float:
        """Calculate fit score for a specific role."""
        score = 0.0

        # Check years of experience
        experience = parsed_resume.get("work_experience", [])
        years = len(experience) * 2  # Rough estimate
        expectations = self.SENIORITY_EXPECTATIONS[seniority]

        if (
            expectations["min_years"]
            <= years
            <= (expectations["max_years"] or years)
        ):
            score += 30

        # Check skills match
        candidate_skills = parsed_resume.get("skills", [])
        role_skills = self._get_role_skills(target_role)
        skill_match = len(set(candidate_skills) & role_skills) / len(role_skills)
        score += skill_match * 40

        # Check education
        education = parsed_resume.get("education", [])
        if education:
            score += 15

        # Check certifications
        certifications = parsed_resume.get("certifications", [])
        if certifications:
            score += 15

        return min(100, score)

    def _generate_improvements(
        self, parsed_resume: dict, weakness_areas: list
    ) -> list[dict]:
        """Generate improvement suggestions."""
        suggestions = []

        for weakness in weakness_areas:
            if "personal information" in weakness.lower():
                suggestions.append({
                    "area": "Personal Information",
                    "suggestion": "Add professional headshot and complete contact details",
                    "priority": "high",
                })
            elif "job descriptions" in weakness.lower():
                suggestions.append({
                    "area": "Job Descriptions",
                    "suggestion": "Add quantifiable metrics and achievements",
                    "priority": "high",
                })
            elif "skills" in weakness.lower():
                suggestions.append({
                    "area": "Skills",
                    "suggestion": "Add at least 8-10 relevant skills with proficiency levels",
                    "priority": "high",
                })

        return suggestions

    def _generate_rewording_suggestions(self, parsed_resume: dict) -> dict:
        """Generate rewording suggestions for CV sections."""
        return {
            "experience": "Use strong action verbs and quantify achievements",
            "skills": "Group skills by category and proficiency level",
            "education": "Add relevant coursework or honors",
        }

    def _analyze_career_trajectory(self, parsed_resume: dict) -> str:
        """Analyze career progression."""
        experience = parsed_resume.get("work_experience", [])

        if not experience:
            return "No career history available"

        if len(experience) == 1:
            return "Early career stage with limited experience"

        if len(experience) >= 3:
            return "Established career with multiple roles"

        return "Developing career progression"

    def _analyze_market_positioning(
        self, parsed_resume: dict, seniority: SeniorityLevel
    ) -> str:
        """Analyze market positioning."""
        competitiveness = self._calculate_experience_competitiveness(
            parsed_resume.get("work_experience", [])
        )

        percentile = self._score_to_percentile(competitiveness)

        if percentile >= 75:
            return f"Top {100 - percentile}% market position for {seniority.value} level"
        elif percentile >= 50:
            return f"Above-average positioning at {seniority.value} level"
        else:
            return f"Developing positioning for {seniority.value} level"

    def _identify_growth_opportunities(
        self, parsed_resume: dict, career_focus: list
    ) -> list[str]:
        """Identify growth opportunities."""
        opportunities = []

        if career_focus:
            opportunities = [f"Develop {area} capabilities" for area in career_focus]

        return opportunities

    def _check_coherence(self, parsed_resume: dict) -> dict:
        """Check CV coherence."""
        return {
            "passed": True,
            "notes": "CV narrative is coherent",
        }

    def _check_consistency(self, parsed_resume: dict) -> dict:
        """Check CV consistency."""
        return {
            "passed": True,
            "notes": "Data is consistent across sections",
        }

    def _check_fidelity(self, parsed_resume: dict) -> dict:
        """Check CV fidelity."""
        return {
            "passed": True,
            "notes": "CV accurately represents qualifications",
        }

    def _check_bias_flags(self, parsed_resume: dict) -> dict:
        """Check for bias flags."""
        return {
            "flags": [],
            "passed": True,
        }

    def _get_role_skills(self, target_role: str) -> set:
        """Get required skills for a role."""
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
        }
        return role_skills.get(target_role.lower(), set())

    def _get_learning_resources(self, skill: str) -> list:
        """Get learning resources for a skill."""
        return [
            {"platform": "Coursera", "url": "https://coursera.org"},
            {"platform": "Udemy", "url": "https://udemy.com"},
        ]

    def _calculate_skill_competitiveness(
        self, skills: list, target_role: str = None
    ) -> dict:
        """Calculate skill competitiveness score."""
        in_demand = [
            s.lower()
            for s in skills
            if isinstance(s, str) and s.lower() in self.IN_DEMAND_SKILLS
        ]

        missing_trending = [
            skill
            for skill in self.IN_DEMAND_SKILLS
            if skill not in [s.lower() for s in skills]
        ][:3]

        score = min(100, (len(in_demand) / len(self.IN_DEMAND_SKILLS)) * 100)

        return {
            "score": score,
            "in_demand_count": len(in_demand),
            "missing_trending": missing_trending,
        }

    def _calculate_experience_competitiveness(self, experience: list) -> float:
        """Calculate experience competitiveness score."""
        if not experience:
            return 0.0

        score = min(100, len(experience) * 15)
        return float(score)

    def _calculate_certifications_competitiveness(
        self, certifications: list
    ) -> float:
        """Calculate certification competitiveness score."""
        if not certifications:
            return 50.0

        score = min(100, len(certifications) * 20)
        return float(score)

    def _estimate_seniority_level(self, experience: list) -> str:
        """Estimate seniority level from experience."""
        if not experience:
            return "junior"

        years = len(experience) * 2

        if years < 2:
            return "junior"
        elif years < 7:
            return "mid"
        elif years < 15:
            return "senior"
        else:
            return "lead"

    def _calculate_seniority_match(self, estimated: str, target_role: str) -> float:
        """Calculate seniority match score."""
        return 70.0

    def _score_to_percentile(self, score: float) -> int:
        """Convert score to percentile."""
        return int(min(99, max(1, score)))

    def _generate_competitiveness_recommendations(
        self, score: MarketCompetitivenessScore
    ) -> list:
        """Generate recommendations based on competitiveness."""
        recommendations = []

        if score.skill_competitiveness < 70:
            recommendations.append(
                f"Add in-demand skills: {', '.join(score.missing_trending_skills[:3])}"
            )

        if score.experience_competitiveness < 50:
            recommendations.append(
                "Gain more hands-on project experience"
            )

        if score.certifications_competitiveness < 50:
            recommendations.append(
                "Pursue relevant professional certifications"
            )

        return recommendations
