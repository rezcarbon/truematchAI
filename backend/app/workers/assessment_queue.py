"""
AI-Native Assessment Job Queue - Phase A+B+C+D Integration

Manages queueing and processing of assessment jobs.
Routes jobs through decision engine and notification system.
Integrates provenance tracking (C) and learning loop (D).
Handles retries, failures, and monitoring.
"""
import asyncio
import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from uuid import UUID, uuid4

from app.config import settings
from app.workers.provenance_learning_orchestrator import (
    get_provenance_learning_orchestrator,
)

logger = logging.getLogger(__name__)


class JobStatus(str, Enum):
    """Assessment job status states."""

    PENDING = "pending"  # Queued, waiting for processing
    QUEUED = "queued"  # Ready to process
    PROCESSING = "processing"  # Currently being assessed
    GATES_PASSED = "gates_passed"  # Governance gates verified
    DECIDED = "decided"  # Decision made
    NOTIFIED = "notified"  # Recruiter notified
    COMPLETED = "completed"  # Job finished
    FAILED = "failed"  # Job failed


class JobPriority(int, Enum):
    """Job priority levels."""

    URGENT = 1
    HIGH = 3
    NORMAL = 5
    LOW = 7
    BATCH = 10


@dataclass
class AssessmentJob:
    """
    Assessment job definition.

    Contains CV/JD data and metadata for single assessment.
    """

    job_id: str
    cv_path: str  # Path to CV file
    jd_id: Optional[str] = None  # If assessing against known JD
    jd_text: Optional[str] = None  # If pasting JD text
    user_id: Optional[str] = None  # Recruiter who submitted
    email_from: Optional[str] = None  # Email of submitter
    priority: JobPriority = JobPriority.NORMAL
    created_at: str = None
    status: JobStatus = JobStatus.PENDING
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow().isoformat()
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["priority"] = self.priority.value
        data["status"] = self.status.value
        return data


