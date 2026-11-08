from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class RepresentativeCommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    comment_id: int
    rank: int
    similarity_score: Optional[float]


class ConcernGroupOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    policy_document_id: int
    method: str
    size: int
    is_noise: bool
    created_at: datetime
    representative_comments: list[RepresentativeCommentOut] = []


class EvidenceReferenceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    comment_id: int
    rank: int


class SummaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    group_id: int
    text: str
    method: str
    model_version_id: Optional[int]
    evidence_references: list[EvidenceReferenceOut] = []
