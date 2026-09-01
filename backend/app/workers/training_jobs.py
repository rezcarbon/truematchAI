"""
Background job processor for training system.

Handles asynchronous processing of training data uploads.
"""
import asyncio
from app.core.clock import utcnow
import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.engines.training_data_parser import TrainingDataParser
from app.engines.training_auto_learner import TrainingAutoLearner
from app.models.training_data import TrainingDataUpload, TrainingDataItem

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

            logger.info(f"Looking up upload record: {upload_id}")
            query = select(TrainingDataUpload).where(TrainingDataUpload.id == upload_id)
            result = await db.execute(query)
            upload = result.scalar_one_or_none()

            if not upload:
                logger.error(f"Upload not found: {upload_id}")
                return

            logger.info("Found upload record, updating status to processing")
            # Update status to processing
            upload.status = "processing"
            await db.commit()

            logger.info(f"Starting upload processing: {upload_id}")

            # Emit progress event: parsing file
            logger.info(
                "Progress: Parsing training file",
                extra={"upload_id": str(upload_id), "filename": upload.filename},
            )

            # Parse file
            logger.info(f"Parsing file: {upload.filename} ({upload.format})")
            parsed_items, parse_errors = await self.parser.parse_file(
                file_content, upload.filename, upload.format
            )
            logger.info(f"Parsing complete: {len(parsed_items)} items, {len(parse_errors)} errors")

            if parse_errors:
                logger.warning(f"Parse errors: {len(parse_errors)}", extra={"errors": parse_errors})

            upload.row_count = len(parsed_items)
            upload.items_failed = len(parse_errors)

            # Emit progress event: creating training items
            logger.info(
                f"Progress: Creating {len(parsed_items)} training items",
                extra={"upload_id": str(upload_id), "item_count": len(parsed_items)},
            )

            # Create TrainingDataItem records
            training_items = []
            for i, item in enumerate(parsed_items, 1):
                # Parse skills from CSV into extracted_capabilities
                skills = item.get("skills", "")
                if isinstance(skills, str):
                    # Remove quotes and split by comma
                    skills = [s.strip() for s in skills.strip('"').split(",") if s.strip()]
                elif not isinstance(skills, list):
                    skills = []

                training_item = TrainingDataItem(
                    upload_id=upload_id,
                    candidate_name=item.get("candidate_name"),
                    candidate_email=item.get("candidate_email"),
                    candidate_profile=item,
                    decision=item.get("decision"),
                    reasoning=item.get("reasoning"),
                    rating=item.get("rating"),
                    experience_years=item.get("experience_years"),
                    skills=skills,
                    education=item.get("education"),
                    extracted_capabilities=skills,
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

            # Emit progress event: running auto-learning
            logger.info(
                "Progress: Running auto-learning analysis",
                extra={"upload_id": str(upload_id), "item_count": len(training_items)},
            )

            # Run auto-learning
            insights = await self.learner.process_training_items(training_items, db)

            logger.info(
                "Auto-learning completed",
                extra={
                    "upload_id": str(upload_id),
                    "capabilities": len(insights.get("new_capabilities", [])),
                    "patterns": len(insights.get("success_patterns", [])),
                },
            )

            # Emit progress event: updating virtual brain
            logger.info(
                f"Progress: Updating virtual brain with {len(insights.get('new_capabilities', []))} capabilities",
                extra={"upload_id": str(upload_id)},
            )

            # Update virtual brain state
            batch = await self.learner.update_virtual_brain_state(upload_id, insights, db)

            if batch:
                upload.insights_extracted = len(insights.get("insights", []))
                logger.info(
                    f"Virtual brain state updated with {len(insights.get('insights', []))} insights",
                    extra={"upload_id": str(upload_id)},
                )

            # Mark all items as applied to training
            for item in training_items:
                item.applied_to_training = True
                item.applied_at = utcnow()

            # Update upload status to completed
            upload.status = "completed"
            upload.completed_at = utcnow()
            await db.commit()

            logger.info(
                "Upload processing completed successfully",
                extra={"upload_id": str(upload_id)},
            )

        except Exception as e:
            # Write full error details to both logger and a debug file
            import traceback
            error_details = traceback.format_exc()

            logger.error(f"Error processing upload: {str(e)}")
            logger.error(f"Traceback:\n{error_details}")

            # Also write to a file for debugging
            with open('/tmp/training_upload_error.log', 'a') as f:
                f.write(f"\n=== Upload Error {upload_id} ===\n")
                f.write(f"{error_details}\n")

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
