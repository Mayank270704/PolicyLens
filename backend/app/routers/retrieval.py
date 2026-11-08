from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.policy import PolicyDocument
from backend.app.schemas.retrieval import RetrievalResponse
from backend.app.services.retrieval import retrieve_sections

router = APIRouter(tags=["retrieval"])


@router.get("/policies/{policy_id}/retrieve", response_model=RetrievalResponse)
def retrieve(
    policy_id: int,
    query: str = Query(min_length=1, max_length=2000),
    top_k: int = Query(default=5, ge=1, le=50),
    version_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    if db.get(PolicyDocument, policy_id) is None:
        raise HTTPException(status_code=404, detail=f"Policy {policy_id} not found")
    results = retrieve_sections(db, policy_id, query, top_k=top_k, policy_document_version_id=version_id)
    return RetrievalResponse(results=results)
