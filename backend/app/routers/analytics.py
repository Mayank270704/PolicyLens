from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.policy import PolicyDocument
from backend.app.schemas.analytics import CrossPolicySummaryOut, PolicyAnalyticsOut
from backend.app.services.analytics import compute_cross_policy_summary, compute_policy_analytics

router = APIRouter(tags=["analytics"])


@router.get("/policies/{policy_id}/analytics", response_model=PolicyAnalyticsOut)
def get_policy_analytics(policy_id: int, db: Session = Depends(get_db)) -> PolicyAnalyticsOut:
    if db.get(PolicyDocument, policy_id) is None:
        raise HTTPException(status_code=404, detail=f"Policy {policy_id} not found")
    return compute_policy_analytics(db, policy_id)


@router.get("/analytics/summary", response_model=CrossPolicySummaryOut)
def get_cross_policy_summary(db: Session = Depends(get_db)) -> CrossPolicySummaryOut:
    return compute_cross_policy_summary(db)
