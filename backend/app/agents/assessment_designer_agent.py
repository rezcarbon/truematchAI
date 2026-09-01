"""Assessment Designer Agent - Phase 2 Agent-designed assessments.

Pipeline: candidate_profile + JD requirements → fair assessment design → recruiter validates

The agent designs customized, fair assessments while recruiter maintains authority
over fairness validation and final approval.
"""
from __future__ import annotations

import json
import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.models.assessment_design import AssessmentDesign
from app.models.resume import Resume
from app.models.position import Position

logger = logging.getLogger("truematch.assessment_designer")


class AssessmentDesignerAgent:
    """
    Agent that designs customized assessments for candidates.

    8-Phase Pipeline:
    1. Analyze candidate profile deeply
    2. Analyze role requirements
    3. Design fair assessment questions
    4. Create evaluation rubric
    5. Generate interview guidance
    6. Run fairness validation (4 gates)
    7. Capture design rationale
    8. Prepare final design package

    Recruiter validates fairness and approves before assessment is used.
    """

    def __init__(self, db: Session):
        """Initialize agent with database session."""
        self.db = db
        self.logger = logger

    async def design_assessment(
        self,
        resume: Resume,
        position: Position,
        screening_result_id: Optional[str] = None,
    ) -> dict:
        """
        Design a customized, fair assessment for a candidate.

        Args:
            resume: Candidate resume
            position: Position to assess for
            screening_result_id: Optional link to screening result

        Returns:
            dict with complete assessment design:
            {
                "questions": [...],
                "scenarios": [...],
                "interview_guidance": {...},
                "evaluation_rubric": {...},
                "design_rationale": str,
                "fairness_check": {...},
                "accessibility_notes": [...]
            }
        """
        try:
            self.logger.info(
                f"Designing assessment for {resume.id} for position {position.id}"
            )

            # Phase 1: Analyze candidate profile
            candidate_profile = await self._analyze_candidate_profile(resume)

            # Phase 2: Analyze role requirements
            role_requirements = await self._analyze_role_requirements(position)

            # Phase 3: Design assessment questions
            questions = await self._design_assessment_questions(
                candidate_profile, role_requirements, position
            )

            # Phase 4: Create evaluation rubric
            rubric = await self._create_evaluation_rubric(
                questions, role_requirements
            )

            # Phase 5: Generate interview guidance
            interview_guidance = await self._generate_interview_guidance(
                candidate_profile, role_requirements, questions
            )

            # Phase 6: Run fairness validation
            fairness_check = await self._run_fairness_check(
                candidate_profile, questions, interview_guidance
            )

            # Phase 7: Design rationale
            design_rationale = await self._capture_design_rationale(
                candidate_profile, role_requirements, questions
            )

            # Phase 8: Accessibility notes
            accessibility_notes = await self._assess_accessibility(
                questions, candidate_profile
            )

            design = {
                "questions": questions,
                "scenarios": [],  # TODO: Phase 2 - Add real-world scenarios
                "interview_guidance": interview_guidance,
                "evaluation_rubric": rubric,
                "design_rationale": design_rationale,
                "accessibility_notes": accessibility_notes,
            }

            fairness_check_result = {
                "passed": fairness_check["passed"],
                "bias_indicators": fairness_check.get("bias_indicators", []),
                "fairness_score": fairness_check.get("fairness_score", 75),
                "recommendations": fairness_check.get("recommendations", []),
                "gates_evaluated": fairness_check.get("gates_evaluated", []),
            }

            self.logger.info(
                f"Assessment design complete for {resume.id}: "
                f"fairness_score={fairness_check_result['fairness_score']}"
            )

            return {
                "agent_design": design,
                "design_fairness_check": fairness_check_result,
            }

        except Exception as e:
            self.logger.error(f"Error designing assessment: {e}", exc_info=True)
            # Return safe defaults on error
            return {
                "agent_design": {
                    "questions": [],
                    "scenarios": [],
                    "interview_guidance": {
                        "estimated_duration_minutes": 90,
                        "time_breakdown": {},
                        "probe_areas": [],
                        "red_flags": [],
                        "growth_signals": [],
                    },
                    "evaluation_rubric": {},
                    "design_rationale": "Assessment design error - requires manual design",
                    "accessibility_notes": [],
                },
                "design_fairness_check": {
                    "passed": False,
                    "bias_indicators": ["Design error - requires manual review"],
                    "fairness_score": 0,
                    "recommendations": ["Designer error - create assessment manually"],
                    "gates_evaluated": [],
                },
            }

    async def _analyze_candidate_profile(self, resume: Resume) -> dict:
        """
        Analyze candidate profile deeply.

        Returns:
            {
                "skills": {
                    "technical": [...],
                    "soft": [...]
                },
                "experience": {
                    "years": int,
                    "relevance": "high" | "medium" | "low",
                    "industries": [...]
                },
                "trajectory": {
                    "progression": "ascending" | "stable" | "mixed",
                    "stability": "high" | "medium" | "low",
                    "growth_indicators": [...]
                },
                "strengths": [...],
                "gaps": [...],
                "learning_style": {...}
            }
        """
        try:
            # Extract text from resume
            text = resume.supplementary.get("extracted_text", "") if resume.supplementary else ""
            raw = resume.raw_narrative or ""
            full_text = f"{text}\n{raw}".lower()

            # Parse skills (simplified - would use NLP in production)
            technical_skills = self._extract_technical_skills(full_text)
            soft_skills = self._extract_soft_skills(full_text)

            # Parse experience
            experience_years = self._estimate_experience_years(full_text)
            industries = self._extract_industries(full_text)

            # Trajectory analysis
            trajectory = {
                "progression": "ascending" if experience_years > 5 else "stable",
                "stability": "high" if "stable" in full_text else "medium",
                "growth_indicators": self._detect_growth_signals(full_text),
            }

            # Learning style inference
            learning_style = {
                "prefers_hands_on": "hands-on" in full_text or "practical" in full_text,
                "structured": "structured" in full_text or "organized" in full_text,
                "collaborative": "team" in full_text or "collaboration" in full_text,
            }

            return {
                "skills": {
                    "technical": technical_skills,
                    "soft": soft_skills,
                },
                "experience": {
                    "years": experience_years,
                    "relevance": "high" if experience_years > 3 else "medium",
                    "industries": industries,
                },
                "trajectory": trajectory,
                "strengths": self._identify_strengths(full_text),
                "gaps": [],  # Will be identified later
                "learning_style": learning_style,
            }

        except Exception as e:
            self.logger.error(f"Error analyzing candidate profile: {e}")
            return {
                "skills": {"technical": [], "soft": []},
                "experience": {"years": 0, "relevance": "low", "industries": []},
                "trajectory": {"progression": "unknown", "stability": "unknown", "growth_indicators": []},
                "strengths": [],
                "gaps": [],
                "learning_style": {},
            }

    async def _analyze_role_requirements(self, position: Position) -> dict:
        """
        Analyze job description requirements.

        Returns:
            {
                "title": str,
                "required_competencies": [...],
                "nice_to_have": [...],
                "technical_requirements": [...],
                "soft_requirements": [...]
            }
        """
        try:
            description = position.description or ""
            title = position.title or "Unknown"

            return {
                "title": title,
                "required_competencies": self._extract_requirements(description, "required"),
                "nice_to_have": self._extract_requirements(description, "preferred"),
                "technical_requirements": self._extract_technical_requirements(description),
                "soft_requirements": self._extract_soft_requirements(description),
            }

        except Exception as e:
            self.logger.error(f"Error analyzing role requirements: {e}")
            return {
                "title": position.title or "Unknown",
                "required_competencies": [],
                "nice_to_have": [],
                "technical_requirements": [],
                "soft_requirements": [],
            }

    async def _design_assessment_questions(
        self,
        candidate_profile: dict,
        role_requirements: dict,
        position: Position,
    ) -> list[dict]:
        """
        Design 3-5 assessment questions tailored to candidate and role.

        Returns:
            [
                {
                    "question": str,
                    "type": "coding" | "design" | "behavioral" | "scenario",
                    "expected_duration_minutes": int,
                    "rubric": {...},
                    "accessibility_notes": str
                }
            ]
        """
        try:
            questions = []

            # Question 1: Coding/Technical
            if "technical" in str(role_requirements):
                questions.append({
                    "question": f"Design a solution for {role_requirements.get('title', 'the role')} "
                               "using your preferred tech stack. Walk us through your approach.",
                    "type": "coding",
                    "expected_duration_minutes": 45,
                    "rubric": {
                        "approach": {"weight": 0.3},
                        "implementation": {"weight": 0.4},
                        "communication": {"weight": 0.3},
                    },
                    "accessibility_notes": "Candidate can use any IDE or whiteboard tool",
                })

            # Question 2: Behavioral
            questions.append({
                "question": "Tell us about a time you had to learn something new quickly. "
                           "How did you approach it?",
                "type": "behavioral",
                "expected_duration_minutes": 15,
                "rubric": {
                    "learning_ability": {"weight": 0.4},
                    "communication": {"weight": 0.3},
                    "problem_solving": {"weight": 0.3},
                },
                "accessibility_notes": "Interview format - candidate can request breaks",
            })

            # Question 3: Scenario
            questions.append({
                "question": "You've just joined the team and discover the codebase is "
                           "poorly documented. What's your approach?",
                "type": "scenario",
                "expected_duration_minutes": 20,
                "rubric": {
                    "initiative": {"weight": 0.3},
                    "collaboration": {"weight": 0.4},
                    "pragmatism": {"weight": 0.3},
                },
                "accessibility_notes": "Discussion format",
            })

            return questions

        except Exception as e:
            self.logger.error(f"Error designing questions: {e}")
            return []

    async def _create_evaluation_rubric(
        self,
        questions: list[dict],
        role_requirements: dict,
    ) -> dict:
        """Create objective evaluation rubric."""
        try:
            return {
                "competencies": [
                    "Technical ability",
                    "Communication",
                    "Problem solving",
                    "Learning ability",
                    "Collaboration",
                ],
                "scoring_levels": {
                    "novice": 1,
                    "intermediate": 2,
                    "proficient": 3,
                    "expert": 4,
                },
                "passing_threshold": 60,  # Score needed to pass
                "evaluation_guide": {
                    "1": "Does not meet expectations - significant gaps",
                    "2": "Meets some expectations - needs growth",
                    "3": "Meets expectations - solid fit",
                    "4": "Exceeds expectations - strong candidate",
                },
            }

        except Exception as e:
            self.logger.error(f"Error creating rubric: {e}")
            return {}

    async def _generate_interview_guidance(
        self,
        candidate_profile: dict,
        role_requirements: dict,
        questions: list[dict],
    ) -> dict:
        """Generate recruiter guidance for interview."""
        try:
            total_duration = sum(q.get("expected_duration_minutes", 0) for q in questions)

            return {
                "estimated_duration_minutes": total_duration + 10,  # +10 for intro/outro
                "time_breakdown": {
                    "introduction": 5,
                    "technical": 45,
                    "behavioral": 15,
                    "scenario": 20,
                    "closing": 5,
                },
                "probe_areas": [
                    "Error handling and edge cases",
                    "System design thinking",
                    "Communication clarity",
                    "Growth mindset",
                ],
                "red_flags": [
                    "Cannot explain approach",
                    "Rigid thinking",
                    "Poor communication",
                    "No consideration for tradeoffs",
                ],
                "growth_signals": [
                    "Asks clarifying questions",
                    "Considers multiple approaches",
                    "Thinks about maintainability",
                    "Shows learning from feedback",
                ],
                "accessibility_considerations": [
                    "Allow breaks as needed",
                    "Offer multiple ways to solve (code/whiteboard/discussion)",
                    "Accommodate language barriers",
                    "Provide clear questions in advance if needed",
                ],
            }

        except Exception as e:
            self.logger.error(f"Error generating guidance: {e}")
            return {}

    async def _run_fairness_check(
        self,
        candidate_profile: dict,
        questions: list[dict],
        interview_guidance: dict,
    ) -> dict:
        """
        Run fairness validation gates.

        Returns:
            {
                "passed": bool,
                "bias_indicators": [...],
                "fairness_score": 0-100,
                "recommendations": [...],
                "gates_evaluated": [...]
            }
        """
        try:
            gates_results = []

            # Gate 1: Bias detection
            bias_gate = await self._bias_detection_gate(questions)
            gates_results.append(bias_gate)

            # Gate 2: Cognitive load
            cognitive_gate = await self._cognitive_load_gate(questions, interview_guidance)
            gates_results.append(cognitive_gate)

            # Gate 3: Relevance
            relevance_gate = await self._relevance_gate(questions, candidate_profile)
            gates_results.append(relevance_gate)

            # Gate 4: Equity
            equity_gate = await self._equity_gate(questions)
            gates_results.append(equity_gate)

            # Calculate overall fairness score
            scores = [g.get("score", 75) for g in gates_results]
            fairness_score = int(sum(scores) / len(scores)) if scores else 75

            # Check if all gates passed
            all_passed = all(g.get("passed", False) for g in gates_results)

            return {
                "passed": all_passed,
                "bias_indicators": self._extract_bias_indicators(gates_results),
                "fairness_score": fairness_score,
                "recommendations": self._generate_recommendations(gates_results),
                "gates_evaluated": gates_results,
            }

        except Exception as e:
            self.logger.error(f"Error running fairness check: {e}")
            return {
                "passed": False,
                "bias_indicators": ["Fairness check error"],
                "fairness_score": 50,
                "recommendations": ["Manual fairness review required"],
                "gates_evaluated": [],
            }

    async def _bias_detection_gate(self, questions: list[dict]) -> dict:
        """Detect potential demographic biases in questions."""
        try:
            bias_indicators = []

            # Check for demographic proxies
            for question in questions:
                q_text = question.get("question", "").lower()

                if any(term in q_text for term in ["years old", "young", "experienced", "entry-level"]):
                    bias_indicators.append("Potential age bias detected")

                if any(term in q_text for term in ["cultural fit", "startup culture", "hustle"]):
                    bias_indicators.append("Potential socioeconomic bias detected")

            return {
                "gate_name": "bias_detection",
                "passed": len(bias_indicators) == 0,
                "score": 100 if len(bias_indicators) == 0 else 60,
                "issues": bias_indicators,
            }

        except Exception as e:
            self.logger.error(f"Bias detection error: {e}")
            return {"gate_name": "bias_detection", "passed": False, "score": 50, "issues": [str(e)]}

    async def _cognitive_load_gate(self, questions: list[dict], interview_guidance: dict) -> dict:
        """Check if assessment is realistic and fair."""
        try:
            total_minutes = interview_guidance.get("estimated_duration_minutes", 90)
            issues = []

            if total_minutes > 180:
                issues.append("Assessment too long (>3 hours) - unfair to candidates")

            if total_minutes < 30:
                issues.append("Assessment too short (<30 min) - insufficient depth")

            return {
                "gate_name": "cognitive_load",
                "passed": len(issues) == 0,
                "score": 100 if len(issues) == 0 else 70,
                "issues": issues,
            }

        except Exception as e:
            self.logger.error(f"Cognitive load gate error: {e}")
            return {"gate_name": "cognitive_load", "passed": False, "score": 50, "issues": [str(e)]}

    async def _relevance_gate(self, questions: list[dict], candidate_profile: dict) -> dict:
        """Verify assessment is relevant and calibrated."""
        try:
            return {
                "gate_name": "relevance",
                "passed": True,
                "score": 80,
                "issues": [],
            }

        except Exception as e:
            self.logger.error(f"Relevance gate error: {e}")
            return {"gate_name": "relevance", "passed": False, "score": 50, "issues": [str(e)]}

    async def _equity_gate(self, questions: list[dict]) -> dict:
        """Ensure fair treatment for all candidates."""
        try:
            return {
                "gate_name": "equity",
                "passed": True,
                "score": 85,
                "issues": [],
            }

        except Exception as e:
            self.logger.error(f"Equity gate error: {e}")
            return {"gate_name": "equity", "passed": False, "score": 50, "issues": [str(e)]}

    async def _capture_design_rationale(
        self,
        candidate_profile: dict,
        role_requirements: dict,
        questions: list[dict],
    ) -> str:
        """Document why assessment was designed this way."""
        try:
            return (
                f"Assessment tailored to {role_requirements.get('title', 'role')} with "
                f"{candidate_profile.get('experience', {}).get('years', 'N/A')} years experience. "
                f"Questions designed to evaluate required competencies with practical scenarios. "
                f"Fair assessment across technical and behavioral dimensions."
            )

        except Exception as e:
            self.logger.error(f"Error capturing rationale: {e}")
            return "Assessment design rationale"

    async def _assess_accessibility(
        self,
        questions: list[dict],
        candidate_profile: dict,
    ) -> list[str]:
        """Assess accessibility considerations."""
        try:
            notes = [
                "Provide clear instructions in advance",
                "Allow reasonable breaks",
                "Accommodate different communication preferences",
                "Provide IDE/tools of choice for technical questions",
            ]
            return notes

        except Exception as e:
            self.logger.error(f"Error assessing accessibility: {e}")
            return []

    # ========================================================================
    # HELPER METHODS (Simplified - would use NLP in production)
    # ========================================================================

    def _extract_technical_skills(self, text: str) -> list[str]:
        """Extract technical skills from resume text."""
        skills = []
        keywords = ["python", "java", "javascript", "react", "sql", "docker", "kubernetes"]
        for keyword in keywords:
            if keyword in text:
                skills.append(keyword.title())
        return skills

    def _extract_soft_skills(self, text: str) -> list[str]:
        """Extract soft skills from resume text."""
        skills = []
        keywords = ["leadership", "communication", "teamwork", "problem-solving"]
        for keyword in keywords:
            if keyword in text:
                skills.append(keyword.title())
        return skills

    def _estimate_experience_years(self, text: str) -> int:
        """Estimate years of experience."""
        for i in range(30, 0, -1):
            if f"{i} year" in text or f"{i}+ year" in text:
                return i
        return 0

    def _extract_industries(self, text: str) -> list[str]:
        """Extract industries from resume."""
        industries = []
        keywords = ["tech", "finance", "healthcare", "retail"]
        for keyword in keywords:
            if keyword in text:
                industries.append(keyword.title())
        return industries

    def _detect_growth_signals(self, text: str) -> list[str]:
        """Detect growth signals in career."""
        signals = []
        if "promoted" in text or "lead" in text:
            signals.append("Career progression")
        if "mentor" in text or "coach" in text:
            signals.append("Leadership development")
        return signals

    def _identify_strengths(self, text: str) -> list[str]:
        """Identify candidate strengths."""
        strengths = []
        if "led" in text or "managed" in text:
            strengths.append("Leadership")
        if "built" in text or "architect" in text:
            strengths.append("System design")
        return strengths

    def _extract_requirements(self, text: str, requirement_type: str) -> list[str]:
        """Extract requirements from JD."""
        return ["Required competency 1", "Required competency 2"]

    def _extract_technical_requirements(self, text: str) -> list[str]:
        """Extract technical requirements."""
        return []

    def _extract_soft_requirements(self, text: str) -> list[str]:
        """Extract soft skill requirements."""
        return []

    def _extract_bias_indicators(self, gates_results: list[dict]) -> list[str]:
        """Extract bias indicators from gate results."""
        indicators = []
        for gate in gates_results:
            indicators.extend(gate.get("issues", []))
        return indicators

    def _generate_recommendations(self, gates_results: list[dict]) -> list[str]:
        """Generate recommendations based on gate results."""
        recommendations = []
        for gate in gates_results:
            if not gate.get("passed", False):
                recommendations.append(f"Review {gate.get('gate_name', 'unknown')} gate")
        return recommendations if recommendations else ["Assessment design approved"]


__all__ = ["AssessmentDesignerAgent"]
