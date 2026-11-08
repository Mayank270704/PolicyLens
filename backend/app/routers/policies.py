from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.documents.ingestion import DocumentValidationError, ingest_policy_document
from backend.app.models.policy import PolicyDocument, PolicySection
from backend.app.schemas.common import PaginatedResponse
from backend.app.schemas.policy import PolicyDocumentCreate, PolicyDocumentOut, PolicySectionOut
from backend.app.services.pagination import paginate

router = APIRouter(tags=["policies"])


@router.post("/policies", response_model=PolicyDocumentOut, status_code=201)
def create_policy(payload: PolicyDocumentCreate, db: Session = Depends(get_db)) -> PolicyDocument:
    policy = PolicyDocument(
        title=payload.title, description=payload.description,
        jurisdiction=payload.jurisdiction, source_url=payload.source_url,
    )
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return policy


@router.get("/policies", response_model=PaginatedResponse[PolicyDocumentOut])
def list_policies(page: int = 1, page_size: int = 25, db: Session = Depends(get_db)):
    stmt = select(PolicyDocument).order_by(PolicyDocument.id)
    return paginate(db, stmt, page, page_size, PolicyDocument, PolicyDocumentOut)


@router.get("/policies/{policy_id}", response_model=PolicyDocumentOut)
def get_policy(policy_id: int, db: Session = Depends(get_db)) -> PolicyDocument:
    policy = db.get(PolicyDocument, policy_id)
    if policy is None:
        raise HTTPException(status_code=404, detail=f"Policy {policy_id} not found")
    return policy


@router.post("/policies/{policy_id}/documents", status_code=201)
async def upload_policy_document(policy_id: int, file: UploadFile, db: Session = Depends(get_db)):
    policy = db.get(PolicyDocument, policy_id)
    if policy is None:
        raise HTTPException(status_code=404, detail=f"Policy {policy_id} not found")

    raw_bytes = await file.read()
    try:
        result = ingest_policy_document(db, policy_id, file.filename or "upload", raw_bytes)
    except DocumentValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))

    return {
        "version_id": result.version.id,
        "version_number": result.version.version_number,
        "status": result.status.value,
        "sections_created": result.sections_created,
        "error": result.error,
    }


@router.get("/policies/{policy_id}/sections", response_model=PaginatedResponse[PolicySectionOut])
def list_sections(policy_id: int, page: int = 1, page_size: int = 25, db: Session = Depends(get_db)):
    if db.get(PolicyDocument, policy_id) is None:
        raise HTTPException(status_code=404, detail=f"Policy {policy_id} not found")
    stmt = (
        select(PolicySection)
        .where(PolicySection.policy_document_id == policy_id)
        .order_by(PolicySection.order_index)
    )
    return paginate(db, stmt, page, page_size, PolicySection, PolicySectionOut)


@router.get("/policies/{policy_id}/sections/{section_id}", response_model=PolicySectionOut)
def get_section(policy_id: int, section_id: int, db: Session = Depends(get_db)) -> PolicySection:
    section = db.get(PolicySection, section_id)
    if section is None or section.policy_document_id != policy_id:
        raise HTTPException(status_code=404, detail=f"Section {section_id} not found under policy {policy_id}")
    return section
