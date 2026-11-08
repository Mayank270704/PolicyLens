from __future__ import annotations

import csv
import io

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.import_log import ImportRun
from backend.app.models.policy import PolicyDocument
from backend.app.schemas.bulk import AnnotationImportResponse, BulkImportResponse, ImportRunOut
from backend.app.schemas.common import PaginatedResponse
from backend.app.services.annotation_import import import_finalized_annotations
from backend.app.services.authz import Role, require_role
from backend.app.services.bulk_export import export_comments_csv
from backend.app.services.bulk_import import import_comments_csv
from backend.app.services.pagination import paginate

router = APIRouter(tags=["bulk"])


def _read_csv_rows(raw_bytes: bytes) -> list[dict]:
    try:
        text = raw_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw_bytes.decode("latin-1")
    return list(csv.DictReader(io.StringIO(text)))


@router.post("/policies/{policy_id}/comments/bulk-import", response_model=BulkImportResponse, status_code=201)
async def bulk_import_comments(
    policy_id: int,
    file: UploadFile,
    db: Session = Depends(get_db),
    _user=Depends(require_role(Role.RESEARCHER)),
):
    if db.get(PolicyDocument, policy_id) is None:
        raise HTTPException(status_code=404, detail=f"Policy {policy_id} not found")
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=422, detail="Uploaded CSV file is empty.")
    rows = _read_csv_rows(raw)
    report = import_comments_csv(db, policy_id, rows, source_label=file.filename or "upload.csv")
    return BulkImportResponse(
        import_run_id=report.import_run_id,
        total_rows=report.total_rows,
        created_count=report.created_count,
        incremented_count=report.incremented_count,
        skipped_already_imported_count=report.skipped_already_imported_count,
        error_count=report.error_count,
        errors=[e.to_dict() for e in report.errors],
    )


@router.get("/policies/{policy_id}/comments/export", response_class=PlainTextResponse)
def export_comments(
    policy_id: int, db: Session = Depends(get_db), _user=Depends(require_role(Role.RESEARCHER))
) -> str:
    if db.get(PolicyDocument, policy_id) is None:
        raise HTTPException(status_code=404, detail=f"Policy {policy_id} not found")
    return export_comments_csv(db, policy_id)


@router.post(
    "/policies/{policy_id}/annotations/import", response_model=AnnotationImportResponse, status_code=201
)
async def import_annotations(
    policy_id: int,
    file: UploadFile,
    db: Session = Depends(get_db),
    _user=Depends(require_role(Role.RESEARCHER)),
):
    """Consumes a CSV in EXACTLY scripts/annotation/finalize.py's output
    schema. Never generates, fabricates, or infers a label -- every
    annotator_label/exclusion_code value in the uploaded file must already
    be a genuine human decision; this endpoint only moves it into the
    backend database."""
    if db.get(PolicyDocument, policy_id) is None:
        raise HTTPException(status_code=404, detail=f"Policy {policy_id} not found")
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=422, detail="Uploaded CSV file is empty.")
    rows = _read_csv_rows(raw)
    report = import_finalized_annotations(db, policy_id, rows, source_label=file.filename or "upload.csv")
    return AnnotationImportResponse(
        import_run_id=report.import_run_id,
        total_rows=report.total_rows,
        comments_created=report.comments_created,
        comments_reused=report.comments_reused,
        predictions_created=report.predictions_created,
        skipped_already_imported_count=report.skipped_already_imported_count,
        error_count=report.error_count,
        errors=[e.to_dict() for e in report.errors],
    )


@router.get("/policies/{policy_id}/import-runs", response_model=PaginatedResponse[ImportRunOut])
def list_import_runs(policy_id: int, page: int = 1, page_size: int = 25, db: Session = Depends(get_db)):
    if db.get(PolicyDocument, policy_id) is None:
        raise HTTPException(status_code=404, detail=f"Policy {policy_id} not found")
    stmt = (
        select(ImportRun)
        .where(ImportRun.policy_document_id == policy_id)
        .order_by(ImportRun.started_at.desc())
    )
    return paginate(db, stmt, page, page_size, ImportRun, ImportRunOut)
