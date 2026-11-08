"""Descriptive analytics (Phase 5).

Every stance/concern-group figure here is wrapped in an explicit
"available: bool" flag. A policy with zero comments and a policy with
1,000 unclassified comments must never report the same "stance_distribution:
{}" with no way to tell them apart -- `available=False` means "no
predictions/groups exist yet" (a pipeline that hasn't run), while
`available=True` with an empty distribution would mean "the pipeline ran
and genuinely found nothing," a materially different and much rarer
situation. No stance distribution is ever computed from anything other
than real StancePrediction rows -- there is no synthetic/placeholder
fallback path anywhere in this module.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.models.comment import Comment, CommentSourceMetadata
from backend.app.models.concern import ConcernGroup
from backend.app.models.policy import PolicyDocument
from backend.app.models.stance import StancePrediction


@dataclass
class PolicyAnalytics:
    policy_document_id: int
    total_comments: int
    comments_by_source: dict[str, int]
    language_distribution: dict[str, int]
    submission_timeline: dict[str, int]  # ISO date -> count
    data_quality: dict[str, int | float]
    stance_available: bool
    stance_distribution: dict[str, int]
    exclusion_distribution: dict[str, int]
    pending_stance_count: int
    concern_groups_available: bool
    concern_group_count: int
    noise_comment_count: int
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


def compute_policy_analytics(db: Session, policy_id: int) -> PolicyAnalytics:
    comments = db.execute(
        select(Comment).where(Comment.policy_document_id == policy_id)
    ).scalars().all()
    total_comments = len(comments)
    comment_ids = [c.id for c in comments]

    source_rows = db.execute(
        select(CommentSourceMetadata.source_dataset, func.count())
        .join(Comment, Comment.id == CommentSourceMetadata.comment_id)
        .where(Comment.policy_document_id == policy_id)
        .group_by(CommentSourceMetadata.source_dataset)
    ).all()
    comments_by_source = {src: n for src, n in source_rows}

    language_distribution = dict(Counter(c.language for c in comments))

    timeline: Counter[str] = Counter()
    for c in comments:
        timeline[c.created_at.date().isoformat()] += 1

    multiplicities = [c.multiplicity for c in comments]
    data_quality = {
        "pii_flagged_count": sum(1 for c in comments if c.pii_flagged),
        "validated_count": sum(1 for c in comments if c.validation_status == "validated"),
        "flagged_for_review_count": sum(1 for c in comments if c.validation_status == "flagged_for_review"),
        "pending_validation_count": sum(1 for c in comments if c.validation_status == "pending"),
        "duplicate_text_merge_count": sum(1 for m in multiplicities if m > 1),
        "max_multiplicity": max(multiplicities) if multiplicities else 0,
    }

    stance_predictions = []
    if comment_ids:
        stance_predictions = db.execute(
            select(StancePrediction)
            .where(StancePrediction.comment_id.in_(comment_ids))
            .order_by(StancePrediction.comment_id, StancePrediction.created_at.desc())
        ).scalars().all()
    latest_by_comment: dict[int, StancePrediction] = {}
    for p in stance_predictions:
        latest_by_comment.setdefault(p.comment_id, p)

    stance_counts: Counter[str] = Counter()
    exclusion_counts: Counter[str] = Counter()
    for p in latest_by_comment.values():
        if p.label:
            stance_counts[p.label.value if hasattr(p.label, "value") else p.label] += 1
        elif p.exclusion_code:
            exclusion_counts[p.exclusion_code.value if hasattr(p.exclusion_code, "value") else p.exclusion_code] += 1

    groups = db.execute(
        select(ConcernGroup).where(ConcernGroup.policy_document_id == policy_id)
    ).scalars().all()

    return PolicyAnalytics(
        policy_document_id=policy_id,
        total_comments=total_comments,
        comments_by_source=comments_by_source,
        language_distribution=language_distribution,
        submission_timeline=dict(sorted(timeline.items())),
        data_quality=data_quality,
        stance_available=len(latest_by_comment) > 0,
        stance_distribution=dict(stance_counts),
        exclusion_distribution=dict(exclusion_counts),
        pending_stance_count=total_comments - len(latest_by_comment),
        concern_groups_available=len(groups) > 0,
        concern_group_count=len([g for g in groups if not g.is_noise]),
        noise_comment_count=sum(g.size for g in groups if g.is_noise),
    )


@dataclass
class CrossPolicySummary:
    total_comments: int
    comments_by_policy: dict[str, int]  # policy title -> count
    total_policies: int


def compute_cross_policy_summary(db: Session) -> CrossPolicySummary:
    rows = db.execute(
        select(PolicyDocument.title, func.count(Comment.id))
        .join(Comment, Comment.policy_document_id == PolicyDocument.id, isouter=True)
        .group_by(PolicyDocument.id, PolicyDocument.title)
    ).all()
    comments_by_policy = {title: count for title, count in rows}
    return CrossPolicySummary(
        total_comments=sum(comments_by_policy.values()),
        comments_by_policy=comments_by_policy,
        total_policies=len(rows),
    )
