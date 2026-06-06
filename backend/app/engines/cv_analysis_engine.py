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
from app.engines.intake import parse_resume, analyze_jd
from app.engines.semantic_match import semantic_score
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
            enriched = await self.claude_client.analyze(prompt, temperature=0.2)

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
        """Identify skill gaps and weakness areas with detailed analysis.

        Returns:
            Dict with missing_capabilities, weakness_areas, strength_summary
        """
        logger.debug("Analyzing capability gaps with deep analysis")

        candidate_skills = set(candidate_capabilities.get("skills", []))
        required_skills = set(target_expectations.get("required_skills", []))
        nice_to_have = set(target_expectations.get("nice_to_have_skills", []))

        # Calculate gaps
        missing_from_required = required_skills - candidate_skills
        missing_from_nice = nice_to_have - candidate_skills

        prompt = f"""Perform a detailed gap analysis between a candidate and a {target_expectations.get('typical_years_experience', 3)}-year {target_expectations.get('title', 'target role')}.

CANDIDATE PROFILE:
- Technical Skills: {candidate_capabilities.get('technical_skills', candidate_skills)}
- Domain Expertise: {candidate_capabilities.get('domain_expertise', [])}
- Leadership Experience: {candidate_capabilities.get('leadership_experience', [])}
- Key Achievements: {candidate_capabilities.get('key_achievements', [])}
- Years Experience: {candidate_capabilities.get('years_experience', 0)}
- Soft Skills: {candidate_capabilities.get('soft_skills', [])}

TARGET ROLE REQUIREMENTS:
- Required Skills: {list(required_skills)}
- Nice-to-Have Skills: {list(nice_to_have)}
- Key Competencies: {target_expectations.get('key_competencies', [])}

Analyze and provide JSON with:
1. missing_critical: Required skills they lack - for EACH, explain why it matters for this role and specific learning path
2. weakness_areas: Skills they have but are below target level - explain gaps and development timeline
3. strengths: Detailed 3-4 sentence analysis of their strongest areas relative to this role
4. readiness_assessment: Overall assessment of readiness for role (0-100 score)
5. transition_path: Specific 6-12 month path to close gaps

Format:
{{
  "missing_critical": [
    {{"capability": "X", "importance": "high/medium", "description": "detailed context", "why_for_role": "specific to role", "how_to_improve": "specific learning path", "timeline_months": 3}}
  ],
  "weakness_areas": [...],
  "strengths": "...",
  "readiness_assessment": 70,
  "transition_path": "..."
}}"""

        try:
            result_text = await self.claude_client.analyze(prompt, temperature=0.2)

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
                    "description": f"Missing required skill for this role",
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
                analysis_prompt = f"""Analyze fit between candidate and position. Be specific and detailed.

CANDIDATE:
- Technical Skills: {candidate_capabilities.get('technical_skills', [])}
- Domain Expertise: {candidate_capabilities.get('domain_expertise', [])}
- Leadership: {candidate_capabilities.get('leadership_experience', [])}
- Achievements: {candidate_capabilities.get('key_achievements', [])}
- Years Experience: {candidate_capabilities.get('years_experience', 0)}

POSITION:
- Title: {position.title}
- Description: {position.description or 'No description'}
- Seniority: {target_seniority}

Provide JSON with:
- match_score: 0-100 based on skill alignment and experience
- why_fit: 3-4 specific reasons they ARE a good fit (concrete examples from their background)
- why_not_fit: 2-3 specific gaps or concerns (concrete)
- aligned_capabilities: 3-5 of their skills that match this role
- missing_for_role: 2-3 skills needed for this role
- growth_potential: Will this role help them grow toward their goals? How?

{{
  "match_score": 75,
  "why_fit": "...",
  "why_not_fit": "...",
  "aligned_capabilities": [...],
  "missing_for_role": [...],
  "growth_potential": "..."
}}"""

                result_text = await self.claude_client.analyze(analysis_prompt, temperature=0.2)

                # Extract JSON
                if "```json" in result_text:
                    json_str = result_text.split("```json")[1].split("```")[0].strip()
                else:
                    json_str = result_text.split("```")[1].split("```")[0].strip() if "```" in result_text else result_text

                analysis = json.loads(json_str)

                # Semantic score for additional signal
                semantic_score = 70
                try:
                    if position.description:
                        result = semantic_score(
                            candidate_capabilities.get("raw_narrative", ""),
                            position.description
                        )
                        semantic_score = result.get("combined_score", 70)
                except Exception as e:
                    logger.debug(f"Semantic scoring failed for position {position.id}: {e}")

                # Blend LLM analysis with semantic score
                match_score = analysis.get("match_score", 65)
                final_score = int(match_score * 0.6 + semantic_score * 0.4)

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

        prompt = f"""Generate specific, detailed CV improvement suggestions targeting a {target_role} role.

CURRENT CV:
{candidate_capabilities.get('raw_narrative', '')}

CANDIDATE PROFILE:
- Current Skills: {candidate_capabilities.get('technical_skills', [])}
- Key Achievements: {candidate_capabilities.get('key_achievements', [])}
- Years Experience: {candidate_capabilities.get('years_experience', 0)}

TARGET ROLE REQUIREMENTS:
- Required Skills: {target_expectations.get('required_skills', [])}
- Key Competencies: {target_expectations.get('key_competencies', [])}
- Growth Areas in Role: {target_expectations.get('growth_areas', [])}

Provide detailed JSON with 8-10 actionable suggestions in categories:
1. skills_to_highlight: Emphasize existing skills relevant to role
2. skills_to_add: Skills to add/develop
3. keywords_missing: Industry keywords to incorporate
4. achievement_reframing: How to reword achievements for more impact
5. structure_improvements: CV format/organization improvements

For EACH suggestion provide:
- category: one of above
- suggestion: What to change
- priority: high/medium/low
- current_example: What they currently have (if applicable)
- suggested_example: How to improve it with SPECIFIC example
- why_it_matters: Why this helps for the target role

{{
  "suggestions": [
    {{
      "category": "skills_to_highlight",
      "suggestion": "Emphasize architecture experience",
      "priority": "high",
      "current_example": "Designed system architecture",
      "suggested_example": "Designed and implemented microservices architecture supporting 50k+ daily active users, improving system latency by 40%",
      "why_it_matters": "Target role values architects who can demonstrate impact at scale"
    }},
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

        prompt = f"""Analyze the career trajectory from this resume:

