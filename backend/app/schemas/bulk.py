from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ImportRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    policy_document_id: int
    import_type: str
    source_label: str
    started_at: datetime
    completed_at: Optional[datetime]
    total_rows: int
    created_count: int
    updated_count: int
    skipped_count: int
    error_count: int
    errors: list[dict]


class BulkImportResponse(BaseModel):
    import_run_id: int
    total_rows: int
    created_count: int
    incremented_count: int
    skipped_already_imported_count: int
    error_count: int
    errors: list[dict]


class AnnotationImportResponse(BaseModel):
    import_run_id: int
    total_rows: int
    comments_created: int
    comments_reused: int
    predictions_created: int
    skipped_already_imported_count: int
    error_count: int
    errors: list[dict]
