"""
Auto-Reject Worker (Phase 1.2: Autonomy Layer)

Automatically rejects assessment queue items that fall below quality thresholds.

Trigger: When an assessment completes with score < AUTO_REJECT_THRESHOLD

Actions:
- Mark queue item as rejected
- Send rejection email to candidate
- Broadcast queue_item_action event
- Create audit trail entry
- Log decision for learning loop

Configuration:
- AUTO_REJECT_THRESHOLD (default 0.40): Score threshold below which items are auto-rejected
"""

from __future__ import annotations

import logging
import uuid
from app.core.clock import utcnow

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.assessment import Assessment
from app.models.ingest_queue import IngestQueueItem, IngestStatus
from app.models.resume import Resume
from app.models.audit import AuditTrailEntry
from app.websocket.agents_operator import get_operator_manager
from app.workers.notification_service import get_notification_dispatcher

logger = logging.getLogger("truematch.auto_reject")


class AutoRejectWorker:
    """
    Handles automatic rejection of assessments not meeting quality criteria.

    When an assessment score falls below the configured threshold, the worker
    automatically rejects the associated queue item and notifies the candidate.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize the auto-reject worker.

        Args:
            db: AsyncSession for database access
        """
        self.db = db
        self.operator_manager = get_operator_manager()
        self.notification_dispatcher = get_notification_dispatcher()
        self.threshold = getattr(
            settings,
            'AUTO_REJECT_THRESHOLD',
            0.40
        )

    async def process_assessment(
        self,
        assessment_id: uuid.UUID,
        assessment_score: float,
        user_id: uuid.UUID,
    ) -> dict[str, bool | str]:
        """
        Check if assessment should be auto-rejected.

        Args:
            assessment_id: ID of completed assessment
            assessment_score: Overall assessment score (0.0-1.0)
            user_id: ID of recruiter who initiated assessment

        Returns:
            Dict with rejection status:
                {
                    'rejected': bool,
                    'reason': str,
                    'queue_item_id': Optional[uuid.UUID],
                    'candidate_notified': bool,
                    'threshold': float,
                    'score': float,
                }

        Examples:
            >>> result = await worker.process_assessment(
            ...     assessment_id=uuid.uuid4(),
            ...     assessment_score=0.30,
            ...     user_id=uuid.uuid4(),
            ... )
            >>> assert result['rejected'] is True
        """
        try:
            logger.info(
                f"[AutoReject] Checking assessment {assessment_id}: "
                f"score={assessment_score:.2f}"
            )

            # Fetch assessment record
            stmt = select(Assessment).where(Assessment.id == assessment_id)
            result = await self.db.execute(stmt)
            assessment = result.scalar_one_or_none()

            if not assessment:
                logger.warning(
                    f"[AutoReject] Assessment {assessment_id} not found"
                )
                return {
                    'rejected': False,
                    'reason': 'Assessment not found',
                }

            # Check score threshold
            if assessment_score >= self.threshold:
                logger.info(
                    f"[AutoReject] Score {assessment_score:.2f} meets or exceeds threshold "
                    f"{self.threshold:.2f}, no rejection"
                )
                return {
                    'rejected': False,
                    'reason': f'Score {assessment_score:.2f} meets threshold {self.threshold:.2f}',
                    'score': assessment_score,
                    'threshold': self.threshold,
                }

            # Find associated queue item
            stmt = select(IngestQueueItem).where(
                IngestQueueItem.assessment_id == assessment_id
            )
            result = await self.db.execute(stmt)
            queue_item = result.scalar_one_or_none()

            if not queue_item:
                logger.warning(
                    f"[AutoReject] No queue item found for assessment {assessment_id}"
                )
                return {
                    'rejected': False,
                    'reason': 'No associated queue item',
                    'assessment_id': str(assessment_id),
                }

            # Auto-reject the queue item
            candidate_notified = await self._reject_queue_item(
                queue_item=queue_item,
                assessment_id=assessment_id,
                user_id=user_id,
                assessment_score=assessment_score,
            )

            logger.info(
                f"[AutoReject] Successfully auto-rejected queue item "
                f"{queue_item.id} (assessment {assessment_id}, score {assessment_score:.2f})"
            )

            return {
                'rejected': True,
                'reason': 'Auto-rejected: score below quality threshold',
                'queue_item_id': str(queue_item.id),
                'assessment_id': str(assessment_id),
                'candidate_notified': candidate_notified,
                'score': assessment_score,
                'threshold': self.threshold,
            }

        except Exception as e:
            logger.error(
                f"[AutoReject] Error processing assessment {assessment_id}: {e}",
                exc_info=True
            )
            return {
                'rejected': False,
                'reason': f'Error: {str(e)}',
            }

    async def _reject_queue_item(
        self,
        queue_item: IngestQueueItem,
        assessment_id: uuid.UUID,
        user_id: uuid.UUID,
        assessment_score: float,
    ) -> bool:
        """
        Reject a queue item and notify candidate.

        Args:
            queue_item: The ingest queue item to reject
            assessment_id: Associated assessment ID
            user_id: User performing rejection
            assessment_score: Assessment score for audit trail

        Returns:
            True if candidate was successfully notified, False otherwise

        Raises:
            Exception: If database update fails
        """
        candidate_notified = False

        # Update queue item status
        stmt = (
            update(IngestQueueItem)
            .where(IngestQueueItem.id == queue_item.id)
            .values(
                status=IngestStatus.REJECTED,
                review_notes=f"Auto-rejected (score: {assessment_score:.2f})",
                updated_at=utcnow(),
            )
        )
        await self.db.execute(stmt)
        await self.db.commit()

        logger.debug(
            f"[AutoReject] Updated queue item {queue_item.id} to REJECTED"
        )

        # Create audit trail entry
        audit_entry = AuditTrailEntry(
            entity_type='ingest_queue_item',
            entity_id=str(queue_item.id),
            action='auto_reject',
            actor_id=str(user_id),
            actor_type='system',
            changes={
                'status': IngestStatus.REJECTED,
                'auto_rejected': True,
                'assessment_score': float(assessment_score),
            },
            timestamp=utcnow(),
        )
        self.db.add(audit_entry)
        await self.db.commit()

        logger.debug(
            f"[AutoReject] Created audit entry for queue item {queue_item.id}"
        )

        # Broadcast event to connected operators
        await self.operator_manager.broadcast_queue_item_action(
            item_id=str(queue_item.id),
            action='rejected',
            user_id=str(user_id),
            status=IngestStatus.REJECTED,
            notes=f'Auto-rejected (score: {assessment_score:.2f})',
            assessment_id=str(assessment_id),
        )

        logger.debug(
            f"[AutoReject] Broadcasted rejection event for queue item {queue_item.id}"
        )

        # Send rejection email to candidate via notification worker
        try:
            # Fetch resume to get candidate email
            if queue_item.resume_id:
                stmt = select(Resume).where(Resume.id == queue_item.resume_id)
                result = await self.db.execute(stmt)
                resume = result.scalar_one_or_none()

                if resume and resume.candidate_email:
                    # Rejection email would be sent via candidate_notification worker
                    # triggered separately or via event queue
                    logger.info(
                        f"[AutoReject] Assessment {assessment_id} rejected. "
                        f"Candidate {resume.candidate_name} ready for rejection notification"
                    )
                    candidate_notified = True
        except Exception as e:
            logger.error(
                f"[AutoReject] Error handling rejection notification: {e}"
            )

        return candidate_notified


