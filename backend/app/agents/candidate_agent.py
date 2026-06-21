"""Candidate Career Coach Agent for CV analysis and job matching."""
import logging

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.enhanced_agent import EnhancedBaseAgent
from app.models.user import User
from app.models.resume import Resume
from app.models.application import Application
from app.models.position import Position

logger = logging.getLogger(__name__)


CANDIDATE_INSTRUCTIONS = """You are the TrueMatch Career Coach. Your job is to help candidates advance their careers.

You can help with:
1. **CV Analysis**: Analyze CVs, identify strengths and gaps
2. **Job Matching**: Find jobs that match the candidate's profile
3. **Skill Development**: Identify skills needed for target roles
4. **CV Optimization**: Suggest improvements and rewording
5. **Career Guidance**: Help with career trajectory and growth
6. **Application Tracking**: Track applications and status
7. **Interview Prep**: Prepare for interviews, mock questions

CAPABILITIES:
- Analyze CV and extract skills, experience, achievements
- Identify skill gaps for target roles
- Find matching jobs from the database
- Suggest CV improvements and better phrasing
- Analyze career trajectory and growth opportunities
- Provide market positioning insights
- Track application status and next steps
- Recommend roles based on profile

PROACTIVE BEHAVIORS:
- After CV upload, offer to analyze it
- Ask about career goals and target roles
- Suggest specific skill improvements
- Alert about new matching job opportunities
- Track application progress
- Provide encouragement and guidance

COMMUNICATION STYLE:
- Be a supportive career coach
- Use specific, actionable advice
- Reference their actual CV/experience
- Show opportunities that match their profile
- Celebrate progress and improvements
- Provide confidence and clarity

When a candidate uploads their CV:
1. Confirm receipt and do quick analysis
2. Ask about their career goals
3. Ask about target roles or seniority level
4. Offer to find matching jobs
5. Suggest CV improvements if needed

When discussing career goals:
1. Ask about target role, seniority, industry
2. Assess current skills vs. target requirements
3. Identify skill gaps
4. Suggest how to close gaps
5. Find matching jobs

When showing job matches:
1. Show top matching positions
2. Explain why they're a good fit
3. Highlight any skill gaps for specific roles
4. Suggest improvements for better fit
5. Offer to help with applications

Always be encouraging and practical - candidates should feel empowered to advance their careers."""


class CandidateAgent(EnhancedBaseAgent):
    """Agent that helps candidates with career development and job matching."""

    def __init__(self):
        super().__init__(
            role="candidate",
            instructions=CANDIDATE_INSTRUCTIONS,
        )

    async def _load_role_context(self, user: User, db: AsyncSession) -> dict:
        """Load candidate-specific context: CVs, applications, recommendations.

        Args:
            user: User object
            db: Database session

        Returns:
            Dict with candidate context
        """

        context = {
            "capabilities": [
                "cv_analysis",
                "skill_assessment",
                "job_matching",
                "market_positioning",
                "career_guidance",
            ],
        }

        try:
            # Load uploaded CVs for this candidate
            cvs_stmt = select(Resume).where(Resume.user_id == user.id)
            result = await db.execute(cvs_stmt)
            cvs = result.scalars().all()

            uploaded_cvs = [
                {
                    "id": str(cv.id),
                    "file_type": cv.file_type or "unknown",
                    "created_at": cv.created_at.isoformat() if cv.created_at else None,
                    "has_parsed_data": bool(cv.parsed_data),
                }
                for cv in cvs
            ]

            # Load applied jobs (applications)
            applications_stmt = (
                select(Application, Position)
                .join(Position)
                .where(Application.user_id == user.id)
                .order_by(Application.applied_at.desc())
                .limit(5)
            )
            result = await db.execute(applications_stmt)
            applications = result.all()

            applied_jobs = [
                {
                    "position_title": pos.title,
                    "stage": app.stage.value,
                    "applied_at": app.applied_at.isoformat() if app.applied_at else None,
                }
                for app, pos in applications
            ]

            # Get pipeline breakdown
            pipeline_stmt = (
                select(
                    Application.stage,
                    select(func.count(Application.id))
                    .where(Application.user_id == user.id)
                    .correlate(None)
                    .scalar_subquery(),
                )
                .where(Application.user_id == user.id)
                .distinct()
            )
            result = await db.execute(pipeline_stmt)
            stages = {stage.value: count for stage, count in result.all()}

            context.update({
                "cv_count": len(uploaded_cvs),
                "uploaded_cvs": uploaded_cvs,
                "applications_count": len(applied_jobs),
                "applied_jobs": applied_jobs,
                "pipeline_breakdown": stages,
            })

            logger.info(
                "Loaded candidate context",
                extra={
                    "user_id": str(user.id),
                    "cv_count": len(uploaded_cvs),
                    "applications": len(applied_jobs),
                },
            )

        except Exception as e:
            logger.error(f"Failed to load candidate context: {e}")
            context.update({
                "uploaded_cvs": [],
                "applied_jobs": [],
                "pipeline_breakdown": {},
            })

        return context

    def _format_context(self, user_context: dict) -> str:
        """Format candidate context for system prompt."""
        capabilities = user_context.get("capabilities", [])
        return f"""
- Capabilities Available: {', '.join(capabilities)}
- Your CVs: {user_context.get('uploaded_cvs', 'N/A')}
- Applied Jobs: {user_context.get('applied_jobs', 'N/A')}
- Recommendations: {user_context.get('recommendations', 'N/A')}

Focus on helping with career development, CV improvement, and job matching."""
