"""LLM token-usage and cost tracking.

Central place to turn an Anthropic ``response.usage`` object into:
- structured logs (per call: model, tokens, cost, cache hit-rate),
- Prometheus counters (total tokens + cost, labelled by model),
- a per-context accumulator (a ``ContextVar``) so a single request/task/chat
  turn can read "how much did this cost" — used to wire real cost into the
  autonomous budget gate (which previously recorded ~0).

Pricing is per-million-tokens (USD), keyed by a substring of the model id with a
conservative default, so a model rename doesn't silently zero the cost.
"""
from __future__ import annotations

import logging
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger("truematch.llm_usage")

# Per-million-token prices (USD): (input, output, cache_write, cache_read).
_PRICING: dict[str, tuple[float, float, float, float]] = {
    "opus":   (15.0, 75.0, 18.75, 1.50),
    "sonnet": (3.0, 15.0, 3.75, 0.30),
    "haiku":  (0.80, 4.0, 1.0, 0.08),
}
_DEFAULT_PRICING = (3.0, 15.0, 3.75, 0.30)  # assume sonnet-class if unknown


def _prices_for(model: str) -> tuple[float, float, float, float]:
    m = (model or "").lower()
    for key, prices in _PRICING.items():
        if key in m:
            return prices
    return _DEFAULT_PRICING


@dataclass
class UsageTotals:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_write_tokens: int = 0
    cache_read_tokens: int = 0
    cost_usd: float = 0.0
    calls: int = 0

    def as_dict(self) -> dict[str, Any]:
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cache_write_tokens": self.cache_write_tokens,
            "cache_read_tokens": self.cache_read_tokens,
            "cost_usd": round(self.cost_usd, 6),
            "calls": self.calls,
        }


# Per-context accumulator. Reset at the start of a request/task; read at the end.
_usage_ctx: ContextVar[UsageTotals | None] = ContextVar("llm_usage", default=None)

# Global day-spend (per process). Used by budget-aware model routing: cheap to
# track, resets at UTC midnight (and on process restart — acceptable: routing is
# an economy heuristic, not an accounting source of truth; Prometheus has the
# durable counters).
_day_key: str | None = None
_day_spend_usd: float = 0.0


def _record_day_spend(cost: float) -> None:
    global _day_key, _day_spend_usd
    from datetime import datetime, timezone

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if _day_key != today:
        _day_key = today
        _day_spend_usd = 0.0
    _day_spend_usd += cost


def day_spend_usd() -> float:
    """This process's LLM spend so far today (USD)."""
    from datetime import datetime, timezone

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return _day_spend_usd if _day_key == today else 0.0


def reset_usage() -> None:
    """Start a fresh accumulation window for the current context."""
    _usage_ctx.set(UsageTotals())


def get_usage() -> UsageTotals:
    """Return the accumulated usage for the current context (zeros if unset)."""
    return _usage_ctx.get() or UsageTotals()


# ── Prometheus (optional; guarded like core.observability) ───────────────────
_prom = None


def _prometheus():
    global _prom
    if _prom is not None:
        return _prom
    try:
        from prometheus_client import Counter, Histogram

        _prom = {
            "tokens": Counter(
                "truematch_llm_tokens_total",
                "LLM tokens consumed",
                ["model", "kind"],
            ),
            "cost": Counter(
                "truematch_llm_cost_usd_total",
                "Estimated LLM cost in USD",
                ["model"],
            ),
            "calls": Counter(
                "truematch_llm_calls_total",
                "LLM API calls",
                ["model"],
            ),
            "latency": Histogram(
                "truematch_llm_latency_seconds",
                "LLM call wall-clock latency",
                ["model"],
                buckets=(0.5, 1, 2, 4, 8, 16, 32, 64),
            ),
        }
    except Exception:  # noqa: BLE001 — metrics are best-effort
        _prom = {}
    return _prom


def record_latency(model: str, seconds: float) -> None:
    """Record an LLM call's wall-clock latency."""
    prom = _prometheus()
    if prom and "latency" in prom:
        prom["latency"].labels(model=model).observe(max(0.0, seconds))


def record_usage(model: str, usage: Any) -> float:
    """Record one call's usage. Returns the call's cost in USD.

    ``usage`` is an Anthropic usage object (or anything with the same int
    attributes). Safe to call with None.
    """
    if usage is None:
        return 0.0

    def _g(name: str) -> int:
        return int(getattr(usage, name, 0) or 0)

    in_tok = _g("input_tokens")
    out_tok = _g("output_tokens")
    cache_write = _g("cache_creation_input_tokens")
    cache_read = _g("cache_read_input_tokens")

    p_in, p_out, p_cw, p_cr = _prices_for(model)
    cost = (
        in_tok * p_in + out_tok * p_out + cache_write * p_cw + cache_read * p_cr
    ) / 1_000_000.0

    # Accumulate into the current context.
    totals = _usage_ctx.get()
    if totals is not None:
        totals.input_tokens += in_tok
        totals.output_tokens += out_tok
        totals.cache_write_tokens += cache_write
        totals.cache_read_tokens += cache_read
        totals.cost_usd += cost
        totals.calls += 1

    # Day-spend accumulator for budget-aware model routing.
    _record_day_spend(cost)

    # Prometheus.
    prom = _prometheus()
    if prom:
        prom["tokens"].labels(model=model, kind="input").inc(in_tok)
        prom["tokens"].labels(model=model, kind="output").inc(out_tok)
        prom["tokens"].labels(model=model, kind="cache_write").inc(cache_write)
        prom["tokens"].labels(model=model, kind="cache_read").inc(cache_read)
        prom["cost"].labels(model=model).inc(cost)
        prom["calls"].labels(model=model).inc()

    cached = cache_read / in_tok if in_tok else 0.0
    logger.info(
        "LLM usage",
        extra={
            "model": model,
            "input_tokens": in_tok,
            "output_tokens": out_tok,
            "cache_read_tokens": cache_read,
            "cache_hit_rate": round(cached, 3),
            "cost_usd": round(cost, 6),
        },
    )
    return cost
