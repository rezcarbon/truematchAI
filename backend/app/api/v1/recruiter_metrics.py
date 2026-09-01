"""
Recruiter metrics and performance analytics
Tracks hiring performance, conversion rates, and efficiency metrics
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.deps import get_db, get_current_recruiter
from app.models import Application, User, Interview

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/recruiter-metrics", tags=["recruiter-metrics"])


@router.get("/{recruiter_id}")
async def get_recruiter_metrics(
    recruiter_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_recruiter),
):
    """
    Get metrics for a specific recruiter
    Returns: KPIs, conversion funnel, performance comparison
    """
    try:
        recruiter_uuid = UUID(recruiter_id)

        # Verify recruiter exists
        stmt = select(User).where(User.id == recruiter_uuid)
        result = await db.execute(stmt)
        recruiter = result.scalar_one_or_none()

        if not recruiter:
            raise HTTPException(status_code=404, detail="Recruiter not found")

        # Get all applications for this recruiter
        stmt = select(Application).where(Application.user_id == recruiter_uuid)
        result = await db.execute(stmt)
        applications = result.scalars().all()

        # Calculate metrics
        total_reviewed = len(applications)

        if total_reviewed == 0:
            return {
                "recruiter_id": str(recruiter_uuid),
                "recruiter_name": recruiter.email,
                "metrics": {
                    "candidates_reviewed": 0,
                    "interviews_scheduled": 0,
                    "offers_made": 0,
                    "hire_rate": 0.0,
                    "avg_time_to_hire": 0,
                    "avg_interviews_per_hire": 0.0,
                },
                "conversion_funnel": {
                    "applied": 0,
                    "phone_screen": 0,
                    "technical": 0,
                    "onsite": 0,
                    "offer": 0,
                    "hired": 0,
                },
            }

        # Count by stage
        stages = ["applied", "phone_screen", "technical", "onsite", "offer", "hired", "rejected"]
        stage_counts = {stage: len([a for a in applications if a.stage == stage]) for stage in stages}

        # Get interview count
        interview_ids = [a.id for a in applications]
        stmt = select(func.count(Interview.id)).where(
            Interview.application_id.in_(interview_ids)
        )
        result = await db.execute(stmt)
        interviews_scheduled = result.scalar() or 0

        hired = stage_counts.get("hired", 0)
        offers = stage_counts.get("offer", 0) + hired

        # Calculate hire rate
        hire_rate = (hired / total_reviewed * 100) if total_reviewed > 0 else 0.0

        # Calculate average time to hire
        hired_apps = [a for a in applications if a.stage == "hired"]
        if hired_apps:
            time_diffs = []
            for app in hired_apps:
                if app.created_at and app.stage_entered_at:
                    diff = (app.stage_entered_at - app.created_at).days
                    time_diffs.append(diff)
            avg_time_to_hire = int(sum(time_diffs) / len(time_diffs)) if time_diffs else 0
        else:
            avg_time_to_hire = 0

        # Calculate interviews per hire
        avg_interviews_per_hire = (
            interviews_scheduled / hired if hired > 0 else 0
        )

        metrics = {
            "recruiter_id": str(recruiter_uuid),
            "recruiter_name": recruiter.email,
            "metrics": {
                "candidates_reviewed": total_reviewed,
                "interviews_scheduled": interviews_scheduled,
                "offers_made": offers,
                "hire_rate": round(hire_rate, 1),
                "avg_time_to_hire": avg_time_to_hire,
                "avg_interviews_per_hire": round(avg_interviews_per_hire, 2),
            },
            "conversion_funnel": {
                "applied": stage_counts.get("applied", 0),
                "phone_screen": stage_counts.get("phone_screen", 0),
                "technical": stage_counts.get("technical", 0),
                "onsite": stage_counts.get("onsite", 0),
                "offer": stage_counts.get("offer", 0),
                "hired": hired,
            },
        }

        return metrics

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid recruiter ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching recruiter metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch recruiter metrics")


@router.get("/")
async def get_all_recruiter_metrics(
    position_id: str = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_recruiter),
):
    """
    Get metrics for all recruiters
    Optionally filter by position
    """
    try:
        # Get all recruiters (users who have created applications)
        stmt = select(User.id, User.email).distinct()
        result = await db.execute(stmt)
        recruiters = result.all()

        recruiter_metrics_list = []

        for recruiter_id, recruiter_email in recruiters:
            # Get applications for this recruiter
            stmt = select(Application).where(Application.user_id == recruiter_id)

            if position_id:
                try:
                    position_uuid = UUID(position_id)
                    stmt = stmt.where(Application.position_id == position_uuid)
                except ValueError:
                    pass

            result = await db.execute(stmt)
            applications = result.scalars().all()

            total_reviewed = len(applications)

            if total_reviewed == 0:
                continue

            # Count by stage
            stage_counts = {
                "applied": len([a for a in applications if a.stage == "applied"]),
                "phone_screen": len([a for a in applications if a.stage == "phone_screen"]),
                "technical": len([a for a in applications if a.stage == "technical"]),
                "onsite": len([a for a in applications if a.stage == "onsite"]),
                "offer": len([a for a in applications if a.stage == "offer"]),
                "hired": len([a for a in applications if a.stage == "hired"]),
            }

            # Get interview count
            app_ids = [a.id for a in applications]
            stmt = select(func.count(Interview.id)).where(
                Interview.application_id.in_(app_ids)
            )
            result = await db.execute(stmt)
            interviews_scheduled = result.scalar() or 0

            hired = stage_counts["hired"]
            offers = stage_counts["offer"] + hired

            hire_rate = (hired / total_reviewed * 100) if total_reviewed > 0 else 0.0

            hired_apps = [a for a in applications if a.stage == "hired"]
            if hired_apps:
                time_diffs = []
                for app in hired_apps:
                    if app.created_at and app.stage_entered_at:
                        diff = (app.stage_entered_at - app.created_at).days
                        time_diffs.append(diff)
                avg_time_to_hire = int(sum(time_diffs) / len(time_diffs)) if time_diffs else 0
            else:
                avg_time_to_hire = 0

            avg_interviews_per_hire = (
                interviews_scheduled / hired if hired > 0 else 0
            )

            recruiter_metrics_list.append({
                "recruiter_id": str(recruiter_id),
                "recruiter_name": recruiter_email,
                "metrics": {
                    "candidates_reviewed": total_reviewed,
                    "interviews_scheduled": interviews_scheduled,
                    "offers_made": offers,
                    "hire_rate": round(hire_rate, 1),
                    "avg_time_to_hire": avg_time_to_hire,
                    "avg_interviews_per_hire": round(avg_interviews_per_hire, 2),
                },
                "conversion_funnel": {
                    "applied": stage_counts["applied"],
                    "phone_screen": stage_counts["phone_screen"],
                    "technical": stage_counts["technical"],
                    "onsite": stage_counts["onsite"],
                    "offer": stage_counts["offer"],
                    "hired": hired,
                },
            })

        # Calculate team averages
        if recruiter_metrics_list:
            all_hire_rates = [m["metrics"]["hire_rate"] for m in recruiter_metrics_list]
            all_times = [m["metrics"]["avg_time_to_hire"] for m in recruiter_metrics_list]
            all_interviews = [m["metrics"]["avg_interviews_per_hire"] for m in recruiter_metrics_list]

            team_averages = {
                "hire_rate": round(sum(all_hire_rates) / len(all_hire_rates), 1),
                "time_to_hire": round(sum(all_times) / len(all_times), 1),
                "reviews_per_hire": round(sum(all_interviews) / len(all_interviews), 2),
            }
        else:
            team_averages = {
                "hire_rate": 0.0,
                "time_to_hire": 0.0,
                "reviews_per_hire": 0.0,
            }

        return {
            "recruiters": recruiter_metrics_list,
            "team_averages": team_averages,
        }

    except Exception as e:
        logger.error(f"Error fetching recruiter metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch recruiter metrics")
