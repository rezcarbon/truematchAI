"""Analysis & Evolution Queue - Phase 3-5 Celery Tasks.

Tasks for asynchronous analysis, matching, and evolution operations:
- analyze_assessment() - Analyze assessment responses
- calculate_match() - Calculate job fit scores
- process_hiring_outcome() - Learn from hiring outcomes
"""
from __future__ import annotations

import logging
import traceback
from uuid import UUID

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.models.analysis_result import AnalysisResult
from app.models.assessment import Assessment
from app.models.assessment_design import AssessmentDesign
from app.models.candidate_match import CandidateMatch
from app.models.hiring_outcome import HiringOutcome
from app.models.position import Position
from app.models.resume import Resume
from app.agents.analysis_agent import AnalysisAgent
from app.agents.matching_agent import MatchingAgent
from app.agents.evolution_agent import EvolutionAgent
from app.workers.celery_app import celery_app

logger = logging.getLogger("truematch.analysis_evolution_queue")

# Synchronous database for Celery worker
_sync_engine = None
_SyncSessionLocal: sessionmaker[Session] | None = None


def _sync_database_url() -> str:
    """Convert async URL to sync for Celery."""
    url = settings.database_url
    if "+asyncpg" in url:
        return url.replace("+asyncpg", "+psycopg")
    return url


def _session_factory() -> sessionmaker[Session]:
    """Get synchronous session factory."""
    global _sync_engine, _SyncSessionLocal
    if _SyncSessionLocal is None:
        _sync_engine = create_engine(
            _sync_database_url(),
            pool_pre_ping=True,
            future=True,
        )
        _SyncSessionLocal = sessionmaker(bind=_sync_engine, expire_on_commit=False)
    return _SyncSessionLocal


@celery_app.task(
    name="analysis_evolution_queue.analyze_assessment",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
    time_limit=600,  # 10 minutes max
)
def analyze_assessment(
    self,
    analysis_result_id: str,
    assessment_id: str,
) -> dict:
    """
    Analyze assessment responses (Celery task).

    Args:
        analysis_result_id: AnalysisResult ID
        assessment_id: Assessment ID

    Returns:
        dict with analysis_result_id and status
    """
    db_session_factory = _session_factory()
    db = db_session_factory()

    try:
        analysis_uuid = UUID(analysis_result_id)
        assessment_uuid = UUID(assessment_id)

        logger.info(f"Starting analysis task for {analysis_result_id}")

        # Load analysis result
        analysis = db.query(AnalysisResult).filter_by(id=analysis_uuid).first()
        if not analysis:
            logger.error(f"Analysis {analysis_result_id} not found")
            return {"analysis_result_id": analysis_result_id, "error": "Analysis not found"}

        # Load assessment
        assessment = db.query(Assessment).filter_by(id=assessment_uuid).first()
        if not assessment:
            logger.error(f"Assessment {assessment_id} not found")
            return {"analysis_result_id": analysis_result_id, "error": "Assessment not found"}

        # Load design
        design = db.query(AssessmentDesign).filter_by(id=analysis.assessment_design_id).first()
        if not design:
            logger.error(f"Design for analysis {analysis_result_id} not found")
            return {
                "analysis_result_id": analysis_result_id,
                "error": "Assessment design not found",
            }

        # Run agent (synchronously in worker)
        import asyncio

        agent = AnalysisAgent(db)
        result = asyncio.run(agent.analyze_assessment(assessment, design, str(analysis_uuid)))

        logger.info(f"Analysis {analysis_result_id} completed successfully")

        return {
            "analysis_result_id": analysis_result_id,
            "status": "analyzed",
            "fairness_score": result.get("analysis_fairness_check", {}).get("fairness_score", 0),
        }

    except Exception as e:
        logger.error(f"Error in analysis task: {e}\n{traceback.format_exc()}")
        raise self.retry(exc=e)

    finally:
        db.close()


