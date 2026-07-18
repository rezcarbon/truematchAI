"""Complete Career Coaching API Implementation."""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional
from math import ceil

from fastapi import APIRouter, Query, status, HTTPException
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, AccessDeniedError
from app.deps import CurrentUser, DBSession
from app.models.career_coach import (
    CareerCoaching,
    CareerGoal,
    PersonalizedCareerPlan,
    SkillAssessment,
    InterviewPrepSession,
    CoachingSession,
    CoachQuestion,
    CoachingProgressReport,
)
from app.schemas.career_coach import (
    RequestCareerCoachingRequest,
    CareerGoalRequest,
    UpdateCareerGoalRequest,
    PersonalizedPlanRequest,
    SkillAssessmentRequest,
    InterviewPrepSessionRequest,
    CareerCoachingResponse,
    CareerGoalResponse,
    CareerGoalListResponse,
    PersonalizedCareerPlan as PersonalizedCareerPlanSchema,
    SkillAssessmentResult,
    SkillAssessmentListResponse,
    CoachingSessionResponse,
    InterviewPrepSessionResponse,
    AskCoachQuestion,
    CoachResponse,
    CoachingProgressReport as CoachingProgressReportSchema,
    ScheduleCoachingSessionRequest,
    GoalStatus,
    SessionStatus,
)
from app.services.career_coach_service import CareerCoachService

router = APIRouter(prefix="/candidates/career-coach", tags=["career-coach"])
logger = logging.getLogger("truematch.career_coach")


# ─────────────────────────────────────────────────────────────────────────
# Helper Functions
# ─────────────────────────────────────────────────────────────────────────

def verify_ownership(user_id: uuid.UUID, record_user_id: uuid.UUID) -> None:
    """Verify user owns the record."""
    if record_user_id != user_id:
        raise AccessDeniedError("You do not have permission to access this resource")


async def paginate_query(db: AsyncSession, query, page: int, page_size: int):
    """Apply pagination to query."""
    total = (await db.execute(select(func.count()).select_from(query.froms[0]).where(*(query.whereclause.clauses if query.whereclause is not None else [])))).scalar() or 0
    pages = ceil(total / page_size)

    query = query.offset((page - 1) * page_size).limit(page_size)
    items = (await db.execute(query)).scalars().all()

    return items, total, pages


# ─────────────────────────────────────────────────────────────────────────
# Career Goals Endpoints
# ─────────────────────────────────────────────────────────────────────────

@router.post(
    "/goals",
    response_model=CareerGoalResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Set a career goal",
)
async def create_career_goal(
    payload: CareerGoalRequest,
    user: CurrentUser,
    db: DBSession,
) -> CareerGoalResponse:
    """Create a new career goal."""
    try:
        goal = CareerGoal(
            user_id=user.id,
            goal_title=payload.goal_title,
            goal_description=payload.goal_description,
            target_date=payload.target_date,
            status=GoalStatus.NOT_STARTED,
            progress_percentage=0,
            success_criteria=json.dumps(payload.success_criteria),
            milestones=json.dumps(payload.milestones or []),
            related_coaching_areas=json.dumps([area.value for area in payload.related_coaching_areas]),
            priority=payload.priority,
        )
        db.add(goal)
        await db.flush()

        return CareerGoalResponse(
            goal_id=goal.id,
            goal_title=goal.goal_title,
            goal_description=goal.goal_description,
            status=goal.status,
            target_date=goal.target_date,
            progress_percentage=goal.progress_percentage,
            related_coaching_areas=payload.related_coaching_areas,
            created_at=goal.created_at,
            updated_at=goal.updated_at,
            completion_date=goal.completion_date,
        )
    except Exception as e:
        logger.error(f"Failed to create career goal: {e}")
        raise HTTPException(status_code=500, detail="Failed to create career goal")


@router.get("/goals/{goal_id}", response_model=CareerGoalResponse)
async def get_career_goal(
    goal_id: uuid.UUID,
    user: CurrentUser,
    db: DBSession,
) -> CareerGoalResponse:
    """Get details of a career goal."""
    goal = await db.get(CareerGoal, goal_id)
    if not goal:
        raise NotFoundError(f"Career goal {goal_id} not found")

    verify_ownership(user.id, goal.user_id)

    return CareerGoalResponse(
        goal_id=goal.id,
        goal_title=goal.goal_title,
        goal_description=goal.goal_description,
        status=goal.status,
        target_date=goal.target_date,
        progress_percentage=goal.progress_percentage,
        related_coaching_areas=json.loads(goal.related_coaching_areas),
        created_at=goal.created_at,
        updated_at=goal.updated_at,
        completion_date=goal.completion_date,
    )


