"""Document ingestion foundation (Phase 4).

Orchestrates: file validation -> text extraction -> section
identification -> versioned, immutable storage -> error reporting.
Never overwrites a previously-ingested version (requirement: "Do not
overwrite original uploaded documents") -- re-ingesting the same
policy_document_id always creates a new PolicyDocumentVersion row with an
incremented version_number.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.config import MAX_UPLOAD_SIZE_BYTES, SUPPORTED_DOCUMENT_EXTENSIONS
from backend.app.documents.extraction import get_extractor
from backend.app.documents.sections import identify_sections
from backend.app.models.enums import DocumentProcessingStatus
from backend.app.models.policy import PolicyDocumentVersion, PolicySection


class DocumentValidationError(ValueError):
    pass


@dataclass
class IngestionResult:
    version: PolicyDocumentVersion
    sections_created: int
    status: DocumentProcessingStatus
    error: str | None


def validate_upload(filename: str, raw_bytes: bytes) -> str:
    """Returns the validated file extension, or raises
    DocumentValidationError. Pure validation -- no side effects."""
    extension = Path(filename).suffix.lower()
    if extension not in SUPPORTED_DOCUMENT_EXTENSIONS:
        raise DocumentValidationError(
            f"Unsupported file type '{extension}'. Supported: {SUPPORTED_DOCUMENT_EXTENSIONS}"
        )
    if len(raw_bytes) == 0:
        raise DocumentValidationError("Uploaded file is empty.")
    if len(raw_bytes) > MAX_UPLOAD_SIZE_BYTES:
        raise DocumentValidationError(
            f"File exceeds the {MAX_UPLOAD_SIZE_BYTES} byte limit (respects the 8 GB RAM constraint)."
        )
    return extension


def ingest_policy_document(
    db: Session, policy_document_id: int, filename: str, raw_bytes: bytes
) -> IngestionResult:
    extension = validate_upload(filename, raw_bytes)  # raises on failure, before any row is written

    next_version_number = (
        db.execute(
            select(func.coalesce(func.max(PolicyDocumentVersion.version_number), 0)).where(
                PolicyDocumentVersion.policy_document_id == policy_document_id
            )
        ).scalar_one()
        + 1
    )

    extractor = get_extractor(extension)
    extraction = extractor.extract(raw_bytes) if extractor else None

    if extraction is None or not extraction.success:
        error = extraction.error if extraction else f"No extractor registered for '{extension}'"
        version = PolicyDocumentVersion(
            policy_document_id=policy_document_id,
            version_number=next_version_number,
            original_filename=filename,
            file_format=extension,
            raw_text="",
            status=DocumentProcessingStatus.FAILED,
            processing_error=error,
            ingested_at=datetime.now(timezone.utc),
        )
        db.add(version)
        db.commit()
        db.refresh(version)
        return IngestionResult(version=version, sections_created=0, status=DocumentProcessingStatus.FAILED, error=error)

    version = PolicyDocumentVersion(
        policy_document_id=policy_document_id,
        version_number=next_version_number,
        original_filename=filename,
        file_format=extension,
        raw_text=extraction.text,
        status=DocumentProcessingStatus.PROCESSED,
        processing_error=None,
        ingested_at=datetime.now(timezone.utc),
    )
    db.add(version)
    db.flush()  # get version.id without committing yet

    identified = identify_sections(extraction.text)
    for sec in identified:
        db.add(
            PolicySection(
                policy_document_id=policy_document_id,
                policy_document_version_id=version.id,
                section_label=sec.label,
                section_text=sec.text,
                order_index=sec.order_index,
            )
        )
    db.commit()
    db.refresh(version)

    return IngestionResult(
        version=version, sections_created=len(identified), status=DocumentProcessingStatus.PROCESSED, error=None
    )
