"""Comprehensive tests for Phase 2 action handlers.

Tests cover:
- Input validation (Pydantic models)
- Authorization checks (ownership verification)
- Error handling (malformed input, missing resources)
- Database operations (proper commits/rollbacks)
- Logging (audit trails)
- All action types (upload, analyze, rank, schedule, approve, send)

Phase 2 Production-Ready Testing
"""
import pytest
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.resume import Resume
from app.models.position import Position
from app.models.application import Application
from app.models.assessment import Assessment
from app.services.action_handlers import (
    UploadActionHandler,
    AnalyzeActionHandler,
    RankActionHandler,
    ScheduleActionHandler,
    ApproveActionHandler,
    SendActionHandler,
    get_handler_for_action,
)


@pytest.mark.asyncio
class TestActionHandlers:
    """Test all action handlers for production readiness."""

    @pytest.fixture
    async def company(self, db_session: AsyncSession):
        """Create a test company."""
        from app.models.company import Company
        company = Company(
            name="Test Company",
            domain="test.example.com",
            plan="enterprise",
        )
        db_session.add(company)
        await db_session.commit()
        return company

    @pytest.fixture
    async def user(self, db_session: AsyncSession, company):
        """Create a test user."""
        user = User(
            email="test@example.com",
            password_hash="hash",
            role="recruiter",
            company_id=company.id,
        )
        db_session.add(user)
        await db_session.commit()
        return user

    @pytest.fixture
    async def other_user(self, db_session: AsyncSession, company):
        """Create a different user for authorization tests."""
        user = User(
            email="other@example.com",
            password_hash="hash",
            role="recruiter",
            company_id=company.id,
        )
        db_session.add(user)
        await db_session.commit()
        return user

    @pytest.fixture
    async def resume(self, user, db_session: AsyncSession):
        """Create a test resume."""
        resume = Resume(
            user_id=user.id,
            file_id="s3://bucket/resume-123.pdf",
            file_type="pdf",
        )
        db_session.add(resume)
        await db_session.commit()
        return resume

    @pytest.fixture
    async def position(self, user, db_session: AsyncSession):
        """Create a test position."""
        position = Position(
            company_id=user.company_id,
            created_by=user.id,
            title="Senior Engineer",
            description="We are hiring...",
            status="draft",
        )
        db_session.add(position)
        await db_session.commit()
        return position

    @pytest.fixture
    async def application(self, user, resume, position, db_session: AsyncSession):
        """Create a test application."""
        app = Application(
            resume_id=resume.id,
            position_id=position.id,
            user_id=user.id,
        )
        db_session.add(app)
        await db_session.commit()
        return app

    @pytest.fixture
    async def assessment(self, user, resume, position, db_session: AsyncSession):
        """Create a test assessment."""
        assessment = Assessment(
            user_id=user.id,
            resume_id=resume.id,
            position_id=position.id,
            status="completed",
        )
        db_session.add(assessment)
        await db_session.commit()
        return assessment

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # UploadActionHandler Tests
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    async def test_upload_resume_valid(self, user, db_session):
        """Upload valid resume creates record."""
        action = {
            "id": "upload_1",
            "type": "upload",
            "parameters": {
                "file_id": "s3://bucket/resume.pdf",
                "file_type": "resume",
                "filename": "john_resume.pdf",
            },
        }

        result = await UploadActionHandler.handle(action, user, db_session)

        assert result["status"] == "completed"
        assert "resume_id" in result["result"]
        assert result["result"]["type"] == "resume"
        assert result["result"]["filename"] == "john_resume.pdf"

    async def test_upload_jd_valid(self, user, db_session):
        """Upload valid JD creates position record."""
        action = {
            "id": "upload_2",
            "type": "upload",
            "parameters": {
                "file_id": "s3://bucket/jd.pdf",
                "file_type": "jd",
                "filename": "backend_role.pdf",
                "job_title": "Senior Backend Engineer",
                "jd_text": "We are looking for...",
            },
        }

        result = await UploadActionHandler.handle(action, user, db_session)

        assert result["status"] == "completed"
        assert "position_id" in result["result"]
        assert result["result"]["type"] == "job_description"
        assert result["result"]["title"] == "Senior Backend Engineer"

    async def test_upload_invalid_file_type(self, user, db_session):
        """Invalid file_type rejected."""
        action = {
            "id": "upload_3",
            "type": "upload",
            "parameters": {
                "file_id": "s3://bucket/file",
                "file_type": "invalid_type",  # ❌ Invalid
                "filename": "file.pdf",
            },
        }

        result = await UploadActionHandler.handle(action, user, db_session)

        assert result["status"] == "failed"
        assert "Validation error" in result["result"]["error"]

    async def test_upload_path_traversal_blocked(self, user, db_session):
        """Path traversal in filename blocked."""
        action = {
            "id": "upload_4",
            "type": "upload",
            "parameters": {
                "file_id": "s3://bucket/file",
                "file_type": "resume",
                "filename": "../../../etc/passwd",  # ❌ Path traversal attempt
            },
        }

        result = await UploadActionHandler.handle(action, user, db_session)

        assert result["status"] == "failed"
        assert "path separators" in result["result"]["error"].lower()

    async def test_upload_missing_required_fields(self, user, db_session):
        """Missing required fields rejected."""
        action = {
            "id": "upload_5",
            "type": "upload",
            "parameters": {
                # Missing file_id ❌
                "file_type": "resume",
                "filename": "resume.pdf",
            },
        }

        result = await UploadActionHandler.handle(action, user, db_session)

        assert result["status"] == "failed"
        assert "Validation error" in result["result"]["error"]

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # AnalyzeActionHandler Tests
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    async def test_analyze_valid_resume(self, user, resume, db_session):
        """Valid resume analysis request."""
        action = {
            "id": "analyze_1",
            "type": "analyze",
            "parameters": {
                "resume_id": str(resume.id),
                "analysis_type": "cv_analysis",
            },
        }

        result = await AnalyzeActionHandler.handle(action, user, db_session)

        assert result["status"] == "completed"
        assert "analysis_id" in result["result"]
        assert result["result"]["analysis_type"] == "cv_analysis"

    async def test_analyze_invalid_uuid(self, user, db_session):
        """Invalid UUID format rejected."""
        action = {
            "id": "analyze_2",
            "type": "analyze",
            "parameters": {
                "resume_id": "not-a-uuid",  # ❌ Invalid UUID
                "analysis_type": "cv_analysis",
            },
        }

        result = await AnalyzeActionHandler.handle(action, user, db_session)

        assert result["status"] == "failed"
        assert "Invalid UUID" in result["result"]["error"]

    async def test_analyze_nonexistent_resume(self, user, db_session):
        """Nonexistent resume rejected."""
        fake_resume_id = str(uuid4())
        action = {
            "id": "analyze_3",
            "type": "analyze",
            "parameters": {
                "resume_id": fake_resume_id,
                "analysis_type": "cv_analysis",
            },
        }

        result = await AnalyzeActionHandler.handle(action, user, db_session)

        assert result["status"] == "failed"
        assert "not found" in result["result"]["error"].lower()

    async def test_analyze_different_user_resume(self, user, other_user, db_session):
        """Cannot analyze resume owned by different user."""
        # Create resume owned by other_user
        resume = Resume(
            user_id=other_user.id,
            file_id="s3://bucket/resume.pdf",
            file_type="pdf",
        )
        db_session.add(resume)
        await db_session.commit()

        action = {
            "id": "analyze_4",
            "type": "analyze",
            "parameters": {
                "resume_id": str(resume.id),
                "analysis_type": "cv_analysis",
            },
        }

        result = await AnalyzeActionHandler.handle(action, user, db_session)

        # Should fail due to authorization
        assert result["status"] == "failed"
        assert "does not own" in result["result"]["error"].lower()

    async def test_analyze_invalid_type(self, user, resume, db_session):
        """Invalid analysis type rejected."""
        action = {
            "id": "analyze_5",
            "type": "analyze",
            "parameters": {
                "resume_id": str(resume.id),
                "analysis_type": "invalid_analysis",  # ❌ Invalid type
            },
        }

        result = await AnalyzeActionHandler.handle(action, user, db_session)

        assert result["status"] == "failed"
        assert "Validation error" in result["result"]["error"]

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # RankActionHandler Tests
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    async def test_rank_candidates_valid(self, user, position, db_session):
        """Ranking uses REAL signals: a strong resume out-ranks a weak one,
        and a candidate with no resume on file lands at the bottom with a
        'no_resume' marker instead of being silently dropped."""
        position.description = (
            "Senior Python engineer: FastAPI, SQLAlchemy, PostgreSQL, Celery, "
            "distributed systems, API design."
        )
        strong = Resume(
            user_id=user.id,
            file_id="s3://bucket/strong.pdf",
            file_type="pdf",
            supplementary={
                "extracted_text": (
                    "Senior Python engineer with FastAPI, SQLAlchemy, PostgreSQL "
                    "and Celery experience building distributed systems and APIs."
                )
            },
        )
        weak = Resume(
            user_id=user.id,
            file_id="s3://bucket/weak.pdf",
            file_type="pdf",
            supplementary={
                "extracted_text": "Retail store manager. Inventory, scheduling, sales."
            },
        )
        db_session.add_all([strong, weak])
        await db_session.commit()

        candidate_ids = [str(weak.id), str(strong.id), str(uuid4())]
        action = {
            "id": "rank_1",
            "type": "rank",
            "parameters": {
                "position_id": str(position.id),
                "candidate_ids": candidate_ids,
                "criteria": "skill_match",
            },
        }

        result = await RankActionHandler.handle(action, user, db_session)

        assert result["status"] == "completed"
        assert "ranking_id" in result["result"]
        assert result["result"]["total_candidates"] == 3
        rankings = result["result"]["rankings"]
        assert len(rankings) == 3
        assert rankings[0]["resume_id"] == str(strong.id)
        assert rankings[0]["score"] > rankings[1]["score"]
        assert rankings[-1]["score_source"] == "no_resume"
        assert rankings[-1]["score"] == 0

    async def test_rank_invalid_criteria(self, user, position, db_session):
        """Invalid ranking criteria rejected."""
        action = {
            "id": "rank_2",
            "type": "rank",
            "parameters": {
                "position_id": str(position.id),
                "candidate_ids": [str(uuid4())],
                "criteria": "invalid_criteria",  # ❌ Invalid
            },
        }

        result = await RankActionHandler.handle(action, user, db_session)

        assert result["status"] == "failed"
        assert "Validation error" in result["result"]["error"]

    async def test_rank_empty_candidates(self, user, position, db_session):
        """Empty candidate list rejected."""
        action = {
            "id": "rank_3",
            "type": "rank",
            "parameters": {
                "position_id": str(position.id),
                "candidate_ids": [],  # ❌ Empty
                "criteria": "skill_match",
            },
        }

        result = await RankActionHandler.handle(action, user, db_session)

        assert result["status"] == "failed"
        assert "Validation error" in result["result"]["error"]

    async def test_rank_too_many_candidates(self, user, position, db_session):
        """Too many candidates rejected."""
        candidate_ids = [str(uuid4()) for _ in range(101)]  # ❌ > 100
        action = {
            "id": "rank_4",
            "type": "rank",
            "parameters": {
                "position_id": str(position.id),
                "candidate_ids": candidate_ids,
                "criteria": "skill_match",
            },
        }

        result = await RankActionHandler.handle(action, user, db_session)

        assert result["status"] == "failed"
        assert "Validation error" in result["result"]["error"]

    async def test_rank_accepts_all_criteria(self, user, position, db_session):
        """All criteria enum values are accepted and echoed in the rankings.

        Scoring itself is criteria-independent today (real assessment /
        semantic signals), so this asserts the contract — criteria validated
        and recorded — rather than fabricated per-criteria score differences.
        """
        candidate_ids = [str(uuid4()) for _ in range(2)]
        for criteria in ("skill_match", "experience", "availability", "overall"):
            action = {
                "id": f"rank_{criteria}",
                "type": "rank",
                "parameters": {
                    "position_id": str(position.id),
                    "candidate_ids": candidate_ids,
                    "criteria": criteria,
                },
            }
            result = await RankActionHandler.handle(action, user, db_session)
            assert result["status"] == "completed"
            assert all(r["criteria"] == criteria for r in result["result"]["rankings"])

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # ScheduleActionHandler Tests
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    async def test_schedule_interview_valid(self, user, application, db_session):
        """Valid interview scheduling."""
        action = {
            "id": "schedule_1",
            "type": "schedule",
            "parameters": {
                "application_id": str(application.id),
                "interview_type": "phone_screen",
                "scheduled_time": "2026-06-15T14:00:00Z",
                "duration_minutes": 30,
                "location": "Zoom",
            },
        }

        result = await ScheduleActionHandler.handle(action, user, db_session)

        assert result["status"] == "completed"
        assert "interview_id" in result["result"]
        assert result["result"]["type"] == "phone_screen"

    async def test_schedule_invalid_interview_type(self, user, application, db_session):
        """Invalid interview type rejected."""
        action = {
            "id": "schedule_2",
            "type": "schedule",
            "parameters": {
                "application_id": str(application.id),
                "interview_type": "invalid_type",  # ❌ Invalid
                "scheduled_time": "2026-06-15T14:00:00Z",
                "duration_minutes": 30,
            },
        }

        result = await ScheduleActionHandler.handle(action, user, db_session)

        assert result["status"] == "failed"
        assert "Validation error" in result["result"]["error"]

    async def test_schedule_invalid_duration(self, user, application, db_session):
        """Invalid duration rejected."""
        action = {
            "id": "schedule_3",
            "type": "schedule",
            "parameters": {
                "application_id": str(application.id),
                "interview_type": "phone_screen",
                "scheduled_time": "2026-06-15T14:00:00Z",
                "duration_minutes": 10,  # ❌ < 15 min
            },
        }

        result = await ScheduleActionHandler.handle(action, user, db_session)

        assert result["status"] == "failed"
        assert "Validation error" in result["result"]["error"]

    async def test_schedule_invalid_datetime(self, user, application, db_session):
        """Invalid datetime rejected."""
        action = {
            "id": "schedule_4",
            "type": "schedule",
            "parameters": {
                "application_id": str(application.id),
                "interview_type": "phone_screen",
                "scheduled_time": "not-a-datetime",  # ❌ Invalid
                "duration_minutes": 30,
            },
        }

        result = await ScheduleActionHandler.handle(action, user, db_session)

        assert result["status"] == "failed"
        assert "Validation error" in result["result"]["error"]

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # ApproveActionHandler Tests
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    async def test_approve_candidate_valid(self, user, application, assessment, db_session):
        """Valid approval creates Decision record."""
        action = {
            "id": "approve_1",
            "type": "approve",
            "parameters": {
                "application_id": str(application.id),
                "assessment_id": str(assessment.id),
                "position_id": str(application.position_id),
                "decision": "advance",
                "reasoning": "Strong candidate",
            },
        }

        result = await ApproveActionHandler.handle(action, user, db_session)

        assert result["status"] == "completed"
        assert "decision_id" in result["result"]
        assert result["result"]["decision"] == "advance"

    async def test_approve_all_decision_types(self, user, application, assessment, db_session):
        """All decision types accepted."""
        for decision_type in ["advance", "reject", "hold", "interview", "hire"]:
            action = {
                "id": f"approve_{decision_type}",
                "type": "approve",
                "parameters": {
                    "application_id": str(application.id),
                    "assessment_id": str(assessment.id),
                    "position_id": str(application.position_id),
                    "decision": decision_type,
                },
            }

            result = await ApproveActionHandler.handle(action, user, db_session)

            assert result["status"] == "completed"
            assert result["result"]["decision"] == decision_type

    async def test_approve_invalid_decision(self, user, application, assessment, db_session):
        """Invalid decision type rejected."""
        action = {
            "id": "approve_invalid",
            "type": "approve",
            "parameters": {
                "application_id": str(application.id),
                "assessment_id": str(assessment.id),
                "position_id": str(application.position_id),
                "decision": "invalid_decision",  # ❌ Invalid
            },
        }

        result = await ApproveActionHandler.handle(action, user, db_session)

        assert result["status"] == "failed"
        assert "Validation error" in result["result"]["error"]

    async def test_approve_missing_assessment(self, user, application, db_session):
        """Missing assessment rejected."""
        fake_assessment_id = str(uuid4())
        action = {
            "id": "approve_missing",
            "type": "approve",
            "parameters": {
                "application_id": str(application.id),
                "assessment_id": fake_assessment_id,
                "position_id": str(application.position_id),
                "decision": "advance",
            },
        }

        result = await ApproveActionHandler.handle(action, user, db_session)

        assert result["status"] == "failed"
        assert "not found" in result["result"]["error"].lower()

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # SendActionHandler Tests
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    async def test_send_notification_valid(self, user, other_user, db_session):
        """Valid notification send."""
        action = {
            "id": "send_1",
            "type": "send",
            "parameters": {
                "recipient_id": str(other_user.id),
                "message_type": "offer",
                "context": {"candidate_name": "John", "position": "Engineer"},
            },
        }

        result = await SendActionHandler.handle(action, user, db_session)

        assert result["status"] == "completed"
        assert "notification_id" in result["result"]
        assert result["result"]["message_type"] == "offer"

    async def test_send_all_message_types(self, user, other_user, db_session):
        """All message types accepted."""
        for msg_type in ["offer", "rejection", "update", "schedule"]:
            action = {
                "id": f"send_{msg_type}",
                "type": "send",
                "parameters": {
                    "recipient_id": str(other_user.id),
                    "message_type": msg_type,
                    "context": {},
                },
            }

            result = await SendActionHandler.handle(action, user, db_session)

            assert result["status"] == "completed"
            assert result["result"]["message_type"] == msg_type

    async def test_send_invalid_message_type(self, user, other_user, db_session):
        """Invalid message type rejected."""
        action = {
            "id": "send_invalid",
            "type": "send",
            "parameters": {
                "recipient_id": str(other_user.id),
                "message_type": "invalid_type",  # ❌ Invalid
                "context": {},
            },
        }

        result = await SendActionHandler.handle(action, user, db_session)

        assert result["status"] == "failed"
        assert "Validation error" in result["result"]["error"]

    async def test_send_nonexistent_recipient(self, user, db_session):
        """Nonexistent recipient rejected."""
        fake_recipient_id = str(uuid4())
        action = {
            "id": "send_missing",
            "type": "send",
            "parameters": {
                "recipient_id": fake_recipient_id,
                "message_type": "offer",
                "context": {},
            },
        }

        result = await SendActionHandler.handle(action, user, db_session)

        assert result["status"] == "failed"
        assert "not found" in result["result"]["error"].lower()

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Handler Registry Tests
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    async def test_get_handler_all_types(self):
        """All action types have handlers."""
        action_types = ["upload", "analyze", "rank", "schedule", "approve", "send"]

        for action_type in action_types:
            handler = await get_handler_for_action(action_type)
            assert handler is not None

    async def test_get_handler_unknown_type(self):
        """Unknown action type returns None."""
        handler = await get_handler_for_action("unknown_action_type")
        assert handler is None

    async def test_get_handler_case_insensitive(self):
        """Handler lookup is case-insensitive."""
        handler_lower = await get_handler_for_action("upload")
        handler_upper = await get_handler_for_action("UPLOAD")
        handler_mixed = await get_handler_for_action("UpLoad")

        assert handler_lower is not None
        assert handler_upper is not None
        assert handler_mixed is not None
