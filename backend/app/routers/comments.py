from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.comment import Comment, CommentSourceMetadata
from backend.app.models.policy import PolicyDocument, PolicySection
from backend.app.schemas.comment import CommentCreate, CommentOut, CommentValidationResult
from backend.app.schemas.common import PaginatedResponse
from backend.app.services.pagination import paginate
from backend.app.services.privacy import scan_for_pii
from backend.app.services.validation import classify_comment_for_exclusion, hash_normalized_text, normalize_text

router = APIRouter(tags=["comments"])


@router.post("/policies/{policy_id}/comments", response_model=CommentOut, status_code=201)
def submit_comment(policy_id: int, payload: CommentCreate, db: Session = Depends(get_db)) -> Comment:
    if db.get(PolicyDocument, policy_id) is None:
        raise HTTPException(status_code=404, detail=f"Policy {policy_id} not found")
    if payload.policy_section_id is not None:
        section = db.get(PolicySection, payload.policy_section_id)
        if section is None or section.policy_document_id != policy_id:
            raise HTTPException(status_code=422, detail="policy_section_id does not belong to this policy")

    normalized = normalize_text(payload.original_text)
    text_hash = hash_normalized_text(payload.original_text)

    existing = db.execute(
        select(Comment).where(
            Comment.policy_document_id == policy_id, Comment.normalized_text_hash == text_hash
        )
    ).scalar_one_or_none()
    if existing is not None:
        # Exact-duplicate text: increment multiplicity rather than create a
        # second row -- mirrors unique_texts.csv's own multiplicity column
        # and keeps comment_id stable/unique per genuinely distinct text.
        existing.multiplicity += 1
        db.commit()
        db.refresh(existing)
        return existing

    comment = Comment(
        policy_document_id=policy_id,
        policy_section_id=payload.policy_section_id,
        original_text=payload.original_text,
        normalized_text=normalized,
        normalized_text_hash=text_hash,
        language=payload.language,
        multiplicity=1,
    )
    db.add(comment)
    db.flush()
    db.add(
        CommentSourceMetadata(
            comment_id=comment.id,
            source_dataset=payload.source_dataset,
            source_record_id=payload.source_record_id,
        )
    )
    db.commit()
    db.refresh(comment)
    return comment


@router.get("/policies/{policy_id}/comments", response_model=PaginatedResponse[CommentOut])
def list_comments(policy_id: int, page: int = 1, page_size: int = 25, db: Session = Depends(get_db)):
    if db.get(PolicyDocument, policy_id) is None:
        raise HTTPException(status_code=404, detail=f"Policy {policy_id} not found")
    stmt = select(Comment).where(Comment.policy_document_id == policy_id).order_by(Comment.id)
    return paginate(db, stmt, page, page_size, Comment, CommentOut)


@router.get("/comments/{comment_id}", response_model=CommentOut)
def get_comment(comment_id: int, db: Session = Depends(get_db)) -> Comment:
    comment = db.get(Comment, comment_id)
    if comment is None:
        raise HTTPException(status_code=404, detail=f"Comment {comment_id} not found")
    return comment


@router.post("/comments/{comment_id}/validate", response_model=CommentValidationResult)
def validate_comment(comment_id: int, db: Session = Depends(get_db)) -> CommentValidationResult:
    """Runs the PII scan and the exclusion-code heuristic over a comment,
    updates its stored validation_status, and returns the result. Per
    services/privacy.py's own disclaimer, a clean PII scan is reported as
    "not flagged by this heuristic," never as "verified anonymous.\""""
    comment = db.get(Comment, comment_id)
    if comment is None:
        raise HTTPException(status_code=404, detail=f"Comment {comment_id} not found")

    pii_result = scan_for_pii(comment.original_text)
    suggested_exclusion = classify_comment_for_exclusion(comment.original_text)

    comment.pii_flagged = pii_result.flagged
    if pii_result.flagged:
        comment.redacted_text_for_display = pii_result.redacted_text
    comment.validation_status = "flagged_for_review" if (pii_result.flagged or suggested_exclusion) else "validated"
    db.commit()

    return CommentValidationResult(
        comment_id=comment_id,
        validation_status=comment.validation_status,
        pii_flagged=pii_result.flagged,
        pii_flag_reasons=pii_result.reasons,
        suggested_exclusion_code=suggested_exclusion,
    )