RESUME:
{capabilities.get('raw_narrative', '')}

PROFILE SUMMARY:
- Years Experience: {capabilities.get('years_experience', 0)}
- Technical Skills: {capabilities.get('technical_skills', [])}
- Domain Expertise: {capabilities.get('domain_expertise', [])}
- Leadership Experience: {capabilities.get('leadership_experience', [])}
- Key Achievements: {capabilities.get('key_achievements', [])}

Provide a detailed 4-6 sentence analysis covering:
1. Career progression pattern and growth trajectory
2. Stability, role progression, and advancement
3. Notable transitions, shifts, or specializations
4. Overall career arc and maturity level
5. Readiness for next-level roles

Be specific to their actual background, not generic."""

        try:
            result = await self.claude_client.analyze(prompt, temperature=0.2)
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

        prompt = f"""Provide a detailed market assessment for this candidate targeting a {target_seniority} {target_role} role.

CANDIDATE PROFILE:
- Years of Experience: {capabilities.get('years_experience', 0)}
- Technical Skills: {capabilities.get('technical_skills', [])}
- Domain Expertise: {capabilities.get('domain_expertise', [])}
- Leadership: {capabilities.get('leadership_experience', [])}
- Soft Skills: {capabilities.get('soft_skills', [])}
- Key Achievements: {capabilities.get('key_achievements', [])}

Provide a detailed 5-7 sentence market assessment covering:
1. How they stack up against typical {target_seniority} level in market
2. Relative strengths (what makes them above-market)
3. Relative weaknesses or gaps vs market averages
4. Unique differentiators or unique strengths
5. Competitive positioning for this role type
6. Salary/opportunity range they should target
7. Which company types/industries would value them most

Be specific, comparative, and actionable."""

        try:
            result = await self.claude_client.analyze(prompt, temperature=0.2)
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
    ) -> list[str]:
        """Identify strategic growth opportunities aligned with career goals.

        Returns:
            List of growth opportunity descriptions
        """
        logger.debug("Identifying strategic growth opportunities")

        focus_text = f"Candidate's career focus areas: {', '.join(career_focus_areas)}\n" if career_focus_areas else ""

        prompt = f"""Identify 5-7 strategic growth opportunities specific to this candidate's profile and goals.

CURRENT PROFILE:
- Technical Skills: {capabilities.get('technical_skills', [])}
- Domain Expertise: {capabilities.get('domain_expertise', [])}
- Leadership: {capabilities.get('leadership_experience', [])}
- Years Experience: {capabilities.get('years_experience', 0)}

TARGET ROLE CONTEXT:
- Required Skills: {target_expectations.get('required_skills', [])}
- Growth Areas in Role: {target_expectations.get('growth_areas', [])}
- Key Competencies: {target_expectations.get('key_competencies', [])}

{focus_text}

For EACH opportunity (returned as numbered list), explain:
1. What specific skill/knowledge to develop
2. Why it matters for their target role and career
3. Concrete first steps or learning path
4. Expected timeline
5. How it opens new doors/opportunities

Make recommendations specific to their actual background and goals, not generic.

Return as numbered list like:
1. [opportunity title]: [2-3 sentence explanation with why + timeline + impact]
2. [opportunity title]: ...

Focus on depth, specificity, and actionability."""

        try:
            result_text = await self.claude_client.analyze(prompt, temperature=0.2)

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
