from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class PolicyDocumentCreate(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    description: Optional[str] = Field(default=None, max_length=10000)
    jurisdiction: Optional[str] = Field(default=None, max_length=200)
    source_url: Optional[str] = Field(default=None, max_length=2000)


class PolicyDocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: Optional[str]
    jurisdiction: Optional[str]
    source_url: Optional[str]
    created_at: datetime


class PolicySectionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    policy_document_id: int
    section_label: str
    section_text: str
    order_index: int
