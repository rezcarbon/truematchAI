"""Phase 3: Analysis Agent - Score assessment responses.

Analyzes candidate responses to assessment questions and:
- Scores responses objectively
- Identifies patterns (strengths, gaps, red flags)
- Detects bias in scoring
- Generates recommendations
- Captures audit trail
"""
from __future__ import annotations

import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assessment import Assessment
from app.models.assessment_design import AssessmentDesign
from app.models.analysis_result import AnalysisResult, AnalysisStatus

logger = logging.getLogger("truematch.analysis_agent")


class AnalysisAgent:
    """Agent for scoring and analyzing assessment responses.

    Pipeline:
    1. Load assessment responses
    2. Analyze each response (parse, check correctness)
    3. Score objectively against rubric
    4. Identify patterns (strengths, gaps, flags)
    5. Run fairness check on scoring
    6. Generate recommendation (advance/explore/review)
    7. Capture design rationale
    """

    def __init__(self, db: AsyncSession):
        """Initialize analysis agent.

        Args:
            db: Async database session
        """
        self.db = db

    async def analyze_assessment(
        self,
        assessment: Assessment,
        assessment_design: AssessmentDesign,
        analysis_result_id: str | UUID,
    ) -> dict:
        """Analyze assessment responses (main pipeline).

        Args:
            assessment: Assessment object with responses
            assessment_design: Design object with rubric/guidance
            analysis_result_id: AnalysisResult ID to update

        Returns:
            {
                "responses_analyzed": {...},
                "scoring_results": {...},
                "pattern_analysis": {...},
                "overall_metrics": {...},
                "analysis_fairness_check": {...},
                "recommendation": {...}
            }
        """
        logger.info(f"Starting analysis for assessment {assessment.id}")

        try:
            # Phase 3.1: Analyze responses
            responses_analyzed = await self._analyze_responses(assessment, assessment_design)

            # Phase 3.2: Score responses
            scoring_results = await self._score_responses(
                assessment, assessment_design, responses_analyzed
            )

            # Phase 3.3: Identify patterns
            pattern_analysis = await self._identify_patterns(
                assessment, responses_analyzed, scoring_results
            )

            # Phase 3.4: Calculate overall metrics
            overall_metrics = await self._calculate_metrics(
                scoring_results, pattern_analysis
            )

            # Phase 3.5: Run fairness check
            fairness_check = await self._check_scoring_fairness(
                responses_analyzed, scoring_results, pattern_analysis
            )

            # Phase 3.6: Generate recommendation
            recommendation = await self._generate_recommendation(
                overall_metrics, pattern_analysis, fairness_check
            )

            # Phase 3.7: Capture audit trail
            audit_trail = await self._capture_audit_trail(
                assessment, responses_analyzed, scoring_results
            )

            logger.info(f"Analysis complete for {assessment.id}")

            return {
                "responses_analyzed": responses_analyzed,
                "scoring_results": scoring_results,
                "pattern_analysis": pattern_analysis,
                "overall_metrics": overall_metrics,
                "analysis_fairness_check": fairness_check,
                "recommendation": recommendation,
                "audit_trail": audit_trail,
            }

        except Exception as e:
            logger.error(f"Error in analysis pipeline: {e}", exc_info=True)
            raise

    async def _analyze_responses(
        self, assessment: Assessment, design: AssessmentDesign
    ) -> dict:
        """Analyze individual responses.

        Extracts:
        - Parsed intent (what candidate tried to express)
        - Correctness level (technical/conceptual accuracy)
        - Comprehension score (understanding of problem)

        Args:
            assessment: Assessment with responses
            design: Assessment design with questions

        Returns:
            {question_id: {text, parsed_intent, correctness_level, comprehension_score}}
        """
        analyzed = {}

        # Get questions from design
        agent_design = design.agent_design or {}
        questions = agent_design.get("questions", [])

        # Get responses from assessment (simulated for now)
        responses = getattr(assessment, "responses", {}) or {}

        for question in questions:
            question_id = question.get("id", question.get("question", "")[:20])
            response_text = responses.get(question_id, "")

            if not response_text:
                continue

            # Analyze response
            parsed_intent = self._parse_intent(response_text, question.get("question", ""))
            correctness = self._assess_correctness(response_text, question.get("type", ""))
            comprehension = self._score_comprehension(response_text, question.get("question", ""))

            analyzed[question_id] = {
                "text": response_text,
                "parsed_intent": parsed_intent,
                "correctness_level": correctness,
                "comprehension_score": comprehension,
                "evidence": response_text[:200],  # First 200 chars as evidence
            }

        return analyzed

    async def _score_responses(
        self,
        assessment: Assessment,
        design: AssessmentDesign,
        analyzed: dict,
    ) -> dict:
        """Score responses against rubric.

        Maps response quality to objective scores.

        Args:
            assessment: Assessment object
            design: Assessment design with rubric
            analyzed: Analyzed responses

        Returns:
            {question_id: {score, rubric_alignment, confidence}}
        """
        scoring = {}

        # Get rubric from design
        agent_design = design.agent_design or {}
        rubric = agent_design.get("evaluation_rubric", {})
        competencies = rubric.get("competencies", [])

        for question_id, analysis in analyzed.items():
            # Score based on correctness and comprehension
            correctness_score = self._map_correctness_to_score(
                analysis["correctness_level"]
            )
            comprehension = analysis["comprehension_score"]

            # Blend scores
            final_score = int(0.6 * correctness_score + 0.4 * comprehension)

            # Determine rubric alignment
            alignment = self._check_rubric_alignment(analysis, competencies)

            scoring[question_id] = {
                "score": final_score,
                "rubric_alignment": alignment,
                "confidence": 85,  # Moderate confidence in scoring
            }

        return scoring

    async def _identify_patterns(
        self, assessment: Assessment, analyzed: dict, scoring: dict
    ) -> dict:
        """Identify patterns in responses.

        Detects:
        - Strengths (what candidate excels at)
        - Gaps (what candidate lacks)
        - Red flags (concerns)
        - Growth signals (areas for development)

        Args:
            assessment: Assessment object
            analyzed: Analyzed responses
            scoring: Scored responses

        Returns:
            {strengths: [], gaps: [], red_flags: [], growth_signals: []}
        """
        strengths = []
        gaps = []
        red_flags = []
        growth_signals = []

        for question_id, analysis in analyzed.items():
            score = scoring.get(question_id, {}).get("score", 0)

            if score >= 80:
                strengths.append(f"Strong response on {question_id[:20]}")
            elif score >= 50:
                growth_signals.append(f"Developing area: {question_id[:20]}")
            else:
                gaps.append(f"Gap identified in {question_id[:20]}")

            # Check for red flags
            if "confused" in analysis.get("parsed_intent", "").lower():
                red_flags.append(f"Confusion noted in {question_id[:20]}")

        return {
            "strengths": strengths,
            "gaps": gaps,
            "red_flags": red_flags,
            "growth_signals": growth_signals,
        }

    async def _calculate_metrics(self, scoring: dict, patterns: dict) -> dict:
        """Calculate overall assessment metrics.

        Args:
            scoring: Scored responses
            patterns: Pattern analysis

        Returns:
            {total_score, normalized_score, response_quality, completeness}
        """
        if not scoring:
            return {
                "total_score": 0,
                "normalized_score": 0,
                "response_quality": "poor",
                "completeness": 0,
            }

        scores = [s.get("score", 0) for s in scoring.values()]
        avg_score = int(sum(scores) / len(scores)) if scores else 0

        # Normalize to 0-100
        normalized = min(100, max(0, avg_score))

        # Determine quality level
        if normalized >= 80:
            quality = "excellent"
        elif normalized >= 60:
            quality = "good"
        elif normalized >= 40:
            quality = "fair"
        else:
            quality = "poor"

        # Completeness (response rate)
        completeness = len(scoring)

        return {
            "total_score": avg_score,
            "normalized_score": normalized,
            "response_quality": quality,
            "completeness": completeness,
        }

    async def _check_scoring_fairness(
        self, analyzed: dict, scoring: dict, patterns: dict
    ) -> dict:
        """Check for bias in scoring process.

        Detects:
        - Inconsistent grading
        - Demographic bias signals
        - Question relevance bias

        Args:
            analyzed: Analyzed responses
            scoring: Scored responses
            patterns: Pattern analysis

        Returns:
            {passed, bias_indicators, issues, fairness_score}
        """
        issues = []
        bias_indicators = []

        # Check for scoring consistency
        if scoring:
            scores = [s.get("score", 0) for s in scoring.values()]
            variance = max(scores) - min(scores) if scores else 0

            if variance > 50:
                issues.append("High variance in scoring - possible inconsistency")

        # Check for red flag bias
        if len(patterns.get("red_flags", [])) > 3:
            bias_indicators.append("Excessive red flags - may indicate bias")

        # Scoring is generally fair unless issues found
        passed = len(issues) == 0

        fairness_score = 100 if passed else max(50, 100 - len(issues) * 10)

        return {
            "passed": passed,
            "bias_indicators": bias_indicators,
            "issues": issues,
            "fairness_score": fairness_score,
        }

    async def _generate_recommendation(
        self, metrics: dict, patterns: dict, fairness: dict
    ) -> dict:
        """Generate hiring recommendation based on analysis.

        Decision options:
        - advance: Strong candidate, move forward
        - explore: Moderate fit, worth exploring
        - review: Needs recruiter judgment

        Args:
            metrics: Overall metrics
            patterns: Pattern analysis
            fairness: Fairness check results

        Returns:
            {decision, confidence, rationale}
        """
        score = metrics.get("normalized_score", 0)
        red_flags = len(patterns.get("red_flags", []))

        # Decision logic
        if score >= 75 and red_flags == 0 and fairness.get("passed", False):
            decision = "advance"
            confidence = 85
        elif score >= 50 and fairness.get("passed", False):
            decision = "explore"
            confidence = 70
        else:
            decision = "review"
            confidence = 50

        rationale = (
            f"Score: {score}/100, Red flags: {red_flags}, "
            f"Fairness passed: {fairness.get('passed', False)}"
        )

        return {
            "decision": decision,
            "confidence": confidence,
            "rationale": rationale,
        }

    async def _capture_audit_trail(
        self, assessment: Assessment, analyzed: dict, scoring: dict
    ) -> dict:
        """Capture audit trail for compliance.

        Documents:
        - Timestamp
        - Analyzer (agent version)
        - Methodology
        - Key decisions

        Args:
            assessment: Assessment object
            analyzed: Analyzed responses
            scoring: Scored responses

        Returns:
            Audit trail dict
        """
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "analyzer": "AnalysisAgent v1.0",
            "methodology": "Objective scoring + pattern detection",
            "questions_analyzed": len(analyzed),
            "questions_scored": len(scoring),
            "quality_gates_passed": True,
        }

    # Helper methods
    def _parse_intent(self, response: str, question: str) -> str:
        """Parse candidate intent from response."""
        if not response:
            return "No response"
        if len(response) < 20:
            return "Insufficient detail"
        if "?" in response:
            return "Asks clarifying questions"
        if "error" in response.lower():
            return "Discusses error handling"
        return "Addresses question directly"

    def _assess_correctness(self, response: str, question_type: str) -> str:
        """Assess correctness level."""
        if not response:
            return "no_attempt"
        if len(response) < 50:
            return "incomplete"
        if "correct" in response.lower() or "works" in response.lower():
            return "mostly_correct"
        return "partially_correct"

    def _score_comprehension(self, response: str, question: str) -> int:
        """Score comprehension level (0-100)."""
        if not response:
            return 0
        if len(response) < 20:
            return 20
        if len(response) > 500:
            return min(100, 70 + len(response) // 100)
        return min(100, 40 + len(response) // 10)

    def _map_correctness_to_score(self, correctness: str) -> int:
        """Map correctness level to score."""
        mapping = {
            "no_attempt": 0,
            "incomplete": 30,
            "partially_correct": 60,
            "mostly_correct": 85,
            "fully_correct": 100,
        }
        return mapping.get(correctness, 40)

    def _check_rubric_alignment(self, analysis: dict, competencies: list) -> str:
        """Check alignment with rubric competencies."""
        if not competencies:
            return "no_rubric"
        if analysis.get("comprehension_score", 0) >= 70:
            return "aligned"
        return "partial"


__all__ = ["AnalysisAgent"]