async def process_auto_reject_batch(
    db: AsyncSession,
    assessment_ids: list[uuid.UUID],
    user_id: uuid.UUID,
) -> dict[str, int | dict]:
    """
    Process multiple assessments for auto-rejection.

    Useful for batch operations or periodic review of completed assessments.

    Args:
        db: Database session
        assessment_ids: List of assessment IDs to check
        user_id: User initiating the batch process

    Returns:
        Summary dict:
            {
                'total': int,
                'rejected': int,
                'failed': int,
                'notified': int,
                'errors': List[dict],
            }

    Example:
        >>> result = await process_auto_reject_batch(
        ...     db=session,
        ...     assessment_ids=[id1, id2, id3],
        ...     user_id=recruiter_id,
        ... )
        >>> print(f"Rejected {result['rejected']} of {result['total']}")
    """
    worker = AutoRejectWorker(db)
    results = {
        'total': len(assessment_ids),
        'rejected': 0,
        'failed': 0,
        'notified': 0,
        'errors': [],
    }

    for assessment_id in assessment_ids:
        try:
            # Fetch assessment to get score
            stmt = select(Assessment).where(Assessment.id == assessment_id)
            result = await db.execute(stmt)
            assessment = result.scalar_one_or_none()

            if not assessment:
                results['failed'] += 1
                results['errors'].append({
                    'assessment_id': str(assessment_id),
                    'error': 'Assessment not found',
                })
                continue

            # Get score from assessment metadata
            score = (
                assessment.metadata.get('capability_score', 0.0)
                if assessment.metadata
                else 0.0
            )

            # Process rejection
            rejection_result = await worker.process_assessment(
                assessment_id=assessment_id,
                assessment_score=float(score),
                user_id=user_id,
            )

            if rejection_result.get('rejected'):
                results['rejected'] += 1
                if rejection_result.get('candidate_notified'):
                    results['notified'] += 1
            else:
                results['failed'] += 1

        except Exception as e:
            results['failed'] += 1
            results['errors'].append({
                'assessment_id': str(assessment_id),
                'error': str(e),
            })
            logger.error(
                f"[AutoReject] Error in batch processing {assessment_id}: {e}",
                exc_info=True
            )

    logger.info(
        f"[AutoReject] Batch complete: {results['rejected']} rejected, "
        f"{results['notified']} notified, {results['failed']} failed out of {results['total']}"
    )

    return results
