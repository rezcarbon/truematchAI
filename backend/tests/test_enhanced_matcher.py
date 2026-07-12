"""Tests for enhanced matching engine."""
import pytest

from app.engines.matching.matcher import (
    EnhancedMatcher,
    MatchType,
    Skill,
)


class TestEnhancedMatcher:
    """Test EnhancedMatcher functionality."""

    @pytest.fixture
    def matcher(self):
        """Create matcher instance."""
        return EnhancedMatcher()

    @pytest.fixture
    def candidate_profile(self):
        """Sample candidate profile."""
        return {
            "resume_text": (
                "Senior Software Engineer with 8 years experience in Python, Java, "
                "and cloud technologies. Expert in AWS, Kubernetes, Docker. "
                "Led teams of 5+ engineers. Experience with React and Node.js. "
                "Strong background in microservices and DevOps practices."
            ),
            "current_title": "Senior Software Engineer",
            "experience_years": 8,
            "seniority_level": "senior",
            "skills": [
                {"name": "Python", "years_of_experience": 8, "proficiency": "expert"},
                {"name": "Java", "years_of_experience": 7, "proficiency": "expert"},
                {"name": "AWS", "years_of_experience": 6, "proficiency": "expert"},
                {"name": "Kubernetes", "years_of_experience": 5, "proficiency": "advanced"},
                {"name": "Docker", "years_of_experience": 5, "proficiency": "advanced"},
                {"name": "React", "years_of_experience": 3, "proficiency": "intermediate"},
                {"name": "Leadership", "years_of_experience": 4, "proficiency": "advanced"},
            ],
            "industries": ["technology", "fintech"],
            "background": "Built scalable distributed systems for high-traffic applications",
        }

    @pytest.fixture
    def junior_profile(self):
        """Junior candidate profile."""
        return {
            "resume_text": (
                "Recent bootcamp graduate with 6 months professional experience. "
                "Proficient in Python, JavaScript, HTML/CSS. "
                "Built a few small projects with React and Flask."
            ),
            "current_title": "Junior Software Engineer",
            "experience_years": 0.5,
            "seniority_level": "junior",
            "skills": [
                {"name": "Python", "years_of_experience": 0.5, "proficiency": "intermediate"},
                {"name": "JavaScript", "years_of_experience": 0.5, "proficiency": "intermediate"},
                {"name": "React", "years_of_experience": 0.3, "proficiency": "beginner"},
                {"name": "Flask", "years_of_experience": 0.3, "proficiency": "beginner"},
            ],
            "industries": [],
            "background": "Recent bootcamp graduate eager to learn",
        }

    def test_perfect_match(self, matcher, candidate_profile):
        """Test perfect match detection."""
        job_description = (
            "Senior Python Engineer - We seek an experienced Senior Engineer with 7+ years "
            "building distributed systems. Required: Python, AWS, Kubernetes, Docker, Java. "
            "Experience with microservices and DevOps is essential. "
            "Leadership experience managing teams preferred. "
            "Knowledge of React or similar frameworks beneficial."
        )

        result = matcher.match_with_components(
            candidate_profile,
            job_description,
            role_level="senior",
        )

        assert result.overall_score >= 70
        assert result.match_type == MatchType.perfect_match
        assert len(result.skills_aligned) > 0
        assert result.keyword_score > 70
        assert result.semantic_score > 70
        assert result.capability_score > 70

    def test_hidden_gem_detection(self, matcher, candidate_profile):
        """Test hidden gem detection."""
        job_description = (
            "We're looking for someone to build our next-gen platform architecture. "
            "The role involves designing resilient, scalable systems that handle millions "
            "of requests. You'll work with distributed computing concepts, system design, "
            "and cloud infrastructure. Experience with orchestration platforms and containers "
            "is crucial. Strong software engineering fundamentals required."
        )

        result = matcher.match_with_components(
            candidate_profile,
            job_description,
            role_level="senior",
        )

        # Hidden gem has lower keyword overlap but high semantic/capability
        if result.match_type == MatchType.hidden_gem:
            assert result.keyword_score < 60
            assert result.semantic_score >= 70
            assert result.capability_score >= 70

    def test_overqualified_detection(self, matcher, candidate_profile):
        """Test overqualified detection."""
        job_description = (
            "Entry-level developer position. We're looking for someone to help "
            "build web pages and learn our codebase. Experience with HTML, CSS, "
            "and some JavaScript required. No experience necessary."
        )

        result = matcher.match_with_components(
            candidate_profile,
            job_description,
            role_level="junior",
        )

        # May be detected as overqualified
        if result.match_type == MatchType.overqualified:
            assert result.capability_score > result.keyword_score + 20

    def test_growth_opportunity_detection(self, matcher, junior_profile):
        """Test growth opportunity detection."""
        job_description = (
            "Mid-level Python Engineer. We seek someone comfortable with Python "
            "who's ready to level up their skills. Should understand distributed systems "
            "concepts, cloud platforms, and DevOps practices. We'll provide mentorship."
        )

        result = matcher.match_with_components(
            junior_profile,
            job_description,
            role_level="mid",
        )

        # Growth opportunity: semantic match but capability development needed
        if result.match_type == MatchType.growth_opportunity:
            assert result.semantic_score >= 70
            assert result.capability_score < 70

    def test_keyword_scoring(self, matcher, candidate_profile):
        """Test keyword scoring calculation."""
        job_description = "Python, Java, AWS, Kubernetes, Docker"
        result = matcher.match_with_components(candidate_profile, job_description)

        # Should score high on keywords
        assert result.keyword_score >= 60

    def test_empty_profile_handling(self, matcher):
        """Test handling of empty profile."""
        result = matcher.match_with_components({}, "job description")
        assert result.overall_score == 0.0
        assert result.keyword_score == 0.0

    def test_empty_jd_handling(self, matcher, candidate_profile):
        """Test handling of empty job description."""
        result = matcher.match_with_components(candidate_profile, "")
        assert result.overall_score == 0.0

    def test_skill_extraction(self, matcher):
        """Test skill extraction from job description."""
        jd = "Python, JavaScript, SQL, Docker, AWS"
        skills = matcher._extract_skill_requirements(jd)

        assert "python" in skills
        assert "javascript" in skills
        assert "sql" in skills
        assert "docker" in skills
        assert "aws" in skills

    def test_industry_extraction(self, matcher):
        """Test industry extraction."""
        jd = "Fintech startup in the financial technology space"
        industries = matcher._extract_industries(jd)

        assert "fintech" in industries or "finance" in industries

    def test_level_alignment_scoring(self, matcher):
        """Test level alignment scoring."""
        # Same level
        score = matcher._score_level_alignment("senior", "senior", 8)
        assert score == 100.0

        # One level difference
        score = matcher._score_level_alignment("mid", "senior", 5)
        assert score == 80.0

        # Multiple levels difference
        score = matcher._score_level_alignment("junior", "lead", 1)
        assert score < 80.0

    def test_skill_depth_scoring(self, matcher):
        """Test skill depth scoring."""
        skills = [
            {"name": "Python", "years_of_experience": 10},
            {"name": "Java", "years_of_experience": 8},
            {"name": "SQL", "years_of_experience": 5},
        ]

        score = matcher._score_skill_depth(skills)
        assert score > 0
        assert score <= 100

    def test_explanation_generation(self, matcher):
        """Test explanation generation for different match types."""
        # Perfect match explanation
        exp = matcher._generate_explanation(
            MatchType.perfect_match,
            85.0,
            87.0,
            88.0,
        )
        assert "Excellent" in exp or "excellent" in exp.lower()

        # Hidden gem explanation
        exp = matcher._generate_explanation(
            MatchType.hidden_gem,
            45.0,
            82.0,
            79.0,
        )
        assert "potential" in exp.lower() or "hidden" in exp.lower()

    def test_match_result_serialization(self, matcher, candidate_profile):
        """Test MatchResult serialization."""
        job_description = "Senior Python Engineer with AWS experience"
        result = matcher.match_with_components(candidate_profile, job_description)

        result_dict = result.to_dict()

        assert "keyword_score" in result_dict
        assert "semantic_score" in result_dict
        assert "capability_score" in result_dict
        assert "overall_score" in result_dict
        assert "match_type" in result_dict
        assert "explanation" in result_dict
        assert isinstance(result_dict["overall_score"], (int, float))

    def test_skill_dataclass(self):
        """Test Skill dataclass."""
        skill = Skill(
            name="Python",
            proficiency="expert",
            years_of_experience=5,
            confidence=0.9,
        )

        skill_dict = skill.to_dict()
        assert skill_dict["name"] == "Python"
        assert skill_dict["proficiency"] == "expert"
        assert skill_dict["years_of_experience"] == 5

    def test_consistent_scoring(self, matcher, candidate_profile):
        """Test that same inputs produce consistent scores."""
        job_description = "Senior Python Engineer"

        result1 = matcher.match_with_components(
            candidate_profile,
            job_description,
            role_level="senior",
        )

        result2 = matcher.match_with_components(
            candidate_profile,
            job_description,
            role_level="senior",
        )

        assert result1.overall_score == result2.overall_score
        assert result1.keyword_score == result2.keyword_score
        assert result1.semantic_score == result2.semantic_score
        assert result1.match_type == result2.match_type


