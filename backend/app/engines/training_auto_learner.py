"""
Training Auto-Learning Engine - Process training signals and update virtual brain.

Handles:
- Capability extraction from training feedback
- Success pattern discovery
- Virtual brain state updates
- Improvement metrics calculation
"""
import json
import logging
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.claude_client import ClaudeClient
from app.models.training_data import (
    TrainingDataItem,
    TrainingInsightBatch,
)
from app.models.training import VirtualBrainState

logger = logging.getLogger(__name__)


class TrainingAutoLearner:
    """Autonomous learning engine for training system."""

    def __init__(self, claude_client: Optional[ClaudeClient] = None):
        self.claude = claude_client or ClaudeClient()

    async def process_training_items(
        self,
        items: list[TrainingDataItem],
        db: AsyncSession,
    ) -> dict:
        """
        Process training items and extract learning signals.

        Args:
            items: List of training data items
            db: Database session

        Returns:
            Dict with discovered insights, capabilities, and metrics
        """
        results = {
            "total_items": len(items),
            "new_capabilities": [],
            "updated_mappings": [],
            "success_patterns": [],
            "insights": [],
            "improvement_metrics": {},
        }

        if not items:
            return results

        logger.info(
            f"Starting auto-learning process",
            extra={"total_items": len(items)},
        )

        # Extract capabilities from each item
        for i, item in enumerate(items):
            try:
                capabilities = await self._extract_capabilities_from_item(item)
                if capabilities:
                    item.extracted_capabilities = capabilities["capabilities"]
                    item.extracted_credentials = capabilities.get("credentials", [])
                    item.capability_confidence = capabilities.get("confidence", 0.0)
                    results["new_capabilities"].extend(capabilities["capabilities"])

                    logger.debug(
                        f"Extracted capabilities",
                        extra={
                            "item_index": i,
                            "capabilities": capabilities["capabilities"],
                            "confidence": capabilities.get("confidence", 0.0),
                        },
                    )
            except Exception as e:
                logger.error(
                    f"Error extracting capabilities",
                    extra={"item_index": i, "error": str(e)},
                )

        # Discover patterns from hiring decisions
        patterns = await self._discover_success_patterns(items)
        results["success_patterns"] = patterns

        # Generate insights
        insights = await self._generate_insights(items)
        results["insights"] = insights

        # Calculate improvement metrics
        metrics = await self._calculate_improvement_metrics(items)
        results["improvement_metrics"] = metrics

        logger.info(
            f"Auto-learning completed",
            extra={
                "new_capabilities": len(set(results["new_capabilities"])),
                "patterns_discovered": len(patterns),
                "insights_generated": len(insights),
            },
        )

        return results

    async def _extract_capabilities_from_item(
        self,
        item: TrainingDataItem,
    ) -> Optional[dict]:
        """
        Extract capabilities from candidate profile and decision reasoning.

        Uses Claude to analyze the reasoning text and identify demonstrated capabilities.
        """
        if not item.reasoning:
            return None

        try:
            profile_text = f"""
Candidate: {item.candidate_name}
Decision: {item.decision.upper()}
Experience: {item.experience_years or 'Not specified'} years
Skills: {', '.join(item.skills) if item.skills else 'Not specified'}
Education: {item.education or 'Not specified'}

Reasoning: {item.reasoning}
"""

            prompt = f"""Analyze this candidate record and extract the demonstrated capabilities and credentials mentioned or implied.

{profile_text}

Return a JSON object with:
- "capabilities": list of demonstrated capabilities (e.g., "Backend Architecture", "Team Leadership")
- "credentials": list of recognized credentials (e.g., "AWS Certified", "5+ years Python")
- "confidence": float 0-1 representing confidence in these extractions

Be specific and avoid generic terms. Focus on what's actually demonstrated or claimed."""

            # Use Claude to extract capabilities
            response = await self.claude.send_message(prompt, max_tokens=500)

            # Parse response
            try:
                # Find JSON in response
                json_start = response.find("{")
                json_end = response.rfind("}") + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = response[json_start:json_end]
                    result = json.loads(json_str)
                    return {
                        "capabilities": result.get("capabilities", []),
                        "credentials": result.get("credentials", []),
                        "confidence": result.get("confidence", 0.7),
                    }
            except (json.JSONDecodeError, ValueError):
                logger.warning(
                    f"Failed to parse Claude response",
                    extra={"response": response[:200]},
                )
                return None

        except Exception as e:
            logger.error(
                f"Error in capability extraction",
                extra={"error": str(e), "candidate": item.candidate_name},
            )
            return None

    async def _discover_success_patterns(
        self,
        items: list[TrainingDataItem],
    ) -> list[dict]:
        """
        Discover success patterns from hired candidates.

        Identifies commonalities in successful candidates.
        """
        hired = [item for item in items if item.decision == "hire"]
        if not hired:
            return []

        patterns = []

        # Pattern: Years of experience
        hired_experience = [h.experience_years for h in hired if h.experience_years]
        if hired_experience:
            avg_experience = sum(hired_experience) / len(hired_experience)
            patterns.append(
                {
                    "pattern_type": "experience_level",
                    "average_years": avg_experience,
                    "sample_size": len(hired_experience),
                    "description": f"Successfully hired candidates average {avg_experience:.1f} years experience",
                }
            )

        # Pattern: Common skills
        all_skills = []
        for h in hired:
            all_skills.extend(h.skills or [])

        if all_skills:
            from collections import Counter

            skill_counts = Counter(all_skills)
            top_skills = skill_counts.most_common(5)
            patterns.append(
                {
                    "pattern_type": "skill_correlation",
                    "top_skills": [skill for skill, _ in top_skills],
                    "frequency": [count for _, count in top_skills],
                    "sample_size": len(hired),
                    "description": f"Top skills in hired candidates: {', '.join(s[0] for s in top_skills)}",
                }
            )

        return patterns

    async def _generate_insights(
        self,
        items: list[TrainingDataItem],
    ) -> list[str]:
        """
        Generate human-readable insights from training data.
        """
        insights = []

        # Insight: Hiring rate
        hired_count = len([i for i in items if i.decision == "hire"])
        hiring_rate = (hired_count / len(items)) * 100 if items else 0
        insights.append(
            f"Overall hiring rate: {hiring_rate:.1f}% ({hired_count}/{len(items)} candidates)"
        )

        # Insight: Decision distribution
        decisions = {}
        for item in items:
            decisions[item.decision] = decisions.get(item.decision, 0) + 1

        insights.append(f"Decision distribution: {decisions}")

        # Insight: Common rejection reasons
        rejects = [i for i in items if i.decision == "reject"]
        if rejects:
            reject_keywords = {}
            for item in rejects:
                words = item.reasoning.lower().split()
                for word in words:
                    if len(word) > 4:  # Skip short words
                        reject_keywords[word] = reject_keywords.get(word, 0) + 1

            if reject_keywords:
                top_reasons = sorted(reject_keywords.items(), key=lambda x: x[1], reverse=True)[:3]
                insights.append(f"Common rejection themes: {[r[0] for r in top_reasons]}")

        return insights

    async def _calculate_improvement_metrics(
        self,
        items: list[TrainingDataItem],
    ) -> dict:
        """
        Calculate improvement metrics based on training data.
        """
        if not items:
            return {}

        metrics = {
            "match_accuracy_delta": 0.05,  # TODO: Calculate from actual data
            "hire_success_delta": 0.03,  # TODO: Calculate from actual data
            "capability_coverage_delta": 0.10,  # TODO: Calculate from actual data
            "new_patterns_discovered": len(items) // 10,
            "learning_velocity": len(items),  # items per batch
        }

        return metrics

    async def update_virtual_brain_state(
        self,
        upload_id: UUID,
        insights: dict,
        db: AsyncSession,
    ) -> Optional[TrainingInsightBatch]:
        """
        Update virtual brain state based on learning results.

        Creates TrainingInsightBatch record with discovered improvements.
        """
        try:
            # Get current virtual brain state (from training.py)
            from sqlalchemy import select

            query = select(VirtualBrainState).order_by(VirtualBrainState.version.desc()).limit(1)
            result = await db.execute(query)
            current_state = result.scalar_one_or_none()

            if not current_state:
                logger.warning("No virtual brain state found")
                return None

            # Create insight batch
            batch = TrainingInsightBatch(
                id=__import__("uuid").uuid4(),
                source="upload",
                source_id=upload_id,
                insights=insights.get("insights", []),
                new_capabilities=list(set(insights.get("new_capabilities", []))),
                new_success_patterns=insights.get("success_patterns", []),
                improvement_metrics=insights.get("improvement_metrics", {}),
                virtual_brain_state_version=current_state.version,
                match_accuracy_before=current_state.match_accuracy,
                match_accuracy_after=current_state.match_accuracy
                + insights.get("improvement_metrics", {}).get("match_accuracy_delta", 0),
            )

            db.add(batch)
            await db.commit()
            await db.refresh(batch)

            logger.info(
                f"Updated virtual brain state",
                extra={
                    "upload_id": str(upload_id),
                    "batch_id": str(batch.id),
                    "accuracy_improvement": batch.match_accuracy_after - batch.match_accuracy_before,
                },
            )

            return batch

        except Exception as e:
            logger.error(
                f"Error updating virtual brain state",
                extra={"upload_id": str(upload_id), "error": str(e)},
            )
            return None
