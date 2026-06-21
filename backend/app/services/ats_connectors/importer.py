"""Connector-agnostic import of normalized ATS data into the platform.

Consumes ``NormalizedJob`` / ``NormalizedCandidate`` (whatever the connector
produced) and upserts them as Position / Resume+Application rows. Idempotent
via ``external_ref`` (``<provider>:job:<id>`` / ``<provider>:candidate:<id>``):
re-importing updates instead of duplicating. Imported candidates are attributed
to the importing recruiter (Resume.user_id) since they have no platform account.
No external network here — fully unit-testable.
"""
from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import Application
from app.models.position import Position
from app.models.resume import Resume
from app.models.user import User
from app.services.ats_connectors.base import NormalizedCandidate, NormalizedJob

logger = logging.getLogger("truematch.ats.importer")


async def import_jobs(
    db: AsyncSession, provider: str, jobs: list[NormalizedJob], actor: User
) -> dict:
    created = updated = 0
    for job in jobs:
        ref = f"{provider}:job:{job.external_id}"
        existing = (
            await db.scalars(select(Position).where(Position.external_ref == ref))
        ).first()
        if existing:
            existing.title = job.title[:255]
            existing.description = job.description
            updated += 1
        else:
            db.add(
                Position(
                    created_by=actor.id,
                    company_id=actor.company_id,
                    title=job.title[:255],
                    description=job.description,
                    external_ref=ref,
                )
            )
            created += 1
    await db.flush()
    logger.info("ATS job import (%s): +%d new, %d updated", provider, created, updated)
    return {"provider": provider, "jobs_created": created, "jobs_updated": updated}


async def import_candidates(
    db: AsyncSession, provider: str, candidates: list[NormalizedCandidate], actor: User
) -> dict:
    created = updated = skipped_no_job = 0
    for cand in candidates:
        # The candidate must map to a job we've imported, so we can attach an
        # Application to the right Position.
        position = None
        if cand.job_external_id:
            position = (
                await db.scalars(
                    select(Position).where(
                        Position.external_ref == f"{provider}:job:{cand.job_external_id}"
                    )
                )
            ).first()

        cand_ref = f"{provider}:candidate:{cand.external_id}"
        resume = (
            await db.scalars(
                select(Resume).where(Resume.file_id == cand_ref)
            )
        ).first()
        supplementary = {
            "intake": "ats",
            "provider": provider,
            "external_ref": cand_ref,
            "candidate_name": cand.name,
            "candidate_email": cand.email,
            "tags": cand.tags,
            "extracted_text": cand.summary,
        }
        if resume:
            resume.supplementary = supplementary
            updated += 1
        else:
            resume = Resume(
                user_id=actor.id,
                file_id=cand_ref,
                file_type="ats_import",
                supplementary=supplementary,
            )
            db.add(resume)
            created += 1
        await db.flush()

        if position is None:
            skipped_no_job += 1
            continue
        app_ref = f"{provider}:application:{cand.external_id}"
        existing_app = (
            await db.scalars(select(Application).where(Application.external_ref == app_ref))
        ).first()
        if existing_app is None:
            db.add(
                Application(
                    resume_id=resume.id,
                    position_id=position.id,
                    user_id=actor.id,
                    source=provider,
                    external_ref=app_ref,
                )
            )
    await db.flush()
    logger.info(
        "ATS candidate import (%s): +%d new, %d updated, %d without a matched job",
        provider, created, updated, skipped_no_job,
    )
    return {
        "provider": provider,
        "candidates_created": created,
        "candidates_updated": updated,
        "candidates_without_job": skipped_no_job,
    }
