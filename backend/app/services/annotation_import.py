"""Annotation import adapter.

Consumes rows matching the EXACT schema scripts/annotation/finalize.py
produces (data/annotations/new_experiment/finalized/
stance_annotations_final.csv) -- comment_id, comment_text, policy_context,
policy_section, annotator_label, exclusion_code, annotation_confidence,
annotation_notes, source_unique_id, source_dataset, language, word_count
-- and maps each row into this backend's Comment + StancePrediction
tables (source="human").

This adapter is tested ONLY with synthetic fixture rows built in the
exact shape finalize.py produces (see
tests/unit/test_annotation_import.py) -- never with real annotation data,
since no finalized export exists yet (annotation is still in progress).
It independently re-validates every row rather than trusting the
"finalized" label at face value, mirroring
ml/stance_classification/validate_splits.py's pattern of auditing a
pipeline's output from scratch.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from scripts.annotation import schema as ann_schema  # noqa: E402
from sqlalchemy import select  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from backend.app.models.comment import Comment, CommentSourceMetadata  # noqa: E402
from backend.app.models.enums import ExclusionCode, PredictionSource, StanceLabel  # noqa: E402
from backend.app.models.import_log import ImportRun  # noqa: E402
from backend.app.models.stance import StancePrediction  # noqa: E402
from backend.app.services.validation import hash_normalized_text, normalize_text  # noqa: E402

REQUIRED_COLUMNS = ("comment_id", "comment_text", "source_dataset", "source_unique_id")
MAX_ERRORS_RETAINED = 200


@dataclass
class AnnotationImportError:
    row_number: int
    source_comment_id: str
    message: str

    def to_dict(self) -> dict:
        return {"row_number": self.row_number, "comment_id": self.source_comment_id, "message": self.message}


@dataclass
class AnnotationImportReport:
    import_run_id: int
    total_rows: int = 0
    comments_created: int = 0
    comments_reused: int = 0
    predictions_created: int = 0
    skipped_already_imported_count: int = 0
    error_count: int = 0
    errors: list[AnnotationImportError] = field(default_factory=list)


def _validate_row(row: dict) -> str | None:
    for col in REQUIRED_COLUMNS:
        if not (row.get(col) or "").strip():
            return f"Missing or blank required column '{col}'"
    label = (row.get("annotator_label") or "").strip()
    excl = (row.get("exclusion_code") or "").strip()
    if label and excl:
        return "Both annotator_label and exclusion_code are set -- violates rule D8 mutual exclusivity"
    if not label and not excl:
        return "Neither annotator_label nor exclusion_code is set -- row is not actually finalized"
    if label and label not in ann_schema.STANCE_LABELS:
        return f"Invalid annotator_label '{label}'"
    if excl and excl not in ann_schema.EXCLUSION_CODES:
        return f"Invalid exclusion_code '{excl}'"
    conf = (row.get("annotation_confidence") or "").strip()
    if conf and conf not in ann_schema.CONFIDENCE_VALUES:
        return f"Invalid annotation_confidence '{conf}'"
    return None


def import_finalized_annotations(
    db: Session,
    policy_id: int,
    rows: Iterable[dict],
    source_label: str,
    annotator_ref: str = "single_annotator",
) -> AnnotationImportReport:
    import_run = ImportRun(
        policy_document_id=policy_id,
        import_type="annotation_import",
        source_label=source_label,
        started_at=datetime.now(timezone.utc),
    )
    db.add(import_run)
    db.flush()

    existing_source_keys: dict[tuple[str, str], int] = {
        (ds, sid): cid
        for ds, sid, cid in db.execute(
            select(
                CommentSourceMetadata.source_dataset,
                CommentSourceMetadata.source_record_id,
                CommentSourceMetadata.comment_id,
            ).join(Comment, Comment.id == CommentSourceMetadata.comment_id).where(
                Comment.policy_document_id == policy_id
            )
        ).all()
    }

    report = AnnotationImportReport(import_run_id=import_run.id)

    for row_number, row in enumerate(rows, start=1):
        report.total_rows += 1

        error = _validate_row(row)
        if error:
            report.error_count += 1
            if len(report.errors) < MAX_ERRORS_RETAINED:
                report.errors.append(AnnotationImportError(row_number, row.get("comment_id", "?"), error))
            continue

        source_key = (row["source_dataset"].strip(), row["source_unique_id"].strip())

        savepoint = db.begin_nested()
        try:
            if source_key in existing_source_keys:
                comment_id = existing_source_keys[source_key]
                report.comments_reused += 1
            else:
                text = row["comment_text"]
                normalized = normalize_text(text)
                comment = Comment(
                    policy_document_id=policy_id,
                    original_text=text,
                    normalized_text=normalized,
                    normalized_text_hash=hash_normalized_text(text),
                    language=row.get("language") or "unknown",
                    multiplicity=1,
                )
                db.add(comment)
                db.flush()
                db.add(
                    CommentSourceMetadata(
                        comment_id=comment.id,
                        source_dataset=source_key[0],
                        source_record_id=source_key[1],
                    )
                )
                existing_source_keys[source_key] = comment.id
                comment_id = comment.id
                report.comments_created += 1

            label = (row.get("annotator_label") or "").strip()
            excl = (row.get("exclusion_code") or "").strip()
            conf_raw = (row.get("annotation_confidence") or "").strip()

            # Idempotency for the PREDICTION itself: re-importing the same
            # finalized row twice must not create a second StancePrediction.
            already_has_prediction = db.execute(
                select(StancePrediction.id).where(
                    StancePrediction.comment_id == comment_id,
                    StancePrediction.annotator_or_model_ref == annotator_ref,
                    StancePrediction.pass_number == 1,
                )
            ).first()
            if already_has_prediction:
                report.skipped_already_imported_count += 1
            else:
                db.add(
                    StancePrediction(
                        comment_id=comment_id,
                        label=StanceLabel(label) if label else None,
                        exclusion_code=ExclusionCode(excl) if excl else None,
                        confidence=int(conf_raw) if conf_raw else None,
                        notes=row.get("annotation_notes") or None,
                        source=PredictionSource.HUMAN,
                        annotator_or_model_ref=annotator_ref,
                        pass_number=1,
                    )
                )
                report.predictions_created += 1
            savepoint.commit()
        except Exception as e:  # noqa: BLE001
            savepoint.rollback()
            report.error_count += 1
            if len(report.errors) < MAX_ERRORS_RETAINED:
                report.errors.append(
                    AnnotationImportError(row_number, row.get("comment_id", "?"), f"Unexpected error: {e}")
                )

    import_run.completed_at = datetime.now(timezone.utc)
    import_run.total_rows = report.total_rows
    import_run.created_count = report.comments_created
    import_run.updated_count = report.predictions_created
    import_run.skipped_count = report.skipped_already_imported_count
    import_run.error_count = report.error_count
    import_run.errors = [e.to_dict() for e in report.errors]
    db.commit()

    return report
