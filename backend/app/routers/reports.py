from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.comment import Comment
from backend.app.models.concern import ConcernGroup
from backend.app.models.policy import PolicyDocument
from backend.app.models.stance import StancePrediction
from backend.app.schemas.report import PolicyReportOut

router = APIRouter(tags=["reports"])


@router.get("/policies/{policy_id}/report", response_model=PolicyReportOut)
def get_policy_report(policy_id: int, db: Session = Depends(get_db)) -> PolicyReportOut:
    """Aggregates stance + concern-group data for one policy.
    `completeness_flags` states explicitly which upstream pipeline has
    produced anything at all -- a report generated before classification
    or clustering has run says so, rather than silently presenting a
    partial picture as complete (docs/architecture/SYSTEM_ARCHITECTURE.md
    component 10's error-handling requirement)."""
    if db.get(PolicyDocument, policy_id) is None:
        raise HTTPException(status_code=404, detail=f"Policy {policy_id} not found")

    comment_ids = db.execute(
        select(Comment.id).where(Comment.policy_document_id == policy_id)
    ).scalars().all()
    total_comments = len(comment_ids)

    # Most recent prediction per comment (a comment may have a human first
    # pass and a human repeat pass, or a human pass and a later model pass --
    # the report reflects the latest decision per comment).
    predictions = db.execute(
        select(StancePrediction)
        .where(StancePrediction.comment_id.in_(comment_ids))
        .order_by(StancePrediction.comment_id, StancePrediction.created_at.desc())
    ).scalars().all()
    latest_by_comment: dict[int, StancePrediction] = {}
    for p in predictions:
        latest_by_comment.setdefault(p.comment_id, p)  # first seen per comment_id is the latest, given the ORDER BY

    stance_counts: Counter[str] = Counter()
    exclusion_counts: Counter[str] = Counter()
    for p in latest_by_comment.values():
        if p.label:
            stance_counts[p.label.value if hasattr(p.label, "value") else p.label] += 1
        elif p.exclusion_code:
            exclusion_counts[p.exclusion_code.value if hasattr(p.exclusion_code, "value") else p.exclusion_code] += 1

    pending_count = total_comments - len(latest_by_comment)

    groups = db.execute(
        select(ConcernGroup).where(ConcernGroup.policy_document_id == policy_id)
    ).scalars().all()
    noise_comment_count = sum(g.size for g in groups if g.is_noise)

    return PolicyReportOut(
        policy_document_id=policy_id,
        generated_at=datetime.now(timezone.utc),
        total_comments=total_comments,
        stance_distribution=dict(stance_counts),
        exclusion_distribution=dict(exclusion_counts),
        pending_count=pending_count,
        concern_group_count=len([g for g in groups if not g.is_noise]),
        noise_comment_count=noise_comment_count,
        completeness_flags={
            "has_stance_predictions": len(latest_by_comment) > 0,
            "has_concern_groups": len(groups) > 0,
            "stance_complete": pending_count == 0 and total_comments > 0,
        },
    )
