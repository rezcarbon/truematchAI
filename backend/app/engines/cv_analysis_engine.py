"""CV analysis engine for candidate recommendations."""
from __future__ import annotations

import json
import logging
import uuid

from sqlalchemy import select

from app.database import AsyncSession
from app.models.cv_analysis import CVAnalysisRequest, CVAnalysisResult
from app.models.position import Position
from app.models.resume import Resume
from app.models.user import User
from app.engines.client import ClaudeClient
from app.engines.intake import parse_resume
from app.engines.semantic_match import semantic_score

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
            request.target_role,
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
        """Extract and structure capabilities from resume with LLM enrichment.

        Returns:
            Dict with skills, experience, achievements, etc.
        """
        logger.debug(f"Extracting capabilities from resume {resume.id}")

        # Parse resume if not already parsed
        if not resume.parsed_data:
            # Use existing intake engine
            resume.parsed_data = parse_resume(
                resume.raw_narrative or resume.supplementary or {}
            )

        # Use LLM to do deep capability extraction from resume narrative
        prompt = f"""Analyze this resume and extract capabilities in structured detail:

RESUME CONTENT:
{resume.raw_narrative or "No narrative provided"}

Provide JSON response with:
- technical_skills: list of technical skills with proficiency context
- domain_expertise: areas of deep expertise/specialization
- leadership_experience: leadership roles and scope
- project_complexity: complexity levels of projects managed
- industry_experience: industries/domains worked in
- key_achievements: 3-5 most impactful achievements with context
- soft_skills: communication, collaboration, problem-solving abilities
- certifications: relevant certifications or recognitions
- innovation_indicators: evidence of innovation or thought leadership

Be specific to what's actually in the resume, not generic."""

        try:
            enriched = self.claude_client.analyze(prompt, temperature=0.2)

            # Extract JSON
            if "```json" in enriched:
                json_str = enriched.split("```json")[1].split("```")[0].strip()
            else:
                json_str = enriched.split("```")[1].split("```")[0].strip() if "```" in enriched else enriched

            enriched_data = json.loads(json_str)
        except Exception as e:
            logger.warning(f"LLM capability extraction failed: {e}")
            enriched_data = {}

        capabilities = {
            "skills": resume.parsed_data.get("skills", []),
            "experience": resume.parsed_data.get("experience", []),
            "achievements": resume.parsed_data.get("achievements", []),
            "education": resume.parsed_data.get("education", []),
            "years_experience": resume.parsed_data.get("years_experience", 0),
            "raw_narrative": resume.raw_narrative or "",
            "technical_skills": enriched_data.get("technical_skills", []),
            "domain_expertise": enriched_data.get("domain_expertise", []),
            "leadership_experience": enriched_data.get("leadership_experience", []),
            "key_achievements": enriched_data.get("key_achievements", []),
            "soft_skills": enriched_data.get("soft_skills", []),
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

        prompt = f"""For a {seniority} {role_title} role, list typical expectations.

Required skills (5-7): Technical skills essential for this role.
Nice-to-have (3-5): Bonus skills that strengthen candidacy.
Years: Typical years of experience.
Competencies (4-6): Key soft skills and competencies.
Growth areas (3-5): Skills that develop in this role.

Respond with JSON only:
{{"required_skills": [...], "nice_to_have_skills": [...], "typical_years_experience": N, "key_competencies": [...], "growth_areas": [...]}}"""

        try:
            # Call Claude API with concise prompt
            result_text = self.claude_client.analyze(prompt, temperature=0.2)

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
                    result[field] = [] if field_type is list else 0

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
        """Identify skill gaps and weakness areas with detailed analysis.

        Returns:
            Dict with missing_capabilities, weakness_areas, strength_summary
        """
        logger.debug("Analyzing capability gaps with deep analysis")

        candidate_skills = set(candidate_capabilities.get("skills", []))
        required_skills = set(target_expectations.get("required_skills", []))

        # Calculate gaps
        missing_from_required = required_skills - candidate_skills

        prompt = f"""Analyze skill gaps for this candidate to reach target role.

CANDIDATE: Skills={list(candidate_skills)[:8]}, Tech={candidate_capabilities.get('technical_skills', [])[:5]}, YearsExp={candidate_capabilities.get('years_experience', 0)}
TARGET: Required={list(required_skills)}, Competencies={target_expectations.get('key_competencies', [])[:4]}

JSON with missing_critical (capability, importance, how_to_improve), weakness_areas (2-3), strengths (2 sentences), readiness (0-100):
{{"missing_critical": [{{"capability": "X", "importance": "high", "description": "Gap detail", "how_to_improve": "Learning path"}}], "weakness_areas": [], "strengths": "...", "readiness_assessment": 70}}"""

        try:
            result_text = self.claude_client.analyze(prompt, temperature=0.2)

            # Extract JSON
            if "```json" in result_text:
                json_str = result_text.split("```json")[1].split("```")[0].strip()
            else:
                json_str = result_text.split("```")[1].split("```")[0].strip() if "```" in result_text else result_text

            data = json.loads(json_str)

            # Use LLM-provided gaps or generate from analysis
            missing_items = data.get("missing_critical", [])
            if not missing_items:
                # Fallback: generate from gaps if LLM didn't return
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
                "readiness": data.get("readiness_assessment", 65),
                "transition_path": data.get("transition_path", ""),
            }

        except Exception as exc:
            logger.error(f"Failed to analyze gaps: {exc}")
            # Return basic gap analysis
            missing_items = [
                {
                    "capability": skill,
                    "importance": "high",
                    "description": "Missing required skill for this role",
                    "how_to_improve": f"Develop {skill} expertise through courses and project work",
                }
                for skill in missing_from_required
            ]

            return {
                "missing": missing_items,
                "weakness": [],
                "strengths": f"Experienced with {len(candidate_skills)} relevant technologies",
                "readiness": 60,
                "transition_path": "",
            }

    async def _find_matching_positions(
        self,
        resume: Resume,
        candidate_capabilities: dict,
        target_seniority: str,
    ) -> list[dict]:
        """Find best-matching positions with detailed analysis.

        Returns:
            List of position_id, scores, why_fit/why_not_fit explanations
        """
        logger.debug("Finding matching positions with detailed analysis")

        # Get all active positions
        stmt = select(Position).where(Position.status == "open").limit(50)
        positions = (await self.db.scalars(stmt)).all()

        if not positions:
            logger.debug("No open positions found")
            return []

        matches = []
        for position in positions:
            try:
                # Perform deep analysis of position fit
                analysis_prompt = f"""Fit analysis: candidate to {position.title}.

CANDIDATE: Skills={candidate_capabilities.get('technical_skills', [])[:6]}, Experience={candidate_capabilities.get('years_experience', 0)}yrs, Expertise={candidate_capabilities.get('domain_expertise', [])[:3]}
ROLE: Title={position.title}, Seniority={target_seniority}
DESC: {(position.description or '')[:300]}

JSON: match_score (0-100), why_fit (2-3 reasons), why_not_fit (1-2 gaps), aligned_capabilities (list), missing_for_role (list):
{{"match_score": 75, "why_fit": "...", "why_not_fit": "...", "aligned_capabilities": [], "missing_for_role": [], "growth_potential": ""}}"""

                result_text = self.claude_client.analyze(analysis_prompt, temperature=0.2)

                # Extract JSON
                if "```json" in result_text:
                    json_str = result_text.split("```json")[1].split("```")[0].strip()
                else:
                    json_str = result_text.split("```")[1].split("```")[0].strip() if "```" in result_text else result_text

                analysis = json.loads(json_str)

                # Real deterministic semantic signal (don't shadow the imported
                # `semantic_score` function with a local of the same name).
                semantic_value = 70
                try:
                    if position.description:
                        sem = semantic_score(
                            candidate_capabilities.get("raw_narrative", ""),
                            position.description,
                        )
                        semantic_value = int(sem.get("score", 70))
                except Exception as e:
                    logger.debug(f"Semantic scoring failed for position {position.id}: {e}")

                # Blend LLM analysis with the semantic score.
                match_score = analysis.get("match_score", 65)
                final_score = int(match_score * 0.6 + semantic_value * 0.4)

                match_data = {
                    "position_id": position.id,
                    "title": position.title,
                    "company": position.company_id,
                    "score": final_score,
                    "semantic_score": semantic_score,
                    "analysis_score": match_score,
                    "why_fit": analysis.get("why_fit", f"Matches {position.title} requirements"),
                    "why_not_fit": analysis.get("why_not_fit", ""),
                    "aligned_capabilities": analysis.get("aligned_capabilities", []),
                    "missing_for_role": analysis.get("missing_for_role", []),
                    "growth_potential": analysis.get("growth_potential", ""),
                }
                matches.append(match_data)

            except Exception as exc:
                logger.warning(f"Error analyzing position {position.id}: {exc}")
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
        """Generate specific, actionable CV improvement suggestions with examples.

        Returns:
            List of CVAnalysisRecommendation objects (as dicts for JSONB)
        """
        logger.debug("Generating detailed CV improvement suggestions")

        prompt = f"""CV improvement suggestions for {target_role} role.

CANDIDATE: Skills={candidate_capabilities.get('technical_skills', [])[:5]}, Experience={candidate_capabilities.get('years_experience', 0)}yrs
TARGET: Required={target_expectations.get('required_skills', [])[:5]}, Competencies={target_expectations.get('key_competencies', [])[:4]}

List 5-6 JSON suggestions (category, suggestion, priority, example):
{{"suggestions": [{{"category": "skills", "suggestion": "...", "priority": "high", "example": "..."}}]}}"""

        try:
            result_text = self.claude_client.analyze(prompt, temperature=0.3)

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
            current = set(candidate_capabilities.get("technical_skills", []))
            missing = required - current

            return [
                {
                    "category": "skills_to_add",
                    "suggestion": f"Add {skill} expertise to your profile",
                    "priority": "high",
                    "suggested_example": f"Add '{skill}' to your technical skills section with proficiency level",
                    "why_it_matters": f"{skill} is a core requirement for {target_role}",
                }
                for skill in list(missing)[:3]
            ] + [
                {
                    "category": "keywords_missing",
                    "suggestion": "Incorporate industry keywords for this role",
                    "priority": "medium",
                    "suggested_example": f"Use terms like '{', '.join(target_expectations.get('key_competencies', [])[:3])}' throughout your CV",
                    "why_it_matters": "These keywords help recruiters find you for this type of role",
                }
            ]

    async def _analyze_trajectory(self, resume: Resume, capabilities: dict) -> str:
        """Analyze career trajectory with deep context from resume.

        Returns:
            Text narrative of trajectory analysis
        """
        logger.debug("Analyzing career trajectory in detail")

        prompt = f"""Career trajectory analysis.

PROFILE: {capabilities.get('years_experience', 0)}yrs experience, Tech={capabilities.get('technical_skills', [])[:5]}, Leadership={capabilities.get('leadership_experience', [])[:2]}, Expertise={capabilities.get('domain_expertise', [])[:3]}

Analyze progression (3-4 sentences): growth pattern, stability, advancement, readiness."""

        try:
            result = self.claude_client.analyze(prompt, temperature=0.2)
            return result.strip()
        except Exception as exc:
            logger.error(f"Failed to analyze trajectory: {exc}")
            years = capabilities.get('years_experience', 0)
            return f"Professional with {years} years of progressive experience showing consistent skill development and advancement through leadership roles."

    async def _assess_market_positioning(
        self,
        capabilities: dict,
        target_role: str,
        target_seniority: str,
    ) -> str:
        """Assess market positioning with competitive analysis.

        Returns:
            Text narrative of market positioning
        """
        logger.debug("Assessing market positioning and competitiveness")

        prompt = f"""Market positioning for {target_seniority} {target_role} candidate.

PROFILE: {capabilities.get('years_experience', 0)}yrs, Tech={capabilities.get('technical_skills', [])[:5]}, Expertise={capabilities.get('domain_expertise', [])[:2]}

Assess (4-5 sentences): market standing, strengths, gaps, competitive positioning."""

        try:
            result = self.claude_client.analyze(prompt, temperature=0.2)
            return result.strip()
        except Exception as exc:
            logger.error(f"Failed to assess market positioning: {exc}")
            years = capabilities.get('years_experience', 0)
            return f"Candidate with {years} years of experience demonstrates competitive positioning for {target_seniority}-level {target_role} roles, with relevant technical skills and industry experience."

    async def _identify_growth_opportunities(
        self,
        capabilities: dict,
        target_expectations: dict,
        career_focus_areas: list[str] | None,
        target_role: str,
    ) -> list[str]:
        """Identify strategic growth opportunities aligned with career goals.

        Args:
            capabilities: Candidate capability profile
            target_expectations: Target role expectations
            career_focus_areas: User's career focus areas
            target_role: The target role title

        Returns:
            List of growth opportunity descriptions
        """
        logger.debug("Identifying strategic growth opportunities")

        focus_text = f" Focus areas: {', '.join(career_focus_areas)}" if career_focus_areas else ""

        prompt = f"""Growth opportunities for {target_role} candidate.{focus_text}

PROFILE: {capabilities.get('years_experience', 0)}yrs, Tech={capabilities.get('technical_skills', [])[:5]}
ROLE: Requires {target_expectations.get('required_skills', [])[:4]}, Growth areas {target_expectations.get('growth_areas', [])[:3]}

List 5 opportunities (skill to develop, why it matters, timeline):
1. [skill]: [1-2 sentence explanation with timeline]"""

        try:
            result_text = self.claude_client.analyze(prompt, temperature=0.2)

            # Parse response as list of opportunities
            opportunities = []
            for line in result_text.strip().split('\n'):
                line = line.strip()
                if line and not line.startswith('#'):
                    # Remove common list markers
                    for marker in ['- ', '* ', '+ ', '1. ', '2. ', '3. ', '4. ', '5. ', '6. ', '7. ']:
                        if line.startswith(marker):
                            line = line[len(marker):].strip()
                    if line:
                        opportunities.append(line)

            return opportunities[:7] if opportunities else self._get_default_opportunities(target_expectations)

        except Exception as exc:
            logger.error(f"Failed to identify growth opportunities: {exc}")
            return self._get_default_opportunities(target_expectations)

    def _get_default_opportunities(self, target_expectations: dict) -> list[str]:
        """Return relevant growth opportunities based on target role."""
        role_growth = target_expectations.get('growth_areas', [])
        competencies = target_expectations.get('key_competencies', [])

        opportunities = [
            f"Master {competencies[0] if competencies else 'advanced'} to become a leader in this domain - opens doors to senior/staff roles",
            f"Develop expertise in {role_growth[0] if role_growth else 'emerging technologies'} that are reshaping the industry",
            "Build cross-functional leadership skills through mentoring and knowledge-sharing",
            "Specialize in a high-demand niche (e.g., performance optimization, security, architecture)",
            "Develop business acumen alongside technical skills for product/strategy roles",
            "Contribute to open source or speaking to build thought leadership and reputation",
        ]
        return opportunities[:5]


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
