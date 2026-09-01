# Enhanced Matching Engine

## Overview

The enhanced matching engine provides comprehensive job-candidate matching using a multi-component scoring system that combines keyword, semantic, and capability signals.

## Components

### matcher.py

**EnhancedMatcher** - Main matching class with the following features:

- **Multi-component scoring**: Combines three independent signals
  - `keyword_score` (0-100): Exact skill and keyword matching
  - `semantic_score` (0-100): Conceptual similarity using embeddings
  - `capability_score` (0-100): Experience level and skill depth alignment

- **Match type classification**:
  - `perfect_match`: All signals >= 80
  - `hidden_gem`: Weak keywords (<60) but strong semantic (>=70) and capability (>=70)
  - `overqualified`: Capability >> expected for role
  - `growth_opportunity`: Strong semantic (>=75) but weaker capability (<70)
  - `partial_match`: Default/mixed signals

- **Comprehensive skill analysis**: 
  - Extracts aligned skills from job description
  - Identifies missing skills for development
  - Provides proficiency and experience breakdowns

- **Deterministic scoring**: 
  - Same candidate+job always produces same score
  - Reproducible results for testing and auditing
  - Leverages existing semantic_match engine with lexical fallback

## Key Methods

### `match_with_components(candidate_profile, job_description, role_level=None) -> MatchResult`

Main matching method returning comprehensive analysis.

**Parameters:**
- `candidate_profile`: Dict with resume_text, skills, experience_years, seniority_level, etc.
- `job_description`: Full JD text
- `role_level`: Optional expected seniority (junior, mid, senior, lead)

**Returns:** `MatchResult` with:
- Component scores and overall score
- Match type classification
- Human-readable explanation
- Aligned and missing skills
- Matched and missing concepts
- Detailed component analysis

## Data Structures

### MatchResult

```python
@dataclass
class MatchResult:
    keyword_score: float  # 0-100
    semantic_score: float  # 0-100
    capability_score: float  # 0-100
    overall_score: float  # Weighted average
    match_type: MatchType  # Classification
    explanation: str  # Human explanation
    skills_aligned: list[Skill]  # Matched skills
    skills_missing: list[Skill]  # Missing skills
    matched_concepts: list[str]  # Semantic matches
    missing_concepts: list[str]  # Semantic gaps
    component_details: dict  # Analysis metadata
```

### Skill

```python
@dataclass
class Skill:
    name: str
    proficiency: Optional[str]  # expert, advanced, intermediate, beginner
    years_of_experience: Optional[float]
    confidence: float  # 0-1
    source: str  # resume, jd, inferred
```

## Scoring Details

### Keyword Score
- Token overlap between resume and JD
- Exact skill matching bonus (+20 for well-matched skills)
- Weighted by skill importance

### Semantic Score
- Uses embeddings model (model2vec) for conceptual matching
- Lexical fallback if embeddings unavailable
- Deterministic and reproducible
- Thresholds configurable via settings

### Capability Score
- Level alignment (same level = 100, ±1 level = 80)
- Skill depth (years of experience, specialization)
- Domain alignment (industry overlap)

### Overall Score
- Weighted combination:
  - 30% keyword
  - 35% semantic
  - 35% capability

## Usage Example

```python
from app.engines.matching.matcher import EnhancedMatcher

matcher = EnhancedMatcher()

candidate = {
    "resume_text": "...",
    "current_title": "Senior Engineer",
    "experience_years": 8,
    "seniority_level": "senior",
    "skills": [
        {"name": "Python", "years_of_experience": 8},
        {"name": "AWS", "years_of_experience": 6},
    ],
}

job_description = "Senior Python Engineer with AWS experience..."

result = matcher.match_with_components(
    candidate,
    job_description,
    role_level="senior"
)

print(f"Match Score: {result.overall_score}")
print(f"Type: {result.match_type.value}")
print(f"Explanation: {result.explanation}")
```

## Testing

Comprehensive test coverage in `tests/test_enhanced_matcher.py`:
- Component scoring accuracy
- Match type classification
- Skill extraction
- Level alignment
- Serialization
- Edge cases and error handling

Run tests:
```bash
pytest tests/test_enhanced_matcher.py -v
```

## Integration

The matcher integrates with:
- `app.engines.semantic_match` - Semantic scoring
- `app.engines.text_utils` - Text tokenization
- `app.models` - Resume and position data

## Performance Considerations

- Scoring is synchronous and fast (< 100ms per match)
- Embeddings are cached in-memory
- Suitable for real-time matching in API endpoints
- Batch matching recommended for large-scale operations
