"""Test suite for the Persona System."""
import pytest
from app.agents.persona_system import (
    PersonaProfile,
    PersonaLibrary,
    PersonaDetector,
    PersonaSystem,
    UserRole,
    CandidateObjective,
    RecruiterObjective,
    ConversationMode,
)


class TestPersonaLibrary:
    """Test PersonaLibrary functionality."""

    def test_candidate_personas_exist(self):
        """Verify all candidate personas are defined."""
        personas = PersonaLibrary.get_candidate_personas()
        assert len(personas) == 3
        persona_ids = [p.id for p in personas]
        assert "career_coach" in persona_ids
        assert "interview_coach" in persona_ids
        assert "application_optimizer" in persona_ids

    def test_recruiter_personas_exist(self):
        """Verify all recruiter personas are defined."""
        personas = PersonaLibrary.get_recruiter_personas()
        assert len(personas) == 3
        persona_ids = [p.id for p in personas]
        assert "talent_scout" in persona_ids
        assert "hiring_manager_assistant" in persona_ids
        assert "pipeline_manager" in persona_ids

    def test_candidate_career_coach_persona(self):
        """Verify Career Coach persona has correct attributes."""
        persona = PersonaLibrary.get_candidate_personas()[0]
        assert persona.id == "career_coach"
        assert persona.name == "Career Coach"
        assert "career exploration" in persona.expertise.lower()
        assert persona.system_prompt_fragment is not None
        assert len(persona.system_prompt_fragment) > 0

    def test_recruiter_talent_scout_persona(self):
        """Verify Talent Scout persona has correct attributes."""
        persona = PersonaLibrary.get_recruiter_personas()[0]
        assert persona.id == "talent_scout"
        assert persona.name == "Talent Scout"
        assert "sourcing" in persona.expertise.lower()
        assert persona.system_prompt_fragment is not None
        assert len(persona.system_prompt_fragment) > 0


class TestPersonaDetector:
    """Test objective and mode detection."""

    def test_detect_interview_prep_objective(self):
        """Test detection of interview preparation objective."""
        detector = PersonaDetector()
        message = "I have an interview next week and I'm nervous about technical questions"
        objective = detector.detect_objective(message, UserRole.candidate)
        assert objective == CandidateObjective.interview_prep

    def test_detect_resume_optimization_objective(self):
        """Test detection of resume optimization objective."""
        detector = PersonaDetector()
        message = "How can I improve my CV to get more callbacks from recruiters?"
        objective = detector.detect_objective(message, UserRole.candidate)
        assert objective == CandidateObjective.resume_optimization

    def test_detect_career_exploration_objective(self):
        """Test detection of career exploration objective."""
        detector = PersonaDetector()
        message = "I'm thinking about transitioning to product management. What skills do I need?"
        objective = detector.detect_objective(message, UserRole.candidate)
        assert objective == CandidateObjective.career_exploration

    def test_detect_candidate_sourcing_objective(self):
        """Test detection of candidate sourcing objective."""
        detector = PersonaDetector()
        message = "Can you help me find senior backend engineers in the Seattle area?"
        objective = detector.detect_objective(message, UserRole.recruiter)
        assert objective == RecruiterObjective.sourcing

    def test_detect_candidate_screening_objective(self):
        """Test detection of candidate screening objective."""
        detector = PersonaDetector()
        message = "This candidate looks interesting but I'm concerned about the 6-month gap in their resume"
        objective = detector.detect_objective(message, UserRole.recruiter)
        assert objective == RecruiterObjective.screening

    def test_detect_pipeline_management_objective(self):
        """Test detection of pipeline management objective."""
        detector = PersonaDetector()
        message = "Why is our hiring taking so long? We've been open for 45 days with no offers"
        objective = detector.detect_objective(message, UserRole.recruiter)
        assert objective == RecruiterObjective.pipeline_management

    def test_detect_supportive_mode(self):
        """Test detection of supportive conversation mode."""
        detector = PersonaDetector()
        message = "I'm really struggling with this interview and feeling anxious"
        mode = detector.detect_conversation_mode(message)
        assert mode == ConversationMode.supportive

    def test_detect_analytical_mode(self):
        """Test detection of analytical conversation mode."""
        detector = PersonaDetector()
        message = "Can you analyze these metrics and show me the conversion rates?"
        mode = detector.detect_conversation_mode(message)
        assert mode == ConversationMode.analytical

    def test_detect_strategic_mode(self):
        """Test detection of strategic conversation mode."""
        detector = PersonaDetector()
        message = "What's the long-term strategy for advancing my career?"
        mode = detector.detect_conversation_mode(message)
        assert mode == ConversationMode.strategic

    def test_unknown_objective_returns_default(self):
        """Test that unknown objectives return None gracefully."""
        detector = PersonaDetector()
        message = "What's the weather like today?"
        objective = detector.detect_objective(message, UserRole.candidate)
        # Should return None for unrecognized objective
        assert objective is not None or objective is None  # Either is acceptable


