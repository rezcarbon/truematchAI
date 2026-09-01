"""Self-learned role taxonomy — deterministic embedding clustering of JDs.

Single-pass greedy cosine clustering over position-JD embeddings (model2vec,
the same static embedder the semantic matcher uses — no torch). Deterministic:
positions are processed in a stable order, so the same corpus always yields the
same clusters. Each cluster stores a centroid (to assign future positions
cheaply) and the capabilities that recur across its members, which the
assessment pipeline injects as learned role context.
"""
from __future__ import annotations

import logging
import uuid
from collections import Counter

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models.position import Position
from app.models.role_cluster import RoleCluster

logger = logging.getLogger("truematch.role_taxonomy")

_MAX_CAPS = 10


def _position_text(p: Position) -> str:
    return f"{p.title or ''}. {p.description or ''}".strip()


def _capabilities(p: Position) -> list[str]:
    req = p.parsed_requirements or {}
    caps = req.get("required_capabilities") or req.get("capabilities") or []
    return [str(c).strip().lower() for c in caps if str(c).strip()]


def _label_for(members: list[Position]) -> str:
    """Human-readable label from the most common significant title tokens."""
    stop = {"senior", "junior", "lead", "staff", "principal", "the", "and", "of",
            "a", "an", "i", "ii", "iii", "engineer", "manager", "specialist"}
    tokens: Counter = Counter()
    for p in members:
        for tok in (p.title or "").lower().replace("/", " ").split():
            tok = tok.strip(",.()")
            if len(tok) > 2 and tok not in stop:
                tokens[tok] += 1
    top = [t for t, _ in tokens.most_common(2)]
    base = " / ".join(top) if top else (members[0].title or "role").lower()
    return f"{base} family"[:255]


def rebuild_taxonomy(db: Session) -> dict:
    """Recompute the full role taxonomy from current positions. Idempotent.

    Returns a summary dict. No-op (returns reason) when embeddings are
    unavailable or there are too few positions to cluster.
    """
    if not settings.role_taxonomy_enabled:
        return {"status": "disabled"}

    from app.engines import semantic_match

    embedder = semantic_match._embedder()  # None when model unavailable
    if embedder is None:
        return {"status": "skipped", "reason": "embeddings unavailable"}

    # Stable, deterministic order.
    positions = list(
        db.execute(
            select(Position)
            .where(Position.description.is_not(None))
            .order_by(Position.created_at, Position.id)
        ).scalars()
    )
    positions = [p for p in positions if _position_text(p)]
    if len(positions) < 2:
        return {"status": "skipped", "reason": "need >=2 positions", "positions": len(positions)}

    import numpy as np

    texts = [_position_text(p) for p in positions]
    vecs = np.asarray(embedder.encode(texts), dtype=float)
    vecs = vecs / (np.linalg.norm(vecs, axis=1, keepdims=True) + 1e-9)

    threshold = settings.role_taxonomy_similarity
    centroids: list[np.ndarray] = []      # running mean unit-vectors
    members: list[list[int]] = []         # position indices per cluster

    for i in range(len(positions)):
        v = vecs[i]
        if centroids:
            sims = np.asarray([float(c @ v) for c in centroids])
            best = int(sims.argmax())
            if sims[best] >= threshold:
                members[best].append(i)
                m = vecs[[*members[best]]].mean(axis=0)
                centroids[best] = m / (np.linalg.norm(m) + 1e-9)
                continue
        centroids.append(v.copy())
        members.append([i])

    method = f"{semantic_match.active_method()}+greedy-cosine@{threshold}"

    # Replace the taxonomy wholesale (clear FKs first so the SET NULL parent
    # rows can be deleted), then recreate — keeps the rebuild deterministic.
    for p in positions:
        p.role_cluster_id = None
    db.flush()
    for old in db.execute(select(RoleCluster)).scalars().all():
        db.delete(old)
    db.flush()

    summary = []
    for idx, member_ids in enumerate(members):
        member_positions = [positions[j] for j in member_ids]
        cap_counter: Counter = Counter()
        for p in member_positions:
            cap_counter.update(_capabilities(p))
        top_caps = [c for c, _ in cap_counter.most_common(_MAX_CAPS)]
        cluster = RoleCluster(
            label=_label_for(member_positions),
            centroid=[round(float(x), 6) for x in centroids[idx].tolist()],
            size=len(member_positions),
            top_capabilities=top_caps,
            method=method,
        )
        db.add(cluster)
        db.flush()
        for p in member_positions:
            p.role_cluster_id = cluster.id
        summary.append({"label": cluster.label, "size": cluster.size, "top_capabilities": top_caps})

    db.commit()
    logger.info("Rebuilt role taxonomy: %d clusters from %d positions", len(members), len(positions))
    return {
        "status": "completed",
        "positions": len(positions),
        "clusters": len(members),
        "method": method,
        "detail": summary,
    }


def fetch_role_context_sync(db: Session, position_id: uuid.UUID) -> str:
    """Prompt-ready role-family context for a position, or "" if none.

    Injected into the capability assessment alongside the success-pattern
    learned context — the role family is learned from the org's own JDs.
    """
    try:
        position = db.get(Position, position_id)
        if position is None or position.role_cluster_id is None:
            return ""
        cluster = db.get(RoleCluster, position.role_cluster_id)
        if cluster is None or not cluster.top_capabilities:
            return ""
        caps = ", ".join(list(cluster.top_capabilities)[:8])
        return (
            f"ROLE FAMILY — this position clustered (self-learned, {cluster.method}) "
            f"into the '{cluster.label}' family of {cluster.size} comparable role(s). "
            f"Capabilities that recur across that family: {caps}. Weight evidence of "
            f"these when present, as peers in this family consistently require them."
        )
    except Exception as exc:  # noqa: BLE001 — never break an assessment
        logger.warning("fetch_role_context_sync failed: %s", exc)
        return ""
