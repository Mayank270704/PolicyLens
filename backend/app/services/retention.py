"""Data retention configuration (Phase 6).

This module only ever IDENTIFIES retention candidates -- it never
deletes anything itself. Deleting real submitted public comments is a
policy-level decision with legal/records-retention implications that
this codebase should never automate silently; an actual deletion
operation (if ever implemented) must be a separate, explicitly-invoked,
audited action -- not a side effect of calling a "find candidates"
function.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.config import get_settings
from backend.app.models.comment import Comment


def find_retention_candidates(db: Session, policy_id: int | None = None) -> list[Comment]:
    """Returns comments older than `RETENTION_POLICY_DAYS` (if configured).
    Returns an empty list (not an error) when no retention policy is
    configured -- indefinite retention is this project's explicit
    default for a research dataset, not a missing feature."""
    settings = get_settings()
    if settings.retention_policy_days is None:
        return []

    cutoff = datetime.now(timezone.utc) - timedelta(days=settings.retention_policy_days)
    stmt = select(Comment).where(Comment.created_at < cutoff)
    if policy_id is not None:
        stmt = stmt.where(Comment.policy_document_id == policy_id)
    return list(db.execute(stmt).scalars().all())
