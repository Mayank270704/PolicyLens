from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CommentCreate(BaseModel):
    """Input validation: text must be non-trivial; source fields required
    so provenance is never lost (requirement: "Preserve source IDs")."""

    original_text: str = Field(min_length=1, max_length=20000)
    language: str = Field(default="unknown", max_length=20)
    source_dataset: str = Field(min_length=1, max_length=200)
    source_record_id: str = Field(min_length=1, max_length=200)
    policy_section_id: Optional[int] = None

    @field_validator("original_text")
    @classmethod
    def not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("original_text must not be blank or whitespace-only")
        return v


class CommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    policy_document_id: int
    policy_section_id: Optional[int]
    original_text: str
    normalized_text: str
    language: str
    multiplicity: int
    validation_status: str
    pii_flagged: bool
    created_at: datetime


class CommentValidationResult(BaseModel):
    comment_id: int
    validation_status: str
    pii_flagged: bool
    pii_flag_reasons: list[str]
    suggested_exclusion_code: Optional[str] = None
