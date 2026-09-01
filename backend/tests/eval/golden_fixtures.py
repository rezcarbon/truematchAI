"""Golden fixtures for the scoring regression eval.

Canonical (resume, JD) pairs with *relative* expectations. We assert ranking and
determinism rather than brittle absolute scores: a strong-match resume must
out-score a weak-match one for the same JD, and the deterministic engines must
return byte-identical results across runs. This catches prompt/engine
regressions without pinning exact numbers that legitimately drift with tuning.
"""

JD_BACKEND = """
Senior Backend Engineer. We are hiring an experienced backend engineer to design
and operate large-scale distributed systems. Requirements: 8+ years building
production services in Python and Go, deep experience with AWS, Kubernetes and
microservices, strong understanding of system design, databases, and CI/CD.
You will lead technical initiatives and mentor other engineers.
"""

# Strong match — directly demonstrates the JD's requirements.
RESUME_STRONG = """
Staff Software Engineer with 11 years building backend systems. Designed and
operated distributed services in Python and Go at scale on AWS, using Kubernetes
and microservices. Led system-design reviews, owned CI/CD pipelines, mentored a
team of 8 engineers. Deep experience with PostgreSQL, Redis, event-driven
architecture and high-availability production operations.
"""

# Weak match — different discipline, little overlap with the JD.
RESUME_WEAK = """
Senior Graphic Designer with 9 years in brand and marketing design. Expert in
Adobe Photoshop, Illustrator, Figma and motion graphics. Led visual identity
projects, managed creative campaigns, collaborated with marketing teams. No
software engineering or backend experience.
"""

# A second JD for cross-checks (frontend/design-ish) where the weak resume above
# should fare comparatively better than against the backend JD.
JD_DESIGN = """
Senior Product Designer. Seeking a designer with strong visual design skills,
expertise in Figma and brand identity, and experience leading creative projects
and collaborating with marketing teams.
"""


GOLDEN_PAIRS = [
    {
        "id": "backend_strong",
        "jd": JD_BACKEND,
        "resume": RESUME_STRONG,
        "expect": "strong",
    },
    {
        "id": "backend_weak",
        "jd": JD_BACKEND,
        "resume": RESUME_WEAK,
        "expect": "weak",
    },
    {
        "id": "design_match",
        "jd": JD_DESIGN,
        "resume": RESUME_WEAK,
        "expect": "moderate",
    },
]

# The prompt registry version in effect when this baseline was recorded. A change
# to any prompt should bump the registry version; this guard makes that change
# *visible* in the eval (update EXPECTED_PROMPT_REGISTRY deliberately when you
# intend a prompt change, after reviewing its score impact).
# 2026.06.15d: added the capability_translation prompt (candidate-facing ATS
# rewrite). No existing scoring prompt changed, so golden score pairs are
# unaffected — this is an additive re-baseline.
# 2026.06.19a: added the transition_intelligence prompt (candidate-facing
# transition prediction). Again additive — no existing scoring prompt changed,
# so golden score pairs are unaffected.
EXPECTED_PROMPT_REGISTRY = "2026.06.19a"
