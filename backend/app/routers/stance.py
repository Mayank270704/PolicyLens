from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.comment import Comment
from backend.app.models.stance import StancePrediction
from backend.app.schemas.stance import StancePredictionOut

router = APIRouter(tags=["stance"])


@router.get("/comments/{comment_id}/stance", response_model=list[StancePredictionOut])
def get_stance_predictions(comment_id: int, db: Session = Depends(get_db)):
    if db.get(Comment, comment_id) is None:
        raise HTTPException(status_code=404, detail=f"Comment {comment_id} not found")
    stmt = (
        select(StancePrediction)
        .where(StancePrediction.comment_id == comment_id)
        .order_by(StancePrediction.created_at)
    )
    return db.execute(stmt).scalars().all()