@celery_app.task(
    name="analysis_evolution_queue.calculate_match",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
    time_limit=600,
)
def calculate_match(
    self,
    candidate_match_id: str,
    analysis_result_id: str,
) -> dict:
    """
    Calculate job-to-candidate fit (Celery task).

    Args:
        candidate_match_id: CandidateMatch ID
        analysis_result_id: AnalysisResult ID

    Returns:
        dict with match_id and overall_score
    """
    db_session_factory = _session_factory()
    db = db_session_factory()

    try:
        match_uuid = UUID(candidate_match_id)
        analysis_uuid = UUID(analysis_result_id)

        logger.info(f"Starting match task for {candidate_match_id}")

        # Load match
        match = db.query(CandidateMatch).filter_by(id=match_uuid).first()
        if not match:
            logger.error(f"Match {candidate_match_id} not found")
            return {"candidate_match_id": candidate_match_id, "error": "Match not found"}

        # Load analysis
        analysis = db.query(AnalysisResult).filter_by(id=analysis_uuid).first()
        if not analysis:
            logger.error(f"Analysis {analysis_result_id} not found")
            return {"candidate_match_id": candidate_match_id, "error": "Analysis not found"}

        # Load position and resume
        position = db.query(Position).filter_by(id=match.position_id).first()
        resume = db.query(Resume).filter_by(id=match.candidate_id).first()

        if not position or not resume:
            logger.error(f"Position or resume not found for match {candidate_match_id}")
            return {"candidate_match_id": candidate_match_id, "error": "Data not found"}

        # Run agent
        import asyncio

        agent = MatchingAgent(db)
        result = asyncio.run(agent.calculate_match(analysis, position, resume))

        logger.info(f"Match {candidate_match_id} completed: score={result.get('overall_score', 0)}")

        return {
            "candidate_match_id": candidate_match_id,
            "status": "matched",
            "overall_score": result.get("overall_score", 0),
            "fit_level": result.get("overall_match", {}).get("fit_level", "unknown"),
        }

    except Exception as e:
        logger.error(f"Error in match task: {e}\n{traceback.format_exc()}")
        raise self.retry(exc=e)

    finally:
        db.close()


@celery_app.task(
    name="analysis_evolution_queue.process_hiring_outcome",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
    time_limit=300,  # 5 minutes max
)
def process_hiring_outcome(
    self,
    hiring_outcome_id: str,
) -> dict:
    """
    Process hiring outcome for learning (Celery task).

    Args:
        hiring_outcome_id: HiringOutcome ID

    Returns:
        dict with outcome_id and accuracy
    """
    db_session_factory = _session_factory()
    db = db_session_factory()

    try:
        outcome_uuid = UUID(hiring_outcome_id)

        logger.info(f"Starting evolution task for {hiring_outcome_id}")

        # Load outcome
        outcome = db.query(HiringOutcome).filter_by(id=outcome_uuid).first()
        if not outcome:
            logger.error(f"Outcome {hiring_outcome_id} not found")
            return {"hiring_outcome_id": hiring_outcome_id, "error": "Outcome not found"}

        # Run agent
        import asyncio

        agent = EvolutionAgent(db)
        result = asyncio.run(agent.process_outcome(outcome))

        logger.info(
            f"Evolution {hiring_outcome_id} complete: "
            f"prediction_correct={result['prediction_accuracy'].get('prediction_correct', False)}"
        )

        return {
            "hiring_outcome_id": hiring_outcome_id,
            "status": "processed",
            "prediction_correct": result["prediction_accuracy"].get("prediction_correct", False),
            "learning_signals": len(result["learning_feedback"].get("unexpected_outcomes", [])),
        }

    except Exception as e:
        logger.error(f"Error in evolution task: {e}\n{traceback.format_exc()}")
        raise self.retry(exc=e)

    finally:
        db.close()


__all__ = [
    "analyze_assessment",
    "calculate_match",
    "process_hiring_outcome",
]
