"""Lightweight phase timing for pipeline observability.

A context manager that times a named phase, logs its duration, and (when
prometheus is available) records it to a labelled histogram. Used to break down
the assessment pipeline latency (intake / scoring / governance / persistence).
"""
from __future__ import annotations

import logging
import time
from contextlib import contextmanager

logger = logging.getLogger("truematch.timing")

_phase_hist = None
_phase_hist_init = False


def _histogram():
    global _phase_hist, _phase_hist_init
    if _phase_hist_init:
        return _phase_hist
    _phase_hist_init = True
    try:
        from prometheus_client import Histogram

        _phase_hist = Histogram(
            "truematch_pipeline_phase_seconds",
            "Wall-clock duration of a named pipeline phase",
            ["phase"],
            buckets=(0.05, 0.1, 0.25, 0.5, 1, 2, 4, 8, 16, 32, 64),
        )
    except Exception:  # noqa: BLE001 — metrics are best-effort
        _phase_hist = None
    return _phase_hist


@contextmanager
def phase_timer(phase: str):
    """Time a code block as a named pipeline phase."""
    started = time.monotonic()
    try:
        yield
    finally:
        elapsed = time.monotonic() - started
        hist = _histogram()
        if hist is not None:
            try:
                hist.labels(phase=phase).observe(elapsed)
            except Exception:  # noqa: BLE001
                pass
        logger.info("phase complete", extra={"phase": phase, "seconds": round(elapsed, 3)})
