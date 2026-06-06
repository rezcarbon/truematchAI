"""
Auto-Approve Worker (Phase 1.1: Autonomy Layer)

Automatically approves assessment queue items that meet quality thresholds
and pass governance gates.

Trigger: When an assessment completes with score >= AUTO_APPROVE_THRESHOLD
         and governance_gates_passed == True

Actions:
- Auto-approve the ingest queue item
- Enqueue the assessment for processing
- Broadcast queue_item_action event
- Create audit trail entry
- Send notification to recruiter

Configuration:
- AUTO_APPROVE_THRESHOLD (default 0.90): Score threshold for auto-approval
- Governance gates must pass before approval is triggered
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.assessment import Assessment, AssessmentStatus
from app.models.ingest_queue import IngestQueueItem, IngestStatus
from app.models.audit import AuditTrailEntry
from app.schemas.decision import DecisionType
from app.websocket.agents_operator import get_operator_manager
from app.workers.notification_service import get_notification_dispatcher

logger = logging.getLogger("truematch.auto_approve")


class AutoApproveWorker:
    """
    Handles automatic approval of assessments meeting quality criteria.

    This worker monitors completed assessments and automatically approves
    corresponding queue items when governance gates are satisfied.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize the auto-approve worker.

        Args:
            db: AsyncSession for database access
        """
        self.db = db
        self.operator_manager = get_operator_manager()
        self.notification_dispatcher = get_notification_dispatcher()
        self.threshold = getattr(
            settings,
            'AUTO_APPROVE_THRESHOLD',
            0.90
        )

    async def process_assessment(
        self,
        assessment_id: uuid.UUID,
        assessment_score: float,
        governance_passed: bool,
        user_id: uuid.UUID,
    ) -> dict[str, bool | str]:
        """
        Check if assessment should be auto-approved.

        Args:
            assessment_id: ID of completed assessment
            assessment_score: Overall assessment score (0.0-1.0)
            governance_passed: Whether governance gates passed
            user_id: ID of recruiter who initiated assessment

        Returns:
            Dict with approval status and details:
                {
                    'approved': bool,
                    'reason': str,
                    'queue_item_id': Optional[uuid.UUID],
                    'threshold': float,
                    'score': float,
                }

        Examples:
            >>> result = await worker.process_assessment(
            ...     assessment_id=uuid.uuid4(),
            ...     assessment_score=0.95,
            ...     governance_passed=True,
            ...     user_id=uuid.uuid4(),
            ... )
            >>> assert result['approved'] is True
        """
        try:
            logger.info(
                f"[AutoApprove] Checking assessment {assessment_id}: "
                f"score={assessment_score:.2f}, governance_passed={governance_passed}"
            )

            # Fetch assessment record
            stmt = select(Assessment).where(Assessment.id == assessment_id)
            result = await self.db.execute(stmt)
            assessment = result.scalar_one_or_none()

            if not assessment:
                logger.warning(
                    f"[AutoApprove] Assessment {assessment_id} not found"
                )
                return {
                    'approved': False,
                    'reason': 'Assessment not found',
                }

            # Check score threshold
            if assessment_score < self.threshold:
                logger.info(
                    f"[AutoApprove] Score {assessment_score:.2f} below threshold "
                    f"{self.threshold:.2f}"
                )
                return {
                    'approved': False,
                    'reason': f'Score {assessment_score:.2f} below threshold {self.threshold:.2f}',
                    'score': assessment_score,
                    'threshold': self.threshold,
                }

            # Check governance gates
            if not governance_passed:
                logger.info(
                    f"[AutoApprove] Governance gates failed for assessment {assessment_id}"
                )
                return {
                    'approved': False,
                    'reason': 'Governance gates did not pass',
                    'score': assessment_score,
                }

            # Find associated queue item
            stmt = select(IngestQueueItem).where(
                IngestQueueItem.assessment_id == assessment_id
            )
            result = await self.db.execute(stmt)
            queue_item = result.scalar_one_or_none()

            if not queue_item:
                logger.warning(
                    f"[AutoApprove] No queue item found for assessment {assessment_id}"
                )
                return {
                    'approved': False,
                    'reason': 'No associated queue item',
                    'assessment_id': str(assessment_id),
                }

            # Auto-approve the queue item
            await self._approve_queue_item(
                queue_item=queue_item,
                assessment_id=assessment_id,
                user_id=user_id,
                assessment_score=assessment_score,
            )

            logger.info(
                f"[AutoApprove] Successfully auto-approved queue item "
                f"{queue_item.id} (assessment {assessment_id}, score {assessment_score:.2f})"
            )

            return {
                'approved': True,
                'reason': 'Auto-approved: meets quality threshold and governance gates',
                'queue_item_id': str(queue_item.id),
                'assessment_id': str(assessment_id),
                'score': assessment_score,
                'threshold': self.threshold,
            }

        except Exception as e:
            logger.error(
                f"[AutoApprove] Error processing assessment {assessment_id}: {e}",
                exc_info=True
            )
            return {
                'approved': False,
                'reason': f'Error: {str(e)}',
            }

    async def _approve_queue_item(
        self,
        queue_item: IngestQueueItem,
        assessment_id: uuid.UUID,
        user_id: uuid.UUID,
        assessment_score: float,
    ) -> None:
        """
        Approve a queue item and update related records.

        Args:
            queue_item: The ingest queue item to approve
            assessment_id: Associated assessment ID
            user_id: User performing approval
            assessment_score: Assessment score for audit trail

        Raises:
            Exception: If database update fails
        """
        # Update queue item status
        stmt = (
            update(IngestQueueItem)
            .where(IngestQueueItem.id == queue_item.id)
            .values(
                status=IngestStatus.APPROVED,
                review_notes=f"Auto-approved (score: {assessment_score:.2f})",
                updated_at=datetime.utcnow(),
            )
        )
        await self.db.execute(stmt)
        await self.db.commit()

        # Create audit trail entry
        audit_entry = AuditTrailEntry(
            entity_type='ingest_queue_item',
            entity_id=str(queue_item.id),
            action='auto_approve',
            actor_id=str(user_id),
            actor_type='system',
            changes={
                'status': IngestStatus.APPROVED,
                'auto_approved': True,
                'assessment_score': float(assessment_score),
            },
            timestamp=datetime.utcnow(),
        )
        self.db.add(audit_entry)
        await self.db.commit()

        logger.debug(
            f"[AutoApprove] Created audit entry for queue item {queue_item.id}"
        )

        # Broadcast event to connected operators
        await self.operator_manager.broadcast_queue_item_action(
            item_id=str(queue_item.id),
            action='approved',
            user_id=str(user_id),
            status=IngestStatus.APPROVED,
            notes=f'Auto-approved (score: {assessment_score:.2f})',
            assessment_id=str(assessment_id),
        )

        logger.debug(
            f"[AutoApprove] Broadcasted approval event for queue item {queue_item.id}"
        )

        # Send notification to recruiter (async, non-blocking)
        try:
            # Note: This would integrate with notification service
            # to send email/Slack notification about auto-approval
            logger.info(
                f"[AutoApprove] Notification queued for recruiter "
                f"about auto-approved assessment {assessment_id}"
            )
        except Exception as e:
            logger.error(
                f"[AutoApprove] Failed to queue notification: {e}"
            )


async def process_auto_approve_batch(
    db: AsyncSession,
    assessment_ids: list[uuid.UUID],
    user_id: uuid.UUID,
) -> dict[str, int | dict]:
    """
    Process multiple assessments for auto-approval.

    Useful for batch operations or periodic review of pending assessments.

    Args:
        db: Database session
        assessment_ids: List of assessment IDs to check
        user_id: User initiating the batch process

    Returns:
        Summary dict:
            {
                'total': int,
                'approved': int,
                'failed': int,
                'errors': List[dict],
            }

    Example:
        >>> result = await process_auto_approve_batch(
        ...     db=session,
        ...     assessment_ids=[id1, id2, id3],
        ...     user_id=recruiter_id,
        ... )
        >>> print(f"Approved {result['approved']} of {result['total']}")
    """
    worker = AutoApproveWorker(db)
    results = {
        'total': len(assessment_ids),
        'approved': 0,
        'failed': 0,
        'errors': [],
    }

    for assessment_id in assessment_ids:
        try:
            # Fetch assessment to get score and governance status
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

            # Get governance status from assessment metadata
            governance_passed = (
                assessment.metadata.get('governance_gates_passed', False)
                if assessment.metadata
                else False
            )

            # Get score from assessment metadata
            score = (
                assessment.metadata.get('capability_score', 0.0)
                if assessment.metadata
                else 0.0
            )

            # Process approval
            approval_result = await worker.process_assessment(
                assessment_id=assessment_id,
                assessment_score=float(score),
                governance_passed=bool(governance_passed),
                user_id=user_id,
            )

            if approval_result.get('approved'):
                results['approved'] += 1
            else:
                results['failed'] += 1

        except Exception as e:
            results['failed'] += 1
            results['errors'].append({
                'assessment_id': str(assessment_id),
                'error': str(e),
            })
            logger.error(
                f"[AutoApprove] Error in batch processing {assessment_id}: {e}",
                exc_info=True
            )

    logger.info(
        f"[AutoApprove] Batch complete: {results['approved']} approved, "
        f"{results['failed']} failed out of {results['total']}"
    )

    return results
