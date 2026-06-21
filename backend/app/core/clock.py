"""Time helpers.

`datetime.utcnow()` is deprecated (Python 3.12+). This is a drop-in replacement
that returns a NAIVE UTC datetime — identical semantics to the old call — so it
can replace `datetime.utcnow` everywhere without introducing aware/naive
comparison bugs. (Use a timezone-aware value explicitly where aware datetimes
are genuinely wanted; this preserves existing behaviour.)
"""
from __future__ import annotations

from datetime import datetime, timezone


def utcnow() -> datetime:
    """Naive UTC now — drop-in for the deprecated ``datetime.utcnow()``."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