@router.get("/goals", response_model=CareerGoalListResponse)
async def list_career_goals(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    filter_status: Optional[str] = Query(None),
    user: CurrentUser = None,
    db: DBSession = None,
) -> CareerGoalListResponse:
    """List user's career goals."""
    query = select(CareerGoal).where(CareerGoal.user_id == user.id)

    if filter_status:
        query = query.where(CareerGoal.status == filter_status)

    query = query.order_by(desc(CareerGoal.created_at))

    items, total, pages = await paginate_query(db, query, page, page_size)

    return CareerGoalListResponse(
        items=[
            CareerGoalResponse(
                goal_id=g.id,
                goal_title=g.goal_title,
                goal_description=g.goal_description,
                status=g.status,
                target_date=g.target_date,
                progress_percentage=g.progress_percentage,
                related_coaching_areas=json.loads(g.related_coaching_areas),
                created_at=g.created_at,
                updated_at=g.updated_at,
                completion_date=g.completion_date,
            )
            for g in items
        ],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.put("/goals/{goal_id}", response_model=CareerGoalResponse)
async def update_career_goal(
    goal_id: uuid.UUID,
    payload: UpdateCareerGoalRequest,
    user: CurrentUser,
    db: DBSession,
) -> CareerGoalResponse:
    """Update a career goal."""
    goal = await db.get(CareerGoal, goal_id)
    if not goal:
        raise NotFoundError(f"Career goal {goal_id} not found")

    verify_ownership(user.id, goal.user_id)

    if payload.goal_title:
        goal.goal_title = payload.goal_title
    if payload.goal_description:
        goal.goal_description = payload.goal_description
    if payload.target_date:
        goal.target_date = payload.target_date
    if payload.status:
        goal.status = payload.status
        if payload.status == GoalStatus.COMPLETED:
            goal.completion_date = datetime.now(timezone.utc)
    if payload.success_criteria:
        goal.success_criteria = json.dumps(payload.success_criteria)
    if payload.milestones:
        goal.milestones = json.dumps(payload.milestones)
    if payload.progress_notes:
        goal.progress_notes = payload.progress_notes

    await db.flush()

    return CareerGoalResponse(
        goal_id=goal.id,
        goal_title=goal.goal_title,
        goal_description=goal.goal_description,
        status=goal.status,
        target_date=goal.target_date,
        progress_percentage=goal.progress_percentage,
        related_coaching_areas=json.loads(goal.related_coaching_areas),
        created_at=goal.created_at,
        updated_at=goal.updated_at,
        completion_date=goal.completion_date,
    )


@router.delete("/goals/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_career_goal(
    goal_id: uuid.UUID,
    user: CurrentUser,
    db: DBSession,
) -> None:
    """Delete a career goal."""
    goal = await db.get(CareerGoal, goal_id)
    if not goal:
        raise NotFoundError(f"Career goal {goal_id} not found")

    verify_ownership(user.id, goal.user_id)

    await db.delete(goal)


# ─────────────────────────────────────────────────────────────────────────
# Career Plans Endpoints
# ─────────────────────────────────────────────────────────────────────────

@router.post(
    "/plans",
    response_model=PersonalizedCareerPlanSchema,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Generate personalized career plan",
)
async def generate_career_plan(
    payload: PersonalizedPlanRequest,
    user: CurrentUser,
    db: DBSession,
) -> PersonalizedCareerPlanSchema:
    """Generate a personalized career plan."""
    service = CareerCoachService(db)

    try:
        # Call AI service to generate plan
        prompt = f"""Generate a personalized {payload.timeframe_months}-month career development plan for someone with:
- Current skills: {', '.join(payload.current_skills)}
- Career goals: {', '.join(payload.career_goals)}
- Target roles: {', '.join(payload.target_roles)}
- Target industries: {', '.join(payload.industries or ['Any'])}
- Constraints: {', '.join(payload.constraints or ['None'])}

Provide a comprehensive plan with:
1. Overall strategy
2. Immediate actions (next 30 days)
3. Skill development roadmap
4. Networking recommendations
5. Learning resources with URLs
6. Industry insights
7. Market positioning strategy

Format as JSON with these exact keys: overall_strategy, immediate_actions, skill_development_roadmap, networking_recommendations, learning_resources, industry_insights, market_positioning_strategy"""

        plan_data = await service._call_claude_api(prompt)

        try:
            plan_json = json.loads(plan_data)
        except json.JSONDecodeError:
            plan_json = {
                "overall_strategy": plan_data[:500],
                "immediate_actions": [],
                "skill_development_roadmap": {},
                "networking_recommendations": [],
                "learning_resources": [],
                "industry_insights": "",
                "market_positioning_strategy": "",
            }

        plan = PersonalizedCareerPlan(
            user_id=user.id,
            timeframe_months=payload.timeframe_months,
            overall_strategy=plan_json.get("overall_strategy", ""),
            immediate_actions=json.dumps(plan_json.get("immediate_actions", [])),
            skill_development_roadmap=json.dumps(plan_json.get("skill_development_roadmap", {})),
            networking_recommendations=json.dumps(plan_json.get("networking_recommendations", [])),
            learning_resources=json.dumps(plan_json.get("learning_resources", [])),
            industry_insights=plan_json.get("industry_insights", ""),
            market_positioning_strategy=plan_json.get("market_positioning_strategy", ""),
            short_term_goals=json.dumps([]),
            long_term_goals=json.dumps([]),
        )
        db.add(plan)
        await db.flush()

        return PersonalizedCareerPlanSchema(
            plan_id=plan.id,
            timeframe_months=plan.timeframe_months,
            overall_strategy=plan.overall_strategy,
            immediate_actions=json.loads(plan.immediate_actions),
            short_term_goals=[],
            long_term_goals=[],
            skill_development_roadmap=json.loads(plan.skill_development_roadmap),
            networking_recommendations=json.loads(plan.networking_recommendations),
            learning_resources=json.loads(plan.learning_resources),
            industry_insights=plan.industry_insights,
            market_positioning_strategy=plan.market_positioning_strategy,
            created_at=plan.created_at,
            updated_at=plan.updated_at,
        )
    except Exception as e:
        logger.error(f"Failed to generate career plan: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate career plan")


@router.get("/plans")
async def list_career_plans(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    user: CurrentUser = None,
    db: DBSession = None,
):
    """List user's career plans."""
    query = select(PersonalizedCareerPlan).where(PersonalizedCareerPlan.user_id == user.id)
    query = query.order_by(desc(PersonalizedCareerPlan.created_at))

    items, total, pages = await paginate_query(db, query, page, page_size)

    return {
        "items": [
            {
                "plan_id": p.id,
                "timeframe_months": p.timeframe_months,
                "overall_strategy": p.overall_strategy[:200],
                "created_at": p.created_at,
            }
            for p in items
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/plans/{plan_id}", response_model=PersonalizedCareerPlanSchema)
async def get_career_plan(
    plan_id: uuid.UUID,
    user: CurrentUser,
    db: DBSession,
) -> PersonalizedCareerPlanSchema:
    """Get details of a career plan."""
    plan = await db.get(PersonalizedCareerPlan, plan_id)
    if not plan or plan.user_id != user.id:
        raise NotFoundError(f"Career plan {plan_id} not found")

    return PersonalizedCareerPlanSchema(
        plan_id=plan.id,
        timeframe_months=plan.timeframe_months,
        overall_strategy=plan.overall_strategy,
        immediate_actions=json.loads(plan.immediate_actions),
        short_term_goals=json.loads(plan.short_term_goals),
        long_term_goals=json.loads(plan.long_term_goals),
        skill_development_roadmap=json.loads(plan.skill_development_roadmap),
        networking_recommendations=json.loads(plan.networking_recommendations),
        learning_resources=json.loads(plan.learning_resources),
        industry_insights=plan.industry_insights,
        market_positioning_strategy=plan.market_positioning_strategy,
        created_at=plan.created_at,
        updated_at=plan.updated_at,
    )


# ─────────────────────────────────────────────────────────────────────────
# Skill Assessment Endpoints
# ─────────────────────────────────────────────────────────────────────────

@router.post(
    "/skills/assess",
    response_model=SkillAssessmentResult,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Assess skills",
)
async def assess_skills(
    payload: SkillAssessmentRequest,
    user: CurrentUser,
    db: DBSession,
) -> SkillAssessmentResult:
    """Assess skills and identify gaps."""
    service = CareerCoachService(db)

    results = []
    for skill in payload.skills_to_assess:
        try:
            prompt = f"""Assess the skill '{skill}' for someone targeting the role '{payload.target_role or 'general'}'.

Provide assessment in JSON format with:
- current_level: beginner/intermediate/advanced/expert
- target_level: beginner/intermediate/advanced/expert
- proficiency_score: 0-100
- market_demand: high/medium/low
- development_recommendations: list of actionable recommendations
- resources: list of learning resources
- estimated_time_to_master: e.g., "3-6 months"

Be specific and practical."""

            assessment_data = await service._call_claude_api(prompt)

            try:
                data = json.loads(assessment_data)
            except json.JSONDecodeError:
                data = {
                    "current_level": "intermediate",
                    "target_level": "advanced",
                    "proficiency_score": 65,
                    "market_demand": "high",
                    "development_recommendations": [],
                    "resources": [],
                    "estimated_time_to_master": "3-6 months",
                }

            assessment = SkillAssessment(
                user_id=user.id,
                assessed_skill=skill,
                current_level=data.get("current_level", "intermediate"),
                target_level=data.get("target_level", "advanced"),
                proficiency_score=int(data.get("proficiency_score", 65)),
                market_demand=data.get("market_demand", "medium"),
                development_recommendations=json.dumps(data.get("development_recommendations", [])),
                resources=json.dumps(data.get("resources", [])),
                estimated_time_to_master=data.get("estimated_time_to_master"),
                target_role=payload.target_role,
                years_of_experience=payload.self_assessed_levels.get(skill.lower().replace(" ", "_"), 0) if payload.self_assessed_levels else 0,
            )
            db.add(assessment)
            await db.flush()

            results.append(SkillAssessmentResult(
                assessment_id=assessment.id,
                assessed_skill=assessment.assessed_skill,
                current_level=assessment.current_level,
                target_level=assessment.target_level,
                proficiency_score=assessment.proficiency_score,
                years_of_experience=assessment.years_of_experience,
                market_demand=assessment.market_demand,
                development_recommendations=json.loads(assessment.development_recommendations),
                resources=json.loads(assessment.resources),
                estimated_time_to_master=assessment.estimated_time_to_master,
            ))
        except Exception as e:
            logger.error(f"Failed to assess skill {skill}: {e}")
            continue

    return results[0] if results else SkillAssessmentResult(
        assessment_id=uuid.uuid4(),
        assessed_skill="unknown",
        current_level="beginner",
        target_level="intermediate",
        proficiency_score=0,
        market_demand="medium",
        development_recommendations=[],
        resources=[],
    )


@router.get("/skills/assessments", response_model=SkillAssessmentListResponse)
async def get_skill_assessments(
    user: CurrentUser = None,
    db: DBSession = None,
) -> SkillAssessmentListResponse:
    """Get all skill assessments for user."""
    query = select(SkillAssessment).where(SkillAssessment.user_id == user.id)
    query = query.order_by(desc(SkillAssessment.created_at))

    assessments = (await db.execute(query)).scalars().all()

    items = [
        SkillAssessmentResult(
            assessment_id=a.id,
            assessed_skill=a.assessed_skill,
            current_level=a.current_level,
            target_level=a.target_level,
            proficiency_score=a.proficiency_score,
            years_of_experience=a.years_of_experience,
            market_demand=a.market_demand,
            development_recommendations=json.loads(a.development_recommendations),
            resources=json.loads(a.resources),
            estimated_time_to_master=a.estimated_time_to_master,
        )
        for a in assessments
    ]

    strengths = [a.assessed_skill for a in assessments if a.proficiency_score >= 70]
    gaps = [a.assessed_skill for a in assessments if a.proficiency_score < 50]
    recommended_focus = [a.assessed_skill for a in assessments if a.market_demand == "high" and a.proficiency_score < 70]

    return SkillAssessmentListResponse(
        items=items,
        total=len(items),
        strengths=strengths,
        gaps=gaps,
        recommended_focus_areas=recommended_focus,
    )


# ─────────────────────────────────────────────────────────────────────────
# Interview Prep Endpoints
# ─────────────────────────────────────────────────────────────────────────

@router.post(
    "/interview-prep",
    response_model=InterviewPrepSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start interview prep session",
)
async def start_interview_prep(
    payload: InterviewPrepSessionRequest,
    user: CurrentUser,
    db: DBSession,
) -> InterviewPrepSessionResponse:
    """Start interview preparation."""
    service = CareerCoachService(db)

    try:
        prompt = f"""Generate comprehensive interview preparation for:
- Company: {payload.company}
- Position: {payload.position}
- Interview Type: {payload.interview_type}
- Focus Areas: {', '.join(payload.focus_areas or ['General preparation'])}

Provide JSON with:
- practice_questions: list of 10-15 practice questions
- key_talking_points: list of 5-7 key points to emphasize
- common_challenges: list of potential challenges
- resources: list of preparation resources
- recommended_next_steps: list of next steps

Be specific to the role and company."""

        prep_data = await service._call_claude_api(prompt)

        try:
            data = json.loads(prep_data)
        except json.JSONDecodeError:
            data = {
                "practice_questions": ["Tell us about yourself", "Why are you interested in this role?"],
                "key_talking_points": ["Relevant experience", "Technical skills", "Problem-solving ability"],
                "common_challenges": [],
                "resources": [],
                "recommended_next_steps": [],
            }

        session = InterviewPrepSession(
            user_id=user.id,
            company=payload.company,
            position=payload.position,
            interview_type=payload.interview_type,
            interview_date=payload.interview_date,
            practice_questions=json.dumps(data.get("practice_questions", [])),
            key_talking_points=json.dumps(data.get("key_talking_points", [])),
            common_challenges=json.dumps(data.get("common_challenges", [])),
            resources=json.dumps(data.get("resources", [])),
            recommended_next_steps=json.dumps(data.get("recommended_next_steps", [])),
            focus_areas=json.dumps(payload.focus_areas or []),
            mock_interview_available=True,
            preparation_progress=20,
        )
        db.add(session)
        await db.flush()

        return InterviewPrepSessionResponse(
            session_id=session.id,
            company=session.company,
            position=session.position,
            interview_type=session.interview_type,
            interview_date=session.interview_date,
            preparation_progress=session.preparation_progress,
            practice_questions=json.loads(session.practice_questions),
            key_talking_points=json.loads(session.key_talking_points),
            common_challenges=json.loads(session.common_challenges),
            resources=json.loads(session.resources),
            mock_interview_available=session.mock_interview_available,
            recommended_next_steps=json.loads(session.recommended_next_steps),
            created_at=session.created_at,
            updated_at=session.updated_at,
        )
    except Exception as e:
        logger.error(f"Failed to start interview prep: {e}")
        raise HTTPException(status_code=500, detail="Failed to start interview prep")


@router.get(
    "/interview-prep/{session_id}",
    response_model=InterviewPrepSessionResponse,
    summary="Get interview prep session",
)
async def get_interview_prep(
    session_id: uuid.UUID,
    user: CurrentUser,
    db: DBSession,
) -> InterviewPrepSessionResponse:
    """Get interview preparation materials."""
    session = await db.get(InterviewPrepSession, session_id)
    if not session or session.user_id != user.id:
        raise NotFoundError(f"Interview prep session {session_id} not found")

    return InterviewPrepSessionResponse(
        session_id=session.id,
        company=session.company,
        position=session.position,
        interview_type=session.interview_type,
        interview_date=session.interview_date,
        preparation_progress=session.preparation_progress,
        practice_questions=json.loads(session.practice_questions),
        key_talking_points=json.loads(session.key_talking_points),
        common_challenges=json.loads(session.common_challenges),
        resources=json.loads(session.resources),
        mock_interview_available=session.mock_interview_available,
        recommended_next_steps=json.loads(session.recommended_next_steps),
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


# ─────────────────────────────────────────────────────────────────────────
# Remaining endpoints (simplified implementations)
# ─────────────────────────────────────────────────────────────────────────

@router.post(
    "/{coaching_id}/sessions/schedule",
    response_model=CoachingSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def schedule_coaching_session(
    coaching_id: uuid.UUID,
    payload: ScheduleCoachingSessionRequest,
    user: CurrentUser,
    db: DBSession,
) -> CoachingSessionResponse:
    """Schedule a coaching session."""
    coaching = await db.get(CareerCoaching, coaching_id)
    if not coaching or coaching.user_id != user.id:
        raise NotFoundError(f"Coaching engagement {coaching_id} not found")

    session = CoachingSession(
        coaching_id=coaching_id,
        session_status=SessionStatus.SCHEDULED,
        scheduled_date=payload.session_date,
        session_format=payload.session_format,
        duration_minutes=payload.duration_minutes,
        session_notes=payload.preparation_notes,
    )
    db.add(session)
    await db.flush()

    return CoachingSessionResponse(
        session_id=session.id,
        coaching_id=session.coaching_id,
        coaching_area=coaching.coaching_area,
        status=session.session_status.value,
        scheduled_date=session.scheduled_date,
        session_format=session.session_format,
    )


@router.get("/{coaching_id}/sessions")
async def get_coaching_sessions(
    coaching_id: uuid.UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    user: CurrentUser = None,
    db: DBSession = None,
):
    """Get all sessions for a coaching engagement."""
    coaching = await db.get(CareerCoaching, coaching_id)
    if not coaching or coaching.user_id != user.id:
        raise NotFoundError(f"Coaching engagement {coaching_id} not found")

    query = select(CoachingSession).where(CoachingSession.coaching_id == coaching_id)
    query = query.order_by(desc(CoachingSession.created_at))

    items, total, pages = await paginate_query(db, query, page, page_size)

    return {
        "items": [
            {
                "session_id": s.id,
                "coaching_id": s.coaching_id,
                "status": s.session_status.value,
                "scheduled_date": s.scheduled_date,
                "session_format": s.session_format,
            }
            for s in items
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/{coaching_id}/questions", status_code=status.HTTP_201_CREATED)
async def ask_coach_question(
    coaching_id: uuid.UUID,
    payload: AskCoachQuestion,
    user: CurrentUser,
    db: DBSession,
):
    """Ask the coach a question."""
    coaching = await db.get(CareerCoaching, coaching_id)
    if not coaching or coaching.user_id != user.id:
        raise NotFoundError(f"Coaching engagement {coaching_id} not found")

    question = CoachQuestion(
        coaching_id=coaching_id,
        user_id=user.id,
        question=payload.question,
        context=payload.context,
        related_coaching_area=payload.related_coaching_area,
        priority=payload.priority,
    )
    db.add(question)
    await db.flush()

    return {
        "question_id": question.id,
        "coaching_id": question.coaching_id,
        "question": question.question,
        "status": "pending",
        "created_at": question.created_at,
    }


@router.get("/{coaching_id}/progress", response_model=CoachingProgressReportSchema)
async def get_coaching_progress(
    coaching_id: uuid.UUID,
    user: CurrentUser,
    db: DBSession,
) -> CoachingProgressReportSchema:
    """Get progress report for coaching."""
    coaching = await db.get(CareerCoaching, coaching_id)
    if not coaching or coaching.user_id != user.id:
        raise NotFoundError(f"Coaching engagement {coaching_id} not found")

    report = CoachingProgressReportSchema(
        report_id=uuid.uuid4(),
        period_start=datetime.now(timezone.utc),
        period_end=datetime.now(timezone.utc),
        coaching_areas_addressed=[coaching.coaching_area],
        goals_achieved=[],
        goals_in_progress=[coaching.goals],
        skills_developed=[],
        challenges_identified=[coaching.challenges or ""],
        recommendations_for_next_period=[],
        overall_progress_score=50,
        next_focus_areas=[coaching.coaching_area],
        generated_at=datetime.now(timezone.utc),
    )

    return report


@router.post("/{coaching_id}/cancel", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_coaching(
    coaching_id: uuid.UUID,
    reason: Optional[str] = Query(None),
    user: CurrentUser = None,
    db: DBSession = None,
) -> None:
    """Cancel a coaching engagement."""
    coaching = await db.get(CareerCoaching, coaching_id)
    if not coaching or coaching.user_id != user.id:
        raise NotFoundError(f"Coaching engagement {coaching_id} not found")

    coaching.status = "cancelled"
    await db.flush()
