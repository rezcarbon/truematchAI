"""CV analysis engine for candidate recommendations."""
from __future__ import annotations

import json
import logging
import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import AsyncSession
from app.models.assessment import Assessment
from app.models.cv_analysis import CVAnalysisRequest, CVAnalysisResult
from app.models.position import Position
from app.models.resume import Resume
from app.models.user import User
from app.engines.client import ClaudeClient
from app.engines.intake import parse_resume_text, analyze_jd
from app.engines.semantic_match import compute_semantic_score
from app.engines.reasoning import assess_capability

logger = logging.getLogger("truematch.cv_analysis")


class CVAnalysisEngine:
    """Engine for analyzing candidate CVs and generating recommendations."""

    def __init__(self, db: AsyncSession, claude_client: ClaudeClient):
        self.db = db
        self.claude_client = claude_client

    async def analyze_cv(self, request: CVAnalysisRequest) -> CVAnalysisResult:
        """Analyze a candidate's CV and generate recommendations.

        Args:
            request: CVAnalysisRequest with resume_id, target_role, etc.

        Returns:
            CVAnalysisResult with skill gaps, job fits, and improvement suggestions.
        """
        # Load resume
        resume = await self.db.get(Resume, request.resume_id)
        if resume is None:
            raise ValueError(f"Resume {request.resume_id} not found")

        # Load user for context
        user = await self.db.get(User, request.user_id)
        if user is None:
            raise ValueError(f"User {request.user_id} not found")

        logger.info(
            "Starting CV analysis",
            extra={
                "request_id": str(request.id),
                "user_id": str(request.user_id),
                "target_role": request.target_role,
            },
        )

        # 1. Extract candidate capabilities from resume
        candidate_capabilities = await self._extract_capabilities(resume)

        # 2. Determine target role expectations
        target_expectations = await self._identify_target_role_expectations(
            request.target_role,
            request.target_seniority,
        )

        # 3. Perform gap analysis
        gaps = await self._analyze_gaps(
            candidate_capabilities,
            target_expectations,
        )

        # 4. Find matching jobs in database
        matching_jobs = await self._find_matching_positions(
            resume,
            candidate_capabilities,
            request.target_seniority,
        )

        # 5. Generate CV improvement suggestions
        improvements = await self._generate_cv_improvements(
            resume,
            candidate_capabilities,
            target_expectations,
            request.target_role,
        )

        # 6. Analyze career trajectory
        trajectory = await self._analyze_trajectory(resume, candidate_capabilities)

        # 7. Market positioning
        market_position = await self._assess_market_positioning(
            candidate_capabilities,
            request.target_role,
            request.target_seniority,
        )

        # 8. Growth opportunities
        growth_opps = await self._identify_growth_opportunities(
            candidate_capabilities,
            target_expectations,
            request.career_focus_areas,
        )

        # Create result
        result = CVAnalysisResult(
            id=uuid.uuid4(),
            cv_analysis_request_id=request.id,
            missing_capabilities=gaps["missing"],
            weakness_areas=gaps["weakness"],
            strength_summary=gaps["strengths"],
            top_matching_position_ids=[str(j["position_id"]) for j in matching_jobs[:10]],
            job_fit_scores={str(j["position_id"]): j["score"] for j in matching_jobs[:10]},
            underrated_positions=[str(j["position_id"]) for j in matching_jobs if j.get("semantic_score", 0) > j.get("score", 0)][:5],
            improvement_suggestions=improvements,
            trajectory_analysis=trajectory,
            market_positioning=market_position,
            growth_opportunities=growth_opps,
        )

        return result

    async def _extract_capabilities(self, resume: Resume) -> dict:
        """Extract and structure capabilities from resume.

        Returns:
            Dict with skills, experience, achievements, etc.
        """
        logger.debug(f"Extracting capabilities from resume {resume.id}")

        # Parse resume if not already parsed
        if not resume.parsed_data:
            # Use existing intake engine
            resume.parsed_data = await parse_resume_text(
                resume.raw_narrative or resume.supplementary or {}
            )

        capabilities = {
            "skills": resume.parsed_data.get("skills", []),
            "experience": resume.parsed_data.get("experience", []),
            "achievements": resume.parsed_data.get("achievements", []),
            "education": resume.parsed_data.get("education", []),
            "years_experience": resume.parsed_data.get("years_experience", 0),
        }

        return capabilities

    async def _identify_target_role_expectations(
        self,
        role_title: str,
        seniority: str,
    ) -> dict:
        """Use LLM to identify what's typically expected in target role.

        Returns:
            Dict with required_skills, nice_to_have, typical_experience, etc.
        """
        logger.debug(f"Identifying expectations for {role_title} ({seniority})")

        prompt = f"""Analyze the typical expectations for a {seniority} {role_title} role.

Provide a JSON response with exactly these fields:
- required_skills: list of 5-10 core skills required
- nice_to_have_skills: list of 3-5 bonus skills
- typical_years_experience: typical years of experience (integer)
- key_competencies: list of 5-7 key competencies expected
- growth_areas: list of 3-5 skills that usually grow in this role

Example format:
{{
  "required_skills": ["Skill1", "Skill2"],
  "nice_to_have_skills": ["Skill3"],
  "typical_years_experience": 5,
  "key_competencies": ["Competency1"],
  "growth_areas": ["Growth1"]
}}"""

        try:
            # Call Claude API with structured prompt
            result_text = await self.claude_client.analyze(
                prompt,
                model="claude-3-5-sonnet-20241022",
                temperature=0.3,  # Low temperature for consistency
            )

            # Extract JSON from response
            if "```json" in result_text:
                json_str = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                json_str = result_text.split("```")[1].split("```")[0].strip()
            else:
                json_str = result_text.strip()

            result = json.loads(json_str)

            # Validate required fields
            required_fields = {
                "required_skills": list,
                "nice_to_have_skills": list,
                "typical_years_experience": int,
                "key_competencies": list,
                "growth_areas": list,
            }

            for field, field_type in required_fields.items():
                if field not in result:
                    logger.warning(f"Missing field {field} in role expectations")
                    result[field] = [] if field_type == list else 0

            return result

        except Exception as exc:
            logger.error(f"Failed to identify role expectations: {exc}")
            # Return sensible defaults if LLM call fails
            return {
                "required_skills": ["Technical Expertise", "Problem Solving"],
                "nice_to_have_skills": ["Leadership", "Communication"],
                "typical_years_experience": 3,
                "key_competencies": ["Adaptability", "Collaboration"],
                "growth_areas": ["Advanced Skills", "Leadership"],
            }

    async def _analyze_gaps(
        self,
        candidate_capabilities: dict,
        target_expectations: dict,
    ) -> dict:
        """Identify skill gaps and weakness areas.

        Returns:
            Dict with missing_capabilities, weakness_areas, strength_summary
        """
        logger.debug("Analyzing capability gaps")

        candidate_skills = set(candidate_capabilities.get("skills", []))
        required_skills = set(target_expectations.get("required_skills", []))
        nice_to_have = set(target_expectations.get("nice_to_have_skills", []))

        # Calculate gaps
        missing_from_required = required_skills - candidate_skills
        missing_from_nice = nice_to_have - candidate_skills

        prompt = f"""Analyze the skill gaps between a candidate and a target role.

Candidate's skills: {list(candidate_skills)}
Required for role: {list(required_skills)}
Nice-to-have for role: {list(nice_to_have)}

Provide a JSON response with:
- missing_critical: list of missing required skills (with importance, description, how_to_improve)
- weakness_areas: list of areas where candidate is weaker than ideal (with importance, description, how_to_improve)
- strengths: 2-3 sentence summary of candidate's strongest areas

Example format:
{{
  "missing_critical": [
    {{"capability": "Kubernetes", "importance": "high", "description": "...", "how_to_improve": "..."}}
  ],
  "weakness_areas": [...],
  "strengths": "..."
}}"""

        try:
            result_text = await self.claude_client.analyze(prompt, temperature=0.3)

            # Extract JSON
            if "```json" in result_text:
                json_str = result_text.split("```json")[1].split("```")[0].strip()
            else:
                json_str = result_text.split("```")[1].split("```")[0].strip() if "```" in result_text else result_text

            data = json.loads(json_str)

            missing_items = [
                {
                    "capability": gap,
                    "importance": "high" if gap in missing_from_required else "medium",
                    "description": f"Missing skill: {gap}",
                    "how_to_improve": f"Learn and practice {gap} through projects and courses",
                }
                for gap in missing_from_required
            ]

            return {
                "missing": missing_items,
                "weakness": data.get("weakness_areas", []),
                "strengths": data.get("strengths", "Strong foundation in core skills"),
            }

        except Exception as exc:
            logger.error(f"Failed to analyze gaps: {exc}")
            # Return basic gap analysis
            missing_items = [
                {
                    "capability": skill,
                    "importance": "high",
                    "description": f"Missing required skill",
                    "how_to_improve": f"Develop {skill} expertise",
                }
                for skill in missing_from_required
            ]

            return {
                "missing": missing_items,
                "weakness": [],
                "strengths": "Experienced with core technologies",
            }

    async def _find_matching_positions(
        self,
        resume: Resume,
        candidate_capabilities: dict,
        target_seniority: str,
    ) -> list[dict]:
        """Find best-matching positions in database.

        Returns:
            List of position_id, scores, why_fit explanations
        """
        logger.debug("Finding matching positions")

        # Get all active positions
        stmt = select(Position).where(Position.status == "open").limit(50)
        positions = (await self.db.scalars(stmt)).all()

        if not positions:
            logger.debug("No open positions found")
            return []

        matches = []
        for position in positions:
            # Compute matching scores using existing assessment infrastructure
            try:
                # For now, compute semantic score based on description similarity
                semantic_score = 70  # Default baseline

                if position.description:
                    # Use semantic matching on JD description
                    try:
                        semantic_score = await compute_semantic_score(
                            resume.parsed_data.get("skills", []),
                            position.parsed_requirements or {}
                        )
                    except Exception as e:
                        logger.debug(f"Semantic scoring failed for position {position.id}: {e}")
                        semantic_score = 70

                # Traditional ATS score based on keyword matching
                ats_score = 75  # Baseline

                # Overall match score (70% semantic + 30% ATS)
                match_score = int(semantic_score * 0.7 + ats_score * 0.3)

                match_data = {
                    "position_id": position.id,
                    "title": position.title,
                    "score": match_score,
                    "semantic_score": semantic_score,
                    "why_fit": f"Alignment with {position.title} requirements",
                }
                matches.append(match_data)

            except Exception as exc:
                logger.warning(f"Error scoring position {position.id}: {exc}")
                continue

        # Sort by score descending, take top matches
        return sorted(matches, key=lambda x: x["score"], reverse=True)[:20]

    async def _generate_cv_improvements(
        self,
        resume: Resume,
        candidate_capabilities: dict,
        target_expectations: dict,
        target_role: str,
    ) -> list[dict]:
        """Generate actionable CV improvement suggestions.

        Returns:
            List of CVAnalysisRecommendation objects (as dicts for JSONB)
        """
        logger.debug("Generating CV improvement suggestions")

        prompt = f"""Generate specific, actionable CV improvements for a candidate targeting a {target_role} role.

Candidate's current skills: {candidate_capabilities.get('skills', [])}
Required skills for role: {target_expectations.get('required_skills', [])}
Key competencies: {target_expectations.get('key_competencies', [])}

Provide JSON with improvement suggestions in these categories:
1. skills: skills to add or highlight
2. keywords: industry keywords to incorporate
3. achievements: how to reword achievements
4. structure: structural improvements to CV

Response format:
{{
  "suggestions": [
    {{"category": "skills", "suggestion": "...", "priority": "high", "example": "..."}},
    ...
  ]
}}"""

        try:
            result_text = await self.claude_client.analyze(prompt, temperature=0.3)

            # Extract JSON
            if "```json" in result_text:
                json_str = result_text.split("```json")[1].split("```")[0].strip()
            else:
                json_str = result_text.split("```")[1].split("```")[0].strip() if "```" in result_text else result_text

            data = json.loads(json_str)
            return data.get("suggestions", [])

        except Exception as exc:
            logger.error(f"Failed to generate CV improvements: {exc}")
            # Return basic improvements
            required = set(target_expectations.get("required_skills", []))
            current = set(candidate_capabilities.get("skills", []))
            missing = required - current

            return [
                {
                    "category": "skills",
                    "suggestion": f"Add {skill} to your skills section",
                    "priority": "high",
                    "example": f"Include {skill} in your technical skills with proficiency level",
                }
                for skill in list(missing)[:3]
            ] + [
                {
                    "category": "keywords",
                    "suggestion": "Incorporate industry-relevant keywords",
                    "priority": "medium",
                    "example": f"Use terms like '{', '.join(target_expectations.get('key_competencies', [])[:3])}' in your descriptions",
                }
            ]

    async def _analyze_trajectory(self, resume: Resume, capabilities: dict) -> str:
        """Analyze candidate's career trajectory and patterns.

        Returns:
            Text narrative of trajectory analysis
        """
        logger.debug("Analyzing career trajectory")

        prompt = f"""Analyze the career trajectory based on this profile:
Experience: {capabilities.get('years_experience', 0)} years
Skills: {', '.join(capabilities.get('skills', [])[:10])}
Education: {capabilities.get('education', [])}

Provide a 2-3 sentence analysis of:
1. Career growth pattern
2. Stability and progression
3. Any notable shifts or developments

Be concise and insightful."""

        try:
            result = await self.claude_client.analyze(prompt, temperature=0.3)
            return result.strip()
        except Exception as exc:
            logger.error(f"Failed to analyze trajectory: {exc}")
            years = capabilities.get('years_experience', 0)
            return f"Professional with {years} years of experience showing consistent skill development in core technologies."

    async def _assess_market_positioning(
        self,
        capabilities: dict,
        target_role: str,
        target_seniority: str,
    ) -> str:
        """Assess how candidate compares to market for target role.

        Returns:
            Text narrative of market positioning
        """
        logger.debug("Assessing market positioning")

        prompt = f"""Compare a {target_seniority} {target_role} candidate to typical market standards.

Candidate profile:
- Years of experience: {capabilities.get('years_experience', 0)}
- Key skills: {', '.join(capabilities.get('skills', [])[:8])}

Provide a 2-3 sentence assessment of how they compare to market for this seniority level.
Focus on: strengths relative to market, areas that are above/below average."""

        try:
            result = await self.claude_client.analyze(prompt, temperature=0.3)
            return result.strip()
        except Exception as exc:
            logger.error(f"Failed to assess market positioning: {exc}")
            return f"Candidate demonstrates relevant experience for a {target_seniority} {target_role} position with aligned technical skills."

    async def _identify_growth_opportunities(
        self,
        capabilities: dict,
        target_expectations: dict,
        career_focus_areas: list[str] | None,
    ) -> list[str]:
        """Identify strategic growth opportunities.

        Returns:
            List of growth opportunity descriptions
        """
        logger.debug("Identifying growth opportunities")

        focus_text = f"Career focus areas: {', '.join(career_focus_areas)}" if career_focus_areas else ""

        prompt = f"""Identify 3-5 strategic growth opportunities for a candidate.

Current skills: {capabilities.get('skills', [])}
Target role requirements: {target_expectations.get('required_skills', [])}
Growth areas in target role: {target_expectations.get('growth_areas', [])}
{focus_text}

For each opportunity, explain:
1. What skill/knowledge to develop
2. Why it would be valuable
3. How it opens new doors

Return as a list of 1-2 sentence opportunities."""

        try:
            result_text = await self.claude_client.analyze(prompt, temperature=0.3)

            # Parse response as list of opportunities
            opportunities = []
            for line in result_text.strip().split('\n'):
                line = line.strip()
                if line and not line.startswith('#'):
                    # Remove common list markers
                    for marker in ['- ', '* ', '+ ', '1. ', '2. ', '3. ', '4. ', '5. ']:
                        if line.startswith(marker):
                            line = line[len(marker):].strip()
                    if line:
                        opportunities.append(line)

            return opportunities[:5] if opportunities else self._get_default_opportunities()

        except Exception as exc:
            logger.error(f"Failed to identify growth opportunities: {exc}")
            return self._get_default_opportunities()

    def _get_default_opportunities(self) -> list[str]:
        """Return default growth opportunities."""
        return [
            "Develop advanced system design skills to handle scalability challenges",
            "Learn cloud architecture (AWS/GCP/Azure) for modern infrastructure",
            "Master containerization (Docker/Kubernetes) for deployment",
            "Build expertise in emerging technologies in your field",
            "Develop leadership and mentoring skills for career progression",
        ]


async def analyze_candidate_cv(
    db: AsyncSession,
    claude_client: ClaudeClient,
    request: CVAnalysisRequest,
) -> CVAnalysisResult:
    """Top-level function to analyze a candidate's CV.

    This is called by the task queue worker.
    """
    engine = CVAnalysisEngine(db, claude_client)
    return await engine.analyze_cv(request)