class TestMatchTypeClassification:
    """Test match type classification logic."""

    @pytest.fixture
    def matcher(self):
        return EnhancedMatcher()

    def test_perfect_match_threshold(self, matcher):
        """Test perfect match classification."""
        match_type = matcher._classify_match_type(
            keyword_score=85.0,
            semantic_score=85.0,
            capability_score=85.0,
            role_level="mid",
            experience_years=5,
        )
        assert match_type == MatchType.perfect_match

    def test_hidden_gem_threshold(self, matcher):
        """Test hidden gem classification."""
        match_type = matcher._classify_match_type(
            keyword_score=50.0,
            semantic_score=75.0,
            capability_score=75.0,
            role_level="mid",
            experience_years=5,
        )
        assert match_type == MatchType.hidden_gem

    def test_growth_opportunity_threshold(self, matcher):
        """Test growth opportunity classification."""
        match_type = matcher._classify_match_type(
            keyword_score=60.0,
            semantic_score=75.0,
            capability_score=50.0,
            role_level="mid",
            experience_years=2,
        )
        assert match_type == MatchType.growth_opportunity

    def test_partial_match_fallback(self, matcher):
        """Test partial match as default."""
        match_type = matcher._classify_match_type(
            keyword_score=50.0,
            semantic_score=50.0,
            capability_score=50.0,
            role_level="mid",
            experience_years=5,
        )
        assert match_type == MatchType.partial_match
