"""Comment validation, text normalization, and traceability integrity
checking.

Text normalization reuses ml.stance_classification.dataset_prep's
normalize_text -- one implementation shared across the annotation
pipeline, the ML dataset-prep pipeline, and this backend, rather than a
third subtly-different copy.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from ml.stance_classification.dataset_prep import normalize_text  # noqa: E402
from sqlalchemy import select  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from backend.app.models.comment import Comment  # noqa: E402
from backend.app.models.concern import GroupMembership, RepresentativeComment  # noqa: E402
from backend.app.models.summary import EvidenceReference, Summary  # noqa: E402

__all__ = ["normalize_text", "hash_normalized_text", "classify_comment_for_exclusion", "check_traceability_integrity"]


def hash_normalized_text(text: str) -> str:
    return hashlib.sha256(normalize_text(text).lower().encode("utf-8")).hexdigest()


# Mirrors rule D8 / scripts/annotation/schema.py's EXCLUSION_CODES. This is a
# structural, length/pattern-based heuristic ONLY -- it suggests a candidate
# exclusion code for human review, exactly as scripts/annotation/validate.py
# never auto-assigns a label.
#
# IMPORTANT: length alone is NOT disqualifying -- STANCE_ANNOTATION_GUIDELINES.md
# section 5 gives "No, too expensive." as an explicit example of a short but
# SUBSTANTIVE comment (a valid, if brief, Oppose) that must NOT be excluded.
# This heuristic therefore only flags genuinely trivial text (empty, pure
# filler, or a tiny handful of characters with no real content), never
# anything that reads as an actual (if short) evaluative statement.
_MIN_CHARS_FLOOR = 8  # below this, even a non-filler string is unlikely to carry evaluable content
_GENERIC_FILLER = {"ok", "n/a", "na", "test", ".", "-", "none"}


def classify_comment_for_exclusion(text: str) -> str | None:
    stripped = text.strip()
    if not stripped:
        return "TOO_SHORT_NONSUBSTANTIVE"
    if stripped.lower() in _GENERIC_FILLER or len(stripped) < _MIN_CHARS_FLOOR:
        return "TOO_SHORT_NONSUBSTANTIVE"
    alpha_chars = sum(1 for c in stripped if c.isalpha())
    if alpha_chars / max(len(stripped), 1) < 0.3:
        return "UNINTELLIGIBLE"
    return None  # not flagged -- still requires eligibility review for SPAM/OFF_TOPIC, which text alone can't determine


def check_traceability_integrity(db: Session) -> list[str]:
    """Independent, after-the-fact structural audit (RQ4 /
    docs/architecture/DATA_MODEL.md's traceability guarantees) -- modeled
    on ml/stance_classification/validate_splits.py's pattern of
    re-validating output from scratch rather than trusting its own
    manifest. Returns a list of problems; empty = clean."""
    problems: list[str] = []

    comment_ids = set(db.execute(select(Comment.id)).scalars().all())

    for cid in db.execute(select(GroupMembership.comment_id)).scalars().all():
        if cid not in comment_ids:
            problems.append(f"GroupMembership references missing comment_id={cid}")

    for cid in db.execute(select(RepresentativeComment.comment_id)).scalars().all():
        if cid not in comment_ids:
            problems.append(f"RepresentativeComment references missing comment_id={cid}")

    for cid in db.execute(select(EvidenceReference.comment_id)).scalars().all():
        if cid not in comment_ids:
            problems.append(f"EvidenceReference references missing comment_id={cid}")

    summary_ids_with_evidence = set(db.execute(select(EvidenceReference.summary_id)).scalars().all())
    for sid in db.execute(select(Summary.id)).scalars().all():
        if sid not in summary_ids_with_evidence:
            problems.append(f"Summary id={sid} has zero evidence references -- invalid per DATA_MODEL.md")

    return problems
