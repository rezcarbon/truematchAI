"""JD simulation engine for recruiter recommendations."""
from __future__ import annotations

import json
import logging
import uuid
from typing import Optional

from sqlalchemy import select

from app.database import AsyncSession
from app.models.candidate_archetype import CandidateArchetype
from app.models.jd_simulation import JDSimulationRequest, JDSimulationResult
from app.models.position import Position
from app.engines.client import ClaudeClient
from app.engines.intake import analyze_jd

logger = logging.getLogger("truematch.jd_simulation")


class JDSimulationEngine:
    """Engine for analyzing job descriptions and generating recommendations."""

    def __init__(self, db: AsyncSession, claude_client: ClaudeClient):
        self.db = db
        self.claude_client = claude_client

    async def simulate_jd(self, request: JDSimulationRequest) -> JDSimulationResult:
        """Simulate and analyze a job description.

        Args:
            request: JDSimulationRequest with position_id or jd_text

        Returns:
            JDSimulationResult with analysis and recommendations
        """
        # Get JD content
        jd_text = request.jd_text
        position = None
        if request.position_id:
            position = await self.db.get(Position, request.position_id)
            if position:
                jd_text = position.description

        if not jd_text:
            raise ValueError("No JD text available")

        logger.info(
            "Starting JD simulation",
            extra={
                "request_id": str(request.id),
                "user_id": str(request.user_id),
                "simulation_type": request.simulation_type.value,
            },
        )

        # 1. Parse JD and extract requirements
        jd_requirements = await self._parse_jd(jd_text)

        # 2. Analyze capability clarity
        capability_gaps = await self._analyze_capability_clarity(jd_requirements)

        # 3. Detect requirement creep
        creep_analysis = await self._analyze_requirement_creep(jd_requirements)

        # 4. Test against candidate archetypes
        archetype_fits = await self._test_archetype_fit(jd_requirements)

        # 5. Assess JD quality
        quality_analysis = await self._assess_jd_quality(jd_requirements)

        # 6. Generate wording suggestions
        wording_suggestions = await self._generate_wording_suggestions(
            jd_requirements,
            jd_text,
        )

        # 7. Market positioning
        market_analysis = await self._assess_market_standards(jd_requirements)

        # Create result
        result = JDSimulationResult(
            id=uuid.uuid4(),
            jd_simulation_request_id=request.id,
            critical_capabilities=capability_gaps["critical"],
            missing_clarity=capability_gaps["clarity_issues"],
            capability_recommendations=capability_gaps["recommendations"],
            requirement_difficulty_score=creep_analysis["difficulty_score"],
            experience_years_assessment=creep_analysis["experience_assessment"],
            tech_stack_balance=creep_analysis["tech_balance"],
            creep_warnings=creep_analysis["warnings"],
            fit_by_archetype=archetype_fits,
            best_archetype_fit=self._get_best_archetype(archetype_fits),
            talent_pool_estimate=self._estimate_talent_pool(archetype_fits),
            quality_score=quality_analysis["score"],
            market_positioning=market_analysis["positioning"],
            missing_sections=quality_analysis["missing_sections"],
            quality_issues=quality_analysis["issues"],
            suggested_job_title_variations=wording_suggestions["title_variations"],
            improved_role_description=wording_suggestions["improved_description"],
            capability_verbiage_suggestions=wording_suggestions["capability_suggestions"],
            benefits_suggestions=wording_suggestions["benefits"],
            culture_fit_language=wording_suggestions["culture_fit"],
        )

        return result

    async def _parse_jd(self, jd_text: str) -> dict:
        """Parse JD and extract structured requirements.

        Returns:
            Dict with title, requirements, experience_level, tech_stack, etc.
        """
        logger.debug("Parsing JD")

        # Use existing intake engine (analyze_jd is synchronous)
        parsed = analyze_jd(jd_text)

        return {
            "title": parsed.get("title"),
            "requirements": parsed.get("requirements", []),
            "experience_level": parsed.get("experience_level"),
            "tech_stack": parsed.get("tech_stack", []),
            "soft_skills": parsed.get("soft_skills", []),
            "responsibilities": parsed.get("responsibilities", []),
        }

    async def _analyze_capability_clarity(self, jd_requirements: dict) -> dict:
        """Analyze clarity and completeness of capability descriptions.

        Returns:
            Dict with critical gaps, clarity issues, recommendations
        """
        logger.debug("Analyzing capability clarity")

        prompt = f"""Analyze the clarity of capability descriptions in this JD.

Requirements listed: {jd_requirements.get('requirements', [])}
Tech stack: {jd_requirements.get('tech_stack', [])}
Soft skills: {jd_requirements.get('soft_skills', [])}

Identify:
1. Vague requirements that need clarification (e.g., "strong communication")
2. Critical capabilities that are underspecified
3. Missing proficiency level details

Return JSON:
{{
  "clarity_issues": ["issue1", "issue2"],
  "critical_gaps": [
    {{"capability": "name", "current": "description", "recommended": "improved description"}}
  ]
}}"""

        try:
            result_text = self.claude_client.analyze(prompt, temperature=0.3)

            # Extract JSON
            if "```json" in result_text:
                json_str = result_text.split("```json")[1].split("```")[0].strip()
            else:
                json_str = result_text.split("```")[1].split("```")[0].strip() if "```" in result_text else result_text

            data = json.loads(json_str)

            # Format critical gaps as CapabilityGapItem dicts
            critical = [
                {
                    "capability": item.get("capability", ""),
                    "current_description": item.get("current", ""),
                    "recommended_description": item.get("recommended", ""),
                }
                for item in data.get("critical_gaps", [])
            ]

            return {
                "critical": critical,
                "clarity_issues": data.get("clarity_issues", []),
                "recommendations": critical,
            }

        except Exception as exc:
            logger.error(f"Failed to analyze capability clarity: {exc}")
            return {
                "critical": [],
                "clarity_issues": ["Some requirements may lack clarity"],
                "recommendations": [],
            }

    async def _analyze_requirement_creep(self, jd_requirements: dict) -> dict:
        """Analyze for requirement creep (asking for too much).

        Returns:
            Dict with difficulty_score, experience_assessment, warnings
        """
        logger.debug("Analyzing requirement creep")

        prompt = f"""Analyze if this JD has requirement creep (asking for too much).

Required skills: {jd_requirements.get('requirements', [])}
Tech stack: {jd_requirements.get('tech_stack', [])}
Experience level: {jd_requirements.get('experience_level', 'mid')}

Assess:
1. Is the experience requirement realistic? (1-10 years)
2. Is the tech stack too broad?
3. Are there unrealistic combinations?

Return JSON:
{{
  "difficulty_score": <0-100>,
  "experience_assessment": "...",
  "tech_balance_assessment": "...",
  "warnings": [
    {{"severity": "high/medium/low", "issue": "...", "suggestion": "..."}}
  ]
}}"""

        try:
            result_text = self.claude_client.analyze(prompt, temperature=0.3)

            # Extract JSON
            if "```json" in result_text:
                json_str = result_text.split("```json")[1].split("```")[0].strip()
            else:
                json_str = result_text.split("```")[1].split("```")[0].strip() if "```" in result_text else result_text

            data = json.loads(json_str)

            return {
                "difficulty_score": int(data.get("difficulty_score", 50)),
                "experience_assessment": data.get("experience_assessment", "Realistic experience requirement"),
                "tech_balance": data.get("tech_balance_assessment", "Balanced tech stack"),
                "warnings": data.get("warnings", []),
            }

        except Exception as exc:
            logger.error(f"Failed to analyze requirement creep: {exc}")
            # Calculate basic difficulty based on tech stack size
            tech_count = len(jd_requirements.get('tech_stack', []))
            difficulty = min(90, 40 + (tech_count * 10))

            return {
                "difficulty_score": difficulty,
                "experience_assessment": "Requirements appear reasonable for the seniority level",
                "tech_balance": f"JD specifies {tech_count} technologies in the tech stack",
                "warnings": [],
            }

    async def _test_archetype_fit(self, jd_requirements: dict) -> dict:
        """Test JD against candidate archetypes (junior/mid/senior/lead).

        Returns:
            Dict mapping archetype name to fit score
        """
        logger.debug("Testing archetype fit")

        # Get system archetypes grouped by role level
        stmt = select(CandidateArchetype).where(CandidateArchetype.is_system.is_(True))
        archetypes = (await self.db.scalars(stmt)).all()

        # Group by role level and get the best example of each
        archetype_by_level = {}
        for archetype in archetypes:
            level = archetype.role_level.value
            if level not in archetype_by_level:
                archetype_by_level[level] = archetype

        fits = {}
        for level, archetype in archetype_by_level.items():
            try:
                score_data = await self._score_archetype_fit(archetype, jd_requirements)
                fits[level] = score_data
            except Exception as exc:
                logger.warning(f"Error scoring archetype {level}: {exc}")
                fits[level] = {
                    "archetype": archetype.role_title,
                    "fit_score": 50,
                    "matched_capabilities": [],
                    "missing_capabilities": [],
                }

        return fits

    async def _score_archetype_fit(
        self,
        archetype: CandidateArchetype,
        jd_requirements: dict,
    ) -> dict:
        """Score how well JD matches a specific archetype.

        Returns:
            Dict with fit_score, matched_capabilities, missing_capabilities
        """
        logger.debug(f"Scoring archetype fit for {archetype.role_title}")

        prompt = f"""Score how well this JD matches the {archetype.role_title} archetype.

Archetype profile:
- Years experience: {archetype.typical_profile.get('years_experience', 0)}
- Key skills: {archetype.typical_profile.get('key_capabilities', [])}
- Tech stack: {archetype.typical_profile.get('preferred_tech_stack', [])}

JD requirements:
- Skills needed: {jd_requirements.get('requirements', [])}
- Tech stack: {jd_requirements.get('tech_stack', [])}
- Experience: {jd_requirements.get('experience_level', '')}

Return JSON:
{{
  "fit_score": <0-100>,
  "matched_capabilities": [...],
  "missing_capabilities": [...],
  "notes": "..."
}}"""

        try:
            result_text = self.claude_client.analyze(prompt, temperature=0.3)

            # Extract JSON
            if "```json" in result_text:
                json_str = result_text.split("```json")[1].split("```")[0].strip()
            else:
                json_str = result_text.split("```")[1].split("```")[0].strip() if "```" in result_text else result_text

            data = json.loads(json_str)

            return {
                "archetype": archetype.role_title,
                "fit_score": int(data.get("fit_score", 50)),
                "matched_capabilities": data.get("matched_capabilities", []),
                "missing_capabilities": data.get("missing_capabilities", []),
            }

        except Exception as exc:
            logger.warning(f"Error scoring archetype: {exc}")
            # Calculate basic score based on skill overlap
            archetype_skills = set(archetype.typical_profile.get('key_capabilities', []))
            required_skills = set(jd_requirements.get('requirements', []))
            overlap = len(archetype_skills & required_skills)
            fit_score = min(100, 30 + (overlap * 10))

            return {
                "archetype": archetype.role_title,
                "fit_score": fit_score,
                "matched_capabilities": list(archetype_skills & required_skills)[:5],
                "missing_capabilities": list(required_skills - archetype_skills)[:5],
            }

    async def _assess_jd_quality(self, jd_requirements: dict) -> dict:
        """Assess overall JD quality and completeness.

        Returns:
            Dict with score, missing_sections, issues
        """
        logger.debug("Assessing JD quality")

        prompt = f"""Assess the quality and completeness of this JD.

JD includes:
- Title: present
- Requirements: {len(jd_requirements.get('requirements', []))} items
- Tech stack: {len(jd_requirements.get('tech_stack', []))} items
- Responsibilities: {len(jd_requirements.get('responsibilities', []))} items
- Experience level: {jd_requirements.get('experience_level', 'not specified')}

Check for:
1. Completeness (missing sections like benefits, culture, compensation)
2. Clarity (vague language like "strong communication")
3. Realism (expectations aligned with role level)

Return JSON:
{{
  "quality_score": <0-100>,
  "missing_sections": [...],
  "clarity_issues": [...],
  "realism_issues": [...]
}}"""

        try:
            result_text = self.claude_client.analyze(prompt, temperature=0.3)

            # Extract JSON
            if "```json" in result_text:
                json_str = result_text.split("```json")[1].split("```")[0].strip()
            else:
                json_str = result_text.split("```")[1].split("```")[0].strip() if "```" in result_text else result_text

            data = json.loads(json_str)

            all_issues = (
                data.get("clarity_issues", []) +
                data.get("realism_issues", [])
            )

            return {
                "score": int(data.get("quality_score", 70)),
                "missing_sections": data.get("missing_sections", []),
                "issues": all_issues,
            }

        except Exception as exc:
            logger.error(f"Failed to assess JD quality: {exc}")
            # Calculate basic score
            completeness = 20  # Base
            completeness += min(50, len(jd_requirements.get('requirements', [])) * 3)
            completeness += min(20, len(jd_requirements.get('tech_stack', [])) * 5)

            return {
                "score": completeness,
                "missing_sections": ["Compensation details", "Culture description"],
                "issues": ["Ensure all requirements are clear and specific"],
            }

    async def _generate_wording_suggestions(
        self,
        jd_requirements: dict,
        original_jd_text: str,
    ) -> dict:
        """Generate wording and phrasing suggestions for JD.

        Returns:
            Dict with improved titles, descriptions, phrasings
        """
        logger.debug("Generating wording suggestions")

        prompt = f"""Generate wording improvements for this JD to make it more attractive and clear.

Current JD excerpt: {original_jd_text[:500]}
Requirements: {jd_requirements.get('requirements', [])}

Suggest:
1. Alternative job titles (2-3 variations)
2. Improved role description (more compelling)
3. Better phrasing for vague requirements
4. Benefits language to include
5. Culture fit language

Return JSON:
{{
  "title_variations": [...],
  "improved_description": "...",
  "capability_suggestions": [
    {{"area": "skill", "current": "vague phrasing", "suggested": "specific phrasing", "reasoning": "..."}}
  ],
  "benefits_suggestions": [...],
  "culture_fit_language": "..."
}}"""

        try:
            result_text = self.claude_client.analyze(prompt, temperature=0.4)

            # Extract JSON
            if "```json" in result_text:
                json_str = result_text.split("```json")[1].split("```")[0].strip()
            else:
                json_str = result_text.split("```")[1].split("```")[0].strip() if "```" in result_text else result_text

            data = json.loads(json_str)

            # Format capability suggestions as WordingSuggestion dicts
            wording_sugg = [
                {
                    "capability_area": item.get("area", ""),
                    "current_phrasing": item.get("current", ""),
                    "suggested_alternatives": [item.get("suggested", "")],
                    "reasoning": item.get("reasoning", ""),
                }
                for item in data.get("capability_suggestions", [])
            ]

            return {
                "title_variations": data.get("title_variations", []),
                "improved_description": data.get("improved_description", ""),
                "capability_suggestions": wording_sugg,
                "benefits": data.get("benefits_suggestions", []),
                "culture_fit": data.get("culture_fit_language", ""),
            }

        except Exception as exc:
            logger.error(f"Failed to generate wording suggestions: {exc}")
            return {
                "title_variations": ["Senior " + jd_requirements.get('experience_level', 'Engineer')],
                "improved_description": "Lead " + jd_requirements.get('experience_level', 'role'),
                "capability_suggestions": [],
                "benefits": ["Competitive salary", "Health benefits", "Professional development"],
                "culture_fit": "Join a team focused on innovation and collaboration",
            }

    async def _assess_market_standards(self, jd_requirements: dict) -> dict:
        """Assess how JD compares to market standards.

        Returns:
            Dict with positioning and comparison notes
        """
        logger.debug("Assessing market standards")

        prompt = f"""Compare this JD to market standards for similar roles.

Requirements: {jd_requirements.get('requirements', [])}
Experience: {jd_requirements.get('experience_level', 'mid')}
Tech stack: {jd_requirements.get('tech_stack', [])}

Assess:
1. Are requirements above/below market average?
2. How does compensation positioning typically compare?
3. Are benefits aligned with market standards?

Provide 2-3 sentences on market positioning."""

        try:
            result = self.claude_client.analyze(prompt, temperature=0.3)
            return {"positioning": result.strip()}
        except Exception as exc:
            logger.error(f"Failed to assess market standards: {exc}")
            return {
                "positioning": "This JD appears to have market-aligned requirements for the experience level specified."
            }

    def _get_best_archetype(self, fit_by_archetype: dict) -> Optional[str]:
        """Determine which archetype has best fit.

        Returns:
            Name of best-fitting archetype or None
        """
        if not fit_by_archetype:
            return None

        best_archetype = None
        best_score = -1

        for archetype_name, fit_data in fit_by_archetype.items():
            if isinstance(fit_data, dict):
                score = fit_data.get("fit_score", 0)
            else:
                score = fit_data

            if score > best_score:
                best_score = score
                best_archetype = archetype_name

        return best_archetype

    def _estimate_talent_pool(self, archetype_fits: dict) -> str:
        """Estimate total talent pool that could fit this JD.

        Returns:
            Text description of estimated pool size
        """
        if not archetype_fits:
            return "Unable to estimate talent pool"

        # Average fit score across archetypes
        scores = []
        for fit_data in archetype_fits.values():
            if isinstance(fit_data, dict):
                scores.append(fit_data.get("fit_score", 0))
            else:
                scores.append(fit_data)

        avg_score = sum(scores) / len(scores) if scores else 50

        # Estimate based on score
        if avg_score >= 80:
            estimate = "200-500+ qualified candidates"
        elif avg_score >= 60:
            estimate = "100-200 qualified candidates"
        elif avg_score >= 40:
            estimate = "50-100 qualified candidates"
        else:
            estimate = "20-50 qualified candidates (highly specialized)"

        return f"Could find {estimate} matching this JD profile"


async def simulate_job_description(
    db: AsyncSession,
    claude_client: ClaudeClient,
    request: JDSimulationRequest,
) -> JDSimulationResult:
    """Top-level function to simulate a job description.

    This is called by the task queue worker.
    """
    engine = JDSimulationEngine(db, claude_client)
    return await engine.simulate_jd(request)
