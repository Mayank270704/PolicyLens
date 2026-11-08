"""Bulk CSV comment ingestion (Phase 2).

Design choices, stated up front:

- **Schema validation** happens per row; a malformed row is recorded as
  an error and the import continues -- one bad row never aborts an
  entire file (requirement: "Error reports", and transaction safety via
  a per-row SAVEPOINT so a failed row can never corrupt rows around it).
- **Idempotency** is keyed on (policy_document_id, source_dataset,
  source_record_id) -- re-running the exact same CSV (e.g. after a
  network retry) must not create duplicate comments or double-count
  `multiplicity`. This is a DIFFERENT concept from the existing
  text-hash dedup used by the single-comment submission endpoint
  (routers/comments.py), which detects two DIFFERENT real source records
  that happen to share identical text and increments `multiplicity` for
  that -- bulk import still applies that same text-hash dedup for
  genuinely new source records, it just also adds a second, source-ID
  based idempotency check first.
- **Batch processing**: rows are committed in chunks (default 500), not
  one giant transaction, so memory and lock duration stay bounded on
  large files.
- **Import reports** are persisted as an `ImportRun` row (also the
  "import audit log" Phase 6 asks for) -- not just returned and
  discarded.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.comment import Comment, CommentSourceMetadata
from backend.app.models.import_log import ImportRun
from backend.app.services.validation import hash_normalized_text, normalize_text

REQUIRED_COLUMNS = ("original_text", "source_dataset", "source_record_id")
MAX_ERRORS_RETAINED = 200  # cap stored error detail; error_count always reports the true total
TEXT_SNIPPET_LEN = 80  # error logs keep only a short snippet, never full comment text


@dataclass
class RowError:
    row_number: int
    message: str
    text_snippet: str | None = None

    def to_dict(self) -> dict:
        return {"row_number": self.row_number, "message": self.message, "text_snippet": self.text_snippet}


@dataclass
class BulkImportReport:
    import_run_id: int
    total_rows: int = 0
    created_count: int = 0
    incremented_count: int = 0
    skipped_already_imported_count: int = 0
    error_count: int = 0
    errors: list[RowError] = field(default_factory=list)


def _validate_row(row: dict, row_number: int) -> str | None:
    for col in REQUIRED_COLUMNS:
        if not (row.get(col) or "").strip():
            return f"Missing or blank required column '{col}'"
    return None


def _load_existing_source_keys(db: Session, policy_id: int) -> set[tuple[str, str]]:
    stmt = (
        select(CommentSourceMetadata.source_dataset, CommentSourceMetadata.source_record_id)
        .join(Comment, Comment.id == CommentSourceMetadata.comment_id)
        .where(Comment.policy_document_id == policy_id)
    )
    return set(db.execute(stmt).all())


def _load_existing_text_hashes(db: Session, policy_id: int) -> dict[str, int]:
    stmt = select(Comment.normalized_text_hash, Comment.id).where(Comment.policy_document_id == policy_id)
    return dict(db.execute(stmt).all())


def import_comments_csv(
    db: Session,
    policy_id: int,
    rows: Iterable[dict],
    source_label: str,
    batch_size: int = 500,
) -> BulkImportReport:
    import_run = ImportRun(
        policy_document_id=policy_id,
        import_type="comment_csv",
        source_label=source_label,
        started_at=datetime.now(timezone.utc),
    )
    db.add(import_run)
    db.flush()

    existing_source_keys = _load_existing_source_keys(db, policy_id)
    existing_text_hashes = _load_existing_text_hashes(db, policy_id)

    report = BulkImportReport(import_run_id=import_run.id)
    batch_counter = 0

    for row_number, row in enumerate(rows, start=1):
        report.total_rows += 1
        batch_counter += 1

        error_message = _validate_row(row, row_number)
        if error_message:
            report.error_count += 1
            if len(report.errors) < MAX_ERRORS_RETAINED:
                snippet = (row.get("original_text") or "")[:TEXT_SNIPPET_LEN]
                report.errors.append(RowError(row_number, error_message, snippet))
            continue

        source_key = (row["source_dataset"].strip(), row["source_record_id"].strip())
        if source_key in existing_source_keys:
            report.skipped_already_imported_count += 1
            continue

        text = row["original_text"]
        normalized = normalize_text(text)
        text_hash = hash_normalized_text(text)

        savepoint = db.begin_nested()
        try:
            if text_hash in existing_text_hashes:
                existing_comment = db.get(Comment, existing_text_hashes[text_hash])
                existing_comment.multiplicity += 1
                report.incremented_count += 1
            else:
                comment = Comment(
                    policy_document_id=policy_id,
                    policy_section_id=row.get("policy_section_id"),
                    original_text=text,
                    normalized_text=normalized,
                    normalized_text_hash=text_hash,
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
                existing_text_hashes[text_hash] = comment.id
                report.created_count += 1
            existing_source_keys.add(source_key)
            savepoint.commit()
        except Exception as e:  # noqa: BLE001 -- intentionally broad: any row-level failure must not abort the import
            savepoint.rollback()
            report.error_count += 1
            if len(report.errors) < MAX_ERRORS_RETAINED:
                report.errors.append(RowError(row_number, f"Unexpected error: {e}", text[:TEXT_SNIPPET_LEN]))

        if batch_counter >= batch_size:
            db.commit()
            batch_counter = 0

    import_run.completed_at = datetime.now(timezone.utc)
    import_run.total_rows = report.total_rows
    import_run.created_count = report.created_count
    import_run.updated_count = report.incremented_count
    import_run.skipped_count = report.skipped_already_imported_count
    import_run.error_count = report.error_count
    import_run.errors = [e.to_dict() for e in report.errors]
    db.commit()

    return report