class AssessmentQueue:
    """
    In-memory job queue for assessments.

    Supports priority-based processing.
    Can be replaced with Redis/RabbitMQ for production.
    """

    def __init__(self, max_concurrent: int = 5):
        self.max_concurrent = max_concurrent
        self.queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self.jobs: Dict[str, AssessmentJob] = {}  # job_id -> job
        self.processing: Dict[str, AssessmentJob] = {}  # Currently processing jobs
        self.completed: Dict[str, AssessmentJob] = {}  # Completed jobs (last 1000)
        self.failed: Dict[str, AssessmentJob] = {}  # Failed jobs (last 1000)

    async def enqueue(self, job: AssessmentJob) -> str:
        """Add job to queue."""
        self.jobs[job.job_id] = job
        job.status = JobStatus.QUEUED

        # Use negative priority so high priority jobs are processed first
        await self.queue.put((job.priority.value, job.job_id))

        logger.info(f"Job enqueued: {job.job_id} (priority: {job.priority.name})")
        return job.job_id

    async def dequeue(self) -> Optional[AssessmentJob]:
        """Get next job from queue."""
        if self.queue.empty():
            return None

        try:
            _, job_id = await asyncio.wait_for(self.queue.get(), timeout=1.0)
            job = self.jobs.get(job_id)

            if job:
                job.status = JobStatus.PROCESSING
                self.processing[job_id] = job
                logger.info(f"Job dequeued: {job_id}")
                return job
        except asyncio.TimeoutError:
            pass

        return None

    async def mark_completed(self, job_id: str, result: Dict[str, Any]):
        """Mark job as completed."""
        job = self.processing.pop(job_id, None)
        if job:
            job.status = JobStatus.COMPLETED
            job.metadata["result"] = result
            job.metadata["completed_at"] = datetime.utcnow().isoformat()

            # Keep last 1000 completed jobs
            self.completed[job_id] = job
            if len(self.completed) > 1000:
                oldest = min(self.completed.items(), key=lambda x: x[1].created_at)
                del self.completed[oldest[0]]

            logger.info(f"Job completed: {job_id}")

    async def mark_failed(self, job_id: str, error: str):
        """Mark job as failed."""
        job = self.processing.pop(job_id, None)
        if job:
            job.status = JobStatus.FAILED
            job.metadata["error"] = error
            job.metadata["failed_at"] = datetime.utcnow().isoformat()

            # Keep last 1000 failed jobs
            self.failed[job_id] = job
            if len(self.failed) > 1000:
                oldest = min(self.failed.items(), key=lambda x: x[1].created_at)
                del self.failed[oldest[0]]

            logger.error(f"Job failed: {job_id} - {error}")

    def get_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job status and details."""
        job = (
            self.jobs.get(job_id)
            or self.processing.get(job_id)
            or self.completed.get(job_id)
            or self.failed.get(job_id)
        )

        if job:
            return job.to_dict()
        return None

    def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        return {
            "queue_size": self.queue.qsize(),
            "processing": len(self.processing),
            "completed": len(self.completed),
            "failed": len(self.failed),
            "max_concurrent": self.max_concurrent,
        }


class AssessmentProcessor:
    """
    Processes assessment jobs from queue.

    Handles:
    1. Assessment execution
    2. Governance gate validation
    3. Decision making
    4. Notification dispatch
    5. Provenance tracking (Phase C)
    6. Learning integration (Phase D)
    """

    def __init__(
        self,
        queue: AssessmentQueue,
        assessment_executor: Optional[Callable] = None,
        governance_validator: Optional[Callable] = None,
        decision_engine: Optional[Callable] = None,
        notification_dispatcher: Optional[Callable] = None,
        provenance_learning_orchestrator: Optional[Any] = None,
    ):
        self.queue = queue
        self.assessment_executor = assessment_executor
        self.governance_validator = governance_validator
        self.decision_engine = decision_engine
        self.notification_dispatcher = notification_dispatcher
        self.provenance_learning = (
            provenance_learning_orchestrator or get_provenance_learning_orchestrator()
        )
        self.is_running = False

    async def process_job(self, job: AssessmentJob) -> Dict[str, Any]:
        """
        Process single assessment job.

        Flow:
        1. Run assessment (keyword + semantic + capability)
        2. Validate governance gates
        3. Apply decision logic
        4. Send notification
        5. Create provenance record (Phase C)
        6. Process training feedback (Phase D)
        """
        start_time = datetime.utcnow()
        try:
            logger.info(f"Processing job: {job.job_id}")

            # Step 1: Run assessment
            if not self.assessment_executor:
                raise RuntimeError("Assessment executor not configured")

            assessment_result = await self.assessment_executor(job)
            job.metadata["assessment"] = assessment_result

            logger.info(f"Assessment complete: {job.job_id}")

            # Step 2: Validate governance gates
            gates_result = None
            if self.governance_validator:
                gates_result = await self.governance_validator(job, assessment_result)
                job.metadata["gates"] = gates_result

                if not gates_result.get("passed", False):
                    logger.warning(f"Governance gates failed: {job.job_id}")
                    job.status = JobStatus.DECIDED
                    job.metadata["decision"] = "MANUAL_REVIEW"
                    job.metadata["reason"] = gates_result.get("reason", "Governance gate validation failed")

            # Step 3: Apply decision logic
            decision = "UNKNOWN"
            decision_reasoning = {}
            if self.decision_engine:
                decision = await self.decision_engine(job, assessment_result, gates_result)
                job.metadata["decision"] = decision
                job.status = JobStatus.DECIDED
                decision_reasoning = {"decision": decision, "source": "decision_engine"}

                logger.info(f"Decision made: {job.job_id} -> {decision}")

            # Step 4: Send notification
            notifications_sent = []
            if self.notification_dispatcher:
                await self.notification_dispatcher(job)
                job.status = JobStatus.NOTIFIED
                notifications_sent = ["notification_service"]

            # Step 5: Create provenance record (Phase C)
            # Get CV and JD content for input hashing
            cv_content = job.metadata.get("cv_content", "")
            jd_content = job.metadata.get("jd_content", job.jd_text or "")

            execution_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            assessment_result["execution_time_ms"] = execution_time_ms

            if self.provenance_learning:
                try:
                    provenance_result = await self.provenance_learning.create_full_provenance_record(
                        assessment_id=job.job_id,
                        cv_content=cv_content,
                        jd_content=jd_content,
                        assessment_inputs={
                            "cv_filename": job.metadata.get("cv_filename"),
                            "jd_id": job.jd_id,
                            "user_id": job.user_id,
                        },
                        assessment_results=assessment_result,
                        governance_results=gates_result or {},
                        decision=decision,
                        decision_reasoning=decision_reasoning,
                        notifications_sent=notifications_sent,
                        actor=job.user_id or "system",
                    )
                    job.metadata["provenance"] = provenance_result
                    logger.info(f"Provenance record created: {job.job_id}")
                except Exception as e:
                    logger.error(f"Error creating provenance record: {e}")
                    # Don't fail the job if provenance tracking fails
                    job.metadata["provenance_error"] = str(e)

            # Step 6: Process training feedback (Phase D)
            if job.metadata.get("training_feedback") and self.provenance_learning:
                try:
                    feedback_type = job.metadata["training_feedback"].get("type")
                    feedback_data = job.metadata["training_feedback"].get("data")

                    learning_result = await self.provenance_learning.process_training_and_learn(
                        feedback_type=feedback_type,
                        feedback_data=feedback_data,
                        source="api",
                    )
                    job.metadata["learning"] = learning_result
                    logger.info(f"Training feedback processed: {job.job_id}")
                except Exception as e:
                    logger.error(f"Error processing training feedback: {e}")
                    job.metadata["learning_error"] = str(e)

            # Mark completed
            await self.queue.mark_completed(job.job_id, job.metadata)
            return job.metadata

        except Exception as e:
            logger.error(f"Error processing job {job.job_id}: {e}")
            await self.queue.mark_failed(job.job_id, str(e))
            raise

    async def worker(self):
        """
        Single worker process.

        Continuously dequeues jobs and processes them.
        """
        logger.info("Assessment worker started")

        while self.is_running:
            try:
                job = await self.queue.dequeue()
                if job:
                    await self.process_job(job)
                else:
                    # Queue empty, wait a bit
                    await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"Worker error: {e}")
                await asyncio.sleep(5)

        logger.info("Assessment worker stopped")

    async def start(self):
        """Start processing workers."""
        self.is_running = True
        logger.info(f"Starting {self.queue.max_concurrent} assessment workers")

        # Start worker coroutines
        workers = [self.worker() for _ in range(self.queue.max_concurrent)]
        await asyncio.gather(*workers)

    def stop(self):
        """Stop processing workers."""
        self.is_running = False
        logger.info("Assessment workers stopping")


# Global queue and processor instances
_queue: Optional[AssessmentQueue] = None
_processor: Optional[AssessmentProcessor] = None


def get_assessment_queue() -> AssessmentQueue:
    """Get or create assessment queue."""
    global _queue
    if _queue is None:
        _queue = AssessmentQueue(max_concurrent=settings.max_concurrent_assessments)
    return _queue


def get_assessment_processor() -> AssessmentProcessor:
    """Get or create assessment processor."""
    global _processor
    if _processor is None:
        _processor = AssessmentProcessor(get_assessment_queue())
    return _processor


async def start_assessment_processing():
    """Start assessment processing on application startup."""
    processor = get_assessment_processor()
    asyncio.create_task(processor.start())
    logger.info("Assessment processing started on application startup")


def stop_assessment_processing():
    """Stop assessment processing on application shutdown."""
    processor = get_assessment_processor()
    processor.stop()
    logger.info("Assessment processing stopped on application shutdown")
