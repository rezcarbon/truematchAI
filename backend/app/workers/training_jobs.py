"""
Background job processor for training system.

Handles asynchronous processing of training data uploads.
"""
import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.engines.training_data_parser import TrainingDataParser
from app.engines.training_auto_learner import TrainingAutoLearner
from app.models.training_data import TrainingDataUpload, TrainingDataItem
from app.database import get_session

logger = logging.getLogger(__name__)


class TrainingJobProcessor:
    """Process training uploads asynchronously."""

    def __init__(self):
        self.parser = TrainingDataParser()
        self.learner = TrainingAutoLearner()

    async def process_upload(self, upload_id: UUID, file_content: bytes, db: AsyncSession):
        """
        Process a training data upload.

        Args:
            upload_id: Upload record ID
            file_content: Raw file bytes
            db: Database session
        """
        upload = None
        try:
            # Get upload record
            from sqlalchemy import select

            query = select(TrainingDataUpload).where(TrainingDataUpload.id == upload_id)
            result = await db.execute(query)
            upload = result.scalar_one_or_none()

            if not upload:
                logger.error(f"Upload not found: {upload_id}")
                return

            # Update status to processing
            upload.status = "processing"
            await db.commit()

            logger.info(f"Starting upload processing: {upload_id}")

            # Parse file
            parsed_items, parse_errors = await self.parser.parse_file(
                file_content, upload.filename, upload.format
            )

            if parse_errors:
                logger.warning(f"Parse errors: {len(parse_errors)}", extra={"errors": parse_errors})

            upload.row_count = len(parsed_items)
            upload.items_failed = len(parse_errors)

            # Create TrainingDataItem records
            training_items = []
            for i, item in enumerate(parsed_items, 1):
                training_item = TrainingDataItem(
                    upload_id=upload_id,
                    candidate_name=item.get("candidate_name"),
                    candidate_email=item.get("candidate_email"),
                    candidate_profile=item,
                    decision=item.get("decision"),
                    reasoning=item.get("reasoning"),
                    rating=item.get("rating"),
                    skills=item.get("skills", []),
                    extracted_capabilities=[],
                    extracted_credentials=[],
                    capability_confidence=0.0,
                    source_row=i,
                )
                training_items.append(training_item)
                db.add(training_item)

            upload.items_processed = len(training_items)
            await db.commit()

            logger.info(
                f"Created {len(training_items)} training items",
                extra={"upload_id": str(upload_id)},
            )

            # Run auto-learning
            insights = await self.learner.process_training_items(training_items, db)

            logger.info(
                f"Auto-learning completed",
                extra={
                    "upload_id": str(upload_id),
                    "capabilities": len(insights.get("new_capabilities", [])),
                    "patterns": len(insights.get("success_patterns", [])),
                },
            )

            # Update virtual brain state
            batch = await self.learner.update_virtual_brain_state(upload_id, insights, db)

            if batch:
                upload.insights_extracted = len(insights.get("insights", []))

            # Mark all items as applied to training
            for item in training_items:
                item.applied_to_training = True
                item.applied_at = __import__("datetime").datetime.utcnow()

            # Update upload status to completed
            upload.status = "completed"
            upload.completed_at = __import__("datetime").datetime.utcnow()
            await db.commit()

            logger.info(
                f"Upload processing completed successfully",
                extra={"upload_id": str(upload_id)},
            )

        except Exception as e:
            logger.error(
                f"Error processing upload",
                extra={"upload_id": str(upload_id), "error": str(e)},
            )
            if upload:
                upload.status = "failed"
                upload.error_message = str(e)
                try:
                    await db.commit()
                except Exception as commit_error:
                    logger.error(f"Error updating upload status: {commit_error}")


# Synchronous wrapper for background job execution
def process_training_upload_sync(upload_id: UUID, file_content: bytes):
    """Synchronous wrapper for background processing."""
    import asyncio

    processor = TrainingJobProcessor()

    # Create a new event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        # Create async session factory
        async_engine = create_async_engine(settings.database_url, echo=False)
        async_session = sessionmaker(
            async_engine, class_=AsyncSession, expire_on_commit=False
        )

        async def run():
            async with async_session() as session:
                await processor.process_upload(upload_id, file_content, session)

        loop.run_until_complete(run())
    finally:
        loop.close()