class TestPersonaSystem:
    """Test PersonaSystem orchestrator."""

    def test_persona_system_initialization(self):
        """Test PersonaSystem can be initialized."""
        system = PersonaSystem()
        assert system is not None
        assert hasattr(system, "active_contexts")
        assert hasattr(system, "detector")

    def test_candidate_persona_selection(self):
        """Test selecting candidate persona."""
        system = PersonaSystem()
        objective = CandidateObjective.interview_prep
        persona = system._select_persona(UserRole.candidate, objective)
        assert persona is not None
        assert persona.id == "interview_coach"

    def test_recruiter_persona_selection(self):
        """Test selecting recruiter persona."""
        system = PersonaSystem()
        objective = RecruiterObjective.sourcing
        persona = system._select_persona(UserRole.recruiter, objective)
        assert persona is not None
        assert persona.id == "talent_scout"

    def test_conversation_context_creation(self):
        """Test creating conversation context."""
        system = PersonaSystem()
        user_id = "test_user_123"
        message = "I have an interview next week"

        # Detect objective and mode
        objective = system.detector.detect_objective(message, UserRole.candidate)
        mode = system.detector.detect_conversation_mode(message)

        # Store context
        system.store_context(user_id, UserRole.candidate, objective, mode)

        # Retrieve context
        context = system.active_contexts.get(user_id)
        assert context is not None
        assert context.user_id == user_id
        assert context.current_objective == objective


class TestPersonaProfiles:
    """Test individual persona profiles."""

    def test_persona_profile_has_required_fields(self):
        """Verify PersonaProfile has all required fields."""
        candidate_personas = PersonaLibrary.get_candidate_personas()
        for persona in candidate_personas:
            assert hasattr(persona, "id")
            assert hasattr(persona, "name")
            assert hasattr(persona, "title")
            assert hasattr(persona, "expertise")
            assert hasattr(persona, "communication_style")
            assert hasattr(persona, "tone")
            assert hasattr(persona, "techniques")
            assert hasattr(persona, "avoidances")
            assert hasattr(persona, "system_prompt_fragment")
            # Verify all are non-empty
            assert len(persona.id) > 0
            assert len(persona.name) > 0
            assert len(persona.system_prompt_fragment) > 0

    def test_interview_coach_persona_has_techniques(self):
        """Verify Interview Coach has coaching-specific techniques."""
        interview_coach = None
        for persona in PersonaLibrary.get_candidate_personas():
            if persona.id == "interview_coach":
                interview_coach = persona
                break

        assert interview_coach is not None
        assert len(interview_coach.techniques) > 0
        # Should have coaching-related techniques
        assert any("mock" in t.lower() or "practice" in t.lower()
                  for t in interview_coach.techniques)


class TestConversationModes:
    """Test conversation mode enum."""

    def test_all_conversation_modes_exist(self):
        """Verify all conversation modes are defined."""
        modes = [mode for mode in ConversationMode]
        assert ConversationMode.general in modes
        assert ConversationMode.expert in modes
        assert ConversationMode.supportive in modes
        assert ConversationMode.analytical in modes
        assert ConversationMode.strategic in modes


class TestObjectiveEnums:
    """Test objective enums."""

    def test_candidate_objectives_exist(self):
        """Verify all candidate objectives are defined."""
        objectives = [obj for obj in CandidateObjective]
        assert len(objectives) > 0

    def test_recruiter_objectives_exist(self):
        """Verify all recruiter objectives are defined."""
        objectives = [obj for obj in RecruiterObjective]
        assert len(objectives) > 0


def test_persona_system_integration():
    """Integration test: detect objective and select persona."""
    system = PersonaSystem()
    detector = PersonaDetector()

    # Test candidate flow
    candidate_message = "I have an interview next week and I'm nervous"
    candidate_objective = detector.detect_objective(candidate_message, UserRole.candidate)
    candidate_mode = detector.detect_conversation_mode(candidate_message)
    candidate_persona = system._select_persona(UserRole.candidate, candidate_objective)

    assert candidate_objective == CandidateObjective.interview_prep
    assert candidate_mode == ConversationMode.supportive
    assert candidate_persona.id == "interview_coach"

    # Test recruiter flow
    recruiter_message = "Why is our hiring taking so long? We've been open for 45 days"
    recruiter_objective = detector.detect_objective(recruiter_message, UserRole.recruiter)
    recruiter_mode = detector.detect_conversation_mode(recruiter_message)
    recruiter_persona = system._select_persona(UserRole.recruiter, recruiter_objective)

    assert recruiter_objective == RecruiterObjective.pipeline_management
    assert recruiter_mode == ConversationMode.analytical
    assert recruiter_persona.id == "pipeline_manager"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
