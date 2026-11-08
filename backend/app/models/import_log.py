from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base, TimestampMixin


class ImportRun(Base, TimestampMixin):
    """Audit log for every bulk import (CSV comment import or annotation
    import) -- requirement: "Import audit logs" (Phase 6) and "Import
    reports" (Phase 2). One row per import attempt, append-only; never
    edited after completion. `errors` holds up to the first N row-level
    errors (full detail), with `error_count` as the true total so a
    large error count is never silently truncated without saying so."""

    __tablename__ = "import_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    policy_document_id: Mapped[int] = mapped_column(ForeignKey("policy_documents.id"), nullable=False)
    import_type: Mapped[str] = mapped_column(String(30), nullable=False)  # "comment_csv" | "annotation_import"
    source_label: Mapped[str] = mapped_column(String(500), nullable=False)  # filename or caller-provided label

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    total_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    skipped_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    errors: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
