"""Server-side prompt registry.

PROPRIETARY: prompt templates are intellectual property and MUST NOT be exposed
via any API endpoint, log line, or client response. They are imported only by
engine modules running server-side.

The templates below are scaffolds/placeholders intended to be hardened before
production use. Treat their wording as non-final.
"""
from app.engines.prompts.registry import PROMPTS, get_prompt

__all__ = ["PROMPTS", "get_prompt"]
