from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.concern import ConcernGroup
from backend.app.models.policy import PolicyDocument
from backend.app.models.summary import Summary
from backend.app.schemas.common import PaginatedResponse
from backend.app.schemas.concern import ConcernGroupOut, SummaryOut
from backend.app.services.pagination import paginate

router = APIRouter(tags=["concerns"])


@router.get("/policies/{policy_id}/concern-groups", response_model=PaginatedResponse[ConcernGroupOut])
def list_concern_groups(policy_id: int, page: int = 1, page_size: int = 25, db: Session = Depends(get_db)):
    if db.get(PolicyDocument, policy_id) is None:
        raise HTTPException(status_code=404, detail=f"Policy {policy_id} not found")
    stmt = select(ConcernGroup).where(ConcernGroup.policy_document_id == policy_id).order_by(ConcernGroup.id)
    return paginate(db, stmt, page, page_size, ConcernGroup, ConcernGroupOut)


@router.get("/concern-groups/{group_id}", response_model=ConcernGroupOut)
def get_concern_group(group_id: int, db: Session = Depends(get_db)) -> ConcernGroup:
    group = db.get(ConcernGroup, group_id)
    if group is None:
        raise HTTPException(status_code=404, detail=f"Concern group {group_id} not found")
    return group


@router.get("/concern-groups/{group_id}/summary", response_model=list[SummaryOut])
def get_group_summaries(group_id: int, db: Session = Depends(get_db)):
    if db.get(ConcernGroup, group_id) is None:
        raise HTTPException(status_code=404, detail=f"Concern group {group_id} not found")
    stmt = select(Summary).where(Summary.group_id == group_id).order_by(Summary.created_at.desc())
    return db.execute(stmt).scalars().all()
