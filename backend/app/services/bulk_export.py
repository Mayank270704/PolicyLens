"""CSV export for a policy's comments, joined with their latest stance
prediction (if any). Read-only; never modifies anything."""
from __future__ import annotations

import csv
import io

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.comment import Comment, CommentSourceMetadata
from backend.app.models.stance import StancePrediction

EXPORT_COLUMNS = (
    "comment_id", "original_text", "normalized_text", "language", "multiplicity",
    "source_dataset", "source_record_id", "validation_status", "pii_flagged",
    "latest_stance_label", "latest_exclusion_code", "latest_stance_source",
)


def export_comments_csv(db: Session, policy_id: int) -> str:
    rows = db.execute(
        select(Comment, CommentSourceMetadata)
        .join(CommentSourceMetadata, CommentSourceMetadata.comment_id == Comment.id, isouter=True)
        .where(Comment.policy_document_id == policy_id)
        .order_by(Comment.id)
    ).all()

    predictions_by_comment: dict[int, StancePrediction] = {}
    comment_ids = [c.id for c, _ in rows]
    if comment_ids:
        preds = db.execute(
            select(StancePrediction)
            .where(StancePrediction.comment_id.in_(comment_ids))
            .order_by(StancePrediction.comment_id, StancePrediction.created_at.desc())
        ).scalars().all()
        for p in preds:
            predictions_by_comment.setdefault(p.comment_id, p)  # first per id, given the ORDER BY, is the latest

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=EXPORT_COLUMNS)
    writer.writeheader()
    for comment, source_meta in rows:
        pred = predictions_by_comment.get(comment.id)
        writer.writerow({
            "comment_id": comment.id,
            "original_text": comment.original_text,
            "normalized_text": comment.normalized_text,
            "language": comment.language,
            "multiplicity": comment.multiplicity,
            "source_dataset": source_meta.source_dataset if source_meta else "",
            "source_record_id": source_meta.source_record_id if source_meta else "",
            "validation_status": comment.validation_status,
            "pii_flagged": comment.pii_flagged,
            "latest_stance_label": (pred.label.value if pred and pred.label else ""),
            "latest_exclusion_code": (pred.exclusion_code.value if pred and pred.exclusion_code else ""),
            "latest_stance_source": (pred.source.value if pred else ""),
        })
    return buf.getvalue()
